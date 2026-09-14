"""The sealed 2008–2013 hold-out: inputs, and the one command that runs it.

`docs/holdout-2008-2013.md` is the rule; this is the instrument. Everything here is an
INPUT taken from a registered series in `docs/sources.md` — no parameter of the model is set
from the episode, and none may be changed after it has been run (model-spec §13.4). That is
the whole value of the exercise: the model has been calibrated on 2014–2025 moments only, so
2008–13 is the only period it has never seen.

The episode runs 24 ticks, 2008Q1 to 2013Q4. Tick 0 is initialised at **2007Q4** conditions —
euríbor 4.68%, household joblessness 3.61%, formation 474k/yr, and a construction pipeline
still delivering at boom rates — because those initial conditions are half of what the
episode is. A bust simulated from a calm steady state with an empty pipeline would be a
different and much easier question.

Run it with:

    uv run python -m resim.holdout --seeds 10

and read the result in `docs/validation.md`. It is run **once**.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import numpy as np

from . import metrics
from .config import SimConfig
from .engine import Engine
from .scenario import CreditCrunch, HouseholdFormation, LabourShock, RateShock, Scenario

SCALE = 2_000  # households per model household (metrics.SCALE)

# --- inputs, one registered series each ------------------------------------------------

# Euríbor 12m, quarterly averages of the monthly series [BdE Boletín Estadístico 19.1,
# D_1NBAF472]. 2008Q1 … 2013Q4. The spike comes first and the collapse second: a hold-out
# that flattened this to an average would lose the sequencing the model is tested on.
EURIBOR = (
    0.04479,
    0.05058,
    0.05367,
    0.04350,  # 2008
    0.02222,
    0.01675,
    0.01336,
    0.01239,  # 2009
    0.01224,
    0.01252,
    0.01405,
    0.01520,  # 2010
    0.01729,
    0.02126,
    0.02116,
    0.02053,  # 2011
    0.01671,
    0.01284,
    0.00893,
    0.00596,  # 2012
    0.00571,
    0.00506,
    0.00537,
    0.00530,  # 2013
)
EURIBOR_2007Q4 = 0.04682

# Households whose active members are ALL unemployed, quarterly [INE EPA tabla 65276].
# The model's household is a single income unit, so this is the right series and the
# individual unemployment rate is not (model-spec §6c.1).
JOBLESS = (
    0.0415,
    0.0439,
    0.0500,
    0.0643,  # 2008
    0.0830,
    0.0860,
    0.0872,
    0.0942,  # 2009
    0.1003,
    0.1017,
    0.1002,
    0.1023,  # 2010
    0.1070,
    0.1054,
    0.1101,
    0.1212,  # 2011
    0.1340,
    0.1346,
    0.1351,
    0.1433,  # 2012
    0.1502,
    0.1434,
    0.1420,
    0.1442,  # 2013
)
JOBLESS_2007Q4 = 0.0361

# Net new households per year [INE EPA tabla 65269, Q4 to Q4], converted to model units per
# tick. Formation did not stop in the bust — it fell by four fifths.
FORMATION_PER_YEAR = {
    2008: 387_000,
    2009: 279_200,
    2010: 255_700,
    2011: 249_300,
    2012: 158_300,
    2013: 91_000,
}
FORMATION_2007 = 474_200

# Viviendas libres terminadas [MIVAU Boletín Online tabla 3.2], converted to model units per
# tick. These are the 2005–08 starts arriving: the model does not decide them, it inherits
# them, which is what `DeveloperConfig.initial_pipeline` is for.
COMPLETIONS_PER_YEAR = {
    2008: 563_631,
    2009: 356_555,
    2010: 218_572,
    2011: 121_043,
    2012: 80_083,
    2013: 43_230,
}

# The credit stop. The BdE lending survey documents the direction quarter by quarter —
# standards on house-purchase loans tightened from 2022Q2 for three consecutive quarters in
# the 2022 episode and, in this one, from 2008 through 2009 — and reports magnitudes as net
# percentages in charts rather than as numbers. So the SIZE here is taken from what the BdE
# reports about realised lending instead: LTVs fell from the boom's bunching at 0.80 toward
# 0.60–0.65, effort ratios were cut, and spreads widened by more than a point.
# Applied at 2008Q3 (tick 2), the quarter of the Lehman failure.
CRUNCH_TICK = 2
CRUNCH = CreditCrunch(start_tick=CRUNCH_TICK, ltv_delta=-0.15, dsti_delta=-0.05, spread_delta=0.015)

# What the model is being asked to reproduce, stated before the run (docs/prereg/).
PREDICTIONS = {
    "price_fall": (-0.45, -0.30),  # peak-to-trough, model-spec §9.6 [BdE/Tinsa/IPV]
    "transaction_fall": (-0.85, -0.40),  # lending/volume collapse, §9.6 [bank §4]
    "arrears_peak": (0.04, 0.09),  # BdE doubtful ratio peaked at 6.28% in 2014Q1
    "foreclosure_peak_per_year": (0.007, 0.020),  # CGPJ 93,636 filings ≈ 1.4% of mortgages
    "reo_builds": True,  # the bank-owned overhang exists at all
    "ownership_falls": True,
}


def _per_tick(per_year: int) -> int:
    return int(round(per_year / SCALE / 4))


def initial_pipeline() -> tuple[int, ...]:
    """Completions already under construction, by arrival tick (2008Q1 onward)."""
    schedule: list[int] = []
    for year in sorted(COMPLETIONS_PER_YEAR):
        schedule.extend([_per_tick(COMPLETIONS_PER_YEAR[year])] * 4)
    return tuple(schedule)


def baseline_config(seed: int, ticks: int = 24) -> SimConfig:
    """Tick 0 = 2007Q4: the world the episode starts from, not a calm steady state."""
    cfg = SimConfig.baseline(seed=seed, ticks=ticks)
    return dataclasses.replace(
        cfg,
        credit=dataclasses.replace(cfg.credit, euribor=EURIBOR_2007Q4),
        labour=dataclasses.replace(cfg.labour, jobless_rate=JOBLESS_2007Q4),
        population=dataclasses.replace(
            cfg.population, formation_per_tick=_per_tick(FORMATION_2007)
        ),
        developer=dataclasses.replace(cfg.developer, initial_pipeline=initial_pipeline()),
        # the legal regime of the period: three unpaid instalments trigger early termination
        # [LEC art. 693 as amended by Ley 1/2013], against twelve under the law in force
        # today. Running the episode under current law would understate the wave by roughly
        # three quarters of arrears per borrower.
        insolvency=dataclasses.replace(cfg.insolvency, foreclosure_regime="ley1_2013"),
    )


def scenario(seed: int, ticks: int = 24) -> Scenario:
    """The episode as a path of interventions, one step per observed quarter."""
    interventions: list = [CRUNCH]
    for tick, rate in enumerate(EURIBOR[:ticks]):
        interventions.append(RateShock(start_tick=tick, euribor=rate))
        interventions.append(LabourShock(start_tick=tick, rate=JOBLESS[tick]))
        year = 2008 + tick // 4
        if tick % 4 == 0 and year in FORMATION_PER_YEAR:
            interventions.append(
                HouseholdFormation(
                    start_tick=tick, formation_per_tick=_per_tick(FORMATION_PER_YEAR[year])
                )
            )
    # the crunch is applied last so a later RateShock cannot undo its spread
    interventions = [iv for iv in interventions if iv is not CRUNCH] + [CRUNCH]
    return Scenario(
        name="holdout-2008-2013",
        baseline=baseline_config(seed, ticks),
        interventions=tuple(sorted(interventions, key=lambda iv: iv.start_tick)),
    )


def run(seeds: int = 10, ticks: int = 24) -> dict:
    """Run the episode on `seeds` seeds and return the measured outcome. Once."""
    rows = []
    for seed in range(1, seeds + 1):
        frame = metrics.to_frame(Engine(scenario(seed, ticks)).run())
        price = frame["price_national"]
        transactions = frame["transactions"]
        rows.append(
            {
                "seed": seed,
                "price_fall": float(price.min() / price.iloc[0] - 1.0),
                "price_end": float(price.iloc[-1] / price.iloc[0] - 1.0),
                "transaction_fall": float(
                    transactions.iloc[-8:].mean() / max(transactions.iloc[:4].mean(), 1e-9) - 1.0
                ),
                "arrears_peak": float(frame["arrears_share"].max()),
                "foreclosure_peak": float(frame["foreclosure_rate"].max()),
                "foreclosures_total": float(frame["foreclosures"].sum()),
                "reo_peak": float(frame["reo_stock"].max()),
                "ownership_change": float(
                    frame["ownership_rate"].iloc[-1] - frame["ownership_rate"].iloc[0]
                ),
                "vacancy_change": float(
                    frame["vacancy_rate"].iloc[-1] - frame["vacancy_rate"].iloc[0]
                ),
                "locked_in_peak": float(frame["locked_in_share"].max()),
                "unemployment_end": float(frame["unemployment_rate"].iloc[-1]),
            }
        )
    summary = {
        key: {
            "mean": float(np.mean([r[key] for r in rows])),
            "sd": float(np.std([r[key] for r in rows])),
            "min": float(np.min([r[key] for r in rows])),
            "max": float(np.max([r[key] for r in rows])),
        }
        for key in rows[0]
        if key != "seed"
    }
    verdict = {
        "price_fall": PREDICTIONS["price_fall"][0]
        <= summary["price_fall"]["mean"]
        <= PREDICTIONS["price_fall"][1],
        "transaction_fall": PREDICTIONS["transaction_fall"][0]
        <= summary["transaction_fall"]["mean"]
        <= PREDICTIONS["transaction_fall"][1],
        "arrears_peak": PREDICTIONS["arrears_peak"][0]
        <= summary["arrears_peak"]["mean"]
        <= PREDICTIONS["arrears_peak"][1],
        "foreclosure_peak": PREDICTIONS["foreclosure_peak_per_year"][0]
        <= summary["foreclosure_peak"]["mean"]
        <= PREDICTIONS["foreclosure_peak_per_year"][1],
        "reo_builds": summary["reo_peak"]["mean"] > 0.0,
        "ownership_falls": summary["ownership_change"]["mean"] < 0.0,
    }
    return {"seeds": seeds, "ticks": ticks, "rows": rows, "summary": summary, "verdict": verdict}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--ticks", type=int, default=24)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    payload = run(args.seeds, args.ticks)
    args.out.mkdir(exist_ok=True)
    path = args.out / f"holdout_2008_2013_{args.seeds}seeds.json"
    path.write_text(json.dumps(payload, indent=1))

    print(f"2008–2013 hold-out, {args.seeds} seeds, {args.ticks} ticks\n")
    for key, block in payload["summary"].items():
        print(
            f"  {key:24s} {block['mean']:+9.4f}  sd {block['sd']:.4f}  "
            f"[{block['min']:+.4f}, {block['max']:+.4f}]"
        )
    print("\n  verdict (against the pre-registered predictions):")
    for key, passed in payload["verdict"].items():
        print(f"    {key:24s} {'PASS' if passed else 'FAIL'}")
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
