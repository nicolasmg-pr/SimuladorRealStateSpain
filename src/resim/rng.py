"""Seeded randomness.

Every stochastic draw in the simulation goes through a Generator handed down from
the engine. No module ever calls `random` or `numpy.random` at module level — a run
must be reproducible from its seed alone.
"""

from __future__ import annotations

import numpy as np


def make_rng(seed: int) -> np.random.Generator:
    """Return the single Generator for one run."""
    raise NotImplementedError


def spawn(rng: np.random.Generator, count: int) -> list[np.random.Generator]:
    """Split a parent Generator into independent child streams (one per agent group)."""
    raise NotImplementedError
