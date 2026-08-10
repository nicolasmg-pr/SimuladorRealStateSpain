"""Government — applies the scenario's interventions inside the world.

Thin by design: policy definitions live in scenario.py; the engine folds them into
the tick's config (step 1). The government emits two kinds of intent — public
construction, and re-letting of public units that fell vacant (nobody else can: the
parque social is outside the private landlord logic, and without this it drains away
as tenants rotate out). Everything else (caps, taxes, subsidies) acts through other
actors' constraints.

Competence split (government §5) is encoded in scenario.py lever metadata; by the
time a PolicyConfig is active here, its veto points are assumed cleared.
"""

from __future__ import annotations

import numpy as np

from ..config import ZoneType
from ..market.stock import PUBLIC_ID, Tenure
from ..state import WorldState
from .base import Intent, ListForRent, StartConstruction


class Government:
    def __init__(self, agent_id: int, rng: np.random.Generator) -> None:
        self.id = agent_id
        self.rng = rng

    def decide(self, state: WorldState) -> list[Intent]:
        pol = state.config.policy
        intents: list[Intent] = []

        # re-let the vacant parque social at the administered rent (a share of market)
        for unit in state.stock.units.values():
            if (
                unit.owner_id != PUBLIC_ID
                or unit.tenure is not Tenure.VACANT
                or unit.id in state.rent_listings
            ):
                continue
            zs = state.zones[unit.zone]
            intents.append(
                ListForRent(
                    agent_id=self.id,
                    unit_id=unit.id,
                    ask=zs.rent_index * unit.quality * pol.public_rent_discount,
                )
            )

        if pol.public_units_per_tick > 0:
            zones = (ZoneType.TENSIONED, ZoneType.SECONDARY, ZoneType.RURAL)
            for zone, weight in zip(zones, pol.public_zone_weights, strict=True):
                n = int(round(pol.public_units_per_tick * weight))
                if n > 0:
                    intents.append(
                        StartConstruction(agent_id=self.id, zone=zone, n_units=n, is_public=True)
                    )
        return intents
