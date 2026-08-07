"""The tick loop — the spine of the simulation.

Tick order is a modelling decision, not an implementation detail: who acts first
changes the outcome. Record the chosen order in docs/model-spec.md and keep this
module the single place it is expressed.

Draft order (to confirm):
    1. macro update      — apply scenario interventions active at this tick
    2. agent decisions   — every agent reads state, returns intents (no writes)
    3. market clearing   — match buyers/sellers and renters/landlords, form prices
    4. settlement        — transfer ownership, update balances, mortgages, occupancy
    5. supply response   — developers start/finish construction
    6. metrics           — snapshot indicators into history
"""

from __future__ import annotations

from collections.abc import Iterator

from .scenario import Scenario
from .state import WorldState


class Engine:
    """Runs one scenario from tick 0 to `ticks`."""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario

    def initialise(self) -> WorldState:
        """Build the tick-0 world: agents, stock, initial prices."""
        raise NotImplementedError

    def step(self, state: WorldState) -> WorldState:
        """Advance exactly one tick, following the order documented above."""
        raise NotImplementedError

    def run(self) -> WorldState:
        """Run to completion and return the final state (history holds the series)."""
        raise NotImplementedError

    def stream(self) -> Iterator[WorldState]:
        """Yield state after each tick — used by the UI to render a run as it progresses."""
        raise NotImplementedError
