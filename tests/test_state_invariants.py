"""Household/unit consistency, asserted on full runs.

Phase A rewrote inheritance (`engine._demography`): estates now pass whole to one heir, and an
heir with no home of their own takes possession of the inherited dwelling. That moves
households between statuses and units between tenures outside the clearing step, which is the
one place in the model allowed to do it apart from the engine itself.

A change like that is only safe if the household↔unit bookkeeping still closes, and "the suite
is green" does not show that: no existing test reads the two registries against each other.
These do. They are invariants, not calibration — if one fails, the state is corrupt and every
number measured on it is meaningless, whatever the validation targets say.
"""

import pytest

from resim.config import SimConfig
from resim.engine import Engine
from resim.market.stock import Tenure
from resim.scenario import Scenario
from resim.state import HouseholdStatus


@pytest.fixture(scope="module")
def finished_states():
    return [
        Engine(Scenario(name="b", baseline=SimConfig.baseline(seed=s, ticks=60))).run()
        for s in (1, 2, 3)
    ]


def test_every_housed_household_occupies_the_unit_it_points_at(finished_states):
    for state in finished_states:
        for hh in state.households.values():
            if hh.unit_id is None:
                assert hh.status is HouseholdStatus.SEEKER, f"hh {hh.id} housed with no unit"
                continue
            unit = state.stock.units.get(hh.unit_id)
            assert unit is not None, f"hh {hh.id} points at missing unit {hh.unit_id}"
            assert unit.occupant_id == hh.id, f"hh {hh.id} does not occupy unit {unit.id}"


def test_status_matches_tenure(finished_states):
    """An OWNER owns and owner-occupies its home; a TENANT's home is RENTED."""
    for state in finished_states:
        for hh in state.households.values():
            if hh.unit_id is None:
                continue
            unit = state.stock.units[hh.unit_id]
            if hh.status is HouseholdStatus.OWNER:
                assert unit.owner_id == hh.id, f"OWNER {hh.id} does not own unit {unit.id}"
                assert unit.tenure is Tenure.OWNER_OCCUPIED, f"unit {unit.id} is {unit.tenure}"
            elif hh.status is HouseholdStatus.TENANT:
                assert unit.tenure is Tenure.RENTED, f"TENANT {hh.id} in a {unit.tenure} unit"


def test_no_ghost_or_mismatched_occupants(finished_states):
    """Every occupant exists and points back. A dissolved household leaves no occupant behind."""
    for state in finished_states:
        for unit in state.stock.units.values():
            if unit.occupant_id is None:
                continue
            occupant = state.households.get(unit.occupant_id)
            assert occupant is not None, f"unit {unit.id} occupied by dissolved hh"
            assert occupant.unit_id == unit.id, f"unit {unit.id} back-reference broken"


def test_owner_occupied_units_are_occupied_by_their_owner(finished_states):
    for state in finished_states:
        for unit in state.stock.units.values():
            if unit.tenure is Tenure.OWNER_OCCUPIED:
                assert unit.occupant_id == unit.owner_id, f"unit {unit.id} owner != occupant"


def test_owner_count_equals_owner_occupied_unit_count(finished_states):
    """The identity the ownership rate is read off. It held before phase A and must still."""
    for state in finished_states:
        owners = sum(1 for h in state.households.values() if h.status is HouseholdStatus.OWNER)
        occupied = sum(1 for u in state.stock.units.values() if u.tenure is Tenure.OWNER_OCCUPIED)
        assert owners == occupied, f"{owners} owner households vs {occupied} owner-occupied units"
