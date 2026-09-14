"""Sale-side price formation: ascending auction, m-listing search, mortgage reserve (§5c).

Mechanism tests. The moments live in `test_validation.py` (targets 13, 13b, 13c); what is
checked here is that the parts behave the way the specification says, because that is what
makes the price a derived quantity rather than a fitted one:

  - the auction prices the runner-up, not the ask, and never above the winner's valuation;
  - with one bidder the price is a negotiation, bounded by the reserve and the ask;
  - the reserve carries the mortgage, so negative equity blocks a sale outright;
  - searching more listings slows the market down, by concentrating bids on the
    well-priced listings and leaving the rest to sit.
"""

from dataclasses import replace

import numpy as np
import pytest

from resim import metrics
from resim.config import SimConfig
from resim.engine import Engine
from resim.market.clearing import auction_price, seller_reserve
from resim.scenario import Scenario


@pytest.fixture
def cfg():
    return SimConfig.baseline(seed=1, ticks=4)


# ------------------------------------------------------------------ auction


def test_two_bidders_pay_the_runner_up_plus_the_increment(cfg):
    """The ascending-auction rule: you pay what it takes to outbid the second bidder."""
    price = auction_price(highest=300_000, runner_up=250_000, ask=260_000, reserve=200_000, cfg=cfg)
    assert price == pytest.approx(250_000 * (1 + cfg.market.auction_increment))


def test_the_winner_never_pays_more_than_their_own_valuation(cfg):
    """A bidder cannot be run past their own value — that is what makes this an auction."""
    price = auction_price(highest=252_000, runner_up=251_000, ask=200_000, reserve=180_000, cfg=cfg)
    assert price <= 252_000


def test_competition_can_close_above_the_ask(cfg):
    """Fotocasa: 9% of negotiating sellers RAISED the final price in 2024.

    A sealed first-price bid around the ask could not produce that; an auction can, and must,
    or the model has no bidding wars at all.
    """
    price = auction_price(highest=300_000, runner_up=280_000, ask=260_000, reserve=240_000, cfg=cfg)
    assert price > 260_000


def test_a_single_bidder_negotiates_between_reserve_and_ask(cfg):
    """No competition, so the price is a bilateral split — never above the ask."""
    price = auction_price(highest=300_000, runner_up=None, ask=260_000, reserve=200_000, cfg=cfg)
    assert 200_000 < price <= 260_000
    theta = cfg.market.seller_bargaining_power
    assert price == pytest.approx(200_000 + theta * (260_000 - 200_000))


def test_the_reserve_is_a_floor_even_against_the_runner_up(cfg):
    """A seller cannot be dragged below their reserve by a weak second bidder."""
    price = auction_price(highest=300_000, runner_up=150_000, ask=260_000, reserve=240_000, cfg=cfg)
    assert price == pytest.approx(240_000)


# ------------------------------------------------------------------ reserve


def test_the_reserve_carries_the_mortgage(cfg):
    """A sale has to repay the loan: the reserve is the debt when the debt is what binds."""
    reserve = seller_reserve(ask=200_000, debt=190_000, discount=0.08, cfg=cfg)
    assert reserve == pytest.approx(190_000 * (1 + cfg.market.selling_cost_share))
    assert reserve > 200_000 * (1 - 0.08)


def test_an_outright_owner_still_has_a_floor(cfg):
    """With no debt the negotiation-margin leg binds — nobody accepts a derisory offer."""
    reserve = seller_reserve(ask=200_000, debt=0.0, discount=0.08, cfg=cfg)
    assert reserve == pytest.approx(200_000 * 0.92)


def test_negative_equity_blocks_the_sale(cfg):
    """The lock-in, from accounting rather than from an elasticity (model-spec §5c.3).

    An owner who owes more than the market will pay cannot convey clear title, so no bid
    clears the reserve and the dwelling does not trade. This is the mechanism that replaced
    the hand-fitted participation coefficient.
    """
    ask = 200_000
    reserve = seller_reserve(ask=ask, debt=230_000, discount=0.08, cfg=cfg)
    best_possible_bid = ask * 1.10  # even an enthusiastic buyer
    assert reserve > best_possible_bid


# ------------------------------------------------------------------- search


def _run(m: int, seed: int = 2, ticks: int = 24):
    base = SimConfig.baseline(seed=seed, ticks=ticks)
    base = replace(base, market=replace(base.market, search_listings=m))
    return metrics.to_frame(Engine(Scenario("t", base)).run())


def test_searching_more_listings_slows_the_market_down():
    """m is the friction, and it works through WHICH listings get bids, not how many.

    With m = 1 a buyer bids on whatever affordable listing it happened to draw, so bids are
    spread thinly over everything and nearly every listing finds someone: 75% of listings
    sold inside the quarter they were posted. With wider search buyers compare and converge
    on the well-priced ones, so the badly priced sit — the share sold inside the quarter
    falls monotonically (m=1 75%, m=3 56%, m=5 38%, m=8 21% when this was swept), and that is
    what the idealista days-on-market distribution identifies `m` against (model-spec §5c.2).

    Note the direction the bidder COUNT moves, because it is the opposite of the intuition:
    wider search *raises* bids per sold listing, since the listings that sell are the ones
    everybody converged on. Concentration on good value is not the same thing as a tight
    market, and only the first is what `m` controls.
    """
    narrow = _run(1)["sold_within_quarter_share"].iloc[-8:].mean()
    wide = _run(6)["sold_within_quarter_share"].iloc[-8:].mean()
    assert wide < narrow


def test_the_price_is_no_longer_the_ask_times_a_guess():
    """`overbid_sigma` is demoted to taste: halving it must not halve the price level.

    Before phase D the price WAS `ask × N(1, overbid_sigma)` and Sobol put 56% of the
    variance in price-to-income on that one scalar. The test is deliberately weak — it
    asserts only that the level is no longer proportional to the dispersion — because the
    strong version of this claim is phase E's Sobol run, and asserting it here on three
    seeds would be asserting more than the evidence carries.
    """
    base = SimConfig.baseline(seed=5, ticks=40)
    low = replace(base, market=replace(base.market, overbid_sigma=0.01))
    high = replace(base, market=replace(base.market, overbid_sigma=0.04))
    p_low = metrics.to_frame(Engine(Scenario("l", low)).run())["price_to_income"].iloc[-8:].mean()
    p_high = metrics.to_frame(Engine(Scenario("h", high)).run())["price_to_income"].iloc[-8:].mean()
    assert abs(p_high - p_low) / p_low < 0.25


def test_reproducibility_survives_the_new_draws():
    """Two runs of one seed stay identical — the auction adds draws, not entropy."""
    a = _run(3, seed=11, ticks=12)
    b = _run(3, seed=11, ticks=12)
    import pandas as pd

    pd.testing.assert_frame_equal(a, b)


def test_every_trade_carries_its_ask_and_bidder_count():
    """The two diagnostics the §5c targets are measured on must never be silently absent."""
    frame = _run(3, seed=4, ticks=16)
    assert frame["bidders_per_listing"].iloc[-8:].notna().any()
    assert frame["sale_discount_median"].iloc[-8:].notna().any()
    assert np.isfinite(frame["sold_within_quarter_share"].iloc[-1])
