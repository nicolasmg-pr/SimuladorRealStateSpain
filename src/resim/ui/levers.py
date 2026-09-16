"""Sidebar widgets for each policy lever.

One function per concern: `lever_params(lever)` renders the sliders for the chosen
lever and returns the kwargs for its Intervention class. Help texts keep the
bias-control rule visible: disputed parameters name the competing estimates.
"""

from __future__ import annotations

import streamlit as st

from resim.scenario import (
    CreditCrunch,
    DemandSubsidy,
    LabourShock,
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
    # Condiciones de contorno, no políticas: nadie las elige. Están aquí porque son las dos
    # entradas del episodio 2008-13 y el usuario tiene que poder moverlas (model-spec §6c).
    "restricción de crédito": CreditCrunch,
    "shock de desempleo": LabourShock,
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
        # WHICH LAW. Added 2026-09-15 with model-spec §5b.1: the two statutes are different
        # instruments and the model is only calibrated in one of them. Without this control the
        # UI silently ran the statute whose size the model may not report.
        regime = st.radio(
            "Qué ley se aplica",
            ("Ley 11/2020 — Cataluña 2020–22", "Ley 12/2023 — la ley vigente"),
            help="Ley 11/2020 ataba el índice de referencia a TODOS los caseros, y es el "
            "mundo que miden los tres estudios catalanes que los dos parámetros de abajo "
            "recorren. Ley 12/2023 sólo obliga al gran tenedor (≥10 viviendas, ≥5 en la "
            "zona); al resto lo topa su propio contrato anterior más el IRAV, y nada si no "
            "hubo contrato en cinco años. Los particulares tienen el 85–92% del parque, así "
            "que la diferencia es casi todo el mercado.",
        )
        params["index_binds_all"] = regime.startswith("Ley 11/2020")
        if not params["index_binds_all"]:
            st.warning(
                "**El tamaño de este resultado no es reportable.** Con el índice atando a un "
                "casero de cada diez, el canal que domina es la retirada de oferta — y su "
                "hazard se identificó en el otro régimen, donde el índice ataba a todos. "
                "Nadie lo ha vuelto a identificar aquí: el modelo llega a subir las rentas "
                "un 16,6%, y eso es una extrapolación fuera de régimen, no una predicción. "
                "Léase el signo, no el número (model-spec §5b.1).",
                icon="⚠️",
            )
        params["selling_cost_share"] = st.slider(
            "Coste de vender (fracción del precio)",
            0.01,
            0.07,
            0.02,
            0.005,
            help="Umbral de salida de §7.2: el casero vende cuando el déficit acumulado del "
            "alquiler topado supera este coste. Los dos extremos son dos rutas de venta reales, "
            "no un margen de error: **0,01 = venta propia** (sólo matriz, plusvalía y aranceles; "
            "Código Civil art. 1455) y **0,07 = venta con agencia** (comisión 3–5% + IVA, redes "
            "grandes hasta 7%). El valor fundamentado es 0,04 — pondera las dos rutas por la "
            "cuota de "
            "intermediación: las agencias intervienen en el 64% de las compraventas de segunda "
            "mano (Fotocasa) y ~70% del total (idealista). El modelo aún envía 0,02: moverlo "
            "descoloca tres canales ajenos al tope, y ese cambio va en su propia rama. "
            "No incluye el IRPF de la ganancia.",
        )
        params["holding_years"] = st.slider(
            "Horizonte de la decisión (años)",
            3.0,
            10.0,
            5.0,
            0.5,
            help="Sobre cuántos años suma el casero el déficit antes de decidir. Con estos "
            "dos se recorre el vano de Monràs (Δln contratos/Δln renta: OLS 0,07, IV 2,0), "
            "que el modelo ahora PRODUCE en vez de recibirlo como dial (model-spec §7.2).",
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
        params["coverage"] = st.slider(
            "Cobertura: parte de la zona declarada tensionada",
            0.1,
            1.0,
            1.0,
            0.05,
            help="La ley se activa municipio a municipio. 1,0 ≈ Cataluña 2024 (≈90% de su "
            "población). España a julio de 2026: 317 municipios en 5 CCAA (Cataluña 271, "
            "Euskadi 18, Navarra 21, Galicia 2, Asturias 5), 9,3M de personas = 19% del "
            "país ≈ 0,42 de la zona tensionada del modelo (BOE 29-jul-2026). Madrid, "
            "Andalucía, Valencia, Murcia y Castilla y León: 0. ⚠️ Con cobertura parcial hay "
            "que mirar los dos segmentos por separado: el alquiler medio del conjunto mezcla "
            "pisos topados y no topados y se mueve con la mezcla. Con 0,42 y elasticidad 2 el "
            "segmento declarado queda plano y pierde un 37% de contratos, mientras el no "
            "declarado firma un 7% más a precios un 8% más altos — el desbordamiento que "
            "muestra Cataluña (zonas tensionadas +1,6% frente a +9,4% fuera). "
            "docs/validation.md T7.",
        )
    elif lever == "impuesto de transmisiones (ITP)":
        params["itp_delta"] = st.slider(
            "Cambio del ITP (pp del precio)",
            -0.06,
            0.10,
            0.02,
            0.01,
            help="Evidencia: −4% a −15% de compraventas por +1pp (estudios de "
            "Reino Unido, Alemania, Países Bajos y Canadá). Se aplica a todos los "
            "compradores, hogares y compradores al contado incluidos.",
        )
        params["investor_delta"] = st.slider(
            "Recargo a grandes tenedores / personas jurídicas (pp)",
            0.0,
            0.15,
            0.0,
            0.01,
            help="Cataluña: 20% de TPO en compras de edificios enteros y de grandes "
            "tenedores (DL 5/2025; Ley 11/2026, en vigor 14-jul-2026) frente al 10% "
            "general ⇒ +0,10. Sólo alcanza al gran inversor del modelo.",
        )
        params["foreign_delta"] = st.slider(
            "Recargo a compradores no residentes (pp)",
            0.0,
            1.0,
            0.0,
            0.05,
            help="El «impuesto del 100%» a compradores extracomunitarios (anunciado en "
            "enero de 2025, atascado en el Congreso desde marzo de 2026) sería ≈ +0,90 "
            "sobre un ITP del 10%. Baleares intentó prohibir la compra a no residentes y "
            "el Parlament lo rechazó (feb-2026). Es una propuesta, no ley.",
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
            "convergencia del Banco de España. La entrega REAL va muy por debajo: 5.215 "
            "calificaciones definitivas en 1T 2026 (+74%, el mejor trimestre desde 2012) "
            "≈ 2–3 unidades del modelo por trimestre; Casa 47 tenía 800 viviendas en su "
            "portal el 7-sep-2026 y 42.000 de la Sareb por movilizar.",
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
        params["phaseout_rate"] = st.slider(
            "Extinción de licencias /año",
            0.0,
            1.0,
            0.25,
            help="Referencia observada sin extinción formal: el parque turístico del INE cayó "
            "−10,7% interanual hasta mayo de 2026 (341.001 viviendas) tras el registro único "
            "y las moratorias municipales ⇒ ≈0,11/año. Barcelona: cero licencias en 2028; "
            "Málaga: 3 años sin licencias nuevas desde jul-2026.",
        )
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

    elif lever == "restricción de crédito":
        params["ltv_delta"] = st.slider(
            "Cambio en el LTV máximo",
            -0.30,
            0.0,
            -0.10,
            0.01,
            help="En 2008-13 el LTV concedido bajó del 0,80 en el que se amontonaban las "
            "operaciones hacia 0,60 [BdE IEF, dossier bank §4].",
        )
        params["dsti_delta"] = st.slider(
            "Cambio en el DSTI máximo",
            -0.15,
            0.0,
            -0.05,
            0.01,
            help="Cuota máxima sobre renta neta. El baseline es 0,35.",
        )
        params["spread_delta"] = st.slider(
            "Cambio en el diferencial",
            0.0,
            0.04,
            0.01,
            0.005,
            help="Puntos sobre euríbor. Los tres se mueven juntos porque así ocurrió: "
            "no es un barrido sobre combinaciones que nunca se dieron.",
        )

    elif lever == "shock de desempleo":
        params["rate"] = st.slider(
            "Hogares con todos sus activos en paro",
            0.02,
            0.20,
            0.15,
            0.005,
            help="NO es la tasa de paro individual: es la serie de hogares del INE (EPA "
            "tabla 65276), que es la que corresponde a un hogar modelado como una sola "
            "unidad de renta. 3,15% en el pico de 2007, 15,02% en 2013T1, 5,28% en 2026T2.",
        )
        params["exit_hazard"] = st.slider(
            "Probabilidad trimestral de salir del paro",
            0.10,
            0.30,
            0.25,
            0.01,
            help="Se deduce del paro de larga duración: (1−f)⁴ = la proporción de parados "
            "de más de un año. 32,1% (2025) ⇒ 0,25; 52,8% (pico de 2014) ⇒ 0,15.",
        )
    return params
