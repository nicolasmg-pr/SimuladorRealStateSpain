# External forecasts — what exists to benchmark model projections against

Research pass 2026-08-10. Question asked: *"can we compare the simulator's predicted
numbers against Banco de España's previsiones?"*

**Answer: not for housing.** BdE publishes no house-price, rent, transaction or
completion forecast. Its quarterly macro projection tables contain zero housing rows.
What BdE does publish is *actuals plus diagnostics* — a measured deficit, an
overvaluation band, a supply elasticity — all backward-looking or structural, none a
projected path.

Forward-looking Spanish house-price paths exist, but from **commercial and multilateral
institutions**, not the central bank, and they are **PDF-only**: no forecast series is
machine-readable anywhere (see §5).

This file is a **benchmark** reference, not a validation one. `validation.md` asks
"does the baseline reproduce history"; a forecast comparison asks "does our projected
path sit inside the range other forecasters project". The second is not a pass/fail
gate — see the honesty note in §6 on how badly the 2026 panel under-forecast.

Every number below carries its variable definition, horizon, publication date and URL.
Numbers that could not be confirmed by fetching are marked **(unverified)**.

---

## 1. BdE macro projections — the thing that does not contain housing

Series: *Proyecciones macroeconómicas e informe trimestral de la economía española*,
4×/yr. Landing page:
https://www.bde.es/wbe/en/publicaciones/analisis-economico-investigacion/proyecciones-macro-informe-trimestral/

Calendar changed in 2026. Per the June 2026 boilerplate: **February and October** are now
full reports (recent developments + horizon extension); **June and December only update**
the existing horizon. Verified consequence — the horizon did *not* extend to 2028.

| Exercise | Cut-off / published | Projection years in table | PDF |
|---|---|---|---|
| **June 2026 (latest)** | 27 May / **18 Jun 2026** | **2026, 2027 only** | [be2602-ite.pdf](https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/InformesBoletinesRevistas/BoletinEconomico/26/T2/Files/be2602-ite.pdf) (ES: `.../26/T2/Fich/be2602-it.pdf`) |
| March 2026 (full) | 20–21 Mar / 27 Mar 2026 | 2026, 2027 only | [be2601-ite.pdf](https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/InformesBoletinesRevistas/BoletinEconomico/26/T1/Files/be2601-ite.pdf) |
| December 2025 | — / 23 Dec 2025 | 2025, 2026, 2027 | `.../25/T4/Files/be2504-ite.pdf` |
| September 2025 | 4 Sep / 16 Sep 2025 | 2025, 2026, 2027 | `.../25/T3/Files/be2503-ite.pdf` |

**2028 appears in no published BdE table as of 2026-08-10.** Expect it first in the
October 2026 exercise.

### Housing variables in the projection tables: none

Table 2 (*Projections for the main macroeconomic aggregates*) rows are exactly: GDP,
private consumption, government consumption, **gross capital formation (no dwellings
split)**, exports, imports, domestic-demand contribution, net-exports contribution,
nominal GDP, GDP deflator, HICP, HICP ex energy & food, employment (persons), employment
(hours), unemployment rate, nation net lending/borrowing, general-government balance,
general-government debt.

No house prices. No residential investment. No housing starts. **No household disposable
income** — which matters, because `metrics.py` needs exactly that for price-to-income
(`DISPOSABLE_FACTOR`). No mortgage rate.

June 2026 baseline (Table 2, % volume change; 2025 column is actual):

| Variable | 2025 | 2026 | 2027 |
|---|---|---|---|
| GDP | 2.8 | **2.3** | **1.7** |
| Private consumption | 3.4 | 2.6 | 1.6 |
| Gross capital formation | 5.8 | 4.1 | 2.2 |
| HICP | 2.7 | **3.6** | **2.6** |
| HICP ex energy & food | 2.6 | 3.2 | 3.2 |
| Employment (persons) | 2.7 | 2.2 | 1.5 |
| Unemployment rate (% LF, avg) | 10.5 | 10.0 | 9.8 |
| GG balance (% GDP) | −2.4 | −2.4 | −2.3 |
| GG debt (% GDP) | 100.7 | 98.9 | 97.9 |

### Nearest thing to a mortgage-rate projection

Table 1, *technical assumptions* — Eurosystem methodology, futures-based, and the report
states explicitly that these are **not a prediction**. Use as a scenario input for
`macro.mortgage_rate`, never as a validation target.

| Assumption | 2025 | 2026 | 2027 |
|---|---|---|---|
| 3-month EURIBOR | 2.2 | 2.4 | 2.8 |
| 10-yr Spanish sovereign yield | 3.2 | 3.5 | 3.7 |
| Brent, $/bbl | 69.1 | 96.9 | 82.2 |
| Wholesale electricity, €/MWh | 65.5 | 65.8 | 57.4 |

### Where housing does appear — narrative nowcast only

March 2026 (full) report, **Chart 18**, p.28 —
[be2601-ite.pdf](https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/InformesBoletinesRevistas/BoletinEconomico/26/T1/Files/be2601-ite.pdf).
Verbatim-verified: residential investment "expected to slow down slightly in early 2026";
housing starts "stabilising at a level of close to **140,000 units per year**"; real house
prices **+9.6% y/y in 2025Q4, +9.7% for 2025 as a whole vs 5.5% in 2024** (deflated by
CPI); house purchases "just over **750,000** transactions in 2025, highest since 2008".

These are actuals and qualitative direction, **not a projected path**.

Inconsistency worth flagging: the March 2026 report's own boilerplate claims "current year
and the next two years", contradicting its own two-year table. The tables are
authoritative.

---

## 2. BdE housing numbers that do exist — actuals and diagnostics

### Informe Anual 2025, chapter 2 (the housing chapter), published 18 Jun 2026

Full PDF (11 MB, ES; ch.2 = pp.127–180):
https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesAnuales/InformesAnuales/25/InfAnual_2025.pdf

| Number | Definition | Period | Location |
|---|---|---|---|
| **750,000 dwellings** | Accumulated differential between **completions** and **net household formation**. Backward-looking, **not a projection** | **2021–2025** | ch.2, "se amplía el déficit acumulado de viviendas, que alcanza unas 750.000 unidades entre 2021 y 2025" |
| **3.7%** | Same deficit as % of resident households in 2025. Cross-country: Italy 1.5%, Portugal 6.6% (≈300k), France ≈0, Germany **+**0.5% (≈+225k surplus) | 2021–2025 | Gráfico 2.11 |
| **−3.9%** | Completions-minus-formation as % of period-average households, by decade: 1982–90 +6.9, 1991–2000 +5.1, 2001–10 +9.4, 2011–20 −1.2, **2021–25 −3.9** | — | Gráfico 2.10.a |
| **240,000** | Net household formation, 2025 (vs annual average **245,000** for 2021–2024) | 2025 | ch.2 |
| **92,000** | New dwellings completed 2025, **−9%** y/y | 2025 | ch.2 |
| **52.5%** | Share of the 750k deficit concentrated in six provinces: **Madrid, Barcelona, Alicante, València, Murcia, Málaga** | 2021–2025 | ch.2 |
| **0.45** | Long-run **housing supply elasticity** for Spain (Caldera & Johansson 2013; Cavalleri et al. 2019). >1 in US/CA/SE, <0.2 in NL/CH. BdE calls 0.45 "an upper bound" for Spain today | structural | ch.2 |
| **>750,000 / 3.8% of households** | Transactions 2025, vs **5.5%** average in the 2004–07 boom. 2025 growth +5.1%, decelerating within the year (Q1 +14.7% → Q4 +0.6%). 90% second-hand. Legal persons = 10% of purchases | 2025 | ch.2 |
| **450,000** | Unsold dwellings left over from the 2000s boom (MIVAU estimate), stable since 2018 | stock | ch.2 |
| **27.1% / 9.9% / 11.9%** | Built non-residential-use dwellings potentially convertible to residential, % of stock: Spain 27.1, **Madrid 9.9**, Barcelona 11.9, Bizkaia 11.6. Rural extreme: Ourense 49.8, Soria 54.1, Ávila 58.2 | 2025 | Cuadro 2.7 |
| **3.8M / 400k** | Vacant dwellings (INE 2020 census); only 400k sit in municipalities >250,000 inhabitants | 2020 | ch.2 n.36 |

**Superseded figures — stop using these.** The ~600,000 deficit (Informe Anual 2023
cap.4; Gavilán presentation 23 Apr 2024, arithmetic 375k for 2022–23 + >225k for 2024–25)
and the **~275,000 households/yr** formation figure are IA2023 vintage. IA2025 replaces
them with **750k / 240–245k**. Both old figures are currently cited in `sources.md`
(rows for IA2023 cap.4, Gavilán, El Mundo) and in `plan.md`. Note that the OECD Economic
Survey of Spain 2025 still quotes the 600k vintage.

**IA2025 contains no forward-looking housing projection.** Grepping the whole chapter-2
line range for `2030|proyecci|se prevé|previsi|escenari` returns zero hits. The chapter is
explicitly diagnostic.

### Informe de Estabilidad Financiera / FSR, Primavera 2026 (published ~May 2026)

ES: https://www.bde.es/f/webbe/Secciones/Publicaciones/InformesBoletinesRevistas/InformesEstabilidadFinancera/26/IEF_Primavera2026.pdf
EN: `.../26/FSR_Spring2026.pdf`

| Number | Definition | Date | Location |
|---|---|---|---|
| **+12.7% nominal / +9.7% real** | House price growth, annual average 2025 (2024: 8.4 / 5.5). Real = INE IPV deflated by CPI | 2025 | ch.4 p.87 |
| **−14.7%** | Real prices at end-2025 relative to the 2007Q3 peak | 2025Q4 | ch.4 |
| **+10.2%** | Annualised q/q real price growth | 2025Q4 | ch.4, Annex Chart A2.4.1.1 |
| **Overvaluation 10–15%, average 12.9%** | Battery of **four** house-price imbalance indicators: (i) price gap vs long-term trend, (ii) price-to-income ratio gap, (iii) OLS model on disposable income + mortgage rates, (iv) error-correction model. BdE: level "similar to that observed in 2004" | **Dec 2025** | Chart 4.3.a. Verified numerically from the chart XLSX: min 10.05, average **12.92**; 2025Q3 12.56, 2025Q2 10.52, 2024Q4 6.48 |
| **Valuation sub-component 0.189** | Synthetic real-estate risk indicator, 0–1 scale. Components 2025Q4: real-estate activity 0.120, **valuation 0.189**, credit conditions 0.099, household financial position 0.045. Composite "similar to 2001, below both the 2000s boom onset and its 2007 peak" | 2025Q4 | Chart 4.3.b XLSX |
| **Asking rents +10% real (2024) → +5% real (2025)** | Real-estate-portal asking indices, real terms. BdE flags they lack INE statistical treatment | 2025 | ch.4 p.88 |
| House-price change under adverse scenarios | FLESB Box 5.2 Chart 6 plots baseline vs Brent-$145 vs Brent-$220 house-price change, **2026–27 average %**. Chart-only, **no XLSX published for Box 5.2** | 2026–27 | Box 5.2 — **values unverified** |
| Borrower-based-measures long-run effects | Figures 6.2/6.3: BBMs → lower ownership rate, **lower house prices**, **higher rents**, larger rental share. **Directional arrows only, no numbers** | long run | ch.6 pp.155–157 |

**Overvaluation estimates conflict across institutions and must not be averaged** — they
are different method sets: BdE **10–15%** (Dec 2025) vs ECB `RESV` four-method average
**20.75%** (2025Q4) vs European Commission valuation gap **10.0%** (2024) vs IMF "a mild
gap has opened up" (qualitative).

---

## 3. Prior art — BdE already has an agent-based housing model

The engine behind the IEF Primavera 2026 ch.6 borrower-based-measures analysis is:

> **Carro, A. (2023), "Taming the housing roller coaster: The impact of macroprudential
> policy on the household cycle", *Journal of Economic Dynamics and Control* 156, 104753.**

A BdE agent-based housing model. This is the closest institutional prior art to this
project and the most direct comparison target available — not for its *numbers* (BdE
publishes only directional arrows from it) but for its *mechanism design*: it is another
ABM in which borrower-based limits bind before preference, which is exactly this model's
"credit binds before preference" rule (`model-spec`, bank dossier).

Worth a deep read before further work on the bank actor or on any LTV/DSTI intervention.
Not yet read as of 2026-08-10.

---

## 4. Third-party Spanish house-price forecast panel

The comparison set that actually exists. All PDF-only.

### Institutions that publish a numeric Spanish house-price path

| Institution | Publication + date | Basis | 2026 | 2027 | 2028 | 2029 |
|---|---|---|---|---|---|---|
| **BBVA Research** | *Observatorio Inmobiliario — perspectivas y red eléctrica*, **28 Jul 2026** (renamed from *Situación Inmobiliaria*) | MIVAU **valor tasado**, nominal (also publishes real) | **+12.0** | **+5.7** | — | — |
| **CaixaBank Research** | *Informe Sectorial Inmobiliario 1S 2026*, **19–20 Mar 2026** (semiannual: Mar + Sep) | INE **IPV** (also publishes valor tasado: +10.0 / +5.0) | **+10.1** | **+5.5** | — | — |
| **Bankinter** | *Informe Sector Inmobiliario*, 16 Feb 2026; repeated in *Estrategia de Inversión 3T 2026* §3.3 | INE vivienda libre, nominal | +7.0 | +4.0 | — | — |
| **S&P Global Ratings** | *European Housing: Supply Shortfalls Limit Price Relief*, 13 Jul 2026 | INE IPV basis, nominal | +9.1 | +7.4 | +6.2 | +5.4 |
| **IMF / EBA baseline** | *Spain: Selected Issues 2026*, CR 26/103, 4 May 2026, Annex III Table 1 | Nominal. Path taken from the **EBA 2025 EU-wide stress test**, not IMF-generated | +7.6 | +6.7 | +4.9 | +4.9 (2030 also 4.9; 2025 8.5) |
| **IMF / EBA adverse** | same | Nominal stress path | — | — | **−4.3** | **−11.0** (2030 −5.6; cumulative **−17.2%** 2027Q2–2030Q2) |
| **European Commission** | **Alert Mechanism Report 2026**, SWD(2025)956, **25 Nov 2025** | Eurostat HPI (MIP scoreboard), nominal y/y | +8.0 | — | — | — |
| **Fitch** | *Global Housing and Mortgage Outlook 2026*, 8 Dec 2025 | Home prices, nominal | **+8 to +10** (highest in the GHMO) | — | — | — |

The **IMF/EBA baseline-plus-adverse pair is the single most useful entry**: longest horizon
(2025–2030), and it is the only published Spanish path with a matched crisis scenario —
directly comparable to running this model with a `CreditCrunch`-style intervention
(`validation.md` known gap: "2008-style bust reproduction untested end-to-end").

Source PDFs:
- BBVA: https://www.bbvaresearch.com/wp-content/uploads/2026/07/Perspectivas_y_electricidad.pdf
- CaixaBank: https://www.caixabankresearch.com/sites/default/files/content/file/2026/03/19/91184/is-immo-2026-1s_esp_acces_0.pdf
- Bankinter: https://broker.bankinter.com/www/es-es/cgi/broker+binarios?secc=ASES&subs=IESP&nombre=Sector_Inmobiliario.pdf
- S&P (paywalled at source; publicly mirrored): https://www.infobuild.it/wp-content/uploads/RatingsDirect_EuropeanHousing_SupplyShortfallsLimitPriceRelief_3593330_Jul-13-2026-1.pdf
- IMF Selected Issues (p.59): https://www.imf.org/-/media/files/publications/cr/2026/english/1espea2026002.pdf
- EC AMR 2026 (ES pp.52–54): https://commission.europa.eu/document/download/7e90444e-12c2-4702-b60e-719eb04b5eb3_en?filename=SWD_2025_956_1_EN.pdf
- Fitch release: https://www.fitchratings.com/research/structured-finance/most-european-housing-markets-to-see-steady-price-growth-in-2026-08-12-2025

Fitch mid-year update (25 Jun 2026) raised Spain; revised % **unverified** (paywalled).

### Non-price housing variables — only two forecasters cover them

Relevant because this model outputs transactions, completions and pipeline, not just
prices.

| Variable | BBVA (Jul 2026) | CaixaBank (Mar 2026) |
|---|---|---|
| Transactions / compraventas | −7.3% (2026), +0.6% (2027); 2027 "algo por encima de 700.000" | 714k actual 2025 → **695k (2026), 670k (2027)** |
| Visados obra nueva | +10.1% (2026), +12.6% (2027) | 139k → **150k (2026), 165k (2027)** |
| Housing starts / iniciadas | **153k (2026), 170k (2027)** vs 139k in 2025 | — |
| Residential investment, % GDP | 5.7% (2026), 6.0% (2027) | — |
| Net household formation | 223k (2026), 217k (2027) | — |
| Deficit | 700k (2025) | >900k by 2029 |

Note BBVA's formation path (223k/217k) runs **below** BdE's measured 240k for 2025, and
their deficit figure (700k) below BdE's 750k. Different definitions of net formation;
do not mix without reconciling.

### Institutions that do NOT forecast Spanish house prices (checked, so nobody re-checks)

| Institution | What was checked | Closest available proxy |
|---|---|---|
| **Funcas Panel** | *Panel de Previsiones de la Economía Española*, Jul 2026, 19 forecasters, bimonthly (Jan/Mar/May/Jul/Sep/Nov). **No house-price row** | **FBCF construcción** consensus 3.3 (2026) / 3.1 (2027), max 4.5/4.8, min 3.0/2.5. Cuadro 2 has quarterly Euríbor 1a: 2.80 (26Q2) → **2.54 (27Q4)**. https://www.funcas.es/wp-content/uploads/2026/07/PP2607.pdf |
| **AIReF** | *Presupuestos iniciales AAPP 2026*, 15 Apr 2026. **No house prices, no residential-investment row** — only aggregated "FBCF Construcción y Propiedad Intelectual" (4.4 for 2026). Viviendas iniciadas/terminadas appear as observed-data charts only | macro horizon to 2029 |
| **EC Spring Forecast 2026** | IP 341, 21 May 2026. **No house prices.** Table 10 = investment in construction, incl. civil engineering | ES construction inv. +4.5 (2026), +2.7 (2027). AMECO `OIGDW` (dwellings only): +4.40 / +2.65 |
| **OECD** | *Economic Survey of Spain 2025* (Nov 2025) is the only OECD product with a "Housing" row — housing GFCF **volume**, 3.7 (2026) / 3.5 (2027). **No price projection.** EO 119 (3 Jun 2026): `IHV` housing GFCF +4.32 / +3.16. Survey still cites the superseded BdE ≈600k deficit for 2022–25, and 345k permits 2022–24 vs 604k household creation | OECD *Analytical House Price Indicators* are **actuals**: ES 2026Q1 nominal +12.8% y/y, **real +9.8%**, price-to-income 127.0, **price-to-rent 166.6** (long-run avg 100; above the 2007 peak of 159.8) — `sdmx.oecd.org … DSD_AN_HOUSE_PRICES/ESP` |
| **IMF Article IV** | Spain 2026 Article IV, CR 26/102, 22 May 2026. No price row in Table 1; housing is narrative + Annex VII. "prices accelerated to about **13 percent** y/y"; "the price boom has **not so far led to major price misalignment, although a mild gap has opened up**". Recommends introducing LTV/DSTI limits within a year | https://www.bde.es/f/webbe/GAP/Secciones/SalaPrensa/InformacionInteres/Otros%20documentos/en/2026-05-22-FMI-ARTICULO4.pdf |
| Tinsa, idealista, Registradores, Notariado, CBRE, JLL, APCEspaña | Actuals and nowcasts only, **no numeric forecast** | Tinsa IMIE May 2026 **+15.4%**; Registradores 2025 compraventas **705,357** |
| FocusEconomics, Oxford Economics, Moody's Analytics, Consensus Economics | Do carry a real house-price consensus line, horizons to 10 yrs | **Values paywalled — unverified.** Do not backfill from tradingeconomics-style aggregators |

### Appraisal / asking-price forecasters (different basis — see §6)

Sociedad de Tasación, *Informe de Tendencias* (Jan + 30 Mar 2026), own survey ≈43k
dwellings, **asking €/m²**: new-build **€3,432/m², ≈+9%** H1 2026; new+used **≈+7.2%** at
mid-2026.
Gloval **+7%** (range 5.6–8.4); Singular Bank **+6% (2026), +4% (2027)**; pisos.com sale
**+7.8%**, rents **+6.8%**; Fotocasa rents **+7%**; UCI/SIRA survey (n=433) prices
**+3.15%**, rents **+5.05%**, compraventas −3.27% H2.

**Rents are forecast only by Fotocasa, pisos.com and UCI/SIRA — all sentiment-based, none
statistically treated.** No institution forecasts Spanish rents on a transacted basis. So
the model's rent path has no credible external benchmark; `rent_transacted_*` can only be
validated against history, not projection.

**No institution publishes regional or provincial forecasts.** The model's three-zone
output has no zone-level external benchmark either.

---

## 5. Machine-readable access

### Forecasts are PDF-only. Verified three ways.

1. The June 2026 release offers **exactly two files, both PDF** (report + infographic).
   No Excel, no CSV, no data annex.
2. Chart-data XLSX exist for the *Report* section but **not the Projections section**.
   Extracted link annotations from `be2601-ite.pdf`: only
   `AB261TR_InformeTrimestral_G09..G25_Ing.xlsx` — Report charts 9–25, including
   **G18 = housing**. Projection charts and tables have no XLSX. `be2602-ite.pdf` (the
   June update) has **zero** chart-data links.
3. Grepping all **14,113** series in BdE's `catalogo_be.csv` for
   `proyecci|previsi|forecast` returns 5 hits, all business-survey expectation balances.
   **No forecast series.** `catalogo_si.csv` returns 0.

**Consequence: any forecast used in this project must be hand-transcribed from a PDF,
stamped with the report date and the data cut-off date.** Treat a forecast row like a
sourced parameter (`plan.md`: units and a source, or it is labelled a guess) — the vintage
*is* part of the value, because these get revised hard (§6).

### BdE report chart data — XLSX per chart, machine-readable, all verified 200

| What | Example (verified) |
|---|---|
| Informe Anual 2025 ch.2 housing charts (14 files, `Cap_2_G01..G14`) | `https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesAnuales/InformesAnuales/25/Graficos/Fich/IA2025_Cap_2_G10.xlsx` (deficit vs household formation); `..._G11.xlsx` (cross-country deficit) |
| IEF/FSR Primavera 2026 | `https://www.bde.es/f/webbe/Secciones/Publicaciones/InformesBoletinesRevistas/InformesEstabilidadFinancera/26/IEF0126_G4.3_Ing.xlsx` (overvaluation, quarterly from 1970Q1, 1,672 rows). Also `G4.2`, `G4.4`–`G4.7`, `G5.1`, `G5.3`, `G6.1`. `_Ing` = English; drop the suffix for Spanish |
| Quarterly report | `http://www.bde.es/f/webbe/SES/Secciones/Publicaciones/InformesBoletinesRevistas/BoletinEconomico/26/T1/Graficos/Files/AB261TR_InformeTrimestral_G18_Ing.xlsx` |

**How these were found**: PDF link annotations behind the "DOWNLOAD" / "DESCARGAR" labels.
They are **not indexed anywhere on the site** — you must parse the PDF's `/Annots`
`/URI` entries. Record this; it is the only route.

### BdE bulk statistics — machine-readable, verified 200

| Endpoint | Content |
|---|---|
| `https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/catalogo_be.csv` | Series catalogue, 14,113 series, 10.4 MB |
| `https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/catalogo_si.csv` | Síntesis de Indicadores catalogue |
| **`https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/si_1_5.csv`** | **Housing-market synthesis, 92 series**: IPV total/new/used, €/m², transactions, mortgage flows, LTV/LTP, construction costs, visados, household debt, affordability. **Single best BdE housing file** — this is the machine-readable form of the `Síntesis de Indicadores 1.5` row already in `sources.md` |
| `.../csv/be1901.csv` | Mortgage reference rates / Euribor |
| `.../csv/be0412.csv`, `be0413`, `be0414`, `be0417` | Credit to households for house purchase / renovation |
| `.../csv/be2307.csv`, `be2308`, `be2309`, `be2507` | Housing starts / visados; construction costs |
| `.../xlsx/si_1_5.xlsx` | XLSX twin — swap `csv/X.csv` → `xlsx/X.xlsx` |
| `.../zip/be.zip` (8.95 MB), `.../zip/be04.zip` | Whole Boletín Estadístico / per chapter |
| `https://www.bde.es/webbe/es/estadisticas/recursos/descargas-completas.html` | Bulk-download index |
| `https://www.bde.es/webbe/es/estadisticas/compartido/docs/manual_archivos_csv.pdf` | CSV layout spec |

Gotchas, all learned the hard way:
- Path prefix is **`/webbe/`** for data files. `/wbe/` is HTML pages; the old `/webbde/` is
  dead.
- Encoding is **ISO-8859-1**, not UTF-8.
- Layout is **transposed wide**: series as columns; rows 1–6 metadata, then `ENE 1970` …
  `JUL 2026` date rows with `_` for missing *and* for the non-quarter months of quarterly
  series; last two rows `FUENTE` / `NOTAS`.
- Validate filenames before trusting them — `be150a.csv` 404s despite appearing in the
  catalogue.

### BdE API — exists, proprietary JSON, no SDMX

Docs: https://www.bde.es/webbe/es/estadisticas/recursos/api-estadisticas-bde.html
Base: `https://app.bde.es/bierest/resources/srdatosapp/`

- `…/favoritas?idioma=es&series=D_1NBAF472` → latest value (verified: Euribor 1y = 2.855,
  Jul-2026)
- `…/listaSeries?idioma=es&series=DHIENA2025IPVUVT_TTVA.T&rango=MAX` → full series +
  metadata (verified: IPV y/y, 77 observations)
- Params: `idioma=es|en`; comma-separated `series=` (URL-encode `#`→`%23`, `%`→`%25`);
  `rango=MAX|30M|60M|2024`
- Gotchas: responses are **gzip regardless of `Accept-Encoding`** → must send
  `--compressed`; send a browser UA. **No search endpoint, no OpenAPI** → pair with
  `catalogo_be.csv` as the lookup table. Real-estate series sit under DSD
  `BDE_BHI` / `BDE_DHI`.

### ECB SDMX 2.1 — the better route for BdE-sourced housing series

`https://data-api.ecb.europa.eu/service/data/{DATAFLOW}/{KEY}?format=csvdata&lastNObservations=N`

Provider code **`ES2` = Banco de España**, so these are BdE numbers with a sane API in
front of them.

| Key | Content | Latest verified |
|---|---|---|
| `RESR/Q.ES._T.N._TR.TVAL.ES2.TB.N.IX` | Spain HPI, quarterly, **provider BdE** (Bol. Est. T25.7 col 8) | 2025Q4 = 151.17 |
| `RESR/Q.ES._T.N._TR.TVAL.4D0.TB.N.IX` | Spain HPI, Eurostat — freshest | 2026Q1 = 107.45 |
| `RESR/Q.ES._T.N.NTR/.XTR.TVAL.ES2.TB.N.IX` | New / existing dwellings, BdE | 2025Q4 = 149.96 / 151.39 |
| `RESR/A.ES.ES30.N._TR.TVAL.5A0.TB.N.IX` | **NUTS2 regional HPI** — all 19 CCAA (`ES11`…`ES70`) | 2024 |
| `RESH/A.ES._T.N._TR.TOOT/.TRAT/.TRAP/.TRAS.ES2._Z.N.RO` | Ownership 73.3%, rental 20.2%, private 16.7, social 3.5 | 2025 |
| `RESH/A.ES._T.N.NTR.HSTA/.HCOM.ES2._Z.N._Z` | Starts 137k / completions 92k | 2025 |
| `RESH/A.ES._T.N._TR.NTRA/.PRHH/.NPRO.ES2._Z.N._Z` | Transactions 752k / households 19,760k / stock 25,106k | 2025 |
| `RESH/A.ES._T.N._TR.VACR.ES2._Z.N.RO` | Vacancy 14.41% | 2021 |
| `MIR/M.ES.B.A2C.A.R.A.2250.EUR.N` | **Mortgage rate, new business, house purchase** | 2026-06 = **2.89%** |
| `BSI/M.ES.N.A.A22.A.1.U6.2250.Z01.E` | Outstanding stock, lending for house purchase, EUR mn | 2026-06 = **521,524** |
| `RESV/Q.ES._T.N._TR.RVAV.4F0._Z._Z.PT` | ECB over/undervaluation, 4-method average | 2025Q4 = **+20.75%** |
| ~~`RPP/Q.ES.N.TD.00.3.00`~~ | **Do not use** — Spain ends 2018Q4; dataflow superseded by `RESR` | — |

Wildcards require the exact dot count (RPP 6, RESR/RESH 10).

The `RESH` block maps almost one-for-one onto `metrics.py` outputs — ownership rate,
tenant share, transactions, vacancy, stock, households — which makes it the natural
validation feed, superseding hand-copied figures.

### ECB MPD — the only machine-readable forecast route, and it has no housing

`https://data-api.ecb.europa.eu/service/data/MPD/A.ES.YER.A.A25.0000?format=csvdata`

Verified: returns Spain real GDP growth **including future years — 2026 = 2.17,
2027 = 1.93, 2028 = 1.80**, labelled "Autumn/December 2025 staff macroeconomic
projections". Vintage-tagged via `PD_ORIGIN` (`A02`–`A25` autumn, `G02`–`G26` spring;
latest `G26`), so it is fully reproducible — the one forecast source that does not need
hand-transcription.

**But Spain has only 3 items: `YER` (real GDP), `HIC` (HICP), `URX` (unemployment).** No
house prices, no mortgage rates, no residential investment. ECB SPF is euro-area only
(`SPF/Q.ES...` → 404).

### INE JSON API — companion, no key needed

`https://servicios.ine.es/wstempus/js/ES/{FUNCTION}/{ID}?nult=N`, UTF-8, plain JSON.

- `DATOS_TABLA/80270?nult=1` → **IPV quarterly by CCAA**, general/new/used, 240 series
  (2026Q1 national index 107.458)
- `TABLAS_OPERACION/IPVA` → rent index tables **59056** (CCAA), **59058** (provincial),
  **59060** (municipal >10k inhabitants), **59061** (districts of provincial capitals) —
  **best zone-level rent input available**, and the natural feed for the three-zone split
- `OPERACIONES_DISPONIBLES` → IPV = id 15, IPVA = id 432

---

## 6. Cross-cutting cautions

### Index families are not interchangeable

Four different things get called "the Spanish house price". Any comparison that mixes them
is meaningless.

| Family | What it measures | Who forecasts on it |
|---|---|---|
| **INE IPV** | Notarial **transaction** prices, nominal. Rebased **2025=100 from Q1 2026**. Feeds Eurostat HPI → EC MIP indicator | CaixaBank, Bankinter, S&P, Fitch |
| **MIVAU/MITMA valor tasado** | **Appraisal** value. Published nominal + real | BBVA |
| **Appraisal indices** (Tinsa IMIE, Gloval, Gesvalt) | Appraiser panels. Running **above** INE through 2025–26 | Gloval |
| **Asking prices** (Sociedad de Tasación, idealista, Fotocasa, pisos.com) | Advertised, systematically above closing, different composition. **Not comparable to anything else** | ST, pisos.com, Fotocasa |

This maps onto a distinction the model already makes: `validation.md` notes the model's
price index is a quality-adjusted **transaction** index (IPV-like) while the rent index
agents observe is an **asking** basis (idealista-like), with `rent_transacted_*` as the
SERPAVI-like contract series. So model price → compare against IPV-basis forecasters
(CaixaBank/S&P/Fitch), **not** BBVA's valor tasado.

### Realised actuals — the anchors that matter more than any forecast

- INE IPV **2026Q1 +12.9% y/y** (nueva +9.1, segunda mano +13.5, +3.5% q/q)
- Eurostat/INE annual: 2022 7.4, 2023 4.0, 2024 8.5, **2025 12.7**
- MIVAU valor tasado 2026Q1 **+13.9%**
- MITMA visados obra nueva 2025 **139,016 (+8.8%)**

### The panel systematically under-forecast, so it is not a validation target

Every 2026 forecast except BBVA (12.0) and CaixaBank (10.0–10.1) sits **below** realised
2026Q1 (+12.9%). BBVA revised 9.0 → 10.2 → 12.0 and CaixaBank 6.3 → 10.0 within two
vintages. EC AMR 2025 projected 2.0/3.0 for 2024/25 against actuals of 8.5/12.7 — a large
miss.

**Do not use any third-party forecast as a baseline validation target. Use realised INE
IPV.** The forecast panel is useful as a *range of contemporary expectations* — "our model
projects X, the professional panel projects 5.5–12.0" — and nothing stronger. If the model
lands outside the panel that is not automatically a model failure.

### Reusable findings for other modules

Two things surfaced that are directly useful elsewhere in the model:

- **Zone migration elasticities.** IMF WP/26/065 (3 Apr 2026) gives Bartik-IV migration
  elasticities across 50 Spanish provinces, 2007–2023: **+10% destination prices → −4.0%
  in-migration; +10% origin prices → +2.8% out-migration**; **rents matter more than sale
  prices**. Directly relevant to the zone/migration module.
  https://www.imf.org/-/media/files/publications/wp/2026/english/wpiea2026065-source-pdf.pdf
- **The rent-cap wedge, measured.** CaixaBank's rent nowcast, built from direct-debit
  receipts, splits **renewed contracts <3% y/y** from **new contracts >10% y/y**. Best
  free evidence on the renewal/new-contract wedge, which is the exact mechanism a rent cap
  operates through (`docs/experiments/rent-cap.md`).
  realtimeeconomics.caixabankresearch.com

---

## 7. What wiring this in would require (not built)

Recorded so the design decision is not re-derived.

1. **A calendar anchor.** The model is tick-based with no start date — nothing aligns to
   2026/2027. Needs a `start_year` on config, tick 0 = Q1. Reporting convention only, no
   behavioural effect; belongs in `config.py` (how the world works), not `scenario.py`.
2. **A forecast panel as sourced data**, hand-transcribed, each path carrying institution,
   price basis, vintage date and URL — because §5 says there is no machine-readable route.
   Typed dataclasses, per project convention; no dicts as informal records.
3. **A metrics function**, `metrics.py` only: quarterly price index → calendar-year mean
   % change, then model-vs-panel. The UI must not compute it inline.
4. **Separate from `validation.md`.** That file reproduces history and gates scenario
   reporting. A forecast comparison is a benchmark with no pass/fail — mixing them would
   make a forecast miss block scenario reporting, which §6 shows would be wrong.

Highest-value follow-up regardless of whether the comparison gets built: **read Carro
(2023)** (§3), and **switch the validation feed to ECB `RESH`/`RESR`** (§5), which covers
ownership rate, tenant share, transactions, vacancy and stock with a stable API instead of
hand-copied figures.

---

## Provenance

Research date 2026-08-10. All URLs fetched on that date unless a row says otherwise.
Numbers marked **(unverified)** were visible only in paywalled or chart-only material and
must not be used until confirmed. Sources registered in `sources.md`.
