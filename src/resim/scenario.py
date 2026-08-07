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

    def apply(self, config: SimConfig) -> SimConfig:
        cfg = config.with_policy(
            rent_cap_enabled=True,
            rent_cap_zones=self.zones,
            cap_reference_discount=self.cap_reference_discount,
            cap_compliance=self.compliance,
            seasonal_segment_capped=self.seasonal_segment_capped,
        )
        market = replace(cfg.market, rental_supply_elasticity=self.supply_response_elasticity)
        return replace(cfg, market=market)


@dataclass(frozen=True)
class TransactionTax(Intervention):
    """ITP change (policies/transaction-tax.md §5)."""

    name: str = "transaction_tax"
    start_tick: int = 8
    itp_delta: float = 0.02  # pp as fraction of price
    zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED, ZoneType.SECONDARY, ZoneType.RURAL)

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(itp_delta=self.itp_delta, itp_zones=self.zones)


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
    rent_subsidy_month: float = 0.0  # 250–300 when active
    rent_subsidy_eligible_share: float = 0.0  # 0.006–0.20

    def apply(self, config: SimConfig) -> SimConfig:
        return config.with_policy(
            guarantee_ltv_boost=self.guarantee_ltv_boost,
            guarantee_eligible_share=self.guarantee_eligible_share,
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
