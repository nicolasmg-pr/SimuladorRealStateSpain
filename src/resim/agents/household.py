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

from ..market.clearing import loss_averse_ask, seller_reserve
from ..state import HouseholdStatus, WorldState
from .bank import cash_price, max_price
from .base import Intent, ListForSale, MakeOffer, RentApplication

# --- participation rule coefficients (free parameters, calibrated — model-spec §9.6b) ---
# d(participation)/d(expected growth above the long-run anchor): the FOMO/boom channel,
# fitted on the 2024–25 easing surge (sales +10.7% to a 17-year high) [household-owner §4]
PARTICIPATION_GROWTH_SENSITIVITY = 15.0
# The rate leg of participation — `PARTICIPATION_RATE_SENSITIVITY = 20` on the mortgage rate
# above a 3.5% comfort threshold — WAS REMOVED IN PHASE D (model-spec §5c.3). It was a
# hand-fitted coefficient standing in for a mechanism the model did not have: when rates rise,
# volume falls before prices do. That now comes out of two things the model computes rather
# than assumes — the credit screen (fewer households clear the DSTI cap at a higher rate) and
# the seller's reserve, which is the outstanding mortgage, so owners who bought at the top
# cannot sell into a lower market. If the rate-shock signature had not survived the removal,
# the honest conclusion would have been that the coefficient carried something real; the
# measurement is in docs/validation.md, phase D.
# WTP momentum moved to market/clearing.py in phase D (MOMENTUM_GAIN, MOMENTUM_CAP live
# there now): expected growth shades the VALUATION of a dwelling, not the credit-limited
# budget, because the budget is a capacity and the capitalisation of expected appreciation
# is a valuation. Kept out of this module entirely rather than imported back, so there is
# exactly one place the expectation reaches a price.

# --- the sharing margin (model-spec §5, household-tenant §6) ---------------------------
# A household that keeps failing to find a home does not leave the market: it accepts a
# higher burden, shares the flat, or sublets a room. Without this the accepted rent is a
# hard share of income, income grows at the exogenous anchor, and the rent index therefore
# CANNOT outrun income — which is counterfactual. Spain absorbed rent growth well above
# income growth exactly through this margin:
#   - mean rent effort rose 26.5% (2015) → 31.7% (2021) → 29.7% (2022) of the consumption
#     basket, and the share of renting households above the 30% line 33.0% → 43.1% → 38.2%
#     [EPF microdata, Romero-Jordán, Funcas 104 ch.6];
#   - 4 of 10 Spanish tenants spend >40% of disposable income on rent, ≈2× the EU average
#     [Eurostat via Torres, Funcas 104 ch.2];
#   - the demand priced out is "embalsada" in delayed emancipation and shared flats —
#     "pisos compartidos, habitaciones subalquiladas y otras fórmulas para compartir las
#     cargas" [Ezquiaga, Funcas 104 ch.4].
# So the MECHANISM and the CEILING are sourced; the per-tick pace is a guess with a range.
# Rent accepted after k ticks of search = base burden × (1 + escalation × k), capped.
SEARCH_BURDEN_ESCALATION = 0.04  # /tick of failed search; range 0.02–0.06 [guess]
MAX_RENT_BURDEN_CEILING = 0.55  # vulnerable Spanish tenants: 40.6% rent, 51.1% with
# utilities [EPF via Funcas 104 ch.6 cuadro 3] — the ceiling is a real observed level, not
# a modelling convenience. Applies to SEEKERS only: a sitting tenant is not under this
# duress and keeps their drawn threshold (they move only if the outsider penalty is bearable).


def search_burden(hh) -> float:
    """Rent/income share a searching household will accept after its current search spell.

    Defined here rather than inline so metrics and tests read the same rule as the agent.
    """
    escalated = hh.max_rent_burden * (1.0 + SEARCH_BURDEN_ESCALATION * hh.ticks_searching)
    return min(escalated, MAX_RENT_BURDEN_CEILING)


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
        discount_draw = self.rng.uniform(
            cfg.market.max_seller_discount_lo, cfg.market.max_seller_discount_hi, n
        )

        for i, hh in enumerate(hhs):
            zone_cfg = cfg.zone(hh.zone)
            zs = state.zones[hh.zone]
            itp = macro.itp[hh.zone]
            if hh.status is HouseholdStatus.OWNER:
                # rare movers: list the home; they re-enter demand after it sells
                if move_draw[i] < pop.owner_move_prob:
                    unit = state.stock.units[hh.unit_id]
                    # posted off the TASTE-NEUTRAL index (model-spec §5c.6): what the
                    # dwelling is worth to an average buyer. The markup over it is the
                    # posting convention, and the selection premium a competitive auction
                    # adds is what turns the posted markup into the realised 6.2% discount
                    value = (zs.valuation_index or zs.price_index) * unit.quality
                    ask = value * (1.0 + zs.expected_price_growth) * (1.0 + cfg.market.ask_markup)
                    # a seller facing a nominal loss asks part of it back, and waits
                    # (model-spec §5d.1; Genesove & Mayer 2001). Zero in a rising market.
                    ask = loss_averse_ask(
                        base_ask=ask,
                        paid=unit.last_sale_price,
                        value=value,
                        alpha=cfg.market.loss_aversion_owner,
                    )
                    # the reserve carries the mortgage: a sale has to repay the loan, so an
                    # owner in negative equity cannot sell at all (model-spec §5c.3)
                    reserve = seller_reserve(
                        ask=ask,
                        debt=hh.mortgage_balance + hh.arrears_balance,
                        discount=float(discount_draw[i]),
                        cfg=cfg,
                    )
                    intents.append(
                        ListForSale(agent_id=hh.id, unit_id=unit.id, ask=ask, reserve=reserve)
                    )
                continue

            # TENANT or SEEKER — first the buy attempt, else the rental market.
            # Non-owners are first-time buyers by construction; the aval means test is the
            # household's own reproducible draw, not a per-tick coin flip.
            first_time = True
            # means test: the seeded eligibility draw stands in for the age/income filters
            # (under 35, ≤7.5×IPREM); the wealth cap is the instrument's own 2026 rule
            # (€150k, BOE 2 Jul 2026) and is applied to the wealth the model carries
            guaranteed = (
                cfg.policy.guarantee_ltv_boost > 0.0
                and first_time
                and hh.eligibility_draw < cfg.policy.guarantee_eligible_share
                and hh.wealth <= cfg.policy.guarantee_wealth_cap
                and macro.guarantee_budget_left > 0.0
            )
            ltv_boost = cfg.policy.guarantee_ltv_boost if guaranteed else 0.0
            limit = max_price(
                hh, macro.mortgage_rate, credit, itp, cfg.market.buyer_fees, ltv_boost
            )
            median_price = zs.price_index
            # Budget shading when renting looks cheap against owning. The comment here used
            # to call this "the channel a rate shock works through (2022–23)", and the
            # redesign spec (§2, finding 6) registered it as an inert term clipped to 1.0
            # below a ~6.2% mortgage rate. **Both statements are wrong, measured 2026-09-12
            # on 3 seeds × 40 ticks, instrumenting every value the model computes:**
            #
            #   baseline    below 1.0 in 5.78% of decisions, min 0.858, mean 0.9951
            #   RateShock   below 1.0 in 3.23% of decisions, min 0.858, mean 0.9978
            #
            # So it is not dead — removing it moves the baseline price level by −1.5% — and
            # it engages LESS under a rate shock than at baseline, which is the opposite of
            # what a rate channel does. The reason is that `gross_yield` dominates the ratio:
            # the shock cuts prices ~10% and lifts rents ~22%, the yield rises, and the ratio
            # clips to 1.0 more often, not less. The 0.5 floor has never bound in any run
            # measured (min 0.858).
            #
            # What it actually is: an unsourced reduced form that shades the bid when the
            # rental yield is low against the user cost of owning. Kept at its measured
            # behaviour rather than removed, because removing an active channel is a
            # modelling decision and phase A is bug fixes; registered in docs/assumptions.md
            # with its falsifier, and owned by phase D, where tenure choice is specified
            # properly instead of as a clipped multiplier on a credit limit.
            # The rate shock reaches the market through `participation` below.
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
                    + PARTICIPATION_GROWTH_SENSITIVITY
                    * (zs.expected_price_growth - cfg.market.long_run_growth),
                    0.4,
                    1.6,
                )
            )
            wants_to_buy = buy_draw[i] < pop.buy_attempt_prob * participation
            # location premium (model-spec §5b): what the dwelling's LOCATION is worth to the
            # household, normalised to 1.0 in the tensioned zone. It discounts willingness in
            # the low-amenity zones; without it nothing stops a rural household from bidding
            # its full credit limit and the zone price ladder closes from below.
            # NOTE (phase D): the expected-growth shading that used to multiply this budget
            # now sits on the VALUATION anchor in market/clearing.py. A budget is what the
            # household can pay; what it is willing to pay for a particular dwelling — and
            # how much of the expected appreciation it capitalises — belongs to the bid, and
            # putting it here meant the index cap in clearing threw it away (model-spec §5c).
            budget = limit * shade_draw[i] * own_vs_rent * zone_cfg.location_premium
            can_buy = budget >= 0.6 * median_price  # cheapest habitable segment [guess]
            if wants_to_buy and can_buy:
                intents.append(
                    MakeOffer(
                        agent_id=hh.id,
                        zone=hh.zone,
                        budget=budget,
                        cash=cash_price(hh, itp, cfg.market.buyer_fees) >= budget,
                        first_time=first_time,
                        guaranteed=guaranteed,
                    )
                )
                continue

            if hh.status is HouseholdStatus.SEEKER:
                max_rent = search_burden(hh) * hh.income / 12.0
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
        return intents

    def _rent_subsidy(self, state: WorldState, hh) -> float:
        pol = state.config.policy
        if pol.rent_subsidy_month <= 0.0:
            return 0.0
        # eligibility fixed per household by its seeded draw: decide() stays pure and the
        # run stays reproducible (a salted hash() would not be — see HouseholdState)
        return (
            pol.rent_subsidy_month if hh.eligibility_draw < pol.rent_subsidy_eligible_share else 0.0
        )
