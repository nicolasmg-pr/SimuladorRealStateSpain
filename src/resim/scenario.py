"""Policy levers — the "what if" layer.

A Scenario is a named set of interventions applied to a baseline SimConfig at given ticks.
This is the module the UI drives: the user picks levers, we produce a Scenario, run it,
and diff its metrics against the baseline run.

Each lever maps 1:1 to a docs/policies/*.md §5 block; disputed magnitudes are fields
with documented ranges, defaulting to midpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .config import SimConfig, ZoneType


@dataclass(frozen=True)
class Intervention:
    """One policy change, applied from `start_tick` onward."""

    name: str
    start_tick: int

    def apply(self, config: SimConfig) -> SimConfig:
        """Return a new config with this intervention folded in. Never mutates."""
        raise NotImplementedError


@dataclass(frozen=True)
class RentCap(Intervention):
    """Ley 12/2023-style cap (policies/rent-cap.md §5). CCAA switch = zones field."""

    name: str = "rent_cap"
    start_tick: int = 8
    zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED,)
    cap_reference_discount: float = 0.05  # 0–0.10
    supply_response_elasticity: float = 1.0  # 0–2 — the three-studies parameter
    compliance: float = 0.85  # 0.25–0.95
    seasonal_segment_capped: bool = False
    # share of the zone inside DECLARED municipalities (PolicyConfig.cap_coverage). 1.0 =
    # Cataluña-2024-like (≈90% of Catalan population declared); ≈0.42 = Spain's 317
    # municipalities of Jul 2026 (9.3M people) mapped onto the model's tensioned zone
    coverage: float = 1.0

    def apply(self, config: SimConfig) -> SimConfig:
        cfg = config.with_policy(
            rent_cap_enabled=True,
            rent_cap_zones=self.zones,
            cap_reference_discount=self.cap_reference_discount,
            cap_compliance=self.compliance,
            cap_coverage=self.coverage,
            seasonal_segment_capped=self.seasonal_segment_capped,
        )
        market = replace(cfg.market, rental_supply_elasticity=self.supply_response_elasticity)
        return replace(cfg, market=market)


@dataclass(frozen=True)
class TransactionTax(Intervention):
    """ITP change (policies/transaction-tax.md §5)."""

    name: str = "transaction_tax"
    start_tick: int = 8
    itp_delta: float = 0.02  # pp as fraction of price, every buyer, in `zones`
    zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED, ZoneType.SECONDARY, ZoneType.RURAL)
    # buyer-type surcharges on top (PolicyConfig): large investor / legal persons — the
    # Catalan 20% TPO on whole-building and gran-tenedor purchases is ≈ +0.10 over the 10%
    # general rate; non-resident overlay — the stalled "100% tax on non-EU buyers" bill is
    # ≈ +0.90. Both default to 0 so the plain lever behaves as before.
    investor_delta: float = 0.0
    foreign_delta: float = 0.0

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(
            itp_delta=self.itp_delta,
            itp_zones=self.zones,
            itp_investor_delta=self.investor_delta,
            itp_foreign_delta=self.foreign_delta,
        )


@dataclass(frozen=True)
class VacancyTax(Intervention):
    """IBI surcharge on empty homes (policies/vacancy-tax.md §5)."""

    name: str = "vacancy_tax"
    start_tick: int = 8
    rate: float = 0.005  # 0.001–0.03 of unit value /yr
    detection: float = 0.15  # 0–0.9 /yr

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(vacancy_tax_rate=self.rate, vacancy_detection=self.detection)


@dataclass(frozen=True)
class PublicHousing(Intervention):
    """Public/protected construction programme (policies/public-housing.md §5)."""

    name: str = "public_housing"
    start_tick: int = 8
    units_per_tick: int = 6  # ≈48k/yr real at 1:2000 scale
    crowding_out: float = 0.33  # 0–0.8
    delivery_lag: int = 20  # 12–32 ticks
    rent_discount: float = 0.5  # rent vs market 0.4–0.7

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(
            public_units_per_tick=self.units_per_tick,
            crowding_out_share=self.crowding_out,
            public_delivery_lag=self.delivery_lag,
            public_rent_discount=self.rent_discount,
        )


@dataclass(frozen=True)
class TouristRestriction(Intervention):
    """VUT phase-out (policies/tourist-rental-restriction.md §5)."""

    name: str = "tourist_restriction"
    start_tick: int = 8
    phaseout_rate: float = 0.25  # /yr share of seasonal stock extinguished
    conversion_share: float = 0.30  # 0.10–0.50 returns to long-term market

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(
            vut_phaseout_rate=self.phaseout_rate,
            vut_conversion_share=self.conversion_share,
        )


@dataclass(frozen=True)
class DemandSubsidy(Intervention):
    """Avales ICO + rent subsidy (policies/demand-subsidy.md §5)."""

    name: str = "demand_subsidy"
    start_tick: int = 8
    guarantee_ltv_boost: float = 0.20
    guarantee_eligible_share: float = 0.25  # sweep 0.05–0.50
    # € liquid-wealth ceiling on eligibility — the ICO line's 2026 addenda added a €150k
    # net-wealth cap (BOE 2 Jul 2026). `inf` reproduces the pre-2026 instrument.
    guarantee_wealth_cap: float = 150_000.0
    rent_subsidy_month: float = 0.0  # 250–300 when active
    rent_subsidy_eligible_share: float = 0.0  # 0.006–0.20

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(
            guarantee_ltv_boost=self.guarantee_ltv_boost,
            guarantee_eligible_share=self.guarantee_eligible_share,
            guarantee_wealth_cap=self.guarantee_wealth_cap,
            rent_subsidy_month=self.rent_subsidy_month,
            rent_subsidy_eligible_share=self.rent_subsidy_eligible_share,
        )


@dataclass(frozen=True)
class LandRelease(Intervention):
    """Finalist land release + faster permits (policies/land-release.md §5)."""

    name: str = "land_release"
    start_tick: int = 8
    extra_units_per_tick: int = 4
    release_lag: int = 40  # 20–60 ticks — no short-run price effect is a validation target
    permit_lag_delta: int = 0  # −6–0 ticks

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(
            extra_land_units_per_tick=self.extra_units_per_tick,
            land_release_lag=self.release_lag,
            permit_lag_delta=self.permit_lag_delta,
        )


@dataclass(frozen=True)
class HouseholdFormation(Intervention):
    """Exogenous demographic path — household formation is an input, not a result.

    The baseline holds formation flat at the observed ≈240k/yr (INE ECP: +226k in 2025, +239k
    y/y to July 2026). Every INE household projection is front-loaded and then fades, but the
    *level* has been cut hard between vintages — see `INE_HOUSEHOLD_PROJECTIONS`. Use
    `ine_household_projection()` to lay one vintage's three steps out over a run; this class is
    the single step (and doubles as the "what if formation is X" lever).
    """

    name: str = "household_formation"
    start_tick: int = 0
    formation_per_tick: int = 27  # ≈216k/yr real at 1:2,000
    formation_income_factor: float | None = None  # None = leave the baseline value

    def apply(self, config: SimConfig) -> SimConfig:
        changes: dict = {"formation_per_tick": self.formation_per_tick}
        if self.formation_income_factor is not None:
            changes["formation_income_factor"] = self.formation_income_factor
        return replace(config, population=replace(config.population, **changes))


# INE Proyección de Hogares, by vintage: net new households per tick (1:`metrics.SCALE`, i.e.
# ×8,000 for households/yr) over three consecutive five-year blocks. Rounded to integers
# because formation is a Poisson count; the rounding costs ≤4k/yr.
#
# The vintages disagree by a factor of three in the first block, which is the point of keeping
# all of them (bias-control rule: disagreement is data, docs/plan.md). The June 2026 revision
# alone removed 1.5M households from the 15-year horizon; migration assumptions dominate.
#   2022–2037: 215k → 190k → 140k/yr, 2023–27 / 2028–32 / 2033–37
#              [INE via Funcas 104 ch.1 §3 gráfico 7]
#   2024–2039: 333k → 228k → 177k/yr (1,667,063 / 1,140,804 / 883,284 over 2024–29 / 2029–34 /
#              2034–39; 19.31M → 23.00M households) [INE nota de prensa 24 Jun 2024]
#   2026–2041: 205k → 139k → 93k/yr (1,024,156 / 696,381 / 463,511 over 2026–31 / 2031–36 /
#              2036–41; 19.76M → 21.94M households, size 2.49 → 2.43)
#              [INE nota de prensa 17 Jun 2026 — docs/kb-refresh-2026-09.md §2]
INE_HOUSEHOLD_PROJECTIONS: dict[str, tuple[int, int, int]] = {
    "2022-2037": (27, 24, 18),
    "2024-2039": (42, 29, 22),
    "2026-2041": (26, 17, 12),
}
INE_LATEST_VINTAGE = "2026-2041"


def ine_household_projection(
    start_tick: int = 0, vintage: str = INE_LATEST_VINTAGE
) -> tuple[HouseholdFormation, ...]:
    """One INE projection vintage as three consecutive steps of 20 ticks (5 years).

    Interventions are applied in order by `Scenario.config_at`, so a later step overrides an
    earlier one and the sequence reads as a path. Default is the latest vintage; pass an
    earlier key of `INE_HOUSEHOLD_PROJECTIONS` to run the demand path Spain was planning on
    before the cut.
    """
    steps = INE_HOUSEHOLD_PROJECTIONS[vintage]
    return tuple(
        HouseholdFormation(start_tick=start_tick + 20 * i, formation_per_tick=per_tick)
        for i, per_tick in enumerate(steps)
    )


@dataclass(frozen=True)
class RateShock(Intervention):
    """Euríbor path shift — the 2022–23 signature reproducer."""

    name: str = "rate_shock"
    start_tick: int = 8
    euribor: float = 0.04

    def apply(self, config: SimConfig) -> SimConfig:
        return replace(config, credit=replace(config.credit, euribor=self.euribor))


@dataclass(frozen=True)
class Scenario:
    """A baseline plus an ordered set of interventions."""

    name: str
    baseline: SimConfig
    interventions: tuple[Intervention, ...] = ()

    def config_at(self, tick: int) -> SimConfig:
        """Config as it stands at `tick`, with all interventions active by then applied."""
        cfg = self.baseline
        for iv in self.interventions:
            if tick >= iv.start_tick:
                cfg = iv.apply(cfg)
        return cfg
