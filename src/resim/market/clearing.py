"""Price formation — the single most consequential module in the model.

Mechanism (model-spec §5, §5c): an **ascending auction** per listing. Each buyer samples
`m` affordable listings in their zone and bids on the one offering the most surplus; the
winner pays what it takes to outbid the runner-up, capped by their own valuation and floored
by the seller's reserve. With a single bidder the price is a bilateral negotiation split by
the seller's bargaining weight. Bidding wars emerge when several buyers converge on one
well-priced listing; sticky asks emerge because failed listings decay slowly.

Until phase D this was a sealed first-price bid drawn as `ask × N(1, overbid_sigma)`, which
made the price the ask times a guessed random number — Sobol put 56% of the variance in
price-to-income on that one scalar. `overbid_sigma` is still here, demoted to idiosyncratic
taste over VALUE rather than dispersion over price.

Rentals: queue matching — applicants sorted by willingness, each takes the BEST listing
they can afford; rent = posted ask (landlords post, tenants accept — the Spanish rental
market is posted-price, not an auction).

A queue-auction markup on top of the ask was tried and removed: measured effect ≈0, because
assortative matching already puts each applicant on a listing at the top of their
affordability, leaving no headroom to bid up. The consequence is structural and worth stating
plainly — the clearing rent equals the winning applicant's willingness to pay, so the only
route for the rent index to outrun income growth is through the *level* of burden households
accept, which is what the sharing margin in agents/household.py does. See model-spec §5.

`settle` is the only writer of ownership/occupancy/balances.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from ..agents.bank import loan_terms
from ..agents.base import MakeOffer, RentApplication
from ..config import ZoneType
from ..state import HouseholdStatus, WorldState
from .stock import LARGE_INVESTOR_ID, Tenure

# Expectation shading of the valuation anchor, moved here from agents/household.py in
# phase D so that it reaches the price instead of being clipped by the index cap below.
#
# RE-IDENTIFIED when the channel moved (5.0 -> 2.5). At 5.0 the shading multiplied a budget
# that the index cap then threw away for every buyer whose credit limit exceeded market
# value; applied to the valuation it reaches the price in full, and the same 5.0 put the
# baseline on a permanent 5.1%/yr boom with price-to-income at 9.5 and purchase effort at
# 45%. Identified on CALIBRATION-WINDOW moments only — price-to-income 7-8 and the BdE's
# 35-40% purchase effort — which put it between 2 and 3 (2.0: 7.42 and 35.0%; 3.0: 8.26 and
# 38.9%). The 2021-25 episode is a hold-out and was NOT used to set it; what the model then
# does in that episode is reported in docs/validation.md, phase D.
MOMENTUM_GAIN = 2.5
MOMENTUM_CAP = 0.10

FOREIGN_ID = -5  # non-resident overlay buyer (holiday/investment purchase)


@dataclass(frozen=True)
class Trade:
    """A matched, priced sale, ready to be settled."""

    unit_id: int
    buyer_id: int
    seller_id: int
    price: float
    cash: bool = False
    guaranteed: bool = False
    ticks_listed: int = 0  # age of the listing when it matched — time-to-sale diagnostic
    ask: float = 0.0  # what it was listed at — the discount (ask − price)/ask is a §5c target
    bidders: int = 0  # how many bids the listing drew — competition, measured not assumed
    # What this sale would have closed at had the price-setting bidders drawn an average
    # taste (ε = 1), everything else — budgets, reserve, ask, bargaining weight — unchanged.
    # The agent-visible price index is updated on THIS, not on `price` (model-spec §5c.6):
    # the winner of an auction is selected on a high draw, so an index built on winners
    # carries a selection premium, and feeding that back as next tick's valuation anchor
    # turns `overbid_sigma` into a growth rate. `price` stays the transaction price and is
    # what every reported indicator uses.
    neutral_price: float = 0.0


@dataclass(frozen=True)
class RentalMatch:
    """A signed lease."""

    unit_id: int
    tenant_id: int
    rent: float  # €/month
    capped: bool = False


def auction_price(
    *, highest: float, runner_up: float | None, ask: float, reserve: float, cfg
) -> float:
    """What the winner pays (model-spec §5c.1).

    Two bidders or more — an ascending auction: the winner pays what it takes to outbid the
    runner-up and never more than their own valuation. Competition reaches the price through
    the BIDDER COUNT, which demand and supply produce, instead of through a dispersion
    parameter nobody measured. A listing several buyers want can close above its ask, and
    Fotocasa's survey says that happens: 9% of negotiating sellers raised the final price in
    2024 against 6% a year earlier.

    One bidder — a bilateral negotiation, split by the seller's bargaining weight θ. This is
    the block's one free parameter and it is calibrated against the measured discount between
    asking and sale price (6.2%, Cátedra Tecnocasa-UPF 2S 2025). The buyer never pays more
    than the ask here: with no competition there is nothing to outbid.
    """
    if runner_up is None:
        theta = cfg.market.seller_bargaining_power
        target = min(highest, ask)
        return max(reserve, reserve + theta * (target - reserve))
    step = runner_up * (1.0 + cfg.market.auction_increment)
    return float(min(max(step, reserve), highest))


def loss_averse_ask(*, base_ask: float, paid: float, value: float, alpha: float) -> float:
    """What a seller facing a nominal loss asks instead (model-spec §5d.1).

    Genesove & Mayer (QJE 2001): owners facing a nominal loss set asking prices 25–35% of the
    gap between the expected selling price and what they paid *above* what they would
    otherwise ask, and their dwellings show a much lower sale hazard. The list-price effect is
    twice as large for owner-occupants as for investors, which is why `alpha` differs by
    seller type rather than being one number.

    Inert in a rising market: `paid <= value` gives back exactly `base_ask`. That is what
    makes this addable after a calibration done on a rising window — it cannot have been
    fitted to it, and it cannot move it.
    """
    loss = max(0.0, paid - value)
    return base_ask + alpha * loss


def seller_reserve(
    *, ask: float, debt: float, discount: float, cfg, paid: float = 0.0, value: float = 0.0
) -> float:
    """The lowest price a seller can accept (model-spec §5c.3).

    `max(debt + selling costs, ask × (1 − max_discount))`. The first leg is accounting, not
    behaviour: a sale has to repay the loan, so a household in negative equity cannot convey
    clear title below what it owes. That is the lock-in the model used to carry as a fitted
    coefficient on the mortgage rate, and it now follows from the LTV distribution and the
    price path the model itself produces. The second leg keeps a floor under an outright
    owner, who still refuses a derisory offer; its size is the measured negotiation margin.
    """
    floor = max(debt * (1.0 + cfg.market.selling_cost_share), ask * (1.0 - discount))
    # the REALISED-price leg of loss aversion (model-spec §5d.1): Genesove & Mayer find
    # realised prices 3–18% of the nominal loss higher, not only asking prices. It belongs
    # here rather than in the ask, because with a low bargaining weight the price is set by
    # the reserve and an ask-only effect withholds the dwelling without holding the price up.
    loss = max(0.0, paid - value)
    if loss > 0.0:
        floor = max(floor, floor + cfg.market.loss_aversion_reserve * loss)
    return floor


def clear_sales(
    state: WorldState, offers: list[MakeOffer], rng: np.random.Generator
) -> list[Trade]:
    """Match sale listings against offers and set transaction prices."""
    cfg = state.config
    trades: list[Trade] = []
    by_zone: dict[ZoneType, list[MakeOffer]] = defaultdict(list)
    for o in offers:
        by_zone[o.zone].append(o)

    listings_by_zone: dict[ZoneType, list] = defaultdict(list)
    for lst in state.sale_listings.values():
        unit = state.stock.units[lst.unit_id]
        listings_by_zone[unit.zone].append(lst)

    for zone, zone_offers in by_zone.items():
        listings = listings_by_zone.get(zone, [])
        if not listings:
            continue
        zs = state.zones[zone]
        # buyers value off the taste-neutral index, sellers post off the realised one
        # (model-spec §5c.6)
        zone_price = zs.valuation_index or zs.price_index
        # What a buyer thinks the dwelling will be worth, not only what it is worth today.
        # This is where expectations reach the SALE PRICE (model-spec §5c.1, §6): the
        # valuation anchor is the index lifted by expected growth, so excess demand raises
        # prices, the rise feeds the adaptive expectation, and the loop runs until credit
        # binds. It used to sit on the buyer's *budget* in agents/household.py, where the
        # index cap in this function silently clipped it away for every buyer whose credit
        # limit exceeded market value — which is most of them, and it is why the model had
        # no scarcity-to-price channel (redesign spec, finding 2).
        momentum = float(
            np.clip(
                MOMENTUM_GAIN * zs.expected_price_growth,
                -MOMENTUM_CAP,
                MOMENTUM_CAP,
            )
        )
        # Market tightness: buyers chasing each listing this tick, in this zone. The option
        # value of searching again falls as this rises, so bids move toward the credit limit
        # (model-spec §5c.7). This is the scarcity-to-price channel, and it runs through
        # BUDGETS — income and credit — not through anybody's taste draw.
        tightness = len(zone_offers) / max(len(listings), 1)
        stretch = tightness / (tightness + cfg.market.tightness_half_saturation)
        # Each buyer samples m affordable listings and bids on the one with the most surplus
        # (what the dwelling is worth to them, minus what it costs). m < ∞ is the friction:
        # with m = 1 (the pre-phase-D rule) buyers bid at random and bidding wars happened
        # because nobody looked; with m = ∞ every buyer converges on the same bargain and the
        # market clears like a single auction. Both are wrong, and m is identified against the
        # days-on-market distribution and the bidders-per-dwelling count (model-spec §5c.2).
        m = max(1, cfg.market.search_listings)
        # SEQUENTIAL ARRIVAL WITHIN THE TICK (model-spec §5c.8). The tick is a quarter, the
        # market is not: offers arrive month by month and a seller answers the ones in front
        # of it [Merlo & Ortalo-Magné 2004; Merlo, Ortalo-Magné & Rust, complete offer
        # histories for 780 English properties]. Clearing a whole quarter at once turned every
        # listing into a simultaneous auction, which is why the model's negotiation margin was
        # a third of the measured one. The sub-period count is the calendar, not a parameter.
        subperiods = max(1, cfg.market.subperiods_per_tick)
        order = rng.permutation(len(zone_offers))
        # a household buys at most one home per tick. Negative agent ids are *aggregates*
        # (the foreign overlay, the large investor): each of their offers is a distinct
        # buyer, so they must not be deduplicated — doing so silently throttled the whole
        # non-resident stream to one purchase per zone per tick.
        taken_buyers: set[int] = set()
        available = list(listings)
        for arrivals in np.array_split(order, subperiods):
            if not len(arrivals) or not available:
                continue
            bids: dict[int, list[tuple[float, MakeOffer, float]]] = defaultdict(list)
            for idx in arrivals:
                offer = zone_offers[int(idx)]
                if offer.agent_id >= 0 and offer.agent_id in taken_buyers:
                    continue
                affordable = [lst for lst in available if lst.ask <= offer.budget * 1.05]
                if not affordable:
                    continue
                sample_size = min(m, len(affordable))
                picks = rng.choice(len(affordable), size=sample_size, replace=False)
                # taste: how much THIS buyer happens to like each dwelling. The demoted
                # `overbid_sigma` (model-spec §5c.1) — dispersion over value, not over price
                taste = rng.normal(1.0, cfg.market.overbid_sigma, sample_size)
                best, best_surplus, best_value, best_neutral = None, -np.inf, 0.0, 0.0
                for k, pick in enumerate(picks):
                    lst = affordable[int(pick)]
                    unit = state.stock.units[lst.unit_id]
                    fundamental = zone_price * unit.quality * (1.0 + momentum)
                    base = min(offer.budget, fundamental * float(taste[k]))
                    # stretch toward the credit limit as the market tightens (§5c.7)
                    value = base + stretch * max(0.0, offer.budget - base)
                    surplus = value - lst.ask
                    if surplus > best_surplus:
                        best, best_surplus, best_value = lst, surplus, value
                        # the same bid with an average taste draw, budget cap still applied
                        neutral_base = min(offer.budget, fundamental)
                        best_neutral = neutral_base + stretch * max(
                            0.0, offer.budget - neutral_base
                        )
                if best is None:
                    continue
                # the bid is what the dwelling is worth to this buyer, capped by the budget
                # the credit screen left them. What they PAY is set by the auction below
                bids[best.unit_id].append((best_value, offer, best_neutral))

            sold: set[int] = set()
            for unit_id, unit_bids in bids.items():
                lst = state.sale_listings[unit_id]
                unit_bids = [
                    (b, o, nb)
                    for b, o, nb in unit_bids
                    if not (o.agent_id >= 0 and o.agent_id in taken_buyers)
                ]
                if not unit_bids:
                    continue
                unit_bids.sort(key=lambda t: -t[0])
                best_bid, best_offer, _ = unit_bids[0]
                if best_bid < lst.reserve:
                    continue
                price = auction_price(
                    highest=best_bid,
                    runner_up=unit_bids[1][0] if len(unit_bids) > 1 else None,
                    ask=lst.ask,
                    reserve=lst.reserve,
                    cfg=cfg,
                )
                # the same auction with the taste draws of both price-setting bidders
                # replaced by the average one. Run through the SAME rule, so the reserve, the
                # ask, the bargaining weight and the budget cap all still bind where they
                # bound before — which is why this cannot be written as a closed-form
                # correction (model-spec §5c.6)
                neutral_bids = sorted((nb for _, _, nb in unit_bids), reverse=True)
                neutral_price = auction_price(
                    highest=neutral_bids[0],
                    runner_up=neutral_bids[1] if len(neutral_bids) > 1 else None,
                    ask=lst.ask,
                    reserve=lst.reserve,
                    cfg=cfg,
                )
                unit = state.stock.units[unit_id]
                trades.append(
                    Trade(
                        unit_id=unit_id,
                        buyer_id=best_offer.agent_id,
                        seller_id=unit.owner_id,
                        price=price,
                        cash=best_offer.cash,
                        guaranteed=best_offer.guaranteed,
                        ticks_listed=lst.ticks_listed,
                        ask=lst.ask,
                        bidders=len(unit_bids),
                        neutral_price=neutral_price,
                    )
                )
                sold.add(unit_id)
                if best_offer.agent_id >= 0:
                    taken_buyers.add(best_offer.agent_id)
            if sold:
                available = [lst for lst in available if lst.unit_id not in sold]
    return trades


def clear_rentals(
    state: WorldState, applications: list[RentApplication], rng: np.random.Generator
) -> list[RentalMatch]:
    """Match rental listings against tenant demand; rent = posted ask."""
    matches: list[RentalMatch] = []
    by_zone: dict[ZoneType, list[RentApplication]] = defaultdict(list)
    for a in applications:
        by_zone[a.zone].append(a)

    listings_by_zone: dict[ZoneType, list] = defaultdict(list)
    for lst in state.rent_listings.values():
        unit = state.stock.units[lst.unit_id]
        listings_by_zone[unit.zone].append(lst)

    for zone, apps in by_zone.items():
        listings = sorted(listings_by_zone.get(zone, []), key=lambda x: x.ask)
        # queue by willingness: highest max_rent first (screening favours solvency);
        # each applicant takes the BEST listing they can afford (housing is a normal
        # good) — assortative matching keeps the contract-rent index demand-driven
        apps = sorted(apps, key=lambda a: -a.max_rent)
        used: set[int] = set()
        for app in apps:
            match = next(
                (
                    lst
                    for lst in reversed(listings)
                    if lst.unit_id not in used and lst.ask <= app.max_rent
                ),
                None,
            )
            if match is None:
                continue
            used.add(match.unit_id)
            matches.append(
                RentalMatch(
                    unit_id=match.unit_id,
                    tenant_id=app.agent_id,
                    rent=match.ask,
                    capped=match.capped,
                )
            )
    _ = rng  # matching is deterministic given the queues; rng kept for symmetry
    return matches


def settle(state: WorldState, trades: list[Trade], rentals: list[RentalMatch]) -> None:
    """Apply trades: ownership, occupancy, balances, mortgages. The only writer."""
    cfg = state.config
    for tr in trades:
        unit = state.stock.units[tr.unit_id]
        seller_id = unit.owner_id
        state.sale_listings.pop(tr.unit_id, None)
        state.rent_listings.pop(tr.unit_id, None)

        # sitting tenant displaced by an investor exit sale (rotation shortcut)
        if (
            unit.tenure is Tenure.RENTED
            and unit.occupant_id is not None
            and unit.occupant_id != tr.buyer_id
        ):
            sitting = state.households.get(unit.occupant_id)
            if sitting is not None:
                sitting.status = HouseholdStatus.SEEKER
                sitting.unit_id = None
                sitting.ticks_searching = 0  # a fresh spell, not the old one
            unit.occupant_id = None
            unit.tenure = Tenure.VACANT
            unit.rent = 0.0

        # seller side
        if seller_id >= 0:
            seller = state.households.get(seller_id)
            if seller is not None:
                proceeds = tr.price
                if seller.unit_id == unit.id:  # owner-occupier sold their home
                    proceeds -= seller.mortgage_balance
                    seller.mortgage_balance = 0.0
                    seller.mortgage_payment = 0.0
                    seller.mortgage_ticks_left = 0
                    seller.status = HouseholdStatus.SEEKER
                    seller.unit_id = None
                    seller.ticks_searching = 0
                seller.wealth += max(0.0, proceeds)

        # buyer side
        if tr.buyer_id >= 0:
            buyer = state.households[tr.buyer_id]
            itp = state.macro.itp[unit.zone]
            fees = cfg.market.buyer_fees
            if tr.cash:
                buyer.wealth = max(0.0, buyer.wealth - tr.price * (1 + itp + fees))
            else:
                principal, payment, n = loan_terms(
                    tr.price,
                    buyer,
                    state.macro.mortgage_rate,
                    cfg.credit,
                    itp,
                    fees,
                    cfg.policy.guarantee_ltv_boost if tr.guaranteed else 0.0,
                )
                equity = tr.price - principal
                buyer.wealth = max(0.0, buyer.wealth - equity - tr.price * (itp + fees))
                buyer.mortgage_balance = principal
                buyer.mortgage_payment = payment
                buyer.mortgage_ticks_left = n
                if tr.guaranteed:
                    state.macro.guarantee_budget_left = max(
                        0.0,
                        state.macro.guarantee_budget_left
                        - cfg.policy.guarantee_ltv_boost * tr.price,
                    )
            # vacate the buyer's rented unit
            if buyer.unit_id is not None:
                old = state.stock.units[buyer.unit_id]
                if old.occupant_id == buyer.id:
                    old.occupant_id = None
                    if old.tenure is Tenure.RENTED:
                        old.tenure = Tenure.VACANT
                        old.vacant_since = state.tick
                        old.rent = 0.0
            buyer.status = HouseholdStatus.OWNER
            buyer.unit_id = unit.id
            buyer.ticks_searching = 0  # housed: the search spell ends
            unit.occupant_id = buyer.id
            unit.tenure = Tenure.OWNER_OCCUPIED
        elif tr.buyer_id == LARGE_INVESTOR_ID:
            unit.occupant_id = None
            unit.tenure = Tenure.VACANT
            unit.vacant_since = state.tick
        else:  # FOREIGN_ID — holiday/second home, leaves the residential market
            unit.occupant_id = None
            unit.tenure = Tenure.VACANT
            unit.vacant_since = state.tick
            unit.withheld = True

        unit.owner_id = tr.buyer_id
        unit.last_sale_price = tr.price
        unit.rent = 0.0

    for rm in rentals:
        unit = state.stock.units[rm.unit_id]
        tenant = state.households[rm.tenant_id]
        state.rent_listings.pop(rm.unit_id, None)
        # vacate the tenant's previous unit (rotation)
        if tenant.unit_id is not None:
            old = state.stock.units[tenant.unit_id]
            if old.occupant_id == tenant.id:
                old.occupant_id = None
                if old.tenure is Tenure.RENTED:
                    old.tenure = Tenure.VACANT
                    old.vacant_since = state.tick
                    # the ceiling the small-landlord cap regime anchors on survives the
                    # tenancy (LAU art. 17.6 as amended: the contract in force in the last
                    # five years), so it is kept rather than zeroed with the rent
                    old.last_contract_rent = old.rent or old.last_contract_rent
                    old.rent = 0.0
        unit.occupant_id = tenant.id
        unit.tenure = Tenure.RENTED
        unit.rent = rm.rent
        unit.contract_start = state.tick
        tenant.status = HouseholdStatus.TENANT
        tenant.unit_id = unit.id
        tenant.ticks_searching = 0  # housed: the search spell ends
