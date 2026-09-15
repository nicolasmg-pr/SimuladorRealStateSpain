"""The lever sweep behind the claims ledger — one command, ten seeds, one artefact.

`docs/claims.md` adjudicates public claims against the model's response to each lever. Those
responses were produced by hand in phase F and cached to `runs/levers_10seeds.json`, which is
gitignored, so the ledger's numbers could not be re-derived after the model changed. They now
can: this module is the instrument, and re-running it is how the ledger is kept honest.

Design, all of it inherited from the ledger's own rules (`docs/claims.md`, "The rules this
ledger obeys"):

- **Ten seeds** (model-spec §13.4), each lever against **the same seed's baseline**, so a
  difference is the lever and not the draw.
- The lever lands at tick 8 and the window is **tick 24 onwards**, which leaves four ticks of
  run-in before the measurement starts.
- Every response carries `mean`, `sd` and **`positive`, the count of seeds that moved up**.
  Five or six out of ten is noise and the ledger must report it as no effect.

    uv run python -m resim.levers --jobs 10
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from . import metrics
from .cli import build_scenario
from .engine import Engine

# What the ledger reads. Keep in step with the columns `docs/claims.md` cites.
COLUMNS = (
    "price_national",
    "price_tensioned",
    "rent_tensioned",
    "rent_transacted_tensioned",
    "transactions",
    "new_leases",
    "rent_overburden_share",
    "ownership_rate",
    "vacancy_rate",
    "starts",
    "completions",
    "price_to_income",
)

# name -> (lever, kwargs). The suffixed entries are the same lever at a different setting,
# which is how the ledger separates "the model's response" from "the response at the top of
# the dial the evidence admits".
RUNS: dict[str, tuple[str, dict]] = {
    # The ledger reports the CATALAN regime (Ley 11/2020, the index binding every landlord),
    # because that is the world the three evaluation studies measure and the one the model's
    # `hazard_scale` was identified in. The state regime (Ley 12/2023, the index binding
    # grandes tenedores only) is run alongside it and is NOT reportable: with the cap barely
    # binding on individuals the withdrawal channel runs on a hazard calibrated for the other
    # regime, and it produces a rent RISE that no evidence covers (docs/validation.md).
    "rent-cap": ("rent-cap", {"index_binds_all": True}),
    "rent-cap-e2": ("rent-cap", {"supply_response_elasticity": 2.0, "index_binds_all": True}),
    "rent-cap-state-law": ("rent-cap", {}),
    "transaction-tax": ("transaction-tax", {}),
    # the 100% non-EU surcharge of claim F-1, as the lever expresses it
    "transaction-tax-foreign": ("transaction-tax", {"itp_delta": 0.0, "foreign_delta": 1.0}),
    "vacancy-tax": ("vacancy-tax", {}),
    "public-housing": ("public-housing", {}),
    "tourist-restriction": ("tourist-restriction", {}),
    "demand-subsidy": ("demand-subsidy", {}),
    "land-release": ("land-release", {}),
    "credit-crunch": ("credit-crunch", {}),
}

START_TICK = 8
POST = 24
TICKS = 60


def _moments(name: str, seed: int, ticks: int, kwargs: dict) -> dict[str, float]:
    scenario = build_scenario(name, seed, ticks, **kwargs)
    if kwargs or name != "baseline":
        scenario = replace(
            scenario,
            interventions=tuple(
                replace(iv, start_tick=START_TICK) if hasattr(iv, "start_tick") else iv
                for iv in scenario.interventions
            ),
        )
    frame = metrics.to_frame(Engine(scenario).run())
    post = frame.iloc[POST:]
    return {c: float(post[c].mean()) for c in COLUMNS if c in frame.columns}


def _job(args: tuple[str, str, dict, int, int]) -> tuple[str, int, dict[str, float]]:
    label, lever, kwargs, seed, ticks = args
    return label, seed, _moments(lever, seed, ticks, kwargs)


def run(seeds: int = 10, ticks: int = TICKS, jobs: int = 1) -> dict:
    seed_list = list(range(1, seeds + 1))
    work: list[tuple[str, str, dict, int, int]] = [
        ("baseline", "baseline", {}, seed, ticks) for seed in seed_list
    ]
    for label, (lever, kwargs) in RUNS.items():
        work += [(label, lever, kwargs, seed, ticks) for seed in seed_list]

    if jobs > 1:
        with Pool(processes=jobs) as pool:
            done = pool.map(_job, work, chunksize=1)
    else:
        done = [_job(w) for w in work]

    by_label: dict[str, dict[int, dict[str, float]]] = {}
    for label, seed, moments in done:
        by_label.setdefault(label, {})[seed] = moments

    baseline = by_label["baseline"]
    out: dict = {
        "seeds": seeds,
        "ticks": ticks,
        "start_tick": START_TICK,
        "post": f"ticks {POST}+",
        "baseline": {str(s): baseline[s] for s in seed_list},
        "levers": {},
    }
    for label in RUNS:
        rows = by_label[label]
        out["levers"][label] = {}
        for column in COLUMNS:
            deltas = []
            for seed in seed_list:
                base = baseline[seed].get(column)
                value = rows[seed].get(column)
                if base in (None, 0.0) or value is None:
                    continue
                deltas.append(value / base - 1.0)
            if not deltas:
                continue
            arr = np.asarray(deltas)
            out["levers"][label][column] = {
                "mean": float(arr.mean()),
                "sd": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
                # how many seeds moved UP. 5 or 6 of 10 is noise, and the ledger says so
                "positive": int((arr > 0).sum()),
            }
    return out


def _report(payload: dict) -> None:
    seeds = payload["seeds"]
    for label, columns in payload["levers"].items():
        print(f"\n== {label}")
        for column, stats in columns.items():
            unanimous = stats["positive"] in (0, seeds)
            flag = "" if unanimous else f"  ({stats['positive']}/{seeds} up)"
            print(f"   {column:28} {stats['mean']:+7.2%}  sd {stats['sd']:.3f}{flag}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--ticks", type=int, default=TICKS)
    parser.add_argument(
        "--jobs", type=int, default=1, help="processes; results do not depend on it"
    )
    parser.add_argument("--out", type=Path, default=Path("runs/levers_10seeds.json"))
    args = parser.parse_args()

    payload = run(args.seeds, args.ticks, args.jobs)
    args.out.parent.mkdir(exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    _report(payload)
    print(f"\n{len(RUNS)} levers × {args.seeds} seeds -> {args.out}")


if __name__ == "__main__":
    main()
