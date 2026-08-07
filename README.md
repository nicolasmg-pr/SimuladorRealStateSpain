# Real Estate Simulator

An agent-based simulation of a real estate market: households, investors, landlords,
developers, a bank, and a government interact each tick, prices emerge from their
transactions, and policy interventions can be applied to see what actually moves prices.

**Status: scaffold.** Structure and seams exist; no model logic is implemented.

## Setup

```bash
uv sync --dev            # or: pip install -e ".[dev]"
```

## Run

```bash
streamlit run src/resim/ui/app.py   # UI
resim --help                        # headless run
pytest                              # tests
ruff check . && ruff format .       # lint + format
```

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
docs/              # model spec and calibration references
```

## Before writing model code

Fill in [docs/model-spec.md](docs/model-spec.md). Tick order, price mechanism, and
expectation formation determine the results more than any parameter does.
