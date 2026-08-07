"""Investors — buy for yield and/or expected capital gain, not to live in.

The lever most policy debates turn on. Their reaction function to taxes, rates,
and expected appreciation is the part of the model worth getting right first.
"""

from __future__ import annotations

from ..state import WorldState
from .base import Intent


class Investor:
    def decide(self, state: WorldState) -> list[Intent]:
        raise NotImplementedError
