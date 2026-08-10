"""Engine-level tests.

For a stochastic model these are the tests that matter — not "does it return 42",
but "is it reproducible" and "does it behave the way the theory says".
"""

import pandas as pd

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
    """2022–23 signature: a rate shock compresses volumes, prices stay sticky."""
    f_base = run_frame(ticks=24, seed=3)
    f_shock = run_frame("rate-shock", ticks=24, seed=3, start_tick=8, euribor=0.05)
    tail = slice(12, 24)
    vol_drop = f_shock["transactions"].iloc[tail].mean() / max(
        f_base["transactions"].iloc[tail].mean(), 1e-9
    )
    price_ratio = (
        f_shock["price_national"].iloc[tail].mean() / f_base["price_national"].iloc[tail].mean()
    )
    assert vol_drop < 0.95  # volumes fall
    assert price_ratio > vol_drop  # prices fall less than volumes (stickiness)
