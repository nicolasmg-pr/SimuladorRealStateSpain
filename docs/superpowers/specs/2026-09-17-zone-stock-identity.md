# Phase H — the zone stock identity, retired

Date: 2026-09-17. Status: **plan only. Nothing is coded, nothing is measured beyond the
diagnosis that produced it.** No branch, no config change.

Origin: §7.3 (buy-to-let entry) has been parked since 2026-09-14 because yield-chasing entry
arbitrages the zone price ladder away. Two repairs were nominated and both failed — the sourced
vacancy gradient closes 7.6% of the gap, and a market-vacancy gate cannot be built because only
one Spanish statistical operation makes the required split. Tracing the third route found that
the blocker is not in the investor's comparison at all. It is an identity in the zone
configuration, three steps upstream. This phase is about retiring it.

## 1. What the identity is

`ZoneConfig.withheld_share` is not sourced. `config.py` says so explicitly: the **gradient**
(rural ≫ secondary > tensioned) is the sourced claim [INE Censo 2021 / Funcas 104 ch.1]; the
**levels are a guess**, fixed by solving

```
(units_per_household − 1) × (1 − withheld_share) = 0.0455    per zone
```

Measured on the shipped config, it holds to three decimals in all three zones:

| zone | `units_per_household` | `withheld_share` | (upH−1)(1−w) |
|---|---|---|---|
| tensioned | 1.0750 | 0.39 | **0.0457** |
| secondary | 1.1240 | 0.63 | **0.0459** |
| rural | 1.2420 | 0.81 | **0.0460** |

`withheld_share` is the variable the equation is solved for. 0.0455 is the mobilisable vacant
stock per household that was calibrated against the §9 moments **before** the empty stock was
recognised zone by zone; the design note defends holding it constant on the ground that
recognising the stock "changes what the model *counts*, not what the market can *use*" — Funcas
104's own claim that the Spanish empty stock "can hardly serve as an umbrella" for unmet demand.

**So the model asserts that a household has the same usable empty stock — 0.046 dwellings —
whether it lives in Madrid or in a village.** All zone variation in vacancy is absorbed into a
flag drawn once at `engine.py:243` and never revisited outside a vacancy-tax intervention.

## 2. The finding this phase exists for

The chain from the identity to §7.3's blocker is short and complete:

1. mobilisable stock per household equal across zones, **by construction** →
2. market vacancy per household equal →
3. market vacancy **rate** lowest where stock per household is highest — rural →
4. a rural landlord faces the least letting risk in the model →
5. the 12.26% rural gross yield is a near-riskless return →
6. yield-chasing buy-to-let entry arbitrages the ladder to T/R **1.65** against a 2.6 floor.

No discount applied at step 4 can undo an identity imposed at step 1, which is why both
nominated repairs failed on arithmetic before they were built.

**Where it binds wrongly.** Against the EUV's 14.9% offered share of non-principal stock, the
model reads rural **14.8%** — right — and tensioned **43.0%**, roughly 3× high. The identity is
not wrong everywhere; it is wrong at the metro end, which is exactly where "equal mobilisable
stock per household" is least plausible: the umbrella argument has least to say about the zone
with the strongest demand and the least empty stock.

**What it blocks.** Target 9 (gross yield, all three zones, strict xfail), target 11 (rent
ordering, strict xfail), and §7.3 itself.

## 3. Three candidate replacements, and none of them is free

**(a) Source the levels directly, keep them exogenous.** Set `withheld_share` per zone from an
independent estimate of the unusable/withheld fraction instead of solving for it. *Cost:* the
only estimate that exists is the EUV, one predominantly urban region — the single-source
objection that already closed the gate route. *Verdict:* not available on current evidence.

**(b) Make withholding a decision rather than an initial condition.** A unit is withheld when
its expected net letting return fails to clear a threshold — condition and rehabilitation cost
against local rent. The zone gradient then **emerges** instead of being imposed, and it responds
to policy. *Cost:* new parameters, each needing ≥2 sources; and the vacancy-tax lever currently
bites on a static flag, so its mechanism and every result it has produced change. *Verdict:* the
most expensive and the most defensible — a model whose stated purpose is testing vacancy taxes
should not represent withholding as an initial condition no policy can move except by decree.

**(c) Keep the identity, vary its constant per zone.** Replace the single 0.0455 with a
per-zone constant anchored on a sourced proxy for how much local empty stock is usable.
*Cost:* cheapest, but it re-parameterises rather than explains, and the proxy would need its own
two sources. *Verdict:* a holding action, not a repair.

**Recommendation: (b)**, with (c) explicitly rejected rather than deferred. The project's
standard is that the model is judged on its specification; an initial condition that cannot
respond to the policies the model exists to test is the weakest kind of specification, and it is
now measurably load-bearing.

## 4. The EUV must be held out, not fitted

The Basque EUV is the only registered measurement of the quantity this phase changes. **Using it
to calibrate spends it**, exactly as the 2008–13 hold-out was spent (§13.11). It is reserved as
the out-of-sample check: the mechanism is specified and parameterised from other evidence, and
the EUV is consulted only to score the result. Any pass that required looking at 14.9% first is
not a pass.

## 5. Order of work

1. **Freeze the baseline.** Record the §9 moments and the zone vacancy table at the current
   identity, with the config hash, so the comparison is against a committed state.
2. **Write the mechanism into `model-spec.md` first**, as a numbered section, with its parameter
   ledger and sources. Nothing is coded before this exists.
3. **Pre-register** (`docs/prereg/`), including the falsifications in §6 below, and commit before
   running.
4. Implement on a branch. Expect the suite red throughout; do not mark anything xfail to keep it
   green.
5. Re-run the §9 moments. Attribute every break.
6. Re-run Morris/Sobol — the variance-rule verdicts (§13.2) will move, and price-to-income's
   status as the project's first reportable magnitude is not guaranteed to survive.
7. Only then re-open §7.3 and the `buy-to-let-remeasure` branch.

## 6. Falsifications, declared before anything runs

- **H1 — the ordering emerges.** Market vacancy must rank rural > secondary > tensioned, or the
  mechanism has replaced one imposed ordering with another.
- **H2 — the tensioned offered share moves toward the EUV figure without being fitted to it.**
  Scored once, against 14.9%, after parameterisation is frozen.
- **H3 — the rural leg does not break.** It already reads 14.8% against 14.9%. A mechanism that
  fixes the metro end by breaking the rural end has moved the error, not removed it.
- **H4 — the ladder survives buy-to-let entry.** With §7.3's mechanism on, T/R must stay above
  its 2.6 floor. This is the gate the whole phase exists to reach; failing it means the identity
  was not the binding constraint after all, and that finding is worth the phase on its own.
- **H5 — the §9 moments that pass today still pass, or every break is attributed.** Named in §7.

## 7. What will break, named in advance

- **The vacancy moments tied to the 0.0455 calibration**: target 5d (vacancy geography, passing
  now at 18.1 / 11.8 / 8.7), the national 10–15% band, and the seeker share — which the design
  note records moving 6.2% → 5.2% when the gradient was absent, i.e. this is the lever that
  stops rural vacancy absorbing latent demand.
- **Secondary-zone vacancy** is already a strict xfail at 13.4% against a 13.1% band top. It
  will move, and it may move either way.
- **`sensitivity.py`**: `withheld_tensioned` is a swept parameter (range 0.30–0.50). Under (b) it
  ceases to exist and the Morris/Sobol design changes with it.
- **The vacancy-tax lever**: it detects long-vacant withheld units of large portfolios and
  mobilises them probabilistically. Under (b) withholding is endogenous and the lever bites on a
  different object. **Every vacancy-tax result the project has reported becomes non-comparable**,
  and `docs/policies/vacancy-tax.md` needs re-running, not just re-reading.
- **`runs/` caches**: the config field set changes, so every cached artefact keyed on the old
  hash is orphaned.

## 8. What this phase may not claim

It does not make the rent side reportable — `small_landlord_premium`'s unsourced residual still
governs that, and is untouched here. It does not repair the rent cap, whose refinement is
stopped on separate grounds. If H4 passes it unblocks targets 9 and 11 and re-opens §7.3; if H4
fails it has still retired a guess that was silently load-bearing, and that is the floor on its
value.

## 9. Honest cost

Steps 1–3 are a day of specification and sourcing. Step 4 touches `config.py`, `engine.py` and
the zone dataclass; step 6 is 2,000+ model evaluations. The re-run of every vacancy-tax result
in §7 is the part most likely to be underestimated, and it is not optional: leaving those
published while their mechanism has changed underneath is the failure mode the limits register
already names once.
