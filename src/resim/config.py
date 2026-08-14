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
    # long-run price elasticity of starts IN THIS ZONE. Land availability is what separates
    # the zones: a tensioned metro core cannot answer a price rise with much new supply, a
    # rural municipality can. Without this gradient nothing holds the zone price ladder
    # apart — every zone converges on its own households' credit ceiling and the T/R price
    # ratio collapses (measured: 3.2× → 1.85× over 60 ticks, with rural ending LESS
    # affordable than the secondary city). Household-share-weighted average is held at the
    # sourced national 0.45–0.58 [Caldera&Johansson/BdE]; the split across zones is a
    # Saiz-style land-availability gradient [guess — developer §7.3, weakest evidence block]
    supply_elasticity: float
    # non-resident cash demand present [Registradores concentration, household-owner §6]
    foreign_overlay: bool
    # dwellings per household IN THIS ZONE: occupied plus EMPTY, excluding tourist rentals
    # (held separately in `seasonal_share`). Sets the zone's initial vacant pool, of which
    # `withheld_share` is off-market. Derived from the INE Censo-2021 empty-dwelling ladder by
    # municipality size — empty as a share of the local park: ≤5k hab 24.6%, 5–10k 17.8%,
    # 10–20k 15.6%, 20–40k 13.1%, 40–150k ≈11.5%, 150–500k ≈8%, 500k–1M 7.0%, >3M 6.3%
    # (national 13.2% of a 24.96M park) [INE Censo 2021 / viviendas por intensidad de uso,
    # via Funcas Estudios 104 ch.1 cuadro 1 — medium]. Zones map to municipality-size bands:
    # tensioned ≈ >300k, secondary ≈ 20k–300k, rural ≈ <20k, so upH = 1/(1−empty share).
    # The ORDERING (rural ≫ secondary > tensioned) is the sourced claim and the reason this
    # is per-zone at all: half the Spanish empty stock sits in municipalities under 20k
    # inhabitants holding 28% of the population, i.e. vacancy is where demand is not.
    units_per_household: float = 1.07
    # share of the zone's initial vacant pool that is WITHHELD — off the market, so no
    # landlord can let it: second homes, strategic holdouts, and above all stock that is
    # empty because it is in the wrong place and in the wrong condition. Funcas 104 ch.1 is
    # explicit that the Spanish empty stock "can hardly serve as an umbrella" for unmet
    # demand: provinces growing slower than the 3.1% national household rate hold >60% of it
    # while the fastest-growing (>4.7%) hold 5%, and much of it needs substantial
    # rehabilitation [INE/Funcas 104 ch.1 — the GRADIENT is sourced, the levels are a guess].
    # Without the gradient the model lets rural vacancy absorb latent demand (measured:
    # seeker share 6.2% → 5.2%), i.e. it reproduces the umbrella the source rules out.
    #
    # LEVELS ARE CALIBRATED, and deliberately so: they hold the *mobilisable* vacant stock,
    # (upH − 1) × (1 − withheld_share), at the 0.0455 per household that was already
    # calibrated against the §9 moments before the empty stock was recognised zone by zone.
    # So recognising it changes what the model *counts*, not what the market can *use* —
    # which is precisely the source's claim. Solve (upH − 1)(1 − w) = 0.0455 per zone.
    withheld_share: float = 0.35
    # tourist-rental (VUT) stock at init, as a share of the zone's residential stock. Held
    # OUTSIDE `units_per_household`, which counts occupied plus empty dwellings only (INE
    # classifies tourist and second-home use as separate categories) — so these
    # are additional dwellings, and converting them back (tourist-restriction lever) genuinely
    # adds housing. National weighted ≈1.8%, matching 329,764 VUT (INE, Nov 2025) against
    # 18.54M dwellings; the tensioned value is the central-Barcelona district figure of
    # 2.8–2.9% of dwellings [INE via El País; tourist-rental-restriction §2 — medium. The
    # dossier also records hotspot census sections at 20–30%, which this abstraction cannot
    # represent: a zone mean, not a hotspot]
    seasonal_share: float = 0.0


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
    # new households' income vs population median: <1 = young penalty (EFF <35: 32k vs
    # 36.1k ⇒ ~0.89); boom scenarios with working-age migration use 1.0 [EFF2024 — medium]
    formation_income_factor: float = 0.9


@dataclass(frozen=True)
class StockConfig:
    """The initial housing stock: how many units, of what quality, where, owned by whom."""

    # NATIONAL ANCHOR for dwellings per household, excl. tourist rentals. The value the
    # engine applies is per-zone (`ZoneConfig.units_per_household`), because the empty stock
    # is not spread evenly — this field is the household-share-weighted mean those zone values
    # must reproduce, asserted in tests/test_validation.py. 1.12 ≈ weighted mean of the
    # INE-derived zone ladder (1.075 / 1.124 / 1.242); the empty-only national basis is
    # 1 + 3.29M empty / 18.9M households = 1.174 [INE Censo 2021 via Funcas 104 ch.1 — medium].
    # Vacancy itself stays emergent, validated against the 6–9% urban Censo figure in the
    # tensioned zone and against the rural ≫ urban ordering [INE via investor-small §6].
    units_per_household: float = 1.12
    median_value: float = 170_000.0  # € national median main residence [EFF2024 — high]
    # m² average dwelling. Used as the developer's build size, so it scales hard cost per
    # dwelling: 90 m² × 1,105–1,323 €/m² ⇒ ≈100–130k € of hard cost [Afi's national average
    # dwelling size, Funcas Estudios 104 ch.5 gráfico 4 note — medium; was an 80 m² guess].
    # Consequence measured, docs/validation.md: rural new build (0.5 × 170,000 = 944 €/m²)
    # falls below the sourced hard-cost floor of 1,080 €/m², so the rural zone only builds
    # once prices have risen ≈15% — which is realistic, and tightens the zone price ladder.
    avg_size_m2: float = 90.0
    # individuals' share of rental stock; range .85–.92 [investor-small §1 — high].
    # NOT an input: it is an emergent cross-check, reported as `small_landlord_rental_share`
    # in metrics.py and asserted in tests/test_validation.py.
    small_landlord_share_target: tuple[float, float] = (0.85, 0.92)
    # public social rental as a share of the TOTAL stock (318k of 18.54M dwellings = 1.7%);
    # range .015–.025 [Housing Europe 2025 / MIVAU Boletín, public-housing §3 — medium].
    # Basis matters: the engine converts this to a share of *rented* units at init.
    public_rental_share: float = 0.017
    # metro concentration of the public stock at init (T/S/R) — social housing is urban
    # [public-housing §3 — guess; mirrors the policy lever's delivery weights]
    public_zone_weights: tuple[float, float, float] = (0.6, 0.3, 0.1)


@dataclass(frozen=True)
class MarketConfig:
    """Rules of exchange: search frictions, listing duration, transaction costs, stickiness."""

    # /tick ask cut while unsold; range .02–.05 [sticky-ask evidence 2008–13 — guess]
    ask_decay: float = 0.03
    # reserve = ask×(1−d), d drawn per listing ~U(lo, hi) (model-spec §5) [guess]
    max_seller_discount_lo: float = 0.05
    max_seller_discount_hi: float = 0.15
    max_listing_ticks: int = 6  # withdraw after; range 4–8 [guess]
    overbid_sigma: float = 0.04  # bid dispersion around ask in sealed bid [guess; calibrated]
    # λ, weight on trailing growth; range 0.5–0.9 [household-owner §6 — low; THE cycle knob]
    expectation_momentum: float = 0.7
    long_run_growth: float = 0.005  # /tick nominal anchor ≈2%/yr [exogenous income growth]
    price_index_smoothing: float = 0.3  # weight of tick median transaction in index update [guess]
    # notary/registry etc., fraction of price, on top of ITP [Fotocasa triangulated — high]
    buyer_fees: float = 0.02
    # required gross yield over bond in the tensioned zone — observed spread there is
    # ~2pp (yield 4.7–5.6 vs bond ~3); appreciation expectations substitute for yield
    # [idealista/BdE RBA structure, investor-small §6 — medium]
    landlord_required_spread: float = 0.02
    # extra spread outside tensioned metros, range .01–.02: reproduces the observed
    # 5.2 / 7.0 / 8.0 zone yield ladder [BdE RBA gradient — medium]
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
    # per-tick partial adjustment of the offered rate toward euríbor+spread. Calibrated to
    # BdE DO 2312: ~32% of a shock passed through after 16 months (5.33 ticks), i.e.
    # 1−(1−p)^5.33 = 0.32 ⇒ p ≈ 0.07 [BdE DO 2312 — medium]
    pass_through: float = 0.07
    max_ltv: float = 0.80  # bank practice, no legal cap; 24% bunching at 0.80 [BdE IEF — high]
    max_dsti: float = 0.35  # payment/net income; range .30–.40 [bank §6 — high]
    term_years: int = 25  # avg 24–26 [INE — medium]
    # NOTE: the state-guarantee LTV boost is a *policy* field (PolicyConfig.guarantee_ltv_boost)
    # and reaches the lending caps as an explicit `ltv_boost` argument to bank.max_price /
    # bank.loan_terms. It is deliberately not duplicated here.


@dataclass(frozen=True)
class DeveloperConfig:
    """Supply side. The lag is what generates cycles — keep it explicit."""

    construction_lag: int = 8  # ticks, visado→CFO; range 6–10 [Euroval, developer §6 — high]
    # min expected margin on cost; range .15–.20 [IMPLICA/KPMG — medium]
    margin_threshold: float = 0.175
    # National long-run price elasticity of starts, d ln(starts)/d ln(price); range .45–.58+
    # [Caldera&Johansson/BdE — medium]. The elasticity the developer actually applies is
    # per-zone (ZoneConfig.supply_elasticity) because land availability differs; this field
    # is the national anchor those zone values must average to, asserted in
    # tests/test_validation.py. Not read by any agent.
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
    # total guarantee envelope at model scale: the ICO line is €2.5bn *once*, not per tick.
    # 2.5e9 / 2000 households-per-model-household [demand-subsidy §5 — high]
    guarantee_budget: float = 1_250_000.0
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
                supply_elasticity=0.25,  # metro core: little developable land left
                foreign_overlay=True,
                units_per_household=1.075,  # INE: 6.3–7.7% empty in >300k-hab municipalities
                withheld_share=0.39,  # strongest demand: most of the empty stock is usable
                seasonal_share=0.028,  # central-district VUT share, 2.8–2.9
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
                supply_elasticity=0.50,  # national average
                foreign_overlay=False,
                units_per_household=1.124,  # INE: 11.1–13.1% empty in 20k–300k-hab
                withheld_share=0.63,
                seasonal_share=0.010,
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
                supply_elasticity=1.00,  # abundant land: supply answers price
                foreign_overlay=False,
                units_per_household=1.242,  # INE: 15.6–24.6% empty in <20k-hab
                withheld_share=0.81,  # weak demand + rehabilitation need: mostly unusable
                seasonal_share=0.005,
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
