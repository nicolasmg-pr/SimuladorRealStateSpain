"""Altair chart builders for the Streamlit UI.

All charts share one visual system: fixed series colors (a zone or a policy always
keeps its color), hover tooltips with the quarter/year equivalence, and an optional
vertical marker at the tick where the policy starts.

Rule (same as app.py): this module never computes an indicator — it only reshapes
frames produced by resim.metrics for display.
"""

from __future__ import annotations

import altair as alt
import pandas as pd

from resim.config import ZoneType

ZONE_LABELS = {
    ZoneType.TENSIONED: "Zona tensionada",
    ZoneType.SECONDARY: "Ciudad secundaria",
    ZoneType.RURAL: "Rural",
}

# Categorical palette (validated: dataviz reference palette, slots 1-8).
_SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

ZONE_COLORS = {
    ZONE_LABELS[ZoneType.TENSIONED]: _SLOTS[0],
    ZONE_LABELS[ZoneType.SECONDARY]: _SLOTS[1],
    ZONE_LABELS[ZoneType.RURAL]: _SLOTS[2],
}

_INK_MUTED = "#898781"
_GRID = "#e1e0d9"


def palette_for(names: list[str]) -> dict[str, str]:
    """Fixed color per name, assigned in order (never cycled past 8)."""
    return {name: _SLOTS[i % len(_SLOTS)] for i, name in enumerate(names)}


def _melt(frame: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """Wide tick-indexed frame -> long (trimestre, año, serie, valor)."""
    data = frame[list(columns)].rename(columns=columns).reset_index()
    long = data.melt(id_vars="tick", var_name="serie", value_name="valor")
    long = long.rename(columns={"tick": "trimestre"})
    long["año"] = (long["trimestre"] / 4).round(1)
    return long


def zone_columns(prefix: str) -> dict[str, str]:
    """Column mapping for a per-zone indicator, e.g. price_tensioned -> label."""
    return {f"{prefix}_{z.value}": ZONE_LABELS[z] for z in ZoneType}


def line_chart(
    frame: pd.DataFrame,
    columns: dict[str, str],
    *,
    y_title: str,
    colors: dict[str, str] | None = None,
    policy_start: int | None = None,
    zero_line: bool = False,
    y_format: str = ",.0f",
    height: int = 320,
) -> alt.LayerChart:
    """Multi-series line chart: hover tooltip, click-on-legend focus, policy marker."""
    long = _melt(frame, columns)
    if colors is None:
        colors = palette_for(list(columns.values()))
    color_scale = alt.Scale(domain=list(colors), range=[colors[k] for k in colors])

    legend_sel = alt.selection_point(fields=["serie"], bind="legend")
    hover = alt.selection_point(
        fields=["trimestre"], nearest=True, on="mouseover", empty=False, clear="mouseout"
    )

    base = alt.Chart(long).encode(
        x=alt.X("trimestre:Q", title="Trimestre", axis=alt.Axis(tickMinStep=4)),
        y=alt.Y("valor:Q", title=y_title, scale=alt.Scale(zero=zero_line)),
        color=alt.Color("serie:N", scale=color_scale, legend=alt.Legend(title=None)),
    )
    lines = base.mark_line(strokeWidth=2, interpolate="monotone").encode(
        opacity=alt.condition(legend_sel, alt.value(1.0), alt.value(0.25))
    )
    points = base.mark_circle(size=64).encode(
        opacity=alt.condition(hover, alt.value(1.0), alt.value(0.0)),
        tooltip=[
            alt.Tooltip("serie:N", title="Serie"),
            alt.Tooltip("trimestre:Q", title="Trimestre"),
            alt.Tooltip("año:Q", title="Año", format=".1f"),
            alt.Tooltip("valor:Q", title=y_title, format=y_format),
        ],
    )
    crosshair = (
        alt.Chart(long)
        .mark_rule(color=_INK_MUTED, strokeWidth=1)
        .encode(x="trimestre:Q")
        .transform_filter(hover)
    )
    layers = [lines, points.add_params(hover), crosshair]

    if zero_line:
        zero = (
            alt.Chart(pd.DataFrame({"valor": [0.0]}))
            .mark_rule(color=_INK_MUTED, strokeDash=[2, 2])
            .encode(y="valor:Q")
        )
        layers.insert(0, zero)

    if policy_start is not None:
        marker_df = pd.DataFrame({"trimestre": [policy_start], "etiqueta": ["Inicio política"]})
        marker = (
            alt.Chart(marker_df)
            .mark_rule(color=_INK_MUTED, strokeDash=[6, 3], strokeWidth=1.5)
            .encode(x="trimestre:Q")
        )
        marker_text = (
            alt.Chart(marker_df)
            .mark_text(align="left", dx=5, dy=-6, color=_INK_MUTED, fontSize=11, baseline="top")
            .encode(x="trimestre:Q", y=alt.value(0), text="etiqueta:N")
        )
        layers += [marker, marker_text]

    chart = alt.layer(*layers).add_params(legend_sel).properties(height=height)
    return chart.configure_axis(
        gridColor=_GRID, labelColor=_INK_MUTED, titleColor=_INK_MUTED, domainColor=_GRID
    ).configure_view(strokeWidth=0)


def data_table(frame: pd.DataFrame, columns: dict[str, str]) -> pd.DataFrame:
    """Table view of exactly what the chart plots (accessibility relief)."""
    table = frame[list(columns)].rename(columns=columns)
    table.index.name = "Trimestre"
    return table
