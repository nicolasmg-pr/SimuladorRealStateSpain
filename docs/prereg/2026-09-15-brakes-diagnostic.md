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

Run 2026-09-15 at commit `9ca8bba`, 10 seeds, `runs/holdout_2008_2013_10seeds.json`.

| Quantity | 14 Sep (no brakes) | 15 Sep (brakes) | Predicted | |
|---|---|---|---|---|
| Price fall | −56.9% ± 2.2 | **−59.0% ± 0.8** | smaller fall | **prediction failed** |
| Transactions (end/start) | +86.6% | +82.8% | lower | weakly right, instrument still broken |
| Arrears, peak | 2.2% ± 0.3 | **3.5% ± 0.3** | higher | **right** |
| Foreclosure flow, peak | 1.34% ± 0.24 | 1.30% ± 0.26 | lower | right, inside noise |
| Forborne share, peak | did not exist | **0.74% ± 0.16** ≈ 34,000 families | > 0 | **right, and the right order**: the CBP reached 45,697 families in five years |

**The price prediction failed and the reason matters.** This comparison is across two model
versions, and the versions differ by more than the brakes: forbearance's take-up draw needed a
new RNG stream, which re-randomises every run. A 2.1pp move against a 0.8–2.2pp seed spread
cannot be attributed to loss aversion at all. The clean attribution is the toggle test in
`tests/test_brakes.py`, same version, brake on and off in a synthetic bust: the fall is
**−68.8% with it against −72.5% without**, and transactions are **10.8 per tick against 63**.
The mechanism does what Genesove & Mayer describe. What it does not do is close a 12pp gap
against the observed −30…−45%.

**The forbearance predictions were right on all three legs**, and the arrears gap against the
BdE's 6.28% peak halved — 2.2% → 3.5%.

Nothing was changed after this run either. The episode's verdict against the observed bands is
still three of six, and it is still not evidence about this model.
