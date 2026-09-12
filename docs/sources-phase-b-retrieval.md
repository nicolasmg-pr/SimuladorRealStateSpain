# Phase-B source retrieval — staging file

Retrieval pass for the §9 priority list of
`docs/superpowers/specs/2026-09-11-model-redesign-design.md`, run **2026-09-12**.
Every row below is destined for `docs/sources.md`; this file is a **staging area only** so
that the merge into the register is a separate, reviewable step. `docs/sources.md` was not
edited.

Conventions follow the register: Tier 1 = raw statistical series or microdata; Tier 2 =
interpretive report, never usable alone. The `Fetched` column distinguishes `(fetched)` —
the document was downloaded and read — from `(search)` — only a search snippet was seen —
and records the blocking error where a fetch failed. **Nothing in this file is reconstructed
from memory.** Where a figure could not be pulled out of a source, the row says so instead
of supplying a number.

Three rows below are **extensions of rows that already exist** in `docs/sources.md`
(BdE DO 2432, CBRE Living Figures, EFF/DO 2610). They are marked `EXTEND` and must be merged
into the existing row, not appended as duplicates.

---

## Tier 1 — statistical series

| Source | Institution | Series / dataset | Granularity | Period | URL | Fetched |
|---|---|---|---|---|---|---|
| EMCR tabla 69753 — Migraciones intermunicipales por año, tamaño del municipio de procedencia y tamaño del municipio de destino | INE (govt statistical office) | Full 6×6 origin-size × destination-size internal-migration matrix, persons. Size bands: ≤10.000 / 10.001–20.000 / 20.001–50.000 / 50.001–100.000 / >100.000 no capital / capitales de provincia. Net flows computed from it in the block below | National, by municipality-size band | 2021–2024 (last update 11/12/2025) | https://www.ine.es/jaxiT3/Tabla.htm?t=69753 (CSV: https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/69753.csv) | 2026-09-12 (fetched — CSV downloaded and parsed, 10.7 kB, 48 cells × 4 years) |
| EVR microdatos, ficheros anuales `datos_YYYY.zip` | INE (govt statistical office) | Residential-variation microdata, one record per registration. Variables `TAMUALTA` / `TAMUBAJA` carry the size band of destination / origin municipality already coded 1–6 (1 = no capital ≤10.000 … 5 = no capital >100.000, 6 = capital de provincia); blank = abroad. Record design: `disreg_vr.xlsx` / `dr_EVR_YYYY.xlsx` inside each zip | Person-level; aggregable to any municipality-size classification | 2015–2021 verified present (series runs from 1988; EVR discontinued after 2021) | https://www.ine.es/ftp/microdatos/varires/datos_2020.zip (pattern `datos_<year>.zip`); record design https://www.ine.es/ftp/microdatos/varires/disreg_vr.xlsx | 2026-09-12 (fetched — 2015, 2016, 2017, 2018, 2019, 2020, 2021 downloaded and the size×size matrix computed for each) |
| EVR tabla tpx 53130 — Variaciones por tamaño del municipio de destino y tamaño del municipio de procedencia | INE (govt statistical office) | Published 2021 cross-tab, same matrix as the microdata computation — used as a check on our own aggregation | National, by size band, by nationality | 2021 only (one table per edition year) | https://www.ine.es/jaxi/Tabla.htm?tpx=53130 (CSV: https://www.ine.es/jaxi/files/tpx/es/csv_bdsc/53130.csv) | 2026-09-12 (fetched — CSV downloaded; 2021 interior total 1.678.649 matches our microdata aggregate exactly) |
| EMCR tabla 69767 — Saldos por municipio, año, sexo y tipo de saldo | INE (govt statistical office) | Net migration balance per municipality, splitting exterior from intermunicipal | Municipality, annual | 2021–2024 | https://www.ine.es/jaxiT3/Tabla.htm?t=69767 | 2026-09-12 (identified on the INEbase results index; table itself not downloaded) |
| Síntesis de Indicadores 1.5 — Indicadores del mercado inmobiliario, serie `D_TKR60REA_VIV_IPV` | Banco de España (central bank) | **Rentabilidad de la vivienda bruta por alquiler, acumulado en los doce últimos meses**, %, quarterly. 2014Q1 4,59 → peak 2014Q2 4,65 → 2019Q4 3,79 → 2021Q4 3,67 → 2024Q4 3,31 → 2025Q4 3,05 → 2026Q2 2,90. Monotone compression across the whole 2014–26 boom: −175 bp from the 2014Q2 peak (4,65 → 2,90), −37,6 % in relative terms | National, quarterly | 2013Q1–2026Q2 (edition stamped 10-Septiembre-2026) | PDF https://www.bde.es/webbe/es/estadisticas/compartido/datos/pdf/si_1_5.pdf · machine-readable CSV https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/si_1_5.csv (also `.xlsx`) | 2026-09-12 (fetched — CSV downloaded, 688 rows × 75 series, full series extracted) |
| Síntesis de Indicadores 1.5, serie `D_TKR600RV_VIV_IPV` | Banco de España (central bank) | **Rentabilidad anual de la vivienda = alquiler más variación de precios**, %, quarterly — the left-hand side of the §7.1 arbitrage condition measured directly. 2013Q1 −10,34 → 2014Q4 +6,48 → 2019Q4 +7,44 → 2021Q4 +10,09 → 2024Q4 +14,60 → 2025Q4 +15,96 → 2026Q1 +15,84 | National, quarterly | 2013Q1–2026Q1 | same CSV as above | 2026-09-12 (fetched) |
| Síntesis de Indicadores 1.5, serie `D_G0B1F0ZP` | Banco de España (central bank) | Bonos y obligaciones del Estado no segregados, 10 años, mercado secundario, %, monthly — the `i_bond` term of §7.1. 2014-12 1,610 · 2016-09 0,991 · 2020-12 0,037 · 2022-09 3,369 · 2025-12 3,287 · 2026-08 3,734 | National, monthly (daily source) | 1970– (2013– extracted) | same CSV as above | 2026-09-12 (fetched) |
| EFF 2024, Cuadro 3 — Tenencia de activos reales por tipo de activo y características de los hogares | Banco de España (central bank, survey) | **Otras propiedades inmobiliarias by net-wealth percentile** — % of households owning, and median value (miles € de 2024) for owners. Full gradient in the block below. Headline: 45,3 % of all households, rising from 8,7 % in the bottom wealth quartile to 92,0 % in the top decile | National, household survey, by net-wealth percentile | EFF 2024 (fieldwork end-2024), EFF 2022 column alongside | Published as Cuadro 3, p. 23 of https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesSeriadas/DocumentosOcasionales/26/Fich/do2610.pdf | 2026-09-12 (fetched — PDF downloaded, Cuadro 3 reconstructed from the content stream; see caveat below) |

### Computed from INE migration sources — net internal migration by municipality size

Both blocks are **our own aggregation**, not a published INE table. Method: count records by
(`TAMUBAJA`, `TAMUALTA`) and take inflow − outflow for each band, restricted to records where
both ends are Spanish municipalities (interior migration only; records with a blank origin or
destination band are arrivals from / departures to abroad and are excluded).

EVR microdata, persons, interior migration only:

```
band                     2015      2016      2017      2018      2019      2020      2021
<=10,000              -26,865   -18,794    -7,674   +15,173   +14,075  +106,294   +55,563
10,001-20,000            +698    +4,748    +3,404    +7,877    +8,862   +21,842   +14,730
20,001-50,000          +8,398    +8,859    +8,169   +10,085   +10,982   +17,845   +13,220
50,001-100,000         +2,858    +2,552       +12      -574      -526    -5,802    +7,264
>100,000 non-capital   +1,839    +2,455      +846    -1,444    -3,993   -22,583   -10,849
provincial capital    +13,072      +180    -4,757   -31,117   -29,400 -117,596   -79,928
gross interior      1,554,413 1,479,117 1,499,820 1,609,124 1,649,351 1,519,606 1,678,649
```

EMCR table 69753, persons, interior migration only (different statistic, census-consistent —
see note):

```
band                     2021      2022      2023      2024
<=10,001              +55,085   +33,555   +25,694   +32,679
10,001-20,000         +14,541    +7,391   +11,755   +15,329
20,001-50,000         +11,626    +7,379   +10,701   +12,737
50,001-100,000         +6,547      +806      +696    -5,148
>100,000 non-capital  -11,990    -8,722    -4,195      -402
provincial capital    -75,809   -40,409   -44,651   -55,195
gross interior      1,670,717 1,725,546 1,719,908 1,754,162
```

Notes that matter for §7.5:

- **The 2020–22 reversal is fully covered and is a clean natural test.** Provincial capitals
  went from a net *gain* of +13,072 in 2015 to −29,400 in 2019 to **−117,596 in 2020** (4.0×
  the 2019 outflow), while municipalities ≤10,000 went from −26,865 (2015) to +14,075 (2019)
  to **+106,294 (2020)** (7.6× the 2019 inflow). Gross interior flows *fell* 7.9 % in 2020
  (1,649,351 → 1,519,606), so 2020 is a pure redirection of a shrinking flow, not a volume
  surge — which is what makes it identifying.
- **The reversal decays but does not undo.** Capitals: −79,928 (2021 EVR) → −40,409 (2022) →
  −44,651 (2023) → −55,195 (2024). Small municipalities: +55,563 → +33,555 → +25,694 →
  +32,679. By 2024 neither has returned to the 2015 pattern.
- **Two statistics, one overlapping year.** EVR ends with 2021, EMCR begins with 2021. For
  2021 they give capitals −79,928 (EVR) vs −75,809 (EMCR) and ≤10k +55,563 vs +55,085 — a
  0.9–5 % gap. The two are therefore chainable, but the join must be declared and 2021 used
  as the calibration point, not spliced silently.
- The band `≤10.000` in EVR and `Menos de 10.001` in EMCR are the same band under different
  labels; `provincial capital` is a *type*, not a size, and overlaps the size bands by
  construction — a capital of 40,000 inhabitants is counted as a capital, not in the
  20,001–50,000 band.

### Computed from EFF 2024 Cuadro 3 — "Otras propiedades inmobiliarias" by net-wealth percentile

Percentage of households owning, and median value for owners in thousands of 2024 euros:

```
net-wealth pct   own other RE (%)   median value (k€)     own main residence (%)
< 25                     8.7               19.9                    15.6
25–50                   34.9               39.5                    79.8
50–75                   55.4               79.2                    92.4
75–90                   75.7              175.9                    94.8
90–100                  92.0              409.9                    94.6
all households          45.3              110.0                    70.6
```

EFF 2022 column of the same table, for the change: <25 7,8 · 25–50 36,9 · 50–75 57,7 ·
75–90 79,8 · 90–100 92,7 · all 46,8.

**Two caveats, both unresolved and both to be carried into the register:**

1. `docs/sources.md` currently records "36.1 % own other real estate (2022) — revised to
   45.3 % in the 2024 wave". DO 2610's own EFF-2022 column of Cuadro 3 reads **46,8 %**, not
   36,1 %. Either the 36,1 % came from a different definition or from the pre-revision
   EFF-2022 publication (DO 2413), which was not fetched in this pass. Recorded as a conflict;
   not resolved.
2. "Otras propiedades inmobiliarias" is *not* "owns a second dwelling". A search snippet from
   press coverage of the same wave puts households owning a property that is not their main
   residence at **33,7 %** and households owning land/fincas at **13,6 %**; 45,3 % is the union
   over all non-main-residence real estate (other dwellings, land, garages, premises). §7.3
   needs the dwelling basis, so 45,3 % is an upper bound on the buy-to-let-capable population
   and 33,7 % the closer figure. The 33,7 % / 13,6 % split was **seen only in a search
   snippet** and must be verified against Cuadro 3's disaggregation before use.
3. The table reconstruction is honest but indirect: DO 2610's tables are drawn as rotated
   text and no PDF renderer was available in this environment, so the numbers were recovered
   by decoding the page content stream and un-reversing the glyph order. The reconstruction
   was validated against three figures DO 2610 states in prose (70,6 % main residence,
   45,3 % other real estate, 98,8 % some asset) and reproduces all three. Anyone merging this
   should still spot-check one row against a rendered PDF.

---

## Tier 2 — interpretive / industry

| Source | Institution | Viewpoint | Topic | URL | Fetched | Triangulated against |
|---|---|---|---|---|---|---|
| NdP "La rentabilidad de la vivienda en España cae y cierra 2025 en 5,9 %" (27 Jan 2026) | Fotocasa / Fotocasa Group | industry portal (asking-price basis, landlord-facing) | **20-year national gross-yield series**: 2006 3,9 · 2007 4,0 · 2008 4,1 · 2009 4,4 · 2010 4,3 · 2011 4,3 · 2012 4,6 · 2013 4,8 · 2014 5,0 · 2015 5,3 · 2016 5,5 · 2017 6,2 · 2018 6,2 · 2019 6,6 · 2020 6,8 · 2021 6,5 · 2022 6,5 · 2023 6,4 · 2024 6,7 · 2025 5,9. Plus a **province panel for 2015 / 2020 / 2024 / 2025** covering ~50 provinces (e.g. Madrid 5,4 → 5,5 → 5,8 → 4,8; Barcelona 5,8 → 6,0 → 7,8 → 7,4; Illes Balears 5,6 → 4,8 → 4,6 → 4,2; Zamora 4,1 → 5,3 → 8,1 → 9,7), a CCAA panel on the same four years, and district/neighbourhood panels for Madrid and Barcelona. Basis: December asking sale price ÷ December asking rent | https://s36360.pcdn.co/wp-content/uploads/2026/01/NdP_Espana_Rentabilidad-de-la-vivienda-2025.pdf | 2026-09-12 (fetched — 19-page PDF, all seven tables extracted) | BdE RBA `D_TKR60REA_VIV_IPV` (central bank, contract-stock basis — **disagrees in sign over 2014–20**); idealista quarterly yields (portal, asking basis, agrees in level) |
| Rentabilidad-vivienda tag index, quarterly national gross yield | idealista | industry portal (landlord-leaning) | National gross yield by quarter as stated in article headlines: 2021Q1 7,2 · 2021Q4 6,9 · 2023Q4 7,1 · 2024Q1 7,3 · 2024Q2 7,5 · 2024Q3 7,2 · 2024Q4 7,2 · 2025Q1 7,3 · 2025Q2 7,2 · 2025Q3 6,9 · 2025Q4 6,7 · 2026Q1 6,7 · 2026Q2 6,5. The tag index carries nothing before 2021 | https://www.idealista.com/news/etiquetas/rentabilidad-vivienda | 2026-09-12 (fetched — tag index page; values read from article titles, the individual quarterly articles were **not** opened, so each figure is a headline, not a verified table) | Fotocasa annual series (portal, same direction from 2024, ~0,5–0,8 pp higher in level); BdE RBA (central bank, half the level) |
| **EXTEND** DO 2432 §3.3, *El mercado del alquiler de vivienda residencial en España* | Banco de España | central bank | Adds to the existing row: (a) the RBA is built from **AEAT declared rents for the stock of let dwellings ÷ Registradores transaction prices, per m²**, and is therefore a *sitting-contract* yield, explicitly below the entry yield; (b) BdE's own estimate of the **entry (new-contract) gross yield since 2015 is a range of 6,5 %–7,5 %** — which reconciles the central-bank and portal numbers as two different objects rather than a dispute; (c) IRPF on rental income reduces the RBA by **0,5 pp (bottom bracket) to 1,25 pp (top brackets)**, and by **0,3–0,8 pp on the 2011–2022 average**; (d) gross yields are **higher where household income and purchase prices are lower** — the zone gradient, stated qualitatively | https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesSeriadas/DocumentosOcasionales/24/Fich/do2432.pdf | 2026-09-12 (fetched — PDF text layer extracted; see "Not retrieved" for the one figure that would not come out) | Fotocasa/idealista entry-basis yields 6,5–7,5 (portal) sit exactly inside BdE's own entry-yield range; AEAT viviendas-declaradas statistic (Tier 1, already registered) is the underlying rent source |
| **EXTEND** Living, market data — Figures Q1 2026 Spain | CBRE | industry (consultancy) | Prime multifamily yields **stable in Q1 2026 at 3,8 % Madrid and 4,0 % Barcelona**. Against BdE's 10-year bond at 3,546 % (March 2026 monthly value, series `D_G0B1F0ZP`) this implies a prime residential spread of roughly **+25 bp Madrid / +45 bp Barcelona** — i.e. π at the prime end is close to zero once `E[g]` is excluded, which is a strong constraint on §7.1 | https://www.cbre.es/en-gb/insights/figures/living-market-data-figures-first-quarter-2026-spain | 2026-09-12 (unverified — values from a search snippet; **HTTP 403 on fetch** of cbre.es) | BdE bond series (Tier 1, fetched); existing CBRE Living Figures row Q4-2024/Q1-2026 in `sources.md` (same numbers, independently) |

### The §7.1 falsification test is source-dependent — record this, do not average it

The spec's compression test ("gross yields fall when expected appreciation rises; national
gross yield falls over the 2014–25 boom") gets **opposite answers** from the two best series:

| Basis | 2014 | 2020 | 2025 | Verdict on 2014–25 |
|---|---|---|---|---|
| BdE RBA — sitting contracts, AEAT rents ÷ Registradores prices | 4,65 % (Q2) | 3,70 % (Q4) | 3,05 % (Q4) | compresses throughout, −160 bp |
| Fotocasa — December asking rent ÷ asking price | 5,0 % | 6,8 % | 5,9 % | *rises* to 2020, compresses only from 2021 |
| idealista — asking basis | n/a | n/a | 6,7 % | compresses only from 2024Q2 (7,5 → 6,5) |

They measure different things — a stock of rent-regulated sitting contracts against the
marginal advertised unit — and the divergence is largest exactly in 2014–20, when new-contract
rents were rising much faster than the regulated stock. Per the project's bias rule this is a
**parameter range, not a number to resolve**: the compression target for §7.1 should be stated
as a band whose sign is unambiguous only from 2021 onwards, and the pre-2021 sign must be
declared an open question rather than a passed test.

---

## Not retrieved

| Item | What was tried | Why it failed | What it blocks in phase B |
|---|---|---|---|
| **idealista gross/net rental-yield series by province, 2014–2026** (§7.1, §7.3, priority 2) | idealista/news rentabilidad tag index (fetched); targeted searches for an idealista historical series or informe; the existing Q4-2025/Q1-2026 cross-section in `sources.md` | idealista does not publish a yield *series*. It publishes one press note per quarter with a current cross-section; the tag index reaches back only to 2021 and carries no province history. No downloadable dataset was found | The province-level within-zone test of §7.1 (yield vs expected appreciation in provincial cross-section over time). **Partly unblocked**: the Fotocasa province panel for 2015 / 2020 / 2024 / 2025 covers ~50 provinces at four dates on the same asking basis, which is enough to sign the within-province correlation but not to band the year-by-year compression path |
| **Net rental yield and the operating-cost share `c`** (§7.1, priority 3) | DO 2432 §3.3 fetched and text-extracted in full | The sentence quantifying it — "los gastos declarados como deducibles en el IRPF por los particulares que arriendan viviendas supondrían, en promedio, una reducción …" — has its figure on a line that the PDF text layer drops. The *tax* wedge came out (0,5–1,25 pp by bracket; 0,3–0,8 pp on the 2011–2022 average); the *cost* wedge did not. **No number is recorded rather than a guessed one** | `c` in `r_req = V·(i_bond + π − E[g]) / (12·(1−c))` has no sourced value. AEAT's *cuenta de resultados del arrendamiento* rows already in `sources.md` (FY2021 2,24 M declarants / mean net €4.503; FY2022 2,37 M / €4.844) give net income but not the gross-to-net ratio, so `c` cannot be derived from them either. §7.1 and §7.2 cannot be coded with a sourced `c` until this is retrieved — the AEAT statistic's gross-income column is the obvious next place to look |
| **BdE RBA zone / risk gradient as numbers** (§7.1, priority 3) | DO 2432 (fetched); AEAT *Estadística de viviendas declaradas en el IRPF* (already registered, landing page only) | DO 2432 states the gradient only qualitatively ("higher gross yields where household income and purchase prices are lower"); its district-level RBA chart data is not in the text layer. The AEAT statistic that would give gross yield by CCAA/province/municipality/postcode was not queried in this pass | The zone gradient of π in §7.1 and the derivation of the yield ladder as a prediction rather than a config value. The AEAT statistic is the right Tier 1 route and is already registered — it just needs to be pulled |
| **CBRE / Savills prime residential yield *series* vs sovereign spread** (§7.1, priority 6) | cbre.es Living Figures Q1 2026; en.savills.es "Rental growth and yields"; searches for a Savills Spain residential yield table | **HTTP 403 on both cbre.es and en.savills.es.** Only a single current cross-section (Madrid 3,8 % / Barcelona 4,0 %, Q1 2026) survives, from a search snippet. Neither house publishes a free historical residential yield series; the Savills Spain material found was rent- and capital-growth, not yields | A time-varying π. What *is* available is the sovereign leg: BdE `D_G0B1F0ZP` monthly 1970– is fetched and in the register, so π can be bounded at a point in time (≈ +25 to +45 bp prime, Q1 2026) but not tracked through the cycle. §7.1 should therefore treat π as a constant-with-zone-gradient parameter and declare it, rather than claim a cyclical π |
| **Registradores: non-resident purchases, quarterly series 2007–2026** (§7.4, priority 7) | `eri_2t_2026` and `eri_4t_2025` PDFs downloaded (9,3 MB / 7,6 MB); `eri_1t_2026` returns 404; registradores.org/analisis-estadistico 404; searches for an open-data file | The ERI PDFs use CID-encoded Type0 fonts with hex string operators, so the text layer will not extract without the embedded ToUnicode CMaps, and no PDF renderer is installed in this environment. No CSV/Excel series is published. Only the most recent quarters are available, and only through press notes already in `sources.md` (2026Q2 15,98 % ≈ 26.800 operations, record; 2025Q4 13,5 % ≈ 24.200; 2026Q1 ≈ 24.800) | The §7.4 falsification test — "if Registradores' non-resident purchase series tracks Spanish transaction volume one-for-one 2007–2025, the exogenous treatment is wrong". Three quarterly points cannot test co-movement over a cycle. Unblocking needs either a PDF renderer (poppler) to read the ERI charts and tables, or the INE *Transmisiones de Derechos de la Propiedad* foreign-buyer breakdown as a substitute Tier 1 series |
| **INE EMCR coverage of 2020** | EMCR table 69753 (fetched) | EMCR begins in **2021**. The pandemic year is only in the predecessor EVR | Nothing — resolved. The EVR microdata route covers 2015–2021 including 2020, and 2021 exists in both statistics as a join point. Recorded here only so the next reader does not repeat the search |
| **AEAT IRPF: taxpayers declaring rental income** (§7.3, priority 5) | Existing register rows re-read | **Already registered; nothing added.** `docs/sources.md` carries FY2024 (3,26 M declaring net rental income; 2,24 M taking the housing-rental reduction), FY2022 (2,37 M declarants, mean net €4.844) and FY2021 (2,24 M, mean €4.503), all fetched 2026-08-07. These answer §7.3's anchor as stated | Nothing. One gap worth noting: **FY2023 is missing** from the register, so the 2022→2024 jump from 2,37 M to 3,26 M has no intermediate point and part of it may be a definitional change (declarants of *net rental income* vs declarants taking the *housing-rental reduction* are two different counts and the FY2024 row mixes both). Before §7.3 uses a growth rate, FY2023 should be fetched and the two counts separated |

### One correction candidate for `docs/sources.md`

Not applied here. The EFF row at line 25 says "36.1% own other real estate (2022) — revised to
45.3% in the 2024 wave". DO 2610's own EFF-2022 column reads 46,8 %. Either the 36,1 % is on a
different basis or it predates the wave's re-weighting. Resolving it needs DO 2413 (EFF 2022),
which was not fetched in this pass.
