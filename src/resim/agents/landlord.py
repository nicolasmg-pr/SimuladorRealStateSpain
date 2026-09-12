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

# how hard queue congestion pushes asking rents up: ask × (1 + gain × clip(applicants per
# listing − 1, −0.5, 3)). THE parameter that decides whether rents can outrun incomes in a
# boom, because it is the only channel through which scarcity, rather than income, reaches
# the asking index [model-spec §9 target 7r]. Swept on the hold-out boom's 10 seeds:
#   0.05 → boom rents +3.6%/yr ± 0.8 (10/10 seeds positive)   ← kept
#   0.15 → +4.9% ± 1.4   ·   0.25 → +6.9% ± 4.9   ·   0.40 → +5.0% ± 6.4 (non-monotone)
# Left at its original 0.05 deliberately. Raising it to 0.15 buys 1.3pp of boom rent growth
# and costs a **22% higher baseline rent level** on the diagnostic that was already the
# model's worst (€1,352 → €1,648 against an EPF €516) plus a weaker rent-cap supply response
# (contracts at elasticity 2: −13.6% → −7.4%, no longer reaching Monràs's −10%). The boom
# target it would have been bought for is already met without it, by the tightness
# recalibration and the location premium. Recorded rather than tuned
# [Barcelona ≈65 contacts per listing, rent-cap §3 — mechanism sourced, level a guess]
CONGESTION_GAIN = 0.05


# The cap-response constants that used to live here — EXIT_SPLIT, HAZARD_SCALE, the magnet
# gain and EXIT_SPLIT_EVASION_BASE — are now `config.CapResponseConfig`, unchanged in value.
# They moved in phase A (spec §2, finding 10) so phase E's screening can reach them: the
# headline rent-cap result depends on all four, and a constant outside config.py cannot be
# swept. Their provenance, ranges and the 2026-09-08 hazard re-fit are documented there.


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


def is_covered(state: WorldState, unit) -> bool:
    """Does this unit sit in a DECLARED tensioned municipality?

    The law is switched on municipality by municipality and the model's zone is bigger than
    Spain's declared map (Jul 2026: 317 municipalities, ≈19% of the population ⇒ ≈0.42 of the
    tensioned zone). Coverage is a persistent property of the unit (`Unit.declaration_draw`),
    not a per-tick draw: a municipality does not change status between quarters, and the
    capped and uncapped segments have to stay separable for the whole run so their rents can
    be reported apart (metrics.py). Distinct from *compliance*, which is a covered landlord
    choosing whether to obey.
    """
    return unit.declaration_draw < state.config.policy.cap_coverage


class SmallLandlords:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        cfg = state.config
        capcfg = cfg.cap_response
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
            floor = required_rent(state, unit.zone, value)
            market_ask = zs.rent_index * unit.quality * (1.0 + zs.expected_rent_growth)
            # the landlord's FUNDAMENTAL ask: what the unit would fetch with no cap — the
            # shadow rent (equal to the index in a free market; inferred from the queue under a
            # cap, engine._update_indices), before any queue congestion. The exit decision
            # compares the cap to THIS. Two earlier versions failed: comparing to the posted
            # ask let the cap unbind (the asking index collapses onto the cap, so the gap went
            # to zero within four ticks), and comparing to the congestion-inflated ask turned
            # exits into a spiral (tenancies −50 to −87% at elasticity 2 in a tight market).
            fundamental_ask = max(
                floor, zs.shadow_rent * unit.quality * (1.0 + zs.expected_rent_growth)
            )
            # queue congestion pushes asks up (65 families/listing in Barcelona,
            # rent-cap §3); slack markets push them down
            pressure = 1.0 + CONGESTION_GAIN * float(
                np.clip(tightness.get(unit.zone, 1.0) - 1.0, -0.5, 3.0)
            )
            market_ask *= pressure
            ask = max(floor, market_ask)

            cap = cap_level(state, unit.zone, unit.quality)
            capped = False
            if cap is not None and not is_covered(state, unit):
                cap = None  # not a declared municipality: no cap applies to this unit
            if cap is not None:
                complies = self.rng.random() < cfg.policy.cap_compliance
                if fundamental_ask > cap and complies:
                    # withdrawal margin: the disputed elasticity parameter. The gap is the
                    # PV shortfall of the capped stream over the landlord's holding horizon.
                    #
                    # The free stream grows at the SHADOW's rate, not at the asking index's:
                    # under a cap `expected_rent_growth` is an expectation formed on capped
                    # asks, and feeding it back in double-counts the cap (model-spec §5b).
                    #
                    # PHASE A (spec §2, finding 9). The wedge is built from two EXOGENOUS
                    # constants — the shadow's growth anchor and the statutory update — so it
                    # is a constant. It used to be ADDED to the level gap:
                    #
                    #     gap = log(ask / cap) + 5 * wedge
                    #
                    # which is discontinuous at the point the cap starts to bind. A cap
                    # binding by one euro produced the same `5 * wedge` term as a cap binding
                    # by a third of the rent, so the exit hazard jumped from zero to a fixed
                    # positive floor the instant the cap touched the ask, and stayed there
                    # however mild the cap was. The floor came from two constants nobody
                    # chose as a hazard, and the headline cap result rode on it.
                    #
                    # The wedge is a real PV term and stays. What changes is that it SCALES
                    # the level gap instead of being added to it: the shortfall of a capped
                    # stream is proportional to how far the cap is below the free rent, and
                    # the growth divergence compounds that shortfall over the holding
                    # horizon. A cap that binds on nothing costs nothing, however long it is
                    # held — which is the property the additive form did not have.
                    level_gap = np.log(fundamental_ask / cap)
                    growth_wedge = max(
                        0.0,
                        capcfg.wedge_annualisation * zs.shadow_growth
                        - cfg.policy.within_contract_update,
                    )
                    gap = level_gap * (1.0 + capcfg.holding_years * growth_wedge)
                    # HAZARD_SCALE maps the per-listing quarterly exit hazard onto the
                    # studies' annual contract-flow elasticity: calibrated so that
                    # elasticity=2 reproduces Monràs & García-Montalvo's Δln contracts
                    # / Δln rent ≈ 2 (−10% tenancies at −5% rents)
                    p_exit = min(
                        0.9, cfg.market.rental_supply_elasticity * capcfg.hazard_scale * gap
                    )
                    if self.rng.random() < p_exit:
                        intents.append(self._exit(unit.id, state))
                        continue
                    ask, capped = min(ask, cap), True
                elif ask < cap:
                    # magnet effect: below-reference asks drift up toward the cap
                    ask = min(cap, ask * capcfg.magnet_gain)
            intents.append(ListForRent(agent_id=self.id, unit_id=unit.id, ask=ask, capped=capped))
        return intents

    def _exit(self, unit_id: int, state: WorldState) -> WithdrawRental:
        pol = state.config.policy
        capcfg = state.config.cap_response
        u = self.rng.random()
        seasonal_open = not pol.seasonal_segment_capped
        p_sale = capcfg.exit_split_sale
        p_seasonal = capcfg.exit_split_seasonal * (
            state.config.market.seasonal_evasion_share / capcfg.exit_split_evasion_base
            if seasonal_open
            else 0.0
        )
        if u < p_sale:
            dest = "sale"
        elif u < p_sale + p_seasonal:
            dest = "seasonal"
        else:
            dest = "vacant"
        return WithdrawRental(agent_id=self.id, unit_id=unit_id, destination=dest)
