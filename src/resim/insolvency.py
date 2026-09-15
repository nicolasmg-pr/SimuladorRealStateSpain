"""Income risk, arrears, statutory foreclosure and bank-owned stock (model-spec §6c).

Before this module the budget constraint did not bind: `engine._household_flows` wrote
`wealth = max(0, wealth - payment)`, so a household that could not pay simply had the
shortfall absorbed. Nothing defaulted and no dwelling ever returned to the market against
its owner's will — which is why the 2008-13 hold-out could not be run at all.

The chain is, in order:

    employment status  ->  arrears  ->  statutory foreclosure  ->  bank REO

The aggregate unemployment rate is an EXOGENOUS path (model-spec §14), on the same footing
as the euríbor. Everything downstream of it is endogenous: which household loses its income,
whether that household can still service its mortgage, when the statute lets the lender
terminate, and what the repossessed dwelling does to supply.

Timing is a statute rather than an estimate — Ley 5/2019 art. 24 for contracts from June
2019, LEC art. 693 (Ley 1/2013) for the regime that governs the hold-out. The one element
with no primary source is the judicial phase, which is why it is a swept range
(`InsolvencyConfig.judicial_lag_range`) and never a reported magnitude.

The engine is still the only writer of state: these functions are called from step 8b of the
tick and mutate what the engine hands them, in one place, after clearing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .agents.bank import NET_INCOME_FACTOR
from .config import ZoneType
from .market.clearing import loss_averse_ask, seller_reserve
from .market.stock import BANK_ID, Tenure
from .state import HouseholdState, HouseholdStatus, SaleListing, WorldState

# Ley 5/2019 art. 25: default interest is the remuneratory rate + 3 percentage points, and
# it may NOT be capitalised into the principal — hence a separate arrears balance.
DEFAULT_INTEREST_SPREAD = 0.03
INSTALMENTS_PER_TICK = 3  # a quarter is three monthly instalments — the statute's unit


@dataclass
class TickInsolvency:
    """What happened this tick, for `metrics.snapshot` to read. Counts, not rates."""

    unemployed: int = 0
    mortgaged: int = 0
    in_arrears: int = 0
    forborne: int = 0
    deliveries: int = 0
    distressed_listings: int = 0
    daciones: int = 0
    residual_debt: float = 0.0
    reo_stock: int = 0
    reo_listed: int = 0


# --------------------------------------------------------------------- labour


def zone_unemployment_targets(cfg) -> dict[ZoneType, float]:
    """Per-zone target rate: the national path times the sourced urbanisation gradient.

    Renormalised on the zones' household weights so the model's aggregate is exactly the
    exogenous path — the gradient redistributes exposure, it does not add to it. Direction
    is the measured one and it is not the intuitive one: the tensioned metro is the LEAST
    exposed zone [Eurostat `lfst_r_urgau`, model-spec §6c.1].
    """
    lab = cfg.labour
    weights = {z.zone: z.household_share for z in cfg.zones}
    mult = dict(zip(ZoneType, lab.zone_multiplier, strict=True))
    mean = sum(weights.get(z, 0.0) * mult[z] for z in ZoneType)
    scale = 1.0 / mean if mean > 0 else 1.0
    return {z: min(0.95, max(0.0, lab.jobless_rate * mult[z] * scale)) for z in ZoneType}


def potential_income_uplift(cfg) -> float:
    """Scale from OBSERVED household income to the model's *potential* (employed) income.

    `PopulationConfig.income_median` is an EFF/ECV measurement, and those surveys measure a
    population that already contains unemployed households. Drawing potential income at that
    median and then applying an unemployment path on top subtracts the same loss twice: the
    model's realised income distribution came out ≈3% below its own calibration target
    (measured: realised mean 0.970 of potential, median 0.964).

    The correction is arithmetic, not a fit. With a constant exit hazard the age distribution
    of ongoing spells is geometric, so the expected replacement ratio at the median income is

        r̄ = P(age < 2)·r₁ + P(2 ≤ age < benefit_max)·r₂ + P(age ≥ benefit_max)·r_floor

    each ratio capped at the statutory maximum, and the uplift is 1 / (1 − u·(1 − r̄)).
    At the baseline (u = 5.28%, f = 0.25) that is 1.034.

    A test asserts the realised median lands back on the configured one, which is what makes
    this a correction rather than a free parameter.
    """
    lab = cfg.labour
    u = lab.jobless_rate
    if u <= 0.0:
        return 1.0
    f = lab.exit_hazard
    median = cfg.population.income_median
    cap = lab.benefit_cap_iprem * lab.iprem_prorrata * lab.iprem_annual
    r_early = min(lab.replacement_initial * median, cap) / median
    r_late = min(lab.replacement_later * median, cap) / median
    r_floor = lab.assistance_floor_iprem * lab.iprem_annual / median

    p_early = 1.0 - (1.0 - f) ** lab.replacement_switch_ticks
    p_exhausted = (1.0 - f) ** lab.benefit_max_ticks
    p_late = max(0.0, 1.0 - p_early - p_exhausted)
    r_bar = p_early * r_early + p_late * r_late + p_exhausted * r_floor
    return 1.0 / max(1e-6, 1.0 - u * (1.0 - r_bar))


def _incidence_weights(incomes: np.ndarray, relative_risk: float) -> np.ndarray:
    """Relative job-loss risk by income tercile, normalised to mean 1 over those passed.

    Bottom tercile carries sqrt(rr), top 1/sqrt(rr), so the bottom/top ratio is exactly the
    measured relative risk. REDUCED FORM: the gradient is measured on education (ISCED 0-2
    against 5-8) and applied over income, because the model has income and not schooling.
    """
    if len(incomes) == 0:
        return incomes
    root = float(np.sqrt(relative_risk))
    lo, hi = np.quantile(incomes, [1 / 3, 2 / 3])
    w = np.ones_like(incomes, dtype=float)
    w[incomes <= lo] = root
    w[incomes >= hi] = 1.0 / root
    mean = float(w.mean())
    return w / mean if mean > 0 else w


def update_employment(state: WorldState, rng: np.random.Generator) -> int:
    """Move households in and out of unemployment so each zone tracks its exogenous rate.

    The exit hazard is fixed (derived from the long-term-unemployment share); the separation
    hazard is then whatever the flow identity requires:

        u' = (1 - f)·u + s·(1 - u)   =>   s = (u* - (1 - f)·u) / (1 - u)

    so the model never invents an aggregate labour-market story. It only decides whose
    mortgage is at risk.
    """
    cfg = state.config
    lab = cfg.labour
    targets = zone_unemployment_targets(cfg)
    f = lab.exit_hazard

    by_zone: dict[ZoneType, list[HouseholdState]] = {z: [] for z in ZoneType}
    for hh in state.households.values():
        by_zone[hh.zone].append(hh)

    unemployed_total = 0
    for zone, members in by_zone.items():
        if not members:
            continue
        unemployed = [h for h in members if not h.employed]
        employed = [h for h in members if h.employed]
        u_now = len(unemployed) / len(members)
        target = targets[zone]

        # exits first: a spell that ends this tick frees the household before new entries are
        # drawn, which is the order the flow identity above assumes
        for hh in unemployed:
            if rng.random() < f:
                hh.employed = True
                hh.unemployed_ticks = 0
            else:
                hh.unemployed_ticks += 1

        s = (target - (1.0 - f) * u_now) / max(1e-9, 1.0 - u_now)
        s = float(min(1.0, max(0.0, s)))
        if s > 0.0 and employed:
            incomes = np.array([h.income for h in employed])
            weights = _incidence_weights(incomes, lab.incidence_relative_risk)
            draws = rng.random(len(employed))
            for hh, w, d in zip(employed, weights, draws, strict=True):
                if d < min(1.0, s * float(w)):
                    hh.employed = False
                    hh.unemployed_ticks = 0

        unemployed_total += sum(1 for h in members if not h.employed)
    return unemployed_total


def effective_income(hh: HouseholdState, cfg) -> float:
    """Income actually received this tick, €/yr.

    Employed: the household's income. Unemployed: the contributory benefit (70% of the base
    for the first 180 days, 60% after, capped at 175% of IPREM) while entitlement lasts, then
    the assistance floor of 80% of IPREM [LGSS arts. 269-270].
    """
    if hh.employed:
        return hh.income
    lab = cfg.labour
    if hh.unemployed_ticks >= lab.benefit_max_ticks:
        return lab.assistance_floor_iprem * lab.iprem_annual
    rate = (
        lab.replacement_initial
        if hh.unemployed_ticks < lab.replacement_switch_ticks
        else lab.replacement_later
    )
    cap = lab.benefit_cap_iprem * lab.iprem_prorrata * lab.iprem_annual
    return min(rate * hh.income, cap)


# -------------------------------------------------------------------- arrears


def _trigger_instalments(hh: HouseholdState, cfg) -> int:
    """Unpaid instalments at which the lender may terminate early — from the statute.

    Ley 5/2019 art. 24: 12 instalments (or 3% of the principal granted) in the first half of
    the loan's life, 15 (or 7%) in the second. Ley 1/2013 (LEC art. 693), which governs the
    2008-13 hold-out: 3. The regime is a config switch because the hold-out and the
    calibration window are legally different worlds — this alone moves the lag by ~3 quarters
    and is not something anyone fits.
    """
    ins = cfg.insolvency
    if ins.foreclosure_regime == "ley1_2013":
        return ins.trigger_instalments_legacy
    n_total = max(1, cfg.credit.term_years * 4)
    elapsed = n_total - hh.mortgage_ticks_left
    first_half = elapsed < n_total / 2
    return ins.trigger_instalments_first_half if first_half else ins.trigger_instalments_second_half


def service_mortgage(
    hh: HouseholdState,
    state: WorldState,
    income_eff: float,
    saving: float,
    median_income: float,
) -> bool:
    """Amortise, or fall into arrears. Returns True if the quarter was paid.

    The budget: the household protects an essential-consumption floor (INE's poverty
    threshold, §6c.2), and everything it spends above that floor is compressible before the
    mortgage goes unpaid. Savings are drawn on first, so a solvent household's wealth path is
    exactly what it was before this module existed.

    A missed quarter is three unpaid monthly instalments — the statute counts instalments,
    so the model does too. The principal is NOT amortised in a missed quarter and default
    interest accrues on a separate balance, because Ley 5/2019 art. 25 forbids capitalising
    it into the principal.
    """
    cfg = state.config
    ins = cfg.insolvency
    rate = state.macro.mortgage_rate / 4.0

    if hh.forbearance_ticks_left > 0:
        # Código de Buenas Prácticas grace period: capital amortisation suspended, interest
        # at euríbor − 0.10pp, arrears frozen rather than cured (§5d.2). The loan still
        # counts as doubtful, which is what the BdE's own classification did to restructured
        # mortgages and a large part of why the ratio stayed high after deliveries peaked.
        grace_rate = max(0.0, (cfg.credit.euribor - ins.forbearance_rate_discount) / 4.0)
        payment = hh.mortgage_balance * grace_rate
        consumption = NET_INCOME_FACTOR * income_eff / 4.0 - saving
        compressible = max(0.0, consumption - ins.essential_share * median_income / 4.0)
        if hh.wealth + compressible + 1e-9 < payment:
            # even interest-only is out of reach: the plan has failed, which the law
            # anticipates (the dación/quita route opens) and the foreclosure clock resumes
            hh.forbearance_ticks_left = 0
            hh.arrears_instalments += INSTALMENTS_PER_TICK
            hh.arrears_balance += payment
            return False
        hh.wealth -= min(hh.wealth, payment)
        hh.forbearance_ticks_left -= 1
        if hh.forbearance_ticks_left == 0:
            _exit_forbearance(hh, state)
        return True

    payment = hh.mortgage_payment
    essential = ins.essential_share * median_income / 4.0
    consumption = NET_INCOME_FACTOR * income_eff / 4.0 - saving
    compressible = max(0.0, consumption - essential)

    if hh.wealth + compressible + 1e-9 < payment:
        hh.arrears_instalments += INSTALMENTS_PER_TICK
        hh.arrears_balance += payment
        hh.arrears_balance *= 1.0 + rate + DEFAULT_INTEREST_SPREAD / 4.0
        return False

    from_wealth = min(hh.wealth, payment)
    hh.wealth -= from_wealth
    spare = (hh.wealth + compressible) - (payment - from_wealth)

    interest = hh.mortgage_balance * rate
    principal = max(0.0, min(hh.mortgage_balance, payment - interest))
    hh.mortgage_balance = max(0.0, hh.mortgage_balance - principal)
    hh.mortgage_ticks_left -= 1

    # cure: spare capacity clears arrears oldest-instalment-first, which is what stops the
    # statutory clock (art. 693.3 lets the debtor liberate the property by paying up)
    if hh.arrears_balance > 0.0 and spare > 0.0:
        instalment = payment / INSTALMENTS_PER_TICK
        cured = min(hh.arrears_balance, spare)
        hh.arrears_balance -= cured
        hh.arrears_instalments = max(0, hh.arrears_instalments - int(cured / max(1e-9, instalment)))
        if hh.arrears_balance <= 1e-6:
            hh.arrears_balance = 0.0
            hh.arrears_instalments = 0

    if hh.mortgage_balance <= 0.0:
        hh.mortgage_ticks_left = 0
        hh.mortgage_payment = 0.0
    return True


# ---------------------------------------------------------------- foreclosure


def _exit_forbearance(hh: HouseholdState, state: WorldState) -> None:
    """Grace over: the term is extended and the instalment recomputed (model-spec §5d.2).

    The law extends the loan to at most forty years from origination, which is what makes the
    restructuring a restructuring rather than a postponement — the household leaves with a
    smaller payment than it entered with.
    """
    cfg = state.config
    ins = cfg.insolvency
    if hh.mortgage_balance <= 0.0:
        hh.mortgage_ticks_left = 0
        hh.mortgage_payment = 0.0
        return
    elapsed = max(0, cfg.credit.term_years * 4 - hh.mortgage_ticks_left)
    remaining = max(4, min(hh.mortgage_ticks_left + 20, ins.forbearance_max_term_ticks - elapsed))
    r = state.macro.mortgage_rate / 4.0
    annuity = r / (1.0 - (1.0 + r) ** -remaining) if r > 0 else 1.0 / remaining
    hh.mortgage_ticks_left = remaining
    hh.mortgage_payment = hh.mortgage_balance * annuity


def offer_forbearance(
    hh: HouseholdState, state: WorldState, income_eff: float, rng: np.random.Generator
) -> bool:
    """The Código de Buenas Prácticas, applied at the first missed quarter (model-spec §5d.2).

    The law's own gates, in the law's order: the household must be behind but not yet past the
    auction announcement; it must be inside the **umbral de exclusión** — income at most three
    times the annual IPREM on fourteen payments *and* an instalment above half its net income,
    which is a poverty gate rather than a distress gate; the restructured payment must not
    exceed 50% of household income (otherwise the plan is refused and the dación route opens);
    one restructuring per loan.
    Five years of grace where the household has lost its income, two otherwise — the model's
    proxy for "the mortgage effort rose by half or more", and declared as a proxy.

    Take-up is the reduced-form leg: the CBP reached roughly a fifth of the distressed flow.
    """
    ins = state.config.insolvency
    if hh.forbearance_used or hh.forbearance_ticks_left > 0:
        return False
    if hh.mortgage_ticks_left <= 0 or hh.arrears_instalments <= 0:
        return False
    if hh.delivery_tick is not None:  # the auction is on the way: too late, by statute
        return False
    # the umbral de exclusión, both legs, in the law's own terms
    if income_eff > ins.forbearance_income_limit_iprem * ins.iprem_annual_14:
        return False
    net_quarterly = NET_INCOME_FACTOR * income_eff / 4.0
    if hh.mortgage_payment <= ins.forbearance_burden_threshold * net_quarterly:
        return False
    grace_rate = max(0.0, (state.config.credit.euribor - ins.forbearance_rate_discount) / 4.0)
    restructured = hh.mortgage_balance * grace_rate
    if restructured > ins.forbearance_viability_share * income_eff / 4.0:
        return False  # the law's viability test, failed
    # ONE draw per household, taken the first quarter it is eligible, not one per tick.
    # The law describes a single application answered within a month, and a per-tick hazard
    # compounds into something the scheme never reached: at 20% per quarter a household in
    # arrears for a year would take it up 59% of the time, against the CBP's roughly one in
    # five of the distressed flow.
    hh.forbearance_used = True
    if rng.random() >= ins.forbearance_takeup:
        return False
    hh.forbearance_ticks_left = (
        ins.forbearance_grace_severe_ticks if not hh.employed else ins.forbearance_grace_mild_ticks
    )
    # the clock stops where it is: arrears are frozen, not forgiven, and the statutory
    # foreclosure trigger cannot mature while the plan is running
    hh.foreclosure_tick = None
    hh.delivery_tick = None
    return True


def advance_foreclosure(hh: HouseholdState, state: WorldState, rng: np.random.Generator) -> None:
    """Move one household along the statutory clock. Does not deliver — `deliver` does.

    Trigger -> one-month demand (art. 24.1.c) -> route: voluntary now, or the judicial phase.
    Curing the arrears cancels the whole thing, which is what art. 693.3 allows.
    """
    ins = state.config.insolvency
    if hh.forbearance_ticks_left > 0:
        # a restructured loan is not on the foreclosure track while the plan holds
        hh.foreclosure_tick = None
        hh.delivery_tick = None
        return
    if hh.arrears_instalments <= 0:
        hh.foreclosure_tick = None
        hh.delivery_tick = None
        return
    if hh.mortgage_ticks_left <= 0 and hh.mortgage_balance <= 0.0:
        # the debt is gone — the household sold, or the loan matured. Nothing is left to
        # foreclose on, and the arrears go with it (the seller repaid out of the proceeds,
        # `clearing.settle`).
        hh.arrears_instalments = 0
        hh.arrears_balance = 0.0
        hh.foreclosure_tick = None
        hh.delivery_tick = None
        return
    if hh.foreclosure_tick is None:
        if hh.arrears_instalments >= _trigger_instalments(hh, state.config):
            hh.foreclosure_tick = state.tick + ins.demand_notice_ticks
        return
    if state.tick >= hh.foreclosure_tick and hh.delivery_tick is None:
        voluntary = rng.random() < ins.voluntary_delivery_share
        hh.delivery_tick = state.tick if voluntary else state.tick + ins.judicial_lag_ticks


def deliver(
    hh: HouseholdState, state: WorldState, rng: np.random.Generator, events: TickInsolvency
) -> None:
    """Possession: the dwelling goes to the bank, the household goes back to searching.

    Price is the statute's, not a parameter: for a debtor's habitual residence the award may
    not be approved below 70% of the auction value [LEC art. 670.4]. Any surplus over the
    debt belongs to the debtor. A dación extinguishes the debt; a judicial award does not —
    Spanish mortgage debt is recourse [LEC art. 579] — and the model carries that difference
    as the credit lockout rather than as a shadow balance it would never collect.
    """
    ins = state.config.insolvency
    unit_id = hh.unit_id
    if unit_id is None or unit_id not in state.stock.units:
        # nothing to take (the home was already sold): the debt follows the household
        hh.foreclosure_tick = None
        hh.delivery_tick = None
        hh.arrears_instalments = 0
        hh.arrears_balance = 0.0
        return
    unit = state.stock.units[unit_id]
    value = state.zones[unit.zone].price_index * unit.quality
    award = ins.award_share_of_value * value
    debt = hh.mortgage_balance + hh.arrears_balance

    # daciones are 0.397 of ALL deliveries and are a subset of the voluntary ones
    # (0.478), so conditional on a voluntary route the probability is 0.397/0.478
    voluntary = hh.delivery_tick == hh.foreclosure_tick
    p_dacion = min(1.0, ins.dacion_share_of_deliveries / max(1e-9, ins.voluntary_delivery_share))
    dacion = voluntary and rng.random() < p_dacion

    residual = 0.0 if dacion else max(0.0, debt - award)
    hh.wealth += max(0.0, award - debt)

    hh.mortgage_balance = 0.0
    hh.mortgage_payment = 0.0
    hh.mortgage_ticks_left = 0
    hh.arrears_instalments = 0
    hh.arrears_balance = 0.0
    hh.foreclosure_tick = None
    hh.delivery_tick = None
    hh.status = HouseholdStatus.SEEKER
    hh.unit_id = None
    hh.ticks_searching = 0
    hh.credit_lockout_ticks = ins.lockout_ticks

    state.sale_listings.pop(unit.id, None)
    state.rent_listings.pop(unit.id, None)
    unit.owner_id = BANK_ID
    unit.occupant_id = None
    unit.tenure = Tenure.VACANT
    unit.vacant_since = state.tick
    unit.rent = 0.0
    unit.withheld = False
    unit.last_sale_price = award

    events.deliveries += 1
    events.daciones += int(dacion)
    events.residual_debt += residual


def list_distressed(state: WorldState, hh: HouseholdState) -> bool:
    """A household facing foreclosure puts its home on the market before the lender takes it.

    This is the forced-sale channel phase C is for, and it is the ordinary Spanish outcome:
    possession is slow and expensive for both sides, so an owner under a credible threat and
    with equity sells first. Nearly half of all deliveries are voluntary [BdE Circular 1/2013],
    and this is the margin that produces them.

    The trigger is the STATUTORY threat, not the first missed instalment: the lender has
    demanded payment and warned of early termination (art. 24.1.c), so the household is
    choosing between selling and losing the home. Listing on the first missed quarter instead
    was measured and rejected — it put ~28 distressed listings in the market at all times in a
    calm baseline, moved the price level 9% and pushed price-to-income out of its §9 band. Most
    arrears spells cure (the exit hazard ends half of them inside three quarters), and a
    household that expects to cure does not sell its home.

    The reserve is the outstanding debt, not a discount off the ask: an owner cannot convey
    clear title for less than the loan. That is the negative-equity lock-in phase D derives
    in general (spec §7.7); here it is unavoidable, because a distressed sale is exactly the
    case where the constraint binds, and pricing it any other way would let the model sell a
    way out of insolvency that Spanish law does not allow.
    """
    if hh.unit_id is None or hh.unit_id in state.sale_listings:
        return False
    unit = state.stock.units.get(hh.unit_id)
    if unit is None or unit.owner_id != hh.id:
        return False
    # the ask is the ORDINARY seller's rule (agents/household.py): a distressed owner has no
    # reason to sticker its home differently. What is different is the floor — it is the debt,
    # not a discount off the ask — so the haste shows up as a sale at the reserve, or as no
    # sale at all in negative equity, rather than as a lower asking price dragging the index.
    zs = state.zones[unit.zone]
    value = (zs.valuation_index or zs.price_index) * unit.quality
    ask = loss_averse_ask(
        base_ask=value * (1.0 + zs.expected_price_growth) * (1.0 + state.config.market.ask_markup),
        paid=unit.last_sale_price,
        value=value,
        # a distressed owner is still an owner-occupier facing a nominal loss, and the
        # reserve below is what stops the loss aversion from blocking a forced sale outright
        alpha=state.config.market.loss_aversion_owner,
    )
    debt = hh.mortgage_balance + hh.arrears_balance
    # phase D made this the general rule (model-spec §5c.3): every seller's reserve is the
    # larger of what the loan requires and what the negotiation margin allows. A distressed
    # seller is no longer a special case — it is the ordinary rule with a large debt leg
    reserve = seller_reserve(
        ask=ask, debt=debt, discount=state.config.market.max_seller_discount_hi, cfg=state.config
    )
    state.sale_listings[unit.id] = SaleListing(
        unit_id=unit.id, ask=ask, reserve=reserve, distressed=True
    )
    return True


def withdraw_distressed(state: WorldState, hh: HouseholdState) -> None:
    """Arrears cured, threat gone: the home comes off the market again.

    Without this the forced-supply channel would ratchet — every spell that ever happened
    would leave a listing behind, and a transient labour shock would look like a permanent
    supply shift.
    """
    if hh.unit_id is None:
        return
    listing = state.sale_listings.get(hh.unit_id)
    if listing is not None and listing.distressed:
        del state.sale_listings[hh.unit_id]


def release_reo(state: WorldState, rng: np.random.Generator, events: TickInsolvency) -> None:
    """The bank sells what it took, at a markdown, a slice at a time.

    This is the bank-owned overhang of 2008-13, a real channel the model did not have. Both
    parameters are the block's weakest — the registered Sareb haircuts are against book
    value, not market price — so they are declared reduced form and swept in phase E.
    """
    ins = state.config.insolvency
    held = [
        u
        for u in state.stock.units.values()
        if u.owner_id == BANK_ID and u.id not in state.sale_listings
    ]
    events.reo_stock = sum(1 for u in state.stock.units.values() if u.owner_id == BANK_ID)
    if not held:
        return
    n = int(round(ins.reo_release_share * len(held)))
    if n <= 0:
        return
    # which units go out is drawn, not taken in stock order: stock order correlates with
    # creation date and would release the oldest repossessions first, every run
    chosen = rng.choice(len(held), size=n, replace=False)
    for i in chosen:
        unit = held[int(i)]
        zsu = state.zones[unit.zone]
        ask = (zsu.valuation_index or zsu.price_index) * unit.quality * (1.0 - ins.reo_discount)
        # the bank took the dwelling at the statutory 70% of auction value and has no loan
        # against it, so only the negotiation-margin leg of the reserve binds
        state.sale_listings[unit.id] = SaleListing(
            unit_id=unit.id,
            ask=ask,
            reserve=seller_reserve(
                ask=ask,
                debt=0.0,
                discount=state.config.market.max_seller_discount_hi,
                cfg=state.config,
            ),
        )
        events.reo_listed += 1
