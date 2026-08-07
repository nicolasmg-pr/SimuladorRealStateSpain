"""Agent decision tests — each actor in isolation, against a hand-built WorldState."""

import pytest


@pytest.mark.skip(reason="scaffold — agents not implemented")
def test_household_cannot_bid_above_credit_limit():
    """Ability-to-pay binds before willingness-to-pay."""


@pytest.mark.skip(reason="scaffold — agents not implemented")
def test_investor_exits_when_yield_below_hurdle():
    """Rate rise past the hurdle turns investors into sellers."""


@pytest.mark.skip(reason="scaffold — agents not implemented")
def test_developer_starts_only_above_margin():
    """No construction when expected margin is negative."""


@pytest.mark.skip(reason="scaffold — agents not implemented")
def test_agents_do_not_mutate_state():
    """decide() is read-only. Guards the whole tick-order contract."""
