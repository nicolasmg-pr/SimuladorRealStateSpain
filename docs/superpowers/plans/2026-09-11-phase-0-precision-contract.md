# Phase 0 — Precision Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the model's reporting rules, its assumption register and seven new observable
validation targets in place — several of them failing on arrival — before any mechanism is
touched.

**Architecture:** Phase 0 adds no behaviour. It adds measurement (five new metric columns and
two per-tick counters), the tests that judge them, and the documents that say what the model is
allowed to claim. Every target that fails becomes a dated strict xfail naming the mechanism
that will fix it, so the redesign's progress is visible in the suite rather than in prose.

**Tech Stack:** Python 3.14 (min 3.12), numpy, pandas, pytest, uv, ruff.

**Spec:** `docs/superpowers/specs/2026-09-11-model-redesign-design.md`

## Global Constraints

- Branch: `model-redesign` (already created and holds the spec commit). Work continues on it.
- `uv sync --dev` before anything runs. Tests: `uv run pytest`. Lint: `uv run ruff check . && uv run ruff format .`
- Indicators are defined once, in `src/resim/metrics.py`. The UI never computes a number inline.
- All randomness flows from the seeded Generator passed down from the engine. No module-level `random` or `np.random`.
- Agents are read-only on state: `decide()` returns intents; the engine and `market/clearing.py` are the only writers.
- Typed dataclasses for config, scenario, state and intents. No dicts as informal records — `tick_events` is the one sanctioned per-tick scratch dict.
- Every model decision is written in `docs/model-spec.md` before it is coded.
- Every figure quoted from an external source needs a row in `docs/sources.md` with a retrieval date. **No figure in this plan is treated as verified**: phase 0 asserts only sourced bands that already exist in `docs/sources.md` and `model-spec.md §7`, and registers the rest as `to verify`.
- Nothing is reported on fewer than 3 seeds; new gates follow the existing convention (3 seeds, last 20 of 60 ticks).
- Never commit secrets. `runs/` output is gitignored — never commit result artefacts.

---

## File Structure

**Created:**
- `docs/assumptions.md` — the assumption register: one row per assumption, with status, source, code site, Sobol share and falsification condition.
- `docs/holdout-2008-2013.md` — the sealed hold-out declaration: what the episode is, which inputs define it, and the rule that no parameter may be changed after it is first run.
- `docs/prereg/TEMPLATE.md` — pre-registration template for scenario runs.
- `tests/test_metrics.py` — mechanical correctness of the new metric columns, against hand-built states. Separate from `test_validation.py`, which judges the model against the world.

**Modified:**
- `src/resim/metrics.py` — five new columns: `gross_yield_<zone>`, `gross_yield_national`, `net_migration_<zone>`, `landlord_household_share`, `median_ticks_to_sale`.
- `src/resim/market/clearing.py` — `Trade` carries `ticks_listed`; `clear_sales` populates it.
- `src/resim/engine.py` — `_demography` records migration flows into `tick_events["migration"]`.
- `tests/test_validation.py` — four new targets (two strict xfails on arrival, one measured-then-decided, one reported-only), and three new fixture keys.
- `docs/model-spec.md` — new §13 reporting contract, new §14 exogenous boundary, §9 pointer, targets 9–15 added to the §9 list.
- `docs/validation.md` — seven new rows in the target table plus a phase-0 record of what each one measured.

---

### Task 1: Assumption register

**Files:**
- Create: `docs/assumptions.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `docs/assumptions.md` — the register later phases append rows to. Column order is fixed by this task: `Assumption | Status | Where | Source | Sobol share | Falsified by`.

Documentation task: no test cycle. It exists as its own task because later tasks cite row ids
from it.

- [ ] **Step 1: Write the register**

Create `docs/assumptions.md` with this content:

```markdown
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
| Priced-out seekers migrate one step down the zone ladder | assumed | `engine.py:417` | none — guess | — | **Already failing**: Spain's net internal flow runs rural→metro; the model has only metro→rural. Phase B replaces it with bidirectional flows identified on INE Migraciones |
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
```

- [ ] **Step 2: Lint the docs tree and commit**

```bash
cd "/Users/nikomendez/Documents/AI Engineering/Real Estate Simulator"
uv run ruff check .
git add docs/assumptions.md
git commit -m "docs: assumption register — every rule with status, source and falsifier

One row per assumption, with status measured/derived/assumed, the code site,
the Sobol share where measured and the observation that would falsify it.
Nine rules currently fail the derived-or-reduced-form rule and are named as
such; six rows are marked already-failing and carry the phase that fixes them."
```

---

### Task 2: Reporting contract, exogenous boundary, sealed hold-out, pre-registration

**Files:**
- Modify: `docs/model-spec.md` (new §13 and §14; one pointer line at the head of §9)
- Create: `docs/holdout-2008-2013.md`
- Create: `docs/prereg/TEMPLATE.md`

**Interfaces:**
- Consumes: `docs/assumptions.md` status vocabulary from Task 1.
- Produces: `model-spec.md §13` — the citable authority for the variance rule and the
  derived-or-reduced-form rule. Later tasks cite `§13` in test docstrings.

- [ ] **Step 1: Append §13 and §14 to `docs/model-spec.md`**

Append at the end of the file:

```markdown
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
```

- [ ] **Step 2: Add the pointer at the head of §9**

In `docs/model-spec.md`, find the line:

```
## 9. Validation (contract for Phase 6)
```

and insert immediately after it (before the existing "Baseline (no intervention…" paragraph):

```markdown
What may be *claimed* from a passing target is governed by the reporting contract (§13):
targets pass or fail here, but a passing target is not automatically a reportable magnitude.
```

- [ ] **Step 3: Create the sealed hold-out declaration**

Create `docs/holdout-2008-2013.md`:

```markdown
# Sealed hold-out: the 2008–2013 bust

**Status: sealed 2026-09-11. Not yet runnable — the mechanisms it needs land in phase C.**

## The rule

No parameter of this model may be changed after this episode has been run. The episode is
evidence about the specification, and re-fitting against it converts it into a fitting sample,
which is the one irreparable objection available against the project (`model-spec.md §13.4`).

Concretely:

- Calibration uses **2014–2025 moments only** (`docs/validation.md`).
- This file may gain inputs and sources. It may not gain *results* until phase E.
- When it is run, the result is recorded here once, pass or fail, with the commit hash and
  seeds. A failure is reported as a failure.

## What the episode is

Spain 2008–2013: the credit stop, the volume collapse, the slow price grind and the
foreclosure wave. The model must reproduce it from inputs alone, with no parameter fitted to
it.

## Inputs that define it (to retrieve — phase C)

| Input | Series | Status |
|---|---|---|
| Euríbor path 2008–2013 | ECB / BdE | to verify |
| Credit tightening (LTV, DSTI, spread) | BdE IEF, survey on bank lending standards | to verify |
| Household formation 2008–2013 | INE EPA / ECP | to verify |
| Completions delivered from the 2005–2008 pipeline | MIVAU / MITMA | to verify |
| Unemployment path | INE EPA | to verify |

## Targets it must reproduce (to fix from sources — phase C)

| Target | Empirical | Status |
|---|---|---|
| Mortgage lending collapse | −40…−85% | sourced in `model-spec.md §9.6` |
| Price decline, slow arrival | −30…−45% over ≥5 years | sourced in `model-spec.md §9.6` |
| Foreclosure flow at the peak | CGPJ mortgage foreclosures initiated | to verify |
| Bank-adjudicated stock overhang | BdE adjudicated assets; Sareb transfer | to verify |

## Why it is the right hold-out

It is the episode no parameter in the model has seen, and the only one that exercises the
mechanisms the model currently lacks: a binding budget constraint, forced sale, and negative
equity locking sellers in. Reproducing a boom the model was built during is a much weaker
claim.
```

- [ ] **Step 4: Create the pre-registration template**

Create `docs/prereg/TEMPLATE.md`:

```markdown
# Pre-registration: <scenario name>

Copy to `docs/prereg/YYYY-MM-DD-<scenario>.md`, fill in, **commit, then run**. The git history
is what makes the ordering verifiable (`model-spec.md §13.4`).

- **Date:**
- **Commit hash:** (`git rev-parse HEAD`)
- **Config hash:** (`resim.cli.config_hash`, printed by the CLI run)
- **Scenario / lever:**
- **Parameters swept, with ranges:**
- **Seeds:**
- **Ticks:**

## Predicted direction, before running

One line per reported quantity: the sign theory predicts and the mechanism that would produce
it. A quantity with no prediction here is a diagnostic, not a result.

| Quantity | Predicted sign | Mechanism |
|---|---|---|

## Reporting category claimed

Per `model-spec.md §13.1`: magnitude / direction / not reportable, per quantity. If claiming
magnitude, state the Sobol share of the largest `assumed` parameter.

## Result (filled in after the run)

- **Run artefacts:** `runs/<file>.csv`
- **Measured:**
- **Prediction held / failed:**
```

- [ ] **Step 5: Verify the spec's section numbering did not collide**

Run:

```bash
cd "/Users/nikomendez/Documents/AI Engineering/Real Estate Simulator"
grep -n "^## " docs/model-spec.md
```

Expected: sections 1 through 12 as before, then `## 13. Reporting contract` and
`## 14. Exogenous boundary`. No duplicate numbers.

- [ ] **Step 6: Commit**

```bash
git add docs/model-spec.md docs/holdout-2008-2013.md docs/prereg/TEMPLATE.md
git commit -m "docs: reporting contract, exogenous boundary, sealed 2008-13 hold-out

model-spec gains §13 (reporting categories, the 25% variance rule, the
derived-or-reduced-form rule, the calibration protocol, falsification and the
adversarial pass) and §14 (what is outside the model by construction).

The bust is sealed before it is runnable: calibration is restricted to
2014-25 moments and no parameter may change after the episode is first run.
Pre-registration template added so the ordering of predict-then-run is
visible in git rather than asserted."
```

---

### Task 3: Emergent gross-yield metric and the zone yield ladder target

**Files:**
- Modify: `src/resim/metrics.py` (per-zone loop, and the national block)
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: `ZoneState.rent_index`, `ZoneState.price_index`.
- Produces: frame columns `gross_yield_tensioned`, `gross_yield_secondary`, `gross_yield_rural`,
  `gross_yield_national`; fixture keys `gy_tensioned`, `gy_secondary`, `gy_rural`. Tasks 4 and 8
  read these.

- [ ] **Step 1: Write the failing test**

In `tests/test_validation.py`, add the three fixture keys inside the `baseline_moments`
dictionary literal, immediately after the `"pti_rural"` entry:

```python
                "gy_tensioned": tail["gross_yield_tensioned"].mean(),
                "gy_secondary": tail["gross_yield_secondary"].mean(),
                "gy_rural": tail["gross_yield_rural"].mean(),
```

Then add the test, after `test_zone_price_ladder_holds`:

```python
@pytest.mark.xfail(
    strict=True,
    reason="2026-09-11: rural gross yield runs to ≈18.8% against a sourced 7–9%. "
    "required_rent pins the yield floor to price, rural rental supply has no entry "
    "margin (investor skips rural, households never buy to let) and downward-only "
    "migration funnels every priced-out seeker into it. Fixed by the total-return "
    "hurdle and buy-to-let entry (spec §7.1, §7.3 — phase B).",
)
def test_zone_gross_yield_ladder(baseline_moments):
    """Target 9: the gross rental yield ladder must EMERGE, not be imposed.

    Sourced levels, idealista + BdE RBA [model-spec §7, investor-small §6]:
    tensioned 4.7–5.6%, secondary 6.5–7.5%, rural 7–9%. Bands widened by 0.5pp on each
    side for seed noise, the same tolerance convention as the other zone targets.

    This is a target only because §7.1 of the redesign makes the yield an output.
    `ZoneConfig.gross_yield` is an initial condition; what the model does with it afterwards
    is a prediction, and right now the prediction is wrong.
    """
    assert 0.042 <= baseline_moments["gy_tensioned"] <= 0.061
    assert 0.060 <= baseline_moments["gy_secondary"] <= 0.080
    assert 0.065 <= baseline_moments["gy_rural"] <= 0.095
```

- [ ] **Step 2: Run it to make sure it fails for the right reason**

```bash
cd "/Users/nikomendez/Documents/AI Engineering/Real Estate Simulator"
uv run pytest tests/test_validation.py::test_zone_gross_yield_ladder -v
```

Expected: `KeyError: 'gross_yield_tensioned'` — the column does not exist yet. A strict xfail
reports as `xfailed`, so read the captured error to confirm it is the KeyError and **not** a
band failure. Do not proceed until the failure is the missing column.

- [ ] **Step 3: Add the metric**

In `src/resim/metrics.py`, inside the `for zone in ZoneType:` loop, immediately after the line
`row[f"rent_transacted_{z}"] = zs.rent_transacted`, insert:

```python
        # gross rental yield, EMERGENT (model-spec §9 target 9). `ZoneConfig.gross_yield` is
        # an initial condition only; the ladder the model then produces is a prediction, and
        # the one observable that tells us whether the landlord's reservation rule is right.
        row[f"gross_yield_{z}"] = zs.rent_index * 12.0 / max(zs.price_index, 1.0)
```

And in the national block, immediately after `row["rent_national"] = ...`, insert:

```python
    row["gross_yield_national"] = row["rent_national"] * 12.0 / max(row["price_national"], 1.0)
```

- [ ] **Step 4: Run the test and confirm the failure is now a band failure**

```bash
uv run pytest tests/test_validation.py::test_zone_gross_yield_ladder -v -rx
```

Expected: `xfailed`, with the reported assertion being the rural band
(`assert 0.065 <= 0.18... <= 0.095` failing). That is the finding the phase-0 target exists to
make visible. If instead the test **passes** (`XPASS` — a strict xfail failure), stop: the
measured ladder disagrees with the 3-seed measurement recorded in the spec, and Task 8's
recorded numbers must be re-measured before going further.

- [ ] **Step 5: Run the whole suite to confirm nothing else moved**

```bash
uv run pytest -q
```

Expected: every previously passing test still passes; one new `xfailed`. A new metric column
must not change any behaviour — if it does, a test is reading `frame.columns` positionally and
that is a defect to report before continuing.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/resim/metrics.py tests/test_validation.py
git commit -m "test(validation): target 9 — zone gross-yield ladder, emergent

Adds gross_yield_<zone> and gross_yield_national to metrics, and gates the
sourced ladder (T 4.7-5.6 / S 6.5-7.5 / R 7-9, idealista + BdE RBA) as an
EMERGENT quantity rather than an input.

Born red, as a dated strict xfail: rural runs to ~18.8%. The yield is pinned
to price by required_rent while rural rental supply has no entry margin and
migration only flows into it. Fixed in phase B."
```

---

### Task 4: Rent-level ordering target

**Files:**
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: existing columns `rent_tensioned`, `rent_secondary`, `rent_rural`.
- Produces: fixture key `rent_ranking`.

- [ ] **Step 1: Write the failing test**

In `tests/test_validation.py`, add to the `baseline_moments` dictionary literal, immediately
after the `"price_ranking"` entry:

```python
                "rent_ranking": (
                    tail["rent_tensioned"].mean()
                    > tail["rent_secondary"].mean()
                    > tail["rent_rural"].mean()
                ),
```

Then add the test immediately after `test_zone_gross_yield_ladder`:

```python
@pytest.mark.xfail(
    strict=True,
    reason="2026-09-11: rural asking rent overtakes the tensioned index around tick 35-40 "
    "and ends 20-35% above it on 3 seeds. The location premium discounts purchase "
    "willingness in rural but nothing discounts rent acceptance (model-spec §5b), while "
    "downward-only migration funnels seekers there and the sharing margin lifts accepted "
    "burden to 0.55. Fixed by bidirectional migration and buy-to-let entry "
    "(spec §7.3, §7.5 — phase B).",
)
def test_rent_level_ordering(baseline_moments):
    """Target 11: asking rent levels must rank tensioned > secondary > rural.

    The price ladder is gated (targets 2b-2d) and the rent ladder is not, which is how a
    rural rent index above the metro one survived unnoticed. Spanish rent levels rank
    strictly the other way at every published basis [idealista, SERPAVI, EPF regional
    averages — €675/month Madrid against €277 Extremadura, Funcas 104 ch.5].
    """
    assert baseline_moments["rent_ranking"]
```

- [ ] **Step 2: Run it**

```bash
uv run pytest tests/test_validation.py::test_rent_level_ordering -v -rx
```

Expected: `xfailed` on `assert False`. If it XPASSes, the inversion has moved with the seed
set — re-measure on 5 seeds and record the result in Task 8 before changing the xfail.

- [ ] **Step 3: Run the suite**

```bash
uv run pytest -q
```

Expected: no regressions; two new `xfailed`.

- [ ] **Step 4: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add tests/test_validation.py
git commit -m "test(validation): target 11 — rent level ordering T > S > R

No gate existed on rent levels, only on prices, which is how a rural asking
rent 20-35% above the tensioned index survived unnoticed across 60 ticks and
3 seeds. Born red as a dated strict xfail; fixed in phase B."
```

---

### Task 5: Migration flow counters and the net-migration target

**Files:**
- Modify: `src/resim/engine.py` (`_demography`, migration block)
- Modify: `src/resim/metrics.py` (per-zone loop)
- Test: `tests/test_metrics.py` (create), `tests/test_validation.py`

**Interfaces:**
- Consumes: `state.tick_events` (the sanctioned per-tick scratch dict).
- Produces: `tick_events["migration"]: dict[tuple[ZoneType, ZoneType], int]` keyed
  `(origin, destination)`; frame columns `net_migration_tensioned`,
  `net_migration_secondary`, `net_migration_rural`. Task 8 reads the columns.

- [ ] **Step 1: Write the failing mechanical test**

Create `tests/test_metrics.py`:

```python
"""Mechanical correctness of metric columns, against hand-built states.

`test_validation.py` judges the model against the world; this file judges the
measurement against the state. A column that is wrong here makes every target
that reads it meaningless.
"""

import numpy as np

from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.scenario import Scenario


def small_state(seed: int = 9):
    """One settled tick, so indices, expectations and tick_events all exist."""
    cfg = SimConfig.baseline(seed=seed, ticks=4)
    engine = Engine(Scenario(name="t", baseline=cfg))
    state = engine.initialise()
    engine.step(state)
    return engine, state


def test_net_migration_columns_sum_to_zero():
    """Migration moves households between zones; it never creates or destroys them."""
    _, state = small_state()
    row = state.history[-1]
    total = sum(row[f"net_migration_{z.value}"] for z in ZoneType)
    assert total == 0


def test_net_migration_counts_the_recorded_flows():
    """The column is inflows minus outflows of the tick's recorded moves."""
    _, state = small_state()
    flows = state.tick_events["migration"]
    row = state.history[-1]
    for zone in ZoneType:
        inflow = sum(n for (_, dest), n in flows.items() if dest is zone)
        outflow = sum(n for (origin, _), n in flows.items() if origin is zone)
        assert row[f"net_migration_{zone.value}"] == inflow - outflow
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run pytest tests/test_metrics.py -v
```

Expected: both tests fail — `KeyError: 'net_migration_tensioned'` and
`KeyError: 'migration'`.

- [ ] **Step 3: Record the flows in the engine**

In `src/resim/engine.py`, replace the migration block at the end of `_demography`:

```python
        # migration: priced-out seekers slide down the zone ladder [guess]
        ladder = {ZoneType.TENSIONED: ZoneType.SECONDARY, ZoneType.SECONDARY: ZoneType.RURAL}
        for hh in state.households.values():
            if hh.status is HouseholdStatus.SEEKER and hh.zone in ladder:
                zs = state.zones[hh.zone]
                if zs.rent_index * 12 > hh.max_rent_burden * hh.income and rng.random() < 0.10:
                    hh.zone = ladder[hh.zone]
```

with:

```python
        # migration: priced-out seekers slide down the zone ladder [guess — reduced form with
        # no identifying episode, and the WRONG SIGN: Spain's net internal flow runs
        # rural→metro. Replaced by bidirectional flows in phase B, spec §7.5. The flows are
        # counted here so the defect is measurable before it is fixed.]
        ladder = {ZoneType.TENSIONED: ZoneType.SECONDARY, ZoneType.SECONDARY: ZoneType.RURAL}
        flows: dict[tuple[ZoneType, ZoneType], int] = {}
        for hh in state.households.values():
            if hh.status is HouseholdStatus.SEEKER and hh.zone in ladder:
                zs = state.zones[hh.zone]
                if zs.rent_index * 12 > hh.max_rent_burden * hh.income and rng.random() < 0.10:
                    origin, dest = hh.zone, ladder[hh.zone]
                    hh.zone = dest
                    flows[(origin, dest)] = flows.get((origin, dest), 0) + 1
        state.tick_events["migration"] = flows
```

- [ ] **Step 4: Add the metric columns**

In `src/resim/metrics.py`, immediately before the `for zone in ZoneType:` loop (next to the
`cap_coverage` line), insert:

```python
    # inter-zone moves recorded by engine._demography this tick, keyed (origin, destination)
    migration = state.tick_events.get("migration", {})
```

Inside the loop, immediately after the `row[f"new_leases_{z}"] = ...` block, insert:

```python
        # net internal migration, model-scale households/tick (model-spec §9 target 12).
        # Spain's net internal flow runs rural→metro; the current rule can only produce the
        # opposite sign, which is why this is measured before it is fixed.
        row[f"net_migration_{z}"] = sum(
            n for (_, dest), n in migration.items() if dest is zone
        ) - sum(n for (origin, _), n in migration.items() if origin is zone)
```

- [ ] **Step 5: Run the mechanical tests**

```bash
uv run pytest tests/test_metrics.py -v
```

Expected: both PASS.

- [ ] **Step 6: Write the failing validation target**

In `tests/test_validation.py`, add the test after `test_rent_level_ordering`:

```python
@pytest.mark.xfail(
    strict=True,
    reason="2026-09-11: the migration rule is downward-only (engine._demography), so net "
    "internal migration into the tensioned zone cannot be positive by construction. "
    "Spain's net internal flow runs rural→metro. Fixed by bidirectional flows identified "
    "on INE Migraciones y Variaciones Residenciales (spec §7.5 — phase B).",
)
def test_net_internal_migration_favours_the_metro():
    """Target 12: cumulative net internal migration into TENSIONED must be positive.

    Direction only — the level needs the INE series, which is not yet in
    `docs/sources.md`. The sign is not in doubt and the model has it inverted: households
    can only move down the ladder, so the tensioned zone is a net loser of internal
    migrants in every run.
    """
    nets = []
    for seed in (1, 2, 3):
        frame = metrics.to_frame(Engine(build_scenario("baseline", seed, 60)).run())
        nets.append(frame["net_migration_tensioned"].sum())
    assert float(np.mean(nets)) > 0
```

- [ ] **Step 7: Run it**

```bash
uv run pytest tests/test_validation.py::test_net_internal_migration_favours_the_metro -v -rx
```

Expected: `xfailed`, the mean being ≤ 0.

- [ ] **Step 8: Run the whole suite**

```bash
uv run pytest -q
```

Expected: no regressions. `test_same_seed_same_run` and
`test_reproducible_across_processes` must still pass — the flows dict is built from the
existing `rng` draws in the existing order, so the random stream is unchanged. If either
reproducibility test fails, the edit changed draw order and must be reverted.

- [ ] **Step 9: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/resim/engine.py src/resim/metrics.py tests/test_metrics.py tests/test_validation.py
git commit -m "test(validation): target 12 — net internal migration, and the counters for it

engine._demography now records inter-zone moves into tick_events['migration'],
and metrics exposes net_migration_<zone>. The random stream is untouched.

The target is born red because the rule has the wrong sign: migration is
downward-only, so the tensioned zone cannot be a net receiver of internal
migrants, while Spain's net internal flow runs rural→metro. Fixed in phase B.

Adds tests/test_metrics.py for mechanical correctness of metric columns,
separate from test_validation.py which judges the model against the world."
```

---

### Task 6: Landlord-household metric (reported, not gated)

**Files:**
- Modify: `src/resim/metrics.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: `state.stock.units`, `state.households`.
- Produces: frame columns `landlord_households` (count, model scale) and
  `landlord_household_share` (share of all households). Task 8 records them; phase B gates
  them against EFF/AEAT once those rows exist in `docs/sources.md`.

- [ ] **Step 1: Write the failing mechanical test**

Append to `tests/test_metrics.py`:

```python
def test_landlord_household_share_counts_owners_of_units_they_do_not_live_in():
    """A landlord household owns at least one unit that is not its own home."""
    _, state = small_state()
    row = state.history[-1]
    expected = {
        hh.id
        for hh in state.households.values()
        for u in state.stock.units.values()
        if u.owner_id == hh.id and u.id != hh.unit_id
    }
    assert row["landlord_households"] == len(expected)
    assert row["landlord_household_share"] == len(expected) / max(1, len(state.households))
    assert 0.0 <= row["landlord_household_share"] <= 1.0
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run pytest tests/test_metrics.py::test_landlord_household_share_counts_owners_of_units_they_do_not_live_in -v
```

Expected: `KeyError: 'landlord_households'`.

- [ ] **Step 3: Add the metric**

In `src/resim/metrics.py`, immediately after the `row["public_rental_share"] = ...` line,
insert:

```python
    # how many HOUSEHOLDS are landlords — the anchor for buy-to-let entry (spec §7.3).
    # Reported, not gated: the EFF2024 second-property share and the AEAT count of taxpayers
    # declaring rental income are not yet rows in docs/sources.md. Today the model has no
    # entry margin at all (a household buyer always becomes an owner-occupier), so this can
    # only fall over a run — which is the defect it exists to measure.
    landlord_ids = {
        u.owner_id
        for u in all_units
        if u.owner_id >= 0
        and u.owner_id in state.households
        and state.households[u.owner_id].unit_id != u.id
    }
    row["landlord_households"] = len(landlord_ids)
    row["landlord_household_share"] = len(landlord_ids) / n_hh
```

- [ ] **Step 4: Run the test**

```bash
uv run pytest tests/test_metrics.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run the whole suite, lint and commit**

```bash
uv run pytest -q
uv run ruff check . && uv run ruff format .
git add src/resim/metrics.py tests/test_metrics.py
git commit -m "feat(metrics): landlord_households — the buy-to-let entry anchor

Share of households owning a unit they do not live in. Reported, not gated:
the EFF2024 second-property share and the AEAT rental-income declarant count
are not yet in docs/sources.md.

The model has no landlord entry margin at all today, so the series can only
fall over a run. That is the asymmetry phase B fixes, and this is how it
becomes visible."
```

---

### Task 7: Time-to-sale metric (reported, not gated)

**Files:**
- Modify: `src/resim/market/clearing.py` (`Trade`, `clear_sales`)
- Modify: `src/resim/metrics.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: `SaleListing.ticks_listed`.
- Produces: `Trade.ticks_listed: int = 0`; frame column `median_ticks_to_sale`. Phase D gates
  it against the idealista days-on-market distribution once that row exists in
  `docs/sources.md`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_metrics.py`:

```python
def test_trade_carries_the_listing_age():
    """A matched trade reports how long its listing had been on the market."""
    from resim.agents.base import MakeOffer
    from resim.market.clearing import clear_sales
    from resim.state import SaleListing

    _, state = small_state()
    unit = next(u for u in state.stock.units.values() if u.owner_id >= 0)
    zs = state.zones[unit.zone]
    ask = zs.price_index * unit.quality
    state.sale_listings.clear()
    state.sale_listings[unit.id] = SaleListing(
        unit_id=unit.id, ask=ask, reserve=ask * 0.5, ticks_listed=3
    )
    # a negative agent id is an aggregate cash buyer, so no credit screen and no
    # one-purchase-per-buyer dedup interferes with the assertion
    offers = [MakeOffer(agent_id=-99, zone=unit.zone, budget=ask * 2.0, cash=True)]
    trades = clear_sales(state, offers, np.random.default_rng(0))
    assert trades, "a cash offer at twice the ask must clear"
    assert trades[0].ticks_listed == 3


def test_median_ticks_to_sale_is_reported():
    """The column exists and is non-negative wherever the tick had trades."""
    _, state = small_state()
    row = state.history[-1]
    value = row["median_ticks_to_sale"]
    assert np.isnan(value) or value >= 0
```

- [ ] **Step 2: Run it to verify it fails**

```bash
uv run pytest tests/test_metrics.py -v
```

Expected: `test_trade_carries_the_listing_age` fails with
`AttributeError: 'Trade' object has no attribute 'ticks_listed'`, and
`test_median_ticks_to_sale_is_reported` fails with `KeyError`.

- [ ] **Step 3: Carry the listing age on the trade**

In `src/resim/market/clearing.py`, in the `Trade` dataclass, add the field after `guaranteed`:

```python
    ticks_listed: int = 0  # age of the listing when it matched — time-to-sale diagnostic
```

In `clear_sales`, in the `trades.append(Trade(...))` call, add the argument after
`guaranteed=best_offer.guaranteed,`:

```python
                    ticks_listed=lst.ticks_listed,
```

- [ ] **Step 4: Add the metric**

In `src/resim/metrics.py`, immediately after the `row["new_leases"] = len(rentals)` line,
insert:

```python
    # time to sell, in ticks (model-spec §9 target 13). Reported, not gated: the idealista
    # days-on-market distribution is not yet a row in docs/sources.md. It is the observable
    # that identifies the phase-D auction without touching the price level (spec §7.7).
    row["median_ticks_to_sale"] = (
        float(np.median([t.ticks_listed for t in trades])) if trades else float("nan")
    )
```

- [ ] **Step 5: Run the tests**

```bash
uv run pytest tests/test_metrics.py -v
```

Expected: all PASS.

- [ ] **Step 6: Run the whole suite**

```bash
uv run pytest -q
```

Expected: no regressions, including both reproducibility tests — `Trade` gains a defaulted
field and no draw order changes.

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff check . && uv run ruff format .
git add src/resim/market/clearing.py src/resim/metrics.py tests/test_metrics.py
git commit -m "feat(metrics): median_ticks_to_sale — the observable that identifies the auction

Trade now carries the age of the listing it matched, and metrics reports the
per-tick median. Reported, not gated: the idealista days-on-market
distribution is not yet in docs/sources.md.

This is the quantity that lets phase D's ascending auction be identified
without tuning against the price level itself (spec §7.7)."
```

---

### Task 8: Yield-compression target, then record phase 0 in validation.md

**Files:**
- Test: `tests/test_validation.py`
- Modify: `docs/validation.md`

**Interfaces:**
- Consumes: `gross_yield_tensioned` (Task 3), the existing `_holdout_boom` helper's scenario
  construction.
- Produces: the phase-0 record in `docs/validation.md` — the measured value of every new
  target, and which are xfailed.

- [ ] **Step 1: Write the compression test**

In `tests/test_validation.py`, add after `test_holdout_boom_rent_growth`:

```python
def test_boom_compresses_the_gross_yield():
    """Target 10: in a boom the gross rental yield must COMPRESS.

    Sign test only. Spain 2014-25 ran prices ahead of rents and gross yields fell; the
    level band needs the idealista yield series, which is not yet a row in
    `docs/sources.md`, so only the direction is asserted here (model-spec §13.1:
    direction, not magnitude).

    Mechanically this is the signature of the landlord's reservation rule. Under the current
    rule the reservation rent is a fixed multiple of value, so the yield floor tracks price
    one-for-one and compression can only come from the gap between the asking index and that
    floor. Under the total-return hurdle (spec §7.1) compression is the rule's direct
    prediction: E[g] up ⇒ required rent yield down.
    """
    starts, ends = [], []
    for seed in (3, 5, 7, 8, 9):
        cfg = SimConfig.baseline(seed=seed, ticks=40)
        cfg = dataclasses.replace(
            cfg,
            population=dataclasses.replace(
                cfg.population, formation_per_tick=33, formation_income_factor=1.0
            ),
            developer=dataclasses.replace(
                cfg.developer, base_starts_per_tick=11, max_starts_per_tick=12
            ),
        )
        scenario = Scenario(
            name="holdout",
            baseline=cfg,
            interventions=(RateShock(start_tick=20, euribor=0.005),),
        )
        frame = metrics.to_frame(Engine(scenario).run())
        starts.append(frame["gross_yield_tensioned"].iloc[20:24].mean())
        ends.append(frame["gross_yield_tensioned"].iloc[36:40].mean())
    assert float(np.mean(ends)) < float(np.mean(starts))
```

- [ ] **Step 2: Run it and record what happens**

```bash
uv run pytest tests/test_validation.py::test_boom_compresses_the_gross_yield -v
```

Two outcomes, both legitimate, and the plan does not prejudge which:

- **PASS** — leave it as a live gate. Record the measured start and end yields in Step 4.
- **FAIL** — add the strict xfail below, with the measured numbers in the reason, and record
  the same numbers in Step 4.

```python
@pytest.mark.xfail(
    strict=True,
    reason="2026-09-11: measured <start> → <end> (5 seeds), i.e. no compression. "
    "required_rent ties the reservation rent to a fixed multiple of value, so the yield "
    "floor tracks price one-for-one. Fixed by the total-return hurdle "
    "(spec §7.1 — phase B).",
)
```

Replace `<start>` and `<end>` with the values printed by:

```bash
uv run pytest tests/test_validation.py::test_boom_compresses_the_gross_yield -v -s --tb=long
```

- [ ] **Step 3: Run the whole suite**

```bash
uv run pytest -q
```

Expected: no regressions; the new targets from Tasks 3–7 present as passes, xfails or
reported-only columns exactly as committed.

- [ ] **Step 4: Record phase 0 in `docs/validation.md`**

Insert this section immediately after the existing target table (before the
`## Zone price ladder — the one failing target` heading), filling in every `<measured>` from
the runs above:

```markdown
## Phase-0 targets (2026-09-11)

Seven observable moments added by the redesign's phase 0
(`docs/superpowers/specs/2026-09-11-model-redesign-design.md` §6). Several are red on
arrival — that is their purpose: they make defects that were invisible into failures the
suite reports. Reporting categories follow `model-spec.md §13.1`.

| # | Target | Empirical range | Model | Status |
|---|---|---|---|---|
| 9 | Zone gross-yield ladder, emergent | T 4.7–5.6 / S 6.5–7.5 / R 7–9% (idealista + BdE RBA) | T <measured> / S <measured> / R <measured> | ✗ **strict xfail** — rural ≈3× the band; phase B |
| 10 | Boom compresses the gross yield | direction only (idealista series not yet sourced) | <measured> → <measured> | <pass or strict xfail> |
| 11 | Rent level ordering T > S > R | strict, at every published basis | <measured> | ✗ **strict xfail** — rural overtakes the metro around tick 35–40; phase B |
| 12 | Net internal migration into TENSIONED > 0 | direction only (INE Migraciones not yet sourced) | <measured> | ✗ **strict xfail** — the rule is downward-only; phase B |
| 13 | Time to sell (`median_ticks_to_sale`) | idealista days on market — **to verify** | <measured> ticks | reported, not gated; phase D gates it |
| 14 | Landlord households (`landlord_household_share`) | EFF2024 second-property share; AEAT declarants — **to verify** | <measured> | reported, not gated; phase B gates it |
| 15 | Foreclosure flow | CGPJ — **to verify** | not measurable | deferred to phase C: no insolvency mechanism exists, so no test is written. Registered in `docs/holdout-2008-2013.md` |

Two of these are the same defect seen from different sides: the rural rent level (11) and the
rural yield (9). The zone ladder was gated on prices only, so a rural asking rent above the
metro index survived 60 ticks and 3 seeds unnoticed.

Target 15 is deliberately **not** written as a test. A test that cannot run is not evidence of
anything, and an xfail on a missing mechanism would be decoration.
```

- [ ] **Step 5: Commit**

```bash
uv run ruff check . && uv run ruff format .
git add tests/test_validation.py docs/validation.md
git commit -m "test(validation): target 10 — boom yield compression; record phase 0

Sign test on the hold-out boom: gross yield must fall when prices run ahead
of rents. Direction only, per model-spec §13.1 — the idealista yield series
is not yet a row in docs/sources.md, so no level band is asserted.

validation.md records all seven phase-0 targets with their measured values
and status. Target 15 (foreclosure flow) is deliberately not written as a
test: no insolvency mechanism exists yet, and an xfail on a missing mechanism
would be decoration."
```

---

### Task 9: Phase-0 adversarial referee pass

**Files:**
- Modify: `docs/validation.md` ("Honest qualifications")

**Interfaces:**
- Consumes: everything committed in Tasks 1–8.
- Produces: the written concessions the reporting contract requires (`model-spec.md §13.6`).

- [ ] **Step 1: Run the full suite one more time and capture the summary**

```bash
cd "/Users/nikomendez/Documents/AI Engineering/Real Estate Simulator"
uv run pytest -q 2>&1 | tail -5
```

Record the counts (passed / xfailed) — they go in the commit message.

- [ ] **Step 2: Append the referee pass to `docs/validation.md`**

Add at the end of the "Honest qualifications" section:

```markdown
### Phase-0 referee pass (2026-09-11)

Objections a hostile reader can raise against phase 0, answered or conceded.

- **"You widened the yield bands by 0.5pp until the test said what you wanted."** Conceded as
  a judgement call, not as a fit: the widening is symmetric, applied before the test was run,
  and the test fails anyway by a factor of three on the rural leg. The convention matches the
  other zone targets (3 seeds, last 20 of 60 ticks).
- **"Four xfails is four failures you are choosing to live with."** Conceded, and that is the
  point of writing them down. Each names the mechanism that will fix it and the phase it
  lands in. Strict xfail means an accidental pass also fails the suite, so none of them can
  quietly stop being true.
- **"`median_ticks_to_sale` and `landlord_household_share` are gates you declined to set."**
  Conceded. Setting a band from memory would be exactly the defect this project exists to
  avoid; both rows say **to verify** and name the source to retrieve.
- **"The assumption register is your own account of your own work."** True, and it is
  falsifiable in the only way that matters: every row names a code site, so any row can be
  checked against the code, and a rule with no row is a finding against the register.
- **"Sealing the hold-out is unverifiable — you could have looked."** Partly conceded. What is
  verifiable is the order of commits: the seal predates the bust inputs, which predate the
  run. What is not verifiable is what the authors knew. The 2008–13 episode is public
  knowledge; the claim is not that nobody knows how it ended, but that no *parameter* was
  fitted to it, which the history does evidence.
```

- [ ] **Step 3: Commit**

```bash
git add docs/validation.md
git commit -m "docs: phase-0 adversarial referee pass

Five objections a hostile reader can raise against phase 0, each answered or
conceded in writing, per the reporting contract (model-spec §13.6). Three are
conceded outright, including that sealing a hold-out evidences the order of
work and not the authors' state of knowledge.

Suite: <N> passed, <M> xfailed."
```

---

## Self-Review

**Spec coverage (§ by §):**

- §3.1 derived-or-reduced-form rule → Task 2 (§13.3), Task 1 (the nine rules named with status).
- §3.2 variance rule → Task 2 (§13.2), Task 1 (Sobol share column).
- §3.3 assumption register → Task 1.
- §3.4 exogenous boundary → Task 2 (§14), Task 1 (boundary table).
- §3.5 falsification conditions → Task 1 (`Falsified by` column), Task 2 (§13.5).
- §3.6 pre-registration → Task 2 (`docs/prereg/TEMPLATE.md`).
- §3.7 adversarial referee pass → Task 2 (§13.6), Task 9 (the pass itself).
- §4 calibration protocol → Task 2 (§13.4), Task 2 (`docs/holdout-2008-2013.md`).
- §6 seven new targets → Tasks 3 (yield ladder), 8 (compression), 4 (rent ordering), 5 (net
  migration), 7 (time to sell), 6 (landlord households), 8 (foreclosure flow registered and
  deliberately not tested).
- Phase-0 row of §5's table ("seal 2008–13") → Task 2.

**Not in this plan, by design:** the config-identity target rows and the four bug fixes belong
to phase A; every mechanism belongs to phases B–D. Phase 0 changes no behaviour.

**Placeholder scan:** the `<measured>`, `<start>`, `<end>`, `<N>` and `<M>` markers in Tasks 8
and 9 are values the implementer must obtain by running the commands given in the step
immediately above each. They are not unspecified work. No other placeholders remain.

**Type consistency check:** `tick_events["migration"]` is written in
`engine._demography` as `dict[tuple[ZoneType, ZoneType], int]` and read in `metrics.snapshot`
and `tests/test_metrics.py` with the same key shape. `Trade.ticks_listed` is written in
`clear_sales` and read in `metrics.snapshot` and `tests/test_metrics.py`. Fixture keys
`gy_tensioned` / `gy_secondary` / `gy_rural` and `rent_ranking` are added to
`baseline_moments` in Tasks 3 and 4 and read only by the tests that add them. Column names
`gross_yield_<zone>`, `net_migration_<zone>`, `landlord_households`,
`landlord_household_share` and `median_ticks_to_sale` are spelled identically in
`metrics.py`, both test files and `docs/validation.md`.
