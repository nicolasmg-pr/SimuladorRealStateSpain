# Phase I — the size margin, and the flat ladder underneath it

Date: 2026-09-17. Status: **plan only. Nothing coded, nothing changed.**

Origin: §5b.2 repaired the rent ladder's *ordering* and closed targets 9 and 11. It did not touch
the *level*, which `model-spec` has recorded as ≈2.6× high since the Funcas contrast rows: every
tenant rents one whole 90 m² unit at asking level, and Spain's renters do not. This phase is that
defect. **Its feasibility arithmetic is done below rather than discovered at implementation** —
phase H was stopped at step 4 by a check that should have been in its plan, and this is that lesson
applied.

## 1. The defect, measured

| | model (after §5b.2) | sourced |
|---|---|---|
| rent, tensioned | 1,692 €/month | — |
| rent, secondary | 1,266 | — |
| rent, rural | 824 | — |
| national level | ≈1,350 | **516** paid [EPF 2022], **691** declared [AEAT FY2024] |
| >30%-of-income share | ≈59% | **38.2%** |
| surface per tenancy | **90 m², always** | see below |

## 2. The feasibility check, and it finds a second defect

Implied surface, EPF rent actually paid ÷ idealista asking €/m²:

| | rent paid €/mo | asking €/m² | **implied m²** |
|---|---|---|---|
| Madrid | 675 | 20.8 | **32.5** |
| Extremadura | 277 | 7.1 (Badajoz) | **39.0** |

**Both are around a third of the model's 90 m².** That is the level defect, and the size margin is
the right instrument for it.

**But the implied size ratio is 0.83, not 1.0** — tenants in the expensive zone rent *less* space,
which is the whole point of the margin. Two consequences follow, and the second is the trap:

1. The **whole-dwelling** T/R ratio the sources imply is `2.44 / 0.83` = **2.93**. The model reads
   **2.05**, so the underlying ladder is **30% too flat** — a defect distinct from the level, and
   one §5b.2 did not fix.
2. **If the size margin lands and the flat ladder is not fixed with it, the observable gets
   worse**: the model's reported ratio would fall from 2.05 to `2.05 × 0.83` = **1.71**, against
   EPF's 2.44. A phase that ships only the margin would improve the level and visibly regress the
   ladder.

**So this phase has two deliverables, not one**, and shipping the first alone is a regression.

**The basis caveat, stated because the whole check rests on it.** EPF rents are *paid* (2022, so
containing below-market sitting contracts); idealista is *asking* (2025). Dividing one by the other
understates surface and mixes vintages. The direction and the order of magnitude are robust to it —
nothing plausible moves 32.5 m² to 90 — but the *values* are not sourced, they are derived. **The
phase's first retrieval replaces them**: INE publishes surface directly (ECEPOV/Censo 2021 table
56864, *viviendas principales según superficie útil*, and the Censo dwelling file carries surface
with régimen de tenencia), which gives surface by tenure without passing through two price series.

## 3. What the mechanism has to be

A tenancy is a **quantity of housing**, not a dwelling. The household chooses how much it rents
given its budget, and rent scales with it. Concretely, `quality` stops being a scalar taste
multiplier and becomes — or is joined by — a size dimension with a sourced distribution.

**Why that is the expensive part.** `quality` multiplies **price** as well as rent. Widening it, or
adding a size term beside it, moves the sale side, the zone price ladder and every §9 moment
calibrated on them. σ is currently **0.15**, which cannot span 30 m² against 90 m² — a
plausible size distribution is several times wider.

## 4. What breaks, named in advance

- **The burden targets.** Rent overburden reads 31.3% inside a 26.8–33% band *because* rents are
  high; cutting the level cuts it, possibly below the band. Target 5 moves.
- **The >30% share** should improve from ≈59% toward 38.2%, which is the point.
- **The zone price ladder**, via `quality` on the sale side. T/R price 3.69 today.
- **Every §9 moment calibrated against a 90 m² tenancy.** This is the largest re-run in the
  project's history to date.
- **The rent-cap channel.** Its co-movement gate reads rents; changing what a rent *is* changes G1.
- **`runs/` caches**, via the config hash.

## 5. Falsifications, declared before anything runs

- **I1 — the level lands.** National rent level must fall to the EPF/AEAT band (516–691), not
  merely downward.
- **I2 — the ladder does not regress.** Reported T/R must not fall below its current 2.05. This is
  the trap in §2 turned into a gate: the margin alone fails it by construction, so passing I2 means
  the flat ladder was addressed too.
- **I3 — the whole-dwelling ladder reaches its implied value.** T/R on a whole-dwelling basis
  toward 2.93, scored against the *replacement* surface source, not the derivation in §2.
- **I4 — the burden targets survive or their breaks are attributed.** Overburden inside 26.8–33%,
  or a named reason.
- **I5 — the size distribution is sourced, not fitted.** If σ has to be chosen to make I1 pass,
  the phase has fitted a distribution to a moment and must say so.

## 6. Order of work

1. **Retrieve surface directly** (INE ECEPOV/Censo by tenure) and retire the derivation in §2.
2. Write the mechanism into `model-spec.md` **with the price-side consequence stated**, not as a
   rent-only change. Nothing coded before this exists.
3. Pre-register, including I1–I5.
4. Implement.
5. Re-run §9 in full, attribute every break.
6. Re-run Morris/Sobol — `quality`'s dispersion will enter the design.
7. Re-run the rent-cap gates, because what a rent means has changed.

## 7. What this phase may not claim

It does not make the rent side reportable: `small_landlord_premium`'s unsourced residual still
governs that. It does not touch the rent cap's magnitude problem except to invalidate its previous
measurements, which must be re-run rather than carried over. And the hold-out is still spent, so
the best reachable outcome remains in-sample.
