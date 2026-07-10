"""Rollout policies — random (ADR-001 baseline) and guided (H2 arm).

The guided policy replaces uniform-random move choice inside rollouts
with eps-greedy over `MoveScorer` scores (eps = 0.2 fixed per the
design note — not tuned, so the H2 comparison stays clean). Applies
only to single-pick selects (maxCount == 1, the dominant case);
multi-pick selects fall back to uniform random, documented v1
limitation.

Returned callables match `search.ismcts` rollout contract:
``(state, rng) -> terminal result code``.
"""

from __future__ import annotations

import random
from typing import Any, Callable

from env import search_engine
from evaluator.heuristic import MoveScorer

RESULT_IN_PROGRESS = -1
RESULT_DRAW = 2
EPSILON = 0.2

RolloutPolicy = Callable[[dict, random.Random], int]


def make_guided_rollout(
    scorer: MoveScorer,
    eps: float = EPSILON,
    cap: int = 3000,
) -> RolloutPolicy:
    """Build an eps-greedy guided rollout policy around `scorer`."""

    def guided(state: dict[str, Any], rng: random.Random) -> int:
        sid, obs = state["search_id"], state["observation"]
        for _ in range(cap):
            cur = obs["current"]
            if cur["result"] != RESULT_IN_PROGRESS:
                return cur["result"]
            sel = obs["select"]
            options = sel["option"]
            k = sel["maxCount"]
            if k == 1 and rng.random() >= eps:
                scores = scorer.score_all(options, obs)
                best = max(scores)
                choice = [rng.choice(
                    [i for i, sc in enumerate(scores) if sc == best]
                )]
            else:
                choice = rng.sample(range(len(options)), k)
            nxt = search_engine.search_step(sid, choice)
            sid, obs = nxt["search_id"], nxt["observation"]
        return RESULT_DRAW  # cap hit — draw, per ADR-004 timeout rule

    return guided
