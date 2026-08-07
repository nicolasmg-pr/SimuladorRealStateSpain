"""Households — the demand side.

Decides each tick whether to stay, rent, buy, or sell, given income, savings,
credit access, current prices/rents, and price expectations.

Open questions for the spec: how is willingness-to-pay formed? Are expectations
adaptive (extrapolate recent price growth) or rational? What triggers a move?
"""

from __future__ import annotations

from ..state import WorldState
from .base import Intent


class Household:
    def decide(self, state: WorldState) -> list[Intent]:
        raise NotImplementedError
