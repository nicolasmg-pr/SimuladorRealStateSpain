# Experiment 5 — tourist-rental restriction

Run 2026-09-15, ten seeds, 40 ticks, lever at tick 20, 16 post-lever ticks.
Artefact: `runs/lever_dials_10seeds.json`. Not pre-registered.

## Design

`TouristRestriction(phaseout_rate, conversion_share)`: what share of the seasonal stock is
extinguished per year, and what share of that returns to the long-term market. The dial spans
Barcelona's announced full phase-out (100%/yr) down to a quarter of it, and the conversion
share spans the dossier's **10–50%** range.

## Results (10 seeds)

| setting | national price | tensioned contract rent | vacancy rate | new leases | transactions |
|---|---|---|---|---|---|
| 25%/yr, 30% return | −0.1% (4/10 up) | +0.4% (5/10) | **+6.8%** (10/10) | +1.2% | +0.2% (5/10) |
| 50%/yr, 30% return | 0.0% (2/10) | +0.4% (6/10) | **+9.8%** (10/10) | — | +0.8% (7/10) |
| 50%/yr, 50% return | 0.0% (4/10) | −0.3% (5/10) | **+9.8%** (10/10) | — | +0.9% (6/10) |
| 100%/yr, 50% return | 0.0% (5/10) | **−1.4%** (3/10 up) | **+11.0%** (10/10) | — | +0.6% (4/10) |

## Reading

Only the **vacancy** column is unanimous, and it is the mechanical one: units leave the
seasonal segment and sit empty while they wait for a long-term tenant. The rent effect is
noise until the most aggressive setting, where it reaches −1.4% with 7 of 10 seeds down.

Set against the sourced **−0…−3% rents per −1pp of VUT share** (Barcelona +1.9% mean, up to
+7% in the densest neighbourhoods): the model's seasonal share in the tensioned zone is 2.8%,
so a full phase-out is ≈−2.8pp and −1.4% of rent is **≈0.5%/pp — inside the sourced band, at
its lower half**. The claim this refutes is not the academic estimate, which the model agrees
with, but the political one that tourist flats are why rents rose.

## What is reportable

The rent leg is direction-only (§7.1b), and at three of the four settings it is not even a
direction. The honest output of this experiment is: **a full phase-out is worth about one
percent of rents in this model, and the stock spends the transition empty.**

## What the model cannot see

Conversion is a parameter here, not an outcome: whether a delisted tourist flat becomes a
long-term tenancy, a temporada let, or a second home is exactly what the Spanish debate is
about, and the dossier's 10–50% range is imported from NYC and Berlin. The model also has no
coastal zone (`docs/validation.md`), where most Spanish VUT stock actually is.
