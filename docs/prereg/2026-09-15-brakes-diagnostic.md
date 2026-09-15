# Pre-registration: the 2008–13 run as a DIAGNOSTIC, after the brakes

**This is not a hold-out.** The 2008–13 episode was spent on 2026-09-14
(`docs/prereg/2026-09-14-holdout-2008-2013.md`). The model has since gained two mechanisms —
nominal loss aversion and Código de Buenas Prácticas forbearance (`model-spec §5d`) — *because
that run showed they were missing*. Whatever the provenance of their parameters, the model is
now in-sample on the episode, and §13.11 says what follows: the run below may be executed as a
check on mechanisms, and may **never** be cited as out-of-sample validation.

It is pre-registered anyway, for the same reason as before: the predictions have to be on the
record before the numbers are, or "the brakes worked" is unfalsifiable.

- **Date:** 2026-09-15
- **Commit hash:** the commit that adds this file; the run follows it
- **Scenario:** `resim.holdout.scenario()`, unchanged — same 24 ticks, same registered inputs
- **Seeds:** 10
- **What changed since the run of 2026-09-14:** only §5d. No parameter of any pre-existing
  mechanism was touched, and neither new parameter was set by looking at 2008–13 output:
  α = 0.30/0.15 is Genesove & Mayer's measured 25–35% halved for investors as they found;
  the forbearance terms, thresholds and viability test are RDL 6/2012 verbatim; take-up 0.20
  comes from the CBP's own operation counts against the deliveries of the same years.

## Predicted direction, before running

| Quantity | 2026-09-14 result | Prediction now | Mechanism |
|---|---|---|---|
| Price fall, peak to trough | −56.9% | **smaller fall** — and still outside −30…−45% is the likely outcome | loss-averse sellers hold out, so the index falls more slowly [Genesove & Mayer] |
| Transactions | recovery, instrument error | **lower volume throughout** | the same sellers withdraw: the price–volume correlation is the source's own conclusion |
| Arrears, peak | 2.2% | **higher**, because restructured loans stay doubtful | the BdE classified refinanced mortgages as doubtful, which is why the ratio stayed high after deliveries peaked |
| Foreclosure flow, peak | 1.34%/yr | **lower** | a restructuring cannot be foreclosed while it holds; the CBP reached ~a fifth of the distressed flow |
| Forborne share | did not exist | **> 0, peaking in the worst years** | the umbral de exclusión binds on income, which collapses in the episode |

**What would count as the brakes failing.** If the price fall does not shrink, loss aversion
does not do in this model what its source says it does in data. If arrears do not rise or
foreclosures do not fall, the forbearance implementation is not the statute it claims to be.
Either would be reported as a failure of the mechanism, not of the episode.

**What no outcome here can establish.** That the model predicts busts. It has now seen this
one.

## Result (filled in after the run)

See `docs/validation.md`, "The brakes, and what the burned episode says about them".
