"""The chat's failure paths: a silent one is worse than a loud one.

OpenRouter reports mid-stream failures as an HTTP 200 whose body carries an `error` object
instead of a choice. Until 2026-09-16 the reader skipped anything without `choices`, so an
exhausted free worker — `ResourceExhausted: Worker local total request limit reached
(16/16)`, which is what the user actually hit — reached the screen as "(respuesta vacía)".
These tests pin the two silent endings to visible ones.

No network: `requests.post` is replaced by a fake that replays a canned SSE body.
"""

from __future__ import annotations

import json

import pytest

from resim.ui import chat


class _FakeResponse:
    def __init__(self, lines: list[str]):
        self._lines = lines
        self.encoding = "utf-8"

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode: bool = False):
        yield from self._lines


def _sse(*events: dict) -> list[str]:
    """One SSE body, in the shape OpenRouter sends: `data:` lines, blanks, then [DONE]."""
    lines: list[str] = []
    for event in events:
        lines.append(f"data: {json.dumps(event)}")
        lines.append("")
    lines.append("data: [DONE]")
    return lines


def _delta(**fields) -> dict:
    return {"choices": [{"delta": fields, "finish_reason": None}]}


@pytest.fixture
def replay(monkeypatch):
    def install(lines: list[str]):
        monkeypatch.setattr(chat.requests, "post", lambda *a, **k: _FakeResponse(lines))

    return install


def _drain(history=None) -> str:
    return "".join(chat._stream("k", "ctx", "ev", history or [{"role": "user", "content": "q"}]))


def test_content_streams_through(replay):
    replay(_sse(_delta(content="Ho"), _delta(content="la")))
    assert _drain() == "Hola"


def test_a_mid_stream_error_is_raised_not_swallowed(replay):
    """The exact failure the user hit: HTTP 200, no choice, an `error` object instead."""
    replay(
        _sse(
            {
                "error": {
                    "message": "Upstream error from Nvidia: ResourceExhausted: Worker local "
                    "total request limit reached (16/16)",
                    "code": 429,
                }
            }
        )
    )
    with pytest.raises(chat.ChatStreamError, match="ResourceExhausted"):
        _drain()


def test_an_empty_stream_says_so_instead_of_returning_nothing(replay):
    replay([*_sse({"choices": [{"delta": {}, "finish_reason": "length"}]})])
    with pytest.raises(chat.ChatStreamError, match="length"):
        _drain()


def test_reasoning_only_answers_fall_back_to_the_reasoning(replay):
    """Some models put the whole answer in `reasoning`. Better that than a blank reply."""
    replay(_sse(_delta(reasoning="Pensando: "), _delta(reasoning="la respuesta.")))
    assert _drain() == "Pensando: la respuesta."


def test_partial_answers_survive_a_late_failure(replay):
    """A stream that dies after writing something keeps what it wrote, plus the reason."""
    replay(
        [
            f"data: {json.dumps(_delta(content='Media '))}",
            "",
            f"data: {json.dumps({'error': {'message': 'boom'}})}",
            "",
        ]
    )
    out = ""
    with pytest.raises(chat.ChatStreamError):
        for piece in chat._stream("k", "c", "e", [{"role": "user", "content": "q"}]):
            out += piece
    assert out == "Media "
