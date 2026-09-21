"""Phase-0 diagnostic targets, evaluated on a run so the app can show them.

Phase 0 of the redesign (`docs/superpowers/specs/2026-09-11-model-redesign-design.md`)
added seven observable moments and changed no model behaviour. Three of them are red on
arrival — that is their purpose: they turn defects that were invisible into failures the
suite reports. This module puts those same moments on screen, so the defects are visible
to whoever runs the app instead of living only in `tests/test_validation.py` and the
hand-maintained table in `docs/validation.md`.

Three separate things, deliberately kept apart:

  - `tests/test_validation.py` — the gate. Strict xfails, ten seeds (`SEEDS`, since the
    phase-E rule that nothing is reported on fewer), `build_scenario`. It decides whether
    a target passes; nothing here does.
  - this module — the same criteria, evaluated on the frame it is handed, for display.
    Diagnostic, never a gate.
  - `benchmarks.py` — national headline numbers against official published figures.
    Different question (is the level right?), different sources, different table.

**The bands here are copied from the assertions in `tests/test_validation.py`, not
re-derived.** If the two ever disagree, the test is right and this file is the bug.
`sourced` carries the band as the dossier states it; `band` carries the test's band,
which widens it for seed noise (±0.5pp on the zone yields, the same tolerance convention
as the other zone targets).

**This is not the gate's basis, whatever it is measured on.** The suite pools ten seeds;
the app hands this module `metrics.pool` over the sidebar's seed pool — three by default
since 2026-09-18, and a single seed only if the reader drags the slider to 1. A row that
reads ✅ on the pool in front of you can still be a registered xfail, and `registered` is
what says so. The UI states this.
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
        # GATED since 2026-09-17 (§5b.2 + §7.1c), verified at ten seeds against the gate.
        registered=Registered.GATED,
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
        # GATED since 2026-09-17 (§5b.2 + §7.1c), verified at ten seeds against the gate.
        registered=Registered.GATED,
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
        # GATED since 2026-09-17, VERIFIED AT TEN SEEDS (8.35%) after §7.1c netted the zone
        # risk premium against the expected-growth gap. An earlier same-day attempt to gate
        # this on a three-seed reading of 8.89% was wrong — at ten seeds it read 10.07% — and
        # was reverted before this. The gate is `test_zone_gross_yield_ladder`, which now
        # passes with its xfail marker removed.
        registered=Registered.GATED,
        source=_YIELD_SOURCE,
        reads=_YIELD_READS,
        note="**Esta es la pata que rompe el objetivo 9.** `required_rent` ancla el suelo del "
        "yield al precio y la oferta de alquiler rural no tiene margen de entrada: el "
        "inversor no entra en rural y los hogares nunca compran para alquilar. El "
        "*total-return hurdle* (§7.1) y la migración bidireccional (§7.5) ya entraron en la "
        "fase B y no bastaron. Lo que queda es la **entrada buy-to-let (§7.3)**, que baja "
        "esta pata de 22% a 8,10% y sigue **aparcada** en la rama `buy-to-let-remeasure`: la "
        "entrada por yield arbitra la escalera de precios entre zonas (T/R cae a 1,65 contra "
        "un suelo de 2,6) y falta meterle el gradiente de vacancia que el inversor debería "
        "*ver* al elegir zona (`docs/validation.md`, «Parked, on buy-to-let-remeasure»).",
    ),
    Criterion(
        key="rent_ordering",
        target="11",
        label="Orden de alquileres T > S > R (margen mínimo)",
        measure=lambda f: _ordering_margin(f, "rent"),
        band=(0.0, float("inf")),
        sourced="orden estricto, en toda base publicada",
        fmt="+,.0f",
        # GATED since 2026-09-17 (§5b.2). The ordering holds; the LEVEL is still compressed,
        # T/R 2.05 against a sourced 2.44, which this criterion does not assert.
        registered=Registered.GATED,
        source="idealista, SERPAVI, EPF regional — 675 €/mes Madrid contra 277 € "
        "Extremadura [Funcas 104 cap.5]",
        reads="La escalera de **precios** está gatillada (objetivos 2b–2d); la de **alquileres** "
        "no lo estaba, y así es como un índice de alquiler rural por encima del metropolitano "
        "sobrevivió 60 trimestres sin que saltara nada.",
        note="El alquiler rural adelanta al tensionado alrededor del trimestre 35–40. La prima "
        "de localización descuenta la disposición a **comprar** en rural, pero nada descuenta la "
        "aceptación de **alquiler** (model-spec §5b), y el margen de compartir sube la carga "
        "aceptada a 0,55. La migración bidireccional (§7.5) entró en la fase B y no lo cerró. "
        "Lo cierra la **entrada buy-to-let (§7.3)**, medida y **aparcada** en la rama "
        "`buy-to-let-remeasure` por el mismo motivo que el objetivo 9: arbitra la escalera de "
        "precios entre zonas.",
    ),
    Criterion(
        key="net_migration_tensioned",
        target="12",
        label="Migración interna neta de la zona tensionada (acumulada)",
        measure=lambda f: _cumulative(f, "net_migration_tensioned"),
        band=(float("-inf"), 0.0),
        sourced="negativa — signo, no nivel",
        fmt="+,.0f",
        registered=Registered.GATED,
        source="INE EVR 2015–21 y EMCR 69753 2021–24, mapeo B (model-spec §13.8): "
        "−33.393 (2019), −140.179 (2020), −55.195 (2024)",
        reads="**Corregido el 2026-09-14.** Hasta la fase B esta fila pedía el signo "
        "contrario y estaba registrada como xfail: se daba por hecho que el flujo interno "
        "neto español va rural → metro. Los datos dicen lo contrario — la zona tensionada "
        "pierde migrantes internos todos los años desde 2017 en los tres mapeos candidatos y "
        "en ambas estadísticas. El modelo acertaba y la ficha lo contaba como fallo "
        "(`docs/validation.md`, «Phase-B finding-11 correction»).",
        note="Escala del modelo (1:`metrics.SCALE`), hogares acumulados sobre la simulación "
        "entera — es un flujo, no un nivel, y por eso no se promedia la cola. Es un test de "
        "**signo**, y sólo significa algo porque la regla ya admite los dos signos: la "
        "migración bidireccional de la fase B sustituyó la regla de sólo-bajar, que afirmaba "
        "esto por construcción (`test_interior_migration_is_bidirectional`).",
    ),
    Criterion(
        key="migration_in_tensioned",
        target="12",
        label="Entradas interiores brutas a la zona tensionada (acumuladas)",
        measure=lambda f: _cumulative(f, "migration_in_tensioned"),
        band=(1.0, float("inf")),
        sourced="cualquier flujo de entrada > 0 — un neto negativo no es un flujo de un sentido",
        fmt="+,.0f",
        registered=Registered.XFAIL,
        source="INE EVR/EMCR: el neto negativo del metro es la diferencia de dos flujos "
        "grandes, no una ausencia de entradas",
        reads="Lo que falla no es el signo del neto, sino que las entradas brutas se van a "
        "cero: nadie entra nunca al metro en la base. Con eso, el neto sale del sitio "
        "correcto por el motivo equivocado.",
        note="**Reabierta el 2026-09-14 por §7.4.** Había cerrado bajo el hurdle de §7.1, que "
        "bajó las rentas metropolitanas lo suficiente para que una entrada superase la "
        "fricción; capitalizar la puja del inversor y desanclar al comprador extranjero "
        "devolvió precios y rentas, y las entradas volvieron a cero. Que un cambio del lado "
        "del precio la abra y la cierre es la prueba de que la sostenía una coincidencia, no "
        "un mecanismo: en `engine._demography` el único tirón hacia el metro es el ratio de "
        "renta, y falta **dónde está el empleo** (término de amenidad, spec §7.5).",
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
        key="sold_within_quarter_share",
        target="13",
        label="Vendidas dentro del trimestre",
        measure=lambda f: _tail_mean(f, "sold_within_quarter_share"),
        band=(0.43, 0.63),
        sourced="≈53% (7% <1 semana, 19% <1 mes, 27% 1–3 meses, 36% 3–12, 11% >1 año)",
        fmt=".1%",
        registered=Registered.GATED,
        source="idealista/data, 2T 2026; el plazo medio de Tecnocasa (77 días) cae dentro",
        reads="Identifica la amplitud de búsqueda `m`: con `m`=1 el comprador puja sobre lo "
        "primero que encuentra y casi todo se vende (75%); cuanto más compara, más se "
        "concentran las pujas en lo bien tasado y más tiempo se queda parado el resto.",
        note="Una vivienda listada y vendida en el mismo trimestre lee `ticks_listed == 0`, "
        "así que «dentro del trimestre» es `== 0`, no `<= 1`.",
    ),
    Criterion(
        key="price_dispersion",
        target="16",
        label="Dispersión idiosincrásica del precio de venta",
        measure=lambda f: _tail_mean(f, "price_dispersion"),
        band=(0.06, 0.17),
        sourced="6–17% por venta (central 10%)",
        fmt=".1%",
        registered=Registered.GATED,
        source="Kotova & Zhang (códigos postales EE.UU. 2012–16, efectos fijos de vivienda, "
        "media 16,8%); Giacoletti, RFS 2021 (6,8–12,4%); Landvoigt-Piazzesi-Schneider, AER "
        "2015 (6,2–9,8%). No existe estimación española publicada: el INE y los Registradores "
        "calculan la magnitud y publican sólo el índice",
        reads="Es contra lo que se identifica `overbid_sigma`, que hasta la fase G era una "
        "conjetura. Mide la desviación típica del log del precio de venta una vez quitados "
        "zona × trimestre y la calidad observable.",
        note="El modelo leía **2,3%** antes de la fase G y lee 8,0% después. Subir el "
        "parámetro movía el NIVEL y no la dispersión hasta que §5c.6 separó los dos índices.",
    ),
    Criterion(
        key="sale_discount_median",
        target="13c",
        label="Margen de negociación (oferta → cierre)",
        measure=lambda f: _tail_mean(f, "sale_discount_median"),
        band=(0.04, 0.12),
        sourced="6,2% de media; sólo el 23% de las negociadas supera el 10%",
        fmt=".2%",
        registered=Registered.GATED,
        source="Cátedra Tecnocasa-UPF (2S 2025); Fotocasa, Experiencia en compraventa 2024",
        reads="Es una **salida**, no una entrada: el vendedor publica con margen y la subasta "
        "decide cuánto queda de él. Por eso se gatilla.",
        note="**CERRADO el 15-09-2026**, tras fallar desde que nació: 5,20% ± 0,10 en diez "
        "semillas, dentro de 4–12% y contra el 6,2% medido. No lo cerró ningún parámetro sino "
        "§5c.8: el trimestre dejó de casarse como una subasta simultánea y las ofertas llegan "
        "mes a mes [Merlo & Ortalo-Magné], así que las pujas por anuncio bajaron de 3,5 a 2,2 "
        "y la mayoría de las ventas pasó a ser la negociación bilateral sobre la que el 6,2% "
        "está medido. Las ventas por encima del precio de salida cayeron con ello, del 21% al "
        "12,8%, contra el 9% de vendedores que suben el precio en Fotocasa.",
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


def xfail_targets() -> tuple[str, ...]:
    """Targets carrying a live strict xfail, in `CRITERIA` order and without a run.

    Frame-independent on purpose: the guide tab states how many targets are red, and a
    hand-written count there is how the guide drifted away from this module in the first
    place. One definition, read by everything that quotes it.
    """
    seen = {c.target for c in CRITERIA if c.registered is Registered.XFAIL}
    ordered = dict.fromkeys(c.target for c in CRITERIA if c.target in seen)
    return tuple(ordered)


def summary(frame: pd.DataFrame) -> dict[str, int]:
    """Counts for the headline row: how many targets are red, and how many are measured."""
    table = evaluate(frame)
    return {
        "targets": len({c.target for c in CRITERIA}),
        "xfail": len(xfail_targets()),
        "inside": int((table["Encaja"] == "✅").sum()),
        "outside": int(table["Encaja"].isin(["🔽", "🔼"]).sum()),
    }
