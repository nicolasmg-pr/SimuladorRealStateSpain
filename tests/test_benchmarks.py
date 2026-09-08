"""Contrast against published BdE figures.

These tests do NOT assert that the model matches BdE — the contrast is a diagnostic, not a
validation gate (that is `test_validation.py`). What they assert is that the comparison is
*honest*: every row reads a column that exists, the model side is put on the same footing as
the published side, and the scale conversion is the documented 1:2,000.

A comparison on mismatched bases is worse than no comparison, which is why the arithmetic is
pinned here rather than trusted.
"""

import numpy as np
import pandas as pd
import pytest

from resim import benchmarks, metrics
from resim.benchmarks import BENCHMARKS, TICKS_PER_YEAR, WINDOW
from resim.cli import build_scenario
from resim.engine import Engine
from resim.metrics import SCALE


@pytest.fixture(scope="module")
def run_frame():
    state = Engine(build_scenario("baseline", 42, 60)).run()
    return metrics.to_frame(state), state.config


def synthetic_frame(**overrides) -> pd.DataFrame:
    """A frame carrying every column the benchmarks read, so conversions can be pinned.

    Defaults are arbitrary; tests override only the columns they are asserting on.
    """
    columns = {
        "formation": 10.0,
        "completions": 4.0,
        "starts": 5.0,
        "transactions": 8.0,
        "price_growth_national": 0.01,
        "rent_growth_national": 0.01,
        "purchase_effort": 0.37,
        "price_to_income": 7.5,
        "vacancy_market_tensioned": 0.07,
        "vacancy_secondary": 0.12,
        "vacancy_rural": 0.19,
        "vacancy_rate": 0.13,
        "ownership_rate": 0.72,
        "rent_burden_over_30_share": 0.35,
        "rent_national": 500.0,
        "cash_purchase_share": 0.35,
        "foreign_purchase_share": 0.08,
        "investor_purchase_share": 0.05,
        "seeker_share": 0.06,
        "households": 10_000.0,
    }
    columns.update(overrides)
    return pd.DataFrame(
        {
            name: ([value] * WINDOW if not isinstance(value, list) else value)
            for name, value in columns.items()
        }
    )


def test_every_benchmark_is_computable(run_frame):
    """No row may reference a metrics column that does not exist, or return a non-number."""
    frame, config = run_frame
    for b in BENCHMARKS:
        value = b.model(frame, config)
        assert isinstance(value, float), f"{b.key} returned {type(value)}"
        assert np.isfinite(value), f"{b.key} returned {value}"


def test_metadata_is_complete(run_frame):
    """Every published figure must carry its provenance and its basis conversion.

    An unsourced number in a comparison table reads as authoritative when it is not.
    """
    keys = [b.key for b in BENCHMARKS]
    assert len(keys) == len(set(keys)), "duplicate benchmark keys"
    for b in BENCHMARKS:
        assert b.source.strip(), f"{b.key} has no source"
        assert b.period.strip(), f"{b.key} has no period"
        assert b.basis.strip(), f"{b.key} does not state how bases are matched"
        assert b.label.strip()
        assert b.official != 0.0
        if b.band is not None:
            lo, hi = b.band
            assert lo < hi, f"{b.key} band is inverted"
            assert lo <= b.official <= hi, f"{b.key} central value sits outside its own band"


def test_scale_conversion_is_the_documented_one():
    """Per-tick model counts → national units per year: × 4 × SCALE, and nothing else.

    Pinned against a synthetic frame so an accidental change to the conversion is caught
    here rather than silently shifting every count row in the app.
    """
    frame = synthetic_frame()
    config = build_scenario("baseline", 1, 4).baseline
    table = benchmarks.contrast(frame, config)
    assert table.loc["formation", "model_value"] == pytest.approx(10.0 * TICKS_PER_YEAR * SCALE)
    assert table.loc["completions", "model_value"] == pytest.approx(4.0 * TICKS_PER_YEAR * SCALE)
    assert table.loc["starts", "model_value"] == pytest.approx(5.0 * TICKS_PER_YEAR * SCALE)
    assert table.loc["transactions", "model_value"] == pytest.approx(8.0 * TICKS_PER_YEAR * SCALE)
    # the deficit is the SUM over the window, the basis BdE's 750,000 is published on —
    # not the window mean, and not a mean of per-tick ratios
    assert table.loc["deficit_5y", "model_value"] == pytest.approx((10.0 - 4.0) * WINDOW * SCALE)


def test_deficit_uses_sums_not_a_mean_of_ratios():
    """Jensen guard: BdE's figure is an aggregate, so per-tick ratios must not be averaged.

    A frame with lumpy completions has a very different mean-of-ratios than ratio-of-sums;
    the benchmark must track the latter.
    """
    lumpy = synthetic_frame(completions=[0.0, 8.0] * (WINDOW // 2))
    config = build_scenario("baseline", 1, 4).baseline
    table = benchmarks.contrast(lumpy, config)
    expected = (10.0 * WINDOW - 4.0 * WINDOW) * SCALE
    assert table.loc["deficit_5y", "model_value"] == pytest.approx(expected)


def test_verdict_bands():
    """`inside` must mean inside the published band, with a ±15% fallback when there is none."""
    banded = next(b for b in BENCHMARKS if b.band is not None)
    lo, hi = banded.band
    assert banded.verdict(banded.official) == "inside"
    assert banded.verdict(lo) == "inside"
    assert banded.verdict(hi) == "inside"
    assert banded.verdict(lo * 0.5) == "below"
    assert banded.verdict(hi * 2.0) == "above"

    unbanded = next(b for b in BENCHMARKS if b.band is None)
    assert unbanded.verdict(unbanded.official) == "inside"
    assert unbanded.verdict(unbanded.official * 1.5) == "above"
    assert unbanded.verdict(unbanded.official * 0.5) == "below"


def test_pooling_averages_across_seeds(run_frame):
    """Several rows swing more between seeds than their published band is wide.

    Pooling must average the model side, so a one-seed miss cannot be reported as a
    systematic gap. Verified against the mean of the two single-seed values.
    """
    _, config = run_frame
    frames = [
        metrics.to_frame(Engine(build_scenario("baseline", seed, 60)).run()) for seed in (1, 2)
    ]
    singles = [benchmarks.contrast(f, config) for f in frames]
    pooled = benchmarks.contrast(frames, config)
    assert (pooled["Semillas"] == 2).all()
    for key in pooled.index:
        expected = (singles[0].loc[key, "model_value"] + singles[1].loc[key, "model_value"]) / 2
        assert pooled.loc[key, "model_value"] == pytest.approx(expected)


def test_formation_row_confirms_the_scale_is_right(run_frame):
    """Formation is a calibrated INPUT, so this row is a scale check, not a result.

    Pooled over seeds it must land on the configured flow — if it does not, the 1:2,000
    conversion is wrong and every other count row in the table is wrong with it.
    """
    _, config = run_frame
    frames = [
        metrics.to_frame(Engine(build_scenario("baseline", seed, 60)).run())
        for seed in (1, 2, 3, 4, 5)
    ]
    table = benchmarks.contrast(frames, config)
    configured = config.population.formation_per_tick * TICKS_PER_YEAR * SCALE
    assert table.loc["formation", "model_value"] == pytest.approx(configured, rel=0.08)


def test_summary_counts_partition_the_table(run_frame):
    frame, config = run_frame
    counts = benchmarks.summary(frame, config)
    assert counts["total"] == len(BENCHMARKS)
    assert counts["inside"] + counts["below"] + counts["above"] == counts["total"]


def test_contrast_rejects_an_empty_frame_list(run_frame):
    _, config = run_frame
    with pytest.raises(ValueError):
        benchmarks.contrast([], config)


def test_app_renders_the_bde_tab():
    """The Streamlit surface must actually execute — a tab that raises is worse than none.

    Streamlit runs every tab's body eagerly, so this exercises the BdE contrast end to end
    (run -> contrast -> render). It is the only coverage the UI has; keep it.
    """
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = Path(__file__).resolve().parents[1] / "src" / "resim" / "ui" / "app.py"
    at = AppTest.from_file(str(app), default_timeout=900)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    headline = {m.label: m.value for m in at.metric}
    assert headline["Indicadores contrastados"] == str(len(BENCHMARKS))
    # the four counters must partition the table
    partition = sum(
        int(headline[k]) for k in ("✅ Dentro de banda", "🔽 Por debajo", "🔼 Por encima")
    )
    assert partition == len(BENCHMARKS)
