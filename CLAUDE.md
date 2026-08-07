# Real Estate Simulator

Agent-based simulation of the **Spanish** real estate market. Actors (households, investors,
landlords, developers, bank, government) interact each tick; prices emerge from their
transactions. Goal: test policy ideas (rent caps, taxes, zoning) and see what actually moves
prices. Currently a scaffold — no model logic implemented. Roadmap: `docs/plan.md`.

## Stack

- Python 3.14 (min 3.12), numpy + pandas, Streamlit for the UI
- Package manager: uv

## Commands

- Setup: `uv sync --dev`
- UI: `streamlit run src/resim/ui/app.py`
- Test: `pytest`
- Lint/format: `ruff check . && ruff format .`

## Conventions

- Layout: src-layout — package in `src/resim/`, tests in `tests/`, docs in `docs/`. `uv sync --dev` is required before anything runs.
- Config vs scenario: `config.py` = how the world works, `scenario.py` = what we do to it. Never mix.
- Agents are read-only on state: `decide()` returns intents, the engine and `market/clearing.py` are the only writers.
- Scope: Spain, 3 zone types (tensioned metro / secondary city / rural) with migration between them.
- Bias control: every behavioural rule cites ≥2 independent sources (register in `docs/sources.md`); disputed estimates become parameter ranges, never resolved point values.

## Engineering standards

- Every model decision is written in `docs/model-spec.md` before it is coded. Code that disagrees with the spec is a bug in one of them.
- Reproducibility is a hard requirement: all randomness flows from a seeded Generator passed down from the engine. No module-level `random` or `np.random`.
- Tick order is a modelling choice, expressed in exactly one place (`engine.py`) and documented in the spec.
- Indicators are defined once, in `metrics.py`. The UI never computes a number inline.
- Parameters carry units and a source. An unsourced parameter is labelled a guess.
- No scenario result is reported until the baseline reproduces the validation targets in the spec.
- Typed dataclasses for config, scenario, state, and intents. No dicts as informal records.
- Keep modules small: one concern each; extract rather than grow.

## Working agreements

- New feature = /clear + new git branch (short kebab-case name).
- Framework work (Streamlit, pandas APIs): fetch current official docs first, cite into `docs/`.
- Delegate: test-runner after changes, lint-fixer before commits, commit-writer for messages.
- Expensive repeated work (parameter sweeps, long runs) gets cached to `runs/` with the seed and config hash in the filename.
- Long session: guided /compact with explicit keep/discard instructions.

## Boundaries

- Never commit secrets. `docs/` is reference material, not keys.
- `runs/` output is gitignored — never commit result artefacts.
- Do not add a database, auth, or LLM dependency without being asked. This project is deliberately lean.
