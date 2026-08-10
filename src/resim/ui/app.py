"""Streamlit app — the demo surface (UI in Spanish).

Run: streamlit run src/resim/ui/app.py

Three tabs: explore one policy in depth (with actor-reaction explanations),
compare all policies on one indicator, and a plain-language guide to the model.
Sidebar: baseline knobs, one policy lever, and the *disputed* parameters exposed as
sliders labeled with the competing estimates (bias-control rule: the model spans the
disagreement, the user explores it).

Rule: this file only calls into resim.scenario, resim.engine, and resim.metrics.
Any number it computes itself is a number the tests do not cover.
"""

from __future__ import annotations

import streamlit as st

from resim import metrics
from resim.config import SimConfig
from resim.engine import Engine
from resim.scenario import Scenario
from resim.ui import charts, chat, texts
from resim.ui.levers import LEVER_CLASSES, lever_params

# Fixed color per policy: assigned once over the full lever list, so a policy keeps
# its color no matter which subset is selected in the comparator.
POLICY_COLORS = charts.palette_for(list(LEVER_CLASSES))

COMPARE_INDICATORS: dict[str, tuple[str, str, str]] = {
    # label -> (metrics column, y-axis title, value format)
    "Alquiler nuevo — zona tensionada (€/mes)": ("rent_tensioned", "Δ €/mes", ",.0f"),
    "Precio — zona tensionada (€)": ("price_tensioned", "Δ €", ",.0f"),
    "Precio — media nacional (€)": ("price_national", "Δ €", ",.0f"),
    "Compraventas (uds./trimestre)": ("transactions", "Δ operaciones", ",.0f"),
    "Nuevos contratos de alquiler": ("new_leases", "Δ contratos", ",.0f"),
    "Hogares buscando vivienda": ("seeker_share", "Δ proporción", ".2%"),
    "Inquilinos con sobrecarga (>40%)": ("rent_overburden_share", "Δ proporción", ".2%"),
    "Vivienda vacía": ("vacancy_rate", "Δ proporción", ".2%"),
}


def _config(seed: int, ticks: int, momentum: float) -> SimConfig:
    import dataclasses

    base = SimConfig.baseline(seed=seed, ticks=ticks)
    return dataclasses.replace(
        base, market=dataclasses.replace(base.market, expectation_momentum=momentum)
    )


@st.cache_data(show_spinner="Ejecutando simulación base…")
def run_baseline(seed: int, ticks: int, momentum: float):
    base = _config(seed, ticks, momentum)
    return metrics.to_frame(Engine(Scenario(name="baseline", baseline=base)).run())


@st.cache_data(show_spinner="Ejecutando escenario…")
def run_scenario(seed: int, ticks: int, lever: str, lever_params: dict, momentum: float):
    base = _config(seed, ticks, momentum)
    intervention = LEVER_CLASSES[lever](**lever_params)
    scenario = Scenario(name=lever, baseline=base, interventions=(intervention,))
    return metrics.to_frame(Engine(scenario).run())


def run(seed: int, ticks: int, lever: str, lever_params: dict, momentum: float):
    baseline_frame = run_baseline(seed, ticks, momentum)
    if lever == "ninguna":
        return baseline_frame, None
    return baseline_frame, run_scenario(seed, ticks, lever, lever_params, momentum)


def chart_block(
    chart_id: str,
    frame,
    columns: dict[str, str],
    *,
    y_title: str,
    colors: dict[str, str] | None = None,
    policy_start: int | None = None,
    zero_line: bool = False,
    y_format: str = ",.0f",
) -> None:
    """One chart + its two companions: 'how do I read this' and the data table."""
    st.altair_chart(
        charts.line_chart(
            frame,
            columns,
            y_title=y_title,
            colors=colors,
            policy_start=policy_start,
            zero_line=zero_line,
            y_format=y_format,
        ),
        width="stretch",
    )
    c1, c2 = st.columns(2)
    with c1, st.expander("❓ ¿Cómo leo este gráfico?"):
        st.markdown(texts.CHART_HELP[chart_id])
    with c2, st.expander("📋 Ver los datos"):
        st.dataframe(charts.data_table(frame, columns), width="stretch")


def kpi_row(frame, baseline_frame) -> None:
    """Headline indicators at the end of the run, with delta vs baseline if any."""
    last = frame.iloc[-1]
    base_last = baseline_frame.iloc[-1] if baseline_frame is not None else None

    def pp_delta(col: str) -> str | None:
        if base_last is None:
            return None
        return f"{(last[col] - base_last[col]) * 100:+.1f} pp vs base"

    cols = st.columns(4)
    cols[0].metric(
        "Tasa de propiedad",
        f"{last['ownership_rate']:.1%}",
        delta=pp_delta("ownership_rate"),
        help=texts.KPI_HELP["ownership_rate"],
    )
    cols[1].metric(
        "Precio / renta disponible",
        f"{last['price_to_income']:.1f}",
        delta=(
            None
            if base_last is None
            else f"{last['price_to_income'] - base_last['price_to_income']:+.2f} vs base"
        ),
        delta_color="inverse",
        help=texts.KPI_HELP["price_to_income"],
    )
    cols[2].metric(
        "Sobrecarga de alquiler (>40%)",
        f"{last['rent_overburden_share']:.1%}",
        delta=pp_delta("rent_overburden_share"),
        delta_color="inverse",
        help=texts.KPI_HELP["rent_overburden_share"],
    )
    cols[3].metric(
        "Vivienda vacía",
        f"{last['vacancy_rate']:.1%}",
        delta=pp_delta("vacancy_rate"),
        delta_color="inverse",
        help=texts.KPI_HELP["vacancy_rate"],
    )
    if base_last is not None:
        st.caption("Las flechas comparan el final del escenario con la base sin política.")


def actor_reactions(lever: str) -> None:
    """How each actor responds to the chosen policy, and the resulting market chain."""
    st.subheader("¿Cómo reaccionan los actores?")
    st.markdown(texts.POLICY_SUMMARIES[lever])
    for actor, reaction in texts.ACTOR_REACTIONS[lever]:
        with st.expander(actor):
            st.markdown(reaction)


def explore_tab(lever: str, params: dict, baseline_frame, scenario_frame) -> None:
    frame = scenario_frame if scenario_frame is not None else baseline_frame
    policy_start = params.get("start_tick") if scenario_frame is not None else None

    if lever == "ninguna":
        st.info(
            "Estás viendo la **simulación base**: el mercado sin ninguna política "
            "nueva. Elige una intervención en la barra lateral para ver su efecto y "
            "cómo reaccionan los actores."
        )
    else:
        actor_reactions(lever)
        st.divider()

    kpi_row(frame, baseline_frame if scenario_frame is not None else None)

    st.subheader("Precios por zona (€, índice ajustado por calidad)")
    chart_block(
        "precios",
        frame,
        charts.zone_columns("price"),
        y_title="€",
        colors=charts.ZONE_COLORS,
        policy_start=policy_start,
    )
    st.subheader("Alquileres por zona (€/mes, oferta de nuevos contratos)")
    chart_block(
        "alquileres",
        frame,
        charts.zone_columns("rent"),
        y_title="€/mes",
        colors=charts.ZONE_COLORS,
        policy_start=policy_start,
    )

    if scenario_frame is not None:
        st.subheader(f"Efecto de la política — escenario menos base ({lever})")
        st.caption(
            "Misma semilla, mismo mercado: la única diferencia entre las dos "
            "simulaciones es la política. Todo lo que ves aquí es efecto causal "
            "*dentro del modelo*."
        )
        diff = metrics.compare(baseline_frame, scenario_frame)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Δ precio por zona (€)**")
            chart_block(
                "diff_precio",
                diff,
                charts.zone_columns("price"),
                y_title="Δ €",
                colors=charts.ZONE_COLORS,
                policy_start=policy_start,
                zero_line=True,
            )
        with c2:
            st.markdown("**Δ alquiler por zona (€/mes)**")
            chart_block(
                "diff_alquiler",
                diff,
                charts.zone_columns("rent"),
                y_title="Δ €/mes",
                colors=charts.ZONE_COLORS,
                policy_start=policy_start,
                zero_line=True,
            )
        st.markdown("**Δ volúmenes (compraventas, nuevos contratos)**")
        chart_block(
            "diff_volumenes",
            diff,
            {"transactions": "Compraventas", "new_leases": "Nuevos contratos"},
            y_title="Δ operaciones",
            policy_start=policy_start,
            zero_line=True,
        )

    st.subheader("Volúmenes y tenencia")
    c1, c2 = st.columns(2)
    with c1:
        chart_block(
            "volumenes",
            frame,
            {"transactions": "Compraventas", "new_leases": "Nuevos contratos"},
            y_title="Operaciones/trimestre",
            policy_start=policy_start,
        )
    with c2:
        chart_block(
            "tenencia",
            frame,
            {
                "ownership_rate": "Propietarios",
                "tenant_share": "Inquilinos",
                "seeker_share": "Buscando vivienda",
            },
            y_title="Proporción de hogares",
            policy_start=policy_start,
            y_format=".1%",
        )


def compare_tab(seed: int, ticks: int, momentum: float) -> None:
    st.subheader("Comparar políticas")
    st.caption(
        "Cada política se simula por separado sobre la misma base, con sus "
        "parámetros por defecto (los puntos medios de la evidencia) y empezando en "
        "el trimestre 8. El gráfico muestra la diferencia frente a no hacer nada."
    )
    selected = st.multiselect(
        "Políticas a comparar",
        list(LEVER_CLASSES),
        default=["tope de alquiler", "vivienda pública", "impuesto a la vivienda vacía"],
    )
    indicator = st.selectbox("Indicador", list(COMPARE_INDICATORS))
    if not selected:
        st.info("Elige al menos una política.")
        return

    column, y_title, y_format = COMPARE_INDICATORS[indicator]
    deltas = {}
    final_rows = {}
    for lever in selected:
        baseline_frame, scenario_frame = run(seed, ticks, lever, {}, momentum)
        diff = metrics.compare(baseline_frame, scenario_frame)
        deltas[lever] = diff[column]
        final_rows[lever] = diff.iloc[-1]

    import pandas as pd

    delta_frame = pd.DataFrame(deltas)
    chart_block(
        "comparador",
        delta_frame,
        {lever: lever for lever in selected},
        y_title=y_title,
        colors={lever: POLICY_COLORS[lever] for lever in selected},
        policy_start=8,
        zero_line=True,
        y_format=y_format,
    )

    st.subheader("Resumen al final de la simulación")
    st.caption("Diferencia frente a la base en el último trimestre, por política.")
    summary = pd.DataFrame(
        {
            "Δ alquiler tensionada (€/mes)": {
                k: f"{v['rent_tensioned']:+,.0f}" for k, v in final_rows.items()
            },
            "Δ precio tensionada (€)": {
                k: f"{v['price_tensioned']:+,.0f}" for k, v in final_rows.items()
            },
            "Δ nuevos contratos": {k: f"{v['new_leases']:+,.0f}" for k, v in final_rows.items()},
            "Δ buscando vivienda (pp)": {
                k: f"{v['seeker_share'] * 100:+.1f}" for k, v in final_rows.items()
            },
            "Δ sobrecarga alquiler (pp)": {
                k: f"{v['rent_overburden_share'] * 100:+.1f}" for k, v in final_rows.items()
            },
        }
    )
    st.dataframe(summary, width="stretch")
    st.caption(
        "⚠️ Ninguna columna es «la buena» por sí sola: una política puede bajar el "
        "alquiler y a la vez dejar a más hogares sin encontrar piso. Para explorar "
        "los parámetros en disputa de cada política, usa la pestaña «Explorar»."
    )


def how_it_works_tab() -> None:
    st.markdown(texts.MODEL_EXPLANATION)


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
        seed = st.number_input(
            "Semilla",
            0,
            10_000,
            42,
            help="Fija el azar de la simulación. Misma semilla = mismo resultado. "
            "Cámbiala para comprobar que una conclusión no depende de la suerte.",
        )
        ticks = st.slider("Trimestres", 20, 80, 60)
        st.caption(f"≈ **{ticks / 4:.0f} años** de simulación ({ticks} trimestres)")

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
        params = lever_params(lever)

    baseline_frame, scenario_frame = run(seed, ticks, lever, params, momentum)

    tab_explore, tab_compare, tab_help = st.tabs(
        ["📈 Explorar una política", "⚖️ Comparar políticas", "❓ Cómo funciona el modelo"]
    )
    with tab_explore:
        explore_tab(lever, params, baseline_frame, scenario_frame)
    with tab_compare:
        compare_tab(seed, ticks, momentum)
    with tab_help:
        how_it_works_tab()

    chat.render(
        chat.screen_context(
            seed=seed,
            ticks=ticks,
            momentum=momentum,
            lever=lever,
            params=params,
            baseline_frame=baseline_frame,
            scenario_frame=scenario_frame,
        )
    )


if __name__ == "__main__":
    main()
