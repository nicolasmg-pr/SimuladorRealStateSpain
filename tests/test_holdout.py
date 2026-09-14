"""The hold-out instrument, tested — not run.

Running the 2008–13 episode is a once-only act (`docs/holdout-2008-2013.md`), so nothing here
runs it. What is checked is that the instrument carries the registered series faithfully and
builds the episode it claims to build: a wrong input would not show up as a failure, it would
show up as a *result*, which is the one thing this project cannot afford here.
"""

import pytest

from resim import holdout
from resim.scenario import CreditCrunch, HouseholdFormation, LabourShock, RateShock


def test_euribor_path_is_the_registered_series():
    """BdE 19.1: the spike comes before the collapse, and both are in the path."""
    assert len(holdout.EURIBOR) == 24
    assert holdout.EURIBOR[2] == pytest.approx(0.05367)  # 2008Q3, the peak
    assert holdout.EURIBOR[21] == pytest.approx(0.00506)  # 2013Q2, the trough
    assert max(holdout.EURIBOR) == holdout.EURIBOR[2]
    assert holdout.EURIBOR_2007Q4 == pytest.approx(0.04682)


def test_jobless_path_is_the_household_series_not_the_individual_one():
    """INE 65276. The individual rate peaked near 26%; this one peaks at 15.02%.

    Picking the wrong one of those two is the mistake phase C measured: it put the model's
    arrears at 6.9% against a BdE doubtful ratio of 1.6–3.4%.
    """
    assert len(holdout.JOBLESS) == 24
    assert max(holdout.JOBLESS) == pytest.approx(0.1502)  # 2013Q1
    assert holdout.JOBLESS.index(max(holdout.JOBLESS)) == 20
    assert holdout.JOBLESS_2007Q4 == pytest.approx(0.0361)
    assert max(holdout.JOBLESS) < 0.20


def test_formation_falls_by_four_fifths_and_never_to_zero():
    """INE 65269: 474k/yr in 2007 against 91k in 2013 — a collapse, not a stop."""
    assert holdout.FORMATION_2007 == 474_200
    assert holdout.FORMATION_PER_YEAR[2013] == 91_000
    assert holdout.FORMATION_PER_YEAR[2013] / holdout.FORMATION_2007 < 0.25
    assert min(holdout.FORMATION_PER_YEAR.values()) > 0


def test_the_pipeline_carries_the_boom_into_the_bust():
    """MIVAU 3.2: completions were still 563,631 in 2008 and 43,230 in 2013.

    The first four ticks must deliver at boom rates — that inherited pipeline is half of what
    the episode is, and a model starting the bust with an empty one is answering an easier
    question.
    """
    pipeline = holdout.initial_pipeline()
    assert len(pipeline) == 24
    assert pipeline[0] == round(563_631 / holdout.SCALE / 4)
    assert pipeline[-1] == round(43_230 / holdout.SCALE / 4)
    assert pipeline[0] > 10 * pipeline[-1]


def test_the_episode_runs_under_the_law_of_the_period():
    """LEC art. 693 as amended by Ley 1/2013: three instalments, not today's twelve."""
    cfg = holdout.baseline_config(seed=1)
    assert cfg.insolvency.foreclosure_regime == "ley1_2013"
    assert cfg.credit.euribor == pytest.approx(holdout.EURIBOR_2007Q4)
    assert cfg.labour.jobless_rate == pytest.approx(holdout.JOBLESS_2007Q4)


def test_the_scenario_applies_each_quarter_of_each_series():
    """One step per observed quarter, so the path is the data and not an average."""
    scenario = holdout.scenario(seed=1, ticks=24)
    rates = {
        iv.start_tick: iv.euribor for iv in scenario.interventions if isinstance(iv, RateShock)
    }
    jobless = {
        iv.start_tick: iv.rate for iv in scenario.interventions if isinstance(iv, LabourShock)
    }
    assert rates[2] == pytest.approx(0.05367)
    assert jobless[20] == pytest.approx(0.1502)
    assert len(rates) == 24 and len(jobless) == 24
    # formation steps once a year, the frequency the source publishes
    formation = [iv for iv in scenario.interventions if isinstance(iv, HouseholdFormation)]
    assert len(formation) == 6
    # and the credit stop lands in the quarter Lehman failed
    crunch = [iv for iv in scenario.interventions if isinstance(iv, CreditCrunch)]
    assert len(crunch) == 1 and crunch[0].start_tick == holdout.CRUNCH_TICK


def test_config_at_resolves_the_path_to_the_right_quarter():
    """The interventions are a path only if the config at tick t carries quarter t's inputs."""
    scenario = holdout.scenario(seed=1, ticks=24)
    for tick in (0, 2, 12, 23):
        cfg = scenario.config_at(tick)
        assert cfg.credit.euribor == pytest.approx(holdout.EURIBOR[tick])
        assert cfg.labour.jobless_rate == pytest.approx(holdout.JOBLESS[tick])
    # the credit stop persists after it lands, instead of being undone by the next rate step
    assert scenario.config_at(23).credit.max_ltv < scenario.config_at(0).credit.max_ltv


def test_predictions_are_stated_as_bands_before_the_run():
    """A pre-registered prediction is a band with a direction, not a point forecast."""
    for key in ("price_fall", "transaction_fall", "arrears_peak", "foreclosure_peak_per_year"):
        lo, hi = holdout.PREDICTIONS[key]
        assert lo < hi
    assert holdout.PREDICTIONS["price_fall"][1] < 0  # prices fall
    assert holdout.PREDICTIONS["transaction_fall"][1] < 0  # volume falls
    assert holdout.PREDICTIONS["arrears_peak"][0] > 0.0
