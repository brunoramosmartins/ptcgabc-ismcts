"""Random agent — Phase 0 ladder floor. To implement in Phase 0."""

from __future__ import annotations

from typing import Any

from agents.base import Agent


class RandomAgent(Agent):
    """Picks `maxCount` distinct option indices uniformly at random."""

    def choose(self, obs: Any) -> list[int]:
        raise NotImplementedError("Implement in Phase 0 — see data/kaggle/sample_submission/main.py.")
