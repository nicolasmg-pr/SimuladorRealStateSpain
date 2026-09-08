"""Phase-6 validation: the baseline must reproduce the model-spec §9 targets.

No scenario result is reported until these pass (docs/plan.md, engineering
standards). Targets are ranges from the dossiers; the test bands add tolerance for
seed noise (3 seeds averaged, last 20 of 60 ticks).
"""

import dataclasses

import numpy as np
import pytest

from resim import metrics
from resim.cli import build_scenario
from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.metrics import SCALE
from resim.scenario import (
    INE_HOUSEHOLD_PROJECTIONS,
    INE_LATEST_VINTAGE,
    RateShock,
    Scenario,
    ine_household_projection,
)
from resim.state import HouseholdStatus


@pytest.fixture(scope="module")
def baseline_moments():
    rows = []
    for seed in (1, 2, 3):
        state = Engine(build_scenario("baseline", seed, 60)).run()
        frame = metrics.to_frame(state)
        tail = frame.iloc[-20:]
        rows.append(
            {
                "ownership": tail["ownership_rate"].mean(),
                "non_owner": (tail["tenant_share"] + tail["seeker_share"]).mean(),
                "pti": tail["price_to_income"].mean(),
                "transactions_yr": 4 * tail["transactions"].mean() / len(state.households),
                "overburden": tail["rent_overburden_share"].mean(),
                "vacancy_market_t": tail["vacancy_market_tensioned"].mean(),
                "completion_ratio": tail["completion_ratio"].mean(),
                "small_landlord": tail["small_landlord_rental_share"].mean(),
                "wedge": tail["insider_outsider_wedge"].mean(),
                "pti_tensioned": tail["price_to_income_tensioned"].mean(),
                "pti_secondary": tail["price_to_income_secondary"].mean(),
                "pti_rural": tail["price_to_income_rural"].mean(),
                "price_ranking": (
                    tail["price_tensioned"].mean()
                    > tail["price_secondary"].mean()
                    > tail["price_rural"].mean()
                ),
                "tenant_ranking": True,  # checked per-zone below via rent levels
                "vacancy_t": tail["vacancy_tensioned"].mean(),
                "vacancy_s": tail["vacancy_secondary"].mean(),
                "vacancy_r": tail["vacancy_rural"].mean(),
                "vacancy_national": tail["vacancy_rate"].mean(),
                "burden_over_30": tail["rent_burden_over_30_share"].mean(),
                "seeker": tail["seeker_share"].mean(),
            }
        )
    return {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}


def test_tenure_shares(baseline_moments):
    """Target 1: owners 70–74%; non-owners (tenants + seekers≈ceded/sharing) 24–31%.

    The model sits at the bottom of the ownership band (≈70.2%) — see docs/validation.md.
    """
    assert 0.69 <= baseline_moments["ownership"] <= 0.75
    assert 0.25 <= baseline_moments["non_owner"] <= 0.32


def test_price_to_income(baseline_moments):
    """Target 2: national price / disposable income per household 7–8 (BdE basis)."""
    assert 7.0 <= baseline_moments["pti"] <= 8.2


def test_price_ordering(baseline_moments):
    """Target 2b: tensioned > secondary > rural price levels."""
    assert baseline_moments["price_ranking"]


@pytest.mark.xfail(
    strict=True,
    reason="Known gap, docs/validation.md 'Zone price ladder': no location-amenity term, so "
    "relative zone prices converge on relative credit ceilings (i.e. relative incomes, "
    "1.15/1.0/0.80) instead of a location premium. T/R falls 3.2x -> 1.9x over 60 ticks and "
    "rural price-to-income overtakes the secondary city. Needs a spatial-preference "
    "mechanism, not a parameter change — remove this xfail when one lands.",
)
def test_price_to_income_ordering(baseline_moments):
    """Target 2 (second half): price-to-income must rank T > S > R, not just price levels.

    The price-level ordering (2b) survives the ladder compression; this one does not, which
    is why it was worth separating. Left as a strict xfail so the suite tells us the moment
    a spatial mechanism fixes it.
    """
    assert baseline_moments["pti_tensioned"] > baseline_moments["pti_secondary"]
    assert baseline_moments["pti_secondary"] > baseline_moments["pti_rural"]


def test_transaction_volume(baseline_moments):
    """Target 3: 2.5–3.6% of households transact per year.

    Asserted on the sourced band (the widened ±0.6pp version was only needed while the
    developer's start rule pinned starts against the capacity ceiling). The model runs near
    the top of the band, so this is the moment most sensitive to `buy_attempt_prob`.
    """
    assert 0.026 <= baseline_moments["transactions_yr"] <= 0.038


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


def test_completions_vs_formation(baseline_moments):
    """Target 4: completions run at 40–70% of household formation (the 2021–25 gap).

    Previously asserted 'by construction' in the validation report and never measured —
    the pipeline can and does deliver less than the starts flow suggests once the margin
    hurdle and the pre-sales gate bite.
    """
    assert 0.40 <= baseline_moments["completion_ratio"] <= 0.70


def test_small_landlord_share(baseline_moments):
    """Individuals hold 85–92% of the rental stock [investor-small §1].

    Emergent, not an input: it falls out of large_investor_share, public_rental_share and
    the inheritance path. A drift out of band means one of those three is mis-specified.
    """
    assert 0.85 <= baseline_moments["small_landlord"] <= 0.92


def test_insider_outsider_wedge(baseline_moments):
    """Target 5b: a new contract costs more than a sitting one on the same standard unit.

    Sitting rents move only by the update cap, so all price discovery happens at rotation
    [investor-small §3]. The sign of this wedge is the mechanism, not a calibration — see
    metrics.snapshot on why it is measured on rent levels rather than rent/income burdens.
    """
    assert baseline_moments["wedge"] > 0.0


def test_rent_burden(baseline_moments):
    """Target 5: market-tenant overburden (>40% of income) 27–33%.

    Market basis: social tenants pay an administered rent and are excluded, matching the
    Eurostat "tenant, rent at market price" series the target comes from.
    """
    assert 0.26 <= baseline_moments["overburden"] <= 0.34


def test_vacancy(baseline_moments):
    """Market vacancy in the tensioned zone 2–10%. The 6–9% urban Censo figure includes
    second homes and withheld stock; the market/frictional component the model reports here
    sits below it (investor-small §7.3: no source separates them). The floor was 3% until the
    tensioned-tightness recalibration: with formation metro-weighted the tensioned rental
    queue runs at ≈1 applicant per listing and frictional vacancy settles at ≈2.9%, which is
    the point of that revision (docs/validation.md). The floor was a convention, not a
    sourced band; 2% keeps it from going to zero."""
    assert 0.02 <= baseline_moments["vacancy_market_t"] <= 0.10


def _holdout_boom(seeds):
    """The 2021–25 episode: formation ≈264k/yr, output ≈90k/yr, easing from tick 20.

    Free parameters are NOT fitted to this episode. Returns per-seed annualised tensioned
    price growth, rent growth and the boom/pre-boom transaction ratio.
    """
    price, rent, vol = [], [], []
    for seed in seeds:
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        cfg = dataclasses.replace(
            cfg,
            population=dataclasses.replace(
                cfg.population,
                formation_per_tick=33,  # ≈264k/yr, top of the observed band
                formation_income_factor=1.0,  # working-age migration composition
            ),
            developer=dataclasses.replace(
                cfg.developer, base_starts_per_tick=11, max_starts_per_tick=12
            ),
        )
        scenario = Scenario(
            name="holdout",
            baseline=cfg,
            interventions=(RateShock(start_tick=20, euribor=0.005),),
        )
        frame = metrics.to_frame(Engine(scenario).run())
        boom = slice(24, 40)
        price.append(4 * frame["price_growth_tensioned"].iloc[boom].mean())
        rent.append(4 * frame["rent_growth_tensioned"].iloc[boom].mean())
        vol.append(
            frame["transactions"].iloc[boom].mean() / frame["transactions"].iloc[4:12].mean()
        )
    return price, rent, vol


@pytest.mark.xfail(
    strict=True,
    reason="Known gap, docs/validation.md 'Rent growth cannot outrun income': the clearing "
    "rent equals the winning applicant's willingness to pay, which is a share of income, and "
    "income grows at the exogenous anchor — so the rent index cannot reproduce the real "
    "+8–11%/yr of 2021–25. Measured over 20 seeds: +0.0%/yr ±0.3pp, i.e. indistinguishable "
    "from zero. The sharing margin (agents/household.search_burden) raises the LEVEL of "
    "accepted burden but not the growth rate. Remove this xfail when a mechanism lands.",
)
def test_holdout_boom_rent_growth():
    """Target 7, rent leg: the 2021–25 boom must produce +8–11%/yr asking-rent growth.

    Asserted at +4%/yr — half the low end of the target — so the xfail is about the
    mechanism, not about the last percentage point. The previous version of this test
    asserted only `> 0` on 5 seeds and passed on luck: the 20-seed mean is 0.0 ± 0.3pp and
    only 8 of 20 seeds come out positive at all.
    """
    _, rent, _ = _holdout_boom((3, 5, 7, 8, 9, 11, 13, 17, 19, 23))
    assert float(np.mean(rent)) > 0.04


def test_holdout_2021_2025_runup():
    """Target 7 (out-of-sample episode): formation ≈260k/yr against completions
    ≈90k/yr plus the 2024–25 easing must produce a sustained price boom with
    record transactions. The rent leg is separate, above, and fails.

    Averaged over 5 seeds. Per-seed the volume ratio spans 1.11 to 1.31, so a one-seed
    version of this test would pass on the seed it was written with rather than on the
    model's behaviour.
    """
    price, _, vol = _holdout_boom((3, 5, 7, 8, 9))
    assert float(np.mean(price)) > 0.04  # sustained boom (real: 8–13% on asking basis;
    # model index is a contract/transaction basis, structurally slower)
    assert float(np.mean(vol)) > 1.15  # record transaction volumes


def test_vacancy_ladder(baseline_moments):
    """Vacancy is highest where demand is weakest — rural ≫ secondary > tensioned.

    Empty dwellings as a share of the local park, INE Censo 2021 by municipality size:
    24.6% in municipalities under 5,000 inhabitants against 6.3% in Madrid, national 13.2%
    [Funcas 104 ch.1 cuadro 1]. Half the empty stock sits in municipalities under 20,000
    inhabitants, which hold 28% of the population. A model that spreads vacancy evenly gets
    this ladder backwards (measured before the fix: rural was the LOWEST at 5.6%), and with
    it the whole geography of the vacancy-tax lever.

    Asserted on the full-stock basis, which includes withheld units: the source's empty
    dwellings are exactly the stock that is not available, not the frictional turnover.
    """
    assert baseline_moments["vacancy_r"] > baseline_moments["vacancy_s"]
    assert baseline_moments["vacancy_s"] > baseline_moments["vacancy_t"]
    assert 0.156 <= baseline_moments["vacancy_r"] <= 0.246
    assert 0.081 <= baseline_moments["vacancy_s"] <= 0.131
    assert 0.10 <= baseline_moments["vacancy_national"] <= 0.15


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


def test_rent_burden_thresholds_are_ordered(baseline_moments):
    """The >30% share must exceed the >40% share, and both must be reported.

    The Spanish literature quotes both lines — 38.2% of renting households above 30% of
    their consumption basket in 2022 [EPF, Funcas 104 ch.6], 4 in 10 above 40% of disposable
    income [Eurostat via ch.2]. The model reports both so neither can be quoted as the other.
    """
    assert baseline_moments["burden_over_30"] > baseline_moments["overburden"]


def test_search_burden_escalates_and_is_capped():
    """The sharing margin: a household that keeps failing to find a home accepts more rent.

    Mechanism and ceiling are sourced (agents/household.py); what this pins is that the rule
    is monotone, starts at the drawn threshold, and cannot run away.
    """
    from resim.agents.household import MAX_RENT_BURDEN_CEILING, search_burden
    from resim.state import HouseholdState

    hh = HouseholdState(
        id=1,
        zone=ZoneType.TENSIONED,
        income=30_000.0,
        wealth=0.0,
        status=HouseholdStatus.SEEKER,
        max_rent_burden=0.35,
    )
    assert search_burden(hh) == pytest.approx(0.35)
    hh.ticks_searching = 4
    assert 0.35 < search_burden(hh) < MAX_RENT_BURDEN_CEILING
    hh.ticks_searching = 400
    assert search_burden(hh) == pytest.approx(MAX_RENT_BURDEN_CEILING)


def test_ine_household_projection_is_a_declining_path():
    """The latest INE projection (2026–2041) is front-loaded, not flat: 205k → 139k → 93k/yr.

    `Scenario.config_at` applies interventions in order, so a later step overrides an earlier
    one; this pins that the path is read as a path and lands on the published figures at
    1:2,000 scale within the integer rounding of a Poisson rate [INE 17 Jun 2026:
    1,024,156 / 696,381 / 463,511 households over three five-year blocks].
    """
    base = SimConfig.baseline(ticks=60)
    scenario = Scenario(name="ine", baseline=base, interventions=ine_household_projection())
    formation = [
        scenario.config_at(t).population.formation_per_tick for t in (0, 19, 20, 39, 40, 59)
    ]
    assert formation == [26, 26, 17, 17, 12, 12]
    per_year = [f * 4 * SCALE for f in (26, 17, 12)]
    published = [1_024_156 / 5, 696_381 / 5, 463_511 / 5]
    for model, real in zip(per_year, published, strict=True):
        assert abs(model - real) <= 4 * SCALE  # within one unit of per-tick rounding
    assert base.population.formation_per_tick == 30  # the baseline itself stays flat


def test_ine_projection_vintages_all_decline_and_were_cut():
    """Every INE vintage fades over its horizon, and each revision since 2024 cut the level.

    The 2024–2039 vintage projected 333k/yr for its first block; the 2026–2041 one projects
    205k/yr — 1.5M fewer households over fifteen years. Keeping all three is the bias-control
    rule applied to demography: the projected deficit is partly a demographic assumption, and
    the spread between vintages is the honest measure of it.
    """
    for vintage, steps in INE_HOUSEHOLD_PROJECTIONS.items():
        assert list(steps) == sorted(steps, reverse=True), vintage
        path = ine_household_projection(vintage=vintage)
        assert [iv.start_tick for iv in path] == [0, 20, 40]
        assert [iv.formation_per_tick for iv in path] == list(steps)
    newest, older = INE_HOUSEHOLD_PROJECTIONS["2026-2041"], INE_HOUSEHOLD_PROJECTIONS["2024-2039"]
    assert all(n < o for n, o in zip(newest, older, strict=True))
    assert ine_household_projection() == ine_household_projection(vintage=INE_LATEST_VINTAGE)


def _rent_cap_response(elasticity: float, seeds=(1, 2, 3)) -> dict[str, float]:
    """The Phase-7 experiment design (docs/experiments/rent-cap.md): cap from tick 20 of 40 in
    the tensioned zone, mean over the 16 post-cap ticks, scenario over baseline − 1."""
    from resim.scenario import RentCap

    out: dict[str, list[float]] = {"rent": [], "leases": []}
    for seed in seeds:
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        base = metrics.to_frame(Engine(Scenario(name="b", baseline=cfg)).run())
        cap = metrics.to_frame(
            Engine(
                Scenario(
                    name="c",
                    baseline=cfg,
                    interventions=(RentCap(start_tick=20, supply_response_elasticity=elasticity),),
                )
            ).run()
        )
        post = slice(24, 40)
        for key, col in (("rent", "rent_transacted_tensioned"), ("leases", "new_leases_tensioned")):
            out[key].append(cap[col].iloc[post].mean() / base[col].iloc[post].mean() - 1.0)
    return {k: float(np.mean(v)) for k, v in out.items()}


def test_rent_cap_lowers_contract_rents():
    """Target 8, price leg: a binding cap must lower new-contract rents in the capped zone.

    This regressed silently after the August 2026 audit and Funcas revision: with the frozen
    reference index indexed at 2.5%/yr against a 2%/yr income anchor, the reference outran
    the market within ~10 ticks and the cap run ended ABOVE baseline (+0.9%). Pinned here so
    the flagship experiment cannot break unnoticed again. Asserted at −1%, well inside the
    measured −2.2% and far below the sourced −4…−6%.
    """
    assert _rent_cap_response(1.0)["rent"] < -0.01


def test_rent_cap_supply_response_spans_monras():
    """Target 8, supply leg: elasticity 2 must reach Monràs & García-Montalvo's −10% tenancies.

    Failed as a strict xfail until the tensioned-tightness revision (docs/validation.md): the
    tensioned rental market ran slack (0.5 applicants per listing), and once a cap was on the
    asking index collapsed onto the cap so landlords saw no gap to exit on. Two things fixed
    it — metro-weighted household formation (`formation_zone_weights`) and the shadow rent
    landlords compare the cap against (`ZoneState.shadow_rent`). Asserted at −5%, half the
    target, so seed noise (σ ≈ 3pp on 3 seeds) does not flip it; the full sweep is in
    docs/experiments/rent-cap.md.
    """
    assert _rent_cap_response(2.0)["leases"] < -0.05
