"""PIMC (Perfect-Information Monte Carlo / Determinized UCT) baseline.

The diagnostic-ladder arm that isolates Cowling's contribution. Where
SO-ISMCTS keeps ONE information-set tree and re-samples a determinization
every iteration (so all worlds share statistics), PIMC fixes ``K``
determinizations up front, runs an INDEPENDENT UCT on each with its own
tree, and picks the action by pooling root visit counts across the ``K``
trees (visit-count voting). No sharing between worlds — this is exactly
the "strategy fusion" regime the ISMCTS paper argues against.

Reads in the diagnostic decomposition (see `notes/phase2-synthesis.md`
experimental ladder):

    W_ISMCTS − W_PIMC  =  value of the shared info-set tree, in PTCG.

If this delta is ≈ 0, Cowling's mechanism buys us little here (the
Dou Di Zhu regime); if large, the shared tree is doing real work.

Everything below reuses `search.ismcts` internals — only the driver
loop differs (K trees, fixed determinization per tree, vote).
"""

from __future__ import annotations

import random
from collections import Counter

from search.determinize import sample_determinization
from search.ismcts import (
    _map_key_to_indices,
    _run_iteration,
    enumerate_moves,
)
from search.node import InfoSetNode
from search.ucb import DEFAULT_C
from env import search_engine

DEFAULT_K = 10


def decide_pimc(
    obs: dict,
    my_deck_list: list[int],
    opponent_deck_list: list[int] | None,
    rng: random.Random,
    iterations: int = 1000,
    k: int = DEFAULT_K,
    c: float = DEFAULT_C,
    filler_card: int | None = None,
) -> list[int]:
    """Run Determinized UCT for one decision; return option indices.

    Args:
        obs: The real observation (with ``search_begin_input``).
        my_deck_list: Our 60-card list.
        opponent_deck_list: Theirs when known (local matches).
        rng: Seeded RNG.
        iterations: Total simulations, split evenly across the ``k``
            trees (``iterations // k`` each) so the total search budget
            matches the ISMCTS arm exactly.
        k: Number of independent determinizations / trees.
        c: UCB1 exploration constant.
        filler_card: Fallback for unknown opponent lists (ladder).

    Returns:
        Option indices chosen by pooled root visit count across trees.
    """
    root_index = obs["current"]["yourIndex"]
    root_moves = enumerate_moves(obs["select"])
    iters_per_tree = max(1, iterations // k)

    vote: Counter = Counter()
    for _ in range(k):
        det = sample_determinization(
            obs, my_deck_list, opponent_deck_list, rng, filler_card
        )
        root_k = InfoSetNode()
        for _ in range(iters_per_tree):
            # Fixed determinization for this whole tree — that is the
            # PIMC distinction from ISMCTS. Rollouts still vary (engine
            # stochasticity beyond the pinned hidden state).
            _run_iteration(root_k, obs, det, root_index, c, rng)
        for key, child in root_k.children.items():
            vote[key] += child.visits

    search_engine.search_end()

    if not vote:
        raise RuntimeError("PIMC explored no moves")
    best_key = max(vote, key=lambda kk: vote[kk])
    return _map_key_to_indices(best_key, root_moves)
