"""Households — the demand side.

One agent object manages the whole registry (faster than 10k objects, same contract):
decide() reads state, returns intents, never writes.

Rules (model-spec §3/§5, household-owner §3, household-tenant §3):
  - Buy vs rent is affordability-gated, not preference-gated: entry needs the down
    payment + costs upfront AND the DSTI screen at the current rate.
  - WTP anchors on the bank-permitted budget, shaded by expected price growth
    (adaptive momentum — the FOMO channel).
  - Owners move rarely (~1.1%/quarter); tenants rotate more (~4–8%/quarter) and pay
    the insider/outsider penalty when they do.
  - Tenants accept rent up to a household-specific burden threshold (30–40% of income).
"""

from __future__ import annotations

import numpy as np

from ..state import HouseholdStatus, WorldState
from .bank import cash_price, max_price
from .base import Intent, ListForSale, MakeOffer, RentApplication


class Households:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        cfg = state.config
        pop = cfg.population
        credit = cfg.credit
        macro = state.macro
        intents: list[Intent] = []

        hhs = list(state.households.values())
        n = len(hhs)
        move_draw = self.rng.random(n)
        buy_draw = self.rng.random(n)
        shade_draw = self.rng.uniform(0.85, 1.0, n)
        guarantee_draw = self.rng.random(n)

        for i, hh in enumerate(hhs):
            zone_cfg = cfg.zone(hh.zone)
            zs = state.zones[hh.zone]
            itp = macro.itp[hh.zone]
            momentum = float(np.clip(5.0 * zs.expected_price_growth, -0.10, 0.10))

            if hh.status is HouseholdStatus.OWNER:
                # rare movers: list the home; they re-enter demand after it sells
                if move_draw[i] < pop.owner_move_prob:
                    unit = state.stock.units[hh.unit_id]
                    ask = zs.price_index * unit.quality * (1.0 + zs.expected_price_growth)
                    reserve = ask * (1.0 - cfg.market.max_seller_discount)
                    intents.append(
                        ListForSale(agent_id=hh.id, unit_id=unit.id, ask=ask, reserve=reserve)
                    )
                continue

            # TENANT or SEEKER — first the buy attempt, else the rental market
            first_time = True
            guaranteed = (
                cfg.policy.guarantee_ltv_boost > 0.0
                and first_time
                and guarantee_draw[i] < cfg.policy.guarantee_eligible_share
                and macro.guarantee_budget_left > 0.0
            )
            limit = max_price(
                hh, macro.mortgage_rate, credit, itp, cfg.market.buyer_fees, guaranteed
            )
            median_price = zs.price_index
            # user-cost check: owning vs renting at the current rate — the channel a
            # rate shock works through (2022–23: volume fell, prices stayed sticky)
            user_cost = max(
                0.005,
                macro.mortgage_rate + 0.01 - 4.0 * zs.expected_price_growth,
            )  # 0.01 = maintenance+IBI /yr [guess]
            gross_yield = zs.rent_index * 12.0 / max(zs.price_index, 1.0)
            own_vs_rent = float(np.clip(gross_yield / user_cost, 0.5, 1.0))
            # participation swings with expectations: buyers rush in booms, freeze in
            # slowdowns — "volume adjusts first, prices are sticky" [household-owner §4]
            participation = float(
                np.clip(
                    1.0
                    + 15.0 * (zs.expected_price_growth - cfg.market.long_run_growth)
                    - 8.0 * max(0.0, macro.mortgage_rate - 0.035),
                    0.4,
                    1.6,
                )
            )
            wants_to_buy = buy_draw[i] < pop.buy_attempt_prob * participation
            budget = limit * shade_draw[i] * (1.0 + momentum) * own_vs_rent
            can_buy = budget >= 0.6 * median_price  # cheapest habitable segment [guess]
            if wants_to_buy and can_buy:
                intents.append(
                    MakeOffer(
                        agent_id=hh.id,
                        zone=hh.zone,
                        budget=budget,
                        cash=cash_price(hh, itp, cfg.market.buyer_fees) >= budget,
                        first_time=first_time,
                    )
                )
                continue

            if hh.status is HouseholdStatus.SEEKER:
                max_rent = hh.max_rent_burden * hh.income / 12.0
                max_rent += self._rent_subsidy(state, hh)
                intents.append(RentApplication(agent_id=hh.id, zone=hh.zone, max_rent=max_rent))
            elif hh.status is HouseholdStatus.TENANT and move_draw[i] < pop.tenant_move_prob:
                # rotation: only move if the outsider penalty is bearable
                unit = state.stock.units[hh.unit_id]
                market_rent = zs.rent_index * unit.quality
                penalty_ok = market_rent <= hh.max_rent_burden * hh.income / 12.0
                if penalty_ok:
                    max_rent = hh.max_rent_burden * hh.income / 12.0
                    max_rent += self._rent_subsidy(state, hh)
                    intents.append(RentApplication(agent_id=hh.id, zone=hh.zone, max_rent=max_rent))
            _ = zone_cfg  # zone config reserved for future household heterogeneity
        return intents

    def _rent_subsidy(self, state: WorldState, hh) -> float:
        pol = state.config.policy
        if pol.rent_subsidy_month <= 0.0:
            return 0.0
        # eligibility drawn once per household id — deterministic hash keeps decide() pure
        eligible = (hash((hh.id, "bono")) % 1000) / 1000.0 < pol.rent_subsidy_eligible_share
        return pol.rent_subsidy_month if eligible else 0.0
