"""Agent decision tests — each actor in isolation, against a hand-built WorldState."""

import copy

import numpy as np

from resim.agents.bank import max_price
from resim.agents.base import ListForSale, MakeOffer, StartConstruction
from resim.agents.developer import Developer
from resim.agents.household import Households
from resim.agents.investor import LargeInvestor
from resim.agents.landlord import SmallLandlords
from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.market.stock import LARGE_INVESTOR_ID, Tenure
from resim.scenario import Scenario
from resim.state import HouseholdState, HouseholdStatus


def small_state(seed: int = 9):
    cfg = SimConfig.baseline(seed=seed, ticks=4)
    engine = Engine(Scenario(name="t", baseline=cfg))
    state = engine.initialise()
    engine.step(state)  # one settled tick so indices/expectations exist
    return engine, state


def test_household_cannot_bid_above_credit_limit():
    """Ability-to-pay binds before willingness-to-pay."""
    engine, state = small_state()
    cfg = state.config
    offers = [
        i
        for i in Households(-10, np.random.default_rng(0)).decide(state)
        if isinstance(i, MakeOffer) and not i.cash and i.agent_id >= 0
    ]
    assert offers, "expected at least one mortgage-financed offer"
    for offer in offers:
        hh = state.households[offer.agent_id]
        limit = max_price(
            hh,
            state.macro.mortgage_rate,
            cfg.credit,
            state.macro.itp[offer.zone],
            cfg.market.buyer_fees,
            guaranteed=True,  # most permissive case still must bound the bid
        )
        assert offer.budget <= limit * 1.15 + 1.0  # momentum shading ≤ +10%, tolerance


def test_investor_exits_when_yield_below_hurdle():
    """Rate rise past the hurdle turns investors into sellers."""
    engine, state = small_state()
    # crush yields: bond yield far above any zone's gross rental yield
    state.macro.bond_yield = 0.20
    intents = LargeInvestor(LARGE_INVESTOR_ID, np.random.default_rng(1)).decide(state)
    sales = [i for i in intents if isinstance(i, ListForSale)]
    buys = [i for i in intents if isinstance(i, MakeOffer)]
    assert sales, "investor should list units for sale when yield < hurdle"
    assert not buys, "no accumulation when yield is below hurdle"


def test_developer_starts_only_above_margin():
    """No construction when expected margin is negative."""
    engine, state = small_state()
    state.tick_events["sales_by_zone"] = {z: 50 for z in ZoneType}
    # price floor: crash the price index so expected price < all-in cost
    for zs in state.zones.values():
        zs.price_index = 30_000.0
        zs.expected_price_growth = 0.0
    intents = Developer(-12, np.random.default_rng(2)).decide(state)
    assert not [i for i in intents if isinstance(i, StartConstruction)]

    # generous prices: starts must appear
    for zs in state.zones.values():
        zs.price_index = 600_000.0
    intents = Developer(-12, np.random.default_rng(2)).decide(state)
    assert [i for i in intents if isinstance(i, StartConstruction)]


def test_agents_do_not_mutate_state():
    """decide() is read-only. Guards the whole tick-order contract."""
    engine, state = small_state()
    before = copy.deepcopy(
        (
            {k: copy.copy(v.__dict__) for k, v in state.households.items()},
            {k: copy.copy(v.__dict__) for k, v in state.stock.units.items()},
            {z: state.zones[z].price_index for z in state.zones},
            dict(state.sale_listings),
            dict(state.rent_listings),
        )
    )
    rng = np.random.default_rng(3)
    for agent in (
        Households(-10, rng),
        SmallLandlords(-11, rng),
        LargeInvestor(LARGE_INVESTOR_ID, rng),
        Developer(-12, rng),
    ):
        agent.decide(state)
    after = (
        {k: copy.copy(v.__dict__) for k, v in state.households.items()},
        {k: copy.copy(v.__dict__) for k, v in state.stock.units.items()},
        {z: state.zones[z].price_index for z in state.zones},
        dict(state.sale_listings),
        dict(state.rent_listings),
    )
    assert before == after


def test_tenant_status_consistency():
    """Every tenant occupies a rented unit; every owner-occupied unit is owned by its occupant."""
    engine, state = small_state()
    for _ in range(4):
        engine.step(state)
    for hh in state.households.values():
        if hh.status is HouseholdStatus.TENANT:
            unit = state.stock.units[hh.unit_id]
            assert unit.tenure is Tenure.RENTED
            assert unit.occupant_id == hh.id
        elif hh.status is HouseholdStatus.OWNER:
            unit = state.stock.units[hh.unit_id]
            assert unit.owner_id == hh.id


def test_max_price_monotone_in_wealth_and_income():
    cfg = SimConfig.baseline()
    poor = HouseholdState(0, ZoneType.SECONDARY, 20_000, 5_000, HouseholdStatus.SEEKER)
    rich = HouseholdState(1, ZoneType.SECONDARY, 60_000, 80_000, HouseholdStatus.SEEKER)
    lo = max_price(poor, 0.03, cfg.credit, 0.08, 0.02)
    hi = max_price(rich, 0.03, cfg.credit, 0.08, 0.02)
    assert 0 <= lo < hi
