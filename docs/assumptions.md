# Assumption register

Every assumption the model makes, in one table, so that an objection either maps to a row —
which already answers or concedes it — or reveals a row that is missing. Companion to
`docs/sources.md` (which registers evidence) and `docs/validation.md` (which registers fit).

Status is built from three values, per the derived-or-reduced-form rule
(`model-spec.md §13`):

- **measured** — set directly from a Tier-1 observation. Not a degree of freedom; never fitted.
- **derived** — follows from a declared primitive (an optimisation, an arbitrage condition, an
  accounting constraint). Its parameters may be measured or assumed, but its *form* is not free.
- **assumed** — reduced form. Must name the episode that identifies it and the range the
  evidence admits. An assumed rule that names no identifying episode is a defect.

Some rows carry a **compound** status — for instance "derived, **inert**", "derived
(mechanism), assumed (pace)", "derived (ordering), assumed (frictionless)", "measured (basis)",
or "derived (arbitrage form), assumed (hurdle level and band)". The list is illustrative, not
exhaustive. That is not sloppiness and it is not flattened here: a rule whose *form* follows
from a primitive while its *level* or *pace* is a guess sits in a different position from one
that is guessed end to end, and collapsing the two to a single word would hide exactly the
distinction the derived-or-reduced-form rule exists to draw. Where a status is compound, the
parentheses name which leg is which, and the **assumed** leg is the one the rule is tested
against.

**Which rules fail the derived-or-reduced-form rule.** A row fails when it is `assumed` — in
whole, or in one leg of a compound status — and it either names no episode that identifies it,
or names no range the evidence admits: both are required to pass, so missing either one fails
it. The design spec named nine (`§3.1`). The phase-0 additions below add **eleven** more:
`NET_INCOME_FACTOR`, `buy_attempt_prob`, `max_listing_ticks`, the frictionless leg of
assortative rental matching, the 5% over-budget search tolerance, `EXIT_SPLIT_EVASION_BASE`,
the investor's ×1.15 accumulation band, `PRIME_HURDLE_SPREAD`, `EXIT_LIST_SHARE`,
`MAX_BUYS_PER_TICK` and the pace leg of search-burden escalation (`SEARCH_BURDEN_ESCALATION`
below: it names a range, 0.02–0.06, but no identifying episode) — **twenty** in total.
`ask_decay` is the one addition that passes: it names both an episode (sticky asks 2008–13)
and a range (.02–.05).

Scope of that count, stated so it can be checked rather than trusted: it is the set of rules to
be **rewritten or relabelled**. Several pre-existing rows already scheduled for wholesale
*replacement* in phases A–D — `overbid_sigma`, the seller reserve, one-listing search,
downward-only migration, the investor's index anchor, absorbed insolvency — would also fail the
test read literally, and are tracked by their phase rather than by this list. A row-by-row
recount on that wider reading is an open item for phase E.

`Sobol share` is the fraction of a reported quantity's variance the row explains, from
`docs/validation.md` "Sensitivity analysis". Empty means not yet measured. Under the variance
rule (`model-spec.md §13`), any reported magnitude with an **assumed** row above 25% is
downgraded to direction-only until the row is sourced.

## Behavioural rules

| Assumption | Status | Where | Source | Sobol share | Falsified by |
|---|---|---|---|---|---|
| Credit screening binds before preference: ability-to-pay clips every financed bid | derived | `engine._credit_screen`, `agents/bank.max_price` | bank §3; BdE IEF | — | Volume responding to rates *after* prices rather than before |
| Net household income is a flat 0.78 of gross, for every household | assumed | `agents/bank.NET_INCOME_FACTOR = 0.78`, entering `max_principal` and so `max_price` | none — guess, and the module docstring says so. Spain's IRPF + SS wedge is progressive, so a flat factor overstates net income at the top of the distribution and understates it at the bottom | — | Any measured net/gross distribution for Spanish mortgage applicants. It scales the DSTI cap one-for-one, so it moves every financed household's borrowing capacity — an unsourced scalar inside the derived rule above |
| Buyer participation rises with expected growth above the long-run anchor | assumed | `agents/household.PARTICIPATION_GROWTH_SENSITIVITY = 15` | identified on the 2024–25 easing surge (sales +10.7%, 17-year high) [household-owner §4] | — | A boom with flat transaction volume |
| Buyer participation falls with the offered rate above a comfort threshold | assumed | `agents/household.PARTICIPATION_RATE_SENSITIVITY = 20`, `RATE_COMFORT_THRESHOLD = 0.035` | identified on 2022–23 (+2.4pp rates, transactions −11%, MIVAU) | — | A rate shock that cuts prices before volumes |
| Willingness-to-pay is shaded by expected growth, capped ±10% | assumed | `agents/household.MOMENTUM_GAIN = 5`, `MOMENTUM_CAP = 0.10` | household-owner §6 price-expectation rule | — | Bids insensitive to expectations in a boom |
| Half of constraint-passing tenants and seekers attempt a purchase each tick | assumed | `PopulationConfig.buy_attempt_prob = 0.50`, read in `agents/household.decide` | none — guess, calibrated; the credit screen is what does the rationing | — (Morris score 0.78, μ\* 0.80 on price-to-income; not among the Sobol seven) | Any measured search-participation rate for Spanish owner-occupiers. Named in `test_validation.test_transaction_volume` as the moment most sensitive for **gated** target 3, which runs near the top of its band |
| Owning-vs-renting user cost scales the budget | derived, **inert** | `agents/household.py:132-137` | Poterba user cost | — | Already failing: `clip(gross_yield/user_cost, 0.5, 1.0)` returns 1.0 below a ≈6.2% mortgage rate, so the term does nothing in baseline. Phase A removes or rewrites it |
| Entry needs a budget above the cheapest habitable segment | assumed | `agents/household.py can_buy = budget >= 0.6 * median_price` | none — pure guess | — | Any measured entry threshold. Phase D derives it from the bank screen |
| Search is frictional: buyers bid on one listing drawn at random from those they can afford | assumed | `market/clearing.clear_sales` | model-spec §5 (mechanism); no source for the sample size | — | Observed viewings-per-purchase inconsistent with a sample of one. Phase D replaces it with m-listing sampling |
| Buyers reach up to 5% over budget when choosing which listing to bid on | assumed | `market/clearing.clear_sales`, `lst.ask <= offer.budget * 1.05` | none — guess | — | Any measured ask-to-budget reach in viewing or offer data. The bid itself is still capped at `offer.budget`, so the tolerance widens the choice set rather than the price — it is what lets a constrained buyer engage with a listing it cannot in fact close at, and it decides how many buyers find no affordable listing at all |
| Rental matching is assortative and frictionless: applicants queue by willingness to pay, each taking the best listing it can afford | derived (ordering), assumed (frictionless) | `market/clearing.clear_rentals` | ordering: landlord screening favours solvency and housing is a normal good [household-tenant §6]; the absence of *any* search friction on the rental side: none — while the sale side above carries one | — | Rental allocations not sorted on tenant income or willingness to pay. The consequence is structural and already stated in the module docstring: the clearing rent equals the winning applicant's WTP, so the rent index can outrun income only through the *level* of accepted burden (the sharing margin). It is also why the insider/outsider wedge is measured on rent levels, not burdens (`metrics.snapshot`) |
| Sale price = highest bid, bids scattered around the ask | assumed | `market/clearing.clear_sales`, `MarketConfig.overbid_sigma = 0.04` | none — calibrated | 56% of price-to-income | Sale-to-ask distribution inconsistent with the model's. Phase D replaces it with an ascending auction |
| Seller reserve is a uniform discount on the ask | assumed | `MarketConfig.max_seller_discount_lo/hi` | none — guess | — | Sellers in negative equity transacting below principal. Phase D derives the reserve from outstanding debt |
| Unsold asks are cut a fixed 3% per tick | assumed | `MarketConfig.ask_decay = 0.03`, applied in `engine._apply_listings` | sticky-ask behaviour in the 2008–13 downturn (episode); range .02–.05 (evidence admitted) | — | Ask-revision hazards outside .02–.05. With `max_listing_ticks` this **is** the model's time-to-sale: the pair decides how long a listing survives before it clears or is withdrawn, so together they are the governing assumptions behind §9 target 13 |
| A listing is withdrawn after 6 ticks unsold | assumed | `MarketConfig.max_listing_ticks = 6`, applied in `engine._apply_listings` | none — guess. A range 4–8 is stated in the code; no episode identifies it | — | idealista days on market, once retrieved (§9 target 13). The other half of the model's time-to-sale, and a hard ceiling on it: `median_ticks_to_sale` cannot exceed this, so the target is bounded by the assumption before the mechanism gets a say |
| Rent is accepted up to a household-specific share of income | measured | `PopulationConfig.max_rent_burden_lo/hi = 0.30/0.40` | household-tenant §6 screening norm | — | A screening norm outside 30–40% |
| A searching household's accepted burden escalates with the spell, capped at 0.55 | derived (mechanism), assumed (pace) | `agents/household.SEARCH_BURDEN_ESCALATION = 0.04`, `MAX_RENT_BURDEN_CEILING = 0.55` | mechanism and ceiling: EPF/Funcas 104 ch.6, Eurostat via ch.2; pace: guess, range 0.02–0.06 | — | Rent effort flat while rents outrun incomes |
| Landlord reservation rent = value × (bond + spread) / 12 | assumed | `agents/landlord.required_rent`, `MarketConfig.landlord_required_spread = 0.02` | investor-small §6 (spread bond+3–5pp) | 65% of overburden, 74% of tensioned market vacancy, 40% of rent level | **Already failing**: it pins gross yield at the observed ladder, so the ladder cannot be a prediction and yields cannot compress. Phase B replaces it with a total-return condition |
| Queue congestion pushes asking rents up | assumed | `agents/landlord.CONGESTION_GAIN = 0.05` | mechanism: Barcelona ≈65 contacts per listing [rent-cap §3]; level: guess | — | Asking rents insensitive to applicants per listing |
| Below-cap asks drift up toward the reference index | assumed | `agents/landlord.py ask * 1.05` | Monràs magnet effect [rent-cap §2] (direction only) | — | No upward drift of below-reference rents under a cap |
| Cap-induced withdrawal hazard is linear in the log rent gap | assumed | `agents/landlord.HAZARD_SCALE = 0.7`, `growth_wedge` | calibrated to Monràs & García-Montalvo's contract elasticity | — | **Already suspect**: the wedge floor (4 × 0.005 − 0.015) makes the hazard permanent even with no level gap, so cap results depend on the 16-tick reporting window. Phase B derives exits from the hurdle |
| Withdrawing landlords split sale / seasonal / vacant 0.5 / 0.35 / 0.15 | assumed | `agents/landlord.EXIT_SPLIT` | none — open question [investor-small §7.1] | — | Any measured destination split of withdrawn rentals |
| The seasonal branch of that split is rescaled proportionally by seasonal evasion, against a 0.15 base | assumed | `agents/landlord.EXIT_SPLIT_EVASION_BASE = 0.15`, against `MarketConfig.seasonal_evasion_share` | Incasòl seasonal counts [medium] fix the base level at which `EXIT_SPLIT` was written; the *proportional* rescaling is a convention with no episode behind it | — | A measured, non-proportional relation between evasion and the destination of withdrawn rentals. The `EXIT_SPLIT` row above covers the split; it does **not** cover this rescaling, which is what makes the split move whenever `seasonal_evasion_share` is swept — including in every tourist-restriction scenario |
| Starts follow price over hard cost at the sourced elasticity | derived | `agents/developer.decide` | Caldera & Johansson; BdE; land as residual claimant [CNMC] | — | d ln(starts)/d ln(price) outside 0.45–0.58 in data |
| Unsold new-build inventory is marked down with holding time | assumed | `agents/developer.INVENTORY_MARKDOWN_PER_TICK = 0.02`, cap 0.25 | mechanism: developer §4; pace: guess | — | Completed unsold stock held at list price indefinitely |
| Priced-out seekers migrate one step down the zone ladder | assumed | `engine._demography` | none — guess | — | **Already failing**: Spain's net internal flow runs rural→metro; the model has only metro→rural. Phase B replaces it with bidirectional flows identified on INE Migraciones |
| The whole estate passes to one surviving household on dissolution | assumed | `engine._demography` | mechanism: avoids orphaned landlord stock | — | **Already failing**: the heir keeps SEEKER status while owning the vacated dwelling, so ownership leaks 77.2% → 69.5% over 60 ticks. Phase A fixes it |
| Non-resident buyers bid a premium on the domestic index | assumed | `engine._collect_intents`, `PopulationConfig.foreign_budget_multiplier = 1.6` | premium level: Registradores/Notariado (€3,063 vs €1,713 per m²) | — | **Already suspect**: the budget is anchored to the index it helps set, and arrivals are proportional to Spanish sales. Phase B anchors both exogenously |
| The large investor bids at the index | assumed | `agents/investor.decide` | none | — | Same anchoring defect. Phase B has it capitalise rents at its own hurdle |
| The large investor enters on gross yield above a hurdle and exits below it, with a 15% accumulation band | derived (arbitrage form), assumed (hurdle level and band) | `agents/investor.decide`: exit if `gross_yield < hurdle`, accumulate if `gross_yield > hurdle * 1.15` | form: yield-versus-bond arbitrage [investor-large §3]; the ×1.15 hysteresis band: none — guess | — | Institutional portfolio flows insensitive to the yield/bond gap, or a measured entry-exit hysteresis. The register described this agent only as "bids at the index"; the entry and exit **rule** is the part that decides whether it is in the market at all, and it compounds the anchoring defect in the row above — the yield it reads is the model's own index, which its own purchases help set |
| Required gross yield for the large investor = bond + 1.5pp | assumed | `agents/investor.PRIME_HURDLE_SPREAD = 0.015` | CBRE/Savills prime residential yield 3.8–4.0% against a ~3% bond [medium]. That is a level observation, not an episode identifying the *spread*, and no range is admitted for it | — | A measured prime-yield-to-sovereign spread outside ≈1–2pp. Phase B's total-return hurdle (spec §7.1) replaces the fixed spread with a risk premium π over the bond, at which point this row is superseded rather than re-fitted |
| An exiting large investor lists 5% of its reachable portfolio per tick | assumed | `agents/investor.EXIT_LIST_SHARE = 0.05` | "piso a piso" retail exits are documented [sources.md, institutional fund exits]; the *pace* is a guess | — | Any measured disposal schedule for a Spanish institutional landlord. It sets how fast a cap-driven or yield-driven institutional exit reaches the market, which is the channel every *grandes tenedores* policy claim runs through |
| The large investor makes at most 4 purchase offers per zone per tick | assumed | `agents/investor.MAX_BUYS_PER_TICK = 4` | none — guess, at model scale (1 offer ≈ 2,000 households' worth of market) | — | Measured institutional acquisition volumes. It is a hard cap on the investor's demand, so any claim about institutional buying pressure is bounded by this guess before the yield rule gets a say |
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
