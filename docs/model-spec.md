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
8b. **Household balance sheets and insolvency** — incomes and savings accrue; the
   exogenous unemployment path is applied and its incidence drawn; mortgages amortise or
   fall into arrears; statutory foreclosure triggers mature, deliveries transfer the
   dwelling to the bank and the household to SEEKER with a credit lockout; the bank lists
   part of its repossessed stock (§6c). It sits *after* clearing on purpose: a dwelling
   repossessed this tick reaches the market next tick, which is the real sequence and
   keeps `clearing.settle` the only writer of ownership inside a tick.
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

## 5c. Sale-side price formation (phase D)

Phase 0 registered this as the model's second finding: the sale price was set by
`overbid_sigma`, a guessed dispersion parameter, and Sobol put **56% of the variance in
price-to-income** on it. A price level whose largest single driver is an unsourced scalar is
not a reportable magnitude (§13.2). Three mechanisms replace it, and each is identified
against an observable the model was not using.

### 5c.1 Ascending auction instead of a sealed first-price bid

Bidding was: each buyer draws a bid around the ask (`ask × N(1, overbid_sigma)`), highest
bid above the reserve wins **at its own bid**. So the price was the ask times a random
number, and the random number's standard deviation was a guess.

Now: bidders on a listing are ordered by what they are willing to pay, and the price is

```
n ≥ 2 bidders:   price = clip( second_highest + increment,  reserve,  highest )
n = 1 bidder:    price = reserve + θ · ( min(bid, ask) − reserve )
```

The two-bidder rule is the ascending (English) auction: the winner pays what it takes to
outbid the runner-up, never more than their own valuation. **Competition enters through the
bidder count**, which is an outcome of demand and supply rather than a parameter — which is
the whole point. The model can now close *above* the ask when several buyers land on one
listing, and Fotocasa's seller survey says that is a real event: 9% of negotiating sellers
raised the final price in 2024, against 6% a year earlier.

The one-bidder rule is a bilateral negotiation, split by a bargaining weight `θ`. It is the
only free parameter in the block, it is **declared reduced form**, and it is identified on a
registered observable: the Cátedra Tecnocasa-UPF measures the discount between asking and
sale price at **6.2% on average (2S 2025)**, and Fotocasa's survey gives the distribution
behind it — 53% of buyers negotiate, 80% of those obtain something, only 23% get more than
10% off. θ is set so the model's realised discount reproduces the mean, and the *shape* of
the distribution is then a prediction, not an input.

`overbid_sigma` survives, demoted exactly as the redesign specified: it is no longer
dispersion around a *price*, it is **idiosyncratic taste** — how much this buyer happens to
like this dwelling, applied to the value they put on it. A real friction, and one that can no
longer set the price level on its own. Whether it stays below the 25% variance threshold is a
question for phase E's Sobol run, and the answer is reported either way.

### 5c.2 Search over m listings

Buyers looked at **one** affordable listing drawn at random. That is why bidding wars
existed: buyers did not look. The rule is now that a buyer samples `m` affordable listings
and bids on the one with the largest surplus (value minus ask), so bid concentration is
endogenous — a well-priced dwelling attracts bidders, an overpriced one does not.

**Rewritten 2026-09-15.** Phase D justified `m` by a direction the model no longer has: it
claimed wider search *slows* the market (swept 75% → 21% sold inside the quarter as m went 1 →
8). Under the taste-neutral anchor and sequential clearing the direction is the opposite and
the sweep is flat — 0.503 (m=1), 0.661 (m=2), 0.686 (m=3), 0.691 (m=6) — because a buyer who
has compared two listings bids nearer its limit on the one it picks, and clears it. The old
reasoning survives only as an artefact of the simultaneous auction §5c.8 removed.

What did not change is the identification: the days-on-market distribution is a **level**, and
only m = 1 puts the model inside it (0.43–0.63). So `m` is still identified on the observable it
was always identified on, and the mechanism story attached to it is now the measured one.

`m` is reduced form and is identified against two observables:

- **Days on market** [idealista/data, 2T 2026]: 7% of dwellings sell in under a week, 19%
  within the month, 27% within three months, 36% within the year and 11% take longer — so
  ≈26% inside a month, ≈53% inside a quarter, ≈89% inside a year. The model's tick is a
  quarter, so the testable statement is the share of listings still unsold after one, two and
  four ticks.
- **Bidders per dwelling** [Cátedra Tecnocasa-UPF]: an average of **seven potential buyers
  per dwelling** in 2S 2025, double the figure two years earlier. Read with care and gated
  loosely because of it: Tecnocasa counts *interested parties on its own agency files*, the
  model counts *bids placed*. Every bid is an interested party; not every interested party
  bids. The model's number should sit at or below seven, and the doubling in two years is the
  part that identifies the mechanism, because it happened while supply fell 16% and demand
  rose 30% — exactly the ratio `m` operates on.

### 5c.3 Seller reservation from the mortgage

The reserve was `ask × (1 − U(0.05, 0.15))`: a guess, and the register said so. It is now

```
reserve = max( outstanding debt + selling costs,  ask × (1 − max_discount) )
```

Two legs, and the first one is accounting rather than behaviour. **A household in negative
equity cannot convey clear title below what it owes**: the sale has to repay the loan. No
elasticity is invented — the lock-in follows from the LTV distribution, which is BdE data
(bunching at 0.80 at origination, 70% on Tecnocasa's 2S-2025 file, realised average 0.63–0.67
across the stock), and from the price path the model itself produces.

This is the mechanism behind "volume adjusts first, prices are sticky", which the model has
been reproducing with `PARTICIPATION_RATE_SENSITIVITY = 20` — a hand-fitted coefficient on
the mortgage rate, one of the twenty rules the register counts as failing the
derived-or-reduced-form rule. **It dies here.** A rate shock now reaches volume through the
credit screen (fewer buyers clear the DSTI cap) and through the reserve (owners who bought at
the top cannot sell into a lower market), both of which are accounting, not coefficients.

The second leg keeps a floor under the reserve when there is no debt — an outright owner with
no mortgage still refuses a derisory offer. `max_discount` stops being `U(0.05, 0.15)` and
becomes the measured negotiation margin: mean 6.2% [Tecnocasa-UPF], with only 23% of
negotiated sales beyond 10% [Fotocasa], so the range is 0.04–0.12.

### 5c.4 What this is checked against

| Indicator | Anchor | Status |
|---|---|---|
| `median_ticks_to_sale` | idealista/data: ≈53% inside a quarter, ≈89% inside a year | gated from phase D (target 13 stops being "reported, not gated") |
| `sale_discount_median` — (ask − price) / ask over transactions | Tecnocasa-UPF 6.2%; Fotocasa's tail (23% beyond 10%) | gated |
| `sales_above_ask_share` | Fotocasa: 9% of negotiating sellers raised the price | reported, not gated — the bases differ |
| `bidders_per_listing` | Tecnocasa: seven interested parties per dwelling, doubled in two years | reported, gated only as an upper bound |
| `locked_in_share` — owners whose debt exceeds what the market would pay | emergent; no Spanish series measures it directly | reported |

**Falsification.** If the auction cannot reproduce the days-on-market distribution at any `m`
in 1–10, the search mechanism is wrong. If removing `PARTICIPATION_RATE_SENSITIVITY` destroys
the rate-shock signature (volume falls first, prices lag), then the coefficient was carrying
something real and the reserve does not replace it — in which case the honest outcome is to
say so, not to put the coefficient back with a new justification.

### 5c.5 What happened when it was built (2026-09-14)

Measured on 3 seeds, 60 ticks, last 20 averaged; the full table is in `docs/validation.md`.

**The mechanism that had to be added, and was not in the redesign spec.** The auction alone
did not produce a scarcity-to-price channel, and the reason is worth recording: a buyer's
valuation was anchored on the price index, so `price ≈ index × (a selection premium in the
taste draw)`, and the premium is proportional to `overbid_sigma`. That swaps one dispersion
dependence for another — with σ small the price cannot respond to competition at all, and
with σ large σ sets the level again. What closes it is where the *expectation* enters:
`MOMENTUM_GAIN × expected growth` used to shade the buyer's **budget**, where the index cap
in clearing threw it away for every buyer whose credit limit exceeded market value. Moved
onto the **valuation anchor**, it reaches the price: excess demand raises prices, the rise
feeds the adaptive expectation (§6), and the loop runs until credit binds. The gain was
re-identified when the channel moved (5.0 → 2.5) on calibration-window moments only —
price-to-income and the BdE's 35–40% purchase effort — never on the 2021–25 hold-out.

**What it closed.** Five gates that phase B had left as dated strict xfails, all of them
rent-side, all of them recorded as "phase D's to close", and all closed by exactly the
mechanism those notes predicted: the landlord's reservation rent is a function of the
dwelling's *value* (§7.1), so once the sale price responds to scarcity the rent floor does
too. The insider/outsider wedge is **+5.1%** (was −6.3%, the wrong sign); a rent cap now cuts
contract rents **−3.6%** (was +4.9%, the wrong sign) and cuts contracts **−11.1%** at
elasticity 2, so Monràs & García-Montalvo's −5%/−10% pair sits inside the dial; coverage
scales the cap as a ceiling rather than as a magnet; and boom-time rent growth holds.
**Finding 2 — no scarcity-to-price channel — is closed on both sides by one change.**

**What it broke, and what that means.**

- *The rate-shock magnitude.* This is the falsification above, and it fired. With
  `PARTICIPATION_RATE_SENSITIVITY` gone, a +2.8pp euríbor shock cuts volume **1.6%** against
  the 5% the gate asserts (prices −1.1%, so the ordering survives). The coefficient was
  carrying something the mechanisms do not reproduce. It is **not** reinstated: the gate
  becomes a dated strict xfail, and the episode as it actually happened — a rate rise *and* a
  tightening of standards, both documented in the BdE lending survey — is tested separately
  and passes (volume −5.5%, prices −1.5%) on mechanisms rather than on a fitted elasticity.
- *The 2021–25 boom's price leg.* +3.88%/yr ± 0.17 over 10 seeds against a 4% threshold that
  was itself a compromise (the sourced episode is +8–13%/yr). The model reaches ≈40% of the
  observed magnitude, which is about where it was before phase D; what changed is that the
  boom is now produced by expectations reaching the price rather than by a fitted
  participation term. Split out as its own xfailing test so the volume leg stays live.
- *The negotiation margin.* 3.0% against a measured 6.2%. The model's sale market is more
  competitive than Spain's on both identifying observables — 3.6 bids per listing and 17% of
  sales above the ask against Fotocasa's 9% — and those are the same fact: with more bidders
  the auction runs the price to the runner-up's valuation and leaves nothing to negotiate
  away. Closing it means fewer buyers per listing, which is `buy_attempt_prob` (an admitted
  guess on the demand side), not the auction this target exists to test.

**Where the price level now comes from.** Not from `overbid_sigma`: halving it moves
price-to-income by less than 25%, where the pre-phase-D model had 56% of that variance on it.
It comes from credit capacity and the expectation loop, and the model sits at price-to-income
**7.78** with purchase effort **36.6%** — inside the BdE's observed 35–40%, which is the
check that says the level is being set by something real. Whether `overbid_sigma` is under
the 25% variance threshold is phase E's Sobol question, and the answer is reported either
way.

### 5c.6 The valuation anchor: what buyers value off, and what sellers post off (2026-09-15)

Sourcing `overbid_sigma` (docs/sources.md, 2026-09-15) exposed a defect in the block phase D
built, and the defect is more interesting than the parameter.

**The parameter.** Its empirical counterpart is exact: the dispersion of log sale prices for
the same dwelling, net of location × period. Three independent studies measure it — Kotova &
Zhang (US zipcodes 2012–16, repeat-sales × hedonic with house fixed effects: mean **16.8%**
per sale, p10 11.2, p90 22.6), Giacoletti (*RFS* 2021, California: **6.8–12.4%** per sale) and
Landvoigt, Piazzesi & Schneider (*AER* 2015, San Diego: **6.2–9.8%**). Their conversions differ
and matter: a round trip carries the error twice, so a published *return* dispersion is √2
times the per-sale one. **Band adopted: 6–17% per sale, central 10%** (§9 target 16). No
Spanish estimate exists — INE's IPV and the Registradores' IPVVR (Calhoun's variance function
on 1,274,958 sale pairs) both estimate the quantity and publish only the index — and the
absence is registered rather than papered over.

**The defect.** The model measured **2.3%**, and raising the parameter did not widen the
distribution: it moved the price level, from a price-to-income of 7.8 to 10.0, which is the
credit ceiling. The reason is that a buyer's valuation was `price_index × quality × taste`,
the index is the median of *winning* prices, and an auction selects its winner on a high
draw. The selection premium was therefore capitalised into the next tick's valuations, every
tick, with nothing nominal to stop it. At σ = 0.02 the loop was invisible; at the measured σ
it runs until credit binds. So the parameter was not a dispersion knob that happened to move
the level — it was holding the level down by being too small.

Two candidate repairs were prototyped and **refuted** before this one was adopted, and both
refutations are kept because they bound what the mechanism can be:

- correcting each transacted price by the expected order statistic of its own auction (κ(n),
  then κ(n, m) to include the search draw) made the level *worse* and then absurd — a
  closed-form correction cannot know that the realised price was clipped by the budget, the
  reserve or the ask;
- a user-cost ceiling (transacted rent capitalised at the mortgage rate plus maintenance minus
  expected growth) never binds: it sits at ≈ 40 years of rent against a price of ≈ 15.

**The mechanism.** Two indices, kept apart on purpose:

| | basis | who uses it |
|---|---|---|
| `ZoneState.price_index` | realised transaction prices | every reported indicator, expectations, the landlord hurdle's `V` |
| `ZoneState.valuation_index` | the same sales **repriced at an average taste draw** | buyers' valuations, and sellers' asks |

The neutral price is not a formula applied to the outcome. Each auction is run **twice**
through the same `auction_price` rule: once with the bids as drawn, once with the same
bidders' valuations recomputed at ε = 1, with the budget cap, the reserve, the ask and the
bargaining weight all still binding where they bound. That is why it survives the three
clipping mechanisms that defeated the closed-form correction, and it is carried on the
`Trade` as `neutral_price` rather than reconstructed later.

Sellers post off the neutral index too. Posting off the realised one re-opens the same loop
through the ask, measurably: the level goes back to moving with σ (price-to-income 6.6 → 8.3 →
9.1 across σ = 0.02 / 0.15 / 0.30).

**What this buys, beyond the parameter.** The ask markup carried two numbers that could not
both be true: the practitioner rule of thumb of **15–20% over the expected price** and the
realised gap between ask and sale of **6.2%** [Cátedra Tecnocasa-UPF 2S 2025]. Under a neutral
anchor the difference between them *is* the selection premium, so the model can now reproduce
both at once, and doing so is the test of the block rather than a calibration convenience.

**Falsification.** If the neutral-anchored price level still moves with `overbid_sigma` by
more than seed noise, this section is wrong. Measured on arrival: 6.38 / 6.40 / 6.44 across
σ = 0.02 / 0.15 / 0.30, against 7.81 / 9.53 / 10.01 before. Re-measured in the shipped block
(with §5c.7): 8.09 / 8.14 / 8.28 across σ = 0.10 / 0.20 / 0.30 — flat over the sourced band.
**Below the band it is not flat** (5.19 at σ = 0.01): with almost no idiosyncratic variation
prices collapse toward the reserve. The claim holds where the evidence puts the parameter, and
nowhere else, which is the honest scope of it.

**What the variance rule says afterwards.** Sobol on 1,536 evaluations puts `overbid_sigma`
at **5.7%** of the variance in price-to-income (phase E: 26%; phase D: 56%) and
`tightness_half_saturation` at 4.1%. The price level is still direction-only, but now because
of `ask_markup` (0.42) and `price_index_smoothing` (0.26) — which is the rule working as
intended: it moved the evidence queue rather than blessing the parameter that was measured.

**Shipped values (phase-G refit, docs/validation.md).** `overbid_sigma` 0.20 (delivers 8.0%
dispersion), `ask_markup` 0.12, `seller_bargaining_power` 0.25, `search_listings` 1,
`tightness_half_saturation` 260, `buy_attempt_prob` 0.64. The bargaining weight moved because
of arithmetic rather than taste: with the reserve floored at ask × (1 − d), a one-bidder price
θ of the way from reserve to ask gives a discount of (1 − θ)·d, so at θ = 0.85 the model could
not reach the measured 6.2% at any markup.

**The frontier this block cannot cross, recorded because it is a property and not an
accident.** `search_listings` trades the boom's rent leg against the negotiation observables:
m = 1 gives price-to-income 8.07, a 3.9% discount, 20% of sales above ask and +1.2%/yr boom
rent; m = 2 gives 8.07, 2.0%, 39% and +4.2%/yr. Raising the markup to pull m = 2's above-ask
share down puts the level out of band (8.96). m = 1 ships; the boom rent leg is a registered
strict xfail rather than a widened gate.

### 5c.7 Market tightness in the bid — the scarcity channel, rebuilt (2026-09-15)

§5c.6 cost the model something it was not entitled to. With the valuation anchor de-biased,
the same supply experiment that used to move prices barely moves them:

| starts/tick | price-to-income, before §5c.6 | growth | after §5c.6 | growth |
|---|---|---|---|---|
| 8 (scarce) | 8.56 | +4.24%/yr | 6.69 | +1.31%/yr |
| 14 (baseline) | 7.81 | +3.16%/yr | 6.61 | +1.24%/yr |
| 20 (ample) | 7.19 | +2.25%/yr | 6.51 | +1.13%/yr |

Halving construction used to add 2.0pp to annual price growth; with the anchor fixed it adds
0.18pp. **Phase D's claim that "competition enters through the bidder count" was the taste
order statistic being capitalised, not scarcity** — the bidder count did move (4.0 → 5.8) and
the price did not follow it. Finding 2 of the redesign spec is therefore re-opened by this
phase, and closed here by a different mechanism.

**The mechanism.** A buyer who loses an auction searches again, and what losing costs depends
on how many buyers there are per listing. In a slack market losing costs a tick; in a tight one
it costs a year, so the buyer stretches toward the most its credit line allows:

```
tightness = buyers in this zone this tick / listings in this zone this tick
stretch   = tightness / (tightness + k)
bid       = base + stretch · max(0, budget − base),  base = min(budget, anchor · quality · ε)
```

At `stretch → 0` the bid is the dwelling's worth to this buyer; at `stretch → 1` it is the
credit limit, and the market clears against the **budget distribution** — income, LTV and
DSTI, all sourced. That is the point: scarcity now reaches the price through the credit
constraint rather than through a dispersion parameter, which is what the redesign asked for
and what the sale block has never actually had.

`k`, the buyers-per-listing at which a buyer bids halfway to its limit, is **reduced form** and
declared as such. It is identified on the 2014–25 price-income wedge and on the cross-zone
price ratio, jointly with `overbid_sigma`, the ask markup, the bargaining weight and `m`
(§9 targets 2, 2b, 13, 16). Range 4–90 buyers per listing.

**Falsification.** Two ways this dies. If the supply experiment above still fails to move
prices at any `k` inside the range, the channel is not in the bid and the model is missing
something else. If matching the wedge requires a `k` so low that buyers bid their credit limit
in a *slack* market, the mechanism is doing the work of a fitted constant and should be
labelled one.

### 7.1b What the small-landlord premium can be justified by (2026-09-15)

`small_landlord_premium` is §7.1's one free parameter and the Sobol run makes it the most
expensive one left: it explains **0.65 of the rent level, 0.75 of tensioned market vacancy and
0.62 of overburden**, so the whole rent side is direction-only while it is unsourced. It cannot
be measured the obvious way — the observed yield minus the bond is the quantity the hurdle
exists to predict — so it is bounded here by pricing its components separately.

| Leg | What prices it | Per year, as a share of value |
|---|---|---|
| Tenant default and eviction | Rent-default insurance, **3–5% of annual rent** (one comparator 5–8%), underwritten by DAS, ARAG, Mutua de Propietarios, Caser, Mapfre. An insurer's premium is what an undiversified owner pays to shed a risk a diversified one need not insure. × a 6.6% contract yield | **0.20–0.33pp** (0.33–0.53pp on the wider quote) |
| Illiquidity | Selling costs 4–7% of value (agency 3–5%, notary/registry/plusvalía 1–2%), amortised over the average holding period — **15 years 256 days** [Registradores, ERI 2020, on 251,269 sales; the 2009 minimum was 7 years 106 days] | **0.25–0.45pp** (0.55–0.96pp at the 2009 horizon) |
| Undiversified idiosyncratic price risk | The per-sale log-price dispersion this project sourced for §9 target 16, 6–17%, incurred twice per round trip and annualised as 2σ²/H, priced at risk aversion γ ∈ 2–5 and a wealth share w ∈ 0.3–0.6 | **0.03–0.37pp** at H = 15.7 (0.07–0.58pp at H = 10) |
| **Sum** | | **0.5–1.2pp**, and ≈2pp only under the shortest horizon and the widest insurance quote |

**The model needs 3.0pp.** Below 2.5pp two §9 targets fail — the insider/outsider wedge turns
negative and the boom stops compressing the yield (target 10, the one §7.1 identifies this
parameter on) — so the value was moved 0.033 → **0.030** and the declared range narrowed from
0.025–0.055 to **0.020–0.030**, the overlap of the old fit with the derivation. The suite is
green there, and the rural gross yield, the model's oldest failing target, improves from 15.6%
to 13.1%.

**The residual is the finding, and it is not being papered over.** Roughly 1.8–2.5pp of the
shipped premium has no component behind it. Three candidates, none priced here: regulatory risk
after Ley 12/2023 (cap exposure, the gran-tenedor thresholds, tenure-security extensions), the
occupation tail (a landlord-side survey puts a quarter of landlords in litigation over it, and
the selection in that number is obvious), and the small landlord's own management time, which
may already sit inside `landlord_cost_share` and must not be counted twice. Until one of them is
priced, the parameter stays **unsourced for the variance rule** and the rent level, tensioned
vacancy and overburden stay direction-only.

**Falsification.** A Spanish estimate of the required return of small landlords, from a survey
or from a revealed-preference study, outside 2.0–3.0pp. Or a component that closes the residual
and is shown not to be double-counting `landlord_cost_share`.

### 5b.1 The rent cap is two statutes, not one (2026-09-15)

The model applied the reference index to every landlord in a capped zone. Spain's law does not,
and the difference is most of the market.

| | who is capped | at what |
|---|---|---|
| **Ley 12/2023** (in force) | gran tenedor (≥10 dwellings, ≥5 in the area) | the reference index |
| | every other landlord | its own previous contract, uprated by IRAV |
| | …with no contract in the last five years | **nothing** — art. 17.6 has nothing to anchor on and art. 17.7 binds grandes tenedores only |
| **Ley 11/2020** (Catalonia, 2020–22) | every landlord | the index |

Individuals hold 85–92% of the Spanish rental stock, so applying the index universally is a far
harder cap than the one the statute imposes. `agents/landlord.cap_level` carries both and
`RentCap.index_binds_all` selects; the default is the law in force. The previous-contract anchor
survives the tenancy (`Unit.last_contract_rent`), because the statute looks back five years —
zeroing it on vacancy, as the model did, promoted every small landlord back to the index regime.

**Which regime a test or an experiment runs is now part of its statement.** The three Catalan
evaluations measure Ley 11/2020, so the targets drawn from them run that regime. Under the law
in force the model produces a rent **rise** (+16.6%, ten seeds) as withdrawal outruns a cap that
binds one landlord in ten — and that number is **not reportable**, because `hazard_scale` was
identified when the index bound everyone and nothing has re-identified it here. It is published
in `runs/levers_10seeds.json` as `rent-cap-state-law` so the gap is visible rather than hidden,
and re-identifying that hazard for the current statute is the one piece of rent-cap work this
project leaves open. **§7.2 below is that work**: it retires the hazard rather than
re-identifying it.

**Outcome (2026-09-16).** §7.2 was written and implemented, and it **failed**. The arbitrage
condition is frictionless: once the cap breaks the reservation rent, the cumulative shortfall over
any horizon beats a one-off transaction cost, so nearly every capped landlord sells at once. The
cap now **raises** tensioned rents 53.6% and costs 78.7% of new leases under **Ley 11/2020 as
well** — the regime it is calibrated against — so the rent cap is no longer reportable in either
statute, in size or in sign. The paragraph above said the +16.6% under the statute in force was
out-of-regime extrapolation; it is now superseded by a refutation that covers both regimes. F4 was
**not run**: this section's own procedure gates it on the three Ley 11/2020 tests being green, and
they are red, so spending the Ley 12/2023 evidence on a mechanism already known to be broken would
have bought nothing. The repair is §7.2b.

### 7.2 The withdrawal margin, from the reservation rent (2026-09-16)

§7.2 has been cited since phase A — here, twice in `docs/validation.md` and once in
`config.CapResponseConfig` — as the arbitrage condition that would replace the rent cap's fitted
`hazard_scale`. It was never written. This section is it.

**What it replaces.** `agents/landlord.decide` currently reaches the withdrawal branch whenever
the cap binds at all, and then draws against a fitted scale factor:

```
if fundamental_ask > cap and complies:
    gap    = ln(fundamental_ask / cap) · (1 + holding_years · growth_wedge)
    p_exit = min(0.9, rental_supply_elasticity · hazard_scale · gap)
```

`hazard_scale` is calibrated so that `rental_supply_elasticity = 2` reproduces Monràs &
García-Montalvo's co-movement under Ley 11/2020. That is why the Ley 12/2023 result is
out-of-regime (§5b.1): the scale factor carries a regime inside it.

**The condition.** `agents/landlord.decide` already computes the reservation rent one screen
earlier — `floor = required_rent(state, unit.zone, value)` — and uses it only as a floor on the
ask. §7.2 promotes it to the decision variable:

```
cap ≥ r_req → list at the cap. No withdrawal.
cap <  r_req → evaluate the alternatives; leave to whichever wins.
```

**The trigger is the change, not the arithmetic.** Today any binding cap generates exit hazard,
including one that binds and still clears the landlord's hurdle. Under §7.2 a cap that binds but
leaves `cap ≥ r_req` produces **zero** withdrawal. This is the property phase A reached for and
did not get: removing the additive hazard floor made a cap that binds on *nothing* cost nothing,
but a cap that binds *a little* still started the hazard the instant `ask > cap`. The landlord's
own margin sits between the cap and its reservation, and §7.2 puts that margin in the trigger.

**A dependency retired as a side effect.** The exit decision stops depending on `shadow_rent`.
The comment at `agents/landlord` records two earlier versions that failed on the choice of
comparison quantity — the posted ask (the cap unbound, the asking index collapsing onto it) and
the congestion-inflated ask (a spiral, tenancies −50 to −87% at elasticity 2). The third works
but rests on a quantity **inferred from the queue** in `engine._update_indices`. `r_req` is
inferred from nothing: it is built from `V`, the bond, π, E[g] and `c`.

#### The branches

| branch | rule | quantities |
|---|---|---|
| stay let at the cap | default while `cap ≥ r_req` | `cap`, `r_req` |
| **seasonal** | if the segment is open and the landlord falls in the diversion | `seasonal_evasion_share` 0.05–0.25 [Incasòl — counts] |
| **sell** | cumulative shortfall over the horizon exceeds the cost of leaving | `holding_years`, `selling_cost_share` |

The sale rule integrates a **widening** shortfall rather than multiplying the instantaneous one:
the cap grows at the statutory IRAV while `r_req` grows with `V` and E[g], so the gap compounds
over the horizon. This keeps phase A's insight — the growth divergence compounds the shortfall —
as an accounting term inside the calculation instead of a multiplier on a hazard.
`wedge_annualisation` survives as what it is, four quarters; `within_contract_update` stays
statutory. No double-counting of appreciation: `r_req` already nets E[g], so `r_req − cap` is the
monthly shortfall against the best alternative use of the capital, appreciation included.

**Vacancy is not a branch, and that is a finding.** On flows, holding empty returns
`− vacancy_tax·V/12` against a strictly positive capped rent. Vacancy is dominated by letting at
*any* cap, however harsh. The 15% of withdrawals that sit empty are not landlords choosing
vacancy — they are units **waiting for the sale channel to clear**, which takes time because
`clear_sales` matches over sub-periods. So `exit_split_vacant` dies with a mechanism behind it.
The share of withdrawn units standing empty *should* become a model output, checked against
evidence, rather than an input assumed — but that is a declared gap, not something this branch
built: no such metric exists in `metrics.py`, and nothing checks it yet.

**Branch order, and the natural experiment that tests it.** Seasonal is evaluated **before** sale,
because leaving to seasonal pays no transaction cost and selling does: whoever exits prefers the
cheap exit. That yields a comparative static with a dated experiment behind it — closing the
seasonal segment pushes exits into sales. Catalonia capped seasonal contracts on 1 Jan 2026
(Ley 11/2025), and the deposit register measured the following quarter: seasonal contracts
**−1,233**, the first fall since the cap began, against a habitual-contract stock **+8,895** over
2025. The model already carries the switch (`PolicyConfig.seasonal_segment_capped`), so the
prediction runs against that quarter without new machinery.

#### Parameter ledger

Retired: `hazard_scale` (0.7, fitted), `exit_split_sale` (0.50), `exit_split_vacant` (0.15), and
`exit_split_evasion_base` (0.15) — the proportional rescaling `docs/assumptions.md` declares "a
convention with no episode behind it", which the direct diversion no longer needs.

**`rental_supply_elasticity` is retired too, and becomes an output.** The 0–2 dial — the
OLS-to-IV span of Monràs & García-Montalvo, the most disputed parameter in the model — cannot
survive an arbitrage condition: the supply response is determined by the distribution of
`(r_req − cap)` across units together with `selling_cost_share` and `holding_years`. The three
Catalan studies stop being a dial and become the targets that adjudicate it. Under this project's
bias-control rule the dispute must stay visible as a range, so **it moves** — to the ranges of
those two structural parameters — rather than disappearing. `ui/levers.py` exposes those two in
place of the elasticity slider, with the Monràs span named in the help text as the thing they
span.

Carried, with changed roles: `holding_years` (5.0, range 3–10, **[guess]**) becomes the horizon of
the sale decision rather than a term inside a gap — more exposure, not less, and it enters the
Sobol sweep on that basis. `selling_cost_share` (0.02 shipped; **band sourced 2026-09-16,
0.01–0.07, weighted point value 0.040 known but deliberately not shipped** — see Sources below)
becomes the **exit threshold**. Unchanged: `cap_compliance` (still in front of
everything), `magnet_gain`, `seasonal_evasion_share`, and all of `cap_level`.

**One parameter becomes load-bearing without anyone having chosen it.** `min_required_yield`
(0.005, **[guess]**) floors `required_yield = max(min_required_yield, bond + π·risk − E[g])`. In a
boom E[g] is large, the floor binds, `r_req` collapses, and `cap < r_req` almost never fires. The
structural prediction that falls out — cap-driven withdrawal is weak in booms and strong in flat
or falling markets — may well be right, since appreciation compensates the landlord for a cap.
But Catalonia 2024–26 was a price boom with substantial claimed withdrawal, so this `[guess]`
would be governing the **sign** of the regime that matters. See F3.

#### Sources

The arbitrage arithmetic needs no source — it is accounting. The quantities do, under the ≥2 rule:

- **`selling_cost_share` — sourced as a band; the point value is known and deliberately not
  shipped (2026-09-16).** Two independent institutional viewpoints now bound it: the statutory
  leg (Código Civil art. 1455, IIVTNU, RD 1426/1989, RD 1427/1989 — a self-sold dwelling's
  floor, 0.5–1.5% of price) against the market leg (agency commission 3–5% + IVA, 4–7% for an
  agency sale), weighted by the intermediation share agencies handle (64% [Fotocasa Research],
  ≈70% [idealista]). That gives a sourced band **0.01–0.07** and a weighted point value
  **0.040** — commit `8fd0c90`, three new rows in `docs/sources.md`, `config.py`
  `MarketConfig.selling_cost_share` around lines 486–520. **The model still ships 0.02**, below
  the sourced point, because moving to 0.040 fixes one registered strict xfail while regressing
  two targets in channels that have nothing to do with the rent cap (`market/clearing.py`'s
  reserve floor tightens for every indebted seller); see `docs/validation.md` "Honest
  qualifications". §7.2's output therefore stays **direction-only regardless of what the tests
  say** — not because the parameter is an unsourced guess any more, but because the shipped
  value is a deliberate choice below the sourced point, pending its own branch to resolve the
  three-channel interaction.
- **`holding_years` — bounded, not set.** `docs/sources.md` carries Registradores ERI 2020:
  mean holding period **15 years 256 days**, series minimum 7 years 106 days (2009). That is the
  *realised* holding period, not the decision horizon, and treating them as the same quantity
  would be an error. It enters as a bound.

#### Falsification

**F1 — the co-movement does not emerge.** If under Ley 11/2020 the model cannot produce
Δln contracts / Δln rent inside Monràs's 0.07–2.0 OLS-to-IV span at **any** point in the declared
ranges of `selling_cost_share` and `holding_years`, the arbitrage condition is false. It is not
rescued by restoring a scale factor.

**F2 — the selling cost has to leave its band.** If reproducing the co-movement requires a
`selling_cost_share` outside the sourced Spanish band, it is a fitted parameter wearing a cost's
clothes and must be declared as one. This is §5c.8's own test applied to itself.

**F3 — `min_required_yield` is carrying the sign.** If withdrawal turns out so decreasing in E[g]
that the 2024–26 Catalan boom produces no withdrawal at all while three independent instruments
say withdrawal occurred, then a `[guess]` floor is governing the sign of the result. The repair is
to rebuild how E[g] enters `r_req`, not to retune the floor.

> **RUN 2026-09-16 — F3 DOES NOT FIRE.** The floor never binds: rebuilding the same comparison
> `required_rent` makes, the unfloored yield is +0.0784 against a 0.0050 floor at a 1%/yr growth
> anchor and still **+0.0212 at an 8%/yr anchor**, in every zone. The route F3 would fire through
> is closed by construction in this calibration.
>
> The probe did find that the cap's response is strongly decreasing in the growth anchor through
> the *unfloored* term: −27.2% leases at 1%/yr, −31.4% at 2%, −35.6% at 4%, and **−13.2% with the
> rent sign corrected to −37.2% at 8%/yr**. The model's baseline anchor is 2%/yr; the Catalan
> evaluations these gates are judged against measure a period of HPI +12.7% (2025) and +12.2% y/y
> (2026Q2). **F1 was therefore adjudicated at an anchor far below the episode it adjudicates
> against**, and re-running F1 across the anchor is the first thing §7.2b should do, before any
> mechanism is changed. Three seeds, non-monotone curve, floor check on one seed at the final
> tick — a hypothesis with a mechanism and a number, not a result. Full record and limits in
> `docs/validation.md`.

**F4 — out of sample, Ley 12/2023 still produces a rent rise.** If after §7.2 the statute in
force still produces a **rise** in tensioned contract rents, outside the in-regime span running
from the register (contracts +1,374; new-contract rent −2.7% real [O-HB no. 4]) to Pérez García
(−13% tenancies, rent effect ≈0), then §7.2 has not done the thing it was written for.

**F4 is not repaired by re-fitting.** A failure there means the arbitrage condition is wrong, not
that a parameter needs tuning. And the warning this project has already earned once applies:
rewriting §7.2 in response to its failure under Ley 12/2023 **spends that evidence**, exactly as
2008–13 was spent (§13.11). From that point the statute in force can no longer validate the
model and becomes a diagnostic. F4 is therefore run **once**, after the three Ley 11/2020 tests
are green, and its result is registered before anything is touched.

#### What §7.2 does not touch

Deliberately, so that a failure can be attributed: `cap_level` and its two statutes; the
previous-contract anchor; coverage, the declared/undeclared segment mix and target T7;
`shadow_rent` as an input to the *ask*; `magnet_gain`; compliance; and the whole sale channel
downstream of `WithdrawRental`.

#### Reporting consequence

If F1–F3 pass and F4 lands inside the span, the rent cap under Ley 12/2023 moves from **not
reportable** to **direction** under §13.2 — not to magnitude, which the variance rule would
refuse while `holding_years` and `selling_cost_share` remain guesses. The warning in
`ui/levers.py` is then rewritten to say what may be read rather than only what may not.

> **SUPERSEDED (2026-09-16).** F1 passed at exactly one corner of the declared ranges while three
> inverted the sign, F3 did not fire, and F4 was never run because this section gates it on the
> Ley 11/2020 tests being green and they are red. The rent cap is not reportable under either
> statute, in size or in sign. §7.2b replaces F1 with the stricter G1 and retires `holding_years`
> outright; read that section's falsifications, not these, for the current state.

### 7.2b The withdrawal margin, dispersed and time-limited (2026-09-16)

§7.2 failed its own F1. This section repairs it. It is specification only until its plan runs.

**The measured diagnosis, and it is sharper than "no friction".** §7.2's exit trigger is
`cap < r_req`, where `r_req = V·(i_bond + π·risk − E[g]) / (12·(1−c))`. Inside a zone every
landlord shares `i_bond`, `π`, `E[g]` and `c`, and differs only in `V`, which scales with
`quality` — **and the reference index scales with quality too**. The ratio `cap / r_req` is
therefore near-identical across the units of a zone, so when it crosses 1 it crosses for all of
them at once. The exit decision is **scale-invariant**, and that is why it behaves as a step
function in E[g]: low E[g] raises `r_req` and everyone sells; high E[g] collapses `r_req` and
nobody does. The ten-seed anchor sweep in `docs/validation.md` measures the boundary between 4%
and 6%/yr — 0/10 seeds with the rent sign right below it, 10/10 above — and shows that moving the
anchor relocates the step without removing it. **Re-anchoring is a closed line of repair.**

> **MEASURED 2026-09-16 (Task 1) — the diagnosis is confirmed at machine precision.** `cap /
> r_req` is not merely "near-identical", it is a **point mass**: cv = 0.000 in a hand-built
> fixture (`_capped_state`) and cv = 1.4×10⁻¹⁶ — machine epsilon — over 4,693 small-landlord
> units in a real `Engine` run, four ticks after activation under `index_binds_all=True`.
> `quality` cancels identically between `required_rent` and the index branch of `cap_level`;
> neither is an approximation. One caution belongs on the record with it: the fixture's own
> *mean* of 0.800 is tautological — `_capped_state` sets `reference_rent` from `cap_ratio`
> directly, so the test could print nothing else — while the real-run mean is **0.8039** and
> drifts **0.61–1.03** across seed and sampled tick. **The bite is not constant in time**, a
> property neither this section nor the plan that implemented it anticipated. Full measurement
> in `docs/validation.md`.

Any repair must break the scale-invariance of `cap / r_req` inside a zone. §7.2b does it with two
pieces that do different jobs.

#### Piece A — the exit cost belongs to the landlord

`Unit` gains a second persistent draw, the sibling of `declaration_draw`: `sale_route_draw`,
U(0,1) from the engine's seeded Generator, drawn once at creation and never redrawn. A landlord
sells through an agency or sells privately, and that is its route for the whole run — persistent
for the same reason coverage is, so a unit cannot cross the threshold and come back, and so two
scenarios stay comparable.

The draw maps monotonically onto the exit cost, cheap routes first:

```
u ∈ [0, 1−s)   → private sale:  k = 0.005 + 0.010·u/(1−s)
u ∈ [1−s, 1)   → agency sale:   k = 0.04  + 0.030·(u−(1−s))/s
```

`k` increases in `u`, so the landlords who are cheap to extract leave first and agency sellers
hold out longest. **Raising the cap's bite adds landlords to the exiting set rather than
reshuffling it** — the monotonicity property `declaration_draw`'s own comment prizes for coverage,
here for the same reason.

Why this disperses where §7.2 could not: with `shortfall/V ≈ H·y/(1−c)·(1 − cap/r_req)`, a
landlord sells when that exceeds `k`. At `y ≈ 0.05`, `c = 0.22` and a three-year term the bite
required to trigger a sale runs from **≈3% at the cheapest private sale to ≈37% at the dearest
agency one** (private 3–8%, agency 21–37%) — an order of magnitude between two landlords facing
the identical cap. The exit share then sweeps the
`k` distribution continuously instead of jumping.

#### Piece B — the cap has a statutory life, and the landlord is myopic about renewal

`RentCap` gains a declared term, default **12 ticks (3 years)**: ZMRT are declared for three years
and renewable, and the BOE resolutions with their `vigencia inicio–fin` are already registered in
`docs/sources.md`. The cumulative shortfall accrues over **the ticks remaining in the current
declared term**, not over a holding horizon. `wedge_annualisation` and the trapezoid survive,
applied to that shorter span.

The statute renews — Catalonia extended to 302 municipalities to 2027 — so the cap stays in force
while the scenario says so, and the term resets on renewal. **The landlord does not anticipate the
renewal.** That is the friction, stated as a modelling assumption rather than smuggled in as a
discount: a renewal is a political act a landlord cannot bank on, so it discounts less shortfall
than it will actually suffer. It is falsifiable — if the model needs landlords to anticipate
renewal in order to match the Catalan evaluations, the assumption is wrong.

Piece B alone would not disperse anything: a shorter horizon moves the step for everyone
together. Piece A alone operates in a narrower window and may not bite. **B brings the scales
together; A separates the landlords.**

#### Parameter ledger, and a count that does not flatter this section

Retired: `holding_years` (5.0, range 3–10, **[guess]**), `holding_years_range`, and the sweep entry
added for it on 2026-09-16.

Added: `intermediation_share` (0.64, range 0.64–0.70), `intermediation_share_regional_range`
(0.40–0.85 — the regional spread, not the national band above; `ui/levers.py` bounds its slider
to it and `sensitivity.py`'s Morris/Sobol sweep reads it), the two exit-cost bands (0.005–0.015
and 0.04–0.07), `cap_term_ticks` (12). `Unit.sale_route_draw` is per-unit state, not a parameter.
Renewal is not a parameter at all: there is no `cap_renews` flag anywhere in `src/` — renewal is
a property of the term arithmetic, `elapsed % cap_term_ticks` at `landlord.py:268`, which
recycles the horizon every declared term without a boolean to carry or default. That is the
better implementation, so this ledger entry is corrected rather than a field added to match it.

**§7.2 retired five parameters and §7.2b returns five.** On a headcount this is a regression, and
it is recorded as one. The project's criterion is not the count but the **unsourced share of
variance** (§13.2): what dies is a `[guess]` that governed the whole channel, and what is born is
five quantities with published sources — four committed on 2026-09-16, one from the BOE. There is
also an asymmetry worth naming: `holding_years` was a guess with **no empirical band**, so
sweeping it measured the model's ignorance; the new bands are ranges of evidence, so sweeping them
measures disagreement between sources.

**A hash consequence, not a modelling one.** Removing `intermediation_share_range` changed
`CapResponseConfig`'s field set, and `cli.py`'s `config_hash()` hashes `asdict(config)` over the
whole config tree — so every configuration's hash string changed with it. No simulation output
changed; this is bookkeeping, not a result. But `runs/` caches expensive work under a filename
keyed on that hash (per this file's own convention), so any cached artefact keyed on a
pre-this-branch hash is now silently orphaned, not invalidated with a warning. A later reader
re-running a sweep and finding no cache hit for a hash that "should" exist need not suspect a
bug: this is why.

#### Sources

- **`intermediation_share`** — agencies handle **64% of second-hand purchases** [Fotocasa
  Research] and ≈70% of all operations [idealista]. The model takes **0.64**: a landlord selling a
  let dwelling makes a second-hand sale, not an operation of any kind. Regional spread is wide
  (Murcia, Navarra, Baleares high; Extremadura, País Vasco, Andalucía low).
- **The two exit-cost bands** — the statutory and market rows registered in `docs/sources.md` on
  2026-09-16. Uniform within band is a declared convention: the sources give ranges, not
  distributions.
- **`cap_term_ticks`** — ZMRT resolutions, MIVAU's compiled table (317 municipalities, vigencia
  inicio–fin), already in `docs/sources.md`.

**A declared debt.** `MarketConfig.selling_cost_share` survives for the **household** seller's debt
leg in `market/clearing.py`. That leaves two consumers of one real quantity: a single value for
the household, a dispersed one for the landlord. §7.2 rejected its own hybrid approach for exactly
this kind of seam, so it is stated rather than hidden — same evidence, two consumers, and the
landlord needs the dispersion while the household reserve floor does not. Unifying them is future
work.

#### Falsification

**G1 — the co-movement does not emerge at the SHIPPED parameters.** §7.2's F1 asked only for a
witness somewhere in the declared ranges, and that proved too weak: it passed at one corner while
three inverted the sign. G1 requires the rent sign correct in **all ten seeds at the shipped
values**, with Δln contracts / Δln rent inside Monràs's 0.07–2.0. A single-corner pass is a
failure.

**G2 — the intermediation share moves nothing.** Sweeping `intermediation_share` from 0.5 to 0.8
must move withdrawal. If it does not, Piece A is decorative.

**G3 — withdrawal is not front-loaded within a term.** It must concentrate after each declaration
and taper toward expiry; nobody sells to escape a cap about to lapse. Flat withdrawal means Piece
B is inert. Testable against Incasòl's quarterly counts.

**G4 — the regime boundary survives.** Re-run the ten-seed anchor sweep recorded in
`docs/validation.md`. If 0/10 below some anchor and 10/10 above persists, the step function
survived and the dispersion is too narrow for the shortfall it faces. This is the direct test that
§7.2b did what it was written to do, and the table to compare against is already committed.

**And the magnitude is not in scope.** Where §7.2 got the sign right it gave −37% rents against
Monràs's −5%. §7.2b attacks *who exits*, not the size of the price response. That less withdrawal
yields a smaller rent move is plausible, not certain. If the sign corrects and the magnitude stays
seven times too large, that is a separate finding and is registered as one rather than folded into
G1.

> **RUN 2026-09-16 (Task 6) — G1 FAILS, G2/G3/G4 PASS.** Ley 11/2020, shipped parameters, ten
> seeds unless noted otherwise.
>
> - **G1 FAILS.** Rent **−16.2%** (sign correct) against new leases **−46.6%**;
>   `ln(1−0.4663)/ln(1−0.1616)` = **3.563**, above Monràs's 0.07–2.0 span. Its per-seed sign
>   assertion **PASSED**: all ten seeds are individually correctly signed, so there is no sign
>   dispersion hiding under the pooled mean. The failure is purely magnitude, and per its own
>   construction it sits in the quantity leg: contracts move far more than rent does.
> - **G2 PASSES.** |Δleases| = **34.7pp** across the sourced intermediation-share corners:
>   0.40 → −61.6% leases (rent −7.0%), 0.85 → −26.8% leases (rent −17.7%). Piece A does the job
>   it claims — shifting the population toward the dearer exit route roughly halves withdrawal.
> - **G3 PASSES.** 133 withdrawals in ticks 20–25 against 84 in ticks 26–31 (one seed,
>   `start_tick=20`, `term_ticks=12`) — front-loaded within the declared term; the raw per-tick
>   series bottoms at the term's last tick and jumps back up at the first tick of the renewal.
> - **G4 PASSES at ten seeds, all four sourced anchors (1/2/4/8%/yr).** The regime boundary this
>   gate re-runs — 0/10 seeds correctly signed below 4%/yr, 10/10 at 6%/yr and above — is gone:
>   the three anchors that actually discriminate (1, 2 and 4%/yr, each inside the old 0/10 band)
>   moved to **10/10**. The 8%/yr corner was already 10/10 before this branch and discriminates
>   nothing. **G4 verified only the rent SIGN at these ten seeds; the per-anchor rent and lease
>   MAGNITUDES were not captured**, so the quantity leg's behaviour across the anchor sweep
>   remains unmeasured at full statistical power. A superseded three-seed probe (disclaimed as
>   not this gate's own measurement) had shown new leases turning **positive (+0.76%)** at the
>   8%/yr anchor even while rent stayed negative — the same large-quantity-response pattern G1
>   falsifies at the shipped anchor, visible again across the anchor but not confirmed at ten
>   seeds.
>
> **Two findings, neither predicted, that belong on the record with the gates themselves.**
>
> 1. **G2's corner locates where the remaining error is NOT.** At `intermediation_share=0.85` —
>    the top of the sourced regional range, the all-agency-exit corner — leases still fall 26.8%
>    against Monràs's −10% tenancies. The model over-responds even at the extreme edge of what
>    the evidence admits: no re-calibration inside the sourced range can reach the measured
>    response, so the excess sits somewhere else in the channel, not in this parameter.
> 2. **The two gates that turned green in Task 3 were checked, not assumed.**
>    `test_cap_coverage_scales_the_rent_cap` and `test_rent_cap_lowers_contract_rents` — two of
>    the four tests red since §7.2 — flipped green as a side effect of Piece B, with no test file
>    touched in that task. Verified here: `git diff` of `03456e8..e47bbda` (Task 3's commit)
>    restricted to `tests/test_validation.py` and `tests/test_engine.py` is **empty**. The
>    assertions that now pass are byte-identical to the ones that failed — the mechanism earned
>    the green, nobody edited a threshold to get there.
>
> **The magnitude is registered separately, per this section's own instruction, not folded into
> G1 beyond G1 itself failing on it.** G1 is the gate built to carry the magnitude question — a
> co-movement ratio, not a bare sign check — and it is the one that fails. The sign is repaired;
> the size is not, and the excess sits in the quantity leg (new leases −46.6% against Monràs's
> −10% and Pérez García's −13% tenancies), not in the price leg alone.
>
> **The price leg carries its own excess too, and it has a number.** Rent −16.2% against
> Monràs's −5% point estimate is **≈3.2×** the sourced magnitude — smaller than §7.2's ≈7×
> overshoot at the one anchor where §7.2's sign was correct, but not close to closed: three
> times the sourced figure is a registered excess, not a rounding difference. This sits
> alongside the quantity leg's excess above, not instead of it — both legs are too large, not
> only the ratio between them.
>
> **Suite at `ea7a795`: 3 failed / 177 passed / 9 xfailed.** The three reds:
> `test_shadow_rent_stays_anchored_under_a_cap` and
> `test_rent_cap_reproduces_the_monras_co_movement` — both inherited from §7.2 and never claimed
> by §7.2b — plus `test_g1_the_co_movement_emerges_at_the_shipped_parameters`, this section's own
> falsification firing as designed. Fix round 1 (`ce61351`) tightened G1 to a genuine per-seed
> sign check and G4 to the full ten-seed, sourced-grid form; neither change moved a verdict — the
> RNG is fully seeded, so G1's ratio is byte-identical, 3.563, before and after.
>
> Three of four falsifications passing is confirmation that the mechanism does what this section
> claims — dispersed exit, front-loaded within the statutory term, and the growth-anchor step
> function is gone. **It is not a claim that the rent cap is reportable.** See "Reporting
> consequence" below.

#### What §7.2b does not touch

`cap_level` and the two statutes; the previous-contract anchor; coverage and the declared segment
mix; compliance, which stays in front of everything; the seasonal branch and its ordering; and
vacancy as the sale channel's waiting state. §7.2b changes the **threshold**, not the branch
structure.

#### Reporting consequence (2026-09-16)

Three of G1–G4 passing means the mechanism does what §7.2b claims: exit is dispersed rather
than a zone-wide step, the statutory term front-loads withdrawal the way a declared, renewable
cap should, and the growth-anchor regime boundary that made §7.2's sign flip is gone at every
anchor tested. **None of that makes the rent cap reportable.** G1 is the gate built to carry the
question a reader actually wants answered — does the model's response sit inside the range the
evidence admits — and G1 fails: new leases fall −46.6% against Monràs's −10% and Pérez García's
−13% tenancies (3.5–4.7× the sourced quantity response), and the co-movement ratio itself
(3.563) sits 1.8× above the top of Monràs's 0.07–2.0 span at the shipped point; G2's own sweep
shows the excess survives at every corner of the sourced `intermediation_share` range too.

**The price leg carries its own excess too, not only the ratio between the two legs.** Rent
−16.2% against Monràs's −5% point estimate is **≈3.2×** the sourced magnitude — smaller than
§7.2's ≈7× overshoot at the one anchor where §7.2's sign was correct, but not close to closed:
three times the sourced figure is a registered excess, not a rounding difference. It sits
alongside the quantity leg's excess above, not instead of it — both legs are too large.

**G4's pass is sign only.** All four sourced anchors (1/2/4/8%/yr) run negative rent at all ten
seeds, and the pre-§7.2b regime boundary is gone at the three anchors that discriminate — that
is what G4 tests, and it passes. But the per-anchor rent and lease *magnitudes* were not
captured at those ten seeds, so whether the quantity leg's overshoot above holds, worsens, or
eases across the anchor sweep is unverified at full statistical power. A superseded three-seed
probe (explicitly disclaimed at the time as not this gate's own measurement) had shown new
leases turning positive at the 8%/yr anchor while rent stayed negative — the same
large-quantity-response pattern G1 falsifies at the shipped anchor, glimpsed again across the
sweep but not confirmed at the ten seeds G4 actually runs.

Under §13.2 the rent cap under Ley 11/2020 stays where §7.2's own "Reporting consequence" left
it — **not reportable** — with the sign of the withdrawal channel now a defensible **direction**
claim (G1's per-seed check, G4) and the size of that channel's contract response an **open,
registered magnitude error**, not a
guess awaiting a parameter fit: G2's own corner shows re-fitting `intermediation_share` inside
its sourced band cannot close it. The Ley 12/2023 out-of-sample test (§7.2's F4) is still not
run — it remains gated on the Ley 11/2020 tests being green, and one of the four, G1, is red.
`ui/levers.py`'s warning is unchanged by this section.

#### UI

The `holding_years` slider dies with the parameter. `selling_cost_share` is no longer the
landlord's exit threshold and stops being the rent cap's dial. In their place the panel exposes
**the share of landlords who sell through an agency**, centred on 0.64 and ranging **0.40–0.85** —
wider than the two national sources measure, because the regional spread is real and large. The
help text names that widening explicitly, and names Monràs's OLS-to-IV span as the thing the
slider traverses.

### 5c.8 The tick is a quarter, the market is not (2026-09-15)

Three registered failures had one cause, and it was the clearing calendar.

`clear_sales` matched every buyer against every listing once per tick. A tick is a quarter, so
every listing faced a full quarter of demand simultaneously and the ascending auction ran on all
of it: 3.5 bids per listing, 21% of sales above the ask, and a negotiation margin of 3.9%
against a measured 6.2% [Cátedra Tecnocasa-UPF, 2S 2025]. That margin had failed since phase D
created the target, and phase G's frontier — the boom's rent leg against the negotiation
observables — was the same fact seen from the other side.

Real offers arrive **sequentially**, and a seller answers the ones in front of it against a
reservation price [Merlo & Ortalo-Magné 2004; Merlo, Ortalo-Magné & Rust, complete offer
histories for 780 English properties]. The tick now clears in **three sub-periods** — the months
in a quarter, the calendar rather than a parameter. Buyers are split across them at random;
each sub-period matches against the listings still unsold; a listing that sells leaves.

Market tightness for §5c.7 is still measured over the whole tick, because the option value of
searching is a property of the quarter's market, not of one month in it.

**What it did**, ten seeds unless noted:

| | before | after | band / source |
|---|---|---|---|
| Negotiation margin | 3.9% | **5.20% ± 0.10** | 4–12%, mean 6.2% [Tecnocasa-UPF] |
| Sales above the ask | 21% | **12.8%** | 9% of negotiating sellers [Fotocasa] — closer, not gated |
| Bids per listing | 3.5 | **2.22** | ≤ 7 [Tecnocasa] |
| Boom rent leg | +1.17%/yr | **+3.03%/yr ± 2.74**, 9/10 positive | gate +2.5% |
| Rate-shock volume cut | 1.6% | **passes** | 5% [the phase-D falsification] |
| Price-to-income | 8.07 | **8.13 ± 0.11** | 7.0–8.2 |
| Sold inside the quarter | 0.47 | **0.607** | 0.43–0.63 [idealista] |

The rate-shock test is the one worth pausing on. Phase D killed
`PARTICIPATION_RATE_SENSITIVITY` and recorded the resulting failure as the falsification the
redesign asked for. It passes again, and **nothing was added to the rate channel**: with the
quarter clearing month by month, a buyer the credit screen prices out is no longer replaced
inside the same tick by the next bidder on the same listing, so the screen reaches volume the
way the 2022–23 episode says it does. The coefficient stays dead.

Re-fit alongside it, both inside their sourced bands: `tightness_half_saturation` 260 → **400**
(the level rises when sales are spread over the quarter) and `ask_markup` 0.12 → **0.125**.

**What it changed beyond the three tests.** On 1,792 fresh Sobol evaluations the largest
*unsourced* share of the price level's variance is `momentum_gain` at 0.109, against 0.24
before. Under §13.2 that makes price-to-income a **reportable magnitude** — the first in the
project — conditional on the ask-markup band, which explains 61% of it: **8.13, and 7.2–9.1
across the parameter ranges the evidence admits**. The verdict follows the consistency check
on `ask_markup` that this section closed; it was refused the day before, when that check
failed. The **rent side stays direction-only** — `small_landlord_premium`, §7.1's declared free
parameter, explains 0.65 of the rent level and 0.75 of tensioned vacancy — and so do the
ownership rate, the zone price ratio, the cash share and the negotiation margin
(docs/validation.md).

**Falsification.** If the sub-period count has to leave 3 to hold the margin — 1 or 6 rather
than the calendar — then it is a fitted parameter wearing a calendar's clothes and must be
declared as one. Measured: 1 gives a 3.9% margin, 2 gives 4.7%, 3 gives 5.1%, 6 gives 5.6% with
70% of listings selling inside the quarter against a 43–63% band. Three is both the calendar and
the only value that satisfies every gate.

### 7.3 Buy-to-let entry — the section this file cited three times and never had (2026-09-17)

**This section records a debt, not a decision.** §7.3 was referenced from three §9 targets (9,
11 and 14) and from four places in `src/` as though it existed. It did not. A spec that cites
its own missing sections lets a reader believe a mechanism has been specified and reviewed when
nothing has been written down, and this project's rule is that code and spec disagreeing is a bug
in one of them — a citation with no referent is the same bug with the code half missing.

**What exists.** An implementation, measured and parked on branch `buy-to-let-remeasure` (two WIP
commits, 2026-09-14, now 90+ commits behind `main`): households buy to let, choosing the zone by
the best risk-adjusted return rather than their own. Nothing of it is on `main`.

**What it closes, measured on that branch.** The rural gross yield falls from 22% to **8.10%**,
inside its sourced 7–9% band, which takes target 9 — a strict xfail on all three zones — with it.
So does target 11's rent ordering, the insider/outsider wedge and the small-landlord share. The
rate is calibrated against its stock anchor (`landlord_household_share` 0.274, inside the
EFF-AEAT bracket), not against the price targets.

**Why it is parked, and it is one thing.** Yield-chasing entry **arbitrages the zone price
ladder away**: T/R falls to 1.65 against a sourced floor of 2.6. The 1.5pp zone risk gradient is
not enough against a rural yield starting at 22%. The missing force is the one the investor
should *see* when choosing a zone and currently cannot: the **vacancy gradient** — *días de
alquiler* 338/365 in Extremadura against 352/365 in Barcelona, against the model's own 18% rural
vacancy. A rural let is not a substitute for a metro one; the branch as it stands says it is.
Twelve tests fail there, deliberately unmarked.

**Three defects it found and fixed on the way**, which are worth salvaging whatever happens to
the mechanism: buy-to-let buyers shopped in their own zone; a latent state bug in
`clearing.settle` left units owner-occupied by nobody (unreachable before this branch, caught by
`tests/test_state_invariants.py`); and the buy-to-let hurdle carried no zone risk gradient while
the small-landlord hurdle already did.

**What has to happen before this becomes a real §7.3 — and the first answer is NO, measured
2026-09-17 before any of it was built.** The plan was: source the vacancy gradient (≥2
independent rows, per the bias rule), enter it into what the investor compares, re-measure the
ladder against its 2.6 floor. The sourcing step succeeded and the arithmetic then refuted the
mechanism.

**The sourced gradient is an order of magnitude too small.** `docs/sources.md` already carries
the AEAT + Catastro *días de alquiler* row (fetched 2026-09-14): **338/365 in Extremadura against
352/365 in Barcelona**, 347 national. That is a **3.98%** relative haircut on the rural yield. The
model's baseline zone gap is **6.43pp** (rural 12.30% against tensioned 5.87%), so the haircut
closes **0.49pp — 7.6% of the gap**. It cannot make a rural let stop looking like the better
investment, and no reading of that source makes it bigger: it is the occupancy of dwellings that
were *let and declared*, so by construction it cannot price the risk of not letting at all.

**What the measurement found instead, and it is the thing to attack.** The model's rural market
is the **tightest of the three**, not the loosest. Ten seeds, mean of the last eight ticks:

| zone | total vacancy | **market vacancy** | gross yield |
|---|---|---|---|
| tensioned | 8.81% | **3.79%** | 5.70% |
| secondary | 13.76% | **7.06%** | 7.55% |
| rural | 17.95% | **2.66%** | 12.26% |

Rural is simultaneously the **emptiest** stock (17.95%, and target 5d gates that ordering, which
passes) and the **tightest market** (2.66% offered and unlet, lower than tensioned in **9 of 10
seeds**). All of the rural vacancy sits in withheld units. So a rural landlord in this model faces
*less* letting risk than a metro one, which is why a 12.26% yield survives and why yield-chasing
entry arbitrages the ladder away. **No haircut applied to the yield can fix a model that says the
risk runs the other way.**

**It is gated, and the gate cannot reach the inversion — which is a source gap, not an
oversight.** `test_vacancy` asserts tensioned **market** vacancy in 2–10% and the model passes at
3.79%. That band was deliberately widened below the 6–9% urban Censo figure, and the reason is on
the record in the test's own docstring: the Censo figure includes second homes and withheld stock,
and **no source separates the market component from the withheld one** (investor-small §7.3).
`test_vacancy_ladder` gates the *full-stock* ordering R > S > T, on the basis the source actually
measures, and it passes. So the rural market leg is ungated **by declared necessity**: there is
nothing registered to gate it against.

**That wall turned out to be lower than it looked (2026-09-17).** A source does make the split:
the Basque **EUV** classifies non-principal dwellings as `en oferta` or `fuera de mercado`, and its
2023 edition is now registered. On its non-principal base **14.9%** of vacant stock is on the
market, against the model's **14.8% rural, 43.0% tensioned, 51.3% secondary** — so the rural leg is
right and the two urban legs are the outliers, the opposite of the attribution the paragraph above
implies. Full measurement, and the three caveats it does not survive without — one source, a
predominantly urban region, and an assumed mapping of `withheld` to second residences — in
`docs/validation.md`. A gate still cannot be built on one regional row without breaching the bias
rule, **and the second, independent split was searched for and does not appear to exist** — the
APCE-UPF monograph is unreachable (403), Fotocasa's owner survey makes no such split, Navarra's
register holds 216 dwellings, and neither the Censo nor MITMA's review classifies by market
status. The search trail is in `docs/validation.md`. So "gate it first" is closed on the evidence.
What remains needed no new source and has now been answered: **there is no withholding rule.**
`Unit.withheld` is drawn once at creation from `ZoneConfig.withheld_share` and never revisited
outside a vacancy-tax intervention, and the per-zone levels are **solved**, not sourced — the
gradient is sourced, the levels hold `(units_per_household − 1)(1 − withheld_share) = 0.0455`
identically in all three zones (measured: 0.0457 / 0.0459 / 0.0460). The model therefore asserts
that a household has the same mobilisable empty stock wherever it lives, which is what makes rural
market vacancy the lowest of the three, which is what makes the rural yield riskless, which is what
lets yield-chasing entry arbitrage the ladder. **§7.3's blocker is a consequence of the zone
configuration three steps upstream, and no discount applied to the investor's comparison can undo
an identity imposed on the initial conditions.** Full chain and the measured table in
`docs/validation.md`.

**So the open decision is not "how big a haircut".** It is whether the withheld/market split is
right in rural, and that is a question about the withholding rule, answerable on the baseline and
without the rent cap or buy-to-let entry anywhere near it. Until it is settled there is no §7.3
decision to write down, and the branch should not merge.

## 5d. What stops a falling market (2026-09-15)

The hold-out found the gap and `docs/assumptions.md` registers it: **nothing in this model
slows a market once it turns.** Fed 2008–13, prices fell 56.9% against an observed 30–45%, and
the arrears stock peaked at 2.2% against the BdE's 6.28%. Both numbers point at the same
absence — every mechanism the model had was symmetric, and a real housing bust is not.

Two brakes are added, each identified on evidence that has nothing to do with the episode
that revealed the gap. **That distinction is the whole of the discipline here**: the hold-out
may not be used to calibrate anything (§13.4), so the parameters below come from a
peer-reviewed estimate and from a statute, and the episode is re-run only as a **diagnostic**,
never again as out-of-sample evidence (§13.11).

### 5d.1 Nominal loss aversion in the seller's ask

Genesove & Mayer (QJE 2001) is the canonical measurement and it is unambiguous: owners facing
a nominal loss set asking prices **25–35% of the gap** between the expected selling price and
what they originally paid *above* what they would otherwise ask, realise selling prices 3–18%
of that gap higher, and show a **much lower sale hazard**. The list-price effect is **twice as
large for owner-occupants as for investors**. Their own conclusion is the mechanism this model
needs: it is what produces the positive price–volume correlation in housing.

```
loss      = max(0, price paid − what the dwelling is worth now)
ask       = (index × quality × (1 + E[g]) × (1 + markup))  +  α · loss
α         = 0.30 owner-occupier,  0.15 landlord/investor      [range 0.25–0.35, halved]
```

Three properties worth stating, because they are what make this safe to add after a
calibration:

- **It is inert in a rising market.** With prices above what the seller paid the loss is zero
  and the ask is exactly what it was before. The calibration window is a rising market, so
  this cannot have been fitted to it and must not move it — which is checked, not assumed
  (`docs/validation.md`).
- **The realised-price effect is not a second parameter.** A higher ask feeds the
  single-bidder negotiation branch of §5c.1 and the reserve floor unchanged; what the seller
  actually gets, and the lower sale hazard, come out of the auction.
- **It does not override the mortgage.** The reserve is still `max(debt + costs, ask × (1 −
  discount))`; loss aversion raises the ask, not the floor, so a household that must sell can
  still sell — it just asks for more first and waits longer.

### 5d.2 Forbearance: the Código de Buenas Prácticas

The second brake is law, and the model's failure to have it was registered as an omission
with the *wrong sign* until the hold-out corrected it (`docs/assumptions.md`).

RDL 6/2012's annex, as the Banco de España's own guide states it: a borrower past the
exclusion threshold gets a **grace period of five years** with capital amortisation suspended
(two years in the milder case), the term extended to at most **40 years** from origination,
and interest during grace at **euríbor − 0.10%**; the plan is refused if the restructured
payment would exceed **50% of household income**; it is available only **before the
foreclosure auction is announced**.

In the model:

- **Entry** at the first missed quarter, before the statutory foreclosure clock matures, if
  the viability test passes — interest-only payment ≤ 50% of income — and the household takes
  it up. Unemployed households get the five-year grace, employed ones the two-year: a proxy
  for "effort ratio rose ≥1.5×", declared as a proxy.
- **During grace** the payment is interest only, the arrears counter is frozen rather than
  cured, and the loan still counts in `arrears_share`. That last point is not a modelling
  convenience: refinanced and restructured loans stayed classified as doubtful in the BdE's
  own statistics, which is a large part of why the ratio stayed above 5% for years after the
  deliveries peaked.
- **On exit** the term is extended by the grace taken (capped at 40 years from origination)
  and the payment is recomputed from the balance and the remaining term — so the household
  leaves with a lower instalment than it entered with, which is the point of the measure.
- **Take-up** is the one reduced-form parameter: 0.20, range **0.10–0.30**, from the CBP's own
  counts — 45,697 families in five years, 14,730 operations in 2016 alone, against roughly
  50,000 deliveries a year in the same period.

**What each brake is predicted to do**, written before either was run, so the check is not
retrospective: loss aversion slows the *price* fall and cuts volume further in a downturn
(Genesove & Mayer's price–volume correlation); forbearance raises the arrears *stock* and
lowers the foreclosure *flow* (it is a delay, not a cure). Neither should move the calibration
window by more than seed noise, because one is inert in a rising market and the other fires
only on arrears the baseline barely has.

### 5d.3 What is still missing

Two of the four brakes the hold-out pointed at are **not** implemented, and are registered
rather than hand-waved:

- **Eviction moratoria.** Spain has suspended evictions for vulnerable households in an
  unbroken chain of decrees since RDL 11/2020. It is policy, not a permanent mechanism, so it
  belongs as a lever, and it does not exist yet.
- **Court congestion.** The judicial phase is a constant in the model, and in the episode it
  was a queue: filings multiplied fourfold while the courts' capacity did not. The CGPJ series
  the model carries has filings but not pending stock, so the queue cannot be identified from
  registered data and the constant stays.

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

## 6c. Insolvency and forced sale (phase C)

Until phase C the budget constraint did not bind: `_household_flows` wrote
`wealth = max(0, wealth − payment)`, so a household that could not pay its mortgage simply
had its shortfall absorbed by the floor. Nothing defaulted, nothing was repossessed, no
dwelling ever came back to the market against its owner's will. The 2008–13 hold-out
cannot be run against a model with no forced-sale channel at all, which is why phase C
precedes phase E (redesign spec §5).

Deriving the mechanism turned up a dependency that had to be fixed first: **there was no
income risk**. Every household's income grew at exactly the nominal anchor, so default had
no source. The chain is therefore, in order: employment status → arrears → statutory
foreclosure → bank-owned stock.

### 6c.1 Employment: exogenous rate, endogenous incidence

The unemployment *rate* is an exogenous path, on the same footing as the euríbor (§14). Who
it lands on is endogenous, and that is the part that matters for housing.

- **Zone rate.** The national path is scaled by the sourced urbanisation gradient: cities
  0.94, towns/suburbs 1.06, rural 1.03 of the national rate, then renormalised on the zones'
  household weights so the model's aggregate equals the path. The direction is the
  interesting one — **the tensioned metro is the least exposed zone**, and the gap widens in
  the bust (2013: 24.2 / 27.3 / 28.7 against 26.1 national) [Eurostat `lfst_r_urgau`].
- **Exit hazard.** A household leaves unemployment with probability `f` per quarter, constant
  within a run. With a constant hazard, the share of spells lasting over a year is
  `(1 − f)⁴`, which is exactly what the long-term-unemployment share measures: 32.1% in 2025
  ⇒ f ≈ 0.25; 52.8% at the 2014 peak ⇒ f ≈ 0.15 [Eurostat `une_ltu_a`]. The parameter is a
  measured range, not a dial.
- **Separation hazard** is then whatever makes the zone's unemployment share track its
  target, from the flow identity `u′ = (1 − f)·u + s·(1 − u)`:

  ```
  s_t = clip( (u*_z − (1 − f)·u_t) / (1 − u_t),  0,  1 )
  ```

  So the model never invents an aggregate labour-market story: it reproduces the one in the
  data, and decides only *whose* mortgage is at risk.
- **Incidence.** Within a zone, the separation hazard is tilted by income: the relative risk
  between the bottom and top income tercile is **2.2**, the ratio the education gradient
  shows over the whole cycle (ISCED 0-2 against 5-8: 2.0 in 2007, 2.2 in 2013, 2.45 in 2025)
  [Eurostat `lfsa_urgaed`]. Weights are normalised so the zone aggregate is unchanged. This
  is **reduced form and declared as such**: the identifying observable is education, and the
  model has income. It is registered as such rather than presented as derived.
- **Income while unemployed.** 70% of previous income for the first two ticks of the spell
  and 60% after, benefit exhausted after 8 ticks, then an assistance floor of 80% of IPREM
  (≈€5,760/yr) [LGSS arts. 269–270; IPREM 2026 €7,200/yr]. The statutory cap (175% of IPREM)
  is applied to the benefit.

**Known limitation, stated rather than fixed**: a model household is a single income unit, so
a labour-market hit removes its whole earned income. Real Spanish households average more
than one earner, which makes the *severity* here an overstatement and the *frequency* an
understatement (two earners give two chances of a hit). The two biases offset in an unknown
ratio; the EFF earner-count distribution would settle it and is not retrieved.

### 6c.2 Arrears: the budget constraint binds

For a mortgaged household each tick, with `income_eff` the income after any benefit
replacement:

```
saving        = saving_rate · income_eff / 4                     (as before)
consumption   = NET_INCOME_FACTOR · income_eff / 4 − saving      (implied by the saving rule)
essential     = essential_share · median_income / 4
compressible  = max(0, consumption − essential)
available     = wealth + compressible
```

If `available ≥ payment` the household pays, taking the money from savings first and cutting
discretionary consumption for the remainder. If not, it **misses the quarter — three monthly
instalments** — the principal is not amortised, and the arrears balance accrues at the
statutory default rate (remuneratory + 3pp, Ley 5/2019 art. 25; the law forbids capitalising
it into the principal, so the model keeps it in a separate balance). Arrears are cured
whenever capacity returns, oldest instalment first.

`essential_share` is the model's only new consumption parameter and it is a **sourced range,
not a guess**: INE's at-risk-of-poverty threshold is €12,220/yr for a one-person household
and €25,663 for two adults with two children (2025), i.e. 0.34 and 0.71 of the model's
median household income. The default sits at the conservative (one-person) end, so the model
under-produces arrears rather than over-produces them.

Note what this does **not** do: an employed household at the DSTI cap never enters arrears,
because 0.35 of net income leaves it above the floor by construction. Arrears in this model
come from *income loss*, which is the mechanism the evidence describes, and their level is
checked against the BdE doubtful ratio (§9 target 15).

### 6c.3 Foreclosure: the lag comes from the law

This is the best-identified mechanism in the model, and the only one whose timing is a
statute rather than an estimate.

- **Trigger** (`ley5_2019`, contracts from 16 Jun 2019): unpaid instalments ≥ **12** (or 3% of
  the principal granted) in the first half of the loan's life, ≥ **15** (or 7%) in the second,
  plus a lender demand giving at least one month [Ley 5/2019 art. 24, verbatim in
  `sources.md`]. The model applies the instalment leg and adds one tick for the demand.
- **Trigger** (`ley1_2013`, the regime governing the 2008–13 hold-out): **3** unpaid monthly
  instalments [LEC art. 693 as amended by Ley 1/2013]. The regime is a config switch, because
  the hold-out and the calibration window are legally different worlds. This alone changes the
  foreclosure lag by roughly three quarters and is not a parameter anyone fits.
- **Outcome.** At the trigger, with probability **0.478** the delivery is voluntary and happens
  without the judicial phase; of deliveries, **0.397** are daciones en pago, which extinguish
  the debt [BdE Circular 1/2013 note, 2014 data]. The remainder goes through a judicial phase
  of `foreclosure_lag_ticks` quarters before possession — **8–16 (2–4 years)**, the only
  element of the chain without a primary source. CGPJ publishes 8.5 months as the average
  duration of *all* first-instance civil matters, which bounds it from below, and only
  practitioner guides estimate the procedure itself, so it enters as a swept range and never
  as a reported magnitude.
- **Price.** The bank takes the dwelling at **70% of the auction value** — the statutory floor
  for a debtor's habitual residence [LEC art. 670.4]. The residual (debt + arrears − award) is
  **not forgiven**: Spanish mortgage debt is recourse [LEC art. 579]. The model writes the
  residual off the household's balance sheet but keeps its consequence, the credit lockout,
  which is what recourse means for the household's ability to buy again.
- **After delivery** the household becomes a SEEKER with a **credit lockout** of
  `lockout_ticks`, defaulted to 20 = the five-year maximum a default may be held in a credit
  register [LOPDGDD art. 20.1.d]. It is the legal ceiling used as a behavioural horizon, so
  it is declared reduced form with a 8–20 range.

### 6c.4 Bank-owned stock (REO)

The bank holds what it takes and releases it at a markdown — the overhang channel that
existed in 2008–13 and that the model has never had. Each tick it lists a share
`reo_release_share` of its stock at `zone price index × quality × (1 − reo_discount)`.

The discount is the weakest parameter in the block and is labelled as such: the registered
anchors (Sareb's 2012 transfer haircuts of 31–63% on housing; the 2012 provisioning
requirements) are haircuts against *book* value, not against market price, so they bound the
range rather than set the value. It enters as 0.10–0.35 with a 0.15 default, declared reduced
form, and the sensitivity analysis (phase E) decides whether anything reportable depends on it.

### 6c.5 What it is checked against, and what would kill it

`metrics.py` gains four indicators, each pointed at a registered series:

| Indicator | Anchor |
|---|---|
| `arrears_share` — mortgaged households in arrears | BdE doubtful ratio: 1.6% (2026Q1), 2.4–3.4% 2019–2024, 6.28% peak 2014Q1 |
| `foreclosure_rate` — deliveries per mortgage per year | BdE Circular 1/2013: **0.7%/yr in 2014** (0.6% main residences) |
| `dacion_share` — voluntary, debt-extinguishing deliveries | BdE note: 39.7% of deliveries |
| `unemployment_rate` — the model's realised rate | the exogenous path it is fed |

**Falsification** (redesign spec §7.6): run with 2008–13 inputs, the foreclosure flow must
reach the order of the CGPJ series at its peak — 93,636 filings in 2010, ≈1.4% of the
6.46M household mortgages outstanding, twice the 0.7% of 2014. If the mechanism cannot
produce that under the 3-instalment regime of the period, it is false and is reported as
false. That test belongs to phase E: the hold-out is run once, after recalibration, and
nothing here is touched afterwards.

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
| ~~Exit hazard scale (`HAZARD_SCALE`)~~ | ~~maps the per-listing quarterly hazard onto the studies' annual contract elasticity; re-fitted after the shadow rent so elasticity 2 reaches Monràs's −10% contracts — value and sweep in validation.md / experiments/rent-cap.md~~ **RETIRED, §7.2 (2026-09-16)**: replaced by the arbitrage condition `cap < r_req`; no fitted hazard remains | dimensionless | was Monràs & García-Montalvo 2023/2025 (IV ≈2) | **retired**, phase §7.2 |
| Public social-rental stock | 1.5–3.3% of stock | % stock | MIVAU/Provivienda [government §6] | medium |
| Unemployment path (level) | exogenous quarterly path; baseline 0.105 (2026Q2), bust leg reaches 0.263 (2013Q1) | share of active population | Eurostat/INE EPA `une_rt_q` | high — it is an input, not a result |
| Zone unemployment gradient | T 0.94 / S 1.06 / R 1.03 of the national rate, renormalised on household weights | dimensionless | Eurostat `lfst_r_urgau` 2006–2025 | high (direction and level) |
| Unemployment exit hazard | 0.25 /quarter (range 0.15–0.25), from (1−f)⁴ = long-term-unemployment share | prob/quarter | Eurostat `une_ltu_a` | derived from a measurement |
| Unemployment incidence gradient | relative risk 2.2 between bottom and top income tercile (range 2.0–2.45) | dimensionless | Eurostat `lfsa_urgaed` (education basis) | reduced form — the observable is education, the model has income |
| Benefit replacement | 0.70 for 2 ticks then 0.60, exhausted after 8 ticks, floor 80% IPREM, cap 175% IPREM | fraction of previous income | LGSS arts. 269–270; IPREM 2026 | high |
| Essential consumption floor | 0.34 of median household income (range 0.34–0.71) | fraction | INE ECV poverty thresholds (1 person / 2 adults + 2 children) | high as a range, conservative end chosen |
| Foreclosure trigger | 12 instalments (3% of principal) first half of the loan, 15 (7%) second half; **3 instalments** under the pre-2019 regime | unpaid monthly instalments | Ley 5/2019 art. 24; LEC art. 693 (Ley 1/2013) | statute — not a parameter |
| Judicial phase | 8–16 (default 10) | quarters | practitioner guides (2–4 yr), bounded below by CGPJ's 8.5-month civil average | low — swept, never reported as a magnitude |
| Delivery outcome split | voluntary 0.478 of deliveries; daciones 0.397 (0.83 of voluntary ones) | share | BdE Circular 1/2013 note, 2014 | high |
| Award price | 0.70 of auction value (habitual residence) | fraction | LEC art. 670.4 | statute |
| Post-foreclosure credit lockout | 20 (range 8–20) | quarters | LOPDGDD art. 20.1.d (5-year register ceiling) | legal ceiling used as a behavioural horizon — reduced form |
| Bank REO discount / release | discount 0.15 (0.10–0.35); release 0.15 of held stock per tick | fraction | Sareb 2012 transfer haircuts (31–63% on book, not market) | the block's weakest parameter — declared reduced form |
| Search breadth `m` | 2 (range 1–10) | affordable listings sampled per buyer per tick | idealista/data days-on-market distribution; Tecnocasa bidders per dwelling | reduced form, identified on two observables |
| Ask markup over expected value | 0.08 (range 0.04–0.12) | fraction | Tecnocasa-UPF 6.2% realised margin; Fotocasa distribution (23% beyond 10%) | medium — the posting convention is sourced, the level is the measured margin |
| Seller reserve | max(debt + 2% selling costs, ask × (1 − discount)) | € | accounting (the sale repays the loan) + the negotiation margin above | derived (debt leg) / medium (floor leg) |
| Auction increment | 0.005 of the runner-up's bid | fraction | institutional minimum | guess — it moves the price by half a percent at most |
| Seller bargaining power θ (single-bidder sales) | 0.85 | fraction of the surplus | calibrated against the 6.2% measured margin | reduced form, the block's one free parameter |
| Taste dispersion (`overbid_sigma`) | 0.02 (range 0.02–0.06) | sd of value multiplier | none — guess, DEMOTED in phase D from price dispersion to taste | guess; its variance share is phase E's Sobol question |
| Expectation gain on the valuation (`MOMENTUM_GAIN`) | 2.5, capped ±10% | multiplier on expected growth | re-identified on price-to-income and the BdE purchase effort when the channel moved | reduced form, calibration-window only |
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
| Credit crunch (`CreditCrunch`, phase C) | max LTV, max DSTI and the lending spread move together; optionally an unemployment path | Bank practice + supervisor (exogenous) | ΔLTV −0.05…−0.20; ΔDSTI −0.03…−0.10; Δspread +0.5…+3pp | lending volume collapses first, arrears and foreclosures follow with the statutory lag, bank REO builds up |
| Unemployment path (`LabourShock`, phase C) | the exogenous quarterly unemployment path, per §6c.1 | exogenous (declared boundary) | any path; the 2008–13 leg is the EPA series itself | arrears → foreclosures → forced supply; the hold-out's main input |
| Rate shock (bonus lever) | euríbor path shift | ECB (exogenous) | ±pp path | volume ↓↓, prices sticky (2022–23 signature) |

## 9. Validation (contract for Phase 6)

What may be *claimed* from a passing target is governed by the reporting contract (§13):
targets pass or fail here, but a passing target is not automatically a reportable magnitude.

Baseline (no intervention, 2015–2025-like inputs) must reproduce, before any scenario
result is reported:

1. **Tenure shares**: owner 70–74% (EFF basis; ECV 2025 gives 73.3% owners, 20.2% renting,
   6.5% ceded), tenant 24–27% national; tenant share ranking T > S > R [household-tenant §6].
   The ranking leg is gated since 2026-09-12 on the `tenant_share_*` columns (31.4 / 22.7 /
   17.0%, holding on each of 3 seeds); its *levels* are not gated — the tensioned leg runs
   above the 0.27–0.30 band in §7, the same zone-aggregation qualification target 2d carries.
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
   Pérez García (≈0 robust price effect, −13% tenancies) worlds [rent-cap §4]. **Status 2026-09-15: NOT MET, after §5b.1 split the cap
   into its two statutes** (`docs/experiments/rent-cap.md`, ten seeds). Under Ley 11/2020 —
   the law the three studies evaluate — the rent leg moves **0.8pp across the whole dial**
   (−19.3% at ε=0 to −18.5% at ε=2) because the cap's level, not the behavioural parameter,
   sets it; the quantity leg spans +21% to −49% and does reach Monràs's −10% at ε≈1. Under the
   law in force two of the three studies can be reproduced (Jofre-Monseny at ε≈0, Pérez García
   at ε≈1.5) but that is a different instrument and is not evidence about theirs. Closing the
   gate means calibrating how far the reference index sits below market per regime — measured
   at 16% here against published implied cuts of −10…−15% (Catalan index) and −20% (state
   index). **Until then the SIZE of any rent-cap rent effect is not quotable, only its sign.**

   *Superseded status, 2026-09-08: met, with all three studies INSIDE the dial* (validation.md
   S3, 5 seeds):
   elasticity 0 → rents −4.9%, contracts +0.9%; elasticity 1.5 → −8.7%; elasticity 2 → rents
   −4.2%, contracts −13.6% ± 2.8, so Monràs's −10% falls between 1.5 and 2 and Pérez García's
   −13% at 2 — where the earlier fit needed ≈2.7 and was documented as out of range. Both legs
   are ordinary passing tests. The gate had silently failed after the August audit (the asking
   index collapses onto an active cap and blinded the landlord's exit decision, and the
   tensioned queue ran slack) and was repaired by the shadow rent (§5b), metro-weighted
   formation (§4 step 2) and two hazard re-fits. Partial coverage (`coverage` < 1) is **not**
   reportable on the pooled rent (T7).

Targets 9–15 are the **phase-0 precision contract** (redesign spec §5, §6): seven observable
moments the model could already have been failing silently. Several are red on arrival — that
is their purpose. Measured values live in `docs/validation.md` "Phase-0 targets" and are not
repeated here; what is fixed here is what each target asserts, on what evidence, and what a
pass is allowed to mean.

9. **Zone gross-yield ladder, EMERGENT**: tensioned 4.7–5.6%, secondary 6.5–7.5%, rural 7–9%
   [idealista Q4-2025/Q1-2026 cross-section — Spain 6.7%, Madrid 4.7%, Barcelona 5.6%,
   capitals to 7.5%; BdE DO 2432 RBA 5.5%]. Bands widened symmetrically by 0.5pp for seed
   noise, the same convention as the other zone targets. Gated. `ZoneConfig.gross_yield` is an
   initial condition only: the ladder the model then produces is a prediction, and the single
   observable that says whether the landlord's reservation rule is right. **Strict xfail** —
   the rural leg runs at roughly twice the band. **STATUS CORRECTED 2026-09-17**: this line
   read *"Fixed by the total-return hurdle and buy-to-let entry (spec §7.1, §7.3 — phase B)"*
   while the leg was, and still is, a strict xfail. The total-return hurdle (§7.1) shipped in
   phase B and did **not** close it. Buy-to-let entry did not ship at all — see §7.3.
10. **Boom compresses the gross yield**: direction only. Spain 2014–25 ran prices ahead of
    rents and gross yields fell. Gated on the sign, and only on the sign: the registered
    idealista row is a **cross-section**, not the 2014–25 **time series** a band on the
    compression itself would need. Passing — and this is phase 0's most important
    qualification, because under the current reservation rule it passes as a byproduct of
    asking rents lagging prices, not as the prediction of a required yield responding to
    expected appreciation (`docs/validation.md`, referee pass). Re-read it after phase B.
11. **Rent level ordering T > S > R**: strict, at every published basis [idealista, SERPAVI,
    EPF regional averages — €675/month Madrid against €277 Extremadura, Funcas 104 ch.5].
    Gated. The zone ladder was gated on *prices* only (target 2b), which is how a rural asking
    rent above the metro index survived 60 ticks and 3 seeds unnoticed. Asserted on all three
    seeds, not on a seed average. **Strict xfail** — rural overtakes the metro around tick
    35–40. **STATUS CORRECTED 2026-09-17**: this line read *"Fixed by bidirectional migration
    and buy-to-let entry (spec §7.3, §7.5 — phase B)"* while the target was, and still is, a
    strict xfail. Bidirectional migration (§7.5) shipped in phase B and did **not** close it.
    Buy-to-let entry did not ship at all — see §7.3.
12. **Net internal migration into TENSIONED > 0**: direction only; the level needs INE
    Migraciones y Variaciones Residenciales, which is not yet registered. Gated on the sign.
    Spain's net internal flow runs rural→metro and the model has it inverted by construction
    (`engine._demography` moves households one step *down* the ladder and never up). **Strict
    xfail** — it cannot be positive until the rule changes. Fixed by bidirectional flows
    identified on the INE series (spec §7.5 — **phase B**).
13. **Time to sell** (`sold_within_quarter_share`): **gated since phase D**, at 43–63%
    against idealista/data's ≈53% of dwellings sold inside a quarter (7% under a week, 19%
    within the month, 27% within three months, 36% within the year, 11% longer). The model
    reads **47.7%**. The within-a-year leg is a floor only (≥85%, model 99.97%): the model
    cannot produce the 11% tail beyond a year, because `max_listing_ticks` withdraws a
    listing after six quarters and that parameter is a guess.
13b. **Bidders per listing**: gated as a **bound**, 1 < b ≤ 7, against Tecnocasa's seven
    interested parties per dwelling (2S 2025, double two years earlier). The bases differ on
    purpose — that is interest on an agency's files, this is bids placed — so the bound is
    what the evidence supports and a band is not. Model **3.6**.
13c. **Negotiation margin** (`sale_discount_median`): gated at 4–12% against a measured 6.2%
    [Cátedra Tecnocasa-UPF] and Fotocasa's distribution. **Strict xfail on arrival**: the
    model reads 3.0%, because its market is more competitive than Spain's (17% of sales above
    the ask against Fotocasa's 9%), and the fix is on the demand side rather than in the
    auction (§5c.5).
    Provenance: until phase D these three were one target, reported and not gated, because no
    source in `docs/sources.md` carried days on market. The two that identify the auction were
    retrieved on 2026-09-14 and the gates followed. `max_listing_ticks` remains a guess and is
    what truncates the model's tail; `ask_decay` is a guessed *level* that names an
    identifying episode and a range, which is why only the first is among the twenty rules
    the register counts as failing the derived-or-reduced-form rule. Conversion note: listings
    age before clearing, so "sold within the tick" is 0 ticks, not ≤1.
14. **Landlord households** (`landlord_household_share`): **reported, not gated**, on an
    explicit **EFF basis** — households owning a dwelling they do not live in, which includes
    vacant second homes, withheld and seasonal stock. Two anchors are registered and they
    bracket rather than band it: EFF 36.1% of households own other real estate (2022 wave),
    revised to 45.3% in the register's most recent wave (2024, DO 2610), and AEAT's 2.37M
    landlord declarants over the 19.87M household anchor (§7) ≈ 11.9% on a
    *declaring-rental-income* basis. Roughly three-to-four-fold apart, because they measure
    different things. What is missing is the EFF **wealth-percentile gradient** (spec §9
    retrieval list), which is what would say where inside the bracket a model with no
    buy-to-let entry margin should sit. Phase B was to specify the AEAT-basis sibling column
    (rented units only) and decide which basis the gate is set against. **It did not, and this
    line claimed otherwise until 2026-09-17**: `metrics.py` emits `landlord_household_share` on
    the EFF basis alone, there is no AEAT sibling, and the gate is set against the only column
    that exists. The choice of basis is therefore still open, not made.
16. **Idiosyncratic sale-price dispersion**: the sd of log sale price net of zone × tick and
   observable quality, **6–17% per sale, central 10%** [Kotova & Zhang, US zipcodes 2012–16,
   mean 16.8%; Giacoletti *RFS* 2021, 6.8–12.4%; Landvoigt-Piazzesi-Schneider *AER* 2015,
   6.2–9.8% — the last two published as RETURN dispersions, ÷√2 here]. No Spanish estimate is
   published and the absence is a registered row in `sources.md`. This is what
   `overbid_sigma` is identified against (§5c.6); the model read 2.3% before phase G and
   8.0% after.
15. **Foreclosure flow and arrears** [BdE Circular 1/2013; BdE table 4.13; CGPJ; INE EH]:
    live since **phase C**, measured on two legs, because the two published bases are not the
    same quantity and conflating them is how this target would be faked.
    - *Arrears*, gated: `arrears_share` — mortgaged households behind on payments — must sit
      in **1.0–4.0%** in a calibration-window baseline. The BdE doubtful ratio on
      house-purchase credit ran 1.60% (2026Q1), 2.33–3.40% over 2019–2024 and peaked at
      **6.28% in 2014Q1**; the band is the calm-period range with room for seed noise, and the
      peak is a hold-out observation, not a baseline one.
    - *Deliveries*, gated and **failing on arrival (strict xfail, 2026-09-14)**:
      `foreclosure_rate` — dwellings delivered per mortgage per year — must sit in
      **0.10–0.80%/yr**. The only like-for-like published figure is the BdE's **0.7% in 2014**
      (0.6% for main residences), the tail of the bust; INE's dwelling series falls from
      34,880 (2014) to 5,361 (2019) main residences, and 2019's flow over ≈5.6M mortgages is
      ≈0.10%. The model produces **≈0.02%/yr**, five times below the floor, and the reason is
      identified: a distressed owner with positive equity always finds a buyer inside the
      listing window, so almost every statutory trigger becomes a voluntary sale. What stops
      that in reality is negative equity after a price fall, the discount on an occupied
      dwelling, and the months a sale takes — the first two are phase D (§7.7) and the third
      is the bust itself. Reported as a failure rather than closed by moving the band.
    - *Composition*, reported not gated: `dacion_share` against the BdE's 39.7% of deliveries.
      It is an outcome split the model is given, so gating it would test the input.
    The bust leg — CGPJ's 93,636 filings of 2010, ≈1.4% of outstanding mortgages — is **not**
    tested here. It is the phase-E hold-out and the mechanism's declared falsification
    (§6c.5): run once, after recalibration, and reported pass or fail.
    Registered in `docs/holdout-2008-2013.md` and in the assumption register.

Three of these (9, 11, 12) are strict xfails. Strict means an accidental pass also fails the
suite, so none of them can quietly stop being true, and none can be retired by a partial fix.

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

Applied to the current model this downgrades to direction-only: the **rent level**
(`small_landlord_premium`, 65%), **tensioned market vacancy** (75%) and **rent overburden**
(62%); the **ownership rate** and the **zone price ratio T/R** (`buy_attempt_prob`, 36% and
34%); the **cash-purchase share** (`search_listings`, 41%); and the **negotiation margin**
(`seller_bargaining_power`, 32%, and circular — it is identified on this). `price_to_income`
is **not** on the list: its largest assumed share is `momentum_gain` at 11%, and it is the
project's first reportable magnitude. The rule sets the evidence-work priority order without
argument: source the parameter, or stop quoting the number.

> **EXAMPLE CORRECTED 2026-09-17.** It read *"`price_to_income` (`overbid_sigma`, 56%),
> `rent_overburden_share` and the rent level (`landlord_required_spread`, 65% and 40%), and
> tensioned market vacancy (74%)"* — the figures from the 230 + 1,152 run. Both parameters it
> named have since stopped being the answer: `overbid_sigma` **left the screening entirely** and
> is now counted as sourced, and `landlord_required_spread` **was retired** in §7.1 (2026-09-14),
> split into a measured prime component and `small_landlord_premium`. The rule that decides what
> this project may quote was illustrated with a parameter the model no longer has, and it pointed
> the evidence work at it. Figures above are the phase-G re-run (390 + 1,792 evaluations,
> `docs/validation.md`).

### 13.3 Derived-or-reduced-form rule

> Every behavioural rule is either **derived** from a declared primitive — an optimisation, an
> arbitrage condition, an accounting constraint — or explicitly labelled **reduced form**, with
> the episode that identifies it and the range the evidence admits. There is no third category.

A reduced-form rule with no identifying episode is a defect, not a simplification.
**Twenty** rules were named as failing this test when the phase-0 register pass was written:
the nine named in the redesign spec §3.1, plus eleven the phase-0 register pass added —
`NET_INCOME_FACTOR`, `buy_attempt_prob`, `max_listing_ticks`, the frictionless leg of
assortative rental matching, the 5% over-budget search tolerance, `EXIT_SPLIT_EVASION_BASE`
(**retired, §7.2, 2026-09-16** — the parameter and the mechanism it patched are both gone, not
replaced by a sourced rule), the investor's ×1.15 accumulation band, `PRIME_HURDLE_SPREAD`,
`EXIT_LIST_SHARE`, `MAX_BUYS_PER_TICK` and the pace leg of `SEARCH_BURDEN_ESCALATION`. The
criterion, the full list and the **current, running** count are in `docs/assumptions.md`, not
restated here as a number so it cannot drift out of step again; a rule with no row there is a
finding against the register.

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

### 13.7 Rental-yield basis (decided 2026-09-12, phase B)

Every yield the model reports or is judged on is on a **contract basis**, not a portal asking
basis. Portal asks are not transactions: prices are negotiated down, listings are edited and
re-posted, and a withdrawn ad leaves no trace. What was signed is the more reliable object.

That decision leaves a second axis, and it is not the same one. Contract-basis yields come in
two flavours, and Banco de España publishes both:

| | What it measures | Value | Series |
|---|---|---|---|
| **Stock** (RBA) | AEAT declared rents for the stock of let dwellings ÷ Registradores prices per m² | 4.65% (2014Q2) → 2.90% (2026Q2) | `D_TKR60REA_VIV_IPV` |
| **Entry** | New contracts, BdE's own estimate since 2015 | **6.5–7.5%** | DO 2432 §3.3, a range not a series |

The stock yield is an average over contracts signed across many years under LAU terms and
capped within-contract updates. It is the right object for asking *what letting has returned*.
It is the wrong object for a landlord's **entry** decision, which is made on the marginal unit
at today's terms — and the entry decision is exactly what §7.1's reservation rent and §7.3's
buy-to-let margin model.

**Therefore:**

1. The model's yield observable is an **entry** yield and is computed on `rent_transacted`
   (median new-contract rent, SERPAVI-like), not on `rent_index` (asking). `gross_yield_*`
   keeps the asking basis and is retained for comparability with the portals;
   `gross_yield_contract_*` is the contract-basis entry yield and is the one the targets are
   set against. Both are reported so the basis can never be silently confused again — the same
   discipline §5b applies to the two rent bases.
2. Target 9's band is BdE's entry range, **6.5–7.5% national**, not the RBA's 2.90%. The
   per-zone ladder keeps its ordering claim; its levels are re-derived in phase B rather than
   carried over from the portal cross-section.
3. The §7.1 compression test is settled by this decision and stops being source-dependent.
   On the contract stock basis the RBA compresses monotonically across the whole 2014–26 boom,
   −175 bp from the 2014Q2 peak. The portal series disagree in sign before 2021 — Fotocasa's
   asking yield *rises* 5.0% → 6.8% to 2020 — and that disagreement is now recorded as a
   basis difference, not as an open question about the world.
4. `π` is a **constant with a zone gradient**, declared, not a cyclical term. No free
   historical prime-yield series exists (403 on CBRE and Savills), so π can be bounded at a
   point — ≈ +25 bp Madrid / +45 bp Barcelona prime against the March 2026 bond — and not
   tracked through a cycle. Claiming a cyclical π would be claiming a series nobody has.

**§7.1's operating-cost share `c` — retrieved 2026-09-15, second-sourced 2026-09-16.**
`r_req = V·(i_bond + π − E[g]) / (12·(1−c))` ships `c = 0.22`, range 0.20–0.24, from AEAT's
declared-rent P&L, with the statutory 3%/yr building depreciation (art. 23.1.b LIRPF, 15–18pp)
and mortgage interest (1.4–4.2pp) taken out — the first double-counts E[g], the second the
financing leg of `i_bond + π` — and with vacancy left out because `market/clearing.py` already
generates it. §7.1 **is** coded, in `agents/landlord.required_rent` and `agents/investor`; the
paragraph that stood here said it was not, and was stale from 2026-09-14.

**The second source is INE's national accounts**, and it is independent of AEAT on the side that
matters. CNE table 69069 publishes branch `68a — alquileres imputados de las viviendas ocupadas
por sus propietarios` separately: its *output* is the stratification estimate (Censo 2021 + EPF +
IPC/IPVA) and its *intermediate consumption* is built from the EPF's COICOP 04.3.3 plus insurer
payouts on multirriesgo policies — not from IRPF [INE, *Inventario de fuentes y métodos de la
RNB*, rev. 2024, §§3.18.2, 3.18.5]. IBI enters ESA as other taxes on production (D.29), not as
intermediate consumption, so it is added back. That gives

| | (CI + D.29) / output |
|---|---|
| 2023 | **10.9%** |
| 2013–2022 | **15.3–18.0%** |
| 1997–1999 | ≈31% |

INE applies the same ratio to *let* dwellings by assumption (§3.18.5, final paragraph), which is
what makes it usable here; the output side of the actual-rental branch does come from IRPF
(§3.18.3), so only the ratio transfers, not the level.

**This is a lower bound on `c`, not a rival estimate of it.** National-accounts IC counts only
the renovation-and-repair part of a comunidad quota and no management or letting cost at all,
and both sit inside AEAT's deductible rows. The gap between ≈16% and 22% is the size of those
two items and is the right sign. What the series does dispute is that `c` is a **constant**: the
ratio falls monotonically from ≈31% (1997–99) to ≈16% (2016–22) because the denominator tracks
rents while maintenance spending does not, and 2023's 10.9% is a level break introduced by the
2024 statistical revision, not a behavioural change. The model ships a constant calibrated to the
recent end of a falling trend, and that is now a declared property of the parameter rather than
an unexamined one.

Still unreconciled, and recorded rather than resolved: DO 2432's 2pp off a ≈5.5% RBA implies
≈36% of gross rent, against AEAT's own 41–45% gross-to-net on the same object while citing it.
Neither figure **is** `c` — both carry depreciation and interest.

**§7.2 was a different blocker, and it was never this one.** It had been referenced here, twice
in `docs/validation.md` and once in `config.CapResponseConfig` as the arbitrage condition that
would replace the rent cap's fitted `hazard_scale`, and it had **never been written** — it was
waiting on being specified, not on a parameter. It was written as of 2026-09-16, and **is now
implemented**: `hazard_scale`, `rental_supply_elasticity`, `exit_split_sale`,
`exit_split_vacant` and `exit_split_evasion_base` are retired, and the cap's withdrawal margin
in `agents/landlord` is the arbitrage condition `cap < r_req` described above, not the reduced
form. Three of §7.2's own calibration gates fail **on purpose**: under Ley 11/2020 the
arbitrage condition triggers mass withdrawal and the rent leg flips sign — measured **rent
+53.6%, leases −78.7%** with the seasonal segment open, **+52.2% / −76.7%** with it closed. This
is the recorded falsification §7.2's own Falsification subsection calls for, not an
implementation defect; see `docs/validation.md` "Honest qualifications" for the full diagnosis
and the repair this leaves for a later spec revision.

### 13.8 Migration: interior and exterior, reported separately (decided 2026-09-12, phase B)

Target 12 is restated on **total** migration — interior plus international — not on interior
flows alone. The reason is that the two run in opposite directions in Spain and only their sum
answers the question the model is asked: does the metro zone grow?

| | Direction, 2017–2024 | Source |
|---|---|---|
| interior | metro **loses** every year (capitals −29,400 in 2019, −117,596 in 2020, −55,195 in 2024) | INE EVR microdata 2015–21; EMCR 69753 2021–24 |
| international | metro gains — this is why Spanish cities grow | INE EVR/EMCR exterior leg |

Stating the target on interior flows alone, as the spec did, registers the model's correct
behaviour as a failure. Stating it on total flows makes the claim the one anybody arguing about
Spanish housing actually makes.

**Structural consequence, and the reason this is worth doing beyond fixing a target.** The
model already contains international arrivals — it just does not say so.
`PopulationConfig.formation_zone_weights` tilts new households toward the metro, and that tilt
is doing the work of immigration while being labelled *household formation*. Two flows with
different drivers, different sources and different policy exposure are fused into one
parameter, and that parameter was calibrated by screening against the §9 gates (finding 8).

Phase B therefore splits it:

1. **Domestic household formation** — Spaniards forming new households. Driven by the INE
   household projection already in `scenario.py`, allocated by existing population.
2. **International arrivals** — allocated on the observed exterior-migration zone gradient,
   with its own rate. **Exogenous, and already declared so**: §14 places "foreign
   origin-country conditions" outside the model, and arrivals are driven by them. Making the
   flow explicit does not widen the exogenous boundary; it stops an exogenous flow from
   hiding inside a fitted weights vector.
3. **Interior migration** — the §7.5 bidirectional rule, from a zone comparison (expected
   income × amenity − housing cost) with a friction, identified against the 2020 reversal:
   the metro outflow is 4.2× its 2019 value while *gross* interior flows fall 7.9%, so it is
   pure redirection of a shrinking flow and identifies the elasticity without a volume
   confound.

Interior and total net migration are both reported per zone, the same discipline already
applied to the two rent bases and the two yield bases (§13.7). Nobody gets to quote one as the
other.

**The zone mapping is declared, because the sign depends on it.** INE's size bands do not sum
to the model's 45% tensioned zone: provincial capitals are 31.7% of the padrón, adding
>100k non-capital gives 42.2%, adding 50–100k gives 53.4%. The tensioned zone sits in the gap.

**Mapping B is fixed: tensioned = provincial capitals + non-capital municipalities above
100,000.** 42.2% against the model's 45% is the closest in size, and the only one that also
matches in character — a tensioned metro market is capitals and large cities, not towns of
50,000. Secondary = 20,001–100,000, rural = ≤20,000.

This is not a cosmetic choice. On total migration the metro is negative in 2020 and 2021 under
mappings A and B and **positive** under C, in both statistics: the 50,001–100,000 band alone,
11% of Spain, carries enough exterior inflow to reverse the aggregate sign in exactly the years
the target is most interesting. A model that passes under B would fail under C. The mapping is
therefore part of the target, declared here, and any result quoted against target 12 is void
without it.

**Target 12, restated.** Two claims, doing different jobs, both falsifiable:

1. **Baseline** — total net migration into the tensioned zone is **positive**. That is what
   Spain does in six of the eight years measured (2017–2024, mapping B).
2. **Identifying episode** — a 2020-like shock turns it **negative**, with the interior outflow
   rising and the exterior inflow falling at the same time. Under mapping B the metro total was
   −14,649 (2020) and −11,548 (2021), driven by the interior outflow quadrupling while capital
   arrivals from abroad halved, 362,085 → 203,256.

The model has to reproduce both. That is strictly harder than the original target, not easier.

**Two signs are robust and may be relied on** regardless of mapping: interior net turns negative
for the metro in 2017 under every mapping and both statistics, and exterior net is positive in
every year under every mapping.

**Caveat carried with the 2021 figure.** *Bajas por caducidad* — expiry of the registration of
non-EU foreigners who do not renew — have counted inside exterior emigration since 2006, and
INE's own methodological note says foreigners' departures are otherwise largely uncaptured.
There is no published split, so part of the capitals' 210,387 departures abroad in 2021 may be
an administrative purge rather than emigration. 2021 is one of the two negative years, so the
episode is identified on 2020 and 2021 is corroboration, not evidence in its own right.

**Levels are not coded yet.** The mechanism is specified; the rates come with the §7.5
implementation.

## 13.9 What the model may claim, after phase E (2026-09-14)

The variance rule is no longer a policy, it is a verdict. Sobol on the eight parameters Morris
left standing (1,280 evaluations, `docs/validation.md`) gives:

| Quantity | Largest unsourced share | Category |
|---|---|---|
| Ownership rate | flat across the design | **magnitude** |
| Arrears | < 0.10 (the 0.78 is `essential_share`, a measured range) | **magnitude, conditional on the INE poverty-threshold band** |
| Completion ratio | `base_starts_per_tick` 0.56, a sourced flow with a range | **magnitude, conditional on that band** |
| Price level, price-to-income, purchase effort | `overbid_sigma` **0.26** | **direction only** |
| Rent level, zone price ratio, overburden | `overbid_sigma` 0.29–0.40 | **direction only** |
| Transactions | `ask_markup` 0.89 | **direction only** |
| Market vacancy, cash share | `overbid_sigma` 0.37–0.42 | **direction only** |
| Time to sale, negotiation margin | `search_listings` 0.94 / 0.56 | **direction only**, and identified on those same observables |

Phase D cut `overbid_sigma`'s share of the price-level variance from **56% to 26%** — and 26%
is still above the threshold, so the price level stays direction-only. The way to change that
is to measure the dispersion of willingness-to-pay for identical dwellings, not to argue about
the threshold.

The 2008–13 hold-out was run once on 2026-09-14 and is reported in full in
`docs/validation.md` and `docs/holdout-2008-2013.md`: three of six pre-registered predictions
passed, including the foreclosure flow, which both phase C and phase D had predicted in
writing would fail. Prices overshoot the observed fall by a fifth and the arrears stock comes
out at a third of the BdE's, both for the same reason — nothing in this model slows a market
once it turns. **No parameter has been changed since that run and none may be.**

## 13.10 Where the model's answers are published

`docs/claims.md` — the claims ledger, added in phase F. One row per public claim, quoted and
attributed: what the claim requires to be true, what the model says in directions on ten
seeds, the verdict (supported / contradicted / conditional / unidentifiable) and what evidence
would settle it. It is the file this project exists to produce, and it obeys §13.9: no row
reports a magnitude the variance rule does not allow.

## 13.12 When parameter sourcing stops (decided 2026-09-15)

The variance rule has a defect as a work queue: it asks which *unsourced* parameter explains
the most variance, and every ranking has a first entry. Close one and the next is promoted.
Since phase E it has named `overbid_sigma`, then `ask_markup`, then `price_index_smoothing`,
then `small_landlord_premium`, and behind them sit `buy_attempt_prob` and `search_listings`. One
of them — `seller_bargaining_power` — **can never be closed**, because it is identified on the
very moment it governs. Followed literally the rule is a treadmill.

So it is bounded here, by purpose rather than by exhaustion:

> **Parameter sourcing stops when every quantity a registered claim in `docs/claims.md` depends
> on is either a reportable magnitude or explicitly published as a direction, and the unsourced
> shares that remain sit on quantities no claim uses.**
>
> What remains unsourced after that point is not a to-do list. It is declared, with its size
> and its falsification condition, in `docs/assumptions.md`, and the model is used.

Three things are declared irreducible under this rule as of 2026-09-15, and no further work is
scheduled against them:

1. **`seller_bargaining_power`** — circular by construction (§5c.1). It is identified on the
   negotiation margin, so the margin can never be independent evidence about it.
2. **The residual of `small_landlord_premium`** — components justify 0.5–1.2pp of a shipped
   3.0pp (§7.1b). Closing it needs a price for regulatory risk that nobody publishes.
3. **A replacement hold-out.** 2008–13 is spent (§13.11). Until an unused episode with the
   right inputs exists, out-of-sample replication is a claim this model cannot renew.

The corollary matters as much as the rule: **after the stop, work on this model is experiments,
not refinement.** A parameter that moves nothing anyone is asking about is not evidence work,
it is decoration.

## 13.11 The hold-out is burned, and what that costs

The 2008–13 episode was run once on 2026-09-14 (§13.4, `docs/holdout-2008-2013.md`). On
2026-09-15 the model gained two mechanisms — §5d — **because that run revealed they were
missing**. Both are identified on evidence unrelated to the episode (a peer-reviewed estimate
from 1990s Boston; a Spanish statute and its published operation counts), and no parameter was
set by looking at 2008–13 output.

That is not enough to keep the episode as evidence, and the contract says so plainly:

- The 2008–13 run **may still be executed**, and is, as a **diagnostic**: does the mechanism
  that was added for a stated reason behave the way the source says it behaves?
- It **may never again be cited as out-of-sample validation of this model**. A model that has
  been changed in response to an episode is in-sample on that episode, whatever the provenance
  of the parameters.
- Any future out-of-sample claim needs a **different sealed episode**, chosen and sealed before
  the mechanisms that would be tested on it exist. Candidates are registered nowhere yet; the
  obvious ones are Spain's 1992–96 correction and a non-Spanish bust with comparable
  registers.

The cost is stated rather than minimised: the project traded its one clean out-of-sample test
for a mechanism it had good independent reason to add. Whether that was the right trade is a
judgement the reader can now make, because both sides of it are on the record.

## 14. Exogenous boundary

What is outside the model by construction, enumerated in `docs/assumptions.md` §"Exogenous
boundary": macro feedback, employment and income paths, policy rates, foreign origin-country
conditions, geography below the zone, construction input costs, landlord taxation and
utilities, and unmodellable shocks. Phase C makes one of these explicit rather than widening
it: the **unemployment rate** is now a declared exogenous path (§6c.1), on the same footing as
the euríbor. What the model decides is incidence — which household loses its income, and what
that does to its mortgage — not the aggregate labour market. Being outside is not a defect. Leaving it unsaid would be.
