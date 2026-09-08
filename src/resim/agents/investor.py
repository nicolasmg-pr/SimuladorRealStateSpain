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
from .landlord import cap_level

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

            # a cap-driven exit only concerns the covered part of the portfolio (no declared
            # municipality, no exit); a yield-driven one concerns all of it
            coverage = state.config.policy.cap_coverage
            exiting = gross_yield < hurdle or (cap_binds and coverage > 0.0)
            if exiting and zone_units:
                reach = 1.0 if gross_yield < hurdle else coverage
                n_list = max(1, int(EXIT_LIST_SHARE * reach * len(zone_units)))
                # piso a piso: vacant units first, then tenanted ones (sold on or at
                # rotation — displaced tenants re-enter the search queue at settlement)
                sellable = sorted(
                    (u for u in zone_units if u.id not in state.sale_listings),
                    key=lambda u: u.tenure is not Tenure.VACANT,
                )
                for u in sellable[:n_list]:
                    ask = zs.price_index * u.quality
                    intents.append(
                        ListForSale(
                            agent_id=self.id,
                            unit_id=u.id,
                            ask=ask,
                            reserve=ask * 0.92,
                        )
                    )
            elif gross_yield > hurdle * 1.15:
                # accumulation: enter with market-rate offers, net of any transaction-tax
                # change aimed at legal persons (Catalan 20% TPO precedent) — a cash buyer's
                # budget moves by the tax wedge, not by a credit screen
                wedge = itp_wedge(
                    state.config.zone(zone).itp_rate,
                    state.macro.itp[zone] + state.config.policy.itp_investor_delta,
                )
                for _ in range(MAX_BUYS_PER_TICK):
                    intents.append(
                        MakeOffer(
                            agent_id=self.id,
                            zone=zone,
                            budget=zs.price_index * float(self.rng.uniform(0.95, 1.05)) * wedge,
                            cash=True,
                        )
                    )

            # rent out vacant portfolio units — at the cap when regulated and the unit sits
            # inside a declared municipality (coverage draw, as for small landlords)
            for u in zone_units:
                if (
                    u.tenure is Tenure.VACANT
                    and u.id not in state.rent_listings
                    and u.id not in state.sale_listings
                ):
                    ask = zs.rent_index * u.quality * (1.0 + zs.expected_rent_growth)
                    capped = False
                    ucap = cap_level(state, zone, u.quality)
                    if ucap is not None and self.rng.random() >= coverage:
                        ucap = None
                    if ucap is not None:
                        ask, capped = min(ask, ucap), ask > ucap
                    intents.append(
                        ListForRent(agent_id=self.id, unit_id=u.id, ask=ask, capped=capped)
                    )
        return intents
