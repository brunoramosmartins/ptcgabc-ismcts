"""Heuristic agent — Phase 1 baseline. Beats random; benchmark for ISMCTS gains."""

from __future__ import annotations

from agents.base import Agent


class HeuristicAgent(Agent):
    def choose(self, obs: dict) -> list[int]:
        raise NotImplementedError("Implement in Phase 1.")
