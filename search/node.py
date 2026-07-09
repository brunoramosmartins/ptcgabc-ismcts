"""Information-set tree node for SO-ISMCTS.

Nodes represent information sets from the root player's perspective
(Cowling, Powley & Whitehouse 2012 — see
`notes/phase2-ismcts-paper-notes.md` §3.1). Three statistics per child,
following the subset-armed bandit formulation:

- ``visits``  ($n_a$) — how many simulations selected this action.
- ``total_reward`` ($w_a$) — cumulative terminal reward backed up
  through this action (terminal-only $r_T \\in \\{-1, 0, +1\\}$,
  per ADR-004).
- ``availability`` ($m_a$) — how many simulations *could have*
  selected this action, i.e. the action was legal in the sampled
  determinization when the parent was visited. This replaces the
  parent visit count in the UCB1 exploration term (see `search/ucb.py`)
  so that actions legal in few determinizations are not spuriously
  under-explored.

Children are keyed by an opaque hashable ``ActionKey``. The agent layer
decides the keying; positional indices into `obs["select"]["option"]`
are NOT stable across determinizations, so callers should key by a
canonical representation of the option content, not by index.
"""

from __future__ import annotations

from typing import Hashable, Iterable

ActionKey = Hashable


class InfoSetNode:
    """One information-set node; also carries the edge statistics
    for the action that led here from the parent."""

    __slots__ = ("visits", "total_reward", "availability", "children")

    def __init__(self) -> None:
        self.visits: int = 0
        self.total_reward: float = 0.0
        self.availability: int = 0
        self.children: dict[ActionKey, InfoSetNode] = {}

    def q(self) -> float:
        """Mean backed-up reward; 0.0 for an unvisited node."""
        if self.visits == 0:
            return 0.0
        return self.total_reward / self.visits

    def ensure_child(self, key: ActionKey) -> InfoSetNode:
        """Return the child for `key`, creating it if absent."""
        child = self.children.get(key)
        if child is None:
            child = InfoSetNode()
            self.children[key] = child
        return child

    def mark_available(self, keys: Iterable[ActionKey]) -> None:
        """Increment availability for every action legal in the current
        determinization, creating children as needed.

        Called once per visit to this node during Selection, BEFORE the
        UCB1 comparison, so that availability counts stay in sync with
        the subset-armed bandit formulation.
        """
        for key in keys:
            self.ensure_child(key).availability += 1

    def update(self, reward: float) -> None:
        """Backpropagation step: add one simulation outcome."""
        self.visits += 1
        self.total_reward += reward

    def unvisited_available(self, keys: Iterable[ActionKey]) -> list[ActionKey]:
        """Actions legal in the current determinization with zero visits.

        Expansion picks from these (expand-one-per-iteration, per
        Browne's default policy — `notes/phase2-mcts-fundamentals.md`
        §2.2).
        """
        out = []
        for key in keys:
            child = self.children.get(key)
            if child is None or child.visits == 0:
                out.append(key)
        return out

    def best_action_by_visits(self) -> ActionKey:
        """Final action selection at the root: max visit count
        (Cowling's recommendation), ties broken arbitrarily.

        Raises:
            ValueError: if the node has no children.
        """
        if not self.children:
            raise ValueError("best_action_by_visits on a node with no children")
        return max(self.children.items(), key=lambda kv: kv[1].visits)[0]
