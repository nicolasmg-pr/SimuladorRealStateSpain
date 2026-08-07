"""Developers — the supply side, and the main source of lag in the model.

Start construction when expected margin clears a hurdle; units arrive N ticks later.
That delay is what generates cycles, so the lag is explicit and configurable.

Rules (developer §3):
  - Start rule: expected sale price ≥ all-in cost × (1 + margin threshold), where
    all-in cost = hard cost + land (land priced as a share of the final price).
  - Demand gate (pre-sales): starts are throttled by recent transacted demand,
    the ABM stand-in for the 30–50% pre-sales requirement.
  - Volume responds to the margin signal; sensitivity is calibrated so the long-run
    stock elasticity lands in the 0.45–0.58 range.
  - Zone capacity: national max split by zone household shares.
"""

from __future__ import annotations

import numpy as np

from ..config import ZoneType
from ..state import WorldState
from .base import Intent, StartConstruction

STARTS_SENSITIVITY = 3.0  # d(starts)/d(margin excess) — calibration knob [guess]
AVG_UNIT_M2 = 80.0


class Developer:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        cfg = state.config
        dev = cfg.developer
        intents: list[Intent] = []
        recent_sales = state.tick_events.get("sales_by_zone", {})

        for zone in ZoneType:
            zcfg = cfg.zone(zone)
            zs = state.zones[zone]
            lag = max(1, dev.construction_lag + cfg.policy.permit_lag_delta)
            expected_price = (
                zs.price_index * dev.new_build_premium * (1.0 + zs.expected_price_growth) ** lag
            )
            hard_cost = zcfg.cost_per_m2 * AVG_UNIT_M2
            land_cost = zcfg.land_share * expected_price
            all_in = hard_cost + land_cost
            margin = expected_price / all_in - 1.0
            if margin < dev.margin_threshold:
                continue

            base = dev.base_starts_per_tick * zcfg.household_share
            factor = 1.0 + STARTS_SENSITIVITY * (margin - dev.margin_threshold)
            n = base * factor

            # pre-sales demand gate: don't start more than recent demand supports
            zone_sales = recent_sales.get(zone, 0)
            demand_ceiling = max(1.0, zone_sales / max(dev.presale_share, 1e-9) * 0.5)
            n = min(n, demand_ceiling, dev.max_starts_per_tick * zcfg.household_share)

            # land-release lever: extra capacity once the lag has elapsed
            n += state.tick_events.get("released_land", {}).get(zone, 0)

            n_units = int(self.rng.poisson(max(0.0, n)))
            if n_units > 0:
                intents.append(StartConstruction(agent_id=self.id, zone=zone, n_units=n_units))
        return intents
