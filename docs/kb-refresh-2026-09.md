# Knowledge-base refresh, 2026-09-08 — what was new, what changed, what broke

**Question asked.** The register (`sources.md`) was last refreshed on 2026-08-10 and the model
was last revised on 2026-08-14 (Funcas 104). Four weeks later: which Tier-1 releases, legal
changes, studies and forecasts had appeared that the knowledge base did not hold, and which of
them change a parameter, a mechanism, a validation band or a benchmark row?

**Method.** Four parallel research passes (statistics, policy/legal, studies, forecast panel),
each row verified by fetching the primary page where possible and flagged otherwise; a fifth
pass mapped every dossier parameter to its data vintage. The verbatim digest is not kept in the
repo (it is a working file); everything that survived is registered in `sources.md` with its
verification flag, appended as a dated `Update 2026-09-08` section to the relevant dossier or
policy note, and summarised here. Nothing below is applied twice: where a figure changed a
parameter, the `config.py` comment carries the same citation.

Verification vocabulary: **verified** = read on the fetched primary page; **via secondary** =
read on a fetched non-primary page because the primary blocks robots (INE tables are JS,
mivau.gob.es returns 403); **unverified** = search snippet or press only.

---

## 1. What changed in the model

| # | Change | Where | Evidence |
|---|---|---|---|
| 1 | **INE household projection vintages.** The scenario path carried the 2022–2037 projection (215k → 190k → 140k/yr) as *the* INE path. INE published 2024–2039 (333k → 228k → 177k) and, on 17 Jun 2026, 2026–2041 (**205k → 139k → 93k**). All three are now selectable; the latest is the default | `scenario.INE_HOUSEHOLD_PROJECTIONS`, `ine_household_projection(vintage=)`, CLI `ine-demography[-2024|-2022]` | INE notas de prensa (verified) — §2 |
| 2 | **Rent-cap coverage.** The law is declared municipality by municipality; Spain has 317 declared municipalities in 5 CCAA covering ≈19% of the population, while the model's tensioned zone holds 45% of households. A per-unit coverage draw (default 1.0) separates "not declared" from "not complying" | `PolicyConfig.cap_coverage`, `RentCap.coverage`, landlord and investor agents, UI slider | BOE-A-2026-16532 (verified) — §3 |
| 3 | **Transaction tax by buyer type.** Cataluña charges 20% TPO on whole-building and gran-tenedor purchases; the "100% tax on non-EU buyers" is a live bill. The two aggregate cash buyers now face a budget wedge `(1+base)/(1+effective)` so a surcharge aimed at them is runnable | `PolicyConfig.itp_investor_delta`, `itp_foreign_delta`, `bank.itp_wedge`, investor and overlay offers, UI sliders | Ley 11/2026 via law-firm summary (medium); Reuters/Congreso (bill) — §3 |
| 4 | **ICO guarantee wealth cap.** The Jul 2026 adenda added a €150k net-wealth filter and extended the line to Dec 2027 | `PolicyConfig.guarantee_wealth_cap`, `DemandSubsidy.guarantee_wealth_cap`, household eligibility | BOE-A-2026-14404 (verified) — §3 |
| 5 | **IRAV read relative to the income anchor.** `within_contract_update` 0.025 → **0.015**. IRAV (2.20–2.44%) runs at 0.6–0.75 of nominal wage growth; the model's anchor is 2%/yr. At 0.025 the frozen reference index outran the market it capped and the cap silently unbound — see §7 | `PolicyConfig.within_contract_update`, engine reference-index indexation | INE IRAV; measured — §7 |
| 6 | **Capped-listing floor.** A rental ask now decays to the cap floor only if the listing was actually clipped by the cap; uncovered or non-complying listings keep the yield floor. Without this a cap with zero coverage still lowered asks | `engine._apply_listings` | mechanism consistency — §7 |
| 7 | **VUT anchor.** Tensioned `seasonal_share` 0.028 → 0.025 so the model's seasonal units re-inflate to ≈345k against INE's 341,001 (May 2026) | `ZoneConfig.seasonal_share` | INE viviendas turísticas 24 Jun 2026 (via secondary) — §4 |
| 8 | **Two new indicators and rows.** `foreign_purchase_share` (non-resident basis, official 7.9%) and `investor_purchase_share` (legal persons, official ≈10%) | `metrics.py`, `benchmarks.py` | CaixaBank Research on MIVAU; BdE IA 2025 — §4 |
| 9 | **Cash-purchase row re-based.** Central value 60.8% (INE-derived) → **29.3%** (Registradores, 12-month 2025), band 23–46% spanning Registradores 2026Q2 and Notariado Jun 2026 | `benchmarks.py` | Registradores ERI; Notariado CIEN (verified) — §4 |
| 10 | **Bands and periods refreshed.** Formation band 225–250k (ECP +226k in 2025, +239k y/y); ownership sources add ECV 2025 73.3%; price-growth row adds IPV 2026Q2 +12.2%; rent-growth row adds idealista Aug 2026 +5.8%; deficit row adds the BBVA path; §9 target 5 lower edge 27 → 26.8% (Eurostat 2025) | `benchmarks.py`, `model-spec` §9 | INE, Eurostat (verified) — §4 |
| 11 | **Rent-cap gate re-tested and found broken on the tenancy leg.** Two new tests pin the honest state: contract rents fall under a cap (passes); new tenancies at elasticity 2 must fall ≥5% (strict xfail) | `tests/test_validation.py` | measured — §7 |

Measured consequences of 5–7 and the re-measured validation table are in `docs/validation.md`
("KB refresh 2026-09 revision"). UI help texts for the rent cap, ITP, public housing and
tourist-rental levers carry the new figures (`ui/levers.py`, `ui/texts.py`).

## 2. Demography — the projection was cut, and the cut is the point

INE's household projections, five-year blocks, net new households per year:

| Vintage (published) | Block 1 | Block 2 | Block 3 | Households at horizon |
|---|---|---|---|---|
| 2022–2037 (Oct 2022, via Funcas 104) | 215k (2023–27) | 190k (2028–32) | 140k (2033–37) | — |
| 2024–2039 (24 Jun 2024) | **333k** (2024–29; 1,667,063) | 228k (2029–34; 1,140,804) | 177k (2034–39; 883,284) | 23.00M |
| **2026–2041 (17 Jun 2026)** | **205k** (2026–31; 1,024,156) | 139k (2031–36; 696,381) | 93k (2036–41; 463,511) | 21.94M |

The June 2026 revision removes ≈1.5M households from the fifteen-year horizon relative to the
2024 vintage; mean household size goes 2.49 → 2.43 and single-person households 28.4% → 30.6%.
Observed formation stays high for now — **+226,279 in 2025, +239k y/y to 1 Jul 2026, 19,874,860
households** (INE ECP, verified) — which is why the baseline keeps 240k/yr and the projection is
a *scenario path*. Bias-control reading: the projected deficit is partly a demographic
assumption, and the spread between vintages is its honest measure. Migration dominates: the
foreign-born population grew +736k, +634k and +626k in 2022–24 to 19.3% of residents (BdE DO
2610, verified); INE's net migration series for 2025 is due Dec 2026.

## 3. Policy and legal — what moved between July and September 2026

**Rent regulation.**
- **Tensioned zones: 317 municipalities in 5 CCAA** — Cataluña 271, Euskadi 18, Navarra 21,
  Galicia 2 (A Coruña, Santiago), Asturias 5 (first use: Llanes, Cabrales, parts of Gijón,
  Avilés, Gozón) — after the BOE resolution of 29 Jul 2026 (BOE-A-2026-16532, verified), plus
  three Basque additions on 27 Apr (BOE-A-2026-9175). MIVAU puts the covered population at
  ≈9.3M (unverified), i.e. 19% of Spain, or ≈0.42 of the model's tensioned zone. Madrid,
  Andalucía, Valencia, Murcia and Castilla y León still refuse (0 municipalities).
- **Cataluña is renewing and expanding**: 118 of the 140 (Mar 2024) municipalities to be
  extended beyond Mar 2027, **22 dropped** (Lleida, Reus, Granollers, Mollet) and 53 added
  (procedures opened 21 Jul 2026, BOE pending — gencat verified). The exit of 22 municipalities
  after their price fall is a dynamic the model does not have (zones are declared once).
  Enforcement: 529 sanction files by Apr 2026 (title verified, page 403).
- **Competence is settled**: STC 53/2026 (8 Jul; BOE 3 Aug, verified) dismissed the Govern's
  challenge to Ley 12/2023. The binding veto point on *national* rent measures is now Congress:
  RDL 8/2026 (2% cap to 2027 + two-year extension) was struck on 28 Apr 2026 (BOE-A-2026-6545,
  verified), and the 69-page omnibus decree (seasonal ≤12 months with cause, room rents under
  the whole-flat cap, extraordinary extension to Jun 2028 for ≈630k contracts/yr, SOCIMI
  15 → 25%, Ley del Suelo reform) was pulled from the 28 Jul Consejo de Ministros and is
  "ready" for September (press, unverified). The TC also admitted the PP's challenge to the
  Catalan seasonal cap (Ley 11/2025) without suspension (BOE-A-2026-13028).
- **Cataluña Ley 11/2026** (in force 14 Jul 2026, via law-firm summary, DOGC not fetched):
  gran tenedor = ≥5 dwellings in Cataluña including natural persons, usage rights and
  co-ownership counted; "rent" includes all charges; room rentals under the cap; **TPO 20% on
  whole-building acquisitions by any buyer** (exempt ≤4 dwellings for family use).

**Credit and demand-side.**
- ICO first-home line: formalisation to **31 Dec 2027**, new **€150k net-wealth cap**, ≤35,
  ≤7.5×IPREM; uptake 8,549 operations / €206.6M guarantees / €1.09bn financed to 31 Oct 2025
  (BOE-A-2026-14404, verified) — ≈10% of the €2.5bn envelope. The ICO facility for social
  housing promotion was cut **€2bn → €375M** (BOE-A-2026-18677, verified).
- Banco de España: CCyB 1% binding from 1 Oct 2026; borrower-based limits remain "under
  study" with a framework monograph promised (IEF primavera 2026, verified). No ESRB warning
  on Spain (verified). The lending survey for 2026Q2 reports tighter housing standards and
  falling demand (BdE, verified). PP pledge of 4% ITP for first homes under 40 in its regions
  (announced 23 Jul 2026, unverified, no enactment found).

**Supply-side.**
- **Casa 47** portal live on 7 Sep 2026: 800 homes, +1,500 announced, 2,800 licensed in
  2026Q1, 42,000 Sareb homes and 2,500 plots to mobilise, rent ≤30% of income, 14-year
  contracts (La Moncloa, verified). VPO calificaciones definitivas 5,215 in 2026Q1 (+74.5%,
  best Q1 since 2012; La Moncloa, verified). Madrid Ley 2/2026: +20% buildability, +30%
  density on VPO plots, tertiary → VPO up to 30% (BOE, verified). Canarias Ley 7/2026:
  "vivienda asequible incentivada" at ≤120% of the VPO module and a presumption that stays
  ≤31 days or on tourist channels are tourist use (BOC, verified for the law).
- CNMC study E/CNMC/001/25 (29 Jun 2026, verified): land up to 45% of the final price, "one
  of the most restrictive land-use regimes in the OECD". SEPE/CNC (Sep 2026): 80% of
  construction vacancies hard to fill, 18.6% unfilled, 22% of the workforce retiring within a
  decade.

**Tourist rentals.** INE May 2026: **341,001** dwellings (−10.7% y/y; reference months are
now May/Nov, published Jun/Dec). Málaga suspended new VUT/hotel licences on residential land for
three years from 25 Jul 2026 (unverified); Barcelona's Nov 2028 extinction survived a repeal
vote (unverified); EU Regulation 2024/1028 applies since 20 May 2026 with Spain on regional
codes after the Supreme Court annulled the Registro Único.

**EU.** European Affordable Housing Plan (16 Dec 2025), SGEI Decision (EU) 2025/2630 in force
8 Jan 2026 with separate social and affordable categories, Housing Alliance 12 May 2026, EIB
€6bn for 2026 (EC pages verified).

## 4. Statistics — the releases the register lacked

| Series | Latest | Value | Effect on the model |
|---|---|---|---|
| INE IPV | 2026Q2 (7 Sep 2026) | **+12.2% y/y** (Q1 +12.9%), +3.4% q/q; new +7.4%, used +12.9% | benchmark period text; H1 average 12.55% — see §6 |
| Registradores ERI | 2026Q2 (7 Aug) | €2,487/m² record; sales 167,934 (−2.3% y/y); **foreigners 15.98%, record**; 77% financed; Jul advance −7.7% y/y | foreign-share range 16.0–18.4; cash row |
| Notariado CIEN | Jun 2026 (27 Aug) | €2,114/m² (+8.8%); H1 sales 353,237 (−7.7%); **46.3% unmortgaged**; LTV 72.3% | cash row band |
| Registradores ERI | 4T 2025 (Feb 2026) | 12-month cash share **29.3%**, Q4 25.7%; Madrid 99.5% financed | cash row central value |
| INE Hipotecas | Jun 2026 (26 Aug) | 45,907 (+10.8%); avg €178,365; **2.96%**; fixed 61.7%; term 25 | bank dossier; config comments |
| Euríbor 12m (BOE) | Aug 2026 (2 Sep) | **2.954%** (Jul 2.855, Jun 2.795; ≈3.07% in Sep) | `euribor` comment; forecast panel stale |
| ECB | 23 Jul 2026 | DFR 2.25% held; next meeting 10 Sep | — |
| INE ECP | 1 Jul 2026 (6 Aug) | 19,874,860 households; +226,279 in 2025 | `n_households` anchor; formation band |
| INE ECV 2025 | 5 Feb 2026 | owners **73.3%**, renting 20.2%, ceded 6.5% (series low) | tenure sources; benchmark row |
| INE ECV module | 27 Apr 2026 | 44.3% of 26–34 live with parents (47.3% for affordability); unsuccessful search: Spain-born 6.3%, non-EU-born 13.7% | age/nationality gap (§10) |
| Eurostat ilc_lvho07c | 2025 | market-tenant overburden **26.8%** (28.1; 30.6) | §9 target 5 lower edge |
| INE VUT | May 2026 (24 Jun) | **341,001** (−10.7% y/y), 1.28% of stock | `seasonal_share` |
| MIVAU VPO | 2026Q1 (11 Jun) | 5,215 definitivas (+74.5%), 4,048 provisionales | public-housing help text |
| SERPAVI | 2026 edition | published Mar 2026, revised Jul 2026 (contents not extracted) | data-landscape: the 2-year lag assumption was wrong |
| idealista | Aug 2026 | sale €2,924/m² +12.5% y/y, **first m/m fall since 2022**; rent €15.1/m² +5.8% y/y | rent-growth row |
| Tinsa IMIE | Aug 2026 | +14.9% y/y, 0.0% m/m | forecast panel anchors |

Not yet available on 8 Sep: INE ETDP and Hipotecas for July, Eurostat HPI 2026Q2 (1 Oct),
MIVAU transacciones 2T (calendar 403), Notariado H1 foreign report, OECD Q2, INE migration 2025.

## 5. Studies — what the model's known gaps gained

- **Rent-cap supply response (gap g).** Monràs & García-Montalvo, CEPR DP20018 (Feb 2025,
  verified PDF): −5% rents, −10% units, **IV elasticity of new contracts to rent ≈2.0 (1.6–3.2),
  OLS 0.07** — the model's 0–2 range is exactly the OLS-to-IV span of one paper. Izquierdo
  Llanes et al. (IJHMA, Jun 2026): DiD vs Madrid/Valencia/Andalucía, "economically substantial"
  supply contraction, magnitudes paywalled. O-HB report no. 4 (May 2026): Barcelona new-contract
  rent −2.7% real vs Q1 2024, 13.6% avoided against the counterfactual, **+1,374 contracts**,
  seasonal contracts **−53% y/y** in Q4 2025 after the seasonal cap. Incasòl Q4 2025: seasonal
  −1,233 (first fall); **tensioned rents +1.6% vs non-tensioned +9.4%** — a spillover signature
  the model does not reproduce. Portals: Barcelona long-term listings −56%, seasonal share 64%
  (idealista, Mar 2026); Catalonia listings −72% vs Madrid −38% (Brainsre, Aug 2026).
- **Location premium (gap a).** De la Roca & Puga (REStud 2017): Madrid earnings +46% vs the
  median city, +55% vs rural; elasticity of earnings to city size 0.0455, half static, half
  accruing with experience. Tinsa 2026Q1: Madrid capital €4,600/m² vs Palencia €1,256; Madrid
  province €3,565 vs Ciudad Real €776. The amenity term in `validation.md` now has both a wage
  and a price gradient to calibrate to. Not implemented: a price-formation mechanism must be
  specified before it is coded.
- **Cash purchases (gap c).** Two like-for-like registral sources disagree — Registradores
  23–29% vs Notariado 46% — and the 60.8% INE derivation is an artefact. Parental money
  gifts 62,000/yr, €5.5bn, avg €90k, tripled since 2019 (BdE via El Independiente); notarial
  donations 225k in 2025; 26% of renters excluded by the LTV cap alone (OBS, Aug 2026).
- **Age and nationality (gap d).** EFF 2024 (DO 2610): ownership <35 36.7% (+4.8pp, first rise
  since 2011), 35–44 56.5%, 45–54 70.1%, 55–64 76.9%, 65–74 82.8%, >74 83.4%; bottom quintile
  53.1%, top decile 88.3%; 45.3% of households own other real estate. ECV 2025 module figures
  above.
- **Landlord taxation (gap e).** AIReF Spending Review 2020: the 60% IRPF reduction cost
  €1,039M for 1.6M taxpayers and AIReF *could not separate formalisation from new supply* —
  a nuance the Funcas note's "judged effective" did not carry. Min. Derechos Sociales/CSIC
  (Apr 2026): private rental units 1.90M → 2.57M (2016–23), **52.8% of individually owned
  rentals held by multi-landlords (≥2)**. No AIReF evaluation of the 2023 tiers exists.
- **Second homes and foreign demand (gap f).** CaixaBank Research (Oct 2025): non-residents
  7.9% of sales paying **€3,063/m² vs €1,713 for Spaniards (×1.8)** — the `foreign_budget_multiplier`
  range 1.6–1.8 is confirmed from a third population. Tinsa Costa 2026: second-home segment
  €3,150/m², coastal effort 40% of income (Baleares 59%).
- **Rents vs incomes (gap b).** CCOO on IPVA 2015–24: new contracts +37%, existing +21%,
  wages +26%, CPI +11%; renter households 15.6% → 20.2%. Núñez (BdE, 1 Sep 2026): renters'
  average burden >25% of net income, one third >30%.
- **2008 crunch anchors (gap h).** García-Montalvo (Funcas, Feb 2026): LTV avg 65% with
  10.9% >80% vs mostly >100% in 2007; LTI 4.5, LSTI 22.6%; household housing credit 30.8% of
  GDP vs 62% in 2007; developer credit 5.8% vs 41.6%. EC Country Report 2026: overvaluation
  ≈18% (EC method), price-to-income flat since 2022. ECB FSR May 2026: Spain's price/income
  deviation positive and rising.

## 6. Forecast panel — no new paths, and the realised data outran the old ones

No institution published a new Spanish house-price path between 25 Jul and 8 Sep 2026
(CaixaBank 2S sectorial due late Oct; Bankinter 4T, Funcas September panel, OECD interim and
ECB projections all still pending on the cut-off date). CaixaBank's Informe Mensual (7 Sep)
keeps +10.1/+5.5 and carries Euríbor end-2026 2.47 / end-2027 2.26 — already below the
realised 2.954% August average. Fotocasa's predictive index has asking rents falling in 32
capitals in Q3 2026 (Madrid −3.1%, Barcelona −6.4% q/q).

Realised: INE IPV averaged **+12.55% y/y over H1 2026**, so every IPV-basis forecast in the
7–9% band needs a second half at +3.5…+5.7% to hold, implausible after +3.4% q/q in Q2; only
BBVA's +12.0% (valor tasado) is close, and appraisal indices (Tinsa +14.9%, Registradores IPVVR
+16.7%) run above it. Volumes point the other way — notarial H1 −7.7%, Registradores July −7.7% —
which puts BBVA's −7.3% transactions on track. Full tables in `external-forecasts.md` §8.

## 7. What re-measurement found — the flagship experiment no longer reproduced

Re-running the Phase-7 design (`experiments/rent-cap.md`: cap at tick 20 of 40, tensioned
zone, seeds 1–3, 16 post-cap ticks) on the pre-refresh code gave **contract rents +0.9%
above baseline** at every elasticity and new tenancies **+2 to +3%**, against the documented
−4.1% and −9.4% (at elasticity 2). The table dates from before the 2026-08-10 audit and the
2026-08-14 Funcas revision, and was never re-run. Two causes, one fixed and one open:

1. **Reference-index indexation above the income anchor (fixed).** While a cap is active the
   reference index is frozen and indexed by `within_contract_update` = 2.5%/yr, but the market's
   nominal anchor is 2%/yr. The reference therefore overtook market rents within ~10 ticks
   (capped tensioned listings 29 → 0 by tick 30), after which the magnet rule pulled sub-cap
   asks *up*. In Spain IRAV runs at 0.6–0.75 of wage growth, so the model value is 0.012–0.015.
   At 0.015 the cap binds throughout and contract rents fall ≈2.2% — the price leg works.
2. **The tensioned rental market is slack (open).** Applicants per listing sit at 0.6–0.8
   before the cap and 1.1–1.5 after it, against ≈65 contacts per listing in Barcelona. With
   60–80 leftover listings per tick, landlord withdrawals (≈60 units over 16 ticks at elasticity
   2, half of them sold) shrink the slack but not the number of contracts signed. The tenancy
   leg of §9.8 fails and is now a strict xfail. The fix is a tightness recalibration of the
   tensioned zone — the mobilisable vacant stock ((upH − 1) × (1 − withheld), held at 0.0455
   per household in every zone by the Funcas revision) or the zone split of formation — which
   moves ownership, market vacancy and overburden together and needs its own measured
   revision. It is the first calibration task after this refresh.

Also measured (validation.md carries the table): the buyer-type ITP wedge at +0.90 on
non-residents cuts their purchases ≈45%, at +0.10 on the large investor cuts its purchases
≈15%; the ICO wealth cap is inert on the tenant wealth distribution (≈1% of tenants above
€150k); the baseline validation moments moved only within seed noise.

## 8. Gaps this refresh opens or sharpens (documented, not fixed)

1. **Spillover to non-declared municipalities** — Catalan tensioned rents +1.6% vs
   non-tensioned +9.4% in 2025. The model's zones are not adjacent markets; migration is
   downward-only and rent-triggered, so displaced demand cannot bid up a neighbouring zone.
2. **Declaration exit** — 22 Catalan municipalities are being dropped after the price fall; the
   model declares a zone once. An endogenous declare/undeclare rule on the 30%-burden criterion
   would close it.
3. **Contract extension as a distinct shock** — the stalled decree's extraordinary extension
   (≈630k contracts/yr to Jun 2028) is not a price cap; the model has no landlord-initiated
   rotation to suppress.
4. **Two-stage seasonal substitution** — the Catalan seasonal cap reversed seasonal contracts
   (−1,233; −53%); `seasonal_segment_capped` exists but the return flow to habitual rental is
   not modelled.
5. **Composition premium of non-residents** — the +60% premium is willingness-to-pay on the
   same stock; in Spain it is largely different stock (coastal, premium). A non-resident tax
   therefore diverts less in the model than it would in Spain.
6. **Multi-landlord structure** — 52.8% of individually owned rentals belong to ≥2-unit
   landlords; the model's small landlords hold ≈1.2 units on average, so the ≥5 Catalan
   gran-tenedor threshold reaches almost nobody in the model.
7. **Location premium** — evidence now sufficient to specify the amenity term (§5); the
   mechanism decision is still pending and blocks every cross-zone claim.

## 9. Sources not verified (kept as pointers only)

Omnibus decree contents (que.es, eldiario.es); MIVAU's 9.3M covered population; Catalonia Ley
11/2026 read via exnovo.law (DOGC not fetched); Málaga moratorium (sector blog); Barcelona
repeal vote (sector blog); Valencia VPO module €2,568/m² (eldiario.es); €90M CCAA transfer
(EFE); PP 4% ITP pledge (moncloa.com); IBI surcharge ordinances 2026 (guiafiscal); ICO uptake
10,453 operations (press; the BOE-verified figure is 8,549 to Oct 2025); MITMS visados H1 2026
(observatorio); Fitch mid-year value; IPVA 2024 (+3.5%); CyTET migration-rent estimate.
