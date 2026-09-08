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

Baseline only: parameters that act through an intervention (the rent cap's `hazard_scale`, for
one) correctly show zero here, and their sensitivity is the elasticity sweep in
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
from pathlib import Path

import numpy as np

from . import metrics
from .agents import household as household_mod
from .agents import landlord as landlord_mod
from .config import SimConfig, ZoneType
from .engine import Engine
from .scenario import Scenario

# parameter -> (low, high). Documented ranges where one exists, else ±30% around a calibrated
# guess. Keep this table and docs/model-spec.md §7 consistent.
SPACE: dict[str, tuple[float, float]] = {
    "expectation_momentum": (0.5, 0.9),
    "overbid_sigma": (0.02, 0.06),
    "ask_decay": (0.02, 0.05),
    "buy_attempt_prob": (0.35, 0.65),
    "seeker_wealth_median": (10_000.0, 20_000.0),
    "landlord_required_spread": (0.015, 0.025),
    "landlord_zone_risk_premium": (0.010, 0.020),
    "hazard_scale": (0.4, 1.2),
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
}
NAMES: list[str] = list(SPACE)

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
        ask_decay=x["ask_decay"],
        landlord_required_spread=x["landlord_required_spread"],
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
    return dataclasses.replace(
        cfg, market=market, population=population, developer=developer, zones=zones
    )


def evaluate(x: dict[str, float], seed: int = 1, ticks: int = 40) -> dict[str, float]:
    """Run the model once at `x` and return the moments the analysis is judged on."""
    cfg = _config_for(x, seed, ticks)
    # three behavioural constants live at module level; set and restore them around the run
    saved = (
        landlord_mod.HAZARD_SCALE,
        landlord_mod.CONGESTION_GAIN,
        household_mod.SEARCH_BURDEN_ESCALATION,
    )
    landlord_mod.HAZARD_SCALE = x["hazard_scale"]
    landlord_mod.CONGESTION_GAIN = x["congestion_gain"]
    household_mod.SEARCH_BURDEN_ESCALATION = x["search_burden_escalation"]
    try:
        state = Engine(Scenario(name="sensitivity", baseline=cfg)).run()
    finally:
        (
            landlord_mod.HAZARD_SCALE,
            landlord_mod.CONGESTION_GAIN,
            household_mod.SEARCH_BURDEN_ESCALATION,
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
    }


def morris(trajectories: int, seed: int, ticks: int, levels: int = 4) -> dict:
    """Elementary-effects screening: `trajectories` × (k+1) runs.

    One parameter moves per step along a random path through the grid, so each parameter gets
    `trajectories` elementary effects. Reports mu_star (mean |effect|, how much it matters) and
    sigma (spread, i.e. interaction or non-linearity).
    """
    delta = levels / (2.0 * (levels - 1))  # 2/3 at 4 levels
    k = len(NAMES)
    rng = np.random.default_rng(20260908)
    effects: dict[str, list[list[float]]] = {o: [[] for _ in range(k)] for o in OUTPUTS}
    evaluations = 0
    for _ in range(trajectories):
        point = rng.choice([0.0, 1.0 - delta], size=k)
        previous = evaluate(scale(point), seed, ticks)
        evaluations += 1
        for i in rng.permutation(k):
            step = delta if point[i] <= 1.0 - delta + 1e-9 else -delta
            moved = point.copy()
            moved[i] = float(np.clip(point[i] + step, 0.0, 1.0))
            taken = moved[i] - point[i]
            current = evaluate(scale(moved), seed, ticks)
            evaluations += 1
            for output in OUTPUTS:
                effects[output][i].append((current[output] - previous[output]) / taken)
            point, previous = moved, current
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


def sobol(params: list[str], n: int, seed: int, ticks: int) -> dict:
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
        return [evaluate(expand(row), seed, ticks) for row in matrix]

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
        variance = float(np.var(np.concatenate([a, b])))
        rows = []
        for position, name in enumerate(params):
            ab = np.array([row[output] for row in f_ab[position]])
            rows.append(
                {
                    "param": name,
                    # Saltelli 2010 for first order, Jansen for total order
                    "S1": float(np.mean(b * (ab - a)) / variance) if variance else float("nan"),
                    "ST": (
                        float(np.mean((a - ab) ** 2) / (2 * variance)) if variance else float("nan")
                    ),
                }
            )
        rows.sort(key=lambda row: -row["ST"])
        results[output] = {"variance": variance, "indices": rows}
    return {
        "method": "sobol",
        "n": n,
        "params": params,
        "evaluations": n * (k + 2),
        "seed": seed,
        "ticks": ticks,
        "results": results,
    }


def _report(payload: dict, top: int = 8) -> None:
    for output, block in payload["results"].items():
        rows = block["indices"] if payload["method"] == "sobol" else block
        print(f"\n== {output}")
        for row in rows[:top]:
            if payload["method"] == "sobol":
                print(f"   {row['param']:28s} S1={row['S1']:+.3f}  ST={row['ST']:+.3f}")
            else:
                print(
                    f"   {row['param']:28s} mu*={row['mu_star']:12.5f}  sigma={row['sigma']:12.5f}"
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("method", choices=("morris", "sobol"))
    parser.add_argument("--trajectories", type=int, default=10, help="morris only")
    parser.add_argument("--n", type=int, default=128, help="sobol only")
    parser.add_argument(
        "--params", default=",".join(NAMES), help="sobol only: comma-separated subset"
    )
    parser.add_argument("--seed", type=int, default=1, help="fixed across the design")
    parser.add_argument("--ticks", type=int, default=40)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    if args.method == "morris":
        payload = morris(args.trajectories, args.seed, args.ticks)
    else:
        payload = sobol(args.params.split(","), args.n, args.seed, args.ticks)

    args.out.mkdir(exist_ok=True)
    path = args.out / f"sensitivity_{args.method}_{payload['evaluations']}.json"
    path.write_text(json.dumps(payload, indent=1))
    _report(payload)
    print(f"\n{payload['evaluations']} evaluations -> {path}")


if __name__ == "__main__":
    main()
