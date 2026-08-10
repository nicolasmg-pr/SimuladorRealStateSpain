# Model spec

The authoritative description of what the simulation claims about the world.
Code that disagrees with this file is a bug in one of them.

Status: **Phase 4 complete** (2026-08-07). Every decision rule below traces to a dossier
row in `actors/` or a policy file in `policies/`; citations are given as
`[dossier §section]`. Disputed magnitudes are parameter **ranges** (bias-control rule,
`plan.md`); the UI exposes them as sliders labeled with the competing estimates.

## 1. Question the model answers

> Which interventions move Spanish residential prices and rents, in which direction, and
> how much — reported as effect distributions over the disputed parameter ranges, per
> zone type. Never one blessed number: "under assumption set A → X; under set B → Y".

## 2. Tick, horizon, scale

- **One tick = 1 quarter** (confirmed; matches IPV/INE/MIVAU/Incasòl frequency).
- Run length **40–80 ticks** (10–20 years). Default 60.
- **3 zone types** as parallel sub-markets with household migration between them:
  `TENSIONED` (Madrid/Barcelona metros + hot coast), `SECONDARY` (other cities),
  `RURAL`. Zone shares of households at init: 0.45 / 0.35 / 0.20 (approximation of
  Censo distribution — labeled guess; calibration may adjust).
- **Representative-agent scaling 1 : 2,000**: ~10,000 household agents ≈ 19.9M real
  households [household-owner §1]; ~13,000 dwelling units ≈ 26M stock. All counts
  reported per-model and re-scaled in `metrics.py`.
- All randomness flows from one seeded `numpy` Generator (`rng.py`); no module-level
  randomness anywhere.

## 3. Actors

`agents/landlord.py` = **small landlord** (individual, 85–92% of rental stock
[investor-small §1]); `agents/investor.py` = **large investor / gran tenedor**
(2–8% of rental stock, concentrated in TENSIONED [investor-large §1]). Decision made
here per plan.md Phase-4 note — modules keep their file names.

| Actor | Observes | Decides | Constrained by |
|---|---|---|---|
| Household (owner / tenant / aspiring buyer) | prices, rents, own income/wealth, mortgage rate, price growth (expectations), reference index | buy (bid), sell (list), rent (apply), move zone, stay | bank LTV/DSTI approval; down payment ≥ 20% + 10–12% costs [bank §3, household-owner §2]; rent ≤ 30–40% income screening [household-tenant §3] |
| Small landlord | own units' yield, market rents, reference index, alternative asset yield (bond), regulation, perceived default risk | set asking rent (≤ cap where bound), re-let / sell / hold vacant / shift to seasonal segment | required yield = bond + 3–5pp spread [investor-small §6]; within-contract update caps (IRAV) |
| Large investor | same + portfolio-level yield hurdle | portfolio buy (when yield ≥ hurdle) / sell unit-by-unit / price at cap | gran-tenedor rent cap binds them harder [investor-large §1]; hold period; prime net-yield hurdle 3.6–4.0% + spread over bond [investor-large §3] |
| Developer | zone price level, expected margin, pre-sales, land stock, permit lag | start projects; deliver after lag | margin ≥ 15–20% on cost; pre-sales ≥ 30–50%; land pipeline; max capacity [developer §2–3] |
| Bank | euríbor path, borrower income/wealth/age | approve/refuse mortgage, set rate | LTV ≤ 80 (bunching), DSTI ≤ 30–40, term ≤ 30y; slow pass-through [bank §3] |
| Government | scenario interventions | enact levers at their tick | competence split: CCAA switch for caps, municipal for IBI/VUT [government §5] — encoded per-lever in `scenario.py` |
| Foreign non-resident overlay | coastal (TENSIONED) prices, origin-country conditions (exogenous) | cash purchases at premium | not credit-constrained; exogenous volume stream ≈ 8% of purchases, ±cycle [household-owner §3] |

## 4. Tick order

Exactly this order, expressed once in `engine.py`:

1. **Macro & policy update** — apply interventions active at this tick; update euríbor
   path, IRAV; government intents.
2. **Demography** — household formation (new aspiring households), inter-zone migration,
   foreign-buyer arrivals; exits (death/dissolution ≈ formation × 0.35, guess).
3. **Expectations update** — each zone's trailing price/rent growth → agents' expected
   growth (adaptive; §6).
4. **Agent decisions** (read-only state → intents): households (list/bid/apply/move),
   landlords (rents, list/sell/withdraw), large investor (buy/sell blocks), developer
   (starts), bank (publishes credit menu: rate, max LTV, max DSTI).
5. **Credit screening** — bank approves each purchase intent (LTV, DSTI at current rate);
   ability-to-pay replaces willingness-to-pay before any bid enters the market
   [bank §3: "credit binds before preference"].
6. **Market clearing** — sales first (sealed-bid per listing), then rentals (queue by
   willingness, reference index caps applied). Produces `Trade`s.
7. **Settlement** — ownership, occupancy, balances, mortgages written by
   `clearing.settle()` only.
8. **Supply response** — developer completions arrive (lag pipeline), new units enter
   stock; construction starts enter pipeline.
9. **Metrics snapshot** — `metrics.snapshot()` appends one row.

Rationale: credit before clearing reproduces "volume adjusts first, prices sticky"
(2022–23: mortgages −18%, prices +4% [bank §4]); supply after clearing gives the
8-quarter completion lag its bite [developer §6].

## 5. Price formation

**Sales: sealed-bid per listing** (chosen in plan.md; reproduces bidding wars and sticky
asks without a global auctioneer).

- Sellers list at ask = expected value = last observed zone price × (1 + expected growth),
  with reserve = ask × (1 − max_discount), max_discount ~ U(0.05, 0.15) (guess).
- Buyers bid min(willingness-to-pay, credit limit) on the best-affordability listing;
  bid ≥ reserve wins; price = highest bid (first-price; ties by rng).
- **Failed listing: ask decays** 2–5% per tick unsold (sticky-ask evidence: 2008–13 price
  grind over 6 years while volume collapsed [household-owner §4, bank §4]); seller
  withdraws after 4–8 ticks below reserve.
- Buyer WTP = budget share drawn around bank limit; foreign non-residents bid with
  premium (they transact at +76–79% €/m² nationally — modelled as higher budgets in
  TENSIONED coastal segment [household-owner §6]).

**Rentals: queue matching with reference index.**

- Asking rent = max(current yield target on unit value, last rent × (1+expected growth)),
  capped by regulation where active: within-contract IRAV cap; new-contract cap in
  tensioned zones; gran-tenedor index cap (`min(optimum, cap)` — cap acts as magnet
  from below too: asks below reference rise toward it [investor-large §3,
  rent-cap §2 Monràs]).
- Tenants accept if rent ≤ max_burden × income (max_burden ~ U(0.30, 0.40)
  [household-tenant §6]); else queue/share/stay.
- **Insider/outsider split**: sitting tenants' rent moves only by the update cap;
  all price discovery happens at rotation (new contracts) [investor-small §3].
- Rent index (SERPAVI-analogue) = median of active contracts; **reference index**
  observable to agents = trailing median of new contracts × (1 − cap_reference_discount)
  — needed to simulate index-based caps [plan.md Phase 4].

## 6. Expectations

**Adaptive extrapolation with momentum** (this is what produces cycles):

```
E[g_{t+1}] = (1 − λ) · g_longrun + λ · mean(g_{t−3..t})
```

- λ (momentum weight) **range 0.5–0.9**, free calibration parameter, confidence low
  [household-owner §6 "price-expectation rule"]. Validated against: 2021–25 run-up
  (buying accelerates while affordability worsens) and 2022–23 (volume −11%, prices +4%).
- g_longrun = nominal income growth (exogenous, default 2%/yr).
- Same rule for rents (landlord side).

## 7. Parameters

Full machine-readable table lives in `config.py` (typed dataclasses, each field
commented with unit + source + confidence). Headline rows (all sourced in dossiers §6):

| Parameter | Value / range | Unit | Source | Conf. |
|---|---|---|---|---|
| Household income distribution | lognormal: median 36,100, mean 46,300 (σ≈0.70); zone multipliers T 1.15 / S 1.0 / R 0.8 (guess) | €/yr | EFF2024 [household-owner §6] | high / guess (zones) |
| Tenant share by zone | T 0.27–0.30 / S ≈0.20 / R 0.12–0.17 | share of households | ECV 2024 [household-tenant §6] | medium |
| Owner-occupancy rate | 70.6% national (init target) | % households | EFF2024 | high |
| Median dwelling value | 170,000 national; zone mult. T 1.6 / S 0.9 / R 0.5 (guess) | € | EFF2024 [household-owner §6] | high / guess |
| Gross rental yield by zone | T 4.7–5.6 / S 6.5–7.5 / R 7–9 | %/yr | idealista + BdE RBA [investor-small §6] | high |
| Max LTV (bank practice) | 0.80 (24% bunching); avg realized 0.63–0.67 | fraction | BdE IEF [bank §6] | high |
| Max DSTI | 0.30–0.40 (default 0.35) | fraction net income | bank practice [bank §6] | high |
| Mortgage term / spread | 25y; euríbor + 0.9–1.2pp; pass-through ~32%/16m, <100% | years / pp | BdE DO 2312 [bank §6] | medium |
| Transaction costs (buyer) | ITP 0.06–0.13 by zone (T 0.10 / S 0.08 / R 0.06 default) + 0.02 fees | fraction of price | OCU/CCAA [government §6] | medium |
| Household formation | 135k–260k/yr real (default 240k → 30/tick model-scale), scenario input | households/yr | EPA/INE [household-owner §6] | high (range) |
| Foreign purchase share | 13.8–18.4% of purchases; non-resident ≈ 8%, cash, TENSIONED-coastal | % purchases | Registradores vs Notariado [household-owner §6] | high (range) |
| Cash-buyer share (domestic incl.) | 0.30–0.40 of purchases | share | INE-derived [bank §6] | medium |
| Supply elasticity (long run) | 0.45–0.58 (possibly higher — Arrazola open q.) | dimensionless | Caldera & Johansson; BdE [developer §6] | medium |
| Construction lag | 8 (6–10) | quarters | Euroval [developer §6] | high |
| Developer margin threshold | 0.15–0.20 on cost | fraction | IMPLICA/KPMG [developer §6] | medium |
| Pre-sales gate | 0.30–0.50 of units | fraction | bank practice [developer §6] | high |
| Max annual output (national) | 150k–220k real (≈19–28/tick model) | dwellings/yr | CNC claim [developer §6] | low |
| Hard cost + land | 1,105–1,323 €/m²; land 25–50% of final price by zone | €/m² / share | UVE/ACR; CNMC [developer §6] | high / medium |
| Landlord required yield | bond + 3–5pp; +1–2pp in low-income zones | %/yr | derived [investor-small §6] | guess |
| Rental supply elasticity to rent cap | **0.0–2.0** (THE disputed parameter) | Δln contracts/Δln rent | 3 Catalonia studies [rent-cap §4] | high (as range) |
| Seasonal-evasion share under cap | 0.05–0.25, ramp 4–6 ticks | share of new contracts | Incasòl [rent-cap §5] | medium |
| Tenant moving probability | 0.04–0.08 /tick, falls with sitting-discount | prob/quarter | derived [household-tenant §6] | low |
| Owner moving probability | 0.010–0.0125 /tick | prob/quarter | CED/BdE [household-tenant §6] | medium |
| Max rent burden accepted | 0.30–0.40 | fraction net income | screening norm [household-tenant §6] | medium |
| Within-contract update cap | 0.02–0.03 /yr (IRAV regime) | %/yr | Ley 12/2023 [government §6] | high |
| Gran tenedor threshold | >10 units (≥5 in tensioned) | dwellings | Ley 12/2023 art. 3.k [investor-large §1] | high |
| Large-investor rental-stock share | T 0.08–0.15 (guess from 2–8% national) / S 0.02 / R ~0 | share rental stock | BdE/Civio/Atlas [investor-large §6–7] | medium/guess |
| Large-investor yield hurdle | prime net 3.8–4.0 + political-risk premium | %/yr | CBRE [investor-large §6] | high |
| Actual tenant default incidence | 0.03–0.07 /yr; perceived = ×1.5–3 markup (guess) | prob/yr | Arag/OESA [investor-small §6] | medium / guess |
| Vacancy (urban baseline) | 6–9% of stock | % stock | INE [investor-small §6] | medium |
| Public social-rental stock | 1.5–3.3% of stock | % stock | MIVAU/Provivienda [government §6] | medium |
| Emancipation/formation age anchor | first purchase ≈41y; buyers 25–44 ≈ 62% | years | Fotocasa [household-owner §6] | medium |

Unsourced values are explicitly labeled `guess` in `config.py`. Zone multipliers are the
weakest block (developer §7.3, investor-large §7.1) — flagged for sensitivity analysis.

## 8. Interventions

One row per lever; mechanics per `policies/*.md §5`. All applied by `scenario.Intervention`
subclasses; effect direction = theory prediction, magnitude must EMERGE from clearing.

| Lever | Mechanically changes | Holder (veto point) | Key params (ranges) | Expected direction |
|---|---|---|---|---|
| Rent cap (`rent-cap.md`) | new-contract rent ≤ min(prev rent, reference index for gran tenedor/5y-vacant); within-contract IRAV | State law, CCAA switch, zone-scoped | supply-response elasticity 0–2; evasion 0.05–0.25; compliance 0.25–0.95 | rents on regulated contracts 0…−11%; tenancies 0…−15% |
| Transaction tax (`transaction-tax.md`) | buyer cost wedge: `max_bid = limit/(1+itp)` | CCAA | Δrate ±pp; per buyer type (incl. gran tenedor 20% Catalan precedent) | volume −4…−15%/pp; capitalization 40–100%+ emergent |
| Vacancy tax (`vacancy-tax.md`) | holding cost on detected vacant units of ≥4-unit owners | Municipal | rate 0.001–0.03 of value; detection 0.0–0.9; mobilization 0.04–0.30/yr | vacant → rental supply; rent effect ≈0 (Vancouver null) emergent |
| Public housing (`public-housing.md`) | public units enter rental stock at 0.4–0.7 × market rent after lag | State funds, CCAA execute, municipal land | units/quarter by zone; crowd-out 0.0–0.8; lag 12–32 ticks | rents −0…−15% at high stock shares only |
| Tourist-rental restriction (`tourist-rental-restriction.md`) | VUT licence cap/phase-out; option value destroyed | Municipal/CCAA | conversion 0.10–0.50; evasion 0.10–0.50 | rents/prices −0…−4%/pp VUT share removed |
| Demand subsidy (`demand-subsidy.md`) | guarantee lifts LTV 0.80→0.95–1.00 for eligible; rent subsidy €250–300/m | State via banks | eligible share 0.05–0.50 FTB; budget cap FIFO | prices ↑ (capitalization 0–100%+ emergent, zone-dependent); access effect ~0.35–0.45 |
| Land release (`land-release.md`) | developer land stock +units after 20–60-tick lag; permit lag −0–6 ticks | Municipal/CCAA | elasticity multiplier 1.0–2.0 | prices: no short-run effect (validation!), long-run 0…−35% |
| Rate shock (bonus lever) | euríbor path shift | ECB (exogenous) | ±pp path | volume ↓↓, prices sticky (2022–23 signature) |

## 9. Validation (contract for Phase 6)

Baseline (no intervention, 2015–2025-like inputs) must reproduce, before any scenario
result is reported:

1. **Tenure shares**: owner 70–74%, tenant 24–27% national; tenant share ranking
   T > S > R [household-tenant §6].
2. **Price-to-income**: national 7–8 (2024–26 window); T > S > R
   [household-owner §6].
3. **Transaction volume**: 2.5–3.6% of households transacting/yr [household-owner §1].
4. **Construction volume**: completions ≈ 40–70% of household formation (2021–25 gap)
   [developer §1].
5. **Rent burden**: market-tenant overburden (>40% income) 27–33%; new-entrant effort >
   sitting-tenant effort (insider/outsider wedge) [household-tenant §6].
6. **Price-cycle amplitude**: demand boom + credit easing produces multi-year price
   growth 8–13%/yr; credit crunch produces volume collapse (−40…−85% lending) with
   price declines arriving slowly (−30…−45% over ≥5 years) [bank §4, household-owner §4].
7. **Hold-out episode (out-of-sample)**: 2021–2025 run-up — formation ≈240k/yr vs
   completions ≈90k/yr + rate shock 2022–23 + easing 2024–25 ⇒ prices +8–13%/yr
   sustained, transactions record-high, rents +8–11%/yr asking. Fit free parameters on
   pre-2021 moments only.
8. **Rent-cap credibility test** (Phase 7 gate): sweeping supply-response elasticity
   0→2 must span Jofre-Monseny (rents −4…−5%, tenancies 0), Monràs (−5%, −10%), and
   Pérez García (≈0 robust price effect, −13% tenancies) worlds [rent-cap §4].

Calibration: direct where observable (EFF distributions, lags, tenure); latin-hypercube
sweep on free parameters (λ, WTP dispersion, ask-decay, matching frictions) against
moments 1–6; Morris screening then Sobol on survivors; hold-out = moment 7.

## 10. Known limitations

- **No macro feedback**: income, employment, euríbor, migration are exogenous paths;
  the model cannot capture housing→GDP→housing loops (2008 amplification understated).
- **Zone types, not geography**: no within-zone heterogeneity, no specific cities; zone
  multipliers on costs/prices are guesses (flagged).
- **Foral territories** absent from AEAT-based sources [investor-small §7].
- **Quality/size ladder simplified** to a scalar quality tier; composition drift under
  caps (smaller flats, §rent-cap) only partially representable.
- **Informal market** (unregistered contracts, room rentals) only as evasion shares.
- **Pre-2008 regime** (appraisal inflation, 100%+ LTP, no pre-sales discipline) is NOT
  modelled; do not validate against 1997–2007 without a regime switch [developer §7.8].
- **Enforcement intensity** of caps poorly measured [government §7.1] — compliance is a
  swept parameter, not a prediction.
- Political-economy dynamics (which government enacts what, court reversals) are
  scenario inputs, not endogenous [government §3.5].

## 11. Derived indicators: housing affordability (accesibilidad de la vivienda)

Two indicators, defined once in `metrics.py` (per zone and national), reported every tick:

1. **Theoretical purchase effort** (`purchase_effort`) — BdE *Síntesis de Indicadores 1.5*
   basis: first-year debt service of a standard loan on the median dwelling
   (principal = `max_ltv` × zone price index, term = `term_years`, rate = current offered
   mortgage rate, quarterly annuity) divided by median gross **disposable** household
   income of the zone (gross × `DISPOSABLE_FACTOR`). Lower = more affordable.
   Real-Spain reference ≈ 0.35–0.40 in 2024–25 [BdE Síntesis 1.5; BdE Informe Anual 2025
   — both registered in docs/sources.md]. Not (yet) a §9 validation target; reference
   value shown in the UI for sanity.
2. **Purchase access share** (`buyer_access`) — share of the zone's non-owner households
   (tenants + seekers) whose bank limit `max_price()` (LTV + DSTI + upfront ITP/fees
   screen, §5, no state guarantee) reaches the zone price index. Emergent from the same
   credit rules the market uses — no new behavioural parameter. Higher = more accessible.
   National value = share over all non-owner households, each against its own zone.

Rationale: effort is the comparable-to-reality series (validatable against BdE);
access is the distributional one (moves when credit, prices or incomes shift who can
buy at all). Neither uses the guarantee boost — the indicator measures unassisted access;
guarantee policies show up as the gap they close in `buyer_access`.
