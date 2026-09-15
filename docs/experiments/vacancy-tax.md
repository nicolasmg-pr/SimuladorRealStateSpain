# Experiment 3 — vacancy tax (IBI surcharge on empty homes)

Run 2026-09-15, ten seeds, 40 ticks, lever at tick 20, 16 post-lever ticks.
Artefact: `runs/lever_dials_10seeds.json`. Not pre-registered.

## Design

`VacancyTax(rate, detection)`. The dial spans the statutory range and beyond it: 0.5% of value
(the typical Spanish IBI surcharge) to 3% (Vancouver's level), at 15% and 60% annual detection.

## Results (10 seeds)

| setting | national price | tensioned rent | transactions | vacancy rate | starts |
|---|---|---|---|---|---|
| 0.5%, detection .15 | −0.1% (3/10 up) | +0.3% (7/10) | −0.4% (5/10) | +0.4% (5/10) | 0.0% |
| 1.5%, detection .15 | 0.0% (4/10) | −0.4% (4/10) | +1.0% (6/10) | −0.1% (4/10) | +1.1% |
| 3%, detection .15 | −0.1% (3/10) | +0.8% (5/10) | +0.5% (6/10) | +0.1% (5/10) | −1.3% |
| 3%, detection .60 | +0.1% (6/10) | +0.2% (3/10) | +1.2% (6/10) | −0.3% (4/10) | +0.8% |

**Every cell is noise.** By the ledger's own rule — 5 or 6 seeds out of 10 in the reported
direction is no effect — this lever does nothing measurable at any setting, including a rate
six times the Spanish one at four times the detection.

## Against the sourced range (`policies/vacancy-tax.md §4`)

The dossier expects vacancy −13% (France) to −21…−67% (Vancouver) **among the taxed stock**,
and notes that adopting Spanish municipalities contain **under 10% of census-vacant homes**,
of whose owners only ~5% meet the statutory test. The model reproduces the *second* half and
therefore cannot reproduce the first: with `withheld_share` at 0.39 in the metro and 0.81 in
rural — stock that is off-market at any tax — the reachable base is small enough that a large
response on it is invisible nationally.

## What is reportable

The **null is the result**, and it is a direction ("no measurable effect"), not a magnitude.
It is also the one result in this set that is robust to the reporting contract: nothing here
depends on a parameter's calibration, because nothing moves.

## The caveat that matters

`withheld_share` is a calibrated guess (`docs/assumptions.md`), and it is doing the work. A
world where the withheld share is much lower is a world where this lever bites; no Spanish
evidence pins it. **The model's null is conditional on that guess**, and the honest claim is
"this instrument cannot reach the stock as the model is calibrated", not "vacancy taxes do
not work".
