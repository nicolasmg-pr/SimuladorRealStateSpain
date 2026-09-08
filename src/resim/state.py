"""World state for a single tick.

One mutable object owned by the engine and passed to agents. Agents read state and
return *intents*; they never write to state directly. The engine and the market
clearing step are the only writers — this is what keeps the tick order auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .config import SimConfig, ZoneType
from .market.stock import Stock


class HouseholdStatus(Enum):
    OWNER = "owner"  # owner-occupier
    TENANT = "tenant"  # renting
    SEEKER = "seeker"  # newly formed / displaced, searching (sharing meanwhile)


@dataclass
class HouseholdState:
    """Registry row for one household. Mutated only by the engine/clearing."""

    id: int
    zone: ZoneType
    income: float  # €/yr gross
    wealth: float  # € liquid savings (excl. housing)
    status: HouseholdStatus
    unit_id: int | None = None  # home occupied (owned or rented)
    max_rent_burden: float = 0.35  # accepted rent/income share, drawn per household
    mortgage_balance: float = 0.0  # € outstanding
    mortgage_payment: float = 0.0  # €/quarter
    mortgage_ticks_left: int = 0
    is_foreign_cash: bool = False  # non-resident overlay buyer
    # consecutive ticks spent as a SEEKER without finding a home. Drives the rent-burden
    # escalation in agents/household.py (the sharing margin) — reset by clearing.settle the
    # moment the household is housed, so it measures the current search spell, not a history.
    ticks_searching: int = 0
    # U(0,1) drawn once from the engine's seeded Generator when the household is created.
    # Means-tested eligibility (rent subsidy) compares it against the eligible share, so
    # decide() stays pure AND reproducible — Python's hash() is salted per process and
    # must never be used for a model draw.
    eligibility_draw: float = 1.0


@dataclass
class ZoneState:
    """Per-zone market observables agents condition on."""

    price_index: float  # € per standard unit (quality 1)
    rent_index: float  # €/month per standard unit, ASKING basis (idealista-like)
    reference_rent: float  # official reference index (SERPAVI-analogue), €/month
    # €/month a standard unit would clear at with NO cap: equals rent_index in a free market;
    # under a cap it is inferred from the applicant queue (engine._update_indices). This is
    # what landlords compare the cap against when deciding to withdraw a unit.
    shadow_rent: float = 0.0
    shadow_anchor: float | None = None  # index / queue-clearing ratio fixed at cap activation
    rent_transacted: float = 0.0  # €/month, median new-contract rent (SERPAVI-like)
    price_growth: list[float] = field(default_factory=list)  # trailing per-tick growth
    rent_growth: list[float] = field(default_factory=list)
    expected_price_growth: float = 0.0  # set each tick by the engine (step 3)
    expected_rent_growth: float = 0.0


@dataclass
class SaleListing:
    unit_id: int
    ask: float  # €
    reserve: float  # €
    ticks_listed: int = 0
    presale: bool = False  # developer new-build sold off-plan


@dataclass
class RentListing:
    unit_id: int
    ask: float  # €/month
    capped: bool = False  # ask was clipped by an active rent cap
    ticks_listed: int = 0


@dataclass
class Macro:
    euribor: float  # /yr
    mortgage_rate: float  # /yr, offered rate (lags euríbor via pass-through)
    bond_yield: float  # /yr, landlord opportunity cost anchor
    itp: dict[ZoneType, float] = field(default_factory=dict)  # effective buyer tax
    guarantee_budget_left: float = 0.0  # demand-subsidy line, model-scale €
    # the envelope is a one-off programme stock, funded on the tick the lever switches on.
    # Without this flag an exhausted budget (== 0.0) would look unfunded and refill forever.
    guarantee_budget_funded: bool = False


@dataclass
class WorldState:
    tick: int = 0
    config: SimConfig | None = None  # config as of this tick (scenario-applied)
    households: dict[int, HouseholdState] = field(default_factory=dict)
    stock: Stock = field(default_factory=Stock)
    zones: dict[ZoneType, ZoneState] = field(default_factory=dict)
    sale_listings: dict[int, SaleListing] = field(default_factory=dict)  # by unit id
    rent_listings: dict[int, RentListing] = field(default_factory=dict)  # by unit id
    macro: Macro | None = None
    pipeline: list[tuple[int, ZoneType, int, bool]] = field(default_factory=list)
    # (completion_tick, zone, n_units, is_public)
    land_release_start: int | None = None  # first tick the land-release lever was active
    next_household_id: int = 0
    # per-tick scratch written by the engine for metrics (trades, counts)
    tick_events: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def new_household_id(self) -> int:
        self.next_household_id += 1
        return self.next_household_id - 1
