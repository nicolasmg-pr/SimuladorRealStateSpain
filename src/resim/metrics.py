"""Run outputs — the numbers the UI plots and the numbers a scenario is judged on.

Keep every indicator defined once, here. If the UI computes a number inline it will
drift from what the tests assert.
"""

from __future__ import annotations

import pandas as pd

from .state import WorldState


def snapshot(state: WorldState) -> dict:
    """One row of the time series for the current tick.

    Candidate indicators: median sale price, price index, median rent, rent-to-income,
    price-to-income, transaction volume, months of supply, vacancy rate, homeownership
    rate, share of purchases by investors, evictions/defaults, new construction starts.
    """
    raise NotImplementedError


def to_frame(state: WorldState) -> pd.DataFrame:
    """History as a tidy DataFrame, one row per tick."""
    raise NotImplementedError


def compare(baseline: pd.DataFrame, scenario: pd.DataFrame) -> pd.DataFrame:
    """Scenario minus baseline, per indicator per tick — the actual answer to 'what changed'."""
    raise NotImplementedError
