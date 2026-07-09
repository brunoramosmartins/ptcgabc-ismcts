"""PIMC agent — diagnostic-ladder arm (Determinized UCT).

Thin adapter binding `search/pimc.py` to the Agent interface. Same
fallback contract as ISMCTSAgent: an unsearchable decision falls back
to the first-`maxCount` heuristic choice and is recorded in
``fallback_events`` for the EXP validity flag.
"""

from __future__ import annotations

import random

from agents.base import Agent
from env.search_engine import SearchApiError
from search import pimc
from search.determinize import DeterminizationError
from search.pimc import DEFAULT_K
from search.ucb import DEFAULT_C


class PIMCAgent(Agent):
    """Perfect-Information Monte Carlo (K independent trees + vote)."""

    def __init__(
        self,
        my_deck_list: list[int],
        opponent_deck_list: list[int] | None = None,
        iterations: int = 1000,
        k: int = DEFAULT_K,
        c: float = DEFAULT_C,
        rng: random.Random | None = None,
        filler_card: int | None = None,
    ) -> None:
        self.my_deck_list = my_deck_list
        self.opponent_deck_list = opponent_deck_list
        self.iterations = iterations
        self.k = k
        self.c = c
        self.rng = rng or random.Random()
        self.filler_card = filler_card
        self.fallback_events: list[str] = []

    def choose(self, obs: dict) -> list[int]:
        try:
            return pimc.decide_pimc(
                obs,
                my_deck_list=self.my_deck_list,
                opponent_deck_list=self.opponent_deck_list,
                rng=self.rng,
                iterations=self.iterations,
                k=self.k,
                c=self.c,
                filler_card=self.filler_card,
            )
        except (SearchApiError, DeterminizationError) as exc:
            turn = (obs.get("current") or {}).get("turn")
            self.fallback_events.append(f"turn={turn}: {exc}")
            return list(range(obs["select"]["maxCount"]))
