"""Price formation — the single most consequential module in the model.

Matches buyers to sellers and renters to landlords, and decides the transaction price.

Mechanism to choose (document it in docs/model-spec.md before writing code):
  - sealed-bid per listing: highest bid above reserve wins, price = bid or second bid
  - random search and bilateral bargaining: price splits the surplus
  - Walrasian tatonnement: single market price adjusts on excess demand

Sealed-bid per listing is usually the best first choice for housing — it reproduces
bidding wars and sticky asking prices without needing a global auctioneer.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..agents.base import Intent
from ..state import WorldState


@dataclass(frozen=True)
class Trade:
    """A matched, priced transaction, ready to be settled."""

    unit_id: int
    buyer_id: int
    seller_id: int
    price: float


def clear_sales(state: WorldState, intents: list[Intent]) -> list[Trade]:
    """Match sale listings against offers and set transaction prices."""
    raise NotImplementedError


def clear_rentals(state: WorldState, intents: list[Intent]) -> list[Trade]:
    """Match rental listings against tenant demand and set rents."""
    raise NotImplementedError


def settle(state: WorldState, trades: list[Trade]) -> None:
    """Apply trades: ownership, occupancy, balances, mortgages. The only writer of that state."""
    raise NotImplementedError
