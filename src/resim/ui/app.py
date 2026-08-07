"""Streamlit app — the demo surface.

Run: streamlit run src/resim/ui/app.py

Intended shape:
  sidebar  — baseline parameters, then policy levers that build a Scenario
  main     — run button, price/rent series over time, baseline vs scenario diff
  bottom   — actor-level view: who bought, who was priced out

Rule: this file only calls into resim.scenario, resim.engine, and resim.metrics.
Any number it computes itself is a number the tests do not cover.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
