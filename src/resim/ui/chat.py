"""Floating AI chat — asks OpenRouter about what is currently on screen.

A popover pinned to the bottom-right corner via CSS. The app hands us a plain-text
snapshot of the visible state (`screen_context`); we send it as the system prompt so
the model answers about *this* run, not housing markets in general.

Rule: this module only formats numbers the app already computed via resim.metrics —
it never derives new indicators.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
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
    /* Streamlit sets 100%, which pushes the button off-screen left */
    width: fit-content !important;
    z-index: 1000;
}
div[data-testid="stPopover"] button[data-testid="stPopoverButton"] {
    width: 3rem;
    height: 3rem;
    min-height: 3rem;
    padding: 0;
    border-radius: 50%;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
}
div[data-testid="stPopover"] button[data-testid="stPopoverButton"] p {
    font-size: 1.3rem;
}
div[data-testid="stPopover"] button[data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {
    display: none;  /* drop the expand_more chevron so only the bubble emoji shows */
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


_OPEN, _CLOSE = "<think>", "</think>"


def _hide_thinking(chunks: Iterator[str]) -> Iterator[str]:
    """Pass chunks through, dropping anything between <think> and </think>.

    Streaming splits tags across chunks, so we hold back a tail as long as the
    tag we are looking for (minus one character) before emitting.
    """
    buffer = ""
    thinking = False
    for chunk in chunks:
        buffer += chunk
        while True:
            marker = _CLOSE if thinking else _OPEN
            index = buffer.find(marker)
            if index == -1:
                break
            if not thinking and index:
                yield buffer[:index]
            buffer = buffer[index + len(marker) :]
            thinking = not thinking
        keep = len(_CLOSE if thinking else _OPEN) - 1
        if thinking:
            buffer = buffer[-keep:]
        elif len(buffer) > keep:
            yield buffer[:-keep]
            buffer = buffer[-keep:]
    if not thinking and buffer:
        yield buffer


def _stream(api_key: str, context: str, history: list[dict[str, str]]) -> Iterator[str]:
    """Yield answer fragments as OpenRouter emits them (server-sent events)."""
    with requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)},
                *history[-HISTORY_SENT:],
            ],
            "stream": True,
        },
        timeout=TIMEOUT_S,
        stream=True,
    ) as response:
        response.raise_for_status()
        reasoning: list[str] = []
        saw_content = False
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue  # blank keep-alives and SSE comments
            payload = line[len("data:") :].strip()
            if payload == "[DONE]":
                break
            try:
                delta = json.loads(payload)["choices"][0]["delta"]
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
            piece = delta.get("content")
            if piece:
                saw_content = True
                yield piece
            elif delta.get("reasoning"):
                reasoning.append(delta["reasoning"])
        if not saw_content and reasoning:
            # Some models put everything in `reasoning`; better that than a blank reply.
            yield _strip_reasoning("".join(reasoning))


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

    with st.popover("💬", type="primary"):
        st.caption("Pregunta sobre lo que ves en pantalla.")
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
                answer = _render_streamed(api_key, context, st.session_state.chat_messages)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})


def _render_streamed(api_key: str, context: str, history: list[dict[str, str]]) -> str:
    """Paint the answer token by token; return the final text for the history."""
    slot = st.empty()
    slot.markdown("_Pensando…_")
    answer = ""
    try:
        for piece in _hide_thinking(_stream(api_key, context, history)):
            answer += piece
            slot.markdown(answer + "▌")
    except requests.RequestException as exc:
        answer = f"⚠️ Error al llamar a OpenRouter: {exc}"
    answer = answer.strip() or "(respuesta vacía)"
    slot.markdown(answer)
    return answer
