"""Government — applies the scenario's interventions inside the world.

Thin by design: it reads the active Scenario and enacts taxes, caps, subsidies, and
permits. Policy definitions live in scenario.py; this is only the actor that applies them.
"""

from __future__ import annotations

from ..state import WorldState
from .base import Intent


class Government:
    def decide(self, state: WorldState) -> list[Intent]:
        raise NotImplementedError
