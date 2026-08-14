"""Price formation — the single most consequential module in the model.

Mechanism (model-spec §5): sealed-bid per listing. Each buyer targets one random
affordable listing in their zone; bids scatter around the ask; the highest bid at or
above the reserve wins at that bid. Bidding wars emerge when several buyers land on
one listing; sticky asks emerge because failed listings decay slowly.

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


@dataclass(frozen=True)
class RentalMatch:
    """A signed lease."""

    unit_id: int
    tenant_id: int
    rent: float  # €/month
    capped: bool = False


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
        # each buyer picks a random listing they can afford and bids around the ask
        bids: dict[int, list[tuple[float, MakeOffer]]] = defaultdict(list)
        order = rng.permutation(len(zone_offers))
        for idx in order:
            offer = zone_offers[int(idx)]
            affordable = [lst for lst in listings if lst.ask <= offer.budget * 1.05]
            if not affordable:
                continue
            lst = affordable[int(rng.integers(len(affordable)))]
            bid = min(
                offer.budget,
                lst.ask * float(rng.normal(1.0, cfg.market.overbid_sigma)),
            )
            bids[lst.unit_id].append((bid, offer))

        # a household buys at most one home per tick. Negative agent ids are *aggregates*
        # (the foreign overlay, the large investor): each of their offers is a distinct
        # buyer, so they must not be deduplicated — doing so silently throttled the whole
        # non-resident stream to one purchase per zone per tick.
        taken_buyers: set[int] = set()
        for unit_id, unit_bids in bids.items():
            lst = state.sale_listings[unit_id]
            unit_bids = [
                (b, o) for b, o in unit_bids if not (o.agent_id >= 0 and o.agent_id in taken_buyers)
            ]
            if not unit_bids:
                continue
            best_bid, best_offer = max(unit_bids, key=lambda t: t[0])
            if best_bid < lst.reserve:
                continue
            unit = state.stock.units[unit_id]
            trades.append(
                Trade(
                    unit_id=unit_id,
                    buyer_id=best_offer.agent_id,
                    seller_id=unit.owner_id,
                    price=best_bid,
                    cash=best_offer.cash,
                    guaranteed=best_offer.guaranteed,
                )
            )
            if best_offer.agent_id >= 0:
                taken_buyers.add(best_offer.agent_id)
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
                    old.rent = 0.0
        unit.occupant_id = tenant.id
        unit.tenure = Tenure.RENTED
        unit.rent = rm.rent
        unit.contract_start = state.tick
        tenant.status = HouseholdStatus.TENANT
        tenant.unit_id = unit.id
        tenant.ticks_searching = 0  # housed: the search spell ends
