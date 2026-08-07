"""The housing stock — units, their attributes, ownership, and occupancy.

Units are heterogeneous in zone and quality (a scalar multiplier on the zone price).
Owner ids: >= 0 are household ids (owner-occupiers and small landlords);
negative ids are institutional owners (see constants below).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..config import ZoneType

LARGE_INVESTOR_ID = -2
PUBLIC_ID = -3
DEVELOPER_ID = -4


class Tenure(Enum):
    OWNER_OCCUPIED = "owner_occupied"
    RENTED = "rented"  # occupied by a tenant
    VACANT = "vacant"  # empty: between tenants, for sale, or withheld
    SEASONAL = "seasonal"  # withdrawn to the uncapped seasonal/tourist segment


@dataclass
class Unit:
    """One dwelling."""

    id: int
    zone: ZoneType
    quality: float  # multiplier on zone price level, ~lognormal around 1
    owner_id: int
    occupant_id: int | None
    tenure: Tenure
    last_sale_price: float
    rent: float = 0.0  # €/month, current contract (0 if not rented)
    contract_start: int = -1  # tick the current lease was signed
    vacant_since: int = -1  # tick the unit became vacant (for vacancy tax)
    withheld: bool = False  # deliberately kept off the market (2nd home / strategic)
    is_public: bool = False


class Stock:
    """The full set of units plus the queries the market and metrics need."""

    def __init__(self) -> None:
        self.units: dict[int, Unit] = {}
        self._next_id = 0

    def new_id(self) -> int:
        self._next_id += 1
        return self._next_id - 1

    def add(self, unit: Unit) -> None:
        """Register a unit (initialisation or a newly completed one from a developer)."""
        if unit.id in self.units:
            raise ValueError(f"duplicate unit id {unit.id}")
        self.units[unit.id] = unit
        self._next_id = max(self._next_id, unit.id + 1)

    def __len__(self) -> int:
        return len(self.units)

    def by_zone(self, zone: ZoneType) -> list[Unit]:
        return [u for u in self.units.values() if u.zone is zone]

    def vacant(self) -> list[Unit]:
        return [u for u in self.units.values() if u.tenure is Tenure.VACANT]

    def rented(self) -> list[Unit]:
        return [u for u in self.units.values() if u.tenure is Tenure.RENTED]

    def owned_by(self, owner_id: int) -> list[Unit]:
        return [u for u in self.units.values() if u.owner_id == owner_id]

    def rental_portfolio_size(self, owner_id: int) -> int:
        """Units the owner holds beyond an owner-occupied home (gran-tenedor test)."""
        return sum(
            1
            for u in self.units.values()
            if u.owner_id == owner_id and u.tenure is not Tenure.OWNER_OCCUPIED
        )
