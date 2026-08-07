"""Landlords — own rented stock, set rents, maintain or let units decay, sometimes exit.

Distinct from Investor if you want to model buy-to-hold operators separately from
speculative buyers. Merge the two if that distinction earns nothing.
"""

from __future__ import annotations

from ..state import WorldState
from .base import Intent


class Landlord:
    def decide(self, state: WorldState) -> list[Intent]:
        raise NotImplementedError
