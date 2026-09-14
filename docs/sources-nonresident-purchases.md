# Non-resident / foreign housing purchases in Spain — retrieval and falsification test

**Retrieved 2026-09-14.** Purpose: settle the falsification test stated in
`docs/superpowers/specs/2026-09-11-model-redesign-design.md` §7.4 —

> **Falsification**: if Registradores' non-resident purchase series tracks Spanish transaction
> volume one-for-one (2007–2025), the exogenous treatment is wrong.

**Result, in one line: it does not.** Over 2007→2013 total Spanish housing transactions fell
**−64%** while non-resident foreign purchases **rose +20%**. Two independent Tier-1 sources
(MIVAU quarterly, Notariado CIEN semi-annual) agree on this to within ~3%. The exogenous
arrival stream survives; the "proportional to recent Spanish sales" treatment it replaces is
falsified. Details and arithmetic in §4.

This file does not edit `docs/sources.md`. The rows in §1 are written in that file's format and
are ready to be merged into it by whoever owns that file.

---

## 1. Register rows (format of `docs/sources.md` — not yet merged)

### Tier 1 — statistical series

| Source | Institution | Series / dataset | Granularity | Period | URL | Fetched |
|---|---|---|---|---|---|---|
| Transacciones inmobiliarias, Tabla 1.6 — "Número de transacciones inmobiliarias según residencia del comprador" | MIVAU (Boletín Estadístico Online) | **The series the model needs.** Quarterly housing transactions split TOTAL / Residentes en España (Españoles, Extranjeros) / No residentes en España (Españoles, Extranjeros). Tipología de la vivienda: **Todas** (libre + protegida, new + second-hand). 77 quarters, one worksheet tab per quarter. 2026Q1 marked "Datos provisionales". Non-resident foreigners 2007Q1 5,885 → 2013Q4 9,078 → 2022Q2 peak 17,814 → 2026Q1 10,704; share of all transactions 2.55% (2007Q1) to 10.67% (2015Q3) | Quarterly; national / CCAA / province | 2007Q1 – 2026Q1 | https://apps.fomento.gob.es/BoletinOnline2/sedal/340101d0.XLS (index: https://apps.fomento.gob.es/BoletinOnline2/?nivel=2&orden=34000000) | 2026-09-14 (XLS fetched, 1.3 MB, BIFF8, read with xlrd) |
| Anexo de tablas — "Compraventa de vivienda por parte de extranjeros 2S25", Hoja 1 "Nacionalidad y residencia" | Consejo General del Notariado / CIEN (Índice Único Informatizado) | **Independent cross-check + the €/m² premium history.** Semi-annual operations and mean €/m² for: Extranjero (No residente / Residente), Nacional (No residente / Residente), Total general. Basis **vivienda libre only**. Non-resident foreigners 1S07 13,002 → 2S13 16,663 → 1S22 peak 33,510 → 2S25 24,793. €/m² non-resident foreigners 2,185 (1S07) → 3,242 (2S25) vs Spanish nationals 2,131 → 1,832 | Semi-annual; national + CCAA + nationality | 1S2007 – 2S2025 | XLSX: https://www.notariado.org/liferay/c/document_library/get_file?uuid=125f548a-e4f2-498c-b9ea-3a736e10941a&groupId=2289837 (from https://www.notariado.org/liferay/web/cien/sala-de-prensa/noticias/detalle?...NOTARIO_INFORMA_DETALLE_ID=32452895) | 2026-09-14 (XLSX fetched, 285 KB) |
| Estadística Registral Inmobiliaria (ERI) 2T 2026 and 4T 2025 — "Compras de vivienda por extranjeros" | Colegio de Registradores | **All-foreigner (nationality of buyer) only — no resident / non-resident split anywhere in the report.** Quarterly national share 15.98% (2026Q2, record), 13.92% (2026Q1), 13.52% (2025Q4); 12-month (interanual) national shares at each Q2: 13.08% (2018), 12.35, 12.06, 10.37, 12.84, 14.49, 14.88, 14.38, 14.22% (2026); at each Q4: 12.64% (2018), 12.45, 11.32, 10.80, 13.75, 14.98, 14.60, 13.82% (2025). €/m² by world zone 2026Q2: North America 4,311, Oceania 3,240, EU 3,149, rest of Europe 2,885, Asia 2,691, South America 2,057, C. America/Caribbean 1,936, Africa 1,054 | Quarterly; national / CCAA / province / nationality | Text: 2026Q2 and 2025Q4 issues; charts back to 2013Q2 (not machine-readable) | https://www.registradores.org/documents/d/guest/eri_2t_2026 ; https://www.registradores.org/documents/d/guest/eri_4t_2025 | 2026-09-14 (PDFs fetched, 9.3 / 7.6 MB; text layer extracted with PyMuPDF 1.28.2) |
| Estadística de Transmisión de Derechos de la Propiedad (ETDP) — table inventory | INE | **Negative result, recorded so it is not re-checked.** The ETDP publishes **no nationality and no residence breakdown**. All 17 published tables enumerated via Tempus3; the only buyer classification is `Tipo de titular` = {Persona física, Persona jurídica} | Monthly; national/CCAA/province | n/a | https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/ETDP ; https://servicios.ine.es/wstempus/js/ES/VALORES_GRUPOSTABLA/50256/110841 | 2026-09-14 (API fetched) |

### Tier 2 — interpretive reports

| Source | Institution | Viewpoint | Topic | URL | Fetched | Triangulated against |
|---|---|---|---|---|---|---|
| "La compraventa de vivienda por extranjeros disminuyó un 4,4% interanual" (2S25 press note + informe analítico) | Consejo General del Notariado | industry (notarial profession) | 2S25: foreign purchases of vivienda libre 66,629 (−4.4% y/y), 18.4% of total (19.5% in 2S24, 20.9% in 2S23); non-resident foreigners paid 3,242 €/m² vs 1,963 resident foreigners vs 1,839 Spanish nationals; by nationality British 5,178 and Moroccan 5,154 operations | https://www.notariado.org/portal/-/la-compraventa-de-vivienda-por-extranjeros-disminuy%C3%B3-un-4-4-interanual | 2026-09-14 (fetched) | Its own Tier-1 annex XLSX (row above); MIVAU Tabla 1.6 (Tier 1, different basis) |

---

## 2. Bases, stated once and applied everywhere below

Four things differ between these series and must never be silently mixed.

| | MIVAU Tabla 1.6 | Notariado CIEN annex | Registradores ERI |
|---|---|---|---|
| **Who counts as "foreign"** | Nationality of buyer, **cross-tabulated with residence** → non-resident foreigners isolable | Nationality of buyer, **cross-tabulated with residence** → non-resident foreigners isolable | Nationality of buyer only — **residents and non-residents pooled**; the split does not exist in the publication |
| **Housing covered** | **All** housing — vivienda libre + vivienda protegida, new + second-hand ("Tipología de la vivienda: Todas") | **Vivienda libre only** | Registered home sale-purchases (compraventa de vivienda) |
| **Denominator of the share** | All housing transactions in the same table (TOTAL column) — *not* free-market only | All vivienda libre compraventas (Total general) | All registered home compraventas |
| **Frequency / span** | Quarterly, 2007Q1–2026Q1 (77 points) | Semi-annual, 1S07–2S25 (38 points) | Quarterly; only current-period values are machine-readable |
| **Unit** | Operations (counts) | Operations (counts) + mean €/m² | Percentages + current-quarter counts |

**The model's overlay is non-resident only.** So the operative column is MIVAU
`No residentes en España → Extranjeros`, and CIEN `Extranjero → No residente`. Everything else
here is context or cross-check.

Two further distinctions that bit during retrieval:

- *Non-resident foreigners* ≠ *all non-residents*. MIVAU also counts **Spanish nationals
  resident abroad** as non-residents (832 in 2026Q1, ~1,000/quarter recently, but 4,426 in
  2007Q1). All-non-resident totals are given in §3 for completeness; the falsification test uses
  non-resident **foreigners**.
- *Non-resident foreigners* ≈ **half** of all foreign buyers, and the ratio moves. In 2025 MIVAU
  has 51,367 non-resident vs 75,640 resident foreigners (40% / 60%). The factor-of-two warning
  in the task brief is real and is why every figure below carries its basis.

### Sources disagree on the all-foreigner share — recorded, not resolved

For 2025, all-foreign share of transactions:

- **MIVAU 16.89%** (denominator = all housing, incl. protegida)
- **Notariado CIEN 18.81%** (2025 = 71,625 + 66,629 foreign / 372,617 + 362,175 libre; denominator = vivienda libre only)
- **Registradores ERI 13.82%** (12-month to 2025Q4) / **13.52%** (2025Q4 alone)

The MIVAU–CIEN gap is explained by the denominator (protegida in / out). The ERI sits ~3–5 pp
below both and I did not find a documented reconciliation. **Do not treat the three as
interchangeable.** The model should use MIVAU or CIEN, which carry the residence split; ERI is
a directional cross-check only.

### Cross-validation of the extraction

Two checks were run before using the numbers.

1. **Against CaixaBank's published percentages** (already in `docs/sources.md` row 221, from
   MIVAU, 4 quarters to 2025Q1): they report foreign purchases 133k = 18.0% of sales, resident
   foreigners 10.1% of all sales, non-residents 7.9%, residents 56.2% of foreign buys.
   From the extracted table, 4 quarters to 2025Q1: total 739,277; resident foreigners 74,743
   (**10.11%**); non-resident foreigners 57,867 (**7.83%**); foreign total 132,610 (**17.94%**,
   ≈133k); residents 56.4% of foreign. All four reproduce.
2. **MIVAU against CIEN**, two statistical systems with different coverage:
   non-resident foreign purchases 2007 = 24,489 (MIVAU) vs 24,570 (CIEN), **0.3% apart**;
   2025 = 51,367 vs 52,781, **2.8% apart**. The series are effectively the same object.

---

## 3. The series

### 3.1 MIVAU, quarterly, 2007Q1–2026Q1 — the primary series

Source: MIVAU Boletín Estadístico Online, Tabla 1.6, `340101d0.XLS`, TOTAL NACIONAL row of each
quarterly worksheet. Basis: **operations**, all housing (libre + protegida), nationality ×
residence of buyer. 2026Q1 is provisional. Columns are exactly as published; nothing is
interpolated, and no quarter is missing.

| Quarter | Total transactions | Non-resident foreigners | Resident foreigners | All foreigners | All non-residents (any nationality) | Non-res. foreign share of total |
|---|---|---|---|---|---|---|
| 2007Q1 | 230,755 | 5,885 | 10,708 | 16,593 | 8,369 | 2.55% |
| 2007Q2 | 227,562 | 7,127 | 10,680 | 17,807 | 9,041 | 3.13% |
| 2007Q3 | 186,504 | 5,519 | 7,639 | 13,158 | 6,804 | 2.96% |
| 2007Q4 | 192,050 | 5,958 | 6,084 | 12,042 | 7,350 | 3.10% |
| 2008Q1 | 159,088 | 5,109 | 4,716 | 9,825 | 6,052 | 3.21% |
| 2008Q2 | 157,008 | 4,749 | 4,378 | 9,127 | 5,450 | 3.02% |
| 2008Q3 | 122,949 | 4,186 | 3,500 | 7,686 | 4,985 | 3.40% |
| 2008Q4 | 125,419 | 3,703 | 5,619 | 9,322 | 4,421 | 2.95% |
| 2009Q1 | 104,703 | 3,143 | 6,390 | 9,533 | 3,661 | 3.00% |
| 2009Q2 | 119,938 | 3,392 | 7,172 | 10,564 | 3,995 | 2.83% |
| 2009Q3 | 107,534 | 3,443 | 6,175 | 9,618 | 3,945 | 3.20% |
| 2009Q4 | 131,544 | 4,146 | 7,095 | 11,241 | 4,362 | 3.15% |
| 2010Q1 | 107,079 | 3,427 | 5,327 | 8,754 | 3,650 | 3.20% |
| 2010Q2 | 153,164 | 4,492 | 7,270 | 11,762 | 4,793 | 2.93% |
| 2010Q3 | 80,550 | 3,228 | 4,467 | 7,695 | 3,506 | 4.01% |
| 2010Q4 | 150,494 | 4,136 | 7,262 | 11,398 | 4,364 | 2.75% |
| 2011Q1 | 74,455 | 3,883 | 4,687 | 8,570 | 4,015 | 5.22% |
| 2011Q2 | 90,756 | 4,813 | 5,786 | 10,599 | 4,990 | 5.30% |
| 2011Q3 | 76,534 | 4,292 | 5,044 | 9,336 | 4,507 | 5.61% |
| 2011Q4 | 107,373 | 5,394 | 6,097 | 11,491 | 5,659 | 5.02% |
| 2012Q1 | 69,420 | 4,394 | 5,333 | 9,727 | 4,567 | 6.33% |
| 2012Q2 | 84,289 | 5,470 | 6,287 | 11,757 | 5,675 | 6.49% |
| 2012Q3 | 75,313 | 5,408 | 5,289 | 10,697 | 5,697 | 7.18% |
| 2012Q4 | 134,601 | 9,769 | 8,388 | 18,157 | 10,141 | 7.26% |
| 2013Q1 | 54,835 | 5,126 | 4,783 | 9,909 | 5,301 | 9.35% |
| 2013Q2 | 81,472 | 8,037 | 6,850 | 14,887 | 8,300 | 9.86% |
| 2013Q3 | 70,604 | 7,255 | 5,758 | 13,013 | 7,591 | 10.28% |
| 2013Q4 | 93,657 | 9,078 | 7,304 | 16,382 | 9,399 | 9.69% |
| 2014Q1 | 81,516 | 7,956 | 7,199 | 15,155 | 8,271 | 9.76% |
| 2014Q2 | 91,769 | 9,682 | 8,162 | 17,844 | 10,056 | 10.55% |
| 2014Q3 | 80,388 | 8,392 | 7,047 | 15,439 | 8,819 | 10.44% |
| 2014Q4 | 111,948 | 10,408 | 9,500 | 19,908 | 10,895 | 9.30% |
| 2015Q1 | 85,605 | 7,894 | 8,121 | 16,015 | 8,239 | 9.22% |
| 2015Q2 | 107,043 | 10,501 | 9,996 | 20,497 | 10,919 | 9.81% |
| 2015Q3 | 94,035 | 10,033 | 9,001 | 19,034 | 10,443 | 10.67% |
| 2015Q4 | 115,030 | 11,162 | 11,004 | 22,166 | 11,654 | 9.70% |
| 2016Q1 | 103,592 | 9,779 | 10,281 | 20,060 | 10,198 | 9.44% |
| 2016Q2 | 123,438 | 12,254 | 12,222 | 24,476 | 12,705 | 9.93% |
| 2016Q3 | 104,142 | 10,061 | 10,290 | 20,351 | 10,578 | 9.66% |
| 2016Q4 | 126,565 | 11,150 | 12,373 | 23,523 | 11,628 | 8.81% |
| 2017Q1 | 124,756 | 10,732 | 12,714 | 23,446 | 11,250 | 8.60% |
| 2017Q2 | 143,761 | 12,555 | 14,765 | 27,320 | 13,109 | 8.73% |
| 2017Q3 | 119,162 | 10,819 | 12,590 | 23,409 | 11,409 | 9.08% |
| 2017Q4 | 144,582 | 12,306 | 14,497 | 26,803 | 12,894 | 8.51% |
| 2018Q1 | 135,438 | 10,794 | 14,145 | 24,939 | 11,333 | 7.97% |
| 2018Q2 | 161,374 | 12,499 | 16,586 | 29,085 | 13,110 | 7.75% |
| 2018Q3 | 131,800 | 10,364 | 11,147 | 21,511 | 11,095 | 7.86% |
| 2018Q4 | 154,276 | 11,267 | 14,275 | 25,542 | 12,019 | 7.30% |
| 2019Q1 | 138,374 | 9,645 | 13,961 | 23,606 | 10,289 | 6.97% |
| 2019Q2 | 149,600 | 11,030 | 14,354 | 25,384 | 11,708 | 7.37% |
| 2019Q3 | 123,687 | 9,568 | 11,861 | 21,429 | 10,216 | 7.74% |
| 2019Q4 | 158,332 | 11,272 | 14,588 | 25,860 | 11,996 | 7.12% |
| 2020Q1 | 116,029 | 8,646 | 11,698 | 20,344 | 9,178 | 7.45% |
| 2020Q2 | 78,918 | 3,244 | 6,537 | 9,781 | 3,508 | 4.11% |
| 2020Q3 | 132,113 | 8,636 | 11,277 | 19,913 | 9,263 | 6.54% |
| 2020Q4 | 160,294 | 8,465 | 13,133 | 21,598 | 9,121 | 5.28% |
| 2021Q1 | 141,851 | 6,242 | 12,279 | 18,521 | 6,791 | 4.40% |
| 2021Q2 | 177,997 | 9,430 | 15,737 | 25,167 | 10,156 | 5.30% |
| 2021Q3 | 161,300 | 12,109 | 14,508 | 26,617 | 13,073 | 7.51% |
| 2021Q4 | 193,101 | 16,010 | 16,675 | 32,685 | 17,108 | 8.29% |
| 2022Q1 | 175,383 | 14,860 | 16,767 | 31,627 | 15,814 | 8.47% |
| 2022Q2 | 199,578 | 17,814 | 19,318 | 37,132 | 18,902 | 8.93% |
| 2022Q3 | 168,793 | 15,526 | 17,177 | 32,703 | 16,642 | 9.20% |
| 2022Q4 | 173,980 | 14,839 | 18,291 | 33,130 | 15,848 | 8.53% |
| 2023Q1 | 158,006 | 13,452 | 17,003 | 30,455 | 14,351 | 8.51% |
| 2023Q2 | 170,564 | 15,202 | 18,278 | 33,480 | 16,132 | 8.91% |
| 2023Q3 | 142,281 | 12,725 | 15,703 | 28,428 | 13,701 | 8.94% |
| 2023Q4 | 167,740 | 13,538 | 17,205 | 30,743 | 14,548 | 8.07% |
| 2024Q1 | 160,441 | 12,617 | 16,850 | 29,467 | 13,532 | 7.86% |
| 2024Q2 | 189,761 | 15,669 | 19,570 | 35,239 | 16,660 | 8.26% |
| 2024Q3 | 166,176 | 13,690 | 17,067 | 30,757 | 14,675 | 8.24% |
| 2024Q4 | 199,300 | 14,801 | 19,091 | 33,892 | 15,955 | 7.43% |
| 2025Q1 | 184,040 | 13,707 | 19,015 | 32,722 | 14,635 | 7.45% |
| 2025Q2 | 196,561 | 13,536 | 19,673 | 33,209 | 14,583 | 6.89% |
| 2025Q3 | 171,056 | 11,531 | 17,356 | 28,887 | 12,541 | 6.74% |
| 2025Q4 | 200,250 | 12,593 | 19,596 | 32,189 | 13,652 | 6.29% |
| 2026Q1 | 163,322 | 10,704 | 16,273 | 26,977 | 11,556 | 6.55% |
Annual sums of the same table (2026 is Q1 only):

| Year | Total transactions | Non-resident foreigners | All foreigners | Non-res. foreign share | All-foreign share |
|---|---|---|---|---|---|
| 2007 | 836,871 | 24,489 | 59,600 | 2.93% | 7.12% |
| 2008 | 564,464 | 17,747 | 35,960 | 3.14% | 6.37% |
| 2009 | 463,719 | 14,124 | 40,956 | 3.05% | 8.83% |
| 2010 | 491,287 | 15,283 | 39,609 | 3.11% | 8.06% |
| 2011 | 349,118 | 18,382 | 39,996 | 5.27% | 11.46% |
| 2012 | 363,623 | 25,041 | 50,338 | 6.89% | 13.84% |
| 2013 | 300,568 | 29,496 | 54,191 | 9.81% | 18.03% |
| 2014 | 365,621 | 36,438 | 68,346 | 9.97% | 18.69% |
| 2015 | 401,713 | 39,590 | 77,712 | 9.86% | 19.35% |
| 2016 | 457,737 | 43,244 | 88,410 | 9.45% | 19.31% |
| 2017 | 532,261 | 46,412 | 100,978 | 8.72% | 18.97% |
| 2018 | 582,888 | 44,924 | 101,077 | 7.71% | 17.34% |
| 2019 | 569,993 | 41,515 | 96,279 | 7.28% | 16.89% |
| 2020 | 487,354 | 28,991 | 71,636 | 5.95% | 14.70% |
| 2021 | 674,249 | 43,791 | 102,990 | 6.49% | 15.27% |
| 2022 | 717,734 | 63,039 | 134,592 | 8.78% | 18.75% |
| 2023 | 638,591 | 54,917 | 123,106 | 8.60% | 19.28% |
| 2024 | 715,678 | 56,777 | 129,355 | 7.93% | 18.07% |
| 2025 | 751,907 | 51,367 | 127,007 | 6.83% | 16.89% |
| 2026 (Q1 only, provisional) | 163,322 | 10,704 | 26,977 | 6.55% | 16.52% |
### 3.2 Notariado CIEN, semi-annual, 1S2007–2S2025 — cross-check plus the €/m² premium

Source: CIEN annex XLSX, sheet "1_Nacionalidad y residencia", Tables 1 (levels) and 1C (mean
€/m²). Basis: **vivienda libre only**, operations and mean price per built m², nationality ×
residence. "Spanish nationals" is the `Nacional` total row (residents + Spaniards abroad);
`Nacional / Residente` differs from it by at most ~1% and is not shown.

| Semester | Total (vivienda libre) | Non-resident foreigners | Resident foreigners | All foreigners | Non-res. foreign share | €/m² non-res. foreign | €/m² resident foreigners | €/m² Spanish nationals | €/m² all buyers | Premium (non-res. foreign / Spanish) |
|---|---|---|---|---|---|---|---|---|---|---|
| 07H1 | 435,835 | 13,002 | 20,146 | 33,148 | 2.98% | 2,185 | 1,731 | 2,132 | 2,113 | 1.02× |
| 07H2 | 354,005 | 11,568 | 12,958 | 24,526 | 3.27% | 2,303 | 1,822 | 1,847 | 1,862 | 1.25× |
| 08H1 | 285,982 | 9,734 | 8,322 | 18,056 | 3.40% | 2,422 | 1,903 | 1,817 | 1,842 | 1.33× |
| 08H2 | 224,388 | 7,910 | 8,748 | 16,658 | 3.53% | 2,309 | 1,959 | 1,801 | 1,828 | 1.28× |
| 09H1 | 197,507 | 6,364 | 13,062 | 19,426 | 3.22% | 2,074 | 1,759 | 1,746 | 1,760 | 1.19× |
| 09H2 | 216,310 | 7,664 | 13,004 | 20,668 | 3.54% | 2,114 | 1,758 | 1,719 | 1,738 | 1.23× |
| 10H1 | 237,747 | 8,005 | 12,364 | 20,369 | 3.37% | 2,059 | 1,728 | 1,737 | 1,749 | 1.19× |
| 10H2 | 212,285 | 7,435 | 11,423 | 18,858 | 3.50% | 1,872 | 1,756 | 1,651 | 1,666 | 1.13× |
| 11H1 | 149,211 | 8,813 | 10,256 | 19,069 | 5.91% | 1,937 | 1,646 | 1,586 | 1,616 | 1.22× |
| 11H2 | 165,673 | 9,745 | 10,856 | 20,601 | 5.88% | 1,834 | 1,544 | 1,557 | 1,575 | 1.18× |
| 12H1 | 143,076 | 10,053 | 11,539 | 21,592 | 7.03% | 1,756 | 1,450 | 1,381 | 1,417 | 1.27× |
| 12H2 | 190,015 | 15,388 | 13,335 | 28,723 | 8.10% | 1,716 | 1,399 | 1,344 | 1,381 | 1.28× |
| 13H1 | 131,228 | 13,338 | 11,512 | 24,850 | 10.16% | 1,640 | 1,428 | 1,238 | 1,303 | 1.32× |
| 13H2 | 159,303 | 16,663 | 13,033 | 29,696 | 10.46% | 1,674 | 1,344 | 1,238 | 1,304 | 1.35× |
| 14H1 | 165,908 | 17,732 | 15,090 | 32,822 | 10.69% | 1,685 | 1,376 | 1,251 | 1,315 | 1.35× |
| 14H2 | 184,325 | 18,959 | 16,266 | 35,225 | 10.29% | 1,706 | 1,362 | 1,212 | 1,284 | 1.41× |
| 15H1 | 185,177 | 18,583 | 17,786 | 36,369 | 10.04% | 1,778 | 1,352 | 1,254 | 1,324 | 1.42× |
| 15H2 | 200,549 | 21,336 | 19,455 | 40,791 | 10.64% | 1,810 | 1,378 | 1,241 | 1,324 | 1.46× |
| 16H1 | 218,199 | 22,204 | 21,974 | 44,178 | 10.18% | 1,856 | 1,366 | 1,285 | 1,356 | 1.44× |
| 16H2 | 221,679 | 21,374 | 22,074 | 43,448 | 9.64% | 1,877 | 1,357 | 1,301 | 1,368 | 1.44× |
| 17H1 | 259,665 | 23,642 | 26,902 | 50,544 | 9.10% | 1,946 | 1,406 | 1,354 | 1,420 | 1.44× |
| 17H2 | 254,538 | 23,258 | 26,316 | 49,574 | 9.14% | 2,026 | 1,420 | 1,350 | 1,426 | 1.50× |
| 18H1 | 286,691 | 23,478 | 29,961 | 53,439 | 8.19% | 1,984 | 1,425 | 1,385 | 1,443 | 1.43× |
| 18H2 | 276,393 | 22,110 | 28,141 | 50,251 | 8.00% | 2,080 | 1,459 | 1,413 | 1,477 | 1.47× |
| 19H1 | 278,499 | 21,204 | 30,520 | 51,724 | 7.61% | 2,099 | 1,444 | 1,428 | 1,486 | 1.47× |
| 19H2 | 273,546 | 21,368 | 29,172 | 50,540 | 7.81% | 2,219 | 1,457 | 1,451 | 1,519 | 1.53× |
| 20H1 | 187,762 | 12,170 | 20,262 | 32,432 | 6.48% | 2,250 | 1,478 | 1,471 | 1,529 | 1.53× |
| 20H2 | 283,208 | 17,583 | 27,479 | 45,062 | 6.21% | 2,219 | 1,425 | 1,406 | 1,467 | 1.58× |
| 21H1 | 310,977 | 16,184 | 31,622 | 47,806 | 5.20% | 2,452 | 1,499 | 1,484 | 1,547 | 1.65× |
| 21H2 | 344,666 | 28,918 | 35,020 | 63,938 | 8.39% | 2,480 | 1,567 | 1,503 | 1,608 | 1.65× |
| 22H1 | 364,429 | 33,510 | 39,957 | 73,467 | 9.20% | 2,526 | 1,630 | 1,563 | 1,673 | 1.62× |
| 22H2 | 332,809 | 31,234 | 38,948 | 70,182 | 9.38% | 2,558 | 1,668 | 1,553 | 1,674 | 1.65× |
| 23H1 | 320,269 | 29,440 | 38,764 | 68,204 | 9.19% | 2,599 | 1,677 | 1,576 | 1,692 | 1.65× |
| 23H2 | 302,635 | 26,980 | 36,210 | 63,190 | 8.92% | 2,716 | 1,720 | 1,580 | 1,712 | 1.72× |
| 24H1 | 343,185 | 29,046 | 40,697 | 69,743 | 8.46% | 2,895 | 1,734 | 1,658 | 1,784 | 1.75× |
| 24H2 | 358,100 | 29,201 | 40,489 | 69,690 | 8.15% | 3,063 | 1,795 | 1,713 | 1,847 | 1.79× |
| 25H1 | 372,617 | 27,988 | 43,637 | 71,625 | 7.51% | 3,125 | 1,915 | 1,812 | 1,934 | 1.72× |
| 25H2 | 362,175 | 24,793 | 41,836 | 66,629 | 6.85% | 3,242 | 1,963 | 1,839 | 1,964 | 1.76× |
The 2S24 column reproduces the point estimate already in `docs/sources.md` (3,063 vs 1,713)
exactly — that row was a snapshot of this series.

### 3.3 Registradores ERI — what is actually readable

The earlier pass's diagnosis was wrong: the ERI PDFs **do** carry an extractable text layer.
PyMuPDF 1.28.2 (installed into a scratch venv with `uv pip`) reads all 122 pages of
`eri_2t_2026.pdf` as text with no CMap work. What blocks a *series* is different and
unfixable by tooling: **ERI's history is published only as vector charts**. Axis tick labels
(`13 T2`, `14 T2`, …) and the current-period data labels are text; the plotted values are line
geometry. Recovering them would mean measuring pixels off a chart, i.e. estimating figures,
which this project forbids.

What the text layer does give, all **all-foreigner basis, no residence split**:

| Basis | Period | Foreign share of registered home purchases |
|---|---|---|
| Quarterly | 2026Q2 | 15.98% (record; ≈26,800 operations) |
| Quarterly | 2026Q1 | 13.92% |
| Quarterly | 2025Q4 | 13.52% |
| 12-month to Q2 | 2018 → 2026 | 13.08, 12.35, 12.06, 10.37, 12.84, 14.49, 14.88, 14.38, 14.22% |
| 12-month to Q4 | 2018 → 2025 | 12.64, 12.45, 11.32, 10.80, 13.75, 14.98, 14.60, 13.82% |

Nine and eight annual points respectively, starting 2018. Too short and too coarse to test
co-movement over a cycle, and on the wrong basis (all foreigners) — which is why §4 uses MIVAU
and CIEN. ERI's 2026Q2 world-zone €/m² table is in the register row in §1; it is a
nationality-zone cut, not a residence cut, so it cannot substitute for the CIEN premium series.

---

## 4. The falsification test

### 4.1 What "one-for-one" has to mean

The mechanism being replaced makes non-resident arrivals **proportional to recent Spanish
sales**: `arrivals_t = k × sales_t` with `k` fixed. One-for-one therefore means two things at
once, and the second is the binding one:

1. **Elasticity 1** — a 1% change in total transactions goes with a 1% change in non-resident
   purchases; and
2. **A stable ratio** — the non-resident *share* of transactions does not wander, because `k`
   is a constant of the mechanism.

A test that only regresses growth rates can pass on (1) while (2) fails badly, so both are
reported. All regressions are OLS on natural logs; `beta` is the elasticity; the 95% CI is
±1.96 × the classical standard error, which is optimistic on serially-correlated quarterly data —
so a CI that already excludes 1 is a strong rejection, and one that includes 1 is weak evidence
for it.

### 4.2 Elasticity — MIVAU quarterly, `log(non-resident foreigners)` on `log(total transactions)`

| Window | n | corr(log) | elasticity β | 95% CI | R² |
|---|---|---|---|---|---|
| 2007Q1–2026Q1 (full) | 77 | +0.502 | **+0.755** | [+0.461, +1.050] | 0.252 |
| 2007Q1–2025Q4 (the spec's window) | 76 | +0.499 | **+0.753** | [+0.455, +1.050] | 0.249 |
| 2007Q1–2013Q4 (**sealed hold-out**) | 28 | **+0.116** | **+0.093** | [−0.215, +0.401] | **0.013** |
| 2014Q1–2026Q1 | 49 | +0.713 | +0.769 | [+0.553, +0.985] | 0.508 |
| 2014–2019 + 2022–2026 (ex-COVID) | 41 | +0.863 | +0.630 | [+0.514, +0.745] | 0.744 |

Comparison rows, same specification:

| Series (vs total transactions, full window) | corr | β | 95% CI | R² |
|---|---|---|---|---|
| **Non-resident foreigners** | +0.502 | +0.755 | [+0.461, +1.050] | 0.252 |
| All non-residents (incl. Spaniards abroad) | +0.568 | +0.828 | [+0.556, +1.099] | 0.323 |
| All foreigners (resident + non-resident) | +0.622 | +0.888 | [+0.635, +1.141] | 0.387 |
| **Resident foreigners** | +0.688 | **+1.009** | [+0.768, +1.250] | 0.473 |

Resident foreigners *do* track domestic volume essentially one-for-one (β = 1.01). Non-residents
do not, and explain a quarter of the variance where residents explain half. That contrast is
itself evidence that the two groups are different mechanisms, which is what the redesign assumes.

### 4.3 Elasticity — Notariado CIEN semi-annual, independent confirmation

| Window | n | corr(log) | β | 95% CI | R² |
|---|---|---|---|---|---|
| 1S07–2S25 (full) | 38 | +0.519 | **+0.797** | [+0.368, +1.226] | 0.269 |
| 1S07–2S13 (**sealed hold-out**) | 14 | **−0.030** | **−0.025** | [−0.502, +0.451] | **0.001** |
| 1S14–2S25 | 24 | +0.727 | +0.696 | [+0.421, +0.971] | 0.528 |
| All foreigners, full window | 38 | +0.645 | +0.993 | [+0.608, +1.377] | 0.416 |
| Resident foreigners, full window | 38 | +0.709 | +1.168 | [+0.788, +1.547] | 0.503 |

Same pattern, same magnitudes, different institution and different housing coverage.

### 4.4 Growth rates, reported because they are the strongest case *for* co-movement

Year-on-year log changes (removes the pronounced quarterly seasonality both series share):

| Window (MIVAU, y/y log changes) | n | corr | β | 95% CI | t(β = 1) |
|---|---|---|---|---|---|
| 2008Q1–2026Q1 | 73 | +0.663 | +0.905 | [+0.667, +1.142] | −0.79 |
| 2008Q1–2013Q4 (**hold-out**) | 24 | +0.655 | +0.838 | [+0.434, +1.242] | −0.79 |
| 2014Q1–2026Q1 | 49 | +0.821 | **+1.446** | [+1.159, +1.733] | **+3.05** |
| excluding 2020 and 2021 | 65 | +0.548 | +0.657 | [+0.409, +0.905] | **−2.71** |
| CIEN, 2-semester log changes, 1S08–2S25 | 36 | +0.607 | +0.712 | [+0.399, +1.025] | −1.81 |

**Stated plainly: on year-on-year growth rates the data cannot reject one-for-one** on the full
window (β = 0.905, CI covers 1). That is the honest strongest form of the opposing case, and it
is reported here as readily as the rest. But the growth-rate result is unstable across
sub-samples — 1.45 after 2013, 0.66 once COVID is dropped, both rejecting 1 in opposite
directions — and a shared response to common shocks (COVID closes notaries for everyone) is not
the same as a proportional mechanism. What settles it is the levels, below.

### 4.5 The decisive number: the ratio is not stable

If `arrivals = k × sales` with `k` fixed, the non-resident share is a constant. It is not.

| | MIVAU (quarterly, all housing) | CIEN (semi-annual, vivienda libre) |
|---|---|---|
| Minimum non-resident foreign share | **2.55%** (2007Q1) | **2.98%** (1S07) |
| Maximum | **10.67%** (2015Q3) | **10.69%** (1S14) |
| Range | **4.18×** | **3.58×** |
| Latest | 6.55% (2026Q1) | 6.85% (2S25) |

**The bust, 2007 → 2013** (this is the sealed hold-out window — reported, used for nothing):

| | MIVAU | CIEN |
|---|---|---|
| Total transactions 2007 → 2013 | 836,871 → 300,568 = **−64.1%** | 789,840 → 290,531 = **−63.2%** |
| Non-resident foreign purchases 2007 → 2013 | 24,489 → 29,496 = **+20.4%** | 24,570 → 30,001 = **+22.1%** |
| Implied arc elasticity log(N₁₃/N₀₇)/log(T₁₃/T₀₇) | **−0.182** | **−0.200** |
| (all foreigners, same calculation) | 59,600 → 54,191 = −9.1%, elasticity +0.093 | 57,674 → 54,546 = −5.4%, elasticity +0.056 |

The domestic market lost roughly two thirds of its volume and non-resident purchases went
**up**. The arc elasticity is not 1; it is slightly negative.

**The counterfactual the replaced mechanism would have produced.** Fix `k` at the 2007 share
(MIVAU 2.926% of all transactions; CIEN 3.111% of vivienda libre) and predict forward:

| Year | Actual non-resident foreign purchases | `k × total transactions` | Actual ÷ predicted |
|---|---|---|---|
| 2013 | 29,496 | 8,795 | **3.35×** (+235%) |
| 2015 | 39,590 | 11,755 | **3.37×** (+237%) |
| 2025 | 51,367 | 22,003 | **2.33×** (+133%) |

CIEN gives 3.32× / 3.33× / 2.31× for the same three years. RMSE of the log ratio across all 77
quarters: **0.891 log points** (CIEN, 38 semesters: 0.887) — the proportional overlay is wrong
by a factor of 2.4 on average, in the same direction for a decade at a stretch.

### 4.6 Verdict

**The falsification test does not fire. The exogenous treatment in §7.4 stands.**

- The non-resident purchase series does **not** track Spanish transaction volume one-for-one in
  levels: full-window elasticity 0.75 (MIVAU) / 0.80 (CIEN) with R² ≈ 0.25–0.27, and over the
  2008–13 bust the relationship is **absent** (corr +0.12 / −0.03, R² 0.013 / 0.001) and the two
  series move in opposite directions.
- The implied ratio moves by a factor of 3.6–4.2 over the sample, so no constant `k` exists.
- The one result that favours the endogenous treatment — a y/y growth elasticity of 0.905 whose
  CI covers 1 — is not robust to sub-sampling and is consistent with common shocks rather than
  proportionality.

Two riders the spec should absorb:

1. **Do not over-claim independence either.** Post-2013, non-resident purchases and domestic
   volume *do* co-move (corr +0.71 to +0.86, elasticity ~0.63–0.77). An exogenous stream with
   its own cycle is right; an exogenous stream that ignores Spanish conditions entirely would
   overshoot in the other direction. The data support "own cycle, partially correlated", not
   "orthogonal".
2. **The contrast is between resident and non-resident foreigners, not between Spaniards and
   foreigners.** Resident foreigners track domestic volume at β = 1.01 (MIVAU) / 1.17 (CIEN).
   If the model has a single "foreign" agent, it is averaging two mechanisms with opposite
   cyclical behaviour. §7.4's overlay must be non-resident only, as written.

**Hold-out discipline.** The 2007Q1–2013Q4 rows above fall inside the sealed window of
`docs/holdout-2008-2013.md`. They are reported here as evidence about the *specification* — the
question "is this mechanism admissible" — and no parameter may be fitted to them. The
calibration window remains 2014–2025.

---

## 5. The €/m² premium (spec §7.4 anchors the foreign budget to it)

§7.4 writes the premium as a fixed pair, "3,063 vs 1,713". That pair is real — it is CIEN
**2S2024**, non-resident foreigners vs all Spanish nationals — but it is one point on a series
that has moved by more than the ratio itself.

| Period | €/m² non-resident foreigners | €/m² Spanish nationals | Premium |
|---|---|---|---|
| 1S2007 | 2,185 | 2,131 | **1.03×** |
| 2S2010 | 1,872 | 1,650 | 1.13× |
| 2S2013 | 1,674 | 1,236 | 1.35× |
| 2S2015 | 1,810 | 1,238 | 1.46× |
| 2S2019 | 2,219 | 1,447 | 1.53× |
| 2S2021 | 2,480 | 1,499 | 1.65× |
| 2S2024 | 3,063 | 1,713 | **1.79×** (the spec's point) |
| 2S2025 | 3,242 | 1,832 | 1.77× |

Full 38-semester history in §3.2. Two things follow for the model:

- **The premium is not a constant.** It ran from 1.03× (1S07) to 1.79× (2S24) — a 75% drift in
  the multiplier, monotone apart from noise, and it widened *through* the bust while volumes
  diverged. A single fixed premium parameter will misprice the overlay in any run that spans
  more than a few years. This is the same finding as §4 wearing different clothes: the
  non-resident buyer is a different buyer, and increasingly so.
- **Nominal €/m², vivienda libre, mean not median, per built m².** Not deflated, not
  quality-adjusted, not hedonic. Compositional shift (non-residents buying more coastal and more
  premium stock) is inside this number and cannot be separated from it with the published
  tables. Treat 1.03× → 1.79× as a *range*, per the project's bias-control rule, not as a
  resolved trend estimate.

Resident foreigners for reference: 1,731 €/m² (1S07) → 1,963 (2S25), i.e. ~1.07× Spaniards
throughout. Again the resident/non-resident line is where the behaviour changes, not the
Spanish/foreign line.

---

## 6. Reproducing this

Everything above comes from two downloads and no manual transcription.

```
# 1. MIVAU quarterly, residence of buyer (1.3 MB BIFF8 .xls, 77 worksheet tabs)
curl -L -o 340101d0.xls https://apps.fomento.gob.es/BoletinOnline2/sedal/340101d0.XLS
#    read with xlrd>=2.0 (xlrd 2.x supports .xls, not .xlsx); TOTAL NACIONAL row of each tab

# 2. Notariado CIEN semi-annual annex (285 KB .xlsx)
curl -L -A "Mozilla/5.0" -o cien_anexo.xlsx \
 "https://www.notariado.org/liferay/c/document_library/get_file?uuid=125f548a-e4f2-498c-b9ea-3a736e10941a&groupId=2289837"
#    read with openpyxl; sheet "1_Nacionalidad y residencia", rows 8-14 (ops) and 40-46 (EUR/m2)

# 3. Registradores ERI (text layer extracts fine, contrary to the earlier pass)
curl -L -o eri_2t_2026.pdf https://www.registradores.org/documents/d/guest/eri_2t_2026
#    uv pip install pymupdf ; pymupdf.open(...).get_text() -- pages 33-45 are the foreign section
```

Regressions: OLS on natural logs via `numpy.polyfit`, classical standard errors. No
seasonal adjustment except where the table says "y/y log changes". No smoothing, no imputation.

---

## 7. Not retrieved

| Item | What blocked it | What it blocks |
|---|---|---|
| **Registradores ERI quarterly non-resident series** | Does not exist as a published statistic. The ERI splits buyers by **nationality only**; no resident/non-resident cut appears anywhere in the 2026Q2 (122 pp) or 2025Q4 reports, nor in their methodology annex (pp. 116–121). | Nothing. The spec names Registradores as the falsification source, but the series it describes is MIVAU's and Notariado's. **The spec's §7.4 wording should be corrected to name the actual source** — see "Follow-ups" below. |
| **Registradores ERI quarterly foreign-share history 2013Q2–2026Q2** | Published only as vector line charts. Text layer extracts (PyMuPDF works — the earlier pass's CID-font diagnosis was wrong), but the plotted values are line geometry, not text; only axis labels and current-period data labels are readable. Recovering them means measuring a chart, i.e. estimating figures. | A third independent long series. Not needed — MIVAU and CIEN already agree to ~3%. |
| **`eri_1t_2026`** | HTTP 404 (93,790-byte error page, `Content-Type: text/html`). Confirmed still 404 on 2026-09-14. | Nothing; 2026Q1 foreign share is quoted in the 2026Q2 report (13.92%). |
| **MIVAU methodology note for Tabla 1.6** | `mivau.gob.es/.../transacciones-inmobiliarias-compraventa/metodologia` → **HTTP 403 "Página web bloqueada"** (WAF, both via WebFetch and curl with a browser UA). Mirror `transportes.gob.es/.../transacciones-inmobiliarias-compraventa` → **403** likewise. The listing page itself (no `/metodologia`) fetches fine but contains only navigation. | **The formal definition of "residencia del comprador"** — whether residence is taken from the escritura, the NIE/NIF, or a fiscal-residence declaration, and how "No consta" is handled (it is 0 in every quarter, which is itself suspicious of a coding rule rather than a genuine absence of unknowns). Recorded as an open question; it does not affect the §4 result, which is robust across two systems that must use different residence rules. |
| **INE ETDP foreign/non-resident breakdown** | Does not exist. All 17 ETDP tables enumerated via Tempus3; the only buyer dimension is `Tipo de titular` = {Persona física, Persona jurídica}. Not a fetch failure — a confirmed negative. | Nothing. Closed; do not re-check. |
| **CIEN series before 1S2007** | The annex starts at 1S07. (Its own ÍNDICE sheet claims "series brutas … desde 1S2016", which contradicts the 1S07 columns actually present. Both statements recorded; not resolved.) | Pre-boom baseline. Not needed for §4. |
| **Non-resident €/m² on a quarterly frequency** | CIEN publishes the residence × price cross-tab semi-annually only. ERI's quarterly €/m² cut is by **world zone of nationality**, not residence. | Quarterly premium dynamics. The 38 semi-annual points in §3.2 are sufficient for a parameter range. |
| **Deflated / quality-adjusted non-resident price premium** | No published hedonic or repeat-sales index split by buyer residence, from any of the three institutions. | Separating the premium's drift from compositional shift. Flagged in §5; the premium must enter the model as a range, not a point. |
| **Non-resident share by zone type (tensioned metro / secondary city / rural)** | MIVAU Tabla 1.6 publishes CCAA and province, not the model's three zone types; the mapping is a modelling decision, not a retrieval. Provincial detail is in the same XLS if wanted (Alicante 46.4%, Málaga 37.0%, Balears 32.3% vs Extremadura 2.9% in ERI 2026Q2 — all-foreigner basis). | Zone-level calibration of the overlay. Retrievable from the same file when phase B needs it; not attempted here. |

### Follow-ups for whoever owns the spec and the register

1. **`docs/superpowers/specs/2026-09-11-model-redesign-design.md` §7.4** names Registradores as
   the falsification source. Registradores does not publish a non-resident series. The test as
   run uses MIVAU Tabla 1.6 and Notariado CIEN; the sentence should name them.
2. **§7.4's "3,063 vs 1,713"** should become a range with a date — it is CIEN 2S2024, and the
   series runs 1.03× (1S07) to 1.79× (2S24).
3. **`docs/sources.md`** rows 55 (ERI) and 58 (CIEN) describe the foreign-buyer content as if it
   were one thing. Row 55's "foreign 13.5% Q4 / 13.8% 2025" is the **all-foreigner** ERI basis;
   row 221's CaixaBank "non-residents 7.9% of sales" is the **non-resident** MIVAU basis. They
   are not comparable and currently read as if they were.
