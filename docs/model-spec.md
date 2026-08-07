# Model spec

The authoritative description of what the simulation claims about the world.
Write this before implementing. Code that disagrees with this file is a bug in one of them.

Status: **empty scaffold** — every section below is an open decision.

## 1. Question the model answers

> Which interventions move real estate prices, in which direction, and how much?

State precisely what counts as an answer: a signed effect, a magnitude, or only a ranking of policies.

## 2. Tick

- What is one tick? (month / quarter / year)
- How many ticks is a run?
- What is the geographic scope? (one city / zones / a single market)

## 3. Actors

For each actor: what it observes, what it decides, what constrains it.

| Actor | Observes | Decides | Constrained by |
|---|---|---|---|
| Household | | | |
| Investor | | | |
| Landlord | | | |
| Developer | | | |
| Bank | | | |
| Government | | | |

## 4. Tick order

Who acts first changes the result. Write the final order here; `engine.py` must match it exactly.

## 5. Price formation

Mechanism (sealed-bid / bilateral bargaining / tatonnement), reserve prices, how the
asking price updates after a failed listing, and how the price index is computed.

## 6. Expectations

How agents forecast future prices. Adaptive extrapolation produces bubbles; perfect
foresight does not. This choice largely determines whether the model shows cycles.

## 7. Parameters

Every parameter with its units, plausible range, and source. Unsourced parameters are guesses —
label them as such.

## 8. Interventions

One row per policy lever: what it changes mechanically, and the effect direction theory predicts.

## 9. Validation

What the baseline run must reproduce before any scenario result is trustworthy
(price-to-income level, transaction volume, vacancy rate, cycle length).
Without this section the model is a plausible-looking random number generator.

## 10. Known limitations

What the model deliberately does not represent, and where its answers should not be used.
