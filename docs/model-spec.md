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
| Foreign non-resident overlay | coastal (TENSIONED) prices, origin-country conditions (exogenous), the non-resident tax wedge | cash purchases at premium | not credit-constrained; exogenous volume stream ≈ 8% of purchases, ±cycle [household-owner §3]; budget × (1+base ITP)/(1+effective ITP) when a surcharge targets it [§8] |

## 4. Tick order

Exactly this order, expressed once in `engine.py`:

1. **Macro & policy update** — apply interventions active at this tick; update euríbor
   path, IRAV; government intents.
2. **Demography** — household formation (new aspiring households, landing by
   `formation_zone_weights` — metro-weighted 0.55 / 0.29 / 0.16, because Spanish household
   growth is where the tensioned markets are [EC Country Report 2026; INE ECP]), inter-zone
   migration; exits (death/dissolution ≈ formation × 0.35, guess), on which the **whole estate** passes
   to a surviving household — the home *and* any rental units, or dissolved small landlords
   leave orphaned stock behind that still behaves as a landlord. Foreign-buyer arrivals are
   generated in step 4 with the other purchase intents, not here: their arrival rate is
   conditioned on recent transaction volume, which is a market observable.
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
- Buyers bid min(willingness-to-pay, credit limit) on **one listing drawn at random from
  those they can afford** (not the best-affordability one): search is frictional and buyers
  do not observe the whole zone. This is what lets several buyers land on one listing and
  produce a bidding war; a best-affordability rule would spread bids evenly and suppress
  them. Bid ≥ reserve wins; price = highest bid (first-price; ties by rng).
- **Failed listing: ask decays** 2–5% per tick unsold (sticky-ask evidence: 2008–13 price
  grind over 6 years while volume collapsed [household-owner §4, bank §4]); seller
  withdraws after 4–8 ticks below reserve. Rental asks decay on the same rule but are
  **floored** at the landlord's required-yield rent (or the cap where one binds) and expire
  on the same clock: an unfloored, non-expiring rental ask grinds down without limit and
  drags the asking-basis index with it.
- Buyer WTP = budget share drawn around bank limit; foreign non-residents bid with
  premium (they transact at +76–79% €/m² nationally — modelled as higher budgets in
  TENSIONED coastal segment [household-owner §6]).
- **Aggregate buyers.** The foreign overlay and the large investor are aggregates carrying
  one agent id each, so a single buyer emits many independent offers per tick. The
  one-purchase-per-buyer-per-tick rule applies only to households; applying it to the
  aggregates throttles the whole non-resident stream to one purchase per zone per tick.

**Rentals: queue matching with reference index.**

- Asking rent = max(current yield target on unit value, last rent × (1+expected growth)),
  capped by regulation where active: within-contract IRAV cap; new-contract cap in
  tensioned zones; gran-tenedor index cap (`min(optimum, cap)` — cap acts as magnet
  from below too: asks below reference rise toward it [investor-large §3,
  rent-cap §2 Monràs]).
- Tenants accept if rent ≤ max_burden × income (max_burden ~ U(0.30, 0.40)
  [household-tenant §6]); else queue/share/stay.
- **The sharing margin.** A SEEKER's accepted burden rises with the length of its current
  search spell — `max_burden × (1 + 0.04 × ticks_searching)`, capped at 0.55 — and resets the
  moment it is housed. Sitting tenants keep their drawn threshold. Rationale: the acceptance
  threshold is *not* a fixed constant in Spain. Mean rent effort rose 26.5% (2015) → 31.7%
  (2021) → 29.7% (2022) of the consumption basket and the share of renting households above
  the 30% line 33.0% → 43.1% → 38.2% [EPF, Funcas 104 ch.6]; 4 in 10 tenants exceed 40% of
  disposable income, ≈2× the EU average [Eurostat via ch.2]; and the absorption channel is
  explicit — shared flats, sublet rooms, later emancipation [ch.4]. The ceiling is an observed
  level (vulnerable tenants: 40.6% on rent alone, 51.1% including utilities, ch.6 cuadro 3);
  the per-tick pace is a guess with range 0.02–0.06.
- **The contract clears at the ask, and that is a binding structural fact.** A queue-auction
  markup on top of the ask was implemented and removed: its measured effect was ≈0, because
  assortative matching already places each applicant on a listing at the top of what they can
  afford, leaving no headroom to bid up. So the clearing rent equals the winning applicant's
  willingness to pay, which is a share of income — and the *only* route for the rent index to
  outrun income growth is the level of burden households accept, i.e. the sharing margin above.
  This is why §9 target 7's rent leg fails: see §10 and docs/validation.md.
- **The shadow rent — what landlords compare a cap against.** `ZoneState.shadow_rent` is the
  rent a standard unit would fetch with *no* cap. In a free market it *is* the asking index.
  Under a cap the asking index is useless for that purpose: every posted ask is clipped, so
  the index collapses onto the cap within ~4 ticks and a landlord reading it sees no loss —
  the withdrawal decision went inert, which is how the Phase-7 gate broke unnoticed
  (validation.md R3). Landlords therefore fall back on what the zone's renters can pay: the
  median of accepted burden × income over all non-owner households in the zone (the
  engine's `renter_capacity`), scaled by its ratio to the asking index on the tick the cap
  switched on — the last free observation — and smoothed like the price index. It moves with
  incomes, the sharing margin and tenure transitions, and with nothing the cap or the exits
  cause within a quarter. Two queue-based anchors were tried and rejected, and the reasons are
  part of the specification: the *marginal* quantile (1 − listings/applicants) rises with
  every withdrawal and ran away (tightness 1.6 → 38, contracts 61 → 9 per tick in four
  years); the median of *this tick's applicants* falls under a cap because cheaper rents pull
  lower-income sitting tenants into the queue, and exits stopped after ten ticks. The exit
  hazard in `agents/landlord.py` uses `ln(shadow-based fundamental ask / cap)`; the posted ask
  still carries the queue-congestion premium, which under a cap cannot be charged and must not
  enter the exit decision either (measured: it turns exits into a spiral). The large investor's
  "cap binds" test reads the same shadow.
- **Insider/outsider split**: sitting tenants' rent moves only by the update cap;
  all price discovery happens at rotation (new contracts) [investor-small §3]. Reported as
  `insider_outsider_wedge` — a **rent-level** ratio, not a rent/income one. Matching is
  assortative (the queue sorts applicants by willingness), so entrants are selected on
  income and their *burden* comes out lower than sitting tenants' even while they pay
  strictly more for the same flat. The wedge the mechanism produces is a price wedge.
- **Three rent series, three bases** — do not conflate them:
  - `rent_*` — the index agents condition on. **Asking** basis (idealista-like): the median
    of live asks plus this tick's new contracts. Asking rather than transacted because the
    transacted median is composition-fragile (rich tenants leaving for ownership drag it
    down even in a shortage, flipping the sign of the cap response).
  - `rent_transacted_*` — median new-contract rent (SERPAVI-like). Runs slower, reproducing
    the real asking/contract wedge [household-tenant §7.4].
  - `reference_rent_*` — the official index agents are capped against: trailing new-contract
    median × (1 − cap_reference_discount), frozen to IRAV updates while a cap is active so
    the table cannot spiral downward on the market it is capping [plan.md Phase 4].
  - `rent_new_declared_*` / `rent_new_free_*` — new-contract medians split by regulatory
    segment (declared municipality or not, `agents/landlord.is_covered`), with their contract
    counts. Under partial coverage these are the reportable series: the pooled median mixes
    the two and moves with the mix (§10, validation.md T7).

  **Public rents are excluded from all four.** They are administered, not market signals;
  including them makes the parque social read as a market price cut.

## 5b. Location premium: why a metro dwelling is worth more than a rural one

A dwelling is a claim on a location as much as on a structure. Two dwellings of the same
quality in Madrid and in Teruel are not the same good, and the model has to say so explicitly,
because nothing else in it does: households bid only in their own zone, so without a stated
location value the zones are three copies of one market differing only in their households'
incomes.

**Rule.** Each zone carries a `location_premium` (`ZoneConfig`), a multiplier on what a
household is willing to pay for a standard unit there, normalised to 1.0 in `TENSIONED`:

```
budget = credit_limit · shade · (1 + momentum) · own_vs_rent · location_premium(zone)
```

It is a **discount on the low-amenity zones**, not a bonus on the metro, and that direction is
the whole mechanism. A bonus would do nothing: bids are clipped by the bank's credit limit
(§4 step 5), so a household told to pay more simply pays its ceiling. A discount binds
regardless of credit — a rural household that *could* borrow €137k does not offer it for a
rural dwelling, because the location is not worth it. Willingness, not ability, is what
separates the zones.

**Why the model needs it, measured.** Without it the tensioned/rural price ratio decays
3.20 → 1.84 over 60 ticks and rural price-to-income (8.4) passes the secondary city (7.4) and
approaches the metro (8.9) — the ordering §9 target 2 requires, inverted. The mechanism behind
that decay is *not* the median credit ceiling the earlier drafts of this file blamed: the
median non-owner's limit runs at 0.19–0.47 of the tensioned price and 0.58–0.69 of the rural
price throughout, so the median household can buy nothing anywhere and prices are set by the
upper tail of the distribution. What actually happens is that rural demand has no ceiling of
its own. Rural starts below replacement cost (€85,000 against a €97,200 hard cost), so no
developer builds there; its capacity is capped at 4.8 starts a tick against 4.9 households
formed; and the migration rule (§4 step 2) is downward-only, so every household priced out of
a metro is added to rural demand with no counterflow. Rural prices therefore climb to twice
replacement cost, which is where the ladder goes.

**What the premium is calibrated to.** The observed price gradient, not the wage gradient —
the two are different quantities and only the first is a price. Tinsa 2026Q1 provincial €/m²:
Madrid €3,565 and Barcelona €2,772 against Ciudad Real €776 and Zamora €881, i.e. metro/rural
≈ 3.5–4.5; capitals Madrid €4,600 against Palencia €1,256 [kb-refresh-2026-09 §5]. The wage
gradient is the *reason* such a premium can be sustained, and it is corroborating rather than
calibrating evidence: Madrid earnings +46% against the median Spanish city and +55% against
rural, elasticity of earnings to city size 0.0455 [De la Roca & Puga, REStud 2017]; Madrid and
Barcelona private-sector wages +45% against the rest of urban Spain, +21% after cost of living
[BdE Forte-Campos et al. via Funcas 104 ch.5]. Part of that wage gap is already in the model
as `income_multiplier` (1.15 / 1.0 / 0.80); the premium carries what is left, which is the
part households pay for the location itself.

**What it is not.** It is not a second income gradient (that is `income_multiplier`), not a
supply constraint (that is `supply_elasticity`, measured to move the ratio by 0.04), and not a
migration rule. Migration stays downward-only and rent-triggered; making it respond to the
price gap net of amenity is the natural next mechanism and is **not** part of this decision.
The premium is applied to purchase willingness only, not to the rent-acceptance threshold: the
30–40% screening band is a sourced behavioural norm [household-tenant §6] and rents follow
prices through the zone yield ladder without it.

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

## 6b. Supply: why land is the residual claimant

Starts respond to **price over hard cost**, not to an accounting margin:

```
start if   E[price] ≥ hard_cost · (1 + margin_threshold)
starts  =  base_starts · zone_share · (E[price] / reference_price) ^ supply_elasticity
```

`reference_price` = `median_value × price_multiplier × new_build_premium`, i.e. the level at
which the observed baseline flow (`base_starts_per_tick`, MIVAU) is what developers actually
build. Derived from config, not a free parameter. The exponent form makes
d ln(starts)/d ln(price) equal `supply_elasticity` exactly, so the sourced 0.45–0.58 range
[Caldera & Johansson; BdE] *is* the elasticity the model exhibits.

The reason it cannot be margin-driven: developers compete for sites, so any surplus above
hard cost plus the required margin capitalises into the **land price** — land is the residual
claimant, which is why realised margins cluster at 15–20% [IMPLICA/KPMG] across very
different price levels. Pricing land as a fixed *share* of the final price instead makes the
implied margin rise without bound as prices rise: measured in this model it reached 38%
(tensioned), 59% (secondary) and **103% (rural)**, which pinned starts against the capacity
ceiling at ≈184k/yr real against Spain's ≈110–130k. Volume, not margin, carries the signal.

Empirical signature, and an independent check on the whole rule: the Spanish index of urban
land price sat at 55 in 2023 against 100 in 2007, while the house price index recovered from
64 (2013–15) to 98 — land flat for a decade while house prices climbed [MITMA/INE via Funcas
104 ch.8 gráfico 3]. Behind it sits planned-but-unexecuted land for **6.78M dwellings**, 25.5%
of the existing park, stalled in approved planning for 20 years [Ministerio de Vivienda SIU
2023 via Funcas 104 ch.4 cuadro 1] — which is also why the land-release lever must show no
short-run price effect: the binding constraint is execution, not classification.

Unsold completed inventory is **re-priced every tick** at a markdown that widens with holding
time (2%/tick, capped at 25% — guess). Developers carry debt against stock and cut to clear;
letting a completion fall out of the market instead creates permanently dead supply.

## 7. Parameters

Full machine-readable table lives in `config.py` (typed dataclasses, each field
commented with unit + source + confidence). Headline rows (all sourced in dossiers §6):

| Parameter | Value / range | Unit | Source | Conf. |
|---|---|---|---|---|
| Household income distribution | lognormal: median 36,100, mean 46,300 (σ≈0.70); zone multipliers T 1.15 / S 1.0 / R 0.8 (guess) | €/yr | EFF2024 [household-owner §6] | high / guess (zones) |
| Tenant share by zone | T 0.27–0.30 / S ≈0.20 / R 0.12–0.17; national 20.2% renting + 6.5% ceded, owners 73.3% (ECV 2025, series low) | share of households | ECV 2024 regional; ECV 2025 national [household-tenant §6, kb-refresh-2026-09 §4] | medium |
| Owner-occupancy rate | 70.6% national (init target; EFF2024); 73.3% ECV 2025; by age <35 36.7 / 35–44 56.5 / 45–54 70.1 / 55–64 76.9 / 65–74 82.8 / >74 83.4 (EFF2024, DO 2610) | % households | EFF2024; INE ECV 2025 | high |
| Median dwelling value | 170,000 national; zone mult. T 1.6 / S 0.9 / R 0.5 (guess) | € | EFF2024 [household-owner §6] | high / guess |
| Gross rental yield by zone | T 4.7–5.6 / S 6.5–7.5 / R 7–9 | %/yr | idealista + BdE RBA [investor-small §6] | high |
| Max LTV (bank practice) | 0.80 (24% bunching); avg realized 0.63–0.67 | fraction | BdE IEF [bank §6] | high |
| Max DSTI | 0.30–0.40 (default 0.35) | fraction net income | bank practice [bank §6] | high |
| Mortgage term / spread | 25y; euríbor + 0.9–1.2pp; pass-through ~32%/16m, <100% | years / pp | BdE DO 2312 [bank §6] | medium |
| Transaction costs (buyer) | ITP 0.06–0.13 by zone (T 0.10 / S 0.08 / R 0.06 default) + 0.02 fees | fraction of price | OCU/CCAA [government §6] | medium |
| Household formation | 135k–260k/yr real (default 240k → 30/tick model-scale), scenario input | households/yr | EPA/INE [household-owner §6] | high (range) |
| Foreign purchase share | all foreigners 16.0% (Registradores 2026Q2, record) – 18.4% (Notariado 2S 2025); **non-resident ≈ 7.9–8.1%**, cash, TENSIONED-coastal, paying €3,063/m² vs €1,713 Spaniards (×1.8) | % purchases | Registradores ERI; Notariado CIEN; CaixaBank Research on MIVAU [household-owner §6, kb-refresh-2026-09 §4] | high (range); emergent share reported as `foreign_purchase_share` |
| Cash-buyer share (domestic incl.) | 0.23–0.29 (Registradores: 12-month 2025 29.3%, 2026Q2 23%) vs 0.46 (Notariado Jun 2026); Madrid ≈0, Baleares 23–40 | share | Registradores ERI; Notariado CIEN [bank §6, kb-refresh-2026-09 §4] | disputed between two like-for-like sources — range |
| Supply elasticity (long run) | 0.45–0.58 (possibly higher — Arrazola open q.) | dimensionless | Caldera & Johansson; BdE [developer §6] | medium |
| Construction lag | 8 (6–10) | quarters | Euroval [developer §6] | high |
| Developer margin threshold | 0.15–0.20 on cost | fraction | IMPLICA/KPMG [developer §6] | medium |
| Pre-sales gate | 0.30–0.50 of units | fraction | bank practice [developer §6] | high |
| Max annual output (national) | 150k–220k real (≈19–28/tick model) | dwellings/yr | CNC claim [developer §6] | low |
| Hard cost + land | 1,105–1,323 €/m²; land 25–50% of final price by zone | €/m² / share | UVE/ACR; CNMC [developer §6] | high / medium |
| Landlord required yield | bond + 3–5pp; +1–2pp in low-income zones | %/yr | derived [investor-small §6] | guess |
| Rental supply elasticity to rent cap | **0.0–2.0** (THE disputed parameter): Monràs & García-Montalvo 2025 give IV ≈2.0 (1.6–3.2) and OLS 0.07 on the same data; Jofre-Monseny ≈0 | Δln contracts/Δln rent | 3 Catalonia studies + CEPR DP20018 [rent-cap §4, Update 2026-09-08] | high (as range) |
| Seasonal-evasion share under cap | 0.05–0.25, ramp 4–6 ticks | share of new contracts | Incasòl [rent-cap §5] | medium |
| Tenant moving probability | 0.04–0.08 /tick, falls with sitting-discount | prob/quarter | derived [household-tenant §6] | low |
| Owner moving probability | 0.010–0.0125 /tick | prob/quarter | CED/BdE [household-tenant §6] | medium |
| Max rent burden accepted | 0.30–0.40 | fraction net income | screening norm [household-tenant §6] | medium |
| Within-contract update cap (IRAV) | **0.015 in model units** = 0.6–0.75 × the 2%/yr income anchor (IRAV 2.20% 2025, 2.44% Jun 2026 vs nominal wages ≈3–4%); range 0.012–0.020. Above the anchor the frozen reference index outruns the market and the cap unbinds (§10) | /yr, relative | INE IRAV; Ley 12/2023 [government §6, kb-refresh-2026-09 §1] | high (ratio) / medium (value) |
| Gran tenedor threshold | >10 units (≥5 in tensioned); Cataluña Ley 11/2026: ≥5 in Cataluña incl. natural persons, usage rights and co-ownership counted | dwellings | Ley 12/2023 art. 3.k; Ley 11/2026 (DOGC 13 Jul 2026, via law-firm summary) [investor-large §1, Update 2026-09-08] | high / medium |
| Large-investor rental-stock share | T 0.08–0.15 (guess from 2–8% national) / S 0.02 / R ~0 | share rental stock | BdE/Civio/Atlas [investor-large §6–7] | medium/guess |
| Large-investor yield hurdle | prime net 3.8–4.0 + political-risk premium | %/yr | CBRE [investor-large §6] | high |
| Actual tenant default incidence | 0.03–0.07 /yr; perceived = ×1.5–3 markup (guess) | prob/yr | Arag/OESA [investor-small §6] | medium / guess |
| Vacancy (urban baseline) | 6–9% of stock | % stock | INE [investor-small §6] | medium |
| Vacancy by municipality size (empty/park, Censo 2021) | <5k hab 24.6 / 10–20k 15.6 / 20–40k 13.1 / 40–150k ≈11.5 / 150–500k ≈8 / >3M 6.3; national 13.2 | % of local park | INE Censo via Funcas 104 ch.1 cuadro 1 | medium |
| Dwellings per household by zone | T 1.075 / S 1.124 / R 1.242 (national anchor 1.12) | dwellings/household | derived from the row above | medium |
| Withheld (non-mobilisable) share of the vacant pool | T 0.39 / S 0.63 / R 0.81 | share of zone vacant stock | gradient from Funcas 104 ch.1 §2; levels calibrated | guess (levels) |
| Average dwelling size | 90 | m² | Afi via Funcas 104 ch.5 | medium |
| Accepted rent burden under search | base × (1 + 0.02–0.06 /tick), ceiling 0.55 | fraction of gross income | EPF/Eurostat via Funcas 104 ch.2, ch.6 | mechanism high, pace guess |
| Household formation projection | INE vintages: 2022–37 215k → 190k → 140k; 2024–39 333k → 228k → 177k; **2026–41 205k → 139k → 93k** (17 Jun 2026; 1,024,156 / 696,381 / 463,511 per block). Observed: +226k (2025), +239k y/y to Jul 2026 (ECP) | households/yr | INE Proyección de Hogares (three vintages), INE ECP [kb-refresh-2026-09 §2]; `scenario.INE_HOUSEHOLD_PROJECTIONS` | high; the spread between vintages is the projection risk |
| Cash (unmortgaged) purchases | 0.23–0.29 (Registradores 2025–2026Q2) vs 0.46 (Notariado Jun 2026); the 0.608 implied by INE 2023 (973,637 sales / 381,560 mortgage deeds) is a scope/timing artefact, no longer the central value | share of purchases | Registradores ERI; Notariado CIEN; Funcas 104 ch.3 | disputed — range |
| Social rental stock | 1.0% (OECD) / 1.7% (Housing Europe-MIVAU) / 2.5% (Provivienda); EU 7–9.3% | % of stock | Funcas 104 ch.6, ch.8 | medium |
| Landlord IRPF reduction on residential rent | 50% general, 60% rehabilitated, 70% tensioned/young, 90% if rent cut ≥5%; cost ≈€1,039M/yr | fraction of net rental income | Ley 12/2023, AIReF via Funcas 104 ch.7 | high — NOT modelled |
| Vacancy-tax instrument | IBI surcharge 50–150% on ≥4 dwellings empty ≥2 yr ⇒ ≈0.1–0.8% of market value/yr | fraction of value/yr | Ley 12/2023 via Funcas 104 ch.7 | high |
| Rent-cap coverage | share of the capped zone inside DECLARED municipalities, applied as a PERSISTENT per-unit property (`Unit.declaration_draw`, drawn once at creation) so a municipality keeps its status and raising coverage adds municipalities monotonically: Spain Jul 2026 = 317 municipalities in 5 CCAA (Cataluña 271, Euskadi 18, Navarra 21, Galicia 2, Asturias 5), ≈9.3M people = 19% of Spain ≈ **0.42** of the model's tensioned zone; Cataluña 2024 ≈ 1.0. New contracts are reported split by segment (§10, validation.md T7) | share | BOE-A-2026-16532 (29 Jul 2026); MIVAU/Civio [kb-refresh-2026-09 §3]; `PolicyConfig.cap_coverage` | high |
| ITP surcharge, legal persons / gran tenedor | +0.10 over the 10% general rate (Cataluña 20% TPO on whole-building and gran-tenedor purchases, Ley 11/2026 in force 14 Jul 2026) | fraction of price | DOGC via law-firm summary [transaction-tax Update 2026-09-08]; `PolicyConfig.itp_investor_delta` | medium |
| ITP surcharge, non-residents | +0.90 over a 10% base = the "100% tax on non-EU buyers" bill (announced Jan 2025, stalled Mar 2026, folded into the stalled Jul 2026 omnibus decree); Baleares non-resident ban rejected Feb 2026 | fraction of price | Reuters/US News; Congreso [transaction-tax Update 2026-09-08]; `PolicyConfig.itp_foreign_delta` | proposal, not law |
| ICO guarantee wealth cap | €150,000 net wealth, added by the Jul 2026 adenda (with ≤35 y and ≤7.5×IPREM); line extended to 31 Dec 2027; uptake 8,549 ops / €206.6M guarantees to Oct 2025 (≈10% of €2.5bn) | € | BOE-A-2026-14404 (2 Jul 2026) [demand-subsidy Update 2026-09-08]; `PolicyConfig.guarantee_wealth_cap` | high |
| Tourist-rental (VUT) stock | 341,001 dwellings, May 2026 (−10.7% y/y; 1.28% of INE's 26.6M total stock); model seasonal units weight to ≈345k | dwellings | INE Estadística experimental de viviendas turísticas, 24 Jun 2026 | medium |
| Location premium | T 1.00 (numeraire) / S 0.85 / R 0.45 — multiplier on purchase willingness (§5b). Screened S∈{0.8,0.85,0.9,1.0} × R∈{0.4,0.45,0.5,0.55,0.7,1.0} on 1 then 3 seeds against every §9 gate; 0.85/0.45 is the pair that holds the ladder with every gate inside band | dimensionless | price gradient Tinsa 2026Q1 (provincial €/m² Madrid 3,565 vs Ciudad Real 776); wage gradient De la Roca & Puga REStud 2017, BdE via Funcas 104 ch.5 [kb-refresh-2026-09 §5] | direction sourced / level calibrated |
| Households (level) | 19,874,860 at 1 Jul 2026 (ECP) — the 1:2,000 anchor | households | INE ECP 2T 2026 | high |
| Formation zone weights | T 0.55 / S 0.286 / R 0.164 (None = household shares 0.45/0.35/0.20). Screened 0.45–0.65 on 3 seeds: 0.55 puts the tensioned queue at ≈1 applicant per listing (was 0.5) with every §9 moment in band | share of new households | EC Country Report 2026 Annex 16 (Madrid+Barcelona ≈27% of household growth), INE ECP; level calibrated [validation.md tensioned-tightness] | medium (direction) / guess (level) |
| Shadow-rent anchor | median renter paying capacity (burden × income) over non-owners, ratio to the asking index fixed at cap activation, smoothing = `price_index_smoothing` 0.3 | €/month, standard unit | mechanism (§5); no free parameter beyond the smoothing it shares with the price index | mechanism high |
| Exit hazard scale (`HAZARD_SCALE`) | maps the per-listing quarterly hazard onto the studies' annual contract elasticity; re-fitted after the shadow rent so elasticity 2 reaches Monràs's −10% contracts — value and sweep in validation.md / experiments/rent-cap.md | dimensionless | Monràs & García-Montalvo 2023/2025 (IV ≈2) | calibrated |
| Public social-rental stock | 1.5–3.3% of stock | % stock | MIVAU/Provivienda [government §6] | medium |
| Emancipation/formation age anchor | first purchase ≈41y; buyers 25–44 ≈ 62% | years | Fotocasa [household-owner §6] | medium |

Unsourced values are explicitly labeled `guess` in `config.py`. Zone multipliers are the
weakest block (developer §7.3, investor-large §7.1) — flagged for sensitivity analysis.

## 8. Interventions

One row per lever; mechanics per `policies/*.md §5`. All applied by `scenario.Intervention`
subclasses; effect direction = theory prediction, magnitude must EMERGE from clearing.

| Lever | Mechanically changes | Holder (veto point) | Key params (ranges) | Expected direction |
|---|---|---|---|---|
| Rent cap (`rent-cap.md`) | new-contract rent ≤ min(prev rent, reference index for gran tenedor/5y-vacant); within-contract IRAV; **coverage** = share of the zone inside declared municipalities (a per-unit draw, distinct from compliance) | State law, CCAA switch, **municipality-scoped**: 317 declared in 5 CCAA (Jul 2026), five CCAA refuse | supply-response elasticity 0–2; evasion 0.05–0.25; compliance 0.25–0.95; coverage 0.1–1.0 (Spain 2026 ≈0.42, Cataluña 2024 ≈1.0) | rents on regulated contracts 0…−11%; tenancies 0…−15% |
| Transaction tax (`transaction-tax.md`) | buyer cost wedge: households `max_bid = limit/(1+itp)`; the two cash aggregates (large investor, non-resident overlay) bid `× (1+base)/(1+effective)` so only a **change** moves them | CCAA | Δrate ±pp all buyers; **investor surcharge** (Cataluña 20% TPO on whole buildings/gran tenedor ⇒ +0.10); **non-resident surcharge** (100%-tax bill ⇒ +0.90) | volume −4…−15%/pp; capitalization 40–100%+ emergent; +0.90 on non-residents cuts their purchases ≈45%, not 100% — the +60% premium absorbs half the wedge (validation.md) |
| Vacancy tax (`vacancy-tax.md`) | holding cost on detected vacant units of ≥4-unit owners | Municipal | rate 0.001–0.03 of value; detection 0.0–0.9; mobilization 0.04–0.30/yr | vacant → rental supply; rent effect ≈0 (Vancouver null) emergent |
| Public housing (`public-housing.md`) | public units enter rental stock at 0.4–0.7 × market rent after lag | State funds, CCAA execute, municipal land | units/quarter by zone; crowd-out 0.0–0.8; lag 12–32 ticks | rents −0…−15% at high stock shares only |
| Tourist-rental restriction (`tourist-rental-restriction.md`) | VUT licence cap/phase-out; option value destroyed | Municipal/CCAA | conversion 0.10–0.50; evasion 0.10–0.50 | rents/prices −0…−4%/pp VUT share removed |
| Demand subsidy (`demand-subsidy.md`) | guarantee lifts LTV 0.80→0.95–1.00 for eligible **with liquid wealth ≤ cap** (ICO 2026 adenda: €150k); rent subsidy €250–300/m | State via banks | eligible share 0.05–0.50 FTB; wealth cap (150k; `inf` = pre-2026 instrument); budget cap FIFO | prices ↑ (capitalization 0–100%+ emergent, zone-dependent); access effect ~0.35–0.45; the wealth cap is nearly inert on tenant wealth distributions (≈1% of tenants above it) |
| Land release (`land-release.md`) | developer land stock +units after 20–60-tick lag; permit lag −0–6 ticks | Municipal/CCAA | elasticity multiplier 1.0–2.0 | prices: no short-run effect (validation!), long-run 0…−35% |
| Rate shock (bonus lever) | euríbor path shift | ECB (exogenous) | ±pp path | volume ↓↓, prices sticky (2022–23 signature) |

## 9. Validation (contract for Phase 6)

What may be *claimed* from a passing target is governed by the reporting contract (§13):
targets pass or fail here, but a passing target is not automatically a reportable magnitude.

Baseline (no intervention, 2015–2025-like inputs) must reproduce, before any scenario
result is reported:

1. **Tenure shares**: owner 70–74% (EFF basis; ECV 2025 gives 73.3% owners, 20.2% renting,
   6.5% ceded), tenant 24–27% national; tenant share ranking T > S > R [household-tenant §6].
2. **Price-to-income**: national 7–8 (2024–26 window); T > S > R
   [household-owner §6]. Both legs pass since the location premium (§5b): 8.35 / 6.24 / 4.78
   with national 7.15, and the tensioned/rural price ratio holds at 2.87 against its initial
   3.21 instead of decaying to 1.80 [validation.md L1–L3].
3. **Transaction volume**: 2.5–3.6% of households transacting/yr [household-owner §1].
4. **Construction volume**: completions ≈ 40–70% of household formation (2021–25 gap)
   [developer §1]. Measured as `completion_ratio` — this must be *measured*, not asserted
   "by construction": the margin hurdle and the pre-sales gate both move it.
5. **Rent burden**: market-tenant overburden (>40% income) **26.8–33%** on the Eurostat
   *tenant, rent at market price* basis (2025: 26.8%, 2024: 28.1%, 2023: 30.6% — the series is
   falling, so the band's lower edge follows it) — social tenants pay an administered rent and
   are excluded [household-tenant §6]; plus a positive insider/outsider wedge, measured on
   quality-adjusted rent *levels* (§5 explains why not on burdens).
5b. **Stock ownership cross-checks** (emergent, not inputs): individuals hold 85–92% of the
   rental stock [investor-small §1]; public rental ≈8% of the rental stock (1.7% of total
   stock); the household-share-weighted zone supply elasticity stays in 0.45–0.58.
5c. **Rent-burden second threshold**: the share of market tenants above **30%** of income must
   exceed the >40% share and is reported alongside it, because the Spanish literature quotes
   both lines and on different bases — 38.2% of renting households above 30% of their
   *consumption basket* (EPF 2022), 4 in 10 above 40% of *disposable income* (Eurostat)
   [Funcas 104 ch.2, ch.6]. Reported, not gated: the model measures burden on gross income.
5d. **Vacancy geography** (emergent): full-stock vacancy must rank **rural > secondary >
   tensioned**, with rural 15.6–24.6%, secondary 8.1–13.1% and national 10–15% — the INE
   Censo-2021 empty-dwelling ladder by municipality size [Funcas 104 ch.1 cuadro 1]. Half the
   Spanish empty stock is in municipalities under 20,000 inhabitants holding 28% of the
   population, and provinces growing slower than the 3.1% national household rate hold >60%
   of it. A model that spreads vacancy evenly gets this backwards and mislocates the whole
   vacancy-tax lever. The per-zone dwellings-per-household ladder that produces it must
   weight to the national anchor in `StockConfig`, and its *mobilisable* part
   ((upH − 1) × (1 − withheld_share)) is held equal across zones on purpose — see §10.
6. **Price-cycle amplitude**: demand boom + credit easing produces multi-year price
   growth 8–13%/yr; credit crunch produces volume collapse (−40…−85% lending) with
   price declines arriving slowly (−30…−45% over ≥5 years) [bank §4, household-owner §4].
7. **Hold-out episode (out-of-sample)**: 2021–2025 run-up — formation ≈240k/yr vs
   completions ≈90k/yr + rate shock 2022–23 + easing 2024–25 ⇒ prices +8–13%/yr
   sustained, transactions record-high, rents +8–11%/yr asking. Fit free parameters on
   pre-2021 moments only. **All three legs now pass.** The rent leg had failed since the
   model was built and is the one to read carefully: **+3.6%/yr ± 0.8 over 10 seeds, all
   positive** (was +0.0% ± 0.3pp), against a sourced +8–11%. It reaches ≈40% of the target,
   so the direction and the fact that rents outrun incomes are reproduced and the *magnitude*
   is not — do not size a rent-inflation claim on it [validation.md S4].
8. **Rent-cap credibility test** (Phase 7 gate): sweeping supply-response elasticity
   0→2 must span Jofre-Monseny (rents −4…−5%, tenancies 0), Monràs (−5%, −10%), and
   Pérez García (≈0 robust price effect, −13% tenancies) worlds [rent-cap §4]. **Status
   2026-09-08: met, with all three studies INSIDE the dial** (validation.md S3, 5 seeds):
   elasticity 0 → rents −4.9%, contracts +0.9%; elasticity 1.5 → −8.7%; elasticity 2 → rents
   −4.2%, contracts −13.6% ± 2.8, so Monràs's −10% falls between 1.5 and 2 and Pérez García's
   −13% at 2 — where the earlier fit needed ≈2.7 and was documented as out of range. Both legs
   are ordinary passing tests. The gate had silently failed after the August audit (the asking
   index collapses onto an active cap and blinded the landlord's exit decision, and the
   tensioned queue ran slack) and was repaired by the shadow rent (§5b), metro-weighted
   formation (§4 step 2) and two hazard re-fits. Partial coverage (`coverage` < 1) is **not**
   reportable on the pooled rent (T7).

Calibration: direct where observable (EFF distributions, lags, tenure); latin-hypercube
sweep on free parameters (λ, WTP dispersion, ask-decay, matching frictions) against
moments 1–6; Morris screening then Sobol on survivors; hold-out = moment 7.

## 10. Known limitations

- **No macro feedback**: income, employment, euríbor, migration are exogenous paths;
  the model cannot capture housing→GDP→housing loops (2008 amplification understated).
- **Zone types, not geography**: no within-zone heterogeneity, no specific cities; zone
  multipliers on costs/prices are guesses (flagged).
- **The zone price ladder is held by a calibrated premium, not by geography.** It used to
  collapse (tensioned/rural 3.2 → 1.8 over 60 ticks, rural price-to-income overtaking the
  secondary city); §5b's location premium fixes it (2.99 on 3 seeds, ordering 8.5 / 6.3 / 4.8)
  and both strict xfails are gone. But the premium's *level* is a calibrated guess, not a
  measurement: only its direction and existence are sourced. The model reaches a 3.0
  tensioned/rural ratio where Spain's provincial extremes run 3.5–4.5, and it should — its
  zones are broad aggregates, not provinces — so **cross-zone ratios are structurally right
  and quantitatively soft**. Report the ordering and the direction of zone differences; do not
  quote the ratio as a prediction. Its cost is visible in two national levels: purchase effort
  33.7% against BdE's 35–40% and ownership 69.3% against an EFF floor of 70%.
- **The shadow rent's growth is assumed, not observed.** Under a cap it grows at the
  exogenous income anchor (2%/yr), because both richer alternatives failed on measurement:
  renter paying capacity is composition-sensitive and lets a cap fade, and the untreated
  zones' index is contaminated by the cap's own displaced demand and runs away (+122% over 80
  ticks) [validation.md S1]. So the counterfactual ignores the cycle: in a boom the model
  understates a cap's bite, in a slump it overstates it. Cap results are reported on the
  16-tick window the empirical studies cover.
- **Foral territories** absent from AEAT-based sources [investor-small §7].
- **Quality/size ladder simplified** to a scalar quality tier; composition drift under
  caps (smaller flats, §rent-cap) only partially representable.
- **Informal market** (unregistered contracts, room rentals) only as evasion shares.
- **Boom rent growth reaches only ≈40% of the observed magnitude.** Rents *do* now outrun
  incomes — +3.6%/yr ± 0.8 against ≈0.6%/yr median non-owner income growth in the hold-out
  boom, all 10 seeds positive — through queue congestion pushing asks above the income anchor.
  That channel was always in the model and was inert only while the tensioned market ran
  slack. But Spain's own figures are +8–11%/yr asking (rent spend +27.7% against household
  income +16.6/22% over 2015–2022; Madrid rents +39% 2015–2022 [Funcas 104 ch.6, ch.2]; new
  contracts +37% against wages +26% 2015–24 [CCOO on IPVA]), and the missing half is the
  size/quality margin below: Spanish tenants absorbed rent growth partly by renting *less
  dwelling*, which a scalar-quality model cannot represent. **Report the direction, not the
  magnitude.** The congestion coefficient that would close more of the gap was swept and
  deliberately left alone — 0.15 buys 1.3pp and costs a 22% worse rent level and a rent-cap
  supply response that no longer reaches Monràs [validation.md S5].
- **Rents are priced per whole average dwelling, so tenant burden is overstated.** Every
  tenant rents one 90 m² unit at asking level. Spain's renters do not: EPF puts average rent
  actually paid at €516/month in 2022 (Madrid €675, Extremadura €277) against the model's
  ≈€1,350, and a young median earner in Spain crosses the one-third threshold at 30 m² and
  half their income at 45 m² [Funcas 104 ch.5, ch.6]. There is no small-dwelling, room or
  shared-flat segment, so the rent *level* row of the official contrast reads ≈2.6× high and
  the >30%-of-income share reads ≈59% against 38.2%. Levels of rent burden are not comparable
  to published Spanish figures; changes in them are.
- **Almost every purchase is mortgage-financed** (measured cash share ≈3%). The like-for-like
  Spanish figures are 23–29% unmortgaged (Registradores, 2026Q2 and 12-month 2025) and 46%
  (Notariado, Jun 2026); the 60.8% once derived from INE sales against mortgage deeds is a
  scope/timing artefact and is no longer the central value [kb-refresh-2026-09 §4]. Credit
  policy — rates, LTV, DSTI, guarantees — therefore still bites harder in the model than in
  Spain, by a factor of roughly 8–15 on the cash share. Fixing it needs the household wealth
  distribution and the inheritance channel to move together: 62,000 parental money gifts a
  year averaging €90k, tripled since 2019 [BdE via El Independiente, Jun 2026].
- **Under partial rent-cap coverage the POOLED rent series must not be reported.** The
  declared and non-declared parts of a zone share one queue, so a cap moves the mix as well as
  the price and the pooled median follows whichever segment is signing contracts (coverage
  0.42, elasticity 2: pooled +8.5% while the declared segment is +0.4% and the free one
  +8.5%). The segments are reported apart (`rent_new_declared_*`, `rent_new_free_*`, with
  contract counts) and *those* are the results; the pooled series is only meaningful at
  coverage 1. The spillover it exposes is real and matches Catalonia (validation.md T7), but
  the model produces it through one channel only — a shared queue plus downward migration —
  with no adjacent-market bidding, so treat its size as a lower bound.
- **The tensioned rental market's tightness is calibrated, not observed.** Formation is
  metro-weighted (0.55) to put the tensioned queue at ≈1.1 applicants per listing; the level is
  a guess with a sourced direction, and it sets frictional tensioned vacancy at 2.9% and
  ownership at 69.98% — the very edge of the EFF band. A per-CCAA formation series would
  replace the guess.
- **Reference-index indexation is read relative to the income anchor.** IRAV is 2.20–2.44%
  in Spain against ≈3–4% nominal wage growth; the model's anchor is 2%/yr, so
  `within_contract_update` is 0.015, not the nominal 0.025. At 0.025 the frozen reference
  outran the market and the cap unbound within ~10 ticks, ending +0.9% above baseline
  [kb-refresh-2026-09 §1]. Any nominal IRAV figure has to be rescaled by the same ratio.
- **Non-resident and investor buyers absorb tax wedges through their premium.** A +0.90
  surcharge on non-residents (the 100%-tax bill) cuts their purchases ≈45%, not 100%: the
  overlay bids at +60% and still reaches 0.7–1.06× the zone price after the wedge. In Spain
  the premium is largely *composition* (coastal, premium stock, €3,063 vs €1,713/m²), which
  the model represents as willingness-to-pay on the same stock — so the model likely
  understates how much a non-resident tax would divert purchases.
- **No second-home or other-province demand stream.** 50,000–60,000 purchases/yr, ≈10% of
  transactions, stable for a decade, on top of the ≈10% non-resident share the model does
  carry [MITMA via Funcas 104 ch.1]. Non-local demand is understated by roughly that much.
- **No age or nationality structure.** Renting is steeply graded on both: 42.7% of
  under-35-headed households rent against 7.5% of over-65s (83% of whom own outright), and
  66.3% of households whose main earner was born outside Europe rent against 11.6% of
  Spanish-headed ones [EPF via Funcas 104 ch.6]. EFF 2024 now gives the ownership ladder
  directly — <35 36.7% (+4.8pp, first rise since 2011), 35–44 56.5%, 45–54 70.1%, 55–64
  76.9%, 65–74 82.8%, >74 83.4%; bottom income quintile 53.1%, top decile 88.3% [BdE DO 2610]
  — and 44.3% of 26–34-year-olds live with their parents, 47.3% of them for affordability
  [INE ECV 2025 module]. Migration is the largest component of household formation
  (foreign-born 19.3% of residents, +626k in 2024) and lands almost entirely in the rental
  market; the model draws new households from one pool.
- **No landlord income taxation**, so the IRPF reduction on residential rent (50% general,
  up to **90% when a new contract cuts the rent 5%**, ≈€1,039M/yr, judged effective by AIReF)
  cannot be represented [Funcas 104 ch.7]. That is the one Spanish lever that pays landlords
  to lower rents, and it interacts with the rent cap.
- **No utilities**, so the Ley 12/2023 *sobreesfuerzo* definition (rent + community charges +
  water + energy) cannot be computed — the threshold that puts 60.5% of Spanish renting
  households above 30%, against 38.2% on rent alone [Funcas 104 ch.6].
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
   — both registered in docs/sources.md]. Not a §9 validation target; it is one row of the
   BdE contrast (`benchmarks.py`, §12).
2. **Purchase access share** (`buyer_access`) — share of the zone's non-owner households
   (tenants + seekers) whose bank limit `max_price()` (LTV + DSTI + upfront ITP/fees
   screen, §5, no state guarantee) reaches the zone price index. Emergent from the same
   credit rules the market uses — no new behavioural parameter. Higher = more accessible.
   National value = share over all non-owner households, each against its own zone.

Rationale: effort is the comparable-to-reality series (validatable against BdE);
access is the distributional one (moves when credit, prices or incomes shift who can
buy at all). Neither uses the guarantee boost — the indicator measures unassisted access;
guarantee policies show up as the gap they close in `buyer_access`.

## 12. Contrast against published official figures

`benchmarks.py` + the app's "Contraste oficial" tab. **Diagnostic, not a validation
gate** — §9 is the gate. Most rows are Banco de España; the rest are INE series (Censo, EPF)
compiled in Funcas *Estudios* 104 (docs/funcas-104.md), which is where the vacancy-geography,
rent-burden, rent-level and latent-demand rows come from, plus the registral and notarial
series added in the 2026-09 refresh (cash purchases re-based on Registradores/Notariado,
non-resident purchases, legal-person purchases — docs/kb-refresh-2026-09.md). Every row names
its own source and none of them is a forecast. Three rules, because a comparison table reads
as authoritative whether or not it deserves to:

1. **There is no BdE housing forecast to compare against.** BdE's quarterly projection
   tables contain zero housing rows — no house prices, no residential investment, no starts,
   no household disposable income, no mortgage rate (verified row by row,
   docs/external-forecasts.md §1). Only *actuals and structural diagnostics* are comparable.
   Forward-looking Spanish price paths exist, but from BBVA/CaixaBank/S&P/IMF-EBA, not the
   central bank. Never present a BdE contrast as a forecast comparison.
2. **Bases are converted explicitly, in code.** The model is 1:`metrics.SCALE` and quarterly;
   each row declares its conversion in `basis` and applies it in its own `model` callable.
   A comparison on mismatched bases is worse than no comparison, so the arithmetic is pinned
   in `tests/test_benchmarks.py` rather than trusted.
3. **The model clock is not a calendar.** 60 ticks is "≈15 years of a Spain-like market", not
   2011–2026, so rows compare the model's *settled phase* against BdE's own multi-year window
   (2021–2025) — never tick-to-year. Growth-rate rows carry an extra caveat: the baseline is a
   steady state and 2025 was Spain's strongest year in 18, so they are expected low. Contrast
   a boom against a boom scenario, not against the baseline.

Rows whose model side is a calibrated *input* rather than a result (household formation,
supply elasticity) are labelled as such: they verify the scale conversion, not the model.

## 13. Reporting contract

What the model is allowed to claim, and on what basis. This section governs every other
section: a result that violates it is not reported, however well it fits.

**The standard is the framing, not the outcome.** What is under the project's control is the
specification — which primitives, which assumptions, which evidence, and what the model
refuses to say. A realised future is not a test of the framing.

### 13.1 Reporting categories

Every quantity carries exactly one:

- **magnitude** — reportable as a number with a seed band. Requires: a sourced empirical band
  it is measured against, ≥10 seeds, and no `assumed` parameter above the variance threshold
  (§13.2).
- **direction** — reportable as a sign and an ordering only.
- **not reportable** — measured internally, used as a diagnostic, never quoted.

### 13.2 Variance rule

> No quantity is reported as a **magnitude** if an `assumed` parameter explains more than 25%
> of its variance in the Sobol decomposition.

Applied to the current model this downgrades to direction-only: `price_to_income`
(`overbid_sigma`, 56%), `rent_overburden_share` and the rent level
(`landlord_required_spread`, 65% and 40%), and tensioned market vacancy (74%). The rule sets
the evidence-work priority order without argument: source the parameter, or stop quoting the
number.

### 13.3 Derived-or-reduced-form rule

> Every behavioural rule is either **derived** from a declared primitive — an optimisation, an
> arbitrage condition, an accounting constraint — or explicitly labelled **reduced form**, with
> the episode that identifies it and the range the evidence admits. There is no third category.

A reduced-form rule with no identifying episode is a defect, not a simplification. The nine
rules currently failing this test are listed in `docs/assumptions.md`.

### 13.4 Calibration protocol

1. Calibrate on **2014–2025 moments only**. 2008–2013 is sealed (`docs/holdout-2008-2013.md`).
2. **Nothing measured is fitted.** A parameter with a direct Tier-1 measurement is data, not a
   degree of freedom.
3. Fitting order: LHS over free parameters → Morris screening → Sobol on survivors → variance
   rule applied → *then* the hold-out is run **once** and reported, pass or fail. A failure is
   reported as a failure. Re-fitting against the hold-out destroys it as evidence and is the
   one irreparable objection available against this project.
4. Runs cached to `runs/` with seed and config hash, with a pre-registration file committed
   before the run (`docs/prereg/TEMPLATE.md`).
5. Nothing is reported on fewer than 10 seeds once phase E has landed.

### 13.5 Falsification

Every mechanism in §5–§7 declares the observation that would kill it. A mechanism that cannot
fail is not saying anything, and is the objection most often fatal to public housing
commentary.

### 13.6 Adversarial referee pass

Each phase closes with an explicit hostile-reader pass: every objection answered **or conceded
in writing**. `docs/validation.md` "Honest qualifications" is the register; it is procedure,
not goodwill.

## 14. Exogenous boundary

What is outside the model by construction, enumerated in `docs/assumptions.md` §"Exogenous
boundary": macro feedback, employment and income paths, policy rates, foreign origin-country
conditions, geography below the zone, construction input costs, landlord taxation and
utilities, and unmodellable shocks. Being outside is not a defect. Leaving it unsaid would be.
