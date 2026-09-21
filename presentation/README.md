# presentation/

One self-contained slide deck, in Spanish, for a reader with no economics and no modelling
background: what the model does, how the repository is built, and which systems-engineering
practices it rests on.

- `simulador-por-dentro.html` — 22 slides. Open it in a browser (`open
  presentation/simulador-por-dentro.html`); arrows or space to move, and it prints one slide
  per page for a PDF. No build step, no dependencies: the only external request is the
  Google Fonts stylesheet, and it falls back to system faces offline.

**It states model facts, so it goes stale like any other file here.** Every figure in it was
read from the repository on the day it was written (2026-09-18) and each one has an owner
elsewhere — the deck is never the source:

| Claim in the deck | Where it actually lives |
|---|---|
| The nine steps of a quarter | `docs/model-spec.md` §4, implemented in `engine.py` |
| Which numbers are citable as magnitudes | `docs/model-spec.md` §13.2 |
| Two live registered failures (targets 12 and 15) | `src/resim/diagnostics.py`, `docs/validation.md` |
| Supply does not reach the rent | `docs/validation.md` (2026-09-18) |
| The pre-registered Ley 12/2023 result | `docs/prereg/2026-09-18-f4-ley-12-2023-out-of-sample.md` |
| Negotiation margin, bids per listing, dispersion | `src/resim/diagnostics.py` criteria |

When one of those changes, fix the slide or drop it. A deck that contradicts
`docs/validation.md` is wrong by definition — the same rule the spec applies to code.
