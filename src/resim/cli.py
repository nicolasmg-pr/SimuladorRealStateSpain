"""Command-line entry point — run a scenario headless, write the series to disk.

Useful for sweeps and for regression-checking the model without the UI in the way.
Results land in runs/<scenario>_<seed>_<confighash>.csv (runs/ is gitignored).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from . import metrics
from .config import SimConfig
from .engine import Engine
from .scenario import (
    DemandSubsidy,
    HouseholdFormation,
    LandRelease,
    PublicHousing,
    RateShock,
    RentCap,
    Scenario,
    TouristRestriction,
    TransactionTax,
    VacancyTax,
    ine_household_projection,
)

LEVERS = {
    "baseline": None,
    "rent-cap": RentCap,
    "transaction-tax": TransactionTax,
    "vacancy-tax": VacancyTax,
    "public-housing": PublicHousing,
    "tourist-restriction": TouristRestriction,
    "demand-subsidy": DemandSubsidy,
    "land-release": LandRelease,
    "rate-shock": RateShock,
    "household-formation": HouseholdFormation,
}

# Multi-step paths, which are not a single Intervention. Kept apart from LEVERS so the
# "one lever = one Intervention class" reading of that table stays true.
PATHS = {"ine-demography": ine_household_projection}


def config_hash(config: SimConfig) -> str:
    payload = json.dumps(asdict(config), sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:10]


def build_scenario(name: str, seed: int, ticks: int, **lever_kwargs) -> Scenario:
    base = SimConfig.baseline(seed=seed, ticks=ticks)
    if name == "baseline":
        return Scenario(name="baseline", baseline=base)
    if name in PATHS:
        return Scenario(name=name, baseline=base, interventions=PATHS[name](**lever_kwargs))
    lever_cls = LEVERS[name]
    return Scenario(name=name, baseline=base, interventions=(lever_cls(**lever_kwargs),))


def main() -> None:
    """Parse args, build a Scenario, run it, write results to runs/."""
    parser = argparse.ArgumentParser(description="Run resim headless.")
    parser.add_argument(
        "scenario", choices=sorted(LEVERS) + sorted(PATHS), default="baseline", nargs="?"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=60)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    scenario = build_scenario(args.scenario, args.seed, args.ticks)
    state = Engine(scenario).run()
    frame = metrics.to_frame(state)

    args.out.mkdir(exist_ok=True)
    path = args.out / (f"{scenario.name}_{args.seed}_{config_hash(scenario.baseline)}.csv")
    frame.to_csv(path)
    last = frame.iloc[-1]
    print(f"wrote {path}")
    print(
        f"final: price_tensioned={last['price_tensioned']:.0f} "
        f"ownership={last['ownership_rate']:.2%} "
        f"overburden={last['rent_overburden_share']:.2%}"
    )


if __name__ == "__main__":
    main()
