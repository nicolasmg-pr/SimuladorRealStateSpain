"""Small landlords — individuals who own the rental stock (85–92% of it).

One agent object manages all household-owned rental units (owner_id >= 0).

Rules (investor-small §3, rent-cap §5):
  - Asking rent = max(required-yield rent, market rent shaded by expectations),
    clipped by the cap where one binds (compliance is probabilistic).
  - Required yield = bond + 3–5pp spread, + risk premium in low-income zones,
    + perceived (not actual) default risk markup.
  - When a cap binds, withdrawal probability per tick ≈ elasticity × relative rent gap
    — the single exposed parameter that spans the Monràs (ε≈2) / Jofre-Monseny (ε≈0) /
    Pérez García worlds. Exits split between sale, seasonal segment (while uncapped)
    and vacancy.
  - Below-cap units drift UP toward the reference (the cap is a magnet, Monràs).
"""

from __future__ import annotations

import numpy as np

from ..config import ZoneType
from ..market.stock import Tenure
from ..state import WorldState
from .base import Intent, ListForRent, WithdrawRental

# exit split when a capped landlord withdraws: sale / seasonal / vacant [guess — open
# question investor-small §7.1; seasonal share reroutes to sale+vacant when capped]
EXIT_SPLIT = {"sale": 0.5, "seasonal": 0.35, "vacant": 0.15}

# per-listing hazard → annual contract-flow elasticity mapping (see decide())
HAZARD_SCALE = 1.75


def required_rent(state: WorldState, zone: ZoneType, value: float) -> float:
    """€/month a small landlord needs to keep a unit on the rental market.

    Required gross yield = bond + 3–5pp spread (the spread already prices default
    risk, investor-small §6); low-income zones add the BdE RBA risk-premium gradient.
    Perceived-risk markup scales the spread, not the whole yield.
    """
    cfg = state.config
    spread = cfg.market.landlord_required_spread
    if zone is not ZoneType.TENSIONED:
        spread += cfg.market.landlord_zone_risk_premium  # BdE RBA gradient
    risk_scaling = 1.0 + cfg.market.default_rate * (cfg.market.perceived_risk_markup - 1.0)
    return value * (state.macro.bond_yield + spread * risk_scaling) / 12.0


def cap_level(state: WorldState, zone: ZoneType, quality: float) -> float | None:
    """Reference-index cap for a new contract, €/month, or None when no cap binds."""
    pol = state.config.policy
    if not (pol.rent_cap_enabled and zone in pol.rent_cap_zones):
        return None
    return state.zones[zone].reference_rent * quality


class SmallLandlords:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        cfg = state.config
        intents: list[Intent] = []
        candidates = [
            u
            for u in state.stock.units.values()
            if u.owner_id >= 0
            and u.tenure is Tenure.VACANT
            and not u.withheld
            and u.id not in state.rent_listings
            and u.id not in state.sale_listings
        ]
        tightness = state.tick_events.get("rental_tightness", {})
        for unit in candidates:
            zs = state.zones[unit.zone]
            value = zs.price_index * unit.quality
            market_ask = zs.rent_index * unit.quality * (1.0 + zs.expected_rent_growth)
            # queue congestion pushes asks up (65 families/listing in Barcelona,
            # rent-cap §3); slack markets push them down
            pressure = 1.0 + 0.05 * float(np.clip(tightness.get(unit.zone, 1.0) - 1.0, -0.5, 3.0))
            market_ask *= pressure
            ask = max(required_rent(state, unit.zone, value), market_ask)

            cap = cap_level(state, unit.zone, unit.quality)
            capped = False
            if cap is not None:
                complies = self.rng.random() < cfg.policy.cap_compliance
                if ask > cap and complies:
                    # withdrawal margin: the disputed elasticity parameter. The gap is
                    # the PV shortfall of the capped stream: today's level gap plus the
                    # growth wedge (capped rents grow at IRAV, market at expectations)
                    # over a ~5-year holding horizon
                    growth_wedge = max(
                        0.0,
                        4.0 * zs.expected_rent_growth - cfg.policy.within_contract_update,
                    )
                    gap = np.log(ask / cap) + 5.0 * growth_wedge
                    # HAZARD_SCALE maps the per-listing quarterly exit hazard onto the
                    # studies' annual contract-flow elasticity: calibrated so that
                    # elasticity=2 reproduces Monràs & García-Montalvo's Δln contracts
                    # / Δln rent ≈ 2 (−10% tenancies at −5% rents)
                    p_exit = min(0.9, cfg.market.rental_supply_elasticity * HAZARD_SCALE * gap)
                    if self.rng.random() < p_exit:
                        intents.append(self._exit(unit.id, state))
                        continue
                    ask, capped = cap, True
                elif ask < cap:
                    # magnet effect: below-reference asks drift up toward the cap
                    ask = min(cap, ask * 1.05)
            intents.append(ListForRent(agent_id=self.id, unit_id=unit.id, ask=ask, capped=capped))
        return intents

    def _exit(self, unit_id: int, state: WorldState) -> WithdrawRental:
        pol = state.config.policy
        u = self.rng.random()
        seasonal_open = not pol.seasonal_segment_capped
        p_sale = EXIT_SPLIT["sale"]
        p_seasonal = EXIT_SPLIT["seasonal"] * (
            state.config.market.seasonal_evasion_share / 0.15 if seasonal_open else 0.0
        )
        if u < p_sale:
            dest = "sale"
        elif u < p_sale + p_seasonal:
            dest = "seasonal"
        else:
            dest = "vacant"
        return WithdrawRental(agent_id=self.id, unit_id=unit_id, destination=dest)
