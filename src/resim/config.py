"""Simulation parameters — the knobs of the world, before any policy is applied.

Split deliberately from `scenario.py`: config describes how the market works,
a scenario describes what we do to it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PopulationConfig:
    """How many actors of each type exist, and how their attributes are distributed."""

    # TODO: n_households, income distribution, savings distribution,
    # n_investors, n_developers, n_landlords.


@dataclass(frozen=True)
class StockConfig:
    """The initial housing stock: how many units, of what quality, where, owned by whom."""

    # TODO: n_units, tenure split (owner-occupied / rented / vacant), quality tiers, zones.


@dataclass(frozen=True)
class MarketConfig:
    """Rules of exchange: search frictions, listing duration, transaction costs, price stickiness."""

    # TODO


@dataclass(frozen=True)
class CreditConfig:
    """Lending environment: base rate, LTV cap, DTI cap, term."""

    # TODO


@dataclass(frozen=True)
class SimConfig:
    """Full input to one run."""

    seed: int
    ticks: int
    population: PopulationConfig
    stock: StockConfig
    market: MarketConfig
    credit: CreditConfig

    @classmethod
    def baseline(cls) -> SimConfig:
        """The reference world every scenario is compared against."""
        raise NotImplementedError
