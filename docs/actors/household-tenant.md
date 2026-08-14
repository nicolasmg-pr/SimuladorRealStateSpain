# Household — tenant

Status: **researched** — web-sourced 2026-08-07. Source register: scratch `sources/household-tenant.md`
(to be merged into `docs/sources.md`). All Eurostat series verified directly against the Eurostat
dissemination API on 2026-08-07; other figures carry their source and a confidence label.

## 1. Role & size in the market

Tenants are the demand side of the rental market and the main claimants of housing policy.
Spain remains an ownership society, but the tenant share is rising steadily and is strongly
concentrated in exactly the zones the model calls "tensioned metro".

- **Share of population in rented housing (Eurostat EU-SILC, ilc_lvho02, verified via API):**
  21.8% (2015) → 23.8% (2019) → 26.3% (2024) → **26.4% (2025)**. Split 2025: 17.4% at market
  rent + 9.0% at reduced price or free. Owners: 73.6% (28.1% with mortgage, 45.5% outright).
- **Share of households (INE ECV 2024, household basis):** 20.4% renting (17.0% at market price +
  3.4% below market), 6.1% in ceded dwellings, 73.6% owning — lowest owner share of the series
  (since 2004). The two statistics reconcile: Eurostat is population-weighted and counts most
  cesión under "reduced/free". (ECV figures read via secondary reporting of the INE release;
  INE tables 9997/4583 are the primary tables.)
- **Zone dispersion (ECV 2024):** renting share ~30% Baleares, 27.9% Cataluña, 27.1% Madrid,
  27.0% Canarias vs. well below 20% in most inland/rural regions. Maps directly onto the
  3-zone design: tensioned metro ≈ 27–30%, secondary ≈ 20%, rural ≈ 12–17% (last figure inferred
  from the national average identity, not a published cell — treat as approximate).
- **Who rents (BdE Documento Ocasional 2432, 2024):** growth since 2015 concentrated among the
  young and the foreign-born population, in urban and tourist areas. Rental demand grew faster
  than supply throughout.
- **Social/protected rental is marginal:** public social rental stock ≈ **318,000 dwellings**
  (~197k regional + ~121k municipal; MIVAU Boletín especial Vivienda Social 2024). As a share of
  the total stock, estimates range **1.5–1.7%** (strict public social rental; MIVAU/Observatorio,
  press summaries) up to **3.3–3.4%** (government's broader "protected" definition, 2025 claims).
  EU peers commonly cite ~8–9%. Both figures should exist in the model as one parameter with a
  definitional range, not two numbers.
- **Flow of new tenancies:** MIVAU/SERPAVI is built on annual data from **>2.5 million rental
  contracts** (IRPF + regional deposit registries); official registries report annual growth of
  ~3.5–5% in registered habitual-rent contracts (MIVAU press notes 2025–2026).

## 2. Balance sheet & constraints

The tenant–owner wealth gap is the single largest balance-sheet fact in the Spanish housing market.

- **Wealth:** EFF 2022 (Banco de España): median net wealth of renter households ≈ **€2,200**
  vs. ≈ **€193,900** for owner households — a factor of ~90. Renters are overrepresented in the
  bottom income quintiles; median income in the three lower quintiles barely grew 2019–2021.
- **Rent effort:** BdE Informe Anual (2025, on 2024 data): tenant households spend on average
  **26.7% of net income** on rent; above 30% in five of the six largest cities. The BdE
  overburden indicator reached **32.5% of non-owner households**, exceeding 40% in Sevilla
  (46.8%), Málaga (46.7%), Barcelona (43.5%) and Madrid (41.3%).
- **Eurostat overburden (>40% of disposable income on total housing costs), tenants at market
  rent, Spain (ilc_lvho07c, verified):** 37.4 (2019) → 35.9 (2020) → **40.9 (2021, peak)** →
  39.4 (2022) → 30.6 (2023) → 28.1 (2024) → **26.8 (2025)**; EU-27: 20.3/19.2/18.6 (2023–25).
  Spain is persistently ~8–20 pp above the EU. The sharp 2022→2023 drop coincides with strong
  nominal income growth and in-contract update caps; treat the level as regime-dependent.
  Tenants at reduced/free rent: 8–11% overburdened; owners with mortgage: only 2–4%.
- **Viewpoint check:** the tenant union's claim that record rents take "half a salary or more"
  matches the data for *new* contracts signed by low-income/young households (BdE: young
  households' mean effort 36.5%, near 50% in Madrid, Málaga, Barcelona, València), not the
  average sitting tenant (26.7%). The landlord association ASVAL uses the same asymmetry from
  the other side: it cites vulnerable families at 50% effort to argue for demand subsidies
  (>€700M/yr) targeting a 30% ratio. Both are selective readings of a wide distribution — the
  ABM should carry the distribution, not either summary.
- **Youth constraint (CJE Observatorio de Emancipación):** renting alone costs **92–99% of the
  average young (16–29) net salary** (2024–2025: avg rent €1,080→€1,176/month vs. ~€1,191 net
  salary); a shared room ≈ **33.6%**. Emancipation rate 16–29 fell to **14.5–15.2%** (2024–2025),
  the lowest on record.
- **Buying constraint:** average age of first home purchase now **~38–41 years** (vs. 31–33 in
  the early 2000s); estimates of the time needed to save a 20% deposit range from **3.6 years**
  (one study, vs. 2.6 in 1993) to **6–9 years** (youth-focused estimates) — keep as a range.
  Only ~7% of Gen Z pay a mortgage (vs. 37% millennials). The ICO 100%-LTV guarantee (May 2024,
  under-35s) is the main policy lever on this margin.

## 3. Observed decision rules (with evidence)

1. **Stay put when protected; the market splits into insiders and outsiders.** In-contract rent
   updates are capped (2% 2022–23, 3% 2024, IRAV ≈2.2–2.4% since 2025) while asking rents rose
   11.5% (2024) and 8.5% (2025) (idealista). Sitting tenants therefore face a large penalty for
   moving, which mechanically lowers mobility and pushes all adjustment onto new contracts.
   Evidence: BdE do2432 ("entry prices decoupled from the existing stock"); idealista price
   series; IRAV/INE. Rule: moving probability falls as (market rent − own rent) grows.
2. **Accept effort up to ~30–40% of income; above that, adjust household size instead of exiting
   the zone.** Landlord solvency screening conventionally requires rent ≤ 30–40% of income;
   observed new-tenant effort for the young clusters at 36–50%. The margin of adjustment is
   sharing (rooms at ~34% of a young salary) and overcrowding, which is rising among tenants
   (press reporting on ECV/Eurostat overcrowding). Confidence: medium — the 30–40% screening
   threshold is an industry norm, not a statistical estimate.
3. **Queue for social housing but do not expect it.** With social rental at 1.5–3.4% of stock,
   registries (e.g. Barcelona's Registre de Sol·licitants, running since 2009) hold waiting
   lists orders of magnitude above annual allocations (registry publishes applicant counts;
   national aggregate not published — see §7). Behaviourally: registration is near-costless,
   allocation probability ≈ 0, so social housing barely alters market behaviour today.
4. **Tenure switch (rent→own) is savings-gated, not preference-gated.** Surveys and the EFF
   consistently show ownership preference; the binding constraint is the ~20% deposit plus taxes
   against a median tenant net wealth of ~€2,200. Rule for the ABM: transition hazard ≈ 0 unless
   (a) family transfer, (b) dual-income consolidation, or (c) policy guarantee (ICO aval);
   first-purchase age ~38–41 anchors the hazard's age profile.
5. **Organised non-payment/negotiation is real but marginal.** Tenant unions (Sindicat de
   Llogateres, founded 2017) run collective bargaining and, since 2025, rent strikes against
   large corporate landlords (Néstar-Azora, InmoCriteria blocks; partial 30% withholding).
   Affects large-landlord segments in tensioned metros only; no national quantification.

## 4. Reaction to past shocks (case episodes)

- **COVID-19 (2020–21).** Policy: eviction moratorium for vulnerable tenants, automatic 6-month
  contract extensions, state-guaranteed 0% microcredits (up to 6 months' rent, 6+4-year
  repayment), direct aid up to €900/month; landlords with >10 dwellings obliged to offer
  moratorium/partial condonation. Landlord-side claim: arrears tripled from **5% to 15%**
  (ASVAL, pandemic peak) — a landlord-association figure not confirmed by independent registry
  data; treat as an upper bound. Eurostat overburden actually *fell* slightly in 2020 (35.9)
  before peaking in 2021 (40.9) as incomes lagged the rebound.
- **Rent surge 2021–2025.** Asking rents: +11.5% (2024, record level), +8.5% (2025) nationally
  (idealista); CJE reports average rent €1,080 (mid-2024) → €1,176 (end-2025). Registered
  contract rents (SERPAVI, IRPF-based) grew far more slowly — the asking/contract wedge is a
  first-order modelling fact. Tenant response: record co-habitation (emancipation at 14.5%),
  room-sharing, and rising overcrowding rather than mass exit from tensioned zones.
- **Catalonia rent cap, 1st generation (Sep 2020 – Mar 2022, struck down).** Academic evaluations
  disagree on magnitude but agree on direction: aggregate rents fell ~**4–6%**, concentrated in
  expensive units, with some cheap units rising *toward* the reference ceiling; García-Montalvo/
  Monràs/Raya find supply exit at the top not offset at the bottom; other work (BSE/TSE
  "high-coverage rent control" papers) finds effectiveness with smaller short-run supply loss.
  Record both; never a point value.
- **Catalonia/Barcelona cap under the 2023 Housing Law (from Mar 2024).** Year one, contested:
  government (MIVAU/Generalitat): prices **−3.7%** in tensioned municipalities, **−6.4%** in
  Barcelona; ~1,000 new contracts/month; supply +17,000 (Cataluña). Sector: Fotocasa survey — 6%
  of Catalan owners withdrew long-term rentals; ~1/3 shifting to unregulated categories;
  idealista — Barcelona permanent-rental listings **−26%** YoY (end-2024), seasonal **+31%**.
  Incasòl contract data do not fully match government claims in the 15 largest municipalities.
- **Seasonal-rental (alquiler de temporada) displacement — the evasion channel.** Idealista
  listing data: seasonal share of rental listings 13% (Q2-2024, supply +55% YoY) → 14% (Q1-2025,
  +25%) → **29% (Q4-2025, +36%; permanent +1%)**; in capped/tensioned cities permanent listings
  fell −6% to −26% (Pamplona −26%, A Coruña −21%, Lleida −20%, Barcelona −15%, Q4-2025).
  Registry counterpart: Generalitat/Incasòl counted **+4,187 seasonal contracts in 2024 (+45%)**.
  Tenant unions call it "generalised fraud" (+51%/yr claim) and won regulation: Catalan law
  extending caps to seasonal/room rentals (approved 2025, in force 2026). Portal (industry) and
  union (tenant) sources here *agree on direction and rough magnitude* — unusually strong
  triangulation for an evasion channel.

## 5. Power & relations to other actors

- **vs. landlords (small):** most tenants rent from individual landlords; relation is bilateral,
  low-conflict, governed by LAU minimums (5 yr + 3 tacit). Tenant power = statutory tenure
  security inside the contract; landlord power = full repricing at rollover and screening at entry.
- **vs. landlords (large/institutional):** target of union collective action (strikes 2025) and
  of stricter obligations (>10-dwelling rules since COVID; legal-person contracts 7 yr).
- **vs. government:** tenants are numerous but historically under-organised; policy since 2023
  (Housing Law, IRAV, tensioned-zone caps, seasonal-rental laws) marks a shift toward tenant-
  protective regulation, with regional divergence (Cataluña applies caps; Madrid does not).
- **vs. banks:** almost no direct relation — the deposit wall keeps most tenants out of the
  mortgage market; ICO guarantees are the bridge.
- **vs. developers/investors:** compete indirectly — seasonal/tourist conversion removes stock
  from the tenant market in tensioned zones.
- **Intermediation frictions:** agency fees now legally on the landlord (2023 law); deposits
  (1 month + up to 2 extra guarantees) are the entry cost that binds for low-wealth tenants.

## 6. Extracted parameters

| Parameter | Value / range | Unit | Source(s) | Confidence |
|---|---|---|---|---|
| Tenant share of population (total rent) | 26.4 (2025); 21.8 (2015); trend ≈ +0.4–0.5/yr | % of population | Eurostat ilc_lvho02 (API-verified) | high |
| — split: market rent / reduced-free | 17.4 / 9.0 (2025) | % of population | Eurostat ilc_lvho02 | high |
| Tenant share of households | 20.4 renting (17.0 market + 3.4 below-market) + 6.1 ceded | % of households | INE ECV 2024 (via press of INE release; INE t.9997) | high |
| Tenant share by zone type | tensioned metro 27–30; secondary ≈ 20; rural 12–17 (inferred) | % of households | INE ECV 2024 regional; rural cell inferred | medium |
| Overburden (>40% disposable income), market-rent tenants | 26.8–28.1 (2024–25); range 2019–25: 26.8–40.9; EU-27 ≈ 19 | % of market tenants | Eurostat ilc_lvho07c (API-verified) | high |
| Overburden, BdE definition (non-owner households) | 32.5 national; 41–47 in Madrid/Barcelona/Málaga/Sevilla | % of non-owner households | BdE Informe Anual 2025 (2024 data) | high |
| Mean rent effort, sitting tenants | 26.7 national; >30 in 5 of 6 big cities | % of net income | BdE Informe Anual 2025 | high |
| Mean rent effort, young households (new entrants) | 36.5 national; ~50 in Madrid/Málaga/Barcelona/València | % of net income | BdE Informe Anual 2025; CJE (92–99% for solo renting) | high |
| Max rent-to-income accepted (entry screening / acceptance threshold) | 30–40 | % of net income | industry screening norm + observed entry-effort distribution | medium (partly convention) |
| Share of income, room-share fallback | ≈ 34 | % of young net salary | CJE Observatorio 2025 | medium |
| Median net wealth, tenant vs owner households | ≈ 2,200 vs ≈ 193,900 | € (2022) | BdE EFF 2022 | high |
| Legal tenancy duration | 5 (individual) / 7 (legal person) + 3 tacit extension; notice 2 mo (tenant) / 4 mo (landlord) | years | LAU art. 9–10 (RDL 7/2019) | high |
| Typical realised tenancy duration | 3–5 (derived from rollover behaviour, pre-2019 contract data) | years | derived; no single official series | low |
| Tenant moving probability | 0.15–0.30 /yr ≈ 0.04–0.08 /quarter (falls with sitting-tenant discount) | probability | derived from duration + EU mobility literature (CED, BdE do2433) | low |
| Owner moving probability (for contrast) | 0.04–0.05 /yr | probability | EU panel studies via CED/BdE | medium |
| New registered tenancies, flow growth | +3.5–5 /yr; base >2.5M contracts in SERPAVI data | %/yr; contracts | MIVAU/SERPAVI press notes 2025–26 | medium |
| In-contract rent-update cap | 2 (2022–23); 3 (2024); IRAV ≈ 2.2–2.4 (2025–26) | %/yr | INE IRAV; Housing Law 12/2023 | high |
| Asking-rent growth (new-contract price signal) | +11.5 (2024); +8.5 (2025) | %/yr | idealista price index (listing basis) | high (for listings) |
| Social rental stock share | 1.5–1.7 (strict public) to 3.3–3.4 (broad protected); ≈ 318k public units | % of dwelling stock; units | MIVAU Boletín Vivienda Social 2024; govt claims 2025 | medium (definition-dependent) |
| Social-housing allocation probability for a registered applicant | ≈ 0 (waiting lists ≫ annual allocations; no national count) | probability/yr | Barcelona Registre de Sol·licitants (counts unpublished nationally) | guess |
| Seasonal-rental share of rental listings (evasion channel) | 13 (Q2-24) → 29 (Q4-25); growth +25–55 /yr | % of listings; %/yr | idealista supply reports; Incasòl +45% contracts 2024 | medium |
| Rent-cap price response (tensioned zones, yr 1) | −3.7 to −6.4 (govt, 2024–25); −4 to −6 aggregate (academic, 2020–21 cap) | % | MIVAU/Generalitat; García-Montalvo–Monràs–Raya; BSE/TSE papers | medium |
| Rent-cap supply response (permanent listings, capped cities) | −6 to −26 /yr; seasonal listings +31 to +85 | %/yr | idealista Q4-2024/Q4-2025; Fotocasa owner survey (6% withdrew) | medium |
| Emancipation rate, 16–29 | 14.5–15.2 (2024–25), record low | % living outside parental home | CJE Observatorio de Emancipación | high |
| Rent→own transition anchors | first purchase age 38–41.8; deposit-saving time 3.6–9 yr; Gen Z w/ mortgage 7% | years; % | sector studies (IFEMA/Fotocasa/press); range kept | medium |
| COVID arrears spike | 5 → 15 (landlord-association claim, pandemic peak) | % of contracts in arrears | ASVAL (landlord viewpoint; not independently confirmed) | low |

### 6b. The acceptance threshold is not a constant (added 2026-08-14)

The `max_rent_burden ~ U(0.30, 0.40)` row above is a *screening* norm. What Spanish households
actually end up paying moved a long way inside a decade, and that movement is the evidence for
the sharing margin in `agents/household.search_burden` (model-spec §5).

| Series (EPF microdata, Funcas 104 ch.6) | 2015 | 2017 | 2019 | 2021 | 2022 |
|---|---|---|---|---|---|
| Mean rent effort, % of consumption basket | 26.5 | 26.0 | 27.0 | 31.7 | 29.7 |
| — under-35s | 24.0 | 24.5 | 26.6 | 29.7 | 30.4 |
| Renting households above 30% | 33.0 | 31.1 | 33.5 | 43.1 | 38.2 |
| Above 30% **including utilities** (Ley 12/2023 *sobreesfuerzo*) | 52.3 | 48.2 | 50.6 | 61.6 | 60.5 |
| Mean monthly rent paid, € | 404 | 428 | 476 | 505 | 516 |

Mean rent spend rose **+27.7%** over 2015–2022 against household income **+16.6%** (single
earner) to ≈22% (two or more). Vulnerable households (<€13,000 annual spend) reached 40.6% on
rent alone and **51.1% including utilities** — the observed ceiling the model uses. Four in ten
Spanish tenants exceed 40% of disposable income, ≈2× the EU average [Eurostat via ch.2], and
the absorption channels named are shared flats, sublet rooms and later emancipation [ch.4].

Two things this also pins:
- **The 2022 rent cap worked on the within-contract channel**: mean rent spend grew **+2.1% in
  2022** under the 2% cap, against **+11.2% in 2019**. That is the cleanest available
  before/after on `within_contract_update`.
- **Territorial spread of effort**: Ceuta/Melilla 35.0%, País Vasco 33.0%, Baleares 32.6%,
  Madrid 31.8%, Cataluña 31.7% at the top; Murcia 21.6%, Extremadura 20.2% at the bottom.
  Monthly spend Madrid €675 vs Extremadura €277. Rental incidence by municipality size:
  22.3% (>100k), 19.5% (50–100k), 15.2% (20–50k), 11.1% (<10k). By nationality of the main
  earner: Spanish 11.6%, rest of EU 45.3%, rest of world 66.3%.

## 7. Open questions

1. **Tenant mobility is the weakest parameter.** No official Spanish series for annual tenant
   moving probability or realised tenancy duration was found; the 0.15–0.30/yr range is derived.
   Candidate sources: ECV mobility module microdata; Incasòl deposit durations; EFF panel dimension.
2. **Share paying >30% (not >40%)** of income is not published as a headline by Eurostat/BdE.
   Needs computation from ECV or EFF microdata; interim guess for tensioned metros: 40–55%.
3. **Social-housing demand registries:** applicant counts exist per region/municipality (Barcelona
   registry publishes them) but no verified national aggregate was fetched. Task: pull Barcelona
   and Madrid registry counts and annual allocations to calibrate the ≈0 allocation probability.
4. **Asking vs. contract rent wedge:** quantify SERPAVI (IRPF) rent growth vs. idealista asking
   growth for the same years — the wedge is the key input for insider/outsider dynamics.
5. **Rural-zone tenant share** (12–17%) is inferred, not published at that granularity. Check INE
   ECV by degree of urbanisation (Eurostat ilc_lvho02 by deg_urb exists).
6. **ASVAL arrears figures** (5%→15% COVID) and union "50% of salary" claims both need a neutral
   registry check (judicial eviction statistics, INE arrears items in ECV) before use beyond bounds.
7. **Q4-2025 jump in seasonal listing share (14%→29% within 2025)** is suspiciously large; check
   whether idealista changed the measurement basis before using the endpoint.
8. Effect of the **Catalan seasonal/room-rental cap (in force 2026)**: first natural experiment on
   closing the evasion channel — no outcome data yet as of 2026-08.
