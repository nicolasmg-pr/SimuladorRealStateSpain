# Bank

Actor: mortgage lenders in Spain (commercial banks; the cajas absorbed post-2012).
Credit availability turns willingness-to-pay into ability-to-pay; this constraint usually
moves prices more than income does.

Research date: 2026-08-07. Source register: see scratch `sources/bank.md` (to be merged
into `docs/sources.md`). Rules: every behavioural claim ≥2 independent sources; disputed
numbers kept as ranges.

## 1. Role & size in the market

- **New lending 2025**: 501,073 home mortgages, +17.8% y/y; capital lent €82.0bn (+32.6%);
  average loan €163,738 (+12.6%) (INE Estadística de Hipotecas, 2025 full year, verified).
- **Stock**: outstanding mortgage credit ≈ €619bn end-2025, +3.3% y/y — first growth year
  after a decade of deleveraging; home-purchase portion +3.8%; mortgage stock < 37% of GDP,
  far below the pre-2008 peak (AHE via idealista/fotocasa press, 2026-05).
- **Share of purchases financed with a mortgage**: DISPUTED, 55–70% depending on measure
  and period. INE-derived ratios: ~33% of purchases without mortgage (Sep 2024), ~34.5%
  (Q1 2025); activist press (La Marea) claims ~60% cash in 2024 using a different
  hipotecas/compraventas ratio. The ratio is noisy because compraventas and hipotecas are
  registered on different dates and not all mortgages finance a purchase. For the ABM: model
  a cash-buyer segment of ~30–40% of transactions (higher among investors/foreigners).
- **Concentration**: big six (CaixaBank, Santander, BBVA, Sabadell, Bankinter, Unicaja)
  hold ~67% of the home-loan stock (2025); CaixaBank alone ~24% (elEconomista, CNMC
  probe coverage). Effectively an oligopoly with active price competition on new lending
  ("mortgage war" whenever funding is cheap).

## 2. Balance sheet & constraints

- **Funding/regulatory frame**: ECB monetary policy sets marginal funding cost; EU capital
  rules (CRR/CRD) apply. Countercyclical capital buffer being raised from 0% toward 1%
  over 2024–2026 (unverified detail; capital-based, small effect on mortgage pricing).
- **Borrower-based macroprudential tools exist but have NEVER been activated.** RD-l
  22/2018 + RD 102/2019 gave Banco de España powers to cap LTV, DSTI, maturity etc.;
  Circular 5/2021 operationalised them; the BdE tools page confirms the power but lists no
  active limit, and in May 2026 BdE publicly argued against activating limits because they
  would hit young buyers hardest (BdE tools page; BOE RD-l 22/2018; elindependiente/merca2
  2026-05). ⇒ In the ABM, LTV/DSTI caps are *bank self-imposed rules*, i.e. policy levers
  a scenario can add, not existing regulation.
- **Asset quality**: total bank NPL ratio 2.87% (Sep 2025, 17-year low; idealista/BdE
  data); house-purchase mortgage doubtful ratio ~2.5–3% in 2024–25 (unverified precise
  value). Crisis peak: developer-loan default >25% of that book (2013).
- **Collateral recovery is slow**: judicial mortgage foreclosure takes ~2–4 years in
  practice (converging law-firm estimates), which makes banks ration credit ex ante rather
  than rely on repossession.

## 3. Observed decision rules (with evidence)

- **LTV rule: 80% of the lower of appraisal/price is the operative cap.** 24% of all new
  operations bunch exactly at 80% LTV (BdE IEF Otoño 2025). Average LTV at origination
  ~65% (series max 66.5% in 2018). Share of new mortgages with LTV > 80%: 6.1% end-2023 →
  11.7% Q2 2025 (highest since 2019, still low vs pre-2008) (BdE from Colegio de
  Registradores data, via IEF Otoño 2025). Caveat from BdE research: pre-2008 the *LTV*
  looked fine while *loan-to-price* often exceeded 100% because appraisals were inflated —
  LTV alone can mislead (Galán & Lamas, BdE WP 1931).
- **DSTI rule: mortgage payment + other debt ≤ 30–35% of net income**, stretched to ~40%
  for strong profiles. Universal bank practice, not law (multiple broker/industry guides;
  consistent with BdE responsible-lending guidance). This is the binding affordability
  constraint to encode.
- **Maturity**: average new-mortgage term ~24–26 years (2026 press reports a record ~26);
  standard maximum 30 years; constraint "borrower age at maturity ≤ 70–75".
- **Pricing**: variable = euríbor 12m + spread ~0.9–1.2 pp; fixed priced off swap curve.
  Pass-through of the 2022–23 euríbor rise to Spanish new-mortgage rates was slow and
  incomplete: +136 bp Dec-2021→Apr-2023, ~32% of the euríbor change and 73 bp less than
  the euro area (BdE Documento Ocasional 2312; CaixaBank Research concurs on "moderate
  adjustment"). Reason: fierce competition for high-quality borrowers + banks pushing
  fixed-rate products. Full pass-through takes >12–18 months and tops out below 100%.
- **Fixed vs variable at origination**: ~98% variable in 2007 → fixed ~40% by 2017 →
  fixed ~70%+ in 2021–22 → fixed 59–72% monthly during 2025 (Dec 2025: 63.4% fixed)
  (INE via idealista 2018 retrospective + INE 2025 press releases). The *stock* remains
  majority variable-linked, so euríbor shocks hit existing borrowers' cash flow.
- **Approval by profile**: banks screen on employment stability; temporary contracts and
  age <35 face materially higher rejection/discouragement (BdE statements 2026; broker
  guides). >60% of under-35s live with parents or spend >half their salary on rent
  (Eurostat via BdE). No published hard rejection-rate levels by profile — ECB BLS gives
  only net-tightening directions (see §7). Avales ICO (2024–2027, €2.5bn): state
  guarantees 20% (25% with energy cert ≥D) so banks lend up to 95–100% LTV to under-35s /
  families with minors; uptake weak — 10,453 operations, €255.8M guarantees, €1.34bn
  mobilised by end-2025, ~10% of the envelope (ICO monthly report; elEspañol 2026-02).
  ⇒ shifts the LTV constraint, not the DSTI constraint, for a small eligible slice.
- **Default handling**: Ley 5/2019 (in force Jun-2019) — foreclosure only after arrears of
  ≥12 monthly payments or 3% of capital (first half of loan) / ≥15 payments or 7% (second
  half), plus 1-month cure notice (BOE, verified). Then 2–4 years of judicial process.

## 4. Reaction to past shocks (case episodes)

- **2000–2007 boom**: lending standards degraded via appraisal inflation (LTP > 100%
  while measured LTV stable); ~98% variable-rate; cajas drove expansion. 1.34M mortgages
  registered at the 2006 peak.
- **2008–2013 bust (the credit crunch template)**: new mortgage counts fell ~85%
  peak-to-trough (1.34M in 2006 → ~200k in 2013; y/y falls >30% in 2008, 2011, 2012)
  (INE via idealista retrospective; press at the time reported −41/−42% y/y in late 2008).
  Banks cut LTV and rationed by profile; 523,607 foreclosures 2007–2013; cajas collapsed
  and were absorbed (ESM programme 2012, €41bn used). House prices fell 30–40% over 6
  years — slowly, because foreclosure/fire-sale supply arrived with years of lag.
- **2022–23 rate shock**: euríbor −0.5% → ~4.0–4.2% (peak autumn 2023). New home
  mortgages −17.8% to −21.3% in 2023 (INE count −17.8%; new house-purchase lending
  ~−18.6%); yet prices *rose* (~+4–8% depending on index). Why muted: cash/foreign/
  replacement buyers took a larger share, supply shortage, banks' slow pass-through, and
  strong household balance sheets (CaixaBank Research; ING; BdE IEF). Key ABM lesson: a
  rate shock with excess demand and a large cash segment compresses *quantities*, not prices.
- **2024–25 easing**: ECB cuts → Dec 2025 average new rate 2.87%; 2025 lending +17.8% in
  count, +32.6% in volume, average loan +12.6%; LTV>80% share doubled from end-2023 —
  standards loosen pro-cyclically but from a conservative base (INE; BdE IEF Otoño 2025).

## 5. Power & relations to other actors

- **Households**: the bank's DSTI×rate×maturity rule converts income into max purchase
  price; it binds hardest on young/temp-contract households, pushing them into renting
  (feedback into tenant demand and rents — BdE's own argument against LTV caps).
- **Government/ICO**: state absorbs tail risk (avales ICO) to relax the down-payment
  constraint; consumer-protection law (Ley 5/2019) lengthens effective foreclosure,
  raising loss-given-default and, at the margin, ex-ante rationing.
- **Banco de España/ECB**: ECB sets the funding-cost level; BdE monitors but does not cap
  lending standards — banks self-regulate at LTV 80 / DSTI 35.
- **Developers**: banks also fund construction; after 2008 they cut developer credit far
  more violently than household credit (developer NPL >25%), throttling new supply — a
  channel worth wiring into the developer actor.
- **Investors/cash buyers**: outside the credit constraint entirely (~1/3 of purchases);
  they arbitrage the gap left when mortgage-dependent buyers are rationed.

## 6. Extracted parameters

| Parameter | Value / range | Unit | Source(s) | Confidence |
|---|---|---|---|---|
| LTV cap in bank practice (no legal cap) | 80 (bunching: 24% of ops exactly at 80) | % of min(appraisal, price) | BdE IEF Otoño 2025 (CdR data); BdE tools page (no activated limit) | high |
| Average LTV at origination | 63–66.5 (≈65 in 2025; max 66.5 in 2018) | % | BdE via CdR (IEF Otoño 2025, press summaries) | medium |
| Share of new mortgages LTV > 80% | 6.1 (end-2023) → 11.7 (Q2 2025); pre-2008 much higher | % of new ops | BdE IEF Otoño 2025 | medium |
| LTV with aval ICO (<35 yrs / family w/ minors) | 95–100; state guarantees 20–25 | % | ICO programme docs; CaixaBank/BBVA product pages | high |
| Aval ICO uptake (through 2025) | 10,453 ops, €255.8M guarantees (~10% of €2.5bn envelope) | count / EUR | ICO monthly report; elEspañol | medium |
| Max DSTI (payment+debts / net income) | 30–35 standard; up to 40 exceptional | % of net income | Multiple broker/industry guides; BdE responsible-lending guidance | high |
| Mortgage maturity, new loans | avg 24–26; max 30; age+term ≤ 70–75 | years | INE-based press; industry guides | medium |
| Variable-rate spread over euríbor 12m | 0.9–1.2 | pp | Industry rate guides (LoanInSpain, brokers) | medium |
| Pass-through of euríbor to new mortgage rates | ~32% of Δeuríbor after 16 months (Dec21–Apr23; 136 bp vs 209 bp euro area); full adjustment >18 m, <100% | share / bp | BdE DO 2312; CaixaBank Research (independent viewpoints agree) | medium |
| Fixed-rate share at origination | 2 (2007) → 40 (2017) → ~70 (2021–22) → 59–72 (2025, Dec: 63.4) | % of new mortgages | INE (2025 press releases); idealista/INE retrospective | high |
| Average rate on new home mortgages | 2.87 (Dec 2025); peak ~3.3–4.0 (late 2023, INE vs BdE TEDR — range kept) | % annual | INE H1225 (verified); 2023 peak (unverified) | medium |
| New-lending crash multiplier, 2008–13 | −85 peak-to-trough over 7 yrs (1.34M → ~0.20M); worst y/y ≈ −42 | % count | INE via idealista; contemporary press | high |
| New-lending fall, 2022–23 shock | −17.8 to −21.3 (2023 y/y); prices still +4–8 | % count / % price | INE; Infobae; CaixaBank Research; ING | high |
| Recovery multiplier, 2024–25 easing | +17.8 count, +32.6 volume (2025 y/y) | % y/y | INE 2025 full year (verified) | high |
| Mortgage NPL / doubtful ratio | total bank 2.87 (Sep 2025, cycle low); mortgage book ~2.5–3; crisis-peak developer book >25 | % | BdE data via idealista; Statista/CEIC; academic (crisis) | medium |
| Foreclosure trigger (Ley 5/2019) | ≥12 payments or 3% capital (1st half); ≥15 or 7% (2nd half) + 1-month notice | months / % | BOE Ley 5/2019 art. 24 (verified) | high |
| Foreclosure duration (judicial) | 2–4 | years | Converging law-firm estimates (Arriaga, Orozco, others) | medium |
| Share of purchases mortgage-financed | 55–70 (measure-dependent; cash ≈ 30–40) | % of transactions | INE-derived press; La Marea (dissenting 60% cash) — range kept | medium |
| Rejection-rate function by profile | No published levels. Proxy: base rejection ~15–25%; ×1.5–2 for temp contract or age<35 without aval; +tightening in BLS episodes | share | ECB BLS (directional only); BdE 2026 statements | guess |
| Big-six share of mortgage stock | ~67 (CaixaBank ~24) | % | elEconomista (CNMC coverage) | medium |

## 7. Open questions

1. **Rejection-rate levels by borrower profile** — BLS only publishes net-tightening
   directions. Check EFF (Encuesta Financiera de las Familias) microdata for
   denied/discouraged-borrower shares by age and contract type before calibrating the
   approval function (currently a guess).
2. **Loan-to-income distribution** — BdE IEF says LTI increases are "limited" but I did
   not extract the level/percentiles. Pull IEF Otoño 2025 chapter 4 charts (LTI, LSTI at
   origination) for a proper DSTI distribution rather than a single 35% cap.
3. **2023 peak new-mortgage rate** — INE avg vs BdE TEDR differ (~3.3 vs ~4.0). Pin down
   the BdE synthetic rate series (unverified here) and use one definition consistently.
4. **Cash-purchase share by zone type** — need tensioned-metro vs rural split (foreign
   buyers concentrate on coasts); INE/notaries publish regional breakdowns.
5. **Does the 80% LTV cap bind on appraisal or price?** Appraisal inflation made LTP the
   better risk measure pre-2008 (Galán & Lamas). Decide which the ABM's bank uses and
   whether appraisal bias is a parameter.
6. **Foreclosure-to-market lag** — 2–4 yr judicial time plus REO disposal; need a
   distribution for how repossessed stock re-enters supply (mattered enormously 2008–2014).
7. **CCyB path 2024–26 and any future borrower-based activation** — watch BdE; a first-ever
   LTV/DSTI cap is exactly the kind of policy scenario this ABM should support.
