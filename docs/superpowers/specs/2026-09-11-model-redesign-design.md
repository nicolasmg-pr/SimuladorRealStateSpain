# Model redesign — design spec

Date: 2026-09-11. Status: **design approved in chat, not yet implemented.**

Origin: a code-level critique of the Phase-6 model found ten defects, three of them
structural (no scarcity→price channel, rental yield imposed rather than emergent, no
insolvency). This spec is the decision record for fixing them. It supersedes nothing in
`model-spec.md` until each phase lands; `model-spec.md` stays the authority on what the
*current* code claims.

## 1. Goal, stated precisely

The model must be **unimpeachable in its framing**, not clairvoyant about outcomes. What is
under our control is the specification: which primitives, which assumptions, which evidence,
and what the model refuses to say. Realised futures are not a test of the framing; a meteorite
is nobody's modelling error.

Operationally that means the model may be judged on:

- **Directions and orderings** — which lever moves what, in which sign, in which zone.
- **Conditional magnitudes** — "over the parameter range the literature admits, the effect is
  X…Y", plus which of those worlds a given public claim requires in order to be true.
- **Out-of-sample replication** — reproducing 2008–13 without having been fitted to it.
- **Identification** — saying which claims are *unidentifiable* on existing evidence. The
  distinction between "false" and "nobody can know this" is the model's sharpest output.

Point forecasts of price levels are outside the contract and stay outside it.

## 2. The findings this spec closes

| # | Finding | Phase |
|---|---|---|
| 1 | Rent ladder inverts: rural rent overtakes metro rent by tick ~35–40, rural gross yield 8% → 18.8% (3 seeds), no test gates it | 0, B |
| 2 | No scarcity→price channel on the sale side: price = ask × noise; `overbid_sigma` (a guess) is the price-level parameter and explains 56% of price-to-income variance | D |
| 3 | Rental yield is an input, not an output: `required_rent = V(bond+spread)/12` pins gross yield at the observed ladder | B |
| 4 | Inheritance leaks ownership: heir keeps SEEKER status while owning a vacated dwelling; ownership drifts 77.2% → 69.5% | A |
| 5 | Two cash buyers (foreign overlay, large investor) bid against the index they help set — positive feedback with no nominal anchor | B |
| 6 | `own_vs_rent` user-cost channel is inert (clipped to 1.0 below a ~6.2% mortgage rate) while its comment claims it carries the rate shock | A |
| 7 | No insolvency or forced sale: `wealth = max(0, wealth − payment)` absorbs non-payment | C |
| 8 | Validation is largely in-sample: `location_premium` was screened against the §9 gates; two target rows are config identities | 0, E |
| 9 | Cap exit hazard has a permanent floor by construction (`growth_wedge` from two exogenous constants) | A, B |
| 10 | Headline cap result rides on guessed constants (`EXIT_SPLIT`, magnet ×1.05, `HAZARD_SCALE`) | A, B |
| 11 | **Internal migration has the wrong sign**: only metro→rural (`engine.py:417`); Spain's net internal flow runs rural→metro | B |

Finding 11 was not in the original critique and is more damaging than several that were.

## 3. The discipline (applies to every phase)

### 3.1 Derived-or-reduced-form rule

> Every behavioural rule is either **derived** from a declared primitive — a household
> optimising something, an arbitrage condition, an accounting constraint — or explicitly
> labelled **reduced form**, with the episode that identifies it and the range the evidence
> admits. There is no third category.

The rules that currently fail this test, and must be rewritten or relabelled. This spec named
nine; the phase-0 assumption register found eleven more when the same criterion — `assumed`,
and either naming no identifying episode or no admitted range (both are required to pass) —
was applied row by row. **Twenty:**

`PARTICIPATION_GROWTH_SENSITIVITY=15` · `PARTICIPATION_RATE_SENSITIVITY=20` ·
`MOMENTUM_GAIN=5` · `CONGESTION_GAIN=0.05` · cap magnet `×1.05` ·
`can_buy ≥ 0.6 × median_price` · `EXIT_SPLIT 0.5/0.35/0.15` · `HAZARD_SCALE=0.7` ·
inventory markdown `0.02/tick` · `NET_INCOME_FACTOR=0.78` · `buy_attempt_prob=0.50` ·
`max_listing_ticks=6` · frictionless assortative rental matching · search tolerance
`ask ≤ budget × 1.05` · `EXIT_SPLIT_EVASION_BASE=0.15` · investor accumulation band `×1.15` ·
`PRIME_HURDLE_SPREAD=0.015` · `EXIT_LIST_SHARE=0.05` · `MAX_BUYS_PER_TICK=4` · pace leg of
`SEARCH_BURDEN_ESCALATION=0.04`

`ask_decay=0.03` was audited at the same time and **passes**: it names an episode (sticky asks
2008–13) and a range (.02–.05). The count covers rules to be rewritten or relabelled; rows
already scheduled for wholesale replacement in phases A–D would also fail read literally, and
are tracked by their phase (`docs/assumptions.md`).

### 3.2 Variance rule

> No quantity is reported as a **magnitude** if an unsourced parameter explains more than 25%
> of its variance in the Sobol decomposition. Direction-only reporting is still allowed.

Applied to today's model this immediately disqualifies, as magnitudes: `price_to_income`
(`overbid_sigma` 56%), `rent_overburden_share` and the rent level
(`landlord_required_spread` 65% / 40%), and tensioned market vacancy (74%). The rule turns the
existing Sobol finding into project policy and fixes the evidence-work priority order without
argument.

### 3.3 Assumption register

`docs/assumptions.md`: one row per assumption, with status (`measured` / `derived` / `assumed`),
sources, where it enters the code, how much it moves results (Sobol), and what observation
would falsify it. Test of adequacy: any critic's objection either maps to a row — which already
answers or concedes it — or reveals a missing row.

### 3.4 Declared exogenous boundary

What is outside the model by construction (macro feedback, employment path, rates, geography
below the zone, meteorites) becomes a contract clause rather than a §10 footnote. Being outside
is not a defect; leaving it unsaid would be.

### 3.5 Falsification conditions

Every mechanism declares the observation that would kill it. A mechanism that cannot fail is
not saying anything.

### 3.6 Pre-registration

Before running a lever: a file with commit hash, seed, config hash and the theory-predicted
direction, committed to git. Then the run. Ordering is visible in history, so "you tuned it
until it said what you wanted" is not available as an objection.

### 3.7 Adversarial referee pass

Each phase closes with an explicit "what would a hostile economist object to" pass, with every
objection answered **or conceded in writing**. `validation.md`'s "Honest qualifications" already
does this well; it becomes procedure rather than goodwill.

## 4. Calibration protocol

1. **Fixed temporal split**: calibrate on 2014–2025 moments only. **2008–2013 is sealed.** The
   bust's input files arrive in phase C; no parameter is touched after it is first run.
2. **Nothing measured is fitted.** A parameter with a direct measurement (LTV, terms, operating
   cost share, statutory foreclosure lag, park size, IRAV) is data, not a degree of freedom.
3. **Fitting order**: LHS over free parameters → Morris screening → Sobol on survivors →
   variance rule applied → *then* the hold-out is run **once** and reported, pass or fail.
   A failure is reported as a failure. Re-fitting against the bust would destroy it as evidence
   and is the one irreparable objection available against this project.
4. **Compute** cached to `runs/` with seed + config hash (existing convention), plus the
   pre-registration file.
5. **Seeds**: nothing is reported on fewer than 10 seeds after phase E. Two tests are already
   documented as having passed on seed luck.

## 5. Phases

Short kebab-case branch per phase. Every merge leaves the suite green or carrying dated,
strict xfails naming the mechanism that broke the target. No scenario result is reported
between phase B and phase E.

| Phase | Branch | Content | Closes |
|---|---|---|---|
| 0 | `precision-contract` | Precision contract in `model-spec.md §9`; `docs/assumptions.md`; 7 new targets in `test_validation.py` (several born red); seal 2008–13 | 8 (partly), 1 (visible) |
| A | `model-bug-fixes` | Inheritance; dead user-cost term; config-identity rows out of the target table; `growth_wedge` and `EXIT_SPLIT` to `config.py` with ranges | 4, 6, 9, 10 |
| B | `profitability-block` | Total-return hurdle; buy-to-let entry; investor and foreign anchors; bidirectional migration | 1, 3, 5, 9, 10, 11 |
| C | `insolvency` | Income risk; arrears; statutory foreclosure; bank REO; `CreditCrunch` lever | 7 |
| D | `price-formation` | Ascending auction; m-listing search; seller reservation from mortgage | 2 |
| E | `recalibration` | LHS + Morris + Sobol on 2014–25 only; variance rule; then the 2008–13 hold-out, once | 8 |
| F | `claims-ledger` | `docs/claims.md`: public claims vs model, with ranges and the parameter each claim requires | the project's purpose |

Non-negotiable ordering: C before E (without forced sale the bust hold-out cannot be run) and
D before E (recalibrating twice wastes the compute).

## 6. New validation targets (phase 0)

Seven observable moments the model could already be failing silently. Several are red on
arrival — that is the point.

| Target | Data | Why it is possible only now |
|---|---|---|
| Zone gross-yield ladder, emergent | idealista/BdE 4.7–5.6 / 6.5–7.5 / 7–9 | today an input; with §7.1 an output. Catches the 18.8% rural |
| Yield compression 2014–25 | idealista gross yield series | impossible to generate today; it is the signature of the new hurdle |
| Rent level ordering T > S > R | idealista / SERPAVI | no gate exists; this is finding 1 |
| Time to sell, in ticks | idealista days on market, converted to quarters | identifies the phase-D auction without touching price |
| Foreclosure flow | CGPJ | validates phase C; impossible without it |
| Households owning a second dwelling / landlord count | EFF2024; AEAT IRPF | validates buy-to-let entry |
| Net internal migration by zone type | INE Migraciones y Variaciones Residenciales | the model's sign is currently inverted |

## 7. Mechanism specifications

### 7.1 Landlord reservation rent — arbitrage condition

A let dwelling is an asset. The landlord holds it while expected total return covers the
opportunity cost of the capital:

```
total return      =  net rent yield + expected capital gain
hold if              12·r·(1−c)/V  +  E[g]  ≥  i_bond + π
reservation rent:    r_req = V·(i_bond + π − E[g]) / (12·(1−c))
```

- `c` — operating costs as a share of gross rent (IBI, comunidad, insurance, maintenance,
  management, vacancy loss).
- `π` — residential risk premium (illiquidity, default, management), with a zone gradient.
- `E[g]` — expected capital gain, from the existing §6 expectations, entered with partial
  extrapolation weight `λ_L < 1`.

**This rule nests the current one.** Today's `r = V(bond + spread)/12` is this expression with
`E[g] = 0` and `c = 0`. The redesign restores two missing terms rather than inventing a
mechanism — a materially harder thing to attack.

Consequences:

- `ZoneConfig.gross_yield` becomes an initial condition only. The yield ladder becomes a
  **contrastable prediction** instead of a parameter the model cannot fail.
- Yields **compress** in a boom (`E[g]` up ⇒ required rent yield down), which is the observed
  Spanish 2014–25 pattern and is currently impossible to generate.
- The zone yield ladder is explained economically: low metro yields follow from high `E[g]`
  and low `π`, not from config.
- The mechanical 1:1 price→rent link of finding 3 is broken.

Guards, declared as such:

- If `E[g] > i_bond + π` the reservation rent goes negative — the landlord holds for capital
  gain alone. That is a bubble and it does happen, but it must be bounded: partial
  extrapolation `λ_L` plus an absolute floor at the lowest gross yield observed in Spain
  (prime Madrid/Barcelona, ≈3.0–3.5%, **to verify**).

**Falsification**: if observed gross yields do *not* fall when expected appreciation rises —
idealista yield against IPV growth 2014–25, and in provincial cross-section — the rule is
false.

The compression target is stated as two tests, so it cannot be passed vacuously: the sign of
the within-zone correlation between gross yield and expected appreciation must be negative, and
the national gross yield must fall over the 2014–25 boom by an amount inside the observed range
(to be fixed from the idealista series in phase 0).

### 7.2 The same condition replaces the cap dial

A landlord under a cap exits when total return *with the cap* falls below the hurdle. This
derives the cap's supply response from the same primitive and removes `HAZARD_SCALE` and the
`growth_wedge` hazard floor (findings 9, 10).

**Decision taken**: the disputed rental-supply elasticity (0–2) stops being an input dial and
becomes an **emergent prediction**, compared against Jofre-Monseny / Monràs / Pérez García.
Dispersion still exists, but it comes from measured uncertainty in the primitives (`π`, `c`,
compliance, coverage, evasion) rather than from a free parameter. Target 8 changes meaning: the
model now predicts the elasticity instead of being told it, and if it lands outside all three
studies that is a visible failure with no dial to hide it.

### 7.3 Buy-to-let entry — closing the one-way asymmetry

Today rental supply can only shrink: `clearing.settle` always sets `OWNER_OCCUPIED` for
household buyers, and `investor.py:40` skips rural entirely (`large_investor_share = 0.0`).
An 18.8% gross yield attracts no capital — indefensible under any framing.

Rule, same primitive. An **already-owner** household invests in a second dwelling to let when

```
12·r·(1−c)/V + E[g]  ≥  i_alt + π_household
```

subject to the bank's second-home screen (lower LTV, rental income counted partially — bank
practice, BdE). `π_household` is heterogeneous (risk aversion); its distribution is the free
element.

Disciplined by four independent anchors: EFF2024 (households owning other real estate, with a
wealth-percentile gradient), AEAT IRPF (taxpayers declaring rental income), and the two
existing targets (individuals hold 85–92% of rental stock; `small_landlord_share`).

This also gives the rent cap the **entry margin** it currently lacks. The three empirical
studies measure contract *flow*, which is entry minus exit; measuring only exits biases the
elasticity by construction.

### 7.4 Cash-buyer anchors (finding 5)

- **Large investor**: `max_bid = expected net rent / y_req(zone)` — it capitalises rents at its
  own hurdle, and stops buying (then sells) when prices exceed that. Replaces
  `price_index × U(0.95, 1.05)`.
- **Foreign overlay**: budget anchored to an **exogenous** path (origin-country income/wealth
  index × the observed €/m² premium, 3,063 vs 1,713), and an exogenous arrival stream with its
  own cycle instead of one proportional to recent Spanish sales.
  **Falsification**: if Registradores' non-resident purchase series tracks Spanish transaction
  volume one-for-one (2007–2025), the exogenous treatment is wrong.

### 7.5 Bidirectional migration, and the fate of the location premium

Today: metro→rural only, triggered by rent burden, 10%/tick, labelled guess. Spain's net
internal flow runs the other way. New rule: gross flows in both directions from a zone
comparison (expected income × amenity − housing cost) with a friction, identified against INE
Migraciones y Variaciones Residenciales — including the 2020–22 reversal, which is a clean
natural test — and the wage gradient (De la Roca & Puga 2017).

Consequence, and the best news in phase B: with amenity inside the location decision, the
`location_premium` (0.85 / 0.45), today calibrated by screening against the very §9 gates it is
then said to pass, is either **derived from the migration indifference condition** or dropped.
It stops being a free multiplier.

### 7.6 Insolvency and forced sale (phase C)

`_household_flows` currently does `wealth = max(0, wealth − mortgage_payment)`: the budget
constraint does not bind.

Dependency discovered while deriving: there is **no income risk** — every household grows at
exactly 2%/yr, so there is no default to model. Phase C therefore needs, in order:

1. **Employment status with stochastic incidence on an exogenous unemployment path.**
   Unemployment is exogenous (declared boundary, like euríbor); who it hits is endogenous.
   Sources: EPA rate and flows, zone gradient.
2. **Arrears**: payment + essential consumption > disposable income with the buffer exhausted ⇒
   arrears counter. Anchor: BdE non-performing housing-credit series (peak ≈6% in 2014,
   **to verify**).
3. **Foreclosure with a statutory, not guessed, lag.** Ley 5/2019 art. 24 (12 unpaid monthly
   instalments or 3% of principal in the second half of the loan), earlier RDL 6/2012 and
   Ley 1/2013 with the Código de Buenas Prácticas; procedure duration from CGPJ statistics.
   **The lag comes from the law** — the best-identified mechanism in the model.
4. **Outcome**: bank adjudication or dación en pago. The bank holds REO stock and releases it
   at a markdown (BdE adjudicated-asset haircuts, Sareb disposal discounts). This reproduces
   the bank-owned overhang, a real 2008–13 channel that does not exist today. The household
   becomes a SEEKER with a temporary credit lockout.
5. **`CreditCrunch` lever** (tighten LTV / DSTI / spread) as the hold-out's input, already
   listed in `validation.md` as the natural next lever.

**Falsification**: with 2008–13 inputs the foreclosure flow must reach the order of the CGPJ
series at its peak. If it cannot, the mechanism is false.

### 7.7 Sale-side price formation (phase D)

**Ascending auction.** Price = `min(second-highest budget + increment, highest budget)`, subject
to reserve. Competition enters through the bidder count, which comes from demand and supply.
`overbid_sigma` is demoted to idiosyncratic taste dispersion — a real friction — and stops
setting the price level. The variance rule then requires Sobol to put it below 25%, or the price
level is not reportable as a magnitude.

**Search over m listings** instead of one at random, so bid concentration is endogenous: today
bidding wars exist because buyers do not look. `m` is declared reduced form, identified against
two currently unused observables: the days-on-market distribution and the distribution of
discounts against asking price.

**Seller reservation from the mortgage.** Today `reserve = ask × U(0.05, 0.15)`, a guess.
Derived: the owner's reservation is the maximum of use value (the user cost of staying) and
**outstanding debt**. A household in negative equity cannot sell below the principal.

This produces, from accounting rather than from a fitted coefficient, the seller lock-in that
`validation.md` records as deliberately not fixed (moving-trigger split unresolved, insufficient
sources to invent an elasticity). No elasticity needs inventing: it follows from the LTV
distribution, which is BdE data. It is also the missing mechanism behind "volume adjusts first,
prices are sticky" — today carried by the hand-fitted `PARTICIPATION_RATE_SENSITIVITY` — and it
closes the magnitude gap in target 6b (−1.9% against an observed +4.0%).

Two ad-hoc rules die here: the participation rate sensitivity — one of the twenty rules §3.1
counts as failing the derived-or-reduced-form rule — and the seller reserve, which was never
in that count; it sits in the phase A–D replacement group `docs/assumptions.md` excludes from
the count rather than in §3.1's list.

## 8. What breaks

Phase B and D will break most of the current gates: 1, 2, 2c, 2d, 3, 5, 5b, 7, 7r, 8 and the
stock-share rows. They enter as dated strict xfails naming the mechanism that broke them. No
scenario result is reported between phase B and phase E.

Tests that must accompany the mechanisms:

- **Nesting**: the new reservation rent collapses to the current one at `E[g] = 0`, `c = 0`.
- **Monotonicity**: reservation rent falls in `E[g]`, rises in `π` and `i_bond`.
- **Sign test**: gross yield compresses when expected appreciation rises.
- **Ladder tests**: zone gross yields in band; rent level ordering T > S > R.
- **Count tests**: landlord counts against EFF and AEAT anchors.
- **Statutory test**: no foreclosure before the legal arrears threshold.
- **Reproducibility**: the existing cross-process seed test keeps passing.

## 9. Sources to verify before coding

Every figure quoted in this spec from memory is marked **to verify**; each becomes a row in
`docs/sources.md` with the retrieval date before the mechanism that uses it is coded. The
project rule (≥2 independent sources per behavioural rule) applies to each mechanism in §7, not
to the spec as a whole.

Priority retrieval list:

- idealista gross/net rental yield series by province, 2014–2026 (§7.1, §7.3, targets).
- BdE RBA: gross vs net yield, operating cost share, zone risk gradient (§7.1).
- CBRE / Savills prime residential yield vs sovereign spread (§7.1 `π`).
- EFF2024 microdata: households owning other real estate by wealth percentile (§7.3).
- AEAT IRPF: taxpayers declaring rental income (§7.3).
- INE Migraciones y Variaciones Residenciales: net flows by municipality size, 2015–2025,
  including the 2020–22 reversal (§7.5).
- CGPJ: mortgage foreclosures initiated, quarterly, 2007–2026 (§7.6).
- BdE: non-performing housing credit; adjudicated-asset haircuts; LTV distribution (§7.6, §7.7).
- BOE: Ley 5/2019 art. 24, Ley 1/2013, RDL 6/2012 (§7.6).
- idealista: days on market and discount-against-ask distributions (§7.7).
- Registradores: non-resident purchases, quarterly series 2007–2026 (§7.4).

## 10. What this model may not be used for

- Point forecasts of prices, rents or volumes at a date.
- Cross-zone ratios as quantities (ordering and direction only) until §7.5 lands and the
  location premium is either derived or dropped.
- Any magnitude that fails the variance rule of §3.2.
- Any scenario result produced between phase B and phase E.
- Rent *levels* compared against published Spanish figures while every tenant rents one whole
  90 m² dwelling (`model-spec.md §10`); changes in them remain comparable.
