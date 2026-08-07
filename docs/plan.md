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

## Progress tracking

Mark phases done here; details and dates in commit history.

- [x] Phase 0 — research infrastructure
- [x] Phase 1 — data landscape (`data-landscape.md`; raw downloads to `data/raw/` deferred)
- [x] Phase 2 — actor dossiers (7/7)
- [x] Phase 3 — policy evidence review (7/7 levers)
- [x] Phase 4 — model spec
- [x] Phase 5 — implementation (all 11 modules; 12 tests green)
- [ ] Phase 6 — calibration & validation
- [ ] Phase 7 — policy experiments
