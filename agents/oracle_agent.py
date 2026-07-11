"""Oracle agent — cheating UCT on the true state. LOCAL DIAGNOSTIC ONLY.

Never submitted (competition-rule violation; `scripts/submit.py`
refuses bundles that mention "oracle"). Same fallback contract as the
other search agents so the EXP validity flag stays comparable.
"""

from __future__ import annotations

import random

from agents.base import Agent
from env.search_engine import SearchApiError
from search import oracle
from search.oracle import OracleError
from search.ucb import DEFAULT_C


class OracleAgent(Agent):
    """Perfect-information UCT fed the true hidden state."""

    def __init__(
        self,
        iterations: int = 1000,
        c: float = DEFAULT_C,
        rng: random.Random | None = None,
    ) -> None:
        self.iterations = iterations
        self.c = c
        self.rng = rng or random.Random()
        self.fallback_events: list[str] = []

    def choose(self, obs: dict) -> list[int]:
        try:
            return oracle.decide_oracle(
                obs,
                rng=self.rng,
                iterations=self.iterations,
                c=self.c,
            )
        except (SearchApiError, OracleError) as exc:
            turn = (obs.get("current") or {}).get("turn")
            self.fallback_events.append(f"turn={turn}: {exc}")
            n = len(obs["select"]["option"])
            return list(range(min(obs["select"]["maxCount"], n)))
