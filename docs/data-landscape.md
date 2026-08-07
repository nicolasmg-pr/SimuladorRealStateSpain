# Data landscape — Tier-1 Spanish housing statistics

Catalogue of the statistical series available for calibrating and validating the model.
Links verified by fetching on 2026-08-07 unless marked otherwise. Facts that could not be
confirmed by a fetch are labelled **(unverified)**. "Latest period" is what was visible on
the fetch date; these series keep updating.

Conventions: *transaction* = deed/registered price of an actual deal; *asking/listing* =
advertised price on a portal, systematically above closing prices and different in composition.

---

## 1. Sale prices

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| Índice de Precios de Vivienda (IPV) | INE | National + CCAA; quarterly; new vs second-hand split | **2007 Q1 – 2026 Q1** (both verified; latest pub. 2026-06-08) | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736152838&menu=ultiDatos&idp=1254735976607 | **Transaction-based** (notarial deeds), quality-mix adjusted. Index only — no €/m² levels. No provincial/municipal detail. Recent quarters revisable. Base-2015 series (table https://www.ine.es/jaxiT3/Tabla.htm?t=25171, 2007T1–2025T4) is frozen after a methodological rebase — splice bases explicitly. |
| Estadística Registral Inmobiliaria (incl. IPVVR repeat-sales index) | Colegio de Registradores | National + CCAA/province; quarterly | Series from ~2004 (unverified) – 2025 Q4 report verified; 2026 Q2 sales reported in press (2026-08) | https://www.registradores.org/actualidad/portal-estadistico-registral/estadisticas-de-propiedad | **Transaction** (registered deeds). Reports include €/m², sales counts, mortgage conditions (rate, term, payment/salary ratio) and **foreign-buyer share**. Registration lags the deed by weeks–months, so quarters are shifted vs notarial data. PDF reports + open-data downloads. |
| Transacciones inmobiliarias (counts + values) | MIVAU (Boletín Estadístico Online) | National / CCAA / province / **municipality**; quarterly | From 2004 (unverified) – ongoing | https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=34000000 | **Transaction** (notarial source). Counts split free/protected, new/second-hand, and by buyer residence status (foreigners). Values: total + mean, free housing. Municipal files are the finest public transaction-count series. The mivau.gob.es site blocks automated fetches (HTTP 403); the apps.fomento.gob.es bulletin works. |
| Valor tasado de la vivienda (appraisal prices) | MIVAU (Boletín Estadístico Online) | National / CCAA / province; municipalities >25k; quarterly | From 1995 (unverified) – ongoing | https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=35000000 | **Appraisal**, not transaction — based on tasaciones; levels in €/m². Long history, but appraisal values smooth turning points. Free vs protected, and by dwelling age (<5y / >5y). |
| Portal Estadístico del Notariado / CIEN series | Consejo General del Notariado | National / CCAA / province / municipality / postal code (portal); monthly national series | Portal launched 2025-10-23; CIEN monthly series from ~2007 (unverified) | https://www.notariado.org/liferay/web/cien/inicio | **Transaction** (deed closing values, not offers), earliest-signal source (deed date, no registration lag). Interactive portal: mean €/m², mean size, mean total price, sales count — suppressed where cells too small. |
| Índice de precios idealista (sale) | Idealista | National / province / municipality / district; monthly | From ~2007 (unverified) | https://www.idealista.com/sala-de-prensa/informes-precio-vivienda/ (site blocks automated fetch — link unverified by robot, well-known URL) | **LISTING prices, not deals.** Mean asking €/m² of active adverts; upward-biased vs closing prices and sensitive to composition of stock advertised. Useful for high-frequency, fine-grain signal only. |
| Índice Inmobiliario Fotocasa | Fotocasa (Fotocasa Research) | National / CCAA / municipality; monthly index + periodic reports | Research portal since 2017 (index older, unverified) | https://research.fotocasa.es/ | **LISTING prices.** Same caveats as idealista; useful as a second portal source to cross-check portal-specific bias (per project rule: ≥2 independent sources). |

## 2. Rents

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| SERPAVI — Sistema Estatal de Referencia del Precio del Alquiler de Vivienda | MIVAU, exploiting AEAT (IRPF declared rents) + Catastro dwelling attributes | **Census section** / district / municipality / province / CCAA; annual | **2011–2024**, full DB downloadable in Excel | https://www.mivau.gob.es/vivienda/alquila-bien-es-tu-derecho/serpavi (page blocks automated fetch; content verified via https://publicaciones.transportes.gob.es/serpavi-2026-sistema-estatal-de-referencia-del-precio-del-alquiler-de-vivienda) | **Actual declared rents** (tax data), not asking. Gives median and **p25/p75** reference ranges, €/m² and per dwelling, adjusted by dwelling characteristics. Only long-term residential leases declared to AEAT — misses informal and seasonal/tourist rentals; Basque Country & Navarra have separate tax systems → coverage gap (unverified detail). ~2-year publication lag. This is also the legal reference system for rent caps in tensioned zones. |
| Índice de Precios de la Vivienda en Alquiler (IPVA) — experimental | INE (AEAT IRPF model 100) | CCAA / province / municipality / district (provincial capitals); annual | Latest year **2024** (verified); first release (2022) covered 2011–2020, current page shows accumulated variation since 2015 | https://www.ine.es/experimental/ipva/experimental_precios_vivienda_alquiler.htm | Experimental. Index of **rent changes for sitting/repeated tenancies** (dwellings rented in consecutive years) — captures contract-rent inertia, not new-contract rents. Complements SERPAVI levels. |
| Índice de Referencia de Arrendamientos de Vivienda (IRAV) | INE | National; monthly | Since Jan 2025 (unverified) | https://www.ine.es/uc/oC7D0Ncd | Legal annual-update cap for leases signed after Ley 12/2023 replaced CPI-indexation; a policy input rather than a market-rent measure. |
| Portal rent indices (idealista / Fotocasa) | Idealista, Fotocasa | Municipality / district; monthly | idealista rent series from ~2007 (unverified) | https://www.idealista.com/sala-de-prensa/informes-precio-vivienda/ ; https://research.fotocasa.es/ | **ASKING rents.** Lead SERPAVI by ~2 years and capture new-contract dynamics, but overstate levels (negotiation, composition) and cover only advertised stock (portals under-represent word-of-mouth and social rentals). |

## 3. Households & income

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| Encuesta Continua de Hogares (ECH) | INE | National / CCAA / province; annual | 2013 (unverified start) – **2020 (discontinued)** | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176952&menu=ultiDatos&idp=1254735572981 | Household counts, size, composition, tenure of dwelling. **Ended in 2020**; INE directs users to the Encuesta Continua de Población (ECP) for 2021+ — series break to handle. |
| Censo de Población y Viviendas 2021 | INE | Down to **census section**; decennial (register-based) | Reference 2021; buildings/dwellings module pub. 2023 (unverified) | https://www.ine.es/censos2021/ | Register-based census (not full enumeration like 2011): tenure, dwelling type, vacancy estimated partly from **electricity-consumption registers** (unverified detail) — vacancy definition not comparable with Censo 2011. Free query tables + microdata. |
| Encuesta Financiera de las Familias (EFF) | Banco de España | National (sample ~6,000 households/wave); triennial 2002–2020, biennial since 2020 | **8 waves: 2002, 2005, 2008, 2011, 2014, 2017, 2020, 2022**; EFF 2022 microdata released 2025 | https://www.bde.es/wbe/es/estadisticas/recursos/encuestas-hogares-empresas/encuesta-financiera-familias-eff-/ (bde.es blocks direct robot fetch; waves verified via BdE Documento Ocasional 2413: https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesSeriadas/DocumentosOcasionales/24/Fich/do2413.pdf) | The only Spanish source joining household **wealth, debt, income and property holdings** (incl. second homes and rental income) — key for investor/landlord agent calibration. **Microdata require registration/request as analyst**; oversamples wealthy households (design), values imputed (5 imputations). |
| Atlas de Distribución de Renta de los Hogares (ADRH) | INE (AEAT + registers) | **Census section** / district / municipality; annual | 2015 (unverified start) – **2023** (pub. 2025-10-21, verified) | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177088&menu=ultiDatos&idp=1254735976608 | Mean/median net income per person & household, Gini, income brackets at census-section level — the natural income layer to join with SERPAVI sections. Tax-data based: Basque Country/Navarra covered via their own agencies with quirks (unverified). ~2-year lag. |
| Encuesta de Condiciones de Vida (ECV / EU-SILC Spain) | INE | National / CCAA; annual | **2004 – 2025** (verified; latest pub. 2026-02-05) | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736176807&menu=ultiDatos&idp=1254735976608 | Income distribution + housing-cost burden at household level; feeds the Eurostat overburden indicators in §6. Microdata freely downloadable. |

## 4. Supply & construction

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| Visados de dirección de obra (building permits, incl. obra nueva dwellings) | MIVAU / Colegios de Arquitectos Técnicos | National / CCAA / province; monthly | From 1992 (unverified) – ongoing | https://apps.fomento.gob.es/BoletinOnline/?nivel=2&orden=09000000 | Leading supply indicator: dwellings authorised (obra nueva / ampliación / reforma), surface, budget. Permits ≠ starts ≠ completions; conversion lag 18–30 months. Lives in the **old** BoletinOnline app, not BoletinOnline2. |
| Certificaciones fin de obra (CFO — completed dwellings) | MIVAU / Colegios de Arquitectos Técnicos | National / CCAA / province; monthly | From 2000 (unverified) – ongoing | https://apps.fomento.gob.es/BoletinOnline/?nivel=2&orden=09000000 (same section as visados) | Completions with number of dwellings, promoter type, liquidation value. The flow that actually adds to stock in the model. |
| Estadística de precios de suelo urbano | MIVAU | National / CCAA / province, by municipality-size band (<1k … >50k inhabitants); quarterly | From 2004 (unverified) – ongoing | https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=36000000 | €/m² of urban land plus land-transaction counts, values and surface, split individuals vs companies. Thin markets → volatile small-province cells. |
| Índice de costes del sector de la construcción | MIVAU | National; monthly (unverified frequency) | Base Jan 2005 = 100 – ongoing | https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=41000000 | Cost index + materials price tables; deflator for developer construction-cost assumptions. CNAE-2009, base 2005. |
| Parque de viviendas (dwelling-stock estimate) | MIVAU | CCAA / province; annual | From 2001 (unverified) – ongoing | https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=33000000 | Stock estimate split main/secondary dwellings; interpolates between censuses using CFO flows (unverified method detail). Anchor for zone stock totals. |

## 5. Credit

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| Estadística de Hipotecas (H) | INE (property registers) | National / CCAA / province; monthly | 2003 (new base; verified note) – May 2026 (verified latest, pub. 2026-07-20) | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736170236&menu=ultiDatos&idp=1254735576757 | New mortgage constitutions: count, average amount, average initial rate, plus changes/cancellations (since 2006). Registration-dated (lags signing). **No LTV** — amount is not linked to a transaction price. |
| Tipos de interés de nuevas operaciones — crédito vivienda | Banco de España (Boletín Estadístico, cap. tipos de interés / MIR) | National; monthly | From 2003 (unverified, MIR harmonised series) – ongoing | https://www.bde.es/webbe/es/estadisticas/compartido/datos/csv/ti_1_5.csv (unverified exact file; bde.es blocks robot fetch — navigate from https://www.bde.es/wbe/es/estadisticas/) | Harmonised Eurosystem (MIR) new-business mortgage rates, APR and NDER, fixed vs variable. The rate input for the bank agent. |
| Indicadores del mercado de la vivienda — incl. **loan-to-price (LTP/LTV)** | Banco de España (síntesis de indicadores, source: Colegio de Registradores for LTP) | National; quarterly | From 2004 (unverified) – ongoing | https://www.bde.es/wbe/es/estadisticas/temas/indicadores-mercado-vivienda.html (unverified — bde.es blocks robot fetch) | One-stop synthesis: LTP ratio, share of mortgages with LTP>80%, average term, affordability (price/income, debt-service/income). LTP uses **registered price** as denominator, understating true LTV when appraisal > price. |

## 6. Tenure & stock

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| Censo 2021 — tenure & dwelling stock | INE | Census section / municipality | 2021 (single reference year) | https://www.ine.es/censos2021/ | Tenure (owned outright / owned with mortgage / rented / other), secondary and vacant dwellings. Vacancy methodology differs from 2011 census — do not splice. |
| Tenure split (owner/tenant, EU-SILC) | Eurostat, dataset `ilc_lvho02` | National (ES) + EU comparators; annual | 2004 (unverified start) – **2025** (2023–2025 verified via API) | https://ec.europa.eu/eurostat/databrowser/view/ilc_lvho02/default/table?lang=en (API verified: .../statistics/1.0/data/ilc_lvho02?geo=ES) | Owner with/without mortgage, tenant market/reduced-free — the target distribution for household tenure states. Survey-based; small-cell noise in breakdowns. |
| Housing cost overburden rate (>40% disposable income) | Eurostat, dataset `ilc_lvho07a` (by age; `ilc_lvho07c` by tenure) | National (ES); annual | 2010 (unverified start) – **2025** (2023–2025 verified via API; total 8.2% 2023 → 7.2% 2025) | https://ec.europa.eu/eurostat/databrowser/view/ilc_lvho07a/default/table?lang=en | Eurostat threshold is **40%**, not the 30% used by Ley 12/2023 for zone declaration — don't conflate. Tenant-at-market-price overburden is the policy-relevant slice. |
| Social / public rental housing stock | MIVAU — Observatorio de Vivienda y Suelo (Boletín especial de vivienda social) | National / CCAA; occasional | 2020 special bulletin; updates in quarterly Observatorio boletines (nº 50 = 2024 Q2) | https://publicaciones.transportes.gob.es/downloadcustom/sample/3730 (Observatorio nº 50; social-housing figure itself unverified) | No live register. Consensus estimate ≈290k–300k public rental dwellings, ~1.5% of main-dwelling stock **(unverified — cite Boletín especial Vivienda Social before use)**. CCAA-level heterogeneity is large. |
| Foreign-buyer share of purchases | Colegio de Registradores (ERI quarterly) + MIVAU transacciones by buyer residence | National / province; quarterly | Registradores series from ~2006 (unverified) | https://www.registradores.org/actualidad/portal-estadistico-registral/estadisticas-de-propiedad and https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=34000000 | Two independent measures (register vs notary based) — levels differ slightly; both split resident vs non-resident foreigners. Key for tourist-metro demand shocks. |

## 7. Zone definitions (zonas de mercado residencial tensionado, Ley 12/2023)

| Series | Source | Granularity | Period | Download link | Quirks |
|---|---|---|---|---|---|
| Quarterly BOE resolutions listing declared tensioned zones | Secretaría de Estado de Vivienda (MIVAU) → BOE | Municipality (or sub-municipal area as declared by CCAA) | First resolution 2024 Q1 (BOE-A-2024-5214, 2024-03-14, verified) – ongoing quarterly | https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-5214 | The legally operative list. Declarations last **3 years** from the day after publication (verified in resolution text), renewable — the set of tensioned municipalities changes over time; snapshot the model's zone map with a date. Rent-cap effect operates through LAU art. 17.7 on new leases. |
| Declared zones by CCAA (state of play) | MIVAU press/registry + CCAA housing agencies | Municipality | Cataluña: first list Mar 2024 (140 per press; automated read of the BOE annex counted 159 entries — reconcile against the annex before use) + 131 added Oct 2024 → 271 per Catalan Housing Agency; Euskadi: 14 municipalities incl. all 3 Basque capitals (by Feb 2026); Navarra: 21 municipalities (Jul 2025); Galicia: declared (count unverified). Total ≈304 municipalities across 4 CCAA (mid-2026, per MIVAU press — (unverified) until BOE cross-check) | https://www.mivau.gob.es/el-ministerio/sala-de-prensa/noticias/lun-02022026-1523 (mivau.gob.es blocks robot fetch; counts from web-search snippets) | Declaration is a **CCAA choice**, not a market measurement: Madrid, Andalucía etc. have tensioned markets but no declarations. Model must separate "market is tensioned" (data) from "zone is declared" (policy switch). |
| Declaration criterion | Ley 12/2023, art. 18 | — | In force since 2023-05-26 (verified: BOE consolidated text confirmed as Ley 12/2023) | https://www.boe.es/buscar/act.php?id=BOE-A-2023-12203 | Either condition suffices: (a) mean housing cost (rent or mortgage + basic utilities) > **30% of mean household income** in the area; or (b) cumulative price/rent growth in the prior 5 years ≥ CCAA CPI growth + **3 pp**. (Criterion text corroborated by SERPAVI methodology and press, not machine-read from art. 18 itself — confirm wording in the consolidated text before coding.) Computable from SERPAVI + ADRH + IPV/IPVA — the model can *endogenise* eligibility. |

---

## Zone operationalization

How to build the model's three zone types from the series above:

**1. Tensioned metro.** Start from the BOE-declared municipality list (§7) for the *policy-on*
world. For the *market* definition (needed because declaration is politically selective),
compute the art. 18 criteria directly: SERPAVI median rent (census-section, §2) + ADRH median
household income (census-section, §3) → rent-burden ratio; flag sections/municipalities where
burden > 30% or where 5-year SERPAVI/IPVA growth exceeds CCAA CPI + 3 pp. Tensioned-metro
archetype = large-municipality sections (Madrid, Barcelona, coastal capitals) meeting the
criteria; calibrate its price level from Registradores/Notariado €/m², foreign-buyer share
from §6, and vacancy from Censo 2021.

**2. Secondary city.** Provincial capitals and 20k–250k municipalities that do *not* meet the
tension criteria. Calibrate from MIVAU municipal transaction counts (§1), SERPAVI municipal
rents, ADRH income, and CFO completions (§4) — these cities have meaningful construction
elasticity, visible in visados/CFO per 1,000 dwellings of stock (parque de viviendas, §4).

**3. Rural.** Municipalities <10k (or the MIVAU land-price "<1,000–10,000 inhabitants" bands,
§4): low or negative household growth (ECH/ECP, Censo), high outright-ownership share
(Censo 2021 tenure), high vacancy, thin transaction volumes (many empty municipal cells in
MIVAU/Notariado data — treat suppressed cells as thin-market signal, not zero).

**Migration flows** between the three zones can be disciplined with INE's residential
variation / municipal register statistics (Estadística de Variaciones Residenciales —
not catalogued above; add when the migration module is specified). Each zone's initial
stock = parque de viviendas aggregated over its member municipalities; tenure mix from
Censo 2021; income distribution from ADRH percentiles; landlord/investor balance-sheet
parameters from EFF waves.
