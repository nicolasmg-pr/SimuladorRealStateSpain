"""Streamlit app — the demo surface.

Run: streamlit run src/resim/ui/app.py

Sidebar: baseline knobs, one policy lever, and the *disputed* parameters exposed as
sliders labeled with the competing estimates (bias-control rule: the model spans the
disagreement, the user explores it).

Rule: this file only calls into resim.scenario, resim.engine, and resim.metrics.
Any number it computes itself is a number the tests do not cover.
"""

from __future__ import annotations

import streamlit as st

from resim import metrics
from resim.config import SimConfig, ZoneType
from resim.engine import Engine
from resim.scenario import (
    DemandSubsidy,
    LandRelease,
    PublicHousing,
    RateShock,
    RentCap,
    Scenario,
    TouristRestriction,
    TransactionTax,
    VacancyTax,
)

ZONE_LABELS = {
    ZoneType.TENSIONED: "Tensioned metro",
    ZoneType.SECONDARY: "Secondary city",
    ZoneType.RURAL: "Rural",
}


@st.cache_data(show_spinner="Running simulation…")
def run(seed: int, ticks: int, lever: str, lever_params: dict, momentum: float):
    import dataclasses

    base = SimConfig.baseline(seed=seed, ticks=ticks)
    base = dataclasses.replace(
        base, market=dataclasses.replace(base.market, expectation_momentum=momentum)
    )
    baseline_frame = metrics.to_frame(Engine(Scenario(name="baseline", baseline=base)).run())
    if lever == "none":
        return baseline_frame, None

    intervention = {
        "rent cap": RentCap,
        "transaction tax": TransactionTax,
        "vacancy tax": VacancyTax,
        "public housing": PublicHousing,
        "tourist-rental restriction": TouristRestriction,
        "demand subsidy": DemandSubsidy,
        "land release": LandRelease,
        "rate shock": RateShock,
    }[lever](**lever_params)
    scenario = Scenario(name=lever, baseline=base, interventions=(intervention,))
    scenario_frame = metrics.to_frame(Engine(scenario).run())
    return baseline_frame, scenario_frame


def main() -> None:
    st.set_page_config(page_title="resim — Spanish housing ABM", layout="wide")
    st.title("Spanish real-estate market simulator")
    st.caption(
        "Agent-based model calibrated on the dossiers in docs/actors/. Disputed "
        "parameters are ranges, not points — outputs are conditional on the sliders."
    )

    with st.sidebar:
        st.header("Run")
        seed = st.number_input("Seed", 0, 10_000, 42)
        ticks = st.slider("Quarters", 20, 80, 60)

        st.header("Disputed parameters")
        momentum = st.slider(
            "Expectation momentum λ",
            0.5,
            0.9,
            0.7,
            help="Weight on trailing price growth. Range 0.5–0.9; no direct Spanish "
            "estimate exists (household-owner §7.1). Higher = bigger cycles.",
        )

        st.header("Policy lever")
        lever = st.selectbox(
            "Intervention",
            [
                "none",
                "rent cap",
                "transaction tax",
                "vacancy tax",
                "public housing",
                "tourist-rental restriction",
                "demand subsidy",
                "land release",
                "rate shock",
            ],
        )
        params: dict = {}
        if lever != "none":
            params["start_tick"] = st.slider("Start quarter", 1, 40, 8)
        if lever == "rent cap":
            params["supply_response_elasticity"] = st.slider(
                "Landlord supply-response elasticity",
                0.0,
                2.0,
                1.0,
                help="THE disputed parameter. 0 = Jofre-Monseny et al. 2023 (rents "
                "−4/−5%, no supply effect). 2 = Monràs & García-Montalvo (−5% rents, "
                "−10% contracts). Mid/high = Pérez García 2026 (−13% tenancies, weak "
                "price effect).",
            )
            params["cap_reference_discount"] = st.slider(
                "Cap below market rent",
                0.0,
                0.10,
                0.05,
                help="Where the reference index sits vs market (0–10%).",
            )
            params["compliance"] = st.slider(
                "Compliance",
                0.25,
                0.95,
                0.85,
                help="Berlin ads ≈0.25 · Paris ≈0.5–0.64 · Catalan registered ≈0.9.",
            )
        elif lever == "transaction tax":
            params["itp_delta"] = st.slider(
                "ITP change (pp of price)",
                -0.06,
                0.10,
                0.02,
                0.01,
                help="Evidence: −4% to −15% volume per +1pp (UK/DE/NL/CA imports).",
            )
        elif lever == "vacancy tax":
            params["rate"] = st.slider(
                "Tax, share of unit value /yr",
                0.001,
                0.03,
                0.005,
                0.001,
                help="IBI surcharge ≈0.001–0.005 · Catalan tax ≈0.003–0.01 · Vancouver ≈0.01–0.03.",
            )
            params["detection"] = st.slider(
                "Detection probability /yr",
                0.0,
                0.9,
                0.15,
                help="Spain today ≈0–0.05 (222 of 8,131 municipalities). "
                "Vancouver-style universal declaration ≈0.5–0.9.",
            )
        elif lever == "public housing":
            params["units_per_tick"] = st.slider(
                "Public starts per quarter (model units ≈ ×2,000 real)",
                1,
                30,
                6,
                help="6 ≈ 48k/yr real ≈ announced plans; 12+ ≈ BdE convergence path.",
            )
            params["crowding_out"] = st.slider(
                "Crowding-out share",
                0.0,
                0.8,
                0.33,
                help="Private starts displaced per public start. Sinai-Waldfogel ≈0.33; "
                "Murray ≈0 for deep-subsidy rental.",
            )
        elif lever == "tourist-rental restriction":
            params["phaseout_rate"] = st.slider("Licence phase-out /yr", 0.0, 1.0, 0.25)
            params["conversion_share"] = st.slider(
                "Share returning to long-term market",
                0.10,
                0.50,
                0.30,
                help="NYC: low · Berlin 2016: substantial. Never a point (rent-cap of hysteresis).",
            )
        elif lever == "demand subsidy":
            params["guarantee_ltv_boost"] = st.slider("Guarantee LTV boost", 0.0, 0.25, 0.20)
            params["guarantee_eligible_share"] = st.slider(
                "Eligible share of first-time buyers",
                0.05,
                0.50,
                0.25,
                help="Observed ICO take-up ≈ narrow; legal eligibility wide. "
                "Capitalization scales with this.",
            )
        elif lever == "land release":
            params["extra_units_per_tick"] = st.slider("Extra land (units/quarter)", 1, 20, 4)
            params["release_lag"] = st.slider(
                "Release lag (quarters)",
                20,
                60,
                40,
                help="Planning→finalist plot = 5–15 years. No short-run effect is the "
                "validation target.",
            )
        elif lever == "rate shock":
            params["euribor"] = st.slider("Euríbor", 0.0, 0.06, 0.04, 0.005)

    baseline_frame, scenario_frame = run(seed, ticks, lever, params, momentum)
    frame = scenario_frame if scenario_frame is not None else baseline_frame

    st.subheader("Prices by zone (€, quality-adjusted index)")
    st.line_chart(frame[[f"price_{z.value}" for z in ZoneType]])
    st.subheader("Rents by zone (€/month, new contracts)")
    st.line_chart(frame[[f"rent_{z.value}" for z in ZoneType]])

    cols = st.columns(4)
    last = frame.iloc[-1]
    cols[0].metric("Ownership rate", f"{last['ownership_rate']:.1%}")
    cols[1].metric("Price-to-income", f"{last['price_to_income']:.1f}")
    cols[2].metric("Rent overburden (>40%)", f"{last['rent_overburden_share']:.1%}")
    cols[3].metric("Vacancy", f"{last['vacancy_rate']:.1%}")

    if scenario_frame is not None:
        st.subheader(f"Scenario minus baseline — {lever}")
        diff = metrics.compare(baseline_frame, scenario_frame)
        c1, c2 = st.columns(2)
        with c1:
            st.line_chart(diff[[f"price_{z.value}" for z in ZoneType]])
            st.caption("Δ price by zone")
        with c2:
            st.line_chart(diff[[f"rent_{z.value}" for z in ZoneType]])
            st.caption("Δ rent by zone")
        st.line_chart(diff[["transactions", "new_leases"]])
        st.caption("Δ volumes (sales, new leases)")

    st.subheader("Volumes & tenure")
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(frame[["transactions", "new_leases"]])
    with c2:
        st.line_chart(frame[["ownership_rate", "tenant_share", "seeker_share"]])


if __name__ == "__main__":
    main()
