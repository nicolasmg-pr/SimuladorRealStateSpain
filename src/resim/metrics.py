"""Run outputs — the numbers the UI plots and the numbers a scenario is judged on.

Keep every indicator defined once, here. If the UI computes a number inline it will
drift from what the tests assert.

Counts are model-scale; SCALE re-inflates to national figures where useful.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .agents.bank import max_price
from .config import ZoneType
from .market.stock import Tenure
from .state import HouseholdStatus, WorldState

SCALE = 2_000  # one model household ≈ 2,000 real households (model-spec §2)
# BdE's price-to-income uses gross DISPOSABLE income per household; model incomes are
# gross. Conversion factor ≈ 0.72 [BdE Síntesis basis — medium]
DISPOSABLE_FACTOR = 0.72


def _annual_debt_service(principal: float, rate_yr: float, term_years: int) -> float:
    """First-year payments of a quarterly annuity loan (model-spec §11)."""
    r = rate_yr / 4.0
    n = term_years * 4
    if r <= 0:
        return 4.0 * principal / n
    return 4.0 * principal * r / (1.0 - (1.0 + r) ** -n)


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
    # construction flow vs household formation (model-spec §9 target 4). All three are
    # model-scale per-tick counts; benchmarks.py re-inflates them with SCALE.
    row["completions"] = state.tick_events.get("completions", 0)
    row["starts"] = state.tick_events.get("starts", 0)
    row["formation"] = state.tick_events.get("formation", 0)
    # per-tick ratio. NOT the same as the ratio of multi-year sums BdE reports (Jensen);
    # benchmarks.py computes that separately from the `completions` / `formation` columns.
    row["completion_ratio"] = row["completions"] / max(1, row["formation"])
    # who owns the rental stock — cross-check against the 85–92% individual share
    # [investor-small §1]. An input nowhere: this is emergent (model-spec §9).
    rented = [u for u in all_units if u.tenure is Tenure.RENTED]
    row["small_landlord_rental_share"] = sum(1 for u in rented if u.owner_id >= 0) / max(
        1, len(rented)
    )
    row["public_rental_share"] = sum(1 for u in rented if u.is_public) / max(1, len(rented))
    row["vacancy_rate"] = sum(1 for u in all_units if u.tenure is Tenure.VACANT) / max(
        1, len(state.stock)
    )
    row["seasonal_units"] = sum(1 for u in all_units if u.tenure is Tenure.SEASONAL)
    row["pipeline_units"] = sum(n for _, _, n, _ in state.pipeline)
    row["sale_listings"] = len(state.sale_listings)
    row["rent_listings"] = len(state.rent_listings)

    # Rent burden of sitting tenants. The headline overburden indicator is MARKET tenants
    # only: the 27–33% target is the Eurostat "tenant, rent at market price" series, and
    # social tenants pay an administered fraction of market rent — folding them in
    # understates the indicator by ~2pp at a realistic size of the parque social.
    tenancies = [
        (state.stock.units[h.unit_id], h.income)
        for h in hhs
        if h.status is HouseholdStatus.TENANT and h.unit_id is not None
    ]
    burdens_all = [u.rent * 12.0 / max(inc, 1.0) for u, inc in tenancies]
    burdens_market = [u.rent * 12.0 / max(inc, 1.0) for u, inc in tenancies if not u.is_public]
    row["rent_burden_mean"] = float(np.mean(burdens_all)) if burdens_all else 0.0
    row["rent_overburden_share"] = (
        float(np.mean([b > 0.40 for b in burdens_market])) if burdens_market else 0.0
    )
    row["rent_overburden_share_all"] = (
        float(np.mean([b > 0.40 for b in burdens_all])) if burdens_all else 0.0
    )

    # insider/outsider wedge (model-spec §9 target 5): sitting rents move only by the
    # update cap, so all price discovery happens at rotation.
    #
    # Measured on QUALITY-ADJUSTED RENT LEVELS, not on rent/income burdens. Burdens are the
    # wrong basis here: rental matching is assortative (the queue sorts applicants by
    # willingness), so entrants are selected on income and their burden ratio comes out
    # *lower* than sitting tenants' even while they pay strictly more for the same flat.
    # The wedge the mechanism produces is a price wedge, so that is what is reported.
    sitting = [
        state.stock.units[h.unit_id].rent / max(state.stock.units[h.unit_id].quality, 1e-9)
        for h in hhs
        if h.status is HouseholdStatus.TENANT
        and h.unit_id is not None
        and not state.stock.units[h.unit_id].is_public
        and state.tick - state.stock.units[h.unit_id].contract_start > 4
    ]
    entrant = [
        r.rent / max(state.stock.units[r.unit_id].quality, 1e-9)
        for r in rentals
        if not state.stock.units[r.unit_id].is_public
    ]
    row["rent_sitting"] = float(np.median(sitting)) if sitting else 0.0
    row["rent_entrant"] = float(np.median(entrant)) if entrant else 0.0
    row["insider_outsider_wedge"] = (
        row["rent_entrant"] / row["rent_sitting"] - 1.0
        if sitting and entrant and row["rent_sitting"] > 0
        else float("nan")
    )

    credit = state.config.credit
    fees = state.config.market.buyer_fees
    rate = state.macro.mortgage_rate
    access_ok = access_total = 0
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

        # affordability (model-spec §11): theoretical effort + unassisted access share
        row[f"purchase_effort_{z}"] = _annual_debt_service(
            credit.max_ltv * zs.price_index, rate, credit.term_years
        ) / (zi * DISPOSABLE_FACTOR)
        # the EFFECTIVE tax, so an ITP intervention actually shows up here
        itp = state.macro.itp[zone]
        non_owners = [h for h in zone_hhs if h.status is not HouseholdStatus.OWNER]
        zone_ok = sum(
            1 for h in non_owners if max_price(h, rate, credit, itp, fees) >= zs.price_index
        )
        row[f"buyer_access_{z}"] = zone_ok / max(1, len(non_owners))
        access_ok += zone_ok
        access_total += len(non_owners)

    row["price_national"] = float(
        sum(state.zones[z].price_index * zone_weights[z] for z in ZoneType)
    )
    row["rent_national"] = float(sum(state.zones[z].rent_index * zone_weights[z] for z in ZoneType))
    # household-weighted national growth, per tick. The zone series already exist; these are
    # the national aggregates the published Spanish figures (INE IPV, BdE) are quoted on.
    row["price_growth_national"] = sum(
        row[f"price_growth_{z.value}"] * zone_weights[z] for z in ZoneType
    )
    row["rent_growth_national"] = sum(
        row[f"rent_growth_{z.value}"] * zone_weights[z] for z in ZoneType
    )
    row["price_to_income"] = row["price_national"] / (median_income * DISPOSABLE_FACTOR)
    row["purchase_effort"] = _annual_debt_service(
        credit.max_ltv * row["price_national"], rate, credit.term_years
    ) / (median_income * DISPOSABLE_FACTOR)
    row["buyer_access"] = access_ok / max(1, access_total)
    return row


def to_frame(state: WorldState) -> pd.DataFrame:
    """History as a tidy DataFrame, one row per tick."""
    return pd.DataFrame(state.history).set_index("tick")


def compare(baseline: pd.DataFrame, scenario: pd.DataFrame) -> pd.DataFrame:
    """Scenario minus baseline, per indicator per tick — the answer to 'what changed'."""
    common = baseline.columns.intersection(scenario.columns)
    idx = baseline.index.intersection(scenario.index)
    return scenario.loc[idx, common] - baseline.loc[idx, common]
