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

# Policy-C floor (t_floor): always run *some* search even when the bank
# is nearly drained, so a valid root move exists and the agent degrades
# to heuristic-speed play rather than forfeiting.
MIN_MOVE_SECONDS = 0.05


class ISMCTSAgent(Agent):
    """SO-ISMCTS with uniform consistent determinization (ADR-001).

    Time-budget policy (#27, EXP-008). By default the agent runs a fixed
    ``iterations`` per decision (policy A — unchanged, so H1–H7 hold).
    Two opt-in wall-clock policies keep it under Kaggle's per-agent
    ``remainingOverageTime`` bank:

    - **B (fixed cap):** set ``max_seconds_per_move`` — each decision
      stops at ``iterations`` or that many seconds, whichever first.
    - **C (adaptive):** set ``adaptive_budget=True`` — each decision
      reads the live bank ``obs["remainingOverageTime"]`` and spends
      ``(bank - overage_reserve) / budget_moves_ahead`` seconds. Re-read
      every move, so the bank cannot go negative regardless of game
      length or hardware speed (see ``notes/phase4-time-budget-calibration.md``).
    """

    def __init__(
        self,
        my_deck_list: list[int],
        opponent_deck_list: list[int] | None = None,
        iterations: int = 1000,
        c: float = DEFAULT_C,
        rng: random.Random | None = None,
        filler_card: int | None = None,
        rollout_policy=None,
        max_seconds_per_move: float | None = None,
        adaptive_budget: bool = False,
        overage_reserve: float = 60.0,
        budget_moves_ahead: int = 40,
        min_iterations: int = 1,
        opponent_list_is_assumed: bool = False,
    ) -> None:
        self.my_deck_list = my_deck_list
        self.opponent_deck_list = opponent_deck_list
        self.opponent_list_is_assumed = opponent_list_is_assumed
        self.iterations = iterations
        self.c = c
        self.rng = rng or random.Random()
        self.filler_card = filler_card
        self.rollout_policy = rollout_policy  # None = random (ADR-001)
        self.max_seconds_per_move = max_seconds_per_move
        self.adaptive_budget = adaptive_budget
        self.overage_reserve = overage_reserve
        self.budget_moves_ahead = budget_moves_ahead
        self.min_iterations = min_iterations
        self.fallback_events: list[str] = []

    def _budget_seconds(self, obs: dict) -> float | None:
        """Wall-clock budget for this decision, or ``None`` for policy A.

        Policy C (adaptive) splits the spendable bank over an estimated
        number of remaining decisions; policy B returns the fixed cap.
        """
        if self.adaptive_budget:
            remaining = obs.get("remainingOverageTime")
            if remaining is None:
                # Observation lacks the field (e.g. the raw sim.lib
                # harness) — fall back to the fixed cap if any.
                return self.max_seconds_per_move
            spendable = remaining - self.overage_reserve
            per_move = spendable / max(self.budget_moves_ahead, 1)
            return max(MIN_MOVE_SECONDS, per_move)
        return self.max_seconds_per_move

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
                max_seconds=self._budget_seconds(obs),
                min_iterations=self.min_iterations,
                opponent_list_is_assumed=self.opponent_list_is_assumed,
            )
        except (SearchApiError, DeterminizationError) as exc:
            turn = (obs.get("current") or {}).get("turn")
            self.fallback_events.append(f"turn={turn}: {exc}")
            n = len(obs["select"]["option"])
            return list(range(min(obs["select"]["maxCount"], n)))
