# Experiment 1 — rent cap (Phase 7)

> **Status 2026-09-15: re-run on the current model, and the Phase-7 credibility gate is NO
> LONGER MET.** Everything below the "Provenance" rule near the end is superseded. The gate
> asked whether one exposed parameter can span the three Catalan studies; with the cap split
> into the two statutes Spain actually has (`model-spec §5b.1`), it cannot. The reason is
> identified and is not the behaviour dial: under the law those studies evaluate, the rent leg
> is set by **how far the reference index sits below market**, and moves 0.8pp across the
> whole elasticity range. This file records that rather than the previous "gate met".

## Design

- Baseline vs `RentCap(start_tick=20, cap_reference_discount=0.05, compliance=0.85)` on the
  tensioned-metro zone, 40 ticks, **ten seeds**, outcomes averaged over the 16 post-cap ticks
  (≈4 years). Ten seeds since `model-spec §13.4`; the original ran three.
- The exposed disagreement parameter `supply_response_elasticity ∈ {0, 0.5, 1, 1.5, 2}`.
- **Both statutory regimes**, because they are different instruments (`model-spec §5b.1`):
  - **Ley 11/2020** (Catalonia 2020–22, `index_binds_all=True`) — the reference index binds
    every landlord. *This is the world the three studies measure.*
  - **Ley 12/2023** (in force, the model's default) — the index binds grandes tenedores; every
    other landlord is held to its own previous contract plus IRAV, or to nothing where there is
    no contract in the last five years. Individuals hold 85–92% of the Spanish rental stock.
- **Not pre-registered.** The predictions for this re-run were not written down first, because
  the levers sweep had already been run when the regime split landed (`docs/prereg/`). It is a
  re-measurement of a registered experiment, and it is labelled as one.

## Results — Ley 11/2020, the regime the studies evaluate (10 seeds)

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | Δ sale prices | Δ overburden | seasonal units gained |
|---|---|---|---|---|---|---|
| 0.0 | −19.3% | −17.7% | **+20.9%** | −2.9% | −1.4% | 0 |
| 0.5 | −19.3% | −17.6% | +8.6% | −3.5% | −1.0% | +20 |
| 1.0 | −19.3% | −17.6% | −11.2% | −3.5% | −1.3% | +41 |
| 1.5 | −19.3% | −17.5% | −32.3% | −3.6% | −0.8% | +62 |
| 2.0 | −18.5% | −16.8% | **−49.4%** | −3.6% | −0.4% | +74 |

Contract rents fall 10/10 seeds at every setting. **The rent leg is flat**: 0.8pp across the
whole dial, because under this statute the cap level is the reference index and the index is
not behavioural. The quantity leg is the dial: +21% to −49%.

## Results — Ley 12/2023, the law in force (10 seeds)

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | Δ sale prices | Δ overburden | seasonal units gained |
|---|---|---|---|---|---|---|
| 0.0 | −3.5% (8/10 down) | −13.3% | +9.0% | −3.1% | −2.5% | 0 |
| 0.5 | −1.9% (6/10) | −10.9% | +4.1% | −3.5% | −2.1% | +12 |
| 1.0 | −0.3% (3/10) | −7.9% | −2.7% | −3.4% | −2.3% | +26 |
| 1.5 | +3.2% (2/10) | −3.3% | −11.8% | −3.7% | −2.6% | +40 |
| 2.0 | **+7.6%** (1/10) | +3.0% | −21.8% | −3.4% | −2.1% | +50 |

Here the rent leg is the dial and it **crosses zero**: with the index binding one landlord in
ten, withdrawal outruns the cap somewhere around elasticity 1. **These numbers are not
reportable** (`model-spec §5b.1`): the exit hazard behind them was identified when the index
bound every landlord, and nothing has re-identified it for a regime where it binds a tenth of
the market. They are published because the gap between the two columns *is* the finding.

## Credibility gate (plan.md Phase 7): does one parameter span the three studies?

| Study | What it found | Where the model puts it |
|---|---|---|
| Jofre-Monseny, Martínez-Mazza & Segú (2023) | rents −4/−5%, **no** supply effect | Ley 11/2020: nowhere — rents −19% at every setting. Ley 12/2023 at ε≈0: **−3.5% rents, +9% tenancies** ✓ but under the wrong statute |
| Monràs & García-Montalvo (2022/23) | rents −5%, new contracts −10% | Ley 11/2020 at ε≈1 gets the contracts (−11.2%) and misses the rents by 4× (−19.3%). Ley 12/2023 gets neither pair jointly ✗ |
| Pérez García (2026) | contracts −13%, price effect not robust | Ley 12/2023 at ε≈1.5: **−11.8% contracts, +3.2% rents (2/10 down)** ✓ |

**Verdict: the gate is not met.** Within the statute the studies evaluate, one parameter spans
their *quantity* findings and none of their *price* findings; the price leg is pinned by the
cap's level. Two of the three can be reproduced under the current statute, which is not
evidence about the one they measured.

What closes it is named and is not this experiment's to fix: the model's reference index sits
**16% below market rents at activation**, against published implied cuts of −10…−15% for the
Catalan index and −20% on average for the state one. Calibrating that distance per regime is a
§5b specification decision, and until it is made the *size* of any rent-cap rent effect in this
model should not be quoted — only its sign and its ordering.

## Side effects, emergent and not imposed anywhere

- **Evasion into the seasonal segment scales with the dial** in both regimes: +74 units in the
  tensioned zone at ε=2 under Ley 11/2020, +50 under the current law. Nobody wrote a rule
  saying landlords flee to temporary lets; it falls out of the exit split.
- **Sale prices fall ≈3–3.6% under both regimes and at every elasticity** — the one leg that
  is insensitive to both the statute and the dial. Capped rents lower the landlord's
  reservation value, and the sale side inherits it through §7.1.
- **Overburden barely moves** (−0.4% to −2.6%): the tenants who keep a tenancy pay less, the
  ones who lose one leave the denominator. A cap that improves affordability for insiders is
  not the same as one that improves it on average, and the model separates them.
- **Ownership rises** ≈1.2–1.5% (10/10 seeds) as frustrated renters buy — reported in
  `docs/claims.md` F-5.

## Regenerate

```
uv run python -m resim.levers --jobs 10            # the ledger's rent-cap rows, both regimes
# the dial in this file: scratch sweep over supply_response_elasticity × index_binds_all,
# 10 seeds × 40 ticks, cached to runs/rentcap_dial_10seeds.json
```

---

## Provenance — superseded measurements below this line

### (2026-08-07 → 2026-09-08 passes, kept for provenance only)

## Design

- Baseline vs `RentCap(start_tick=20, cap_reference_discount=0.05, compliance=0.85)`
  applied to the tensioned-metro zone (the CCAA-declaration step).
- Sweep of the single exposed disagreement parameter
  `supply_response_elasticity ∈ {0, 0.5, 1, 1.5, 2}` × seeds {1, 2, 3}, 40 ticks,
  outcomes averaged over the 16 post-cap ticks (~4 years), tensioned zone only.

## Results (mean over 3 seeds)

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | seasonal units gained | Δ sale prices |
|---|---|---|---|---|---|
| 0.0 | −4.1% | −3.5% | **+2.3%** | 0 | −0.3% |
| 0.5 | −4.1% | −3.3% | −0.4% | +15 | −1.3% |
| 1.0 | −4.1% | −3.3% | −4.8% | +26 | −1.9% |
| 1.5 | −4.1% | −3.2% | −6.8% | +33 | −4.0% |
| 2.0 | −4.1% | −3.2% | **−9.4%** | +47 | −4.1% |

## Credibility test (plan.md Phase 7 gate): does one parameter span the three studies?

- **Jofre-Monseny, Martínez-Mazza & Segú (2023)** — rents −4/−5%, *no* supply effect:
  reproduced at elasticity ≈ 0 (−4.1% rents, tenancies ≈ +2%). ✓
- **Monràs & García-Montalvo (2022/23)** — rents −5%, new contracts −10%: reproduced at
  elasticity ≈ 2 (−4.1% rents, −9.4% tenancies). ✓
- **Pérez García (2026)** — quantity effect robust (−13% tenancies), price effect not:
  the quantity side is approached at elasticity 2 (−9.4%; the raw Barcelona −17…−21%
  includes demand-side confounds the study itself flags). The "no robust price effect"
  world corresponds to low `compliance` (~0.25) or `cap_reference_discount` ≈ 0 —
  a second dial, as in the study's reading that enforcement/bindingness was weak. ~✓

**Gate passed** with one honest caveat: Pérez García's full −13% needs elasticity ≈ 2.7
under this mapping — inside his own "elasticity > 2" reading but outside the 0–2 UI
range; documented rather than tuned away.

## Emergent side effects (not imposed anywhere)

- **Seasonal-segment evasion**: capped landlords shift units to the uncapped seasonal
  segment, scaling with elasticity (0 → 47 units ≈ 2–4% of the zone's rental stock over
  4 years; Catalonia observed 6.1% → 11% of contracts in 1 year — same order).
- **Sale-price dip** (−2…−4% at high elasticity): exited units are sold to
  owner-occupiers, echoing the tenure-shift channel in Diamond–McQuade–Qian (SF) and
  the piso-a-piso exits in investor-large §3.
- **Asking rents fall slightly less than contract rents** — the compliant segment
  transacts at the cap while asks stay above it.

## Interpretation (conditional, per the bias-control rule)

Under assumption set A (elasticity ≈ 0 — Jofre-Monseny world): the cap delivers
−4% rents with no measurable supply loss: tenants gain, evasion minimal.
Under assumption set B (elasticity ≈ 2 — Monràs world): the same −4% on rents costs
≈ −9% of new tenancies plus a seasonal-segment shift: sitting/insider tenants gain,
searching/outsider tenants lose access. The data cannot yet tell A from B —
that is the finding, not a defect.

## Regenerate

```bash
uv run python - <<'PY'
# (see runs/rentcap_sweep_seeds123.csv header; sweep code in git history / this file's
#  commit — build_scenario('rent-cap', seed, 40, start_tick=20,
#  supply_response_elasticity=eps) vs build_scenario('baseline', seed, 40))
PY
```


## Re-measurement 2026-09-08 (KB refresh)

Same design — `RentCap(start_tick=20, cap_reference_discount=0.05, compliance=0.85)` in the
tensioned zone, elasticity sweep × seeds {1, 2, 3}, 40 ticks, mean over the 16 post-cap ticks
against a same-seed baseline. Two code states:

**Before the refresh** (HEAD 0561a3d): contract rents **+0.9%** at every elasticity, new
tenancies +2 to +3%, seasonal units +1 to +5. The reference index, frozen at activation and
indexed at 2.5%/yr, overtook a market growing at the 2%/yr income anchor within ~10 ticks
(capped tensioned listings 29 → 0 by tick 30), after which the magnet rule pulled sub-cap asks
up. The cap was, in effect, off for three of the four measured years.

**After the refresh** (`within_contract_update` 0.015, i.e. IRAV at 0.75 of the income anchor
as in Spain; capped-listing floor applied only to clipped listings):

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | seasonal units gained | Δ sale prices |
|---|---|---|---|---|---|
| 0.0 | −2.2% | −1.8% | +3.6% | 0 | −2.8% |
| 0.5 | −2.2% | −1.8% | +2.6% | +1.8 | −3.4% |
| 1.0 | −2.2% | −1.8% | +3.6% | +4.6 | −3.0% |
| 1.5 | −2.2% | −1.8% | +4.0% | +5.6 | −3.3% |
| 2.0 | −2.2% | −1.9% | +3.8% | +7.5 | −3.5% |

Credibility test, re-read: Jofre-Monseny's world (rents down, no supply effect) is
reproduced at every elasticity, which is the problem — the elasticity dial no longer moves
tenancies, so neither Monràs & García-Montalvo (−10%) nor Pérez García (−13%) can be reached.
Cause: the tensioned rental market is slack in the current baseline (0.6–0.8 applicants per
listing before the cap, 1.1–1.5 under it, against ≈65 contacts per listing in Barcelona), so the
≈60 withdrawals the hazard produces over four years shrink leftover listings without cutting
the number of contracts signed. A hazard rescale cannot fix a slack market; the tensioned
zone's tightness must be recalibrated first (`docs/validation.md` R3). The new
`RentCap.coverage` field (Spain 2026 ≈ 0.42 of the model's tensioned zone) scales the price
effect to −1.4% at 0.42.

New evidence since the original run, all in `docs/policies/rent-cap.md` Update 2026-09-08:
Monràs & García-Montalvo's 2025 CEPR version puts the IV elasticity at ≈2.0 (1.6–3.2) and the
OLS at 0.07 — the 0–2 dial is exactly that span; Incasòl Q4 2025 shows tensioned Catalan rents
+1.6% against +9.4% outside the zones (a spillover the model cannot produce) and the first fall
in seasonal contracts (−1,233) after the seasonal cap; O-HB counts +1,374 contracts in
Barcelona since the regulation against portal listings −56%.


## Re-measurement 2026-09-08, after the tightness revision

Same design, 5 seeds (1–5), `HAZARD_SCALE` 3.0, `formation_zone_weights` 0.55 / 0.286 / 0.164,
shadow rent active. ± is the seed standard deviation.

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | seasonal units gained | Δ sale prices |
|---|---|---|---|---|---|
| 0.0 | −4.6% ± 2.4 | −4.2% | **+1.6%** ± 2.3 | 0 | −3.0% |
| 0.5 | −4.4% ± 2.4 | −4.0% | −0.8% ± 4.9 | +11 | −3.1% |
| 1.0 | −4.1% ± 2.4 | −3.8% | −2.6% ± 2.8 | +17 | −4.1% |
| 1.5 | −3.2% ± 2.5 | −3.3% | −6.5% ± 4.8 | +21 | −4.7% |
| 2.0 | −3.6% ± 2.6 | −3.5% | **−11.6%** ± 6.7 | +25 | −5.0% |

- Jofre-Monseny, Martínez-Mazza & Segú (2023): rents −4/−5%, no supply effect — elasticity 0
  (−4.6%, +1.6%). ✓
- Monràs & García-Montalvo (2023; CEPR 2025, IV ≈2.0): rents −5%, contracts −10% — elasticity
  2 (−3.6%, −11.6%). ✓
- Pérez García (2026): −13% tenancies, weak price effect — just past the dial (≈2.2); the
  weak-price world still needs the second dial (compliance ≈0.25 or discount ≈0). ~✓

What changed since the original table: the withdrawal now runs on the shadow rent (the cap no
longer blinds the landlord), the tensioned queue starts at ≈1.1 applicants per listing instead
of 0.5, and the hazard scale is 3.0 instead of 1.75. Rents fall a little less than in August
(−3.6…−4.6% vs −4.1%) because the IRAV-indexed reference now grows at 0.75 of the income anchor
rather than above it. New in this table: the secondary zone's contract rents rise +1.7% at
elasticity 2 (priced-out seekers migrating down the ladder), a small version of Catalonia's
non-tensioned +9.4%. Partial coverage (`coverage` < 1) is measured in `docs/validation.md` T7
and is not reportable on the pooled rent yet.


## Re-measurement 2026-09-08, final (shadow-anchor revision)

Same design, 5 seeds (1–5). `HAZARD_SCALE` 0.7, exogenous shadow anchor, shadow-based growth
wedge, `CONGESTION_GAIN` 0.05. ± is the seed standard deviation.

| elasticity | Δ contract rents | Δ asking rents | Δ new tenancies | seasonal units gained | Δ sale prices |
|---|---|---|---|---|---|
| 0.0 | −4.9% ± 1.4 | −4.3% | **+0.9%** ± 3.3 | 0 | −4.2% |
| 0.5 | −4.5% ± 1.8 | −3.9% | −1.7% ± 3.3 | +5.8 | −4.8% |
| 1.0 | −4.3% ± 1.8 | −3.7% | −5.2% ± 1.8 | +12.3 | −5.2% |
| 1.5 | −4.2% ± 1.9 | −3.6% | −8.7% ± 3.4 | +18.9 | −5.7% |
| 2.0 | −4.2% ± 1.9 | −3.6% | **−13.6%** ± 2.8 | +24.0 | −5.8% |

Credibility test — the first time all three studies land inside the exposed range:

- **Jofre-Monseny, Martínez-Mazza & Segú (2023)** — rents −4/−5%, no supply effect:
  elasticity 0 (−4.9%, +0.9%). ✓
- **Monràs & García-Montalvo (2023; CEPR 2025, IV ≈2.0)** — rents −5%, contracts −10%:
  between elasticity 1.5 and 2. ✓
- **Pérez García (2026)** — −13% tenancies: elasticity 2 (−13.6%). ✓ The "no robust price
  effect" reading still needs the second dial (compliance ≈0.25 or discount ≈0), since rents
  fall 4–5% at every elasticity here.

Ownership rises +0.5 to +0.9pp under every cap (withdrawn units sold to tenants) and the
capped zone's queue tightens from 1.08 to 1.19–1.90 applicants per listing. Partial coverage
is reported by regulatory segment in `docs/validation.md` T7, never on the pooled rent.
