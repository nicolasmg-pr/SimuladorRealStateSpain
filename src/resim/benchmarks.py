"""Contrast between what the model produces and the official published Spanish figures.

Most rows are Banco de España; the rest are INE series (Censo, EPF) as compiled in Funcas
*Estudios* 104, *Mercado inmobiliario y política de la vivienda en España* (2024) — see
docs/funcas-104.md for what each of those figures is and is not. Every row names its own
source; none of them is a forecast.

**Read this first: BdE publishes no housing forecast.** Its quarterly macro projection
tables contain zero housing rows — no house prices, no residential investment, no starts,
no household disposable income, no mortgage rate (docs/external-forecasts.md §1, verified).
So there is nothing to compare a *projected path* against. What BdE does publish is
**actuals and structural diagnostics**, and those are directly comparable to the model's
settled phase. That is what this module does.

Three separate things, deliberately kept apart:

  - `docs/validation.md` — "does the baseline reproduce history?" A pass/fail gate.
  - this module — "how do the model's headline national numbers sit against the official
    published figures for the same variables?" Diagnostic, **not** a gate. It exists so the
    gaps are visible in the app instead of living only in a hand-maintained doc table.
  - `docs/external-forecasts.md` §4 — the third-party forecast panel (BBVA, CaixaBank,
    IMF/EBA…), which *is* forward-looking, and is not BdE.

Every reference value carries its definition, period, and source. Bases are converted
explicitly: the model runs at 1:`metrics.SCALE`, and its per-tick counts are quarterly.
A comparison on mismatched bases is worse than no comparison, so the conversion for each
row is stated in `basis` and applied in `_model_value`, never by the caller.

The model's clock is not calendar-anchored: 60 ticks is "≈15 years of a Spain-like market",
not 2011–2026. Rows are therefore compared against BdE's own multi-year window (2021–2025)
using the model's settled phase (the last `WINDOW` ticks), never tick-by-tick.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from .config import SimConfig
from .metrics import SCALE

WINDOW = 20  # ticks (5 years) — matches BdE's 2021–2025 accumulation window
TICKS_PER_YEAR = 4


@dataclass(frozen=True)
class Benchmark:
    """One officially published figure and how to compute its model counterpart."""

    key: str
    label: str  # UI label (Spanish, like the rest of the app surface)
    official: float  # the published central value
    band: tuple[float, float] | None  # published range, where the source gives one
    unit: str
    fmt: str  # format spec for both sides
    period: str
    source: str
    basis: str  # how the model side is put on the same footing
    model: Callable[[pd.DataFrame, SimConfig], float]
    note: str = ""

    def verdict(self, model_value: float) -> str:
        """'inside' when the model lands in the published band, else which way it misses.

        With no published band, a ±15% tolerance around the central value stands in — wide
        enough that it flags direction and order of magnitude, not calibration noise.
        """
        lo, hi = self.band if self.band else (self.official * 0.85, self.official * 1.15)
        if lo <= model_value <= hi:
            return "inside"
        return "below" if model_value < lo else "above"


def _per_year(frame: pd.DataFrame, column: str) -> float:
    """Model-scale per-tick count → national units per year."""
    return float(frame[column].tail(WINDOW).mean()) * TICKS_PER_YEAR * SCALE


def _annualised(frame: pd.DataFrame, column: str) -> float:
    """Per-tick growth rate → per-year, over the settled window."""
    return float(frame[column].tail(WINDOW).mean()) * TICKS_PER_YEAR


def _mean(frame: pd.DataFrame, column: str) -> float:
    return float(frame[column].tail(WINDOW).mean())


def _deficit_5y(frame: pd.DataFrame, _config: SimConfig) -> float:
    """Accumulated completions-minus-formation gap over the window, national units.

    BdE's headline housing number. Computed from the SUM over the window, which is the basis
    the 750,000 figure is published on — not from the mean of per-tick ratios.
    """
    tail = frame.tail(WINDOW)
    gap = float(tail["formation"].sum() - tail["completions"].sum())
    return gap * SCALE


def _deficit_share_of_households(frame: pd.DataFrame, config: SimConfig) -> float:
    """The same deficit as a share of households — BdE's cross-country comparable."""
    households = config.population.n_households
    tail = frame.tail(WINDOW)
    gap = float(tail["formation"].sum() - tail["completions"].sum())
    return gap / max(1.0, households)


def _transactions_share(frame: pd.DataFrame, config: SimConfig) -> float:
    """Transactions per year as a share of households (BdE: 3.8% in 2025)."""
    per_tick = float(frame["transactions"].tail(WINDOW).mean())
    return per_tick * TICKS_PER_YEAR / max(1.0, config.population.n_households)


def _zone_weighted_supply_elasticity(_frame: pd.DataFrame, config: SimConfig) -> float:
    return sum(z.household_share * z.supply_elasticity for z in config.zones)


def _latent_demand(frame: pd.DataFrame, _config: SimConfig) -> float:
    """Households in the model with no dwelling of their own, at national scale.

    The comparable published figure is Ezquiaga's deficit of ≈1.6M *potential* young
    households: people who would head a household at the 2002–08 age structure and do not,
    because they cannot afford to leave home or are sharing. Basis warning, in both
    directions: Spain's 18.9M households does NOT count them, while the model's household
    count DOES (a SEEKER is an existing model household without a unit). The like-for-like
    Spanish ratio is therefore 1.6/(18.9+1.6) ≈ 7.8%.
    """
    tail = frame.tail(WINDOW)
    return float((tail["seeker_share"] * tail["households"]).mean()) * SCALE


# HICP 2025, used to put BdE's *real* asking-rent growth on the model's nominal basis
# [BdE June 2026 projections Table 2, 2025 actual — docs/external-forecasts.md §1]
HICP_2025 = 0.027


BENCHMARKS: tuple[Benchmark, ...] = (
    Benchmark(
        key="deficit_5y",
        label="Déficit acumulado de vivienda (5 años)",
        official=750_000.0,
        band=None,
        unit="viviendas",
        fmt=",.0f",
        period="2021–2025",
        source="BdE Informe Anual 2025, cap. 2",
        basis="Σ(formación − terminadas) sobre 20 trimestres × 2.000",
        model=_deficit_5y,
        note="El número titular del BdE sobre vivienda. Es un dato observado acumulado, "
        "no una previsión. Sendas alternativas: BBVA Research 562k (2024) → 669k (2025) → "
        "747k (2026) → ≈794k (2027), con las terminadas cubriendo ≈48% de los hogares nuevos; "
        "CaixaBank >900k en 2029. La proyección de hogares del INE de jun-2026 (205k/año en "
        "2026–31) reduce el déficit FUTURO, no el acumulado.",
    ),
    Benchmark(
        key="deficit_share",
        label="Déficit acumulado (% de hogares)",
        official=0.037,
        band=None,
        unit="% de hogares",
        fmt=".2%",
        period="2021–2025",
        source="BdE Informe Anual 2025, gráfico 2.11",
        basis="mismo déficit / hogares del modelo",
        model=_deficit_share_of_households,
        note="Comparable entre países: Italia 1,5% · Portugal 6,6% · Francia ≈0 · "
        "Alemania +0,5% (superávit).",
    ),
    Benchmark(
        key="formation",
        label="Formación neta de hogares",
        official=240_000.0,
        band=(225_000.0, 250_000.0),
        unit="hogares/año",
        fmt=",.0f",
        period="2025 (BdE 240k; INE ECP +226k en 2025, +239k interanual a jul-2026)",
        source="BdE Informe Anual 2025, cap. 2; INE Estadística Continua de Población 2T 2026",
        basis="formación por trimestre × 4 × 2.000",
        model=lambda f, c: _per_year(f, "formation"),
        note="Es un PARÁMETRO de entrada calibrado (`formation_per_tick`), no un "
        "resultado: aquí sólo confirma que la escala 1:2.000 está bien aplicada. La "
        "proyección del INE (jun-2026) va por debajo: 205k/año en 2026–31, 139k en 2031–36, "
        "93k en 2036–41 — disponible como senda `ine-demography` (docs/kb-refresh-2026-09.md).",
    ),
    Benchmark(
        key="completions",
        label="Viviendas terminadas",
        official=92_000.0,
        band=None,
        unit="viviendas/año",
        fmt=",.0f",
        period="2025 (−9% interanual)",
        source="BdE Informe Anual 2025, cap. 2",
        basis="terminadas por trimestre × 4 × 2.000",
        model=lambda f, c: _per_year(f, "completions"),
        note="El modelo no pierde nada entre inicio y terminación; en la realidad hay "
        "abandono de proyectos y plazos más largos.",
    ),
    Benchmark(
        key="starts",
        label="Viviendas iniciadas",
        official=140_000.0,
        band=(130_000.0, 150_000.0),
        unit="viviendas/año",
        fmt=",.0f",
        period="principios de 2026, «estabilizándose»",
        source="BdE Boletín Económico 2026/T1, gráfico 18",
        basis="iniciadas por trimestre × 4 × 2.000",
        model=lambda f, c: _per_year(f, "starts"),
    ),
    Benchmark(
        key="transactions",
        label="Compraventas de vivienda",
        official=750_000.0,
        band=(700_000.0, 800_000.0),
        unit="operaciones/año",
        fmt=",.0f",
        period="2025 (máximo desde 2008); 1S 2026 −7,7% interanual (Notariado)",
        source="BdE Informe Anual 2025, cap. 2; Registradores 2025: 705.357; INE 2025: 714k",
        basis="compraventas por trimestre × 4 × 2.000",
        model=lambda f, c: _per_year(f, "transactions"),
        note="90% vivienda de segunda mano; las personas jurídicas son el 10% de las compras. "
        "En 2026 el volumen cae (Notariado 1S −7,7%; Registradores 2T −2,3%, jul −7,7%) con "
        "el precio subiendo +12%: la firma «volumen primero, precio pegajoso» en sentido "
        "contrario al de 2024–25.",
    ),
    Benchmark(
        key="transactions_share",
        label="Compraventas (% de hogares)",
        official=0.038,
        band=(0.025, 0.040),
        unit="% de hogares/año",
        fmt=".2%",
        period="2025",
        source="BdE Informe Anual 2025, cap. 2",
        basis="compraventas anuales / hogares del modelo",
        model=_transactions_share,
        note="Referencia de burbuja: 5,5% de media en el auge de 2004–07.",
    ),
    Benchmark(
        key="price_growth",
        label="Precio de la vivienda (nominal)",
        official=0.127,
        band=None,
        unit="%/año",
        fmt="+.1%",
        period="2025 (media anual; 2024: +8,4%); 2026T2 +12,2% interanual (INE, 7-sep-2026)",
        source="BdE IEF Primavera 2026, cap. 4 — base INE IPV; INE IPV 2T 2026",
        basis="crecimiento nacional por trimestre × 4, fase estabilizada",
        model=lambda f, c: _annualised(f, "price_growth_national"),
        note="⚠️ Dos sesgos, los dos a la baja, y ninguno es un error: (1) se compara la "
        "fase ESTABILIZADA del modelo con 2025, el año más fuerte en 18 años — para "
        "contrastar un auge hay que cargar un escenario de auge, no la base; (2) el índice "
        "del modelo es de TRANSACCIÓN ajustado por calidad, estructuralmente más lento que "
        "el IPV. Esperar que quede por debajo (docs/validation.md).",
    ),
    Benchmark(
        key="rent_growth",
        label="Alquiler de oferta (nominal)",
        official=0.05 + HICP_2025,
        band=None,
        unit="%/año",
        fmt="+.1%",
        period="2025 (+5% real; 2024: +10% real); ago-2026 +5,8% nominal (idealista)",
        source="BdE IEF Primavera 2026, cap. 4 — portales inmobiliarios; idealista ago-2026",
        basis="crecimiento nacional por trimestre × 4; +2,7% HICP para pasar real a nominal",
        model=lambda f, c: _annualised(f, "rent_growth_national"),
        note="⚠️ Mismo sesgo de fase que el precio (base estabilizada vs año de auge). "
        "Además: el propio BdE advierte que estos índices de portales no tienen tratamiento "
        "estadístico del INE, y en el modelo el alquiler está acotado por el crecimiento de "
        "la renta porque no hay margen de sobreocupación. Límite inferior, no estimación.",
    ),
    Benchmark(
        key="purchase_effort",
        label="Esfuerzo teórico de compra",
        official=0.375,
        band=(0.35, 0.40),
        unit="% de renta disponible",
        fmt=".1%",
        period="2024–25",
        source="BdE Síntesis de Indicadores 1.5",
        basis="mismo indicador, definido en metrics.py (modelo-spec §11)",
        model=lambda f, c: _mean(f, "purchase_effort"),
    ),
    Benchmark(
        key="price_to_income",
        label="Precio / renta disponible",
        official=7.5,
        band=(7.0, 8.0),
        unit="años",
        fmt=".2f",
        period="2024–26",
        source="BdE Síntesis de Indicadores / household-owner §6",
        basis="mismo indicador, base de renta disponible (factor 0,72)",
        model=lambda f, c: _mean(f, "price_to_income"),
    ),
    Benchmark(
        key="supply_elasticity",
        label="Elasticidad de oferta a largo plazo",
        official=0.45,
        band=(0.45, 0.58),
        unit="Δln inicios/Δln precio",
        fmt=".2f",
        period="estructural",
        source="BdE Informe Anual 2025 cap. 2 (Caldera & Johansson 2013)",
        basis="media de las elasticidades por zona ponderada por hogares",
        model=_zone_weighted_supply_elasticity,
        note="El BdE califica 0,45 de «cota superior» para la España actual. Es un "
        "parámetro de entrada, no un resultado.",
    ),
    Benchmark(
        key="vacancy_market",
        label="Vivienda vacía de mercado (zona tensionada)",
        official=0.075,
        band=(0.06, 0.09),
        unit="% del parque",
        fmt=".1%",
        period="Censo urbano",
        source="INE Censo vía investor-small §6 (BdE cita 3,8M vacías, censo 2020)",
        basis="vacantes no retenidas / parque de la zona",
        model=lambda f, c: _mean(f, "vacancy_market_tensioned"),
        note="No comparable con los 3,8M absolutos del censo: ese total incluye segundas "
        "residencias y parque retenido, que el modelo contabiliza aparte.",
    ),
    Benchmark(
        key="vacancy_rural",
        label="Vivienda vacía (zona rural, todo el parque vacío)",
        official=0.195,
        band=(0.156, 0.246),
        unit="% del parque",
        fmt=".1%",
        period="Censo 2021, municipios <20.000 hab.",
        source="INE Censo 2021 vía Funcas 104 cap. 1, cuadro 1",
        basis="vacantes de la zona (incluido parque retenido) / parque de la zona",
        model=lambda f, c: _mean(f, "vacancy_rural"),
        note="La mitad del parque vacío español está en municipios de menos de 20.000 "
        "habitantes, que reúnen el 28% de la población: el vacío está donde no hay demanda. "
        "Aquí sí entra el parque retenido, porque es precisamente el que la fuente describe "
        "como no movilizable (mala localización y necesidad de rehabilitación).",
    ),
    Benchmark(
        key="vacancy_secondary",
        label="Vivienda vacía (ciudad secundaria)",
        official=0.115,
        band=(0.081, 0.131),
        unit="% del parque",
        fmt=".1%",
        period="Censo 2021, municipios 20.000–300.000 hab.",
        source="INE Censo 2021 vía Funcas 104 cap. 1, cuadro 1",
        basis="vacantes de la zona (incluido parque retenido) / parque de la zona",
        model=lambda f, c: _mean(f, "vacancy_secondary"),
    ),
    Benchmark(
        key="vacancy_national",
        label="Vivienda vacía (nacional)",
        official=0.132,
        band=None,
        unit="% del parque",
        fmt=".1%",
        period="Censo 2021 (3,29M de un parque de 24,96M)",
        source="INE Censo 2021 vía Funcas 104 cap. 1, cuadro 1",
        basis="vacantes / parque total del modelo",
        model=lambda f, c: _mean(f, "vacancy_rate"),
        note="El texto del capítulo cita 3,8M de viviendas vacías; el cuadro suma 3,29M. Se "
        "usa el cuadro, que es el que da el desglose por tamaño de municipio.",
    ),
    Benchmark(
        key="ownership_rate",
        label="Hogares en propiedad",
        official=0.75,
        band=(0.70, 0.77),
        unit="% de hogares",
        fmt=".1%",
        period="2022–2025",
        source="ECV 2025 (73,3%); EPF 2022 (76,4%) vía Funcas 104 cap. 6; MITMA 75,3%; "
        "EFF2024 70,6%",
        basis="mismo indicador, hogares del modelo",
        model=lambda f, c: _mean(f, "ownership_rate"),
        note="Cuatro fuentes y tres bases: la ECV 2025 da 73,3% en propiedad, 20,2% en alquiler "
        "y 6,5% cedidas (mínimo de la serie; 2024: 73,6 / 20,4 / 6,1), la EPF 2022 76,4%, la "
        "EFF 2024 70,6% (el 36,7% entre menores de 35, 83% por encima de 65) y el 75,3% es "
        "sobre parque. El modelo queda en el borde bajo de todas ellas.",
    ),
    Benchmark(
        key="rent_burden_over_30",
        label="Inquilinos con alquiler > 30% de sus ingresos",
        official=0.382,
        band=(0.31, 0.44),
        unit="% de hogares en alquiler",
        fmt=".1%",
        period="2022 (2015: 33,0% · 2019: 33,5% · 2021: 43,1%)",
        source="EPF vía Romero-Jordán, Funcas 104 cap. 6, cuadro 2",
        basis="inquilinos de mercado con alquiler/renta > 0,30",
        model=lambda f, c: _mean(f, "rent_burden_over_30_share"),
        note="⚠️ Bases distintas: la fuente mide el alquiler sobre la CESTA DE CONSUMO y el "
        "modelo sobre la renta bruta, así que el modelo debería quedar por debajo. Con "
        "suministros básicos incluidos (el «sobreesfuerzo» de la Ley 12/2023) la fuente sube "
        "al 60,5%, algo que el modelo no puede calcular: no tiene gastos de energía ni agua.",
    ),
    Benchmark(
        key="rent_level",
        label="Gasto medio mensual en alquiler",
        official=516.0,
        band=(476.0, 560.0),
        unit="€/mes",
        fmt=",.0f",
        period="2022 (2019: 476 € · 2021: 505 €; SEF 2021 ≈520 €)",
        source="EPF vía Funcas 104 cap. 6, cuadro 2",
        basis="índice de alquiler nacional del modelo (€/mes de una vivienda estándar)",
        model=lambda f, c: _mean(f, "rent_national"),
        note="Contraste de NIVEL, no de crecimiento: sirve para ver si el ancla de alquiler "
        "del modelo (precio × rentabilidad bruta por zona) está en el orden correcto. La "
        "dispersión territorial real es enorme: Madrid 675 € frente a Extremadura 277 €.",
    ),
    Benchmark(
        key="cash_purchases",
        label="Compras sin hipoteca",
        official=0.293,
        band=(0.23, 0.46),
        unit="% de compraventas",
        fmt=".1%",
        period="2025 (Registradores, 12 meses); 2T 2026: 23% · Notariado jun-2026: 46,3%",
        source="Registradores ERI 4T 2025 y 2T 2026; Notariado CIEN jun-2026; INE 2023 (60,8%)",
        basis="proporción de operaciones marcadas `cash` en el modelo",
        model=lambda f, c: _mean(f, "cash_purchase_share"),
        note="⚠️ La banda cubre un desacuerdo real entre dos fuentes registrales que sí miden "
        "lo mismo: Registradores (hipotecas inscritas sobre compraventas) da 29,3% al contado "
        "en 2025 y 23% en 2T 2026 (Madrid ≈0%, Baleares 23–40%); el Notariado (préstamos "
        "firmados con la compra) da 46,3% en junio de 2026. El 60,8% que se deducía de "
        "compraventas INE / escrituras de hipoteca es un artefacto de desfase y ámbito y deja "
        "de ser el valor central. El modelo sigue muy por debajo de cualquiera de ellas: "
        "financia casi todas las compras, así que la política de crédito muerde más aquí "
        "que en España.",
    ),
    Benchmark(
        key="foreign_purchases",
        label="Compras de no residentes",
        official=0.079,
        band=(0.07, 0.10),
        unit="% de compraventas",
        fmt=".1%",
        period="4T 2024–1T 2025 (7,9%); Notariado 2S 2025: 44% del 18,4% extranjero ≈ 8,1%",
        source="CaixaBank Research sobre MIVAU (oct-2025); Notariado CIEN; Registradores 2T 2026",
        basis="compras del overlay no residente / compraventas del modelo, fase estabilizada",
        model=lambda f, c: _mean(f, "foreign_purchase_share"),
        note="Base NO RESIDENTE, que es lo que representa el overlay del modelo. Todos los "
        "extranjeros (residentes incluidos) son el 16,0% de las compras en 2T 2026 — récord "
        "de la serie registral, con los extranjeros creciendo +11% mientras los nacionales "
        "caen — y el 18,4% en la base notarial. Los no residentes pagan 3.063 €/m² frente a "
        "1.713 € los españoles (×1,8), la prima que fija `foreign_budget_multiplier`.",
    ),
    Benchmark(
        key="investor_purchases",
        label="Compras de personas jurídicas",
        official=0.10,
        band=(0.08, 0.12),
        unit="% de compraventas",
        fmt=".1%",
        period="2025",
        source="BdE Informe Anual 2025, cap. 2 (Notariado/BdE DO 2433)",
        basis="compras del gran inversor / compraventas del modelo, fase estabilizada",
        model=lambda f, c: _mean(f, "investor_purchase_share"),
        note="⚠️ El comprador institucional del modelo es sólo el GRAN TENEDOR (fondos, "
        "SOCIMI); la cifra oficial incluye a toda persona jurídica — promotoras, sociedades "
        "patrimoniales de una familia, pequeñas empresas. Se espera por debajo. Sirve para ver "
        "si el recargo del ITP a personas jurídicas (Cataluña: 20% en compras de edificios "
        "enteros, Ley 11/2026) hace algo visible.",
    ),
    Benchmark(
        key="latent_demand",
        label="Demanda embalsada (hogares potenciales sin vivienda)",
        official=1_600_000.0,
        band=None,
        unit="hogares",
        fmt=",.0f",
        period="2022",
        source="Ezquiaga, Funcas 104 cap. 4 (EFF: hogares <35 años, 15% en 2002 → <6% en 2022)",
        basis="hogares del modelo en estado SEEKER × 2.000",
        model=_latent_demand,
        note="⚠️ Bases asimétricas: los 18,9M de hogares españoles NO incluyen esos 1,6M "
        "hogares potenciales, mientras que el recuento de hogares del modelo SÍ incluye a sus "
        "SEEKER. La ratio comparable española es 1,6/(18,9+1,6) ≈ 7,8%. Es la contrapartida "
        "del parque vacío: coexisten porque el vacío está donde no hay demanda.",
    ),
)


def contrast(frames: pd.DataFrame | list[pd.DataFrame], config: SimConfig) -> pd.DataFrame:
    """Model versus published figure, one row per benchmark.

    `frames` is one run's metrics frame, or several frames from runs that differ only by
    seed — in which case the model side is the mean across them. Pooling matters: several of
    these quantities have a single-seed spread wider than their published band (household
    formation is a Poisson draw, so a 20-tick window swings ±10,000/yr at national scale),
    so a one-seed contrast can flag a miss that is pure noise.

    The settled phase (last `WINDOW` ticks) is used. Returns raw numbers plus preformatted
    strings, so the UI renders and never computes.
    """
    frame_list = [frames] if isinstance(frames, pd.DataFrame) else list(frames)
    if not frame_list:
        raise ValueError("contrast needs at least one frame")
    rows = []
    for b in BENCHMARKS:
        values = [b.model(f, config) for f in frame_list]
        model_value = float(sum(values) / len(values))
        verdict = b.verdict(model_value)
        gap = model_value - b.official
        rel = gap / b.official if b.official else float("nan")
        rows.append(
            {
                "key": b.key,
                "Indicador": b.label,
                "Modelo": format(model_value, b.fmt),
                "Oficial (publicado)": format(b.official, b.fmt),
                "Banda": (
                    f"{format(b.band[0], b.fmt)} – {format(b.band[1], b.fmt)}" if b.band else "—"
                ),
                "Δ relativa": f"{rel:+.0%}",
                "Encaja": {"inside": "✅", "below": "🔽", "above": "🔼"}[verdict],
                "Periodo": b.period,
                "Fuente": b.source,
                "Semillas": len(frame_list),
                "model_value": model_value,
                "official": b.official,
                "verdict": verdict,
                "basis": b.basis,
                "note": b.note,
            }
        )
    return pd.DataFrame(rows).set_index("key")


def summary(frames: pd.DataFrame | list[pd.DataFrame], config: SimConfig) -> dict[str, int]:
    """How many benchmarks land inside their band, and how many miss each way."""
    table = contrast(frames, config)
    counts = table["verdict"].value_counts().to_dict()
    return {
        "inside": int(counts.get("inside", 0)),
        "below": int(counts.get("below", 0)),
        "above": int(counts.get("above", 0)),
        "total": int(len(table)),
    }
