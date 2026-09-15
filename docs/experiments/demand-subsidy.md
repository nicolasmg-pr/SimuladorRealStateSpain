# Experiment 6 — demand subsidy (ICO guarantees, and a rent subsidy)

Run 2026-09-15, ten seeds, 40 ticks, lever at tick 20, 16 post-lever ticks.
Artefact: `runs/lever_dials_10seeds.json`. Not pre-registered.

## Design

`DemandSubsidy`: the ICO aval (an LTV boost for eligible first-time buyers, means-tested on
net wealth since the BOE resolution of 2 Jul 2026) and, as a separate arm, a €275/month rent
subsidy to 10% of tenants. The dial sweeps the eligible share (25% → 50%), removes the wealth
cap to reproduce the pre-2026 instrument, and then switches instrument entirely.

## Results (10 seeds)

| setting | national price | tensioned contract rent | transactions | ownership | starts |
|---|---|---|---|---|---|
| aval, 25% eligible | **+0.6%** (10/10 up) | −0.9% (4/10) | **+3.2%** (9/10) | +0.03% (5/10) | +1.5% |
| aval, 50% eligible | **+1.4%** (10/10) | −4.0% (0/10 up) | **+4.9%** (9/10) | +0.08% (7/10) | +2.6% |
| aval, no wealth cap | +0.6% (10/10) | −1.0% (4/10) | +3.3% (9/10) | +0.01% (4/10) | +1.5% |
| rent subsidy €275, 10% | +0.1% (7/10) | −0.4% (3/10) | +1.0% (6/10) | −0.03% (3/10) | +0.7% |

## Three readings

1. **The guarantee capitalises and does not move ownership.** Prices up 10/10 seeds at every
   setting, transactions up 9/10, the ownership rate inside noise. It changes *who buys when*,
   not how many households own — which is the standard prediction for a credit-side subsidy in
   a supply-constrained market, and the model reproduces it rather than testing it.
2. **The wealth cap is inert.** Removing it entirely — the pre-2026 instrument — changes
   nothing measurable (+0.6% price either way). `docs/validation.md` says why: with a €150,000
   net-wealth ceiling, about 1% of tenants are excluded by it. A means test that screens out
   one household in a hundred is a press release, not an instrument.
3. **Doubling eligibility doubles the price effect and cuts rents 4%.** The rent leg is the
   mirror of the ITP result in experiment 2: households moved into ownership stop bidding for
   tenancies. It is direction-only (§7.1b) and it is the only part of this lever that helps
   anyone who is not already close to buying.

## Against the sourced range (`policies/demand-subsidy.md §4`)

Capitalisation of purchase subsidies runs **0–10%** (UK NAO) to **over 100%** of present value
(Carozzi-Hilber-Yu, Greater London), with Spanish IRPF-deduction estimates of −1% to −8.5% on
removal. The model's +0.6% price for a 25%-eligible aval sits at the **low-capitalisation end**
of that spread. Rent-subsidy capture by landlords is sourced at **10–78%**; the model's rent
arm moves rents −0.4% (3/10), i.e. **no measurable capture** — which is below the entire
sourced range and is a flag against the model, not against the evidence. Its rental market
clears on tenant budgets, and a subsidy that raises those budgets should raise rents; that it
does not is a gap worth the next person's attention.

## What is reportable

Prices and transactions are magnitudes conditional on the ask-markup band; the ownership rate
is **direction-only** (`buy_attempt_prob` carries 0.36 of its variance), which matters here
because the ownership null is the headline. Read it as "no measurable effect", not "zero".
