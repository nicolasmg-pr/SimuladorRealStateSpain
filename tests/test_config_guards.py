"""Config guards — internal consistency of `SimConfig.baseline()`. NOT validation.

These two checks were rows in the `docs/validation.md` target table, sitting beside measured
moments with a ✓. They are not measured moments: neither one runs an engine. They assert that
config fields agree with the config anchors they were derived from — that the per-zone ladders
still average to their national value and still run the right way round.

That is worth keeping. A zone ladder silently drifting away from its anchor is a real defect,
and these catch it. But it is a claim about the config's internal arithmetic, not evidence that
the model reproduces Spain, and the target table is reserved for the second kind (spec §2,
finding 8: "two target rows are config identities"). Moved here 2026-09-12, phase A, with no
assertion weakened — what changed is what the check is said to prove.
"""

import pytest

from resim.config import SimConfig, ZoneType


def test_zone_supply_elasticities_average_to_the_national_anchor():
    """The per-zone land-availability split is a guess; its national average is not.

    Zone elasticities may be re-shaped freely, but their household-share-weighted mean has
    to stay inside the sourced 0.45–0.58 band [Caldera&Johansson/BdE], and the gradient has
    to run the right way (metro cores least able to answer a price rise with supply).
    """
    cfg = SimConfig.baseline()
    weighted = sum(z.household_share * z.supply_elasticity for z in cfg.zones)
    assert 0.45 <= weighted <= 0.58, f"national elasticity drifted to {weighted:.3f}"
    by_zone = {z.zone: z.supply_elasticity for z in cfg.zones}
    assert by_zone[ZoneType.TENSIONED] < by_zone[ZoneType.SECONDARY] < by_zone[ZoneType.RURAL]


def test_zone_stock_ratios_hold_their_anchors():
    """Two invariants on the per-zone dwellings-per-household ladder.

    1. Its household-weighted mean reproduces the national anchor in `StockConfig`, the same
       contract the supply elasticities are held to.
    2. The *mobilisable* part — (upH − 1) × (1 − withheld_share) — is deliberately equal
       across zones: recognising the empty stock zone by zone changes what the model counts,
       not what its market can use, which is precisely what Funcas 104 ch.1 argues (that
       stock "can hardly serve as an umbrella" for unmet demand). If a future calibration
       moves the mobilisable stock, it should do so on purpose and for a reason.
    """
    cfg = SimConfig.baseline()
    weighted = sum(z.household_share * z.units_per_household for z in cfg.zones)
    assert abs(weighted - cfg.stock.units_per_household) < 0.01, f"drifted to {weighted:.3f}"
    by_zone = {z.zone: z.units_per_household for z in cfg.zones}
    assert by_zone[ZoneType.RURAL] > by_zone[ZoneType.SECONDARY] > by_zone[ZoneType.TENSIONED]
    usable = [(z.units_per_household - 1.0) * (1.0 - z.withheld_share) for z in cfg.zones]
    assert max(usable) - min(usable) < 0.004, f"mobilisable stock diverged: {usable}"


def test_zone_income_multipliers_average_to_the_national_anchor():
    """`income_multiplier` is "× national household income", so it must average to 1.0.

    It did not. Until 2026-09-14 the guessed gradient 1.15 / 1.00 / 0.80 weighted by household
    share came to **1.0275**: the model's households were 2.75% richer than the national anchor
    they were said to be drawn against, by construction, and nothing checked it. The supply
    elasticities and the stock ratios were both held to their anchors by the guards above; the
    income ladder was not.

    The gradient is now INE ECV table 59952 (*renta neta media por hogar* by grado de
    urbanización) renormalised to this model's household shares, so this is exact rather than
    banded — it is arithmetic on config, not a measurement.
    """
    cfg = SimConfig.baseline()
    weighted = sum(z.household_share * z.income_multiplier for z in cfg.zones)
    assert weighted == pytest.approx(1.0, abs=1e-3), f"income gradient averages {weighted:.4f}"


def test_zone_income_gradient_matches_the_published_ladder():
    """The metro/rural income ratio must be the one ECV publishes, not a wider invented one.

    ADRH on the model's own zone
    cut: **1.205** (ECV DEGURBA gave 1.211). The model asserted 1.15 / 0.80 = 1.437 — it had the
    metro household earning 44% more than the rural one where the published figure is 21%, and
    the published ratio has been narrowing (1.29 in 2019 to 1.21 in 2025), not widening.

    Asserted loosely at ±0.02: renormalising to the model's zone shares is a linear rescaling
    and preserves ratios exactly, so this only guards against someone re-widening the ladder.
    """
    cfg = SimConfig.baseline()
    by_zone = {z.zone: z.income_multiplier for z in cfg.zones}
    ratio = by_zone[ZoneType.TENSIONED] / by_zone[ZoneType.RURAL]
    assert ratio == pytest.approx(1.205, abs=0.02), f"metro/rural income ratio is {ratio:.3f}"
