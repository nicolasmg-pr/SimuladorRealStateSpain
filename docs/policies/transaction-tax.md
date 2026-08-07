# Transaction tax (ITP)

Researched 2026-08-07. Sources registered in `docs/sources.md` conventions; full rows in
scratch `sources/policy-transaction-tax.md`. All effect estimates kept as ranges.

## 1. Mechanism

- **What it is.** The Impuesto de Transmisiones Patrimoniales Onerosas (ITP) is a buyer-paid
  ad-valorem tax on **second-hand** dwelling sales. New builds instead pay **IVA 10%** plus
  **AJD** (stamp duty on the deed, ~0.5–3.5% depending on region and case). Since 2022 the
  taxable base is the cadastral *valor de referencia* if higher than the declared price.
- **Who holds the lever.** ITP is a state tax fully ceded to the CCAA (autonomous
  communities): each region sets rates, reduced rates, and surcharges within the state
  framework. The central state controls IVA and the overall framework; municipalities have
  no ITP lever.
- **Current rates (verified 2026, idealista/guiafiscal/ATC).** General rates range roughly
  **6% to 13%**: Madrid 6% (4% large families), Canarias 6.5%, Andalusia and Basque Country
  7%, Murcia 7.75%, Galicia 8%, Aragon 8–10%, Balearics 8–13% (progressive), Asturias
  8–10%, Castilla-La Mancha 9%, Valencia 10% → **9% from June 2026** (11% above €1M),
  Catalonia progressive **10–13%** plus a **20%** rate for large holders (>10 dwellings, or
  ≥5 in tensioned zones) and whole-building purchases (Decreto ley 5/2025, in force
  27-06-2025). Most regions have reduced rates (0–5%) for young first-time buyers, VPO,
  large families, disability, rural areas.
- **Natural experiments available (2025–26).**
  - Catalonia 27-06-2025: general hike to a 10–13% progressive scale + 20% large-holder
    rate — a targeted hike on investor buyers.
  - Murcia 25-07-2025: cut 8% → 7.75% (Ley 3/2025). Valencia 01-06-2026: cut 10% → 9%.
  - The January 2025 announcement of a **100% tax on non-EU non-resident buyers** was
    submitted as a bill in May 2025 but **stalled in Congress: never debated or voted, and
    dropped from the government's January 2026 housing package. As of mid-2026 it is not
    law** (US News 2026-03-27; multiple legal-advisory trackers).
- **Spanish empirical work.** We found **no published Spanish quasi-experimental study** of
  ITP effects on volumes/prices exploiting regional variation (search: Fedea, Banco de
  España, academic; 2026-08-07). Fedea/Cámaras de la Propiedad (Menéndez 2026) is
  descriptive/normative: total lifecycle tax burden can exceed 62% of the purchase price;
  ITP disparity (6% Madrid/Navarra vs 10–20% Catalonia/Balearics/Valencia) "punishes labour
  mobility"; proposes correcting ITP cascading and abolishing AJD. Banco de España
  Documento Ocasional 0506 describes the tax structure. Treat Spanish ITP elasticities as
  **imported from international evidence**, a stated model limitation.

## 2. Evidence for

(the case that raising ITP cools prices / cutting it stimulates, and that it is a usable lever)

- **Best & Kleven (2018, ReStud; UK stamp duty).** A temporary elimination of a 1%
  transaction tax raised housing-market activity by **~20% in the short run** (timing +
  extensive margin); **less than half** of the stimulus reversed after reintroduction;
  extra spending ≈ $1 per $1 of tax cut. So a *cut* is a strong, cheap stimulus — and
  symmetrically, hikes suppress activity.
- **Capitalization into lower prices.** Dachis, Duranton & Turner (2012, J. Econ. Geog.;
  Toronto 1.1% LTT): prices fell **by roughly the amount of the tax** (≈full
  capitalization) — i.e., part of the statutory buyer burden shifts to sellers, so a hike
  does push observed prices down. Kopczuk & Munroe (2015; NY/NJ mansion tax): incidence
  falls on sellers and **may exceed the tax** locally (over-shifting).
- **Targeting.** Catalonia's 20% large-holder rate shows the lever can be aimed at investor
  demand while sparing owner-occupiers (reduced 5% young-buyer rate widened in the same
  decree). Petkova & Weichenrieder (2017, Germany) find quantity effects concentrated in
  owner-occupied single-family homes, while investor-held apartments show **price** (not
  volume) responses — consistent with taxing investors lowering prices more than volumes.
- **Revenue.** ITP+AJD is a major CCAA revenue line; Fedea's 62%-lifecycle-burden figure
  itself documents how much revenue rides on housing transactions.

## 3. Evidence against / side effects

- **Lock-in and lost mobility.** Van Ommeren & Van Leuvensteijn (2005, J. Regional Sci.;
  NL): +1pp transaction cost ⇒ residential mobility **−(≥8%)**. Hilber & Lyytikäinen
  (2017, JUE; UK): higher stamp duty strongly reduces housing-related and short-distance
  moves (job-related/long-distance moves unaffected) — mismatch (wrong-sized homes), not
  labour-market damage, is the main distortion. Fedea makes the same mobility argument for
  Spain's 6–20% regional spread.
- **Large volume distortions.** Toronto: 1.1pp ⇒ **−15% sales**. Germany (Fritzsche &
  Vandrei 2019, RSUE): +1pp ⇒ **~−6% transactions long-run** plus large anticipation
  spikes before pre-announced hikes. Kopczuk & Munroe: markets "unravel" around notches —
  missing transactions exceed bunching.
- **Deadweight loss.** Dachis et al.: welfare loss ≈ **$1 per $8 of revenue**, far worse
  than an equivalent recurrent property tax (IBI). Petkova & Weichenrieder: for vacant
  lots the quantity elasticity is near −1 — close to the top of the Laffer curve.
- **Prices fall but affordability may not improve.** The price drop reflects seller-side
  capitalization; buyer's all-in cost (price + tax) is roughly unchanged or higher, and
  fewer homes change hands. Cooling *measured* prices via ITP is partly a statistical
  artefact.
- **Temporary cuts mostly retime.** Besley, Meads & Surico (2014, JPubE; 2008–09 UK
  holiday): transactions +**~8%**, mostly reversed after withdrawal; only ~**60%** of the
  surplus reached buyers. (Disagrees with Best & Kleven's <50% reversal — keep as range.)
- **Anticipation effects.** Pre-announced hikes (Catalonia 2025: 3-month lead) cause
  transaction spikes then troughs — noisy data around reform dates.

## 4. Effect-size range

Per **1pp permanent change** in the transaction-tax rate (sign: hike ⇒ minus):

| Outcome | Range | Sources (disagreeing, kept as range) |
|---|---|---|
| Transaction volume, long run | **−4% to −15% per +1pp** | Fritzsche & Vandrei ~−6%/pp; Petkova & Weichenrieder elasticity −0.23 wrt rate (≈−4 to −5%/pp at Spanish 5–10% bases); Dachis et al. ≈−14%/pp (1.1pp ⇒ −15%) |
| Transaction volume, temporary cut (holiday), short run | **+8% to +20% per −1pp**, 40–100% later reversed | Besley et al. +8%, mostly reversed; Best & Kleven +20%, <50% reversed |
| Price capitalization (share of tax borne by sellers via lower price) | **~40% to >100%** | Besley et al. ~40% (short-run holiday); Dachis et al. ≈100%; Kopczuk & Munroe >100% locally; Petkova & Weichenrieder ≈0 for owner-occupied houses, negative for investor apartments |
| Owner residential mobility | **−8% or more per +1pp**, concentrated in short-distance/housing-related moves | Van Ommeren & Van Leuvensteijn ≥−8%/pp; Hilber & Lyytikäinen (direction verified; magnitude not extracted) |
| Welfare cost | ≈ **$1 lost per $8 revenue** (single estimate, Toronto) | Dachis et al. |

No Spanish quasi-experimental estimate exists (as of 2026-08-07); ranges above are UK/DE/NL/
CA/US imports and should be widened, not narrowed, when calibrating Spain.

## 5. Model mapping

Proposed `scenario.Intervention` parameters (typed dataclass, per project conventions):

```python
@dataclass(frozen=True)
class ItpIntervention:
    itp_rate_delta: float  # percentage points, e.g. +0.02 = +2pp; unit: fraction of price
    zone_types: tuple[ZoneType, ...]  # ITP is CCAA-level: apply per zone type or all
    applies_to: tuple[BuyerType, ...]  # {HOUSEHOLD_FTB, HOUSEHOLD_MOVER, SMALL_INVESTOR,
    #  LARGE_HOLDER, FOREIGN_NON_EU} — Catalonia 2025
    #  precedent: LARGE_HOLDER-only surcharge
    reduced_rate_delta: float = 0.0  # separate lever for young/FTB reduced rates
    announcement_lag_ticks: int = 0  # >0 reproduces anticipation spike (Fritzsche & Vandrei)
```

Implementation notes:

- **Capitalization is endogenous, not a parameter.** Buyers compute willingness-to-pay net
  of tax: `max_bid = affordability_limit / (1 + itp_rate)`, so a hike mechanically lowers
  bids; how much of that reaches transacted prices depends on sellers' reservation-price
  stickiness in `market/clearing.py`. Validation target: emergent capitalization within the
  40–100%+ range of §4, and volume response within −4% to −15% per +1pp.
- **Mobility channel:** add the (expected) round-trip transaction cost to the moving
  threshold in household `decide()`; calibrate so +1pp ⇒ ~−8% owner moves (range: −4% to
  −15%, wider than the NL point estimate). Suppress the effect for forced/job moves per
  Hilber & Lyytikäinen.
- **New builds** are untouched by `itp_rate_delta` (they pay IVA+AJD — separate lever);
  this asymmetry shifts demand between new and second-hand stock and must be in the spec.
- Baseline rates per zone type: tensioned metro ≈ Catalonia/Madrid poles (6–13%+20%),
  secondary ≈ 7–9%, rural ≈ reduced rates common — store as sourced config, not scenario.
