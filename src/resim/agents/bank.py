"""Bank — sets the credit constraint that turns willingness-to-pay into ability-to-pay.

Approves or refuses mortgages against LTV/DTI caps and the current rate. Credit
availability usually moves prices more than income does; keep it a first-class actor.
"""

from __future__ import annotations

from ..state import WorldState
from .base import Intent


class Bank:
    def decide(self, state: WorldState) -> list[Intent]:
        raise NotImplementedError
