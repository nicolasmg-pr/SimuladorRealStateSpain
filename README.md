# Real Estate Simulator

An agent-based simulation of a real estate market: households, investors, landlords,
developers, a bank, and a government interact each tick, prices emerge from their
transactions, and policy interventions can be applied to see what actually moves prices.

**Status: the redesign's seven phases are done** (precision contract, bug fixes,
profitability block, insolvency, price formation, recalibration, claims ledger). The model
runs, is calibrated on 2014–2025 moments, has been tested out of sample twice — the sealed
2008–13 episode and the rent-cap statute in force — and quotes a number only where the variance
rule allows one, **never a dated forecast** — see the reporting contract below.

New here, or explaining this to someone else? Open
**[presentation/simulador-por-dentro.html](presentation/simulador-por-dentro.html)** — 22
slides, plain Spanish, no prerequisites: how the model works, how it is built, and the
systems-engineering practices behind it.

Start here: **[docs/claims.md](docs/claims.md)** — public claims about Spanish housing, each
quoted and attributed, against what the model can actually say about them. That file is what
the rest of the repository exists to produce.

## Setup

```bash
uv sync --dev            # or: pip install -e ".[dev]"
```

## Run

```bash
uv run streamlit run src/resim/ui/app.py   # UI  (bare `streamlit` is not on PATH)
uv run resim --help                        # headless run
uv run pytest                              # tests
uv run ruff check . && uv run ruff format .  # lint + format
uv run python -m resim.levers --jobs 10    # the lever sweep behind docs/claims.md
```

Everything runs through `uv run`, which uses the project venv without activating it. If you
would rather type the bare commands, `source .venv/bin/activate` once per shell.

## Layout

```
src/resim/
├── config.py      # how the world works
├── scenario.py    # what we do to it (policy levers)
├── state.py       # world state for one tick
├── engine.py      # the tick loop
├── metrics.py     # run outputs, baseline vs scenario diff
├── rng.py         # seeded randomness
├── agents/        # household, investor, landlord, developer, bank, government
├── market/        # housing stock, matching, price formation
└── ui/            # Streamlit app
tests/             # outside the package
presentation/      # one Spanish slide deck explaining the model to non-specialists
docs/
├── claims.md            # public claims vs the model — the output
├── model-spec.md        # every model decision, written before it was coded
├── validation.md        # what was measured, including what fails
├── assumptions.md       # every assumption, with its falsifier
├── sources.md           # every document used, tier and viewpoint
├── holdout-2008-2013.md # the sealed episode, run once
├── prereg/              # predictions committed before each run
├── actors/ policies/    # the evidence dossiers behind the rules
└── experiments/         # lever write-ups
```

## What the model may and may not claim

The variance rule (`model-spec §13.2`) decides it, not taste: no quantity is quoted as a
number if an unsourced parameter explains more than 25% of its variance in the Sobol
decomposition. After the phase-G re-run (1,792 evaluations) and the sourcing work of §5c.8
that leaves:

- **magnitudes**, each conditional on its sourced bands — the price level and price-to-income,
  transactions, completions, arrears, time to sale, bids per listing.
- **direction only** — the whole rent side (rent level, tensioned vacancy, overburden), the
  ownership rate, the zone price ratio, the cash-purchase share and the negotiation margin.
  Read the sign and the seed count, never the size.
- **neither** — the rent leg of any supply lever. Building at saturation fills the zone with
  empty dwellings and leaves the posted ask where it was, because the one channel from supply
  to the ask is clipped at −2.5% (`docs/validation.md`, 2026-09-18).

Point forecasts are outside the contract by design: the model has no calendar, so tick 60 is
"≈15 years of a Spain-like market", not 2041.

Nothing is reported on fewer than ten seeds and no result is quoted without the seed count.
Two out-of-sample tests have been taken, each exactly once and each pre-registered before it
ran: the 2008–13 hold-out (2026-09-14 — three of six predictions passed, and no parameter may
be changed on its evidence again) and Ley 12/2023, the rent-cap statute in force (2026-09-18 —
the failure condition was a rise in tensioned rent; the model produced −0.79%, indistinguishable
from zero, so the prediction held and the evidence is not spent).

## Before changing model code

Read [docs/model-spec.md](docs/model-spec.md) first and change it first: a decision that is
not in the spec is not a decision this project has taken, and code that disagrees with the
spec is a bug in one of them. Tick order, price mechanism and expectation formation determine
the results more than any parameter does.
