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
from .market.clearing import FOREIGN_ID
from .market.stock import LARGE_INVESTOR_ID, Tenure
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
    row["households"] = n_hh  # model scale; × SCALE for national counts
    row["ownership_rate"] = owners / n_hh
    row["tenant_share"] = tenants / n_hh
    row["seeker_share"] = seekers / n_hh
    row["transactions"] = len(trades)
    row["new_leases"] = len(rentals)
    # time to sell, in ticks (model-spec §9 target 13). Reported, not gated: the idealista
    # days-on-market distribution is not yet a row in docs/sources.md. It is the observable
    # that identifies the phase-D auction without touching the price level (spec §7.7).
    # Unit of the scale, for whoever converts that distribution to quarters: listings age at
    # the top of `engine._apply_listings`, before clearing, so a listing created and matched
    # inside the same tick reads 0, not 1 — "sold within the tick" maps to 0, not to ≤1.
    row["median_ticks_to_sale"] = (
        float(np.median([t.ticks_listed for t in trades])) if trades else float("nan")
    )
    row["mortgage_rate"] = state.macro.mortgage_rate
    # how the purchase was paid for. Spain 2023: 973,637 sales against 381,560 new mortgage
    # deeds ⇒ 60.8% of purchases carried no registered mortgage [INE via Funcas 104 ch.3],
    # against the 30–40% cash share the model's dossiers record [bank §6]. Emergent here:
    # households paying out of wealth, investors and the non-resident overlay.
    row["cash_purchase_share"] = (
        float(np.mean([t.cash for t in trades])) if trades else float("nan")
    )
    # who bought, by buyer type. Non-residents were 7.9% of Spanish sales in the 4 quarters
    # to 2025Q1 (CaixaBank Research on MIVAU; all foreigners 16.0% in 2026Q2, Registradores);
    # legal persons ≈10% (BdE IA 2025). Emergent here from the overlay's Poisson stream and
    # the large investor's yield rule — neither is an input share of *completed* purchases.
    row["foreign_purchase_share"] = (
        float(np.mean([t.buyer_id == FOREIGN_ID for t in trades])) if trades else float("nan")
    )
    row["investor_purchase_share"] = (
        float(np.mean([t.buyer_id == LARGE_INVESTOR_ID for t in trades]))
        if trades
        else float("nan")
    )

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
    # how many HOUSEHOLDS are landlords — the anchor for buy-to-let entry (spec §7.3).
    #
    # BASIS: this is the EFF "owns other real estate" basis — any household owning a unit it
    # does not live in, so vacant second homes, withheld stock, seasonal units and the
    # inherited-but-vacant dwellings the assumption register flags as an ownership leak all
    # count. It is NOT the AEAT "declares rental income" basis. Phase B will need a sibling
    # column restricted to units at `Tenure.RENTED` — that is the AEAT basis, and it is the
    # one buy-to-let entry should be judged on. Not added here: phase 0 adds no mechanism.
    #
    # Reported, not gated. Both anchors ARE registered — EFF 36.1% of households own other
    # real estate (2022 wave), revised to 45.3% in the register's most recent wave (2024, DO
    # 2610) — and AEAT 2.37M landlord declarants ≈ 11.9% of the model's 19.87M household
    # anchor [docs/sources.md, model-spec §7]. They differ roughly three-to-four-fold because
    # they measure different things, so they bracket rather than band this column; what is
    # missing is the EFF wealth-percentile gradient that would say where inside the bracket
    # the model should sit (redesign spec §9 retrieval list).
    #
    # Today the model has no entry margin at all (a household buyer always becomes an
    # owner-occupier), which is the defect this column exists to measure. It does NOT follow
    # that the share can only fall: measured 0.27116 at tick 1 against 0.27097 at tick 60
    # (3-seed mean, a 0.02pp move), rising on roughly half the tick transitions, because
    # dissolution hands whole estates to surviving households.
    landlord_ids = {
        u.owner_id
        for u in all_units
        if u.owner_id >= 0
        and u.owner_id in state.households
        and state.households[u.owner_id].unit_id != u.id
    }
    row["landlord_households"] = len(landlord_ids)
    row["landlord_household_share"] = len(landlord_ids) / n_hh
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
    # the 30% line, the other threshold the Spanish literature reports on: EPF 2022 puts
    # 38.2% of renting households above it (2015: 33.0%; 2021: 43.1%) and 60.5% above it once
    # utilities are added — the Ley 12/2023 "sobreesfuerzo" definition, which this model has
    # no utilities to compute [Romero-Jordán, Funcas 104 ch.6 cuadros 2 and 4]
    row["rent_burden_over_30_share"] = (
        float(np.mean([b > 0.30 for b in burdens_market])) if burdens_market else 0.0
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
    # the declared/non-declared line units are sorted on (agents/landlord.is_covered). With no
    # cap in force the whole zone reads as "declared", so the split degenerates to the pooled
    # series and nothing spurious is reported.
    cap_coverage = state.config.policy.cap_coverage
    # inter-zone moves recorded by engine._demography this tick, keyed (origin, destination)
    migration = state.tick_events.get("migration", {})
    access_ok = access_total = 0
    zone_weights: dict[ZoneType, float] = {}
    for zone in ZoneType:
        zs = state.zones[zone]
        z = zone.value
        zone_units = [u for u in all_units if u.zone is zone]
        row[f"price_{z}"] = zs.price_index
        row[f"rent_{z}"] = zs.rent_index
        row[f"rent_transacted_{z}"] = zs.rent_transacted
        # gross rental yield, EMERGENT (model-spec §9 target 9). `ZoneConfig.gross_yield` is
        # an initial condition only; the ladder the model then produces is a prediction, and
        # the one observable that tells us whether the landlord's reservation rule is right.
        row[f"gross_yield_{z}"] = zs.rent_index * 12.0 / max(zs.price_index, 1.0)
        row[f"reference_rent_{z}"] = zs.reference_rent
        # the uncapped clearing rent landlords compare a cap against (= rent index when free)
        row[f"shadow_rent_{z}"] = zs.shadow_rent
        row[f"rental_tightness_{z}"] = state.tick_events.get("rental_tightness", {}).get(
            zone, float("nan")
        )
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
        # net internal migration, model-scale households/tick (model-spec §9 target 12).
        # Spain's net internal flow runs rural→metro; the current rule can only produce the
        # opposite sign, which is why this is measured before it is fixed.
        row[f"net_migration_{z}"] = sum(
            n for (_, dest), n in migration.items() if dest is zone
        ) - sum(n for (origin, _), n in migration.items() if origin is zone)
        # New contracts split by REGULATORY SEGMENT, so a partial-coverage cap can be read.
        # The pooled median mixes declared and non-declared municipalities and moves with the
        # mix, not with either segment's rent: at coverage 0.42 it comes out ABOVE baseline
        # while both segments' own rents behave sensibly, because withdrawals in the declared
        # part push demand into the free part and shift the median toward it (validation.md
        # T7). Reported per zone; NaN where the segment had no contract this tick. Public
        # units are excluded from both, as everywhere else in the rent series.
        declared, free = [], []
        for r in rentals:
            unit = state.stock.units[r.unit_id]
            if unit.zone is not zone or unit.is_public:
                continue
            adjusted = r.rent / max(unit.quality, 1e-9)
            side = declared if unit.declaration_draw < cap_coverage else free
            side.append(adjusted)
        row[f"rent_new_declared_{z}"] = float(np.median(declared)) if declared else float("nan")
        row[f"rent_new_free_{z}"] = float(np.median(free)) if free else float("nan")
        row[f"new_leases_declared_{z}"] = len(declared)
        row[f"new_leases_free_{z}"] = len(free)
        row[f"seasonal_{z}"] = sum(1 for u in zone_units if u.tenure is Tenure.SEASONAL)
        zone_hhs = [h for h in hhs if h.zone is zone]
        zone_weights[zone] = len(zone_hhs) / n_hh
        # tenure mix by zone — the ranking leg of model-spec §9 target 1, which was stubbed
        # out in the validation fixture and so went unmeasured. Renting is a metro tenure in
        # Spain: T 0.27–0.30 / S ≈0.20 / R 0.12–0.17 [model-spec §7; household-tenant §6].
        row[f"tenant_share_{z}"] = sum(
            1 for h in zone_hhs if h.status is HouseholdStatus.TENANT
        ) / max(1, len(zone_hhs))
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
    row["gross_yield_national"] = row["rent_national"] * 12.0 / max(row["price_national"], 1.0)
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
