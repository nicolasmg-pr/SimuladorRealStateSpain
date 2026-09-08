# Experiment 1 — Catalonia-style rent cap (Phase 7)

> **Status 2026-09-08 (second pass): gate met again.** The table below is the original
> 2026-08-07 measurement and is kept for provenance; it stopped reproducing after the August
> audit and Funcas revision (see "Re-measurement 2026-09-08" at the end). The tensioned-
> tightness revision (`docs/validation.md`) restored the credibility test with three changes —
> metro-weighted household formation, a shadow rent landlords compare the cap against, and a
> re-fitted hazard scale. **Current numbers are in "Re-measurement 2026-09-08, after the
> tightness revision" at the end of this file; quote those.**

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
