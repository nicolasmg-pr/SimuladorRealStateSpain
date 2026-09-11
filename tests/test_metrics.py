"""Mechanical correctness of metric columns, against hand-built states.

`test_validation.py` judges the model against the world; this file judges the
measurement against the state. A column that is wrong here makes every target
that reads it meaningless.
"""

from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.scenario import Scenario


def small_state(seed: int = 9):
    """One settled tick, so indices, expectations and tick_events all exist."""
    cfg = SimConfig.baseline(seed=seed, ticks=4)
    engine = Engine(Scenario(name="t", baseline=cfg))
    state = engine.initialise()
    engine.step(state)
    return engine, state


def test_net_migration_columns_sum_to_zero():
    """Migration moves households between zones; it never creates or destroys them."""
    _, state = small_state()
    row = state.history[-1]
    total = sum(row[f"net_migration_{z.value}"] for z in ZoneType)
    assert total == 0


def test_net_migration_counts_the_recorded_flows():
    """The column is inflows minus outflows of the tick's recorded moves."""
    _, state = small_state()
    flows = state.tick_events["migration"]
    row = state.history[-1]
    for zone in ZoneType:
        inflow = sum(n for (_, dest), n in flows.items() if dest is zone)
        outflow = sum(n for (origin, _), n in flows.items() if origin is zone)
        assert row[f"net_migration_{zone.value}"] == inflow - outflow
