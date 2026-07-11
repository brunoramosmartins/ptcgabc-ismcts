"""Random agent — Phase 0 ladder floor.

Picks `maxCount` distinct option indices uniformly at random. Mirrors the
reference `random_agent` from `kaggle_environments/envs/cabt/cabt.py`.
"""

from __future__ import annotations

import random

from agents.base import Agent


class RandomAgent(Agent):
    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()

    def choose(self, obs: dict) -> list[int]:
        n_options = len(obs["select"]["option"])
        max_count = min(obs["select"]["maxCount"], n_options)
        return self.rng.sample(range(n_options), max_count)
