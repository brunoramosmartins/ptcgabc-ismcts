"""ISMCTS agent — Phase 3. Determinize → Select → Expand → Rollout → Backprop."""

from __future__ import annotations

from agents.base import Agent


class ISMCTSAgent(Agent):
    def choose(self, obs: dict) -> list[int]:
        raise NotImplementedError("Implement in Phase 3.")
