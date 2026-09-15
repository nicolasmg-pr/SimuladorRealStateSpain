# Experiment 4 — public housing

Run 2026-09-15, ten seeds, lever at tick 20. **Two horizons**, and the difference between them
is the first finding: the programme's delivery lag is 20 ticks, so a 40-tick run measures the
starts and none of the deliveries. The reportable table is the 80-tick one.
Artefacts: `runs/lever_dials_10seeds.json` (40 ticks), `runs/lever_dials_long_10seeds.json` (80).

## Design

`PublicHousing(units_per_tick, crowding_out, delivery_lag=20, rent_discount=0.5)`. The dial
spans the announced ambition (≈48k/yr at the model's 1:2000 scale) and double it, and then
sweeps the parameter the dossier refuses to resolve: **crowd-out**, the share of public
building that displaces private building. `policies/public-housing.md §4` keeps net stock
added per public unit at **0.2–1.0**, i.e. crowd-out 0–0.8.

## Results at 80 ticks (10 seeds, deliveries included)

| setting | national price | tensioned contract rent | starts | ownership | vacancy |
|---|---|---|---|---|---|
| 6/tick (≈48k/yr) | **+1.1%** (10/10 up) | −2.9% | +33% | −0.24% | +2.1% |
| 12/tick (≈96k/yr) | **+3.2%** (10/10) | −5.9% | +51% | −0.61% | −0.3% |
| 12/tick, crowd-out 0.60 | **+9.7%** (10/10) | +0.9% | +37% | −1.99% | −5.3% |
| 12/tick, crowd-out 0.10 | **−1.2%** (0/10 up) | −6.7% | +68% | +0.24% | +6.6% |

At 40 ticks the same rows read +0.1% to +0.8% on price and −0.4% to −1.8% on rent: the
programme looks small because its output has not arrived yet.

## The result worth the experiment

**Crowd-out decides the sign of the price effect.** At 0.10 public building lowers sale prices;
at 0.60 it raises them 9.7%, because the programme consumes builders and land that the private
sector would have used and the households it houses stay out of ownership (−2.0%). Rents fall
in every case *except* the high-crowd-out one, where the private rental stock shrinks faster
than the public stock replaces it.

That is a conditional prediction of exactly the shape this project exists to produce: the
answer is not "public housing raises prices" or "lowers them", it is **"it lowers them if the
crowd-out is at the low end of the range the evidence admits, and raises them if it is at the
high end"** — and the evidence admits both (Sinai-Waldfogel ≈1/3, Murray ≈1.0).

## Against the sourced range

- **Rent effect, 0 to −15% at a 40% stock share, ≈−0.3…−0.5%/pp.** The programme adds ≈4pp of
  rental stock at 12/tick over the horizon and cuts rents 5.9%, i.e. ≈−1.5%/pp — **three times
  the sourced slope**, and a flag rather than a success. The model's public units are let at
  half market rent with no queue rationing beyond the model's own matching, which is more
  generous than a real allocation system.
- **Occupant discount −37…−57%.** Imposed (`rent_discount=0.5`), not tested.
- **Annual output 11–14.5k qualifications/yr today against 40–60k announced.** The 6/tick row
  is the announced ambition; the model says even that is +1.1% on prices if crowd-out sits
  mid-range.

## What is reportable

Starts and completions are magnitudes (largest unsourced share 0.14). **The price sign is
reportable and the rent leg is not** (§7.1b, `small_landlord_premium`). The crowd-out result
should be quoted as a *sign conditional on a parameter range*, never as a level.
