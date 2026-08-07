"""Engine-level tests.

For a stochastic model these are the tests that matter — not "does it return 42",
but "is it reproducible" and "does it behave the way the theory says".
"""

import pytest


@pytest.mark.skip(reason="scaffold — engine not implemented")
def test_same_seed_same_run():
    """Two runs with one seed produce identical series. Non-negotiable."""


@pytest.mark.skip(reason="scaffold — engine not implemented")
def test_conservation():
    """Units are never created or destroyed outside construction/demolition."""


@pytest.mark.skip(reason="scaffold — engine not implemented")
def test_baseline_reaches_steady_state():
    """With no intervention, prices settle rather than diverge."""


@pytest.mark.skip(reason="scaffold — engine not implemented")
def test_supply_shock_lowers_prices():
    """Sanity direction check: more construction, lower prices. If not, the model is wrong."""
