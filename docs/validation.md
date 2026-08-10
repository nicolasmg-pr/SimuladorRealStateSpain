# Phase 6 — Calibration & validation report

Baseline = `SimConfig.baseline()`, 60 ticks, seeds {1,2,3}, last 20 ticks averaged.
Enforced continuously by `tests/test_validation.py` — no scenario result is reported unless
that suite passes (engineering standard, `plan.md`).

Revised 2026-08-10 after the model audit. The audit changed enough of the mechanics that
every number below was re-measured; the previous revision's figures are not comparable. What
changed and why is in "Audit corrections" at the end.

## Direct calibration

Observable parameters set straight from Tier-1 data (see `config.py` field comments):
EFF2024 income/wealth distributions, ECV tenure shares by zone, BdE LTV/DSTI/term/pass-through,
Euroval construction lag, MIVAU output flow, idealista/BdE yield ladder, Registradores foreign
share, Housing Europe/MIVAU social-rental stock.

Free parameters (calibrated, labeled `guess`): buyer participation level and its two
sensitivities, overbid dispersion, ask decay, seeker wealth, tightness pressure, hazard
scale, inventory markdown, zone land-availability split.

Two parameters are now *derived* rather than fitted, which removes two degrees of freedom:
- the developer's start-volume coefficient — the rule is a constant-elasticity form, so
  `ZoneConfig.supply_elasticity` **is** the elasticity the model exhibits (model-spec §6b);
- the developer's reference price level, computed from `median_value × price_multiplier ×
  new_build_premium` instead of being a knob.

## Validation targets vs baseline (model-spec §9)

3-seed means, last 20 of 60 ticks.

| # | Target | Empirical range | Model | Pass |
|---|---|---|---|---|
| 1 | Ownership rate | 70–74% (EFF2024, declining) | 70.4% | ✓ (bottom of band) |
| 1b | Non-owner share (tenant + seeker ≈ ceded/sharing) | 24–31% | 29.6% (23.7 + 6.0) | ✓ |
| 2 | Price-to-income (disposable basis, BdE) | 7–8 | 7.64 | ✓ |
| 2b | Price *level* ranking T > S > R | — | holds | ✓ |
| 2c | Price-to-**income** ranking T > S > R | — | 8.19 / 6.79 / **7.22** | ✗ **see "Zone price ladder"** |
| 3 | Transactions / households / yr | 2.5–3.6% | 3.57% | ✓ (top of band) |
| 4 | Completions vs formation | 40–70% | 58.6% | ✓ **now measured** |
| 5 | Market-tenant overburden (>40%) | 27–33% | 27.3% | ✓ (bottom of band) |
| 5b | Insider/outsider wedge > 0 | — | +10.4% | ✓ **now measured** |
| 6 | Vacancy (market basis, tensioned) | 3–10% (Censo urban 6–9 incl. 2nd homes) | 4.2% | ✓ |
| 6b | Rate shock: volume falls, prices sticky | 2023: sales −11%, prices +4% | vol −7.5%, price −1.9% | ✓ direction, magnitude qualified |
| 7 | Hold-out 2021–25 run-up | prices +8–13%/yr (asking), record volumes, rents up | +5–6%/yr (transaction basis), volumes +15%+, contract rents > 0 | ✓ qualified |
| — | Individuals' share of rental stock | 85–92% [investor-small §1] | 86.6% | ✓ **new cross-check** |
| — | Public rental share of rental stock | ≈8% (1.7% of total stock) | 6.8% | ✓ **new cross-check** |
| — | National supply elasticity (zone-weighted) | 0.45–0.58 | 0.49 | ✓ **new cross-check** |

Targets 3, 4 and 5 are now asserted on their **sourced** bands. The previous revision needed
a +0.6pp widening on target 3 and recorded target 4 as "✓ by construction" without measuring
it — both were artefacts of the developer start rule pinning starts against the capacity
ceiling (see "Audit corrections", D1).

## Zone price ladder — the one failing target

**Symptom.** The tensioned/rural price ratio decays from 3.18× at tick 1 to 1.89× at tick 60,
and rural price-to-income (7.2) overtakes the secondary city (6.8). Real Spain runs the other
way: metro-core €/m² is roughly 5–7× rural and the gap has widened.

**Cause.** Nothing in the model makes a location intrinsically worth more. Households bid
only in their own zone, so each zone's price is pinned by the credit ceiling of the households
living there. Relative prices therefore converge on relative *incomes*
(1.15 / 1.0 / 0.80 → T/R ≈ 1.44 asymptotically), not on a location premium. Two things make
this unavoidable in the current specification:

- construction capacity is below household formation in **every** zone by design
  (24 starts/tick vs 30 formations/tick nationally — this is the sourced Spanish deficit, BdE
  600–750k), so no zone can build its way out and every zone runs to its ceiling;
- the initial `price_multiplier` ladder (1.6 / 0.9 / 0.5) is an initial condition, not an
  equilibrium of the model's own mechanics, so the dynamics erode it.

**Not a parameter problem.** A per-zone land-availability gradient was added during the audit
(tensioned 0.25 / secondary 0.50 / rural 1.00, weighted mean 0.49, holding the sourced
national anchor) on the correct grounds that metro cores cannot answer a price rise with
supply. It moved T/R by 0.04. That measurement is the evidence that supply elasticity is
**not** what holds the ladder apart. The gradient is retained because it makes zone-targeted
supply policy (land release) behave differently by zone, which a uniform elasticity cannot.

**What would fix it** — a spatial-preference mechanism, which is a design decision, not a
recalibration. Candidates, cheapest first:
1. a location amenity term in willingness-to-pay (households pay a premium for the tensioned
   zone), calibrated to the observed €/m² gradient;
2. two-directional endogenous migration responding to price *and* wage differentials —
   currently migration is downward-only and rent-triggered;
3. explicit commuting/job-access geography, i.e. abandoning the 3-zone abstraction.

Tracked as a strict `xfail` in `tests/test_validation.py::test_price_to_income_ordering`, so
the suite reports the moment a mechanism fixes it. **Until it is fixed, no cross-zone
comparative claim from this model should be reported** — within-zone results and national
aggregates are unaffected.

## Honest qualifications

- **Index bases matter.** The price index is a quality-adjusted *transaction* index
  (IPV-like); its boom growth (+5–6%/yr) sits below the +12.7% (2025) IPV peak. The rent
  index agents see is an *asking* basis (idealista-like); the transacted median
  (`rent_transacted_*`, SERPAVI-like) runs slower, reproducing the real asking/contract
  wedge (household-tenant §7.4). Public rents are excluded from all rent indices — they are
  administered, not market signals.
- **Rate-shock magnitude.** Direction and ordering reproduce (volumes fall, prices fall
  less). Magnitude is measured on a 3-seed mean because the single-seed spread on this ratio
  is ±5pp — wider than the effect — and the previous single-seed version of that test was
  passing on luck. Prices come out −1.9% against 2023's +4.0%: the model carries no exogenous
  nominal drift, and the demand-side channel is the only one acting, because seller-side
  postponement is not modelled (household-owner §7.7 flags the split of moving triggers into
  forced vs opportunistic as unresolved). Expect the volume response to stay understated
  until that lands.
- **Rent growth is bounded by income growth.** In the hold-out boom the asking rent index
  grows ≈+0.7%/yr (5-seed mean) against a real +8–11%/yr. The cause is structural, not a
  parameter: tenants accept rent up to a hard share of income (`max_rent_burden` ~ U(0.30,
  0.40)), incomes grow at the exogenous 2%/yr anchor, and there is **no sharing or
  overcrowding margin** for demand to absorb more. Real Spain absorbed above-income rent
  growth through later home-leaving, more sharing and rising burdens. `SEEKER` exists as a
  "sharing meanwhile" state but plays no rent-absorbing role. Treat the model's boom-time
  rent response as a floor, and do not use it to size rent-inflation claims.
- **Tourist-restriction magnitude is conservative and noisy.** 5-seed means: rents −0.85%,
  prices −0.88%, against the dossier's implied −1.9% / −5.3% (Garcia-López et al. 2020
  reversed). Direction is right and the phase-out works (seasonal stock 183 → 15 units), but
  only `vut_conversion_share` = 0.30 of phased-out units return to the long-term market
  (sourced range .10–.50), and the per-seed spread is −6.0% to +3.2% — wider than the effect.
  Any claim from this lever needs a multi-seed mean.
- **Ownership and overburden both sit at the bottom of their bands**, price-to-income and
  transactions near the top. The model is internally consistent but leaves little headroom;
  a parameter sweep should treat these four as jointly constrained rather than independent.
- **`landlord_required_spread` was deliberately NOT re-fitted.** Overburden initially came out
  1.5pp below its band and the sensitivity screen names this spread as the dominant lever for
  it. But 0.02 is *directly observed* (tensioned-zone yield 4.7–5.6 against a ~3% bond), and
  the gap turned out to be a measurement-basis error, not a parameter error (D5 below).
  Bending an observed parameter to fix a mis-specified indicator would have hidden the bug.

## Sensitivity screen (OAT, seed 42 — screening only, ±2–3% ≈ noise floor)

⚠️ **Stale.** The table below was measured before the audit. The developer start rule, the
public-stock basis, the foreign-buyer stream and the rate pass-through all changed, and at
least the construction and rent rows must have moved. Re-run before citing. Retained only
because the qualitative headline (landlord spread dominates rent levels) is what motivated
leaving that spread alone above.

%Δ vs baseline on last-20-tick means:

| Variant | price_T | rent_T | overburden | transactions |
|---|---|---|---|---|
| momentum λ 0.5 / 0.9 | −1.5 / +2.2 | −0.2 / +2.2 | −7 / −5 | +1 / +3 |
| ask_decay .02 / .05 | +2.7 / +1.9 | +2.5 / +3.0 | −2 / −8 | ≈0 |
| landlord spread .015 / .03 | −2.4 / +0.9 | **−11.2 / +15.8** | **−12 / +2** | +2 / −3 |
| max DSTI .30 / .40 | +4.9 / +1.7 | +2.0 / +3.2 | −6 / −5 | −3 / +2 |
| formation 25 / 33 | +3.1 / +0.9 | +1.7 / +0.4 | −3 / −5 | −1 / −5 |
| foreign share .04 / .12 | +2.8 / +1.0 | +2.7 / +0.8 | −4 / −3 | +2 / ≈0 |

Reading (subject to the re-run): **the landlord required-yield spread is the dominant
disputed parameter for rent levels and burden** — exactly the parameter flagged `guess` in
investor-small §7.5. Follow-up research effort should go there first.

## Audit corrections (2026-08-10)

Defects found and fixed. Each was verified by measurement before and after, not by inspection.

**Correctness**

- **C1 — reproducibility violated.** Rent-subsidy eligibility used `hash((id, "bono"))`.
  Python salts string hashing per process, so the same seed produced different runs under
  different `PYTHONHASHSEED` (measured: 2% apart on the tensioned rent index). Replaced with
  a per-household draw from the engine's seeded Generator. Guarded by
  `test_reproducible_across_processes`, which runs two subprocesses with different hash seeds.
- **C2 — the demand-subsidy guarantee was completely inert.** The LTV boost was read from
  `CreditConfig.guarantee_ltv_boost`, which no intervention ever set (`DemandSubsidy` writes
  only `PolicyConfig`). `max_price` returned an identical limit with and without the aval, so
  the whole guarantee arm did nothing while still draining its budget. The duplicated field is
  gone; the boost is now an explicit `ltv_boost` argument. Guarded by
  `test_state_guarantee_reaches_the_lending_cap`.
- **C3 — the guarantee means test was bypassed downstream.** Eligibility was re-derived from
  `first_time` in clearing and screening, and every non-owner is first-time, so
  `guarantee_eligible_share` gated nothing past the household's own decision. The decision now
  travels on `MakeOffer.guaranteed`.
- **C4 — the guarantee budget refilled every tick.** The funding condition was
  `budget_left == 0.0`, which is exactly the state an exhausted budget is in, so the €2.5bn
  one-off ICO line re-funded itself indefinitely. Now a one-shot `guarantee_budget_funded`
  flag, with the envelope a named policy parameter.
- **C5 — non-resident demand throttled to 1 purchase/zone/tick.** The one-purchase-per-buyer
  rule was applied to the aggregate buyer ids too. The foreign overlay emitted 414 offers over
  60 ticks and won 59 — exactly the 1-per-tick ceiling — so foreign buyers were **1.1% of
  transactions against a sourced 8%** (Registradores/Notariado, high confidence). The rule now
  applies to households only.
- **C6 — dead stock, two kinds.** (a) New builds whose ask decayed below reserve were delisted
  and never touched again by any actor: permanently dead supply, measured at 71 units after 60
  ticks and growing with the horizon, silently muting the construction channel. Developers now
  re-price inventory each tick at a markdown that widens with holding time. (b) Public units
  that fell vacant were re-let by nobody, draining the parque social from 8% of rental stock to
  2.8% over the run; the Government actor now re-lets them.
- **C7 — orphaned estates.** Dissolution passed only the deceased's home to an heir, leaving
  any rental units owned by a household that no longer exists — 172 units (1.5% of stock) after
  60 ticks, still behaving as landlords. The whole estate now passes. The same block had
  `if hh.unit_id` guarding a listing cleanup, which is falsy for unit id 0, and never cleaned
  up rent listings.
- **C8 — rental asks decayed without floor or expiry.** Unmatched rent listings aged
  indefinitely (max observed 18 ticks, ask at 0.58× its start) and dragged the asking-basis
  rent index down. Now floored at the landlord's required yield (or the cap where one binds)
  and expiring on `max_listing_ticks`, after which the landlord re-prices.
- **C9 — the ITP lever was invisible in its own headline indicator.** `buyer_access` read
  `config.zone().itp_rate` instead of the effective `macro.itp`, so a transaction-tax
  intervention moved nothing in the UI's accessibility comparator.
- **C10 — latent double-booking.** A unit listed for both sale and rent could be sold and
  leased in the same tick (0 occurrences measured, but reachable via the investor's exit path).
  Sale now wins and clears the rent listing.

**Calibration and specification**

- **D1 — the developer's start rule was margin-driven, and the margin was meaningless.**
  Land was priced as a fixed share of the final price, which makes the implied margin rise
  without bound as prices rise: measured at 38% (tensioned), 59% (secondary), **103% (rural)**
  against a sourced 15–20%. Starts pinned against the capacity ceiling at ≈184k/yr real versus
  Spain's ≈110–130k, and completions ran at 75% of formation versus a sourced 40–70%. Land is
  now the residual claimant and volume follows a constant-elasticity rule on price-over-hard-cost
  (model-spec §6b). Starts fell to ≈128k/yr, completions to 58.6% of formation, and transaction
  volume dropped into its sourced band without needing the widened test.
- **D2 — rate pass-through was more than twice its cited speed.** `pass_through = 0.15`/tick
  implies ~48% of a euríbor shock passed through in 16 months; BdE DO 2312 says ~32%. Solving
  `1−(1−p)^5.33 = 0.32` gives 0.07. Corrected, and the participation rate-sensitivity refitted
  against target 6b alongside it (the two are jointly identified — the config comment says so).
- **D3 — public rental stock was undercounted ~4×.** `public_rental_share` is sourced as a
  share of **total** stock (318k of 18.54M dwellings = 1.7%) and was applied as a share of
  **rented** units. Fixed with an explicit basis conversion and metro-concentrated allocation;
  the value moved to the sourced 0.017. Public stock is now 6.8% of rental and individuals'
  share landed at 86.6%, inside the independent 85–92% source that previously read 94.4%.
- **D4 — the insider/outsider wedge was measured on the wrong basis.** Rent/income burden
  makes the wedge come out **negative** (−0.14 measured): rental matching is assortative, so
  entrants are selected on income and their burden ratio is lower even while they pay strictly
  more for the same flat. The wedge the mechanism produces is a price wedge; it is now measured
  on quality-adjusted rent levels (+10.4%).
- **D5 — the overburden indicator mixed administered and market rents.** The 27–33% target is
  the Eurostat *tenant, rent at market price* series, but the indicator averaged over all
  tenants including social ones paying half market rent. Once D3 raised public stock to a
  realistic size this understated overburden by ~1.6pp. Market and all-tenant versions are now
  reported separately.
- **D6 — single-seed stochastic assertions.** Two tests asserted effects smaller than their
  own single-seed noise band, so both were passing on the seed they were written with rather
  than on the model's behaviour. `test_rate_shock_cuts_transactions_before_prices` asserted a
  ~5% effect on a ±5pp spread (now a 3-seed mean). `test_holdout_2021_2025_runup` asserted
  three things whose per-seed ranges are price +3.9…+5.4%/yr, rent −1.1…+3.0%/yr and volume
  ratio 1.11…1.31 — all three straddling their thresholds (now a 5-seed mean).
- **D8 — one policy lever was structurally inert.** `initialise()` created no tourist-rental
  segment, and the only other route into `Tenure.SEASONAL` is rent-cap evasion, so
  `TouristRestriction` had nothing to phase out and read as an exact no-op — indistinguishable
  from a broken lever. A VUT segment now exists at init (`ZoneConfig.seasonal_share`,
  national ≈1.8% matching 329,764 units INE Nov 2025 against 18.54M dwellings; tensioned 2.8%
  from the central-Barcelona district figure), held outside `units_per_household`, which is
  documented as excluding second homes. Verified directionally correct after the change; see
  the qualification above.
- **D7 — dead and mislabelled parameters.** `DeveloperConfig.supply_elasticity` was documented
  as sourced and read by nothing (it now drives the start rule). `stock.DEVELOPER_ID` was
  defined and unused while the engine hard-coded `-6` for the same thing.
  `StockConfig.avg_size_m2` duplicated a module constant in `developer.py`.
  `small_landlord_share` and `vacancy_rate` were inputs for quantities the model produces
  emergently — both are now emergent cross-checks. Magic numbers extracted and sourced:
  crowding-out's undocumented `/3` (now per-zone), the seasonal-evasion rescaling denominator,
  and the participation/momentum coefficients.

**Not fixed, deliberately**

- The zone price ladder (above) — needs a mechanism, not a parameter.
- Seller-side postponement in a downturn. Would close the remaining rate-shock magnitude gap,
  but household-owner §7.7 flags the forced-vs-opportunistic split of moving triggers as
  unresolved, and the project standard requires ≥2 independent sources per behavioural rule.
  Inventing an elasticity here would have manufactured the result.

## Known gaps

- Zone price ladder compression (blocking for cross-zone claims — see above).
- Sensitivity screen needs re-running post-audit.
- Formal Morris screening + Sobol indices not yet run (light OAT only).
- Latin-hypercube moment fitting not needed yet — hand calibration hits the targets — but
  becomes necessary if targets tighten further. Four moments now sit at band edges.
- 2008-style bust reproduction untested end-to-end; a `CreditCrunch` intervention (tightening
  `max_ltv` / `max_dsti` / spread) is the natural next lever and would close §9.6's second half.
- Seller-side postponement (above).
