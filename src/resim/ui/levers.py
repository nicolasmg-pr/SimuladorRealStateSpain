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
        # REWRITTEN 2026-09-17. The text had gone stale at §7.2: it still reported the arbitrage
        # condition's +53.6% rent RISE and its three failing tests, both of which §7.2b repaired.
        #
        # REWRITTEN AGAIN 2026-09-18, and stale for the same reason: §5b.3 landed that morning and
        # the panel still announced the state of the night before — G1 at 3,655 over a 3,2 ceiling,
        # the flow/stock divergence, the channel's refinement "stopped", and, in the other tab, a
        # deferral justified by a gate that is no longer red. `reference_rent` was an EWMA at
        # weight 0.1 (mean lag 9 quarters) against a declared 5% discount, so the realised discount
        # read −20.7% and the cap bound on EVERY unit instead of the upper tail; with the parameter
        # honoured the price leg lands inside all three evaluations and G1 reads 1.061. Suite:
        # 181 passed, 8 xfailed, 0 failed.
        #
        # What does not change across any of these rewrites: NEITHER tab is ever shown without a
        # caveat. A silent tab reads as a sound one, which is the error the 2026-09-16 note
        # guarded — and a green suite is the moment that error is easiest to make. Numbers here are
        # quoted from the limits register in `docs/validation.md` ("Zero failures, and exactly what
        # was changed to get there", 2026-09-18); the UI computes none of them (CLAUDE.md).
        if params["index_binds_all"]:
            st.info(
                "**Bajo la Ley 11/2020 el precio ya es reportable como cantidad; el tamaño de la "
                "respuesta de oferta, no.** §5b.3 (2026-09-18) corrigió un desacuerdo de factor "
                "cuatro entre la especificación y el código: el índice de referencia se construía "
                "como una media exponencial de retardo medio 9 trimestres, así que el descuento "
                "realizado en la activación era del **−20,7%** frente al **5%** declarado, y el "
                "tope mordía en **todas** las viviendas en vez de en la cola alta. Con el "
                "parámetro respetado, el tope recorta la renta de los contratos un **−6,84%**, "
                "dentro de las tres evaluaciones independientes que **coinciden** en el precio "
                "(−4/−6% [Jofre-Monseny, Martínez-Mazza y Segú 2023]; −6/−7% en anuncios "
                "[Kholodilin et al. 2022]; −3,7/−6,4% [Generalitat, año 1]), donde antes marcaba "
                "−20,6%. El co-movimiento Δln contratos / Δln renta queda en **1,061**, dentro del "
                "vano 0,07–3,2 (Monràs, CEPR DP20018, feb. 2025), y no depende del dial: en todo "
                "el rango fuenteado de ventas por agencia (0,40–0,85) la renta se queda fija en "
                "−6,84% y el co-movimiento va de 0,85 a 1,27, dentro del vano en los cinco puntos.",
                icon="📐",
            )
            st.warning(
                "**Lo que sigue sin ser un resultado: la magnitud de la retirada de oferta.** Ahí "
                "la literatura no coincide, y el modelo no puede coincidir con ella. Dos de los "
                "tres estudios registrados no encuentran efecto de oferta alguno (Jofre-Monseny "
                "et al.; Kholodilin et al., sin efecto en anuncios) frente al −10% a −20% de "
                "contratos de Monràs. El modelo da **−7,24%**: dentro del vano que admite la "
                "evidencia y por debajo de todo lo que mide Monràs — dentro de la evidencia, no "
                "un ajuste a ella. La prueba que lo cubre se ensanchó ese mismo día a ese vano, "
                "por la regla de sesgo de CLAUDE.md (una estimación disputada es un rango, nunca "
                "un valor resuelto), así que **acota** la cifra, no la confirma. Detalle y "
                "límites en docs/validation.md.",
                icon="⚠️",
            )
        else:
            # F4 RAN 2026-09-18, once, and did not fire. §7.2's "Reporting consequence" says in
            # as many words that this warning is then rewritten "to say what may be read rather
            # than only what may not" — so it is. But the consequence is discharged LEG BY LEG,
            # because that is how F4 passed: the lease leg carries a sign (t = −3.59, 8/10 seeds)
            # and the rent leg lands on the span's zero end (|mean| < 1 se, 4/10 seeds positive),
            # which is Pérez García's endpoint reproduced and not a measured fall. Pre-registered
            # at 4c4eb58 before the run at 21a5623; record in the prereg file and in
            # docs/validation.md ("F4, the one shot, taken"). The UI computes none of it.
            st.info(
                "**Bajo la ley vigente se puede leer una dirección, y sólo en los contratos.** La "
                "prueba fuera de muestra de este régimen (§7.2, F4) se corrió **una vez**, el "
                "2026-09-18, con el vano y el diseño registrados por escrito **antes** de "
                "ejecutarla. No disparó: el tope **no** sube las rentas — lo que este escenario "
                "publicaba antes (+16,6%) era un artefacto anterior a §7.2b y §5b.3. Diez "
                "semillas, parámetros de serie: nuevos contratos **−8,06%** (t = −3,59, "
                "negativo en 8 de 10 semillas), dentro del vano que va de +1.374 contratos "
                "[registro, O-HB nº 4] a −13% de arrendamientos [Pérez García]. Eso es una "
                "**dirección**: el tope contrae los contratos nuevos.",
                icon="🧭",
            )
            st.warning(
                "**Y no se puede leer nada más: ni el tamaño, ni el efecto sobre la renta.** La "
                "renta de los contratos marca −0,79%, indistinguible de cero (error típico 1,59pp,"
                " cuatro de las diez semillas en positivo). Eso reproduce el extremo «efecto ≈0» "
                "del vano y **no** es la medida de una caída: aquí no hay dirección que reportar, "
                "sólo la ausencia de la subida que F4 buscaba. **Ninguna cifra de este panel es "
                "una cantidad citable** — la categoría se fijó en «dirección, nunca magnitud» "
                "antes de conocer los números. Recuerda además que la ley topa a otra población: "
                "al particular lo ata su propio contrato anterior más el IRAV, no el índice, y "
                "los particulares tienen el 85–92% del parque. Registro completo en "
                "docs/prereg/2026-09-18-f4-ley-12-2023-out-of-sample.md.",
                icon="⚠️",
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
            "País Vasco y Andalucía abajo. Desde §5b.3 (2026-09-18) este dial ya NO recorre el "
            "vano de Monràs: barrido de 0,40 a 0,85, la renta no se mueve (−6,84% en los cinco "
            "puntos) y el co-movimiento va sólo de 1,27 a 0,85, dentro del vano en todo el rango "
            "(OLS 0,07 · IV 2,0 · techo 3,2).",
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
            "del coste de salida de cada casero — y desde §5b.3 (2026-09-18) la magnitud del "
            "precio también es reportable (−6,84%, dentro de las tres evaluaciones). Esta cifra "
            "concreta de cobertura parcial, en cambio, sigue sin remedir bajo ninguna de las dos "
            "revisiones. docs/validation.md T7.",
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
