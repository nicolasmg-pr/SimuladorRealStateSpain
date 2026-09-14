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
                "gy_tensioned": tail["gross_yield_tensioned"].mean(),
                "gy_secondary": tail["gross_yield_secondary"].mean(),
                "gy_rural": tail["gross_yield_rural"].mean(),
                "gy_contract_national": tail["gross_yield_contract_national"].mean(),
                "price_ranking": (
                    tail["price_tensioned"].mean()
                    > tail["price_secondary"].mean()
                    > tail["price_rural"].mean()
                ),
                "rent_ranking": (
                    tail["rent_tensioned"].mean()
                    > tail["rent_secondary"].mean()
                    > tail["rent_rural"].mean()
                ),
                "price_ratio_tr": (tail["price_tensioned"] / tail["price_rural"]).mean(),
                "price_ratio_ts": (tail["price_tensioned"] / tail["price_secondary"]).mean(),
                "tenant_ranking": (
                    tail["tenant_share_tensioned"].mean()
                    > tail["tenant_share_secondary"].mean()
                    > tail["tenant_share_rural"].mean()
                ),
                "arrears": tail["arrears_share"].mean(),
                "foreclosure_rate": tail["foreclosure_rate"].mean(),
                "dacion_share": tail["dacion_share"].mean(),
                "vacancy_t": tail["vacancy_tensioned"].mean(),
                "vacancy_s": tail["vacancy_secondary"].mean(),
                "vacancy_r": tail["vacancy_rural"].mean(),
                "vacancy_national": tail["vacancy_rate"].mean(),
                "burden_over_30": tail["rent_burden_over_30_share"].mean(),
                "seeker": tail["seeker_share"].mean(),
                "foreign_share": tail["foreign_purchase_share"].mean(),
            }
        )
    return {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}


def test_tenure_shares(baseline_moments):
    """Target 1: owners 70–74%; non-owners (tenants + seekers≈ceded/sharing) 24–31%.

    The model sits at the bottom of the ownership band (≈70.2%) — see docs/validation.md.
    """
    assert 0.69 <= baseline_moments["ownership"] <= 0.75
    assert 0.25 <= baseline_moments["non_owner"] <= 0.32


def test_tenant_share_ranking(baseline_moments):
    """Target 1, ranking leg: tenant share must rank T > S > R.

    This leg was carried in the fixture as a hardcoded `True` with a comment claiming it was
    "checked per-zone below via rent levels" — it was not, by that test or any other, so the
    leg was unmeasured. Now measured on `tenant_share_*` (metrics.snapshot): 31.4 / 22.7 /
    17.0% on 3 seeds, and it holds on each seed separately.

    Ranking only, not levels. Renting is a metro tenure in Spain and the ordering is not in
    doubt [model-spec §7: T 0.27–0.30 / S ≈0.20 / R 0.12–0.17; household-tenant §6], but the
    model's tensioned leg runs above that band, so a level gate here would be a claim the
    zone abstraction cannot support (a tensioned zone holding 45% of households is not
    Madrid). Asserted at exactly 1.0 — the fixture averages a per-seed boolean, so anything
    less would let one seed of three carry the ranking.
    """
    assert baseline_moments["tenant_ranking"] == 1.0


def test_price_to_income(baseline_moments):
    """Target 2: national price / disposable income per household 7–8 (BdE basis)."""
    assert 7.0 <= baseline_moments["pti"] <= 8.2


def test_price_ordering(baseline_moments):
    """Target 2b: tensioned > secondary > rural price levels."""
    assert baseline_moments["price_ranking"]


def test_price_to_income_ordering(baseline_moments):
    """Target 2 (second half): price-to-income must rank T > S > R, not just price levels.

    A strict xfail until the location premium landed (model-spec §5b): with nothing making a
    location intrinsically worth more, rural demand had no ceiling of its own, rural prices
    ran to twice replacement cost and rural price-to-income (7.4) passed the secondary city
    (6.7). Now 8.5 / 6.3 / 4.8 on 3 seeds.
    """
    assert baseline_moments["pti_tensioned"] > baseline_moments["pti_secondary"]
    assert baseline_moments["pti_secondary"] > baseline_moments["pti_rural"]


def test_zone_price_ladder_holds(baseline_moments):
    """The tensioned/rural price ratio must still be a ladder at the end of a 60-tick run.

    It is the model's own initial gradient (`price_multiplier` 1.6 / 0.9 / 0.5 ⇒ 3.2) that has
    to survive its dynamics; before the location premium it decayed to 1.9. Spain's provincial
    extremes are wider still (Madrid €3,565/m² against Ciudad Real €776, ≈4.6 — Tinsa 2026Q1),
    but the model's zones are broad aggregates (a tensioned zone holding 45% of households is
    not Madrid province), so the target is that the ladder holds, not that it reaches the
    provincial spread. Asserted loosely: seed spread on this ratio is ±0.1.
    """
    assert baseline_moments["price_ratio_tr"] > 2.6
    assert baseline_moments["price_ratio_ts"] > 1.3


def test_national_entry_yield_matches_the_bank_of_spain(baseline_moments):
    """Target 9, national leg, on the CONTRACT basis (model-spec §13.7).

    Decided 2026-09-12: yields are judged on contracts, not on portal asks. Portal asks are
    not transactions — negotiated down, edited, re-posted, withdrawn without trace.

    The band is BdE's own estimate of the **entry** (new-contract) gross yield since 2015,
    6.5–7.5% [DO 2432 §3.3]. It is deliberately NOT the RBA's 2.90%: the RBA is a *stock*
    yield over contracts signed across many years under LAU terms and capped updates, and the
    landlord decision this model contains is an entry decision on the marginal unit at
    today's terms. Both are contract-basis; they are different objects.

    Measured on `rent_transacted` (median new-contract rent), not `rent_index` (asking).
    Asserted on the sourced band without widening: this leg passes on it as it stands, and a
    tolerance added where none is needed would only hide a future drift.
    """
    assert 0.065 <= baseline_moments["gy_contract_national"] <= 0.075


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-11: rural gross yield runs to ≈17.2% against a sourced 7–9%. "
    "required_rent pins the yield floor to price, rural rental supply has no entry "
    "margin (investor skips rural, households never buy to let) and downward-only "
    "migration funnels every priced-out seeker into it. Fixed by the total-return "
    "hurdle and buy-to-let entry (spec §7.1, §7.3 — phase B).",
)
def test_zone_gross_yield_ladder(baseline_moments):
    """Target 9: the gross rental yield ladder must EMERGE, not be imposed.

    Sourced levels, idealista + BdE RBA [model-spec §7, investor-small §6]:
    tensioned 4.7–5.6%, secondary 6.5–7.5%, rural 7–9%. Bands widened by 0.5pp on each
    side for seed noise, the same tolerance convention as the other zone targets.

    This is a target only because §7.1 of the redesign makes the yield an output.
    `ZoneConfig.gross_yield` is an initial condition; what the model does with it afterwards
    is a prediction, and right now the prediction is wrong.
    """
    assert 0.042 <= baseline_moments["gy_tensioned"] <= 0.061
    assert 0.060 <= baseline_moments["gy_secondary"] <= 0.080
    assert 0.065 <= baseline_moments["gy_rural"] <= 0.095


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-11: rural asking rent overtakes the tensioned index around tick 35-40 "
    "and ends ≈13.5% above it on 3 seeds. The location premium discounts purchase "
    "willingness in rural but nothing discounts rent acceptance (model-spec §5b), while "
    "downward-only migration funnels seekers there and the sharing margin lifts accepted "
    "burden to 0.55. Fixed by bidirectional migration and buy-to-let entry "
    "(spec §7.3, §7.5 — phase B).",
)
def test_rent_level_ordering(baseline_moments):
    """Target 11: asking rent levels must rank tensioned > secondary > rural.

    The price ladder is gated (targets 2b-2d) and the rent ladder is not, which is how a
    rural rent index above the metro one survived unnoticed. Spanish rent levels rank
    strictly the other way at every published basis [idealista, SERPAVI, EPF regional
    averages — €675/month Madrid against €277 Extremadura, Funcas 104 ch.5].

    Asserted at exactly 1.0, not on truthiness. `rent_ranking` is a per-seed boolean and the
    fixture collapses it with `float(np.mean(...))`, so any nonzero mean is truthy: a partial
    fix that put one seed of three in the right order would read as "fixed", the strict xfail
    would flip, and the target would be deleted while two seeds still had rural above the
    metro. == 1.0 means ALL THREE seeds rank T > S > R, not an average that is merely
    nonzero. This target exists to flip in phase B, once, and for the right reason.
    """
    assert baseline_moments["rent_ranking"] == 1.0


def test_interior_migration_runs_out_of_the_metro():
    """Target 12, interior leg: the tensioned zone must be a net LOSER of interior migrants.

    Mapping B (model-spec §13.8): tensioned = provincial capitals + non-capital municipalities
    above 100,000. INE EVR 2015–21 and EMCR 69753 2021–24 give that zone a negative interior
    net in every year from 2017 — −33,393 (2019), −140,179 (2020), −55,195 (2024) — and the
    sign is robust across all three candidate mappings and both statistics.

    This is a SIGN test, and it is only meaningful because the rule can now produce either
    sign: the old downward-only rule asserted this by construction. Raise the metro income
    multiplier 35% and inbound flows appear (see `test_interior_migration_is_bidirectional`).
    """
    nets = []
    for seed in (1, 2, 3):
        frame = metrics.to_frame(Engine(build_scenario("baseline", seed, 60)).run())
        nets.append(frame["net_migration_tensioned"].sum())
    assert float(np.mean(nets)) < 0
    # and the flows must close: nobody enters or leaves the country through this rule
    frame = metrics.to_frame(Engine(build_scenario("baseline", 1, 60)).run())
    total = sum(frame[f"net_migration_{z.value}"].sum() for z in ZoneType)
    assert total == pytest.approx(0.0, abs=1e-6), f"interior flows do not close: {total}"


def test_interior_migration_is_bidirectional():
    """The sign must be an OUTCOME of the comparison, not a property of the code.

    The rule this replaced could only move households down the ladder, so its direction was
    unfalsifiable — no parameter, policy or shock could reverse it. This asserts the opposite
    property: widen the metro income advantage and households move IN.

    Uses a 35% income shock because that is well outside any plausible calibration; the point
    is that the mechanism admits the other sign, not that 35% is a realistic figure.
    """
    import dataclasses

    inbound = 0.0
    for seed in (1, 2, 3):
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        cfg = dataclasses.replace(
            cfg,
            zones=tuple(
                dataclasses.replace(z, income_multiplier=z.income_multiplier * 1.35)
                if z.zone is ZoneType.TENSIONED
                else z
                for z in cfg.zones
            ),
        )
        frame = metrics.to_frame(Engine(Scenario(name="b", baseline=cfg)).run())
        inbound += frame["migration_in_tensioned"].sum()
    assert inbound > 0, "no household ever moves into the metro under any income gradient"


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14: re-opened by section 7.4. It had closed under the section 7.1 hurdle, "
    "which lowered metro rents enough for inbound moves to clear the friction; capitalising "
    "the investor's bid and de-anchoring the foreign buyer moved metro prices and rents "
    "back, and inbound interior flows return to zero. The underlying deficiency is "
    "unchanged and is recorded at engine._demography: the only pull toward the metro is the "
    "income ratio, and what is missing is where the JOB is. That it can be closed and re- "
    "opened by unrelated price-side changes is itself the evidence that it is being held "
    "shut by a coincidence rather than by a mechanism. Needs spec 7.5's amenity term with "
    "its own identification.",
)
def test_interior_migration_has_gross_flows_both_ways():
    """Gross interior flows into the tensioned zone must be non-zero at the baseline."""
    inbound = 0.0
    for seed in (1, 2, 3):
        frame = metrics.to_frame(Engine(build_scenario("baseline", seed, 60)).run())
        inbound += frame["migration_in_tensioned"].sum()
    assert inbound > 0


def test_total_migration_leg_of_target_12_is_not_yet_modelled():
    """Target 12's TOTAL leg needs international arrivals, which are not a mechanism yet.

    The old test here asserted that cumulative net INTERIOR migration into the tensioned zone
    must be positive, and carried a strict xfail saying the model had the sign inverted. Both
    were wrong: INE EVR/EMCR give that zone a negative interior net in every year from 2017
    under every candidate mapping, so the test was registering correct behaviour as a failure
    (docs/validation.md, "Phase-B finding-11 correction"). It is deleted rather than re-xfailed
    — an xfail on a claim the data contradicts is not a record of a defect, it is a defect in
    the record.

    Target 12 is now two claims (model-spec §13.8). The interior leg is gated above by
    `test_interior_migration_runs_out_of_the_metro`. The total leg — interior plus
    international arrivals, positive at baseline and negative in a 2020-like shock — cannot be
    tested until arrivals exist as a mechanism, and they do not: `formation_zone_weights` still
    fuses domestic household formation and immigration into one fitted vector. This test
    asserts that honestly rather than leaving a silent gap.
    """
    state = Engine(build_scenario("baseline", 1, 20)).run()
    assert "international_arrivals" not in state.tick_events, (
        "arrivals now exist as a mechanism — replace this placeholder with the real total-"
        "migration target: positive at baseline, negative under a 2020-like shock"
    )


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14, ATTRIBUTION CORRECTED the same day. 2.23% against an observed 6.5-8% for "
    "the non-resident basis (not the ~17% all-foreigner share - resident and non-resident "
    "foreigners are different objects and the model's overlay is non-resident only). The "
    "first reason written here blamed the budget anchor's growth rate, on the retrieval's "
    "own diagnosis: the anchor compounded at 2%/yr, which is Spanish CPI to within 0.1pp, "
    "while the observed non-resident buyer ran +3.69%/yr real. That was correct about the "
    "anchor and WRONG about the binding constraint. The growth rate is now sourced at "
    "+5.86%/yr nominal (CIEN Tabla 1C, calibration window) and the share moved 2.28% to "
    "2.23% - i.e. not at all. Measured instead: 310 foreign offers over a 40-tick run "
    "against 3,471 transactions, so every offer winning would give 8.9%, and they win 31%. "
    "The constraint is LISTING SUPPLY in the one zone the overlay operates in, not budget. "
    "Behind that sits a zone-abstraction problem the spec did not anticipate: Spanish non- "
    "resident purchases concentrate in coastal and island markets - Alicante, Malaga, "
    "Balears - and this model's three zones have no coastal type, so the overlay is "
    "confined to a tensioned metro zone that is not where non-residents actually buy. "
    "Raising foreign_arrivals_per_tick would not fix it either; it would just make more "
    "offers lose. Closing this needs either a coastal zone or an overlay that reaches more "
    "than one zone, and that is a specification decision, not a calibration.",
)
def test_emergent_non_resident_share_matches_registradores(baseline_moments):
    """Target: the non-resident share of purchases, now an OUTPUT of the arrival stream.

    Non-residents are ≈8% of Spanish purchases — all foreigners run 16.0% (Registradores ERI
    2026Q2) to 18.4% (Notariado 2S 2025) and non-residents are ≈44% of that. Before phase B
    this was an input (`foreign_purchase_share × recent sales`) and could not be wrong; it is
    now produced by a constant exogenous stream and can be.

    Asserted on a wide 6–11% band: the anchor is a share and the seed spread on it is large.
    """
    assert 0.06 <= baseline_moments["foreign_share"] <= 0.11


def test_transaction_volume(baseline_moments):
    """Target 3: 2.5–3.6% of households transact per year.

    Asserted on the sourced band (the widened ±0.6pp version was only needed while the
    developer's start rule pinned starts against the capacity ceiling). The model runs near
    the top of the band, so this is the moment most sensitive to `buy_attempt_prob`.
    """
    assert 0.026 <= baseline_moments["transactions_yr"] <= 0.038


def test_completions_vs_formation(baseline_moments):
    """Target 4: completions run at 40–70% of household formation (the 2021–25 gap).

    Previously asserted 'by construction' in the validation report and never measured —
    the pipeline can and does deliver less than the starts flow suggests once the margin
    hurdle and the pre-sales gate bite.
    """
    assert 0.40 <= baseline_moments["completion_ratio"] <= 0.70


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14: phase B replaced two guessed zone parameters with sourced ones - the "
    "income gradient (INE ECV 59952, 1.15/1.00/0.80 to 1.085/0.950/0.896) and the tenant "
    "share (INE ECV 60181, 0.28/0.20/0.145 to 0.237/0.186/0.108, the rural cell having been "
    "inferred). Attributed on 3 seeds by running each change alone: the tenure change alone "
    "takes it to 0.842, the income change alone leaves it at 0.856. 0.838 against a 0.85 "
    "floor. A smaller rental market concentrates it. NOT re-fitted - these are published "
    "values replacing guesses, and re-tuning a sourced parameter to restore a target is "
    "what this project's standard forbids. See docs/validation.md, Phase-B sourced- "
    "parameter revision.",
)
def test_small_landlord_share(baseline_moments):
    """Individuals hold 85–92% of the rental stock [investor-small §1].

    Emergent, not an input: it falls out of large_investor_share, public_rental_share and
    the inheritance path. A drift out of band means one of those three is mis-specified.
    """
    assert 0.85 <= baseline_moments["small_landlord"] <= 0.92


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14: the section 7.1 total-return hurdle. Required rent is now V(i_bond + pi - "
    "E[g]) / (12(1-c)), so a landlord expecting appreciation accepts less rent. That lands "
    "the target it exists for - target 10, boom yield compression, which now passes - and "
    "breaks the rent LEVEL machinery, because in this model the landlord's reservation "
    "dominates rent formation while the demand channel (CONGESTION_GAIN = 0.05) is too weak "
    "to offset a falling floor. That is spec finding 2 - no scarcity-to-price channel - on "
    "the rent side rather than the sale side, and it is phase D's to close. Here: the wedge "
    "goes negative (-6.3%). Sitting tenants now pay MORE than entrants, because entrant "
    "asks track a reservation that falls with expected appreciation while sitting contracts "
    "are indexed.",
)
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
    reason="2026-09-14: the section 7.1 total-return hurdle. Required rent is now V(i_bond + pi - "
    "E[g]) / (12(1-c)), so a landlord expecting appreciation accepts less rent. That lands "
    "the target it exists for - target 10, boom yield compression, which now passes - and "
    "breaks the rent LEVEL machinery, because in this model the landlord's reservation "
    "dominates rent formation while the demand channel (CONGESTION_GAIN = 0.05) is too weak "
    "to offset a falling floor. That is spec finding 2 - no scarcity-to-price channel - on "
    "the rent side rather than the sale side, and it is phase D's to close. Here: boom "
    "rents now FALL 5.4% against a +2.5% floor, because E[g] rises through the boom and "
    "pulls the reservation down faster than congestion pushes asks up.",
)
def test_holdout_boom_rent_growth():
    """Target 7, rent leg: the 2021–25 boom must produce sustained asking-rent growth.

    A strict xfail for a long time, on the reading that it was structural — the clearing rent
    is the winning applicant's willingness to pay, a share of income, so rents could not
    outrun income. That reading was wrong, or rather it had become wrong: the tensioned
    market was slack, so the queue-congestion channel never fired. With the tightness
    recalibration and the location premium the same episode now gives **+3.6%/yr ± 0.8 over
    the 10 seeds, all of them positive**, against a measured +0.0% ± 0.3pp before — and with
    no change to the congestion parameter itself (docs/validation.md, boom-rent revision).

    Asserted at +2.5%/yr, four standard errors below the measured mean. That is still only
    about 40% of the sourced +8–11%/yr: the rest needs a size/quality margin the model does
    not have (docs/model-spec.md §10). Do not read the level as calibrated.
    """
    _, rent, _ = _holdout_boom((3, 5, 7, 8, 9, 11, 13, 17, 19, 23))
    assert float(np.mean(rent)) > 0.025


def test_boom_compresses_the_gross_yield():
    """Target 10: in a boom the gross rental yield must COMPRESS.

    Sign test only. Spain 2014-25 ran prices ahead of rents and gross yields fell.

    A band on the *level* of the compression would need the 2014–25 idealista yield **time
    series**. What `docs/sources.md` registers is the Q4-2025/Q1-2026 **cross-section**
    (Spain 6.7%, Madrid 4.7%, Barcelona 5.6%, capitals to 7.5%) — enough to anchor the zone
    ladder in target 9, and silent about the path. The direction is what is asserted here
    (model-spec §13.1: direction, not magnitude).

    **The margin is thin, deliberately left as it is.** 5 seeds, change in the tensioned
    gross yield over the boom: −29.6 / −22.2 / −1.5 / −2.9 / −34.8 bp, mean −18.2bp
    (0.0539 → 0.0521). All five compress, but two are all but flat, and the assertion carries
    no seed band. Tightening a gate belongs to a measurement campaign, not to a fix wave, so
    phase B should revisit whether this needs a band — by which time compression is the
    hurdle rule's direct prediction rather than the lag artefact described below, and the
    right band will be a different question.

    Mechanically this is the signature of the landlord's reservation rule. Under the current
    rule the reservation rent is a fixed multiple of value, so the yield floor tracks price
    one-for-one and compression can only come from the gap between the asking index and that
    floor. Under the total-return hurdle (spec §7.1) compression is the rule's direct
    prediction: E[g] up ⇒ required rent yield down.
    """
    starts, ends = [], []
    for seed in (3, 5, 7, 8, 9):
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        cfg = dataclasses.replace(
            cfg,
            population=dataclasses.replace(
                cfg.population, formation_per_tick=33, formation_income_factor=1.0
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
        starts.append(frame["gross_yield_tensioned"].iloc[20:24].mean())
        ends.append(frame["gross_yield_tensioned"].iloc[36:40].mean())
    assert float(np.mean(ends)) < float(np.mean(starts))


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
    assert 0.10 <= baseline_moments["vacancy_national"] <= 0.15


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14 (phase C): secondary-zone vacancy runs at 13.4% against a Censo band "
    "topping out at 13.1%. It sat at 13.10% — the boundary itself — before insolvency "
    "landed, and the 0.29pp it moved is MARKET vacancy (6.68% against 6.38%), not withheld "
    "stock: the forced-sale channel puts distressed and repossessed dwellings on the market "
    "while the credit lockout removes some of the buyers for them, so units spend longer "
    "empty. The ladder, the rural band and the national band all still hold, which is why "
    "only this leg is split out. Not fixable by tuning insolvency: the band edge and the "
    "listing-to-sale friction are phase D's price-formation work (spec §7.7).",
)
def test_vacancy_secondary_band(baseline_moments):
    """The secondary-zone leg of the ladder, on its own because it is the one that fails."""
    assert 0.081 <= baseline_moments["vacancy_s"] <= 0.131


def test_arrears_share_matches_the_bank_of_spain(baseline_moments):
    """Target 15, arrears leg: mortgaged households behind on payments (model-spec §6c).

    Anchor: the BdE doubtful ratio on household house-purchase credit — 1.60% (2026Q1),
    2.33–3.40% across 2019–2024, **6.28% at the 2014Q1 peak** [docs/sources.md, BdE table
    4.13]. The band 1.0–4.0% is the calm-period range; the peak is a hold-out observation
    and is deliberately not a baseline target.

    The two quantities are not identical and the band is wide because of it: the BdE counts
    euros of credit, this counts households, and they coincide only if arrears are
    uncorrelated with loan size — which the incidence gradient (§6c.1) makes unlikely. What
    is being tested is an order of magnitude, and that the model does not sit at zero, which
    is where it sat before insolvency existed.
    """
    assert 0.010 <= baseline_moments["arrears"] <= 0.040


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14 (phase C, on arrival): deliveries run at ~0.02%/yr against an "
    "observed calm-period 0.10–0.16%/yr (INE's 5,361 main residences in 2019 and 8,940 in "
    "2024 over ≈5.5M mortgages). The cause is identified, not mysterious: a distressed owner "
    "with positive equity always finds a buyer inside the listing window, so the model "
    "converts almost every statutory trigger into a voluntary sale. Real foreclosures happen "
    "because that sale often cannot: negative equity after a price fall, the discount on an "
    "occupied dwelling, and the months a sale takes. Two of those three are phase D's "
    "price-formation work (spec §7.7, seller reservation from the mortgage and search over m "
    "listings); the third is the bust itself, which is the phase-E hold-out. Reported as a "
    "failure rather than closed by lowering the band — the band is the data.",
)
def test_foreclosure_flow_matches_the_published_rate(baseline_moments):
    """Target 15, deliveries leg: dwellings delivered to the lender per mortgage per year.

    Anchors: the BdE's **0.7%/yr in 2014** (0.6% for main residences) — the only published
    like-for-like rate [BdE Circular 1/2013 note] — and ≈0.10%/yr implied by INE's 2019
    trough. A calm baseline belongs at the bottom of that range, a crisis at the top.
    """
    assert 0.0010 <= baseline_moments["foreclosure_rate"] <= 0.0080


def test_delivery_composition_is_reported(baseline_moments):
    """Target 15, composition leg: reported, never gated.

    The voluntary/dación split (0.478 and 0.397 of deliveries) is an input the model is
    GIVEN from the BdE note, so a gate on it would test the input. What is asserted is only
    that the column exists and is a share — the number belongs in `docs/validation.md`.
    """
    share = baseline_moments["dacion_share"]
    assert np.isnan(share) or 0.0 <= share <= 1.0


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


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14: the section 7.1 total-return hurdle. Required rent is now V(i_bond + pi - "
    "E[g]) / (12(1-c)), so a landlord expecting appreciation accepts less rent. That lands "
    "the target it exists for - target 10, boom yield compression, which now passes - and "
    "breaks the rent LEVEL machinery, because in this model the landlord's reservation "
    "dominates rent formation while the demand channel (CONGESTION_GAIN = 0.05) is too weak "
    "to offset a falling floor. That is spec finding 2 - no scarcity-to-price channel - on "
    "the rent side rather than the sale side, and it is phase D's to close. Here: the cap "
    "raises contract rents 4.9%. With the reservation floor lower, market rents sit below "
    "the reference index and the magnet pulls asks up to it - the cap acts as a floor, the "
    "same mechanism recorded on 2026-09-12 and re-opened by the hurdle.",
)
def test_rent_cap_lowers_contract_rents():
    """Target 8, price leg: a binding cap must lower new-contract rents in the capped zone.

    This regressed silently after the August 2026 audit and Funcas revision: with the frozen
    reference index indexed at 2.5%/yr against a 2%/yr income anchor, the reference outran
    the market within ~10 ticks and the cap run ended ABOVE baseline (+0.9%). Pinned here so
    the flagship experiment cannot break unnoticed again. Asserted at −1%, well inside the
    measured −2.2% and far below the sourced −4…−6%.
    """
    assert _rent_cap_response(1.0)["rent"] < -0.01


def test_rent_cap_supply_response_is_negative_at_the_top_of_the_dial():
    """Target 8, supply leg, WEAK form: elasticity 2 must produce a real contraction.

    Asserted at −5%, well below what the studies report, so seed noise (σ ≈ 3pp on 3 seeds)
    does not flip it. This is the leg that survives phase A; the strong form — reaching
    Monràs — is the strict xfail below.

    History: this failed as a strict xfail until the tensioned-tightness revision, when
    metro-weighted formation (`formation_zone_weights`) and the shadow rent landlords compare
    the cap against (`ZoneState.shadow_rent`) fixed it. The full sweep is in
    docs/experiments/rent-cap.md.
    """
    assert _rent_cap_response(2.0)["leases"] < -0.05


@pytest.mark.xfail(
    strict=True,
    reason="2026-09-14: the quantity leg clears easily (-21.8% contracts at elasticity 2) but "
    "the price leg moves the WRONG WAY (+6.8% rents), so the co-movement Monras and "
    "Garcia-Montalvo actually measure is not reproduced. Cause: the section 7.1 hurdle lowers "
    "the reservation floor via expected appreciation, market rents fall below the reference "
    "index, and the cap's magnet pulls asks up - the cap acts as a floor. This test was "
    "rewritten on the same day to assert BOTH legs: asserting the quantity alone let it pass "
    "while the mechanism was wrong, which would have put a number in the validation table that "
    "reads as evidence for a mechanism the model does not have. Both legs close together or "
    "not at all, and they are phase D's - the rent side needs the scarcity channel the sale "
    "side is getting (spec finding 2).",
)
def test_rent_cap_reproduces_the_monras_co_movement():
    """Target 8, supply leg: Monràs is a CO-MOVEMENT, not a quantity.

    Monràs & García-Montalvo measure Δln contracts / Δln rent ≈ 2 — roughly −10% tenancies AT
    −5% rents. Both halves are the claim. A model that sheds tenancies while rents RISE has not
    reproduced that elasticity; it has reproduced one number out of two and inverted the other.

    Asserted on both legs at elasticity 2: contracts below −9%, and rents inside the −4…−6% the
    three studies report, widened a point on each side for seed noise.
    """
    response = _rent_cap_response(2.0)
    assert response["leases"] < -0.09, f"quantity leg: {response['leases']:.1%}"
    assert -0.07 <= response["rent"] <= -0.03, f"price leg: {response['rent']:+.1%}"
