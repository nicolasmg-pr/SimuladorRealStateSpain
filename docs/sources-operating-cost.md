# Operating-cost share `c` — source register

Retrieval pass 2026-09-14. Scope: the `c` in §7.1's reservation-rent condition

    r_req = V · (i_bond + π − E[g]) / (12 · (1 − c))

defined in `docs/superpowers/specs/2026-09-11-model-redesign-design.md` §7.1 as *"operating costs
as a share of gross rent (IBI, comunidad, insurance, maintenance, management, vacancy loss)"*.

This file does not amend `docs/sources.md`. Rows below are in that file's table format so they can
be merged when the register is next edited.

---

## Tier 1 — statistical series

| Source | Institution | Series / dataset | Granularity | Period | URL | Fetched |
|---|---|---|---|---|---|---|
| Estadística de viviendas declaradas en el IRPF 2024 — Cuenta de resultados de la actividad de arrendamiento, **Vivienda habitual = Sí** | AEAT | Full landlord P&L per equivalent dwelling: gross income €21,005,241,943 over 2,404,250 equivalent dwellings; total deductible expenses €9,349,448,516 (44.51% of gross); of which building amortisation 16.03%, comunidad 9.01%, tributos 4.28%, seguros 2.75%, combined interest+repairs 7.53% | National + CCAA of taxpayer's domicile | FY2024 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpfvivienda/2024/jrubik4a903c3f4f80af0b64168ea4d6fa90c035d20361.html | 2026-09-14 (fetched) |
| Same table, **Vivienda habitual = Total** (adds tourist/seasonal lettings) | AEAT | Gross €24,609,240,620 / 2,650,952 dwellings; deductible 43.93%; per-CCAA columns | National + CCAA | FY2024 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpfvivienda/2024/jrubikf6dab530d3943a3876eb332fcaebe8535f33f367.html | 2026-09-14 (fetched) |
| Estadística de viviendas declaradas en el IRPF 2023 — Cuenta de resultados, **Vivienda habitual = Sí** | AEAT | Gross €19,239,954,791 / 2,306,583 dwellings; deductible 44.89%; building amortisation 16.87% | National + CCAA | FY2023 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpfvivienda/2023/jrubikf23e185484ff4d6d1a2a147fb5e89dae42e4949e6.html | 2026-09-14 (fetched) |
| Estadística de los declarantes del IRPF 2022 — Cuenta de resultados del arrendamiento, **Vivienda habitual = Sí** | AEAT | Gross €17,498,052,846 / 2,187,650 dwellings; deductible 43.19% | National | FY2022 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2022/jrubikf75a6823e530a74ded36ac43d44825bec435c3c42.html | 2026-09-14 (fetched) |
| Same, FY2021, **Vivienda habitual = Sí** | AEAT | Gross €15,948,700,047 / 2,079,193 dwellings; deductible 43.79% | National | FY2021 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2021/jrubikd2b1c2e04d93f5cb1278f69fe95bb7a7bb7057f.html | 2026-09-14 (fetched) |
| Same, FY2020, **Vivienda habitual = Sí** | AEAT | Gross €14,972,103,265 / 2,010,931 dwellings; deductible 43.05% | National | FY2020 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2020/jrubik64938b79ffbdd538066e022af87435c0d2f6132f.html | 2026-09-14 (fetched) |
| Same, FY2019, **Vivienda habitual = Sí** (first year of the housing module) | AEAT | Gross €16,138,388,285 / 2,142,868 dwellings; deductible 41.06% | National | FY2019 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2019/jrubikf573cdbf99e965fc56267e76d750561ae39bde3b1.html | 2026-09-14 (fetched) |
| IRPF partida **105** — Intereses de los capitales invertidos en la adquisición o mejora del inmueble y demás gastos de financiación | AEAT | Financing interest, all urban property, per declarant: €397.8M (2019), €345.4M (2020), €395.2M (2021), €361.2M (2022), €987.6M (2023), €1,230.8M (2024) | National, per declarant | FY2019–FY2024 | FY2024: https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2024/jrubikf3c0eb0367df6458cc21782521777fe4b5356fc7f.html | 2026-09-14 (fetched, all six years) |
| IRPF partida **106** — Gastos de reparación y conservación | AEAT | Maintenance, all urban property, per declarant: €686.6M (2019), €601.9M (2020), €725.1M (2021), €808.2M (2022), €897.2M (2023), €964.4M (2024) | National, per declarant | FY2019–FY2024 | FY2024: https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2024/jrubik31819e69687a24646910ede6d7d828b685e3de11.html | 2026-09-14 (fetched, all six years) |
| IRPF partida **107** — Intereses y gastos de reparación y conservación que se aplican en la declaración | AEAT | The *capped and applied* sum of 105+106 (cap = gross income per dwelling, art. 23.1 LIRPF, 4-yr carry-forward). €1,985.9M (2024) vs 105+106 = €2,195.2M, i.e. 9.5% deferred | National, per declarant | FY2019–FY2024 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpf/2024/jrubik231ffd465aeb104aa87aa08846b58885ebdaedd7.html | 2026-09-14 (fetched) |
| Estadística de viviendas declaradas en el IRPF 2024 — Rentabilidad y precios de alquiler como vivienda habitual | AEAT + Catastro | **Gross** yield only (5.4% national 2024, 5.1% in 2023), on effective rent ÷ valor de referencia; mean rent €691/month; **días de alquiler medios 347** (2024) and 339 (2023) out of 365; Madrid 351, Barcelona 352, Teruel 339, Extremadura 338 | CCAA / province / municipality >20k / postcode | FY2023–FY2024 | https://sede.agenciatributaria.gob.es/AEAT/Contenidos_Comunes/La_Agencia_Tributaria/Estadisticas/Publicaciones/sites/irpfvivienda/2024/jrubikf53b07ce4916495be456684ec99760a9e5f321e9c.html | 2026-09-14 (fetched) |
| Nota metodológica — Estadística de viviendas declaradas en el IRPF 2023 | AEAT | Defines the **vivienda equivalente** = ownership share × days in that use; *"Todos los conceptos económicos, tanto los ingresos y gastos del alquiler … están afectados por esa proporción"*. Scope: Territorio de Régimen Fiscal Común (excludes Navarra and País Vasco); **stock** of let dwellings, not new contracts | Methodology | 2019– | https://sede.agenciatributaria.gob.es/static_files/Sede/Tema/Estadisticas/Estadisticas_impuesto/Irpf_patrimonio/Irpfviviendas/Documentacion/nota_viviendas_2023.pdf | 2026-09-14 (fetched, PDF text extracted) |
| Ley 35/2006 del IRPF, art. 23.1 (texto consolidado) | BOE / Estado | Legal contents of "gastos deducibles": 23.1.a.1º interest + repairs (capped jointly at gross income, 4-yr carry-forward); 23.1.a.2º non-state taxes; 23.1.a.3º doubtful debts; 23.1.a.4º third-party services; **23.1.b building amortisation at 3%/yr** of the greater of acquisition cost or cadastral value, land excluded | Legal text | In force | https://www.boe.es/buscar/act.php?id=BOE-A-2006-20764 | 2026-09-14 (fetched, via subagent) |

## Tier 2 — interpretive reports and studies

| Source | Institution | Viewpoint | Topic | URL | Fetched | Triangulated against |
|---|---|---|---|---|---|---|
| BdE DO 2432 §3.3, printed p. 35 — cost wedge on gross rental yield | Banco de España | central bank | *"los gastos declarados como deducibles en el Impuesto sobre la Renta de las Personas Físicas por los particulares que arriendan viviendas supondrían, en promedio, una reducción del rendimiento bruto de **2 pp**"*, against an RBA of ≈5.5%/yr for 2011–2022 ⇒ ≈36% of gross rent. Mean, not median. Unit (per dwelling vs per declarant) **not stated**. Source declared as AEAT's Servicio de Estudios Tributarios (fn. 39). **Costs only — the IRPF wedge is quantified separately in the next sentences (0.5–1.25 pp by bracket; 0.3–0.8 pp on the 2011–2022 average).** The paper never itemises the concepts; the strings "amortiz" and "interes" appear nowhere in its 66 pages | https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesSeriadas/DocumentosOcasionales/24/Fich/do2432.pdf | 2026-09-14 (fetched, pypdf p. 35) | AEAT direct computation (**disagrees** — see §4); BdE Informe Anual 2023 (agrees) |
| Informe Anual 2023, cap. 4, printed p. 249 | Banco de España | central bank | Repeats the same figure citing Khametshin, López-Rodríguez y Pérez (2024): *"los gastos asociados al alquiler, que, de acuerdo con lo declarado por los particulares en el IRPF, reducirían dicho rendimiento en unos **2 pp**"* | https://www.bde.es/f/webbe/SES/Secciones/Publicaciones/PublicacionesAnuales/InformesAnuales/23/Fich/InfAnual_2023_Cap4.pdf | 2026-09-14 (fetched, via subagent) | DO 2432 (same figure, same underlying AEAT source — **not an independent confirmation**) |
| Anuario del mercado del alquiler en España 2024, cap. "Inversión y rentabilidad" | Observatorio del Alquiler (Fundación Alquiler Seguro + URJC + U. Carlos III) | industry, landlord-side (the foundation funds the university units — flagged by *Público*) | Reports **net** yields from a stylised "modelo base": Madrid persona física long-let **3.5%**, Barcelona **3.5%**; persona jurídica 2.8% / 2.9%; seasonal 3.2%, tourist 2.9–3.1%. **Does not state the gross yield the model starts from, and the figure is net of both costs and tax.** Carries no operating-cost share and cannot be inverted to one | https://www.observatoriodavivenda.gal/sites/w_igvobs/files/anuario-baja.pdf | 2026-09-14 (fetched, 7.5 MB PDF, text extracted) | Not usable as triangulation — basis incompatible |

---

## What `c` is

**`c` = 0.20–0.24, before tax, excluding vacancy** — or **0.24–0.30 if vacancy is folded in** (see §3).

### 1. The measurement

AEAT's *cuenta de resultados de la actividad de arrendamiento* publishes gross income
(*ingresos íntegros computables*), every deductible-expense concept separately, and net income,
for the same population in the same table. `c` therefore does not have to be inferred — it is
read off, concept by concept. Restricting to **Vivienda habitual = Sí** (dwellings let as the
tenant's habitual residence, i.e. long-term residential letting, which is what §7.1 models and
what the model's rental market is) gives, as a share of gross rent:

| Concept (AEAT line) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | In `c`? |
|---|---|---|---|---|---|---|---|
| Gastos de comunidad | 8.02% | 8.74% | 8.72% | 8.89% | 8.96% | 9.01% | **yes** — *gastos de comunidad* |
| Tributos, recargos y tasas | 4.76% | 4.96% | 4.87% | 4.68% | 4.45% | 4.28% | **yes** — IBI, tasa de basuras |
| Primas de contratos de seguro | 2.00% | 2.35% | 2.49% | 2.57% | 2.64% | 2.75% | **yes** — insurance |
| Reparación y conservación (split-adjusted, see §2) | 3.04% | 2.81% | 2.85% | 3.08% | 3.38% | 3.31% | **yes** — maintenance |
| Servicios personales devengados por terceros | 0.60% | 0.47% | 0.51% | 0.53% | 0.59% | 0.57% | **yes** — management, portería |
| Gastos de formalización del contrato | 0.16% | 0.12% | 0.15% | 0.16% | 0.25% | 0.33% | **yes** — letting/agency |
| Gasto de defensa jurídica | 0.07% | 0.06% | 0.07% | 0.06% | 0.06% | 0.07% | **yes** — legal |
| Saldos de dudoso cobro | 0.26% | 0.49% | 0.44% | 0.33% | 0.30% | 0.30% | **yes** — non-payment allowance |
| **`c` narrow — sum of the eight above** | **18.91%** | **20.01%** | **20.09%** | **20.29%** | **20.63%** | **20.62%** | |
| Servicios y suministros (luz, agua, gas) | 1.12% | 0.80% | 0.83% | 0.86% | 0.81% | 0.82% | optional — landlord-paid utilities |
| Resto de otros gastos fiscalmente deducibles | 2.64% | 1.95% | 1.72% | 1.64% | 1.63% | 1.57% | optional — AEAT does not itemise |
| Amortización de bienes muebles | 0.73% | 0.65% | 0.63% | 0.62% | 0.62% | 0.60% | optional — furniture replacement |
| **`c` broad — narrow + the three above** | **23.41%** | **23.40%** | **23.28%** | **23.42%** | **23.69%** | **23.61%** | |
| Financing interest inside the capped box (§2) | 1.76% | 1.61% | 1.55% | 1.37% | 3.72% | 4.22% | **NO** — financing, not operating |
| Interés de ejercicios anteriores aplicado (box 104) | 0.62% | 0.66% | 0.60% | 0.61% | 0.61% | 0.64% | **NO** — financing carry-forward |
| Amortización del inmueble y mejoras (3%/yr, art. 23.1.b) | 15.27% | 17.37% | 18.35% | 17.78% | 16.87% | 16.03% | **NO** — capital consumption, double-counts `E[g]` |
| *All fiscally deductible expenses* | *41.06%* | *43.05%* | *43.79%* | *43.19%* | *44.89%* | *44.51%* | |

Read the two bolded rows. **`c` narrow is 18.9–20.6% and `c` broad is 23.3–23.7% in every one of
six years** — through the pandemic, a rent boom, and a full Euribor cycle. It is one of the most
stable objects in this register. The stability is structural: the fixed heads (comunidad + IBI +
insurance + management + bad debt, excluding repairs) sit at **17.19–17.31% of gross in 2020–2024**,
a five-year band 12 bp wide.

The two exclusions are the whole point of the basis question:

- **Building amortisation (15–18% of gross)** is out. §7.1 already carries capital value change in
  `E[g]`; charging a 3%/yr statutory write-down of construction cost *and* an expected capital gain
  against the same asset counts the same thing twice, with opposite signs.
- **Financing interest (1.4–4.2% of gross)** is out. §7.1's hurdle is `i_bond + π` against the
  **whole** of `V` — the opportunity cost of unlevered capital. Interest is the cost of the debt
  half of that same capital. Including it double-counts the financing leg.

### 2. The line that had to be decomposed

The dwelling-level P&L reports one line, *"Intereses y gastos de reparación y conservación que se
aplican"*, which fuses interest and maintenance — art. 23.1.a.1º LIRPF deducts them jointly and
caps the pair at gross income per dwelling. Taking it whole would put mortgage interest inside `c`;
dropping it whole would put maintenance at zero. Both are wrong.

The declarant-level partidas tables publish the two halves separately: **box 105** (financing
interest) and **box 106** (repairs and conservation), with **box 107** the capped applied sum. The
repairs share, 106/(105+106), is:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| repairs share of the combined box | 63.3% | 63.5% | 64.7% | 69.1% | 47.6% | 43.9% |

The combined line's jump from 4.45% of gross (2022) to 7.53% (2024) is **not** a renovation boom
driven by Ley 12/2023's refurbishment reductions, which was the obvious reading. Box 106 (repairs)
is nearly flat — €808M → €964M — while box 105 (interest) triples, €361M → €1,231M. It is the
Euribor spike, and it belongs outside `c`. Applying the split gives the maintenance row in §1:
**2.8–3.4% of gross, flat across six years**.

Caveat on this correction: boxes 105/106 cover all urban property (dwellings, premises, garages)
per declarant, while the P&L line is dwellings per equivalent dwelling. The split ratio is imported
across populations. It is the only decomposition AEAT publishes. Its effect on `c` is bounded:
with repairs at 0% of the combined line `c` narrow would be 17.3%, with repairs at 100% it would be
24.8%; the ratio is the difference between those, and the answer is near the middle.

### 3. Vacancy — measured, but not inside the AEAT number

The methodological note is explicit that the statistical unit is the *vivienda equivalente* =
ownership share × **days in that use**, and that income and expenses are both scaled by it.
So AEAT's `c` is **per euro of rent actually received**: the vacant fraction of the year is in
neither numerator nor denominator. §7.1's `c` lists vacancy loss as a component. They are not the
same object and must not be silently equated.

The same statistic measures the missing piece. *Días de alquiler medios* for dwellings let as
habitual residence: **347/365 in 2024 (4.9% vacant), 339/365 in 2023 (7.1%)** — and it has the
zone gradient the model wants, in the right direction:

| 2024 | días let | within-year vacancy |
|---|---|---|
| Barcelona | 352 | 3.6% |
| Madrid | 351 | 3.8% |
| Spain | 347 | 4.9% |
| Teruel | 339 | 7.1% |
| Extremadura | 338 | 7.4% |

Folding vacancy in depends on whether costs are treated as accruing only while let (AEAT's own
proration) or all year round (true of IBI, comunidad and insurance — 16 of the 20.6 pp):

| | narrow (0.206) | broad (0.236) |
|---|---|---|
| 2024, costs prorated | 0.245 | 0.274 |
| 2024, costs fixed | 0.255 | 0.285 |
| 2023, costs prorated | 0.262 | 0.291 |
| 2023, costs fixed | 0.277 | 0.308 |

**The decision §7.1 must make explicitly:** if the engine already generates vacancy endogenously
(dwellings sitting unlet in `market/clearing.py`), then `c` must be the **0.20–0.24** figure, or
vacancy is charged twice. If §7.1's landlord is assumed always-let, `c` must be **0.24–0.30**.
Whichever is chosen, the choice is a modelling decision and belongs in the spec, not in this file.

One warning on the vacancy figure: 347 days is the mean over dwellings that were let *at some point*
in the year. A dwelling vacant for a whole year leaves the rental table entirely and reappears under
*renta imputada*. So 4.9% is frictional between-tenancy vacancy for a going concern, and is a **floor**
on a landlord's true vacancy exposure.

### 4. Gross-of-tax or net-of-tax — and the disagreement with BdE

**Every figure above is before tax.** AEAT's *gastos deducibles* are subtracted from gross income to
reach *rendimiento neto*; the art. 23.2 housing reduction (60%, and 50/60/70/90% for contracts from
26-5-2023) is applied *after* that, as a separate line — *Reducción por arrendamiento de inmuebles
destinados a vivienda*, €6.63bn in 2024, which this file does not touch. `c` as computed here is
the pre-tax cost share §7.1 needs. The tax wedge is a different parameter and DO 2432 already
quantifies it (0.5–1.25 pp of yield by bracket; 0.3–0.8 pp on the 2011–2022 average) — that figure
is already in `docs/sources.md` and must not be added into `c`.

**BdE and AEAT disagree, and the disagreement is recorded, not resolved.** DO 2432 puts all declared
IRPF expenses at a 2 pp reduction of a ≈5.5% gross yield ⇒ **≈36% of gross rent**. The same object
computed directly from AEAT's own tables is **41.1–44.9%**. Both claim the same source (AEAT's
Servicio de Estudios Tributarios) and the same concept (all IRPF-deductible expenses). Possible
causes — none verified: DO 2432's 2011–2022 window predates the years published here (the housing
module starts in 2019); "2 pp" may be rounded from a value up to 2.4 pp; the RBA's denominator is
Registradores price per m² while AEAT's yield uses *valor de referencia*, so the two yields are not
the same ratio and a pp wedge does not convert cleanly. **The discrepancy does not touch `c`**: both
numbers describe the all-deductible aggregate, which includes building depreciation and interest and
is therefore *not* `c` under either reading. It is recorded because a future reader will find the
2 pp figure and be tempted to use it.

### 5. Zone gradient — weaker than expected

The cost account is published by CCAA. On the *all-uses* basis (interest still inside the repairs
line, so levels are inflated ~1–4 pp), the 2024 spread is **18.8% (Balears) to 27.8% (Asturias)**,
with Cataluña 24.6%, Madrid 26.3% and Spain 24.1%.

This does **not** deliver a tensioned-metro / rural ladder. Madrid is near the *top*, on a comunidad
charge of 10.95% of gross — concierge-staffed buildings — while Balears and Canarias are lowest
because high rents dilute a largely fixed cost base. If §7.1 wants a zone gradient in `c`, the
defensible one runs on **rent level, not on urbanity**, and the model should not assert a
metro-vs-rural ordering this source does not support. The vacancy component (§3) does have a clean
metro/rural gradient and is where a zone difference legitimately enters.

### 6. Recommended parameterisation

| | value | basis |
|---|---|---|
| `c` central, pre-tax, vacancy excluded | **0.22** | midpoint of narrow 0.206 and broad 0.236, FY2024, vivienda habitual |
| `c` range, pre-tax, vacancy excluded | **0.20 – 0.24** | narrow-to-broad concept envelope, stable 2019–2024 |
| `c` range, pre-tax, vacancy included | **0.24 – 0.30** | above, plus 4.9% (2024) to 7.1% (2023) within-year vacancy |
| — of which fixed (comunidad + IBI + insurance) | 0.160 | FY2024, invariant to occupancy |
| — of which maintenance | 0.033 | FY2024, split-adjusted |
| — of which management + letting + legal | 0.010 | FY2024 |
| — of which non-payment allowance | 0.003 | FY2024, fiscal *dudoso cobro* only — see Not retrieved |

Units: dimensionless share of gross contractual rent. Population: dwellings let as the tenant's
habitual residence, Territorio de Régimen Fiscal Común, equivalent-dwelling basis. **Mean, not
median** — AEAT publishes aggregate amounts and an arithmetic mean per dwelling; no dispersion.
Per **equivalent dwelling**, not per declarant. **Before tax.** Excludes building depreciation and
financing interest by construction.

---

## Not retrieved

1. **A dispersion measure for `c`.** Every AEAT figure here is an aggregate ratio or an arithmetic
   mean. No percentile, no distribution by rent level, dwelling age or landlord size is published in
   the housing module. §7.1 gets a point/range, not a distribution, and a landlord-heterogeneity
   extension cannot be sourced from here.

2. **The interest/repairs split at dwelling level.** Boxes 105 and 106 are published only per
   declarant and over all urban property. The dwelling-level P&L publishes only the capped sum
   (box 107). The correction in §2 imports a ratio across populations; AEAT publishes nothing finer.
   Blocking cause: the statistic is designed that way, not a fetch failure.

3. **True economic non-payment cost.** *Saldos de dudoso cobro* is 0.3% of gross, but art. 23.1.a.3º
   only allows the deduction after six months of arrears and it is reversed if later collected, so it
   measures written-off arrears, not the cost of arrears. CGPJ eviction counts (already registered:
   18,317 rental non-payment evictions in 2025) are a flow of cases, not a euro loss. No source
   reconciling the two was found. If §7.1's `π` carries default risk, 0.3% is a floor on what `c`
   contributes and the rest belongs in `π`.

4. **A genuinely independent second measurement of `c`.** Every quantified source found traces back
   to AEAT: DO 2432 §3.3 says so in footnote 39; Informe Anual 2023 cites DO 2432. The industry
   material is not a measurement — idealista, Fotocasa, Bankinter, TaxDown and the *calculadora de
   rentabilidad* pages give worked examples with illustrative euro amounts, not a measured wedge, and
   several (`bankinter.com`, `taxdown.es`) put net yield 2 pp below gross without stating a
   population. The Observatorio del Alquiler's *Anuario 2024* (Tier 2, landlord-industry funded) was
   fetched in full and reports net yields of 3.5% for Madrid and Barcelona from a stylised "modelo
   base", but never prints the gross yield it starts from and is net of tax as well as costs, so it
   cannot be inverted. **`c` currently rests on one institutional source.** That is a real
   qualification and belongs in `docs/validation.md` "Honest qualifications".

5. **Coverage of undeclared letting.** The statistic counts 2.40M equivalent dwellings let as
   habitual residence in 2024, against a Spanish rental stock nearer 3.4M (INE). Informal lettings
   and foral-territory landlords (Navarra, País Vasco — excluded by construction) are outside. If
   informal landlords face a different cost structure — plausibly lower declared comunidad and
   insurance, no management — `c` is measured on the formal segment only. No source quantifying the
   gap was found.

6. **A pre-2019 series.** The AEAT housing module starts in FY2019, so `c` cannot be carried back
   into the 2014–2018 calibration window, let alone the sealed 2008–2013 hold-out. The six years
   available are so stable (18.9–20.6% narrow) that holding `c` constant across the calibration
   period is defensible, but it is an assumption, not a measurement, and needs an
   `docs/assumptions.md` row.

7. **FY2025.** Not yet published; the IRPF declarantes statistic runs roughly two years behind.
   FY2024 (published 2026) is the latest.

8. **Composition of *"Resto de otros gastos fiscalmente deducibles"*** (1.6% of gross). AEAT
   publishes it as a residual with no breakdown, which is why it sits in the broad-minus-narrow gap
   rather than being assigned. Searched the 2023 methodological note and the statistic's *metadatos*
   page; neither itemises it.

9. **Whether DO 2432's 2 pp and AEAT's 41–45% describe the same aggregate.** Attempted
   reconciliation is set out in §4 and failed. Resolving it would need the unpublished AEAT
   tabulation DO 2432 fn. 39 refers to, which is a bespoke extract from the Servicio de Estudios
   Tributarios, not a public table. **The conflict is recorded unresolved.** It does not affect `c`,
   because neither figure is `c`.

10. **English edition of DO 2432.** `do2432e.pdf`, `do2432en.pdf` and the `/Files/` path variant all
    return HTTP 404; BdE's landing page offers no English version. The Spanish text layer did in fact
    contain the sentence on printed p. 35 — the previous pass's failure was a line-break artefact
    ("una reducción\ndel rendimiento bruto de 2 pp") plus a garbled adjacent table, not a missing
    figure. Recorded so the route is not retried a third time.
