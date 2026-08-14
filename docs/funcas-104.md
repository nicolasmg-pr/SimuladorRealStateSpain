# Funcas *Estudios* 104 — reading note and model impact

**Source.** Santiago Carbó Valverde (coord.), *Mercado inmobiliario y política de la vivienda
en España*, Estudios de la Fundación, serie Economía y Sociedad n.º 104, Funcas, 2024.
ISBN 978-84-17609-82-5. Local copy: `docs/Estudios104_3.pdf` (130 pp., 8 chapters).
Registered in `docs/sources.md`, Tier 2.

Eight independent authors, mostly reworking primary statistics (INE Censo and EPF, MIVAU,
Banco de España EFF, Eurostat, AEAT). It is a **secondary compilation**: every figure below
is attributed to the primary series it comes from, because that is what decides whether it
can be combined with what the model already uses.

This note is the audit trail for one question per figure: *does it change the model, confirm
it, or only warn us?* Nothing here is applied twice — where a figure changed a parameter, the
parameter comment in `config.py` carries the same citation.

---

## 1. What changed in the model

| # | Change | Where | Evidence |
|---|---|---|---|
| 1 | Vacancy is now **per zone**, and inverted: rural ≫ secondary > tensioned | `ZoneConfig.units_per_household` 1.075 / 1.124 / 1.242; `engine.initialise` | ch.1 cuadro 1 (INE Censo 2021) |
| 2 | The empty stock is mostly **not mobilisable**, and less so the weaker the local demand | `ZoneConfig.withheld_share` 0.39 / 0.63 / 0.81 | ch.1 §2 (province-growth table + condition argument) |
| 3 | Average dwelling size 80 → **90 m²**, which is the developer's build cost basis | `StockConfig.avg_size_m2` | ch.5 gráfico 4 note (Afi, national average) |
| 4 | A **sharing margin**: a household that keeps failing to find a home accepts a higher rent burden, up to an observed ceiling | `agents/household.search_burden`, `HouseholdState.ticks_searching` | ch.6 cuadro 2 (EPF effort path) + ch.2 (Eurostat 4-in-10) + ch.4 (shared flats as the absorption channel) |
| 5 | The **INE household projection** is available as a scenario path, replacing the flat 240k/yr assumption | `scenario.HouseholdFormation`, `scenario.ine_household_projection`, CLI `ine-demography` | ch.1 §3 gráfico 7 |
| 6 | Eight new rows in the official contrast, incl. the ones that expose gaps (cash purchases, rent level, latent demand) | `benchmarks.py` | ch.1, ch.3, ch.4, ch.6 |
| 7 | Two new reported indicators: `cash_purchase_share`, `rent_burden_over_30_share` | `metrics.py` | ch.3, ch.6 |
| 8 | The hold-out rent target is now an explicit **failing** target, at its real magnitude | `tests/test_validation.py::test_holdout_boom_rent_growth` | ch.2, ch.6 (rents grew far above income) |

Measured consequences of 1–4 are in `docs/validation.md` ("Funcas 104 revision").

## 2. What the source confirms (no change, higher confidence)

- **Construction shortfall.** ≈100k dwellings/yr against 175k–200k needed for the next five
  years; since 2015, 75k starts/yr against ~120k new households/yr; 2019–2023 households
  +900k against 430k completions (ch.1 §2–3, ch.2 §2). Matches the model's completions =
  40–70% of formation target and the BdE deficit row.
- **Construction lag and capacity.** Labour scarcity is named as a binding constraint on any
  supply push, alongside >120,000 unemployed ex-construction workers on the EPA (ch.8 §5) —
  independent support for `max_starts_per_tick` being a real ceiling *and* for calling it
  low-confidence.
- **Land as the residual claimant** (`model-spec` §6b). Land price index 55 vs house price
  index 98 (2007=100, 2023): land flat for a decade while house prices climbed (ch.8
  gráfico 3). This is the empirical signature of the model's start rule, and it was the
  defect the audit's D1 fixed. Ezquiaga adds the stock behind it: planned-but-unexecuted
  land for **6.78M dwellings**, 25.5% of the existing park, sitting in approved planning for
  20 years (ch.4 cuadro 1) — the reason `land_release_lag` is 20–60 ticks and why the lever
  must show no short-run price effect.
- **`formation_income_factor` = 0.9.** EFF median real income of households headed under 35:
  €29.1k in 2022 against €32.4k for all households ⇒ 0.90 (ch.4 cuadro 3). The config value
  was derived from a different EFF cut and lands in the same place.
- **`max_dsti` = 0.35.** "A loan is refused when repayments exceed 30–35% of income", citing
  Banco de España (ch.6 §2 note 8).
- **Transaction taxes.** Direct purchase taxation is 10–15% of the price (ch.7); the national
  average ITP rate is 8% on a €96.8bn base (ch.8 cuadro 1). The model's ITP ladder
  (0.10 / 0.08 / 0.06) plus 2% fees reproduces both.
- **ICO guarantee.** €2.5bn line, up to 20% of the price, under-35s and families with
  children, designed so the buyer needs no full down payment and stays under 30% of income
  (ch.8 §3). Exactly `guarantee_ltv_boost` = 0.20 and `guarantee_budget` = €2.5bn *once*.
- **IRAV cap.** 2% from April 2022 to December 2023, 3% in 2024, then the new SERPAVI-based
  index (ch.6 §2, ch.8 §3). `within_contract_update` = 0.025 sits between the two.
- **Gran tenedor** = >10 dwellings or >1,500 m² of residential floor space; only Cataluña has
  declared tensioned zones (140 municipalities, from March 2024) (ch.8 §3–4). Confirms both
  the threshold and the zone-scoped switch.
- **Vacancy-tax instrument.** Ley 12/2023 allows a **50–150% IBI surcharge** on owners of
  four or more residential units empty ≥2 years without justification; Cataluña has taxed
  empty dwellings since 2015 (ch.7 §3). Confirms `vacancy_min_portfolio` = 4 and puts the
  model's `vacancy_tax_rate` (0.001–0.03 of value) on a real instrument: IBI runs ≈0.4–1.1%
  of cadastral value, so the surcharge is ≈0.2–1.6pp of cadastral, i.e. roughly 0.1–0.8% of
  market value per year — the low half of the model's range.
- **Demand subsidies capitalise.** "A hypothetical VAT cut on new housing… could become a
  transfer of resources to developers (*efecto ganga*)"; generalised demand incentives are
  judged low-efficacy and inequality-increasing while supply is constrained (ch.8 §6–7).
  Same direction the model's demand-subsidy lever is expected to show.
- **Social rental is marginal.** 1% of stock (OECD, ch.6) or 2.5% (Provivienda, ch.8) against
  7% (OECD average) / 9.3% (EU). `public_rental_share` = 0.017 sits between the two Spanish
  readings; the range widens to 0.010–0.025.
- **Rent-cap evidence stays disputed.** No rigorous estimate of the supply response exists;
  portals claim −30% rental supply in 2022 (Servihabitat, Fotocasa), which the author
  explicitly flags as not a study (ch.6 §2). Keeps `rental_supply_elasticity` a swept range.

## 3. What the source disputes (ranges widened, no point value moved)

- **Cash purchases.** 2023: 973,637 sales against 381,560 new mortgage deeds ⇒ **60.8% of
  purchases carried no registered mortgage** (ch.3 §3), against the 30–40% cash share in the
  model's dossiers. The two series do not count the same thing (the mortgage statistic is new
  deeds on dwellings; it misses subrogations and registration lags), so this is a range, not
  a correction. But the model itself comes out at **3.2%**, an order of magnitude below even
  its own assumption — see the gap list below.
- **Foreign buyer premium.** `foreign_budget_multiplier` = 1.6 comes from non-residents paying
  +76–79% per m² (Notariado). This source gives foreign *mortgaged* purchases at €326,227
  against a national €258,575, i.e. **+26%** (ch.5 note 3). Different populations: mortgaged
  foreign buyers exclude the cash-rich non-resident segment the model's overlay represents,
  so +26% is a lower bound. Documented range 1.26–1.79, midpoint unchanged.
- **Ownership rate.** EPF 2022: 76.4% owners / 17.7% renters / 5.8% ceded (ch.6 cuadro 1);
  MITMA 2023: 75.3% of the park owner-occupied (ch.8 §2); the model's EFF-based target band
  is 70–74%. Three bases, one direction: the model's 70.1% is at the bottom of all of them.
  Recorded as a benchmark row with the band 70–77% rather than a re-fit.
- **Non-resident share of purchases.** ≈60,000/yr, ≈10% of transactions, 85% of them in
  tourist regions; 9.2% in 3Q2023; 30% in Alicante, Málaga and Baleares (ch.1 §2, ch.5 §2).
  Brackets the model's `foreign_purchase_share` = 0.08 and confirms the coastal concentration
  the tensioned zone's `foreign_overlay` stands for.

## 4. Gaps this source opens (documented, not yet fixed)

1. **Rent level relative to income.** EPF average rent paid: €516/month in 2022 (Madrid €675,
   Extremadura €277; SEF 2021 gives €10.7/m² in Madrid against €4.4 in Extremadura). The
   model's national rent index is ≈€1,350/month for a standard 90 m² unit, and its mean
   tenant burden is 40% of gross income against an EPF effort of 29.7% of the consumption
   basket. Part is basis (the model prices a whole average dwelling at asking level; EPF
   averages what all sitting tenants actually pay, in dwellings of every size), and part is
   real: **the model has no small-dwelling or shared-flat segment**, while Funcas ch.5 shows
   a young median earner crosses the one-third threshold at 30 m² and half their income at
   45 m². Tracked as a benchmark row (`rent_level`) and a limitation in `model-spec` §10.
2. **Cash purchases are almost absent** (3.2% against 30–40% assumed and 60.8% implied by
   INE). The model finances nearly every household purchase with a mortgage, which makes
   credit policy — rates, LTV, DSTI, guarantees — bite harder in the model than in Spain.
   New benchmark row `cash_purchases`; no fix attempted, because the household wealth
   distribution and the inheritance channel would both have to move.
3. **Rent growth still cannot outrun income growth.** Spain 2015–2022: rent spend +27.7%
   against household income +16.6% (single earner) to ~22% (two or more) (ch.6 cuadro 2);
   Madrid rents +39% 2015–2022 against +26% in other European capitals (ch.2 §2); young
   wages +25% against rent inflation 20pp higher (ch.2 gráfico 5). The model produces
   0.0% ± 0.3pp in the hold-out boom. The sharing margin raises the *level* of accepted
   burden but not the growth rate, because the clearing rent equals the winning applicant's
   willingness to pay and that is a share of income. Now a strict xfail at the real target
   magnitude instead of a `> 0` assertion that passed on luck.
4. **No second-home or other-province demand stream.** 50,000–60,000 purchases/yr by
   residents of other provinces, ≈10% of transactions, stable over a decade (ch.1 §2) —
   on top of the ≈10% non-resident share the model does carry. The model understates
   non-local demand by roughly that much.
5. **No age structure.** Renting is steeply age-graded: 42.7% of households headed by an
   under-35 rent, against 17.3% at 45–55 and 7.5% over 65, where 83% own outright (ch.6
   cuadro 1). The model has one household type with an income draw, so it cannot reproduce
   the age gradient that drives the emancipation story.
6. **Nationality.** 66.3% of households whose main earner was born outside Europe rent,
   against 11.6% of Spanish-headed households (ch.6 cuadro 1). Migration is the largest
   component of household formation, and it lands almost entirely in the rental market; the
   model's new households are drawn from one pool.
7. **No landlord income tax.** The IRPF reduction on residential rental income (60% → 50%
   general from 2024, 60% if rehabilitated, 70% in tensioned zones for young tenants, **90%
   if the new contract cuts the rent 5%** versus the previous one) costs ≈€1,039M/yr and
   AIReF judges it effective at fostering rental supply (ch.7 §1.2, ch.8 §6). The model has
   no landlord taxation, so it cannot represent the one lever that pays landlords to lower
   rents — a natural next policy, and one that interacts with the rent cap.
8. **No connectivity lever.** Both ch.2 and ch.8 propose improving transport links between
   tensioned cities and adjacent territories (Puertollano, Ciudad Real, Valladolid on
   high-speed rail) as a supply-side measure. In this model that maps onto migration
   propensity between zones, which is currently downward-only and rent-triggered.
9. **Utilities are not modelled**, so the Ley 12/2023 *sobreesfuerzo* definition (rent plus
   community charges, water and energy) cannot be computed. That threshold puts 60.5% of
   Spanish renting households above 30% in 2022, against 38.2% on rent alone (ch.6 cuadro 2).

## 5. Evidence for the zone price ladder (the model's other failing target)

`docs/validation.md` lists a location-amenity term as candidate fix #1 for the collapsing
tensioned/rural price ratio, and says it needs calibration evidence. This source supplies it:

- Private-sector wages in Madrid and Barcelona are **45% above** the rest of urban Spain,
  the cost of living **~20% above**, so the purchasing-power-adjusted gain is **21%**
  (Banco de España cost-of-living index, Forte-Campos et al. 2021, via ch.5 §1).
- 35.7% of 20–34-year-olds live in the functional urban areas of the five largest
  municipalities, up 2.5pp in a decade; Madrid and Barcelona alone hold 27.1% of the young
  (ch.5 §1) — the migration pull the amenity term would represent.
- The rent gradient it has to reproduce: Madrid €10.7/m² against Extremadura €4.4/m² (SEF
  2021, ch.6 §2), and rent spend 1.8× higher in group I regions than in group III.

Not implemented here: it is a price-formation mechanism, and `model-spec` requires the
decision to be written before it is coded. What this note adds is that the calibration
targets now exist.

## 6. Figures kept for context (not model inputs)

Cycle history (ch.1, ch.4): >600k completions/yr in 2007–08 and 4.7M over the decade, of
which household growth was >50% migration-driven; unsold new stock peaked above 640k units in
2010 and was still ≈455k in 2020; 2010s completions averaged 75k/yr. Banking legacy (ch.4):
developer NPLs reached 38% against under 6% on household mortgages, and property was 70% of
all NPLs — the reason the model's crisis lever should tighten *developer* credit first;
credit/GDP 86.3% (2000) → 171.9% (2009) → 80.8% (2023); the bank rescue cost 5.5% of GDP.
Emancipation (ch.2, ch.5): 30.3 years against an EU 26.4; 46.3% of 25–34-year-olds live with
their parents against ~30% in the EU; youth unemployment 28% against an EU 14%; temporary
contracts 35% among under-30s. Tenure preference (ch.1 §4, CIS 2019): 66.3% agree that buying
is always better than renting, 75.4% that renting gives more freedom to move, and 54.6%
expect not to be able to pay rent once retired — the cultural prior behind the model's
affordability-gated, not preference-gated, tenure rule.
