# Phase G — the valuation anchor, and `overbid_sigma` sourced

Date: 2026-09-15. Status: **mechanism prototyped and measured; recalibration not done. Suite
red (7 failures) on the branch `source-overbid-sigma`.**

Origin: the KB-refresh audit named sourcing `overbid_sigma` and `landlord_required_spread` as
the highest-value evidence work left on the model, because between them they were blocking
every reportable magnitude under the variance rule (§13.2). `landlord_required_spread` no
longer exists — phase B split it into a measured prime spread, a sourced cost share and one
declared free premium — so this phase is about the other one, and about what trying to source
it exposed.

## 1. What `overbid_sigma` is, and what it turned out to be

Since phase D it is **idiosyncratic taste**: how much this buyer happens to like this dwelling,
applied to the value they put on it (`model-spec §5c.1`). Its empirical counterpart is exact
and standard: the dispersion of log transaction prices for the same dwelling, net of location ×
period and of observable quality — what the literature calls idiosyncratic price dispersion.

### 1.1 The evidence (registered in `sources.md`, 2026-09-15)

| Source | Data | Idiosyncratic dispersion, **per sale** |
|---|---|---|
| Kotova & Zhang (Stanford GSB / Chicago Booth, working paper) | US zipcodes 2012–2016, repeat-sales + hedonic hybrid, house and zipcode-month fixed effects | mean **16.8%**, sd 4.6%, p10 11.2%, p90 22.6% |
| Giacoletti, *RFS* 34(8) 2021 | California resales 1989–2013, with capital-expenditure data | returns 9.6–17.6% ⇒ **6.8–12.4%** |
| Landvoigt, Piazzesi & Schneider, *AER* 2015 | San Diego 1999–2007 | returns 8.8–13.8% ⇒ **6.2–9.8%** |
| BdE DO 2508 (2025) | **1,032,960 Spanish transactions 2015–2022**, census-section × quarter fixed effects | R² 85.70% — bounds the residual *share*, not its level |

Three methods, three datasets, one overlapping range. The conversion matters: a buy-and-sell
incurs the error twice, so return dispersion = per-sale dispersion × √2, and Giacoletti's and
LPS's published numbers are returns.

**There is no published Spanish estimate.** Checked: INE's IPV methodology (estimates residual
variances by category, publishes none), Registradores' ERI Anuario §1.2.2 (the IPVVR runs
Calhoun's three-stage weighting on **1,274,958 sale pairs** — its variance function *is* this
quantity — and publishes only the index), BdE DO 2010, CaixaBank's dispersion note (across
municipalities, which is the zone ladder, not this). Registered as a negative result. Closing
it needs Registradores or Catastro microdata.

**Target band adopted: 6–17% per sale, central 10%.** The low end is LPS, the high end is
Kotova & Zhang's national mean; Giacoletti spans the middle.

### 1.2 What the model does

Measured on the model's own transactions — residual sd of log price after removing zone ×
tick and log quality, 60 ticks, last 20, three seeds:

**2.3%.** Between three and seven times too concentrated.

## 2. The finding this phase exists for

Raising `overbid_sigma` to anything near its measured value does **not** just widen the
distribution — it moves the price level:

| σ | dispersion | price-to-income (band 7.0–8.2) | discount (4–12%) | sold in the quarter (0.43–0.63) |
|---|---|---|---|---|
| 0.02 (shipped) | 2.3% | 7.81 | 3.1% | 0.48 |
| 0.10 | 6.0% | 9.53 | 1.0% | 0.40 |
| 0.30 | 9.2% | 10.01 | 0.9% | 0.39 |
| 0.45 | 10.5% | 10.25 | 0.9% | 0.39 |

**Cause, identified by elimination rather than asserted.** Two hypotheses were prototyped and
both were refuted before the third was adopted:

1. *The index carries the auction's selection premium and compounds it.* Correcting each
   transacted price by the expected order statistic of its own auction (Monte-Carlo κ(n), then
   κ(n, m) including the search draw) made the level **worse** (p/inc 10.7 at σ = 0.15) and
   then absurd (p/inc 3.6, 72% of sales above ask). An analytic correction cannot work,
   because the realised price is also clipped by the budget, the reserve and the ask.
2. *A user-cost ceiling would discipline the level.* Capitalising the model's transacted rent
   at the mortgage rate plus maintenance minus expected growth gives a ceiling ≈ 40 years of
   rent against a price of ≈ 15, so it never binds. Measured: identical results to no ceiling.
3. **Adopted:** `value = index × quality × taste` has **no nominal anchor**. The index is the
   median of *winning* prices, the winner is selected on a high draw, and the result is fed
   back as next tick's valuation. At σ = 0.02 the loop is invisible; at the sourced σ the
   market runs to the only thing that does stop it — the credit ceiling — which is why
   price-to-income lands at ≈ 10 whatever σ is beyond 0.1.

So `overbid_sigma` has been holding the price level down by being too small, and the Sobol
finding (26–42% of the variance of every price-like moment) was reading this, not noise.

## 3. The mechanism (to become `model-spec §5c.6`)

Two indices, kept apart on purpose:

- `ZoneState.price_index` — **realised** transaction basis. What every indicator reports, what
  expectations are formed on, what the landlord hurdle capitalises. Unchanged.
- `ZoneState.valuation_index` — **taste-neutral** basis: the same sales repriced as if the
  price-setting bidders had drawn an average taste (ε = 1), with the budget cap, the reserve,
  the ask and the bargaining weight all still binding where they bound. This is what a buyer
  anchors on.

The neutral price is not a closed-form correction: each auction is run twice, once as it
happened and once with the neutral valuations of the same bidders, through the same
`auction_price` rule. That is why it survives budget caps and ask clipping, which defeated
hypothesis 1.

**Verified core claim.** With buyers valuing off the neutral index, the price level stops
responding to σ while the dispersion keeps responding:

| σ | 0.02 | 0.15 | 0.30 |
|---|---|---|---|
| dispersion | 1.6% | 6.8% | 11.0% |
| price-to-income | 6.38 | 6.40 | 6.44 |

σ is now a dispersion parameter. That is the whole point of the phase.

**Falsification.** If the neutral-anchored level still moves with σ by more than seed noise,
the correction is not doing what this section claims and the section is wrong.

## 4. What it costs, and what is not done

The old calibration was absorbing the selection premium, so removing it moves everything:

- price-to-income falls to ≈ 6.6 at the shipped σ (band 7.0–8.2);
- the contract-basis gross yield rises to 8–9% (band 6.5–7.5%) — prices fell against rents;
- with sellers still posting off the realised index the level partly re-compounds through the
  ask (p/inc 6.6 → 8.3 → 9.1 across σ), so sellers were moved onto the neutral index too;
- posting off the neutral index at the shipped 8% markup makes 55% of sales close above the
  ask (Fotocasa: 9%), because the posted markup no longer covers the premium.

That last one is the phase's opportunity as well as its bill. The ask-markup row already
records two numbers it could not reconcile — the practitioner rule of thumb of **15–20% over
the expected price** and the realised gap of **6.2%** — and under a neutral anchor those are no
longer in conflict: the difference between them *is* the selection premium. Reproducing both
is the test that the block is right.

A 27-point grid over (σ, ask_markup, θ) at two seeds does **not** find a point that meets all
four observables: the best corner sits at the grid edge (σ 0.10, markup 0.16, θ 0.70) with the
discount at 2.8% against 4–12%, 12% of sales above ask against 9%, p/inc 8.5 and the quarter
share at 0.35 against 0.43–0.63. **A grid search is not the instrument.** The block needs the
phase-E treatment: LHS over (σ, ask_markup, θ, m, buy_attempt_prob), scored on the four
observables with the guard rails as constraints, then ten seeds, then Sobol re-run to see
whether the price level finally clears the variance rule.

Suite state on arrival: **7 failures** at the shipped σ — `price_to_income`,
`national_entry_yield`, `holdout_boom_rent_growth`, `sale_discount`, two rent-cap gates, and
`rate_shock_cuts_transactions_before_prices`. None of them are re-banded; they are the bill.

## 5. Order of work from here

1. `model-spec §5c.6` written from §3 above, with §9 gaining the dispersion target (6–17%).
2. LHS re-identification of the sale block (§4), on the calibration window only.
3. Ten-seed validation, `docs/validation.md` write-up, adversarial pass.
4. Sobol re-run on the surviving free parameters; apply the variance rule as written.
5. The 2008–13 episode is **spent** (§13.11) — it can only be a diagnostic here, never a test.
