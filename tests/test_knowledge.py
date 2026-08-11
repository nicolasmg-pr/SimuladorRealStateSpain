"""The chat's retrieval over `docs/`: does a Spanish question reach the right note?

These are behavioural tests, not string matching on doc contents: they assert which
file wins, so rewording a note does not break them, but breaking the Spanish→English
expansion or the section split does.
"""

from __future__ import annotations

import pytest

from resim.ui import knowledge


def sources(question: str, pinned: str | None = None) -> list[str]:
    """Distinct doc paths the retriever attaches, in order."""
    ordered: list[str] = []
    for line in knowledge.retrieve(question, pinned=pinned).splitlines():
        if line.startswith("--- ") and line.endswith(" ---"):
            path = line[4:-4].split(" › ")[0]
            if path not in ordered:
                ordered.append(path)
    return ordered


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("¿por qué liberar suelo no abarata la vivienda?", "docs/policies/land-release.md"),
        ("¿qué pasó con el tope de alquiler en Cataluña?", "docs/policies/rent-cap.md"),
        ("¿cuánta vivienda vacía hay y cómo se grava?", "docs/policies/vacancy-tax.md"),
        ("¿los pisos turísticos suben el alquiler?", "docs/policies/tourist-rental-restriction.md"),
        ("¿los avales del ICO se capitalizan en precios?", "docs/policies/demand-subsidy.md"),
        ("¿qué objetivos de validación tiene el modelo?", "docs/validation.md"),
    ],
)
def test_spanish_question_reaches_the_english_note(question: str, expected: str) -> None:
    assert expected in sources(question)


def test_active_lever_note_is_pinned_first() -> None:
    # Question names no policy; the note for the lever on screen must still lead.
    found = sources("¿qué está pasando aquí?", pinned="docs/policies/rent-cap.md")
    assert found[0] == "docs/policies/rent-cap.md"


def test_evidence_stays_within_the_budget() -> None:
    text = knowledge.retrieve(
        "suelo alquiler impuesto vivienda vacía turístico aval hogares promotores banca",
        pinned="docs/policies/land-release.md",
    )
    assert len(text) <= knowledge.EVIDENCE_BUDGET_CHARS


def test_unmatched_question_still_lists_what_exists() -> None:
    text = knowledge.retrieve("zzzqqq")
    assert "docs/model-spec.md" in text


def test_catalogue_covers_every_doc() -> None:
    listed = {line.removeprefix("- ") for line in knowledge.catalogue().splitlines()}
    on_disk = {
        str(path.relative_to(knowledge.DOCS_DIR.parent))
        for path in knowledge.DOCS_DIR.rglob("*.md")
    }
    assert listed == on_disk
