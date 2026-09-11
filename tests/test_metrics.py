"""Mechanical correctness of metric columns, against hand-built states.

`test_validation.py` judges the model against the world; this file judges the
measurement against the state. A column that is wrong here makes every target
that reads it meaningless.
"""

import numpy as np

from resim import metrics
from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.scenario import Scenario


def small_state(seed: int = 9):
    """One settled tick, so indices, expectations and tick_events all exist."""
    cfg = SimConfig.baseline(seed=seed, ticks=4)
    engine = Engine(Scenario(name="t", baseline=cfg))
    state = engine.initialise()
    engine.step(state)
    return engine, state


def test_net_migration_columns_sum_to_zero():
    """Migration moves households between zones; it never creates or destroys them."""
    _, state = small_state()
    row = state.history[-1]
    total = sum(row[f"net_migration_{z.value}"] for z in ZoneType)
    assert total == 0


def test_net_migration_is_inflow_minus_outflow_on_known_flows():
    """Hand-built flows, hand-computed expectations — no formula shared with the metric.

    The previous version of this test recomputed the production expression on the same
    dict, so it could catch a wiring regression but never a wrong definition.
    """
    _, state = small_state()
    state.tick_events["migration"] = {
        (ZoneType.TENSIONED, ZoneType.SECONDARY): 3,
        (ZoneType.SECONDARY, ZoneType.RURAL): 2,
    }
    row = metrics.snapshot(state)
    assert row["net_migration_tensioned"] == -3
    assert row["net_migration_secondary"] == 1
    assert row["net_migration_rural"] == 2


def test_landlord_household_share_counts_owners_of_units_they_do_not_live_in():
    """A landlord household owns at least one unit that is not its own home."""
    _, state = small_state()
    row = state.history[-1]
    expected = {
        hh.id
        for hh in state.households.values()
        for u in state.stock.units.values()
        if u.owner_id == hh.id and u.id != hh.unit_id
    }
    assert row["landlord_households"] == len(expected)
    assert row["landlord_household_share"] == len(expected) / max(1, len(state.households))


def test_trade_carries_the_listing_age():
    """A matched trade reports how long its listing had been on the market."""
    from resim.agents.base import MakeOffer
    from resim.market.clearing import clear_sales
    from resim.state import SaleListing

    _, state = small_state()
    unit = next(u for u in state.stock.units.values() if u.owner_id >= 0)
    zs = state.zones[unit.zone]
    ask = zs.price_index * unit.quality
    state.sale_listings.clear()
    state.sale_listings[unit.id] = SaleListing(
        unit_id=unit.id, ask=ask, reserve=ask * 0.5, ticks_listed=3
    )
    # a negative agent id is an aggregate cash buyer, so no credit screen and no
    # one-purchase-per-buyer dedup interferes with the assertion
    offers = [MakeOffer(agent_id=-99, zone=unit.zone, budget=ask * 2.0, cash=True)]
    trades = clear_sales(state, offers, np.random.default_rng(0))
    assert trades, "a cash offer at twice the ask must clear"
    assert trades[0].ticks_listed == 3


def test_median_ticks_to_sale_is_reported():
    """The column exists and is non-negative wherever the tick had trades."""
    _, state = small_state()
    row = state.history[-1]
    value = row["median_ticks_to_sale"]
    assert np.isnan(value) or value >= 0


def test_median_ticks_to_sale_is_the_median_of_matched_listing_ages():
    """Hand-built trades, hand-computed median — catches a mean-for-median swap."""
    from resim.market.clearing import Trade

    _, state = small_state()
    unit_ids = [u.id for u in list(state.stock.units.values())[:3]]
    trades = [
        Trade(unit_id=unit_ids[0], buyer_id=1, seller_id=2, price=1.0, ticks_listed=1),
        Trade(unit_id=unit_ids[1], buyer_id=1, seller_id=2, price=1.0, ticks_listed=5),
        Trade(unit_id=unit_ids[2], buyer_id=1, seller_id=2, price=1.0, ticks_listed=3),
    ]
    row = metrics.snapshot(state, trades=trades)
    assert row["median_ticks_to_sale"] == 3


def test_gross_yield_columns_are_rent_over_price_not_a_mean_of_zones():
    """Two definitions the yield columns carry that only a mechanical test can hold.

    Their only other test is target 9's strict xfail, which cannot validate a definition:
    drop the × 12 or invert the ratio and it still xfails, silently.

    1. Each zone column is that zone's annualised asking rent over its price index.
    2. The national column is built from the household-weighted national indices, NOT from
       the mean of the three zone yields. On the baseline those differ substantially
       (≈6.8% against ≈9.5%, the mean dragged up by rural's ≈17%), and phase B reads this
       column to judge the total-return hurdle, so the basis is pinned before it does.

    Indices are hand-set to an inverted ladder — rural rent above the metro rent, as the
    model in fact produces — so the second assertion cannot pass by the two bases happening
    to coincide on a well-behaved state.
    """
    _, state = small_state()
    levels = {
        ZoneType.TENSIONED: (300_000.0, 1_250.0),
        ZoneType.SECONDARY: (150_000.0, 825.0),
        ZoneType.RURAL: (80_000.0, 1_150.0),
    }
    for zone, (price, rent) in levels.items():
        state.zones[zone].price_index = price
        state.zones[zone].rent_index = rent

    row = metrics.snapshot(state)
    for zone, (price, rent) in levels.items():
        assert row[f"gross_yield_{zone.value}"] == rent * 12.0 / price

    assert row["gross_yield_national"] == row["rent_national"] * 12.0 / row["price_national"]
    zone_mean = float(np.mean([row[f"gross_yield_{z.value}"] for z in ZoneType]))
    assert abs(row["gross_yield_national"] - zone_mean) > 0.01, (
        f"national yield {row['gross_yield_national']:.4f} collapsed onto the "
        f"mean of the zone yields {zone_mean:.4f} — the basis is no longer pinned"
    )
