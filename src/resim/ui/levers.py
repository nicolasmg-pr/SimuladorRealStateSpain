"""Sidebar widgets for each policy lever.

One function per concern: `lever_params(lever)` renders the sliders for the chosen
lever and returns the kwargs for its Intervention class. Help texts keep the
bias-control rule visible: disputed parameters name the competing estimates.
"""

from __future__ import annotations

import streamlit as st

from resim.config import CapResponseConfig
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

# Slider bounds for the rent-cap lever's agency-share dial read from here, not from literals:
# `CapResponseConfig.intermediation_share_regional_range` is the WIDE regional band (model-spec
# §7.2b), `intermediation_share` its national default.
_cap_defaults = CapResponseConfig()


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
            "mundo que miden los tres estudios catalanes que el parámetro de abajo "
            "recorre. Ley 12/2023 sólo obliga al gran tenedor (≥10 viviendas, ≥5 en la "
            "zona); al resto lo topa su propio contrato anterior más el IRAV, y nada si no "
            "hubo contrato en cinco años. Los particulares tienen el 85–92% del parque, así "
            "que la diferencia es casi todo el mercado.",
        )
        params["index_binds_all"] = regime.startswith("Ley 11/2020")
        # The warning is UNCONDITIONAL since 2026-09-16 and stays so: it used to fire only for
        # Ley 12/2023, on the ground that the withdrawal hazard had been identified in the other
        # regime, and §7.2 retired that hazard for a condition that broke BOTH.
        #
        # REWRITTEN 2026-09-17. The text below had gone stale at §7.2: it still reported the
        # arbitrage condition's +53.6% rent RISE and its three failing tests, both of which §7.2b
        # repaired. The two regimes no longer carry the same defect, so they no longer carry the
        # same text — but what does not change is that NEITHER tab is ever shown without a caveat.
        # A silent tab reads as a sound one, which is the error the 2026-09-16 note guarded.
        # Numbers here are quoted from the limits register in `docs/validation.md`, including its
        # own same-day correction of G1's ceiling; the UI computes none of them (CLAUDE.md).
        if params["index_binds_all"]:
            st.warning(
                "**Bajo la Ley 11/2020 la dirección es reportable; la magnitud no.** §7.2b "
                "repartió el coste de salida entre caseros y le dio al tope su vida estatutaria: "
                "con eso el signo de la renta sale correcto en las **diez** semillas y desaparece "
                "la frontera de régimen que antes invertía el resultado según el ancla de "
                "crecimiento de precios. Lo que no se reparó es el tamaño. El modelo responde con "
                "un co-movimiento Δln contratos / Δln renta de **3,655**, por encima del **3,2** "
                "que es el techo del rango IV publicado (Monràs, CEPR DP20018, feb. 2025). "
                "Ninguna cifra de este panel puede citarse como cantidad.",
                icon="⚠️",
            )
            st.info(
                "**Lo que sí se ha medido**, y por qué el error queda acotado: el exceso es de "
                "≈14% sobre el techo del rango publicado, no un múltiplo — flujo de nuevos "
                "contratos **−48,2%** con la renta en **−16,5%**, contra el −10% a −20% que "
                "reporta el propio paper. Y no se cierra recalibrando: en el extremo alto de la "
                "banda regional fuenteada (85% de ventas por agencia) los contratos aún caen "
                "26,8%. Queda abierta una divergencia sin identificar entre el flujo y el stock, "
                "factor ≈3,7; el exceso de rotación quedó descartado como causa (rotación medida "
                "14,5%/año, tenencia media 6,9 años). El refinamiento de este canal se **paró** el "
                "2026-09-17: a partir de ahí son experimentos, no ajuste. Detalle y límites en "
                "docs/validation.md.",
                icon="🔎",
            )
        else:
            st.error(
                "**Este régimen no está medido — aquí no se reporta ni la dirección.** La prueba "
                "fuera de muestra de la Ley 12/2023 (§7.2, F4) está aplazada por diseño: no corre "
                "hasta que las pruebas del régimen calibrado estén verdes, y G1 sigue en rojo. Lo "
                "que ves sale de un canal de retirada de oferta cuyo tamaño ya falla en el "
                "régimen contra el que **sí** está calibrado, aplicado además a una ley que topa a "
                "otra población: al particular lo ata su propio contrato anterior más el IRAV, no "
                "el índice. Nada de este panel es un resultado.",
                icon="⛔",
            )
        # RETIRED (2026-09-16, §7.2b). Was two sliders: `selling_cost_share` ("Coste de vender
        # (fracción del precio)", 0.01-0.07) and `holding_years` ("Horizonte de la decisión
        # (años)", 3.0-10.0) — the two structural parameters that carried the supply-response
        # dispute under §7.2's arbitrage condition. `selling_cost_share` is no longer the
        # landlord's exit threshold (that's `exit_cost_for`, driven by the per-unit
        # `sale_route_draw`) and `holding_years` no longer exists (the shortfall now accrues
        # over the cap's own statutory term). In their place: the share of landlords who sell
        # through an agency, below. Kept as a dated note rather than deleted outright: this
        # project keeps the archaeology of its parameters. See model-spec.md §7.2b, "UI".
        params["intermediation_share"] = st.slider(
            "Caseros que venden por agencia",
            _cap_defaults.intermediation_share_regional_range[0],
            _cap_defaults.intermediation_share_regional_range[1],
            _cap_defaults.intermediation_share,
            0.01,
            help="Decide cuántos caseros tienen una salida BARATA, y con ello cuántos se "
            "retiran ante un tope dado (model-spec §7.2b). Medido: las agencias intermedian "
            "el 64% de las compraventas de segunda mano (Fotocasa) y ~70% del total "
            "(idealista). El rango va más allá de esas dos fuentes a propósito, porque la "
            "dispersión regional es grande — Murcia, Navarra y Baleares arriba; Extremadura, "
            "País Vasco y Andalucía abajo. Es el dial que recorre el vano de Monràs "
            "(Δln contratos/Δln renta: OLS 0,07, IV 2,0).",
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
            "pisos topados y no topados y se mueve con la mezcla. Medido ANTES de §7.2 "
            "(2026-09-16), bajo el hazard fitted y el dial de elasticidad ya retirados: con "
            "0,42 y elasticidad 2 el segmento declarado quedaba plano y perdía un 37% de "
            "contratos, mientras el no declarado firmaba un 7% más a precios un 8% más "
            "altos — el desbordamiento que muestra Cataluña (zonas tensionadas +1,6% frente "
            "a +9,4% fuera). Desde §7.2b la elasticidad ya no es un dial — es un resultado "
            "del coste de salida de cada casero — y el signo del alquiler sale correcto en "
            "las diez semillas, aunque su magnitud siga sin ser reportable; esta cifra "
            "concreta queda sin remedir. docs/validation.md T7.",
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
