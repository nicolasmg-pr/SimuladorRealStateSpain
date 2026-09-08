"""Engine-level tests.

For a stochastic model these are the tests that matter — not "does it return 42",
but "is it reproducible" and "does it behave the way the theory says".
"""

import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from resim import metrics
from resim.cli import build_scenario
from resim.config import SimConfig
from resim.engine import Engine
from resim.market.stock import Tenure
from resim.scenario import Scenario

TICKS = 16


def run_frame(
    scenario_name: str = "baseline", seed: int = 7, ticks: int = TICKS, **kwargs
) -> pd.DataFrame:
    scenario = build_scenario(scenario_name, seed, ticks, **kwargs)
    return metrics.to_frame(Engine(scenario).run())


def test_same_seed_same_run():
    """Two runs with one seed produce identical series. Non-negotiable."""
    a = run_frame(seed=123)
    b = run_frame(seed=123)
    pd.testing.assert_frame_equal(a, b)


def test_reproducible_across_processes():
    """Reproducibility must not depend on PYTHONHASHSEED.

    Python salts str/tuple hashing per process, so `hash()` can never carry a model draw.
    This runs a policy that exercises means-tested eligibility in a fresh interpreter with
    two different hash seeds and requires an identical fingerprint.
    """
    script = (
        "from resim import metrics;"
        "from resim.config import SimConfig;"
        "from resim.engine import Engine;"
        "from resim.scenario import DemandSubsidy, Scenario;"
        "sc = Scenario('ds', SimConfig.baseline(seed=42, ticks=12),"
        " (DemandSubsidy(start_tick=1, rent_subsidy_month=280.0,"
        "  rent_subsidy_eligible_share=0.15),));"
        "f = metrics.to_frame(Engine(sc).run());"
        "print(f'{f[\"rent_tensioned\"].iloc[-1]:.9f}')"
    )
    out = []
    for hash_seed in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed}
        out.append(
            subprocess.run(
                [sys.executable, "-c", script], capture_output=True, text=True, check=True, env=env
            ).stdout.strip()
        )
    assert out[0] == out[1], f"run depends on PYTHONHASHSEED: {out}"


def test_different_seed_different_run():
    a = run_frame(seed=1)
    b = run_frame(seed=2)
    assert not a["price_tensioned"].equals(b["price_tensioned"])


def test_conservation():
    """Units are never created or destroyed outside construction/demolition."""
    scenario = Scenario(name="baseline", baseline=SimConfig.baseline(seed=5, ticks=TICKS))
    engine = Engine(scenario)
    state = engine.initialise()
    n0 = len(state.stock)
    completions = 0
    for _ in range(TICKS):
        arriving = [p for p in state.pipeline if p[0] == state.tick + 1]
        engine.step(state)
        completions += sum(n for _, _, n, _ in arriving)
    assert len(state.stock) == n0 + completions
    # every occupied unit's occupant exists and points back
    for u in state.stock.units.values():
        if u.occupant_id is not None:
            assert state.households[u.occupant_id].unit_id == u.id
        if u.tenure is Tenure.RENTED:
            assert u.occupant_id is not None


def test_affordability_indicators_sane():
    """Affordability (model-spec §11): bounded, present per zone, and directionally sound —
    a rate shock must raise the theoretical effort."""
    frame = run_frame(seed=9)
    for zone in ("tensioned", "secondary", "rural", ""):
        suffix = f"_{zone}" if zone else ""
        assert (frame[f"buyer_access{suffix}"].between(0, 1)).all()
        assert (frame[f"purchase_effort{suffix}"] > 0).all()
    # tensioned zone is the least affordable one
    tail = frame.tail(8)
    assert tail["purchase_effort_tensioned"].mean() > tail["purchase_effort_rural"].mean()

    f_shock = run_frame("rate-shock", seed=9, start_tick=4, euribor=0.06)
    tail = slice(8, TICKS)
    assert f_shock["purchase_effort"].iloc[tail].mean() > frame["purchase_effort"].iloc[tail].mean()


def test_baseline_reaches_steady_state():
    """With no intervention, prices settle rather than diverge."""
    frame = run_frame(ticks=40)
    growth = frame["price_tensioned"].pct_change().dropna().tail(12)
    assert growth.abs().mean() < 0.05  # < 5%/quarter drift in the settled phase
    assert frame["price_tensioned"].iloc[-1] > 0


def test_supply_shock_lowers_prices():
    """Sanity direction check: more construction, lower prices. If not, the model is wrong."""
    import dataclasses

    base_cfg = SimConfig.baseline(seed=11, ticks=40)
    boosted = dataclasses.replace(
        base_cfg,
        developer=dataclasses.replace(
            base_cfg.developer,
            base_starts_per_tick=base_cfg.developer.base_starts_per_tick * 6,
            max_starts_per_tick=base_cfg.developer.max_starts_per_tick * 6,
            presale_share=0.05,  # bypass the demand gate: pure supply shock
        ),
    )
    f_base = metrics.to_frame(Engine(Scenario(name="b", baseline=base_cfg)).run())
    f_boost = metrics.to_frame(Engine(Scenario(name="s", baseline=boosted)).run())
    tail = slice(-12, None)
    assert f_boost["price_national"].iloc[tail].mean() < f_base["price_national"].iloc[tail].mean()


def test_rate_shock_cuts_transactions_before_prices():
    """2022–23 signature: a rate shock compresses volumes, prices stay sticky.

    Two deliberate choices:
      - the window starts 4 ticks after the shock, because mortgage-rate pass-through is
        slow (~32% of a euríbor move after 16 months, BdE DO 2312). Measuring from the
        shock tick would test the pass-through parameter, not the demand response.
      - averaged over 3 seeds. The single-seed spread on this ratio is ±5pp, wider than
        the effect being asserted, so a one-seed version of this test measures noise.
    """
    tail = slice(12, 24)
    vol, price = [], []
    for seed in (3, 9, 11):
        f_base = run_frame(ticks=24, seed=seed)
        f_shock = run_frame("rate-shock", ticks=24, seed=seed, start_tick=8, euribor=0.05)
        vol.append(
            f_shock["transactions"].iloc[tail].mean()
            / max(f_base["transactions"].iloc[tail].mean(), 1e-9)
        )
        price.append(
            f_shock["price_national"].iloc[tail].mean() / f_base["price_national"].iloc[tail].mean()
        )
    vol_drop = float(np.mean(vol))
    price_ratio = float(np.mean(price))
    assert vol_drop < 0.95  # volumes fall
    assert price_ratio > vol_drop  # prices fall less than volumes (stickiness)


# --- KB refresh 2026-09: buyer-type tax wedges, cap coverage, guarantee wealth cap ----------


def _tail_mean(frame: pd.DataFrame, column: str, start: int) -> float:
    return float(frame[column].iloc[start:].mean())


def test_non_resident_surcharge_removes_foreign_purchases():
    """A 100%-style tax on non-EU buyers must cut the overlay's completed purchases hard.

    The stalled bill would put ≈+0.90 on a 10% ITP; the cash buyer's budget is scaled by
    (1 + base)/(1 + effective) = 0.55. It does NOT eliminate them: non-residents bid with a
    +60% premium (they pay ≈1.8× the Spanish €/m²), so after the wedge they still reach
    0.7–1.06× the zone price and win the listings whose reserve sits below that. Measured:
    ≈−45% of non-resident purchases over 3 seeds — the premium absorbs half the tax. Averaged
    over seeds because the overlay is a Poisson stream conditioned on recent sales.
    """
    base, taxed = [], []
    for seed in (3, 5, 8):
        f_base = run_frame(ticks=24, seed=seed)
        f_tax = run_frame(
            "transaction-tax", ticks=24, seed=seed, start_tick=4, itp_delta=0.0, foreign_delta=0.9
        )
        base.append(_tail_mean(f_base, "foreign_purchase_share", 8))
        taxed.append(_tail_mean(f_tax, "foreign_purchase_share", 8))
    assert float(np.mean(base)) > 0.03  # the overlay is alive in the baseline
    assert float(np.mean(taxed)) < 0.75 * float(np.mean(base))


def test_investor_surcharge_lowers_investor_bids_only():
    """The Catalan 20% TPO on whole-building purchases (+0.10 over the 10% general rate) must
    cut what the large investor bids, and touch no other buyer.

    Asserted on the BID, not on the investor's completed share of sales: the model's
    institutional buyer is only the gran tenedor and it wins ≈1% of transactions, so its
    realised share moves less between policies than between seeds (measured 0.98% → 1.13%,
    σ 0.17pp — docs/validation.md R5). Testing the emergent share would be testing noise.
    """
    from resim.agents.base import MakeOffer
    from resim.agents.investor import LargeInvestor
    from resim.market.stock import LARGE_INVESTOR_ID

    cfg = SimConfig.baseline(seed=9, ticks=4)
    engine = Engine(Scenario(name="t", baseline=cfg))
    state = engine.initialise()
    engine.step(state)

    def investor_bids(policy_state):
        return [
            i.budget
            for i in LargeInvestor(LARGE_INVESTOR_ID, np.random.default_rng(0)).decide(policy_state)
            if isinstance(i, MakeOffer)
        ]

    base_bids = investor_bids(state)
    state.config = state.config.with_policy(itp_investor_delta=0.10)
    taxed_bids = investor_bids(state)
    assert base_bids and len(base_bids) == len(taxed_bids)
    # (1 + base) / (1 + base + 0.10) on the tensioned zone's 10% rate ≈ 0.917
    for base, taxed in zip(base_bids, taxed_bids, strict=True):
        assert taxed < base
        assert taxed / base == pytest.approx(1.10 / 1.20, rel=0.05)


def test_household_bids_ignore_the_investor_surcharge():
    """The investor surcharge must not reach households: their screen uses the zone rate."""
    from resim.agents.base import MakeOffer
    from resim.agents.household import Households

    cfg = SimConfig.baseline(seed=9, ticks=4)
    engine = Engine(Scenario(name="t", baseline=cfg))
    state = engine.initialise()
    engine.step(state)

    def household_budgets(policy_state):
        return {
            i.agent_id: i.budget
            for i in Households(-10, np.random.default_rng(0)).decide(policy_state)
            if isinstance(i, MakeOffer)
        }

    before = household_budgets(state)
    state.config = state.config.with_policy(itp_investor_delta=0.10)
    after = household_budgets(state)
    assert before and before == after


def test_cap_coverage_scales_the_rent_cap():
    """Coverage 0 = the law exists but no municipality is declared: no capped contract and
    contract rents within noise of the baseline. Coverage 1 = the whole zone is declared and
    contract rents fall. Phase-7 experiment design (cap at tick 20 of 40, 16 post ticks)."""
    from resim.scenario import RentCap

    def response(coverage: float, seed: int) -> tuple[int, float]:
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        base = metrics.to_frame(Engine(Scenario(name="b", baseline=cfg)).run())
        sc = Scenario(
            name="cap",
            baseline=cfg,
            interventions=(RentCap(start_tick=20, coverage=coverage),),
        )
        engine = Engine(sc)
        state = engine.initialise()
        capped = 0
        for _ in range(40):
            engine.step(state)
            capped += sum(1 for lst in state.rent_listings.values() if lst.capped)
        cap = metrics.to_frame(state)
        post = slice(24, 40)
        col = "rent_transacted_tensioned"
        return capped, float(cap[col].iloc[post].mean() / base[col].iloc[post].mean() - 1.0)

    zero = [response(0.0, s) for s in (1, 2, 3)]
    full = [response(1.0, s) for s in (1, 2, 3)]
    assert all(c == 0 for c, _ in zero)
    assert all(c > 0 for c, _ in full)
    zero_effect = float(np.mean([d for _, d in zero]))
    full_effect = float(np.mean([d for _, d in full]))
    assert full_effect < -0.01
    # an undeclared zone keeps only the NATIONAL part of the law (IRAV on sitting rents, which
    # slows rotation a little); that residual must be small next to the declared-zone effect
    assert abs(zero_effect) < 0.5 * abs(full_effect)
    assert full_effect < zero_effect


def test_guarantee_wealth_cap_excludes_wealthy_first_time_buyers():
    """The ICO line's €150k wealth filter (BOE 2 Jul 2026): a rich tenant is not guaranteed."""
    from resim.agents.base import MakeOffer
    from resim.agents.household import Households
    from resim.state import HouseholdStatus

    cfg = SimConfig.baseline(seed=4, ticks=4).with_policy(
        guarantee_ltv_boost=0.20, guarantee_eligible_share=1.0, guarantee_wealth_cap=150_000.0
    )
    engine = Engine(Scenario(name="g", baseline=cfg))
    state = engine.initialise()
    engine.step(state)
    state.macro.guarantee_budget_left = 1e12
    rich = next(h for h in state.households.values() if h.status is HouseholdStatus.TENANT)
    rich.wealth = 400_000.0
    rich.income = 60_000.0
    offers = {
        i.agent_id: i
        for i in Households(-10, np.random.default_rng(0)).decide(state)
        if isinstance(i, MakeOffer)
    }
    guaranteed_ids = {aid for aid, o in offers.items() if o.guaranteed}
    assert guaranteed_ids, "eligible share 1.0 must guarantee somebody"
    assert rich.id not in guaranteed_ids
    for aid in guaranteed_ids:
        assert state.households[aid].wealth <= 150_000.0


# --- tensioned-tightness revision: shadow rent and formation weights ------------------------


def test_shadow_rent_equals_the_index_in_a_free_market():
    """With no cap the shadow rent IS the asking index, in every zone, every tick — the
    mechanism must be invisible until a cap switches on (model-spec §5)."""
    frame = run_frame(seed=4, ticks=12)
    for zone in ("tensioned", "secondary", "rural"):
        pd.testing.assert_series_equal(
            frame[f"shadow_rent_{zone}"], frame[f"rent_{zone}"], check_names=False
        )


def test_shadow_rent_stays_anchored_under_a_cap():
    """Under a cap the shadow must NOT follow the asking index down onto the cap, and must
    not run away either: it tracks renter paying capacity, so it stays within a narrow band
    of its activation value while the asking index drops to the reference."""
    from resim.scenario import RentCap

    cfg = SimConfig.baseline(seed=1, ticks=40)
    sc = Scenario(name="cap", baseline=cfg, interventions=(RentCap(start_tick=20),))
    frame = metrics.to_frame(Engine(sc).run())
    at_activation = frame["shadow_rent_tensioned"].loc[19]
    post = frame.loc[21:40]
    # bounded: no runaway (the rejected marginal-quantile anchor tripled it), no collapse
    assert (post["shadow_rent_tensioned"] / at_activation).between(0.9, 1.25).all()
    # the asking index drops onto the cap at activation; the shadow must NOT follow it down —
    # that is the whole point of the mechanism (the blind exit rule read the index and went
    # inert within four ticks). Asserted on the mean over the year after activation, not tick
    # by tick: later in a long cap the IRAV-indexed reference climbs past the shadow and asks
    # recover above it, which is a documented limitation (docs/validation.md) and not
    # something this test should pin.
    early = frame.loc[21:25]
    assert early["shadow_rent_tensioned"].mean() > early["rent_tensioned"].mean()
    assert early["rent_tensioned"].mean() < at_activation


def test_formation_zone_weights_are_a_distribution():
    cfg = SimConfig.baseline()
    weights = cfg.population.formation_zone_weights
    assert weights is not None
    assert sum(weights) == pytest.approx(1.0, abs=1e-3)
    assert weights[0] > cfg.zones[0].household_share  # metro-weighted by design


# --- rent-cap coverage as a regulatory segment ----------------------------------------------


def test_coverage_is_a_persistent_monotone_property_of_the_unit():
    """A municipality is declared or it is not: the same unit must stay on the same side of
    the line for the whole run, and raising coverage must ADD municipalities rather than
    reshuffle them. Both follow from `Unit.declaration_draw` being drawn once at creation."""
    from resim.agents.landlord import is_covered

    cfg = SimConfig.baseline(seed=6, ticks=12).with_policy(cap_coverage=0.42)
    engine = Engine(Scenario(name="c", baseline=cfg))
    state = engine.initialise()
    covered_at_start = {u.id for u in state.stock.units.values() if is_covered(state, u)}
    assert 0 < len(covered_at_start) < len(state.stock.units)
    for _ in range(12):
        engine.step(state)
        still = {u.id for u in state.stock.units.values() if is_covered(state, u)}
        assert covered_at_start <= still  # membership never lapses (new units may join)
    # monotone in the parameter: the 0.42 set is a subset of the 0.70 set
    state.config = state.config.with_policy(cap_coverage=0.70)
    wider = {u.id for u in state.stock.units.values() if is_covered(state, u)}
    assert covered_at_start < wider


def test_new_contracts_split_into_declared_and_free_segments():
    """The two segment counts partition the zone's non-public new contracts, and with the
    whole zone declared the free segment is empty."""
    from resim.scenario import RentCap

    for coverage, free_expected in ((0.42, True), (1.0, False)):
        cfg = SimConfig.baseline(seed=2, ticks=28)
        sc = Scenario(
            name="c", baseline=cfg, interventions=(RentCap(start_tick=12, coverage=coverage),)
        )
        frame = metrics.to_frame(Engine(sc).run()).loc[16:]
        split = frame["new_leases_declared_tensioned"] + frame["new_leases_free_tensioned"]
        assert (split <= frame["new_leases_tensioned"]).all()  # ≤: public units are excluded
        if free_expected:
            assert frame["new_leases_free_tensioned"].sum() > 0
        else:
            assert frame["new_leases_free_tensioned"].sum() == 0


def test_partial_coverage_pushes_demand_into_the_free_segment():
    """Spain's spillover signature: under a partial cap the non-declared segment takes more
    contracts and prices above the declared one.

    Catalonia 2025: rents +1.6% inside the tensioned zones against +9.4% outside (Incasòl).
    The pooled median cannot show this — it mixes the two and moves with the mix, which is
    why the segments are reported apart (docs/validation.md T7).
    """
    from resim.scenario import RentCap

    declared_gap, lease_shift = [], []
    for seed in (1, 2, 3):
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        sc = Scenario(
            name="c",
            baseline=cfg,
            interventions=(RentCap(start_tick=20, supply_response_elasticity=2.0, coverage=0.42),),
        )
        frame = metrics.to_frame(Engine(sc).run()).loc[24:]
        declared_gap.append(
            frame["rent_new_free_tensioned"].mean() / frame["rent_new_declared_tensioned"].mean()
        )
        lease_shift.append(
            frame["new_leases_free_tensioned"].mean()
            / frame["new_leases_declared_tensioned"].mean()
        )
    assert float(np.mean(declared_gap)) > 1.0  # the free segment prices above the capped one
    assert float(np.mean(lease_shift)) > 1.0  # and signs more of the contracts
