"""Agent protocol and the intent types agents emit.

Agents are pure with respect to world state: `decide` reads state, returns intents.
The engine applies them. Nothing else keeps the tick order honest.

Each agent object receives its own child Generator (rng.spawn) at construction —
that keeps decide() reproducible without letting agents share streams.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from ..config import ZoneType
from ..state import WorldState


@dataclass(frozen=True)
class Intent:
    """Base for anything an agent wants to do this tick."""

    agent_id: int


@dataclass(frozen=True)
class ListForSale(Intent):
    unit_id: int = -1
    ask: float = 0.0  # €
    reserve: float = 0.0  # €


@dataclass(frozen=True)
class MakeOffer(Intent):
    """A budget-limited buyer entering the sale market of one zone.

    `budget` is the maximum *price* payable after the credit screen (engine step 5
    clips it); `cash` buyers skip the screen entirely.
    """

    zone: ZoneType = ZoneType.SECONDARY
    budget: float = 0.0  # € max price (pre-screen willingness)
    cash: bool = False
    first_time: bool = False  # buyer owns no home (first-time-buyer status)
    # the buyer passed the guarantee means test AND the programme still has budget. Decided
    # once, by the household, and carried through screening and settlement — never
    # re-derived from `first_time`, which would hand the aval to every buyer.
    guaranteed: bool = False


@dataclass(frozen=True)
class ListForRent(Intent):
    unit_id: int = -1
    ask: float = 0.0  # €/month
    capped: bool = False  # ask was clipped by an active cap


@dataclass(frozen=True)
class WithdrawRental(Intent):
    """Landlord pulls a unit out of the standard rental segment."""

    unit_id: int = -1
    destination: Literal["sale", "seasonal", "vacant"] = "sale"


@dataclass(frozen=True)
class RentApplication(Intent):
    zone: ZoneType = ZoneType.SECONDARY
    max_rent: float = 0.0  # €/month acceptance threshold


@dataclass(frozen=True)
class StartConstruction(Intent):
    zone: ZoneType = ZoneType.SECONDARY
    n_units: int = 0
    is_public: bool = False


@dataclass(frozen=True)
class SetCredit(Intent):
    """Bank publishes this tick's mortgage offer."""

    mortgage_rate: float = 0.0  # /yr


@dataclass
class IntentBundle:
    """Everything collected in engine step 4, split by market."""

    sale_listings: list[ListForSale] = field(default_factory=list)
    offers: list[MakeOffer] = field(default_factory=list)
    rent_listings: list[ListForRent] = field(default_factory=list)
    withdrawals: list[WithdrawRental] = field(default_factory=list)
    rent_applications: list[RentApplication] = field(default_factory=list)
    construction: list[StartConstruction] = field(default_factory=list)
    credit: SetCredit | None = None


class Agent(Protocol):
    """Every actor implements this."""

    id: int

    def decide(self, state: WorldState) -> list[Intent]:
        """Read the world, return what this agent wants to do this tick."""
        ...
