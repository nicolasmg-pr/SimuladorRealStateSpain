# Phase 6 — Calibration & validation report

Baseline = `SimConfig.baseline()`, 60 ticks, seeds {1..5}, last 20 ticks averaged.
Enforced continuously by `tests/test_validation.py` — no scenario result is reported unless
that suite passes (engineering standard, `plan.md`).

Revised 2026-09-08, fourth pass ("Shadow-anchor and boom-rent revision" below): the shadow
rent's anchor is now exogenous, the hazard scale is re-fitted so all three rent-cap studies
sit inside the 0–2 dial, and boom-time rent growth passes. **The suite carried no xfails at that point**; phase C (14 Sep 2026) adds two, both dated
and both naming the mechanism that has to close them — see "Phase C" below.

Revised 2026-09-08, third pass ("Location-premium revision" below): the zone price ladder
holds and the price-to-income ordering is restored, closing the model's oldest known gap.

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

5-seed means, last 20 of 60 ticks. **Current as of the 2026-09-08 fourth pass — every target in
*this* table passes.** The suite does carry three strict xfails; they belong to the phase-0
targets below (9, 11, 12), added 2026-09-11. The revision sections below are dated records of how
each one was reached; where their numbers differ from this table, this table is the live one.

| # | Target | Empirical range | Model | Pass |
|---|---|---|---|---|
| 1 | Ownership rate | 70–74% (EFF2024); 75.3–76.4% (MITMA/EPF, Funcas 104) | 69.3% | ✓ gate (69–75), but **below the EFF band** — see "Honest qualifications" |
| 1b | Non-owner share (tenant + seeker ≈ ceded/sharing) | 24–31% | 30.8% (25.2 + 5.6) | ✓ |
| 1c | Tenant share ranking T > S > R | strict; renting is a metro tenure [model-spec §7: T 0.27–0.30 / S ≈0.20 / R 0.12–0.17] | **31.4 / 22.7 / 17.0%** (3 seeds), ranking holds on each seed | ✓ **ranking gated; levels are not** — the tensioned leg runs above its band, same zone-aggregation qualification as 2d. Was an unmeasured stub until 2026-09-12 |
| 2 | Price-to-income (disposable basis, BdE) | 7–8 | 7.15 | ✓ |
| 2b | Price *level* ranking T > S > R | — | holds | ✓ |
| 2c | Price-to-**income** ranking T > S > R | — | **8.35 / 6.24 / 4.78** | ✓ **fixed by the location premium (§5b); was inverted** |
| 2d | T/R price ratio at tick 60 (initial 3.21) | Spanish provincial extremes 3.5–4.5 | 2.95 | ✓ holds; was decaying to 1.90 |
| 3 | Transactions / households / yr | 2.5–3.6% | 3.43% | ✓ |
| 4 | Completions vs formation | 40–70% | 51.1% | ✓ |
| 5 | Market-tenant overburden (>40%) | 26.8–33% (Eurostat 2025–2023) | 28.2% | ✓ |
| 5b | Insider/outsider wedge > 0 | — | +12.0% | ✓ |
| 5c | Share of market tenants > 30% of income | reported, not gated (EPF 38.2% on a consumption basket) | 56.4% | reported — **see "Rent levels"** |
| 5d | Vacancy ranking R > S > T, with levels | R 15.6–24.6%, S 8.1–13.1%, national 10–15% | 18.1 / 11.8 / 8.7; national 11.8% | ✓ |
| 6 | Vacancy (market basis, tensioned) | 2–10% | 3.1% | ✓ (the tightness revision moved this down on purpose) |
| 6b | Rate shock: volume falls, prices sticky | 2023: sales −11%, prices +4% | direction holds (magnitude qualified) | ✓ |
| 7 | Hold-out 2021–25: prices, volumes | prices +8–13%/yr (asking), record volumes | +4.4%/yr (transaction basis), volumes ×1.42 | ✓ qualified |
| 7r | Hold-out 2021–25: **rents** | +8–11%/yr asking | **+3.6%/yr ± 0.8 (10 seeds, all positive)** | ✓ **passes; ≈40% of the sourced magnitude — direction only** |
| 8 | Rent-cap credibility (Phase-7 gate) | span Jofre-Monseny / Monràs / Pérez García | ε=0 → −3.8% rents, +3.6% contracts; ε=1 → −3.7%, −1.0%; ε=2 → −3.8%, **−1.6%** | ✗ **supply leg: two strict xfails**; rent leg now just below the studies' −4…−6% — see "Phase-A hazard-floor revision" and "finding-4 correction" |
| — | Individuals' share of rental stock | 85–92% [investor-small §1] | 86.0% | ✓ |
| — | Public rental share of rental stock | ≈8% (1.7% of total stock) | 6.8% | ✓ qualified |

Targets 3, 4 and 5 are asserted on their **sourced** bands. **No target in this table is an xfail.** Two were
until 2026-09-08: the zone price ladder (2c), fixed by the location premium, and the hold-out
rent leg (7r), fixed by the tightness recalibration without touching the rent mechanism. What
remains is not a failing target but two *qualified* ones — 7r reaches only ≈40% of the observed
magnitude, and 1 sits below the EFF ownership band — both carried in "Honest qualifications"
and `model-spec` §10.

## Phase-A hazard-floor revision (2026-09-12)

Phase A removed the additive hazard floor in `agents/landlord.decide` (spec §2, finding 9).
The withdrawal margin used to read `gap = log(ask/cap) + 5 × growth_wedge`, and because the
wedge is built from two exogenous constants, a cap binding by one euro produced the same
`5 × wedge` term as a cap binding by a third of the rent. The exit hazard jumped from zero to
a fixed positive floor the instant the cap touched the ask and stayed there however mild the
cap was. The wedge now **scales** the level gap instead of being added to it, which makes the
hazard continuous at the point the cap starts to bind: a cap that costs nothing produces no
withdrawals, however long the unit is held.

Measured effect on the Phase-7 dial (3 seeds, cap from tick 20 of 40, 16 post-cap ticks):

| ε | rents, before | rents, after | contracts, before | contracts, after |
|---|---|---|---|---|
| 0 | −4.9% | −4.9% | −0.7% | −0.7% |
| 1 | −4.4% | −5.2% | −4.8% | −1.4% |
| 2 | −4.4% | −4.4% | −13.6% / −14.0% | **−7.3%** |

ε=0 is identical, as it must be — `p_exit` is multiplied by the elasticity, so at zero the
hazard change cannot reach the result. That the two ends move differently is the signature of
a hazard change and not of seed noise.

**What this costs, stated plainly.** The supply leg no longer spans the studies: at the top of
the 0–2 dial the model gives −7.3% contracts against Monràs & García-Montalvo's −10% and Pérez
García's −13%. Target 8's supply leg is therefore split in two — a weak form that still passes
(`test_rent_cap_supply_response_is_negative_at_the_top_of_the_dial`) and a strong form carried
as a dated strict xfail (`test_rent_cap_supply_response_reaches_monras`).

`hazard_scale` was **not** re-fitted to recover the old number. The −13.6% was produced by a
floor built out of two exogenous constants; re-fitting a scale factor to reproduce a result a
defect was generating is the move this project's standard exists to forbid. Phase B re-derives
the withdrawal margin from the arbitrage condition (spec §7.2) and the dial is re-derived
there, not re-tuned here.

## Phase-A finding-6 correction: the user-cost term is not dead (2026-09-12)

The redesign spec registered finding 6 as *"`own_vs_rent` user-cost channel is inert (clipped
to 1.0 below a ~6.2% mortgage rate) while its comment claims it carries the rate shock"*, and
phase A was to delete it. **The first half of that finding is wrong.** Instrumented on 3 seeds
× 40 ticks, recording every value the model computes:

| Scenario | below 1.0 | min | mean |
|---|---|---|---|
| baseline | **5.78%** of decisions | 0.858 | 0.9951 |
| `RateShock` | **3.23%** of decisions | 0.858 | 0.9978 |

It is active, the 0.5 floor has never bound, and removing it moves the baseline price level by
−1.5% (196,233 → 193,321 €, 3 seeds, tail of 40 ticks) and transactions by +2.2%.

The second half of the finding stands, and is worse than registered: the term engages **less**
under a rate shock than at baseline — the opposite of a rate channel. `gross_yield` dominates
the ratio, and the shock lifts the yield (prices −10%, rents +22%), so the ratio clips to 1.0
more often, not less. A term documented as carrying the rate shock moves against it.

**Action taken:** the term is kept at its measured behaviour and its comment corrected to the
measurement; it is registered in `docs/assumptions.md` as an unsourced reduced form with its
falsifier. It is **not** deleted. Deleting an active channel is a modelling decision, phase A is
bug fixes, and the decision belongs to phase D, where tenure choice is specified as a mechanism
rather than as a clipped multiplier on a credit limit. The rate-shock claim now sits on
`participation`, which is where it is true.

## Phase-A effect on the rent-cap dial, end to end (2026-09-12)

Two bug fixes compounded on target 8's supply leg. Measured the same way each time (3 seeds,
cap from tick 20 of 40, mean over the 16 post-cap ticks):

| ε | before phase A | after the hazard floor went (A3) | after inheritance was rewritten (A1) |
|---|---|---|---|
| 0 | −4.9% rents, −0.7% contracts | −4.9%, −0.7% | −3.8%, **+3.6%** |
| 1 | −4.4%, −4.8% | −5.2%, −1.4% | −3.7%, −1.0% |
| 2 | −4.4%, −13.6% | −4.4%, −7.3% | −3.8%, **−1.6%** |

The two fixes act through different channels, and the ε=0 column proves it. A3 changed the
exit *hazard*, and at ε=0 the hazard is multiplied by zero — so A3 could not and did not move
that row. A1 moved it from −0.7% to +3.6%, which can only be composition: whole estates now
land on one heir instead of being scattered per-unit, and heirs with no home take possession of
vacant dwellings, so the rental stock a cap acts on is a different stock.

Both forms of the supply leg are now dated strict xfails. `hazard_scale` is **not** re-fitted
and inheritance is **not** reverted: the −13.6% was produced by a floor built from two
exogenous constants, and the inheritance rewrite is verified against state invariants on 3
seeds × 60 ticks (`tests/test_state_invariants.py`, five checks, zero violations). Re-fitting
either to recover a number that two defects were generating is the move this project's
standard exists to forbid. Phase B re-derives the withdrawal margin from the arbitrage
condition (spec §7.2) and owns this target.

The rent leg also slipped, from −4.4% to −3.8%, just below the studies' −4…−6%. It is not
separately xfailed: `test_rent_cap_lowers_contract_rents` asserts a real fall and still passes,
and the band is phase B's to re-derive along with the rest.

## Phase-A finding-4 correction: the ownership drift is not an inheritance leak (2026-09-12)

The redesign spec registered finding 4 as *"Inheritance leaks ownership: heir keeps SEEKER
status while owning a vacated dwelling; ownership drifts 77.2% → 69.5%"*. The heir defect is
real and is fixed. **It is not what causes the drift.**

Measured, 3 seeds, 60 ticks, before and after the fix:

| | before | after |
|---|---|---|
| ownership, tick 1 | 0.7693 | 0.7690 |
| ownership, tail 20 | 0.6907 | **0.6934** |
| drift | −7.86 pp | **−7.56 pp** |
| `landlord_household_share` | 0.2715 | **0.2606** |

The fix is worth 0.3 pp of a 7.9 pp drift — about 4% of it. It also consolidates estates onto
one heir instead of scattering them per-unit, which is why the landlord share falls 1.1 pp.

**The actual cause**, same runs:

| | tick 1 | tick 60 | change |
|---|---|---|---|
| households | 10,041 | 11,159 | **+11.13%** |
| owners | 7,722 | 7,668 | **−0.69%** |

The owner stock is flat — slightly shrinking — while the population grows 11%. Ownership
falls because the denominator grows and the numerator does not. Nothing leaks: the accounting
identity holds exactly at every tick (owner-occupied units == owner households, 7,678 == 7,678
on seed 1 at tick 60).

That is a much larger problem than the one registered, and it is the reason target 1 sits below
the EFF band. New households form as SEEKERs and the model does not convert them into owners at
anything like the rate needed to hold the ratio. Whether that is a credit constraint, a
supply constraint or a missing first-time-buyer margin is not answered here — it is a mechanism
question, and phase A is bug fixes. Recorded as a finding for the spec, to be scoped before
phase B's calibration leans on the ownership level.

## Phase-B finding-11 correction: internal migration already has the right sign (2026-09-12)

The redesign spec registers finding 11 as *"Internal migration has the wrong sign
(`engine.py:417`); Spain's net internal flow runs rural→metro"*, and target 12 asserts that
cumulative net internal migration into the tensioned zone must be **positive**. It is carried
as a strict xfail on that basis.

**The retrieved data says the opposite.** INE EVR microdata 2015–2021 and EMCR table 69753
2021–2024, interior migration only, aggregated to the model's three zones. Both defensible
mappings of INE's size bands give the same sign in every year:

| tensioned = | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|---|
| capital + >100k non-capital | +14,911 | +2,635 | −3,911 | −32,561 | −33,393 | **−140,179** | −90,777 |
| provincial capital only | +13,072 | +180 | −4,757 | −31,117 | −29,400 | **−117,596** | −79,928 |

The metro zone is a net **loser** of internal migrants in every year from 2017 on, and EMCR
continues it: capitals −75,809 (2021) → −40,409 (2022) → −44,651 (2023) → −55,195 (2024). By
2024 the flow has decayed but has not returned to the 2015 pattern.

**Why the spec believed otherwise.** Spanish cities do grow — through *international* arrivals,
which the interior-only figures exclude by construction. Internal and total migration run in
opposite directions, and the spec's claim conflates them. The model's downward-only rule
therefore has the **correct sign** for 2017–2024, and target 12 asserts a direction the data
does not support.

**What is still wrong with the rule**, and what §7.5 is still for:

1. It is downward-only **by construction**, so the sign is an artefact, not a result. It cannot
   reproduce 2015–16, when the flow genuinely ran the other way, and it cannot respond to any
   policy — a rule that can only produce one sign cannot be falsified on sign.
2. It has no mechanism: a 10%/tick coin flip on rent burden, with no income, amenity or
   friction term, and no identifying episode.
3. Its magnitude has never been validated against anything.

The 2020 reversal remains the identifying episode and is sharper than the spec hoped: the metro
outflow is **4.2× its 2019 value** while *gross* interior flows **fell 7.9%** (1,649,351 →
1,519,606). It is pure redirection of a shrinking flow, not a volume surge, which is what makes
it identifying.

### The exterior leg, and why the mapping decides the answer (2026-09-12)

Retrieved after the correction above: the exterior component the first pass excluded, computed
from the same EVR microdata (the 12 cells with a blank size band; 36 interior + 12 exterior
exhaust the file) and, for 2021–24, reconstructed from EMCR table 69767's `Saldo exterior` by
joining padrón table 29005 and INE's own 50-capital list from table 69747.

That reconstruction validates hard: it reproduces INE's **published** interior bands exactly
for the 50,001–100,000, >100,000 non-capital and provincial-capital bands in all four years,
and to within 0.03–0.3% for the three smallest. The capital band does not depend on the padrón
join at all. The exterior band figures for 2021–24 are nonetheless **ours, not INE's** — INE
does not publish the exterior leg at band level, since table 69753 is intermunicipal by
construction and the exterior result groups break down by province, country and island only.

Does the exterior inflow flip the metro positive? **Six years of eight, not two:**

| year | interior | exterior | total | flips? |
|---|---|---|---|---|
| 2017 | −4,757 | +116,286 | **+111,529** | yes |
| 2018 | −31,117 | +176,777 | +145,660 | yes |
| 2019 | −29,400 | +217,352 | +187,952 | yes |
| 2020 | −117,596 | +102,164 | **−15,432** | **no** — exterior covers 87% |
| 2021 | −79,928 | +52,675 | **−27,253** | **no** — covers 66% |
| 2022 | −40,409 | +303,290 | +262,881 | yes |
| 2023 | −44,651 | +290,220 | +245,569 | yes |
| 2024 | −55,195 | +266,948 | +211,753 | yes |

The two failures have different causes. In 2020 the interior outflow quadrupled *while* capital
arrivals from abroad halved (362,085 → 203,256) — the borders shut at the moment of the urban
exit. In 2021 the interior outflow was still 2.7× its 2019 level and the exterior *outflow* hit
210,387, the series maximum. That makes 2020–22 a **stronger** natural test on total migration
than on interior alone: the only window in eleven years in which the big cities lost on every
margin at once, with recovery driven entirely by the exterior leg and not by interior return.

**The sign is not robust to the zone mapping, and that is the problem.** Padrón shares:
capitals 31.7%, plus >100k non-capital 42.2%, plus 50–100k 53.4%. The model's tensioned zone
holds **45% of households** — it sits in the gap, and nothing sums to it.

| mapping | 2019 | 2020 | 2021 |
|---|---|---|---|
| A capitals only (31.7%) | +187,952 | −15,432 | −27,253 |
| B capitals + >100k non-capital (42.2%) | +237,236 | −14,649 | −11,548 |
| C B + 50–100k (53.4%) | +301,329 | **+7,070** | **+31,939** |

In 2020 and 2021 the metro total is negative under A and B and **positive under C**, in both
statistics. The 50,001–100,000 band alone — 11% of Spain — carries enough exterior inflow to
reverse the aggregate sign, in exactly the years the target is most interesting.

Two signs **are** robust and can be relied on: interior net turns negative for the metro
aggregate in 2017 under all three mappings and both statistics (so the correction above is
safe), and exterior net is positive in every year under every mapping without exception.

**Caveat that must travel with the 2021 figure.** *Bajas por caducidad* — the expiry of
registrations of non-EU foreigners who do not renew — have counted inside exterior emigration
since 2006, and INE's own methodological note warns that foreigners' departures are otherwise
largely uncaptured. There is no published split. Part of the capitals' 210,387 departures
abroad in 2021 may therefore be an administrative purge rather than real emigration, and 2021
is one of the two years the metro total is negative. The figure is not wrong, but it is not a
measured outflow either.

**Target 12 cannot stand as written.** Its direction is wrong, so the strict xfail on it is
currently registering the model's correct behaviour as a failure. Pending a decision on the
replacement, it stays xfailed and this section is the reason — the xfail is not evidence of a
defect, and must not be read as one.

## Phase-B sourced-parameter revision (2026-09-14)

Two guessed zone parameters replaced with published ones. Both were free numbers; neither is
any more.

| | was (guess) | now (INE ECV) | table |
|---|---|---|---|
| `income_multiplier` | 1.15 / 1.00 / 0.80 | **1.085 / 0.950 / 0.896** | 59952, *renta neta media por hogar* by grado de urbanización |
| `tenant_share` | 0.28 / 0.20 / **0.145 (inferred)** | **0.237 / 0.186 / 0.108** | 60181, *régimen de tenencia* by grado de urbanización |

Two defects fixed on the way. The income multipliers are labelled "× national household
income" and weighted by household share came to **1.0275** — the model's households were 2.75%
richer than their own national anchor, by construction, and no guard checked it (the supply
elasticities and stock ratios both had one). And the model asserted a metro/rural income ratio
of **1.437** where ECV publishes **1.211**, a ratio that has been *narrowing* (1.29 in 2019 →
1.21 in 2025), not widening.

### What it cost, attributed

Each change was run alone on 3 seeds, so the breakage is attributed rather than guessed:

| variant | cap rent | cap leases | price-to-income | small-landlord share | ownership |
|---|---|---|---|---|---|
| both guesses | −3.70% | −1.04% | 7.11 | 0.858 | 0.693 |
| ECV income only | −4.08% | +0.26% | 7.21 | 0.856 | 0.691 |
| ECV tenure only | −2.41% | −6.70% | **6.73** | **0.842** | 0.713 |
| both sourced | **+0.88%** | −1.66% | 6.68 | 0.838 | **0.716** |

**The income gradient alone breaks nothing.** Every gate it touches still passes, and the cap's
rent leg gets *stronger*. The tenure change carries price-to-income (6.73) and the small-landlord
share (0.842) below their gates on its own.

**The cap sign flip is an interaction.** Neither change flips it alone; together the cap raises
tensioned contract rents by 0.88%. It is **not** the pooled-median composition artefact the
model already documents: `cap_coverage` is 1.0 in the baseline, so the declared and pooled
columns are identical and both read +0.88%. The mechanism is that the cap **stops binding** —
market rents fall below the reference index, and the magnet (`ask × magnet_gain` toward the cap)
then pulls asks *up*. The cap acts as a floor rather than a ceiling, while `shadow_rent` rises
6.58% as withdrawals tighten supply. That is a real model result on a real reference-index
mechanism, and reference indices acting as focal points is not a fictional phenomenon.

Five targets are now dated strict xfails: price-to-income, small-landlord share, the 2021–25
run-up, and the cap's rent leg in both its validation and engine tests. **Nothing was re-fitted.**
These are published values replacing guesses; re-tuning a sourced parameter to restore a target
is precisely the move this project's standard exists to forbid.

**One target improved.** Ownership rose 0.693 → 0.716, well inside its 0.69–0.75 gate and closer
to the EFF band it has been sitting below. Sourcing the rural tenure cell did that.

### The caveat that matters more than the breakage

**ECV's `densamente poblada` is not the model's `TENSIONED`.** ECV classifies by population
density (Eurostat DEGURBA); the model's tensioned zone is defined by *housing-market tension*.
Madrid and Barcelona have market-rent tenant shares well above the 19.5% ECV reports for all
densely-populated Spain, so taking the dense cell for the tensioned zone probably understates
renting there — and understating the tensioned rental market is the most likely explanation for
why the cap stopped binding.

**RELEASED 2026-09-14 — the caveat was right in direction and wrong in magnitude.** The
declared tensioned-municipality list was retrieved (MIVAU national compilation, 317
municipalities in 5 CCAA, every name joined to its INE code against padrón 29005, 317/317
matched) and the aggregate the model's zone actually is — **the 89 largest municipalities**,
all above 50,000 so Censo 2021 covers them directly — was measured:

| | model (ECV dense) | top-89, measured | gap |
|---|---|---|---|
| `tenant_share` | 0.237 | **0.248** | +1.1 pp |
| `income_multiplier` raw ratio | 1.0683 | **1.0766** | +0.8% |

Barcelona (31.1% renting) and Madrid (24.0%) really are above the dense cell, but the 45%
aggregate they sit inside is diluted by Sevilla 13.9%, Málaga 13.5%, Bilbao 14.4%, Murcia
16.0%. **A 1.1 pp understatement cannot explain a rent cap that stopped binding**, so that
hypothesis is withdrawn. The sign flip is re-attributed below, and the re-attribution is
confirmed by the fix: the phase-B migration rewrite restored the cap without either parameter
being touched.

Two further findings from the same pass, both worth keeping:

- **The declared list is a political aggregate, not a tension aggregate.** It is 19.98% of
  Spanish households, not 45%, and 15 of 19 CCAA have declared nothing. **Madrid is not
  declared**, at 24.0% renting, out-renting 26 of the 33 measured declared municipalities; 12
  of the 20 highest rental shares among the 151 published municipalities are undeclared, and
  the Balearic, Canarian and Levantine markets are absent entirely, while Barakaldo (11.0%) is
  in. Validating a 45% zone against it would be validating against politics.
- **`household_share = 0.45` is now the binding guess.** Every figure above is conditional on
  it, because it decides which municipalities enter the aggregate.

This is the same mapping problem the migration data raised, and it was declared the same way
rather than absorbed — which is what made it checkable, and what let it be checked. A real datum on the wrong aggregate is not automatically better than an
inference on the right one; what makes it better here is that it is checkable, and this
paragraph is what makes it checkable. Resolving it needs a tension-based rather than
density-based aggregate — the MIVAU declared tensioned-zone municipality list crossed with ECV
or ADRH — which is not retrieved.

## Phase-B §7.5: bidirectional migration, and what it restored (2026-09-14)

The downward-only migration rule is replaced by a comparison (`engine._demography`):

    gain(d) = income × (mult(d)/mult(o) − 1) − 12 × (rent(d) − rent(o)) − friction

Both directions are reachable, so the sign is an outcome rather than a property of the code.
Measured, 3 seeds × 60 ticks, cumulative net interior flows in model households:

| zone | model | observed sign, mapping B |
|---|---|---|
| TENSIONED | **−103.3** | negative every year from 2017 |
| SECONDARY | +45.7 | positive |
| RURAL | +57.7 | positive |
| sum | 0.0 | 0 by construction |

### What it restored, without touching a parameter

The sourced-parameter revision above broke five targets. **The migration rewrite closed six**,
and no guess was reinstated to do it:

| target | after sourcing | after §7.5 |
|---|---|---|
| price-to-income | 6.68 ✗ | passes |
| 2021–25 run-up | 0.0371 ✗ | passes |
| cap rent leg (direction) | +0.88% ✗ | passes |
| cap coverage scaling | ✗ | passes |
| cap supply leg, weak form | ✗ (phase A) | passes |
| cap supply leg, **reaches Monràs** | ✗ (phase A) | **passes** |

The rent-cap dial, measured the same way each time:

| ε | phase A | after sourcing | after §7.5 |
|---|---|---|---|
| 0 | −4.9% / −0.7% | — | −13.3% / +3.0% |
| 2 | −4.4% / −7.3% | +0.9% / — | **−13.3% / −10.1%** |

**That is the real attribution of everything phase A and the sourced parameters appeared to
break.** The guessed income and tenure ladders were compensating for a migration rule that
funnelled every priced-out household into the rural zone. Fix the rule and the sourced values
work. The 1.1 pp tenure understatement was never the explanation.

### What it costs, and what it does not fix

**The rent leg is now three times too strong**: −13.3% against the studies' −4…−6%. The
supply leg reaches Monràs and the rent leg overshoots; target 8 is not closed, it has moved.
No test gates the rent *magnitude* today — only its direction — so this is recorded here and
belongs to §7.1, which re-derives the withdrawal margin from the arbitrage condition.

Two targets broke and are dated strict xfails: the boom yield compression (target 10 — the
boom now *raises* the yield, because the new rule sends households out of the metro faster as
the boom widens the rent gap; the old rule could not respond to a boom at all, so its
compression was insensitivity rather than mechanism) and the secondary vacancy ladder (13.36%
against a 13.1% band top, a 0.26 pp overshoot, not re-fitted).

**And the rule's gross flows are wrong, which is registered, not hidden.** At baseline there is
**no interior inflow to the tensioned zone at all** — 3 seeds × 40 ticks give tensioned→rural
224, secondary→rural 37, and nothing the other way. Spain's interior net (≈100k/yr) is a small
difference between two large gross flows (≈1.6M moves/yr) and this rule has one of them at
zero. The mechanism is not one-directional — a 35% metro income shock produces 329 and 124
inbound immediately, which `test_interior_migration_is_bidirectional` asserts — but the only
pull toward the metro here is the 1.21 income ratio, and it clears the rent gap for nobody.
What is missing is where the job is, rather than what the average wage ratio is. **Not closed
by adding an unsourced amenity term tuned until the gross flows look right**, which is the move
phase B exists to remove; it needs §7.5's amenity term with its own identification — the same
term that would make `location_premium` derivable rather than free.

## Zone ladders measured on the model's own zones (2026-09-14)

The ECV `grado de urbanización` gradient adopted two days earlier is superseded by one measured
on the model's *own* zone definition: all 8,131 Spanish municipalities ranked by Censo-2021
households and cut at 45/35/20.

| zone | municipalities | households | share | `income_multiplier` | `tenant_share` measured |
|---|---|---|---|---|---|
| TENSIONED | 89 | 8,359,782 | 45.09% | **1.0766** | **0.2478** (100% measured) |
| SECONDARY | 708 | 6,473,671 | 34.92% | **0.9621** | **0.1784** (23.2% measured) |
| RURAL | 7,334 | 3,705,770 | 19.99% | **0.8934** | **0.1461** (0% measured) |

**Both identities close without being forced.** The income ladder weights to 0.99989 — the
renormalisation the previous gradient needed (×1.0157) becomes ×1.0001. The tenure ladder
weights to 0.2032 against ECV's national 0.202, a +0.12 pp residual against the 0.87 pp the
model was declaring.

### Why the old residuals existed

**ECV's DEGURBA classes are 54/31/15 of households, not 45/35/20.** Recovered by solving ECV
table 60181's four over-determined tenure rows with sum-to-one imposed: 0.5416 / 0.3104 /
0.1479, fitting all four rows to ≤0.03 pp and independently reproducing ECV's national *income*
anchor — held out of the fit — to €20, or 0.05%.

So the model was mixing DEGURBA cells with size-rank-shaped weights, and both declared
residuals were that mismatch rather than measurement error in the cells. Only the income ladder
is switched here; the tenure ladder has an open cell, below.

### The RURAL tenure cell is not a measurement, and is not adopted

Zero rural municipalities have published tenure. The 0.1461 is imputed from ECEPOV's single
≤50k band, which holds **47.4% of Spain — 2.4× the zone it fills** — and that band publishes no
internal size gradient, so only CCAA composition separates rural from the secondary zone's small
towns. Re-splitting the band, pooled total held fixed:

| RURAL assumption | RURAL | SECONDARY | national identity |
|---|---|---|---|
| as imputed | 0.1461 | 0.1784 | 0.2032 |
| ECV *poco poblada*, all renting | 0.1368 | 0.1837 | 0.2032 |
| ECV *poco poblada*, market rent only | 0.1089 | 0.1996 | 0.2032 |
| flat across the band | 0.1561 | 0.1726 | 0.2031 |

**The identity is invariant across all four**, so the national check cannot discriminate between
them. Defensible range 0.109–0.156. The model's current 0.108 sits at the very bottom of it.

The tenure ladder is therefore **not changed in this commit**. Picking a rural cell is a
basis decision — size-rank Censo for two zones and DEGURBA ECV for the third is mixed-basis and
has to be declared as such — and it is left open rather than made silently.

### Effect

One target moved: the cap's supply leg at elasticity 2 went from −10.1% to −7.85% contracts,
failing the −9% assertion again. A ≈1 pp change in two zone income multipliers moved it 2.25 pp.
That target has now moved five times in one phase (−13.6 → −7.3 → −1.6 → −10.1 → −7.85) and is
not robustly passing in either direction; it is re-xfailed with that history on it rather than
treated as a near miss.

### A coherence defect in the size-rank cut, recorded

The rank is by households, so metro commuter municipalities land in SECONDARY — Castelldefels,
a *declared tensioned zone* renting at 27.1%, plus Tres Cantos, Sitges and Pozuelo — while Arona
enters TENSIONED on size alone. A functional-urban-area cut would fix it. The MIVAU *Áreas
Urbanas* list and a municipal DEGURBA classification are the two highest-value gaps remaining.

## Phase-B §7.1: the total-return hurdle (2026-09-14)

`agents/landlord.required_rent` becomes

    r_req = V · (i_bond + π − E[g]) / (12 · (1 − c))

The old form was `required yield = bond + spread` with the spread fitted to reproduce the
observed zone ladder — the yield pinned to its own target (spec §2, finding 3). With E[g] in
the expression it is an **output**.

**π is split, because only half of it is measured.** `prime_risk_spread = 0.0035` is CBRE's
Q1-2026 prime residential yield against BdE's 10-year bond (Madrid +25 bp, Barcelona +45 bp);
`small_landlord_premium = 0.033` is **the one free parameter of §7.1, declared rather than
buried**. The old 2 pp spread could not be reused: it *was* the observed yield minus the bond,
i.e. the quantity the hurdle is meant to predict.

**`c = 0.22`** of a sourced 0.20–0.24 [AEAT *cuenta de resultados del arrendamiento*,
FY2019–FY2024, `Vivienda habitual = Sí`], pre-tax, **vacancy excluded** — AEAT's unit is the
*vivienda equivalente* (ownership share × days in that use), and the model already generates
vacancy, so the vacancy-inclusive 0.24–0.30 would charge it twice. No zone gradient, and that
is counter-intuitive: `c` falls with rent level, not urbanity (Madrid 26.3%, Balears 18.8%).

### What it fixed

| target | before §7.1 | after |
|---|---|---|
| 10 — boom compresses the gross yield | ✗ xfail | **passes** |
| vacancy ladder | ✗ xfail | **passes** |
| interior migration has gross flows both ways | ✗ xfail | **passes** |
| national entry yield (contract basis) | 7.09% | **7.00%**, mid-band of BdE's 6.5–7.5% |

Target 10 is the identifying test — the compression is the signature of the hurdle, and it is
what the free premium is identified on rather than a level fit.

### What it broke, and the single reason

**The model's rents are set by the landlord's reservation, not by demand.** Lower the floor —
which is what expected appreciation does — and the whole rent path follows it down, because
`CONGESTION_GAIN = 0.05` is too weak for scarcity to push back. Five targets are dated strict
xfails on that one cause: boom rent growth (now −5.4% against a +2.5% floor), the
insider/outsider wedge (now −6.3%, sitting tenants paying more than entrants), and three
rent-cap tests where the cap now acts as a **floor** — market rents sit below the reference
index and the magnet pulls asks up to it.

This is spec finding 2 — *"no scarcity→price channel"* — **on the rent side rather than the
sale side**. Phase D is already scoped to add it for sales; it has to do both.

### The false positive that was not allowed to stand

`test_rent_cap_supply_response_reaches_monras` **passes numerically and is held xfailed
anyway.** The dial reads −9.8% contracts at ε=0 and −21.8% at ε=2, clearing the −9% assertion
easily. But Monràs & García-Montalvo measure −10% tenancies **at −5% rents** — a co-movement —
and the model gives −21.8% tenancies at **+6.8% rents**: same sign on quantity, opposite sign
on price. Letting it go green would put a number in this table that reads as evidence for a
mechanism the model does not have.

## Phase-B §7.4: cash-buyer anchors (2026-09-14)

Finding 5 — *"two cash buyers bid against the index they help set: positive feedback with no
nominal anchor"*. Both are re-anchored.

**Large investor.** `budget = price_index × U(0.95, 1.05)` becomes a capitalised bid,
`max_bid = 12·r·(1 − c) / y_req`. Anchoring to RENT breaks the loop: rents are set in a
different market by different agents, so the investor now has an opinion about value its own
purchases do not manufacture, and it stops buying when prices outrun rents — which is what a
yield hurdle is supposed to mean and what the old form could not express. `(1 − c)` nets the
rent down, the same cost share `required_rent` grosses up by in §7.1, because both agents are
pricing the same cash flow.

**Foreign overlay.** The arrival rate was `foreign_purchase_share × recent Spanish sales` — a
declared-exogenous demand source made a function of the market it buys into, so a domestic
slump cut foreign arrivals mechanically and the 8% share could never be falsified because it
was an input. It is now a constant, and the budget prices off an exogenous path (the zone's
initial level compounded at the nominal anchor × the observed non-resident €/m² premium)
rather than off `ZoneState.price_index`.

### Effect

| | before §7.4 | after |
|---|---|---|
| price-to-income | 9.89 (post-§7.3) / — | **7.48**, inside 7.0–8.2 |
| national entry yield | — | **7.00%**, mid-band of BdE's 6.5–7.5% |
| non-resident share of purchases | 8% **by construction** | **2.28%**, a prediction and wrong |

**The share becoming wrong is the point.** It was an input and could not be wrong; it is now
produced by a constant stream and can be.

**The cause, corrected 2026-09-14 after measuring it.** The first diagnosis — the retrieval's
and mine — was that the budget anchor compounded at the model's 2%/yr rate, which is Spanish CPI
to within 0.1 pp, while the observed non-resident buyer ran +3.69%/yr real. That was right about
the anchor and **wrong about the binding constraint**. The growth rate is now sourced at
+5.86%/yr nominal [CIEN Tabla 1C, calibration window only — the full-window +2.16%/yr contains
the sealed bust and adopting it would import hold-out information], and the share moved 2.28% →
2.23%, which is to say not at all.

Measured instead: **310 foreign offers over a 40-tick run against 3,471 transactions.** Every
offer winning would give 8.9%; they win 31%. The constraint is **listing supply in the one zone
the overlay operates in**, not budget.

Behind that sits a zone-abstraction problem the spec did not anticipate. Spanish non-resident
purchases concentrate in **coastal and island markets** — Alicante, Málaga, Balears — and this
model's three zones have no coastal type, so the overlay is confined to a tensioned metro zone
that is not where non-residents actually buy. Raising `foreign_arrivals_per_tick` would not fix
it; it would make more offers lose. Closing it needs a coastal zone or an overlay reaching more
than one zone, and that is a **specification decision, not a calibration**.

The sourced growth rate is kept regardless: a budget flat in real terms by construction was
wrong whether or not it was what bound.

It is **not** closed by raising `foreign_arrivals_per_tick` until the share returns: that
restores the number by fitting the flow to the target it is supposed to predict, which is the
defect §7.4 exists to remove. Registered as a dated strict xfail
(`test_emergent_non_resident_share_matches_registradores`), along with the non-resident
surcharge test, whose 25% threshold is measured against a base that has itself moved.

### One target closed and re-opened, which is itself the finding

`test_interior_migration_has_gross_flows_both_ways` closed under §7.1 — the hurdle lowered metro
rents enough for inbound moves to clear the friction — and re-opened under §7.4 when the
investor and foreign anchors moved metro prices back. **That it can be closed and re-opened by
unrelated price-side changes is the evidence that it was being held shut by a coincidence rather
than by a mechanism.** The underlying deficiency is unchanged: the only pull toward the metro is
the income ratio, and what is missing is where the job is.

## §7.4's falsification test, run (2026-09-14)

The spec states it explicitly: *"if Registradores' non-resident purchase series tracks Spanish
transaction volume one-for-one (2007–2025), the exogenous treatment is wrong."*

**It does not track it. The exogenous treatment stands.**

Series: **MIVAU Boletín Online Tabla 1.6**, quarterly 2007Q1–2026Q1, 77 points, operations, all
housing, split TOTAL / residentes (españoles, extranjeros) / no residentes (españoles,
extranjeros). Independently confirmed by the Notariado CIEN annex (semi-annual, *vivienda libre*
only): non-resident foreign purchases 2007 = 24,489 (MIVAU) vs 24,570 (CIEN), 0.3% apart; 2025 =
51,367 vs 52,781, 2.8% apart.

**2007→2013: total Spanish transactions −64.1% while non-resident foreign purchases +20.4%.**
Arc elasticity **−0.18**.

| window | corr | elasticity | 95% CI | R² |
|---|---|---|---|---|
| 2007Q1–2025Q4 (the spec's window) | +0.499 | +0.753 | [0.455, 1.050] | 0.249 |
| 2007Q1–2013Q4 (**sealed hold-out**) | +0.116 | +0.093 | [−0.215, 0.401] | 0.013 |
| 2014Q1–2026Q1 | +0.713 | +0.769 | [0.553, 0.985] | 0.508 |

The decisive fact is the ratio rather than the elasticity: the non-resident share ran **2.55% →
10.67%**, a 4.18× swing, so no constant `k` exists. Freezing `k` at its 2007 value predicts
8,795 non-resident purchases for 2013 against 29,496 actual — wrong by **3.35×**; RMSE of the
log ratio is 0.891 across all 77 quarters.

**Reported against the conclusion**, because it belongs in the record: on year-on-year *growth
rates* the full-window elasticity is 0.905 with a confidence interval covering 1, so growth
co-movement alone cannot reject one-for-one. It is 1.45 post-2013 and 0.66 excluding COVID —
unstable, and consistent with common shocks rather than with proportionality. The level and
ratio evidence is what carries the conclusion.

Hold-out discipline: the 2007–2013 numbers are evidence about the *specification* and are
flagged unusable for calibration. The calibration window stays 2014–2025.

### Four corrections this pass forced

1. **The spec names the wrong institution.** Registradores does not publish a non-resident
   series and says it cannot — ERI methodology annex folio 117 (PDF page 117 of 122; an earlier note said 116, which was PyMuPDF's 0-based index): *"no se adentran en el concepto de
   residencia, ya que no es un dato que quede recogido en la escritura de compraventa."* §7.4's
   falsification test should name **MIVAU / Notariado**.
2. **The earlier "CID-encoded PDF" diagnosis was wrong.** PyMuPDF reads all 122 ERI pages as
   text with no CMap work; the blocker was simply that no renderer was installed. What does
   block a series there is that ERI's history is drawn as **vector charts**.
3. **INE ETDP has no nationality or residence breakdown** — all 17 tables enumerated. Confirmed
   negative, recorded so it is not re-checked.
4. **The €/m² premium is not a constant.** §7.4's "3,063 vs 1,713" is exactly CIEN 2S2024 — one
   point on a series running **1.02× (1S07) → 1.79× (2S24)**, a ~75% drift. It must enter as a
   range or a path, not a point, and this is the identified cause of the model's 2.28%
   emergent share.

### The finding that outranks the test result

**Resident foreigners track domestic volume at β = 1.01; non-residents do not.** The model has
ONE foreign agent, so it is averaging two opposite mechanisms. That is a specification defect
§7.4 did not anticipate and neither did the critique it answers.

Post-2013 the two series do co-move (corr +0.71 to +0.86, elasticity 0.63–0.77), so the
defensible claim is **"own cycle, partially correlated"**, not "orthogonal". The model's
exogenous stream is the right shape and should not be described as independent.

## Phase B, consolidated (2026-09-14)

`profitability-block` merged: **0 failures, 11 dated strict xfails**. What landed, what it cost,
and what is parked.

### Landed

| § | Mechanism | The thing it changed |
|---|---|---|
| 7.1 | Total-return hurdle, `r_req = V(i_bond + π − E[g]) / (12(1−c))` | the rental yield stops being an input pinned to its own target and becomes an output |
| 7.4 | Both cash buyers re-anchored — investor capitalises rents, foreign buyer prices off an exogenous path | neither bids against the index it helps set |
| 7.5 | Bidirectional interior migration from a zone comparison | the sign of migration is an outcome, not a property of the code |
| 13.7 | Yields judged on the **contract entry** basis | national entry yield 7.00%, mid-band of BdE's own 6.5–7.5% |
| 13.8 | Migration stated on total flows, mapping B declared | the target stops registering correct behaviour as a failure |
| — | Zone income ladder measured on the model's own zones (ADRH) | a guessed 1.15/1.00/0.80 replaced, and a 1.0275 identity defect fixed |
| — | Zone tenure ladder from ECV; the rural cell was **inferred** | published where it was guessed |

§7.4's falsification test was **run** and did not fire: 2007→2013 Spanish transactions −64.1%
against non-resident purchases +20.4%, the share swinging 2.55% → 10.67%, so no constant `k`
exists. The exogenous treatment stands.

### Four spec findings that did not survive contact with data

Recorded here because the pattern matters more than any one of them: **every empirical claim in
the redesign spec that was written from model memory rather than retrieved turned out wrong.**

| finding | what the spec said | what the data said |
|---|---|---|
| 4 | inheritance leaks ownership, 77.2% → 69.5% | the leak is real but worth 0.3 pp of 7.9; owners are flat while households grow 11% |
| 6 | `own_vs_rent` is inert | active in 5.78% of decisions, and it engages *less* in the rate shock it was said to carry |
| 11 | Spain's internal flow runs rural→metro | it runs metro→rural every year from 2017; cities grow through *international* arrivals |
| §7.4 | the series is Registradores' | Registradores cannot publish it — residence is not in the deed |

This is the project's ≥2-sources rule earning its place four times in one phase.

### The cost, unpaid

Eleven dated strict xfails, all naming a mechanism and a phase. The single largest cause is
one sentence: **the model's rents are set by the landlord's reservation, not by demand**, because
`CONGESTION_GAIN = 0.05` is too weak for scarcity to push back. That is spec finding 2 — *no
scarcity→price channel* — on the rent side, where the spec scoped it only for sales. Phase D has
to do both. Five of the eleven trace to it: boom rent growth, the insider/outsider wedge, and
three rent-cap tests where the cap now acts as a floor rather than a ceiling.

Nothing was re-fitted to close any of them. `hazard_scale` was not re-tuned when the hazard floor
came out; `small_landlord_premium` is identified on target 10's compression, not on a level fit;
`foreign_arrivals_per_tick` was not raised to restore a share it is supposed to predict.

### Parked, on `buy-to-let-remeasure`

§7.3 buy-to-let entry. It **closes target 11** — one of the three original phase-0 xfails — plus
the insider/outsider wedge and the small-landlord share, and takes the rural gross yield from 22%
to 8.10%. It also found three implementation defects, one of them a **latent pre-existing state
bug** (`clearing.settle` left a unit owner-occupied by nobody), caught by the invariant tests
added in phase A.

One thing keeps it out: yield-chasing entry **arbitrages the zone price ladder away** — T/R falls
to 1.65 against a floor of 2.6. The 1.5 pp zone premium cannot hold against a rural yield
starting at 22%. The concrete, sourced hypothesis for the missing force is the **vacancy
gradient** the operating-cost retrieval measured and `c` deliberately excludes: *días de alquiler*
338/365 in Extremadura against 352/365 in Barcelona, on top of the model's own 18% rural vacancy.
Excluding it from `c` was right — the market already generates vacancy — but the investor should
still **see** it when choosing a zone, which is a different thing from charging it as a cost.

### What phase B did not reach

- §7.3, above.
- International arrivals as a mechanism: `formation_zone_weights` still fuses domestic household
  formation and immigration into one fitted vector (model-spec §13.8).
- Two foreign agents. Resident foreigners track domestic volume at β = 1.097 (R² 0.940);
  non-residents at β = 0.093 (R² 0.013) through the bust. One agent averages two opposite
  mechanisms.
- A coastal zone. Non-resident purchases concentrate in Alicante, Málaga and Balears, and the
  model's three zones have no coastal type, which is why the overlay's emergent share is 2.2%
  against 6.5–8%.

## Phase E — recalibration, the variance rule, and the sealed hold-out (2026-09-14)

The calibration protocol (`model-spec.md §13.4`) in order: LHS over the free parameters →
Morris screening → Sobol on the survivors → the variance rule → then the 2008–13 hold-out,
**once**. Everything before the hold-out uses 2014–2025 moments only.

### Step 0 — a defect in the instrument, found before it was used

`hazard_scale` moved into `CapResponseConfig` in phase A, and `sensitivity.py` went on
patching a module attribute that no longer existed. Every sweep since has therefore held it
at its default while reporting it as swept. It is fixed here, and it shows up in the Morris
table below exactly as it should: zero effect at baseline, because the rent cap it governs is
not switched on.

### Step 1 — LHS, 200 points × 3 seeds, scored on the §9 bands

Scored by a **band loss**: zero inside each band, squared relative distance outside it. A
distance to band midpoints would have invented precision the sources do not have and dragged
the model toward the centre of bands it is already inside.

| | loss |
|---|---|
| shipped defaults | **0.0142** |
| best of 200 sampled points | 0.0177 |
| 10th percentile | 0.0738 |
| median | 0.3333 |

**No sampled point beat the defaults — 0 of 200.** The protocol's fitting step therefore
returns "keep what you have", which is the outcome least likely to be an artefact of the
exercise: the parameters were identified one at a time against their own observables in
phases B, C and D, and a 37-dimensional sweep cannot find a better joint point.

What the defaults are still outside, on the LHS basis (40 ticks, 3 seeds): the foreclosure
rate (0.04% against a 0.10–0.80% band) and the negotiation margin (3.1% against 4–12%) — the
two failures phases C and D already registered as dated strict xfails, with their causes
named. Purchase effort reads 33.9% against a 35–40% band at 40 ticks; at the 60-tick basis the
gates use it is 36.6%, inside.

### Step 2 — Morris screening, 380 evaluations

Ranked by the mean of each parameter's normalised μ\* across the sixteen reported moments:

| rank | parameter | mean | max |
|---|---|---|---|
| 1 | `ask_markup` | 0.70 | 1.00 |
| 2 | `overbid_sigma` | 0.54 | 0.96 |
| 3 | `search_listings` | 0.52 | 1.00 |
| 4 | `price_index_smoothing` | 0.49 | 0.89 |
| 5 | `buy_attempt_prob` | 0.47 | 1.00 |
| 6 | `essential_share` | 0.44 | 1.00 |
| 7 | `base_starts_per_tick` | 0.43 | 1.00 |
| 8 | `momentum_gain` | 0.43 | 1.00 |
| … | `small_landlord_premium` | 0.41 | 1.00 |
| last | `hazard_scale` | 0.00 | 0.00 |

Four of the top eight are phase-C and phase-D parameters, which is what one would expect
after adding two mechanisms — and three of those four are the ones this project has already
labelled reduced form. The screening is the reason to decompose exactly these eight.

### Step 3 — Sobol on the eight survivors, 1,280 evaluations

Total-order indices (ST), with the coefficient of variation of each moment across the design,
because a large share of a small variance is not the same statement as a large share of a
large one:

| Moment | CV | first | second | third |
|---|---|---|---|---|
| price-to-income | 0.102 | `ask_markup` 0.34 | **`overbid_sigma` 0.26** | `price_index_smoothing` 0.19 |
| purchase effort | 0.102 | `ask_markup` 0.34 | **`overbid_sigma` 0.26** | `price_index_smoothing` 0.19 |
| price-to-income ladder margin | 0.222 | `ask_markup` 0.42 | `price_index_smoothing` 0.36 | `overbid_sigma` 0.35 |
| transactions | 0.164 | `ask_markup` 0.89 | `search_listings` 0.17 | `price_index_smoothing` 0.09 |
| completion ratio | 0.187 | `base_starts_per_tick` 0.56 | `ask_markup` 0.39 | `overbid_sigma` 0.18 |
| rent overburden | 0.039 | `ask_markup` 0.69 | `overbid_sigma` 0.40 | `price_index_smoothing` 0.32 |
| tensioned/rural price ratio | 0.118 | `ask_markup` 0.62 | `price_index_smoothing` 0.34 | `overbid_sigma` 0.31 |
| rent level | 0.106 | `ask_markup` 0.50 | `price_index_smoothing` 0.46 | `overbid_sigma` 0.29 |
| tensioned market vacancy | 0.302 | `base_starts_per_tick` 0.41 | `overbid_sigma` 0.37 | `search_listings` 0.31 |
| cash-purchase share | 0.128 | `price_index_smoothing` 0.47 | `ask_markup` 0.44 | `overbid_sigma` 0.42 |
| arrears | 0.217 | **`essential_share` 0.78** | `price_index_smoothing` 0.06 | `buy_attempt_prob` 0.06 |
| foreclosure rate | 0.464 | `ask_markup` 0.58 | `search_listings` 0.36 | `essential_share` 0.30 |
| negotiation margin | 2.956 | `search_listings` 0.56 | `ask_markup` 0.32 | `overbid_sigma` 0.13 |
| sold inside the quarter | 0.678 | **`search_listings` 0.94** | `ask_markup` 0.35 | `overbid_sigma` 0.08 |
| bidders per listing | 0.152 | `overbid_sigma` 0.40 | `search_listings` 0.32 | `buy_attempt_prob` 0.23 |
| ownership rate | 0.0065 | — flat across the design, not decomposed | | |

Three readings that matter more than the table:

1. **`overbid_sigma` fell from 56% of the price-to-income variance to 26% — and 26% is still
   above the threshold.** Phase D wrote this test down in advance and it comes back half
   passed: the guessed dispersion no longer dominates the price level, and it has not been
   demoted far enough to make the level reportable as a magnitude.
2. **Arrears are a measured uncertainty, not an invented one.** 78% of their variance is
   `essential_share`, whose range (0.34–0.71) is INE's own poverty-threshold spread between a
   one-person household and two adults with two children. The model's arrears level is
   therefore *conditional on where in that band a household's consumption floor sits*, which
   is a statement about the evidence rather than about the model.
3. **Two of the phase-D targets are governed by the parameter that was identified on them.**
   `search_listings` explains 94% of the time-to-sale variance and 56% of the negotiation
   margin's — and `m` was identified against exactly those two observables. That is not a
   defect, it is what identification means, but it does mean neither can be reported as an
   independent confirmation of the auction. They are the fit, not a test of the fit.

### Step 4 — the variance rule, applied

`model-spec §13.2`: a reported magnitude whose variance is more than 25% explained by an
`assumed` (unsourced) parameter is downgraded to direction-only. Applied as written, without
adjustment after seeing the numbers:

| Quantity | Largest assumed share | Category after the rule |
|---|---|---|
| Price level, price-to-income, purchase effort | `overbid_sigma` 0.26 | **direction only** |
| Rent level, tensioned/rural ratio, overburden | `overbid_sigma` 0.29–0.40 | **direction only** |
| Transactions | `ask_markup` 0.89 — assumed that sellers post a markup, measured (6.2%) how big | **direction only** |
| Tensioned market vacancy | `overbid_sigma` 0.37 | **direction only** |
| Cash-purchase share | `overbid_sigma` 0.42 | **direction only** |
| Negotiation margin, time to sale | `search_listings` 0.56 / 0.94 | **direction only**, and circular besides (§ above) |
| Arrears | largest assumed share below 0.10; the 0.78 belongs to a measured range | **magnitude, conditional on the essential-consumption band** |
| Ownership rate | flat across the design | **magnitude** |
| Completion ratio | `base_starts_per_tick` 0.56, a sourced flow with a range | **magnitude, conditional on the starts band** |

So after five phases the model reports **two magnitudes and everything else as a direction**.
That is a worse-sounding result than "the price level is 7.78", and it is the honest one: the
price level moves by ±10% across the range of a parameter nobody has measured, and saying so
is the whole point of having the rule. What phase D bought is not a reportable price level —
it is that the dependence is now 26% instead of 56%, that the mechanism producing the level is
an auction rather than a dispersion parameter, and that the remaining exposure has a name and
a way to close it: measure the dispersion of willingness-to-pay for identical dwellings.

### Step 5 — ten seeds, because three were hiding things

`model-spec §13.4`: nothing is reported on fewer than ten seeds after phase E. The validation
fixture ran on three until today. Re-measured on ten (60 ticks, last 20 averaged):

| Moment | 10 seeds | sd | band | |
|---|---|---|---|---|
| Price-to-income | 7.91 | 0.14 | 7.0–8.2 | pass |
| Ownership rate | 0.716 | 0.003 | 0.70–0.74 | pass |
| Transactions /yr | 3.70% | 0.12pp | 2.6–3.8% (test), 2.5–3.6% (sourced) | pass on the test's band, **0.1pp above the sourced one** |
| Market-tenant overburden | 0.323 | 0.013 | 0.26–0.34 | pass |
| Completion ratio | 0.547 | 0.036 | 0.40–0.70 | pass |
| Gross yield, contract basis | 0.0685 | 0.0031 | 0.065–0.075 | pass |
| Purchase effort | 0.373 | 0.006 | BdE 35–40% | pass |
| Arrears | 0.0248 | 0.0027 | 0.010–0.040 | pass |
| Sold inside the quarter | 0.481 | 0.026 | 0.43–0.63 | pass |
| Bidders per listing | 3.47 | 0.14 | 1 < b ≤ 7 | pass |
| Insider/outsider wedge | +0.045 | 0.032 | > 0 | pass, and the sd is most of the mean |
| Foreclosure rate | 0.0003 | 0.0002 | 0.0010–0.0080 | fail (phase C's, unchanged) |
| Negotiation margin | 0.031 | 0.002 | 0.04–0.12 | fail (phase D's, unchanged) |
| Vacancy, secondary | 0.141 | 0.006 | 0.081–0.131 | fail (phase C's, unchanged) |

Two things the three-seed basis was hiding. Transaction volume sits **above the sourced band**
(3.70% against 2.5–3.6%) and inside only the widened band the test carries — the widening is
documented in the test and predates this phase, but on ten seeds it is load-bearing, and the
Sobol run says 89% of that moment's variance is `ask_markup`. And the insider/outsider wedge
has a standard deviation of 0.032 around a mean of 0.045: it is positive on the average and
not reliably positive on a single seed, so it is a direction that holds in expectation, which
is weaker than the gate's wording suggests.

## The brakes on a falling market (2026-09-15)

`docs/assumptions.md` carried one row as the largest known gap after phase E: **nothing in
this model slows a market once it turns.** Two mechanisms close part of it, and the discipline
around them is the interesting half of the entry.

### What was added, and why it is not a fit

| Mechanism | Identified on | What it is allowed to move |
|---|---|---|
| Nominal loss aversion in the ask (§5d.1) | Genesove & Mayer, QJE 2001: asking prices 25–35% of the nominal loss higher, sale hazard much lower, list-price effect twice as large for owner-occupants | nothing in a rising market — the loss is zero and the ask is unchanged |
| Forbearance, Código de Buenas Prácticas (§5d.2) | RDL 6/2012 annex verbatim, and the CBP's own counts (45,697 families in five years) | only households inside the umbral de exclusión, a poverty gate |

Neither was calibrated on the episode that revealed the gap, and **the episode can no longer
validate this model** (§13.11) — that cost is recorded, not minimised.

### The calibration window does not move

Ten seeds, 60 ticks, last 20 averaged, against the phase-E baseline:

| Moment | phase E | with brakes | band | |
|---|---|---|---|---|
| Price-to-income | 7.91 | **7.88** | 7.0–8.2 | pass |
| Ownership rate | 0.716 | **0.718** | 0.70–0.74 | pass |
| Purchase effort | 0.373 | **0.371** | 0.35–0.40 | pass |
| Gross yield, contract | 0.0685 | **0.0679** | 0.065–0.075 | pass |
| Overburden | 0.323 | **0.322** | 0.26–0.34 | pass |
| Completion ratio | 0.547 | **0.551** | 0.40–0.70 | pass |
| Sold inside the quarter | 0.481 | **0.473** | 0.43–0.63 | pass |
| Arrears | 0.0248 | **0.0334** | 0.010–0.040 | pass — 0.5pp of the rise is the new forborne column |

That is the test that matters for an addition made after a calibration: loss aversion is
inert in a rising market by construction, and the numbers say so.

### An engineering finding worth more than it looks

The take-up draw first shared the insolvency RNG stream. That alone — the same mechanisms,
the same parameters, a different draw order — **flipped three unrelated gates**: cap coverage
scaling, the Monràs co-movement and boom-time yield compression. Two facts follow. Giving
forbearance its own stream is not tidiness, it is what makes a mechanism's effect attributable
at all. And three gates that flip on a re-randomisation are sitting on thin margins — the
yield-compression test says so in its own docstring ("two are all but flat"), and the other
two now deserve the same warning.

### The diagnostic run, and a prediction that failed

Pre-registered in `docs/prereg/2026-09-15-brakes-diagnostic.md` at commit `9ca8bba`, and
labelled a **diagnostic**: the 2008–13 episode was spent on 14 September, and a model changed
in response to an episode is in-sample on it.

| Quantity | 14 Sep | 15 Sep | predicted | |
|---|---|---|---|---|
| Price fall | −56.9% ± 2.2 | **−59.0% ± 0.8** | smaller | **failed** |
| Arrears, peak | 2.2% | **3.5%** | higher | right |
| Foreclosure flow, peak | 1.34%/yr | 1.30%/yr | lower | right, inside noise |
| Forborne, peak | — | **0.74%** ≈ 34,000 families | > 0 | right, and the right order |

**The price prediction failed, and the honest reading is that the comparison could not have
settled it.** The two runs differ by the brakes *and* by a new RNG stream, and a 2.1pp move
against a 0.8–2.2pp seed spread attributes to nothing. What does attribute is the toggle test,
same version, brake on and off in a synthetic bust built from round numbers rather than from
the registered series:

| | loss aversion on | off |
|---|---|---|
| price, peak to trough | **−68.8%** | −72.5% |
| transactions per tick | **10.8** | 63.0 |
| sold inside the quarter | 20.5% | 42.2% |

That is Genesove & Mayer's price–volume correlation, reproduced: sellers facing losses hold
out, the fall is cushioned, and the market pays for it in volume. The mechanism works as its
source describes. What it cannot do at α = 0.30 is close a twelve-point gap on its own — and
the volume cost it imposes (−83% against the no-brake counterfactual, where Spain's own
transactions fell about 64% peak to trough) suggests the model now over-uses the margin it was
given.

### What is still missing

Two of the four brakes named in §5d.3 are still not there, and both would push the same way:
**eviction moratoria** (policy, so a lever, and Spain has had them unbroken since RDL 11/2020)
and **court congestion** (the judicial phase is a constant in the model and was a queue in the
episode — filings quadrupled, capacity did not). The CGPJ series the project carries has
filings but not pending stock, so the queue cannot be identified from registered data. The
gap is narrower than it was and it is not closed.

## Phase E — the hold-out, run once (2026-09-14)

Pre-registered in `docs/prereg/2026-09-14-holdout-2008-2013.md`, committed as
`af1b60d` **before** the run. 10 seeds, 24 ticks, 2008Q1–2013Q4, every input a registered
series, no parameter touched before or after.

| Quantity | Predicted in advance | Measured | |
|---|---|---|---|
| Price, peak to trough | −30% … −45% | **−56.9% ± 2.2** | FAIL |
| Transactions, end vs start | −40% … −85% | **+86.6% ± 16.8** | FAIL |
| Arrears, peak | 4% … 9% | **2.2% ± 0.3** | FAIL |
| Foreclosure flow, peak per year | 0.7% … 2.0% | **1.34% ± 0.24** | **PASS** |
| Bank REO stock | builds | 47 units ≈ 94,000 dwellings | **PASS** |
| Ownership rate | falls | −2.0pp | **PASS** |

Three of six. The path, seed 1, quarterly:

| | 2008Q1 | 2009Q1 | 2010Q1 | 2011Q1 | 2012Q1 | 2013Q1 | 2013Q4 |
|---|---|---|---|---|---|---|---|
| price (2008Q1 = 1) | 1.00 | 0.97 | 0.89 | 0.77 | 0.65 | 0.54 | 0.45 |
| arrears | 0.0% | 0.3% | 0.8% | 0.9% | 1.3% | 2.1% | 1.9% |
| foreclosures /yr | 0.0% | 0.3% | 0.9% | 0.3% | 0.0% | 1.3% | 0.9% |
| negative equity | 2.9% | 2.6% | 2.9% | 3.9% | 6.5% | 9.8% | 11.9% |
| vacancy | 11.7% | 13.6% | 14.9% | 16.4% | 17.6% | 18.4% | 18.3% |

### What passed, and it is the one that was predicted to fail

**The foreclosure flow.** Phases C and D both put in writing, before this run, that the model
was expected to miss it low: a calm baseline produced ≈0.02%/yr of deliveries against an
observed 0.10–0.16%, because owners with positive equity sell before the lender can take the
home, and phase D's note said the mechanism that should close the gap in a bust is negative
equity blocking that sale. It does. Negative equity spreads from 2.9% of mortgaged owners to
**11.9%**, the escape route closes, and the peak flow reaches **1.34%/yr** against the ≈1.4%
CGPJ's 93,636 filings imply. The mechanism was specified in phase C, completed in phase D and
tested here on data neither phase had seen.

Two qualifications, both against the model. The peak arrives in **2013**, three years after
Spain's; and the cumulative count is ≈154,000 deliveries over six years against the roughly
500,000 procedures CGPJ filed 2008–13, so the model reproduces the *rate at the peak* and
about a third of the *total*.

### What failed, and what each failure says

**Prices overshoot: −57% against −30…−45%.** The expectation loop that phase D added to close
finding 2 has no brake in a fall. Expected growth turns negative, the valuation anchor drops
below the index, transactions confirm the drop, and the loop runs; nothing in the model plays
the role of the nominal-rigidity floor, the seller who withdraws rather than realise a loss, or
the bank that will not foreclose into a dead market. The reserve does hold some of it — that is
what the 11.9% locked-in share is — but the price index is a transaction median, so the sales
that do clear are the distressed ones, which drags it further. The honest statement is that the
model's bust is more violent than Spain's, and by a fifth.

**Transactions: the instrument was built wrong.** The measure compared the last two years of
the window against its first, and the collapse happens *at* the start — tick 0 already carries
2007Q4's euríbor and the crunch lands in the second quarter — so what it captured is the
model's recovery as prices fall by half. Against the calm baseline the same run starts at 17
transactions per tick against 96, i.e. −82%, inside the predicted band. That comparison is a
diagnostic and not the result: the pre-registered test failed, and it failed because of how it
was written, which is recorded rather than corrected.

**Arrears under-produce: 2.2% peak against the BdE's 6.28%.** This one is informative next to
the foreclosure pass. Under the three-instalment regime of the period the model converts
arrears into deliveries in three quarters, so the *stock* of households behind on payments
never accumulates while the *flow* of possessions matches. Spain's stock accumulated because
the flow was slowed by things the model does not have: the Código de Buenas Prácticas
restructurings, the 2012–13 eviction moratoria, and a court system that took years. Their
absence was registered in phase C's referee pass as pushing arrears **up**; this run says the
opposite, and the register is wrong on the sign. Both mechanisms shorten the time a household
spends in arrears, which lowers the stock and raises the flow — the model has the second and
not the first.

### What the hold-out is evidence for, and what it is not

It is evidence that the insolvency chain works in the regime it was built for: fed nothing but
the period's rate path, joblessness, formation, completions, credit stop and foreclosure law,
the model produces a foreclosure wave of the right order at the right rate, a bank-owned
overhang, a spreading negative-equity lock-in and a falling ownership rate. None of those
existed before phase C, and the price-formation mechanism that makes the lock-in bite arrived
in phase D, after the calibration.

It is not evidence that the model can predict a bust's depth. It over-predicts the price fall
by a fifth and it gets the arrears stock wrong by a factor of three, and both failures point
at the same missing thing: nothing in this model slows a market down once it turns —
no forbearance, no moratoria, no court backlog, no seller who simply refuses.

**Nothing has been changed since this run.** Under §13.4 the episode is spent: the next time
it can be informative is against a model whose mechanisms were built without it, and that
model no longer exists.

## Phase D — sale-side price formation (2026-09-14)

The price used to be `ask × N(1, overbid_sigma)`: the ask times a guessed random number, with
56% of the variance in price-to-income on that one scalar. It is now an ascending auction over
search, with the seller's reserve carrying the mortgage. 3 seeds, 60 ticks, last 20 averaged,
unless a line says otherwise.

### Baseline, after

| Moment | Before (phase C) | After | §9 band | |
|---|---|---|---|---|
| Price-to-income | 7.04 | **7.78 ± 0.10** | 7.0–8.2 | pass |
| Purchase effort | — | **36.6% ± 0.5** | BdE 35–40% | pass |
| Gross yield, contract basis | 0.069 | **0.070 ± 0.002** | 0.065–0.075 | pass |
| Market-tenant overburden | 0.323 | **0.323 ± 0.001** | 0.26–0.34 | pass |
| Ownership rate | 0.711 | **0.715 ± 0.004** | 0.70–0.74 | pass |
| Sold inside the quarter | — | **47.7% ± 2.9** | 43–63% (idealista ≈53%) | pass |
| Bidders per listing | — | **3.59 ± 0.12** | 1 < b ≤ 7 (Tecnocasa 7) | pass |
| Negotiation margin | — | **3.0%** | 4–12% (Tecnocasa 6.2%) | **fail** |
| Sales above the ask | — | **17.3%** | Fotocasa 9% (different basis) | reported |
| Arrears, share of mortgaged | 0.029 | **0.028** | 0.010–0.040 | pass |
| Vacancy, secondary | 0.135 | **0.139** | 0.081–0.131 | fail (phase C's, unchanged) |

### The mechanism the redesign spec did not name, and the model needed

The ascending auction on its own did **not** produce a scarcity-to-price channel. With the
buyer's valuation anchored on the price index, `price ≈ index × (a selection premium in the
taste draw)`, and that premium is proportional to `overbid_sigma` — so the model swapped one
dispersion dependence for another: at σ = 0.02 competition could not move prices at all
(baseline growth +2.1%/yr, the boom leg +1.7%/yr), at σ = 0.04 σ set the level again
(price-to-income 8.4, purchase effort 38%).

What closes it is **where the expectation enters**. `MOMENTUM_GAIN × expected growth` shaded
the buyer's *budget*, and the index cap in clearing threw that away for every buyer whose
credit limit exceeded market value — which is most of them. Moved onto the *valuation anchor*
it reaches the price, and the adaptive loop of §6 runs until credit binds.

Re-identifying the gain when the channel moved (5.0 → 2.5), on calibration-window moments
only:

| gain | price-to-income | purchase effort | baseline price growth | 2021–25 boom leg |
|---|---|---|---|---|
| 0 | 6.59 | 31.1% | +2.0%/yr | +1.7%/yr |
| 1 | 6.94 | 32.7% | +2.6%/yr | +2.3%/yr |
| 2 | 7.42 | 35.0% | +3.3%/yr | +3.0%/yr |
| **2.5** | **7.78** | **36.6%** | **+3.7%/yr** | **+3.9%/yr** |
| 3 | 8.26 | 38.9% | +4.3%/yr | +4.5%/yr |
| 5 | 9.52 | 44.8% | +5.1%/yr | +8.5%/yr |

The hold-out column is shown because it is informative, **not** because it was used: the gain
was set on price-to-income and the BdE's 35–40% purchase effort, both calibration-window
objects. Setting it on the boom column would have picked 5.0 and put the baseline on a
permanent 5%/yr boom at 45% effort, which is how a model gets a good hold-out number and a
wrong world.

### Five gates closed, and by the mechanism their xfail notes predicted

Every one of these was a dated strict xfail from phase B whose recorded reason ended "it is
phase D's to close — the rent side needs the scarcity channel the sale side is getting". The
§7.1 hurdle had made the landlord's reservation rent a function of the dwelling's *value*,
and the sale side had no channel, so that floor only ever fell:

| Gate | Before | After |
|---|---|---|
| Insider/outsider wedge | −6.3% (wrong sign) | **+5.1%** |
| Rent cap on contract rents | +4.9% (wrong sign) | **−3.6%** |
| Monràs co-movement (elasticity 2) | +6.8% rents, −21.8% contracts | **−3.6% rents, −11.1% contracts** |
| Cap coverage scaling | scaled a magnet | scales a ceiling |
| Boom-time rent growth | xfail | passes |

Finding 2 of the redesign spec is closed on both sides by one change.

### Three gates broken, one of them a falsification that fired

**The rate-shock magnitude — the falsification §5c.4 wrote down in advance.** Removing
`PARTICIPATION_RATE_SENSITIVITY = 20`, a coefficient fitted so a +2.4pp rate move cut
transactions 11%, leaves the euríbor its mechanical channel only. Measured on 3 seeds, a
+2.8pp shock now cuts volume **1.6%** against the 5% the gate asserts; prices −1.1%, so the
*ordering* survives and the *magnitude* does not. The coefficient was carrying something the
mechanisms do not reproduce. It is not reinstated. What is added instead is the episode as it
happened: 2022–23 was a rate rise **and** a tightening of standards, the second documented
quarter by quarter in the BdE lending survey, and with both inputs the model gives volume
−5.5% against prices −1.5% — the right signature, from mechanisms.

**The 2021–25 boom's price leg.** +3.88%/yr ± 0.17 over 10 seeds against a 4% threshold, with
the sourced episode at +8–13%/yr. So ≈40% of the observed magnitude, about where the model
was before phase D; what changed is that the boom is now produced by expectations reaching
the price instead of by a participation coefficient fitted on a rate episode. Volume leg
passes at 1.62× (gate 1.15×) and stays a live test; the price leg is split out and xfailed.

**The negotiation margin.** 3.0% against a measured 6.2%. The model's market is more
competitive than Spain's on both identifying observables — 3.6 bids per listing, 17% of sales
above the ask against Fotocasa's 9% — and these are one fact, not two: with more bidders the
auction runs the price to the runner-up's valuation and leaves nothing to negotiate away.
Closing it means fewer buyers per listing, i.e. `buy_attempt_prob` on the demand side, an
admitted guess — not the auction this target exists to test.

### Referee pass — what a hostile economist would say

- *"You moved a coefficient and called it a mechanism."* The coefficient moved from the budget
  to the valuation, which is a modelling claim with a consequence: a budget is capacity and a
  valuation capitalises expectations, and only the second can bid a price above today's index.
  The consequence is testable and was tested — it is what closed the five rent-side gates.
- *"You re-fitted the gain to get your numbers."* On calibration-window moments, and the
  hold-out column is printed above so the choice can be checked against the alternative. The
  gain that the hold-out would have chosen (5.0) is visibly rejected.
- *"`m = 2` is not how people search."* Correct, and it is why `m` is declared reduced form.
  It is affordable listings *sampled per quarter*, not viewings; what identifies it is the
  days-on-market distribution, and 2 is what reproduces it.
- *"Your discount is half the measured one."* Conceded in the table and in the gate, which
  fails rather than being widened. The diagnosis names the demand-side parameter responsible.
- *"The price level is still a guess."* Less of one: halving `overbid_sigma` now moves
  price-to-income by under 25%, where 56% of its variance used to sit on that scalar, and
  purchase effort lands inside the BdE's observed 35–40%. Whether σ is under the variance
  rule's 25% threshold is phase E's Sobol run, and it is reported either way.

## Phase C — insolvency and forced sale (2026-09-14)

The budget constraint binds from this pass. `engine._household_flows` used to write
`wealth = max(0, wealth − payment)`: non-payment was absorbed, nothing defaulted, and no
dwelling ever returned to the market against its owner's will. Everything below is measured
on 5 seeds, 60 ticks, last 20 averaged, unless a line says otherwise.

### Baseline, after

| Moment | Before (main) | After | §9 band | |
|---|---|---|---|---|
| Price-to-income | 7.49 | **7.11 ± 0.18** | 7.0–8.2 | pass |
| Market-tenant overburden | 0.338 | **0.323 ± 0.010** | 0.26–0.34 | pass |
| Gross yield, contract basis | 0.070 | **0.069 ± 0.001** | 0.065–0.075 | pass |
| Ownership rate | 0.712 | **0.711 ± 0.002** | 0.70–0.74 | pass |
| Vacancy, national | 0.126 | **0.129 ± 0.004** | 0.10–0.15 | pass |
| Vacancy, secondary | 0.131 | **0.135 ± 0.006** | 0.081–0.131 | **fail** |
| Unemployment (households, all actives) | — | **0.0529 ± 0.0002** | input 0.0528 | tracks |
| Arrears, share of mortgaged | — | **0.0291 ± 0.0022** | 0.010–0.040 | pass |
| Foreclosure rate, /yr | — | **0.0001** | 0.0010–0.0080 | **fail** |

### The two failures, and why neither is closed by tuning

**Foreclosure flow, ≈0.01–0.02%/yr against an observed 0.10–0.16%/yr in calm years.** The
model converts almost every statutory trigger into a voluntary sale: a distressed owner with
positive equity lists, and in a market with rising prices the listing clears inside its
window. What stops that in Spain is negative equity after a price fall, the discount an
occupied dwelling carries, and the months a sale takes — the first two are phase D's price
formation (spec §7.7) and the third is the bust itself. Lowering the band would be fitting
the target to the model; the band is the data, and the gate is a dated strict xfail.

**Secondary-zone vacancy, 13.5% against a Censo band topping out at 13.1%.** It sat at
13.10% — the boundary — before this pass. The 0.3pp it moved is **market** vacancy (6.68%
against 6.38%), not withheld stock: forced supply arrives while the credit lockout removes
some of the buyers for it, so units spend longer empty. The ladder, the rural band and the
national band all still hold, so only this leg is split out into its own xfailing test.

### Three defects the new mechanism exposed

1. **The opening mortgage book was never screened.** Initial balances were drawn as
   `60,900 × lognormal(0, 0.5)` independently of income, so a household with a €15k income
   could start the run owing €150k on a five-year tail — a payment of twice its income.
   Invisible while non-payment was absorbed; with the constraint binding, those households
   were in arrears on tick 1 and their forced listings moved the price level (price-to-income
   6.93 against main's 7.49). The book now passes the same DSTI screen the bank applies to
   every new loan, which is what it should always have done.
2. **The income distribution was double-counting unemployment.** `income_median` is an
   EFF/ECV measurement over a population that already contains unemployed households, so
   drawing potential income at that median and then applying an unemployment path subtracted
   the same loss twice — the realised distribution came out 3.0% (mean) and 3.6% (median)
   below the model's own calibration target. `insolvency.potential_income_uplift` corrects it
   analytically (1.034 at the baseline) rather than by fitting.
3. **Distressed listing on the first missed instalment was wrong and the data said so.**
   It put ≈28 forced listings in a calm market at all times, moved the price level 9% and
   pushed price-to-income to 6.99. Most arrears spells cure — the exit hazard ends half of
   them inside three quarters — and a household that expects to cure does not sell. The
   trigger is now the **statutory** threat: the lender has demanded payment and warned of
   early termination (Ley 5/2019 art. 24.1.c). The ask is the ordinary seller's; only the
   reserve differs, and it is the debt.

### The bust leg, as a direction check (not the hold-out)

`LabourShock(0.15, exit 0.15)` + `CreditCrunch(−0.15 LTV, −0.07 DSTI, +2pp spread)` from
tick 20, 3 seeds — the 2013 household-joblessness peak with a credit stop, but **not** the
2008–13 hold-out, which is run once in phase E and is not touched here:

| | calm | bust |
|---|---|---|
| Price-to-income | 7.11 | **5.46** |
| Arrears | 2.9% | **3.6%** |
| Foreclosure rate /yr | 0.01% | **0.09%** |
| Ownership rate | 0.711 | **0.697** |
| Vacancy, national | 0.129 | **0.140** |

Directions are right and the magnitudes are not claimed: foreclosures rise nine-fold and
still land an order of magnitude below the 0.7%/yr the BdE measured in 2014, for the reason
given above. That is the gap phase D and phase E have to close, and it is on the record
before either is run.

### Referee pass — what a hostile economist would say

- *"You chose the unemployment series that flatters you."* The opposite: the household-level
  series (all actives unemployed, 5.28% now, 15.02% at the 2013 peak) is roughly half the
  individual rate, and using the individual rate put arrears at 6.9% against a BdE doubtful
  ratio of 1.6–3.4%. The choice is forced by the model's household being a single income
  unit, and it is the conservative one for every headline this block produces.
- *"Your household has one earner, so job loss is catastrophic."* Conceded, and it cuts both
  ways: severity is overstated, frequency understated (two earners are two chances of a hit).
  The EFF earner-count distribution would settle it and is not retrieved.
- *"The judicial lag is a guess."* It is, and it is the only guessed element in the chain:
  CGPJ publishes 8.5 months for all first-instance civil matters, which bounds it below, and
  the 2–4 year estimate is practitioner-side. It is swept, never reported as a magnitude.
- *"There is no forbearance."* True. The Código de Buenas Prácticas (RDL 6/2012, and the
  2022–23 vulnerable-debtor codes) restructured a material share of distressed mortgages and
  is not modelled. Its absence pushes arrears **up** and the model still sits inside the BdE
  band, so the direction of the omission is stated rather than hidden.
- *"REO is a free parameter."* The discount and release rate are the block's weakest values
  and are labelled reduced form; the registered Sareb haircuts are against book value, not
  market price. The bank's *acquisition* price is not free: it is the statutory 70% of
  auction value (LEC art. 670.4). Phase E's Sobol run decides whether anything reportable
  depends on the discount.

## Config guards — not validation targets (moved 2026-09-12)

Two rows used to sit in the table above with a ✓: the zone-weighted national supply elasticity
(0.49 against a sourced 0.45–0.58) and the zone dwellings-per-household weight to its national
anchor (1.13 against 1.12 ± 0.01). Neither runs an engine. Both construct `SimConfig.baseline()`
and assert that config fields agree with the config anchors they were derived from.

That is a real check and it is kept, unweakened, in `tests/test_config_guards.py`. It is not
evidence that the model reproduces Spain, which is what this table is for, and counted among
the passing targets it inflated the count with arithmetic the model cannot fail at runtime.
Spec §2, finding 8: *"two target rows are config identities"*. Phase A, `model-bug-fixes`.

## Phase-0 targets (2026-09-11)

Seven observable moments added by the redesign's phase 0
(`docs/superpowers/specs/2026-09-11-model-redesign-design.md` §6). Several are red on
arrival — that is their purpose: they make defects that were invisible into failures the
suite reports. Reporting categories follow `model-spec.md §13.1`.

| # | Target | Empirical range | Model | Status |
|---|---|---|---|---|
| 9 | Zone gross-yield ladder, emergent | T 4.7–5.6 / S 6.5–7.5 / R 7–9% (idealista + BdE RBA) | T 5.1 / S 6.6 / R 17.2% | ✗ **strict xfail** — rural ≈2× the band; phase B |
| 10 | Boom compresses the gross yield | direction only. `sources.md` registers an idealista **cross-section** (Q4-2025/Q1-2026: Spain 6.7%, Madrid 4.7%, Barcelona 5.6%, capitals to 7.5%); a band on the *compression* needs the 2014–25 **time series**, which is not registered | 5.39% → 5.21% (5 seeds × 40 ticks, hold-out boom — not the table's 3-seed tail-mean basis). Per-seed: −29.6 / −22.2 / −1.5 / −2.9 / −34.8 bp — all compress, two are all but flat | ✓ **pass** — live gate, thin margin (0.18pp, no seed band); phase B should revisit whether it needs one |
| 11 | Rent level ordering T > S > R | strict, at every published basis | False; R +13.5% over T (tail mean) | ✗ **strict xfail** — rural overtakes the metro around tick 35–40; phase B |
| 12 | Net internal migration into TENSIONED > 0 | direction only (INE Migraciones not yet sourced) | −433.67 (cumulative sum over the run, not a tail mean; seeds −424 / −432 / −445) | ✗ **strict xfail** — the rule is downward-only; phase B |
| 13 | Time to sell (`median_ticks_to_sale`) | idealista days on market — **to verify** | 0.0 ticks | reported, not gated; phase D gates it |
| 14 | Landlord households (`landlord_household_share`), **EFF basis** — owns a dwelling it does not live in | A **bracket**, not a band: EFF 36.1% of households own other real estate (2022 wave), revised to 45.3% in the register's most recent wave (2024, DO 2610) — the *ownership* basis, which is what the column measures — against AEAT's 2.37M landlord declarants over the 19.87M household anchor (`model-spec §7`) ≈ **11.9%**, a *declaring-rental-income* basis. Both waves registered in `docs/sources.md`; what is missing is the EFF **wealth-percentile gradient** (redesign spec §9 retrieval list) | 27.1% — between the two ends | reported, not gated. Two bases roughly three-to-four-fold apart bracket the column, they do not band it; which end the gate is set against is a phase-B decision, and depends on the AEAT-basis sibling column described below |
| 15 | Foreclosure flow | CGPJ — **to verify** | not measurable | deferred to phase C: no insolvency mechanism exists, so no test is written. Registered in `docs/holdout-2008-2013.md` |

Two of these are the same defect seen from different sides: the rural rent level (11) and the
rural yield (9). The zone ladder was gated on prices only, so a rural asking rent above the
metro index survived 60 ticks and 3 seeds unnoticed.

These seven targets are also on screen, in the app's **🔬 Diagnóstico del modelo** tab
(`src/resim/ui/app.py::diagnostics_tab`, criteria in `src/resim/diagnostics.py`). That panel
is display-only and gates nothing; the bands it shows are copied from the assertions in
`tests/test_validation.py`, and `tests/test_diagnostics.py` fails if the two drift apart. It
evaluates whatever seed the sidebar is set to, not the 3-seed tail-mean basis this table is
quoted on, so a row can read ✅ there while the target stays a registered xfail — the panel
carries both columns and says which one is authoritative.

Target 15 is deliberately **not** written as a test. A test that cannot run is not evidence of
anything, and an xfail on a missing mechanism would be decoration.

**Target 14 measures ownership, not letting.** `landlord_household_share` counts any household
owning a unit it does not live in, so vacant second homes, withheld stock, seasonal units and
the inherited-but-vacant dwellings the assumption register flags as an ownership leak all count.
That is the EFF "owns other real estate" basis, and it is not the basis of the AEAT end of the
bracket. Phase B needs a **sibling column restricted to `Tenure.RENTED` units** — the AEAT
basis, and the one buy-to-let entry should actually be judged on. It is not added here: phase 0
adds no mechanism, and specifying that measurement is phase B's job.

Two corrections to what was previously written about this column. Its anchors are **not**
unregistered — EFF 36.1% and the AEAT declarant counts are both rows in `docs/sources.md`; the
figure the redesign spec's retrieval list is still missing is the EFF wealth-percentile
gradient. And the share does **not** "only fall over a run": measured 0.27116 at tick 1 against
0.27097 at tick 60 (3-seed mean, a 0.02pp move), and rising on roughly half the tick
transitions. The claim does not hold analytically either, because the dissolution rule hands
whole estates to surviving households, which creates landlord households as readily as the
absence of a buy-to-let margin retires them.

**Target 1's ranking leg is now measured.** `model-spec §9` target 1 has a "tenant share
ranking T > S > R" leg that the validation fixture carried as a hardcoded `True`, with a comment
claiming it was checked via rent levels — it was not, by that test or any other, so the leg was
unmeasured. Measured on the new `tenant_share_*` columns, 3 seeds, last 20 of 60 ticks:
**31.4 / 22.7 / 17.0%**, ranking correctly on every seed separately (seed 1: 31.1 / 22.5 / 17.2;
seed 2: 31.7 / 22.9 / 17.7; seed 3: 31.6 / 22.8 / 16.1). Now gated, on the ranking only: the
tensioned leg runs above the 0.27–0.30 band in `model-spec §7`, which is the same
zone-aggregation qualification that target 2d carries — a tensioned zone holding 45% of
households is not Madrid.

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

## Sensitivity analysis (2026-09-08) — Morris screening

`plan.md` Phase 6 has required Morris screening and Sobol indices since the model was built;
only a light one-at-a-time pass had ever been run, and the report above still marked it
"Stale. Re-run before citing." This is the real thing. `src/resim/sensitivity.py` implements it and the numbers below are reproducible from it:
`uv run python -m resim.sensitivity morris --trajectories 10`.

**Design.** 22 free and `guess` parameters at their documented ranges (sourced point values —
LTV, DSTI, construction lag — are not uncertainty the model owns, so they are excluded).
Morris elementary effects, 10 trajectories × 23 points = **230 evaluations**, 4 levels,
Δ = 2/3, 40 ticks, via `python -m resim.sensitivity morris`. **Common random numbers**: one fixed seed across the whole design, so an
elementary effect measures the parameter and not the seed. Ten outputs: the §9 moments plus
the price-to-income ordering margin, the tensioned/rural ratio, rent level, market vacancy and
cash share. μ\* is the mean absolute effect, σ its spread across trajectories (interaction or
non-linearity).

**What matters.** Ranked by each parameter's largest μ\* across the ten moments, normalised
so the strongest parameter for each moment scores 1.0:

| Parameter | Score | Confidence in the model | Largest single effect |
|---|---|---|---|
| `overbid_sigma` | 1.00 | **guess** | price-to-income (μ\* 1.03) |
| `landlord_required_spread` | 1.00 | **guess** | rent level (μ\* €218), overburden |
| `base_starts_per_tick` | 1.00 | sourced (MIVAU) | completions/formation (μ\* 0.147) |
| `premium_secondary` | 1.00 | calibrated | cash share, price-to-income |
| `premium_rural` | 1.00 | calibrated | **T/R ratio (μ\* 0.74), ordering margin (0.87)** |
| `default_rate` | 0.99 | medium (Arag/OESA) | rent level, via the risk markup |
| `congestion_gain` | 0.97 | **guess** | rent level (μ\* €211) |
| `landlord_zone_risk_premium` | 0.81 | medium | overburden, ordering margin |
| `buy_attempt_prob` | 0.78 | guess, calibrated | price-to-income (μ\* 0.80) |
| `formation_metro_weight` | 0.78 | guess (level) | market vacancy, rent level |
| … | | | |
| `margin_threshold` | 0.06 | medium | — |
| `hazard_scale` | **0.00** | calibrated | — |
| `max_starts_per_tick` | **0.00** | **low (CNC claim)** | — |
| `presale_share` | **0.00** | high | — |

**Three findings worth acting on.**

1. **The model's most influential parameters are its least sourced.** `overbid_sigma` and
   `landlord_required_spread` are both labelled `guess`, and they top the ranking — the first
   drives price-to-income, the second the rent level and the overburden share. The
   sensitivity screen the plan asked for exists to point exactly here, and it points at the
   two parameters with no source behind them. They are the priority for the next evidence
   pass, ahead of anything currently better documented.
2. **The weakest-sourced parameter in the model does not matter.** `max_starts_per_tick` is a
   CNC industry claim labelled low confidence, and its μ\* is **zero on every moment**: the
   capacity ceiling never binds in the baseline, because starts are gated by demand and by the
   margin hurdle long before capacity. The same holds for `presale_share` (sourced high, but
   inert) and nearly for `margin_threshold`. That is a real result: three parameters can be
   left alone, and one flagged weakness is harmless.
3. **`hazard_scale` scores zero, and that is the harness working.** It only acts when a rent
   cap is in force, and the screen is run on the baseline, which has none. Cap-only parameters
   are correctly invisible here; their sensitivity is the elasticity sweep in
   `experiments/rent-cap.md`, which is a separate exercise. Read this table as *baseline*
   sensitivity only.

The location premium's two parameters rank at the top for the ordering margin and the T/R
ratio, which is what §5b claims they do — the screen confirms the mechanism is load-bearing
rather than decorative, and equally that the ladder now rests on a calibrated guess (already
stated as a limitation in `model-spec` §10).

### Sobol indices on the seven survivors

**Design.** Saltelli first-order (S1) and total-order (ST) indices, N = 128, seven parameters,
**1,152 evaluations**, same fixed seed and 40 ticks. Sampling is plain uniform: a Sobol'
sequence would need scipy, which this project does not carry, and the estimators are unbiased
either way — only slower to converge. Parameters outside the seven sit at their midpoint, so
these are shares of the variance *this subset* generates.

Two estimator notes, because the first attempt got them wrong. The Saltelli S1 estimator must
be applied to **centred** outputs: uncentred it returned S1 of +22 and +33 for ownership, whose
mean (0.70) dwarfs its spread (0.004), where a first-order index must lie in [0, 1]. And a
moment that barely moves has no variance to decompose, so anything under a 1% coefficient of
variation is now reported as flat rather than given spurious indices. Raw evaluations are
cached in the output file so indices can be re-estimated without re-running the model.

| Moment | CV | Dominant parameter | S1 | ST | Runner-up |
|---|---|---|---|---|---|
| price-to-income | 0.05 | **`overbid_sigma`** (guess) | 0.56 | 0.63 | `landlord_required_spread` 0.11 |
| P/I ordering margin | 0.20 | `premium_rural` | 0.74 | 0.86 | `premium_secondary` 0.25 |
| ownership | 0.005 | — flat, not decomposed — | | | |
| transactions | 0.03 | `base_starts_per_tick` (sourced) | 0.60 | 0.72 | interactions dominate the rest |
| completions / formation | 0.18 | `base_starts_per_tick` (sourced) | 0.72 | 0.92 | `premium_rural` 0.07 |
| market-tenant overburden | 0.04 | **`landlord_required_spread`** (guess) | 0.65 | 0.86 | `overbid_sigma` 0.07 |
| T/R price ratio | 0.08 | `premium_rural` | 0.88 | 1.14 | `overbid_sigma` −0.01 |
| rent level | 0.09 | **`landlord_required_spread`** (guess) | 0.40 | 0.55 | `congestion_gain` 0.24 |
| market vacancy, tensioned | 0.24 | **`landlord_required_spread`** (guess) | 0.74 | 0.86 | `overbid_sigma` 0.13 |
| cash purchases | 0.13 | `premium_rural` | 0.30 | 0.63 | `premium_secondary` 0.19 |

**What the decomposition adds to the screening.**

1. **The Morris finding is not a ranking artefact, it is a variance share.** Two parameters
   labelled `guess` are *first-order dominant* — not merely influential — for four of the nine
   decomposable moments: `overbid_sigma` explains **56%** of the variance in price-to-income,
   and `landlord_required_spread` **65%** of market-tenant overburden, **74%** of tensioned
   market vacancy and **40%** of the rent level. Three of those four are §9 validation targets.
   The model's calibration rests on two numbers nobody sourced, and that is now quantified
   rather than suspected. It is the single most useful thing this analysis produced.
2. **The location premium does exactly its job and nothing else.** `premium_rural` owns the
   ordering margin (0.74) and the T/R ratio (0.88) — the two things §5b exists to fix — and is
   a minor term everywhere else except cash purchases, which is the cross-validation reported
   in L4 showing up again from the other direction. A mechanism that dominated moments it was
   not introduced for would be a warning; this one does not.
3. **A sourced parameter owns the supply moments**, which is the healthy case:
   `base_starts_per_tick` (MIVAU) explains 72% of completions/formation and 60% of
   transactions.
4. **Ownership is flat** (CV 0.005): robust to all seven parameters at their full ranges. It
   sits at the bottom edge of its band for structural reasons, not because a knob is holding
   it there.
5. **The model is close to additive in these parameters.** For every dominant term the ST − S1
   gap is 0.07–0.21, so there is no hidden interaction structure to hunt. The exception is
   `transactions`, where S1 is small for six of seven parameters but ST is 0.24–0.36 across the
   board — transaction volume is where the parameters interact, which fits its position
   downstream of credit, prices and supply all at once.

**Caveats.** `price_ratio_tr` returns ST = 1.14 for `premium_rural`, slightly above the
theoretical maximum: estimator noise at N = 128 with uniform sampling when one parameter
dominates. Indices are shares of the variance the seven screened parameters generate, not of
the model's total variance, and the design is the **baseline** — cap-only parameters are
absent by construction, and their sensitivity is `experiments/rent-cap.md`.

## Shadow-anchor and boom-rent revision (2026-09-08)

Closes the last two open items: the shadow rent's composition-sensitive anchor (limitation L6)
and the boom-time rent-growth target (§9.7r), the model's oldest failing target. **After this
revision the suite carries no xfails: every §9 target is met.**

**S1 — three anchors, two rejected on measurement.** The shadow rent is what a unit would
fetch with no cap; under a cap the asking index *is* the cap, so it cannot serve. The anchor
question is what to grow the last free observation by.

| Anchor | Behaviour under a 60-tick cap | Verdict |
|---|---|---|
| Median renter paying capacity | Grows ≈1.5%/yr against a 3.2%/yr free-market rent, because the non-owner pool is refreshed with poorer households (median non-owner income grows just 0.2%/yr, formation income factor 0.9). Gap to the IRAV reference closes; cap fades after ~10 ticks | rejected — too weak |
| The untreated zones' rent index (the studies' own treated-vs-control identification) | **Explosive.** Cap displaces demand into the controls, their rents rise, that lifts the shadow, which widens the gap and drives more exits. Over 80 ticks the gap reached **+122%**, tensioned lettings fell 89 → 10 per tick and secondary rents ran 824 → 1,534 | rejected — contaminated by the effect it measures |
| **Level from the last free observation, growth from the exogenous income anchor** (`long_run_growth`, 2%/yr) | Gap widens 0.5pp/yr — exactly the income-versus-IRAV wedge — reaching +9.5% at tick 76; lettings decline gradually 89 → 32 over 14 years | **kept** |

The kept anchor is deliberately dumb. Only the growth rate is assumed; the level is observed.
It is immune to feedback from the cap by construction, and its economics are the right ones: a
reference index indexed below wage growth makes a cap gradually *more* binding, which is what
IRAV does in Spain. The cost is that it ignores the cycle — in a boom the true counterfactual
would rise faster and the model understates the cap's bite. **Verification that it changes
nothing else:** with no cap the shadow equals the asking index, so the baseline is
byte-identical to the previous revision's, which was checked moment by moment.

**S2 — the same bug, found a second time, in the growth wedge.** The exit hazard's
`growth_wedge` compared `4 × expected_rent_growth` to IRAV. But `expected_rent_growth` is an
expectation formed on *capped* asks — the identical category error as reading the level off the
capped index — and worse, it clamped to zero exactly when capped asks were falling, i.e. when
the cap was biting hardest. It now reads the shadow's own growth rate (`ZoneState.shadow_growth`:
the zone's expectation while free, the income anchor while capped).

**S3 — hazard scale re-fitted, and the studies now span inside the dial.** Fixing S2 made every
gap larger and never zero, so the response became far too strong (elasticity 2 → contracts
−59% at the old `HAZARD_SCALE` 3.0). Re-swept on 3 seeds, then confirmed on 5:

| `HAZARD_SCALE` | ε=0 rents / contracts | ε=1 | ε=2 |
|---|---|---|---|
| 3.0 | −4.9% / −0.7% | −4.4% / −30% | −4.2% / −59% |
| 1.0 | −4.9% / −0.7% | −4.4% / −7.5% | −4.4% / −15.3% |
| **0.7** | −4.9% / −0.7% | −4.4% / −4.8% | −4.4% / **−14.0%** |
| 0.5 | −4.9% / −0.7% | −5.3% / 0.0% | −4.4% / −7.5% |

Five-seed sweep at 0.7 — the table the experiment note now carries:

| elasticity | Δ contract rents | Δ new tenancies | seasonal gained | Δ sale prices |
|---|---|---|---|---|
| 0.0 | −4.9% ± 1.4 | +0.9% ± 3.3 | 0 | −4.2% |
| 0.5 | −4.5% ± 1.8 | −1.7% ± 3.3 | +5.8 | −4.8% |
| 1.0 | −4.3% ± 1.8 | −5.2% ± 1.8 | +12.3 | −5.2% |
| 1.5 | −4.2% ± 1.9 | −8.7% ± 3.4 | +18.9 | −5.7% |
| 2.0 | −4.2% ± 1.9 | **−13.6% ± 2.8** | +24.0 | −5.8% |

All three studies now sit **inside** the 0–2 dial: Jofre-Monseny at 0, Monràs & García-Montalvo
(−10%) between 1.5 and 2, and Pérez García (−13%) at 2 — where the previous fit needed ≈2.7 and
was documented as out of range. Rents stay at −4.2…−4.9% throughout, the studies' −4…−6%.

**S4 — boom-time rent growth: the structural claim was wrong.** §9.7r had failed since the
model was built, on the reading that it was structural — "the clearing rent equals the winning
applicant's willingness to pay, which is a share of income, so the rent index cannot outrun
income". Re-measured on the same hold-out episode and the same 10 seeds after the tightness
recalibration and the location premium: **+3.6%/yr ± 0.8, with all 10 seeds positive**, against
+0.0% ± 0.3pp before. Median non-owner income grows 0.6%/yr in that episode, so rents outrun
income by ≈3pp/yr. The channel was always there — queue congestion pushing asks above the
income anchor — but it was inert while the tensioned market ran slack at 0.5 applicants per
listing. Nothing about the rent mechanism was changed to achieve this. The target is now a
passing test asserted at +2.5%/yr, four standard errors below the mean.

It reaches roughly 40% of the sourced +8–11%/yr, and the rest is a missing size and quality
margin, which stays in `model-spec` §10.

**S5 — and a guess left alone on purpose.** The congestion coefficient was extracted as a named
parameter (`CONGESTION_GAIN`) and swept, since it is the only channel by which scarcity rather
than income reaches the asking index: 0.05 → +3.6%/yr, 0.15 → +4.9%, 0.25 → +6.9% (σ 4.9pp),
0.40 → non-monotone. **Left at 0.05.** Raising it to 0.15 would buy 1.3pp of boom rent growth
and cost a 22% higher baseline rent level — €1,352 → €1,648 against an EPF €516, on the
diagnostic that was already the model's worst — plus a rent-cap supply response falling from
−13.6% to −7.4% at elasticity 2, no longer reaching Monràs. The target it would have been
bought for is already met without it. Recorded rather than tuned; the sweep is the evidence
that the choice was made on measurement.

## Location-premium revision (2026-09-08)

Closes the model's oldest known gap: the zone price ladder. Mechanism specified in
`model-spec` §5b before it was coded, per the engineering standard.

**L1 — the recorded diagnosis was wrong, and the wrong diagnosis ruled out the fix.** Every
earlier draft said relative zone prices "converge on relative credit ceilings, i.e. relative
incomes". Measured, that is not what happens: the median non-owner's credit limit runs at
0.19–0.47 of the tensioned price and 0.58–0.69 of the rural price for the whole run, so the
median household can buy nothing anywhere and prices are set by the upper tail. What actually
drives the collapse is that **rural demand has no ceiling of its own**. Rural starts at
€85,000 against a €97,200 hard cost — below replacement, so no developer builds there; its
capacity is capped at 4.8 starts a tick against 4.9 households formed; and migration is
downward-only, so every household priced out of a metro is added to rural demand with no
counterflow. Rural prices climb to **twice replacement cost** (€85k → €198k, +133%, P/I 4.1 →
8.4) while tensioned rises 34%, and the ladder closes from below. This matters beyond
book-keeping: the old diagnosis implied a willingness-to-pay term could not work, since
willingness is clipped by the credit screen. It cannot work *upward*. It works downward.

**L2 — the premium is a discount on the low-amenity zones.** `ZoneConfig.location_premium`
multiplies purchase willingness, normalised to 1.0 in TENSIONED. A bonus on the metro would be
inert — bids are clipped at the bank limit, so a household told to pay more pays its ceiling.
A discount binds on willingness rather than ability: a rural household that could borrow €137k
does not offer it for a rural dwelling. Screened S ∈ {0.7, 0.8, 0.85, 0.9, 1.0} × R ∈ {0.4,
0.45, 0.5, 0.55, 0.7, 1.0}, first on 1 seed then on 3 against every §9 gate:

| S | R | T/R (from 3.21) | T/S | P/I T / S / R | P/I national | gates failing |
|---|---|---|---|---|---|---|
| 1.00 | 1.00 (none) | 1.90 | 1.48 | 8.4 / 6.7 / **7.4** | 7.74 | P/I ordering |
| 0.90 | 0.50 | 2.69 | 1.55 | 8.3 / 6.4 / 5.2 | 7.26 | none |
| **0.85** | **0.45** | **2.99** | **1.64** | **8.5 / 6.3 / 4.8** | **7.26** | **none** |
| 0.85 | 0.40 | 3.09 | 1.60 | 8.3 / 6.3 / 4.5 | 7.10 | none |
| 0.80 | 0.40 | 3.14 | 1.62 | 8.2 / 6.1 / 4.4 | 7.02 | ownership |

**0.85 / 0.45** chosen: the widest P/I ordering margin among the pairs that hold the ladder,
with national P/I and purchase effort closest to their published values. Calibration target is
the *price* gradient, not the wage gradient — Tinsa 2026Q1 provincial €/m² Madrid €3,565 and
Barcelona €2,772 against Ciudad Real €776 and Zamora €881. The model lands at 2.99 rather than
that 3.5–4.5 because its zones are broad aggregates: a tensioned zone holding 45% of households
is not Madrid province, and the provincial figures are the extremes of a distribution the model
represents by three means. What the premium has to do is stop the ladder decaying, and it does.

**L3 — baseline moments, 5 seeds, last 20 of 60 ticks** (previous value in brackets):

| Moment | Now | Before | Gate |
|---|---|---|---|
| T/R price ratio, tick 60 | **2.87** | 1.80 | initial 3.21 |
| P/I tensioned / secondary / rural | **8.35 / 6.24 / 4.78** | 8.30 / 6.82 / 7.20 | ordering required |
| P/I national | 7.15 | 7.70 | 7.0–8.2 ✓ |
| Ownership | 69.3% | 70.0% | 69–75 ✓ (at the floor) |
| Transactions /yr | 3.6% | 3.7% | 2.6–3.8 ✓ |
| Completions / formation | 51% | 57% | 40–70 ✓ |
| Market-tenant overburden | 28.2% | 29.5% | 26–34 ✓ |
| Insider/outsider wedge | +12.0% | +8.6% | >0 ✓ |
| Vacancy T / S / R | 8.7 / 11.8 / 18.1% | 8.7 / 12.5 / 17.8% | ladder ✓ |
| Market vacancy tensioned | 3.1% | 2.9% | 2–10 ✓ |
| **Cash purchases** | **18.7%** | 3.1% | 23–46 (still below) |
| Purchase effort | 33.7% | 36.3% | 35–40 ✗ below |

Every §9 gate holds and the two strict xfails on the ladder are now ordinary passing tests
(`test_price_to_income_ordering`, plus a new `test_zone_price_ladder_holds`).

**L4 — an unplanned cross-validation, and an honest cost.** Cash purchases went **3.1% →
18.7%** against a 23–46% target, without anything in the change touching wealth, credit or the
cash rule. Discounted willingness simply brings more purchases within reach of the buyer's own
savings. That a mechanism introduced for the price ladder independently moves an unrelated
failing diagnostic two-thirds of the way to its band is the strongest evidence available that
the premium is capturing something real rather than fitting one moment. The cost is on the
other side of the same coin: the national price index falls, so purchase effort drops to 33.7%
against BdE's 35–40% and ownership sits at 69.3%, below the EFF band's own 70% floor (the §9
gate has 1pp of tolerance and still passes). Both are reported "below" in the official
contrast. They are the price of a correct *relative* structure and should not be tuned away by
re-inflating the metro, which the credit screen makes impossible anyway.

**L5 — the rent cap still spans the studies, a little more tightly.** Re-measured on the new
baseline (3 seeds): elasticity 0 → contract rents −4.5%, contracts −1.0%; elasticity 2 → rents
−3.2%, contracts −8.0%. Still Jofre-Monseny at one end and Monràs at the other, and
`test_rent_cap_supply_response_spans_monras` (≤ −5%) passes, but the supply response is weaker
than the −11.6% measured before the premium, because a cheaper rural zone gives withdrawing
landlords a better outside option.

**L6 — limitation found while testing: a long cap gradually unbinds.** The shadow rent tracks
median renter paying capacity, which under a cap grows at ≈0.2%/yr rather than the 2% income
anchor, because the cap changes *who* is renting (composition), while the frozen reference
index is indexed at IRAV 1.5%/yr. The reference therefore overtakes the shadow about ten ticks
after activation and the cap stops binding. Within the 16-tick window the studies cover — and
the window every result above is measured on — the cap binds throughout. **Do not run cap
scenarios much beyond 40 ticks post-activation without re-checking that the cap still binds.**
A composition-robust anchor is the fix and is not attempted here.

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

Both strict xfails stood at this point in the sequence (zone price ladder; boom-time rent growth —
re-checked
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

**T7 — partial coverage: the pooled rent is a composition artefact, the segments are not.**
With `coverage` 0.42 (Spain's 317 declared municipalities mapped onto the model's tensioned
zone) the *pooled* new-contract rent comes out **+8.5% ± 9.6** above baseline at elasticity 2,
while contracts fall −11%. That reading is an artefact, and the fix was to stop pooling.
Coverage is now a persistent property of each unit (`Unit.declaration_draw`, drawn once at
creation, so a municipality keeps its status for the whole run and raising coverage *adds*
municipalities instead of reshuffling them), and `metrics.py` reports new contracts split by
segment. Measured on 5 seeds, each against a same-seed baseline split on the same line:

| coverage | ε | declared rents | free rents | pooled rents | declared contracts | free contracts | pooled contracts |
|---|---|---|---|---|---|---|---|
| 0.42 | 1 | **−2.3% ± 2.4** | +0.5% ± 3.9 | +0.4% | −12.0% | +8.9% | 0.0% |
| 0.42 | 2 | **+0.4% ± 3.8** | +8.5% ± 9.6 | +8.5% | −37.4% | +7.1% | −11.2% |
| 0.70 | 1 | −2.9% ± 2.6 | −2.3% ± 1.8 | −2.9% | −1.4% | +12.5% | +2.9% |
| 0.70 | 2 | −2.2% ± 2.3 | −1.2% ± 1.3 | −1.8% | −6.8% | +8.3% | −2.3% |

Read across the top two rows: the cap holds the declared segment flat to −2.3% and takes 12%
to 37% of its contracts out, while the non-declared segment signs 7–9% more contracts at
rents up to 8.5% higher. That is Catalonia's own signature — **tensioned rents +1.6% against
non-tensioned +9.4% in 2025** (Incasòl) — reproduced from nothing but a shared queue and
priced-out demand, and it is invisible in the pooled series, which simply follows whichever
segment is signing the contracts. At coverage 0.70 the free segment is too small to absorb the
displacement and both segments fall together, so the pooled number becomes honest again.

Two caveats on the table. The declared segment's **+0.4% at elasticity 2** is itself a
composition effect one level down: 37% of its contracts are gone, and the units still letting
are the ones worth letting under the cap. And the free segment's dispersion (± 9.6pp) is wide
because it is a small median under heavy displacement. Report coverage < 1 by segment, with
contract counts alongside — never the pooled rent alone. Pinned by
`test_partial_coverage_pushes_demand_into_the_free_segment`. (The earlier R4 figure, −1.4% at
coverage 0.42, was measured with the old hazard and the blind exit rule and is superseded.)

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
random stream and nothing structural. The §9 table stood as it was at that date; both strict xfails
stood. (Both were closed later the same day — see the two revisions above and the current table.)

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

- **G1's ceiling was the central IV estimate, not the top of the reported range — corrected on
  source grounds, and the gate still fails (2026-09-17).** G1 asserted the Δln co-movement inside
  "Monràs's 0.07–2.0 OLS-to-IV span". Read at the source (CEPR DP20018, Feb 2025, §4.2.1), 2.0 is
  the point estimate of the paper's **baseline** IV specification: *"In the baseline specification
  with the full sample, a decrease of 1% in rental prices implies a decrease of around 2% in the
  supply of rental housing"*, and then *"In Columns 4 to 6... removing the lockdown period... Point
  estimates are, if anything, slightly larger than in the full sample, **reaching an estimate of
  approximately three**."* `docs/sources.md` had already recorded the IV range as **1.6–3.2 across
  specifications**; the test used the centre as its ceiling. **Corrected to 3.2.**

  **The correction does not rescue the gate**, which is what licenses making it: the model reads
  **3.655**, still above 3.2. Had it rescued G1 it would have been fitting a band to a model.

  **Disclosed, because it decides the verdict**: the superseded working-paper edition (FRBSF WP
  2023-28) reports a supply elasticity of ≈2–4, under which the model's 3.655 would **pass**. The
  Feb 2025 edition is current and is the one `docs/sources.md` marks verified, so its 3.2 binds.
  The earlier figure is named rather than quietly unused.

  **What this changes about the size of the failure.** The limits register written earlier the same
  day described the quantity leg as overshooting by a large multiple, against a −10% figure. Both
  halves were wrong. The paper's own quantity outcome is *"the number of new contracts decreased by
  around **10% to 20%**"* (§4.2), not a point −10%, and its elasticity range tops at ≈3, not 2.
  The model's flow is **−48.2%** at a rent of −16.5% — so the honest statement is that the supply
  response sits **≈14% above the top of the published IV range**, not 83% above its centre.

  **And one hypothesis the same day's measurements refuted, recorded so it is not retried.** The
  divergence between the model's flow (−48.2%) and its stock (−13.1% of tensioned dwellings rented,
  against the paper's −10% overall supply) is **not** explained by excessive churn: measured on the
  baseline, the model's tensioned rental market turns over at **14.5%/yr, an implied mean tenancy of
  6.9 years** — *slower* than the ≈5-year LAU minimum for an individual landlord implies. Monràs
  states that *"new contracts signed is a good approximation of changes in the overall supply"*; in
  this model that approximation fails by a factor of about 3.7, and the cause is **not identified**.
- **The cause IS identified, and it is turnover — measured 2026-09-17, ten seeds.** The bullet
  above left the flow/stock divergence open. `metrics.py` now emits the denominator
  (`rented_stock_{z}`) and the rate (`rental_turnover_{z}`, annualised, reciprocal = mean tenancy
  in years), because `flow = stock x turnover` is an identity and nothing in the model was
  emitting the third term for the residual to be read off. On the G1 design (cap at tick 20 of 40,
  Ley 11/2020, mean of ticks 24-40, seeds 1-10):

  | | baseline | capped | change |
  |---|---|---|---|
  | new leases, tensioned | 45.74 | 23.57 | **-48.2%** |
  | rented stock, tensioned | 1219.4 | 1140.1 | **-6.5%** |
  | rental turnover, tensioned | 0.150/yr | 0.082/yr | **-44.9%** |

  The identity closes: Δln flow -0.6571 = Δln stock -0.0670 + Δln turnover -0.5954, residual
  +5.3x10⁻³ (aggregation, not a leak). **Mean tenancy goes from 6.7 to 12.2 years under the cap.**

  **A basis error in the register, corrected here.** The -13.1% stock figure above is the **final
  tick**; the flow and rent figures it is compared against are **means of the post-cap window**.
  Measured on the window basis the stock falls **-6.5%**, so the divergence is a factor of
  **≈7.4, not ≈3.7** — the register understated it by comparing two different bases. (-13.1% at
  the final tick is reproduced exactly, so the number was right and its label was not.)

- **And it is neither tenant lock-in nor a seeker queue: the rental market drains (2026-09-17).**
  The turnover collapse has two readings with opposite policy meanings, and seekers discriminate
  between them. Same design, ten seeds:

  | | baseline | capped | change |
  |---|---|---|---|
  | seeker share | 0.0454 | 0.0454 | **+0.1%** |
  | tenant share | 0.2111 | 0.2028 | -3.9% |
  | ownership rate | 0.7435 | 0.7518 | +1.1% |
  | market vacancy, tensioned | 0.0387 | 0.0193 | **-49.7%** |
  | rental tightness, tensioned | 1.157 | 13.045 | **+1041%** |

  Seekers do not pile up, so it is not a matching failure with a queue; tenants leave the tenure
  for ownership instead. But the offered pool **halves** and tightness goes up **11-fold**.
  Turnover does not fall because sitting tenants choose to stay — it falls because there is
  nothing to move into.

  **This relocates the error away from where every repair has aimed.** §7.2, §7.2b Piece A and
  Piece B all target the **exit margin** — which landlords sell, and when. The measurement says
  the exit margin is the small term (-6.5% of stock) and the large one is what happens to the
  units that **stay** rented. A tensioned rental market at tightness 13 has no counterpart in the
  episode being matched: Catalonia 2020-22 is where Monràs measures -5% rents and -10% to -20%
  new contracts, not a market where the offered pool halves. Under `index_binds_all=True` every
  unit is capped and no rent can rise to clear, so the model has no relief valve; the real episode
  had several (temporada contracts, rooms, informal letting, non-compliance) and
  `MarketConfig.seasonal_evasion_share` is 0.15 of exits. Whether those valves are under-sized is
  a **sourceable** question, and it is not the question the register named as the reopening
  condition ("a mechanism that makes SOME landlords hold on").

  **It does not rescue G1, which is what licenses recording it.** G1 reads the flow, and the flow
  is unchanged at **3.655**. Read on the stock the same ratio is **0.373**, inside Monràs's span —
  so the gate's verdict rests entirely on which of the two the model is asked for, and the honest
  statement is that the model's flow is being driven by a tightness regime the episode did not
  have. No parameter was moved and no threshold was touched to produce any of this.
- **`selling_cost_share` ships at its sourced 0.040, and the joint it was co-calibrated with
  breaks — in both directions (2026-09-17).** The band (0.01–0.07, two real sale routes) and the
  intermediation-weighted point (0.040) were sourced on 2026-09-16 and deliberately held back for
  one branch, so that §7.2's and §7.2b's falsifications stayed attributable to their mechanism
  rather than to a parameter moving underneath them. Shipping it now, **re-measured on the
  post-§7.2b model** rather than carried over from the earlier reading, which was taken before
  §7.2b existed:

  | | |
  |---|---|
  | **fixes** | `test_shadow_rent_stays_anchored_under_a_cap` — **one of the two reds §7.2b left behind** |
  | **restores** | `test_non_resident_surcharge_removes_foreign_purchases` (strict xfail → XPASS) |
  | **breaks** | `test_forbearance_raises_the_arrears_stock_and_lowers_the_flow` — foreclosures **112** with forbearance against **103** without; the assertion inverts |
  | **breaks** | `test_rate_shock_cuts_transactions_before_prices` — `vol_drop` 0.9587 against a `< 0.95` bound, a 0.9pp miss |
  | bookkeeping | `test_the_registered_xfails_show_red_in_the_panel`, because the xfail register changed when the non-resident test stopped failing |

  Suite 3 failed / 177 passed / 9 xfailed → **6 failed / 175 passed / 8 xfailed**. The raw count
  hides the composition: two improvements, two regressions and one bookkeeping consequence.

  **One mechanism explains every row.** `market/clearing.py`'s reserve floor is
  `max(debt·(1+k), ask·(1−discount))`. Raising `k` lifts the floor for every **indebted** seller
  and suppresses sales. Fewer sales means more dwellings stay let, which is why the shadow rent
  stops detaching from the transacted one under a cap — §7.2b had narrowed that gap from 1693 to
  1568 without crossing, and the sourced cost crosses it. The same suppression means a distressed
  owner cannot sell its way out of trouble, which is why forbearance now leaves **more**
  foreclosures than it prevents. And it thins the baseline the rate shock's incremental volume cut
  is measured against.

  **What this establishes, beyond the parameter.** §7.2b's mechanism and the sourced cost point the
  same way and **neither reached the shadow-rent anchor alone**. That is the first evidence on this
  model that the rent-cap channel and the sale-side reserve floor are one problem rather than two.

  **The two regressions are recorded, not repaired.** `selling_cost_share` was a `[guess]`
  co-calibrated with other guesses, and sourcing it alone breaks that joint — which is the finding
  rather than a side effect of it. Repairing them by moving another guess would re-form the joint
  somewhere else and hide it again. The forbearance inversion in particular is worth its own
  investigation: it is economically coherent — a seller who cannot sell is a seller who
  forecloses — and it may mean the test's claim, not the model, is what needs restating.
- **§7.2b step 1: re-anchoring does NOT rescue §7.2, and the sweep that tested it refutes the
  hypothesis that proposed it (2026-09-16).** §7.2's F3 record said the cap's sign depends on the
  growth anchor, that the baseline runs at 2%/yr against Catalan evidence generated at HPI +12.7%,
  and that re-running F1 across the anchor was the first thing §7.2b should do before changing any
  mechanism. Done, properly: **ten seeds**, seven anchors, Ley 11/2020 (`index_binds_all=True`),
  cap at tick 20 of 40, mean over the 16 post-cap ticks, scenario over baseline − 1, sweeping
  `MarketConfig.long_run_growth`.

  | anchor /tick | ≈%/yr | rent | new leases | Δln ratio | seeds with the rent sign right |
  |---|---|---|---|---|---|
  | 0.0025 | 1% | +32.6% ± 6.4 | −26.6% ± 2.4 | — | 0/10 |
  | 0.0050 | 2% | +45.3% ± 14.6 | −33.1% ± 2.7 | — | 0/10 |
  | 0.0075 | 3% | +52.1% ± 12.7 | −34.1% ± 3.5 | — | 0/10 |
  | 0.0100 | 4% | +36.1% ± 13.6 | −35.1% ± 2.7 | — | 0/10 |
  | 0.0150 | 6% | −12.7% ± 23.3 | −31.9% ± 5.2 | 2.392 | 9/10 |
  | 0.0200 | 8% | −36.9% ± 5.4 | −7.7% ± 9.0 | **0.206** | 10/10 |
  | 0.0300 | 12% | −40.5% ± 5.0 | −0.1% ± 2.6 | 0.003 | 10/10 |

  **It is not seed noise.** 0/10 below 4%/yr, 9/10 at 6%, 10/10 at 8% and above: a sharp regime
  boundary between 4% and 6%, which is what the earlier three-seed probe had seen as a
  non-monotone curve.

  **But re-anchoring moves the model from one pathology to another, so it is not the repair.**
  Below ≈5%/yr the cap triggers mass exit and raises rents. At the **observed** anchor — 12%/yr,
  matching HPI +12.7% (2025) — the supply response vanishes entirely: new leases −0.1% ± 2.6,
  a cap with no quantity effect at all, against a rent cut of 40.5%. The Δln contracts / Δln rent
  ratio is inside Monràs's 0.07–2.0 span at **exactly one anchor, 8%/yr**, and that anchor is
  neither the baseline nor the observed one. And the rent MAGNITUDE is wrong everywhere: Monràs
  measures −5%, the model gives −36.9% and −40.5% where it gets the sign right — a factor of
  seven to eight.

  **Diagnosis, and it is the frictionless condition seen from its other side.** The exit decision
  is a **step function in E[g]**. With E[g] low, `r_req` is high, the cap breaks it on nearly every
  unit, and everyone sells. With E[g] high, `r_req` collapses because appreciation alone pays the
  required return, the cap never breaks it, and nobody sells. There is no stable intermediate
  regime — only a narrow boundary the curve passes through. A mechanism with no friction cannot
  produce Monràs's −10% of tenancies at ANY anchor, because it has no way to make *some* landlords
  leave and others stay.

  **Consequence: §7.2b is a redesign, not a recalibration.** The friction declined in §7.2's design
  — the option value of waiting for a cap declared for a fixed term — is not optional, and this
  sweep is the evidence for why. Re-anchoring is now a **closed** line of repair, recorded so it is
  not reopened.
- **§7.2's F1 is deleted, superseded by G1 (2026-09-16, §7.2b Task 5).**
  `test_the_supply_elasticity_lands_inside_the_monras_span` swept two structural parameters —
  `MarketConfig.selling_cost_share_range` and `CapResponseConfig.holding_years_range` — and
  asked only for a witness at ANY corner of the declared ranges. §7.2b retired `holding_years`
  outright (the withdrawal horizon is now the cap's own remaining statutory term, not a swept
  structural parameter), so the second dimension F1 swept no longer exists in the model. A test
  that can only vary a parameter the model no longer reads cannot be evaluated — it is not a
  falsification, it is a probe of retired machinery — so it is deleted rather than xfailed, which
  would misrecord a defect that is not there. §7.2b's own Falsification subsection (model-spec.md
  §7.2b) names G1 as F1's declared successor, and G1 is strictly stricter: F1 accepted a witness
  at ANY corner of its two swept parameters' declared ranges, and — before `holding_years` was
  retired — it passed at exactly one of the four corners while three inverted the sign; a
  single-corner pass is a failure by G1's own standard. G1 requires the rent sign correct in ALL
  TEN seeds at the SHIPPED values, with no parameter swept at all. G1's measured result is
  recorded in the verdict bullet immediately below.
- **Task 1's premise gate: `cap / r_req` is a point mass, not merely near-uniform
  (2026-09-16).** The test that licensed §7.2b's whole design
  (`test_the_cap_to_reservation_ratio_is_near_uniform_within_a_zone`, threshold `cv < 0.10`)
  measured **cv = 0.000** in the hand-built fixture and **cv = 1.4×10⁻¹⁶** — machine epsilon —
  over 4,693 small-landlord units in a real `Engine` run (seed 42, Ley 11/2020, 4 ticks after
  activation). `quality` cancels identically between `required_rent` and the index branch of
  `cap_level`; the scale-invariance §7.2b diagnosed is confirmed at machine precision, not merely
  "small enough." **A caution belongs on the record with the pass.** The fixture's *mean* of
  0.800 is tautological: `_capped_state` sets `zone.reference_rent` directly from the
  `cap_ratio` argument, so the test could print nothing else — it would report `mean = 0.4` if
  called with `cap_ratio=0.4`. The real-run mean is **0.8039** and a robustness sweep (seed ∈
  {1, 7, 42} × ticks-since-activation ∈ {2, 4, 8}) found it drifting **0.61–1.03**, while `cv`
  stayed at machine epsilon throughout. **The bite is not constant in time** — neither §7.2b nor
  the plan that implemented it anticipated this, and it is not tested by any of G1–G4, which all
  condition on a fixed post-activation window.
- **G1–G4, run at the shipped parameters (2026-09-16, §7.2b Task 5/6): G1 FAILS, G2/G3/G4
  PASS.** Ley 11/2020, ten seeds unless noted.

  | gate | result | measured |
  |---|---|---|
  | G1 | **FAILS** | rent −16.2% (sign correct, all ten seeds individually), leases −46.6%, Δln ratio **3.563** against Monràs's 0.07–2.0 span |
  | G2 | PASSES | \|Δleases\| = **34.7pp** across the sourced `intermediation_share` corners: 0.40 → −61.6% leases (rent −7.0%); 0.85 → −26.8% leases (rent −17.7%) |
  | G3 | PASSES | 133 withdrawals ticks 20–25 against 84 ticks 26–31 (one seed, `start_tick=20`, `term_ticks=12`) — front-loaded within the declared term |
  | G4 | PASSES | rent sign negative at all four sourced anchors (1/2/4/8%/yr), ten seeds each; the pre-§7.2b boundary (0/10 below 4%/yr, 10/10 at 6%/yr+) is gone at the three anchors that discriminate (1, 2, 4%/yr each moved 0/10 → 10/10) — 8%/yr was already 10/10 before this branch and discriminates nothing. **Sign only** — per-anchor rent/lease magnitudes were not captured at ten seeds |

  **G1's failure is purely magnitude, not sign dispersion.** Its per-seed sign assertion passed:
  all ten seeds are individually correctly signed, so there is no sign inversion hiding under
  the pooled mean the way §7.2's F1 had. The `3.563` ratio comes from the quantity leg
  (−46.6% new leases) moving far more than the price leg (−16.2% rent) — the model still sheds
  contracts several times faster than the sourced studies' own quantity-to-price ratio allows.

  **G4's magnitude at ten seeds is unmeasured — only the sign was checked.** The per-anchor rent
  and lease magnitudes were not captured at ten seeds, so the quantity leg's behaviour across
  the anchor sweep remains unverified at full statistical power. A superseded three-seed probe
  (explicitly disclaimed at the time as not this gate's own measurement) had shown new leases
  turning **positive (+0.76%)** at the 8%/yr anchor while rent stayed negative — the same
  large-quantity-response pattern G1 falsifies at the shipped anchor, seen again across the
  anchor but not confirmed at the ten seeds G4 actually runs.

  **Two findings, neither predicted, that belong in this record with the gates themselves.**

  1. **G2's corner locates where the remaining error is NOT.** At `intermediation_share=0.85` —
     the top of the sourced regional range, the all-agency-exit corner — leases still fall 26.8%
     against Monràs's −10% tenancies. The model over-responds even at the extreme edge of what
     the evidence admits: re-calibrating `intermediation_share` anywhere inside its sourced band
     cannot reach the measured response, so the excess sits elsewhere in the channel, not in
     this parameter.
  2. **The two gates that turned green in Task 3 were checked, not assumed.**
     `test_cap_coverage_scales_the_rent_cap` and `test_rent_cap_lowers_contract_rents` — two of
     the four tests red since §7.2 — flipped green as a side effect of Piece B (commit
     `e47bbda`), with no test file touched in that task. Verified independently for this record:
     `git diff 03456e8..e47bbda -- tests/test_validation.py tests/test_engine.py` is **empty**.
     The assertions that now pass are byte-identical to the ones that were red — the mechanism
     earned the green, no threshold, band or comparison-direction was edited to get there.

  **The magnitude is registered separately, per §7.2b's own Falsification subsection, and not
  folded into G1 beyond G1 itself failing on it.** G1 is the gate built to carry the magnitude
  question — a co-movement ratio, not a bare sign check — and it is the one that fails. The
  sign of who exits is repaired; the size of the response is not, and the excess sits in the
  quantity leg (new leases, against Monràs's −10% and Pérez García's −13% tenancies), not in
  the price leg alone.

  **The price leg carries its own excess too, and it has a number.** Rent −16.2% against
  Monràs's −5% point estimate is **≈3.2×** the sourced magnitude — smaller than §7.2's ≈7×
  overshoot at the one anchor where §7.2's sign was correct, but not close to closed: three
  times the sourced figure is a registered excess, not a rounding difference. It sits alongside
  the quantity leg's excess above, not instead of it — both legs are too large, not only the
  ratio between them.

  **Suite at `ea7a795`: 3 failed / 177 passed / 9 xfailed.** The three reds:
  `test_shadow_rent_stays_anchored_under_a_cap` and
  `test_rent_cap_reproduces_the_monras_co_movement` — both inherited from §7.2 and never claimed
  by §7.2b — plus `test_g1_the_co_movement_emerges_at_the_shipped_parameters`, §7.2b's own
  falsification firing as designed. Fix round 1 (`ce61351`, current HEAD of
  `spec-7-2b-anchor`) tightened G1 to a genuine per-seed sign check and G4 to the full ten-seed,
  sourced-grid form; neither change moved a verdict — the model's randomness is fully seeded, so
  G1's ratio is byte-identical, `3.5627...`, before and after the fix.

  **What this does and does not license.** Three of four falsifications passing means the
  dispersed-exit mechanism does what §7.2b claims — it is not a step function in the growth
  anchor any more, and withdrawal concentrates inside the statutory term the way a declared,
  renewable cap should. **It does not mean the rent cap is reportable.** The rent cap under Ley
  11/2020 stays **not reportable** under `model-spec §13.2`: the sign of the withdrawal channel
  is now a defensible **direction** claim, and the size of the quantity response is an **open,
  registered magnitude error** — not a guess awaiting a parameter fit, since G2's own corner
  shows the sourced range of `intermediation_share` cannot close it. Ley 12/2023 (§7.2's F4) is
  still not run: it stays gated on the Ley 11/2020 tests being green, and G1 is red.
- **§7.2 F3 does not fire, and the probe that settled it found something larger
  (2026-09-16).** F3 asked whether `min_required_yield` — a `[guess]` — was governing the SIGN of
  the rent-cap result, by flooring `required_yield = max(min_required_yield, bond + π·risk − E[g])`
  in a boom, collapsing `r_req` and stopping `cap < r_req` from firing. **It is not.** Rebuilding
  the same comparison `required_rent` makes, the floor never binds in any zone at any growth
  anchor: at a 1%/yr anchor the unfloored yield is +0.0784 against a floor of 0.0050, and even at
  an **8%/yr** anchor it is +0.0212 — still four times the floor. The route F3 would fire through
  is closed by construction in this calibration.
  **What the sweep found instead.** The cap's response is strongly decreasing in the exogenous
  growth anchor, through the *unfloored* term rather than the floor — a larger E[g] lowers
  `bond + π·risk − E[g]`, lowers `r_req`, and fires `cap < r_req` less often:

  | anchor /tick | ≈%/yr | rent | new leases |
  |---|---|---|---|
  | 0.0025 | 1.0% | +31.7% | −27.2% |
  | 0.0050 | 2.0% | +43.8% | −31.4% |
  | 0.0100 | 4.0% | +33.3% | −35.6% |
  | 0.0200 | 8.0% | **−37.2%** | **−13.2%** |

  At the 8%/yr anchor **the sign corrects**: the cap lowers rents and costs 13.2% of leases — a
  figure sitting on top of Pérez García's −13% tenancies. The model's baseline anchor is
  **2%/yr**, while the Catalan evaluations the gates are adjudicated against measure a period of
  **HPI +12.7% nominal (2025) and +12.2% y/y (2026Q2)** [INE IPV, kb-refresh-2026-09]. The
  calibration is being run in a low-growth world against evidence generated in a high-growth one.
  **What this is not.** Three seeds; the curve is **not monotone** (+31.7 → +43.8 → +33.3 → −37.2),
  and that non-monotonicity is unseparated — it may be seed noise or a threshold effect. The floor
  check is one seed at the final tick. This is a hypothesis with a mechanism and a number, not a
  result: it says the rent-cap sign depends strongly on the growth anchor, and that F1 was
  adjudicated at an anchor far below the episode it is judged against. Re-running F1 across the
  anchor is the first thing §7.2b should do, before any mechanism is changed.
- **`selling_cost_share` is sourced as a BAND, and the point value is deliberately not shipped
  yet (2026-09-16).** §7.2 makes this parameter the rent cap's exit threshold, so it stopped being
  tolerable as a `[guess, order of magnitude from buyer_fees]`. Two institutional viewpoints now
  bound it. **Statutory**: Código Civil art. 1455 puts the `escritura matriz` on the seller and
  everything after it on the buyer — *salvo pacto*, and the pacto shifts more onto the buyer, so
  this is a floor; IIVTNU falls on the transmitente but is levied on cadastral **land** value, not
  on price; aranceles RD 1426/1989 and RD 1427/1989. That gives **0.5–1.5% for a self-sold
  dwelling**. **Market**: agency commission 3–5% + IVA — at 21% IVA a 4% fee costs 4.84% of price
  — giving **4–7% for an agency sale**. What fixes the point rather than the band is the
  intermediation share: agencies handle **64% of second-hand purchases** [Fotocasa Research] and
  **≈70% of all operations** [idealista], two portals competing for the same sellers and agreeing
  within 6pp. Weighting the two routes at 0.66 gives **0.040**.
  **The model still ships 0.02.** Moving it to 0.040 was measured on the full suite and it fixes
  one registered strict xfail while breaking two targets in channels unrelated to the rent cap:
  `test_non_resident_surcharge_removes_foreign_purchases` **XPASSes** (restored — its note recorded
  that the surcharge no longer cleared the 25% threshold because the foreign base had fallen to
  2.28%), while `test_rate_shock_cuts_transactions_before_prices` and
  `test_forbearance_raises_the_arrears_stock_and_lowers_the_flow` **regress**. The mechanism is
  `market/clearing.py`'s reserve floor, `max(debt·(1+k), ask·(1−discount))`: raising `k` lifts the
  floor for every indebted seller and suppresses sales. The parameter was a guess co-calibrated
  with other guesses, and sourcing it alone breaks that joint — which is this register's recurring
  finding, not a new one. Shipping the value belongs on its own branch with its own write-up of
  those three channels, so that §7.2's falsifications stay attributable to the mechanism rather
  than to a parameter that moved underneath them. The **band is sourced and is swept**; only the
  point waits.
- **`landlord_cost_share` now has two institutions behind it, and they do not say the same
  thing — on purpose.** The shipped `c = 0.22` (range 0.20–0.24) comes from AEAT's declared-rent
  P&L with depreciation and mortgage interest stripped out. Since 2026-09-16 the second source is
  INE's national accounts: CNE table 69069 publishes branch `68a alquileres imputados` separately,
  its cost side is built from the EPF (COICOP 04.3.3) and insurer payouts rather than from IRPF,
  and adding IBI back as D.29 gives **(CI + D.29)/output = 10.9% (2023), 15.3–18.0% (2013–2022)**.
  That is a **lower bound**, not a competing estimate: national-accounts IC carries only the
  repair slice of a comunidad quota and no management or letting cost, and both are inside AEAT's
  rows. ≈16% against 22% is the size of those two items and the sign is right, so **the parameter
  was not moved.** Two things the second source does establish that the first could not. First,
  the ≥2 rule is satisfied for `c` — previously every figure traced back to AEAT through DO 2432
  and the Informe Anual. Second, **`c` is not a constant**: the ratio falls monotonically from
  ≈31% (1997–99) to ≈16% (2016–22), because the denominator tracks rents and maintenance spending
  does not, and 2023's 10.9% is a level break from the 2024 statistical revision rather than a
  behavioural one. The model ships a constant calibrated to the recent end of a falling trend.
  Unchanged and still unreconciled: DO 2432's ≈36% of gross rent against AEAT's own 41–45% on the
  same object while citing it — neither of which **is** `c`, since both carry depreciation and
  interest.
- **§7.2 did not exist until 2026-09-16; it is now written AND implemented.** It had been cited
  in `model-spec §13.7`, twice in this file and once in `config.CapResponseConfig` as the
  arbitrage condition that would replace the rent cap's fitted `hazard_scale`, and it had never
  been written. The spec also said until 2026-09-16 that §7.1 and §7.2 were "not coded until
  [`c`] is retrieved"; `c` was retrieved on 2026-09-15 and §7.1 was coded with it, so that
  sentence was stale in both halves. §7.2 is now written (`model-spec §7.2`) **and the code has
  moved**: `hazard_scale`, `rental_supply_elasticity`, `exit_split_sale`, `exit_split_vacant`
  and `exit_split_evasion_base` are retired, and the cap's withdrawal margin is the arbitrage
  condition `cap < r_req`, decided in `agents/landlord._exit_destination`. Its F1–F4 have been
  run against Ley 11/2020 (F4, the Ley 12/2023 out-of-sample test, is deferred until F1–F3 pass
  per §7.2's own protocol), and three of the four calibration gates fail **on purpose** — see
  the falsification recorded immediately below. The rent cap under Ley 12/2023 therefore stays
  **not reportable** (`model-spec §13.7`, "Reporting consequence"); it does not move to
  **direction** until F1–F3 pass and F4 lands inside the span.
- **§7.2's arbitrage condition triggers mass withdrawal, and the rent leg flips sign — a
  recorded, user-approved falsification (2026-09-16).** Under Ley 11/2020 the withdrawal
  channel is meant to lower tensioned contract rents (target 8, F1); instead it RAISES them.
  Measured, three seeds: **rent +53.6%, leases −78.7%** with the seasonal segment open;
  **+52.2%, −76.7%** with it closed. This is not repaired here — it is a faithful, measured
  consequence of the specified rule, registered for a later spec revision rather than tuned,
  softened or skipped away.
  **Diagnosis, which matters for that repair.** The sign flip comes from the **sale branch**,
  not the seasonal one: closing the seasonal segment barely moves the rent figure (+52.2%
  against +53.6%), so the seasonal diversion is a minor leak, not the driver. The sale
  threshold compares **60 undiscounted months** of `(r_req − cap)` against `0.02·V`
  (`selling_cost_share` shipped at 0.02), and since `r_req ≈ V·yield/(12·(1−c))`, a monthly
  shortfall of roughly **15% of `r_req`** already clears that threshold over the horizon — so
  nearly every binding cap ends up selling. The parameters that will decide the repair are
  `holding_years` and `selling_cost_share` (both structural, both swept in F1/F2), **not**
  `seasonal_evasion_share`, which the diagnosis above rules out as the lever.
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
- **Boom rent growth reaches ≈40% of the observed magnitude** (target 7r — passing since the
  2026-09-08 fourth pass, previously a strict xfail). Rents now outrun incomes: +3.6%/yr ± 0.8
  over 10 seeds, all positive, against ≈0.6%/yr median non-owner income growth in the hold-out
  boom, where the earlier measurement was +0.0% ± 0.3pp. The reading recorded here for a long
  time — that the clearing rent is a share of income and so *cannot* outrun it — was wrong: the
  queue-congestion channel was in the model all along and was inert only while the tensioned
  market ran slack at 0.5 applicants per listing. But Spain's own figure is +8–11%/yr, and the
  missing half is the size/quality margin (below). **Report the direction; do not size a
  rent-inflation claim on this model.**
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

### Phase-0 referee pass (2026-09-11)

Objections a hostile reader can raise against phase 0, answered or conceded.

- **"You widened the yield bands by 0.5pp until the test said what you wanted."** Conceded as
  a judgement call, not as a fit: the widening is symmetric, applied before the test was run,
  and the test fails anyway by roughly a factor of two on the rural leg. The convention matches the
  other zone targets (3 seeds, last 20 of 60 ticks).
- **"Three xfails is three failures you are choosing to live with."** Conceded, and that is the
  point of writing them down. Each names the mechanism that will fix it and the phase it
  lands in. Strict xfail means an accidental pass also fails the suite, so none of them can
  quietly stop being true.
- **"`median_ticks_to_sale` and `landlord_household_share` are gates you declined to set."**
  Conceded, but for two different reasons, and the first version of this answer got the second
  one wrong. `median_ticks_to_sale` has no anchor at all: nothing in `docs/sources.md` carries
  days on market, the row says **to verify**, and phase D gates it.
  `landlord_household_share` has *two* registered anchors — EFF 36.1% (2022 wave) / 45.3%
  (2024 wave, DO 2610) and the AEAT declarant counts — which is precisely why it is not gated:
  on an ownership basis and a declaring-rental-income basis they sit roughly three-to-four-fold
  apart, so they bracket the column rather than banding it. Setting a gate would mean choosing
  a basis, and that choice needs the EFF wealth-percentile gradient and the AEAT-basis sibling
  column, both phase B.
- **"The assumption register is your own account of your own work."** True, and it is
  falsifiable in the only way that matters: every row names a code site, so any row can be
  checked against the code, and a rule with no row is a finding against the register.
- **"Sealing the hold-out is unverifiable — you could have looked."** Partly conceded. What is
  verifiable is the order of commits: the seal predates the bust inputs, which predate the
  run. What is not verifiable is what the authors knew. The 2008–13 episode is public
  knowledge; the claim is not that nobody knows how it ended, but that no *parameter* was
  fitted to it, which the history does evidence.
- **"Target 10 passes, so the model gets yield compression right."** Conceded, and this is
  phase 0's most important qualification. Under the current rule a landlord's reservation rent
  is a fixed multiple of the unit's value, so the compression measured here (5.39% → 5.21%,
  5 seeds, hold-out boom, ticks 20:24 against 36:40) is a byproduct of asking rents lagging
  prices, not of a required yield responding to expected appreciation. The lag figures quoted
  for that reading, +3.6%/yr rents against +4.4%/yr prices, are the **10-seed `_holdout_boom`**
  numbers (3.57 / 4.38) on a ticks-24:40 window — a different basis from the compression
  measurement. The 5-seed basis agrees (3.78 / 4.57), which is why the reasoning stands; every
  other basis on this branch is labelled and this one now is too. The target passes
  for a reason that is not the mechanism it was written to identify, which makes it
  uninformative until phase B replaces the reservation rule with a total-return condition and
  compression becomes that rule's direct prediction. A target that passes for the wrong reason
  is worse than one that fails, because it stops being evidence. Re-read this row after
  phase B.

## Sensitivity screen, superseded (OAT, seed 42)

> Superseded by the Morris/Sobol analysis above. Kept for provenance; do not cite.

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

## Phase G — the valuation anchor and the sourced `overbid_sigma` (2026-09-15)

Branch `source-overbid-sigma`. The KB-refresh audit named this the highest-value evidence work
left on the model. It was, and not for the reason the audit gave.

### What the parameter is, and what the evidence says

`overbid_sigma` has been idiosyncratic taste since phase D, and the counterpart of that is
exact: the dispersion of log sale prices for the same dwelling, net of location × period.
Three independent studies measure it (`sources.md`, five new rows):

| Source | Data | Per-sale dispersion |
|---|---|---|
| Kotova & Zhang | US zipcodes 2012–16, house + zipcode-month fixed effects | mean **16.8%**, p10 11.2, p90 22.6 |
| Giacoletti, *RFS* 34(8) 2021 | California resales 1989–2013 | **6.8–12.4%** |
| Landvoigt, Piazzesi & Schneider, *AER* 2015 | San Diego 1999–2007 | **6.2–9.8%** |
| BdE DO 2508 (2025) | 1,032,960 Spanish sales, census-section × quarter FE, R² 85.70% | bounds the *share*, not the level |

The last two publish RETURN dispersions, which carry the error twice; the per-sale figures
above are theirs ÷ √2. **Band adopted 6–17%, central 10%** (§9 target 16, `metrics.price_dispersion`).

**No Spanish estimate exists.** INE's IPV estimates residual variances by category and
publishes none; the Registradores' IPVVR runs Calhoun's three-stage weighting on **1,274,958
sale pairs** — whose variance function *is* this quantity — and publishes only the index.
Registered as a negative result rather than filled with a guess.

The model measured **2.3%**.

### Raising it moved the level, not the dispersion

| σ | dispersion | price-to-income | discount | sold in the quarter |
|---|---|---|---|---|
| 0.02 (shipped) | 2.3% | 7.81 | 3.1% | 0.48 |
| 0.10 | 6.0% | 9.53 | 1.0% | 0.40 |
| 0.30 | 9.2% | 10.01 | 0.9% | 0.39 |

Two candidate causes were prototyped and **refuted**, and both are kept because they bound the
mechanism: correcting each price by the expected order statistic of its own auction (κ(n), then
κ(n, m)) made the level worse and then absurd, because the realised price is clipped by the
budget, the reserve and the ask; and a user-cost ceiling never binds, sitting at ≈40 years of
rent against a price of ≈15.

The cause is that `value = price_index × quality × taste` has no nominal anchor and the index
is the median of *winning* prices. The selection premium was capitalised every tick. At σ=0.02
the loop is invisible; at the measured σ it runs to the credit ceiling.

### §5c.6, and the bill it presented

Two indices: `price_index` stays realised (reported, expectations, the landlord hurdle);
`valuation_index` reprices each sale at an average taste draw by running the same auction twice
through the same rule. Level becomes σ-invariant — 6.38 / 6.40 / 6.44 across σ = 0.02 / 0.15 /
0.30 — and the suite goes red by seven, because the old calibration was absorbing the premium.

Then the diagnostic that decided the rest of the phase. The same supply experiment, before and
after (3 seeds, 60 ticks):

| starts/tick | before, p/inc | growth | after §5c.6 | growth |
|---|---|---|---|---|
| 8 | 8.56 | +4.24%/yr | 6.69 | +1.31%/yr |
| 20 | 7.19 | +2.25%/yr | 6.51 | +1.13%/yr |

**Phase D's scarcity-to-price channel was the taste order statistic.** Halving construction
used to add 2.0pp to annual price growth and now adds 0.18pp; the bidder count moved (4.0 →
5.8) and the price did not follow. Finding 2 of the redesign spec re-opens here.

### §5c.7 — the channel, rebuilt on budgets

`stretch = t/(t+k)` on the gap between the dwelling's worth and the buyer's credit limit, with
`t` the buyers per listing. Scarcity now reaches the price through income, LTV and DSTI. The
supply experiment recovers: p/inc +2.2 to +3.0 and growth +2.1 to +2.8pp across the same
starts range, against the old model's +1.37 and +2.0pp.

### The refit

LHS over five parameters (96 points), then six (128 points) once §5c.7 existed, two seeds each,
scored on dispersion / discount / above-ask / time-to-sale with the §9 gates as weighted guard
rails; then focused grids. Shipped:

| parameter | was | now | identified on |
|---|---|---|---|
| `overbid_sigma` | 0.02 | **0.20** | the sourced 6–17% dispersion band (delivers 8.0%) |
| `tightness_half_saturation` | — | **260** | the price-income wedge; searched 4–1400 |
| `ask_markup` | 0.08 | **0.12** | the realised discount, at the top of its sourced range |
| `seller_bargaining_power` | 0.85 | **0.25** | arithmetic: a one-bidder price θ of the way from reserve to ask gives a discount of (1−θ)·d, so 0.85 could not reach 6.2% at any markup |
| `search_listings` | 2 | **1** | see the frontier below |
| `buy_attempt_prob` | 0.50 | **0.64** | transaction volume; top of its guessed range, declared |

Ten-seed suite: **no failures**, and the level is σ-invariant over the sourced band (p/inc 8.09
/ 8.14 / 8.28 at σ = 0.10 / 0.20 / 0.30). Below σ ≈ 0.05 it is not — p/inc 5.19 at σ = 0.01 —
and that is recorded rather than hidden: the model is not meant to run there.

### The frontier, and the four regressions

`search_listings` buys one sourced observable with another, and no third setting escapes it:

| | price-to-income | discount | sales above ask | boom rent |
|---|---|---|---|---|
| m=1, k=260 (shipped) | 8.07 | 3.9% | 20% | +1.2%/yr |
| m=2, k=1400 | 8.07 | 2.0% | 39% | +4.2%/yr |
| m=2, k=1000, markup 0.16 | 8.96 | 3.4% | 24% | +4.2%/yr |

Fotocasa puts sales above ask at 9% of negotiating sellers; the Tecnocasa discount is 6.2%; the
boom's sourced rent leg is +8–11%/yr. m=1 keeps two of the three closer and loses the third.

Four tests are now **strict xfails labelled as phase-G regressions**, each with the diagnosis in
its reason string rather than a widened band:

1. **Boom rent growth** +1.17%/yr against a +2.5% gate — the frontier above.
2. **Wider search no longer slows the market** (m=6 sells 37.3% inside the quarter against
   m=1's 34.7%, where phase D swept 75% → 21%). The old ordering was produced by the same
   selection §5c.6 removed; §5c.2 needs rewriting against the days-on-market distribution.
3. **The rent cap's rent leg** reads −21% against −4…−6%, and is now *mechanical*: identical at
   hazard 0.3 / 0.5 / 0.7 and at elasticity 0 / 1 / 2. What moved is the distance between market
   rents and the reference index, which updates at 0.1/tick behind them. A reference-rent
   specification question.
4. **Loss aversion deepens the fall** (−69.7% against −66.9%) instead of cushioning it, because
   §5c.6 moved θ to 0.25, so a one-bidder sale prices near the reserve and a higher ask now only
   withholds the dwelling. Closing it means the reserve, not the ask, carrying §5d.1.

### Sobol after phase G (2026-09-15) — 390 + 1,536 evaluations

Morris first, 10 trajectories over the 39 free parameters, then Saltelli on the eight
survivors plus the two parameters this phase owns. The runner now takes `--jobs`; the design is
evaluated in a process pool and the numbers do not depend on it (every point is a deterministic
run of its own config at the one fixed seed).

**`overbid_sigma` is out of the screening entirely** — it does not reach the Morris top eight
on any moment. Total-order indices on the moments that matter:

| Moment | CV | first | second | third | `overbid_sigma` | `tightness_half_saturation` |
|---|---|---|---|---|---|---|
| price-to-income | 0.092 | `ask_markup` 0.42 | `price_index_smoothing` 0.26 | `momentum_gain` 0.24 | **0.057** | 0.041 |
| purchase effort | 0.092 | `ask_markup` 0.42 | `price_index_smoothing` 0.26 | `momentum_gain` 0.24 | **0.057** | 0.041 |
| transactions | 0.123 | `ask_markup` 0.68 | `momentum_gain` 0.18 | `price_index_smoothing` 0.18 | 0.050 | — |
| rent level | 0.157 | `small_landlord_premium` 0.68 | `ask_markup` 0.35 | `price_index_smoothing` 0.16 | 0.130 | 0.134 |
| tensioned market vacancy | 0.405 | `small_landlord_premium` 0.93 | `momentum_gain` 0.17 | `ask_markup` 0.15 | 0.103 | 0.100 |
| rent overburden | 0.041 | `small_landlord_premium` 0.69 | `ask_markup` 0.64 | `price_index_smoothing` 0.56 | 0.374 | 0.402 |
| arrears | 0.177 | **`essential_share` 0.96** | `ask_markup` 0.10 | `overbid_sigma` 0.08 | 0.083 | — |
| ownership | 0.0067 | flat across the design, not decomposed | | | | |

Phase E put 26% of the price level's variance on `overbid_sigma` and called that the reason the
level could not be reported as a magnitude. It is now **5.7%**, and the parameter is sourced
besides. The phase did what it was for.

**The variance rule (§13.2), applied as written and not adjusted after seeing the numbers.**
The verdict does not change — two magnitudes, everything else direction-only — but the reason
does, and that is the useful part:

| Quantity | Largest assumed share | After the rule |
|---|---|---|
| Price level, price-to-income, purchase effort | `ask_markup` 0.42 | direction only |
| Transactions | `ask_markup` 0.68 | direction only |
| Rent level, overburden, tensioned vacancy | `small_landlord_premium` 0.68–0.93 | direction only |
| Cash-purchase share, zone price ratio, completion ratio, foreclosure rate | assumed shares 0.29–0.78 | direction only |
| Arrears | largest assumed below 0.10; the 0.96 is a measured band | magnitude, conditional on the essential-consumption band |
| Ownership rate | flat | magnitude |

**The evidence queue is therefore rewritten.** The KB refresh named `overbid_sigma` and
`landlord_required_spread` as the two highest-value measurements. Both are closed — one
measured here, one split into sourced parts in phase B — and what now blocks every price-like
magnitude is, in order: `ask_markup` (assumed that sellers post a markup; the 6.2% realised
margin is measured, the posting convention is not), `price_index_smoothing` (a guess, and not
yet a row in `assumptions.md`), and `small_landlord_premium` (declared fitted, §7.1's one free
parameter). None of them is the dispersion parameter this phase spent its time on, which is how
a variance rule is supposed to work.

### What this phase did not do

Sobol **has** been re-run (above). What the phase did not do: close the four regressions,
re-identify the rent-cap block against the new price side, or source `ask_markup` and
`price_index_smoothing`, which is where the variance rule now points. The 2008–13 episode is spent
(§13.11) and was not touched. The four regressions are open, and three of them are
specification questions rather than calibration ones.

## Sourcing `ask_markup` and `price_index_smoothing` (2026-09-15)

Phase G's Sobol run left three parameters holding every price-like magnitude: `ask_markup`
(0.42 of the price level's variance), `price_index_smoothing` (0.26) and
`small_landlord_premium` (0.68–0.93 on the rent side). The first two are done here. Five source
rows, two of them Tier-1 series pulled and computed with rather than quoted.

### `price_index_smoothing` — measured, and the guess was right

The parameter is the weight of this tick's transactions in the index agents condition on. Its
empirical counterpart is not a preference: **the price signal Spanish buyers, sellers and
lenders actually see is an appraisal**, and an appraisal under ECO/805/2003 is built from
recent comparables, so it tracks transacted prices with a lag. Two Tier-1 quarterly series make
that measurable:

- **INE IPV**, national general index, transaction-based hedonic — 78 quarters 2007Q1–2026Q2,
  pulled through the INE API (table 80270).
- **MIVAU Estadística de Valor Tasado**, table 1, appraisal €/m² — 79 quarters 1995Q1–2026Q1,
  the XLS parsed.

Fitting `dlog(appraisal) = s·dlog(IPV) + (1−s)·dlog(appraisal[−1])`:

| Window | n | s on current transactions | persistence | implied s | R² |
|---|---|---|---|---|---|
| 2014Q1–2026Q1 (calibration) | 47 | **0.307** (se 0.104) | 0.490 (se 0.145) | 0.510 | 0.36 |
| 2007Q1–2026Q1 (with the bust) | 75 | **0.287** (se 0.065) | 0.520 (se 0.094) | 0.480 | 0.70 |
| 2014Q1–2019Q4 | 26 | 0.306 (se 0.109) | −0.014 (se 0.191) | 1.014 | 0.07 |

The model ships **0.30**. The two legs do not sum to one (0.31 + 0.49), so the appraisal series
carries drift the pure EMA does not: the honest range is **0.29–0.51**, with 0.30 at its lower
edge. The third row is the interesting one — in the calm expansion the appraisal tracks
transactions contemporaneously, so the smoothing is state-dependent, and a constant is a
simplification recorded in the register rather than averaged away.

### `ask_markup` — the outcome is measured, the parameter is derived, and the mapping fails

Per dwelling, the distance from a listing's own initial ask to its own sale price is:

- **6.2%** at the point of sale [Cátedra Tecnocasa-UPF, 2S 2025], plus
- the in-listing cuts, which idealista measures separately: **14%** of live listings cut in
  2026Q1 (11% a year earlier), by **7% of the initial ask** (€29,390 average).

So a dwelling never revised closes 6.2% below its ask and one revised once ≈13% below:
**a sourced band of 0.06–0.13**, and the model's 0.12 sits inside it, at the top — which is
where §5c.6 says it belongs, because with a taste-neutral anchor the posted markup must cover
the selection premium as well as the negotiation margin. The 15–20% practitioner rule of thumb
is the same statement from the seller's side.

Two things this does **not** license.

1. **The parameter is not the measured number.** The model's realised discount is 3.9% against
   the sourced 6.2% (§9 target 13c, a registered failure). The mapping from the observable to
   the parameter is therefore off by 2.3pp, and the register carries `ask_markup` as *derived,
   with a failing consistency check* rather than as measured.
2. **The markup is cyclical and the model's is constant.** The same per-dwelling gap was **27%**
   in October 2012, with 78% of unsold sellers having already cut 25% [Fotocasa seller survey].
   A constant markup understates asks in a bust — the same gap §5d.1's loss aversion attacks
   from the other side, and one more reason that regression matters.

The aggregate portal-to-notary gap (8–12% in 2021 → 32–44% in 2025, UVE Valoraciones) is
registered as a contrast and deliberately not used: it compares the stock on offer with what
sold, which is composition, not a markup.

### The variance rule, re-applied — and the price level stays a direction

With `price_index_smoothing` measured and `overbid_sigma` measured, the shares left on the
price level are `ask_markup` 0.42, `momentum_gain` 0.238, `search_listings` 0.155.

**If `ask_markup` counted as sourced, the largest unsourced share would be `momentum_gain` at
0.238 — below the 25% threshold — and price-to-income would become a reportable magnitude for
the first time in the project's history.** It is not being counted as sourced, because its own
consistency check fails by 2.3pp, and promoting a magnitude on a parameter whose mapping to its
observable is visibly wrong is exactly the move the rule exists to block. The price level stays
direction-only.

What that leaves is a short, specific route to the first reportable price level: close §9
target 13c. The discount is a frontier of the sale block (validation.md, phase G) rather than a
missing measurement, so the work is mechanism — a seller who concedes through the reserve
rather than the ask, or a demand side with fewer buyers per listing — not more evidence.

## §5c.8 and the first reportable magnitude (2026-09-15)

### Three failures, one cause: the clearing calendar

`clear_sales` matched a whole quarter of demand against every listing at once, so the ascending
auction ran on all of it. Offers do not arrive that way — they arrive sequentially, and the
seller answers what is in front of it [Merlo & Ortalo-Magné 2004; Merlo, Ortalo-Magné & Rust,
complete offer histories for 780 English properties]. The tick now clears in **three
sub-periods**, which is the number of months in a quarter and not a fitted number.

| Sub-periods | discount | above ask | bids/listing | sold in the quarter | price-to-income |
|---|---|---|---|---|---|
| 1 (before) | 3.9% | 21.3% | 3.49 | 0.47 | 8.07 |
| 2 | 4.7% | 16.4% | 2.59 | 0.57 | 8.16 |
| **3 (calendar)** | **5.1%** | **13.0%** | **2.22** | **0.61** | 8.28 → 8.13 after the re-fit |
| 6 | 5.6% | 9.8% | 1.88 | 0.70 (band tops at 0.63) | 8.37 |

Re-fit alongside it, both inside their sourced bands: `tightness_half_saturation` 260 → 400,
`ask_markup` 0.12 → 0.125. Ten-seed moments after both: discount **5.20% ± 0.10** (band 4–12%,
source 6.2%), dispersion 7.15%, price-to-income **8.13 ± 0.11**, sold inside the quarter 0.607,
contract yield 6.88%, ownership 0.724, transactions 3.3%/yr, arrears 3.2%.

**Three registered failures closed at once**, none of them by a parameter:

1. **§9 target 13c, the negotiation margin** — failing since phase D created it. 3.0% on
   arrival, 3.9% after phase G, **5.20%** now.
2. **The boom's rent leg** — phase G's frontier, which said the margin and boom rents could not
   both be had. **+3.03%/yr ± 2.74**, positive on nine of ten seeds. The frontier was an
   artifact of clearing the quarter at once.
3. **The phase-D falsification on the rate shock** — `PARTICIPATION_RATE_SENSITIVITY` was killed
   in phase D and the resulting failure recorded rather than patched. It passes again, and
   **nothing was added to the rate channel**: a buyer the credit screen prices out is no longer
   replaced inside the same tick by the next bidder on the same listing. The coefficient stays
   dead, which is the point.

One test changed rather than closed: `test_shadow_rent_stays_anchored_under_a_cap` had a leg
comparing post-cap asks with the shadow's level two ticks earlier, which only holds while the
trend is flat. §5c.8 made rents grow faster and the capped ask passed that level by 1.6% — while
sitting **9.6% / 12.2% / 16.9% below the no-cap counterfactual** on three seeds. The leg is now
the counterfactual, which is the claim the mechanism makes.

### Morris and Sobol re-run, and the variance rule flips

390 + **1,792** evaluations over twelve parameters. `ask_markup` now dominates almost everything
(ST 0.42–0.74) and `overbid_sigma` has left the screening entirely. Applying §13.2 as written,
with `ask_markup`, `price_index_smoothing`, `overbid_sigma`, `small_landlord_premium`,
`essential_share` and `base_starts_per_tick` counted as sourced and the rest as assumed:

| Moment | CV | largest assumed share | verdict |
|---|---|---|---|
| Price-to-income, purchase effort | 0.115 | `momentum_gain` 0.109 | **magnitude** |
| Price-to-income ladder margin | 0.293 | `momentum_gain` 0.131 | **magnitude** |
| Transactions | 0.115 | `search_listings` 0.199 | **magnitude** |
| Rent level | 0.144 | `small_landlord_premium` 0.654 | direction only |
| Tensioned market vacancy | 0.427 | `small_landlord_premium` 0.751 | direction only |
| Completion ratio | 0.203 | `expectation_momentum` 0.135 | **magnitude** |
| Arrears | 0.191 | `search_listings` 0.090 | **magnitude** |
| Foreclosure rate | 0.840 | `search_listings` 0.140 | magnitude, on a CV that large |
| Sold inside the quarter | 0.238 | `search_listings` 0.125 | **magnitude** |
| Bidders per listing | 0.179 | `buy_attempt_prob` 0.189 | **magnitude** |
| Ownership rate | 0.008 | `buy_attempt_prob` 0.358 — but the moment is flat (CV 0.008) | direction only, on the rule as written |
| Rent overburden | 0.041 | `small_landlord_premium` 0.619 | direction only |
| Zone price ratio T/R | 0.186 | `buy_attempt_prob` 0.336 | direction only |
| Cash-purchase share | 0.114 | `search_listings` 0.408 | direction only |
| Negotiation margin | 0.308 | `seller_bargaining_power` 0.317 | direction only, and circular — it is identified on this |

**CORRECTION, made before this section was committed.** The first pass of this table counted
`small_landlord_premium` as sourced and promoted the rent level and tensioned vacancy with it.
It is not sourced: §7.1 declares it the block's one **free** parameter, fitted on target 10.
Counted correctly it explains 65% of the rent level and 75% of tensioned vacancy, and both stay
direction-only. The error flattered the model, which is the direction errors of this kind
always run in, and it is recorded here rather than quietly fixed.

**The price level is a reportable magnitude for the first time in the project's history**, and
the three conditions that make it one are worth stating plainly because they are what a critic
should attack:

1. It is **conditional on the ask-markup band** (0.06–0.13 per dwelling), which explains 61% of
   its variance. Across the whole sourced design the moment's CV is 11.5%, so the honest
   reported form is *8.13, and 7.2–9.1 over the parameter ranges the evidence admits* — not a
   point.
2. It rests on counting `ask_markup` as **derived rather than assumed**. That call was refused a
   day earlier, when the model's realised discount was 3.9% against its source's 6.2%; it is
   made now because §5c.8 closed that gap to 5.20%, inside the band. The verdict follows the
   consistency check, not the other way round.
3. `momentum_gain` at 0.109 is the largest genuinely unsourced share. It was 0.24 before §5c.8.
   If a future change lifts it back above 0.25, the magnitude goes away again, and it should.

Direction-only survives where an unsourced parameter still dominates, and the queue is now
explicit about which one: **`small_landlord_premium`** carries the whole rent side (0.65 of the
rent level, 0.75 of tensioned market vacancy, 0.62 of overburden) and is §7.1's declared free
parameter; **`buy_attempt_prob`** carries the ownership rate (0.36) and the zone price ratio
(0.34); **`search_listings`** carries the cash-purchase share (0.41); and the negotiation margin
is governed by the weight it is identified against, which is circular by construction and cannot
be fixed by measuring anything.

## `small_landlord_premium`: bounded by its components, and the residual named (2026-09-15)

The Sobol run after §5c.8 leaves one parameter holding the whole rent side: 0.65 of the rent
level, 0.75 of tensioned market vacancy, 0.62 of overburden. §7.1 declares it free, and it
cannot be measured the obvious way — the observed yield minus the bond is what the hurdle is
supposed to predict, so reusing it would re-pin the quantity. So it is bounded by pricing the
things it is supposed to compensate:

| Leg | Priced by | pp of value per year |
|---|---|---|
| Tenant default and eviction | rent-default insurance, 3–5% of annual rent (one comparator 5–8%) × a 6.6% contract yield | 0.20–0.33 |
| Illiquidity | selling costs 4–7%, amortised over the **15-year-256-day** average holding period [Registradores ERI 2020, 251,269 sales; 2009 minimum 7y 106d] | 0.25–0.45 |
| Undiversified idiosyncratic price risk | the §9 target-16 dispersion (6–17% per sale), twice per round trip, annualised, at γ ∈ 2–5 and a wealth share 0.3–0.6 | 0.03–0.37 |
| **Sum** | | **0.5–1.2**, ≈2.0 at the shortest horizon and widest quote |

**The model needs 3.0.** The behaviour at lower values, five seeds:

| premium | rent (€/mo) | contract yield | rural yield | overburden | tensioned market vacancy | p/inc |
|---|---|---|---|---|---|---|
| 0.010 | 1,318 | 6.44% | 11.9% | 0.259 | 2.3% | 7.61 |
| 0.020 | 1,373 | 6.52% | 13.4% | 0.296 | 2.3% | 7.86 |
| 0.025 | — | — | — | — | — | two §9 targets fail |
| **0.030 (shipped)** | 1,438 | **6.57%** | 13.1% | **0.318** | 3.1% | **8.13** |
| 0.033 (before) | 1,523 | 6.93% | 15.6% | 0.327 | 4.0% | 8.11 |

At 0.025 the insider/outsider wedge inverts and the boom stops compressing the yield — target
10, the one §7.1 identifies this parameter on. So the value moves **0.033 → 0.030** and the
declared range narrows from 0.025–0.055 to **0.020–0.030**: the overlap of the old fit with the
derivation. The suite is green there, and the rural gross yield — the model's oldest failing
target — improves from 15.6% to 13.1% against a sourced 7–9%.

**What this does not do.** Roughly 1.8–2.5pp of the shipped premium still has no component
behind it, so the parameter stays unsourced for §13.2 and **the rent level, tensioned vacancy
and overburden stay direction-only**. The gain is that the parameter is now bounded by evidence
instead of free, its range is a third of what it was, and the residual has a name and a size.

Three candidates for that residual, none priced here: regulatory risk after Ley 12/2023 (cap
exposure, gran-tenedor thresholds, tenure-security extensions); the occupation tail, where the
only figure available is a landlord-side survey putting a quarter of landlords in litigation and
the selection in it is obvious; and the small landlord's own management time, which may already
sit inside `landlord_cost_share` — AEAT's cost line includes management — and must not be
counted twice. Pricing one of them without double-counting is the next piece of evidence work on
the rent side.

## The last three regressions, and the stopping rule (2026-09-15)

Phase G left four registered regressions. One (the boom's rent leg) fell to §5c.8. The other
three are closed here, and **none of them by a parameter**.

### 1. Loss aversion was carrying one of its source's two legs

`test_loss_aversion_reproduces_the_price_volume_correlation` broke in phase G: the brakes
deepened a bust (−69.7%) instead of cushioning it (−66.9% without). The xfail wrote down what
the fix would have to be and it was right. Genesove & Mayer measure **two** effects — asking
prices 25–35% of the nominal loss higher, *and realised prices 3–18% of it higher* — and the
model carried only the first. Once §5c.6 moved the bargaining weight to 0.25, a one-bidder sale
priced near the reserve, so an ask-only effect withheld dwellings without holding prices up.
The realised leg now sits in `seller_reserve` at **0.10 of the loss**, the centre of the paper's
0.03–0.18. The test passes and the price–volume correlation is back.

### 2. The search effect's direction was an artefact of simultaneous clearing

Phase D justified `m` with a sweep in which wider search *slowed* the market (75% → 21% sold
inside the quarter as m went 1 → 8). Measured now: **0.503 / 0.661 / 0.686 / 0.691** at m = 1 /
2 / 3 / 6 — the opposite, and flat above m = 2. A buyer who has compared two listings bids
nearer its limit on the one it picks, and clears it; the old ordering came from the simultaneous
auction §5c.8 removed. §5c.2 is rewritten around the measurement, and the test now asserts what
is true and identifying — the direction on every seed, with the *level* gated where ten seeds
exist. `m` is unchanged at 1, still identified on the same idealista distribution.

### 3. The rent cap was applying the wrong statute to nine tenths of the market

The rent leg read −24% against Monràs's ≈−5% and was diagnosed in phase G as "mechanical". The
mechanism turned out to be a **law the model was not implementing**. Ley 12/2023 binds the
reference index on **grandes tenedores only**; every other landlord is held to its own previous
contract plus IRAV, and to nothing at all where no contract exists in the last five years (LAU
art. 17.6–17.7). Individuals hold 85–92% of the Spanish rental stock. The model applied the
index to all of them.

`cap_level` now carries both regimes and `RentCap.index_binds_all` selects between them —
`True` is Catalonia's Ley 11/2020, which every evaluation study measures. Three fixes were
needed to make the small-landlord anchor real: the previous contract's rent survives the
tenancy (`Unit.last_contract_rent`, because the statute anchors on the last five years, and
zeroing it on vacancy had silently promoted every small landlord to the index regime), the
rotation path in `clearing.settle` keeps it too, and initially-let units start with it.

Measured, ten seeds, the ledger's horizon:

| | Ley 11/2020 (index binds all) | Ley 12/2023 (current law) |
|---|---|---|
| tensioned contract rent | −23.5% | **+16.6%** |
| new leases | −22.1% | −16.1% |
| national price | −6.3% | −6.9% |
| rent overburden | −4.3% | −8.2% |

**The second column is not reportable and says so in the ledger.** With the cap binding one
landlord in ten, the withdrawal channel dominates — and that channel's `hazard_scale` was
identified in the regime where the index bound everyone. Nothing has re-identified it for this
one, so the rent *rise* is an out-of-regime extrapolation, not a prediction. It is published in
the artefact as `rent-cap-state-law` precisely so the gap is visible.

What the split does settle: the targets that come from the Catalan evaluations now run the
Catalan statute (`test_rent_cap_lowers_contract_rents`, `test_cap_coverage_scales_the_rent_cap`,
`test_rent_cap_reproduces_the_monras_co_movement`), which is the difference between adjudicating
a 2020 evaluation against a 2020 law and against a 2023 one. The Monràs overshoot survives at
−20.6%, now attributed to one measured quantity — the model's reference index sits **16% below
market at activation**, against published implied cuts of −10…−15% (Catalan index) and −20% on
average (state index).

### The stopping rule (`model-spec §13.12`)

The variance rule cannot terminate: it names the largest unsourced share, and every ranking has
a first entry. Since phase E it has named `overbid_sigma`, `ask_markup`, `price_index_smoothing`
and `small_landlord_premium` in turn, and one of its candidates —`seller_bargaining_power` — can
never be closed, because it is identified on the moment it governs.

So sourcing now stops on purpose rather than on exhaustion: **when every quantity a registered
claim depends on is either a reportable magnitude or published as a direction, and the unsourced
shares that remain sit on quantities no claim uses.** Three things are declared irreducible and
nothing further is scheduled against them: the bargaining weight, the residual of the
small-landlord premium, and a replacement hold-out. After the stop, work on this model is
experiments, not refinement.

**Where that leaves the suite**: 10 registered xfails, none of them a phase-G regression, and
every one carrying its diagnosis and its falsification condition.

## What this model cannot do, and where refinement stopped (2026-09-17)

§13.12 says sourcing stops on purpose rather than on exhaustion. This is that stop applied to
the rent-cap work, and this section is the register it produces. **After it, work on this channel
is experiments, not refinement.**

### The suite is at 6 failed / 175 passed / 8 xfailed, and the count is misleading

Before §7.2 the suite read 0 failed. That number was not precision — it was concealment. The rent
cap under the statute in force produced a **rent rise of +16.6%**, and that failure lived inside a
fitted `hazard_scale` and a 0–2 dial, **labelled as not-reportable rather than tested**. A model
whose broken channel is annotated instead of asserted will always show fewer failures than one
whose breakage is under test. The six break down as:

| | |
|---|---|
| `test_rent_cap_reproduces_the_monras_co_movement` | **pre-existing**, unmasked. It was a strict xfail; §7.2b removed the marker because its recorded reason had been superseded. Same failure, now visible |
| `test_g1_the_co_movement_emerges_at_the_shipped_parameters` | **new test**. §7.2b's own declared falsification firing. Its failure is the finding |
| `test_non_resident_surcharge_removes_foreign_purchases` | **an improvement**. A strict xfail that now XPASSes, which pytest reports as a failure |
| `test_the_registered_xfails_show_red_in_the_panel` | bookkeeping, downstream of the row above |
| `test_forbearance_raises_the_arrears_stock_and_lowers_the_flow` | **genuine regression** |
| `test_rate_shock_cuts_transactions_before_prices` | **genuine regression**, missing its bound by 0.9pp |

**Two genuine regressions.** Both in the sale-side channel, both from one mechanism, both caused by
replacing a `[guess]` with evidence.

### What the rent cap can and cannot be used for

**Can**: the direction of the supply response, and its ordering across policies. The sign is
repaired in all ten seeds, the regime boundary in the growth anchor is gone, and the supply
response now varies with a measured quantity (the intermediation share) rather than with a dial.

**Cannot**: any magnitude. G1 fails at a Δln co-movement of **3.655** against the **0.07–3.2** span
Monràs & García-Montalvo report. The quantity leg reads **−48.2%** against the paper's own *"the
number of new contracts decreased by around 10% to 20%"*, and against Pérez García's −13%
tenancies, the second independent estimate and inside that band; the price leg reads **−16.5%**
against Monràs's −5%. Neither the number nor its confidence interval may be quoted.

> **FIGURES CORRECTED 2026-09-17.** This paragraph was first written on the pre-correction
> numbers — a 0.07–2.0 ceiling, a −46.6% quantity leg, point targets of −10% [Monràs] and −13%
> [Pérez García], and a "≈3.2×" price multiple. All four were superseded the same day by the G1
> ceiling correction recorded above, which read the ceiling and the quantity target at the source
> and found both misstated. The corrections were registered there but not propagated here for
> some hours. **The verdict is unchanged in every case** — G1 fails on the corrected ceiling too,
> which is what licensed making the correction — but the register was quoting its own superseded
> figures, and a limits register that cannot keep its own numbers current is not doing its job.

**And the excess is not where re-calibration could reach it.** At an intermediation share of 0.85 —
the top of the sourced regional band — leases still fall 26.8%. The model over-responds at the
extreme edge of what the evidence admits, so no setting within the sourced range reproduces the
measured response.

### Three things left deliberately outside, knowing they matter

1. **The forbearance inversion.** With the sourced selling cost, forbearance leaves **more**
   foreclosures (112) than its absence (103). The mechanism is coherent — a seller who cannot sell
   is a seller who forecloses — and the suspicion is that the test's claim, not the model, is what
   needs restating. Left open rather than repaired, because repairing it by moving another guess
   would re-form the guess-joint somewhere else and hide it again.
2. **The rate shock's volume leg**, missing its bound by 0.9pp for the same reason: a thinner
   baseline of sales to measure an incremental cut against.
3. **The magnitude of the rent-cap response**, above. Left outside, but **no longer unexplained**:
   the decomposition recorded earlier the same day locates it in turnover, not in the exit margin.
   What stays outside is the repair, not the diagnosis.

### What would reopen this

> **REWRITTEN 2026-09-17, because the condition first written here was aimed at the wrong term.**
> It read: *"something that makes some landlords hold on where the current two pieces make them
> all leave together"*, with a source for `small_landlord_premium` as the obvious candidate. The
> turnover decomposition recorded earlier the same day refutes the premise. The exit margin is the
> **small** term — the rented stock falls 6.5% while the flow falls 48.2% — and the residual is a
> 44.9% collapse in turnover. A condition written against the exit margin would have licensed
> reopening on evidence that could not move the quantity that is actually wrong. The superseded
> text is quoted here rather than deleted, because a register whose reopening condition can
> silently change is not a commitment.

Not a better parameter inside the sourced ranges — that is closed, measured, and unchanged by the
rewrite. What it would take is one of two things, and they are separable.

**1. The size of the escape segment, sourced.** Under `index_binds_all=True` every unit is capped
and no rent can rise to clear, so the model has no relief valve: market vacancy in the tensioned
zone **halves** (−49.7%) and rental tightness goes up **11-fold** (1.157 → 13.045). A market in
that state has no counterpart in the episode being matched — Catalonia 2020–22 is where the −5%
rent and −10% to −20% contract figures were measured. The episode had valves the model either
lacks or under-sizes: *contratos de temporada*, room lets, informal letting, and plain
non-compliance. The model has one, `MarketConfig.seasonal_evasion_share` at 0.15 of exits, and
that value has never been tested against what Catalonia actually observed. **What would reopen
this is a sourced estimate of how many would-be ordinary contracts left the ordinary segment**
under the cap — ≥2 independent sources, per the bias rule, and Incasòl's own quarterly series
splits contract types.

**2. Whether the tightness response is itself over-strong.** Tightness at 13 may be a correct
reading of a drained market, or it may be that the matching rule over-converts scarcity into
non-transaction. That is a question about the rental matching mechanism, **not about the rent cap
at all**, and it would be answered on the baseline rather than under a policy. If it is the
mechanism, the rent cap is only where the defect happened to become visible.

`small_landlord_premium` stays on the list, demoted. It is still the largest unsourced share on
the rent side, so sourcing it is worth doing on its own terms — but it acts on the exit margin,
and the exit margin is now measured as the small term. It is no longer the obvious candidate, and
sourcing it should not be expected to move the magnitude.

**And a ceiling that no reopening removes.** The 2008–13 hold-out is spent (§13.11). Even a green
G1 would be an in-sample result until a replacement hold-out exists, so the best outcome reachable
by either route above is "magnitude reportable, in sample, unvalidated out of it" — not
"magnitude reportable". Any reopening that does not say which of the two it is aiming at is
aiming at neither.

**Until one of those is sourced, this channel is finished.** It reports directions, it refuses
magnitudes, and it knows which of its own tests are red and why.

## Known gaps

- Boom-time rent growth (target 7r) — structural, see F4–F6 above and `model-spec` §10.
- Rent level and cash-purchase share, both exposed by the Funcas 104 contrast rows (F7).
- No second-home/other-province demand stream, no age or nationality structure in tenure, no
  landlord income taxation, no utilities — figures and consequences in `docs/funcas-104.md` §4.
- Zone price ladder compression (blocking for cross-zone claims — see above). Calibration
  evidence for the location-amenity fix now exists (Funcas 104 ch.5: Madrid/Barcelona wages
  +45%, cost of living +20%, net +21%); the mechanism decision does not.
- Sensitivity: Morris screening and Sobol indices are DONE (see "Sensitivity analysis" above).
  What they leave open is the finding, not the method: **`small_landlord_premium` explains 65% of
  the rent level, 75% of tensioned market vacancy and 62% of overburden, and its 1.8–2.5pp
  residual is declared unexplained (§7.1b)** — so the whole rent side stays direction-only.
  `buy_attempt_prob` is next (36% of the ownership rate, 34% of the zone price ratio), then
  `search_listings` (41% of the cash share). **Sourcing `small_landlord_premium`'s residual is
  the highest-value evidence work available on this model.**

  > **CORRECTED 2026-09-17.** This bullet read *"`overbid_sigma` explains 56% of the variance in
  > price-to-income and `landlord_required_spread` 65% of overburden, 74% of tensioned market
  > vacancy and 40% of the rent level — and both are unsourced guesses"*, on the 230 + 1,152 run.
  > `landlord_required_spread` **no longer exists** — retired in §7.1 on 2026-09-14 — and
  > `overbid_sigma` has left the screening entirely and is counted as sourced; price-to-income is
  > now a reportable magnitude, the opposite of what the bullet claimed. The list of gaps was
  > directing evidence work at a parameter that had been deleted from the model three days
  > earlier. Figures above are the phase-G re-run recorded in "Morris and Sobol re-run, and the
  > variance rule flips".
- Latin-hypercube moment fitting not needed yet — hand calibration hits the targets — but
  becomes necessary if targets tighten further. Four moments now sit at band edges.
- 2008-style bust reproduction untested end-to-end; a `CreditCrunch` intervention (tightening
  `max_ltv` / `max_dsti` / spread) is the natural next lever and would close §9.6's second half.
- Seller-side postponement (above).
