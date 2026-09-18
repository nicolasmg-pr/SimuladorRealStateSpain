"""Does new supply reach the rent? Measured, because the answer is "no" and it is not a bug.

Written 2026-09-18 after an outside reading of the UI asked the obvious question: a public
programme at saturation raises vacancy by 4pp and leaves the rent alone, so where does the
supply go? The reading offered was a defect in the buyer/unit matching or in the vacancy rule.
It is neither. The units are built, they are listed, and they house people — the first test
here exists to close that reading off.

WHAT IS ACTUALLY CLOSED is the channel by which supply could reach the ask. There is exactly
one, in `agents/landlord.decide`:

    pressure = 1 + CONGESTION_GAIN · clip(tightness − 1, −0.5, 3.0)      # gain 0.05

Saturation drives rental tightness to ≈0.2 in the priced zones, i.e. raw slack ≈ −0.8, and the
clip throws away everything past −0.5. So the most that any amount of new supply can take off
a posted ask is **2.5%**, and the model is already against that bound at every seed tested.
The channel is not merely weak, it is saturated: the marginal unit buys nothing at all.

Measured over ten seeds, tail-20 mean of a 60-tick run, saturated minus baseline:

    zone         rent Δ (€/month)                    vacancy Δ        tightness
    TENSIONED    mean −14.9  (−197 … +92, 6/10 neg)  +4.28pp (min +3.83)  mean 0.23
    SECONDARY    mean +14.6  ( −44 … +87, 5/10 neg)  +2.18pp (min +1.55)  mean 0.16

The rent response is indistinguishable from zero — the sign splits 6/4 and 5/5 and the spread
is an order of magnitude wider than the mean. The vacancy response is large and present in
every seed. That is the whole finding: **supply becomes empty dwellings, not cheaper ones.**

A SECOND MECHANISM, observed and deliberately NOT asserted here. `ask = max(floor, market_ask)`
floors every ask at the landlord's total-return hurdle `required_rent` (model-spec §7.1), which
is a function of the price index and of expected price growth — never of how many units stand
empty. Supply depresses E[g], E[g] enters the hurdle negatively, so the floor can RISE with
supply. Across the same ten seeds the share of vacant private units sitting on that floor is
bimodal rather than universal (tensioned 3/10 seeds, secondary 6/10, and the secondary share
FALLS from 0.90 baseline to 0.60 saturated), so it is a regime the model enters in some seeds,
not a law. It reinforces the closure where it binds; it is not the cause of it. Asserting it
would be asserting one seed's accident — the mistake that produced the first draft of this file.

THE RENT LEG ONLY. docs/claims.md F-3 measures the land-release lever moving the national SALE
price −7.5% to −12.9% (0/10 seeds up) once the pipeline lag is halved. The sale market has a
tightness term in its auction (§5c.7); the rental market has only the clipped multiplier above.
Do not read this file as "supply does nothing in this model" — it does, on the other side.

Nothing here licenses a rent quantity from a supply lever. See docs/validation.md, "Supply
saturation does not reach the rent", and model-spec §7.6.
"""

import numpy as np
import pytest

from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.market.stock import PUBLIC_ID, Tenure
from resim.metrics import to_frame
from resim.scenario import PublicHousing, Scenario

# Ten seeds, per model-spec §13.4: the rent and vacancy responses below ARE reported
# quantities, and this project does not report on fewer. It costs twenty 60-tick runs.
SEEDS = tuple(range(1, 11))

# The dose: 30 units/tick against a ~12k-unit stock — ≈+8% of the parque over the run — with
# `crowding_out=0` so no private construction is displaced. Deliberately far past anything a
# government would build. The point is that even this does not reach the rent.
SATURATION = PublicHousing(start_tick=8, units_per_tick=30, crowding_out=0.0)

PRICED_ZONES = (ZoneType.TENSIONED, ZoneType.SECONDARY)
TAIL = 20


def _run(seed: int, interventions=()):
    scenario = Scenario(
        name="saturation",
        baseline=SimConfig.baseline(seed=seed, ticks=60),
        interventions=interventions,
    )
    return Engine(scenario).run()


@pytest.fixture(scope="module")
def runs():
    """(baseline, saturated) end state and frame per seed."""
    out = {}
    for seed in SEEDS:
        base, sat = _run(seed), _run(seed, (SATURATION,))
        out[seed] = (base, sat, to_frame(base), to_frame(sat))
    return out


def _tail_delta(runs, column: str) -> list[float]:
    """Saturated minus baseline, tail-20 mean, one entry per seed."""
    return [
        sat_f[column].tail(TAIL).mean() - base_f[column].tail(TAIL).mean()
        for _, _, base_f, sat_f in runs.values()
    ]


def test_the_units_are_built_and_do_reach_households(runs):
    """Close off the reading that was offered: the units are not lost in the matching.

    Public tenancies multiply and the number of housed dwellings rises, in every seed.
    Whatever is wrong with the supply channel, it is not that new stock fails to enter.
    """
    for seed, (base, sat, _, _) in runs.items():

        def public_rented(state):
            return sum(
                1
                for u in state.stock.units.values()
                if u.owner_id == PUBLIC_ID and u.tenure is Tenure.RENTED
            )

        def housed(state):
            return sum(
                1
                for u in state.stock.units.values()
                if u.tenure in (Tenure.RENTED, Tenure.OWNER_OCCUPIED)
            )

        assert public_rented(sat) > 2 * public_rented(base), seed
        assert housed(sat) > housed(base), seed


def test_the_only_supply_to_ask_channel_is_clipped_shut(runs):
    """The root cause, asserted where it lives: the congestion clip binds at every seed.

    `clip(tightness − 1, −0.5, 3.0)` — saturation puts the priced zones at tightness ≈0.2, so
    raw slack is ≈ −0.8 and the clip discards the part past −0.5. Asserting that the clip BINDS
    is the point: an unclipped channel would still be a gradient, and further supply would
    still do something. Against the bound, the marginal unit does nothing at all.

    If this ever goes red because tightness came back above 0.5, the supply channel has been
    rebuilt and this file needs rewriting — not silencing.
    """
    for seed, (_, sat, _, _) in runs.items():
        for zone in PRICED_ZONES:
            tightness = sat.tick_events["rental_tightness"][zone]
            assert tightness - 1.0 < -0.5, (seed, zone, tightness)


def test_the_rent_response_to_saturation_is_indistinguishable_from_zero(runs):
    """The headline, stated as what it is — and NOT as a measured fall or a measured rise.

    Both priced zones split their sign across the ten seeds and carry a spread an order of
    magnitude wider than their mean. Asserted as: the sign is not consistent, and the mean is
    small against the dispersion. Deliberately no magnitude and no direction — there is none
    to report, and the UI must not draw one.
    """
    for zone in PRICED_ZONES:
        deltas = _tail_delta(runs, f"rent_{zone.name.lower()}")
        negatives = sum(d < 0 for d in deltas)
        assert 3 <= negatives <= 7, (zone, negatives, deltas)
        mean, sd = float(np.mean(deltas)), float(np.std(deltas, ddof=1))
        assert abs(mean) < sd, (zone, mean, sd)


def test_saturation_shows_up_as_vacancy_instead(runs):
    """Where the supply goes when it cannot go into the price: it stands empty.

    This is the observable that made the panel look broken, and it is the correct behaviour of
    a market whose asks cannot fall — the spec's own words for the rural zone are that
    discounting demand further "would leave units unlet". Present in every seed, both priced
    zones, which is why it can be asserted per seed where the rent cannot.
    """
    for zone in PRICED_ZONES:
        deltas = _tail_delta(runs, f"vacancy_{zone.name.lower()}")
        assert min(deltas) > 0.01, (zone, deltas)


def test_the_composition_control_moves_when_the_headline_does(runs):
    """Why `rent_overburden_share` cannot be read straight off this scenario either.

    A public programme moves the poorest tenants onto administered rents, which takes them out
    of the MARKET-tenant denominator the headline is averaged over. `tenant_entry_share`
    (metrics, 2026-09-18) is the dial that says so. Asserting it moves is asserting that the
    headline's population differs between the two runs — i.e. that any delta drawn between
    them mixes a burden change with a composition change.
    """
    deltas = _tail_delta(runs, "tenant_entry_share")
    assert max(abs(d) for d in deltas) > 0.005, deltas
