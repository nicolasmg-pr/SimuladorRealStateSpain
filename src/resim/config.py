"""Simulation parameters — the knobs of the world, before any policy is applied.

Split deliberately from `scenario.py`: config describes how the market works,
a scenario describes what we do to it.

Every field carries: unit, source (dossier §, see docs/actors and docs/policies) and a
confidence tag. `guess` = unsourced, per the bias-control rule in docs/plan.md.
Disputed values default to the midpoint of their documented range; the range itself is
recorded in the comment and exposed in the UI.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum


class ZoneType(Enum):
    TENSIONED = "tensioned"  # tensioned metro (Madrid/Barcelona cores + hot coast)
    SECONDARY = "secondary"  # secondary city
    RURAL = "rural"


@dataclass(frozen=True)
class ZoneConfig:
    """Zone-type differentiation. Multipliers apply to national anchors.

    Zone multipliers are the weakest evidence block (developer §7.3) — most are guesses,
    flagged for sensitivity analysis.
    """

    zone: ZoneType
    household_share: float  # share of all households at init [Censo approx — guess]
    # Share of zone households renting. SOURCED 2026-09-14 from INE ECV table 60181, *hogares
    # por régimen de tenencia y grado de urbanización* — the rural cell was **inferred** until
    # then; ECV publishes it. ECV-2025, % of households, market rent + below-market rent:
    #
    #   densamente poblada  19.5 + 4.2 = 23.7      (→ TENSIONED)
    #   nivel intermedio    15.7 + 2.9 = 18.6      (→ SECONDARY)
    #   poco poblada         8.6 + 2.2 = 10.8      (→ RURAL)
    #   national            16.7 + 3.5 = 20.2
    #
    # BASIS, declared because the two halves are not interchangeable. `HouseholdStatus.TENANT`
    # covers every renter, so the comparable ECV object is the SUM of the two rent rows, not
    # the market row alone. Quoting the market row (19.5 / 15.7 / 8.6) against this parameter
    # would understate renting by 2–4 pp per zone. Ceded/free-use households (5.0 / 7.2 / 10.4)
    # are NOT renters and are excluded — the model carries them inside `SEEKER` sharing.
    #
    # DECLARED RESIDUAL, not rescaled away: these published cells weighted by this model's
    # household shares (0.45 / 0.35 / 0.20) give a national 19.3%, against ECV's own 20.2%.
    # The 0.9 pp gap is not a measurement problem — it is `household_share`, still a guess
    # ("Censo approx"), not matching ECV's urbanisation shares. Renormalising the cells to
    # close it would hide a guess inside three sourced numbers, so the published values stand
    # and the residual is stated. It is `household_share` that should move when it is sourced.
    # [INE ECV table 60181 (ECV-2025); household-tenant §6 — high]
    tenant_share: float
    # × national household income. MEASURED ON THE MODEL'S OWN ZONES, 2026-09-14: all 8,131
    # Spanish municipalities ranked by Censo-2021 households and cut at this model's 45/35/20
    # shares (89 / 708 / 7,334 municipalities), then household-weighted mean income from the
    # 54 INE ADRH municipal tables (income year 2023, ADRH reaches 99.93–100% of each zone).
    # Raw ratios to the national figure: 1.0766 / 0.9621 / 0.8934.
    #
    # Those weight to **0.99989** — the identity holds without being forced, because the zones
    # are defined to hit 45/35/20 and ratios computed inside that partition reconcile. The
    # values below carry the residual ×1.000115 so the config guard is exact.
    #
    # Supersedes the ECV *grado de urbanización* gradient used from 2026-09-12 to 2026-09-14
    # (1.0683 / 0.9352 / 0.8824). ECV measures DEGURBA density classes, and those classes are
    # **54/31/15 of households, not 45/35/20** — recovered by solving ECV table 60181's four
    # over-determined tenure rows, which fits them to ≤0.03 pp and independently reproduces
    # ECV's national income anchor, held out of the fit, to €20 (0.05%). Mixing ECV cells with
    # size-rank-shaped weights was the source of the residuals this model was declaring; that
    # diagnosis is what these figures replace, not a measurement error in ECV.
    #
    # Basis: ADRH *renta neta media por hogar* — disposable household income after transfers
    # and tax, a MEAN. Not a wage. The gradient is taken from it, not the level; the level
    # anchor stays `PopulationConfig.income_median`. Year misalignment is declared, not
    # corrected: tenure 2021, income 2023, population 2025.
    #
    # Was a free guess of 1.15 / 1.00 / 0.80 until 2026-09-12.
    income_multiplier: float
    price_multiplier: float  # × national median dwelling value [guess from €/m² press]
    gross_yield: float  # /yr, rent/price at init [idealista+BdE RBA, investor-small §6 — high]
    itp_rate: float  # fraction of price, buyer transaction tax [OCU/CCAA, government §6 — medium]
    # share of zone rental stock held by gran tenedor [investor-large §6 — medium/guess]
    large_investor_share: float
    # € hard construction cost [UVE/ACR 1105–1323 national, developer §6 — high; zone mult guess]
    cost_per_m2: float
    # land as fraction of final new-build price [CNMC 25–50%, developer §6 — medium]
    land_share: float
    # long-run price elasticity of starts IN THIS ZONE. Land availability is what separates
    # the zones: a tensioned metro core cannot answer a price rise with much new supply, a
    # rural municipality can. It is NOT what holds the zone price ladder apart — adding this
    # gradient moved the tensioned/rural ratio by 0.04, and `location_premium` is what does
    # the work (model-spec §5b). It is kept because zone-targeted supply policy (land
    # release) behaves differently by zone, which a uniform elasticity cannot show.
    # Household-share-weighted average is held at the sourced national 0.45–0.58
    # [Caldera&Johansson/BdE]; the split across zones is a Saiz-style land-availability
    # gradient [guess — developer §7.3, weakest evidence block]
    supply_elasticity: float
    # non-resident cash demand present [Registradores concentration, household-owner §6]
    foreign_overlay: bool
    # multiplier on what a household will pay for a standard dwelling HERE, normalised to 1.0
    # in TENSIONED (model-spec §5b). A discount on the low-amenity zones, not a metro bonus:
    # bids are clipped by the credit limit, so a bonus is inert, while a discount binds on
    # willingness rather than ability — a rural household that could borrow €137k does not
    # offer it for a rural dwelling. Calibrated to the observed price gradient (Tinsa 2026Q1
    # provincial €/m²: Madrid 3,565 / Barcelona 2,772 vs Ciudad Real 776 / Zamora 881, i.e.
    # metro/rural ≈ 3.5–4.5), which the zone `price_multiplier` ladder 1.6/0.9/0.5 also
    # reflects; the wage gradient (De la Roca & Puga 2017: Madrid +46% vs the median city,
    # +55% vs rural) is why such a premium is sustainable, and part of it already sits in
    # `income_multiplier`. Value calibrated, direction and existence sourced
    # [kb-refresh-2026-09 §5; docs/validation.md location-premium revision — guess (level)]
    location_premium: float = 1.0
    # dwellings per household IN THIS ZONE: occupied plus EMPTY, excluding tourist rentals
    # (held separately in `seasonal_share`). Sets the zone's initial vacant pool, of which
    # `withheld_share` is off-market. Derived from the INE Censo-2021 empty-dwelling ladder by
    # municipality size — empty as a share of the local park: ≤5k hab 24.6%, 5–10k 17.8%,
    # 10–20k 15.6%, 20–40k 13.1%, 40–150k ≈11.5%, 150–500k ≈8%, 500k–1M 7.0%, >3M 6.3%
    # (national 13.2% of a 24.96M park) [INE Censo 2021 / viviendas por intensidad de uso,
    # via Funcas Estudios 104 ch.1 cuadro 1 — medium]. Zones map to municipality-size bands:
    # tensioned ≈ >300k, secondary ≈ 20k–300k, rural ≈ <20k, so upH = 1/(1−empty share).
    # The ORDERING (rural ≫ secondary > tensioned) is the sourced claim and the reason this
    # is per-zone at all: half the Spanish empty stock sits in municipalities under 20k
    # inhabitants holding 28% of the population, i.e. vacancy is where demand is not.
    units_per_household: float = 1.07
    # share of the zone's initial vacant pool that is WITHHELD — off the market, so no
    # landlord can let it: second homes, strategic holdouts, and above all stock that is
    # empty because it is in the wrong place and in the wrong condition. Funcas 104 ch.1 is
    # explicit that the Spanish empty stock "can hardly serve as an umbrella" for unmet
    # demand: provinces growing slower than the 3.1% national household rate hold >60% of it
    # while the fastest-growing (>4.7%) hold 5%, and much of it needs substantial
    # rehabilitation [INE/Funcas 104 ch.1 — the GRADIENT is sourced, the levels are a guess].
    # Without the gradient the model lets rural vacancy absorb latent demand (measured:
    # seeker share 6.2% → 5.2%), i.e. it reproduces the umbrella the source rules out.
    #
    # LEVELS ARE CALIBRATED, and deliberately so: they hold the *mobilisable* vacant stock,
    # (upH − 1) × (1 − withheld_share), at the 0.0455 per household that was already
    # calibrated against the §9 moments before the empty stock was recognised zone by zone.
    # So recognising it changes what the model *counts*, not what the market can *use* —
    # which is precisely the source's claim. Solve (upH − 1)(1 − w) = 0.0455 per zone.
    withheld_share: float = 0.35
    # tourist-rental (VUT) stock at init, as a share of the zone's residential stock. Held
    # OUTSIDE `units_per_household`, which counts occupied plus empty dwellings only (INE
    # classifies tourist and second-home use as separate categories) — so these
    # are additional dwellings, and converting them back (tourist-restriction lever) genuinely
    # adds housing. Calibrated so the model's seasonal units re-inflate to the INE count:
    # 341,001 VUT in May 2026 (−10.7% y/y; 1.28% of INE's 26.6M total stock; 329,764 in
    # Nov 2025). The zone values weight to ≈173 model units ≈ 345k real. The tensioned value
    # sits below the central-Barcelona district figure of 2.8–2.9% of dwellings because the
    # zone is a metro mean, not a hotspot [INE Estadística experimental de viviendas
    # turísticas, 24 Jun 2026; tourist-rental-restriction §2 — medium. The dossier also records
    # hotspot census sections at 20–30%, which this abstraction cannot represent]
    seasonal_share: float = 0.0


@dataclass(frozen=True)
class PopulationConfig:
    """How many actors of each type exist, and how their attributes are distributed."""

    # 1:2,000 of 19.87M Spanish households (INE ECP 1 Jul 2026; +226k in 2025, +239k y/y)
    # [INE ECP, household-owner §1 — high]
    n_households: int = 10_000
    income_median: float = 36_100.0  # €/yr gross [EFF2024 — high]
    income_sigma: float = 0.70  # lognormal sigma, implies mean≈46.3k [EFF2024 — high]
    saving_rate: float = 0.13  # share of income saved /yr [INE CNTR 13–14% — low]
    owner_wealth_median: float = 60_000.0  # € liquid (excl. housing) [EFF2024-derived — medium]
    # € net wealth tenants [EFF 2022, household-tenant §6 — high]
    tenant_wealth_median: float = 2_200.0
    wealth_sigma: float = 1.2  # lognormal sigma of owner liquid wealth [guess]
    # fatter tail: aspiring buyers sit in the top decile of tenant wealth [EFF dispersion — guess]
    tenant_wealth_sigma: float = 1.8
    # new households/tick, model scale ≈240k/yr real; range 135k–260k [EPA/INE — high as range]
    formation_per_tick: int = 30
    dissolution_rate: float = 0.35  # exits as share of formation [guess]
    # NON-RESIDENT cash buyers, share of purchases. All foreigners incl. residents run
    # .160 (Registradores 2026Q2, series record, foreigners +11% y/y while nationals fell)
    # to .184 (Notariado 2S 2025); non-residents are ≈44% of that ⇒ ≈.08, and the model's
    # overlay is non-resident only [Registradores ERI 2026Q2; Notariado CIEN — high as range;
    # emergent share reported as `foreign_purchase_share` in metrics.py]
    foreign_purchase_share: float = 0.08
    # EXOGENOUS non-resident arrivals per tick, model scale (model-spec §7.4, phase B).
    #
    # The stream used to be `foreign_purchase_share × recent Spanish sales`, which made an
    # exogenous demand source a FUNCTION OF THE MARKET IT BUYS INTO: a domestic slump cut
    # foreign arrivals mechanically, and the 8% share could never be wrong because it was an
    # input. Spec §2, finding 5.
    #
    # A constant stream makes the share an OUTPUT — it now rises when domestic volume falls,
    # which is what actually happened in Spain (2026Q2: foreigners +11% y/y *while* nationals
    # fell, Registradores ERI). `foreign_purchase_share` above is retained as the TARGET that
    # emergent share is judged against, not as the thing that produces it.
    #
    # Exogeneity is already declared: model-spec §14 places foreign origin-country conditions
    # outside the model, and arrivals are driven by them. This makes an existing exogenous flow
    # explicit rather than widening the boundary.
    #
    # Level set so the baseline emergent share reproduces the observed ≈8% of purchases at
    # baseline volume. [Registradores ERI / Notariado CIEN — high as a share; the constancy is
    # an assumption, and the falsification test is whether the real series co-moves one-for-one
    # with Spanish transaction volume]
    foreign_arrivals_per_tick: float = 7.7
    # Nominal growth of the non-resident buyer's budget, per TICK. SOURCED 2026-09-14: the
    # €/m² a non-resident actually paid grew **+5.86%/yr over 2014H1–2025H2** [Consejo General
    # del Notariado, CIEN anexo Tabla 1C, row Extranjero→No residente, 38 semi-annual points].
    # 0.0143/tick compounds to that.
    #
    # WHY IT IS NOT THE MODEL'S 2%/yr NOMINAL ANCHOR, which is what it was until today. That
    # anchor is Spanish CPI to within 0.1 pp (+2.09%/yr on the same window), so a budget
    # growing at it is **flat in real terms by construction**, while the observed non-resident
    # buyer ran +3.69%/yr REAL. Over the 11.5-year window that is a factor of 1.53 — the order
    # of the gap between the model's 2.28% emergent non-resident share and the observed ≈8%.
    # The failure was in the growth rate of the budget, not in the arrival rate and not in the
    # premium level.
    #
    # CALIBRATION WINDOW ONLY. The full-window CAGR is +2.16%/yr, close enough to 2% that it is
    # presumably where the old anchor came from — but it differs from this figure by 2.7×
    # *because it contains the bust*, so adopting it would import sealed 2007–2013 hold-out
    # information into a calibrated parameter. The series is also not monotone (−32.3% drawdown
    # 08H1→13H1), so no constant-growth anchor is right in both directions and this one is
    # explicitly a calibration-window object.
    #
    # CAVEAT, and it is why the §7.4 xfail is narrowed rather than closed: this is what
    # non-residents paid **in Spain**, so it embeds Spanish market conditions. It is a large
    # improvement on anchoring to `ZoneState.price_index` — it is a price they pay, not an
    # index their purchases set — but it is a HYBRID, not the origin-country income/wealth
    # index §7.4 specifies. That index is not retrieved.
    foreign_budget_growth: float = 0.0143
    # × zone median value; non-res pay +76–79% €/m² [Notariado CIEN — high]
    foreign_budget_multiplier: float = 1.6
    tenant_move_prob: float = 0.06  # /tick; range 0.04–0.08 [derived, household-tenant §6 — low]
    owner_move_prob: float = 0.011  # /tick; range 0.010–0.0125 [CED/BdE — medium]
    # min of accepted rent/income screening [household-tenant §6 — medium]
    max_rent_burden_lo: float = 0.30
    # max of accepted rent/income screening [household-tenant §6 — medium]
    max_rent_burden_hi: float = 0.40
    # /tick, prob a constraint-passing tenant/seeker tries to buy; the credit screen does the
    # rationing [guess; calibrated — 0.64 of a searched 0.35–0.65 at the phase-G refit, which
    # is the top of its range and is declared as such: it carries transaction volume, and the
    # phase-G block clears fewer sales per tick than the one it replaced]
    buy_attempt_prob: float = 0.64
    # € initial wealth of new households incl. family transfers (30–40% of FTBs get help,
    # household-owner §6) [guess]
    seeker_wealth_median: float = 15_000.0
    # new households' income vs population median: <1 = young penalty (EFF <35: 32k vs
    # 36.1k ⇒ ~0.89); boom scenarios with working-age migration use 1.0 [EFF2024 — medium]
    formation_income_factor: float = 0.9
    # where new households form, as zone weights (T/S/R); None = the zones' household shares
    # (0.45/0.35/0.20). Spanish household growth is metro-concentrated: Madrid and Barcelona
    # provinces added ≈+43k and +18k households in the 12 months to Sep 2025 against ≈226k
    # nationally (27% in two metros), with Valencia, Málaga, Alicante and Baleares next — the
    # coastal and metro areas the TENSIONED zone stands for [EC Country Report Spain 2026 Annex
    # 16; INE ECP — medium on the direction, guess on the level]. 0.55 is the value at which
    # the tensioned rental queue runs at ≈1 applicant per listing instead of 0.5, which is
    # what lets a rent cap's withdrawals reduce contracts (docs/validation.md, tensioned-
    # tightness revision: screened 0.45/0.50/0.55/0.60/0.65 on 3 seeds). S/R keep their
    # relative shares.
    formation_zone_weights: tuple[float, float, float] | None = (0.55, 0.286, 0.164)


@dataclass(frozen=True)
class MigrationConfig:
    """Interior migration between zones (model-spec §7.5).

    Replaces a downward-only coin flip. The old rule moved a priced-out SEEKER one step down
    the ladder at 10%/tick and could produce metro→rural and nothing else, so its sign was an
    artefact of its construction rather than a result, and no policy could move it.

    The new rule is a comparison, so both directions are reachable and the sign is an OUTCOME:
    a household weighs what it would earn in another zone against what housing costs there,
    net of a move friction. Metro→rural falls out when the rent gap dominates the income gap,
    which is what Spain's interior flows do — and rural→metro falls out for households whose
    income gain clears it, which is what they did before 2017 and what a policy that cut metro
    housing costs would restore.

    IDENTIFICATION. Interior net flows by municipality-size band, INE EVR microdata 2015–2021
    and EMCR table 69753 2021–2024, aggregated on the declared mapping B (model-spec §13.8:
    tensioned = provincial capitals + non-capital municipalities above 100,000). Persons:

        zone         2015      2017      2019      2020      2021
        TENSIONED  +14,911    -3,911   -33,393  -140,179   -90,777
        SECONDARY  +11,256    +8,181   +10,456   +12,043   +20,484
        RURAL      -26,167    -4,270   +22,937  +128,136   +70,293

    The 2020 reversal identifies the responsiveness without a volume confound: the metro
    outflow is 4.2× its 2019 value while GROSS interior flows FELL 7.9% (1,649,351 → 1,519,606),
    so it is redirection of a shrinking flow, not a surge.

    NOT SOURCED, and declared: migration statistics count PERSONS and this model moves
    HOUSEHOLDS. No published Spanish series gives interior migration on a household basis, so
    the levels below are fitted to reproduce the observed net DIRECTION and relative magnitude
    by zone, not a persons-per-household conversion. Any claim about migration *volumes* is
    therefore out of scope; direction and response are what this rule supports.
    """

    # Per-tick probability a household even considers moving zone. A move is then made only
    # if the comparison clears the friction, so this is an attention rate, not a move rate.
    # [guess — the observed flows identify the net response, not the consideration rate]
    consideration_rate: float = 0.08
    consideration_rate_range: tuple[float, float] = (0.04, 0.15)

    # Move friction as a share of annual household income: search, deposit, removal, and the
    # social cost of leaving. Sets how large a gain must be before anyone moves, so it is what
    # keeps gross flows finite. [guess]
    move_cost_share: float = 0.35
    move_cost_share_range: tuple[float, float] = (0.15, 0.60)

    # Scales how sharply the move probability responds once a gain clears the friction. THE
    # parameter the 2020 episode identifies: a shock that widens the metro rent gap has to
    # amplify the outflow ≈4× without gross flows rising. [fitted to the 2020 reversal]
    responsiveness: float = 1.8
    responsiveness_range: tuple[float, float] = (0.8, 3.0)

    # An OWNER faces transaction costs a renter does not (ITP/notary on the way in, agency and
    # timing on the way out), so owners move an order of magnitude less. The model already
    # carries this for within-zone moves as `owner_move_prob` 0.011 against
    # `tenant_move_prob` 0.06 [CED/BdE — medium]; this is the same ratio applied to the zone
    # decision, not a second estimate of it.
    owner_friction_multiplier: float = 5.5


@dataclass(frozen=True)
class StockConfig:
    """The initial housing stock: how many units, of what quality, where, owned by whom."""

    # NATIONAL ANCHOR for dwellings per household, excl. tourist rentals. The value the
    # engine applies is per-zone (`ZoneConfig.units_per_household`), because the empty stock
    # is not spread evenly — this field is the household-share-weighted mean those zone values
    # must reproduce, asserted in tests/test_validation.py. 1.12 ≈ weighted mean of the
    # INE-derived zone ladder (1.075 / 1.124 / 1.242); the empty-only national basis is
    # 1 + 3.29M empty / 18.9M households = 1.174 [INE Censo 2021 via Funcas 104 ch.1 — medium].
    # Vacancy itself stays emergent, validated against the 6–9% urban Censo figure in the
    # tensioned zone and against the rural ≫ urban ordering [INE via investor-small §6].
    units_per_household: float = 1.12
    median_value: float = 170_000.0  # € national median main residence [EFF2024 — high]
    # m² average dwelling. Used as the developer's build size, so it scales hard cost per
    # dwelling: 90 m² × 1,105–1,323 €/m² ⇒ ≈100–130k € of hard cost [Afi's national average
    # dwelling size, Funcas Estudios 104 ch.5 gráfico 4 note — medium; was an 80 m² guess].
    # Consequence measured, docs/validation.md: rural new build (0.5 × 170,000 = 944 €/m²)
    # falls below the sourced hard-cost floor of 1,080 €/m², so the rural zone only builds
    # once prices have risen ≈15% — which is realistic, and tightens the zone price ladder.
    avg_size_m2: float = 90.0
    # individuals' share of rental stock; range .85–.92 [investor-small §1 — high].
    # NOT an input: it is an emergent cross-check, reported as `small_landlord_rental_share`
    # in metrics.py and asserted in tests/test_validation.py.
    small_landlord_share_target: tuple[float, float] = (0.85, 0.92)
    # public social rental as a share of the TOTAL stock (318k of 18.54M dwellings = 1.7%);
    # range .015–.025 [Housing Europe 2025 / MIVAU Boletín, public-housing §3 — medium].
    # Basis matters: the engine converts this to a share of *rented* units at init.
    public_rental_share: float = 0.017
    # metro concentration of the public stock at init (T/S/R) — social housing is urban
    # [public-housing §3 — guess; mirrors the policy lever's delivery weights]
    public_zone_weights: tuple[float, float, float] = (0.6, 0.3, 0.1)


@dataclass(frozen=True)
class MarketConfig:
    """Rules of exchange: search frictions, listing duration, transaction costs, stickiness."""

    # /tick ask cut while unsold; range .02–.05 [sticky-ask evidence 2008–13 — guess]
    ask_decay: float = 0.03
    # --- §5c sale-side price formation (phase D, 2026-09-14) ------------------------------
    # The floor leg of the seller's reserve: how far below the ask an owner will go before
    # refusing. SOURCED as of phase D, where it used to be a bare guess: the Cátedra
    # Tecnocasa-UPF measures the discount between asking and sale price at **6.2% on average**
    # (2S 2025, "very similar to 2007"), and Fotocasa's buyer survey gives the distribution
    # behind it — 53% of buyers negotiate, 80% of those obtain something, and only 23% get
    # more than 10% off. Hence 0.04–0.12 rather than the old U(0.05, 0.15)
    # [Cátedra Tecnocasa-UPF XLII; Fotocasa Experiencia en compraventa 2024 — medium]
    max_seller_discount_lo: float = 0.04
    max_seller_discount_hi: float = 0.12
    max_listing_ticks: int = 6  # withdraw after; range 4–8 [guess]
    # DEMOTED in phase D (model-spec §5c.1). It used to be dispersion around the *ask* and,
    # through that, the thing that set the price: Sobol put 56% of the variance in
    # price-to-income on it. It is now idiosyncratic TASTE — how much this buyer happens to
    # like this dwelling — applied to the value they put on it, which is a real friction that
    # cannot set the level on its own. Whether it stays under the 25% variance threshold is
    # phase E's Sobol question [guess; range 0.02–0.06]
    # MEASURED as of phase G (2026-09-15), where it was a guess: the idiosyncratic
    # per-sale dispersion of log sale prices is 6–17% [Kotova & Zhang, US zipcodes
    # 2012–16, house fixed effects, mean 16.8%; Giacoletti RFS 2021, 6.8–12.4%;
    # Landvoigt-Piazzesi-Schneider AER 2015, 6.2–9.8% — the last two published as
    # RETURN dispersions, which carry the error twice]. No Spanish estimate is
    # published; the absence is a registered row in docs/sources.md. This parameter is
    # the taste sd that DELIVERS that dispersion once the auction, the budget cap and
    # the ask have had their say — 0.20 gives 8.0% against the sourced band (§9 target
    # 16). It no longer moves the price level: §5c.6 separated the two
    overbid_sigma: float = 0.20
    # --- §5c.7 market tightness in the bid (phase G, 2026-09-15) ---------------------------
    # Buyers per listing at which a buyer bids HALFWAY between what the dwelling is worth to
    # an average buyer and the most its credit line allows. The mechanism is the option value
    # of carrying on searching: in a slack market losing an auction costs a week, so nobody
    # stretches; in a tight one losing costs a year, so buyers bid toward their limit and the
    # market clears against the BUDGET distribution — which is income and credit, both
    # sourced, rather than a taste draw. Phase G exists because the channel that used to do
    # this was the taste order statistic being capitalised into the anchor (§5c.6): with the
    # anchor fixed, halving construction moved price growth by 0.18pp/yr where the old model
    # moved it by 2.0pp. REDUCED FORM, identified on the 2014–25 price-income wedge and on
    # the cross-zone price ratio (fitted 2026-09-15: 400 against a searched 4–1400, and
    # re-fitted from 260 when §5c.8 made clearing sequential, so the
    # stretch is small per tick — ≈5% of the gap to the credit limit at the model's own
    # buyers-per-listing — and works by compounding into the anchor, bounded by budgets)
    tightness_half_saturation: float = 400.0
    # How many affordable listings a buyer actually looks at before bidding. Reduced form,
    # identified against two observables the model did not use before: the days-on-market
    # distribution [idealista/data 2T 2026 — 26% inside a month, 53% inside a quarter, 89%
    # inside a year] and bidders per dwelling [Tecnocasa: seven interested parties, double
    # two years earlier]. m = 1 is the pre-phase-D model, and it produced bidding wars for
    # the wrong reason: buyers did not look [range 1–10]
    # Phase G refit: 1. Phase D set this to 2 arguing that m = 1 "produced bidding wars for
    # the wrong reason: buyers did not look". Under the taste-neutral anchor the opposite
    # holds — m = 2 concentrates bids on the same well-priced listings and pushes sales above
    # the ask to 31–39% against 20% at m = 1, while costing price-to-income (8.9 vs 8.1). The
    # two observables m was identified on still pass at m = 1 (3.4 bids per listing against
    # Tecnocasa's ≤7; 46% sold inside the quarter against idealista's 43–63%)
    search_listings: int = 1
    # Sub-periods a tick clears in (model-spec §5c.8). The tick is a quarter and the market is
    # not: offers arrive month by month and the seller answers what is in front of it [Merlo &
    # Ortalo-Magné 2004; Merlo, Ortalo-Magné & Rust, 780 English properties with complete offer
    # histories]. Three is the calendar, not a fitted number — clearing the whole quarter at
    # once made every listing a simultaneous auction, and the negotiation margin came out a
    # third of the measured one
    subperiods_per_tick: int = 3
    search_listings_range: tuple[int, int] = (1, 10)
    # What an ordinary seller posts ABOVE what it expects to get. Spanish sellers build the
    # negotiation margin into the ask — the practitioner rule of thumb is 15–20% over the
    # expected price, and the REALISED gap between asking and sale price is 6.2% on average
    # [Cátedra Tecnocasa-UPF 2S 2025; Fotocasa 2024]. The model posts the smaller, measured
    # number: the markup is the posting convention, and the discount that comes out of it is
    # an OUTCOME of competition, not an input — high in a slack market, negative (sales above
    # ask) when several buyers converge on one listing.
    #
    # **SOURCED BAND 0.06–0.13 per dwelling (2026-09-15)**, where the row used to read
    # "[guess]" for the size: the distance from a listing's own initial ask to its own sale
    # price is the 6.2% negotiation margin at the point of sale [Cátedra Tecnocasa-UPF, 2S
    # 2025] plus the in-listing cuts, which idealista measures separately — 14% of live
    # listings cut in 2026Q1, by 7% of the initial ask — so a dwelling never revised closes
    # 6.2% below its ask and one revised once closes ≈13% below. Phase G's refit put this at
    # the TOP of the band, which is where the mechanism says it belongs: with the taste-
    # neutral anchor (§5c.6) the posted markup has to cover the selection premium as well as
    # the negotiation margin, and the 15–20% practitioner rule of thumb is the same statement
    # from the seller's side.
    #
    # **The markup is cyclical and this one is not.** The same quantity was **27%** in
    # October 2012, with 78% of unsold sellers having already cut 25% [Fotocasa seller
    # survey]. A constant markup therefore understates asks in a bust, which is the same gap
    # §5d.1's loss aversion is trying to cover from the other side.
    #
    # The aggregate portal-to-notary gap (8–12% in 2021 → 32–44% in 2025, UVE Valoraciones)
    # measures the stock on offer against what sold. It is composition, not this parameter,
    # and is registered as a contrast rather than used.
    ask_markup: float = 0.125
    # --- §5d.1 nominal loss aversion (2026-09-15) -----------------------------------------
    # A seller facing a nominal loss asks for a fraction of that loss back. MEASURED, and by
    # the canonical study: Genesove & Mayer (QJE 2001) find asking prices 25–35% of the gap
    # between expected sale price and original purchase price higher, realised prices 3–18%
    # of it higher, and a much lower sale hazard — with the list-price effect **twice as
    # large for owner-occupants as for investors**, which is why there are two values here.
    #
    # It is INERT in a rising market: with the dwelling worth more than it cost, the loss is
    # zero and the ask is unchanged. That is what makes it safe to add after a calibration
    # done on a rising window — and it is checked rather than assumed (docs/validation.md).
    # THE REALISED-PRICE LEG (added 2026-09-15). Genesove & Mayer measure TWO effects and the
    # model carried only one: asking prices 25–35% of the nominal loss higher, and **realised
    # prices 3–18% of it higher**. Carrying only the ask made loss aversion inert on price once
    # §5c.6 moved the bargaining weight to 0.25 — a one-bidder sale prices near the reserve, so
    # a higher ask withheld the dwelling without holding the price up, and the brakes deepened
    # a bust instead of cushioning it. The reserve now carries this leg [QJE 2001, central 0.10
    # of a measured 0.03–0.18]
    loss_aversion_reserve: float = 0.10
    loss_aversion_reserve_range: tuple[float, float] = (0.03, 0.18)
    loss_aversion_owner: float = 0.30
    loss_aversion_owner_range: tuple[float, float] = (0.25, 0.35)
    loss_aversion_investor: float = 0.15
    # Ascending-auction increment, as a fraction of the runner-up's bid: what it takes to
    # outbid them. Institutional minimum, not a behavioural parameter [guess; range .002–.01]
    auction_increment: float = 0.005
    # Seller's share of the surplus when there is only ONE bidder and the price is a bilateral
    # negotiation rather than an auction. The block's one free parameter, declared reduced
    # form and calibrated so the realised discount reproduces the measured 6.2% mean; the
    # SHAPE of the discount distribution is then a prediction, not an input.
    #
    # Phase G (2026-09-15) moved it 0.85 → 0.25, and the arithmetic says why it had to. With
    # the reserve floored at ask × (1 − d), d ∈ 0.04–0.12, a one-bidder price θ of the way
    # from reserve to ask gives a discount of (1 − θ)·d ≈ 2.2% at θ = 0.85 — the model could
    # not reach the sourced 6.2% at any markup, and the old value was reproducing the ask, not
    # the negotiation. It is identified on the discount and nothing else
    seller_bargaining_power: float = 0.25
    # Selling costs the seller must cover out of the price before the loan is repaid — the
    # reserve's debt leg is debt + this. SOURCED 2026-09-16 (model-spec §7.2), two institutional
    # viewpoints, because §7.2 makes this the rent cap's EXIT THRESHOLD and an exit threshold
    # cannot be a guess.
    #
    # STATUTORY LEG. Código Civil art. 1455: the seller pays the `escritura matriz`, the buyer the
    # first authorised copy and everything after — "salvo pacto en contrario", and the pacto in
    # practice shifts more onto the buyer, so this is the seller's FLOOR. IIVTNU (TRLRHL arts.
    # 104–110): the transmitente is the taxpayer, levied on the cadastral LAND value rather than
    # the price, which is why it is small as a share of price. Aranceles RD 1426/1989 (notarial)
    # and RD 1427/1989 (registry). Energy certificate and cédula are de minimis.
    #   => self-sold, no agency: 0.005–0.015 of price.
    #
    # MARKET LEG. Agency commission 3–5% + IVA; at 21% IVA a 4% fee costs 4.84% of price. Large
    # networks 5–7%, small agencies 1–4%.
    #   => agency sale: 0.04–0.07 of price.
    #
    # WHICH ROUTE, and this is what fixes the point value rather than only the band: agencies
    # intermediate **64% of second-hand purchases** [Fotocasa Research] and ~70% of all operations
    # [idealista] — two portals, independently collected, agreeing within 6pp while competing for
    # the same sellers. At a 0.66 weight:
    #   0.66 * 0.055 + 0.34 * 0.010 = 0.040.
    #
    # EXCLUDED DELIBERATELY: IRPF on the realised gain (19–28% OF THE GAIN, not of the price). It
    # is a real cost of exiting, but §7.2's `r_req` already nets E[g] and the model carries no
    # per-unit gain basis, so pricing it here would double-count appreciation or invent a basis.
    # Same discipline by which `landlord_cost_share` excludes vacancy.
    #
    # THE SOURCED VALUE IS 0.040 AND THIS SHIPS 0.02 — deliberately, and not for long. Measured
    # on 2026-09-16, moving it to 0.040 fixes one registered strict xfail and breaks two targets
    # in channels that have nothing to do with the rent cap:
    #   XPASS   test_non_resident_surcharge_removes_foreign_purchases  (restored)
    #   FAIL    test_rate_shock_cuts_transactions_before_prices        (regression)
    #   FAIL    test_forbearance_raises_the_arrears_stock_and_lowers_the_flow (regression)
    # The mechanism is `market/clearing.py`'s reserve floor, max(debt*(1+k), ask*(1-discount)):
    # raising k lifts the floor for every INDEBTED seller and suppresses sales. This parameter was
    # a [guess] co-calibrated with other guesses, and sourcing it alone breaks that joint.
    # Shipping the change belongs on its own branch with its own write-up of those three channels,
    # so that §7.2's own falsifications (F1–F3) stay attributable to the MECHANISM rather than to
    # a parameter that moved underneath them. The BAND below is sourced and is swept; only the
    # point value waits.
    selling_cost_share: float = 0.02
    # The sourced band, spanning the two real sale routes — NOT an error margin.
    selling_cost_share_range: tuple[float, float] = (0.01, 0.07)
    # λ, weight on trailing growth; range 0.5–0.9 [household-owner §6 — low; THE cycle knob]
    expectation_momentum: float = 0.7
    long_run_growth: float = 0.005  # /tick nominal anchor ≈2%/yr [exogenous income growth]
    # The §7.2b G4 comparison grid (model-spec §7.2b, Falsification): the four anchors the
    # ten-seed rent-cap sweep in docs/validation.md re-runs `long_run_growth` at, spanning the
    # pre-§7.2b regime boundary the sweep found between 4%/yr (0/10 seeds correctly signed) and
    # 6%/yr (9/10) — 1%, 2%, 4%/yr sit inside the old 0/10 band, 8%/yr was already 10/10. A
    # config field rather than a literal in the test, so the grid is declared once and the test
    # reads it rather than retyping it (the same discipline `intermediation_share_regional_range`
    # is read from, not hardcoded, in G2).
    long_run_growth_sweep: tuple[float, float, float, float] = (0.0025, 0.0050, 0.0100, 0.0200)
    # Weight of this tick's median transaction in the index update. **MEASURED 2026-09-15**,
    # where it was a bare guess, and it is the second-largest term in the price level's
    # variance (Sobol ST 0.26). The observable: the price signal Spanish buyers, sellers and
    # lenders actually see is an APPRAISAL, built from recent comparables, so it tracks
    # transacted prices with a lag. Regressing
    #     dlog(valor tasado) = s · dlog(IPV) + (1 − s) · dlog(valor tasado[−1])
    # gives s = **0.307** (se 0.104) on 2014Q1–2026Q1 and **0.287** (se 0.065) on 2007–2026;
    # the lag leg implies a slower 0.48–0.51, so the sourced range is **0.29–0.51** and this
    # value sits at its lower edge. The 2014–2019 subsample shows no persistence at all
    # (s ≈ 1) — the smoothing is state-dependent, recorded rather than averaged away
    # [INE IPV table 80270 via the INE API; MIVAU Estadística de Valor Tasado, table 1]
    price_index_smoothing: float = 0.3
    # notary/registry etc., fraction of price, on top of ITP [Fotocasa triangulated — high]
    buyer_fees: float = 0.02
    # required gross yield over bond in the tensioned zone — observed spread there is
    # --- §7.1 total-return hurdle (phase B, 2026-09-14) -----------------------------------
    # The landlord's required RENT yield is what is left of a required TOTAL return once
    # expected appreciation is taken out, grossed up for the costs that never reach the
    # landlord's pocket:
    #
    #     r_req = V · (i_bond + π − E[g]) / (12 · (1 − c))
    #
    # This is what makes the rental yield an OUTPUT. The old form pinned it: required yield =
    # bond + a spread fitted to the observed ladder, so the model could only ever reproduce
    # the yield it was given (spec §2, finding 3). Its own comment conceded the mechanism —
    # "appreciation expectations substitute for yield" — without implementing it.
    #
    # π is split because only one half of it is measured, and fusing them would hide that.
    #
    # MEASURED. Prime residential yield against the sovereign: CBRE Q1-2026 Madrid 3.8% /
    # Barcelona 4.0% against BdE's 10-year bond at 3.546% (Mar 2026, series `D_G0B1F0ZP`)
    # ⇒ ≈ +25bp / +45bp. A point, not a series — no free historical prime-yield series exists
    # (HTTP 403 on cbre.es and en.savills.es), so π is a constant with a zone gradient and
    # NOT a cyclical term. Claiming a cyclical π would be claiming a series nobody publishes.
    prime_risk_spread: float = 0.0035
    # PARTIALLY DERIVED as of 2026-09-15 (model-spec §7.1b), and still the most expensive
    # parameter in the model: Sobol puts 0.65 of the rent level, 0.75 of tensioned market
    # vacancy and 0.62 of overburden on it. Its components price at 0.5–1.2pp — tenant default
    # at the rent-default insurance price (3–5% of rent), illiquidity over the 15-year-256-day
    # average holding period [Registradores ERI 2020], and undiversified idiosyncratic price
    # risk from the §9 target-16 dispersion band — against the 3.0pp the model needs. Below
    # ≈2.5pp the insider/outsider wedge inverts and the boom stops compressing the yield. The
    # residual, 1.8–2.5pp, is declared unexplained; candidates are regulatory risk after Ley
    # 12/2023, the occupation tail and management time (which may already be inside
    # `landlord_cost_share`). Until one of them is priced this stays unsourced for §13.2.
    #
    # Previously: FITTED, and the one free parameter of §7.1 — declared rather than
    # buried. What a small
    # Spanish landlord demands over an institution holding prime multifamily: illiquidity, no
    # diversification across tenants, and the eviction timeline. There is no independent
    # estimate of it; the old `landlord_required_spread = 0.02` was the observed yield minus
    # the bond, which is the quantity the hurdle is supposed to PREDICT, so reusing it would
    # re-pin the yield under a new name. Identified instead by target 10: with E[g] in the
    # formula the boom must compress the yield, and the size of that compression constrains
    # this in a way a level fit cannot.
    small_landlord_premium: float = 0.030
    small_landlord_premium_range: tuple[float, float] = (0.020, 0.030)
    # Operating costs as a share of gross rent, PRE-TAX, VACANCY EXCLUDED. Central 0.22 of a
    # sourced 0.20–0.24 [AEAT cuenta de resultados del arrendamiento, FY2019–FY2024, selector
    # `Vivienda habitual = Sí`]. Inside: comunidad, IBI, insurance, maintenance, management.
    #
    # NOT `1 − net/gross`, which is 41–45%: 15–18pp of that is the statutory 3%/yr building
    # depreciation (art. 23.1.b LIRPF) and 1.4–4.2pp is mortgage interest. Both must stay out
    # — depreciation double-counts E[g], interest double-counts the financing leg of
    # `i_bond + π`.
    #
    # VACANCY IS EXCLUDED ON PURPOSE. AEAT's unit is the *vivienda equivalente* = ownership
    # share × days in that use, so both sides are per euro actually received. The model
    # already generates vacancy in `market/clearing.py`; folding the sourced 0.24–0.30
    # vacancy-inclusive figure in here would charge it twice. The same source measures the
    # missing piece if it is ever wanted explicitly: *días de alquiler medios* 347/365 (2024),
    # Barcelona 352 / Madrid 351 / Teruel 339 / Extremadura 338.
    #
    # NO ZONE GRADIENT, deliberately, and this is counter-intuitive: `c` falls with rent
    # level, not with urbanity. Madrid sits near the TOP of the CCAA spread (26.3%, on a
    # 10.95% comunidad charge) and Balears at the bottom (18.8%). The legitimate zone
    # difference is in vacancy, not in cost.
    #
    # SECOND SOURCE, 2026-09-16 (model-spec §13.7). Until today every quantified figure for
    # this traced back to AEAT — BdE DO 2432 cites AEAT, the Informe Anual cites DO 2432 — so
    # it rested on ONE institutional source against this project's ≥2 rule. INE's national
    # accounts now supply the second: CNE table 69069 publishes branch `68a alquileres
    # imputados` on its own, and its cost side is EPF-built (COICOP 04.3.3 plus insurer
    # payouts), not IRPF-built [INE, Inventario de fuentes y métodos de la RNB rev. 2024,
    # §§3.18.2 and 3.18.5]. Adding IBI back — ESA books it as D.29, not as intermediate
    # consumption — gives (CI + D.29)/output = 10.9% (2023) and 15.3–18.0% across 2013–22.
    #
    # That is a LOWER BOUND on `c`, not a rival estimate: national-accounts IC carries only the
    # repair-and-renovation slice of a comunidad quota and no management or letting cost, both
    # of which are inside AEAT's deductible rows. ≈16% vs 22% is the size of those two items,
    # and the sign is right. The shipped 0.22 is NOT moved by this.
    #
    # What the series does dispute is that `c` is a CONSTANT: it falls monotonically from ≈31%
    # (1997–99) to ≈16% (2016–22) — the denominator tracks rents, maintenance spending does
    # not — and 2023's 10.9% is a level break from the 2024 statistical revision. A constant
    # here is calibrated to the recent end of a falling trend. Declared, not hidden.
    #
    # STILL UNRESOLVED, recorded rather than closed: DO 2432 states 2pp off a ~5.5% RBA ⇒
    # ≈36% of gross rent, which disagrees with AEAT's own 41–45% on the same object while
    # citing it. Neither figure IS `c` — both carry depreciation and interest.
    landlord_cost_share: float = 0.22
    landlord_cost_share_range: tuple[float, float] = (0.20, 0.24)
    # Floor on the required rent YIELD once appreciation is netted off. Without it a boom in
    # which E[g] exceeds i_bond + π drives the required rent to zero and then negative: real
    # in the sense that people do buy for capital gain alone, nonsense as a rent. [guess]
    min_required_yield: float = 0.005
    # extra spread outside tensioned metros, range .01–.02: reproduces the observed
    # 5.2 / 7.0 / 8.0 zone yield ladder [BdE RBA gradient — medium]
    landlord_zone_risk_premium: float = 0.015
    # RETIRED (2026-09-16). Was Δln offered/Δln regulated rent, RANGE 0.0–2.0 — the
    # three-Catalonia-studies parameter [rent-cap §4 — high as range]. The arbitrage condition
    # of model-spec §7.2 makes the supply response an OUTPUT of `selling_cost_share` (above)
    # and `holding_years` (CapResponseConfig) rather than an input anyone dials; the disputed
    # range moved to those two structural parameters' own ranges. Kept as a dated note rather
    # than deleted outright: this project keeps the archaeology of its parameters. See
    # model-spec.md §7.2, "Parameter ledger".
    # share of capped new contracts diverted; range .05–.25 [Incasòl — medium]
    seasonal_evasion_share: float = 0.15
    default_rate: float = 0.05  # actual tenant non-payment /yr; range .03–.07 [Arag/OESA — medium]
    # landlord perceived over actual default; range 1.5–3 [guess]
    perceived_risk_markup: float = 2.0


@dataclass(frozen=True)
class CreditConfig:
    """Lending environment: base rate, LTV cap, DTI cap, term."""

    # /yr, 12m euríbor level [exogenous path via scenario]. The baseline is a 2015–2025-like
    # steady state, not a nowcast: the Aug-2026 monthly average was 2.954% (BOE 2 Sep 2026;
    # 3.1% daily on 7 Sep) with the ECB deposit rate at 2.25% and the BdE lending survey
    # reporting tighter standards — use `RateShock` for a 2026-like path.
    euribor: float = 0.022
    spread: float = 0.011  # pp over euríbor; range .009–.012 [bank §6 — medium]
    # per-tick partial adjustment of the offered rate toward euríbor+spread. Calibrated to
    # BdE DO 2312: ~32% of a shock passed through after 16 months (5.33 ticks), i.e.
    # 1−(1−p)^5.33 = 0.32 ⇒ p ≈ 0.07 [BdE DO 2312 — medium]
    pass_through: float = 0.07
    max_ltv: float = 0.80  # bank practice, no legal cap; 24% bunching at 0.80 [BdE IEF — high]
    max_dsti: float = 0.35  # payment/net income; range .30–.40 [bank §6 — high]
    term_years: int = 25  # avg 24–26 [INE — medium]
    # NOTE: the state-guarantee LTV boost is a *policy* field (PolicyConfig.guarantee_ltv_boost)
    # and reaches the lending caps as an explicit `ltv_boost` argument to bank.max_price /
    # bank.loan_terms. It is deliberately not duplicated here.


@dataclass(frozen=True)
class DeveloperConfig:
    """Supply side. The lag is what generates cycles — keep it explicit."""

    construction_lag: int = 8  # ticks, visado→CFO; range 6–10 [Euroval, developer §6 — high]
    # min expected margin on cost; range .15–.20 [IMPLICA/KPMG — medium]
    margin_threshold: float = 0.175
    # National long-run price elasticity of starts, d ln(starts)/d ln(price); range .45–.58+
    # [Caldera&Johansson/BdE — medium]. The elasticity the developer actually applies is
    # per-zone (ZoneConfig.supply_elasticity) because land availability differs; this field
    # is the national anchor those zone values must average to, asserted in
    # tests/test_validation.py. Not read by any agent.
    supply_elasticity: float = 0.5
    # national capacity ≈190k/yr real at model scale; range 150k–220k [CNC claim — low]
    max_starts_per_tick: int = 24
    base_starts_per_tick: int = 14  # ≈112k/yr real, 2024–25-like baseline flow [MIVAU — high]
    presale_share: float = 0.40  # pre-sales gate .30–.50 [developer §6 — high]
    new_build_premium: float = 1.15  # new-build price vs zone median [guess]
    # Units already under construction at tick 0, by arrival tick: `initial_pipeline[i]`
    # units complete at tick i+1, split across zones by household share. Empty in the
    # baseline, where the run starts from a steady state. It exists for the 2008-13
    # hold-out, whose defining initial condition is that Spain entered the bust with the
    # 2005-08 pipeline still delivering — completions were 563,631 in 2008 against 43,230
    # in 2013 [MIVAU tabla 3.2] — so a model that starts the episode with an empty
    # pipeline cannot produce the glut that followed.
    initial_pipeline: tuple[int, ...] = ()


@dataclass(frozen=True)
class PolicyConfig:
    """Active policy levers — the state the government actor enacts.

    Baseline = Spain without the tensioned-zone machinery switched on.
    Interventions (scenario.py) return modified copies. Ranges per docs/policies/*.md §5.
    """

    # rent cap (rent-cap.md)
    rent_cap_enabled: bool = False
    rent_cap_zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED,)
    cap_reference_discount: float = 0.05  # cap below prevailing market rent; range 0–.10
    # WHICH LAW. Ley 12/2023 (the default) binds the reference index on grandes tenedores
    # only; everyone else is capped at their own previous contract plus IRAV, and at
    # nothing when there is no contract in the last five years. Catalonia's Ley 11/2020,
    # which the three evaluation studies measure, bound the index on EVERY landlord —
    # so a run that reproduces Monràs and García-Montalvo must set this True
    cap_index_binds_all: bool = False
    cap_compliance: float = 0.85  # share of new contracts actually at/below cap; range .25–.95
    # share of the capped zone's units that sit inside a DECLARED tensioned municipality.
    # Distinct from compliance (whether a covered landlord obeys): the law is a CCAA switch
    # applied municipality by municipality, and the model's TENSIONED zone (45% of
    # households) is much bigger than Spain's declared map. As of the BOE resolution of
    # 29 Jul 2026 there are 317 declared municipalities in 5 CCAA (Cataluña 271, Euskadi 18,
    # Navarra 21, Galicia 2, Asturias 5) covering ≈9.3M people — 19% of Spain, i.e. ≈0.42 of
    # the model's tensioned zone; Cataluña alone (2024 declaration) covered ≈90% of Catalan
    # population, ≈1.0 of a Cataluña-shaped tensioned zone. 1.0 = the whole zone is declared
    # [BOE-A-2026-16532; MIVAU/Civio — docs/kb-refresh-2026-09.md §3 — high]
    cap_coverage: float = 1.0
    # /yr IRAV-style cap on sitting rents AND on the frozen reference index while a cap is
    # active. Calibrated RELATIVE to the model's nominal income anchor (`long_run_growth`,
    # 2%/yr), not in Spanish nominal terms: IRAV printed 2.20% (2025) and 2.44% (Jun 2026)
    # against nominal wage growth of ≈3–4%, i.e. ≈0.6–0.75 of income growth ⇒ 0.012–0.015 in
    # model units. The previous 0.025 (the nominal 2–3% range) sat ABOVE the anchor, so the
    # frozen reference outran the market it capped and the cap silently unbound within ~10
    # ticks (measured: capped tensioned listings 29 → 0 by tick 30 after a tick-20 cap, and
    # the magnet rule then pulled asks up, ending +0.9% above baseline instead of below it)
    # [INE IRAV via lexway/irav.es; Ley 12/2023; docs/kb-refresh-2026-09.md §1 — high on the
    # ratio, medium on the exact value]
    within_contract_update: float = 0.015
    seasonal_segment_capped: bool = False  # Jan-2026-style closure of the evasion segment
    # The tick the current cap term was declared, and its statutory length. ZMRT are declared
    # for THREE YEARS and renewable (MIVAU's compiled table gives vigencia inicio–fin for all
    # 317 municipalities), so a landlord's shortfall accrues over what is left of the current
    # term, not over a holding horizon. The statute renews — Catalonia extended 302
    # municipalities to 2027 — so the term resets rather than the cap lapsing, and the
    # landlord does NOT anticipate that renewal: model-spec §7.2b, and that is the friction.
    cap_start_tick: int = -1
    cap_term_ticks: int = 12
    # transaction tax (transaction-tax.md)
    itp_delta: float = 0.0  # pp change on zone ITP rate, every buyer
    itp_zones: tuple[ZoneType, ...] = (ZoneType.TENSIONED, ZoneType.SECONDARY, ZoneType.RURAL)
    # buyer-type surcharges ON TOP of the zone rate, as a fraction of price. Spain taxes by
    # buyer type in practice and the model's two aggregate buyers pay cash, so without these
    # the ITP lever only ever reached households:
    # - large investor / legal persons: Cataluña charges 20% TPO on whole-building
    #   acquisitions by any buyer and on gran-tenedor purchases (DL 5/2025, Ley 11/2026 in
    #   force 14 Jul 2026) against a 10% general rate ⇒ delta ≈ +0.10 [Tier 2 law-firm
    #   summaries of DOGC; docs/kb-refresh-2026-09.md §3 — medium]
    # - non-resident overlay: the "100% tax on non-EU buyers" bill (announced Jan 2025,
    #   stalled in Congress Mar 2026, folded into the stalled Jul 2026 omnibus decree) would
    #   be delta ≈ +0.90 over a 10% base; Baleares' non-resident purchase ban was rejected
    #   Feb 2026 [Reuters/US News; docs/kb-refresh-2026-09.md §3 — not law]
    # Both act as a price wedge on the buyer's budget: (1 + base) / (1 + base + delta).
    itp_investor_delta: float = 0.0
    itp_foreign_delta: float = 0.0
    # vacancy tax (vacancy-tax.md)
    vacancy_tax_rate: float = 0.0  # /yr fraction of unit value; range .001–.03
    vacancy_detection: float = 0.0  # /yr prob a liable vacant unit is billed; range 0–.9
    vacancy_min_portfolio: int = 4  # statutory scope [government §6]
    # public housing (public-housing.md)
    public_units_per_tick: int = 0  # started per tick, all zones pooled by zone weights
    public_zone_weights: tuple[float, float, float] = (0.6, 0.3, 0.1)  # T/S/R
    public_delivery_lag: int = 20  # ticks; range 12–32
    public_rent_discount: float = 0.5  # rent vs market; range .4–.7
    crowding_out_share: float = 0.33  # private starts displaced per public start; range 0–.8
    # tourist rental (tourist-rental-restriction.md)
    vut_phaseout_rate: float = 0.0  # /yr share of tourist units extinguished
    vut_conversion_share: float = 0.30  # returned to long-term market; range .10–.50
    # demand subsidy (demand-subsidy.md)
    guarantee_ltv_boost: float = 0.0  # extra LTV via state guarantee; ICO = .20
    guarantee_eligible_share: float = 0.0  # of first-time buyers; sweep .05–.50
    # € liquid-wealth ceiling for eligibility. The ICO line's 2026 addenda (BOE 2 Jul 2026)
    # extended formalisation to 31 Dec 2027 and added a €150k net-wealth cap on top of the
    # under-35 / ≤7.5×IPREM income filters. Applied to the household's liquid wealth, which
    # is what the model carries; `inf` = no cap [BOE-A-2026-14404 — high]
    guarantee_wealth_cap: float = float("inf")
    # total guarantee envelope at model scale: the ICO line is €2.5bn *once*, not per tick.
    # 2.5e9 / 2000 households-per-model-household [demand-subsidy §5 — high]
    guarantee_budget: float = 1_250_000.0
    rent_subsidy_month: float = 0.0  # €/month to eligible tenants
    rent_subsidy_eligible_share: float = 0.0  # of under-35 tenants; sweep .006–.20
    # land release (land-release.md)
    extra_land_units_per_tick: int = 0  # finalist-equivalent capacity added after lag
    land_release_lag: int = 40  # ticks; range 20–60
    permit_lag_delta: int = 0  # ticks off construction lag; range −6–0


@dataclass(frozen=True)
class CapResponseConfig:
    """How a small landlord reacts to a binding rent cap.

    This is behaviour — how the world works — not a lever. The cap's *level*, coverage and
    compliance are `PolicyConfig`; what a landlord does when one binds is here.

    Every field below was a module-level literal in `agents/landlord.py` until phase A
    (spec §2, finding 10: "the headline cap result rides on guessed constants"). None of them
    changed value in the move. They are here so that they can be swept: a constant that is not
    in `config.py` is unreachable by phase E's Morris/Sobol screening, and the variance rule of
    spec §3.2 cannot be applied to something it cannot vary.

    Read the `*_range` fields as the honest span of the evidence, not as error bars. Where the
    evidence is a guess, the range says how wide the guess is, and the bias-control rule then
    forbids reporting any magnitude the span dominates.
    """

    # RETIRED (2026-09-16). `exit_split_sale` (0.50), `exit_split_seasonal` (0.35),
    # `exit_split_vacant` (0.15), `exit_split_sale_range` ((0.35, 0.65)) and
    # `exit_split_evasion_base` (0.15) used to fix, as a proportional rescaling, where a
    # withdrawn unit went — [guess — open question investor-small §7.1. No Spanish study
    # decomposes withdrawals], a convention `docs/assumptions.md` itself called "a convention
    # with no episode behind it". §7.2's direct branches (`Landlord._exit_destination`) no
    # longer need a split to rescale: SEASONAL is a draw against
    # `MarketConfig.seasonal_evasion_share` gated on the segment being open, SALE is the
    # deterministic shortfall-vs-cost-of-leaving rule, and vacancy was never a destination
    # (model-spec §7.2, "Vacancy is not a branch") — the empty share left withdrawal is now an
    # output of the sale channel's own clearing delay, not an input split. Kept as a dated
    # note rather than deleted outright: this project keeps the archaeology of its parameters.

    # Maps the per-listing quarterly exit hazard onto the studies' annual contract-flow
    # elasticity. FITTED, not observed [docs/experiments/rent-cap.md]. A fitted constant with
    # no range would be a point estimate of something nobody measured.
    #
    # It was fitted on 2026-09-08 so that the three rent-cap studies spanned the 0–2 dial.
    # **They no longer do.** Removing the additive hazard floor (phase A, finding 9) cut the
    # supply response at the top of the dial roughly in half:
    #
    #     ε=0: rents −4.9%, contracts −0.7%   (unchanged — p_exit is multiplied by ε)
    #     ε=1: rents −5.2%, contracts −1.4%
    #     ε=2: rents −4.4%, contracts −7.3%   (was −13.6% / −14.0%)
    #
    # So ε=2 now reaches neither Monràs & García-Montalvo's −10% nor Pérez García's −13%.
    # This value is deliberately NOT re-fitted to recover them: the old number was produced
    # by a floor built from two exogenous constants, and re-fitting a scale factor to
    # reproduce a result that a defect was generating is the one move this project's
    # standard forbids. The arbitrage condition that replaces this machinery was WRITTEN
    # (spec §7.2, 2026-09-16) to retire `hazard_scale` outright rather than re-derive it —
    # along with `rental_supply_elasticity`, which becomes an output.
    #
    # RETIRED (2026-09-16). `Landlord._exit_destination` (agents/landlord.py) now decides the
    # withdrawal deterministically — cumulative shortfall over the holding horizon against the
    # cost of leaving — with no fitted scale anywhere in it. Kept as a dated note rather than
    # deleted outright: this project keeps the archaeology of its parameters. See
    # model-spec.md §7.2 for what runs instead.

    # Below-reference asks drift up toward the cap: ask × this, capped at the cap itself.
    # [guess — the mechanism (a cap read as a target) is documented in the Catalan evaluations;
    # the pace is not]
    magnet_gain: float = 1.05
    magnet_gain_range: tuple[float, float] = (1.00, 1.10)

    # `wedge_annualisation` turns a per-tick growth rate into a per-year one (4 quarters —
    # arithmetic, not a guess). It survives §7.2b: the trapezoid it feeds is now applied over
    # the ticks remaining in the cap's declared term (`PolicyConfig.cap_term_ticks`), not over
    # the horizon below, but the quarterly-to-annual conversion is unchanged.
    wedge_annualisation: float = 4.0

    # RETIRED (2026-09-16, §7.2b). Was `holding_years: float = 5.0`, `holding_years_range:
    # tuple[float, float] = (3.0, 10.0)` — the horizon `agents/landlord` summed the monthly
    # shortfall `(r_req - cap)` over. [guess]: Spanish holding periods ARE in docs/sources.md
    # (Registradores ERI Anuario 2020 — mean 15y 256d, series minimum 7y 106d), but the
    # REALISED holding period is not the same quantity as the decision horizon a landlord
    # weighs when comparing the withdrawal margin, and no source gave that horizon directly —
    # hence the [guess]. §7.2b replaces it with a measured one: the shortfall now accrues over
    # the ticks remaining in the cap's declared statutory term (`PolicyConfig.cap_term_ticks`,
    # `RentCap.term_ticks`), which is sourced (BOE ZMRT resolutions, three-year vigencia) where
    # `holding_years` was a bare guess with no empirical band. Kept as a dated note rather than
    # deleted outright: this project keeps the archaeology of its parameters. See
    # model-spec.md §7.2b, "Parameter ledger".

    # Share of dwelling sales that go through an agency, which decides how many landlords have
    # a CHEAP exit and therefore how many leave at a given cap (model-spec §7.2b). Agencies
    # handle 64% of SECOND-HAND purchases [Fotocasa Research] and ~70% of all operations
    # [idealista] — two portals competing for the same sellers, agreeing within 6pp. The model
    # takes the second-hand figure: a landlord selling a let dwelling makes a second-hand sale.
    # Regional spread is wide (Murcia, Navarra, Baleares high; Extremadura, País Vasco,
    # Andalucía low), which is why the UI slider is wider than this band.
    intermediation_share: float = 0.64
    intermediation_share_range: tuple[float, float] = (0.64, 0.70)
    # The regional spread behind `intermediation_share`, not the national band above: Murcia,
    # Navarra and Baleares run high, Extremadura, País Vasco and Andalucía run low [Fotocasa
    # Research / idealista, by autonomous community]. A later task's sweep and the UI slider
    # read this field rather than hardcoding the regional extremes.
    intermediation_share_regional_range: tuple[float, float] = (0.40, 0.85)
    # The two sale routes, as shares of price. Statutory: CC art. 1455 puts the escritura
    # matriz on the seller, IIVTNU falls on the transmitente but is levied on cadastral LAND
    # value, plus aranceles RD 1426/1989 and RD 1427/1989. Market: commission 3–5% + IVA, so a
    # 4% fee costs 4.84% of price; large networks reach 7%. Uniform within band is a declared
    # convention — the sources give ranges, not distributions.
    exit_cost_private: tuple[float, float] = (0.005, 0.015)
    exit_cost_agency: tuple[float, float] = (0.04, 0.07)


@dataclass(frozen=True)
class LabourConfig:
    """Income risk: an exogenous unemployment path, an endogenous incidence (model-spec §6c.1).

    The rate is data. Who it lands on is the model's business — that is the whole reason this
    block exists, because a mortgage defaults when a *particular* household loses its income,
    not when an aggregate moves.
    """

    # THE EXOGENOUS PATH, and note carefully which rate it is: the share of households whose
    # ACTIVE MEMBERS ARE ALL UNEMPLOYED, not the individual unemployment rate. The model's
    # household is a single income unit, so the individual rate would be the wrong object —
    # it counts a two-earner household that lost one job as fully hit. INE publishes the
    # household-level series directly (EPA tabla 65276, "todos los activos son parados"):
    # 2007Q2 3.15% → **2013Q1 15.02% (peak)** → 2026Q2 5.28%, quarterly since 2002. The
    # individual rate on the same dates is roughly twice as high, and using it put the model's
    # arrears at 6.9% of mortgaged households against a BdE doubtful ratio of 1.6–3.4%.
    # The bust leg is the hold-out's input and arrives through `scenario.LabourShock`, never
    # as a fitted value [INE EPA tabla 65276 — high]
    jobless_rate: float = 0.0528
    # Per-zone multiplier on the national rate, renormalised on household weights at use.
    # MEASURED, and the direction is the surprising one: the metro is the LEAST exposed zone.
    # 2006–2025 averages of DEG1/DEG2/DEG3 against the national rate; in the 2013 trough the
    # spread is 24.2 / 27.3 / 28.7 against 26.1 national [Eurostat `lfst_r_urgau` — high].
    # APPROXIMATION, declared: the gradient is measured on the INDIVIDUAL rate and applied to
    # the household-level path above. Both are EPA products and their national paths move
    # together, but nobody has published the household series by degree of urbanisation.
    zone_multiplier: tuple[float, float, float] = (0.94, 1.06, 1.03)
    # Probability a household leaves unemployment in a quarter. DERIVED FROM A MEASUREMENT,
    # not guessed: with a constant hazard f the share of spells running past a year is
    # (1−f)⁴, which is what the long-term-unemployment share reports — 32.1% (2025) ⇒ 0.25,
    # 52.8% (2014 peak) ⇒ 0.15 [Eurostat `une_ltu_a` — high as a range]
    exit_hazard: float = 0.25
    exit_hazard_range: tuple[float, float] = (0.15, 0.25)
    # Relative risk of job loss, bottom vs top income tercile. REDUCED FORM: the observable is
    # education (ISCED 0-2 against 5-8 — 2.0 in 2007, 2.2 in 2013, 2.45 in 2025) and the model
    # has income, so this is the education gradient carried across a correlated attribute. The
    # stability of that ratio across boom and bust is what makes it usable at all
    # [Eurostat `lfsa_urgaed` — high on the gradient, reduced form on the mapping]
    incidence_relative_risk: float = 2.2
    incidence_relative_risk_range: tuple[float, float] = (2.0, 2.45)
    # Unemployment benefit [LGSS art. 270 — statute]: 70% of the regulatory base for the
    # first 180 days (2 ticks), 60% after.
    replacement_initial: float = 0.70
    replacement_later: float = 0.60
    replacement_switch_ticks: int = 2
    # Benefit duration [LGSS art. 269 — statute]: 120 days at the minimum contribution record,
    # 720 (24 months = 8 ticks) at 2,160 days contributed. The model uses the maximum, which
    # is the generous end and therefore under-produces arrears.
    benefit_max_ticks: int = 8
    # €/yr. IPREM 2026 = €600/month × 12, frozen since 2022 (PGE 2023 rolled over). The
    # benefit is capped at 175% of it and the post-benefit assistance floor is 80%
    # [LGSS art. 270; IPREM 2026 — high]
    iprem_annual: float = 7_200.0
    benefit_cap_iprem: float = 1.75
    # The cap is 175% of IPREM *plus the sixth for prorated extra payments*, which is why
    # SEPE's published 2026 maximum without dependent children is €1,225/month and not
    # €1,050 (600 × 1.75 × 7/6 = 1,225). Leaving the prorrata out would have made the model's
    # benefit 14% meaner than the law allows [LGSS art. 270.3; SEPE published maximum]
    iprem_prorrata: float = 7.0 / 6.0
    assistance_floor_iprem: float = 0.80


@dataclass(frozen=True)
class InsolvencyConfig:
    """Arrears, statutory foreclosure, and what the bank does with what it takes (§6c.2–6c.4).

    The timing here is a statute, not an estimate: that is what makes this the best-identified
    block in the model, and why the one element without a primary source (the judicial phase)
    is a swept range rather than a point value.
    """

    # Consumption floor a household protects before servicing the mortgage, as a fraction of
    # the population's MEDIAN income (not its own — a floor that scaled with own income would
    # make the constraint non-binding by construction). INE's at-risk-of-poverty threshold is
    # €12,220/yr for a one-person household and €25,663 for two adults with two children
    # (2025), i.e. 0.34 and 0.71 of the model's €36,100 median. Defaulted to the conservative
    # end: the model under-produces arrears rather than over-produces them
    # [INE ECV tabla 79342 — high as a range]
    essential_share: float = 0.34
    essential_share_range: tuple[float, float] = (0.34, 0.71)
    # Which statutory early-termination regime is in force. "ley5_2019" (default) = 12 unpaid
    # instalments in the first half of the loan, 15 in the second [Ley 5/2019 art. 24].
    # "ley1_2013" = 3 instalments [LEC art. 693 as amended] — the regime that governs the
    # 2008–13 hold-out, which is why it is a switch and not a parameter.
    foreclosure_regime: str = "ley5_2019"
    trigger_instalments_first_half: int = 12
    trigger_instalments_second_half: int = 15
    trigger_instalments_legacy: int = 3
    # Ley 5/2019 art. 24.1.c: the lender must demand payment giving at least one month. One
    # tick is the shortest the quarterly clock can represent.
    demand_notice_ticks: int = 1
    # Quarters from trigger to possession on the judicial route. THE ONE UNSOURCED ELEMENT of
    # the chain: CGPJ publishes 8.5 months for all first-instance civil matters (a lower
    # bound) and only practitioner guides estimate the procedure itself at 2–4 years. Swept,
    # never reported as a magnitude [law-firm guides — low]
    judicial_lag_ticks: int = 10
    judicial_lag_range: tuple[int, int] = (8, 16)
    # Share of deliveries that happen voluntarily, without the judicial phase, and the share
    # of ALL deliveries that are daciones en pago (debt-extinguishing). 2014, the only year
    # with a published like-for-like split [BdE Circular 1/2013 note — high]
    voluntary_delivery_share: float = 0.478
    dacion_share_of_deliveries: float = 0.397
    # What the creditor pays for the dwelling at auction: the statutory floor for a debtor's
    # habitual residence [LEC art. 670.4 — statute]. Makes the bank's acquisition price
    # accounting rather than a parameter.
    award_share_of_value: float = 0.70
    # Quarters a foreclosed household cannot obtain a mortgage. The legal ceiling on holding a
    # default in a credit register is five years (20 ticks) [LOPDGDD art. 20.1.d]; using it as
    # a behavioural horizon is REDUCED FORM — nobody measured how long banks actually refuse.
    lockout_ticks: int = 20
    lockout_ticks_range: tuple[int, int] = (8, 20)
    # Bank-owned (REO) stock: the share of it listed each tick, and the discount to the zone
    # price index it is listed at. THE WEAKEST PARAMETERS IN THE BLOCK — the registered
    # anchors (Sareb's 2012 transfer haircuts, 31–63% on housing; the 2012 provisioning
    # requirements) are haircuts against BOOK value, not market price, so they bound the range
    # and do not set the value [Sareb/FROB — low; declared reduced form]
    # --- §5d.2 forbearance, the Código de Buenas Prácticas (2026-09-15) -------------------
    # RDL 6/2012's annex, as the Banco de España's guide states it: capital amortisation
    # suspended for five years where the mortgage effort rose ≥1.5× or the household is
    # specially vulnerable, two years otherwise; term extended to at most 40 years from
    # origination; interest during grace at euríbor − 0.10%; refused if the restructured
    # payment would exceed 50% of household income; available only before the auction is
    # announced. All of that is statute, not parameter [BdE Cliente Bancario — high]
    forbearance_grace_severe_ticks: int = 20  # five years
    forbearance_grace_mild_ticks: int = 8  # two years
    forbearance_max_term_ticks: int = 160  # forty years from origination
    forbearance_viability_share: float = 0.50  # of household income, the law's own test
    # The umbral de exclusión, verbatim [RDL 6/2012 art. 3, BdE Cliente Bancario]: household
    # income at most **three times the annual IPREM on fourteen payments** (3 × €8,400 =
    # €25,200) AND a mortgage instalment above **50% of net income**. It is a poverty gate,
    # not a distress gate, and that is the point — leaving it out put 2.4% of all mortgaged
    # households into a restructuring in a calm baseline, against a scheme that reached
    # 45,697 families in five years nationally.
    iprem_annual_14: float = 8_400.0
    forbearance_income_limit_iprem: float = 3.0
    forbearance_burden_threshold: float = 0.50
    forbearance_rate_discount: float = 0.001  # euríbor − 0.10pp during the grace period
    # The one reduced-form leg: how many eligible households actually get it. The CBP's own
    # counts — 45,697 families in five years, 14,730 operations in 2016 — against roughly
    # 50,000 dwelling deliveries a year put the reach at 15–25% of the distressed flow
    # [Comisión de Control del CBP — medium]
    forbearance_takeup: float = 0.20
    forbearance_takeup_range: tuple[float, float] = (0.10, 0.30)
    reo_release_share: float = 0.15
    reo_discount: float = 0.15
    reo_discount_range: tuple[float, float] = (0.10, 0.35)


@dataclass(frozen=True)
class SimConfig:
    """Full input to one run."""

    seed: int
    ticks: int
    population: PopulationConfig
    stock: StockConfig
    market: MarketConfig
    credit: CreditConfig
    developer: DeveloperConfig
    policy: PolicyConfig
    migration: MigrationConfig = field(default_factory=MigrationConfig)
    cap_response: CapResponseConfig = field(default_factory=CapResponseConfig)
    labour: LabourConfig = field(default_factory=LabourConfig)
    insolvency: InsolvencyConfig = field(default_factory=InsolvencyConfig)
    zones: tuple[ZoneConfig, ...] = field(default_factory=tuple)

    @classmethod
    def baseline(cls, seed: int = 42, ticks: int = 60) -> SimConfig:
        """The reference world every scenario is compared against."""
        zones = (
            ZoneConfig(
                zone=ZoneType.TENSIONED,
                household_share=0.45,
                tenant_share=0.237,  # ECV densa: 19.5 market + 4.2 below-market
                income_multiplier=1.0767,  # ADRH, top-89 municipalities
                price_multiplier=1.6,
                gross_yield=0.052,  # 4.7–5.6
                itp_rate=0.10,
                large_investor_share=0.10,  # 8–15 guess
                cost_per_m2=1_450.0,  # ×1.2 national — guess
                land_share=0.45,  # 40–50
                supply_elasticity=0.25,  # metro core: little developable land left
                foreign_overlay=True,
                location_premium=1.0,  # numeraire: the metro is what the others are priced against
                units_per_household=1.075,  # INE: 6.3–7.7% empty in >300k-hab municipalities
                withheld_share=0.39,  # strongest demand: most of the empty stock is usable
                seasonal_share=0.025,  # weights to INE May-2026 341k VUT (was .028 ≈ 374k)
            ),
            ZoneConfig(
                zone=ZoneType.SECONDARY,
                household_share=0.35,
                tenant_share=0.186,  # ECV intermedia: 15.7 + 2.9
                income_multiplier=0.9622,  # ADRH, next 708
                price_multiplier=0.9,
                gross_yield=0.070,  # 6.5–7.5
                itp_rate=0.08,
                large_investor_share=0.02,
                cost_per_m2=1_200.0,
                land_share=0.30,  # 25–35
                supply_elasticity=0.50,  # national average
                foreign_overlay=False,
                location_premium=0.85,
                units_per_household=1.124,  # INE: 11.1–13.1% empty in 20k–300k-hab
                withheld_share=0.63,
                seasonal_share=0.010,
            ),
            ZoneConfig(
                zone=ZoneType.RURAL,
                household_share=0.20,
                tenant_share=0.108,  # ECV poco poblada: 8.6 + 2.2 — was inferred
                income_multiplier=0.8935,  # ADRH, remaining 7,334
                price_multiplier=0.5,
                gross_yield=0.080,  # 7–9
                itp_rate=0.06,
                large_investor_share=0.0,
                cost_per_m2=1_080.0,
                land_share=0.20,  # 15–25
                supply_elasticity=1.00,  # abundant land: supply answers price
                foreign_overlay=False,
                location_premium=0.45,
                units_per_household=1.242,  # INE: 15.6–24.6% empty in <20k-hab
                withheld_share=0.81,  # weak demand + rehabilitation need: mostly unusable
                seasonal_share=0.005,
            ),
        )
        return cls(
            seed=seed,
            ticks=ticks,
            population=PopulationConfig(),
            stock=StockConfig(),
            market=MarketConfig(),
            credit=CreditConfig(),
            developer=DeveloperConfig(),
            policy=PolicyConfig(),
            zones=zones,
        )

    def zone(self, zone: ZoneType) -> ZoneConfig:
        for z in self.zones:
            if z.zone is zone:
                return z
        raise KeyError(zone)

    def with_policy(self, **changes) -> SimConfig:
        """New config with policy fields replaced. Never mutates."""
        return replace(self, policy=replace(self.policy, **changes))

    def with_credit(self, **changes) -> SimConfig:
        """New config with credit fields replaced. Never mutates."""
        return replace(self, credit=replace(self.credit, **changes))

    def with_labour(self, **changes) -> SimConfig:
        """New config with labour-market fields replaced. Never mutates."""
        return replace(self, labour=replace(self.labour, **changes))
