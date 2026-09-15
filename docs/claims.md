# Claims ledger — what public argument requires, and what this model can say about it

This is the file the project exists for. Spanish housing is argued about with confident
numbers and almost no comparable evidence work; the point of building the model was to be
able to answer, for a given public claim, three questions:

1. **What would have to be true** for the claim to hold — which mechanism, which parameter,
   which value of it.
2. **What the model says**, at the only resolution it is allowed to speak in.
3. **What evidence would settle it** — including the cases where nothing available can,
   which is the sharpest thing the model produces (redesign spec §1).

## The rules this ledger obeys

- **Directions first, and now a few magnitudes.** The variance rule (`model-spec §13.2`) has
  moved twice since this ledger was written. Phase E left exactly two reportable magnitudes;
  after §5c.8 and the sourcing of `ask_markup`, `price_index_smoothing` and `overbid_sigma`
  the set is **price-to-income and the price level, transactions, completions, arrears, time
  to sale and bids per listing**, each conditional on the sourced parameter bands. What is
  *not* reportable is the **rent side** — the rent level, tensioned vacancy and overburden all
  rest on `small_landlord_premium`, a parameter §7.1b can justify only a third of — plus the
  ownership rate, the zone price ratio and the cash share, which rest on `buy_attempt_prob`
  and `search_listings`. **Every rent number below is therefore a direction with a size
  attached for transparency, not an estimate**, and every number anywhere in this file is the
  measurement of this model's response, never a forecast about Spain.
- **Ten seeds, and the sign count is shown.** Every model response here is the mean over
  seeds 1–10, 60 ticks, measured from tick 24 (the lever lands at tick 8), against the same
  seed's baseline. `9/10` means nine of ten seeds moved in the reported direction; anything
  at 5/10 or 6/10 is noise and is reported as **no effect**, not as a small one.
  Artefacts: `runs/levers_10seeds.json`.
- **The claim is quoted, attributed and dated.** Every row's source is a line in
  `docs/sources.md`. Paraphrasing a claim into something easier to refute is the failure mode
  this file is most exposed to.
- **A verdict is one of four**: *supported* · *contradicted* · *conditional* (true only in
  part of the range the evidence admits, and the row says which part) · *unidentifiable*
  (neither this model nor the registered evidence can settle it).

## Re-run against the current model (2026-09-15)

Every number below was re-measured after phases G and §5c.8 changed the sale block — the
valuation anchor, the scarcity channel and the clearing calendar. The instrument is now a
module rather than a hand-run: `uv run python -m resim.levers --jobs 10`, artefact
`runs/levers_10seeds.json`, ten seeds, lever at tick 8, window from tick 24.

**What moved, and it is not decimals.** The rent cap's rent leg deepened (−15.4% → −24.1%
transacted) and its price leg halved (−15.3% → −10.3% tensioned); the credit crunch roughly
doubled on volume (−9.7% → −18.6%); the transaction tax acquired a rental spillover it did not
have (+2.9% on tensioned rents, 8/10); the demand subsidy's rent effect went from noise to
+2.2% (8/10); and the tourist restriction's rent effect shrank to −1.6% (3/10), which moves it
*into* the academic range for Barcelona instead of above it. Two verdicts are affected in
substance (F-4, F-9) and one carries a new caveat that did not exist before (F-5).

## Summary

| # | Claim | Verdict |
|---|---|---|
| F-1 | A 100% tax on non-EU buyers frees up housing | conditional — real channel, effect an order of magnitude below the problem |
| F-2 | Mobilising the 3.8M empty homes fixes the shortage | contradicted, on the geography |
| F-3 | Spain is 700,000 homes short, so building closes the gap | first half supported, second half unidentifiable on this horizon |
| F-4 | Tourist flats are why rents rose | conditional — right sign, and the re-run brings the size inside the academic estimate |
| F-5 | The Catalan rent cap works: new contracts fell 4.7% | supported in direction; size overshoots, and Spain's *current* law is a different instrument the model cannot yet report |
| F-6 | The Catalan rent cap destroyed supply: listings −72% | direction supported, the −72% is a basis error |
| F-7 | Public housing lowers rents | supported for rents and access; sale prices do not fall |
| F-8 | Cutting ITP for young buyers improves access | conditional — much of it capitalises into price |
| F-9 | The ICO guarantees help young people buy | unsupported, and mildly counterproductive: rents +2.2% |
| F-10 | Housing always goes up | contradicted by the model's own hold-out |
| F-11 | *(implicit in all of the above)* housing policy is what moves housing | contradicted — credit conditions move it more than any lever here |

---

## F-1 · "A 100% tax on non-EU buyers"

> "Solo en 2023, los no residentes de fuera de la Unión Europea compraron 27.000 casas y
> departamentos en España. No para vivir en ellas, lo hicieron principalmente para especular
> y ganar dinero. Algo que en el contexto de escasez que vivimos no podemos permitirnos."
> — Pedro Sánchez, 13 January 2025

**What it requires.** That non-resident purchases are a large enough share of demand for
removing them to relieve prices, and that a tax removes them rather than being absorbed.

**What the model says.** Applying the announced surcharge (+90pp on a 10% base) as
`TransactionTax(foreign_delta=0.90)`:

| | response | seeds |
|---|---|---|
| national price | −2.4% | 9/10 |
| tensioned price | −3.3% | 10/10 |
| transactions | −1.7% | 9/10 |
| tensioned contract rent | +0.2% | 5/10 → **no effect** |

The channel roughly doubled when the sale block was rebuilt (§5c.6–§5c.8): with prices
anchored to budgets rather than to a selection premium, removing a segment of unconstrained
cash demand bites harder. It is still about two percent.

Validation records the mechanism separately: the surcharge cuts non-resident purchases by
about **45%, not 100%**, because the +60–79% price premium those buyers pay absorbs half the
wedge before it bites.

**Verdict: conditional.** The channel is real and the sign is right, but the model's price
response is about two percent — an order of magnitude below the affordability gap the claim
invokes. The claim's own premise is also weaker than stated: non-residents are 7.9–8.1% of
purchases [Registradores, Notariado], and "principalmente para especular" is an assertion
about motive that no registered series measures.

**What would settle it.** The elasticity of non-resident demand to a transaction tax. Nobody
has measured it; the Baleares and Canadian restrictions are the closest natural experiments
and neither is in `docs/sources.md` yet.

---

## F-2 · "There are 3.8 million empty homes — expropriate or mobilise them"

> "Somos partidarios de la expropiación de viviendas en desuso de entidades bancarias, fondos
> de inversión, empresas multipropietarias." — Sumar, April 2025
> "Ojalá estuvieran donde las necesitamos." — the housing minister, June 2025

**What it requires.** That the empty stock sits where the shortage is, and that a holding cost
moves it into the market.

**What the model says.** The vacancy tax lever (0.5% of value, 15% detection):

| | response | seeds |
|---|---|---|
| vacancy rate | −0.5% | 6/10 → **no effect** |
| tensioned contract rent | +0.9% | 7/10 → weak, wrong sign for the claim |
| national price | −0.0% | 5/10 → **no effect** |

Weaker than in phase F, when the vacancy leg at least moved 8/10. On the current model the
lever moves **nothing** at ten seeds.

And the model's vacancy geography, which is gated against the Censo: vacancy runs **rural
19.0% > secondary 14.1% > tensioned**, because that is where the INE ladder puts it.

**Verdict: contradicted as stated, and the minister's objection is the model's too.** The
lever mobilises a little stock and does not move rents where rents are the problem. The
model's `withheld_share` — the part of the empty stock that is not mobilisable at any tax,
0.39 in the metro and 0.81 in rural — is a calibrated guess and is the row this verdict
leans on hardest.

**What would settle it.** A measured mobilisation response to the IBI surcharge in the
municipalities that have applied it. The model's 0.04–0.30/yr range is an invention; the
Vancouver null result is the only comparable evidence registered.

---

## F-3 · "Spain is 700,000 homes short"

> The Banco de España raises to 700,000 the number of missing dwellings; 345,000 permits
> against 604,000 households formed in 2022–24; half the deficit in Madrid, Barcelona,
> Valencia, Alicante and Málaga. — José Luis Escrivá, September 2025

**What it requires.** For the count: an accounting identity between formation and completions.
For the *inference* usually attached to it — "so build and prices come down" — a supply
channel that reaches prices inside the horizon anyone cares about.

**What the model says.** The count is reproduced by construction: completions run at **55% of
formation** (§9 target 4, band 40–70%, ten seeds). The inference is not: the land-release
lever raises starts **+6.6% (10/10)** and moves the national price **0.0% (5/10, no effect)**
over 60 ticks, which is what an 8-quarter construction lag plus a 20–60-tick land lag implies.

**Verdict: the count is supported; the inference is unidentifiable on this horizon.** A model
whose supply lever cannot move prices in fifteen years is not evidence that supply does not
work — it is evidence that the question is about a horizon longer than the one anybody argues
over.

---

## F-4 · "Tourist flats are why rents rose"

**What it requires.** That the stock withdrawn to seasonal use is large enough, and that
returning it lowers rents by the amount the debate assumes.

**What the model says.** The tourist-restriction lever:

| | response | seeds |
|---|---|---|
| tensioned contract rent | −1.6% | 7/10 down |
| tensioned asking rent | −0.8% | 6/10 down |
| vacancy rate | +9.2% | 10/10 |
| new leases | +1.2% | 6/10 → **no effect** |

**What the data says.** The VUT stock *fell* 15.4% between August 2024 (403,267) and May 2026
(341,001) while rents went on setting records. The best-identified academic estimate for
Barcelona is **+1.9% on average, up to +7% in the densest neighbourhoods**.

**Verdict: conditional — right sign, and after the re-run the model's size AGREES with the
evidence rather than exceeding it.** The response fell from −3.5% to **−1.6%**, which sits
inside Segú's Barcelona estimate of +1.9% on average (up to +7% in the densest neighbourhoods)
instead of above it. That is the one place in this ledger where a model change moved a reading
toward its source without being aimed at it. Removing seasonal units lowers rents by one to two
percent, concentrated where the seasonal share is high. It cannot be the main driver of a 46% five-year rent rise, and the
observed VUT contraction running alongside continued rent growth is the cleanest available
falsification of the strong version.

---

## F-5 · "The Catalan cap works — new contracts down 4.7%"

> New rental contracts in Barcelona fell 4.7% since the cap came in; €/m² −2% in 2026Q1.
> — Generalitat/Incasòl data via press, July 2026

**What the model says.** `RentCap` at full coverage:

Run under **Ley 11/2020**, the Catalan statute these studies evaluate, in which the reference
index binds *every* landlord:

| | ε = 1 | ε = 2 | seeds |
|---|---|---|---|
| tensioned contract rent | **−23.5%** | −20.6% | 10/10 |
| new leases | −22.1% | −32.3% | 10/10 |
| rent overburden | −4.3% | −1.0% | 10/10 |
| tensioned price | −10.4% | −11.1% | 10/10 |

**Two caveats, and the second is new on 2026-09-15.**

*The size still overshoots.* −23.5% against Barcelona's measured ≈−5%, and
`test_rent_cap_reproduces_the_monras_co_movement` stays an open registered failure. The
overshoot is now attributed rather than mysterious: the model's reference index sits **16% below
market rents at activation**, where the published implied cuts are −10…−15% for the Catalan
index and −20% on average for the state one. The model's cap is simply harder than the one
Monràs evaluated, and the rest of the distance is compliance, composition, and contracts that
were already below the index — none of which the model separates. Read the sign, not the size.

*Spain's current law is a different instrument, and the model cannot yet report it.* §5b now
carries both statutes: Ley 11/2020 binds the index on everyone, Ley 12/2023 binds it on grandes
tenedores and holds everyone else to their own previous contract plus IRAV — or to nothing at
all, where no contract exists in the last five years. Individuals hold 85–92% of the Spanish
rental stock, so the difference is most of the market. Run under the current law the model
produces **rents +16.6% (10/10)** with new leases −16.1%: the withdrawal channel with almost no
cap holding rents down. **That number is not reportable and is not a prediction** — the exit
hazard behind it was identified when the index bound every landlord, and nothing has
re-identified it for a regime where it binds one landlord in ten. It is in the artefact as
`rent-cap-state-law` so that the gap is visible rather than hidden.

**Verdict: supported in direction, and the model overshoots the size.** Its cap covers the
whole tensioned zone where Spain's covers ≈42% of it, and the measured −15% against Barcelona's
−4.7% is consistent with that alone. The model also cannot see the margin the same balance
reports: average floor area fell from 73.7 m² to 71.5 m², so €/m² *rose* 3.5% while the
headline rent fell. **Dwelling size is a scalar quality index in this model**
(`model-spec §10`), so the composition response is outside it — a claim about quality-adjusted
rents is **unidentifiable here**, and the model says so rather than pretending its rent index
settles it.

---

## F-6 · "The cap destroyed supply — listings down 72%"

> Long-term rental listings in Catalonia fell from 68,629 (2024Q1) to 18,878 (2026Q2), −72%.
> — industry data, 2026

**What the model says**, under Ley 11/2020 as F-5 explains: new leases fall **−22.1% (ε=1) to
−32.3% (ε=2)**, 10/10 seeds. The three registered Catalan studies put the contract response
between **0 and −13%**. Under the current state law the same lever gives −16.1%, which is
closer to the studies and, for the reason F-5 gives, still not reportable.

**Verdict: the direction is supported; the −72% is a basis error.** Portal listings are a
stock of advertisements, and contracts are a flow; a cap that shortens the time a flat spends
advertised will cut the first without cutting the second by anything like as much. The model
measures contracts, the studies measure contracts, and both land an order of magnitude below
the headline. Quoting the listings figure as the supply response is the same mistake this
project made twice internally and documented both times: asking versus contract rents, stock
versus entry yields.

---

## F-7 · "Public housing lowers rents"

**What the model says.** The public-housing lever:

| | response | seeds |
|---|---|---|
| new leases | **+10.6%** | 10/10 |
| rent overburden | **−4.4%** | 10/10 |
| tensioned contract rent | −2.7% | 8/10 down |
| construction starts | +37.9% | 10/10 |
| national price | **+1.4%** | **10/10** |

**Verdict: supported for rents and access — and note what it does not do.** Sale prices do
not fall; they tick *up*, and after the re-run that is unanimous across seeds (10/10, +1.4%)
rather than 9/10, because the programme competes for the same builders and land while
adding households who stay in the rental market. Anyone arguing public housing as a
house-price policy is arguing for something the model does not produce; as a rental-access
policy it is the strongest lever in this table on overburden.

---

## F-8 · "Cut ITP for young buyers and access improves"

> The PP's proposal: 4% ITP on a first home for under-40s across the regions it governs.
> — July 2026

**What the model says**, reading the transaction-tax lever symmetrically (+2pp measured):
prices **−1.6% (10/10 down)**, transactions **−4.3% (9/10 down)**, and — new since the block
was rebuilt — tensioned rents **+2.9% (8/10 up)**. A cut of the same size therefore raises
prices by roughly the same order, raises volume by more than phase F showed, and *lowers*
rents, because the households it moves into ownership stop bidding for tenancies.

**Verdict: conditional — much of it capitalises, and the rental spillover is new.** The buyer
keeps only the part of the cut that is not capitalised into the price, and the model says a
substantial part is. The re-run adds a second channel the phase-F reading did not have: the
tenure switch it induces shows up in rents, which is an argument for the policy that its
advocates do not make and its critics do not answer. It is a transfer to sellers in
proportion to how tight the market is — which is the standard theoretical prediction, and the
model reproduces it rather than testing it.

---

## F-9 · "The ICO guarantees help young people buy"

**What the model says.** The demand-subsidy lever: price **+0.5% (8/10)**, ownership rate
**−0.08% (6/10 → no effect)**, transactions **+0.7% (7/10)**, and tensioned rents **+2.2%
(8/10 up)** — the last of these is new since the re-run and it points the wrong way for the
claim: the instrument leaves renters paying more while moving nobody across the ownership line. Validation adds why: with the 2026
wealth cap of €150,000, about **1% of tenants** are excluded by it — the cap is nearly inert —
and the LTV lift reaches a small eligible group whose bids rise with it.

**Verdict: unsupported at the modelled scale, and after the re-run mildly counterproductive.**
What the instrument does in this model is lift prices slightly, lift rents by more, and move
almost nobody across the ownership line. The access effect the
literature attributes to guarantee schemes (0.35–0.45) is registered in the dossiers and the
model does not reproduce it, which is a mark against the model as much as against the claim —
`buy_attempt_prob` and the eligible share are both guesses.

---

## F-10 · "Housing always goes up"

The claim that needs no citation because it is the background assumption of most popular
commentary — and the one this project is best placed to answer, because the answer came out of
an episode the model had never seen.

**What the model says.** Fed the 2008–13 inputs and nothing else — the euríbor path, household
joblessness, formation, the completions already in the pipeline, the credit stop and the
foreclosure law of the period — the national price index falls **−56.9% ± 2.2** peak to trough
over six years, negative equity reaches **11.9%** of mortgaged owners, and the foreclosure flow
reaches the order CGPJ measured.

**Verdict: contradicted.** With two qualifications that make it honest. The model
*overshoots* the observed −30…−45%, so the right reading is "housing can fall by a third or
more, and this model falls harder than Spain did". And the episode is now **spent twice over**:
the model gained two brakes on 2026-09-15 because that run showed they were missing
(`model-spec §5d`), so it is in-sample on 2008–13 and the re-run is a diagnostic rather than
evidence (`model-spec §13.11`). The verdict survives, because it rests on the *direction* of a
fall the model produces from inputs alone — but nobody should quote −57% as a prediction, and
with the brakes it reads −59%.

---

## F-11 · The claim nobody makes, which the table makes for them

Ranked by how much each lever moves the national price, over ten seeds:

| lever | price | transactions | seeds |
|---|---|---|---|
| **credit crunch** | **−6.8%** | **−18.6%** | 10/10 |
| rent cap, Ley 11/2020 (ε=2) | −6.6% | −9.3% | 10/10 |
| rent cap, Ley 11/2020 (ε=1) | −6.3% | −8.1% | 10/10 |
| rent cap, Ley 12/2023 | −6.9% | −7.3% | 10/10 · 9/10 (rents **rise**; see F-5) |
| non-resident surcharge | −2.4% | −1.7% | 9/10 |
| transaction tax +2pp | −1.6% | −4.3% | 10/10 · 9/10 |
| tourist restriction | −0.1% | no effect | 6/10 |
| vacancy tax | −0.0% | no effect | 5/10 |
| land release | 0.0% | no effect | 5/10 |
| demand subsidy | +0.5% | +0.7% | 8/10 · 7/10 |
| public housing | +1.4% | no effect | 10/10 |

**The re-run sharpened this row rather than softening it.** The credit crunch is now the
largest price mover outright — it was third — and its volume effect roughly doubled, to
−18.6%. It is still the only lever that moves rents **up** (+7.6%, 10/10) as frustrated buyers
stay in the rental market, and it is still the one no housing ministry sets. The rent cap ties
it on price, but that is a rental policy whose price effect is a side-effect, and its size is
currently inflated by the registered defect F-5 records.

**Verdict: contradicted.** The honest summary of the whole ledger: **the levers that dominate
public argument are, in this model, the small ones.** As of 2026-09-15 the price level *is*
reportable as a magnitude (§13.2, after §5c.8), so this row no longer rests on a model that
cannot speak about prices at all — but it remains a statement about *relative* size, which is
what it was always for — because it is a claim about *relative* size, which is exactly what a model that
refuses to give point forecasts can still support.

---

## What this ledger cannot do

- It cannot rank two levers whose measured responses are within each other's seed noise.
- It cannot speak to composition — flat size, quality, neighbourhood — because quality is a
  scalar index (`model-spec §10`). Half the Catalan cap debate is about exactly that.
- It cannot price a bust it has already been tested on: the hold-out is spent.
- It cannot adjudicate motive ("para especular"), which no registered series measures.
- Its **rent** side is direction-only: `small_landlord_premium` explains 0.65 of the rent
  level and 0.75 of tensioned vacancy, and §7.1b can justify only 0.5–1.2pp of the 3.0pp the
  model uses. The price level stopped being direction-only on 2026-09-15 (§13.2). Every
  magnitude in this
  file is a property of the model, not an estimate of Spain.
