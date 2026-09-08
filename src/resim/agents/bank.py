"""Bank — sets the credit constraint that turns willingness-to-pay into ability-to-pay.

Approves or refuses mortgages against LTV/DSTI caps and the current rate. Credit
availability usually moves prices more than income does; keep it a first-class actor.

Rules (model-spec §3, bank dossier §3/§6):
  - LTV ≤ 0.80 of price (bank practice, no legal cap; 24% of ops bunch at 0.80),
    lifted toward 1.0 for guarantee-eligible first-time buyers (avales ICO).
  - payment + debts ≤ max_dsti of NET income (net ≈ 0.78 × gross — guess).
  - Offered rate follows euríbor + spread with slow, incomplete pass-through
    (~32% of a shock after 16 months, BdE DO 2312).
Rationing happens entirely through these caps; explicit rejection-rate levels by
profile are unpublished (bank dossier §7.1) and not modelled.
"""

from __future__ import annotations

import numpy as np

from ..config import CreditConfig
from ..state import HouseholdState, WorldState
from .base import Intent, SetCredit

NET_INCOME_FACTOR = 0.78  # net/gross household income [guess]


def quarterly_rate(annual: float) -> float:
    return annual / 4.0


def max_principal(income: float, rate_yr: float, credit: CreditConfig) -> float:
    """Largest loan the DSTI cap allows at the offered rate (annuity formula)."""
    payment_cap = credit.max_dsti * income * NET_INCOME_FACTOR / 4.0  # €/quarter
    r = quarterly_rate(rate_yr)
    n = credit.term_years * 4
    if r <= 0:
        return payment_cap * n
    annuity = r / (1.0 - (1.0 + r) ** -n)
    return payment_cap / annuity


def max_price(
    hh: HouseholdState,
    rate_yr: float,
    credit: CreditConfig,
    itp: float,
    fees: float,
    ltv_boost: float = 0.0,
) -> float:
    """Highest price this household can close at, given wealth, income and the caps.

    Two binding constraints (model-spec §5):
      equity:  price·(1 − ltv + itp + fees) ≤ wealth   (down payment + taxes upfront)
      dsti:    financed part ≤ max_principal            (income services the loan)

    `ltv_boost` is the state-guarantee lift (PolicyConfig.guarantee_ltv_boost) and must be
    passed by the caller for guarantee-eligible buyers only — 0.0 is the unassisted screen.
    """
    ltv = min(1.0, credit.max_ltv + ltv_boost)
    principal_cap = max_principal(hh.income, rate_yr, credit)
    equity_bound = hh.wealth / max(1e-9, 1.0 - ltv + itp + fees)
    cashflow_bound = (hh.wealth + principal_cap) / (1.0 + itp + fees)
    return max(0.0, min(equity_bound, cashflow_bound))


def cash_price(hh: HouseholdState, itp: float, fees: float) -> float:
    return hh.wealth / (1.0 + itp + fees)


def itp_wedge(base_rate: float, effective_rate: float) -> float:
    """Budget multiplier a cash buyer applies when the tax it faces moves off the zone rate.

    Households already carry ITP inside `max_price`; the two aggregate cash buyers (large
    investor, non-resident overlay) bid at observed market levels that embed the baseline
    rate, so for them only the CHANGE is a wedge: (1 + base) / (1 + effective). Equal to 1
    when nothing changed. Spain taxes by buyer type in practice — Cataluña's 20% TPO on
    whole-building and gran-tenedor purchases, the stalled 100% surcharge on non-EU buyers —
    which is why the effective rate is buyer-specific [transaction-tax.md §5].
    """
    return (1.0 + base_rate) / (1.0 + effective_rate)


def loan_terms(
    price: float,
    hh: HouseholdState,
    rate_yr: float,
    credit: CreditConfig,
    itp: float,
    fees: float,
    ltv_boost: float = 0.0,
) -> tuple[float, float, int]:
    """(principal, quarterly payment, n quarters) for a closed purchase."""
    ltv = min(1.0, credit.max_ltv + ltv_boost)
    upfront = price * (itp + fees)
    equity = max(0.0, min(hh.wealth - upfront, price))
    principal = min(price - equity, ltv * price)
    principal = max(0.0, principal)
    r = quarterly_rate(rate_yr)
    n = credit.term_years * 4
    payment = principal * (r / (1.0 - (1.0 + r) ** -n)) if r > 0 else principal / n
    return principal, payment, n


class Bank:
    """Publishes the credit menu; the engine applies the screen per offer."""

    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        credit = state.config.credit
        macro = state.macro
        target = credit.euribor + credit.spread
        # partial adjustment toward the target rate (slow pass-through, BdE DO 2312)
        new_rate = macro.mortgage_rate + credit.pass_through * (target - macro.mortgage_rate)
        return [SetCredit(agent_id=self.id, mortgage_rate=new_rate)]
