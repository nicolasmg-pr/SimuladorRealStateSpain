# Experiment 7 — land release and permitting speed

Run 2026-09-15, ten seeds, lever at tick 20, **80 ticks**. The horizon is the first finding:
the release lag is 40 ticks, so the 40-tick run this project used until today measured *nothing
at all* — every outcome, including starts, came back exactly 0.00%. A lever slower than the
experiment is not a null result, it is an unmeasured one.
Artefact: `runs/lever_dials_long_10seeds.json`.

## Design

`LandRelease(extra_units_per_tick, release_lag, permit_lag_delta)`: how much serviced land
enters per tick, how long it takes to arrive, and whether permitting is accelerated. The dial
spans the dossier's pipeline range (10–20 years planning-to-homes ⇒ 40 ticks, against a
reformed 20) and the measured Madrid permit reform (−17.5 months ⇒ ≈−6 ticks).

## Results at 80 ticks (10 seeds)

| setting | national price | tensioned contract rent | starts | ownership | vacancy |
|---|---|---|---|---|---|
| 4/tick, lag 40 | −0.3% (0/10 up) | +0.5% (6/10) | **+15%** (10/10) | +0.09% (10/10) | +0.6% |
| 12/tick, lag 40 | −1.0% (0/10) | +4.4% (9/10) | **+55%** (10/10) | +0.31% (10/10) | +1.9% |
| 12/tick, lag 20 | **−7.5%** (0/10) | +9.4% (8/10) | +60% (10/10) | +1.73% (10/10) | +12.2% |
| 12/tick, lag 20, permits −6 | **−12.9%** (0/10) | +6.1% (8/10) | +50% (10/10) | +2.62% (10/10) | +18.3% |

## Two findings, and the second is uncomfortable

**1. Building does lower prices — the lag is the whole story.** At the dossier's unreformed
pipeline (40 ticks) a tripled land release moves prices −1.0%. Halve the lag and the same
release moves them −7.5%; add the Madrid permit reform on top and −12.9%, with the ownership
rate up 2.6% on 10/10 seeds. The lever is not weak, it is **slow**, and speed is the part
policy can actually change. This corrects `docs/claims.md` F-3, which reported "0.0%, no
effect" from a 40-tick run.

**2. It raises rents.** +9.4% at 12/tick, lag 20, on 8 of 10 seeds. The mechanism is §7.1 and
it is worth stating plainly: the landlord's required rent is
`V · (bond + premium − E[g]) / (12 · (1 − c))`. A credible supply programme kills expected
appreciation — measured here at **−1.9pp/yr** — and the return the landlord is no longer
getting as capital gain has to come from the yield instead, which rises **+1.14pp**. Prices
−7.5%, rents +11.2%, contract yield +1.14pp, on the same runs.

Nobody wrote that rule. Whether Spain works that way is untested: the dossier's land-release
evidence covers prices and permits, **not rents**, so this is a prediction the model makes and
no registered source can adjudicate. It is also direction-only under §13.2, because the rent
side rests on `small_landlord_premium`.

## Against the sourced range (`policies/land-release.md §4`)

- **Long-run price effect of restrictiveness, 0% (Montalvo) to 25–35% of the price level.**
  The reformed-pipeline settings land at 7.5–12.9%, inside that spread and below its top.
- **Land release during a boom: +28–30% land ⇒ ≈7% of a 130–180% boom, i.e. near-zero net
  restraint.** The model agrees at the unreformed lag (−1.0%) and disagrees once the lag is
  halved — which is the same statement the sources make, since their episodes had the long lag.
- **Permit reform −17.5 months, ≈€50k/unit carry cost.** Reproduced as a lag change; the cost
  saving is not modelled.

## What is reportable

Starts, completions and the price level are magnitudes conditional on the sourced bands. The
rent rise is a **direction**, and a novel one. The vacancy rise (+12 to +18%) is mechanical —
new stock waits for buyers — and should not be read as slack demand.
