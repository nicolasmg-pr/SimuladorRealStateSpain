"""The tick loop — the spine of the simulation.

Tick order is a modelling decision, not an implementation detail (model-spec §4).
This module is the single place it is expressed:

    1. macro & policy update   — scenario config, rates, taxes, sitting-rent indexation,
                                 vacancy-tax mobilization, tourist-rental phase-out
    2. demography              — formation, dissolution, migration
    3. expectations update     — adaptive extrapolation per zone
    4. agent decisions         — read-only decide(), intents collected
    5. credit screening        — bank caps clip every mortgage-financed offer
    6. market clearing         — sales (sealed bid), then rentals (queue)
    7. settlement              — clearing.settle is the only ownership writer
    8. supply response         — completions arrive, starts enter the pipeline
    8b. balance sheets & insolvency — incomes and savings, the exogenous unemployment path
                                 and its incidence, arrears, statutory foreclosure,
                                 bank REO release (insolvency.py)
    9. metrics snapshot
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from . import insolvency as insolvency_mod
from . import metrics
from . import rng as rng_mod
from .agents.bank import NET_INCOME_FACTOR, Bank, itp_wedge, max_price
from .agents.base import (
    IntentBundle,
    ListForRent,
    ListForSale,
    MakeOffer,
    RentApplication,
    SetCredit,
    StartConstruction,
    WithdrawRental,
)
from .agents.developer import Developer
from .agents.government import Government
from .agents.household import Households, search_burden
from .agents.investor import LargeInvestor
from .agents.landlord import SmallLandlords, cap_level, required_rent
from .config import ZoneType
from .market.clearing import (
    FOREIGN_ID,
    clear_rentals,
    clear_sales,
    loss_averse_ask,
    settle,
)
from .market.stock import (
    DEVELOPER_ID,
    LARGE_INVESTOR_ID,
    PUBLIC_ID,
    Stock,
    Tenure,
    Unit,
)
from .scenario import Scenario
from .state import (
    HouseholdState,
    HouseholdStatus,
    Macro,
    RentListing,
    SaleListing,
    WorldState,
    ZoneState,
    ask_basis,
)

HOUSEHOLDS_AGENT_ID = -10
LANDLORDS_AGENT_ID = -11
DEVELOPER_AGENT_ID = -12
BANK_AGENT_ID = -13
GOVERNMENT_AGENT_ID = -14

GROWTH_WINDOW = 4  # ticks of trailing growth feeding expectations


class Engine:
    """Runs one scenario from tick 0 to `ticks`."""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        base = scenario.baseline
        self.rng = rng_mod.make_rng(base.seed)
        # 9 streams. The eighth is insolvency (model-spec §6c) and the ninth is forbearance
        # (§5d.2). Spawning more children does not disturb the earlier ones — SeedSequence
        # children are keyed by index — and giving forbearance its own stream is not tidiness:
        # its take-up draw sits inside the arrears path, so sharing the insolvency stream
        # would shift every later draw in the run and re-randomise the whole model. That was
        # measured: three unrelated gates flipped on the stream shift alone, one of them a
        # marginal gate whose own docstring admits the margin is thin.
        streams = rng_mod.spawn(self.rng, 9)
        self.households_agent = Households(HOUSEHOLDS_AGENT_ID, streams[0])
        self.landlords_agent = SmallLandlords(LANDLORDS_AGENT_ID, streams[1])
        self.investor_agent = LargeInvestor(LARGE_INVESTOR_ID, streams[2])
        self.developer_agent = Developer(DEVELOPER_AGENT_ID, streams[3])
        self.bank_agent = Bank(BANK_AGENT_ID, streams[4])
        self.government_agent = Government(GOVERNMENT_AGENT_ID, streams[5])
        self.market_rng = streams[6]
        self.insolvency_rng = streams[7]
        self.forbearance_rng = streams[8]

    # ------------------------------------------------------------------ init

    def initialise(self) -> WorldState:
        """Build the tick-0 world: agents, stock, initial prices."""
        cfg = self.scenario.baseline
        rng = self.rng
        state = WorldState(tick=0, config=cfg, stock=Stock())
        pop, stk = cfg.population, cfg.stock

        state.macro = Macro(
            euribor=cfg.credit.euribor,
            mortgage_rate=cfg.credit.euribor + cfg.credit.spread,
            bond_yield=cfg.credit.euribor + 0.010,
            itp={z.zone: z.itp_rate for z in cfg.zones},
            guarantee_budget_left=0.0,
        )

        for zcfg in cfg.zones:
            price = stk.median_value * zcfg.price_multiplier
            rent = price * zcfg.gross_yield / 12.0
            state.zones[zcfg.zone] = ZoneState(
                price_index=price,
                valuation_index=price,
                rent_index=rent,
                reference_rent=rent * (1.0 - cfg.policy.cap_reference_discount),
                shadow_rent=rent,
            )

        # incomes are drawn as POTENTIAL (employed) income: the EFF/ECV median the config
        # carries was measured on a population that already contains unemployed households,
        # so drawing at that median and then applying the unemployment path would subtract
        # the same loss twice (insolvency.potential_income_uplift)
        uplift = insolvency_mod.potential_income_uplift(cfg)
        for zcfg in cfg.zones:
            n_hh = int(round(pop.n_households * zcfg.household_share))
            incomes = rng.lognormal(
                np.log(pop.income_median * zcfg.income_multiplier * uplift),
                pop.income_sigma,
                n_hh,
            )
            n_tenants = int(round(n_hh * zcfg.tenant_share))
            statuses = [HouseholdStatus.TENANT] * n_tenants + [HouseholdStatus.OWNER] * (
                n_hh - n_tenants
            )
            rng.shuffle(statuses)  # type: ignore[arg-type]
            burdens = rng.uniform(pop.max_rent_burden_lo, pop.max_rent_burden_hi, n_hh)
            zs = state.zones[zcfg.zone]

            for i in range(n_hh):
                hid = state.new_household_id()
                status = statuses[i]
                if status is HouseholdStatus.OWNER:
                    wealth_median, wealth_sigma = pop.owner_wealth_median, pop.wealth_sigma
                else:
                    wealth_median, wealth_sigma = (
                        pop.tenant_wealth_median,
                        pop.tenant_wealth_sigma,
                    )
                hh = HouseholdState(
                    id=hid,
                    zone=zcfg.zone,
                    income=float(incomes[i]),
                    wealth=float(rng.lognormal(np.log(wealth_median), wealth_sigma)),
                    status=status,
                    max_rent_burden=float(burdens[i]),
                    eligibility_draw=float(rng.random()),
                )
                state.households[hid] = hh

                quality = float(rng.lognormal(0.0, 0.15))
                unit = Unit(
                    id=state.stock.new_id(),
                    zone=zcfg.zone,
                    quality=quality,
                    owner_id=hid,
                    occupant_id=hid,
                    tenure=Tenure.OWNER_OCCUPIED,
                    last_sale_price=zs.price_index * quality,
                    declaration_draw=float(rng.random()),
                )
                if status is HouseholdStatus.TENANT:
                    unit.tenure = Tenure.RENTED
                    unit.rent = zs.rent_index * quality
                    unit.last_contract_rent = unit.rent
                    unit.contract_start = -int(rng.integers(1, 12))
                    unit.owner_id = -1  # assigned to a landlord below
                    hh.unit_id = unit.id
                else:
                    hh.unit_id = unit.id
                    # ~35% of owners still carry a mortgage [EFF2024]
                    if rng.random() < 0.35:
                        hh.mortgage_balance = 60_900.0 * float(rng.lognormal(0.0, 0.5))
                        r = state.macro.mortgage_rate / 4
                        n_left = int(rng.integers(20, 90))
                        annuity = r / (1 - (1 + r) ** -n_left)
                        payment = hh.mortgage_balance * annuity
                        # The opening mortgage book must satisfy the SAME screen the bank
                        # applies to every new loan. It did not: balance and income were drawn
                        # independently, so a household with a €15k income could open the run
                        # owing €150k on a five-year tail — a payment of twice its income.
                        # Nothing noticed while non-payment was absorbed by
                        # `wealth = max(0, wealth - payment)`; with the budget constraint
                        # binding (§6c.2) those households went into arrears on tick 1 and
                        # their forced listings moved the price level. Phase C found it; the
                        # fix belongs here, at the source [bank §3, model-spec §4 step 5].
                        cap = cfg.credit.max_dsti * NET_INCOME_FACTOR * hh.income / 4.0
                        if payment > cap:
                            hh.mortgage_balance *= cap / payment
                            payment = cap
                        hh.mortgage_payment = payment
                        hh.mortgage_ticks_left = n_left
                state.stock.add(unit)

            # vacant stock on top. Per-zone, not national: the Spanish empty stock sits where
            # demand is weakest (half of it in municipalities under 20k inhabitants, which hold
            # 28% of the population), so a uniform ratio puts the vacancy ladder the wrong way
            # round [INE Censo 2021 via Funcas 104 ch.1 — see ZoneConfig.units_per_household].
            n_vacant = int(round(n_hh * (zcfg.units_per_household - 1.0)))
            for _ in range(n_vacant):
                quality = float(rng.lognormal(0.0, 0.15))
                state.stock.add(
                    Unit(
                        id=state.stock.new_id(),
                        zone=zcfg.zone,
                        quality=quality,
                        owner_id=-1,
                        occupant_id=None,
                        tenure=Tenure.VACANT,
                        last_sale_price=zs.price_index * quality,
                        # off-market share rises as local demand weakens: 2nd homes, holdouts
                        # and stock empty for want of location and condition [ZoneConfig]
                        withheld=bool(rng.random() < zcfg.withheld_share),
                        declaration_draw=float(rng.random()),
                    )
                )

            # tourist-rental (VUT) segment, on top of the residential stock. Without it the
            # tourist-restriction lever has nothing to phase out and reads as a no-op: the
            # only other route into Tenure.SEASONAL is rent-cap evasion.
            n_seasonal = int(round(n_hh * zcfg.units_per_household * zcfg.seasonal_share))
            for _ in range(n_seasonal):
                quality = float(rng.lognormal(0.0, 0.15))
                state.stock.add(
                    Unit(
                        id=state.stock.new_id(),
                        zone=zcfg.zone,
                        quality=quality,
                        owner_id=-1,
                        occupant_id=None,
                        tenure=Tenure.SEASONAL,
                        last_sale_price=zs.price_index * quality,
                        declaration_draw=float(rng.random()),
                    )
                )

        self._assign_landlords(state)
        self._load_initial_pipeline(state)
        return state

    def _load_initial_pipeline(self, state: WorldState) -> None:
        """Units already under construction at tick 0 (`DeveloperConfig.initial_pipeline`).

        Empty in the baseline. The 2008-13 hold-out needs it: Spain entered the bust with the
        2005-08 pipeline still delivering, and completions ran at 563,631 in 2008 against
        43,230 in 2013 [MIVAU 3.2]. Without this the model would start the episode with no
        overhang and would be answering an easier question than the one being asked.
        """
        cfg = state.config
        schedule = cfg.developer.initial_pipeline
        if not schedule:
            return
        shares = {z.zone: z.household_share for z in cfg.zones}
        for offset, total in enumerate(schedule):
            if total <= 0:
                continue
            for zone, share in shares.items():
                n = int(round(total * share))
                if n > 0:
                    state.pipeline.append((offset + 1, zone, n, False))

    def _assign_landlords(self, state: WorldState) -> None:
        """Distribute rented + vacant units to owners per dossier shares.

        `public_rental_share` is a share of the TOTAL stock (318k of 18.54M dwellings), so it
        has to be converted to a per-zone share of *rented* units before it can be used as an
        assignment probability — reading it directly as a rental-stock share undercounted the
        public parque by roughly 4×. Public stock is metro-concentrated, hence the weights.
        """
        cfg = state.config
        rng = self.rng
        owners = [h.id for h in state.households.values() if h.status is HouseholdStatus.OWNER]
        n_public_total = cfg.stock.public_rental_share * len(state.stock)
        rented_by_zone = {z: 0 for z in ZoneType}
        for unit in state.stock.units.values():
            if unit.tenure is Tenure.RENTED:
                rented_by_zone[unit.zone] += 1
        public_share_of_rented = {}
        for zone, weight in zip(ZoneType, cfg.stock.public_zone_weights, strict=True):
            public_share_of_rented[zone] = min(
                0.9, n_public_total * weight / max(1, rented_by_zone[zone])
            )

        for unit in state.stock.units.values():
            if unit.owner_id != -1:
                continue
            zcfg = cfg.zone(unit.zone)
            r = rng.random()
            if unit.tenure is not Tenure.RENTED:
                # vacant stock is held by individuals (2nd homes, inherited, between lets)
                unit.owner_id = int(owners[int(rng.integers(len(owners)))])
            elif r < zcfg.large_investor_share:
                unit.owner_id = LARGE_INVESTOR_ID
            elif r < zcfg.large_investor_share + public_share_of_rented[unit.zone]:
                unit.owner_id = PUBLIC_ID
                unit.is_public = True
                unit.rent *= cfg.policy.public_rent_discount
            else:
                # small landlord: skew toward higher-wealth owners [EFF: age/wealth gradient]
                unit.owner_id = int(owners[int(rng.integers(len(owners)))])

    # ------------------------------------------------------------------ step

    def step(self, state: WorldState) -> WorldState:
        """Advance exactly one tick, following the order documented above."""
        state.tick += 1
        state.tick_events = {
            "sales_by_zone": state.tick_events.get("sales_by_zone", {}),
            "rental_tightness": state.tick_events.get("rental_tightness", {}),
            "renter_capacity": state.tick_events.get("renter_capacity", {}),
        }

        self._macro_update(state)  # 1
        self._demography(state)  # 2
        self._expectations(state)  # 3
        bundle = self._collect_intents(state)  # 4
        self._credit_screen(state, bundle)  # 5
        self._apply_listings(state, bundle)
        self._record_tightness(state, bundle)
        trades = clear_sales(state, bundle.offers, self.market_rng)  # 6
        for tr in trades:
            # a unit sold this tick cannot also be leased this tick (a landlord can hold
            # both listings open); the sale wins
            state.rent_listings.pop(tr.unit_id, None)
        rentals = clear_rentals(state, bundle.rent_applications, self.market_rng)
        settle(state, trades, rentals)  # 7
        self._update_indices(state, trades, rentals)
        self._supply_response(state, bundle)  # 8
        self._household_flows(state)
        state.history.append(metrics.snapshot(state, trades, rentals))  # 9
        return state

    # -- 1 ------------------------------------------------------------------

    def _macro_update(self, state: WorldState) -> None:
        cfg = self.scenario.config_at(state.tick)
        state.config = cfg
        macro = state.macro
        macro.euribor = cfg.credit.euribor
        macro.bond_yield = cfg.credit.euribor + 0.010
        for zcfg in cfg.zones:
            delta = cfg.policy.itp_delta if zcfg.zone in cfg.policy.itp_zones else 0.0
            macro.itp[zcfg.zone] = zcfg.itp_rate + delta
        if cfg.policy.guarantee_ltv_boost > 0.0 and not macro.guarantee_budget_funded:
            # the ICO line is a one-off envelope, funded the tick the lever switches on.
            # Once spent it stays spent — the programme closes [demand-subsidy §5].
            macro.guarantee_budget_left = cfg.policy.guarantee_budget
            macro.guarantee_budget_funded = True

        # sitting-rent indexation at contract anniversaries. Public rents are administrative
        # and are not indexed on the private update path.
        annual_update = (
            cfg.policy.within_contract_update
            if cfg.policy.rent_cap_enabled
            else cfg.market.long_run_growth * 4
        )
        for unit in state.stock.rented():
            if not unit.is_public and (state.tick - unit.contract_start) % 4 == 0:
                unit.rent *= 1.0 + annual_update

        # vacancy tax: detected long-vacant units of large-portfolio owners re-enter
        pol = cfg.policy
        if pol.vacancy_tax_rate > 0.0 and pol.vacancy_detection > 0.0:
            for unit in state.stock.vacant():
                if not unit.withheld or state.tick - unit.vacant_since < 8:
                    continue
                if state.stock.rental_portfolio_size(unit.owner_id) < pol.vacancy_min_portfolio:
                    continue
                if self.market_rng.random() < pol.vacancy_detection / 4.0:
                    # mobilization: tax bite vs holding — probability scales with rate
                    p_mobilize = min(0.9, 10.0 * pol.vacancy_tax_rate)
                    if self.market_rng.random() < p_mobilize:
                        unit.withheld = False

        # tourist-rental phase-out: seasonal units forced back
        if pol.vut_phaseout_rate > 0.0:
            seasonal = [u for u in state.stock.units.values() if u.tenure is Tenure.SEASONAL]
            n_out = int(len(seasonal) * pol.vut_phaseout_rate / 4.0)
            for u in seasonal[:n_out]:
                u.tenure = Tenure.VACANT
                u.vacant_since = state.tick
                u.withheld = self.market_rng.random() > pol.vut_conversion_share

        # land release bookkeeping
        if pol.extra_land_units_per_tick > 0 and state.land_release_start is None:
            state.land_release_start = state.tick
        if (
            state.land_release_start is not None
            and state.tick >= state.land_release_start + pol.land_release_lag
        ):
            share_t = {"tensioned": 0.6, "secondary": 0.3, "rural": 0.1}
            state.tick_events["released_land"] = {
                z: int(pol.extra_land_units_per_tick * share_t[z.value]) for z in ZoneType
            }

    # -- 2 ------------------------------------------------------------------

    def _demography(self, state: WorldState) -> None:
        cfg = state.config
        pop = cfg.population
        rng = self.rng
        n_new = int(rng.poisson(pop.formation_per_tick))
        state.tick_events["formation"] = n_new
        # new households land where growth is: metro-weighted when configured, else in
        # proportion to the existing population [PopulationConfig.formation_zone_weights]
        shares = np.array(
            pop.formation_zone_weights
            if pop.formation_zone_weights is not None
            else [z.household_share for z in cfg.zones]
        )
        zone_ids = rng.choice(len(cfg.zones), size=n_new, p=shares / shares.sum())
        for zi in zone_ids:
            zcfg = cfg.zones[int(zi)]
            hid = state.new_household_id()
            state.households[hid] = HouseholdState(
                id=hid,
                zone=zcfg.zone,
                income=float(
                    rng.lognormal(
                        np.log(
                            pop.income_median
                            * zcfg.income_multiplier
                            * pop.formation_income_factor
                            * insolvency_mod.potential_income_uplift(cfg)
                        ),
                        pop.income_sigma,
                    )
                ),
                wealth=float(rng.lognormal(np.log(pop.seeker_wealth_median), pop.wealth_sigma)),
                status=HouseholdStatus.SEEKER,
                max_rent_burden=float(rng.uniform(pop.max_rent_burden_lo, pop.max_rent_burden_hi)),
                eligibility_draw=float(rng.random()),
            )

        # dissolutions: the WHOLE estate passes to ONE surviving household (inheritance) —
        # the home *and* any rental units, otherwise dissolved small landlords leave
        # permanently orphaned stock behind that still acts as a landlord.
        #
        # PHASE A (spec §2, finding 4). Two defects lived here.
        #
        # 1. The heir never took possession. `owner_id` was reassigned and nothing else was:
        #    a SEEKER who inherited a dwelling stayed a SEEKER while owning an empty home.
        #    `ownership_rate` counts `status is OWNER`, so ownership drifted 77.2% → 69.5%
        #    over 60 ticks and target 1 sat below the EFF band for a reason that has nothing
        #    to do with Spanish tenure. An heir with no home of their own now moves into the
        #    inherited dwelling. An heir who already has one keeps it and holds the rest as
        #    stock — the conservative branch, and the first path in the model by which a
        #    household becomes a landlord without buying, which is the margin phase B has to
        #    get right. A TENANT heir is deliberately left renting: moving in breaks a
        #    tenancy, which is a behavioural claim the register carries no source for.
        #
        # 2. The estate was split. The draw sat INSIDE a loop over units, so a fresh heir was
        #    drawn per unit while this comment and `docs/assumptions.md` both said the whole
        #    estate passes to one household. Code and spec disagreed; the register is right.
        #    Splitting an estate across N random strangers is not a choice anyone made, it is
        #    what a loop over units does when the draw is inside it.
        n_exit = int(rng.poisson(pop.formation_per_tick * pop.dissolution_rate))
        ids = list(state.households.keys())
        if len(ids) > n_exit > 0:
            gone = [int(h) for h in rng.choice(ids, size=n_exit, replace=False)]
            # the deceased's own dwelling, where they owned the one they lived in: it is the
            # unit an heir moves into by preference, and it is guaranteed vacant by this loop
            vacated_home: dict[int, int] = {}
            for hid in gone:
                hh = state.households.pop(hid)
                if hh.unit_id is None:
                    continue
                unit = state.stock.units[hh.unit_id]
                owned_own_home = unit.owner_id == hid
                unit.occupant_id = None
                unit.tenure = Tenure.VACANT
                unit.vacant_since = state.tick
                unit.last_contract_rent = unit.rent or unit.last_contract_rent
                unit.rent = 0.0
                state.sale_listings.pop(hh.unit_id, None)
                state.rent_listings.pop(hh.unit_id, None)
                if owned_own_home:
                    vacated_home[hid] = hh.unit_id

            heirs = list(state.households.keys())
            if heirs:
                estates: dict[int, list] = {hid: [] for hid in gone}
                for unit in state.stock.units.values():
                    if unit.owner_id in estates:
                        estates[unit.owner_id].append(unit)
                inherited_homes = 0
                for hid in gone:
                    estate = estates[hid]
                    if not estate:
                        continue
                    heir = state.households[int(heirs[int(rng.integers(len(heirs)))])]
                    for unit in estate:
                        unit.owner_id = heir.id
                    if heir.unit_id is not None:
                        continue  # already housed: the estate is stock, not a home
                    # move in — the deceased's own home first, else any vacant unit of the
                    # estate. Never a RENTED one: inheriting a landlord does not evict a
                    # tenant (LAU: the lease runs with the dwelling, not with the owner).
                    home = state.stock.units.get(vacated_home.get(hid, -1))
                    if home is None or home.tenure is not Tenure.VACANT:
                        home = next((u for u in estate if u.tenure is Tenure.VACANT), None)
                    if home is None:
                        continue
                    state.sale_listings.pop(home.id, None)
                    state.rent_listings.pop(home.id, None)
                    home.occupant_id = heir.id
                    home.tenure = Tenure.OWNER_OCCUPIED
                    home.vacant_since = -1
                    home.last_contract_rent = home.rent or home.last_contract_rent
                    home.rent = 0.0
                    home.withheld = False
                    heir.unit_id = home.id
                    heir.status = HouseholdStatus.OWNER
                    heir.ticks_searching = 0
                    inherited_homes += 1
                state.tick_events["inherited_homes"] = inherited_homes

        # Interior migration between zones (model-spec §7.5, phase B).
        #
        # Replaces a downward-only coin flip: `if rent burden too high and rng < 0.10: move one
        # step down the ladder`. That rule could produce metro→rural and nothing else, so its
        # sign was an artefact of its construction — it could not reproduce 2015–16, when
        # Spain's interior flow genuinely ran the other way, and no policy could move it.
        #
        # The rule is now a COMPARISON, so both directions are reachable and the sign is an
        # outcome. A household weighs annual income in the destination zone against annual
        # housing cost there, net of a move friction:
        #
        #     gain(d) = income × (mult(d)/mult(o) − 1) − 12 × (rent(d) − rent(o)) − friction
        #
        # `income` already embeds the origin zone's multiplier (households are drawn with it at
        # formation), so the income term is the RATIO, not the level. Metro→rural falls out
        # when the rent gap dominates the income gap, which is what Spain's interior flows do
        # under the declared mapping B; rural→metro falls out for households whose income gain
        # clears the friction. Owners face a larger friction, the same asymmetry the model
        # already carries for within-zone moves (`owner_move_prob` vs `tenant_move_prob`).
        #
        # KNOWN DEFICIENCY, measured and registered rather than patched (2026-09-14). At the
        # baseline calibration this rule produces NO interior inflow to the tensioned zone at
        # all — gross flows over 3 seeds × 40 ticks are tensioned→rural 224 and
        # secondary→rural 37, and nothing in the other direction. The net direction is right
        # and matches Spain; the gross flows are not. Spain's interior net (≈100k/yr) is a
        # small difference between two large gross flows (≈1.6M interior moves/yr), and this
        # rule has one of them at zero.
        #
        # The mechanism itself is not one-directional — raise the metro income multiplier 35%
        # and secondary→tensioned 329 and rural→tensioned 124 appear immediately. The cause is
        # that the only pull toward the metro here is the income ratio (1.085/0.896 = 1.21),
        # and it does not clear the rent gap for anyone. What is missing is the reason people
        # actually move to cities and that this model has no representation of: where the job
        # is, rather than what the average wage ratio is, plus amenity and study.
        #
        # Not fixed by adding an amenity parameter, which is the obvious patch: an unsourced
        # free term tuned until the gross flows look right is precisely what phase B exists to
        # remove, and it would be fitted against the same targets it would then be said to
        # pass. `tests/test_validation.py::test_interior_migration_has_gross_flows_both_ways`
        # carries it as a dated strict xfail. Closing it needs a job-location or amenity
        # mechanism with its own identification — spec §7.5's amenity term, which is also what
        # would make `location_premium` derivable rather than free.
        #
        # Reproducibility: every draw comes from the engine's seeded Generator, and households
        # are visited in registry order, so the flows are a function of the seed alone.
        mig = cfg.migration
        zone_list = [z.zone for z in cfg.zones]
        mult = {z.zone: z.income_multiplier for z in cfg.zones}
        rents = {z: state.zones[z].rent_index for z in zone_list}
        flows: dict[tuple[ZoneType, ZoneType], int] = {}
        for hh in state.households.values():
            if rng.random() >= mig.consideration_rate:
                continue
            friction = mig.move_cost_share * hh.income
            if hh.status is HouseholdStatus.OWNER:
                friction *= mig.owner_friction_multiplier
            origin = hh.zone
            best, best_gain = None, 0.0
            for dest in zone_list:
                if dest is origin:
                    continue
                income_gain = hh.income * (mult[dest] / mult[origin] - 1.0)
                housing_gain = 12.0 * (rents[origin] - rents[dest])
                gain = income_gain + housing_gain - friction
                if gain > best_gain:
                    best, best_gain = dest, gain
            if best is None:
                continue
            # Response scales with the gain relative to income, so a bigger gap moves more
            # households without the consideration rate having to change — which is what the
            # 2020 episode requires: a 4.2× metro outflow while gross interior flows FELL.
            p_move = min(0.9, mig.responsiveness * best_gain / max(hh.income, 1.0))
            if rng.random() >= p_move:
                continue
            # A household that owns or rents a home here does not teleport out of it: moving
            # zone means giving up the dwelling, so it re-enters the market as a SEEKER. An
            # owner keeps the unit (it becomes stock they hold in the old zone) — selling it is
            # the sale market's job, not demography's.
            if hh.unit_id is not None:
                unit = state.stock.units[hh.unit_id]
                unit.occupant_id = None
                unit.tenure = Tenure.VACANT
                unit.vacant_since = state.tick
                unit.last_contract_rent = unit.rent or unit.last_contract_rent
                unit.rent = 0.0
                state.sale_listings.pop(hh.unit_id, None)
                state.rent_listings.pop(hh.unit_id, None)
                hh.unit_id = None
            hh.status = HouseholdStatus.SEEKER
            hh.ticks_searching = 0
            hh.zone = best
            flows[(origin, best)] = flows.get((origin, best), 0) + 1
        state.tick_events["migration"] = flows

    # -- 3 ------------------------------------------------------------------

    def _expectations(self, state: WorldState) -> None:
        m = state.config.market
        for zs in state.zones.values():
            for series, attr in (
                (zs.price_growth, "expected_price_growth"),
                (zs.rent_growth, "expected_rent_growth"),
            ):
                recent = series[-GROWTH_WINDOW:]
                trailing = float(np.mean(recent)) if recent else m.long_run_growth
                setattr(
                    zs,
                    attr,
                    (1 - m.expectation_momentum) * m.long_run_growth
                    + m.expectation_momentum * trailing,
                )

    # -- 4 ------------------------------------------------------------------

    def _collect_intents(self, state: WorldState) -> IntentBundle:
        bundle = IntentBundle()
        all_intents = (
            self.households_agent.decide(state)
            + self.landlords_agent.decide(state)
            + self.investor_agent.decide(state)
            + self.developer_agent.decide(state)
            + self.government_agent.decide(state)
            + self.bank_agent.decide(state)
        )
        for intent in all_intents:
            match intent:
                case ListForSale():
                    bundle.sale_listings.append(intent)
                case MakeOffer():
                    bundle.offers.append(intent)
                case ListForRent():
                    bundle.rent_listings.append(intent)
                case WithdrawRental():
                    bundle.withdrawals.append(intent)
                case RentApplication():
                    bundle.rent_applications.append(intent)
                case StartConstruction():
                    bundle.construction.append(intent)
                case SetCredit():
                    bundle.credit = intent

        # Foreign non-resident overlay (model-spec §3, §7.4).
        #
        # PHASE B: the arrival rate is a constant, not a share of recent Spanish sales. It used
        # to read `foreign_purchase_share × recent sales`, which made a declared-exogenous
        # demand source a function of the market it buys into — a domestic slump cut foreign
        # arrivals mechanically, and the 8% share could never be falsified because it was an
        # input (spec §2, finding 5). With a constant stream the share is an OUTPUT and rises
        # when domestic volume falls, which is what Spain actually shows (2026Q2: foreigners
        # +11% y/y while nationals fell).
        cfg = state.config
        lam = cfg.population.foreign_arrivals_per_tick
        for zcfg in cfg.zones:
            if not zcfg.foreign_overlay:
                continue
            # transaction-tax wedge for a cash buyer: the baseline rate is already inside the
            # observed premium, so only a CHANGE (general delta or the non-resident surcharge)
            # moves the budget [model-spec §8, transaction-tax.md §5]
            wedge = itp_wedge(
                zcfg.itp_rate, state.macro.itp[zcfg.zone] + cfg.policy.itp_foreign_delta
            )
            for _ in range(int(self.market_rng.poisson(lam))):
                bundle.offers.append(
                    MakeOffer(
                        agent_id=FOREIGN_ID,
                        zone=zcfg.zone,
                        # Budget on an EXOGENOUS path, not on the domestic index. The old form
                        # multiplied `zs.price_index`, so a cash buyer big enough to move the
                        # index bid a multiple of the index it moved — the same unanchored
                        # feedback the large investor had. The anchor is now the zone's INITIAL
                        # price level carried forward at the model's nominal growth anchor,
                        # times the observed non-resident €/m² premium (3,063 vs 1,713 €/m²,
                        # Notariado CIEN). Origin-country conditions are declared exogenous
                        # (model-spec §14), so a path that does not read the Spanish index is
                        # the honest form; a cyclical one would need an origin-country income
                        # index, which is NOT retrieved, so the path is the nominal anchor and
                        # says so.
                        budget=self._foreign_anchor(state, zcfg)
                        * cfg.population.foreign_budget_multiplier
                        * float(self.market_rng.uniform(0.8, 1.2))
                        * wedge,
                        cash=True,
                    )
                )
        return bundle

    def _foreign_anchor(self, state: WorldState, zcfg) -> float:
        """Exogenous €-level a non-resident buyer prices off, model-spec §7.4.

        The zone's INITIAL price level compounded at `foreign_budget_growth` — the +5.86%/yr
        the €/m² actually paid by non-residents grew over 2014H1–2025H2 [CIEN Tabla 1C], not
        the model's own 2%/yr nominal anchor, which is Spanish CPI and would leave this buyer
        flat in real terms while the real one gained 3.69%/yr.

        It deliberately never reads `ZoneState.price_index`: the whole point is that this
        buyer's willingness to pay is formed abroad and does not respond to what Spanish prices
        have done, so the model can be ASKED whether foreign demand is propping prices up
        rather than assuming it either way.
        """
        base = state.config.stock.median_value * zcfg.price_multiplier
        return base * (1.0 + state.config.population.foreign_budget_growth) ** state.tick

    # -- 5 ------------------------------------------------------------------

    def _credit_screen(self, state: WorldState, bundle: IntentBundle) -> None:
        """Ability-to-pay replaces willingness-to-pay: clip every financed offer."""
        cfg = state.config
        if bundle.credit is not None:
            state.macro.mortgage_rate = bundle.credit.mortgage_rate
        screened: list[MakeOffer] = []
        for offer in bundle.offers:
            if offer.cash or offer.agent_id < 0:
                screened.append(offer)
                continue
            hh = state.households.get(offer.agent_id)
            if hh is None:
                continue
            # a foreclosed household is in the credit register for up to five years
            # [LOPDGDD art. 20.1.d, model-spec §6c.3]. It may still buy for cash — the
            # register blocks credit, not purchases — and cash offers never reach here.
            if hh.credit_lockout_ticks > 0:
                continue
            # the guarantee decision belongs to the household (means test); the bank only
            # re-checks that the programme envelope is still open at screening time
            guaranteed = offer.guaranteed and state.macro.guarantee_budget_left > 0.0
            limit = max_price(
                hh,
                state.macro.mortgage_rate,
                cfg.credit,
                state.macro.itp[offer.zone],
                cfg.market.buyer_fees,
                cfg.policy.guarantee_ltv_boost if guaranteed else 0.0,
            )
            if limit <= 0:
                continue
            if offer.budget > limit or guaranteed != offer.guaranteed:
                offer = MakeOffer(
                    agent_id=offer.agent_id,
                    zone=offer.zone,
                    budget=min(offer.budget, limit),
                    cash=offer.cash,
                    first_time=offer.first_time,
                    guaranteed=guaranteed,
                )
            screened.append(offer)
        bundle.offers = screened

    # -- listings / withdrawals ---------------------------------------------

    def _apply_listings(self, state: WorldState, bundle: IntentBundle) -> None:
        cfg = state.config
        # age + decay existing sale listings
        for unit_id in list(state.sale_listings):
            lst = state.sale_listings[unit_id]
            lst.ticks_listed += 1
            lst.ask *= 1.0 - cfg.market.ask_decay
            if lst.ticks_listed > cfg.market.max_listing_ticks or lst.ask < lst.reserve:
                del state.sale_listings[unit_id]
        # rental asks decay too, but they have a FLOOR (the landlord's required yield, or the
        # cap where one binds) and they EXPIRE. Without both, unmatched listings ground their
        # ask down indefinitely and dragged the asking-basis rent index with them.
        for unit_id in list(state.rent_listings):
            lst = state.rent_listings[unit_id]
            unit = state.stock.units[unit_id]
            if unit.is_public:
                continue  # administrative rent, allocated by queue — no decay, no expiry
            lst.ticks_listed += 1
            if lst.ticks_listed > cfg.market.max_listing_ticks:
                # the landlord gives up on this ask; they re-decide (and re-price at the
                # current market level) next tick
                del state.rent_listings[unit_id]
                continue
            zs = state.zones[unit.zone]
            floor = required_rent(state, unit.zone, zs.price_index * unit.quality)
            # a listing clipped by the cap decays no lower than the cap; an uncovered or
            # non-complying listing keeps the landlord's yield floor — otherwise the cap
            # would lower asks in municipalities where it was never declared
            # the same two-regime cap the lister faced (§5b, Ley 12/2023 art. 17.6–17.7):
            # the index for a gran tenedor, the previous contract plus IRAV for anyone else
            cap = cap_level(
                state,
                unit.zone,
                unit.quality,
                previous_rent=unit.rent or unit.last_contract_rent,
                large_holder=unit.owner_id == LARGE_INVESTOR_ID,
            )
            if cap is not None and lst.capped:
                floor = min(floor, cap)
            lst.ask = max(floor, lst.ask * (1.0 - cfg.market.ask_decay))

        for w in bundle.withdrawals:
            unit = state.stock.units[w.unit_id]
            state.rent_listings.pop(w.unit_id, None)
            if w.destination == "sale":
                zs = state.zones[unit.zone]
                value = ask_basis(zs) * unit.quality
                ask = loss_averse_ask(
                    base_ask=value * (1.0 + cfg.market.ask_markup),
                    paid=unit.last_sale_price,
                    value=value,
                    # a landlord's list-price response to a nominal loss is half an
                    # owner-occupier's [Genesove & Mayer 2001, model-spec §5d.1]
                    alpha=cfg.market.loss_aversion_investor,
                )
                discount = float(
                    self.market_rng.uniform(
                        cfg.market.max_seller_discount_lo, cfg.market.max_seller_discount_hi
                    )
                )
                # a landlord's unit carries no household mortgage in this model, so the
                # reserve is the negotiation-margin leg only (model-spec §5c.3)
                state.sale_listings[unit.id] = SaleListing(
                    unit_id=unit.id, ask=ask, reserve=ask * (1.0 - discount)
                )
            else:
                # "seasonal" is the only other destination `Landlord._exit_destination`
                # (agents/landlord.py) ever returns. RETIRED (2026-09-16): a trailing
                # `else: unit.withheld = True` used to catch a "vacant" destination that
                # `Landlord._exit` (deleted, §7.2) produced as its residual share. Vacancy is
                # not a branch (model-spec §7.2) — `grep -rn "WithdrawRental(" src` confirms
                # the cap channel is the only producer left, and it never emits anything but
                # "sale" and "seasonal" — so the vacancy fallback is dead code, deleted rather
                # than kept, unlike a retired *parameter*.
                assert w.destination == "seasonal", w.destination
                unit.tenure = Tenure.SEASONAL

        for ls in bundle.sale_listings:
            if ls.unit_id not in state.sale_listings:
                state.sale_listings[ls.unit_id] = SaleListing(
                    unit_id=ls.unit_id, ask=ls.ask, reserve=ls.reserve
                )
        for lr in bundle.rent_listings:
            unit = state.stock.units[lr.unit_id]
            if lr.unit_id not in state.rent_listings and unit.tenure is Tenure.VACANT:
                state.rent_listings[lr.unit_id] = RentListing(
                    unit_id=lr.unit_id, ask=lr.ask, capped=lr.capped
                )

    def _record_tightness(self, state: WorldState, bundle: IntentBundle) -> None:
        """Applicants per rental listing, and the zone's renter paying capacity.

        Tightness is what a landlord sees when a unit is advertised. Paying capacity — the
        median of (accepted burden × income) over the zone's non-owner households — feeds
        `ZoneState.shadow_rent` (see _update_indices), which matters because the asking index
        collapses onto the cap once a cap is active (every posted ask is clipped), so without
        it landlords lose sight of the uncapped market within a few ticks and the withdrawal
        decision goes inert. Two queue-based anchors were tried and rejected: the marginal
        quantile 1 − listings/applicants rises with every withdrawal and ran away (tightness
        1.6 → 38, contracts 61 → 9 per tick); the median of this tick's applicants falls under
        a cap because cheaper rents pull lower-income sitting tenants into the queue, and the
        exits stopped after ten ticks. Capacity over ALL non-owners moves only with incomes,
        the sharing margin and tenure transitions — nothing the cap or the exits cause within
        a quarter (docs/validation.md, tensioned-tightness revision). Landlords read next tick.
        """
        apps: dict[ZoneType, int] = dict.fromkeys(ZoneType, 0)
        for a in bundle.rent_applications:
            apps[a.zone] += 1
        listings: dict[ZoneType, int] = dict.fromkeys(ZoneType, 0)
        for lst in state.rent_listings.values():
            listings[state.stock.units[lst.unit_id].zone] += 1
        state.tick_events["rental_tightness"] = {z: apps[z] / max(1, listings[z]) for z in ZoneType}

        capacity: dict[ZoneType, list[float]] = {z: [] for z in ZoneType}
        for hh in state.households.values():
            if hh.status is HouseholdStatus.OWNER:
                continue
            burden = (
                search_burden(hh) if hh.status is HouseholdStatus.SEEKER else hh.max_rent_burden
            )
            capacity[hh.zone].append(burden * hh.income / 12.0)
        previous = state.tick_events.get("renter_capacity", {})
        state.tick_events["renter_capacity"] = {
            z: (
                float(np.median(capacity[z]))
                if capacity[z]
                else previous.get(z, state.zones[z].rent_index)
            )
            for z in ZoneType
        }

    # -- indices --------------------------------------------------------------

    def _update_indices(self, state: WorldState, trades, rentals) -> None:
        cfg = state.config
        s = cfg.market.price_index_smoothing
        sales_by_zone: dict[ZoneType, int] = {}
        for zone in ZoneType:
            zs = state.zones[zone]
            zone_trades = [
                t.price / state.stock.units[t.unit_id].quality
                for t in trades
                if state.stock.units[t.unit_id].zone is zone
            ]
            # The same sales on a TASTE-NEUTRAL basis (model-spec §5c.6): what each would
            # have closed at had the price-setting bidders drawn an average taste. An
            # auction selects its winner on a high draw, so the realised index carries a
            # selection premium; buyers anchoring on it would capitalise that premium every
            # tick and `overbid_sigma` would set the growth rate of prices rather than their
            # dispersion. Sellers still post off the realised index — they observe sales.
            zone_neutral = [
                (t.neutral_price or t.price) / state.stock.units[t.unit_id].quality
                for t in trades
                if state.stock.units[t.unit_id].zone is zone
            ]
            sales_by_zone[zone] = len(zone_trades)
            old_p = zs.price_index
            if zone_trades:
                zs.price_index = (1 - s) * old_p + s * float(np.median(zone_trades))
            zs.price_growth.append(zs.price_index / old_p - 1.0)
            if zone_neutral:
                zs.valuation_index = (1 - s) * zs.valuation_index + s * float(
                    np.median(zone_neutral)
                )

            # the agent-visible rent index is ASKING-based (idealista-like): the
            # transacted median is composition-fragile (rich tenants exiting to
            # ownership drags it down even in a shortage). Transacted rents are
            # recorded separately in metrics (SERPAVI-like basis).
            # public rents are administrative, not market signals — they must not enter the
            # index agents condition on, or the parque social would look like a price cut
            zone_asks = [
                lst.ask / state.stock.units[lst.unit_id].quality
                for lst in state.rent_listings.values()
                if state.stock.units[lst.unit_id].zone is zone
                and not state.stock.units[lst.unit_id].is_public
            ]
            zone_rents = [
                r.rent / state.stock.units[r.unit_id].quality
                for r in rentals
                if state.stock.units[r.unit_id].zone is zone
                and not state.stock.units[r.unit_id].is_public
            ]
            old_r = zs.rent_index
            signal = zone_asks + zone_rents
            if signal:
                zs.rent_index = (1 - s) * old_r + s * float(np.median(signal))
            zs.rent_growth.append(zs.rent_index / old_r - 1.0)
            zs.rent_transacted = float(np.median(zone_rents)) if zone_rents else zs.rent_transacted

            # official reference index: while a cap is active in this zone the table
            # is administrative — frozen at activation and updated by IRAV only
            # (re-anchoring it on the capped market would spiral the cap downward);
            # otherwise it tracks new-contract rents with a lag
            cap_here = cfg.policy.rent_cap_enabled and zone in cfg.policy.rent_cap_zones
            if cap_here:
                zs.reference_rent *= 1.0 + cfg.policy.within_contract_update / 4.0
            else:
                zs.reference_rent = 0.9 * zs.reference_rent + 0.1 * zs.rent_index * (
                    1.0 - cfg.policy.cap_reference_discount
                )

            zs.capped_here = cap_here
        state.tick_events["sales_by_zone"] = sales_by_zone
        self._update_shadow_rents(state)

    def _update_shadow_rents(self, state: WorldState) -> None:
        """What a standard unit would fetch in each zone with NO cap in force.

        Free market: the shadow *is* the asking index. Under a cap the asking index is the cap
        itself, so it cannot serve — a landlord reading it sees no loss and stops withdrawing
        (model-spec §5b). The counterfactual therefore takes its **level** from the last free
        observation (the index on the tick before the cap switched on) and its **growth** from
        the model's exogenous nominal income anchor, `MarketConfig.long_run_growth`. The
        assumption is stated in one line — absent the cap, rents would have grown at the
        long-run anchor — and it is the only part that is assumed; the level is observed.

        Two richer anchors were built and rejected, and their failure modes are why this one is
        deliberately dumb (docs/validation.md, shadow-anchor revision):

        - *Median renter paying capacity.* Composition-sensitive: the non-owner pool is
          refreshed with poorer new households, so its median grows ≈1.5%/yr against a 3.2%/yr
          free-market rent, the gap to the IRAV-indexed reference closes, and the cap quietly
          stops binding after ~10 ticks.
        - *The untreated zones' rent index*, the studies' own treated-vs-control
          identification. Contaminated by the effect it measures, and explosively: the cap
          displaces demand into the control zones, their rents rise, that lifts the shadow,
          which widens the gap and drives more exits. Measured over 80 ticks the gap reached
          **+122%** and tensioned lettings collapsed from 89 to 10 per tick.

        Against those, an exogenous path is bounded and honest: the reference grows at IRAV
        (1.5%/yr) and the shadow at the income anchor (2%/yr), so a long cap becomes gradually
        *more* binding at 0.5pp/yr — which is what indexing rents below wages does in reality.
        The cost is that the shadow ignores the cycle: in a boom the true counterfactual would
        rise faster and the model understates the cap's bite, in a slump the reverse.
        """
        anchor = state.config.market.long_run_growth
        for zone in ZoneType:
            zs = state.zones[zone]
            if zs.capped_here:
                zs.shadow_rent *= 1.0 + anchor
                zs.shadow_growth = anchor
            else:
                zs.shadow_rent = zs.rent_index
                zs.shadow_growth = zs.expected_rent_growth

    # -- 8 ------------------------------------------------------------------

    def _supply_response(self, state: WorldState, bundle: IntentBundle) -> None:
        cfg = state.config
        pol = cfg.policy
        lag = max(1, cfg.developer.construction_lag + pol.permit_lag_delta)

        public_starts: dict[ZoneType, int] = dict.fromkeys(ZoneType, 0)
        for c in bundle.construction:
            if c.is_public:
                public_starts[c.zone] += c.n_units
        started = 0
        for c in bundle.construction:
            n = c.n_units
            if not c.is_public:
                # crowding out: public programmes absorb private capacity in the SAME zone
                # (builders, trades and land compete locally, not nationally)
                n = max(0, n - int(pol.crowding_out_share * public_starts[c.zone]))
            if n > 0:
                started += n
                state.pipeline.append(
                    (
                        state.tick + (pol.public_delivery_lag if c.is_public else lag),
                        c.zone,
                        n,
                        c.is_public,
                    )
                )
        # starts net of crowding out — the visados-equivalent flow, comparable to the
        # ≈140k/yr BdE reports (benchmarks.py). Completions arrive `lag` ticks later.
        state.tick_events["starts"] = started

        arrivals = [p for p in state.pipeline if p[0] <= state.tick]
        state.pipeline = [p for p in state.pipeline if p[0] > state.tick]
        state.tick_events["completions"] = sum(n for _, _, n, _ in arrivals)
        for _, zone, n_units, is_public in arrivals:
            zs = state.zones[zone]
            for _ in range(n_units):
                # the new-build premium is quality, not price inflation — keeps the
                # quality-adjusted price index composition-neutral
                quality = float(
                    self.market_rng.lognormal(np.log(cfg.developer.new_build_premium), 0.10)
                )
                unit = Unit(
                    id=state.stock.new_id(),
                    zone=zone,
                    quality=quality,
                    owner_id=PUBLIC_ID if is_public else DEVELOPER_ID,
                    occupant_id=None,
                    tenure=Tenure.VACANT,
                    last_sale_price=zs.price_index * quality,
                    vacant_since=state.tick,  # completion date = start of inventory ageing
                    is_public=is_public,
                    declaration_draw=float(self.market_rng.random()),
                )
                state.stock.add(unit)
                if is_public:
                    state.rent_listings[unit.id] = RentListing(
                        unit_id=unit.id,
                        ask=zs.rent_index * quality * pol.public_rent_discount,
                    )
                else:
                    # first listing only; the developer re-prices unsold inventory itself
                    # (developer.py) rather than letting it fall out of the market
                    ask = zs.price_index * quality
                    state.sale_listings[unit.id] = SaleListing(
                        unit_id=unit.id, ask=ask, reserve=ask * 0.9, presale=True
                    )

    # -- household balance-sheet flows ---------------------------------------

    def _household_flows(self, state: WorldState) -> None:
        """Step 8b: incomes, savings, income risk, arrears, foreclosure, REO (§6c).

        Runs after clearing on purpose: a dwelling repossessed this tick reaches the market
        next tick, which is the real sequence, and it keeps `clearing.settle` the only writer
        of ownership *inside* a tick.
        """
        cfg = state.config
        sr = cfg.population.saving_rate
        income_growth = cfg.market.long_run_growth  # nominal wage anchor, /tick
        rng = self.insolvency_rng
        events = insolvency_mod.TickInsolvency()

        events.unemployed = insolvency_mod.update_employment(state, rng)
        incomes = [hh.income for hh in state.households.values()]
        median_income = float(np.median(incomes)) if incomes else 1.0

        for hh in state.households.values():
            # the wage anchor grows POTENTIAL income; unemployment takes a household off it
            # for the length of the spell, it does not reset the career path
            hh.income *= 1.0 + income_growth
            if hh.credit_lockout_ticks > 0:
                hh.credit_lockout_ticks -= 1
            # search spell: counted here, at the end of the tick, so a household formed this
            # tick starts at 0 and only a *failed* search increments it. Reset by settle()
            # when the household is housed — the escalation is a spell, not a history
            # (agents/household.search_burden: the sharing margin).
            if hh.status is HouseholdStatus.SEEKER:
                hh.ticks_searching += 1

            income_eff = insolvency_mod.effective_income(hh, cfg)
            saving = sr * income_eff / 4.0
            if hh.status is HouseholdStatus.TENANT and hh.unit_id is not None:
                rent_y = state.stock.units[hh.unit_id].rent * 12.0
                saving *= max(0.0, 1.0 - rent_y / max(income_eff, 1.0))
            hh.wealth += saving

            if hh.mortgage_ticks_left > 0:
                events.mortgaged += 1
                insolvency_mod.service_mortgage(hh, state, income_eff, saving, median_income)
            if hh.arrears_instalments > 0:
                events.in_arrears += 1
                # the Código de Buenas Prácticas is offered at the first missed quarter and
                # before the auction is announced — the order the statute sets (§5d.2)
                insolvency_mod.offer_forbearance(hh, state, income_eff, self.forbearance_rng)
            if hh.forbearance_ticks_left > 0:
                events.forborne += 1
            insolvency_mod.advance_foreclosure(hh, state, rng)
            # the sale decision follows the statutory threat, not the first missed payment
            if hh.foreclosure_tick is not None and hh.status is HouseholdStatus.OWNER:
                events.distressed_listings += int(insolvency_mod.list_distressed(state, hh))
            elif hh.arrears_instalments == 0:
                insolvency_mod.withdraw_distressed(state, hh)

        # deliveries are collected after the pass so the arrears count above is the state at
        # the end of servicing, not a mix of before and after possession
        for hh in list(state.households.values()):
            if hh.delivery_tick is not None and state.tick >= hh.delivery_tick:
                insolvency_mod.deliver(hh, state, rng, events)

        insolvency_mod.release_reo(state, rng, events)
        state.tick_events["insolvency"] = events

    # ------------------------------------------------------------------ run

    def run(self) -> WorldState:
        """Run to completion and return the final state (history holds the series)."""
        state = self.initialise()
        for _ in range(self.scenario.baseline.ticks):
            self.step(state)
        return state

    def stream(self) -> Iterator[WorldState]:
        """Yield state after each tick — used by the UI to render a run as it progresses."""
        state = self.initialise()
        for _ in range(self.scenario.baseline.ticks):
            yield self.step(state)
