"""ISMCTS agent — Phase 3. Determinize → Select → Expand → Rollout → Backprop.

Thin adapter binding `search/ismcts.py` to the Agent interface. All
search behavior (iterations, exploration constant, opponent-deck
knowledge) is fixed at construction so the agent is stateless across
decisions, matching the local-ladder factory contract.

Fallback policy: some decisions may be unsearchable — the engine can
reject SearchBegin (e.g. during the setup phase), or the determinizer
can hit a zone it doesn't account for yet. Rather than crash
mid-match, the agent falls back to the heuristic first-`maxCount`
choice for that single decision and records the event in
``fallback_events`` so bring-up scripts can report exactly what was
skipped. Persistent fallbacks would bias any experiment, so EXP runs
must assert the counter stays at (or near) zero outside the setup
phase.
"""

from __future__ import annotations

import random

from agents.base import Agent
from env.search_engine import SearchApiError
from search import ismcts
from search.determinize import DeterminizationError
from search.ucb import DEFAULT_C


class ISMCTSAgent(Agent):
    """SO-ISMCTS with uniform consistent determinization (ADR-001)."""

    def __init__(
        self,
        my_deck_list: list[int],
        opponent_deck_list: list[int] | None = None,
        iterations: int = 1000,
        c: float = DEFAULT_C,
        rng: random.Random | None = None,
        filler_card: int | None = None,
        rollout_policy=None,
    ) -> None:
        self.my_deck_list = my_deck_list
        self.opponent_deck_list = opponent_deck_list
        self.iterations = iterations
        self.c = c
        self.rng = rng or random.Random()
        self.filler_card = filler_card
        self.rollout_policy = rollout_policy  # None = random (ADR-001)
        self.fallback_events: list[str] = []

    def choose(self, obs: dict) -> list[int]:
        try:
            return ismcts.decide(
                obs,
                my_deck_list=self.my_deck_list,
                opponent_deck_list=self.opponent_deck_list,
                rng=self.rng,
                iterations=self.iterations,
                c=self.c,
                filler_card=self.filler_card,
                rollout_policy=self.rollout_policy,
            )
        except (SearchApiError, DeterminizationError) as exc:
            turn = (obs.get("current") or {}).get("turn")
            self.fallback_events.append(f"turn={turn}: {exc}")
            return list(range(obs["select"]["maxCount"]))
