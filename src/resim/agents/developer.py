"""Developers — the supply side, and the main source of lag in the model.

Start construction when expected margin clears a hurdle; units arrive N ticks later.
That delay is what generates cycles, so the lag is explicit and configurable.

Rules (developer §3):
  - Start rule: expected sale price ≥ hard cost × (1 + margin threshold). **Land is the
    residual claimant** — developers compete for sites, so surplus above hard cost plus the
    required margin capitalises into the land price and realised margins sit near the
    hurdle [CNMC land-share evidence, developer §6]. Consequence: the *margin* carries
    almost no information and must not be the volume signal. Pricing land as a fixed share
    of the final price instead implies a margin that rises without limit as prices rise
    (it reached 103% in the rural zone, versus the 15–20% observed range) and pins starts
    against the capacity ceiling.
  - Volume signal: expected price over hard cost, relative to that ratio's level in the
    calibration period, raised to the sourced long-run supply elasticity. This makes
    d ln(starts)/d ln(price) = `supply_elasticity` by construction — no free coefficient.
  - Demand gate (pre-sales): starts are throttled by recent transacted demand,
    the ABM stand-in for the 30–50% pre-sales requirement.
  - Zone capacity: national max split by zone household shares.
  - Unsold completed inventory is RE-PRICED every tick, with a markdown that grows the
    longer it sits. Developers carry debt against stock; they cut to clear rather than let
    a unit fall out of the market [developer §4 — mechanism sourced, markdown pace a guess].
"""

from __future__ import annotations

import numpy as np

from ..config import ZoneType
from ..market.stock import DEVELOPER_ID, Tenure
from ..state import WorldState
from .base import Intent, ListForSale, StartConstruction

# inventory markdown per tick held, and its ceiling [guess]
INVENTORY_MARKDOWN_PER_TICK = 0.02
MAX_INVENTORY_MARKDOWN = 0.25


class Developer:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        cfg = state.config
        dev = cfg.developer
        intents: list[Intent] = []
        recent_sales = state.tick_events.get("sales_by_zone", {})
        intents.extend(self._reprice_inventory(state))

        for zone in ZoneType:
            zcfg = cfg.zone(zone)
            zs = state.zones[zone]
            lag = max(1, dev.construction_lag + cfg.policy.permit_lag_delta)
            expected_price = (
                zs.price_index * dev.new_build_premium * (1.0 + zs.expected_price_growth) ** lag
            )
            hard_cost = zcfg.cost_per_m2 * cfg.stock.avg_size_m2

            # go/no-go: with land as the residual claimant the site is only worth acquiring
            # once the price covers hard cost plus the required margin on it
            if expected_price < hard_cost * (1.0 + dev.margin_threshold):
                continue

            # volume signal. The reference ratio is the price-to-hard-cost level implied by
            # the calibration-period config (median_value × zone multiplier × new-build
            # premium over hard cost) — the level at which observed starts equal
            # base_starts_per_tick. It is derived, not a new free parameter.
            reference_price = cfg.stock.median_value * zcfg.price_multiplier * dev.new_build_premium
            factor = (expected_price / max(reference_price, 1e-9)) ** zcfg.supply_elasticity
            n = dev.base_starts_per_tick * zcfg.household_share * factor

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

    def _reprice_inventory(self, state: WorldState) -> list[Intent]:
        """Re-list completed-but-unsold stock at a markdown that widens with holding time.

        Without this, a new build whose ask decayed below its reserve was delisted and never
        touched again by any actor: permanently dead supply that muted the whole construction
        channel.
        """
        cfg = state.config
        intents: list[Intent] = []
        for unit in state.stock.units.values():
            if (
                unit.owner_id != DEVELOPER_ID
                or unit.tenure is not Tenure.VACANT
                or unit.id in state.sale_listings
            ):
                continue
            held = max(0, state.tick - unit.vacant_since)
            markdown = min(MAX_INVENTORY_MARKDOWN, INVENTORY_MARKDOWN_PER_TICK * held)
            ask = state.zones[unit.zone].price_index * unit.quality * (1.0 - markdown)
            intents.append(
                ListForSale(
                    agent_id=self.id,
                    unit_id=unit.id,
                    ask=ask,
                    reserve=ask * (1.0 - cfg.market.max_seller_discount_hi),
                )
            )
        return intents
