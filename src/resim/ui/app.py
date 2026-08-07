"""Streamlit app — the demo surface (UI in Spanish).

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
    ZoneType.TENSIONED: "Zona tensionada",
    ZoneType.SECONDARY: "Ciudad secundaria",
    ZoneType.RURAL: "Rural",
}

LEVER_CLASSES = {
    "tope de alquiler": RentCap,
    "impuesto de transmisiones (ITP)": TransactionTax,
    "impuesto a la vivienda vacía": VacancyTax,
    "vivienda pública": PublicHousing,
    "restricción de pisos turísticos": TouristRestriction,
    "ayudas a la demanda (avales)": DemandSubsidy,
    "liberación de suelo": LandRelease,
    "shock de tipos": RateShock,
}


def _rename_zones(frame, prefix: str):
    cols = {f"{prefix}_{z.value}": ZONE_LABELS[z] for z in ZoneType}
    return frame[list(cols)].rename(columns=cols)


@st.cache_data(show_spinner="Ejecutando simulación…")
def run(seed: int, ticks: int, lever: str, lever_params: dict, momentum: float):
    import dataclasses

    base = SimConfig.baseline(seed=seed, ticks=ticks)
    base = dataclasses.replace(
        base, market=dataclasses.replace(base.market, expectation_momentum=momentum)
    )
    baseline_frame = metrics.to_frame(Engine(Scenario(name="baseline", baseline=base)).run())
    if lever == "ninguna":
        return baseline_frame, None

    intervention = LEVER_CLASSES[lever](**lever_params)
    scenario = Scenario(name=lever, baseline=base, interventions=(intervention,))
    scenario_frame = metrics.to_frame(Engine(scenario).run())
    return baseline_frame, scenario_frame


def main() -> None:
    st.set_page_config(page_title="resim — ABM del mercado de vivienda español", layout="wide")
    st.title("Simulador del mercado inmobiliario español")
    st.caption(
        "Modelo basado en agentes, calibrado con los dosieres de docs/actors/. Los "
        "parámetros en disputa son rangos, no puntos — los resultados son "
        "condicionales a los deslizadores."
    )

    with st.sidebar:
        st.header("Ejecución")
        seed = st.number_input("Semilla", 0, 10_000, 42)
        ticks = st.slider("Trimestres", 20, 80, 60)

        st.header("Parámetros en disputa")
        momentum = st.slider(
            "Momento de expectativas λ",
            0.5,
            0.9,
            0.7,
            help="Peso del crecimiento reciente de precios en las expectativas. Rango "
            "0,5–0,9; no existe estimación directa para España (household-owner §7.1). "
            "Más alto = ciclos más amplios.",
        )

        st.header("Palanca de política")
        lever = st.selectbox(
            "Intervención",
            ["ninguna", *LEVER_CLASSES],
        )
        params: dict = {}
        if lever != "ninguna":
            params["start_tick"] = st.slider("Trimestre de inicio", 1, 40, 8)
        if lever == "tope de alquiler":
            params["supply_response_elasticity"] = st.slider(
                "Elasticidad de retirada de oferta",
                0.0,
                2.0,
                1.0,
                help="EL parámetro en disputa. 0 = Jofre-Monseny et al. 2023 (rentas "
                "−4/−5%, sin efecto en oferta). 2 = Monràs y García-Montalvo (−5% "
                "rentas, −10% contratos). Medio/alto ≈ Pérez García 2026 (−13% "
                "contratos, efecto en precios débil).",
            )
            params["cap_reference_discount"] = st.slider(
                "Índice de referencia por debajo del mercado",
                0.0,
                0.10,
                0.05,
                help="Dónde queda el índice de referencia frente al alquiler de mercado (0–10%).",
            )
            params["compliance"] = st.slider(
                "Cumplimiento",
                0.25,
                0.95,
                0.85,
                help="Berlín (anuncios) ≈0,25 · París ≈0,5–0,64 · contratos "
                "registrados en Cataluña ≈0,9.",
            )
        elif lever == "impuesto de transmisiones (ITP)":
            params["itp_delta"] = st.slider(
                "Cambio del ITP (pp del precio)",
                -0.06,
                0.10,
                0.02,
                0.01,
                help="Evidencia: −4% a −15% de compraventas por +1pp (estudios de "
                "Reino Unido, Alemania, Países Bajos y Canadá).",
            )
        elif lever == "impuesto a la vivienda vacía":
            params["rate"] = st.slider(
                "Impuesto, fracción del valor /año",
                0.001,
                0.03,
                0.005,
                0.001,
                help="Recargo IBI ≈0,001–0,005 · impuesto catalán ≈0,003–0,01 · "
                "Vancouver ≈0,01–0,03.",
            )
            params["detection"] = st.slider(
                "Probabilidad de detección /año",
                0.0,
                0.9,
                0.15,
                help="España hoy ≈0–0,05 (222 de 8.131 municipios). Declaración "
                "universal estilo Vancouver ≈0,5–0,9.",
            )
        elif lever == "vivienda pública":
            params["units_per_tick"] = st.slider(
                "Viviendas públicas iniciadas por trimestre (unidades modelo ≈ ×2.000 reales)",
                1,
                30,
                6,
                help="6 ≈ 48k/año reales ≈ planes anunciados; 12+ ≈ senda de "
                "convergencia del Banco de España.",
            )
            params["crowding_out"] = st.slider(
                "Desplazamiento de obra privada",
                0.0,
                0.8,
                0.33,
                help="Viviendas privadas desplazadas por cada pública. "
                "Sinai-Waldfogel ≈0,33; Murray ≈0 para alquiler social profundo.",
            )
        elif lever == "restricción de pisos turísticos":
            params["phaseout_rate"] = st.slider("Extinción de licencias /año", 0.0, 1.0, 0.25)
            params["conversion_share"] = st.slider(
                "Proporción que vuelve al alquiler habitual",
                0.10,
                0.50,
                0.30,
                help="Nueva York: baja · Berlín 2016: sustancial. Nunca un punto "
                "(histéresis, tourist-rental-restriction.md).",
            )
        elif lever == "ayudas a la demanda (avales)":
            params["guarantee_ltv_boost"] = st.slider("Aumento de LTV por aval", 0.0, 0.25, 0.20)
            params["guarantee_eligible_share"] = st.slider(
                "Proporción de compradores primerizos elegibles",
                0.05,
                0.50,
                0.25,
                help="Uso observado del aval ICO ≈ estrecho; elegibilidad legal "
                "amplia. La capitalización en precios crece con esta escala.",
            )
        elif lever == "liberación de suelo":
            params["extra_units_per_tick"] = st.slider("Suelo extra (unidades/trimestre)", 1, 20, 4)
            params["release_lag"] = st.slider(
                "Retraso de la liberación (trimestres)",
                20,
                60,
                40,
                help="De planeamiento a suelo finalista: 5–15 años. Que no haya "
                "efecto a corto plazo es un objetivo de validación.",
            )
        elif lever == "shock de tipos":
            params["euribor"] = st.slider("Euríbor", 0.0, 0.06, 0.04, 0.005)

    baseline_frame, scenario_frame = run(seed, ticks, lever, params, momentum)
    frame = scenario_frame if scenario_frame is not None else baseline_frame

    st.subheader("Precios por zona (€, índice ajustado por calidad)")
    st.line_chart(_rename_zones(frame, "price"))
    st.subheader("Alquileres por zona (€/mes, oferta de nuevos contratos)")
    st.line_chart(_rename_zones(frame, "rent"))

    cols = st.columns(4)
    last = frame.iloc[-1]
    cols[0].metric("Tasa de propiedad", f"{last['ownership_rate']:.1%}")
    cols[1].metric("Precio / renta disponible", f"{last['price_to_income']:.1f}")
    cols[2].metric("Sobrecarga de alquiler (>40%)", f"{last['rent_overburden_share']:.1%}")
    cols[3].metric("Vivienda vacía", f"{last['vacancy_rate']:.1%}")

    if scenario_frame is not None:
        st.subheader(f"Escenario menos base — {lever}")
        diff = metrics.compare(baseline_frame, scenario_frame)
        c1, c2 = st.columns(2)
        with c1:
            st.line_chart(_rename_zones(diff, "price"))
            st.caption("Δ precio por zona")
        with c2:
            st.line_chart(_rename_zones(diff, "rent"))
            st.caption("Δ alquiler por zona")
        st.line_chart(
            diff[["transactions", "new_leases"]].rename(
                columns={"transactions": "Compraventas", "new_leases": "Nuevos contratos"}
            )
        )
        st.caption("Δ volúmenes (compraventas, nuevos contratos de alquiler)")

    st.subheader("Volúmenes y tenencia")
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(
            frame[["transactions", "new_leases"]].rename(
                columns={"transactions": "Compraventas", "new_leases": "Nuevos contratos"}
            )
        )
    with c2:
        st.line_chart(
            frame[["ownership_rate", "tenant_share", "seeker_share"]].rename(
                columns={
                    "ownership_rate": "Propietarios",
                    "tenant_share": "Inquilinos",
                    "seeker_share": "Buscando vivienda",
                }
            )
        )


if __name__ == "__main__":
    main()
