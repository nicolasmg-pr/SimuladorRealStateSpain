"""Simulation parameters — the knobs of the world, before any policy is applied.

Split deliberately from `scenario.py`: config describes how the market works,
a scenario describes what we do to it.

Every field carries: unit, source (dossier §, see docs/actors and docs/policies) and a
confidence tag. `guess` = unsourced, per the bias-control rule in docs/plan.md.
Disputed values default to the midpoint of their documented range; the range itself is
recorded in the comment and exposed in the UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum


class ZoneType(Enum):
    TENSIONED = "tensioned"  # tensioned metro (Madrid/Barcelona cores + hot coast)
    SECONDARY = "secondary"  # secondary city
    RURAL = "rural"


@dataclass(frozen=True)
class ZoneConfig:
    """Zone-type differentiation. Multipliers apply to national anchors.

    Zone multipliers are the weakest evidence block (developer §7.3) — most are guesses,
    flagged for sensitivity analysis.
    """

    zone: ZoneType
    household_share: float  # share of all households at init [Censo approx — guess]
    tenant_share: float  # share of zone households renting [ECV 2024, household-tenant §6 — medium]
    income_multiplier: float  # × national income distribution [guess]
    price_multiplier: float  # × national median dwelling value [guess from €/m² press]
    gross_yield: float  # /yr, rent/price at init [idealista+BdE RBA, investor-small §6 — high]
    itp_rate: float  # fraction of price, buyer transaction tax [OCU/CCAA, government §6 — medium]
    # share of zone rental stock held by gran tenedor [investor-large §6 — medium/guess]
    large_investor_share: float
    # € hard construction cost [UVE/ACR 1105–1323 national, developer §6 — high; zone mult guess]
    cost_per_m2: float
    # land as fraction of final new-build price [CNMC 25–50%, developer §6 — medium]
    land_share: float
    # non-resident cash demand present [Registradores concentration, household-owner §6]
    foreign_overlay: bool


@dataclass(frozen=True)
class PopulationConfig:
    """How many actors of each type exist, and how their attributes are distributed."""

    n_households: int = 10_000  # 1:2,000 of 19.9M Spanish households [EPA, household-owner §1]
    income_median: float = 36_100.0  # €/yr gross [EFF2024 — high]
    income_sigma: float = 0.70  # lognormal sigma, implies mean≈46.3k [EFF2024 — high]
    saving_rate: float = 0.13  # share of income saved /yr [INE CNTR 13–14% — low]
    owner_wealth_median: float = 60_000.0  # € liquid (excl. housing) [EFF2024-derived — medium]
    # € net wealth tenants [EFF 2022, household-tenant §6 — high]
    tenant_wealth_median: float = 2_200.0
    wealth_sigma: float = 1.2  # lognormal sigma of owner liquid wealth [guess]
    # fatter tail: aspiring buyers sit in the top decile of tenant wealth [EFF dispersion — guess]
    tenant_wealth_sigma: float = 1.8
    # new households/tick, model scale ≈240k/yr real; range 135k–260k [EPA/INE — high as range]
    formation_per_tick: int = 30
    dissolution_rate: float = 0.35  # exits as share of formation [guess]
    # non-resident cash buyers, share of purchases; range .138–.184 incl. residents
    # [Registradores/Notariado — high as range]
    foreign_purchase_share: float = 0.08
    # × zone median value; non-res pay +76–79% €/m² [Notariado CIEN — high]
    foreign_budget_multiplier: float = 1.6
    tenant_move_prob: float = 0.06  # /tick; range 0.04–0.08 [derived, household-tenant §6 — low]
    owner_move_prob: float = 0.011  # /tick; range 0.010–0.0125 [CED/BdE — medium]
    # min of accepted rent/income screening [household-tenant §6 — medium]
    max_rent_burden_lo: float = 0.30
    # max of accepted rent/income screening [household-tenant §6 — medium]
    max_rent_burden_hi: float = 0.40
    # /tick, prob a constraint-passing tenant/seeker tries to buy; the credit screen does the
    # rationing [guess; calibrated]
    buy_attempt_prob: float = 0.50
    # € initial wealth of new households incl. family transfers (30–40% of FTBs get help,
    # household-owner §6) [guess]
    seeker_wealth_median: float = 15_000.0


@dataclass(frozen=True)
class StockConfig:
    """The initial housing stock: how many units, of what quality, where, owned by whom."""

    # dwellings incl. vacant, excl. 2nd homes [Censo-derived — guess]
    units_per_household: float = 1.10
    vacancy_rate: float = 0.07  # urban 6–9% [INE via investor-small §6 — medium]
    median_value: float = 170_000.0  # € national median main residence [EFF2024 — high]
    avg_size_m2: float = 80.0  # m² [Censo approx — guess]
    # individuals' share of rental stock; range .85–.92 [investor-small §1 — high]
    small_landlord_share: float = 0.90
    # share of stock; range .015–.033 [MIVAU/Provivienda — medium]
    public_rental_share: float = 0.02


@dataclass(frozen=True)
class MarketConfig:
    """Rules of exchange: search frictions, listing duration, transaction costs, stickiness."""

    # /tick ask cut while unsold; range .02–.05 [sticky-ask evidence 2008–13 — guess]
    ask_decay: float = 0.03
    max_seller_discount: float = 0.10  # reserve = ask×(1−this); range .05–.15 [guess]
    max_listing_ticks: int = 6  # withdraw after; range 4–8 [guess]
    overbid_sigma: float = 0.04  # bid dispersion around ask in sealed bid [guess; calibrated]
    # λ, weight on trailing growth; range 0.5–0.9 [household-owner §6 — low; THE cycle knob]
    expectation_momentum: float = 0.7
    long_run_growth: float = 0.005  # /tick nominal anchor ≈2%/yr [exogenous income growth]
    price_index_smoothing: float = 0.3  # weight of tick median transaction in index update [guess]
    # notary/registry etc., fraction of price, on top of ITP [Fotocasa triangulated — high]
    buyer_fees: float = 0.02
    # required gross yield over bond, range .03–.05 [investor-small §6 — guess]
    landlord_required_spread: float = 0.04
    # extra spread in low-income zones, range .01–.02 [BdE RBA gradient — medium]
    landlord_zone_risk_premium: float = 0.015
    # Δln offered/Δln regulated rent; RANGE 0.0–2.0 — the three-Catalonia-studies parameter
    # [rent-cap §4 — high as range]
    rental_supply_elasticity: float = 1.0
    # share of capped new contracts diverted; range .05–.25 [Incasòl — medium]
    seasonal_evasion_share: float = 0.15
    default_rate: float = 0.05  # actual tenant non-payment /yr; range .03–.07 [Arag/OESA — medium]
    # landlord perceived over actual default; range 1.5–3 [guess]
    perceived_risk_markup: float = 2.0


@dataclass(frozen=True)
class CreditConfig:
    """Lending environment: base rate, LTV cap, DTI cap, term."""

    euribor: float = 0.022  # /yr, 12m euríbor level [exogenous path via scenario]
    spread: float = 0.011  # pp over euríbor; range .009–.012 [bank §6 — medium]
    # per-tick adjustment of offered rate toward euríbor+spread (~32%/16m) [BdE DO 2312 — medium]
    pass_through: float = 0.15
    max_ltv: float = 0.80  # bank practice, no legal cap; 24% bunching at 0.80 [BdE IEF — high]
    max_dsti: float = 0.35  # payment/net income; range .30–.40 [bank §6 — high]
    term_years: int = 25  # avg 24–26 [INE — medium]
    guarantee_ltv_boost: float = 0.0  # policy: ICO aval lifts LTV toward 1.0 [demand-subsidy §5]
    guarantee_eligible_share: float = 0.0  # share of first-time buyers eligible [demand-subsidy §5]


@dataclass(frozen=True)
class DeveloperConfig:
    """Supply side. The lag is what generates cycles — keep it explicit."""

    construction_lag: int = 8  # ticks, visado→CFO; range 6–10 [Euroval, developer §6 — high]
    # min expected margin on cost; range .15–.20 [IMPLICA/KPMG — medium]
    margin_threshold: float = 0.175
    # long-run price elasticity of starts; range .45–.58+ [Caldera&Johansson/BdE — medium]
    supply_elasticity: float = 0.5
    # national capacity ≈190k/yr real at model scale; range 150k–220k [CNC claim — low]
    max_starts_per_tick: int = 24
    base_starts_per_tick: int = 14  # ≈112k/yr real, 2024–25-like baseline flow [MIVAU — high]
    presale_share: float = 0.40  # pre-sales gate .30–.50 [developer §6 — high]
    new_build_premium: float = 1.15  # new-build price vs zone median [guess]


@dataclass(frozen=True)
class PolicyConfig:
    """Active policy levers — the state the government actor enacts.

    Baseline = Spain without the tensioned-zone machinery switched on.
    Interventions (scenario.py) return modified copies. Ranges per docs/policies/*.md §5.
    """

    # rent cap (rent-cap.md)
    rent_cap_enabled: bool = False
    rent_cap_zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED,)
    cap_reference_discount: float = 0.05  # cap below prevailing market rent; range 0–.10
    cap_compliance: float = 0.85  # share of new contracts actually at/below cap; range .25–.95
    within_contract_update: float = 0.025  # /yr IRAV-style cap on sitting rents; range .02–.03
    seasonal_segment_capped: bool = False  # Jan-2026-style closure of the evasion segment
    # transaction tax (transaction-tax.md)
    itp_delta: float = 0.0  # pp change on zone ITP rate
    itp_zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED, ZoneType.SECONDARY, ZoneType.RURAL)
    # vacancy tax (vacancy-tax.md)
    vacancy_tax_rate: float = 0.0  # /yr fraction of unit value; range .001–.03
    vacancy_detection: float = 0.0  # /yr prob a liable vacant unit is billed; range 0–.9
    vacancy_min_portfolio: int = 4  # statutory scope [government §6]
    # public housing (public-housing.md)
    public_units_per_tick: int = 0  # started per tick, all zones pooled by zone weights
    public_zone_weights: tuple[float, float, float] = (0.6, 0.3, 0.1)  # T/S/R
    public_delivery_lag: int = 20  # ticks; range 12–32
    public_rent_discount: float = 0.5  # rent vs market; range .4–.7
    crowding_out_share: float = 0.33  # private starts displaced per public start; range 0–.8
    # tourist rental (tourist-rental-restriction.md)
    vut_phaseout_rate: float = 0.0  # /yr share of tourist units extinguished
    vut_conversion_share: float = 0.30  # returned to long-term market; range .10–.50
    # demand subsidy (demand-subsidy.md)
    guarantee_ltv_boost: float = 0.0  # extra LTV via state guarantee; ICO = .20
    guarantee_eligible_share: float = 0.0  # of first-time buyers; sweep .05–.50
    rent_subsidy_month: float = 0.0  # €/month to eligible tenants
    rent_subsidy_eligible_share: float = 0.0  # of under-35 tenants; sweep .006–.20
    # land release (land-release.md)
    extra_land_units_per_tick: int = 0  # finalist-equivalent capacity added after lag
    land_release_lag: int = 40  # ticks; range 20–60
    permit_lag_delta: int = 0  # ticks off construction lag; range −6–0


@dataclass(frozen=True)
class SimConfig:
    """Full input to one run."""

    seed: int
    ticks: int
    population: PopulationConfig
    stock: StockConfig
    market: MarketConfig
    credit: CreditConfig
    developer: DeveloperConfig
    policy: PolicyConfig
    zones: tuple[ZoneConfig, ...] = field(default_factory=tuple)

    @classmethod
    def baseline(cls, seed: int = 42, ticks: int = 60) -> SimConfig:
        """The reference world every scenario is compared against."""
        zones = (
            ZoneConfig(
                zone=ZoneType.TENSIONED,
                household_share=0.45,
                tenant_share=0.28,  # ECV: 27–30
                income_multiplier=1.15,
                price_multiplier=1.6,
                gross_yield=0.052,  # 4.7–5.6
                itp_rate=0.10,
                large_investor_share=0.10,  # 8–15 guess
                cost_per_m2=1_450.0,  # ×1.2 national — guess
                land_share=0.45,  # 40–50
                foreign_overlay=True,
            ),
            ZoneConfig(
                zone=ZoneType.SECONDARY,
                household_share=0.35,
                tenant_share=0.20,
                income_multiplier=1.0,
                price_multiplier=0.9,
                gross_yield=0.070,  # 6.5–7.5
                itp_rate=0.08,
                large_investor_share=0.02,
                cost_per_m2=1_200.0,
                land_share=0.30,  # 25–35
                foreign_overlay=False,
            ),
            ZoneConfig(
                zone=ZoneType.RURAL,
                household_share=0.20,
                tenant_share=0.145,  # 12–17
                income_multiplier=0.80,
                price_multiplier=0.5,
                gross_yield=0.080,  # 7–9
                itp_rate=0.06,
                large_investor_share=0.0,
                cost_per_m2=1_080.0,
                land_share=0.20,  # 15–25
                foreign_overlay=False,
            ),
        )
        return cls(
            seed=seed,
            ticks=ticks,
            population=PopulationConfig(),
            stock=StockConfig(),
            market=MarketConfig(),
            credit=CreditConfig(),
            developer=DeveloperConfig(),
            policy=PolicyConfig(),
            zones=zones,
        )

    def zone(self, zone: ZoneType) -> ZoneConfig:
        for z in self.zones:
            if z.zone is zone:
                return z
        raise KeyError(zone)

    def with_policy(self, **changes) -> SimConfig:
        """New config with policy fields replaced. Never mutates."""
        return replace(self, policy=replace(self.policy, **changes))
