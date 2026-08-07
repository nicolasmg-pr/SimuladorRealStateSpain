"""World state for a single tick.

One mutable object owned by the engine and passed to agents. Agents read state and
return *intents*; they never write to state directly. The engine and the market
clearing step are the only writers — this is what keeps the tick order auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorldState:
    tick: int = 0

    # TODO: agent registries (households, investors, developers, landlords, bank, government)
    # TODO: housing stock (units, ownership, occupancy, quality)
    # TODO: open listings (for sale, for rent) and their asking prices
    # TODO: last-period price index and rent index — agents form expectations from these
    # TODO: macro variables set by config/scenario at this tick (interest rate, taxes)

    history: list[dict] = field(default_factory=list)
