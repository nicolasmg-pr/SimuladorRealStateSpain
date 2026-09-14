"""Large investor — grandes tenedores, SOCIMIs, funds (owner_id == LARGE_INVESTOR_ID).

Rules (investor-large §3):
  - Yield-hurdle entry: buy when zone gross yield clears prime hurdle + spread over
    the bond; countercyclical appetite (entered at 30–60% discounts 2013–17).
  - Price AT the cap when regulated (min(optimum, cap)); the index cap binds them
    harder than small landlords (compliance ≈ 1 — they are visible).
  - Exit unit-by-unit ("piso a piso") when the cap binds or yield falls below hurdle.
"""

from __future__ import annotations

import numpy as np

from ..config import ZoneType
from ..market.stock import LARGE_INVESTOR_ID, Tenure
from ..state import WorldState
from .bank import itp_wedge
from .base import Intent, ListForRent, ListForSale, MakeOffer
from .landlord import cap_level, is_covered

PRIME_HURDLE_SPREAD = 0.015  # required gross yield over bond [CBRE prime 3.8–4.0 — medium]
EXIT_LIST_SHARE = 0.05  # share of portfolio listed for sale per tick when exiting [medium]
MAX_BUYS_PER_TICK = 4  # portfolio purchases per tick per zone at model scale [guess]


class LargeInvestor:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        intents: list[Intent] = []
        portfolio = [u for u in state.stock.units.values() if u.owner_id == LARGE_INVESTOR_ID]
        hurdle = state.macro.bond_yield + PRIME_HURDLE_SPREAD

        for zone in ZoneType:
            zs = state.zones[zone]
            zone_units = [u for u in portfolio if u.zone is zone]
            if not zone_units and state.config.zone(zone).large_investor_share == 0.0:
                continue
            gross_yield = zs.rent_index * 12.0 / max(zs.price_index, 1.0)
            cap = cap_level(state, zone, 1.0)
            # binds against the SHADOW rent (what the units would fetch uncapped) — the
            # asking index is the cap itself once a cap is on
            cap_binds = cap is not None and cap < zs.shadow_rent

            # a cap-driven exit only concerns the DECLARED part of the portfolio, unit by
            # unit; a yield-driven one concerns all of it
            yield_exit = gross_yield < hurdle
            reachable = (
                zone_units if yield_exit else [u for u in zone_units if is_covered(state, u)]
            )
            exiting = yield_exit or (cap_binds and reachable)
            if exiting and reachable:
                n_list = max(1, int(EXIT_LIST_SHARE * len(reachable)))
                # piso a piso: vacant units first, then tenanted ones (sold on or at
                # rotation — displaced tenants re-enter the search queue at settlement)
                sellable = sorted(
                    (u for u in reachable if u.id not in state.sale_listings),
                    key=lambda u: u.tenure is not Tenure.VACANT,
                )
                for u in sellable[:n_list]:
                    ask = zs.price_index * u.quality * (1.0 + state.config.market.ask_markup)
                    intents.append(
                        ListForSale(
                            agent_id=self.id,
                            unit_id=u.id,
                            ask=ask,
                            # an institutional seller carries no mortgage in this model,
                            # so only the negotiation-margin leg of the reserve binds
                            reserve=ask * (1.0 - state.config.market.max_seller_discount_hi),
                        )
                    )
            elif gross_yield > hurdle * 1.15:
                # CAPITALISED BID (model-spec §7.4, phase B). The investor pays at most what
                # the rent is worth at its own hurdle:
                #
                #     max_bid = 12 · r · (1 − c) / y_req
                #
                # It used to bid `price_index × U(0.95, 1.05)` — at the index it is itself
                # helping to set. That is positive feedback with no nominal anchor (spec §2,
                # finding 5): a cash buyer large enough to move the index bidding a multiple of
                # the index it moves. Nothing in it could ever say a price was too high.
                #
                # Anchoring to RENT breaks the loop. Rents are set in a different market by
                # different agents, so the investor now has an opinion about value that its own
                # purchases do not manufacture, and it stops buying when prices outrun rents —
                # which is what a yield hurdle is supposed to mean and what the old form could
                # not express.
                #
                # `(1 − c)` nets the rent down: the same operating-cost share the small
                # landlord grosses up by in `required_rent` (§7.1), applied in the opposite
                # direction, because both agents are pricing the same cash flow.
                max_bid = (
                    zs.rent_index * 12.0 * (1.0 - state.config.market.landlord_cost_share) / hurdle
                )
                # transaction-tax change aimed at legal persons (Catalan 20% TPO precedent) —
                # a cash buyer's budget moves by the tax wedge, not by a credit screen
                wedge = itp_wedge(
                    state.config.zone(zone).itp_rate,
                    state.macro.itp[zone] + state.config.policy.itp_investor_delta,
                )
                for _ in range(MAX_BUYS_PER_TICK):
                    intents.append(
                        MakeOffer(
                            agent_id=self.id,
                            zone=zone,
                            budget=max_bid * float(self.rng.uniform(0.95, 1.05)) * wedge,
                            cash=True,
                        )
                    )

            # rent out vacant portfolio units — at the cap when regulated and the unit sits
            # inside a declared municipality (same persistent coverage test as small landlords)
            for u in zone_units:
                if (
                    u.tenure is Tenure.VACANT
                    and u.id not in state.rent_listings
                    and u.id not in state.sale_listings
                ):
                    ask = zs.rent_index * u.quality * (1.0 + zs.expected_rent_growth)
                    capped = False
                    ucap = cap_level(state, zone, u.quality)
                    if ucap is not None and not is_covered(state, u):
                        ucap = None
                    if ucap is not None:
                        ask, capped = min(ask, ucap), ask > ucap
                    intents.append(
                        ListForRent(agent_id=self.id, unit_id=u.id, ask=ask, capped=capped)
                    )
        return intents
