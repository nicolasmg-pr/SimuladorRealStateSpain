# Research & Development Plan — Spanish Real Estate Market Simulator

Step-by-step plan for gathering the evidence base and building the agent-based model.
Scope and method decisions are fixed here; the model spec (`model-spec.md`) is derived
from the research this plan produces.

## Goal

An agent-based simulation of the Spanish residential market that models the main actors,
their power and their relations, and — once calibrated — predicts how the market, and
especially prices, reacts to laws the government might implement.

## Fixed decisions

| Decision | Choice |
|---|---|
| Market | Spain, national |
| Spatial structure | Exactly 3 zone types: tensioned metro / secondary city / rural, as parallel sub-markets with household migration between them |
| Model design | Own model, built from gathered documentation. Not derived from any institution's existing model. Academic ABM literature is used for *technique* only (market clearing, validation methods) |
| Evidence standard | Thorough sourced dossier per actor before any behaviour code |
| Tick (proposed, confirm in Phase 4) | 1 quarter — matches the frequency of Spanish housing statistics |

## Bias-control method

Applies to every research step below. The goal is not "sources with no opinion" — those
barely exist in housing — but a process where no single viewpoint can steer the model.

1. **Two-tier sources.**
   - *Tier 1 — raw statistical series, used as data:* INE, Eurostat, MIVAU (transactions, visados, SERPAVI), Colegio de Registradores, Consejo General del Notariado, Agencia Tributaria exploitations, EFF microdata.
   - *Tier 2 — interpretive reports, never used alone:* Banco de España reports, Fedea, EsadeEcPol, Funcas, CaixaBank Research, CCOO/UGT, CEOE, tenant unions (Sindicat de Llogateres), landlord associations (ASVAL), portals (Idealista/Fotocasa research). Every Tier-2 claim is triangulated against at least one source from a *different* institutional viewpoint before entering a dossier.
2. **Every behavioural rule cites ≥2 independent sources.** Where sources disagree, the dossier records all estimates and the model takes a **parameter range, not a point value**. Sweeps and the UI explore the range.
3. **Disagreement is data.** Known example: the Catalonia rent-control evaluations conflict — Monràs & García-Montalvo (2022): ~−5% rents *and* supply decline; Jofre-Monseny et al. (2023): similar rent effect, *no* supply effect; Pérez García (2025): rent effect not robust, ~13% drop in new tenancies. The model must be able to reproduce *any* of these worlds by moving one exposed elasticity parameter, labeled in the UI with the competing estimates.
4. **Conditional predictions.** Output is always "under assumption set A → X; under set B → Y" — an ensemble over the disputed ranges, never one blessed number.

## Phase 0 — Research infrastructure (~half a day)

- [x] `sources.md`: register of every document used — source, institution, tier, viewpoint, URL, date fetched. No document informs the model without a row here.
- [x] Dossier template fixed (see `actors/` skeletons): Role & size → Balance sheet & constraints → Observed decision rules (with evidence) → Reaction to past shocks (case episodes) → Power & relations to other actors → Extracted parameters (value/range + sources) → Open questions.

## Phase 1 — Map the data landscape (2–3 days)

Catalogue the Tier-1 series; record coverage, granularity, and first/last period in `sources.md`. Download what is downloadable into `data/raw/` (gitignored if large). Starting inventory, from initial research:

- **Sale prices:** INE Índice de Precios de Vivienda (notarial transaction prices); Registradores statistics; MIVAU transaction counts and values; portal asking-price indices as a *listing price* complement (they measure asks, not deals — keep the distinction).
- **Rents:** **SERPAVI** (Agencia Tributaria + Catastro exploitation, 2011–2024, downloadable, down to census-section level, median + p25/p75) — the least politicized rent source available; portal rent indices as complement.
- **Households:** INE Encuesta Continua de Hogares; Censo 2021; **Encuesta Financiera de las Familias (EFF)** for income/wealth/debt distributions (produced at Banco de España, but it is raw survey microdata — Tier 1).
- **Supply:** MIVAU visados de obra nueva (~139k in 2025) and viviendas terminadas (~92k in 2025); land price statistics; INE Estadística de Hipotecas.
- **Credit:** mortgage rate and LTV statistical series (Tier 1 series, distinct from any institution's *reports*).
- **Tenure & stock:** Censo/Eurostat — ≈75% ownership, renting/ceded ≈26% and rising; social housing <3% of stock; foreign buyers ≈14–17% of transactions (Registradores).
- **Zones:** operationalize the 3 zone types from data — tensioned (official zona tensionada declarations + the >30% income-burden criterion of Ley 12/2023), secondary, rural. Extract per-zone price, rent, vacancy, construction series.

Deliverable: `data-landscape.md` — one table per topic: series, source, granularity, period, download link, quirks.

## Phase 2 — Actor dossiers (1–2 weeks)

One dossier per actor in `actors/`, filled one at a time, each claim with ≥2 sources. The seven actors and their key open questions:

1. **`household-owner.md`** — owner-occupiers & aspiring buyers. Income/savings distributions (EFF); observed price-to-income at purchase; how willingness-to-pay forms; the foreign-buyer segment as a demand overlay (≈14–17% of purchases, concentrated coast/islands).
2. **`household-tenant.md`** — tenants. Rent-burden distribution (share above 30%); mobility rates; access queues for protected housing. Tenant-union and landlord-association claims triangulated against SERPAVI/EFF data.
3. **`investor-large.md`** — grandes tenedores, SOCIMIs, funds. Share of purchases and of rental stock (housing SOCIMIs ≈35k units, concentrated in Madrid/Barcelona); yield hurdles; observed reactions to rent regulation (exit to sale? conversion to short-term rental?). Legal definition of gran tenedor (≥10 units, ≥5 in tensioned zones) matters — several levers apply only to them.
4. **`investor-small.md`** — small landlords, the dominant Spanish landlord type. Count and portfolio-size distribution; yield expectations; regulation response (Catalonia evidence, all three studies).
5. **`developer.md`** — construction lag (visado → terminada, ≈24 months); cost structure; the land constraint; supply elasticity (long-run estimates around 0.45 circulate — verify against ≥1 independent academic estimate; treat as a range).
6. **`bank.md`** — LTV/DTI caps in practice; rate pass-through; approval behaviour by borrower profile. Credit availability is the binding constraint that turns willingness-to-pay into ability-to-pay.
7. **`government.md`** — all levels. Inventory of *real* levers and who holds each one: Ley 12/2023 (zonas tensionadas, rent reference index, gran tenedor obligations), ITP/AJD and IBI (regional/municipal), vivienda protegida programs, tourist-flat licensing (municipal), golden-visa abolition (2025), demand subsidies (avales ICO). Regional competencies decide which levers a national government can actually pull — record this per lever.

Exit criterion: every dossier's "Extracted parameters" table filled, every row sourced or explicitly labeled a guess.

## Phase 3 — Policy evidence review (3–5 days, parallel with late Phase 2)

One file per lever in `policies/`: mechanism → Spanish/EU empirical evidence **for and against** → effect-size range. Priority levers:

- Rent caps (Catalonia 2020–22 under Ley 11/2020; 2024 wave under Ley 12/2023 — three conflicting studies already identified, all three go in).
- Transaction-tax (ITP) changes.
- IBI surcharge on empty homes / vacancy tax.
- Public & protected housing construction.
- Tourist-rental restrictions.
- Demand subsidies (avales ICO — standard theory predicts capitalization into prices; find empirical work both ways).
- Zoning / land release and permitting speed.

## Phase 4 — Model specification (1 week)

Fill `model-spec.md` completely; every decision rule must trace to a dossier row.

- Tick = 1 quarter; run length 40–80 ticks; 3 zones with migration.
- **Price formation:** sealed-bid per listing with reserve prices and asking-price decay on failure — reproduces bidding wars and sticky asks without a global auctioneer. Rental market analogous, with a SERPAVI-style reference index observable to agents (needed to simulate index-based caps).
- **Expectations:** adaptive extrapolation of recent price growth (the mechanism that produces cycles), extrapolation weight calibrated.
- **Credit binds before preference:** the bank approves against LTV/DTI before a household can bid.
- Parameter table: every parameter with units, range, source(s); unsourced = labeled guess.
- **Validation targets (contract for Phase 6):** tenure shares, price-to-income by zone, transaction volume, construction volume, rent-burden distribution, price-cycle amplitude, and one out-of-sample historical episode — e.g. the 2021–2025 run-up (household formation ≈240k/yr vs completions ≈92k/yr → sustained excess demand, prices +12.7% y/y at peak).

## Phase 5 — Implementation (2–3 weeks)

Order chosen so each layer is testable without the next; tests first per module; unskip the scaffolded tests as modules land.

1. `rng` — seeded streams (`test_same_seed_same_run` is the gate for everything after).
2. `config` — zone-typed configs.
3. `market/stock` — units with zone/tenure/quality (`test_conservation`).
4. `state` — registries, listings, indices.
5. `agents/*` — household, small landlord/investor, large investor, developer, bank, government (read-only `decide()` guard test).
6. `market/clearing` — sealed-bid sales + rental matching.
7. `engine` — tick order exactly as spec'd.
8. `metrics` — indicators defined once (`test_supply_shock_lowers_prices` as direction sanity).
9. `scenario` — the Phase-3 levers as `Intervention`s.
10. `cli` — headless sweeps to `runs/`, keyed seed + config hash.
11. `ui/app.py` — Streamlit: baseline-vs-scenario diff, per-zone series, and range sliders for disputed parameters labeled with the competing estimates.

Note: the scaffold has `agents/landlord.py` + `agents/investor.py`; Phase 4 decides whether they map to small/large investor or get renamed — dossiers 3–4 drive that.

## Phase 6 — Calibration & validation (1–2 weeks)

- **Direct calibration** for observable parameters: distributions from EFF, lags from visados→terminadas, tenure shares from Censo.
- **Fit the free parameters** by matching the validation-target moments (latin-hypercube sweep via `cli`, cached in `runs/`).
- **Sensitivity analysis:** Morris screening, then Sobol indices on the surviving parameters — standard ABM practice, and it identifies which *disputed* parameters actually move results, focusing follow-up research where bias would matter.
- **Hold-out validation:** reproduce one historical episode not used in fitting. No scenario result is reported before this passes.

## Phase 7 — Policy experiments (ongoing)

- Each lever from Phase 3 becomes a `scenario.Intervention`; run baseline vs scenario across the parameter-range ensemble; report **effect distributions per zone type**, not point predictions.
- First experiment: a Catalonia-style rent cap. Credibility test: the model must be able to span the range of the three empirical studies by moving the exposed supply-response parameter.

- [x] Claims ledger re-run against the current model (`docs/claims.md`, `src/resim/levers.py`,
  2026-09-15). The eleven published readings were computed in phase F, before the valuation
  anchor, the scarcity channel and the clearing calendar changed, so they no longer described
  the model. The sweep is now a module — `uv run python -m resim.levers --jobs 10` — instead of
  a hand-run whose artefact was gitignored. **Two verdicts move in substance**: F-4, where the
  tourist restriction's rent effect fell from −3.5% to −1.6% and thereby moved *inside* the
  Barcelona academic estimate instead of above it, and F-9, where the ICO guarantees now raise
  rents 2.2% (8/10) while still moving nobody across the ownership line. **F-5 gains a caveat**:
  the cap's rent leg deepened to −24.1% and is a registered defect, not a reading. And F-11
  sharpens — the credit crunch is now the largest price mover outright and its volume effect
  doubled to −18.6%.

- [x] The last three phase-G regressions, and the stopping rule (2026-09-15). Loss aversion was
  carrying one of Genesove & Mayer's two legs — the realised-price effect (3–18% of the nominal
  loss) now sits in the seller's reserve, and the price–volume correlation is back. The search
  effect's direction turned out to be an artefact of simultaneous clearing, so §5c.2 is rewritten
  around the measurement and `m` keeps its identification. And the rent cap was **applying the
  wrong statute to nine tenths of the market**: Ley 12/2023 binds the reference index on grandes
  tenedores only, everyone else on their own previous contract plus IRAV. Both regimes now exist
  (`RentCap.index_binds_all`), the Catalan evaluations are adjudicated against the Catalan law,
  and the current law's result — rents +16.6% through withdrawal — is published as **not
  reportable**, because its hazard was identified in the other regime. **`model-spec §13.12` now
  carries a stopping rule**: sourcing ends when every quantity a registered claim depends on is a
  magnitude or a published direction, with the bargaining weight, the premium residual and a
  replacement hold-out declared irreducible. After the stop, the work is experiments.

- [x] Phase 7 complete — **all seven levers now have write-ups** (`docs/experiments/`,
  2026-09-15), ten seeds each, each measured against its own dossier's effect-size range and
  labelled for what the reporting contract allows. Two are corrections rather than additions:
  **land release** was being measured on a 40-tick horizon with a 40-tick release lag, so every
  column read exactly zero — on 80 ticks it moves prices −1% at Spain's current pipeline and
  −7.5% to −12.9% with the lag halved, which overturns the ledger's F-3 "no effect"; and
  **public housing**'s price sign flips with crowd-out (+9.7% at 0.60, −1.2% at 0.10, both
  inside the dossier's admitted range), which is a conditional prediction rather than an answer.
  The other five: the ITP's capitalisation lands at ≈45% (sourced 40–100%) and its volume
  response just below the sourced band; the **vacancy tax does nothing measurable at any
  setting**, including six times the Spanish rate; the tourist restriction is worth ≈1% of rents
  at a full phase-out, inside the Barcelona estimate; the ICO aval capitalises, moves no one
  across the ownership line, and its wealth cap is inert. One prediction recurs and nothing
  registered can adjudicate it: **supply programmes lower prices and raise rents**, because
  killing expected appreciation forces the landlord's return into the yield (§7.1).

## Progress tracking

Mark phases done here; details and dates in commit history.

- [x] Phase 0 — research infrastructure
- [x] Phase 1 — data landscape (`data-landscape.md`; raw downloads to `data/raw/` deferred)
- [x] Phase 2 — actor dossiers (7/7)
- [x] Phase 3 — policy evidence review (7/7 levers)
- [x] Phase 4 — model spec
- [x] Phase 5 — implementation (all 11 modules; 12 tests green)
- [x] Phase 6 — calibration & validation (`validation.md`; Morris/Sobol pass still open)
- [x] Phase 7 — first experiment done and **re-run 2026-09-15**: the rent-cap dial no longer
  spans the three Catalonia studies (`experiments/rent-cap.md`). Under the statute they
  evaluate the rent leg is flat across the dial — the cap's level sets it, not the
  behavioural parameter — so the Phase-7 credibility gate is **not met** and the size of any
  rent-cap rent effect is not quotable. Previously recorded as met against a model that
  applied the index to every landlord (`experiments/rent-cap.md`); remaining levers implemented and runnable, experiments ongoing
- [x] Redesign phases 0, A and B (`docs/superpowers/specs/2026-09-11-model-redesign-design.md`):
  the precision contract and seven new targets; the model bug fixes; the profitability block
  (total-return hurdle, cash-buyer anchors, bidirectional migration). Detail
  in `docs/validation.md` and in the merge commits.
  **Two items of phase B's declared scope did NOT ship, and this entry listed them as delivered
  until 2026-09-17.** (1) **Buy-to-let entry** — measured and parked on branch
  `buy-to-let-remeasure`; nothing of it is on `main`, and `model-spec.md` cited a §7.3 it did not
  contain from three §9 targets and four places in `src/`. §7.3 now exists and records the debt.
  (2) **The AEAT-basis sibling column** for target 14 — never added; `landlord_household_share`
  is emitted on the EFF basis alone and the choice of basis is still open, not made. The
  misstatement mattered because targets 9 and 11 are strict xfails *for want of the first item*:
  the plan said the work that would close them was done, while the spec said those targets were
  already "fixed by" it.
- [x] Redesign phase C — insolvency and forced sale (`model-spec.md §6c`, branch `insolvency`,
  2026-09-14): income risk on an exogenous household-jobless path, arrears against a
  poverty-threshold consumption floor, statutory foreclosure (Ley 5/2019 art. 24, with the
  pre-2019 three-instalment regime as a switch for the hold-out), bank REO, `CreditCrunch` and
  `LabourShock` levers. Sixteen source rows retrieved first. Target 15 goes live: the arrears
  leg passes against the BdE doubtful ratio (2.9% against 1.6–3.4%), **the deliveries leg
  fails on arrival** (≈0.02%/yr against 0.10–0.16%) and is reported rather than banded away —
  distressed owners with positive equity sell before the lender can take the home, and the
  frictions that stop that in reality are phase D. Two defects it exposed were fixed at the
  source: the opening mortgage book was never screened against DSTI, and the income draw
  double-counted unemployment.
- [x] Redesign phase D — sale-side price formation (`model-spec.md §5c`, branch
  `price-formation`, 2026-09-14): ascending auction, search over m listings, seller reserve
  from the mortgage. Three sources retrieved first (idealista days-on-market distribution,
  Tecnocasa-UPF negotiation margin and bidder count, Fotocasa's negotiation survey). It
  **closed finding 2 on both sides** — five phase-B rent-side xfails fell to one change, the
  expectation moving from the buyer's budget to its valuation, because the landlord's
  reservation rent is a function of the sale value. `PARTICIPATION_RATE_SENSITIVITY` died as
  specified and **its falsification fired**: the rate channel is now weaker than the 2022–23
  episode, recorded as an xfail rather than patched, with the episode as it happened (rate
  rise + tighter standards) tested separately and passing. The negotiation margin (3.0%
  against 6.2%) and the boom's price leg (+3.9%/yr against a 4% threshold and a sourced
  8–13%) fail and are reported.
- [x] Redesign phase E — recalibration and the sealed hold-out (branch `recalibration`,
  2026-09-14). LHS over 37 free parameters, 200 points × 3 seeds: **no sampled point beat the
  shipped defaults**, so the fitting step adopted nothing. Morris (380 evaluations) then Sobol
  on the eight survivors (1,280 evaluations): `overbid_sigma`'s share of the price-level
  variance is down from 56% to **26%** — still above the 25% threshold, so the price level
  stays **direction only**, and after five phases the model reports two magnitudes and
  everything else as a direction. The validation fixture moved to ten seeds. Then the
  **2008–13 hold-out, run once**, pre-registered beforehand: three of six predictions passed,
  including the foreclosure flow at 1.34%/yr against CGPJ's ≈1.4% — the one both earlier
  phases had predicted in writing would fail. Prices overshoot (−57% against −30…−45%) and the
  arrears stock comes out at a third of the BdE's; both failures point at the same absence, a
  market with no brakes once it turns. Nothing was changed after the run.
- [x] Redesign phase F — the claims ledger (`docs/claims.md`, branch `claims-ledger`,
  2026-09-14). Eleven public claims, each quoted, attributed and dated, against the model at
  the only resolution phase E leaves it: directions on ten seeds with the sign count shown.
  Five new source rows for the claims themselves. The result the ledger exists to produce:
  **the levers that dominate public argument are the small ones** — a rent cap and a credit
  crunch move prices by 7–11% in this model while the vacancy tax, the land release, the
  guarantees and the tourist restriction do not move them measurably, and the largest single
  mover is lending standards, which no housing ministry sets. Two claims are marked
  unidentifiable rather than answered, which is the output the redesign spec asked for.
- [x] Brakes on a falling market (`model-spec §5d`, branch `market-brakes`, 2026-09-15) —
  the largest gap the hold-out left. Nominal loss aversion in the seller's ask
  [Genesove & Mayer 2001: 25–35% of the nominal loss, halved for investors, much lower sale
  hazard] and Código de Buenas Prácticas forbearance [RDL 6/2012 verbatim, gated by the
  umbral de exclusión, take-up from the scheme's own counts]. The calibration window does not
  move — loss aversion is inert in a rising market by construction and the ten-seed moments
  say so. Toggled in a synthetic bust it cushions the fall (−68.8% against −72.5%) and costs
  volume (10.8 transactions per tick against 63), which is its source's own price–volume
  correlation. **The 2008–13 episode is now spent as evidence** (§13.11): the model changed in
  response to it, so its re-run is a diagnostic — in which the forbearance predictions held
  (arrears 2.2% → 3.5%, foreclosures down, forborne peak ≈34,000 families) and the price
  prediction could not be settled, because a new RNG stream re-randomised the comparison.
- [x] Phase G — the valuation anchor, and `overbid_sigma` sourced (`model-spec §5c.6`, `§5c.7`,
  branch `source-overbid-sigma`, 2026-09-15). Five source rows: the per-sale idiosyncratic
  price dispersion is **6–17%** [Kotova & Zhang; Giacoletti RFS 2021; Landvoigt-Piazzesi-
  Schneider AER 2015], **no Spanish estimate is published** (INE and the Registradores both
  estimate it and publish only the index — a registered negative result), and the model read
  **2.3%**. Raising the parameter moved the price LEVEL, not the dispersion, because the
  valuation anchor was the median of winning prices and an auction selects on a high draw.
  Two candidate repairs were prototyped and refuted before the third was adopted. Fixing it
  exposed the larger finding: **phase D's scarcity-to-price channel was that selection** —
  halving construction used to add 2.0pp to annual price growth and added 0.18pp once the
  anchor was clean — so §5c.7 rebuilds the channel on budgets (buyers stretch toward their
  credit limit as the market tightens). Refit by LHS + focused grids; ten-seed suite green.
  Four **registered regressions**: the boom rent leg, the direction of the search effect, the
  rent cap's rent leg (now mechanical) and loss aversion's sign in a bust. **Morris + Sobol
  re-run** (390 + 1,536 evaluations, and the runner now takes `--jobs`): `overbid_sigma` is out
  of the Morris top eight and explains **5.7%** of the price level's variance against 26% in
  phase E and 56% in phase D. The variance rule's verdict is unchanged — two magnitudes,
  everything else direction-only — but the blockers are now `ask_markup` (0.42), 
  `price_index_smoothing` (0.26, which had no register row until now) and
  `small_landlord_premium` (0.68–0.93 on the rent side). **Sourcing those three is the new
  highest-value evidence work.**
- [x] `ask_markup` and `price_index_smoothing` sourced (2026-09-15, `docs/validation.md`).
  Smoothing is **measured**: the signal agents see is an appraisal, and regressing MIVAU's
  valor tasado on INE's IPV (two Tier-1 quarterly series, pulled and computed with) gives
  s = 0.307 ± 0.104 on the calibration window — the model ships 0.30. The ask markup's
  *outcome* is measured at 0.06–0.13 per dwelling (Tecnocasa 6.2% at sale plus idealista's
  in-listing cuts, 14% of listings at 7%), and it is **cyclical**: 27% in Oct 2012
  [Fotocasa]. But the model's realised discount is 3.9% against the sourced 6.2%, so the
  parameter is carried as *derived with a failing consistency check* and the price level is
  **not** promoted to a magnitude — closing §9 target 13c is now the last thing between the
  model and its first reportable price level.
- [x] §5c.8 — the tick is a quarter, the market is not (2026-09-15). `clear_sales` matched a
  whole quarter of demand at once, so every listing was a simultaneous auction. Offers arrive
  sequentially [Merlo & Ortalo-Magné; Merlo, Ortalo-Magné & Rust, 780 English properties], so
  the tick now clears in **three sub-periods — the months in a quarter, not a fitted number**.
  **Three registered failures closed at once and none by a parameter**: the negotiation margin
  (3.9% → **5.20% ± 0.10**, inside 4–12%, failing since phase D created it), the boom's rent
  leg (**+3.03%/yr**, and phase G's frontier with it), and the phase-D falsification on the
  rate shock — which passes again with nothing added to the rate channel. Re-fit inside the
  sourced bands: `tightness_half_saturation` 260 → 400, `ask_markup` 0.12 → 0.125.
  **Then the variance rule flipped**: on 1,792 fresh Sobol evaluations the largest unsourced
  share of the price level is `momentum_gain` at 0.109, so **price-to-income is the project's
  first reportable magnitude — 8.13, and 7.2–9.1 across the sourced parameter ranges** —
  together with transactions, completions, arrears, time to sale and bids per listing. The
  **rent side stays direction-only**: `small_landlord_premium`, §7.1's declared free parameter,
  explains 0.65 of the rent level, 0.75 of tensioned vacancy and 0.62 of overburden. So do the
  ownership rate and the zone price ratio (`buy_attempt_prob` 0.34–0.36), the cash share
  (`search_listings` 0.41) and the negotiation margin (circular). **Sourcing
  `small_landlord_premium` is now the highest-value evidence work**, and `buy_attempt_prob`
  after it.
- [x] `small_landlord_premium` bounded by its components (`model-spec §7.1b`, 2026-09-15). It
  cannot be measured directly — the observed yield minus the bond is what the hurdle predicts —
  so its legs were priced separately: tenant default at the rent-default insurance price (3–5%
  of rent), illiquidity over the **15-year-256-day** average holding period [Registradores ERI
  2020], and undiversified idiosyncratic risk from the §9 target-16 dispersion. **They sum to
  0.5–1.2pp against the 3.0pp the model needs.** Value moved 0.033 → 0.030 and the range
  narrowed 0.025–0.055 → 0.020–0.030; below ≈2.5pp the insider/outsider wedge inverts and the
  boom stops compressing the yield. The rural gross yield improves 15.6% → 13.1%. **The residual
  of 1.8–2.5pp is declared unexplained**, so the rent side stays direction-only: pricing
  regulatory risk, the occupation tail or management time — without double-counting
  `landlord_cost_share` — is the next job.
- [x] KB refresh 2026-09-08 (`kb-refresh-2026-09.md`): sources re-checked against Jul–Sep 2026 releases; INE projection vintages, rent-cap coverage, buyer-type ITP, ICO wealth cap, IRAV-relative indexation added. **Re-measurement found the Phase-7 rent-cap gate no longer met on the tenancy leg** (the August audit and Funcas revision changed the baseline and the experiment was not re-run) — fixed the same day by the tensioned-tightness revision (`validation.md` T1–T7): metro-weighted formation, a shadow rent under caps, hazard scale 3.0; gate met again on 5 seeds. Then partial coverage was made reportable by regulatory segment, and the location premium (`model-spec` §5b) closed the zone price ladder — the model's oldest known gap — restoring the price-to-income ordering and, unplanned, lifting cash purchases 3.1% → 18.7%. Then the shadow-rent anchor was made exogenous (two richer anchors measured and rejected), the hazard scale re-fitted so all three rent-cap studies sit inside the 0–2 dial, and boom-time rent growth passed for the first time (+3.6%/yr, ≈40% of the sourced magnitude) — **the suite now carries no xfails and every §9 target is met**. Open: the size/quality margin behind the remaining boom-rent gap; a per-CCAA formation series to replace the metro-weighting guess. **Morris screening and Sobol indices are done** (`src/resim/sensitivity.py`, validation.md, 230 + 1,152 evaluations): `overbid_sigma` explains 56% of the variance in price-to-income and `landlord_required_spread` 65% of overburden, 74% of tensioned market vacancy and 40% of the rent level — **both are unsourced guesses, and sourcing them is now the highest-value evidence work on this model**. Three weakly-sourced parameters (`max_starts_per_tick`, `presale_share`, `margin_threshold`) are inert and can be left alone
