"""Agent protocol and the intent types agents emit.

Agents are pure with respect to world state: `decide` reads state, returns intents.
The engine applies them. Nothing else keeps the tick order honest.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..state import WorldState


@dataclass(frozen=True)
class Intent:
    """Base for anything an agent wants to do this tick.

    Subtypes to define: ListForSale, MakeOffer, ListForRent, SignLease,
    RaiseRent, RenovateUnit, StartConstruction, SetPolicy, SetRate.
    """

    agent_id: int


class Agent(Protocol):
    """Every actor implements this."""

    id: int

    def decide(self, state: WorldState) -> list[Intent]:
        """Read the world, return what this agent wants to do this tick."""
        ...
