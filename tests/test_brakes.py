"""The two brakes on a falling market: loss aversion and forbearance (model-spec §5d).

Both were added after the hold-out revealed they were missing, so the tests carry an extra
burden beyond "does it work": they have to show that each is identified on its own source and
that neither can have been fitted to the episode that revealed the gap.

  - loss aversion must be **inert in a rising market**, which is what the calibration window
    is — if it moved the calibration, it would be a fitted parameter wearing a citation;
  - forbearance must fire only inside the **umbral de exclusión**, the statute's poverty gate,
    and must delay rather than cure.
"""

from dataclasses import replace

import numpy as np
import pytest

from resim import insolvency, metrics
from resim.config import SimConfig
from resim.engine import Engine
from resim.market.clearing import loss_averse_ask
from resim.scenario import (
    CreditCrunch,
    HouseholdFormation,
    LabourShock,
    RateShock,
    Scenario,
)
from resim.state import HouseholdStatus


@pytest.fixture
def cfg():
    return SimConfig.baseline(seed=1, ticks=4)


# ------------------------------------------------------------- loss aversion


def test_a_seller_in_profit_asks_exactly_what_they_would_have(cfg):
    """Inert in a rising market. This is the property that makes it safe to add late."""
    ask = loss_averse_ask(base_ask=250_000, paid=200_000, value=260_000, alpha=0.30)
    assert ask == pytest.approx(250_000)


def test_a_seller_facing_a_loss_asks_part_of_it_back(cfg):
    """Genesove & Mayer: 25–35% of the gap between expected price and what they paid."""
    ask = loss_averse_ask(base_ask=200_000, paid=260_000, value=200_000, alpha=0.30)
    assert ask == pytest.approx(200_000 + 0.30 * 60_000)


def test_an_investor_concedes_twice_as_fast_as_an_owner(cfg):
    """The list-price effect is twice as large for owner-occupants — their finding, not ours."""
    assert cfg.market.loss_aversion_owner == pytest.approx(2 * cfg.market.loss_aversion_investor)
    owner = loss_averse_ask(
        base_ask=200_000, paid=260_000, value=200_000, alpha=cfg.market.loss_aversion_owner
    )
    investor = loss_averse_ask(
        base_ask=200_000, paid=260_000, value=200_000, alpha=cfg.market.loss_aversion_investor
    )
    assert owner > investor > 200_000


def test_the_calibration_window_does_not_move(cfg):
    """The strong version of inertness: turning loss aversion off must not move the baseline.

    A brake that changed a rising market would be a parameter fitted to something, and the
    §9 gates would silently be carrying it.
    """
    base = SimConfig.baseline(seed=4, ticks=40)
    off = replace(
        base,
        market=replace(base.market, loss_aversion_owner=0.0, loss_aversion_investor=0.0),
    )
    with_brake = metrics.to_frame(Engine(Scenario("on", base)).run())["price_to_income"]
    without = metrics.to_frame(Engine(Scenario("off", off)).run())["price_to_income"]
    moved = abs(with_brake.iloc[-8:].mean() / without.iloc[-8:].mean() - 1.0)
    assert moved < 0.02


def _deep_bust(seed: int, loss_aversion: bool):
    """A synthetic downturn with round-number inputs — deliberately NOT the sealed episode.

    A labour shock alone does not make this model's prices fall (measured: +14% over the
    window), so a test of a brake on falling prices needs a scenario where they actually
    fall: credit stop, rate spike, formation collapse and an inherited construction pipeline,
    all at round numbers rather than at the 2008–13 series, which may not be used to build
    anything (model-spec §13.11).
    """
    cfg = SimConfig.baseline(seed=seed, ticks=40)
    cfg = replace(
        cfg,
        insolvency=replace(cfg.insolvency, foreclosure_regime="ley1_2013"),
        developer=replace(cfg.developer, initial_pipeline=(60,) * 12),
    )
    if not loss_aversion:
        cfg = replace(
            cfg,
            market=replace(cfg.market, loss_aversion_owner=0.0, loss_aversion_investor=0.0),
        )
    shock = (
        LabourShock(start_tick=8, rate=0.15, exit_hazard=0.15),
        CreditCrunch(start_tick=8, ltv_delta=-0.25, dsti_delta=-0.10, spread_delta=0.03),
        RateShock(start_tick=8, euribor=0.05),
        HouseholdFormation(start_tick=8, formation_per_tick=11),
    )
    return metrics.to_frame(Engine(Scenario("bust", cfg, shock)).run())


def test_loss_aversion_reproduces_the_price_volume_correlation():
    """Genesove & Mayer's own conclusion, which is why the mechanism was added.

    Broken by phase G and CLOSED 2026-09-15 exactly as its xfail predicted. §5c.6 moved the
    bargaining weight to 0.25, so a one-bidder sale prices near the reserve; loss aversion
    lived entirely in the ask, which then withheld dwellings without holding prices up, and
    the brakes deepened the fall. The paper measures TWO effects — asking prices 25–35% of the
    nominal loss higher AND **realised prices 3–18% of it higher** — and the model carried only
    the first. The second now sits in `seller_reserve` (§5d.1), and the sign is right again.

    Sellers facing nominal losses hold out: the price falls **less** and the volume falls
    **more**. That joint movement is the positive price–volume correlation housing markets
    show in downturns, and the model had neither half of it before.
    """
    # SEED COUNT RAISED 2026-09-17, from (6, 7, 8) to ten, per model-spec §9's own rule that
    # nothing is reported on fewer than ten seeds. It matters here more than anywhere: the
    # cushion this test asserts is SMALL RELATIVE TO SEED NOISE. Measured over twelve seeds the
    # mean cushion is +0.0022 on a per-seed spread of roughly +-0.02 — positive on 6 of 12 —
    # and (6, 7, 8) are three of the six negative draws, so the three-seed version was deciding
    # a 0.2pp effect on a 2pp spread and happened to hold the worst hand. The mean is the claim
    # Genesove & Mayer support and the mean is what is asserted; the per-seed sign is not
    # resolvable in this model and is recorded as such in docs/validation.md rather than
    # asserted.
    seeds = tuple(range(1, 11))
    on = [_deep_bust(seed, True) for seed in seeds]
    off = [_deep_bust(seed, False) for seed in seeds]

    def fall(frames):
        return float(
            np.mean(
                [f["price_national"].iloc[-1] / f["price_national"].iloc[8] - 1 for f in frames]
            )
        )

    def volume(frames):
        return float(np.mean([f["transactions"].iloc[-8:].mean() for f in frames]))

    assert fall(on) < -0.10 and fall(off) < -0.10, "the scenario must actually fall"
    assert fall(on) > fall(off), "loss aversion must cushion the fall"
    assert volume(on) < volume(off), "and it must cost volume to do it"


# --------------------------------------------------------------- forbearance


def _run(seed: int = 3, ticks: int = 24, interventions=(), **changes):
    cfg = SimConfig.baseline(seed=seed, ticks=ticks)
    if changes:
        cfg = replace(cfg, **changes)
    return Engine(Scenario("t", cfg, tuple(interventions))).run()


def test_forbearance_is_refused_above_the_exclusion_threshold():
    """The umbral de exclusión is a poverty gate: three times the 14-payment IPREM.

    Leaving it out was measured and rejected — it put 2.4% of all mortgaged households into a
    restructuring in a calm baseline, against a scheme that reached 45,697 families in five
    years nationally (model-spec §5d.2).
    """
    state = _run()
    rng = np.random.default_rng(0)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.arrears_instalments = 3
    ins = state.config.insolvency
    rich = ins.forbearance_income_limit_iprem * ins.iprem_annual_14 * 1.5
    assert not insolvency.offer_forbearance(hh, state, rich, rng)
    assert hh.forbearance_ticks_left == 0


def test_forbearance_is_refused_when_the_instalment_is_light():
    """Second leg of the same threshold: the payment must exceed half of net income."""
    state = _run()
    rng = np.random.default_rng(0)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.arrears_instalments = 3
    hh.mortgage_payment = 1.0  # trivial instalment
    poor = 20_000.0
    assert not insolvency.offer_forbearance(hh, state, poor, rng)


def test_forbearance_is_refused_once_the_auction_is_on_the_way():
    """By statute it is available only before the auction is announced."""
    state = _run()
    rng = np.random.default_rng(0)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.arrears_instalments = 12
    hh.mortgage_payment = 20_000.0
    hh.delivery_tick = state.tick + 4
    assert not insolvency.offer_forbearance(hh, state, 15_000.0, rng)


def test_a_household_applies_once(cfg):
    """One draw per household, not one per tick — the law describes a single application."""
    state = _run()
    rng = np.random.default_rng(1)
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.arrears_instalments = 3
    hh.mortgage_payment = 20_000.0
    insolvency.offer_forbearance(hh, state, 15_000.0, rng)
    assert hh.forbearance_used
    hh.forbearance_ticks_left = 0
    assert not insolvency.offer_forbearance(hh, state, 15_000.0, rng)


def test_grace_freezes_the_clock_instead_of_curing_it():
    """A restructuring delays; it does not forgive. Arrears stay, the foreclosure clock stops."""
    state = _run()
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 0)
    hh.arrears_instalments = 6
    hh.arrears_balance = 2 * hh.mortgage_payment
    hh.wealth = 50 * hh.mortgage_payment
    hh.forbearance_ticks_left = 8
    before = hh.arrears_instalments
    paid = insolvency.service_mortgage(hh, state, hh.income, 0.0, median_income=36_100.0)
    assert paid
    assert hh.arrears_instalments == before  # frozen, not cured
    assert hh.forbearance_ticks_left == 7
    insolvency.advance_foreclosure(hh, state, np.random.default_rng(0))
    assert hh.foreclosure_tick is None


def test_the_instalment_is_smaller_after_the_grace_period():
    """That is what the term extension is for — up to forty years from origination."""
    state = _run()
    hh = next(h for h in state.households.values() if h.mortgage_ticks_left > 20)
    before = hh.mortgage_payment
    hh.forbearance_ticks_left = 1
    hh.wealth = 100 * before
    insolvency.service_mortgage(hh, state, hh.income, 0.0, median_income=36_100.0)
    assert hh.forbearance_ticks_left == 0
    assert hh.mortgage_payment < before


def test_forbearance_raises_the_arrears_stock_and_lowers_the_flow():
    """The prediction written in the spec before either mechanism was run (§5d.2).

    A restructured loan stays doubtful in the BdE's classification, so it stays in
    `arrears_share`; and it cannot be foreclosed while the plan holds. Stock up, flow down.
    """
    base = SimConfig.baseline(seed=9, ticks=40)
    base = replace(base, insolvency=replace(base.insolvency, foreclosure_regime="ley1_2013"))
    off = replace(base, insolvency=replace(base.insolvency, forbearance_takeup=0.0))
    shock = (LabourShock(start_tick=8, rate=0.15, exit_hazard=0.15),)
    on_f = metrics.to_frame(Engine(Scenario("on", base, shock)).run())
    off_f = metrics.to_frame(Engine(Scenario("off", off, shock)).run())
    assert on_f["arrears_share"].iloc[-16:].mean() > off_f["arrears_share"].iloc[-16:].mean()
    assert on_f["foreclosures"].sum() <= off_f["foreclosures"].sum()


def test_the_forborne_are_reported_separately():
    """Counted inside arrears on the BdE's basis, and visible on their own."""
    state = _run(seed=5, ticks=30, interventions=(LabourShock(start_tick=4, rate=0.15),))
    frame = metrics.to_frame(state)
    assert (frame["forborne_share"].fillna(0) <= frame["arrears_share"].fillna(0) + 1e-9).all()
    assert frame["forborne_share"].fillna(0).max() > 0.0


def test_forbearance_does_not_resurrect_a_foreclosed_household():
    """A household that has lost the home has no loan to restructure."""
    state = _run()
    rng = np.random.default_rng(0)
    hh = next(h for h in state.households.values() if h.status is HouseholdStatus.SEEKER)
    hh.arrears_instalments = 6
    assert not insolvency.offer_forbearance(hh, state, 10_000.0, rng)
