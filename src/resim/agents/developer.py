"""Developers — the supply side, and the main source of lag in the model.

Start construction when expected margin clears a hurdle; units arrive N ticks later.
That delay is what generates cycles, so make the lag explicit and configurable.
"""

from __future__ import annotations

from ..state import WorldState
from .base import Intent


class Developer:
    def decide(self, state: WorldState) -> list[Intent]:
        raise NotImplementedError
