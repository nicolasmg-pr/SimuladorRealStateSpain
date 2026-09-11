# Pre-registration: <scenario name>

Copy to `docs/prereg/YYYY-MM-DD-<scenario>.md`, fill in, **commit, then run**. The git history
is what makes the ordering verifiable (`model-spec.md §13.4`).

- **Date:**
- **Commit hash:** (`git rev-parse HEAD`)
- **Config hash:** (`resim.cli.config_hash`, printed by the CLI run)
- **Scenario / lever:**
- **Parameters swept, with ranges:**
- **Seeds:**
- **Ticks:**

## Predicted direction, before running

One line per reported quantity: the sign theory predicts and the mechanism that would produce
it. A quantity with no prediction here is a diagnostic, not a result.

| Quantity | Predicted sign | Mechanism |
|---|---|---|

## Reporting category claimed

Per `model-spec.md §13.1`: magnitude / direction / not reportable, per quantity. If claiming
magnitude, state the Sobol share of the largest `assumed` parameter.

## Result (filled in after the run)

- **Run artefacts:** `runs/<file>.csv`
- **Measured:**
- **Prediction held / failed:**
