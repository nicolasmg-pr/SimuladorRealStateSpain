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
    9. metrics snapshot
"""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from . import metrics
from . import rng as rng_mod
from .agents.bank import Bank, max_price
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
from .agents.household import Households
from .agents.investor import LargeInvestor
from .agents.landlord import SmallLandlords
from .config import ZoneType
from .market.clearing import FOREIGN_ID, clear_rentals, clear_sales, settle
from .market.stock import (
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
        streams = rng_mod.spawn(self.rng, 7)
        self.households_agent = Households(HOUSEHOLDS_AGENT_ID, streams[0])
        self.landlords_agent = SmallLandlords(LANDLORDS_AGENT_ID, streams[1])
        self.investor_agent = LargeInvestor(LARGE_INVESTOR_ID, streams[2])
        self.developer_agent = Developer(DEVELOPER_AGENT_ID, streams[3])
        self.bank_agent = Bank(BANK_AGENT_ID, streams[4])
        self.government_agent = Government(GOVERNMENT_AGENT_ID, streams[5])
        self.market_rng = streams[6]

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
                rent_index=rent,
                reference_rent=rent * (1.0 - cfg.policy.cap_reference_discount),
            )

        for zcfg in cfg.zones:
            n_hh = int(round(pop.n_households * zcfg.household_share))
            incomes = rng.lognormal(
                np.log(pop.income_median * zcfg.income_multiplier), pop.income_sigma, n_hh
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
                )
                if status is HouseholdStatus.TENANT:
                    unit.tenure = Tenure.RENTED
                    unit.rent = zs.rent_index * quality
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
                        hh.mortgage_payment = hh.mortgage_balance * (r / (1 - (1 + r) ** -n_left))
                        hh.mortgage_ticks_left = n_left
                state.stock.add(unit)

            # vacant stock on top
            n_vacant = int(round(n_hh * (stk.units_per_household - 1.0)))
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
                        withheld=bool(rng.random() < 0.5),  # 2nd homes etc. [guess]
                    )
                )

        self._assign_landlords(state)
        return state

    def _assign_landlords(self, state: WorldState) -> None:
        """Distribute rented + vacant units to owners per dossier shares."""
        cfg = state.config
        rng = self.rng
        owners = [h.id for h in state.households.values() if h.status is HouseholdStatus.OWNER]
        for unit in state.stock.units.values():
            if unit.owner_id != -1:
                continue
            zcfg = cfg.zone(unit.zone)
            r = rng.random()
            if unit.tenure is Tenure.RENTED and r < zcfg.large_investor_share:
                unit.owner_id = LARGE_INVESTOR_ID
            elif (
                unit.tenure is Tenure.RENTED
                and r < zcfg.large_investor_share + cfg.stock.public_rental_share
            ):
                unit.owner_id = PUBLIC_ID
                unit.is_public = True
                unit.rent *= 0.5  # public rent discount
            else:
                # small landlord: skew toward higher-wealth owners [EFF: age/wealth gradient]
                unit.owner_id = int(owners[int(rng.integers(len(owners)))])

    # ------------------------------------------------------------------ step

    def step(self, state: WorldState) -> WorldState:
        """Advance exactly one tick, following the order documented above."""
        state.tick += 1
        state.tick_events = {"sales_by_zone": state.tick_events.get("sales_by_zone", {})}

        self._macro_update(state)  # 1
        self._demography(state)  # 2
        self._expectations(state)  # 3
        bundle = self._collect_intents(state)  # 4
        self._credit_screen(state, bundle)  # 5
        self._apply_listings(state, bundle)
        trades = clear_sales(state, bundle.offers, self.market_rng)  # 6
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
        if cfg.policy.guarantee_ltv_boost > 0.0 and macro.guarantee_budget_left == 0.0:
            # model-scale ICO line: €2.5bn/2000 [demand-subsidy §5]
            macro.guarantee_budget_left = 2.5e9 / 2000.0

        # sitting-rent indexation at contract anniversaries
        annual_update = (
            cfg.policy.within_contract_update
            if cfg.policy.rent_cap_enabled
            else cfg.market.long_run_growth * 4
        )
        for unit in state.stock.rented():
            if (state.tick - unit.contract_start) % 4 == 0:
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
        shares = np.array([z.household_share for z in cfg.zones])
        zone_ids = rng.choice(len(cfg.zones), size=n_new, p=shares / shares.sum())
        for zi in zone_ids:
            zcfg = cfg.zones[int(zi)]
            hid = state.new_household_id()
            state.households[hid] = HouseholdState(
                id=hid,
                zone=zcfg.zone,
                income=float(
                    rng.lognormal(
                        np.log(pop.income_median * zcfg.income_multiplier * 0.8),
                        pop.income_sigma,
                    )
                ),  # young households earn less [EFF <35 median 32k]
                wealth=float(rng.lognormal(np.log(pop.seeker_wealth_median), pop.wealth_sigma)),
                status=HouseholdStatus.SEEKER,
                max_rent_burden=float(rng.uniform(pop.max_rent_burden_lo, pop.max_rent_burden_hi)),
            )

        # dissolutions: estate passes to a random surviving household (inheritance)
        n_exit = int(rng.poisson(pop.formation_per_tick * pop.dissolution_rate))
        ids = list(state.households.keys())
        if len(ids) > n_exit > 0:
            for hid in rng.choice(ids, size=n_exit, replace=False):
                hh = state.households.pop(int(hid))
                if hh.unit_id is not None:
                    unit = state.stock.units[hh.unit_id]
                    unit.occupant_id = None
                    if unit.tenure is Tenure.OWNER_OCCUPIED:
                        heirs = list(state.households.keys())
                        unit.owner_id = int(heirs[int(rng.integers(len(heirs)))])
                    unit.tenure = Tenure.VACANT
                    unit.vacant_since = state.tick
                    unit.rent = 0.0
                state.sale_listings.pop(hh.unit_id, None) if hh.unit_id else None

        # migration: priced-out seekers slide down the zone ladder [guess]
        ladder = {ZoneType.TENSIONED: ZoneType.SECONDARY, ZoneType.SECONDARY: ZoneType.RURAL}
        for hh in state.households.values():
            if hh.status is HouseholdStatus.SEEKER and hh.zone in ladder:
                zs = state.zones[hh.zone]
                if zs.rent_index * 12 > hh.max_rent_burden * hh.income and rng.random() < 0.10:
                    hh.zone = ladder[hh.zone]

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

        # foreign non-resident overlay (exogenous demand stream, model-spec §3)
        cfg = state.config
        recent = sum(state.tick_events.get("sales_by_zone", {}).values())
        lam = cfg.population.foreign_purchase_share * max(recent, 3)
        for zcfg in cfg.zones:
            if not zcfg.foreign_overlay:
                continue
            zs = state.zones[zcfg.zone]
            for _ in range(int(self.market_rng.poisson(lam))):
                bundle.offers.append(
                    MakeOffer(
                        agent_id=FOREIGN_ID,
                        zone=zcfg.zone,
                        budget=zs.price_index
                        * cfg.population.foreign_budget_multiplier
                        * float(self.market_rng.uniform(0.8, 1.2)),
                        cash=True,
                    )
                )
        return bundle

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
            guaranteed = (
                offer.first_time
                and cfg.policy.guarantee_ltv_boost > 0.0
                and state.macro.guarantee_budget_left > 0.0
            )
            limit = max_price(
                hh,
                state.macro.mortgage_rate,
                cfg.credit,
                state.macro.itp[offer.zone],
                cfg.market.buyer_fees,
                guaranteed,
            )
            if limit <= 0:
                continue
            if offer.budget > limit:
                offer = MakeOffer(
                    agent_id=offer.agent_id,
                    zone=offer.zone,
                    budget=limit,
                    cash=offer.cash,
                    first_time=offer.first_time,
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
        for unit_id in list(state.rent_listings):
            lst = state.rent_listings[unit_id]
            lst.ticks_listed += 1
            lst.ask *= 1.0 - cfg.market.ask_decay

        for w in bundle.withdrawals:
            unit = state.stock.units[w.unit_id]
            state.rent_listings.pop(w.unit_id, None)
            if w.destination == "sale":
                zs = state.zones[unit.zone]
                ask = zs.price_index * unit.quality
                state.sale_listings[unit.id] = SaleListing(
                    unit_id=unit.id, ask=ask, reserve=ask * (1 - cfg.market.max_seller_discount)
                )
            elif w.destination == "seasonal":
                unit.tenure = Tenure.SEASONAL
            else:
                unit.withheld = True

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
            sales_by_zone[zone] = len(zone_trades)
            old_p = zs.price_index
            if zone_trades:
                zs.price_index = (1 - s) * old_p + s * float(np.median(zone_trades))
            zs.price_growth.append(zs.price_index / old_p - 1.0)

            zone_rents = [
                r.rent / state.stock.units[r.unit_id].quality
                for r in rentals
                if state.stock.units[r.unit_id].zone is zone
            ]
            old_r = zs.rent_index
            if zone_rents:
                zs.rent_index = (1 - s) * old_r + s * float(np.median(zone_rents))
            zs.rent_growth.append(zs.rent_index / old_r - 1.0)

            # official reference index follows new-contract rents with a lag
            zs.reference_rent = 0.9 * zs.reference_rent + 0.1 * zs.rent_index * (
                1.0 - cfg.policy.cap_reference_discount
            )
        state.tick_events["sales_by_zone"] = sales_by_zone

    # -- 8 ------------------------------------------------------------------

    def _supply_response(self, state: WorldState, bundle: IntentBundle) -> None:
        cfg = state.config
        pol = cfg.policy
        lag = max(1, cfg.developer.construction_lag + pol.permit_lag_delta)

        public_starts = sum(c.n_units for c in bundle.construction if c.is_public)
        for c in bundle.construction:
            n = c.n_units
            if not c.is_public and public_starts > 0:
                # crowding out: public programmes absorb private capacity
                n = max(0, n - int(pol.crowding_out_share * public_starts / 3))
            if n > 0:
                state.pipeline.append(
                    (
                        state.tick + (pol.public_delivery_lag if c.is_public else lag),
                        c.zone,
                        n,
                        c.is_public,
                    )
                )

        arrivals = [p for p in state.pipeline if p[0] <= state.tick]
        state.pipeline = [p for p in state.pipeline if p[0] > state.tick]
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
                    owner_id=PUBLIC_ID if is_public else -6,  # -6 = developer inventory
                    occupant_id=None,
                    tenure=Tenure.VACANT,
                    last_sale_price=zs.price_index * quality,
                    is_public=is_public,
                )
                state.stock.add(unit)
                if is_public:
                    state.rent_listings[unit.id] = RentListing(
                        unit_id=unit.id,
                        ask=zs.rent_index * quality * pol.public_rent_discount,
                    )
                else:
                    ask = zs.price_index * quality
                    state.sale_listings[unit.id] = SaleListing(
                        unit_id=unit.id, ask=ask, reserve=ask * 0.9, presale=True
                    )

    # -- household balance-sheet flows ---------------------------------------

    def _household_flows(self, state: WorldState) -> None:
        cfg = state.config
        sr = cfg.population.saving_rate
        for hh in state.households.values():
            saving = sr * hh.income / 4.0
            if hh.status is HouseholdStatus.TENANT and hh.unit_id is not None:
                rent_y = state.stock.units[hh.unit_id].rent * 12.0
                saving *= max(0.0, 1.0 - rent_y / max(hh.income, 1.0))
            hh.wealth += saving
            if hh.mortgage_ticks_left > 0:
                r = state.macro.mortgage_rate / 4.0
                interest = hh.mortgage_balance * r
                principal = min(hh.mortgage_balance, hh.mortgage_payment - interest)
                hh.mortgage_balance = max(0.0, hh.mortgage_balance - max(0.0, principal))
                hh.wealth = max(0.0, hh.wealth - hh.mortgage_payment)
                hh.mortgage_ticks_left -= 1
                if hh.mortgage_balance <= 0.0:
                    hh.mortgage_ticks_left = 0
                    hh.mortgage_payment = 0.0

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
