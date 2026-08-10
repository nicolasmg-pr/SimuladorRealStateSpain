"""Sidebar widgets for each policy lever.

One function per concern: `lever_params(lever)` renders the sliders for the chosen
lever and returns the kwargs for its Intervention class. Help texts keep the
bias-control rule visible: disputed parameters name the competing estimates.
"""

from __future__ import annotations

import streamlit as st

from resim.scenario import (
    DemandSubsidy,
    LandRelease,
    PublicHousing,
    RateShock,
    RentCap,
    TouristRestriction,
    TransactionTax,
    VacancyTax,
)

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


def lever_params(lever: str) -> dict:
    """Render the sliders for `lever` and return the Intervention kwargs."""
    params: dict = {}
    if lever == "ninguna":
        return params
    params["start_tick"] = st.slider(
        "Trimestre de inicio",
        1,
        40,
        8,
        help="Cuándo entra en vigor la política. Antes de ese trimestre, el escenario "
        "es idéntico a la base.",
    )
    st.caption(f"≈ año {params['start_tick'] / 4:.1f} de la simulación")

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
            help="Recargo IBI ≈0,001–0,005 · impuesto catalán ≈0,003–0,01 · Vancouver ≈0,01–0,03.",
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
    return params
