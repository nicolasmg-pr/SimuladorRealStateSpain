"""Insolvency block: income risk, arrears, statutory foreclosure, bank REO (model-spec §6c).

These are mechanism tests, not moment tests — the moments live in `test_validation.py`
(target 15). What is checked here is that the parts do what the statute and the flow
identity say they do, because that is what makes the block evidence rather than machinery:

  - the labour path is tracked, not invented;
  - the incidence gradient is the measured one;
  - the arrears trigger is the budget constraint, and a solvent household's wealth path is
    untouched by this module existing;
  - the foreclosure clock is the statute's, and switching regimes moves it as the statute
    says it should;
  - possession conserves the stock and does not leave a household owning nothing while
    still carrying a mortgage.
"""

from dataclasses import replace

import numpy as np
import pytest

from resim import insolvency
from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.market.stock import BANK_ID, Tenure
from resim.scenario import CreditCrunch, LabourShock, Scenario
from resim.state import HouseholdStatus

TICKS = 24


def run(seed: int = 3, ticks: int = TICKS, interventions=(), **cfg_changes):
    cfg = SimConfig.baseline(seed=seed, ticks=ticks)
    if cfg_changes:
        cfg = replace(cfg, **cfg_changes)
    return Engine(Scenario("t", cfg, tuple(interventions))).run()


# ------------------------------------------------------------------ labour


def test_model_tracks_the_exogenous_jobless_path():
    """The aggregate is data. Only incidence is the model's business (§6c.1)."""
    state = run(seed=5)
    target = state.config.labour.jobless_rate
    realised = [r["unemployment_rate"] for r in state.history[4:]]
    assert abs(float(np.mean(realised)) - target) < 0.01


def test_labour_shock_moves_the_path_and_nothing_else_sets_it():
    """A different path in, a different path out — with no free parameter in between."""
    calm = run(seed=5)
    bust = run(seed=5, interventions=(LabourShock(start_tick=6, rate=0.15),))
    assert abs(bust.history[-1]["unemployment_rate"] - 0.15) < 0.02
    assert calm.history[-1]["unemployment_rate"] < 0.08


def test_zone_targets_renormalise_to_the_national_path():
    """The urbanisation gradient redistributes exposure; it must not add to it."""
    cfg = SimConfig.baseline(seed=1, ticks=4)
    targets = insolvency.zone_unemployment_targets(cfg)
    weights = {z.zone: z.household_share for z in cfg.zones}
    national = sum(weights[z] * targets[z] for z in ZoneType)
    assert national == pytest.approx(cfg.labour.jobless_rate, rel=1e-9)
    # and the measured direction: the metro is the LEAST exposed zone [Eurostat lfst_r_urgau]
    assert targets[ZoneType.TENSIONED] < targets[ZoneType.RURAL]
    assert targets[ZoneType.TENSIONED] < targets[ZoneType.SECONDARY]


def test_incidence_gradient_is_the_measured_relative_risk():
    """Bottom vs top income tercile must carry exactly the sourced 2.2 relative risk."""
    incomes = np.arange(1.0, 301.0)
    w = insolvency._incidence_weights(incomes, 2.2)
    assert w[:100].mean() / w[-100:].mean() == pytest.approx(2.2, rel=1e-9)
    assert w.mean() == pytest.approx(1.0, rel=1e-9)


def test_benefit_follows_the_statute():
    """LGSS art. 270: 70% for the first 180 days, 60% after, then the assistance floor."""
    cfg = SimConfig.baseline(seed=1, ticks=4)
    lab = cfg.labour
    state = run(seed=1, ticks=4)
    hh = next(iter(state.households.values()))
    hh.income = 30_000.0
    hh.employed = False

    cap = lab.benefit_cap_iprem * lab.iprem_prorrata * lab.iprem_annual  # €14,700/yr
    hh.unemployed_ticks = 0
    assert insolvency.effective_income(hh, cfg) == pytest.approx(min(0.70 * 30_000.0, cap))
    hh.unemployed_ticks = 3
    assert insolvency.effective_income(hh, cfg) == pytest.approx(min(0.60 * 30_000.0, cap))
    # and the cap is what binds at a median Spanish income: 70% of €36,100 is €25,270/yr,
    # the statutory maximum €14,700 — the single-earner household loses 59% of its income,
    # not 30%, which is why arrears in this model come from job loss and nothing else
    assert cap < 0.70 * 36_100.0
    hh.unemployed_ticks = lab.benefit_max_ticks
    assert insolvency.effective_income(hh, cfg) == pytest.approx(
        lab.assistance_floor_iprem * lab.iprem_annual
    )
    # and the cap bites on a high earner, at 175% of IPREM
    hh.income, hh.unemployed_ticks = 200_000.0, 0
    assert insolvency.effective_income(hh, cfg) == pytest.approx(cap)


# ----------------------------------------------------------------- arrears


def test_a_solvent_household_pays_and_its_wealth_path_is_the_old_one():
    """The module must not move a household that was never in trouble.

    Before phase C the payment came out of wealth. For any household that can afford it,
    that is still exactly what happens — the compressible-consumption margin is a *rescue*,
    not a new income source, so it must not appear in a solvent household's balance.
    """
    state = run(seed=2, ticks=8)
    hh = next(
        h
        for h in state.households.values()
        if h.mortgage_ticks_left > 0 and h.wealth > 5 * h.mortgage_payment and h.employed
    )
    before_wealth, before_balance = hh.wealth, hh.mortgage_balance
    paid = insolvency.service_mortgage(hh, state, hh.income, saving=0.0, median_income=36_100.0)
    assert paid
    assert hh.wealth == pytest.approx(before_wealth - hh.mortgage_payment)
    assert hh.mortgage_balance < before_balance
    assert hh.arrears_instalments == 0


def test_income_loss_with_no_buffer_produces_arrears_in_instalments():
    """The statute counts monthly instalments, so the model does too — three per quarter."""
    state = run(seed=2, ticks=8)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.wealth = 0.0
    hh.employed = False
    hh.unemployed_ticks = 8  # benefit exhausted: assistance floor only
    income_eff = insolvency.effective_income(hh, state.config)
    paid = insolvency.service_mortgage(hh, state, income_eff, 0.0, median_income=36_100.0)
    assert not paid
    assert hh.arrears_instalments == 3
    assert hh.arrears_balance > hh.mortgage_payment  # default interest accrued


def test_arrears_are_cured_when_capacity_returns():
    """Art. 693.3: paying up liberates the property and stops the clock."""
    state = run(seed=2, ticks=8)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.arrears_instalments = 6
    hh.arrears_balance = 2 * hh.mortgage_payment
    hh.wealth = 50 * hh.mortgage_payment
    insolvency.service_mortgage(hh, state, hh.income, 0.0, median_income=36_100.0)
    assert hh.arrears_instalments == 0
    assert hh.arrears_balance == 0.0
    insolvency.advance_foreclosure(hh, state, np.random.default_rng(0))
    assert hh.foreclosure_tick is None


# ------------------------------------------------------------- foreclosure


def test_the_trigger_is_the_statute_not_a_parameter():
    """Ley 5/2019 art. 24 vs LEC art. 693 (Ley 1/2013): 12 instalments against 3."""
    state = run(seed=2, ticks=8)
    rng = np.random.default_rng(0)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)

    hh.arrears_instalments = 9  # three quarters unpaid: short of art. 24's twelve
    insolvency.advance_foreclosure(hh, state, rng)
    assert hh.foreclosure_tick is None

    hh.arrears_instalments = 12
    insolvency.advance_foreclosure(hh, state, rng)
    assert hh.foreclosure_tick == state.tick + state.config.insolvency.demand_notice_ticks

    # the pre-2019 regime, which governs the hold-out, terminates at three
    legacy = replace(
        state.config, insolvency=replace(state.config.insolvency, foreclosure_regime="ley1_2013")
    )
    state.config = legacy
    other = next(
        h for h in state.households.values() if h.mortgage_ticks_left > 0 and h.id != hh.id
    )
    other.arrears_instalments = 3
    insolvency.advance_foreclosure(other, state, rng)
    assert other.foreclosure_tick is not None


def test_possession_transfers_the_dwelling_and_frees_the_household():
    """The bank ends up owning it; the household ends up searching, and locked out."""
    state = run(seed=2, ticks=8)
    hh = next(
        h
        for h in state.households.values()
        if h.status is HouseholdStatus.OWNER and h.unit_id is not None
    )
    unit_id = hh.unit_id
    hh.mortgage_balance = max(hh.mortgage_balance, 50_000.0)
    hh.arrears_instalments = 15
    hh.foreclosure_tick = state.tick
    hh.delivery_tick = state.tick + 10  # judicial route
    events = insolvency.TickInsolvency()
    n_units = len(state.stock)

    insolvency.deliver(hh, state, np.random.default_rng(0), events)

    assert len(state.stock) == n_units  # conservation: possession creates no dwelling
    unit = state.stock.units[unit_id]
    assert unit.owner_id == BANK_ID
    assert unit.tenure is Tenure.VACANT
    assert hh.status is HouseholdStatus.SEEKER
    assert hh.unit_id is None
    assert hh.mortgage_balance == 0.0 and hh.arrears_instalments == 0
    assert hh.credit_lockout_ticks == state.config.insolvency.lockout_ticks
    assert events.deliveries == 1


def test_a_locked_out_household_cannot_borrow_again():
    """LOPDGDD art. 20.1.d as a behavioural horizon: no mortgage while the flag stands."""
    state = run(seed=4, ticks=20, interventions=(LabourShock(start_tick=2, rate=0.25),))
    locked = [h for h in state.households.values() if h.credit_lockout_ticks > 0]
    assert locked, "the bust leg must produce at least one foreclosed household"
    assert all(h.mortgage_ticks_left == 0 for h in locked)


def test_repossessed_stock_is_relisted_not_absorbed():
    """The bank-owned overhang must reach the market — that is the whole point of REO."""
    state = run(seed=4, ticks=30, interventions=(LabourShock(start_tick=2, rate=0.25),))
    assert sum(r["foreclosures"] for r in state.history) > 0
    listed_reo = [
        u
        for u in state.stock.units.values()
        if u.owner_id == BANK_ID and u.id in state.sale_listings
    ]
    reo_total = [u for u in state.stock.units.values() if u.owner_id == BANK_ID]
    assert not reo_total or listed_reo, "REO was taken but never offered for sale"
    for unit in listed_reo:
        index = state.zones[unit.zone].price_index * unit.quality
        assert state.sale_listings[unit.id].ask < index  # sold at a markdown


# ----------------------------------------------------------------- levers


def test_credit_crunch_tightens_the_three_caps_together():
    """2008–13 was not one dial: LTV, DSTI and the spread moved at once (§8)."""
    cfg = SimConfig.baseline(seed=1, ticks=4)
    tightened = CreditCrunch(
        start_tick=0, ltv_delta=-0.15, dsti_delta=-0.07, spread_delta=0.02
    ).apply(cfg)
    assert tightened.credit.max_ltv == pytest.approx(cfg.credit.max_ltv - 0.15)
    assert tightened.credit.max_dsti == pytest.approx(cfg.credit.max_dsti - 0.07)
    assert tightened.credit.spread == pytest.approx(cfg.credit.spread + 0.02)
    # and the baseline is untouched — interventions never mutate
    assert cfg.credit.max_ltv == 0.80


def test_insolvency_does_not_break_reproducibility():
    """The block draws from its own stream; two runs of one seed stay identical."""
    from resim import metrics

    a = run(seed=11, ticks=12, interventions=(LabourShock(start_tick=3, rate=0.12),))
    b = run(seed=11, ticks=12, interventions=(LabourShock(start_tick=3, rate=0.12),))
    # via the frame, not the dicts: a tick with no deliveries reports NaN shares, and
    # NaN != NaN would make a dict comparison fail on identical runs
    import pandas as pd

    pd.testing.assert_frame_equal(metrics.to_frame(a), metrics.to_frame(b))
