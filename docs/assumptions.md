# Assumption register

Every assumption the model makes, in one table, so that an objection either maps to a row —
which already answers or concedes it — or reveals a row that is missing. Companion to
`docs/sources.md` (which registers evidence) and `docs/validation.md` (which registers fit).

Status has exactly three values, per the derived-or-reduced-form rule
(`model-spec.md §13`):

- **measured** — set directly from a Tier-1 observation. Not a degree of freedom; never fitted.
- **derived** — follows from a declared primitive (an optimisation, an arbitrage condition, an
  accounting constraint). Its parameters may be measured or assumed, but its *form* is not free.
- **assumed** — reduced form. Must name the episode that identifies it and the range the
  evidence admits. An assumed rule that names no identifying episode is a defect.

`Sobol share` is the fraction of a reported quantity's variance the row explains, from
`docs/validation.md` "Sensitivity analysis". Empty means not yet measured. Under the variance
rule (`model-spec.md §13`), any reported magnitude with an **assumed** row above 25% is
downgraded to direction-only until the row is sourced.

## Behavioural rules

| Assumption | Status | Where | Source | Sobol share | Falsified by |
|---|---|---|---|---|---|
| Credit screening binds before preference: ability-to-pay clips every financed bid | derived | `engine._credit_screen`, `agents/bank.max_price` | bank §3; BdE IEF | — | Volume responding to rates *after* prices rather than before |
| Buyer participation rises with expected growth above the long-run anchor | assumed | `agents/household.PARTICIPATION_GROWTH_SENSITIVITY = 15` | identified on the 2024–25 easing surge (sales +10.7%, 17-year high) [household-owner §4] | — | A boom with flat transaction volume |
| Buyer participation falls with the offered rate above a comfort threshold | assumed | `agents/household.PARTICIPATION_RATE_SENSITIVITY = 20`, `RATE_COMFORT_THRESHOLD = 0.035` | identified on 2022–23 (+2.4pp rates, transactions −11%, MIVAU) | — | A rate shock that cuts prices before volumes |
| Willingness-to-pay is shaded by expected growth, capped ±10% | assumed | `agents/household.MOMENTUM_GAIN = 5`, `MOMENTUM_CAP = 0.10` | household-owner §6 price-expectation rule | — | Bids insensitive to expectations in a boom |
| Owning-vs-renting user cost scales the budget | derived, **inert** | `agents/household.py:132-137` | Poterba user cost | — | Already failing: `clip(gross_yield/user_cost, 0.5, 1.0)` returns 1.0 below a ≈6.2% mortgage rate, so the term does nothing in baseline. Phase A removes or rewrites it |
| Entry needs a budget above the cheapest habitable segment | assumed | `agents/household.py can_buy = budget >= 0.6 * median_price` | none — pure guess | — | Any measured entry threshold. Phase D derives it from the bank screen |
| Search is frictional: buyers bid on one listing drawn at random from those they can afford | assumed | `market/clearing.clear_sales` | model-spec §5 (mechanism); no source for the sample size | — | Observed viewings-per-purchase inconsistent with a sample of one. Phase D replaces it with m-listing sampling |
| Sale price = highest bid, bids scattered around the ask | assumed | `market/clearing.clear_sales`, `MarketConfig.overbid_sigma = 0.04` | none — calibrated | 56% of price-to-income | Sale-to-ask distribution inconsistent with the model's. Phase D replaces it with an ascending auction |
| Seller reserve is a uniform discount on the ask | assumed | `MarketConfig.max_seller_discount_lo/hi` | none — guess | — | Sellers in negative equity transacting below principal. Phase D derives the reserve from outstanding debt |
| Rent is accepted up to a household-specific share of income | measured | `PopulationConfig.max_rent_burden_lo/hi = 0.30/0.40` | household-tenant §6 screening norm | — | A screening norm outside 30–40% |
| A searching household's accepted burden escalates with the spell, capped at 0.55 | derived (mechanism), assumed (pace) | `agents/household.SEARCH_BURDEN_ESCALATION = 0.04`, `MAX_RENT_BURDEN_CEILING = 0.55` | mechanism and ceiling: EPF/Funcas 104 ch.6, Eurostat via ch.2; pace: guess, range 0.02–0.06 | — | Rent effort flat while rents outrun incomes |
| Landlord reservation rent = value × (bond + spread) / 12 | assumed | `agents/landlord.required_rent`, `MarketConfig.landlord_required_spread = 0.02` | investor-small §6 (spread bond+3–5pp) | 65% of overburden, 74% of tensioned market vacancy, 40% of rent level | **Already failing**: it pins gross yield at the observed ladder, so the ladder cannot be a prediction and yields cannot compress. Phase B replaces it with a total-return condition |
| Queue congestion pushes asking rents up | assumed | `agents/landlord.CONGESTION_GAIN = 0.05` | mechanism: Barcelona ≈65 contacts per listing [rent-cap §3]; level: guess | — | Asking rents insensitive to applicants per listing |
| Below-cap asks drift up toward the reference index | assumed | `agents/landlord.py ask * 1.05` | Monràs magnet effect [rent-cap §2] (direction only) | — | No upward drift of below-reference rents under a cap |
| Cap-induced withdrawal hazard is linear in the log rent gap | assumed | `agents/landlord.HAZARD_SCALE = 0.7`, `growth_wedge` | calibrated to Monràs & García-Montalvo's contract elasticity | — | **Already suspect**: the wedge floor (4 × 0.005 − 0.015) makes the hazard permanent even with no level gap, so cap results depend on the 16-tick reporting window. Phase B derives exits from the hurdle |
| Withdrawing landlords split sale / seasonal / vacant 0.5 / 0.35 / 0.15 | assumed | `agents/landlord.EXIT_SPLIT` | none — open question [investor-small §7.1] | — | Any measured destination split of withdrawn rentals |
| Starts follow price over hard cost at the sourced elasticity | derived | `agents/developer.decide` | Caldera & Johansson; BdE; land as residual claimant [CNMC] | — | d ln(starts)/d ln(price) outside 0.45–0.58 in data |
| Unsold new-build inventory is marked down with holding time | assumed | `agents/developer.INVENTORY_MARKDOWN_PER_TICK = 0.02`, cap 0.25 | mechanism: developer §4; pace: guess | — | Completed unsold stock held at list price indefinitely |
| Priced-out seekers migrate one step down the zone ladder | assumed | `engine._demography` | none — guess | — | **Already failing**: Spain's net internal flow runs rural→metro; the model has only metro→rural. Phase B replaces it with bidirectional flows identified on INE Migraciones |
| The whole estate passes to one surviving household on dissolution | assumed | `engine._demography` | mechanism: avoids orphaned landlord stock | — | **Already failing**: the heir keeps SEEKER status while owning the vacated dwelling, so ownership leaks 77.2% → 69.5% over 60 ticks. Phase A fixes it |
| Non-resident buyers bid a premium on the domestic index | assumed | `engine._collect_intents`, `PopulationConfig.foreign_budget_multiplier = 1.6` | premium level: Registradores/Notariado (€3,063 vs €1,713 per m²) | — | **Already suspect**: the budget is anchored to the index it helps set, and arrivals are proportional to Spanish sales. Phase B anchors both exogenously |
| The large investor bids at the index | assumed | `agents/investor.decide` | none | — | Same anchoring defect. Phase B has it capitalise rents at its own hurdle |
| Households never default: insolvency is absorbed | assumed | `engine._household_flows` (`wealth = max(0, wealth − payment)`) | none — the budget constraint does not bind | — | **Already failing**: any foreclosure series. Phase C adds arrears, statutory foreclosure and bank REO |
| Household income grows at the nominal anchor, identically for all | assumed | `engine._household_flows` | exogenous 2%/yr anchor | — | Any measured idiosyncratic income risk. Phase C adds employment status |

## Structural / measurement assumptions

| Assumption | Status | Where | Source | Sobol share | Falsified by |
|---|---|---|---|---|---|
| One tick = one quarter; 1:2,000 representative scaling | measured | `config.py`, `metrics.SCALE` | IPV/INE/MIVAU frequency; INE ECP 19,874,860 households | — | — |
| Three zone types stand in for Spanish geography | assumed | `config.ZoneType` | project scope decision | — | Within-zone heterogeneity dominating between-zone (would require abandoning the abstraction) |
| Zone income multipliers 1.15 / 1.0 / 0.80 | assumed | `ZoneConfig.income_multiplier` | guess; corroborated by De la Roca & Puga (2017) elasticity 0.0455 | — | Measured zone income ratios outside the ladder |
| Location premium 1.00 / 0.85 / 0.45 on purchase willingness | assumed | `ZoneConfig.location_premium` | direction sourced (Tinsa price gradient); **level calibrated by screening against the §9 gates** | — | It is not independent evidence: it was fitted to the targets it is said to pass. Phase B derives it from the migration indifference condition or drops it |
| Quality is a scalar tier; every tenant rents one 90 m² dwelling | assumed | `StockConfig.avg_size_m2`, `Unit.quality` | model-spec §10 | — | Already conceded: rent levels read ≈2.6× the EPF average actually paid |
| Price index is a quality-adjusted transaction median; rent index is an asking median | measured (basis) | `engine._update_indices` | IPV-like; idealista-like | — | — |
| Public rents are excluded from all market rent series | derived | `engine._update_indices`, `metrics.snapshot` | administered prices are not market signals | — | — |
| Vacancy ladder rural > secondary > tensioned | measured | `ZoneConfig.units_per_household`, `withheld_share` | INE Censo 2021 via Funcas 104 ch.1 | — | A measured ladder in the other direction |

## Exogenous boundary

Outside the model by construction. Being outside is not a defect; leaving it unsaid would be.

| Outside | Consequence | Where |
|---|---|---|
| Macro feedback (housing → GDP → housing) | 2008 amplification understated | no channel exists |
| Employment and income paths | no endogenous income risk until phase C | `_household_flows` |
| Euríbor and the bond yield | rate shocks are inputs, never outcomes | `CreditConfig`, `Macro` |
| Foreign origin-country conditions | the non-resident stream is a scenario input | `engine._collect_intents` |
| Geography below the zone; commuting | no city, district or job-access structure | `ZoneType` |
| Construction input costs | hard cost is a config path, not a market | `ZoneConfig.cost_per_m2` |
| Landlord income taxation, utilities, second-home demand from other provinces | known gaps | `docs/validation.md` "Known gaps" |
| Unmodellable shocks (pandemic, war, meteorite) | not a modelling error; not in scope | — |
