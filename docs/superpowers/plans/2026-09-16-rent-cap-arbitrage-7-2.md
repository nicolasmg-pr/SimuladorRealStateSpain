# §7.2 Rent-Cap Arbitrage Condition — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the rent cap's fitted `hazard_scale` withdrawal hazard with the reservation-rent arbitrage condition specified in `docs/model-spec.md` §7.2, retiring five parameters and turning the supply elasticity into a model output.

**Architecture:** `Landlord.decide` already computes the reservation rent as `floor = required_rent(...)` and uses it only as a floor on the ask. The trigger for withdrawal moves from "the cap binds at all" (`fundamental_ask > cap`) to "the cap breaks the hurdle" (`cap < floor`). Behind that trigger, a deterministic comparison replaces the probabilistic hazard: seasonal diversion first (the cheap exit, no transaction cost), then sale when the cumulative widening shortfall over the holding horizon exceeds the cost of leaving. Vacancy stops being a destination and becomes the waiting state of the sale channel.

**Tech Stack:** Python 3.14 (min 3.12), numpy, pandas, Streamlit, pytest, ruff, uv.

**Spec:** `docs/model-spec.md` §7.2 "The withdrawal margin, from the reservation rent (2026-09-16)". Read it before Task 1. §5b.1 (the two statutes) and §13.7 (the yield basis and `c`) are its immediate context.

## Global Constraints

- All randomness flows from the seeded `Generator` passed down from the engine. No module-level `random` or `np.random`. Agents draw from `self.rng`.
- Agents are read-only on state: `decide()` returns intents; the engine and `market/clearing.py` are the only writers.
- Typed dataclasses for config, scenario, state and intents. No dicts as informal records.
- Parameters carry units and a source in the `config.py` comment. An unsourced parameter is labelled `[guess]`.
- **Nothing in this plan may be re-fitted to make a target pass.** A failing target is recorded with its diagnosis, as `docs/validation.md` does throughout. This is the project's hardest rule and §7.2's F1–F4 depend on it.
- Commands: `uv sync --dev` first; `uv run pytest`; `uv run ruff check . && uv run ruff format .`.
- Ten-seed measurements use the existing harness, not ad-hoc loops.

---

## File Structure

| File | Responsibility after this plan |
|---|---|
| `src/resim/agents/landlord.py` | The arbitrage condition: trigger, branch order, destination. New private method `_exit_destination`. `_exit` is deleted. |
| `src/resim/config.py` | `CapResponseConfig` loses `hazard_scale`, `hazard_scale_range`, `exit_split_sale`, `exit_split_sale_range`, `exit_split_seasonal`, `exit_split_vacant`, `exit_split_evasion_base`. `MarketConfig` loses `rental_supply_elasticity`. |
| `src/resim/scenario.py` | `RentCap` loses `supply_response_elasticity`, gains `selling_cost_share` and `holding_years` overrides. |
| `src/resim/sensitivity.py` | Drops `hazard_scale`, adds `holding_years`. |
| `src/resim/ui/levers.py` | Elasticity slider replaced by two structural sliders. |
| `tests/test_validation.py` | The three Ley 11/2020 gates rewritten for a world with no dial; new F1 span test. |
| `tests/test_agents.py` | New unit tests for the trigger property and the branch order. |
| `docs/model-spec.md`, `docs/validation.md`, `docs/claims.md`, `docs/sources.md` | Results, F1–F4 records, and the `selling_cost_share` source rows. |

---

## Task 0: Source `selling_cost_share` (runs in parallel, blocks nothing until Task 7)

`selling_cost_share = 0.02` is `[guess, order of magnitude from buyer_fees]` and §7.2 makes it the exit threshold. Two independent institutional viewpoints are required by the project's bias-control rule.

**Files:**
- Modify: `docs/sources.md` (Tier 1 and Tier 2 tables)
- Modify: `src/resim/config.py:492` (the comment and, only if the evidence says so, the value and a new `_range`)
- Modify: `docs/validation.md` ("Honest qualifications")

**Interfaces:**
- Consumes: nothing.
- Produces: a sourced band for `MarketConfig.selling_cost_share`, or a registered negative result. Task 7 reads the band; Task 9 reads the qualification.

**The coupling to check first, before any value changes.** `selling_cost_share` is already load-bearing in `market/clearing.py:146`: `floor = max(debt * (1.0 + cfg.market.selling_cost_share), ask * (1.0 - discount))`. That is the **household** seller's reserve — the debt leg. The landlord's sale listing in `engine.py` builds its reserve from the negotiation margin only and carries no debt leg, so raising this parameter moves household lock-in, not the landlord exit price. It is still a real knock-on and must be measured, not assumed away.

- [ ] **Step 1: Record the pre-change baseline**

Run: `uv run pytest tests/test_price_formation.py -v`
Note the negotiation-margin figure currently recorded in `docs/validation.md` (5.20% ± 0.10 against a sourced 6.2% [Cátedra Tecnocasa-UPF]). Write it into the task notes; Step 5 compares against it.

- [ ] **Step 2: Retrieve viewpoint 1 — the regulated schedule**

Notarial tariff (Real Decreto 1426/1989 and successors) and registry tariff (RD 1427/1989) for a residential conveyance, plus plusvalía municipal (IIVTNU) as levied. These are published norms, not market estimates. Record the per-transaction amounts and the implied share of a €200,000 sale.

- [ ] **Step 3: Retrieve viewpoint 2 — the market side**

Estate-agency commission for residential resale in Spain (industry or consumer-organisation surveys — OCU, agency networks' own published schedules). Different institutional viewpoint from Step 2 by construction. Record the range, not a point.

- [ ] **Step 4: Register both in `docs/sources.md`**

One row per viewpoint, in the project's existing table format, with `Triangulated against` naming the other. If either retrieval fails, write the negative result row — `docs/validation.md` records that "every empirical claim written from model memory rather than retrieved turned out wrong", and a registered failure is worth more than a plausible number.

- [ ] **Step 5: Decide the value, and measure the knock-on**

If the two viewpoints support a band, set `selling_cost_share` and add `selling_cost_share_range`. Then run the ten-seed suite and compare the negotiation margin and any price-formation target against Step 1's baseline. **Record the movement; do not tune anything to restore it.**

Run: `uv run pytest -q`

- [ ] **Step 6: Commit**

```bash
git add docs/sources.md docs/validation.md src/resim/config.py
git commit -m "docs(sources): selling_cost_share, from two institutional viewpoints"
```

---

## Task 1: The trigger moves to the reservation rent

The isolated, reviewable half of the change: *when* withdrawal is considered. The hazard draw stays in place for now so that this task's effect can be attributed.

**Files:**
- Modify: `src/resim/agents/landlord.py` (the `if cap is not None:` branch in `decide`)
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: `required_rent(state, zone, value)` — already imported and called as `floor` in `decide`.
- Produces: the invariant "a cap with `cap >= floor` yields no `WithdrawRental`", which Tasks 2 and 3 must preserve.

- [ ] **Step 1: Write the failing test**

```python
def test_a_cap_that_binds_but_clears_the_hurdle_produces_no_withdrawal():
    """§7.2. The trigger is the reservation rent, not the cap binding at all.

    A cap set between the landlord's reservation rent and its fundamental ask binds —
    the posted rent falls — but the dwelling still clears the total-return hurdle, so
    there is nothing to arbitrage against and the landlord stays let. Under the
    pre-§7.2 hazard this configuration produced exits at any positive elasticity.
    """
    state = _capped_state(cap_between_reservation_and_ask=True)
    landlord = state.agents_by_id[_SMALL_LANDLORD_ID]
    intents = [landlord.decide(state) for _ in range(200)]
    withdrawals = [i for batch in intents for i in batch if isinstance(i, WithdrawRental)]
    assert withdrawals == [], f"{len(withdrawals)} withdrawals from a cap that clears the hurdle"
```

Build `_capped_state` from the existing fixtures in `tests/test_agents.py`; do not invent a new world builder. The cap must satisfy `required_rent(...) <= cap < fundamental_ask` for the unit under test — assert that precondition inside the helper so the test cannot silently pass by testing nothing.

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_agents.py::test_a_cap_that_binds_but_clears_the_hurdle_produces_no_withdrawal -v`
Expected: FAIL — withdrawals occur, because today's trigger is `fundamental_ask > cap`.

- [ ] **Step 3: Move the trigger**

In `decide`, restructure the capped branch so the withdrawal gate is the reservation rent and the ask is still capped independently:

```python
            if cap is not None:
                complies = self.rng.random() < cfg.policy.cap_compliance
                # §7.2: the trigger is the RESERVATION rent, not the cap binding at all. A cap
                # that binds but leaves `cap >= floor` still clears the landlord's hurdle, so
                # there is nothing to arbitrage against and nothing is withdrawn.
                if complies and cap < floor:
                    ...  # the existing hazard block, unchanged, moves inside here
                if complies and fundamental_ask > cap:
                    ask, capped = min(ask, cap), True
                elif ask < cap:
                    ask = min(cap, ask * capcfg.magnet_gain)
```

Keep the existing `level_gap` / `growth_wedge` / `p_exit` lines exactly as they are inside the new gate. Only the gate changes in this task.

- [ ] **Step 4: Run the new test and the three gates**

Run: `uv run pytest tests/test_agents.py -v && uv run pytest tests/test_validation.py -k rent_cap -v && uv run pytest tests/test_engine.py::test_cap_coverage_scales_the_rent_cap -v`
Expected: the new test PASSES. The three gates may move. **If a gate fails, record the measured values in the task notes and continue — do not adjust any parameter.** Task 7 adjudicates.

- [ ] **Step 5: Commit**

```bash
git add src/resim/agents/landlord.py tests/test_agents.py
git commit -m "feat(landlord): §7.2 trigger — withdrawal gated on the reservation rent"
```

---

## Task 2: The sale rule replaces the hazard

**Files:**
- Modify: `src/resim/agents/landlord.py`
- Modify: `src/resim/config.py` (`CapResponseConfig`)
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: Task 1's gate, `capcfg.holding_years`, `capcfg.wedge_annualisation`, `cfg.policy.within_contract_update`, `zs.shadow_growth`, `mk.selling_cost_share`.
- Produces: `Landlord._exit_destination(unit, state, *, cap, r_req, value) -> str | None`, returning `"seasonal"`, `"sale"` or `None`. Task 3 extends it; Task 6 asserts against it.

- [ ] **Step 1: Write the failing test**

```python
def test_sale_requires_the_shortfall_to_beat_the_cost_of_leaving():
    """§7.2 sale rule. The cumulative shortfall over the holding horizon must exceed the
    cost of leaving. A cap one euro below the reservation rent does not pay for a sale.
    """
    state = _capped_state(cap_below_reservation_by=1.0)
    landlord = state.agents_by_id[_SMALL_LANDLORD_ID]
    intents = [i for _ in range(200) for i in landlord.decide(state)]
    assert not [i for i in intents if isinstance(i, WithdrawRental)]

def test_a_deep_cap_pays_for_the_sale():
    """The same landlord, with the cap far below the reservation rent, sells."""
    state = _capped_state(cap_fraction_of_reservation=0.4, seasonal_closed=True)
    landlord = state.agents_by_id[_SMALL_LANDLORD_ID]
    intents = [i for _ in range(200) for i in landlord.decide(state)]
    dests = {i.destination for i in intents if isinstance(i, WithdrawRental)}
    assert dests == {"sale"}
```

- [ ] **Step 2: Run them and watch them fail**

Run: `uv run pytest tests/test_agents.py -k "shortfall or deep_cap" -v`
Expected: FAIL — the hazard is probabilistic, so the shallow cap still produces exits.

- [ ] **Step 3: Implement the deterministic rule**

```python
    def _exit_destination(
        self, unit: Unit, state: WorldState, *, cap: float, r_req: float, value: float
    ) -> str | None:
        """§7.2. Which alternative use beats letting at the cap, or None if none does."""
        cfg = state.config
        capcfg, pol, zs = cfg.cap_response, cfg.policy, state.zones[unit.zone]
        # SALE. The shortfall WIDENS over the horizon: the cap grows at the statutory IRAV
        # while the reservation rent grows with V and E[g]. The (1 + H·wedge/2) factor is the
        # trapezoid of that widening gap — arithmetic, not a parameter.
        growth_wedge = max(
            0.0, capcfg.wedge_annualisation * zs.shadow_growth - pol.within_contract_update
        )
        horizon = capcfg.holding_years
        shortfall = (r_req - cap) * 12.0 * horizon * (1.0 + horizon * growth_wedge / 2.0)
        if shortfall > value * cfg.market.selling_cost_share:
            return "sale"
        return None
```

Call it from the Task 1 gate in place of the hazard block, and delete the `level_gap` / `gap` / `p_exit` lines.

- [ ] **Step 4: Retire `hazard_scale`**

Delete `hazard_scale` and `hazard_scale_range` from `CapResponseConfig`, keeping the historical comment block as a dated note that ends with a pointer to §7.2. Run `grep -rn hazard_scale src tests` and fix every hit except documentation prose.

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_agents.py -v && uv run pytest -q`
Expected: the two new tests PASS. Gate movement is recorded, not repaired.

- [ ] **Step 6: Commit**

```bash
git add src/resim/agents/landlord.py src/resim/config.py tests/test_agents.py
git commit -m "feat(landlord): §7.2 sale rule replaces the fitted exit hazard"
```

---

## Task 3: Branch order, and vacancy as a waiting state

**Files:**
- Modify: `src/resim/agents/landlord.py` (`_exit_destination`; delete `_exit`)
- Modify: `src/resim/config.py` (`CapResponseConfig`)
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: Task 2's `_exit_destination`.
- Produces: seasonal-before-sale ordering; no `"vacant"` destination is ever returned by the cap channel.

- [ ] **Step 1: Write the failing test**

```python
def test_closing_the_seasonal_segment_pushes_exits_into_sales():
    """§7.2 branch order, and the comparative static Catalonia dated for us.

    Seasonal is the cheap exit — it pays no transaction cost — so it is taken first.
    Closing the segment (Ley 11/2025, in force 1 Jan 2026) must therefore convert
    seasonal exits into sales, not into staying let. Incasòl measured the quarter:
    seasonal contracts −1,233, the first fall since the cap began.
    """
    open_ = _exit_destinations(_capped_state(cap_fraction_of_reservation=0.4))
    closed = _exit_destinations(_capped_state(cap_fraction_of_reservation=0.4, seasonal_closed=True))
    assert open_["seasonal"] > 0
    assert closed["seasonal"] == 0
    assert closed["sale"] > open_["sale"]
    assert "vacant" not in open_ and "vacant" not in closed
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_agents.py::test_closing_the_seasonal_segment_pushes_exits_into_sales -v`
Expected: FAIL — `_exit_destination` has no seasonal branch yet.

- [ ] **Step 3: Add the seasonal branch, first**

Insert at the top of `_exit_destination`, before the sale block:

```python
        # SEASONAL, evaluated FIRST because it is the cheap exit: diverting to a seasonal
        # contract pays no transaction cost and selling does. Closing the segment therefore
        # pushes exits into sales, which is the comparative static Ley 11/2025 dated.
        if not pol.seasonal_segment_capped and self.rng.random() < cfg.market.seasonal_evasion_share:
            return "seasonal"
```

- [ ] **Step 4: Delete `_exit` and the split parameters**

Remove `Landlord._exit` entirely; the call site now constructs `WithdrawRental` from `_exit_destination`'s return. Delete `exit_split_sale`, `exit_split_sale_range`, `exit_split_seasonal`, `exit_split_vacant` and `exit_split_evasion_base` from `CapResponseConfig`.

Verify the engine still handles the narrowed destination set: `engine.py` branches on `"sale"`, then `"seasonal"`, then `else: unit.withheld = True`. With no `"vacant"` destination the `else` becomes unreachable **from the cap channel**. Run `grep -rn "WithdrawRental(" src` and confirm whether any other producer still needs it. Leave the `else` in place if another producer exists; delete it only if none does.

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_agents.py -v && uv run pytest -q`

- [ ] **Step 6: Commit**

```bash
git add src/resim/agents/landlord.py src/resim/config.py tests/test_agents.py
git commit -m "feat(landlord): §7.2 branch order — seasonal first, vacancy as the sale channel's waiting state"
```

---

## Task 4: Retire the elasticity dial, and re-cut the UI

**Files:**
- Modify: `src/resim/config.py:607` (`MarketConfig.rental_supply_elasticity`)
- Modify: `src/resim/scenario.py:55-62` (`RentCap`)
- Modify: `src/resim/ui/levers.py:82-90`
- Modify: `src/resim/levers.py` (the claims-ledger runner, if it sets the elasticity)

**Interfaces:**
- Consumes: Tasks 2 and 3 — nothing reads `rental_supply_elasticity` once the hazard is gone.
- Produces: `RentCap(selling_cost_share=..., holding_years=...)` overrides replacing `supply_response_elasticity`. Task 6's test helpers call this signature.

- [ ] **Step 1: Delete the parameter and its scenario override**

Remove `rental_supply_elasticity` from `MarketConfig`. In `scenario.RentCap`, delete `supply_response_elasticity` and the `replace(cfg.market, ...)` line that consumes it; add optional `selling_cost_share: float | None = None` and `holding_years: float | None = None`, applied only when set.

- [ ] **Step 2: Re-cut the UI slider**

Replace the "Elasticidad de retirada de oferta" slider in `ui/levers.py` with two sliders over the structural parameters, carrying the dispute in their help text:

```python
        params["selling_cost_share"] = st.slider(
            "Coste de vender (fracción del precio)",
            0.01,
            0.12,
            0.02,
            0.01,
            help="Umbral de salida de §7.2: el casero vende cuando el déficit acumulado del "
            "alquiler topado supera este coste. Aranceles notariales y registrales, plusvalía "
            "municipal y comisión de agencia. Barato = salidas fáciles.",
        )
        params["holding_years"] = st.slider(
            "Horizonte de la decisión (años)",
            3.0,
            10.0,
            5.0,
            0.5,
            help="Sobre cuántos años suma el casero el déficit antes de decidir. Con estos "
            "dos se recorre el vano de Monràs (Δln contratos/Δln renta: OLS 0,07, IV 2,0), "
            "que el modelo ahora PRODUCE en vez de recibirlo como dial (model-spec §7.2).",
        )
```

- [ ] **Step 3: Verify nothing still reads the dial**

Run: `grep -rn "rental_supply_elasticity\|supply_response_elasticity" src tests docs`
Expected: hits only in documentation prose describing the retirement.

- [ ] **Step 4: Run the suite and the app**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format .`
Then: `uv run streamlit run src/resim/ui/app.py`, open the rent-cap lever, and confirm both sliders render and change the result.

- [ ] **Step 5: Commit**

```bash
git add src/resim/config.py src/resim/scenario.py src/resim/ui/levers.py src/resim/levers.py
git commit -m "feat(scenario,ui): retire the supply-elasticity dial; expose the two structural parameters"
```

---

## Task 5: Sensitivity harness

**Files:**
- Modify: `src/resim/sensitivity.py:16, 62, 199, 216, 370`

**Interfaces:**
- Consumes: the `CapResponseConfig` shape from Tasks 2 and 3.
- Produces: `holding_years` in the swept set; Task 7 reads the Sobol output.

- [ ] **Step 1: Swap the parameters**

Delete `"hazard_scale": (0.4, 1.2)` and its `dataclasses.replace` in `_config_for`, and the entry in the baseline recorder at line 370. Add `"holding_years": (3.0, 10.0)` with a `cap_response` replace, and confirm `selling_cost_share` keeps whatever range Task 0 produced.

- [ ] **Step 2: Update the module docstring**

Line 16 names `hazard_scale` as the example of a parameter that acts only through an intervention. Replace the example with `holding_years`, preserving the point.

- [ ] **Step 3: Smoke-run**

Run: `uv run python -m resim.sensitivity morris --jobs 10`
Expected: completes; `holding_years` appears in the ranking.

- [ ] **Step 4: Commit**

```bash
git add src/resim/sensitivity.py
git commit -m "chore(sensitivity): swap hazard_scale for holding_years in the swept set"
```

---

## Task 6: Rewrite the three gates for a world with no dial

**Files:**
- Modify: `tests/test_validation.py:858` (`test_rent_cap_lowers_contract_rents`), `:923` (`test_rent_cap_reproduces_the_monras_co_movement`), and the `_rent_cap_response` helper
- Modify: `tests/test_engine.py:316` (`test_cap_coverage_scales_the_rent_cap`)

**Interfaces:**
- Consumes: `RentCap(index_binds_all=..., selling_cost_share=..., holding_years=...)` from Task 4.
- Produces: `_rent_cap_response(*, index_binds_all, selling_cost_share=None, holding_years=None)` — the elasticity argument is gone.

- [ ] **Step 1: Change the helper's signature**

`_rent_cap_response(2.0, index_binds_all=True)` becomes `_rent_cap_response(index_binds_all=True)`, with optional structural overrides. Every call site updates.

- [ ] **Step 2: Restate the co-movement test as an emergence test**

```python
def test_rent_cap_reproduces_the_monras_co_movement():
    """Target 8, supply leg. Under §7.2 this measures something strictly stronger than it
    used to: the co-movement is no longer produced by a dial set to 2.0, it EMERGES from
    the arbitrage condition at the shipped structural parameters.

    Monràs & García-Montalvo: Δln contracts / Δln rent ≈ 2 — roughly −10% tenancies at −5%
    rents. Both halves are the claim; a model that sheds tenancies while rents RISE has
    reproduced one number and inverted the other.
    """
    response = _rent_cap_response(index_binds_all=True)
    assert response["leases"] < -0.09, f"quantity leg: {response['leases']:.1%}"
    assert -0.07 <= response["rent"] <= -0.03, f"price leg: {response['rent']:+.1%}"
```

- [ ] **Step 3: Add the F1 span test**

```python
def test_the_supply_elasticity_lands_inside_the_monras_span():
    """§7.2 F1. The elasticity is an OUTPUT now. Somewhere in the declared ranges of the
    two structural parameters the model must produce Δln contracts / Δln rent inside
    Monràs's own OLS-to-IV span of 0.07–2.0. If no corner reaches it, §7.2 is false and is
    NOT rescued by restoring a scale factor.
    """
    ratios = []
    for cost in (0.01, 0.12):
        for horizon in (3.0, 10.0):
            r = _rent_cap_response(
                index_binds_all=True, selling_cost_share=cost, holding_years=horizon
            )
            if r["rent"] < -0.001:
                ratios.append(r["leases"] / r["rent"])
    assert any(0.07 <= x <= 2.0 for x in ratios), f"no corner inside the span: {ratios}"
```

- [ ] **Step 4: Run the gates**

Run: `uv run pytest tests/test_validation.py -k rent_cap -v && uv run pytest tests/test_engine.py::test_cap_coverage_scales_the_rent_cap -v`
Record every measured value. **A failure here is F1 or F2 firing and is an outcome, not a bug to tune away.**

- [ ] **Step 5: Commit**

```bash
git add tests/test_validation.py tests/test_engine.py
git commit -m "test(rent-cap): the co-movement must emerge, not be dialled in"
```

---

## Task 7: Run F1–F3 under Ley 11/2020 and record

**Files:**
- Modify: `docs/validation.md`, `docs/model-spec.md` §7.2

**Interfaces:**
- Consumes: Tasks 1–6, and Task 0's band if it landed.
- Produces: the recorded F1–F3 verdicts that gate Task 8.

- [ ] **Step 1: Ten-seed run of the Ley 11/2020 regime**

Run: `uv run python -m resim.levers --jobs 10`
Record the rent leg, the lease leg and their ratio.

- [ ] **Step 2: Adjudicate F1**

Does the co-movement land inside 0.07–2.0 at some point in the declared ranges? Record the corner and the value. If not: **F1 has fired.** Write it up in `docs/validation.md` with the measured grid and stop — Task 8 does not run.

- [ ] **Step 3: Adjudicate F2**

Does reproducing the co-movement require `selling_cost_share` outside Task 0's sourced band? If yes, **F2 has fired**: the parameter is a fitted coefficient wearing a cost's clothes and must be declared as one, exactly as §5c.8 declared the sub-period count.

- [ ] **Step 4: Adjudicate F3**

Run the cap in a boom and in a flat market. If withdrawal is essentially nil in the boom because `min_required_yield` floors the required yield and collapses `r_req`, **F3 has fired**: a `[guess]` is governing the sign. Record it; the repair is to rebuild how E[g] enters `r_req`, not to retune the floor.

- [ ] **Step 5: Commit the record**

```bash
git add docs/validation.md docs/model-spec.md
git commit -m "docs(validation): §7.2 F1–F3 under Ley 11/2020"
```

---

## Task 8: Run F4 once, and register before touching anything

**Files:**
- Modify: `docs/validation.md`, `docs/claims.md`, `runs/` artefact

**Interfaces:**
- Consumes: green F1–F3 from Task 7. **Do not run this task if F1 fired.**
- Produces: the out-of-sample verdict on Ley 12/2023.

- [ ] **Step 1: Run the statute in force, ten seeds, once**

Run: `uv run python -m resim.levers --jobs 10`
Read the `rent-cap-state-law` entry.

- [ ] **Step 2: Compare against the in-regime span, and stop**

The span runs from the register (contracts +1,374; new-contract rent −2.7% real [O-HB no. 4]) to Pérez García (−13% tenancies, rent effect ≈0). Inside the span, or at least no longer a rent **rise**, is a pass.

**Write the result down before changing a single line.** Rewriting §7.2 in response to a failure here spends the Ley 12/2023 evidence exactly as 2008–13 was spent (§13.11), and from that point the statute in force can no longer validate this model.

- [ ] **Step 3: Commit the record**

```bash
git add docs/validation.md docs/claims.md
git commit -m "docs(validation): §7.2 F4, out of sample under Ley 12/2023"
```

---

## Task 9: Reporting status and the UI warning

**Files:**
- Modify: `src/resim/ui/levers.py:72` (the warning), `docs/model-spec.md` §5b.1 and §7.2, `docs/claims.md`

**Interfaces:**
- Consumes: Task 8's verdict.
- Produces: the final reporting status of the rent cap under Ley 12/2023.

- [ ] **Step 1: Set the status**

If F4 passed: the lever moves from **not reportable** to **direction** under §13.2 — not to magnitude, which the variance rule refuses while `holding_years` and, if Task 0 failed, `selling_cost_share` remain guesses. If F4 failed: the lever stays not reportable and the warning gains the new diagnosis.

- [ ] **Step 2: Rewrite the warning to match**

The current text says only what cannot be read. Replace it with what may be read and why, keeping the §-reference and the reading rule ("léase el signo, no el número") only if the status still requires it.

- [ ] **Step 3: Update §5b.1's closing sentence**

It currently says re-identifying the hazard "is the one piece of rent-cap work this project leaves open", amended to point at §7.2. Restate it in the past tense with the outcome.

- [ ] **Step 4: Full verification**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format .`
Then open the app and read the rent-cap panel end to end.

- [ ] **Step 5: Commit**

```bash
git add src/resim/ui/levers.py docs/model-spec.md docs/claims.md
git commit -m "docs(ui,spec): the rent cap's reporting status after §7.2"
```

---

## Self-Review

**Spec coverage.** §7.2's condition → Task 1. Sale rule and the widening shortfall → Task 2. Branch order, seasonal-first, vacancy as waiting state → Task 3. Parameter ledger: `hazard_scale` → Task 2; the three `exit_split_*` and `exit_split_evasion_base` → Task 3; `rental_supply_elasticity` → Task 4; sensitivity roles → Task 5. Sources (`selling_cost_share` pending, `holding_years` bounded) → Task 0. F1/F2/F3 → Task 7; F4 and the spend clause → Task 8. Scope boundary → respected: no task touches `cap_level`, coverage, `magnet_gain`, compliance or the sale channel downstream of `WithdrawRental`. Reporting consequence → Task 9.

**Known gap, deliberate.** §7.2 says the share of withdrawn units standing empty becomes a model output to be checked. No task checks it against a number, because none is registered in `docs/sources.md`. Task 3 asserts the mechanism produces it; quantifying it is future evidence work, not part of this plan.

**Type consistency.** `_exit_destination(unit, state, *, cap, r_req, value) -> str | None` is defined in Task 2 and extended in Task 3 with the same signature. `_rent_cap_response(*, index_binds_all, selling_cost_share=None, holding_years=None)` is defined in Task 6 Step 1 and used in Steps 2 and 3. `RentCap`'s new optional fields are named identically in Tasks 4 and 6.

**Placeholder scan.** No TBDs. Task 0's "if the evidence says so" is a declared branch with both outcomes specified, not an unfinished step.
