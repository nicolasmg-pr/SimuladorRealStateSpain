# Experiment 2 — transaction tax (ITP)

Run 2026-09-15 on the post-§5c.8 model. Ten seeds, 40 ticks, lever at tick 20, outcomes
averaged over the 16 post-lever ticks. Artefact: `runs/lever_dials_10seeds.json`.
**Not pre-registered** — a re-measurement of a registered lever, labelled as such.

## Design

`TransactionTax(itp_delta)` moves the effective buyer tax in every zone. The dial runs from a
+2pp hike to the −4pp cut the PP has pledged for under-40s (ITP 10% → 6% is the headline case;
the model has no age structure, so this is the whole-market version of it).

## Results (10 seeds, sign count in brackets)

| setting | national price | tensioned contract rent | transactions | starts | ownership |
|---|---|---|---|---|---|
| +1pp | −0.3% (3/10 up) | +1.7% | **−3.5%** (0/10 up) | +0.1% | −0.15% |
| +2pp | −0.8% (0/10) | +2.3% (9/10) | **−4.6%** (0/10) | −1.0% | −0.26% |
| −2pp | **+0.9%** (10/10) | −2.0% | **+6.4%** (10/10) | +1.3% | +0.07% |
| −4pp | **+1.9%** (10/10) | −5.5% | **+11.1%** (10/10) | +3.4% | +0.10% |

## Against the sourced range (`policies/transaction-tax.md §4`)

- **Volume, −4% to −15% per +1pp.** The model gives −3.5%/pp at +1pp and −2.3%/pp at +2pp:
  **at or just below the bottom of the range**, and sub-linear where the sources are roughly
  linear. Read as a lower bound on the volume response.
- **Capitalisation, 40% to >100% of the tax.** A 2pp cut on a ≈€243k price is ≈€4.9k; the
  price rises 0.9%, ≈€2.2k, so **≈45% is capitalised** — the low end of the sourced band, and
  the one number in this experiment that lands inside it comfortably.
- **Mobility, −8% per +1pp.** Not measurable here: the model has no distance-differentiated
  moves.

## What is reportable

Transactions are a magnitude under §13.2 (largest unsourced share 0.20). Price effects are a
magnitude too, conditional on the ask-markup band. **The rent leg is direction-only** — the
+2.3% under a hike and −5.5% under a cut rest on the rent side, which `small_landlord_premium`
governs (§7.1b). Its sign is the interesting part and it is new: a purchase tax pushes
households into the rental market and rents follow, which is a cost of ITP that neither its
defenders nor its critics cite.

## Side effects

Starts respond in the same direction as volume but a third as strongly; ownership barely moves
(±0.26%), which is the standard result that a transaction tax reallocates *when* people move
rather than *whether* they own.
