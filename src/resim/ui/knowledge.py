"""Lexical retrieval over `docs/` so the chat can reach every note in the repo.

The docs tree is ~460 kB (~130k tokens): sources, model spec, validation targets, one
note per actor and one per policy. Too much to paste into every request, and the
answer to a given question lives in one or two sections of it. So we index the tree by
markdown section, score sections against the question with BM25, and hand the chat the
best ones within a character budget.

No new dependencies and no embeddings: the corpus is small, Spanish-and-English
technical prose, and the questions reuse its vocabulary ("suelo", "tope de alquiler",
"vivienda vacía"), which is where lexical scoring is strongest.

This module is read-only on `docs/` and never derives model numbers.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"
EVIDENCE_BUDGET_CHARS = 60_000  # ≈17k tokens of notes per request
SECTION_MAX_CHARS = 12_000  # a single over-long section cannot eat the whole budget
TOP_SECTIONS = 12

_K1 = 1.5  # BM25 term-frequency saturation
_B = 0.75  # BM25 length normalisation

# Roadmap and index files name every topic without explaining any of them; they should
# lose to the note that actually holds the evidence.
_WEIGHTS = {
    "docs/plan.md": 0.5,
    "docs/README.md": 0.5,
    "docs/policies/README.md": 0.5,
    "docs/actors/README.md": 0.5,
}

_WORD = re.compile(r"[a-z0-9]{3,}")
_HEADING = re.compile(r"^(#{1,3}) +(.*)$", re.MULTILINE)

# Function words only: BM25's IDF already discounts domain words like "vivienda".
_STOPWORD_TEXT = """
para por con sin sobre como que del las los una unos unas esta este estos estas
son ser sea han hay mas pero cuando donde cual cuales porque segun entre desde hasta
solo tambien muy todo toda todos todas otro otra otros otras cada tras ante bajo
the and for with that this from are was were has have not but they their its
"""
_STOPWORDS = frozenset(_STOPWORD_TEXT.split())

# The notes are written in English, the questions arrive in Spanish. Without this the
# scorer never connects "inversor" to `docs/actors/investor-large.md`. Query-side only:
# both the Spanish word and its English counterparts are searched.
_EXPANSIONS = {
    "inversor": ("investor", "landlord"),
    "inversores": ("investor", "landlord"),
    "casero": ("landlord",),
    "caseros": ("landlord",),
    "arrendador": ("landlord",),
    "propietario": ("owner", "landlord"),
    "propietarios": ("owner", "landlord"),
    "propiedad": ("ownership", "tenure"),
    "inquilino": ("tenant", "renter"),
    "inquilinos": ("tenant", "renter"),
    "hogar": ("household",),
    "hogares": ("household",),
    "promotor": ("developer",),
    "promotores": ("developer",),
    "banco": ("bank", "lender"),
    "banca": ("bank", "lender"),
    "gobierno": ("government", "policy"),
    "vivienda": ("housing", "dwelling", "home"),
    "viviendas": ("housing", "dwellings", "homes"),
    "alquiler": ("rent", "rental", "lease"),
    "alquileres": ("rent", "rental"),
    "tope": ("cap", "control"),
    "suelo": ("land", "zoning"),
    "urbanizable": ("land", "zoning", "planning"),
    "licencia": ("permit", "permitting", "licence"),
    "impuesto": ("tax",),
    "impuestos": ("tax", "taxation"),
    "transmisiones": ("transaction", "transfer"),
    "vacia": ("vacancy", "vacant", "empty"),
    "vacias": ("vacancy", "vacant", "empty"),
    "turistico": ("tourist", "short", "airbnb"),
    "turisticos": ("tourist", "short", "airbnb"),
    "turistica": ("tourist", "short", "airbnb"),
    "aval": ("guarantee", "subsidy"),
    "avales": ("guarantee", "subsidy"),
    "ayuda": ("subsidy", "support"),
    "ayudas": ("subsidy", "support"),
    "publica": ("public", "social"),
    "hipoteca": ("mortgage",),
    "hipotecas": ("mortgage",),
    "tipos": ("rates", "interest", "euribor"),
    "oferta": ("supply", "elasticity"),
    "demanda": ("demand",),
    "precio": ("price",),
    "precios": ("price", "prices"),
    "renta": ("income",),
    "asequibilidad": ("affordability",),
    "acceso": ("affordability", "access"),
    "migracion": ("migration",),
    "construccion": ("construction", "completions", "supply"),
    "obra": ("construction", "permit"),
    "burbuja": ("bubble", "boom"),
    "expectativas": ("expectations", "momentum"),
    "validacion": ("validation", "targets"),
    "fuente": ("source", "register"),
    "fuentes": ("source", "register"),
}


@dataclass(frozen=True)
class Section:
    """One markdown section: its source path, its heading trail, and its text."""

    path: str  # repo-relative, e.g. "docs/policies/land-release.md"
    heading: str  # e.g. "Land release & permitting speed › 3. Evidence against"
    text: str

    def render(self) -> str:
        body = self.text
        if len(body) > SECTION_MAX_CHARS:
            body = body[:SECTION_MAX_CHARS] + "\n[…sección truncada…]"
        return f"--- {self.path} › {self.heading} ---\n{body}"


def _fold(text: str) -> str:
    """Lowercase and strip accents so 'liberación' and 'liberacion' match."""
    lowered = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in lowered if unicodedata.category(char) != "Mn")


def _tokens(text: str) -> list[str]:
    return [word for word in _WORD.findall(_fold(text)) if word not in _STOPWORDS]


def _query_tokens(question: str) -> set[str]:
    """Question words plus their English counterparts, since the notes are English."""
    words = _tokens(question)
    expanded = set(words)
    for word in words:
        expanded.update(_EXPANSIONS.get(word, ()))
    return expanded


def _split_sections(path: Path, root: Path) -> list[Section]:
    """Split a markdown file at its headings; the title travels with every section."""
    raw = path.read_text()
    relative = str(path.relative_to(root.parent))
    matches = list(_HEADING.finditer(raw))
    if not matches:
        return [Section(relative, path.stem, raw)] if raw.strip() else []

    title = matches[0].group(2) if matches[0].group(1) == "#" else path.stem
    sections = []
    preamble = raw[: matches[0].start()].strip()
    if preamble:
        sections.append(Section(relative, f"{title} › (intro)", preamble))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        body = raw[match.start() : end].strip()
        if not body:
            continue
        heading = match.group(2)
        trail = heading if heading == title else f"{title} › {heading}"
        sections.append(Section(relative, trail, body))
    return sections


@lru_cache(maxsize=1)
def _index() -> tuple[tuple[Section, ...], tuple[Counter, ...], Counter, float]:
    """Sections, their term counts, document frequencies, and mean section length."""
    sections: list[Section] = []
    for path in sorted(DOCS_DIR.rglob("*.md")):
        sections.extend(_split_sections(path, DOCS_DIR))

    # Path and heading are indexed too: "investor-large.md › Investor (large)" is the
    # strongest signal a section carries, and it is not always repeated in the body.
    counts = tuple(
        Counter(_tokens(f"{section.path} {section.heading} {section.heading}\n{section.text}"))
        for section in sections
    )
    document_frequency: Counter = Counter()
    for count in counts:
        document_frequency.update(count.keys())
    mean_length = sum(sum(count.values()) for count in counts) / max(len(counts), 1)
    return tuple(sections), counts, document_frequency, mean_length


def _scored(question: str) -> list[tuple[float, Section]]:
    sections, counts, document_frequency, mean_length = _index()
    query = _query_tokens(question)
    if not query or not sections:
        return []

    total = len(sections)
    ranked = []
    for section, count in zip(sections, counts, strict=True):
        length = sum(count.values()) or 1
        score = 0.0
        for term in query:
            frequency = count.get(term, 0)
            if not frequency:
                continue
            appearances = document_frequency[term]
            idf = math.log(1 + (total - appearances + 0.5) / (appearances + 0.5))
            norm = _K1 * (1 - _B + _B * length / mean_length)
            score += idf * frequency * (_K1 + 1) / (frequency + norm)
        if score > 0:
            ranked.append((score * _WEIGHTS.get(section.path, 1.0), section))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    return ranked


def catalogue() -> str:
    """One line per document, so the model knows what else it could be asked about."""
    paths = sorted({str(p.relative_to(DOCS_DIR.parent)) for p in DOCS_DIR.rglob("*.md")})
    return "\n".join(f"- {path}" for path in paths)


def retrieve(question: str, *, pinned: str | None = None) -> str:
    """Docs sections most relevant to `question`, plus `pinned` (the active lever's note).

    `pinned` is a repo-relative path; its sections always come first, because the run
    on screen is that policy and the user's question is usually about it.
    """
    chosen: list[Section] = []
    used = 0

    def take(section: Section) -> bool:
        nonlocal used
        rendered = section.render()
        if used + len(rendered) > EVIDENCE_BUDGET_CHARS:
            return False
        chosen.append(section)
        used += len(rendered)
        return True

    if pinned:
        for section in _index()[0]:
            if section.path == pinned and not take(section):
                break

    seen = {(section.path, section.heading) for section in chosen}
    for _, section in _scored(question)[:TOP_SECTIONS]:
        if (section.path, section.heading) in seen:
            continue
        if not take(section):
            break
        seen.add((section.path, section.heading))

    if not chosen:
        return (
            "(Ninguna sección de `docs/` coincide con la pregunta. Documentos "
            f"disponibles:\n{catalogue()})"
        )
    return "\n\n".join(section.render() for section in chosen)
