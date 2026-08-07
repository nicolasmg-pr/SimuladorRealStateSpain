"""Run outputs — the numbers the UI plots and the numbers a scenario is judged on.

Keep every indicator defined once, here. If the UI computes a number inline it will
drift from what the tests assert.

Counts are model-scale; SCALE re-inflates to national figures where useful.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ZoneType
from .market.stock import Tenure
from .state import HouseholdStatus, WorldState

SCALE = 2_000  # one model household ≈ 2,000 real households (model-spec §2)
# BdE's price-to-income uses gross DISPOSABLE income per household; model incomes are
# gross. Conversion factor ≈ 0.72 [BdE Síntesis basis — medium]
DISPOSABLE_FACTOR = 0.72


def snapshot(state: WorldState, trades=(), rentals=()) -> dict:
    """One row of the time series for the current tick."""
    row: dict = {"tick": state.tick}
    hhs = state.households.values()
    n_hh = max(1, len(state.households))
    owners = sum(1 for h in hhs if h.status is HouseholdStatus.OWNER)
    tenants = sum(1 for h in hhs if h.status is HouseholdStatus.TENANT)
    seekers = n_hh - owners - tenants
    row["ownership_rate"] = owners / n_hh
    row["tenant_share"] = tenants / n_hh
    row["seeker_share"] = seekers / n_hh
    row["transactions"] = len(trades)
    row["new_leases"] = len(rentals)
    row["mortgage_rate"] = state.macro.mortgage_rate

    incomes = np.array([h.income for h in hhs])
    median_income = float(np.median(incomes)) if len(incomes) else 1.0

    all_units = state.stock.units.values()
    row["stock_total"] = len(state.stock)
    row["vacancy_rate"] = sum(1 for u in all_units if u.tenure is Tenure.VACANT) / max(
        1, len(state.stock)
    )
    row["seasonal_units"] = sum(1 for u in all_units if u.tenure is Tenure.SEASONAL)
    row["pipeline_units"] = sum(n for _, _, n, _ in state.pipeline)
    row["sale_listings"] = len(state.sale_listings)
    row["rent_listings"] = len(state.rent_listings)

    # rent burden of sitting tenants (distributional, not just mean)
    burdens = [
        state.stock.units[h.unit_id].rent * 12.0 / max(h.income, 1.0)
        for h in hhs
        if h.status is HouseholdStatus.TENANT and h.unit_id is not None
    ]
    row["rent_burden_mean"] = float(np.mean(burdens)) if burdens else 0.0
    row["rent_overburden_share"] = float(np.mean([b > 0.40 for b in burdens])) if burdens else 0.0

    zone_weights: dict[ZoneType, float] = {}
    for zone in ZoneType:
        zs = state.zones[zone]
        z = zone.value
        zone_units = [u for u in all_units if u.zone is zone]
        row[f"price_{z}"] = zs.price_index
        row[f"rent_{z}"] = zs.rent_index
        row[f"rent_transacted_{z}"] = zs.rent_transacted
        row[f"reference_rent_{z}"] = zs.reference_rent
        row[f"price_growth_{z}"] = zs.price_growth[-1] if zs.price_growth else 0.0
        row[f"rent_growth_{z}"] = zs.rent_growth[-1] if zs.rent_growth else 0.0
        row[f"vacancy_{z}"] = sum(1 for u in zone_units if u.tenure is Tenure.VACANT) / max(
            1, len(zone_units)
        )
        # market vacancy excludes withheld units (second homes, strategic holdouts) —
        # the Censo-comparable 6–9% urban figure is closer to this basis
        row[f"vacancy_market_{z}"] = sum(
            1 for u in zone_units if u.tenure is Tenure.VACANT and not u.withheld
        ) / max(1, len(zone_units))
        row[f"new_leases_{z}"] = sum(
            1 for r in rentals if state.stock.units[r.unit_id].zone is zone
        )
        row[f"seasonal_{z}"] = sum(1 for u in zone_units if u.tenure is Tenure.SEASONAL)
        zone_hhs = [h for h in hhs if h.zone is zone]
        zone_weights[zone] = len(zone_hhs) / n_hh
        zi = float(np.median([h.income for h in zone_hhs])) if zone_hhs else median_income
        row[f"price_to_income_{z}"] = zs.price_index / (zi * DISPOSABLE_FACTOR)

    row["price_national"] = float(
        sum(state.zones[z].price_index * zone_weights[z] for z in ZoneType)
    )
    row["price_to_income"] = row["price_national"] / (median_income * DISPOSABLE_FACTOR)
    return row


def to_frame(state: WorldState) -> pd.DataFrame:
    """History as a tidy DataFrame, one row per tick."""
    return pd.DataFrame(state.history).set_index("tick")


def compare(baseline: pd.DataFrame, scenario: pd.DataFrame) -> pd.DataFrame:
    """Scenario minus baseline, per indicator per tick — the answer to 'what changed'."""
    common = baseline.columns.intersection(scenario.columns)
    idx = baseline.index.intersection(scenario.index)
    return scenario.loc[idx, common] - baseline.loc[idx, common]
