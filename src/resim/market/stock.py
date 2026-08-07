"""The housing stock — units, their attributes, ownership, and occupancy.

Supply is a stock with a slow flow. Decide early whether units are heterogeneous
(quality, size, zone) or interchangeable; that choice drives everything downstream.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Unit:
    """One dwelling."""

    id: int
    # TODO: zone, quality, size, owner_id, occupant_id, tenure, last_sale_price, condition


class Stock:
    """The full set of units plus the queries the market and metrics need."""

    def vacant(self) -> list[Unit]:
        raise NotImplementedError

    def for_sale(self) -> list[Unit]:
        raise NotImplementedError

    def for_rent(self) -> list[Unit]:
        raise NotImplementedError

    def add(self, unit: Unit) -> None:
        """Register a newly completed unit from a developer."""
        raise NotImplementedError
