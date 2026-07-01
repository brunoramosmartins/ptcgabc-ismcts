"""Heuristic agent — Phase 1 baseline.

Deterministically picks the first `maxCount` options in the order the
`cabt` engine presents them. Rationale: the engine's option ordering is
not documented as random; even a weak correlation with plausibility
means a deterministic first-index pick strictly reduces variance vs a
uniform random baseline, and the H1 comparison in Phase 3 measures
whatever win-rate lift this produces.

The design is intentionally minimal:

- Zero state. No hidden RNG, no bookkeeping.
- Zero information about card semantics. Phase 4 evaluator (ADR-003)
  replaces this with a real feature-based scorer; the interface
  stays the same.
- Deterministic. Two runs on the same match seed produce identical
  action sequences, so paired bootstrap variance-reduction from
  `docs/benchmark-protocol.md` applies cleanly.

Subclass with `score(option, index) -> float` to swap in a real
scorer without changing the selection logic.
"""

from __future__ import annotations

from agents.base import Agent


class HeuristicAgent(Agent):
    """First-`maxCount` deterministic selector."""

    def score(self, option: object, index: int) -> float:
        """Score one option. Default: prefer earlier indices."""
        return -float(index)

    def choose(self, obs: dict) -> list[int]:
        options = obs["select"]["option"]
        max_count = obs["select"]["maxCount"]
        ranked = sorted(
            range(len(options)),
            key=lambda i: (-self.score(options[i], i), i),
        )
        return ranked[:max_count]
