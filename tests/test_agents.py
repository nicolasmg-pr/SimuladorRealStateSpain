"""Agent decision tests — each actor in isolation, against a hand-built WorldState."""

import collections
import copy

import numpy as np

from resim.agents.bank import max_price
from resim.agents.base import ListForSale, MakeOffer, StartConstruction, WithdrawRental
from resim.agents.developer import Developer
from resim.agents.household import Households
from resim.agents.investor import LargeInvestor
from resim.agents.landlord import SmallLandlords, cap_level, required_rent
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


def _capped_state(*, cap_ratio: float, seasonal_closed: bool = False):
    """Return (state, landlord_agent) with a rent cap active in the tensioned zone.

    `cap_ratio` is the cap expressed as a fraction of the unit's reservation rent
    (`agents.landlord.required_rent`): > 1.0 binds the posted ask but still clears the
    hurdle; < 1.0 breaks the hurdle. `seasonal_closed` sets
    `PolicyConfig.seasonal_segment_capped` (unused in Task 1; Task 3 needs it).
    """
    _, state = small_state()
    zone = ZoneType.TENSIONED
    # cap_coverage=0.0 makes every naturally-drawn unit (declaration_draw in [0, 1)) UNCOVERED,
    # so only the one unit we mark below (declaration_draw < 0.0) sits under the cap — the rest
    # of the tensioned-zone stock cannot contaminate the withdrawal count with unrelated caps.
    state.config = state.config.with_policy(
        rent_cap_enabled=True,
        cap_index_binds_all=True,
        cap_coverage=0.0,
        seasonal_segment_capped=seasonal_closed,
    )
    unit = next(
        u
        for u in state.stock.units.values()
        if u.zone is zone
        and u.owner_id >= 0
        and u.tenure is Tenure.VACANT
        and not u.withheld
        and u.id not in state.rent_listings
        and u.id not in state.sale_listings
    )
    unit.declaration_draw = -1.0  # the one unit `is_covered` returns True for
    zs = state.zones[zone]
    value = zs.price_index * unit.quality
    floor = required_rent(state, zone, value)
    cap = cap_ratio * floor
    zs.reference_rent = cap / unit.quality  # cap_level(index_binds_all=True) reads this back
    # push the fundamental ask well above the cap, so the cap binds the posted rent regardless
    # of which side of the hurdle `cap_ratio` lands on
    zs.shadow_rent = (2.0 * max(cap, floor)) / (unit.quality * (1.0 + zs.expected_rent_growth))
    fundamental_ask = max(floor, zs.shadow_rent * unit.quality * (1.0 + zs.expected_rent_growth))

    # precondition: `cap_ratio` must land on the intended side of the hurdle, and the cap must
    # actually bind the ask — otherwise the test below would pass by testing nothing.
    clears_hurdle = cap >= floor
    assert clears_hurdle == (cap_ratio >= 1.0), (
        f"cap_ratio={cap_ratio} landed on the wrong side of the hurdle: "
        f"floor={floor:.2f} cap={cap:.2f}"
    )
    assert cap < fundamental_ask, (
        f"cap does not bind the ask: cap={cap:.2f} fundamental_ask={fundamental_ask:.2f}"
    )

    landlord = SmallLandlords(-11, np.random.default_rng(7))
    return state, landlord


def _exit_destinations(state, landlord: SmallLandlords, *, draws: int = 200) -> collections.Counter:
    """Counter of `WithdrawRental.destination` over `draws` calls to `landlord.decide`.

    State is never mutated by `decide` (agents are read-only, engine.py is the only writer —
    CLAUDE.md), so the same candidate unit is redrawn every call rather than being consumed
    after its first exit.
    """
    counter: collections.Counter = collections.Counter()
    for _ in range(draws):
        for intent in landlord.decide(state):
            if isinstance(intent, WithdrawRental):
                counter[intent.destination] += 1
    return counter


def test_a_cap_that_binds_but_clears_the_hurdle_produces_no_withdrawal():
    """§7.2. The trigger is the reservation rent, not the cap binding at all.

    A cap set between the landlord's reservation rent and its fundamental ask binds —
    the posted rent falls — but the dwelling still clears the total-return hurdle, so
    there is nothing to arbitrage against and the landlord stays let. Under the
    pre-§7.2 hazard this configuration produced exits at any positive elasticity.
    """
    state, landlord = _capped_state(cap_ratio=1.1)
    intents = [landlord.decide(state) for _ in range(200)]
    withdrawals = [i for batch in intents for i in batch if isinstance(i, WithdrawRental)]
    assert withdrawals == [], f"{len(withdrawals)} withdrawals from a cap that clears the hurdle"


def test_sale_requires_the_shortfall_to_beat_the_cost_of_leaving():
    """§7.2 sale rule. The cumulative shortfall over the holding horizon must exceed the
    cost of leaving. A cap one euro below the reservation rent does not pay for a sale.

    Seasonal closed (`seasonal_closed=True`) isolates the sale rule under test: since Task 3
    the seasonal branch is evaluated first and diverts independently of the shortfall, so an
    open segment would let seasonal exits through here regardless of this test's premise.
    """
    state, landlord = _capped_state(cap_ratio=0.999, seasonal_closed=True)
    intents = [i for _ in range(200) for i in landlord.decide(state)]
    withdrawals = [i for i in intents if isinstance(i, WithdrawRental)]
    assert not withdrawals, f"{len(withdrawals)} withdrawals from a shortfall too small to sell"


def test_a_deep_cap_pays_for_the_sale():
    """The same landlord, with the cap far below the reservation rent, sells."""
    state, landlord = _capped_state(cap_ratio=0.4, seasonal_closed=True)
    intents = [i for _ in range(200) for i in landlord.decide(state)]
    dests = {i.destination for i in intents if isinstance(i, WithdrawRental)}
    assert dests == {"sale"}


def test_closing_the_seasonal_segment_pushes_exits_into_sales():
    """§7.2 branch order, and the comparative static Catalonia dated for us.

    Seasonal is the cheap exit — it pays no transaction cost — so it is taken first.
    Closing the segment (Ley 11/2025, in force 1 Jan 2026) must therefore convert
    seasonal exits into sales, not into staying let. Incasòl measured the quarter:
    seasonal contracts −1,233, the first fall since the cap began.
    """
    open_ = _exit_destinations(*_capped_state(cap_ratio=0.4))
    closed = _exit_destinations(*_capped_state(cap_ratio=0.4, seasonal_closed=True))
    assert open_["seasonal"] > 0
    assert closed["seasonal"] == 0
    assert closed["sale"] > open_["sale"]
    assert "vacant" not in open_ and "vacant" not in closed


def test_the_cap_to_reservation_ratio_is_near_uniform_within_a_zone():
    """§7.2b's premise, measured rather than assumed.

    §7.2b claims the exit decision is scale-invariant: `cap` and `r_req` both scale with
    `Unit.quality`, so `cap / r_req` is near-identical across a zone's units and crosses 1
    for all of them at once. If that is false, the dispersion §7.2b adds is repairing the
    wrong thing. Asserted as a coefficient of variation below 0.10 — tight enough that no
    meaningful share of units sits on the other side of the threshold from the rest.

    Measured under Ley 11/2020 (`cap_index_binds_all=True`, set unconditionally by
    `_capped_state`): the reference index binds every landlord regardless of `large_holder`
    or declared-municipality coverage, which is the regime where the scale-invariance claim
    is strongest.
    """
    state, _ = _capped_state(cap_ratio=0.8)
    ratios = []
    for unit in state.stock.units.values():
        if unit.zone is not ZoneType.TENSIONED:
            continue
        value = state.zones[unit.zone].price_index * unit.quality
        r_req = required_rent(state, unit.zone, value)
        cap = cap_level(
            state,
            unit.zone,
            unit.quality,
            previous_rent=unit.rent or unit.last_contract_rent,
            large_holder=False,
        )
        if cap is None or r_req <= 0:
            continue
        ratios.append(cap / r_req)
    assert len(ratios) > 50, f"too few capped units to measure: {len(ratios)}"
    mean = sum(ratios) / len(ratios)
    sd = (sum((x - mean) ** 2 for x in ratios) / (len(ratios) - 1)) ** 0.5
    cv = sd / mean
    assert cv < 0.10, f"cap/r_req is NOT near-uniform: cv={cv:.3f}, mean={mean:.3f}"


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
            ltv_boost=0.20,  # most permissive case still must bound the bid
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


def test_state_guarantee_reaches_the_lending_cap():
    """The aval must actually lift the equity constraint, and only for eligible buyers.

    Regression guard: the boost used to live on CreditConfig, which no intervention ever
    set, so the whole demand-subsidy guarantee arm was inert while still draining budget.
    """
    from resim.scenario import DemandSubsidy, Scenario

    cfg = SimConfig.baseline(seed=42, ticks=12)
    active = Scenario(
        name="ds",
        baseline=cfg,
        interventions=(DemandSubsidy(start_tick=1, guarantee_ltv_boost=0.20),),
    ).config_at(6)
    hh = HouseholdState(0, ZoneType.TENSIONED, 40_000, 20_000, HouseholdStatus.SEEKER)
    unassisted = max_price(hh, 0.033, active.credit, 0.10, 0.02)
    assisted = max_price(hh, 0.033, active.credit, 0.10, 0.02, active.policy.guarantee_ltv_boost)
    assert assisted > unassisted * 1.2, "guarantee must relax the down-payment constraint"

    # and the envelope is a one-off stock, not a per-tick allowance
    state = Engine(
        Scenario(
            name="ds",
            baseline=cfg,
            interventions=(
                DemandSubsidy(start_tick=1, guarantee_ltv_boost=0.20, guarantee_eligible_share=1.0),
            ),
        )
    ).run()
    assert state.macro.guarantee_budget_funded
    assert state.macro.guarantee_budget_left < active.policy.guarantee_budget


def test_max_price_monotone_in_wealth_and_income():
    cfg = SimConfig.baseline()
    poor = HouseholdState(0, ZoneType.SECONDARY, 20_000, 5_000, HouseholdStatus.SEEKER)
    rich = HouseholdState(1, ZoneType.SECONDARY, 60_000, 80_000, HouseholdStatus.SEEKER)
    lo = max_price(poor, 0.03, cfg.credit, 0.08, 0.02)
    hi = max_price(rich, 0.03, cfg.credit, 0.08, 0.02)
    assert 0 <= lo < hi
