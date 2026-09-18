"""Streamlit app — the demo surface (UI in Spanish).

Run: streamlit run src/resim/ui/app.py

Five tabs: explore one policy in depth (with actor-reaction explanations), compare all
policies on one indicator, contrast the model's national figures against what Banco de
España actually publishes, show the phase-0 diagnostic targets (including the four that
still carry a live strict xfail), and a plain-language guide to the model.
Sidebar: baseline knobs, one policy lever, and the *disputed* parameters exposed as
sliders labeled with the competing estimates (bias-control rule: the model spans the
disagreement, the user explores it).

Rule: this file only calls into resim.scenario, resim.engine, resim.metrics and
resim.benchmarks. Any number it computes itself is a number the tests do not cover — the
BdE contrast in particular is computed in benchmarks.py, including its basis conversions,
precisely so the comparison arithmetic is testable.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from resim import benchmarks, diagnostics, metrics
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
    "Accesibilidad de la vivienda (% que puede comprar)": ("buyer_access", "Δ proporción", ".2%"),
    "Esfuerzo teórico de compra (% renta disponible)": ("purchase_effort", "Δ proporción", ".2%"),
    "Vivienda vacía": ("vacancy_rate", "Δ proporción", ".2%"),
}


# The settled tail every number in docs/validation.md is quoted on. The UI used the LAST TICK
# until 2026-09-18, which is one draw of a noisy path rather than a level.
TAIL_WINDOW = 20


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


# Seeds are consecutive from the sidebar's seed. Consecutive rather than drawn: the user can
# reproduce any single one of them by typing it into the seed box, which a random pool would
# not allow, and `SimConfig.baseline` seeds a fresh Generator per run so neighbouring seeds
# are as independent as distant ones.
def seed_pool(seed: int, n_seeds: int) -> list[int]:
    return [int(seed) + k for k in range(int(n_seeds))]


def run_many(seed: int, n_seeds: int, ticks: int, lever: str, lever_params: dict, momentum: float):
    """One (baseline, scenario) frame pair per seed, plus the pooled medians to plot.

    Returns `(baselines, scenarios, pooled_baseline, pooled_scenario)`; the scenario entries
    are None when no lever is selected. Each underlying run is `@st.cache_data`-memoised, so
    raising the seed count re-uses everything already computed and only pays for the new ones.
    """
    seeds = seed_pool(seed, n_seeds)
    baselines = [run_baseline(s, ticks, momentum) for s in seeds]
    pooled_baseline = metrics.pool(baselines)
    if lever == "ninguna":
        return baselines, [], pooled_baseline, None
    scenarios = [run_scenario(s, ticks, lever, lever_params, momentum) for s in seeds]
    return baselines, scenarios, pooled_baseline, metrics.pool(scenarios)


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
    reference: pd.DataFrame | None = None,
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
            reference=reference,
        ),
        width="stretch",
    )
    c1, c2 = st.columns(2)
    with c1, st.expander("❓ ¿Cómo leo este gráfico?"):
        st.markdown(texts.CHART_HELP[chart_id])
    with c2, st.expander("📋 Ver los datos"):
        st.dataframe(charts.data_table(frame, columns), width="stretch")


def kpi_row(frame, baseline_frame, baselines=(), scenarios=()) -> None:
    """Headline indicators, pooled over seeds, with the seed spread attached to every delta.

    Two changes on 2026-09-18, both for the same reason: a single seed's delta is not an
    estimate. The LEVEL is the pooled median's settled tail rather than one seed's last tick —
    the basis docs/validation.md has always used, and the one the diagnostics panel quotes. The
    DELTA carries its half-range across seeds, and is greyed to "≈ 0" when it is smaller than
    that: an arrow the seed draw could flip is not a finding, and drawing it as green or red is
    the app asserting something the run does not support.

    `baselines`/`scenarios` are the per-seed frames. With fewer than two seeds there is no
    spread to quote, so the delta is shown bare and labelled as one seed.
    """
    tail = frame.tail(TAIL_WINDOW)
    pooled = len(baselines) > 1

    def delta_text(col: str, *, scale: float, unit: str, fmt: str) -> tuple[str | None, str]:
        """(text, colour) for one metric's delta. Colour 'off' greys it out."""
        if baseline_frame is None:
            return None, "normal"
        if not scenarios:
            return None, "normal"
        if not pooled:
            plain = (
                frame[col].tail(TAIL_WINDOW).mean() - baseline_frame[col].tail(TAIL_WINDOW).mean()
            ) * scale
            return f"{plain:{fmt}} {unit} (1 semilla)", "normal"
        median, half_range = metrics.pooled_delta(
            list(baselines), list(scenarios), col, tail=TAIL_WINDOW
        )
        median, half_range = median * scale, half_range * scale
        if not abs(median) > half_range:
            return f"≈ 0 {unit} · ±{half_range:{fmt.replace('+', '')}} entre semillas", "off"
        return f"{median:{fmt}} ± {half_range:{fmt.replace('+', '')}} {unit}", "normal"

    def metric(slot, label, col, *, value_fmt, scale, unit, fmt, inverse=False, help_key=None):
        text, colour = delta_text(col, scale=scale, unit=unit, fmt=fmt)
        slot.metric(
            label,
            f"{tail[col].mean():{value_fmt}}",
            delta=text,
            delta_color=("off" if colour == "off" else ("inverse" if inverse else "normal")),
            help=texts.KPI_HELP[help_key or col],
        )

    cols = st.columns(5)
    metric(
        cols[0],
        "Tasa de propiedad",
        "ownership_rate",
        value_fmt=".1%",
        scale=100.0,
        unit="pp",
        fmt="+.1f",
    )
    metric(
        cols[1],
        "Precio / renta disponible",
        "price_to_income",
        value_fmt=".1f",
        scale=1.0,
        unit="",
        fmt="+.2f",
        inverse=True,
    )
    metric(
        cols[2],
        "Sobrecarga de alquiler (>40%)",
        "rent_overburden_share",
        value_fmt=".1%",
        scale=100.0,
        unit="pp",
        fmt="+.1f",
        inverse=True,
    )
    metric(
        cols[3],
        "Accesibilidad de compra",
        "buyer_access",
        value_fmt=".1%",
        scale=100.0,
        unit="pp",
        fmt="+.1f",
    )
    metric(
        cols[4],
        "Vivienda vacía",
        "vacancy_rate",
        value_fmt=".1%",
        scale=100.0,
        unit="pp",
        fmt="+.1f",
        inverse=True,
    )

    if baseline_frame is not None and scenarios:
        if pooled:
            st.caption(
                f"Nivel: mediana de {len(baselines)} semillas sobre los últimos "
                f"{TAIL_WINDOW} trimestres. La flecha es la mediana de la diferencia frente a "
                "la base, emparejada semilla a semilla, y ± es la semi-amplitud entre "
                "semillas. **Gris «≈ 0» = la diferencia es menor que esa amplitud**: cambiar "
                "de semilla le cambia el signo, así que no hay nada que leer."
            )
        else:
            st.warning(
                "Una sola semilla: las flechas no llevan intervalo y varias de estas "
                "magnitudes cambian de signo entre semillas. Sube «Semillas a promediar» "
                "en la barra lateral antes de leer ninguna de ellas.",
                icon="🎲",
            )
        _composition_note(frame, baseline_frame)


def _composition_note(frame, baseline_frame) -> None:
    """Say when the sobrecarga arrow is measuring a different population, not a worse one.

    `rent_overburden_share` averages over whoever is a MARKET tenant this tick, and a policy
    moves that population: a cap changes who signs, a public programme moves the poorest
    tenants onto administered rents and out of the denominator entirely. `tenant_entry_share`
    (metrics, 2026-09-18) is how much of the population is not from the founding cohort; when
    the scenario moves it away from the baseline, the two averages are over different people
    and the difference between them is not a burden change. The founding-cohort reading is
    shown alongside because it is the one whose denominator the policy cannot touch.
    """
    entry_scen = float(frame["tenant_entry_share"].tail(TAIL_WINDOW).mean())
    entry_base = float(baseline_frame["tenant_entry_share"].tail(TAIL_WINDOW).mean())
    shift = entry_scen - entry_base
    if abs(shift) < 0.01:
        return
    founding_scen = float(frame["rent_overburden_share_founding"].tail(TAIL_WINDOW).mean())
    founding_base = float(baseline_frame["rent_overburden_share_founding"].tail(TAIL_WINDOW).mean())
    st.info(
        "**La flecha de sobrecarga mezcla dos cosas.** Esta política cambia *quién* es "
        f"inquilino de mercado: la proporción de inquilinos que no venían del inicio se mueve "
        f"{shift * 100:+.1f} pp respecto a la base. Parte de la flecha de arriba es esa "
        "recomposición, no que los mismos hogares paguen más o menos.\n\n"
        "Sobre la **cohorte fundacional** —los hogares que ya existían en el trimestre 0, un "
        "grupo al que ninguna política puede añadir— la sobrecarga pasa de "
        f"**{founding_base:.1%}** a **{founding_scen:.1%}** "
        f"({(founding_scen - founding_base) * 100:+.1f} pp). Ese denominador la política no lo "
        "toca. No es una corrección de la cifra de arriba: es lo que permite decidir si se "
        "puede leer. Detalle en docs/validation.md.",
        icon="🧮",
    )


def actor_reactions(lever: str) -> None:
    """How each actor responds to the chosen policy, and the resulting market chain."""
    st.subheader("¿Cómo reaccionan los actores?")
    st.markdown(texts.POLICY_SUMMARIES[lever])
    for actor, reaction in texts.ACTOR_REACTIONS[lever]:
        with st.expander(actor):
            st.markdown(reaction)


def explore_tab(
    lever: str, params: dict, baseline_frame, scenario_frame, baselines=(), scenarios=()
) -> None:
    frame = scenario_frame if scenario_frame is not None else baseline_frame
    policy_start = params.get("start_tick") if scenario_frame is not None else None
    # The same indicators WITHOUT the policy, drawn dashed underneath so the reader sees what
    # the model predicted before the intervention rather than holding it in their head. Only
    # when a policy is active: with none, the scenario IS the baseline and a second copy of the
    # same line would be noise. The Δ charts below never take it — their baseline is the zero
    # rule they already draw.
    reference = baseline_frame if scenario_frame is not None else None

    if lever == "ninguna":
        st.info(
            "Estás viendo la **simulación base**: el mercado sin ninguna política "
            "nueva. Elige una intervención en la barra lateral para ver su efecto y "
            "cómo reaccionan los actores."
        )
    else:
        actor_reactions(lever)
        st.divider()

    kpi_row(
        frame,
        baseline_frame if scenario_frame is not None else None,
        baselines=baselines,
        scenarios=scenarios,
    )

    st.subheader("Precios por zona (€, índice ajustado por calidad)")
    chart_block(
        "precios",
        frame,
        charts.zone_columns("price"),
        y_title="€",
        colors=charts.ZONE_COLORS,
        policy_start=policy_start,
        reference=reference,
    )
    st.subheader("Alquileres por zona (€/mes, oferta de nuevos contratos)")
    chart_block(
        "alquileres",
        frame,
        charts.zone_columns("rent"),
        y_title="€/mes",
        colors=charts.ZONE_COLORS,
        policy_start=policy_start,
        reference=reference,
    )
    st.subheader("Accesibilidad de la vivienda (% de no propietarios que puede comprar)")
    chart_block(
        "accesibilidad",
        frame,
        charts.zone_columns("buyer_access"),
        y_title="Proporción de no propietarios",
        colors=charts.ZONE_COLORS,
        policy_start=policy_start,
        y_format=".1%",
        reference=reference,
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
            reference=reference,
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
            reference=reference,
        )


def compare_tab(seed: int, ticks: int, momentum: float, n_seeds: int) -> None:
    st.subheader("Comparar políticas")
    st.caption(
        "Cada política se simula por separado sobre la misma base, con sus parámetros por "
        "defecto y empezando en el trimestre 8. El gráfico muestra la diferencia frente a no "
        "hacer nada, como mediana de las semillas."
    )
    # "los puntos medios de la evidencia" stood here until 2026-09-18, three screens after the
    # ❓ tab explains that for a disputed parameter the midpoint does not exist — a dataclass
    # default is a default, not a central estimate, and calling it one turned the comparison
    # table into a claim about the evidence. See docs/assumptions.md.
    st.caption(
        "⚠️ Los valores por defecto de cada política son **valores por defecto**, no el centro "
        "de la evidencia: para los parámetros en disputa no existe tal centro. Para recorrer "
        "el rango de uno de ellos, usa la pestaña «Explorar»."
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
    per_seed: dict[str, tuple[list, list]] = {}
    for lever in selected:
        baselines, scenarios, pooled_base, pooled_scen = run_many(
            seed, n_seeds, ticks, lever, {}, momentum
        )
        deltas[lever] = metrics.compare(pooled_base, pooled_scen)[column]
        per_seed[lever] = (baselines, scenarios)

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

    st.subheader("Resumen del tramo final")
    st.caption(
        f"Mediana de la diferencia frente a la base sobre los últimos {TAIL_WINDOW} "
        f"trimestres, emparejada semilla a semilla ({n_seeds} semillas). **«≈ 0» significa "
        "que la diferencia es menor que la amplitud entre semillas**: en esa celda la "
        "política y el azar son indistinguibles, y el número que había antes ahí era ruido "
        "con un decimal. Redondeo: alquiler al euro, precio al millar, pp a un decimal."
    )
    # ROUNDING (2026-09-18). Rent to the euro, price to the thousand, shares to 0.1pp. The
    # table printed "+7.022 €" against a seed spread of thousands — five significant figures
    # on a quantity whose second one is noise.
    summary_columns = [
        ("Δ alquiler tensionada (€/mes)", "rent_tensioned", 1.0, "+,.0f"),
        ("Δ precio tensionada (miles €)", "price_tensioned", 1e-3, "+,.0f"),
        ("Δ nuevos contratos", "new_leases", 1.0, "+,.0f"),
        ("Δ buscando vivienda (pp)", "seeker_share", 100.0, "+.1f"),
        ("Δ sobrecarga alquiler (pp)", "rent_overburden_share", 100.0, "+.1f"),
    ]
    summary = pd.DataFrame(
        {
            label: {lever: _pooled_cell(*per_seed[lever], column, scale, fmt) for lever in selected}
            for label, column, scale, fmt in summary_columns
        }
    )
    st.dataframe(summary, width="stretch")
    st.caption(
        "⚠️ Ninguna columna es «la buena» por sí sola: una política puede bajar el "
        "alquiler y a la vez dejar a más hogares sin encontrar piso. Para explorar "
        "los parámetros en disputa de cada política, usa la pestaña «Explorar»."
    )


def _pooled_cell(baselines, scenarios, column: str, scale: float, fmt: str) -> str:
    """One summary cell: the pooled delta, or «≈ 0» when the seed spread swallows it."""
    median, half_range = metrics.pooled_delta(baselines, scenarios, column, tail=TAIL_WINDOW)
    median, half_range = median * scale, half_range * scale
    if median != median:  # NaN
        return "—"
    if len(baselines) < 2:
        return f"{median:{fmt}} (1 semilla)"
    if not abs(median) > half_range:
        return f"≈ 0 (±{half_range:{fmt.replace('+', '')}})"
    return f"{median:{fmt}} ± {half_range:{fmt.replace('+', '')}}"


def bde_tab(
    seed: int, ticks: int, momentum: float, lever: str, params: dict, n_seeds: int = 1
) -> None:
    """Model output against the official published figures (BdE, INE/EPF via Funcas 104)."""
    st.subheader("Contraste con las cifras oficiales publicadas")
    st.markdown(texts.BDE_INTRO)

    scenario_label = "base (sin política)" if lever == "ninguna" else lever
    # The opt-in "Promediar 3 semillas" checkbox that used to live here is GONE (2026-09-18).
    # It was the only place in the app that averaged, which put the honest machinery in the one
    # tab where conclusions are NOT drawn; the sidebar's "Semillas a promediar" now governs
    # every tab at once, so this one no longer has a private answer to the question.
    st.caption(
        f"Escenario contrastado: **{scenario_label}** · semillas "
        f"{', '.join(str(x) for x in seed_pool(seed, n_seeds))} · {ticks} trimestres"
    )
    if n_seeds < 2:
        st.warning(
            "Con una sola semilla varias de estas magnitudes tienen más dispersión que la "
            "banda publicada — la formación de hogares es un sorteo de Poisson y una ventana "
            "de 5 años oscila ±10.000 viviendas/año a escala nacional. Un desajuste que veas "
            "aquí puede ser puro azar. Sube «Semillas a promediar» en la barra lateral.",
            icon="🎲",
        )

    seeds = seed_pool(seed, n_seeds)
    frames = []
    for s in seeds:
        base_frame, scen_frame = run(s, ticks, lever, params, momentum)
        frames.append(scen_frame if scen_frame is not None else base_frame)

    config = _config(seed, ticks, momentum)
    table = benchmarks.contrast(frames, config)
    counts = benchmarks.summary(frames, config)

    k = st.columns(4)
    k[0].metric("Indicadores contrastados", counts["total"])
    k[1].metric("✅ Dentro de banda", counts["inside"])
    k[2].metric("🔽 Por debajo", counts["below"])
    k[3].metric("🔼 Por encima", counts["above"])

    st.dataframe(
        table[
            [
                "Indicador",
                "Modelo",
                "Oficial (publicado)",
                "Banda",
                "Δ relativa",
                "Encaja",
                "Periodo",
            ]
        ],
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "**Δ relativa** = (modelo − oficial) / oficial. **Banda** es el rango publicado "
        "cuando la fuente da uno; si no, «encaja» usa una tolerancia de ±15% alrededor del "
        "valor central, suficiente para detectar signo y orden de magnitud, no calibración "
        "fina. Ningún ✅ o 🔽 es un aprobado o un suspenso: son diagnósticos."
    )

    st.subheader("Cómo se compara cada indicador, y qué mirar con cuidado")
    for key, row in table.iterrows():
        flagged = "⚠️ " if row["note"].startswith("⚠️") else ""
        with st.expander(f"{row['Encaja']} {flagged}{row['Indicador']}"):
            st.markdown(
                f"- **Modelo:** {row['Modelo']}  ·  **Oficial:** {row['Oficial (publicado)']}"
                f"  ·  **Δ** {row['Δ relativa']}\n"
                f"- **Periodo de la cifra oficial:** {row['Periodo']}\n"
                f"- **Fuente:** {row['Fuente']}\n"
                f"- **Cómo se igualan las bases:** {row['basis']}"
                + (f"\n- {row['note']}" if row["note"] else "")
            )
        _ = key

    st.divider()
    st.markdown(texts.BDE_FORECAST_PANEL)


def diagnostics_tab(baseline_frame, scenario_frame, params: dict, lever: str) -> None:
    """The phase-0 targets on screen — including the four that still carry a strict xfail.

    Always evaluated on the BASELINE frame, never the scenario one. These targets ask
    whether the model reproduces Spain, and a rent cap moving a number is not evidence
    about that; `docs/validation.md` quotes them on the baseline for the same reason.
    """
    st.subheader("Diagnóstico del modelo — objetivos de la fase 0")
    st.markdown(texts.DIAGNOSTICS_INTRO)
    with st.expander("Qué puede decir el modelo, y qué no", expanded=False):
        st.markdown(texts.REPORTING_CONTRACT)

    frame = baseline_frame
    if scenario_frame is not None:
        st.caption(
            f"Medido siempre sobre la **base sin política**, no sobre «{lever}»: estos "
            "objetivos preguntan si el modelo reproduce España, y una política moviendo "
            "un número no es evidencia sobre eso."
        )

    table = diagnostics.evaluate(frame)
    counts = diagnostics.summary(frame)

    k = st.columns(4)
    k[0].metric("Objetivos de fase 0", counts["targets"])
    k[1].metric("✗ xfail estrictos", counts["xfail"])
    # Labels distinct from the BdE tab's counters on purpose: Streamlit renders every tab
    # body eagerly into one flat element list, so two tabs sharing a metric label are
    # ambiguous both to a reader flipping between them and to anything reading the surface.
    k[2].metric("✅ Criterios dentro de banda", counts["inside"])
    k[3].metric("🔽🔼 Criterios fuera de banda", counts["outside"])

    st.dataframe(
        table[["Objetivo", "Indicador", "Este run", "Criterio", "Encaja", "Estado"]],
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "**Criterio** es la banda tal y como la enuncia el dosier; la evaluación usa la "
        "banda de `tests/test_validation.py`, que la ensancha 0,5 pp por lado para ruido "
        "de semilla. **Encaja** es dónde cae **la mediana de las semillas que estés "
        "promediando** (desde 2026-09-18 este panel ya no evalúa una sola semilla, salvo que "
        "pongas el deslizador en 1); **Estado** es cómo está registrado el objetivo en "
        "`docs/validation.md`, que se cita sobre su propia base de semillas. Responden a "
        "preguntas distintas y pueden discrepar."
    )

    st.subheader("Qué significa cada fila")
    for _key, row in table.iterrows():
        with st.expander(
            f"{row['Encaja']} {row['Estado']} · objetivo {row['Objetivo']} — {row['Indicador']}"
        ):
            st.markdown(
                f"- **Este run:** {row['Este run']}  ·  **Criterio:** {row['Criterio']}\n"
                f"- **Fuente:** {row['source']}\n"
                f"- **Cómo se lee:** {row['reads']}" + (f"\n- {row['note']}" if row["note"] else "")
            )

    st.divider()
    st.subheader("Yield bruto del alquiler por zona (salida del modelo, no un ajuste)")
    chart_block(
        "yields",
        frame,
        charts.zone_columns("gross_yield"),
        y_title="Yield bruto anual",
        colors=charts.ZONE_COLORS,
        y_format=".2%",
    )

    st.subheader("Alquileres por zona — el orden T > S > R que el modelo rompe")
    chart_block(
        "alquileres_diag",
        frame,
        charts.zone_columns("rent"),
        y_title="€/mes",
        colors=charts.ZONE_COLORS,
    )

    st.subheader("Migración interna neta por zona (hogares/trimestre, escala del modelo)")
    chart_block(
        "migracion",
        frame,
        charts.zone_columns("net_migration"),
        y_title="Hogares/trimestre",
        colors=charts.ZONE_COLORS,
        zero_line=True,
    )

    st.subheader("Proporción de inquilinos por zona")
    chart_block(
        "tenencia_zona",
        frame,
        charts.zone_columns("tenant_share"),
        y_title="Proporción de hogares de la zona",
        colors=charts.ZONE_COLORS,
        y_format=".1%",
    )

    st.divider()
    st.markdown(texts.DIAGNOSTICS_OUTRO)
    _ = params


def how_it_works_tab() -> None:
    # The list of red targets is read from diagnostics, not retyped here: this tab claimed
    # "the baseline reproduces the validation targets" for three phases after it stopped
    # being true, precisely because the claim was prose nothing checked.
    st.markdown(
        texts.MODEL_EXPLANATION.format(xfail_targets=", ".join(diagnostics.xfail_targets()))
    )


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
        # NO CALENDAR (2026-09-18). The model has no start date: tick 1 is not 2026Q1, and
        # nothing in it is dated. Readers were mapping 60 quarters onto 2026–2041 anyway,
        # which turns a conditional path into a forecast with years attached. Said once, here,
        # where the horizon is chosen. Euros are constant at the calibration base for the same
        # reason — there is no inflation path to deflate by.
        st.caption(
            "⚠️ Sin calendario: el trimestre 1 **no** es 2026T1 y ninguna cifra lleva fecha. "
            "Es un horizonte, no un pronóstico fechado. Los euros son constantes en la base "
            "de calibración, no nominales de un año concreto."
        )
        # DEFAULT 3, not 1 (2026-09-18). Several headline deltas change SIGN between seeds —
        # measured, ten seeds: the tensioned rent response to saturated public housing runs
        # −197 to +92 €/month around a mean of −15. Running one seed and drawing the result as
        # a coloured arrow was the app asserting a finding the run does not contain. The
        # averaging machinery already existed behind a checkbox in the 🏛️ tab; it now applies
        # where the conclusions are actually read. Cost is linear: 3 seeds is 3 runs.
        n_seeds = st.slider(
            "Semillas a promediar",
            1,
            10,
            3,
            help="Cada semilla es un mundo distinto con las mismas reglas. Las flechas y la "
            "tabla comparativa muestran la MEDIANA entre semillas y la amplitud entre ellas; "
            "cuando la diferencia es menor que esa amplitud se marca «≈ 0» en gris, porque "
            "cambiar de semilla le cambiaría el signo. Con 1 semilla no hay intervalo que "
            "mostrar y la app te lo advierte. Más lento de forma lineal.",
        )

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

    baselines, scenarios, baseline_frame, scenario_frame = run_many(
        seed, n_seeds, ticks, lever, params, momentum
    )

    tab_explore, tab_compare, tab_bde, tab_diag, tab_help = st.tabs(
        [
            "📈 Explorar una política",
            "⚖️ Comparar políticas",
            "🏛️ Contraste oficial",
            "🔬 Diagnóstico del modelo",
            "❓ Cómo funciona el modelo",
        ]
    )
    with tab_explore:
        explore_tab(
            lever, params, baseline_frame, scenario_frame, baselines=baselines, scenarios=scenarios
        )
    with tab_compare:
        compare_tab(seed, ticks, momentum, n_seeds)
    with tab_bde:
        bde_tab(seed, ticks, momentum, lever, params, n_seeds)
    with tab_diag:
        diagnostics_tab(baseline_frame, scenario_frame, params, lever)
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
            n_seeds=n_seeds,
        ),
        lever=lever,
    )


if __name__ == "__main__":
    main()
