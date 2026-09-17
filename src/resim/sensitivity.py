"""Sensitivity analysis — which parameters actually move the model's moments.

`plan.md` Phase 6 asks for Morris screening and then Sobol indices on the survivors. This is
that, with no new dependencies: Morris elementary effects and the Saltelli estimators are a
few lines each, and the alternative was adding SALib and scipy for them.

Two decisions worth knowing before reading any output:

- **Only free and `guess` parameters are screened.** A sourced point value (max LTV, DSTI,
  the construction lag) is not uncertainty the model owns; varying it would measure the
  world's sensitivity, not the model's.
- **Common random numbers.** One fixed seed across a whole design, so a difference between two
  points is the parameters and not the seed. Without it the elementary effects of a stochastic
  ABM are mostly noise.

Baseline only: parameters that act through an intervention (the rent cap's `intermediation_share`,
for one) correctly show zero here, and their sensitivity is the elasticity sweep in
`docs/experiments/rent-cap.md`.

    uv run python -m resim.sensitivity morris --trajectories 10
    uv run python -m resim.sensitivity sobol --n 128 --params overbid_sigma,premium_rural,...

Results land in `runs/` (gitignored), and the reported run is written up in
`docs/validation.md` under "Sensitivity analysis".
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from . import metrics
from .agents import household as household_mod
from .agents import landlord as landlord_mod
from .config import CapResponseConfig, SimConfig, ZoneType
from .engine import Engine
from .market import clearing as clearing_mod
from .scenario import Scenario

# parameter -> (low, high). Documented ranges where one exists, else ±30% around a calibrated
# guess. Keep this table and docs/model-spec.md §7 consistent.
SPACE: dict[str, tuple[float, float]] = {
    "expectation_momentum": (0.5, 0.9),
    # phase G: the range that delivers the sourced 6–17% per-sale dispersion
    "overbid_sigma": (0.10, 0.35),
    # phase G §5c.7, the scarcity channel's one free parameter
    "tightness_half_saturation": (120.0, 1400.0),
    "ask_decay": (0.02, 0.05),
    "buy_attempt_prob": (0.35, 0.65),
    "seeker_wealth_median": (10_000.0, 20_000.0),
    # §7.1 (2026-09-14): `landlord_required_spread` was split into a measured prime
    # spread and the declared free premium. The premium is what a sweep should move —
    # the prime spread is measured and `c` has its own sourced range.
    "small_landlord_premium": (0.020, 0.030),  # narrowed by §7.1b, 2026-09-15
    "landlord_cost_share": (0.20, 0.24),
    "landlord_zone_risk_premium": (0.010, 0.020),
    # spec §7.2b (2026-09-16): G2's dial — the share of landlords with a cheap (private) exit
    # vs an expensive (agency) one, in place of the retired `holding_years`. The WIDE regional
    # band, not the two-national-source band: G2 sweeps beyond Fotocasa/idealista's 0.64–0.70
    # on purpose, because the regional spread (Murcia/Navarra/Baleares high,
    # Extremadura/País Vasco/Andalucía low) is real. Read from
    # `CapResponseConfig.intermediation_share_regional_range`, not invented here.
    "intermediation_share": CapResponseConfig().intermediation_share_regional_range,
    "congestion_gain": (0.02, 0.15),
    "search_burden_escalation": (0.02, 0.06),
    "premium_secondary": (0.75, 0.95),
    "premium_rural": (0.35, 0.55),
    "formation_metro_weight": (0.45, 0.65),
    "withheld_tensioned": (0.30, 0.50),
    "max_starts_per_tick": (19.0, 28.0),
    "base_starts_per_tick": (11.0, 17.0),
    "margin_threshold": (0.15, 0.20),
    "presale_share": (0.30, 0.50),
    "default_rate": (0.03, 0.07),
    "perceived_risk_markup": (1.5, 3.0),
    "price_index_smoothing": (0.2, 0.4),
    "tenant_move_prob": (0.04, 0.08),
    # --- phase D, sale-side price formation (model-spec §5c) ------------------------------
    "search_listings": (1.0, 10.0),  # rounded to an int inside _config_for
    "ask_markup": (0.08, 0.16),
    # phase G: identified on the measured discount, which needs a LOW weight
    "seller_bargaining_power": (0.15, 0.60),
    "auction_increment": (0.002, 0.010),
    "momentum_gain": (1.5, 3.5),
    "max_listing_ticks": (4.0, 8.0),
    "selling_cost_share": (0.01, 0.07),  # widened to the sourced band, 2026-09-16
    # --- phase C, insolvency (model-spec §6c) ---------------------------------------------
    # The jobless PATH is data and is not here: screening it would measure the world's
    # uncertainty, not the model's. What is here is everything the model had to assume.
    "essential_share": (0.34, 0.71),
    "exit_hazard": (0.15, 0.25),
    "incidence_relative_risk": (2.0, 2.45),
    "judicial_lag_ticks": (8.0, 16.0),
    "lockout_ticks": (8.0, 20.0),
    "reo_discount": (0.10, 0.35),
    "reo_release_share": (0.05, 0.30),
}
NAMES: list[str] = list(SPACE)

# below this coefficient of variation across a design, a moment is treated as flat and its
# variance decomposition is not reported: there is no variance to attribute (see `sobol`)
CV_FLOOR = 0.01

# the §9 moments, plus the two the zone ladder is judged on and three diagnostics
OUTPUTS: list[str] = [
    "pti",
    "pti_order_margin",
    "ownership",
    "transactions",
    "completion_ratio",
    "overburden",
    "price_ratio_tr",
    "rent_level",
    "vacancy_market_t",
    "cash_share",
    # phases C and D added mechanisms, so they added moments to decompose. The variance rule
    # (model-spec §13.2) applies to these exactly as it does to the price level.
    "purchase_effort",
    "arrears",
    "foreclosure_rate",
    "sale_discount",
    "sold_in_quarter",
    "bidders",
]


def scale(unit: np.ndarray) -> dict[str, float]:
    """Map a point in the unit hypercube onto the parameter space."""
    return {
        name: SPACE[name][0] + u * (SPACE[name][1] - SPACE[name][0])
        for name, u in zip(NAMES, unit, strict=True)
    }


def _config_for(x: dict[str, float], seed: int, ticks: int) -> SimConfig:
    cfg = SimConfig.baseline(seed=seed, ticks=ticks)
    market = dataclasses.replace(
        cfg.market,
        expectation_momentum=x["expectation_momentum"],
        overbid_sigma=x["overbid_sigma"],
        tightness_half_saturation=x["tightness_half_saturation"],
        ask_decay=x["ask_decay"],
        search_listings=int(round(x["search_listings"])),
        ask_markup=x["ask_markup"],
        seller_bargaining_power=x["seller_bargaining_power"],
        auction_increment=x["auction_increment"],
        max_listing_ticks=int(round(x["max_listing_ticks"])),
        selling_cost_share=x["selling_cost_share"],
        small_landlord_premium=x["small_landlord_premium"],
        landlord_cost_share=x["landlord_cost_share"],
        landlord_zone_risk_premium=x["landlord_zone_risk_premium"],
        default_rate=x["default_rate"],
        perceived_risk_markup=x["perceived_risk_markup"],
        price_index_smoothing=x["price_index_smoothing"],
    )
    metro = x["formation_metro_weight"]
    rest = 1.0 - metro
    population = dataclasses.replace(
        cfg.population,
        buy_attempt_prob=x["buy_attempt_prob"],
        seeker_wealth_median=x["seeker_wealth_median"],
        tenant_move_prob=x["tenant_move_prob"],
        formation_zone_weights=(metro, rest * 0.35 / 0.55, rest * 0.20 / 0.55),
    )
    developer = dataclasses.replace(
        cfg.developer,
        max_starts_per_tick=int(round(x["max_starts_per_tick"])),
        base_starts_per_tick=int(round(x["base_starts_per_tick"])),
        margin_threshold=x["margin_threshold"],
        presale_share=x["presale_share"],
    )
    premium = {
        ZoneType.TENSIONED: 1.0,
        ZoneType.SECONDARY: x["premium_secondary"],
        ZoneType.RURAL: x["premium_rural"],
    }
    zones = tuple(
        dataclasses.replace(
            z,
            location_premium=premium[z.zone],
            withheld_share=(
                x["withheld_tensioned"] if z.zone is ZoneType.TENSIONED else z.withheld_share
            ),
        )
        for z in cfg.zones
    )
    labour = dataclasses.replace(
        cfg.labour,
        exit_hazard=x["exit_hazard"],
        incidence_relative_risk=x["incidence_relative_risk"],
    )
    insolvency = dataclasses.replace(
        cfg.insolvency,
        essential_share=x["essential_share"],
        judicial_lag_ticks=int(round(x["judicial_lag_ticks"])),
        lockout_ticks=int(round(x["lockout_ticks"])),
        reo_discount=x["reo_discount"],
        reo_release_share=x["reo_release_share"],
    )
    cap_response = dataclasses.replace(
        cfg.cap_response, intermediation_share=x["intermediation_share"]
    )
    return dataclasses.replace(
        cfg,
        cap_response=cap_response,
        market=market,
        population=population,
        developer=developer,
        zones=zones,
        labour=labour,
        insolvency=insolvency,
    )


def evaluate(x: dict[str, float], seed: int = 1, ticks: int = 40) -> dict[str, float]:
    """Run the model once at `x` and return the moments the analysis is judged on."""
    cfg = _config_for(x, seed, ticks)
    # Behavioural constants that still live at module level; set and restore them around the
    # run. `hazard_scale` used to trip this exact bug — phase A moved it into
    # `CapResponseConfig`, and this module went on patching a module attribute that no longer
    # existed, so every sweep since had silently held it at its default (fixed in phase E).
    # It is moot now: model-spec §7.2 retired `hazard_scale` outright, so there is no field
    # left to patch, correctly or not. `intermediation_share`, §7.2b's dial in the swept set
    # (retiring `holding_years` in turn), is a `CapResponseConfig` field like
    # `selling_cost_share`, so it goes through `dataclasses.replace` in `_config_for` above,
    # never through this module-level save/restore.
    saved = (
        landlord_mod.CONGESTION_GAIN,
        household_mod.SEARCH_BURDEN_ESCALATION,
        clearing_mod.MOMENTUM_GAIN,
    )
    landlord_mod.CONGESTION_GAIN = x["congestion_gain"]
    household_mod.SEARCH_BURDEN_ESCALATION = x["search_burden_escalation"]
    clearing_mod.MOMENTUM_GAIN = x["momentum_gain"]
    try:
        state = Engine(Scenario(name="sensitivity", baseline=cfg)).run()
    finally:
        (
            landlord_mod.CONGESTION_GAIN,
            household_mod.SEARCH_BURDEN_ESCALATION,
            clearing_mod.MOMENTUM_GAIN,
        ) = saved
    frame = metrics.to_frame(state)
    tail = frame.iloc[-16:]
    households = max(1, len(state.households))
    return {
        "pti": float(tail.price_to_income.mean()),
        # how much room the T > S > R ordering has: negative means the ladder inverted
        "pti_order_margin": float(
            min(
                tail.price_to_income_tensioned.mean() - tail.price_to_income_secondary.mean(),
                tail.price_to_income_secondary.mean() - tail.price_to_income_rural.mean(),
            )
        ),
        "ownership": float(tail.ownership_rate.mean()),
        "transactions": float(4 * tail.transactions.mean() / households),
        "completion_ratio": float(tail.completion_ratio.mean()),
        "overburden": float(tail.rent_overburden_share.mean()),
        "price_ratio_tr": float((tail.price_tensioned / tail.price_rural).mean()),
        "rent_level": float(tail.rent_national.mean()),
        "vacancy_market_t": float(tail.vacancy_market_tensioned.mean()),
        "cash_share": float(tail.cash_purchase_share.mean()),
        "purchase_effort": float(tail.purchase_effort.mean()),
        "arrears": float(tail.arrears_share.mean()),
        "foreclosure_rate": float(tail.foreclosure_rate.mean()),
        "sale_discount": float(tail.sale_discount_median.mean()),
        "sold_in_quarter": float(tail.sold_within_quarter_share.mean()),
        "bidders": float(tail.bidders_per_listing.mean()),
    }


# The §9 bands the calibration window is judged on — 2014–2025 moments ONLY. The 2008–13
# hold-out is sealed (model-spec §13.4) and appears nowhere in this table, which is the
# point: a parameter fitted here has never seen the episode it will be tested on.
CALIBRATION_BANDS: dict[str, tuple[float, float]] = {
    "pti": (7.0, 8.2),
    "ownership": (0.70, 0.74),
    "transactions": (0.025, 0.036),
    "completion_ratio": (0.40, 0.70),
    "overburden": (0.26, 0.34),
    "purchase_effort": (0.35, 0.40),
    "arrears": (0.010, 0.040),
    "foreclosure_rate": (0.0010, 0.0080),
    "sold_in_quarter": (0.43, 0.63),
    "sale_discount": (0.04, 0.12),
    "bidders": (1.0, 7.0),
    "pti_order_margin": (0.0, float("inf")),
}


def band_loss(moments: dict[str, float]) -> tuple[float, dict[str, float]]:
    """Squared relative distance outside each band, summed. Zero inside every band.

    A band loss rather than a distance to a point: the evidence gives ranges, and scoring
    against a midpoint would invent precision the sources do not have and would drag the
    model toward the centre of bands it is already inside.
    """
    per: dict[str, float] = {}
    for name, (lo, hi) in CALIBRATION_BANDS.items():
        value = moments.get(name, float("nan"))
        if value != value:  # NaN: a moment with no observations this run
            per[name] = 1.0
            continue
        scale_ = max(abs(lo), abs(hi) if hi != float("inf") else abs(lo), 1e-9)
        if value < lo:
            per[name] = ((lo - value) / scale_) ** 2
        elif value > hi:
            per[name] = ((value - hi) / scale_) ** 2
        else:
            per[name] = 0.0
    return float(sum(per.values())), per


def lhs(n: int, seeds: tuple[int, ...], ticks: int) -> dict:
    """Latin-hypercube sweep over the free parameters, scored against the §9 bands.

    This is the first step of the calibration protocol (model-spec §13.4): sample the space,
    score each point on the calibration window, and report where the model wants to be. It
    does NOT adopt anything — adoption is a decision recorded in docs/validation.md, because
    "the sweep said so" is not a reason to move a parameter that has a source.
    """
    rng = np.random.default_rng(14092026)
    k = len(NAMES)
    # one stratified sample per parameter, independently shuffled: the Latin-hypercube design
    cuts = (np.arange(n)[:, None] + rng.random((n, k))) / n
    design = np.column_stack([rng.permutation(cuts[:, j]) for j in range(k)])

    rows = []
    for i in range(n):
        point = scale(design[i])
        losses, moments = [], []
        for seed in seeds:
            m = evaluate(point, seed, ticks)
            loss, _ = band_loss(m)
            losses.append(loss)
            moments.append(m)
        mean_moments = {o: float(np.mean([m[o] for m in moments])) for o in OUTPUTS}
        rows.append(
            {
                "point": {name: float(point[name]) for name in NAMES},
                "loss": float(np.mean(losses)),
                "moments": mean_moments,
            }
        )
    rows.sort(key=lambda r: r["loss"])

    # the defaults, scored the same way, so "better than what we have" is answerable
    default = {name: float(getattr_default(name)) for name in NAMES}
    default_losses, default_moments = [], []
    for seed in seeds:
        m = evaluate(default, seed, ticks)
        loss, per = band_loss(m)
        default_losses.append(loss)
        default_moments.append(m)
    default_row = {
        "point": default,
        "loss": float(np.mean(default_losses)),
        "moments": {o: float(np.mean([m[o] for m in default_moments])) for o in OUTPUTS},
        "per_moment": per,
    }
    return {
        "method": "lhs",
        "n": n,
        "seeds": list(seeds),
        "ticks": ticks,
        "evaluations": (n + 1) * len(seeds),
        "default": default_row,
        "rows": rows,
    }


def getattr_default(name: str) -> float:
    """The shipped value of a swept parameter, for scoring the defaults on the same design."""
    cfg = SimConfig.baseline(seed=1, ticks=4)
    lookups: dict[str, float] = {
        "intermediation_share": cfg.cap_response.intermediation_share,
        "congestion_gain": landlord_mod.CONGESTION_GAIN,
        "search_burden_escalation": household_mod.SEARCH_BURDEN_ESCALATION,
        "momentum_gain": clearing_mod.MOMENTUM_GAIN,
        "formation_metro_weight": cfg.population.formation_zone_weights[0],
        "premium_secondary": cfg.zone(ZoneType.SECONDARY).location_premium,
        "premium_rural": cfg.zone(ZoneType.RURAL).location_premium,
        "withheld_tensioned": cfg.zone(ZoneType.TENSIONED).withheld_share,
    }
    if name in lookups:
        return float(lookups[name])
    for block in (cfg.market, cfg.population, cfg.developer, cfg.labour, cfg.insolvency):
        if hasattr(block, name):
            return float(getattr(block, name))
    raise KeyError(name)


def _eval_one(job: tuple[dict[str, float], int, int]) -> dict[str, float]:
    """Pool worker: one design point. Module level because a Pool must pickle it."""
    point, seed, ticks = job
    return evaluate(point, seed, ticks)


def _eval_many(
    points: list[dict[str, float]], seed: int, ticks: int, jobs: int
) -> list[dict[str, float]]:
    """Evaluate a design, in parallel when asked. Results are identical either way: every
    point is a deterministic run of its own config at the same fixed seed (the common-random-
    numbers rule above), so process order cannot change a number."""
    jobs_ = max(1, jobs)
    if jobs_ == 1:
        return [evaluate(point, seed, ticks) for point in points]
    with Pool(processes=jobs_) as pool:
        return pool.map(_eval_one, [(point, seed, ticks) for point in points], chunksize=1)


def _morris_trajectory(job: tuple[int, int, int, int, int]) -> tuple[list[list[float]], int]:
    """One Morris trajectory, k+1 runs walked in sequence. Trajectories are independent of
    each other, which is where the parallelism is; the walk inside one is not."""
    index, trajectories, seed, ticks, levels = job
    delta = levels / (2.0 * (levels - 1))
    k = len(NAMES)
    rng = np.random.default_rng((20260908, index))
    point = rng.choice([0.0, 1.0 - delta], size=k)
    previous = evaluate(scale(point), seed, ticks)
    per_param: list[list[float]] = [[] for _ in range(k)]
    order = rng.permutation(k)
    effects: dict[str, list[list[float]]] = {o: [[] for _ in range(k)] for o in OUTPUTS}
    for i in order:
        step = delta if point[i] <= 1.0 - delta + 1e-9 else -delta
        moved = point.copy()
        moved[i] = float(np.clip(point[i] + step, 0.0, 1.0))
        taken = moved[i] - point[i]
        current = evaluate(scale(moved), seed, ticks)
        for output in OUTPUTS:
            effects[output][i].append((current[output] - previous[output]) / taken)
        point, previous = moved, current
    del per_param
    return effects, k + 1


def morris(trajectories: int, seed: int, ticks: int, levels: int = 4, jobs: int = 1) -> dict:
    """Elementary-effects screening: `trajectories` × (k+1) runs.

    One parameter moves per step along a random path through the grid, so each parameter gets
    `trajectories` elementary effects. Reports mu_star (mean |effect|, how much it matters) and
    sigma (spread, i.e. interaction or non-linearity).
    """
    k = len(NAMES)
    effects: dict[str, list[list[float]]] = {o: [[] for _ in range(k)] for o in OUTPUTS}
    evaluations = 0
    jobs_list = [(i, trajectories, seed, ticks, levels) for i in range(trajectories)]
    if jobs > 1:
        with Pool(processes=jobs) as pool:
            walked = pool.map(_morris_trajectory, jobs_list, chunksize=1)
    else:
        walked = [_morris_trajectory(job) for job in jobs_list]
    for per_trajectory, runs in walked:
        evaluations += runs
        for output in OUTPUTS:
            for i in range(k):
                effects[output][i].extend(per_trajectory[output][i])
    results = {}
    for output in OUTPUTS:
        rows = [
            {
                "param": name,
                "mu_star": float(np.mean(np.abs(effects[output][i]))),
                "sigma": float(np.std(effects[output][i])),
            }
            for i, name in enumerate(NAMES)
        ]
        rows.sort(key=lambda row: -row["mu_star"])
        results[output] = rows
    return {
        "method": "morris",
        "trajectories": trajectories,
        "levels": levels,
        "evaluations": evaluations,
        "seed": seed,
        "ticks": ticks,
        "results": results,
    }


def sobol(params: list[str], n: int, seed: int, ticks: int, jobs: int = 1) -> dict:
    """Saltelli first-order and total-order indices over `params`, n·(k+2) runs.

    Parameters outside `params` sit at their midpoint, so the indices are shares of the
    variance THIS subset generates — not of the model's whole variance. Sampling is plain
    uniform (a Sobol' sequence would need scipy, which this project does not carry); the
    estimators are unbiased either way, they just converge more slowly.
    """
    k = len(params)
    indices = [NAMES.index(p) for p in params]
    rng = np.random.default_rng(9082026)
    a_sub, b_sub = rng.random((n, k)), rng.random((n, k))
    midpoint = np.full(len(NAMES), 0.5)

    def expand(row: np.ndarray) -> dict[str, float]:
        point = midpoint.copy()
        for position, index in enumerate(indices):
            point[index] = row[position]
        return scale(point)

    def run_all(matrix: np.ndarray) -> list[dict[str, float]]:
        return _eval_many([expand(row) for row in matrix], seed, ticks, jobs)

    f_a, f_b = run_all(a_sub), run_all(b_sub)
    f_ab = []
    for position in range(k):
        swapped = a_sub.copy()
        swapped[:, position] = b_sub[:, position]
        f_ab.append(run_all(swapped))

    results = {}
    for output in OUTPUTS:
        a = np.array([row[output] for row in f_a])
        b = np.array([row[output] for row in f_b])
        both = np.concatenate([a, b])
        variance = float(np.var(both))
        # CENTRE the outputs first. The Saltelli first-order estimator is unbiased either way,
        # but its variance blows up when a moment's mean dwarfs its spread — ownership has
        # mean 0.70 and sd 0.004 — because f_B multiplies a small difference and never
        # cancels. Uncentred, this returned S1 values of +22 and +33 where a first-order index
        # must lie in [0, 1]. Centring is the standard remedy and costs nothing.
        centre = float(np.mean(both))
        a_c, b_c = a - centre, b - centre
        rows = []
        for position, name in enumerate(params):
            ab_c = np.array([row[output] for row in f_ab[position]]) - centre
            rows.append(
                {
                    "param": name,
                    # Saltelli et al. 2010 for first order, Jansen 1999 for total order
                    "S1": (
                        float(np.mean(b_c * (ab_c - a_c)) / variance) if variance else float("nan")
                    ),
                    "ST": (
                        float(np.mean((a_c - ab_c) ** 2) / (2 * variance))
                        if variance
                        else float("nan")
                    ),
                }
            )
        rows.sort(key=lambda row: -row["ST"])
        # Coefficient of variation across the design. A variance decomposition of a moment
        # that barely moves is meaningless — the estimators divide by that variance, so the
        # indices wander outside [0, 1]. `_report` refuses to interpret rows below CV_FLOOR,
        # and a moment landing there is itself the finding: it is robust to these parameters.
        results[output] = {
            "variance": variance,
            "mean": centre,
            "cv": float(np.sqrt(variance) / abs(centre)) if centre else float("inf"),
            "interpretable": bool(
                variance > 0 and abs(centre) and np.sqrt(variance) / abs(centre) >= CV_FLOOR
            ),
            "indices": rows,
        }
    return {
        "method": "sobol",
        "n": n,
        "params": params,
        "evaluations": n * (k + 2),
        "seed": seed,
        "ticks": ticks,
        "results": results,
        # raw evaluations, so the indices can be re-estimated without re-running the model —
        # which is what the uncentred-estimator mistake above would otherwise have cost
        "raw": {
            "outputs": OUTPUTS,
            "A": [[row[o] for o in OUTPUTS] for row in f_a],
            "B": [[row[o] for o in OUTPUTS] for row in f_b],
            "AB": [[[row[o] for o in OUTPUTS] for row in block] for block in f_ab],
        },
    }


def _report_lhs(payload: dict, top: int = 10) -> None:
    default = payload["default"]
    print(f"\ndefaults: loss {default['loss']:.4f}")
    for name, value in sorted(default.get("per_moment", {}).items(), key=lambda kv: -kv[1]):
        if value > 0:
            print(f"   outside band: {name:18s} {default['moments'][name]:.4f}  loss {value:.4f}")
    print(f"\nbest {top} of {payload['n']} sampled points")
    for row in payload["rows"][:top]:
        moved = {k: v for k, v in row["point"].items() if abs(v - getattr_default(k)) > 1e-9}
        head = ", ".join(f"{k}={v:.3g}" for k, v in list(moved.items())[:6])
        print(f"   loss {row['loss']:.4f}  pti {row['moments']['pti']:.2f}  {head} ...")
    # crude marginal: mean loss in the lower and upper half of each parameter's range
    print("\nwhere the sweep wants each parameter (mean loss, low half vs high half)")
    for name in NAMES:
        lo, hi = SPACE[name]
        mid = 0.5 * (lo + hi)
        low = [r["loss"] for r in payload["rows"] if r["point"][name] < mid]
        high = [r["loss"] for r in payload["rows"] if r["point"][name] >= mid]
        if not low or not high:
            continue
        print(
            f"   {name:28s} low {np.mean(low):8.3f}   high {np.mean(high):8.3f}"
            f"   {'LOW' if np.mean(low) < np.mean(high) else 'HIGH'}"
        )


def _report(payload: dict, top: int = 8) -> None:
    if payload["method"] == "lhs":
        _report_lhs(payload)
        return
    for output, block in payload["results"].items():
        rows = block["indices"] if payload["method"] == "sobol" else block
        if payload["method"] == "sobol" and not block["interpretable"]:
            print(f"\n== {output}  (CV {block['cv']:.4f} < {CV_FLOOR}: flat, not decomposed)")
            continue
        suffix = f"  (CV {block['cv']:.3f})" if payload["method"] == "sobol" else ""
        print(f"\n== {output}{suffix}")
        for row in rows[:top]:
            if payload["method"] == "sobol":
                print(f"   {row['param']:28s} S1={row['S1']:+.3f}  ST={row['ST']:+.3f}")
            else:
                print(
                    f"   {row['param']:28s} mu*={row['mu_star']:12.5f}  sigma={row['sigma']:12.5f}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("method", choices=("lhs", "morris", "sobol"))
    parser.add_argument("--trajectories", type=int, default=10, help="morris only")
    parser.add_argument("--n", type=int, default=128, help="sobol only")
    parser.add_argument(
        "--params", default=",".join(NAMES), help="sobol only: comma-separated subset"
    )
    parser.add_argument("--seed", type=int, default=1, help="fixed across the design")
    parser.add_argument("--seeds", default="1,2,3", help="lhs only: comma-separated")
    parser.add_argument("--ticks", type=int, default=40)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    parser.add_argument(
        "--jobs", type=int, default=1, help="processes; results do not depend on it"
    )
    args = parser.parse_args()

    if args.method == "lhs":
        payload = lhs(args.n, tuple(int(s) for s in args.seeds.split(",")), args.ticks)
    elif args.method == "morris":
        payload = morris(args.trajectories, args.seed, args.ticks, jobs=args.jobs)
    else:
        payload = sobol(args.params.split(","), args.n, args.seed, args.ticks, jobs=args.jobs)

    args.out.mkdir(exist_ok=True)
    path = args.out / f"sensitivity_{args.method}_{payload['evaluations']}.json"
    path.write_text(json.dumps(payload, indent=1))
    _report(payload)
    print(f"\n{payload['evaluations']} evaluations -> {path}")


if __name__ == "__main__":
    main()
