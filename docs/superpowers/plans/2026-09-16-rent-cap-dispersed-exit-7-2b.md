# §7.2b Dispersed, Time-Limited Withdrawal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Break the scale-invariance of the rent cap's exit decision, so withdrawal sweeps a distribution of landlords instead of switching on for all of them at once.

**Architecture:** Two pieces. **A** gives the exit cost to the landlord: a persistent per-unit U(0,1) draw, the sibling of `Unit.declaration_draw`, mapped monotonically onto an exit cost `k` so private sellers leave first and agency sellers hold out. **B** gives the cap a statutory life: a three-year declared term over which the shortfall accrues, replacing the `[guess]` `holding_years`, with renewal the landlord does not anticipate. B brings the two scales together; A separates the landlords.

**Tech Stack:** Python 3.14 (min 3.12), numpy, pandas, Streamlit, pytest, ruff, uv.

**Spec:** `docs/model-spec.md` §7.2b "The withdrawal margin, dispersed and time-limited (2026-09-16)". Read §7.2 immediately above it for what failed and why, and the §7.2b entries in `docs/validation.md` for the measurements.

## Global Constraints

- All randomness flows from the seeded `Generator` passed down from the engine. No module-level `random` or `np.random`.
- Agents are read-only on state: `decide()` returns intents; the engine and `market/clearing.py` are the only writers.
- Typed dataclasses for config, scenario, state and intents. No dicts as informal records.
- Parameters carry units and a source in the `config.py` comment. An unsourced parameter is labelled `[guess]`.
- Retired parameters keep dated historical notes rather than being erased.
- **Nothing may be re-fitted, loosened, re-banded, xfail-marked or skipped to make a calibration target pass.** Four tests are currently red on purpose — the recorded falsification of §7.2. They are expected to go GREEN if §7.2b works, but only by the mechanism, never by an edited assertion.
- `-q` on pytest is swallowed by this environment's hook; use `rtk proxy uv run pytest ...` for real output.
- Commands: `uv run pytest`, `uv run ruff check . && uv run ruff format .`.

---

## File Structure

| File | Responsibility after this plan |
|---|---|
| `src/resim/market/stock.py` | `Unit` gains `sale_route_draw`, the persistent route draw. |
| `src/resim/engine.py` | Populates the new draw at all four unit-creation sites. |
| `src/resim/config.py` | `CapResponseConfig` gains the intermediation share and the two exit-cost bands, loses `holding_years`. `PolicyConfig` gains `cap_start_tick` and `cap_term_ticks`. |
| `src/resim/agents/landlord.py` | `exit_cost_for(unit, cfg)` maps the draw to `k`; `_exit_destination` uses it and the remaining term. |
| `src/resim/scenario.py` | `RentCap` records its start tick and term; drops the `holding_years` override. |
| `src/resim/sensitivity.py` | Swaps `holding_years` for `intermediation_share`. |
| `src/resim/ui/levers.py` | The agency-share slider replaces the two structural ones. |
| `tests/test_agents.py` | Unit tests for the map's monotonicity and the term countdown. |
| `tests/test_validation.py` | G1–G4. |

---

## Task 1: The measurement gate — is `cap / r_req` actually uniform within a zone?

**Everything below depends on this.** §7.2b's diagnosis is that the exit decision is scale-invariant because `cap` and `r_req` both scale with `quality`, so every unit in a zone crosses the threshold together. **That was deduced from reading the code and has never been measured.** If the ratio is already well dispersed, the step function has some other cause and Pieces A and B repair nothing.

**Files:**
- Create: `tests/test_agents.py::test_the_cap_to_reservation_ratio_is_near_uniform_within_a_zone`

**Interfaces:**
- Consumes: `agents.landlord.required_rent(state, zone, value)` and `agents.landlord.cap_level(...)`, both already exported.
- Produces: the measured coefficient of variation of `cap / r_req`, which Task 5's G4 compares against.

- [ ] **Step 1: Write the measuring test**

```python
def test_the_cap_to_reservation_ratio_is_near_uniform_within_a_zone():
    """§7.2b's premise, measured rather than assumed.

    §7.2b claims the exit decision is scale-invariant: `cap` and `r_req` both scale with
    `Unit.quality`, so `cap / r_req` is near-identical across a zone's units and crosses 1
    for all of them at once. If that is false, the dispersion §7.2b adds is repairing the
    wrong thing. Asserted as a coefficient of variation below 0.10 — tight enough that no
    meaningful share of units sits on the other side of the threshold from the rest.
    """
    state, _ = _capped_state(cap_ratio=0.8)
    ratios = []
    for unit in state.stock.units.values():
        if unit.zone is not ZoneType.TENSIONED:
            continue
        value = state.zones[unit.zone].price_index * unit.quality
        r_req = required_rent(state, unit.zone, value)
        cap = cap_level(
            state, unit.zone, unit.quality,
            previous_rent=unit.rent or unit.last_contract_rent, large_holder=False,
        )
        if cap is None or r_req <= 0:
            continue
        ratios.append(cap / r_req)
    assert len(ratios) > 50, f"too few capped units to measure: {len(ratios)}"
    mean = sum(ratios) / len(ratios)
    sd = (sum((x - mean) ** 2 for x in ratios) / (len(ratios) - 1)) ** 0.5
    cv = sd / mean
    assert cv < 0.10, f"cap/r_req is NOT near-uniform: cv={cv:.3f}, mean={mean:.3f}"
```

- [ ] **Step 2: Run it and record the number, whichever way it goes**

Run: `rtk proxy uv run pytest tests/test_agents.py::test_the_cap_to_reservation_ratio_is_near_uniform_within_a_zone -v`

**This is a gate, not a test to make pass.** Record the measured `cv` and `mean`.

- **If `cv < 0.10`:** the premise holds. Continue to Task 2.
- **If `cv >= 0.10`:** **STOP THE PLAN.** The diagnosis in §7.2b is wrong, the step function has another cause, and Tasks 2–6 would build on a false premise. Report the measured value and the distribution's shape, and do not proceed.

Run it under Ley 11/2020 (`index_binds_all=True`) — that is the identifying regime, and the one where the index binds everyone and the invariance claim is strongest.

- [ ] **Step 3: Commit the gate**

```bash
git add tests/test_agents.py
git commit -m "test(landlord): measure §7.2b's scale-invariance premise before building on it"
```

---

## Task 2: The exit cost belongs to the landlord

**Files:**
- Modify: `src/resim/market/stock.py` (`Unit`)
- Modify: `src/resim/engine.py` (four creation sites: around lines 186, 240, 259, 1093)
- Modify: `src/resim/config.py` (`CapResponseConfig`)
- Modify: `src/resim/agents/landlord.py`
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: Task 1's confirmed premise.
- Produces: `Unit.sale_route_draw: float` and `agents.landlord.exit_cost_for(unit, cfg) -> float`. Task 3 calls `exit_cost_for`; Task 5's G2 sweeps the share it reads.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_exit_cost_map_is_monotone_in_the_draw():
    """§7.2b Piece A. `k` must increase with the draw, so raising the cap's bite ADDS
    landlords to the exiting set rather than reshuffling it — the same monotonicity
    `declaration_draw`'s comment prizes for coverage, and for the same reason: two cap
    scenarios have to stay comparable.
    """
    cfg = SimConfig.baseline(seed=1, ticks=4)
    ks = [exit_cost_for(_unit_with_draw(u), cfg) for u in (0.0, 0.2, 0.4, 0.6, 0.8, 0.99)]
    assert ks == sorted(ks), f"not monotone: {ks}"

def test_the_exit_cost_map_lands_in_the_two_sourced_bands():
    """Private sales 0.005–0.015 (Código Civil art. 1455, IIVTNU, aranceles); agency sales
    0.04–0.07 (commission 3–5% + IVA). The share on the agency side is the measured
    intermediation share, 0.64 of second-hand purchases [Fotocasa Research].
    """
    cfg = SimConfig.baseline(seed=1, ticks=4)
    s = cfg.cap_response.intermediation_share
    private = [exit_cost_for(_unit_with_draw(u), cfg) for u in (0.0, (1 - s) * 0.99)]
    agency = [exit_cost_for(_unit_with_draw(u), cfg) for u in (1 - s, 0.999)]
    assert all(0.005 <= k <= 0.015 for k in private), private
    assert all(0.04 <= k <= 0.07 for k in agency), agency
```

Add `_unit_with_draw(u)` beside `_capped_state` in `tests/test_agents.py`: it builds a minimal `Unit` with `sale_route_draw=u` and whatever other fields the dataclass requires.

- [ ] **Step 2: Run them and watch them fail**

Run: `rtk proxy uv run pytest tests/test_agents.py -k exit_cost -v`
Expected: FAIL — neither the field nor the function exists.

- [ ] **Step 3: Add the persistent draw**

In `src/resim/market/stock.py`, beside `declaration_draw`:

```python
    # U(0,1) drawn once from the engine's seeded Generator when the unit is created, and never
    # redrawn. Maps to the landlord's cost of LEAVING the rental market (model-spec §7.2b):
    # a private sale is cheap, an agency sale is not, and a landlord's route is a property of
    # the landlord rather than of the quarter. Persistent for the same reason
    # `declaration_draw` is: a per-tick coin flip would let the same unit cross the exit
    # threshold and come back, and would stop two cap scenarios being comparable.
    sale_route_draw: float = 1.0
```

Then add `sale_route_draw=float(rng.random())` at each of the four creation sites in `engine.py`. Use the same generator each site already uses for `declaration_draw` — `rng` at three of them, `self.market_rng` at the fourth.

- [ ] **Step 4: Add the sourced parameters**

In `CapResponseConfig`:

```python
    # Share of dwelling sales that go through an agency, which decides how many landlords have
    # a CHEAP exit and therefore how many leave at a given cap (model-spec §7.2b). Agencies
    # handle 64% of SECOND-HAND purchases [Fotocasa Research] and ~70% of all operations
    # [idealista] — two portals competing for the same sellers, agreeing within 6pp. The model
    # takes the second-hand figure: a landlord selling a let dwelling makes a second-hand sale.
    # Regional spread is wide (Murcia, Navarra, Baleares high; Extremadura, País Vasco,
    # Andalucía low), which is why the UI slider is wider than this band.
    intermediation_share: float = 0.64
    intermediation_share_range: tuple[float, float] = (0.64, 0.70)
    # The two sale routes, as shares of price. Statutory: CC art. 1455 puts the escritura
    # matriz on the seller, IIVTNU falls on the transmitente but is levied on cadastral LAND
    # value, plus aranceles RD 1426/1989 and RD 1427/1989. Market: commission 3–5% + IVA, so a
    # 4% fee costs 4.84% of price; large networks reach 7%. Uniform within band is a declared
    # convention — the sources give ranges, not distributions.
    exit_cost_private: tuple[float, float] = (0.005, 0.015)
    exit_cost_agency: tuple[float, float] = (0.04, 0.07)
```

- [ ] **Step 5: Write the map**

In `src/resim/agents/landlord.py`:

```python
def exit_cost_for(unit: Unit, cfg: SimConfig) -> float:
    """The landlord's cost of leaving, as a share of the dwelling's value (model-spec §7.2b).

    Monotone in `unit.sale_route_draw`: the cheap-to-extract private sellers sit at the bottom
    and leave first, agency sellers at the top and hold out longest. Monotonicity is the point —
    it makes a harder cap ADD landlords to the exiting set instead of reshuffling it.
    """
    c = cfg.cap_response
    s = c.intermediation_share
    u = unit.sale_route_draw
    if u < 1.0 - s:
        lo, hi = c.exit_cost_private
        frac = u / (1.0 - s) if s < 1.0 else 0.0
    else:
        lo, hi = c.exit_cost_agency
        frac = (u - (1.0 - s)) / s if s > 0.0 else 0.0
    return lo + (hi - lo) * frac
```

- [ ] **Step 6: Run the tests**

Run: `rtk proxy uv run pytest tests/test_agents.py -v && rtk proxy uv run pytest`
The four red gates may move. **Record what you measure; repair nothing.**

- [ ] **Step 7: Commit**

```bash
git add src/resim/market/stock.py src/resim/engine.py src/resim/config.py src/resim/agents/landlord.py tests/test_agents.py
git commit -m "feat(landlord): §7.2b piece A — the exit cost belongs to the landlord"
```

---

## Task 3: The cap has a statutory life

**Files:**
- Modify: `src/resim/config.py` (`PolicyConfig`, `CapResponseConfig`)
- Modify: `src/resim/scenario.py` (`RentCap`)
- Modify: `src/resim/agents/landlord.py` (`_exit_destination`)
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes: `exit_cost_for` from Task 2.
- Produces: `PolicyConfig.cap_start_tick`, `PolicyConfig.cap_term_ticks`, and the remaining-term term inside `_exit_destination`. Task 4 retires `holding_years` on top of this.

- [ ] **Step 1: Write the failing test**

```python
def test_withdrawal_tapers_as_the_declared_term_runs_out():
    """§7.2b Piece B. The shortfall accrues over the ticks left in the CURRENT declared term,
    so nobody sells to escape a cap about to lapse. ZMRT are declared for three years and
    renewed; the landlord does not anticipate the renewal, which is the friction.
    """
    early = _exit_share_at_tick(cap_ratio=0.6, ticks_into_term=1)
    late = _exit_share_at_tick(cap_ratio=0.6, ticks_into_term=11)
    assert early > late, f"no taper: early={early:.3f} late={late:.3f}"
```

`_exit_share_at_tick` builds a capped state with `PolicyConfig.cap_start_tick` set so the unit sits the given number of ticks into a 12-tick term, then returns the share of 200 `decide()` draws that produce a `WithdrawRental`.

- [ ] **Step 2: Run it and watch it fail**

Run: `rtk proxy uv run pytest tests/test_agents.py::test_withdrawal_tapers_as_the_declared_term_runs_out -v`
Expected: FAIL — the shortfall still uses `holding_years` and does not know the tick.

- [ ] **Step 3: Add the term to the policy**

In `PolicyConfig`:

```python
    # The tick the current cap term was declared, and its statutory length. ZMRT are declared
    # for THREE YEARS and renewable (MIVAU's compiled table gives vigencia inicio–fin for all
    # 317 municipalities), so a landlord's shortfall accrues over what is left of the current
    # term, not over a holding horizon. The statute renews — Catalonia extended 302
    # municipalities to 2027 — so the term resets rather than the cap lapsing, and the
    # landlord does NOT anticipate that renewal: model-spec §7.2b, and that is the friction.
    cap_start_tick: int = -1
    cap_term_ticks: int = 12
```

In `RentCap.apply`, pass `cap_start_tick=self.start_tick` and `cap_term_ticks=self.term_ticks` through `with_policy`, adding `term_ticks: int = 12` to the `RentCap` dataclass.

- [ ] **Step 4: Use the remaining term in the shortfall**

In `_exit_destination`, replace the `holding_years` horizon:

```python
        # §7.2b: the shortfall accrues over what is LEFT of the current declared term, not
        # over a holding horizon. Terms repeat because the statute is renewed; the landlord
        # discounts only the term it can see.
        elapsed = max(0, state.tick - pol.cap_start_tick)
        remaining_ticks = pol.cap_term_ticks - (elapsed % pol.cap_term_ticks)
        horizon = remaining_ticks / TICKS_PER_YEAR
        shortfall = (r_req - cap) * 12.0 * horizon * (1.0 + horizon * growth_wedge / 2.0)
        if shortfall > value * exit_cost_for(unit, cfg):
            return "sale"
        return None
```

Confirm `state.tick` exists on `WorldState`; if the attribute has another name, use that one and say so in your report.

- [ ] **Step 5: Run the tests**

Run: `rtk proxy uv run pytest tests/test_agents.py -v && rtk proxy uv run pytest`

- [ ] **Step 6: Commit**

```bash
git add src/resim/config.py src/resim/scenario.py src/resim/agents/landlord.py tests/test_agents.py
git commit -m "feat(landlord): §7.2b piece B — the cap has a statutory life"
```

---

## Task 4: Retire `holding_years`

**Files:**
- Modify: `src/resim/config.py` (`CapResponseConfig`)
- Modify: `src/resim/scenario.py` (`RentCap`)
- Modify: `src/resim/sensitivity.py`
- Modify: `src/resim/ui/levers.py`

**Interfaces:**
- Consumes: Task 3's remaining-term horizon, which is what replaced it.
- Produces: an `intermediation_share` entry in the swept set, and the agency-share slider Task 5's G2 exercises.

- [ ] **Step 1: Delete the parameter and its overrides**

Remove `holding_years` and `holding_years_range` from `CapResponseConfig`, keeping the historical comment as a dated note ending in a pointer to §7.2b. Remove the `holding_years` override from `RentCap` and its branch in `apply`.

- [ ] **Step 2: Swap the swept parameter**

In `sensitivity.py`, delete the `holding_years` entry and its `dataclasses.replace`, and add `"intermediation_share": (0.40, 0.85)` with the corresponding `cap_response` replace — the WIDE range, because G2 sweeps beyond the two national sources for the reason the spec gives.

- [ ] **Step 3: Re-cut the UI**

Replace both structural sliders with one:

```python
        params["intermediation_share"] = st.slider(
            "Caseros que venden por agencia",
            0.40,
            0.85,
            0.64,
            0.01,
            help="Decide cuántos caseros tienen una salida BARATA, y con ello cuántos se "
            "retiran ante un tope dado (model-spec §7.2b). Medido: las agencias intermedian "
            "el 64% de las compraventas de segunda mano (Fotocasa) y ~70% del total "
            "(idealista). El rango va más allá de esas dos fuentes a propósito, porque la "
            "dispersión regional es grande — Murcia, Navarra y Baleares arriba; Extremadura, "
            "País Vasco y Andalucía abajo. Es el dial que recorre el vano de Monràs "
            "(Δln contratos/Δln renta: OLS 0,07, IV 2,0).",
        )
```

Add the matching `intermediation_share: float | None = None` override to `RentCap` and apply it when set.

- [ ] **Step 4: Verify nothing still reads the retired parameter**

Run: `grep -rn "holding_years" src tests`
Expected: hits only in dated retirement comments.

Run: `rtk proxy uv run pytest && uv run ruff check . && uv run ruff format .`
Then confirm the app starts: `uv run streamlit run src/resim/ui/app.py`.

- [ ] **Step 5: Commit**

```bash
git add src/resim/config.py src/resim/scenario.py src/resim/sensitivity.py src/resim/ui/levers.py
git commit -m "chore: retire holding_years, replaced by the statutory term"
```

---

## Task 5: G1–G4

**Files:**
- Modify: `tests/test_validation.py`

**Interfaces:**
- Consumes: `RentCap(intermediation_share=...)` from Task 4 and `_rent_cap_response` as it stands.
- Produces: the four gates §7.2b is judged on.

- [ ] **Step 1: Write G1 — the co-movement at the SHIPPED parameters**

```python
def test_g1_the_co_movement_emerges_at_the_shipped_parameters():
    """§7.2b G1, deliberately stricter than the F1 it replaces. §7.2's F1 asked only for a
    witness somewhere in the declared ranges, and passed at ONE corner while three inverted
    the sign. G1 requires the rent sign right at the shipped values, with Δln contracts /
    Δln rent inside Monràs's 0.07–2.0 OLS-to-IV span.
    """
    r = _rent_cap_response(index_binds_all=True, seeds=tuple(range(1, 11)))
    assert r["rent"] < 0, f"rent sign wrong at the shipped parameters: {r['rent']:+.1%}"
    ratio = math.log1p(r["leases"]) / math.log1p(r["rent"])
    assert 0.07 <= ratio <= 2.0, f"co-movement outside Monràs's span: {ratio:.3f}"
```

- [ ] **Step 2: Write G2 — the intermediation share must move withdrawal**

```python
def test_g2_the_intermediation_share_moves_withdrawal():
    """§7.2b G2. If sweeping the agency share does not move the supply response, Piece A is
    decorative and the dispersion is not doing the work the section claims for it.
    """
    low = _rent_cap_response(index_binds_all=True, intermediation_share=0.40)
    high = _rent_cap_response(index_binds_all=True, intermediation_share=0.85)
    assert abs(low["leases"] - high["leases"]) > 0.02, (
        f"withdrawal is insensitive to the agency share: {low['leases']:.1%} vs {high['leases']:.1%}"
    )
```

Extend `_rent_cap_response` with an `intermediation_share: float | None = None` parameter, passed through to `RentCap`.

- [ ] **Step 3: Write G3 — withdrawal is front-loaded within a term**

```python
def test_g3_withdrawal_is_front_loaded_within_the_declared_term():
    """§7.2b G3. Withdrawal must concentrate after each declaration and taper toward expiry —
    nobody sells to escape a cap about to lapse. Flat withdrawal means the statutory term is
    inert. Contrastable against Incasòl's quarterly counts.
    """
    per_tick = _withdrawals_per_tick(index_binds_all=True, start_tick=20, ticks=44)
    first_half = sum(per_tick[20:26])
    second_half = sum(per_tick[26:32])
    assert first_half > second_half, f"no taper within the term: {first_half} vs {second_half}"
```

`_withdrawals_per_tick` runs one capped scenario and returns the per-tick count of `WithdrawRental` intents; add it beside `_rent_cap_response`, reading the counts from the metrics frame if one exists for withdrawals, and otherwise from a counter the engine already keeps — say which you used.

- [ ] **Step 4: Write G4 — the regime boundary must be gone**

```python
def test_g4_the_growth_anchor_no_longer_flips_the_sign():
    """§7.2b G4, the direct test that this section did what it was written to do. Before
    §7.2b the ten-seed anchor sweep gave 0/10 seeds with the rent sign right below 4%/yr and
    10/10 above — a step function relocated, not removed, by the anchor. The table is in
    docs/validation.md. If the boundary survives, the dispersion is too narrow for the
    shortfall it faces.
    """
    for anchor in (0.0025, 0.0050, 0.0100, 0.0200):
        r = _rent_cap_response(index_binds_all=True, long_run_growth=anchor)
        assert r["rent"] < 0, f"rent sign still flips at anchor {anchor}: {r['rent']:+.1%}"
```

Extend `_rent_cap_response` with a `long_run_growth: float | None = None` parameter that replaces `MarketConfig.long_run_growth` when set.

- [ ] **Step 5: Run the four gates and record every number**

Run: `rtk proxy uv run pytest tests/test_validation.py -k "g1 or g2 or g3 or g4" -v`

**A failure here is a result, not a bug to tune away.** Record what each measured.

- [ ] **Step 6: Commit**

```bash
git add tests/test_validation.py
git commit -m "test(rent-cap): G1–G4, the falsifications §7.2b declared"
```

---

## Task 6: Run the three Ley 11/2020 gates and record the outcome

**Files:**
- Modify: `docs/validation.md`, `docs/model-spec.md` §7.2b

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces: the recorded verdict on §7.2b.

- [ ] **Step 1: Run the full suite**

Run: `rtk proxy uv run pytest`

The four tests red since §7.2 — `test_cap_coverage_scales_the_rent_cap`, `test_shadow_rent_stays_anchored_under_a_cap`, `test_rent_cap_lowers_contract_rents`, `test_rent_cap_reproduces_the_monras_co_movement` — are expected to go GREEN if §7.2b works. **If they do, verify it is the mechanism and not an edited assertion: `git diff main -- tests/` must show no threshold, band or comparison-direction change on any of the four.**

- [ ] **Step 2: Record the verdict**

Write the outcome into `docs/validation.md` and into §7.2b: G1–G4's measured values, the state of the four gates, and — if the rent sign corrects but the magnitude stays far from Monràs's −5% — that finding registered separately, as §7.2b's falsification section requires.

- [ ] **Step 3: Commit**

```bash
git add docs/validation.md docs/model-spec.md
git commit -m "docs(validation): §7.2b's verdict"
```

---

## Self-Review

**Spec coverage.** Scale-invariance premise → Task 1 (as a gate). Piece A, the persistent draw and monotone map → Task 2. Piece B, the statutory term and the landlord's myopia about renewal → Task 3. Parameter ledger: `holding_years` retired → Task 4; the three new sourced parameters → Task 2 (share and bands) and Task 3 (term). UI → Task 4. Sources → carried in the config comments written in Tasks 2 and 3. G1–G4 → Task 5. Reporting outcome → Task 6.

**Deliberate gap.** §7.2b says the rent MAGNITUDE is out of scope — it attacks who exits, not the size of the price response. No task targets the magnitude, and Task 6 Step 2 requires it be registered separately if it survives. That is the spec's instruction, not an omission.

**Type consistency.** `exit_cost_for(unit, cfg) -> float` is defined in Task 2 Step 5 and called in Task 3 Step 4 with the same signature. `PolicyConfig.cap_start_tick` / `cap_term_ticks` are defined in Task 3 Step 3 and read in Step 4. `_rent_cap_response` gains three optional parameters across Task 5 — `intermediation_share`, `long_run_growth` — each added in the step that first uses it. `RentCap.term_ticks` (Task 3) and `RentCap.intermediation_share` (Task 4) are both applied in `apply`.

**Placeholder scan.** No TBDs. Task 1's two branches are both fully specified, including the instruction to stop the plan.
