"""Floating AI chat — asks OpenRouter about what is currently on screen.

A popover pinned to the bottom-right corner via CSS. The app hands us a plain-text
snapshot of the visible state (`screen_context`); we send it as the system prompt so
the model answers about *this* run, not housing markets in general.

Rule: this module only formats numbers the app already computed via resim.metrics —
it never derives new indicators.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import requests
import streamlit as st

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
HISTORY_SENT = 12  # messages sent to the API; full history stays in session state
TIMEOUT_S = 90

_FLOAT_CSS = """
<style>
div[data-testid="stPopover"] {
    position: fixed;
    bottom: 1.25rem;
    right: 1.25rem;
    z-index: 1000;
}
div[data-testid="stPopover"] > div > button {
    border-radius: 2rem;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}
div[data-testid="stPopoverBody"] {
    width: min(420px, 90vw);
}
</style>
"""

_SYSTEM_PROMPT = """\
Eres el asistente del «Simulador del mercado inmobiliario español», un modelo basado
en agentes (hogares, caseros, inversores, promotores, banca y gobierno) que simula
por trimestres el mercado de vivienda en tres tipos de zona (metro tensionada,
ciudad secundaria, rural).

Responde en español, breve y claro, a preguntas sobre lo que el usuario ve en
pantalla. Usa SOLO los datos del estado actual que aparecen a continuación; si algo
no está en ellos, dilo. Recuerda al usuario, cuando proceda, que los resultados son
condicionales al modelo y a los deslizadores, no predicciones.

Estado actual de la pantalla:

{context}
"""


def _api_key() -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            name, _, value = line.strip().partition("=")
            if name.strip() == "OPENROUTER_API_KEY":
                return value.strip().strip("'\"") or None
    return None


def _strip_reasoning(text: str) -> str:
    """Reasoning models may prepend a <think>…</think> block; the user wants the answer."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _ask(api_key: str, context: str, history: list[dict[str, str]]) -> str:
    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)},
                *history[-HISTORY_SENT:],
            ],
        },
        timeout=TIMEOUT_S,
    )
    response.raise_for_status()
    message = response.json()["choices"][0]["message"]
    answer = _strip_reasoning(message.get("content") or "")
    return answer or _strip_reasoning(message.get("reasoning") or "") or "(respuesta vacía)"


def screen_context(
    *,
    seed: int,
    ticks: int,
    momentum: float,
    lever: str,
    params: dict,
    baseline_frame,
    scenario_frame,
) -> str:
    """Plain-text snapshot of the current run for the system prompt."""
    lines = [
        f"- Semilla: {seed}; trimestres simulados: {ticks} (≈ {ticks / 4:.0f} años).",
        f"- Momento de expectativas λ: {momentum}.",
        f"- Política activa: {lever}"
        + (f" con parámetros {params}." if params else " (simulación base, sin política)."),
    ]

    def row(label: str, frame) -> str:
        last = frame.iloc[-1]
        return (
            f"- {label} (último trimestre): "
            f"precio zona tensionada {last['price_tensioned']:,.0f} €; "
            f"precio media nacional {last['price_national']:,.0f} €; "
            f"alquiler nuevo zona tensionada {last['rent_tensioned']:,.0f} €/mes; "
            f"compraventas {last['transactions']:,.0f}/trim.; "
            f"nuevos contratos de alquiler {last['new_leases']:,.0f}; "
            f"tasa de propiedad {last['ownership_rate']:.1%}; "
            f"hogares buscando vivienda {last['seeker_share']:.1%}; "
            f"sobrecarga de alquiler (>40%) {last['rent_overburden_share']:.1%}; "
            f"vivienda vacía {last['vacancy_rate']:.1%}; "
            f"precio/renta disponible {last['price_to_income']:.1f}."
        )

    lines.append(row("Base sin política", baseline_frame))
    if scenario_frame is not None:
        lines.append(row(f"Escenario con «{lever}»", scenario_frame))
        lines.append(
            "- El efecto de la política es escenario menos base: misma semilla, misma "
            "economía; la única diferencia es la intervención."
        )
    return "\n".join(lines)


def render(context: str) -> None:
    """Floating chat window, bottom-right. Call once at the end of the page."""
    st.markdown(_FLOAT_CSS, unsafe_allow_html=True)
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    with st.popover("💬 Asistente", type="primary"):
        st.caption("Pregunta sobre lo que ves en pantalla. Modelo: Nemotron 3 Nano (gratuito).")
        api_key = _api_key()
        if api_key is None:
            st.warning("Falta `OPENROUTER_API_KEY` en `.env` — el chat está desactivado.")
            return

        history_box = st.container(height=320)
        for message in st.session_state.chat_messages:
            with history_box.chat_message(message["role"]):
                st.markdown(message["content"])

        prompt = st.chat_input("Ej.: ¿por qué sube el alquiler al final?")
        if prompt:
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with history_box.chat_message("user"):
                st.markdown(prompt)
            with history_box.chat_message("assistant"):
                try:
                    with st.spinner("Pensando…"):
                        answer = _ask(api_key, context, st.session_state.chat_messages)
                except requests.RequestException as exc:
                    answer = f"⚠️ Error al llamar a OpenRouter: {exc}"
                st.markdown(answer)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})
