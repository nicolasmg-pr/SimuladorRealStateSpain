"""Small landlords — individuals who own the rental stock (85–92% of it).

One agent object manages all household-owned rental units (owner_id >= 0).

Rules (investor-small §3, rent-cap §5, withdrawal margin §7.2):
  - Asking rent = max(required-yield rent, market rent shaded by expectations),
    clipped by the cap where one binds (compliance is probabilistic).
  - Required yield = bond + 3–5pp spread, + risk premium in low-income zones,
    + perceived (not actual) default risk markup.
  - A cap that still clears the landlord's reservation rent is nothing to arbitrage
    against: no withdrawal. A cap that breaks the reservation hurdle is weighed against
    the alternative uses of the capital: the seasonal-segment diversion first, because it
    is the cheaper exit, then sale, which beats letting when the cumulative shortfall over
    the holding horizon exceeds the cost of leaving (`_exit_destination`, §7.2). Vacancy is
    not a branch — it is the sale channel waiting for `clear_sales` to match it.
  - Below-cap units drift UP toward the reference (the cap is a magnet, Monràs).
"""

from __future__ import annotations

import numpy as np

from ..config import SimConfig, ZoneType
from ..market.stock import Tenure, Unit
from ..state import WorldState
from .base import Intent, ListForRent, WithdrawRental

TICKS_PER_YEAR = 4  # model ticks are quarters

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

    THE TOTAL-RETURN HURDLE (model-spec §7.1, phase B 2026-09-14):

        r_req = V · (i_bond + π − E[g]) / (12 · (1 − c))

    A landlord holds a dwelling for rent AND for what it will be worth. The required *total*
    return is the bond plus a risk premium; whatever the price is expected to deliver on its
    own is return the rent does not have to produce. The rent yield is therefore the residual,
    grossed up for the costs that never reach the landlord's pocket.

    What changed and why it matters: the old form was

        required yield = bond + spread

    with `spread` fitted to reproduce the observed 5.2 / 7.0 / 8.0 zone ladder. That pins the
    yield to its own target, so the model could only ever return the ladder it was handed
    (spec §2, finding 3), and `ZoneConfig.gross_yield` was an input pretending to be a
    prediction. With E[g] in the expression the yield becomes an OUTPUT: it compresses when
    appreciation is expected and widens when it is not, which is the one observable that says
    whether this rule is right (model-spec §9 targets 9 and 10).

    π is split into a measured prime spread and a declared small-landlord premium — see
    `MarketConfig`; reusing the old 2pp would have re-pinned the yield under a new name,
    because that 2pp *was* the observed yield minus the bond.

    E[g] is the zone's expected price growth, annualised. It is the landlord's own
    expectation, formed by the same EWMA the buyers use, so a boom is self-reinforcing on the
    sale side and self-limiting on the rent side — which is the asymmetry the compression
    target tests. Floored so a boom cannot produce a negative rent.
    """
    cfg = state.config
    mk = cfg.market
    pi = mk.prime_risk_spread + mk.small_landlord_premium
    if zone is not ZoneType.TENSIONED:
        pi += mk.landlord_zone_risk_premium  # BdE RBA gradient
    # perceived default risk scales the PREMIUM, not the bond and not the whole yield: a
    # landlord does not demand a higher risk-free rate, only more compensation for the risk
    risk_scaling = 1.0 + mk.default_rate * (mk.perceived_risk_markup - 1.0)
    expected_growth = TICKS_PER_YEAR * state.zones[zone].expected_price_growth
    required_yield = max(
        mk.min_required_yield,
        state.macro.bond_yield + pi * risk_scaling - expected_growth,
    )
    return value * required_yield / (12.0 * (1.0 - mk.landlord_cost_share))


def cap_level(
    state: WorldState,
    zone: ZoneType,
    quality: float,
    *,
    previous_rent: float = 0.0,
    large_holder: bool = True,
) -> float | None:
    """The cap on a new contract, €/month, or None when none binds.

    **Two caps, because the statute has two** (Ley 12/2023 amending LAU art. 17.6–17.7, and
    docs/policies/rent-cap.md). In a declared tensioned area:

    - a **gran tenedor** (≥10 dwellings, ≥5 in the area) is capped at the **reference index**;
    - **everyone else** is capped at the **rent of the previous contract**, uprated by the
      statutory within-contract index (IRAV), and only falls back to the reference index when
      the dwelling has no previous contract to anchor on.

    The model applied the index to every landlord until 2026-09-15, which is a much harder cap
    than the law: individuals hold 85–92% of the Spanish rental stock, so the index was binding
    on the nine tenths of the market it does not bind on in Spain. That single error was the
    whole of the rent-cap rent leg's overshoot — the model cut tensioned contract rents 24%
    where Monràs and García-Montalvo measure ≈5% (docs/validation.md).
    """
    pol = state.config.policy
    if not (pol.rent_cap_enabled and zone in pol.rent_cap_zones):
        return None
    index_cap = state.zones[zone].reference_rent * quality
    if large_holder or pol.cap_index_binds_all:
        return index_cap
    if previous_rent <= 0.0:
        # a small landlord whose dwelling had no contract in the last five years is capped by
        # NOTHING: art. 17.6 anchors on a previous contract it does not have, and art. 17.7's
        # index binds grandes tenedores only. Returning the index here — as the model did
        # until 2026-09-15 — invents a ceiling the law does not impose
        return None
    # the small landlord's ceiling is its own last contract plus IRAV, which in a market that
    # has run ahead of the index is far LOOSER than the index — and that is the law
    return previous_rent * (1.0 + pol.within_contract_update / 4.0)


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

            # a small landlord is capped by its own previous contract, not by the index
            cap = cap_level(
                state,
                unit.zone,
                unit.quality,
                previous_rent=unit.rent or unit.last_contract_rent,
                large_holder=False,
            )
            capped = False
            if cap is not None and not is_covered(state, unit):
                cap = None  # not a declared municipality: no cap applies to this unit
            if cap is not None:
                complies = self.rng.random() < cfg.policy.cap_compliance
                # §7.2: the trigger is the landlord's RESERVATION rent (`floor`), not the cap
                # binding at all. A cap that binds but leaves `cap >= floor` still clears the
                # landlord's total-return hurdle, so there is nothing to arbitrage against and
                # nothing is withdrawn — only a cap that breaks the hurdle triggers an exit.
                #
                # RETIRED (2026-09-16): a fitted exit hazard used to sit here — a PV level gap
                # (`log(fundamental_ask / cap)`, scaled by a growth wedge) drawn against a
                # fitted `hazard_scale`. It is replaced by the deterministic sale rule of
                # model-spec §7.2: which alternative use, if any, beats letting at the cap.
                # See `_exit_destination`.
                if complies and cap < floor:
                    dest = self._exit_destination(unit, state, cap=cap, r_req=floor, value=value)
                    if dest is not None:
                        intents.append(
                            WithdrawRental(agent_id=self.id, unit_id=unit.id, destination=dest)
                        )
                        continue
                if complies and fundamental_ask > cap:
                    ask, capped = min(ask, cap), True
                elif ask < cap:
                    # magnet effect: below-reference asks drift up toward the cap
                    ask = min(cap, ask * capcfg.magnet_gain)
            intents.append(ListForRent(agent_id=self.id, unit_id=unit.id, ask=ask, capped=capped))
        return intents

    def _exit_destination(
        self, unit: Unit, state: WorldState, *, cap: float, r_req: float, value: float
    ) -> str | None:
        """§7.2. Which alternative use beats letting at the cap, or None if none does.

        Evaluated in the branch order the spec fixes ("Branch order, and the natural
        experiment that tests it"): SEASONAL first, then SALE. There is no third branch —
        vacancy is not a destination this method ever returns (spec §7.2, "Vacancy is not a
        branch"); a unit that sells sits empty only while waiting for `clear_sales` to match
        it, which is an output of the sale channel, not a choice made here.
        """
        cfg = state.config
        capcfg, pol, zs = cfg.cap_response, cfg.policy, state.zones[unit.zone]
        # SEASONAL, evaluated FIRST because it is the cheap exit: diverting to a seasonal
        # contract pays no transaction cost and selling does. Closing the segment therefore
        # pushes exits into sales, which is the comparative static Ley 11/2025 dated.
        seasonal_open = not pol.seasonal_segment_capped
        if seasonal_open and self.rng.random() < cfg.market.seasonal_evasion_share:
            return "seasonal"
        # SALE. The shortfall WIDENS over the horizon: the cap grows at the statutory IRAV
        # while the reservation rent grows with V and E[g]. The (1 + H·wedge/2) factor is the
        # trapezoid of that widening gap — arithmetic, not a parameter. No double-counting of
        # appreciation: `r_req` already nets E[g], so `r_req - cap` is the monthly shortfall
        # against the best alternative use of the capital, appreciation included.
        growth_wedge = max(
            0.0, capcfg.wedge_annualisation * zs.shadow_growth - pol.within_contract_update
        )
        horizon = capcfg.holding_years
        shortfall = (r_req - cap) * 12.0 * horizon * (1.0 + horizon * growth_wedge / 2.0)
        if shortfall > value * cfg.market.selling_cost_share:
            return "sale"
        return None


def exit_cost_for(unit: Unit, cfg: SimConfig) -> float:
    """The landlord's cost of leaving, as a share of the dwelling's value (model-spec §7.2b).

    Monotone in `unit.sale_route_draw`: the cheap-to-extract private sellers sit at the bottom
    and leave first, agency sellers at the top and hold out longest. Monotonicity is the point —
    it makes a harder cap ADD landlords to the exiting set instead of reshuffling it.
    """
    c = cfg.cap_response
    s = c.intermediation_share
    u = unit.sale_route_draw
    if u < 1.0 - s:
        lo, hi = c.exit_cost_private
        frac = u / (1.0 - s) if s < 1.0 else 0.0
    else:
        lo, hi = c.exit_cost_agency
        frac = (u - (1.0 - s)) / s if s > 0.0 else 0.0
    return lo + (hi - lo) * frac
