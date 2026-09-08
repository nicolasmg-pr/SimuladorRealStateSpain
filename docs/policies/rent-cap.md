# Rent cap

Rent caps / rent controls in Spain. Primary evidence: Catalonia 2020–22 (Ley 11/2020) and the
2024 wave under Ley 12/2023 (Ley por el Derecho a la Vivienda). International evidence
(Berlin, San Francisco, Paris) is secondary calibration context. All URLs fetched 2026-08-07.

## 1. Mechanism

**What changes mechanically.** In a declared *zona de mercado residencial tensionado*
(tensioned zone), the rent of a **new contract** is capped at the rent of the previous contract
for that unit (updated only by the permitted annual index). Two groups face a second, stricter
cap — the official **reference price index** (Sistema Estatal de Referencia del Precio del
Alquiler): (a) **grandes tenedores** (large holders; state default ≥10 dwellings, lowered to ≥5
in tensioned zones — the option Catalonia uses), and (b) units not rented in the previous
5 years. **Within-contract** annual updates are capped economy-wide (not only in tensioned
zones): 2% in 2023, 3% in 2024, and from 2025 the new **IRAV** index (INE), designed to sit at
or below CPI. Catalonia's 2020–22 predecessor (Ley 11/2020) was similar in core design — new
rent ≤ min(reference index, previous rent) — applied to municipalities >20,000 inhabitants with
a tight market (~60 municipalities), and was struck down by the Constitutional Court in
March 2022 (competence grounds), giving a clean policy-off event.

**Who holds the lever.** The cap instrument is **state law** (Ley 12/2023), but it only
activates where the **CCAA** requests/declares tensioned zones (3-year renewable declarations,
published by the Ministry). Catalonia declared 140 municipalities on 16 March 2024 and added
131 more on 10 October 2024 (271 total, ~90% of Catalan population). A handful of Basque,
Navarrese and Galician municipalities followed from 2025; Madrid and most CCAA refuse to
declare. So in the model the lever is **regional (CCAA-level) activation of a state
instrument**, applied by zone. Catalonia additionally extended the cap to **seasonal and room
rentals from January 2026** (regional law of Dec 2025) — before that, contracts of 1–12 months
("alquiler de temporada") were an uncapped escape segment.

## 2. Evidence for

### Catalonia 2020–22 (Ley 11/2020) — the three headline studies

**Monràs & García-Montalvo (2023 version; first circulated 2022).** *The Effect of
Second-Generation Rent Controls: New Evidence from Catalonia*, FRBSF WP 2023-28 / CEPR DP18485.
(Academic; Monràs at the SF Fed.) Data: universe of tenancy agreements from INCASÒL deposits +
Agència de l'Habitatge de Catalunya + Colegio de Registradores, ~2016–2022, >400 municipalities.
Identification: diff-in-diff allowing heterogeneous municipality trends, plus a novel
nonparametric comparison of "excess price" (price − official reference price) histograms; >50
months of clean pre-trends. Findings: rents **−5%** on average in treated municipalities;
strong **convergence toward the reference price** — units priced below reference *increased*
rents while units above it fell (a distributional effect the model should reproduce). Also
found a supply decline — see §3.

**Jofre-Monseny, Martínez-Mazza & Segú (2023).** *Effectiveness and supply effects of
high-coverage rent control policies*, Regional Science and Urban Economics. (Academic — IEB
Barcelona / UCL–Uppsala / CY Cergy.) Same INCASÒL+AHC microdata, 2016–2022, aggregated to
municipality-quarter. Identification: diff-in-diff + event study with a **restricted control
group** — 90 non-regulated municipalities that also had tight markets but were below the
20,000-inhabitant threshold, vs 58 treated (148 total); parallel pre-trends by construction;
extensive COVID controls (unemployment, furloughs, donut effects, migration). Findings: rents
**−4% to −5%**; **no effect** on tenancy agreements signed, ended agreements, stock of rented
units, or unit quality. Two clean quasi-experimental extras: an **anticipation spike** in
registrations in the two weeks before approval, and full **reversal of the price effect after
the March 2022 repeal** (price gap returned to pre-regulation levels). Tenant savings ≈ €358/yr
per new contract, ~190,000 contracts affected.

**Kholodilin, López, Rey Blanco & González Arbués (2022)** (DIW Berlin DP 2008; fourth study,
useful triangulation; academic + portal data). Idealista **posted** rents/listings,
diff-in-diff: asking rents **−6% to −7%**, **no significant effect on the number of
advertisements**.

So all three (four) studies agree the cap cut regulated rents by mid-single digits while in
force. The 2020–22 policy *worked as a price instrument*.

### 2024 wave (Ley 12/2023, Catalonia from 16 March 2024)

- **Generalitat / Incasòl deposit data (government viewpoint, pro-policy).** Over the first 18
  months (2024Q1–2025Q3), average new-contract rents rose **+0.8% in tensioned zones vs +5.7%
  in non-tensioned Catalan municipalities** (cumulative CPI +3.1%); Barcelona new-contract
  rents **−3.3% to −3.4%**. Pre-cap the market was rising ~7%/yr. Year-1 snapshots: Barcelona
  −6.4% from peak, first-140 municipalities −3.7% (March 2025 joint Ministry–Generalitat
  presentation); 2025Q1 y/y: −4.7% Catalonia, −8.9% Barcelona.
- **Sindicat de Llogateres two-year report (tenant union viewpoint).** Same public registers:
  +0.9% accumulated in 18 months vs **+14.9% in the comparable preceding period**; stresses
  that the **stock of active contracts grew** (+15,676 dwellings; 165,225 new contracts signed
  in 18 months) and reads fewer new signings as **lower tenant rotation** (longer contracts,
  fewer evictions-by-price), not lost supply. IDRA (Palomera) makes the same rotation argument.
- **INE rental index (statistical office).** Catalonia rents +3.1% in 2024 vs Spain +3.5% —
  mild containment on a market-wide (not just new-contract) basis.
- **Pérez García (arXiv 2602.08631, Feb 2026; single-author academic preprint)** finds a
  ~3 pp reduction in rental price growth in baseline DiD — though not robust (see §3).

## 3. Evidence against / side effects

### Catalonia 2020–22

**Monràs & García-Montalvo:** overall **supply of units in the rental market ≈ −10%** (new
contracts), driven by exit of above-reference-price units not compensated by entry below;
implied **elasticity of rental-unit supply (Δln new contracts / Δln rent) ≈ 2**. No change in
contract duration or time-between-contracts, supporting "units left the rental market" rather
than slower turnover. Directly contradicted by Jofre-Monseny et al. (no supply effect, same
microdata) — the divergence comes **entirely from the control-group / trend-adjustment
choice** (restricted tight-market control group vs all-municipalities with heterogeneous-trend
correction), per the IEB's own comparison (García-Montalvo, Monràs & Raya 2023, EsadeEcPol,
ruled out data aggregation and Barcelona-exclusion as explanations). This is the single
sharpest disagreement the model must span.

**Pérez García (2026), on the 2024 policy:** municipality-level DiD (140 treated vs 173
control municipalities of 680, missing-data limits), event studies, PSM-DiD, synthetic DiD, on
newly released Generalitat administrative data, sample through ~2025. Findings: **new tenancy
agreements fall by 5–7 contracts per 10,000 inhabitants (~−13%), robust across
specifications**; the **rent-growth effect (~−3 pp, ≈ −€246/yr on a €681/month base) loses
significance** under propensity-score matching and synthetic DiD. Author flags diverging
pre-trends and data limitations. Read: the *supply* effect is the robust one, the *price*
effect is not — the mirror image of Jofre-Monseny et al.

### 2024 wave — side effects (label viewpoints)

- **Seasonal-rental substitution (all sides confirm the direction, magnitudes differ).**
  Registered seasonal contracts (Incasòl): **+44.9% in 2024** (+4,187 contracts), **+52% y/y in
  2025Q1**; share of new contracts 6.1% → 11% in Catalonia (Generalitat); in Barcelona 1,449 →
  2,347 in Q1 (+62%), reaching **24–28.1% of new registrations by 2025Q3** (Sindicat de
  Llogateres, vs ~3% (IDRA) to 7.1% (Cambra de la Propietat) in 2023). Listings side —
  **idealista (portal viewpoint, anti-cap):** permanent-rental stock −13% in the first month;
  Barcelona long-duration listings −45% y/y by 2024Q2; by end-2025 **seasonal = ~64% of all
  Barcelona rental listings (34% in March 2024)**; Hospitalet −66% permanent listings.
  **O-HB (public observatory, neutral):** seasonal reached 54.1% of Barcelona listings in
  2024Q3 (11–32% pre-cap). Tenant union frames this as **evasion** (hence the Jan 2026
  extension of caps to seasonal/room rentals); landlords (Donpiso, COAPI, Cambra) frame it as
  flight from legal insecurity. Early post-closure data (2025Q4): seasonal contracts fell
  (−740 in Barcelona Oct–Dec) but did **not** return as ordinary contracts (+7 net) — Cambra
  claims sale, vacancy or family use instead.
- **New-contract volumes.** New signings in tensioned municipalities fell **−21% Q1→Q4 2024**
  (Incasòl, via press); Barcelona −17% over the three post-cap quarters of 2024; Catalonia
  ~34,500 (2024) → 26,962 (2025Q3), **−21.9%** (El Mundo on Incasòl); Idescat: 2025Q4
  accumulated −8.9% y/y. Contrast: net *active* contracts still grew (+8,697 in 2024), though
  the net balance is shrinking — Barcelona 2025Q3 recorded its first net loss (−244) since
  records began excl. COVID; Cambra de la Propietat (landlord viewpoint): 2021 net balance
  9,661 → +534 in 2025 (−94.5%), ratio ~100 entries per 99.9 exits.
- **Composition / quality drift (landlord & press analysis).** Barcelona average contract
  price fell while **price per m² rose +7% y/y to 2025Q3 (+0.6% since 2024Q1)**; average
  contracted surface fell 75 → 71–72 m². Falling average rents partly reflect smaller flats,
  not cheaper housing (Cambra de la Propietat via Ara/El Periódico). Asking prices on portals
  kept rising (+12% Catalonia, +14% Barcelona in 2024 — idealista/Fotocasa listings, which
  increasingly exclude the capped segment).
- **Search congestion.** idealista: ~65 families per Barcelona listing vs 34 national average
  (2026); ~54 vs ~40 pre-law (2025). Rent burden ~46% of income in Barcelona (idealista,
  2025Q4 — portal viewpoint).

### International (secondary)

**Berlin Mietendeckel (Feb 2020 – Apr 2021, struck down by the Federal Constitutional
Court).** A first-generation freeze + hard €/m² caps on ~95% of the stock. Hahn, Kholodilin,
Waltl & Fongoni (DIW DP 1999 / Management Science 2023; academic + central-institute):
advertised rents of regulated units **−7% to −11%** (hedonic DiD and spatial RDD at the city
border); **rental listings roughly halved (−50% to −57.5%)**; only ~25% of post-enactment ads
were rule-compliant; spillover: Potsdam asking rents **+12%**. IW Köln (industry-adjacent
institute): asking rents −10.3%, listings **−51.8%** — "supply decline five times the price
decline". ifo: supply down **up to 60%**, persisting after repeal; regulated-segment rents grew
11 pp/quarter less than comparable cities. Consistent story: big price effect, very large
listed-supply contraction, evasion via conversion to owner-occupancy and modernization.

**San Francisco (Diamond, McQuade & Qian 2019, AER 109(9); academic).** 1994 ballot-law
quasi-experiment on third-generation control (within-tenancy caps). Rent control reduced
covered tenants' mobility by **20%** and lowered displacement, but treated landlords cut
**rental housing supply by −15%** (condo conversion, sale to owner-occupants, redevelopment);
the lost supply "likely drove up market rents in the long run" (the paper's welfare analysis
puts the citywide rent increase at ~+5.1% — figure from the paper body, (unverified in this
fetch; abstract verified)). Canonical evidence that supply exit happens where conversion to an
uncontrolled use is easy.

**Paris (encadrement des loyers, from July 2019).** Morin, Regnaud, Breuillé & Le Gallo (2025,
Journal of Housing Economics; academic, with Apur — Paris city agency — and SeLoger portal
data; 559k ads 2018–2023, DiD vs 8 unregulated tight-market cities): rents **−3.7% to −4.2%**
on average, effect **growing over time** (−2.5% year 1 → −5.9% in 2022–23 → −8.2% in 2023–24;
cumulative −5.2% to mid-2024 per Apur update) and stronger for small flats (−10.2% for
8–18 m²); **no evidence of a decline in listings**. Compliance is the weak point: 36–48.6% of
ads exceed the legal ceiling depending on year; full compliance would roughly **double** the
price effect (−8.2% to −8.7%). OLAP (official rent observatory): 28% of 2019 move-ins above
cap; over-cap rents fell ~3%. Paris ≈ the Jofre-Monseny world: moderate price effect, no
measured supply effect, imperfect compliance.

## 4. Effect-size range

The spans the model must be able to reproduce (all relative to no-cap counterfactual, on
regulated new contracts, over ~1–2 years of a cap in a tensioned zone):

| Quantity | Range | Anchors |
|---|---|---|
| Rent level, regulated new contracts | **0% to −11%; central −4% to −7%** | JMS −4/−5; M&M −5; Kholodilin −6/−7; Paris −2.5 to −5.9; Berlin −7 to −11; Pérez García ~−3 pp growth *not robust* (⇒ 0 admissible) |
| Rent differential vs uncapped zones (2024 wave, descriptive) | −4 to −6 pp over 18 months | Incasòl: +0.8% tensioned vs +5.7% untensioned |
| New tenancies / rental supply | **0% to −15%; Catalonia span 0% to −13%** | JMS ≈ 0; Kholodilin ≈ 0 (ads); Paris ≈ 0 (ads); M&M −10%; Pérez García −13%; SF covered units −15%; Berlin listings −50/−60% (freeze, extreme design — upper bound, not Spanish-cap central case) |
| Implied landlord supply-response elasticity (Δln tenancies / Δln rent) | **0 to ~2** | 0 = JMS/Paris world; ~2 = M&M world; Pérez García: large quantity effect with weak price effect (elasticity >2 or demand-side confound) |
| Seasonal/uncapped-segment evasion, share of new contracts | **3–7% pre-cap → 11% (Catalonia) / 24–28% (Barcelona) after 6 quarters** | Incasòl registrations; Sindicat; Generalitat |
| Seasonal share of *listings* (portal, stock measure) | 34% → 54–64% Barcelona | idealista, O-HB |
| Compliance with cap | ~25% (Berlin) to ~52–64% of ads (Paris) — Catalonia registered contracts near-mechanical compliance (deposits) | DIW; Apur/Morin et al. |
| Reversal on repeal | full price reversion within ~2 quarters | JMS on March 2022 repeal |
| Anticipation | registration spike in weeks before enactment | JMS |
| Spillover to uncapped neighbours | up to +12% (Potsdam; extreme freeze case) | DIW |

Disputed estimates stay ranges: the rent effect and especially the supply effect must **never**
be resolved to a point. One exposed parameter (below) must span the Monràs / Jofre-Monseny /
Pérez García worlds.

→ see Update 2026-09-08 (KB refresh) at the end of this note.

## 5. Model mapping

Proposed `scenario.Intervention` parameters (typed dataclass fields; ranges are parameter
ranges per the bias-control rule, not point values):

- `rent_cap_enabled: bool` — activates the lever.
- `applies_to_zone: ZoneType` — tensioned metro only (the CCAA-declaration step: caps exist
  only in zones the scenario declares; default `TENSIONED_METRO`).
- `cap_reference_discount: float` — where the reference index sits relative to the zone's
  prevailing market rent for equivalent units. Range **0.00–0.10** (a cap ~0–10% below market
  reproduces the −4…−7% realized effects given partial bindingness).
- `cap_scope: Literal["gran_tenedor", "all_new_contracts"]` — Ley 12/2023 index cap binds
  gran tenedores (≥5 dwellings in-zone) and first-time-in-5-years units; the
  previous-rent cap binds everyone. Model both tiers or collapse to scope switch.
- `within_contract_update_rate: float` — annual in-contract update (IRAV/CPI cap), units:
  %/year. Range **0.02–0.03**, vs CPI for uncapped.
- `landlord_supply_response_elasticity: float` — Δln(units offered for standard rental) /
  Δln(regulated rent). **Range 0.0–2.0** — THE exposed disagreement parameter: 0 =
  Jofre-Monseny/Paris world, 2 = Monràs–Montalvo world, upper half ≈ Pérez García world.
  Exit routes in-model: sale to owner-occupiers, vacancy, seasonal segment.
- `seasonal_evasion_share: float` — share of would-be regulated new contracts diverted to an
  uncapped seasonal segment per tick while that segment is uncapped. **Range 0.05–0.25**
  (Catalonia: 11% Catalonia-wide, 24–28% Barcelona after ~6 quarters), ramping in over ~4–6
  quarters.
- `seasonal_segment_capped: bool` — the Jan 2026 closure; when flipped, diverted units do
  *not* automatically return (Cambra evidence: sale/vacancy instead) — route via
  `landlord_supply_response_elasticity`.
- `compliance_rate: float` — share of new regulated contracts actually at/below cap. Range
  **0.25–0.95** (Berlin ads 0.25; Paris 0.52–0.64; Catalan registered deposits high).
- `anticipation_ticks: int` (default 1) — contract-signing spike before enactment (JMS).
- `repeal_reversion: bool` (default True) — prices revert on removal (JMS, Catalonia 2022).

Validation targets for the baseline scenario replication: Catalonia 2020–22 (−4…−7% rents;
tenancies between 0 and −10%) and 2024-wave Incasòl trajectories (tensioned vs untensioned
rent-growth gap ≈ 5 pp; seasonal share path). A calibration that can only produce one of the
three Catalan studies' outcomes is wrong; the elasticity range must sweep across all three.

## Sources

Registered in `docs/sources.md` register format; full rows with fetch dates in the research
scratchpad source table (policy-rent-cap.md). Key primary URLs:

- Monràs & García-Montalvo, FRBSF WP 2023-28: https://www.frbsf.org/wp-content/uploads/wp2023-28.pdf (fetched 2026-08-07)
- Jofre-Monseny, Martínez-Mazza & Segú, RSUE 2023: https://www.sciencedirect.com/science/article/abs/pii/S0166046223000510 ; author summary IEB Info 44: https://ieb.ub.edu/wp-content/uploads/2023/03/INFO-IEB_44_ENG.pdf (fetched 2026-08-07)
- Pérez García 2026, arXiv:2602.08631: https://arxiv.org/abs/2602.08631 (fetched 2026-08-07). Note: task briefs sometimes cite this as "2025"; arXiv submission is 2026-02-09.
- Kholodilin et al. 2022, DIW DP 2008: https://ssrn.com/abstract=4159469 (cited via IEB Info 44; direct fetch not performed — (unverified beyond secondary citation))
- Sindicat de Llogateres 2-year report (2026-03-16): https://sindicatdellogateres.org/es/informe-sobre-los-efectos-de-la-regulacion-de-alquileres-dos-anos-desde-la-entrada-en-vigor/
- O-HB ZMRT monitoring report no. 2 (2025): https://www.ohb.cat/en/project/biannual-monitoring-report-of-the-residential-market-pressure-zone-zmrt-barcelona-no-2-april-2025/
- idealista studies: https://www.idealista.com/en/news/property-for-rent-in-spain/2024/04/26/816612 ; https://www.idealista.com/news/inmobiliario/vivienda/2024/07/16/818502
- Incasòl series via Idescat: https://www.idescat.cat/indicadors/?id=basics&lang=en&n=22279
- Press triangulation: El País 2026-03-16; Ara.cat 2025-03-14 / 2025-06-17 / 2025-06-18 / 2026-02-23; El Mundo 2026-03-16; elEconomista 2026-03-16; El Periódico 2026-04-21; SpanishPropertyInsight 2025-04-12/16 (all fetched 2026-08-07)
- Berlin: Hahn, Kholodilin, Waltl & Fongoni, DIW DP 1999 / Mgmt Science 2023: https://www.diw.de/documents/publikationen/73/diw_01.c.836357.de/dp1999.pdf ; DIW Wochenbericht 8/2021: https://www.diw.de/documents/publikationen/73/diw_01.c.811443.de/21-8-3.pdf ; IW-Trends 3/2021: https://www.iwkoeln.de/fileadmin/user_upload/Studien/IW-Trends/PDF/2021/IW-Trends-2021-03-03_Sagner-Voigtl%C3%A4nder.pdf ; ifo press 2022: https://www.ifo.de/en/press-release/2022-04-12/berlins-rent-cap-drastically-shrank-supply-rental-properties
- San Francisco: Diamond, McQuade & Qian 2019, AER: https://www.aeaweb.org/articles?id=10.1257/aer.20181289
- Paris: Morin, Regnaud, Breuillé & Le Gallo 2025, J. Housing Economics: https://ideas.repec.org/a/eee/jhouse/v70y2025ics1051137725000609.html ; Apur evaluations: https://www.apur.org/sites/default/files/2025-06/rapport-impact_encadrement_loyers_paris.pdf ; https://www.apur.org/fr/logement-hebergement/evolution-parc-logements/effets-encadrement-loyers-paris ; OLAP 2019 bilan: https://www.observatoire-des-loyers.fr/sites/default/files/olap_documents/etudes_partenariats/Bilan%20encadrement%20en%202019-resume-def.pdf

## Update 2026-09-08 (KB refresh)

Digest: `research-2026-09-08.md` (Reports A6, B, C2). Flags as in the digest: verified = read on
the fetched primary page; "via secondary" = primary blocked; unverified = press/snippet only.

**New evidence**

- Monràs & García-Montalvo, CEPR DP20018 (Feb 2025 edition of the FRBSF WP in §2/§3; academic):
  rents −5% treated vs control; units above reference fall, below rise; total supply of units
  −10%; probability a unit is rented −2 pp; **IV elasticity of new contracts w.r.t. rent ≈2.0
  (1.6–3.2 across specs), OLS 0.07** (PDF, verified). The model's `supply_response_elasticity`
  range 0–2 spans exactly this paper's OLS (≈0, the Jofre-Monseny/Paris world) to its IV
  (≈2); the upper IV specs (3.2) sit above the range — not widened, documented.
- Izquierdo Llanes, García-López, Cabezas & Pinto, *The rent control paradox*, IJHMA 4 Jun 2026
  (academic, UNED/URJC): DiD Catalonia vs Madrid/Valencia/Andalusia on portal-barometer data
  2019–25 — "economically substantial" relative supply contraction, more moderate listed-price
  increase, large rise in contacts per listing; magnitudes paywalled (abstract, verified).
  Same direction as Pérez García (§3): supply effect robust, price effect weak — on listings.
- O-HB ZMRT monitoring report no.4, 27 May 2026 (municipal observatory): new-contract rent Q4
  2025 €1,161 vs €1,193 Q1 2024 (−2.7% real); counterfactual trend €1,319 ⇒ 13.6% avoided;
  +1,374 active contracts since regulation; seasonal contracts 1,282 in Q4 2025 (−53% y/y);
  rents 2000–23 +178% vs income +88% (ohb.cat, verified).
- Incasòl deposits Q4 2025 (Generalitat via Infobae 18 Apr 2026; government data): seasonal
  contracts net **−1,233** in Q4 2025 (first fall); habitual stock +8,895 in 2025; rents
  tensioned €902 (+1.6%) vs non-tensioned €639 (+9.4%); Barcelona −2.7%; 96% of seasonal
  contracts in tensioned zones (article, verified). Govern claim: −1.3% rents in zones vs +9.5%
  outside (gencat, verified). Both are government readings of the same register.
- Portal/industry readings, side by side with the above: idealista 16 Mar 2026 — Barcelona
  long-term listings −56% in two years, seasonal +58%, seasonal share 64% (34% Mar 2024),
  Hospitalet −66%, Girona/Tarragona ≈−50%, 65 contacts/listing, asking rents +12.9% Barcelona /
  +15.9% Tarragona (verified). Brainsre 6 Aug 2026 — long-term listings Q1 2024→Q2 2026
  Catalonia **−72% vs Madrid −38%**; asking rents Catalonia +13.7% vs Madrid +25.6%; seasonal
  ≈40% of the Catalan market; 90% of listings by professional operators (verified). The Madrid
  comparator says part of the Catalan listing fall is national, and that Catalan asking rents
  rose less than Madrid's — a reading the portal frames as scarcity and the Govern as
  containment. Not resolved here.
- Spillover signature: +1.6% tensioned vs +9.4% non-tensioned Catalan municipalities in the
  same register (Incasòl Q4 2025, verified). Government = containment; landlord (Cambra) =
  displaced demand into uncapped municipalities. Same number, two readings.
- Enforcement: 529 sanction files, 74% ex officio; fines up to €90k (serious) / €900k (very
  serious) (govern.cat 22 Apr 2026, title only verified — page 403 on fetch).

**Legal / institutional status**

- BOE 29 Jul 2026 (BOE-A-2026-16532, verified): Asturias becomes the 5th CCAA (Llanes,
  Cabrales, parts of Gijón, Avilés, Gozón); Galicia adds Santiago de Compostela; Euskadi adds
  Basauri. National total **317 municipalities in 5 CCAA: Cataluña 271, Euskadi 18, Navarra 21,
  Galicia 2, Asturias 5** (BOE / Civio, verified); ≈9.3M people covered (MIVAU 29 Jul,
  unverified) ≈ 19% of INE's 49.8M population (INE ECP 1 Jul 2026, verified); valid 3 yrs (to
  Jul 2029). Q1 2026 additions: Pasaia, Zestoa, Arrasate, 3 yrs from 27 Apr 2026
  (BOE-A-2026-9175, verified).
- Euskadi list (Gobierno Vasco portal, verified): Donostia, Errenteria, Barakaldo, Irun,
  Lasarte-Oria, Zumaia, Astigarraga, Bilbao, Usurbil, Vitoria-Gasteiz, Galdakao, Hernani, Lezo,
  Tolosa, Arrasate, Pasaia, Zestoa, Basauri.
- Catalonia renewal + expansion (gencat, verified; govern.cat 403): procedures opened 21 Jul
  2026, public information extended 19 Aug, BOE pending — extend **118 of the 140** (Mar 2024)
  beyond Mar 2027, **drop 22** (incl. Lleida, Reus, Granollers, Mollet), **add 53** (incl.
  Martorell, Sant Andreu de la Barca) ⇒ ~302–324 if approved; ~90% of Catalan population.
  Exit dynamic: municipalities are leaving the regime at the 3-year mark — coverage is not
  monotone in time.
- CCAA still refusing to declare: Madrid, Andalucía, Valencia, Murcia, Castilla y León — 0
  municipalities; Valencia studying Burjassot / La Pobla requests (Valencia Plaza, press,
  unverified).
- **STC 53/2026** (8 Jul 2026; BOE-A-2026-16928, 3 Aug, verified): the Govern de Cataluña's
  recurso against Ley 12/2023 dismissed; arts 12, 18.5–6, 23, 24, DF7 upheld under art.
  149.1.13 CE; earlier annulments (arts 16, 27.1 §3, 27.3, DT1) stand. The competence question
  that ended Ley 11/2020 (§1) is settled for the state instrument.
- TC admitted the PP recurso 2415-2026 against Catalan Ley 11/2025 (seasonal/room cap): admitted
  9 Jun, BOE-A-2026-13028 16 Jun 2026 (title verified); arts 2.2, 3.8, 5.5, 5.6, 5.8, 5.9, 5.14,
  5.15, 8.1; **no suspension**. The Jan 2026 seasonal closure (§1) is in force but sub judice.
- **RDL 8/2026** (20 Mar): 2% rent-update cap to 31 Dec 2027 + 2-yr extraordinary extension —
  rejected by Congress 28 Apr 2026, derogation BOE 30 Apr (BOE-A-2026-6545 / Iberley, verified).
  `within_contract_update_rate` stays at IRAV, not 2%.
- Stalled omnibus RDL (que.es 27 Jul / eldiario.es; press, unverified): seasonal contracts ≤12
  months only with written cause, else 5/7-yr LAU; room rents summed ≤ whole-flat cap
  (tensioned zones only); extraordinary extension for contracts expiring before 30 Jun 2028
  (~630k contracts/yr, ~4M people). Draft 21 Jul, pulled from the 28 Jul Consejo de Ministros
  (Junts, Podemos); minister 2 Sep: "text ready", aiming September; fallback ordinary bill.
- Catalonia **Ley 11/2026** (DOGC 13 Jul, in force 14 Jul 2026; gran-tenedor rules for contracts
  from 31 Jul; exnovo.law law-firm note, DOGC unverified): gran tenedor = ≥5 dwellings in
  Cataluña / ≥10 Spain-wide, **incl. natural persons**, usage rights and co-ownership counted;
  "rent" = all charges (no fee pass-through); room rentals under the cap + bonds; cédula in all
  ads; error-regularisation before sanction.

**What it changes for the model**

- `RentCap.coverage` (new field → `PolicyConfig.cap_coverage`): share of the zone inside
  declared municipalities. Spain-2026 ≈ **0.42** of the model's tensioned zone (317
  municipalities / 9.3M people mapped onto it); Cataluña-2024 ≈ **1.0** (~90% of Catalan
  population). Constant per scenario today; the Catalan exit/entry churn argues for a
  time path — documented gap.
- `supply_response_elasticity` 0–2: now explicitly the OLS→IV span of one paper (0.07 → 2.0);
  M&M's 3.2 upper spec is outside — recorded, range not widened.
- `seasonal_segment_capped`: first empirical anchors for the closure — Incasòl −1,233 seasonal
  contracts in Q4 2025 (verified), O-HB −53% y/y (verified). Whether those units return as
  ordinary contracts stays disputed: O-HB +1,374 active contracts vs Cambra "sale, vacancy or
  family use" (§3). No parameter change.
- Spillover to non-capped zones (+1.6% vs +9.4%, Incasòl; Potsdam +12%, §4): the model has no
  cross-zone rent channel beyond migration and **does not reproduce this** — gap, and a
  validation target once the channel exists.
- §5 validation target "tensioned vs untensioned gap ≈5 pp over 18 months" (+0.8 vs +5.7) keeps
  that horizon; add the Q4 2025 anchors ≈8 pp (+1.6 vs +9.4, Incasòl) and ≈11 pp (−1.3 vs +9.5,
  Govern) as the ~2-year reading. Both kept; not averaged.
- §4 ranges unchanged; the "supply robust / price weak" cell gains a second study (IJHMA).
