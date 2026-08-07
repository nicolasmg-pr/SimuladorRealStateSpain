"""Government — applies the scenario's interventions inside the world.

Thin by design: policy definitions live in scenario.py; the engine folds them into
the tick's config (step 1). The only *intent* the government emits is public
construction — everything else (caps, taxes, subsidies) acts through other actors'
constraints.

Competence split (government §5) is encoded in scenario.py lever metadata; by the
time a PolicyConfig is active here, its veto points are assumed cleared.
"""

from __future__ import annotations

import numpy as np

from ..config import ZoneType
from ..state import WorldState
from .base import Intent, StartConstruction


class Government:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        pol = state.config.policy
        intents: list[Intent] = []
        if pol.public_units_per_tick > 0:
            zones = (ZoneType.TENSIONED, ZoneType.SECONDARY, ZoneType.RURAL)
            for zone, weight in zip(zones, pol.public_zone_weights, strict=True):
                n = int(round(pol.public_units_per_tick * weight))
                if n > 0:
                    intents.append(
                        StartConstruction(agent_id=self.id, zone=zone, n_units=n, is_public=True)
                    )
        return intents
