# Phase A — model bug fixes

Branch `model-bug-fixes`. Closes findings 4, 6, 9 and 10 of
`docs/superpowers/specs/2026-09-11-model-redesign-design.md` §2.

Phase A is **not** a redesign. Every item below is one of three things: code that disagrees
with its own comment, a term that does nothing while claiming to do something, or a guessed
constant hidden in a module instead of declared in `config.py` with a range. No new mechanism
is added; that is phase B's job, and doing any of it here would make phase B's calibration
unreadable.

The reason A precedes B is not procedural. Finding 4 leaks ownership into exactly the
quantity phase B calibrates buy-to-let entry against (`landlord_household_share`, EFF basis =
"owns a dwelling it does not live in"). Entry fitted against a leak is fitted against noise.

---

## A1 — Inheritance (finding 4)

`engine._demography`, the dissolution block. Three defects, one of which is the registered
finding and two of which surfaced while reading it.

### A1.a The heir does not become an owner — the registered leak

On dissolution the deceased's home is vacated (`tenure = VACANT`, `occupant_id = None`) and
every unit they owned has `owner_id` reassigned. **Nothing else is touched.** A SEEKER who
inherits a dwelling stays a SEEKER: the model counts them as a non-owner while they own an
empty home. `ownership_rate` counts `status is OWNER`, so ownership drifts 77.2% → 69.5%
over 60 ticks, and target 1 sits below the EFF band for a reason that has nothing to do with
Spanish tenure.

**Rule.** An heir with no home of their own moves into the inherited dwelling:

> If the heir's `unit_id is None` (a SEEKER), they occupy one inherited unit — the deceased's
> own home where there is one, otherwise the first unit of the estate. Status → `OWNER`,
> `unit_id` → that unit, `tenure` → `OWNER_OCCUPIED`, `vacant_since` cleared.

An heir who already has a home keeps it, and the inherited dwellings stay vacant stock owned
by them. That is the **conservative** branch on purpose: it is the one the current code
already produces, it needs no new behavioural claim, and it is what makes the inherited-and-
vacant dwelling a real category in `landlord_household_share` rather than an artefact.

A TENANT heir is deliberately left renting. Moving in would break a tenancy, which is a
behavioural claim about Spanish heirs that the register carries no source for; phase B can
add it with one. Recorded in `docs/assumptions.md` as assumed, with its falsifier.

### A1.b The estate splits, but the comment and the register both say it does not

```python
for unit in state.stock.units.values():
    if unit.owner_id in gone:
        unit.owner_id = int(heirs[int(rng.integers(len(heirs)))])
```

A fresh heir is drawn **per unit**. The comment above it says "the WHOLE estate passes to a
surviving household", and `docs/assumptions.md` registers the same claim. Code and spec
disagree, which the engineering standard says is a bug in one of them.

**Resolution: the code is wrong, the register is right.** One heir per dissolved household,
drawn once. Splitting an estate across N random strangers is not a modelling choice anyone
made — it is what a loop over units does when the draw is inside it. The register's reason
for one heir (avoid orphaned landlord stock) is also better served by it.

### A1.c Dwelling-level consequence

With A1.a and A1.b, a dissolved small landlord's whole portfolio reaches one household, and
if that household was homeless it becomes an owner-occupier of one unit and a landlord of the
rest. That is the intended shape, and it is the first path in the model by which a household
becomes a landlord without buying — which is exactly the margin phase B has to get right.

**Expected effect:** ownership rate rises and stops drifting; `landlord_household_share`
moves. Both are gated or reported targets, so the numbers are re-measured, not predicted here.

---

## A2 — The dead user-cost term (finding 6)

`agents/household.decide`:

```python
user_cost = max(0.005, macro.mortgage_rate + 0.01 - 4.0 * zs.expected_price_growth)
own_vs_rent = float(np.clip(gross_yield / user_cost, 0.5, 1.0))
```

The comment calls this "the channel a rate shock works through (2022–23: volume fell, prices
stayed sticky)". It is not. The ratio only falls below 1.0 when `user_cost > gross_yield`,
i.e. above roughly a 6.2% mortgage rate at baseline growth — so at every baseline rate the
term is exactly 1.0 and multiplies the budget by nothing. The rate shock actually travels
through `participation` (`PARTICIPATION_RATE_SENSITIVITY`), a few lines below.

> **AMENDED 2026-09-12, after measuring.** The premise below is false and the rule was not
> executed. Instrumented on 3 seeds × 40 ticks the term is below 1.0 in 5.78% of baseline
> decisions and 3.23% under `RateShock`; the 0.5 floor has never bound; removing it moves the
> baseline price level −1.5%. It is not inert. The half of the finding that survives is worse
> than registered: it engages LESS in the shock it was said to carry, because the yield
> dominates the ratio. Action taken instead: comment corrected to the measurement, registered
> in `docs/assumptions.md` as an unsourced reduced form, mechanism handed to phase D. Full
> record in `docs/validation.md`, "Phase-A finding-6 correction".

**Superseded rule.** Delete `own_vs_rent` from the budget and move the rate-shock claim to the comment on
`participation`, which is where it is true. A real user-cost channel — tenure choice on the
full cost of ownership against the cost of renting — is a mechanism, not a bug fix, and
belongs in phase D with the sale-side redesign.

**Care required:** the term is inert *at baseline*, not in every scenario. `RateShock` may
push the rate above the ~6.2% threshold, in which case removing it changes target 6b. The
implementation measures the shock scenario before and after and records the delta. If it moves,
the change is still correct — a channel that only exists above 6.2% and is documented as
carrying the ordinary rate shock is worse than no channel — but the number gets recorded, not
hidden.

---

## A3 — The growth-wedge hazard floor (finding 9)

`agents/landlord.decide`:

```python
growth_wedge = max(0.0, 4.0 * zs.shadow_growth - cfg.policy.within_contract_update)
gap = np.log(fundamental_ask / cap) + 5.0 * growth_wedge
```

Under a cap, `shadow_growth` is the exogenous income anchor and `within_contract_update` is a
policy constant. Both are exogenous, so the wedge is **a constant**, and `gap` therefore has a
positive floor of `5 × growth_wedge` even when the cap binds on nothing at all
(`fundamental_ask == cap`, log term zero). Landlords exit a cap that costs them nothing.

**Rule.** The wedge stays — it is a real PV term — but the floor becomes visible and
falsifiable instead of structural:

1. The horizon multipliers `4.0` (annualisation) and `5.0` (holding years) move to
   `config.py` as named, unit-carrying parameters with ranges. `5.0` years is a guess about
   Spanish holding periods and must be labelled one.
2. The exit hazard is gated on the cap actually binding: no level gap, no growth wedge. A
   landlord whose fundamental ask is at or below the cap has nothing to escape.

This changes the rent-cap result. That is the point of the finding: the headline was riding on
a floor nobody chose. The re-measured elasticity dial is recorded in `docs/validation.md`, and
if the three studies no longer span the 0–2 dial, **that is written down, not re-fitted** —
phase B replaces this machinery with the arbitrage condition anyway (spec §7.2).

---

## A4 — Guessed cap constants into `config.py` with ranges (finding 10)

Four constants currently live as module-level literals in `agents/landlord.py`, and the
headline rent-cap result rides on all of them:

| Constant | Today | Status |
|---|---|---|
| `EXIT_SPLIT` `{sale .5, seasonal .35, vacant .15}` | module literal | guess, open question investor-small §7.1 |
| `HAZARD_SCALE = 0.7` | module literal | fitted to the studies' dial, not observed |
| magnet `ask * 1.05` | inline literal | guess |
| `EXIT_SPLIT_EVASION_BASE = 0.15` | module literal | Incasòl, medium confidence |

**Rule.** All four become fields on a `CapConfig` dataclass in `config.py`, each carrying its
unit, its source (or the word `guess`), and — where the evidence is disputed — a **range**, per
the project's bias-control rule. The module keeps no literal that the cap result depends on.

This is what makes them reachable by phase E's Sobol screening. A constant that is not in
`config.py` cannot be swept, and the variance rule of spec §3.2 cannot be applied to it.

---

## A5 — Config identities out of the validation target table (finding 8, partly)

Two rows of the `docs/validation.md` target table are not validation:

- *National supply elasticity (zone-weighted) — 0.45–0.58 — 0.49 ✓*
- *Zone dwellings/household weight to the national anchor — 1.12 ± 0.01 — 1.13 ✓ invariant*

Their tests (`test_zone_supply_elasticities_average_to_the_national_anchor`,
`test_zone_stock_ratios_hold_their_anchors`) construct `SimConfig.baseline()` and assert on
config fields. **No engine runs.** They check that the config is internally consistent with
its own anchor — worth keeping, and genuinely useful as guards — but they are not evidence
that the model reproduces anything, and sitting in the target table with a ✓ they read as if
they were.

**Rule.** Move both to a separate **"Config guards"** section in `docs/validation.md`, stated
as what they are, and out of the counted target table. The tests move to
`tests/test_config_guards.py` under the same name. Nothing is deleted and no assertion
weakens: the claim changes, not the check.

---

## Order of work

1. A5 first — it is pure bookkeeping and touches nothing the others touch.
2. A4 — mechanical extraction, no behaviour change. Suite must stay green on the same numbers.
3. A2 — measure `RateShock` before, remove, measure after, record.
4. A3 — the hazard gate. Re-measure the rent-cap dial. Expect movement.
5. A1 last — it moves ownership, which every tenure target reads.

Each step re-runs the full suite. A step that moves a gated target records the before/after in
`docs/validation.md` in the same commit that moves it.

## What phase A must NOT do

- No new mechanism: no buy-to-let entry, no bidirectional migration, no total-return hurdle.
  Those are phase B and they need the sources that are still being retrieved.
- No re-fitting a target that A breaks. A broken target gets a dated strict xfail naming the
  mechanism, exactly as phase 0 did. Re-fitting is phase E, once, on 2014–25 only.
- No touching the three phase-0 xfails (targets 9, 11, 12). They are phase B's to flip.
