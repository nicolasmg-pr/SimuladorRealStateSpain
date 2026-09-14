"""Phase-0 diagnostic targets, evaluated on a run so the app can show them.

Phase 0 of the redesign (`docs/superpowers/specs/2026-09-11-model-redesign-design.md`)
added seven observable moments and changed no model behaviour. Three of them are red on
arrival — that is their purpose: they turn defects that were invisible into failures the
suite reports. This module puts those same moments on screen, so the defects are visible
to whoever runs the app instead of living only in `tests/test_validation.py` and the
hand-maintained table in `docs/validation.md`.

Three separate things, deliberately kept apart:

  - `tests/test_validation.py` — the gate. Strict xfails, 3 seeds, `build_scenario`.
    It decides whether a target passes; nothing here does.
  - this module — the same criteria, evaluated on **one** frame for display. Diagnostic,
    never a gate.
  - `benchmarks.py` — national headline numbers against official published figures.
    Different question (is the level right?), different sources, different table.

**The bands here are copied from the assertions in `tests/test_validation.py`, not
re-derived.** If the two ever disagree, the test is right and this file is the bug.
`sourced` carries the band as the dossier states it; `band` carries the test's band,
which widens it for seed noise (±0.5pp on the zone yields, the same tolerance convention
as the other zone targets).

**One seed is not the gate's basis.** The suite averages 3 seeds; the app runs whatever
seed the sidebar is set to. A row that reads ✅ here on one seed can still be a registered
xfail, and `registered` is what says so. The UI states this.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import pandas as pd

WINDOW = 20  # ticks — the settled tail the validation table is quoted on


class Registered(StrEnum):
    """Status of the target in `docs/validation.md`, as registered. Not recomputed here."""

    XFAIL = "✗ xfail estricto"
    GATED = "✓ gatillado"
    REPORTED = "○ reportado, no gatillado"
    DEFERRED = "— diferido"


def _tail_mean(frame: pd.DataFrame, column: str) -> float:
    """Mean over the settled tail — the basis every number in docs/validation.md uses."""
    return float(frame[column].tail(WINDOW).mean())


def _cumulative(frame: pd.DataFrame, column: str) -> float:
    """Sum over the whole run. Target 12's basis: a flow, not a level."""
    return float(frame[column].sum())


def _ordering_margin(frame: pd.DataFrame, prefix: str, scale: float = 1.0) -> float:
    """Smallest gap in a T > S > R ordering. Positive ⇒ the ordering holds.

    Reported as a margin rather than a boolean so the table shows how far off the model is,
    and in which direction, instead of a bare False.
    """
    t = _tail_mean(frame, f"{prefix}_tensioned")
    s = _tail_mean(frame, f"{prefix}_secondary")
    r = _tail_mean(frame, f"{prefix}_rural")
    return min(t - s, s - r) * scale


@dataclass(frozen=True)
class Criterion:
    """One phase-0 target: what it asks, how it is measured, and how the answer is read."""

    key: str
    target: str  # the model-spec §9 target number this row belongs to
    label: str  # UI label (Spanish, like the rest of the app surface)
    measure: Callable[[pd.DataFrame], float]
    band: tuple[float, float] | None  # the assertion in tests/test_validation.py
    sourced: str  # the band as the dossier states it, before the seed-noise tolerance
    fmt: str
    registered: Registered
    source: str
    reads: str  # what a miss means — the mechanism, not a restatement of the number
    note: str = ""

    def verdict(self, value: float) -> str:
        """Where this run lands against the band. '—' when the row is not gated."""
        if self.band is None or value != value:  # no band, or NaN
            return "—"
        lo, hi = self.band
        if lo <= value <= hi:
            return "✅"
        return "🔽" if value < lo else "🔼"


# Sourced levels: idealista + BdE RBA [model-spec §7, investor-small §6]. Bands as asserted
# in test_zone_gross_yield_ladder — the sourced range widened by 0.5pp on each side.
_YIELD_SOURCE = "idealista + BdE RBA [model-spec §7; investor-small §6]"
_YIELD_READS = (
    "El yield es una **salida** del modelo, no una condición inicial: `ZoneConfig.gross_yield` "
    "sólo fija el punto de partida. Lo que el modelo hace después es una predicción, y es el "
    "único observable que dice si la regla de reserva del casero está bien."
)

CRITERIA: tuple[Criterion, ...] = (
    Criterion(
        key="gross_yield_tensioned",
        target="9",
        label="Yield bruto — zona tensionada",
        measure=lambda f: _tail_mean(f, "gross_yield_tensioned"),
        band=(0.042, 0.061),
        sourced="4,7–5,6%",
        fmt=".2%",
        registered=Registered.XFAIL,
        source=_YIELD_SOURCE,
        reads=_YIELD_READS,
    ),
    Criterion(
        key="gross_yield_secondary",
        target="9",
        label="Yield bruto — ciudad secundaria",
        measure=lambda f: _tail_mean(f, "gross_yield_secondary"),
        band=(0.060, 0.080),
        sourced="6,5–7,5%",
        fmt=".2%",
        registered=Registered.XFAIL,
        source=_YIELD_SOURCE,
        reads=_YIELD_READS,
    ),
    Criterion(
        key="gross_yield_rural",
        target="9",
        label="Yield bruto — rural",
        measure=lambda f: _tail_mean(f, "gross_yield_rural"),
        band=(0.065, 0.095),
        sourced="7–9%",
        fmt=".2%",
        registered=Registered.XFAIL,
        source=_YIELD_SOURCE,
        reads=_YIELD_READS,
        note="**Esta es la pata que rompe el objetivo 9.** `required_rent` ancla el suelo del "
        "yield al precio, la oferta de alquiler rural no tiene margen de entrada (el inversor "
        "no entra en rural y los hogares nunca compran para alquilar) y la migración sólo "
        "baja, así que todo buscador expulsado acaba allí. Lo arregla el *total-return hurdle* "
        "y la entrada buy-to-let (spec §7.1, §7.3 — fase B).",
    ),
    Criterion(
        key="rent_ordering",
        target="11",
        label="Orden de alquileres T > S > R (margen mínimo)",
        measure=lambda f: _ordering_margin(f, "rent"),
        band=(0.0, float("inf")),
        sourced="orden estricto, en toda base publicada",
        fmt="+,.0f",
        registered=Registered.XFAIL,
        source="idealista, SERPAVI, EPF regional — 675 €/mes Madrid contra 277 € "
        "Extremadura [Funcas 104 cap.5]",
        reads="La escalera de **precios** está gatillada (objetivos 2b–2d); la de **alquileres** "
        "no lo estaba, y así es como un índice de alquiler rural por encima del metropolitano "
        "sobrevivió 60 trimestres sin que saltara nada.",
        note="El alquiler rural adelanta al tensionado alrededor del trimestre 35–40. La prima "
        "de localización descuenta la disposición a **comprar** en rural, pero nada descuenta la "
        "aceptación de **alquiler** (model-spec §5b), mientras la migración sólo-hacia-abajo "
        "canaliza buscadores allí y el margen de compartir sube la carga aceptada a 0,55. Lo "
        "arreglan la migración bidireccional y la entrada buy-to-let (spec §7.3, §7.5 — fase B).",
    ),
    Criterion(
        key="net_migration_tensioned",
        target="12",
        label="Migración interna neta hacia la zona tensionada (acumulada)",
        measure=lambda f: _cumulative(f, "net_migration_tensioned"),
        band=(0.0, float("inf")),
        sourced="sólo dirección — el nivel necesita INE Migraciones, aún no en sources.md",
        fmt="+,.0f",
        registered=Registered.XFAIL,
        source="INE Migraciones y Variaciones Residenciales — pendiente de registrar",
        reads="En España el flujo interno neto va **rural → metro**. El modelo lo tiene "
        "invertido por construcción: la regla de `engine._demography` sólo deja bajar la "
        "escalera, así que la zona tensionada pierde migrantes internos en todas las semillas.",
        note="Escala del modelo (1:`metrics.SCALE`), hogares acumulados sobre la simulación "
        "entera — es un flujo, no un nivel, y por eso no se promedia la cola. Lo arreglan los "
        "flujos bidireccionales identificados sobre INE MVR (spec §7.5 — fase B).",
    ),
    Criterion(
        key="tenant_ordering",
        target="1c",
        label="Orden de inquilinos T > S > R (margen mínimo, pp)",
        measure=lambda f: _ordering_margin(f, "tenant_share", scale=100.0),
        band=(0.0, float("inf")),
        sourced="orden estricto — T 0,27–0,30 / S ≈0,20 / R 0,12–0,17",
        fmt="+.1f",
        registered=Registered.GATED,
        source="model-spec §7; household-tenant §6",
        reads="Alquilar es una tenencia **metropolitana** en España. El orden no está en duda; "
        "los niveles sí, y por eso se gatilla el orden y no el nivel.",
        note="Hasta el 2026-09-12 esta pata estaba en el fixture como un `True` fijo con un "
        "comentario que decía que se comprobaba en otro sitio. No se comprobaba en ninguno: "
        "iba sin medir. La pata tensionada corre por encima de su banda, misma matización de "
        "agregación de zona que el objetivo 2d — una zona tensionada con el 45% de los hogares "
        "no es Madrid.",
    ),
    Criterion(
        key="landlord_household_share",
        target="14",
        label="Hogares caseros (base EFF: posee vivienda en la que no vive)",
        measure=lambda f: _tail_mean(f, "landlord_household_share"),
        band=None,
        sourced="un **corchete**, no una banda: EFF 36,1% (oleada 2022) revisado a 45,3% "
        "(2024, DO 2610) contra AEAT 11,9% (2,37 M declarantes / 19,87 M hogares)",
        fmt=".1%",
        registered=Registered.REPORTED,
        source="EFF 2022/2024 y AEAT [docs/sources.md; model-spec §7]",
        reads="Hoy el modelo **no tiene margen de entrada**: un hogar comprador siempre acaba "
        "de propietario-ocupante. Esta columna existe para medir ese defecto, no para aprobarlo.",
        note="Mide **propiedad, no arrendamiento**: cuenta cualquier hogar dueño de una vivienda "
        "en la que no vive, así que segundas residencias vacías, stock retenido, vivienda "
        "estacional y lo heredado-pero-vacío entran todos. Ésa es la base EFF, no la base AEAT. "
        "Dos bases separadas por un factor de tres o cuatro **acotan** la columna, no la "
        "bandean; contra cuál se gatilla es una decisión de fase B, y depende de la columna "
        "hermana restringida a `Tenure.RENTED` que fase B tiene que especificar.",
    ),
    Criterion(
        key="median_ticks_to_sale",
        target="13",
        label="Tiempo hasta vender (trimestres, mediana)",
        measure=lambda f: _tail_mean(f, "median_ticks_to_sale"),
        band=None,
        sourced="distribución de días en mercado de idealista — **por verificar**",
        fmt=".2f",
        registered=Registered.REPORTED,
        source="idealista, días en mercado — aún no es una fila de docs/sources.md",
        reads="Es el observable que identifica la subasta de fase D **sin tocar el nivel de "
        "precios** (spec §7.7). Por eso se mide ya, aunque todavía no se pueda gatillar.",
        note="Unidad de la escala: los anuncios envejecen al principio de "
        "`engine._apply_listings`, antes del casamiento, así que un anuncio creado y casado "
        "dentro del mismo trimestre lee "
        "**0, no 1**. «Vendido dentro del trimestre» mapea a 0, no a ≤1.",
    ),
    Criterion(
        key="boom_yield_compression",
        target="10",
        label="El boom comprime el yield bruto",
        measure=lambda _f: float("nan"),
        band=None,
        sourced="sólo dirección — una banda sobre la *compresión* necesita la serie temporal "
        "2014–25, que no está registrada",
        fmt=".2%",
        registered=Registered.GATED,
        source="idealista, corte transversal Q4-2025/Q1-2026 [docs/sources.md]",
        reads="Pasa en la suite (5,39% → 5,21%, 5 semillas × 40 trimestres), pero se mide "
        "sobre el **escenario de hold-out con boom**, no sobre la base. No es medible en este "
        "run, y por eso no se inventa un número aquí.",
        note="Margen fino: 0,18 pp y sin banda por semilla. Dos de las cinco semillas apenas "
        "se mueven (−1,5 y −2,9 pb). Fase B debería revisar si el objetivo necesita una banda.",
    ),
    Criterion(
        key="arrears_share",
        target="15",
        label="Impago — hogares hipotecados en mora",
        measure=lambda f: _tail_mean(f, "arrears_share"),
        band=(0.010, 0.040),
        sourced="1,6% (2026T1), 2,3–3,4% en 2019–2024, 6,28% en el pico de 2014T1",
        fmt=".2%",
        registered=Registered.GATED,
        source="BdE, Boletín Estadístico cuadro 4.13 (dudosos / crédito para adquisición "
        "de vivienda)",
        reads="Antes de la fase C el impago no existía: `wealth = max(0, wealth − cuota)` "
        "absorbía cualquier falta de pago. Lo que mide esta fila es que la restricción "
        "presupuestaria **ata**, y que ata en el orden de magnitud correcto.",
        note="El BdE cuenta euros de crédito y esto cuenta hogares: coinciden sólo si la mora "
        "no está correlacionada con el tamaño del préstamo, y el gradiente de incidencia "
        "(§6c.1) hace improbable que lo esté. Por eso la banda es ancha y la comparación es "
        "de orden de magnitud.",
    ),
    Criterion(
        key="foreclosure_rate",
        target="15",
        label="Entregas de vivienda al acreedor (anual, por hipoteca viva)",
        measure=lambda f: _tail_mean(f, "foreclosure_rate"),
        band=(0.0010, 0.0080),
        sourced="0,7%/año en 2014 (0,6% vivienda habitual); ≈0,10%/año en el suelo de 2019",
        fmt=".2%",
        registered=Registered.XFAIL,
        source="BdE, nota informativa sobre ejecuciones hipotecarias (Circular 1/2013); "
        "INE Estadística sobre Ejecuciones Hipotecarias",
        reads="El modelo convierte casi todo disparo estatutario en **venta voluntaria**: un "
        "propietario con equity positivo encuentra comprador dentro de la ventana de "
        "publicación. Lo que lo impide en la realidad es el equity negativo tras una caída de "
        "precios, el descuento de una vivienda ocupada y los meses que tarda una venta.",
        note="**Esta es la pata que falla al nacer**: ≈0,01–0,02%/año contra 0,10–0,16% "
        "observado en años tranquilos. Dos de las tres fricciones que faltan son formación de "
        "precios (spec §7.7 — fase D) y la tercera es la propia crisis (fase E). Se reporta "
        "como fallo en lugar de bajar la banda: la banda es el dato.",
    ),
)


def evaluate(frame: pd.DataFrame) -> pd.DataFrame:
    """Every phase-0 criterion measured on one run, as a display table.

    One row per criterion, in `CRITERIA` order. `Encaja` is where *this* frame lands;
    `Estado` is what the target is registered as in `docs/validation.md`. They answer
    different questions and can disagree — a single seed passing a band does not flip a
    registered xfail, and the UI says so.
    """
    rows = []
    for c in CRITERIA:
        value = c.measure(frame)
        measurable = value == value  # False for NaN
        rows.append(
            {
                "key": c.key,
                "Objetivo": c.target,
                "Indicador": c.label,
                "Este run": format(value, c.fmt) if measurable else "no medible aquí",
                "Criterio": c.sourced,
                "Encaja": c.verdict(value),
                "Estado": str(c.registered),
                "value": value,
                "reads": c.reads,
                "source": c.source,
                "note": c.note,
            }
        )
    return pd.DataFrame(rows).set_index("key")


def summary(frame: pd.DataFrame) -> dict[str, int]:
    """Counts for the headline row: how many targets are red, and how many are measured."""
    table = evaluate(frame)
    return {
        "targets": len({c.target for c in CRITERIA}),
        "xfail": len({c.target for c in CRITERIA if c.registered is Registered.XFAIL}),
        "inside": int((table["Encaja"] == "✅").sum()),
        "outside": int(table["Encaja"].isin(["🔽", "🔼"]).sum()),
    }
