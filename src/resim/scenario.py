"""Policy levers — the "what if" layer.

A Scenario is a named set of interventions applied to a baseline SimConfig at given ticks.
This is the module the UI drives: the user picks levers, we produce a Scenario, run it,
and diff its metrics against the baseline run.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import SimConfig


@dataclass(frozen=True)
class Intervention:
    """One policy change, applied from `start_tick` onward.

    Candidate levers to model (pick and formalise in docs/model-spec.md):
    rent cap, property tax change, transaction tax, interest rate shock,
    LTV/DTI limit change, social housing construction, zoning/permit volume,
    short-term-rental restriction, vacancy tax, buyer subsidy.
    """

    name: str
    start_tick: int

    def apply(self, config: SimConfig) -> SimConfig:
        """Return a new config with this intervention folded in. Never mutates."""
        raise NotImplementedError


@dataclass(frozen=True)
class Scenario:
    """A baseline plus an ordered set of interventions."""

    name: str
    baseline: SimConfig
    interventions: tuple[Intervention, ...] = ()

    def config_at(self, tick: int) -> SimConfig:
        """Config as it stands at `tick`, with all interventions active by then applied."""
        raise NotImplementedError
