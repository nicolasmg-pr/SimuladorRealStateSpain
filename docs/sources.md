# Source register

Every document that informs the model gets a row here. No row, no influence.

- **Tier 1** = raw statistical series or microdata — used as data.
- **Tier 2** = interpretive report — never used alone; triangulate against a source with a different institutional viewpoint.
- **Viewpoint**: the institution's structural position (central bank / govt / industry / labour / tenant / landlord / academic / portal), not a judgment of the content.

## Tier 1 — statistical series

| Source | Institution | Series / dataset | Granularity | Period | URL | Fetched |
|---|---|---|---|---|---|---|
| IPV (Índice de Precios de Vivienda) | INE | Transaction-based sale price index | Quarterly, CCAA | 2007– | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736152838 | TODO |
| SERPAVI | MIVAU + AEAT + Catastro | Rent medians p25/p75 from tax data | Annual, census section | 2011–2024 | https://serpavi.mivau.gob.es/ | TODO |
| Transacciones inmobiliarias | MIVAU | Sale transaction counts/values | Quarterly, municipal | 2004– | https://www.mivau.gob.es/el-ministerio/observatorios-y-estadisticas/estadisticas/transacciones-inmobiliarias-compraventa | TODO |
| Visados de obra nueva | MIVAU / Colegios de Aparejadores | New construction permits | Monthly | — | TODO | TODO |
| Estadística de Hipotecas | INE | Mortgage counts and amounts | Monthly, provincial | 2003– | https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736170236 | TODO |
| EFF (Encuesta Financiera de las Familias) | Banco de España (survey microdata) | Household income/wealth/debt distributions | Triennial waves | 2002– | TODO | TODO |
| Censo de Población y Viviendas 2021 | INE | Tenure, stock, vacancy | Decennial, fine | 2021 | TODO | TODO |
| Encuesta Continua de Hogares | INE | Household formation | Annual | — | TODO | TODO |
| Estadística Registral Inmobiliaria | Colegio de Registradores | Prices, foreign-buyer share | Quarterly | — | TODO | TODO |
| Housing statistics | Eurostat | Tenure split, overburden rates, EU comparison | Annual | — | TODO | TODO |
| datos.gob.es housing catalogue | Gobierno de España | Open-data index for the above | — | — | https://datos.gob.es/es/sectores/vivienda | TODO |

## Tier 2 — interpretive reports and studies

| Source | Institution | Viewpoint | Topic | URL | Fetched | Triangulated against |
|---|---|---|---|---|---|---|
| Monràs & García-Montalvo (2022), rent control Catalonia | Academic (UPF/IESE) | academic | Ley 11/2020 effects: ~−5% rents, supply decline | TODO | TODO | Jofre-Monseny et al. 2023 |
| Jofre-Monseny, Martínez-Mazza, Segú (2023) | Academic (IEB/UB) | academic | Same policy: similar rent effect, no supply effect | https://www.sciencedirect.com/science/article/abs/pii/S0166046223000510 | TODO | Monràs & García-Montalvo 2022 |
| Pérez García (2025), rent control effectiveness Spain | Academic | academic | 2024 caps: rent effect not robust, ~13% fewer new tenancies | https://arxiv.org/html/2602.08631 | 2026-08-07 | both above |
| — add rows as research proceeds — | | | | | | |

## Method references (technique only, not Spanish facts)

| Reference | Used for |
|---|---|
| JASSS 27(4)5 (2024), behavioural housing ABM UK | Market-clearing and pattern-oriented validation technique |
| Morris screening + Sobol indices literature | Sensitivity-analysis method in Phase 6 |
| Method of simulated moments for ABMs | Calibration approach in Phase 6 |
