# Phase 6 — Calibration & validation report

Baseline = `SimConfig.baseline()`, 60 ticks, seeds {1..5}, last 20 ticks averaged.
Enforced continuously by `tests/test_validation.py` — no scenario result is reported unless
that suite passes (engineering standard, `plan.md`).

Revised 2026-09-08, second pass ("Tensioned-tightness revision" below): the rent-cap gate's
supply leg is met — metro-weighted formation, a shadow rent landlords compare the cap against,
hazard scale re-fitted; every §9 moment re-measured on 5 seeds.

Revised 2026-09-08 after the KB refresh (`docs/kb-refresh-2026-09.md`, section "KB refresh
2026-09 revision" below): baseline moments unchanged within seed noise, three new contrast
rows, and the Phase-7 rent-cap gate re-measured and found **not met on its supply leg**.

Revised 2026-08-14 after reading Funcas *Estudios* 104 (`docs/funcas-104.md`). Four mechanics
changed — vacancy geography, the non-mobilisable empty stock, dwelling size, and a sharing
margin in tenant behaviour — so every number below was re-measured on 5 seeds. What changed
and why is in "Funcas 104 revision"; the previous "Audit corrections" section is kept below it
for provenance.

## Direct calibration

Observable parameters set straight from Tier-1 data (see `config.py` field comments):
EFF2024 income/wealth distributions, ECV tenure shares by zone, BdE LTV/DSTI/term/pass-through,
Euroval construction lag, MIVAU output flow, idealista/BdE yield ladder, Registradores foreign
share, Housing Europe/MIVAU social-rental stock.

Free parameters (calibrated, labeled `guess`): buyer participation level and its two
sensitivities, overbid dispersion, ask decay, seeker wealth, tightness pressure, hazard
scale, inventory markdown, zone land-availability split, per-zone withheld share (its
gradient is sourced, its levels are not) and the search-burden escalation pace (0.02–0.06,
mechanism and ceiling sourced).

Added from Funcas *Estudios* 104 (2024): per-zone dwellings-per-household from the INE
Censo-2021 empty-dwelling ladder, 90 m² average dwelling size, and the INE household
projection as a scenario path. See "Funcas 104 revision" below.

Two parameters are now *derived* rather than fitted, which removes two degrees of freedom:
- the developer's start-volume coefficient — the rule is a constant-elasticity form, so
  `ZoneConfig.supply_elasticity` **is** the elasticity the model exhibits (model-spec §6b);
- the developer's reference price level, computed from `median_value × price_multiplier ×
  new_build_premium` instead of being a knob.

## Validation targets vs baseline (model-spec §9)

5-seed means, last 20 of 60 ticks.

| # | Target | Empirical range | Model | Pass |
|---|---|---|---|---|
| 1 | Ownership rate | 70–74% (EFF2024); 75.3–76.4% (MITMA/EPF, Funcas 104) | 70.1% | ✓ (bottom of every band) |
| 1b | Non-owner share (tenant + seeker ≈ ceded/sharing) | 24–31% | 29.9% (24.1 + 5.8) | ✓ |
| 2 | Price-to-income (disposable basis, BdE) | 7–8 | 7.58 | ✓ |
| 2b | Price *level* ranking T > S > R | — | holds | ✓ |
| 2c | Price-to-**income** ranking T > S > R | — | 8.03 / 6.82 / **7.40** | ✗ **see "Zone price ladder"** |
| 3 | Transactions / households / yr | 2.5–3.6% | 3.64% | ✓ (top of band) |
| 4 | Completions vs formation | 40–70% | 59.4% | ✓ |
| 5 | Market-tenant overburden (>40%) | 27–33% | 29.2% | ✓ (mid-band, was 27.3%) |
| 5b | Insider/outsider wedge > 0 | — | +10.2% | ✓ |
| 5c | Share of market tenants > 30% of income | reported, not gated (EPF 38.2% on a consumption basket) | 58.7% | reported — **see "Rent levels"** |
| 5d | Vacancy ranking R > S > T, with levels | R 15.6–24.6%, S 8.1–13.1%, national 10–15% (INE Censo by municipality size) | 18.2 / 12.3 / 10.0; national 12.6% | ✓ **new, was inverted** |
| 6 | Vacancy (market basis, tensioned) | 3–10% (Censo urban 6–9 incl. 2nd homes) | 4.3% | ✓ |
| 6b | Rate shock: volume falls, prices sticky | 2023: sales −11%, prices +4% | direction holds (magnitude qualified) | ✓ |
| 7 | Hold-out 2021–25: prices, volumes | prices +8–13%/yr (asking), record volumes | +4.3%/yr (transaction basis), volumes +22% | ✓ qualified |
| 7r | Hold-out 2021–25: **rents** | +8–11%/yr asking | **+0.0%/yr ± 0.3pp (20 seeds)** | ✗ **strict xfail — see "Rent growth"** |
| — | Individuals' share of rental stock | 85–92% [investor-small §1] | 86.4% | ✓ |
| — | Public rental share of rental stock | ≈8% (1.7% of total stock) | 7.3% | ✓ |
| — | National supply elasticity (zone-weighted) | 0.45–0.58 | 0.49 | ✓ |
| — | Zone dwellings/household weight to the national anchor | 1.12 ± 0.01 | 1.12 | ✓ **new invariant** |

Targets 3, 4 and 5 are asserted on their **sourced** bands. Two targets now fail and both are
strict xfails, so the suite reports the moment a mechanism fixes either: the zone price ladder
(2c) and the hold-out rent leg (7r).

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

## Funcas 104 revision (2026-08-14)

Source: Funcas, *Estudios* 104, *Mercado inmobiliario y política de la vivienda en España*
(2024). Full reading note, figure by figure, in `docs/funcas-104.md`. Four mechanics changed;
each was measured before and after.

**F1 — vacancy was spread evenly across zones, and the ladder came out backwards.** The model
had one national `units_per_household` = 1.07, which produced rural as the *least* vacant zone
(5.6% against 10.1% tensioned). The INE Censo-2021 ladder runs the other way and steeply:
24.6% of the local park empty in municipalities under 5,000 inhabitants against 6.3% in
Madrid, 13.2% nationally; half the empty stock sits in municipalities under 20,000
inhabitants holding 28% of the population; provinces growing slower than the 3.1% national
household rate hold >60% of it. `units_per_household` is now per zone (1.075 / 1.124 / 1.242,
weighting to a national 1.12) and the ladder inverts to 18.2 / 12.3 / 10.0% with a national
12.6%, all inside the source's bands. This matters beyond realism: the vacancy-tax lever acts
on stock the model was putting in the wrong places.

**F2 — recognising that stock must not hand it to the market.** With F1 alone, the extra rural
vacancy absorbed latent demand (seeker share 6.2% → 5.2%) — exactly the "umbrella" Funcas ch.1
argues does not exist, because the empty stock is where demand is not and much of it needs
substantial rehabilitation. `withheld_share` is now per zone (0.39 / 0.63 / 0.81) and
deliberately calibrated so the *mobilisable* stock, (upH − 1) × (1 − withheld), is unchanged
at 0.0455 per household in every zone. So the revision changes what the model counts, not what
its market can use. Pinned by `test_zone_stock_ratios_hold_their_anchors`; the gradient is
sourced, the levels are not, and they are labelled accordingly.

**F3 — dwelling size 80 → 90 m².** 80 was a `guess`; 90 m² is Afi's national average (ch.5).
It is the developer's build size, so hard cost per dwelling rises 12.5%. Measured effect is
small but one-directional and worth stating: rural new build is priced at 0.5 × 170,000 over
90 m² = 944 €/m², **below** the sourced hard-cost floor of 1,080 €/m², so the rural zone only
builds after prices have risen ≈15%. That is realistic (little new build happens in cheap
rural Spain) and it tightens the zone price ladder further: T/R went 1.85× → 1.80×.

**F4 — a sharing margin in tenant behaviour.** The accepted rent burden was a fixed draw,
U(0.30, 0.40), for the whole run. Spain's is not fixed: mean rent effort rose 26.5% (2015) →
31.7% (2021) → 29.7% (2022) of the consumption basket, the share above the 30% line 33.0% →
43.1% → 38.2% (EPF, ch.6), 4 in 10 tenants exceed 40% of disposable income (Eurostat, ch.2),
and the absorption channel is named explicitly — shared flats, sublet rooms, later
emancipation (ch.4). A SEEKER's threshold now escalates with its search spell (+4%/tick,
ceiling 0.55, reset on being housed). Measured: market-tenant overburden 27.4% → 29.2%, i.e.
off the bottom of its band and into the middle; rent level +2%; latent demand slightly lower.
It does **not** fix boom-time rent growth — see below.

**F5 — a queue auction was tried and removed.** Letting excess rental demand clear above the
posted ask (rent = min(willingness, ask × (1 + g·ln(applicants/listing)))) measured ≈0 at
every gain tried. The reason is structural and is now written into `clearing.py` and
`model-spec` §5: assortative matching already puts each applicant on a listing at the top of
what they can afford, so there is no headroom to bid up. Kept out of the code — an inert
mechanism is worse than none (the audit's D8 lesson).

**F6 — the hold-out rent target was passing on luck, and now fails honestly.** The old test
asserted `mean rent growth > 0` on 5 seeds and got +0.39%. Two independent perturbations (F1,
F3) flipped it negative, which is the signature of an assertion inside its own noise band. Re-
measured on 20 seeds: **+0.0%/yr ± 0.3pp**, with only 8 of 20 seeds positive at any escalation
setting. It is now a separate strict xfail asserting the *real* target (+4%/yr, half the low
end of the sourced +8–11%), so the suite reports the moment a mechanism fixes it, and the
price and volume legs stay as ordinary passing assertions.

**F7 — three new diagnostics that expose gaps rather than close them.** Reported in
`benchmarks.py`, not gated:

| Row | Official | Model | Reading |
|---|---|---|---|
| Cash (unmortgaged) purchases | 60.8% (INE 2023); 30–40% assumed in the dossiers | **3.2%** | The model finances nearly every purchase. Credit policy bites harder here than in Spain. |
| Average rent paid | €516/month (EPF 2022) | **≈€1,350** | Basis differs (asking, whole 90 m² dwelling vs all sitting contracts of every size) but not by this much: there is no small-dwelling or shared-flat segment. |
| Latent demand | 1.6M potential households (Ezquiaga) | 1.27M | Same order; bases are asymmetric (Spain's 18.9M households excludes them, the model's count includes them). |

Not attempted: the second-home/other-province purchase stream (≈10% of Spanish transactions),
age and nationality structure in tenure, landlord income taxation, and utilities. All are
listed in `model-spec` §10 with their figures.

## Tensioned-tightness revision (2026-09-08)

Follow-up to R3 of the KB refresh below: the Phase-7 rent-cap gate was not met on its supply
leg because landlord withdrawals under a cap did not reduce the number of contracts. This
revision fixes it. It took a calibration change *and* a mechanism, and two rejected mechanism
variants are recorded because their failure modes are part of the specification (model-spec
§5, "The shadow rent").

**T1 — the tensioned rental market was slack, and formation is where it should be.** Applicants
per listing in the tensioned zone ran at 0.5 before a cap. Spanish household growth is
metro-concentrated — Madrid and Barcelona provinces alone added ≈27% of the national household
growth in the twelve months to Sep 2025 (EC Country Report 2026, INE ECP) — while the model
landed new households in proportion to the existing population (0.45 / 0.35 / 0.20). New
field `PopulationConfig.formation_zone_weights`, screened at 0.45 / 0.50 / 0.55 / 0.60 / 0.65 on
3 seeds: tightness 0.52 / 0.65 / 0.97 / 1.01 / 1.29. **0.55 / 0.286 / 0.164** chosen — the
lowest weight at which the queue runs at ≈1 applicant per listing. At 0.60 the counterfactual
rent path steepens so much that a cap measures −13% against it, outside every study. Level is
a guess; direction is sourced.

**T2 — tightness alone did nothing, because the cap blinds the landlord.** With the market
tight and the old exit rule, tenancies at elasticity 2 still moved +2.7%. Instrumented (seed 1,
formation weight 0.60): exits 13 → 4 → 0 within four ticks of activation, because the asking
index — every posted ask clipped — collapsed onto the cap, so `ln(ask / cap)` went to zero
while the same-seed baseline rent kept climbing (1,181 → 1,575 over the window). The landlord
had no view of the uncapped market. This is the actual reason the gate failed; slack only
hid it.

**T3 — the shadow rent, and the two versions that failed.** `ZoneState.shadow_rent` is what a
standard unit would fetch with no cap: the asking index in a free market; under a cap, an
anchored demand-side measure. Three anchors were built and measured on the same seed:

| Anchor for the shadow under a cap | Outcome at elasticity 2, formation weight 0.60, seed 1 | Verdict |
|---|---|---|
| Marginal applicant quantile 1 − listings/applicants (queue-implied clearing rent) | Tightness 1.6 → 38, shadow 1,181 → 3,756, contracts 61 → 9 per tick: every withdrawal raises the marginal quantile, which widens the gap, which drives more withdrawals | rejected — runaway |
| Median willingness of this tick's applicants | Exits 13 → 19 → 9 → 1 → 0 by tick 30: cheaper rents pull lower-income sitting tenants into the queue and the median falls below the reference | rejected — composition |
| **Median paying capacity (accepted burden × income) over all non-owners in the zone**, ratio to the index fixed at activation, smoothed at 0.3 | Shadow 1,181 → 1,233 (+4.4% over five years, tracking incomes and the sharing margin); reference 1,116 → 1,203 (IRAV); gap 5.5% → 2.5%; exits 13 / 8 / 11 / 11 / 7 / 5 / 1 / 3 / 5 / 10 / 4 per two ticks; rented stock 1,452 → 1,313 (−10%), contracts 62 → 50 (−19%), seasonal +38 | **kept** |

The exit hazard now reads the shadow-based fundamental ask (`ln(fundamental / cap)`), never
the posted ask and never the congestion-inflated ask — comparing to the latter turned exits
into a spiral in the first screen (tenancies −50 to −87%). The large investor's "cap binds"
test reads the same shadow. In a free market the shadow equals the index, so the baseline is
untouched by construction.

**T4 — hazard scale re-fitted.** `HAZARD_SCALE` exists to map the per-listing hazard onto the
studies' annual contract elasticity, and its 1.75 was fitted before the August audit on a
baseline that no longer exists. Sweep at the new defaults (3 seeds, cap at tick 20 of 40,
16 post-cap ticks; contracts σ ≈ 5–8pp):

| `HAZARD_SCALE` | ε=0 rents / contracts | ε=1 rents / contracts | ε=2 rents / contracts | seasonal at ε=2 |
|---|---|---|---|---|
| 1.75 | −5.6% / +2.1% | −4.9% / −2.5% | −4.8% / −5.0% | +20 |
| 2.5 | −5.6% / +2.1% | −3.8% / −4.6% | −3.9% / −7.4% | +20 |
| **3.0** | −5.6% / +2.1% | −4.9% / −2.1% | **−4.6% / −12.6%** | +27 |

3.0 chosen: elasticity 0 is Jofre-Monseny's world (rents −4…−6%, contracts ≈0), elasticity 2
reaches Monràs & García-Montalvo's −10% and approaches Pérez García's −13%, all inside the
0–2 dial, with rents −4.6…−5.6% throughout — the studies' −4…−6%. The five-seed table for the
experiment note is in T6.

**T5 — baseline moments after the revision** (5 seeds, last 20 of 60 ticks; previous value in
brackets). Ownership **70.0%** (70.2), non-owners 30.0% (29.8), price-to-income 7.70 (7.68; σ
0.28), transactions 3.6%/yr of households (3.6), completions/formation 57% (59), market-tenant
overburden 29.5% (28.7), >30% share 58.9% (59.2), insider/outsider wedge +8.6% (+11.9),
vacancy 8.7 / 12.5 / 17.8% by zone (10.0 / 12.3 / 18.0), national 12.0% (12.6), **market
vacancy tensioned 2.9%** (4.3), individuals' rental share 86.3% (86.5), public 7.2% (7.3),
seeker share 5.4% (5.8), T/R price ratio 3.20 → 1.80 (3.19 → 1.75). Every §9 gate holds. Two
things moved on purpose and are recorded as such: tensioned market vacancy fell from 4.3% to
2.9%, which is the tightness the revision set out to create (the `test_vacancy` floor moved
from 3% to 2%; it was a convention, not a sourced band — investor-small §7.3 says no source
separates frictional from total vacancy); and ownership sits at 69.98%, a hair under the 70%
edge of the EFF band, so the contrast row now reads "below" by 0.02pp. Buyer-type wedges
re-measured: a +0.90 non-resident surcharge cuts non-resident purchases 58% (3.3% → 1.4% of
sales); the +0.10 investor surcharge is inside seed noise on the institutional share (0.98% →
1.13%, σ 0.17pp) and its price effect (tensioned −0.9%) is what remains — the institutional
buyer is too small a share of the model's sales for the row to resolve it.

Both strict xfails from before stand (zone price ladder; boom-time rent growth — re-checked
under the new defaults, still fails, no XPASS). `test_rent_cap_supply_response_spans_monras`
is now an ordinary passing test.

**T6 — the Phase-7 sweep, re-run** (5 seeds, cap at tick 20 of 40 in the tensioned zone, mean
over the 16 post-cap ticks against the same-seed baseline; ± is the seed standard deviation):

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | seasonal units gained | Δ sale prices | Δ contract rents, secondary zone |
|---|---|---|---|---|---|---|
| 0.0 | −4.6% ± 2.4 | −4.2% | **+1.6% ± 2.3** | 0 | −3.0% | +0.1% |
| 0.5 | −4.4% ± 2.4 | −4.0% | −0.8% ± 4.9 | +11 | −3.1% | 0.0% |
| 1.0 | −4.1% ± 2.4 | −3.8% | −2.6% ± 2.8 | +17 | −4.1% | +0.6% |
| 1.5 | −3.2% ± 2.5 | −3.3% | −6.5% ± 4.8 | +21 | −4.7% | +1.1% |
| 2.0 | −3.6% ± 2.6 | −3.5% | **−11.6% ± 6.7** | +25 | −5.0% | **+1.7% ± 0.5** |

Credibility test (§9.8): Jofre-Monseny at elasticity 0 (rents −4…−5%, contracts unchanged),
Monràs & García-Montalvo at elasticity 2 (rents −5%, contracts −10%), Pérez García's −13% just
past the dial's end (≈2.2). Rents fall 3–5% at every elasticity; the price effect grows with
withdrawals (units sold to owner-occupiers, sale prices −3 → −5%); the secondary zone's contract
rents rise +1.7% at elasticity 2 — a small version of the spillover Spain shows (Catalan tensioned
+1.6% vs non-tensioned +9.4%), produced here only through priced-out seekers migrating down the
ladder. **The gate is met.** Ownership rises +0.5pp under every cap (withdrawals sold to
tenants). Tightness in the capped zone rises from 1.1 to 1.3 (ε=0) → 1.8 (ε=2).

**T7 — partial coverage is not reportable on the pooled rent.** With `coverage` 0.42 (Spain's
317 declared municipalities mapped onto the model's tensioned zone) the *pooled* new-contract
rent comes out **+7.7% ± 12.5** (ε=1) and **+18% ± 17** (ε=2) against baseline, while contracts
fall −10% / −26%. The covered 42% of units are capped and part of them withdraw; the uncovered
58% share the same queue, see the tightness the withdrawals create (1.1 → 1.7–2.3) and raise
their asks through the congestion premium, and the median of new contracts shifts toward
them. The direction is the Incasòl spillover — non-declared neighbours' rents rise — but the
magnitude is unstable across seeds because it is a composition effect on one pooled median. The
metrics do not yet split new contracts into capped and uncapped; until they do, coverage < 1 is
a mechanism demonstration, not a result, and the UI slider says so. (The earlier R4 figure,
−1.4% at coverage 0.42, was measured with the old hazard and the blind exit rule and is
superseded.)

## KB refresh 2026-09 revision (2026-09-08)

Source: the Jul–Sep 2026 release cycle, catalogued in `docs/kb-refresh-2026-09.md`. Six
mechanics or parameters changed (INE projection vintages, rent-cap coverage, buyer-type ITP
wedges, ICO wealth cap, IRAV read relative to the income anchor, the capped-listing floor) and
one calibration anchor moved (tourist stock 374k → 345k real). Every number below was
re-measured on 5 seeds, last 20 of 60 ticks, with the same script design as the Funcas revision.

**R1 — the baseline moments did not move beyond seed noise.** Ownership 70.2% (was 70.1),
non-owners 29.8% (29.9), price-to-income 7.68 (7.58, σ across seeds 0.10), transactions
3.6%/yr of households (3.64), completions/formation 58.8% (59.4), market-tenant overburden
28.7% (29.2), >30% share 59.2% (58.7), insider/outsider wedge +11.9% (+10.2, σ 2.5pp), vacancy
10.0 / 12.3 / 18.0% by zone (10.0 / 12.3 / 18.2), national 12.6% (12.6), market vacancy
tensioned 4.3% (4.3), individuals' rental share 86.5% (86.4), public 7.3% (7.3), zone-weighted
supply elasticity 0.49, T/R price ratio 3.19 → 1.75 over 60 ticks (3.18 → 1.89). None of the
default values of the new policy fields is active in the baseline (coverage 1.0, surcharges 0,
wealth cap ∞), so the only baseline perturbation is the tourist-stock anchor, which changes the
random stream and nothing structural. The §9 table above stands; both strict xfails stand.

**R2 — new contrast rows.** Non-resident purchases 2.2% of the model's sales against 7.9%
published (CaixaBank Research on MIVAU) — the overlay is calibrated as an *offer* stream
(`foreign_purchase_share` 8% of recent sales) and only ≈28% of those offers close, because a
+60% budget still loses sealed bids on the listings it lands on and the one-listing-per-offer
search is frictional. Legal-person purchases 0.5% against ≈10% (BdE) — expected far below,
the model's institutional buyer is only the gran tenedor. Cash purchases 2.9% against a
re-based 29.3% (Registradores 12-month 2025; band 23–46% to the Notariado reading) — the gap
is now stated at its honest size, ×10 rather than ×20. Formation 243k inside the widened
225–250k band.

**R3 — the rent-cap gate, re-measured, is not met on its supply leg.** The Phase-7 design
(`experiments/rent-cap.md`: cap from tick 20 of 40, tensioned zone, seeds 1–3, mean over the 16
post-cap ticks) re-run on the code *before* this revision gave contract rents **+0.9% above
baseline** at every elasticity and new tenancies **+2 to +3%**, against the table's −4.1% and
−9.4%. The table predates the 2026-08-10 audit and the 2026-08-14 Funcas revision and was not
re-run after either. Diagnosis, seed 1, elasticity 2: the reference index, frozen at activation
and indexed by `within_contract_update` = 2.5%/yr, overtook a market growing at the 2%/yr
anchor; capped tensioned listings went 7 → 29 → 21 → 14 → 6 → **0** between ticks 20 and 30,
after which the magnet rule (sub-cap asks rise toward the reference) *lifted* asks. In Spain
IRAV (2.20–2.44%) runs at 0.6–0.75 of nominal wage growth, so the model value is 0.012–0.015;
at **0.015** the cap binds throughout. Re-measured after the fix:

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | seasonal units gained | Δ sale prices | Δ contract rents, secondary zone |
|---|---|---|---|---|---|---|
| 0.0 | **−2.2%** | −1.8% | +3.6% | 0 | −2.8% | −0.3% |
| 0.5 | −2.2% | −1.8% | +2.6% | +1.8 | −3.4% | −0.7% |
| 1.0 | −2.2% | −1.8% | +3.6% | +4.6 | −3.0% | −0.1% |
| 1.5 | −2.2% | −1.8% | +4.0% | +5.6 | −3.3% | +0.3% |
| 2.0 | −2.2% | −1.9% | **+3.8%** | +7.5 | −3.5% | 0.0% |

The price leg works and is now pinned (`test_rent_cap_lowers_contract_rents`, −1% floor). The
supply leg does not: at elasticity 2 tenancies *rise*. Instrumented (seed 1): every vacant
candidate's ask exceeds the cap (the yield floor sits ≈2% above market rent), 85% comply, and
the per-listing exit hazard is 0.06–0.17 — ≈60 withdrawals over the 16 ticks, half of them
sold to owner-occupiers. But **applicants per listing in the tensioned zone are 0.64–0.77
before the cap and 1.1–1.5 under it**: there are 60–80 leftover listings every tick, so
withdrawing 60 units over four years shrinks the slack, not the number of contracts. Barcelona
runs at ≈65 contacts per listing (idealista, Mar 2026). This is a calibration fact about the
baseline, not about the hazard: no `HAZARD_SCALE` reproduces Monràs's −10% in a slack market.
Strict xfail `test_rent_cap_supply_response_spans_monras` (elasticity 2 must give ≤ −5%). The
fix — a tightness recalibration of the tensioned zone via the mobilisable vacant stock,
currently held at 0.0455 per household in every zone by the Funcas revision's F2, or via the
zone split of household formation — moves ownership, market vacancy and overburden together
and is the next measured revision. **Until then no rent-cap supply-response claim, and no
elasticity sweep, should be reported from this model.** The sale-price and secondary-zone
columns are reported for completeness; the cross-zone spillover Spain shows (Catalan tensioned
rents +1.6% vs non-tensioned +9.4% in 2025, Incasòl) is absent, as expected from zones that are
not adjacent markets.

**R4 — coverage.** Same design, elasticity 1: coverage 1.0 gives contract rents −2.2%,
coverage 0.42 (Spain's 317 declared municipalities mapped onto the model's tensioned zone)
−1.4%, i.e. ≈0.64 of the full effect for 0.42 of the units, because the asking-basis index that
uncapped landlords condition on also falls. Coverage 0 leaves only the national IRAV channel
on sitting rents (−1.0% over 3 seeds, σ 1pp, indistinguishable from zero), pinned at under half
the full effect by `test_cap_coverage_scales_the_rent_cap`.

**R5 — buyer-type tax wedges.** Cap from tick 8 of 40, seeds 1–3, mean over ticks 16–40:

| Lever | Non-resident share of sales | Institutional share of sales | Transactions | Tensioned prices |
|---|---|---|---|---|
| baseline | 3.3% | 0.80% | — | — |
| non-resident surcharge +0.90 (the 100%-tax bill) | **1.6% (−51%)** | 1.5% | +2.3% | **−5.2%** |
| non-resident surcharge +0.20 | 3.2% (−3%) | 1.3% | +3.0% | −1.9% |
| investor surcharge +0.10 (Catalan 20% TPO) | 3.6% | **0.68% (−15%)** | +1.5% | −1.1% |

The +0.90 surcharge halves rather than eliminates non-resident purchases: the overlay bids at
+60% and, after the wedge `(1.10)/(2.00) = 0.55`, still reaches 0.7–1.06× the zone price and
wins the listings whose reserve sits below that. In Spain the non-resident premium is largely
*composition* (coastal, premium stock: €3,063 vs €1,713/m²), which the model represents as
willingness-to-pay on the same stock — so it likely understates the diversion. The
institutional buyer picks up part of what non-residents drop (0.8 → 1.5%). Transactions
*rise* slightly under both surcharges because the aggregates' lost purchases free listings for
credit-screened households at lower prices — a redistribution the lever is designed to produce.

**R6 — ICO wealth cap.** Guarantee with eligible share 0.5, cap €150k vs none, 24 ticks,
seeds 1–3: identical budget exhaustion (100% of the envelope spent) and unassisted access 18.61%
vs 18.62%. Inert on the model's tenant wealth distribution (≈1% of tenants above €150k), as the
instrument's own design implies; kept because it is the instrument.

**R7 — tourist stock.** Seasonal units 172 (≈344k real) against INE's 341,001 (May 2026); was
187 (≈374k). The tourist-restriction lever's magnitude scales with it.

Not attempted: the tensioned-zone tightness recalibration (R3), the location-amenity term, the
declaration exit rule, the contract-extension shock and the seasonal return flow — listed with
their evidence in `docs/kb-refresh-2026-09.md` §8 and `model-spec` §10.

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
- **Rent growth is bounded by income growth** (target 7r, now a strict xfail). The clearing
  rent equals the winning applicant's willingness to pay, which is a share of income, and
  income grows at the exogenous 2%/yr anchor. Measured over 20 seeds the hold-out boom
  response is +0.0%/yr ± 0.3pp against a real +8–11%/yr. The sharing margin added in this
  revision (F4) raises the accepted *level* — overburden 27.4% → 29.2% — but cannot change the
  growth rate, and a queue auction on top of the ask measured ≈0 because matching is already
  assortative (F5). **Do not use this model to size any rent-inflation claim.**
- **Rent levels are not comparable to published Spanish figures; changes in them are.** Every
  model tenant rents one whole 90 m² dwelling at asking level, so the national rent index
  (≈€1,350/month) sits ≈2.6× the EPF average rent actually paid (€516 in 2022), and the share
  of market tenants above 30% of income reads 58.7% against EPF's 38.2% of the consumption
  basket. Spain's renters use a margin the model does not have: a young median earner there
  crosses one third of income at 30 m² and half at 45 m² (Funcas 104 ch.5). The >40% market
  overburden target survives this because it was calibrated on the same basis; the absolute
  rent and >30% rows were not, and are reported as diagnostics.
- **Tourist-restriction magnitude is conservative and noisy.** 5-seed means: rents −0.85%,
  prices −0.88%, against the dossier's implied −1.9% / −5.3% (Garcia-López et al. 2020
  reversed). Direction is right and the phase-out works (seasonal stock 183 → 15 units), but
  only `vut_conversion_share` = 0.30 of phased-out units return to the long-term market
  (sourced range .10–.50), and the per-seed spread is −6.0% to +3.2% — wider than the effect.
  Any claim from this lever needs a multi-seed mean.
- **Ownership sits at the bottom of its band**, price-to-income and transactions near the
  top; overburden moved to mid-band with the sharing margin. Funcas 104 widens the ownership
  question rather than settling it: EPF 2022 says 76.4% of households own, MITMA 75.3% of the
  park, EFF 70–74%. On all three bases the model's 70.1% is the low end. The four moments are
  jointly constrained — a parameter sweep should not treat them as independent.
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

- Boom-time rent growth (target 7r) — structural, see F4–F6 above and `model-spec` §10.
- Rent level and cash-purchase share, both exposed by the Funcas 104 contrast rows (F7).
- No second-home/other-province demand stream, no age or nationality structure in tenure, no
  landlord income taxation, no utilities — figures and consequences in `docs/funcas-104.md` §4.
- Zone price ladder compression (blocking for cross-zone claims — see above). Calibration
  evidence for the location-amenity fix now exists (Funcas 104 ch.5: Madrid/Barcelona wages
  +45%, cost of living +20%, net +21%); the mechanism decision does not.
- Sensitivity screen needs re-running post-audit.
- Formal Morris screening + Sobol indices not yet run (light OAT only).
- Latin-hypercube moment fitting not needed yet — hand calibration hits the targets — but
  becomes necessary if targets tighten further. Four moments now sit at band edges.
- 2008-style bust reproduction untested end-to-end; a `CreditCrunch` intervention (tightening
  `max_ltv` / `max_dsti` / spread) is the natural next lever and would close §9.6's second half.
- Seller-side postponement (above).
