"""SO-ISMCTS four-phase loop over the engine's native search API.

One decision = many iterations of:

1. **Determinize** — sample a hidden world consistent with the root
   observation (`search/determinize.py`), reconstruct it in the engine
   (`env/search_engine.search_begin`).
2. **Select** — descend the information-set tree with subset-armed
   UCB1 (`search/ucb.py`), applying each selected move to the engine
   via `search_step`. Only moves legal in *this* determinization
   participate; availability counts stay in sync via
   ``mark_available``.
3. **Expand + Rollout** — on reaching a node with unvisited available
   moves, expand one (uniformly at random) and play uniformly random
   moves to the terminal state.
4. **Backpropagate** — terminal reward from the root player's
   perspective ($+1$ win, $-1$ loss, $0$ draw, per ADR-004) updates
   every node on the path.

Design notes:

- **Move keys.** A "move" is a list of option indices (the engine's
  `select` contract). Indices are positional and unstable across
  determinizations, so tree edges are keyed by the canonical JSON of
  the option *contents*. Known limitation: options that reference
  hidden zones positionally (e.g. deck picks under a search effect)
  may alias across determinizations; acceptable for the Phase 3
  baseline, revisit if EXP results suggest collisions matter.
- **Combination cap.** When ``maxCount > 1`` the move space is
  combinatorial; we enumerate index-combinations of size ``maxCount``
  capped at ``MAX_MOVES`` (64, matching the public notebook's
  convention). ``minCount == maxCount`` in the vast majority of
  engine decisions.
- **Opponent nodes.** SO-ISMCTS keeps one tree from the root player's
  perspective. At nodes where the opponent acts, selection *minimizes*
  the root player's value (the exploitation term flips sign).
- **Memory.** Each iteration replays its path on a fresh
  determinization (information-set tree, determinized states), so no
  engine search-state is cached across iterations; ``search_end()``
  recycles everything when the decision returns.
"""

from __future__ import annotations

import json
import random
from itertools import combinations, islice

from env import search_engine
from search.determinize import sample_determinization
from search.node import InfoSetNode
from search.ucb import DEFAULT_C, ucb1_score

MAX_MOVES = 64
RESULT_IN_PROGRESS = -1
RESULT_DRAW = 2

MoveKey = tuple[str, ...]


def enumerate_moves(select: dict) -> list[tuple[MoveKey, list[int]]]:
    """Legal moves of a selection, as (canonical key, indices) pairs.

    Enumerates index-combinations of size ``maxCount`` (the engine's
    dominant case is ``minCount == maxCount``), capped at
    ``MAX_MOVES``. Keys are canonical JSONs of the chosen options'
    contents, order-normalized, so the same semantic move maps to the
    same tree edge across determinizations.
    """
    options = select["option"]
    # Some card effects ("search for up to N ...") emit selects whose
    # maxCount exceeds the options actually present; picking everything
    # available is the only legal move then.
    k = min(select["maxCount"], len(options))
    moves: list[tuple[MoveKey, list[int]]] = []
    for combo in islice(combinations(range(len(options)), k), MAX_MOVES):
        key = tuple(sorted(
            json.dumps(options[i], sort_keys=True) for i in combo
        ))
        moves.append((key, list(combo)))
    return moves


def _terminal_reward(result: int, root_index: int) -> float:
    if result == RESULT_DRAW:
        return 0.0
    return 1.0 if result == root_index else -1.0


def _rollout(state: dict, rng: random.Random, cap: int = 3000) -> int:
    """Uniform-random rollout to terminal; returns the result code."""
    sid, obs = state["search_id"], state["observation"]
    for _ in range(cap):
        cur = obs["current"]
        if cur["result"] != RESULT_IN_PROGRESS:
            return cur["result"]
        sel = obs["select"]
        n = len(sel["option"])
        choice = rng.sample(range(n), min(sel["maxCount"], n))
        nxt = search_engine.search_step(sid, choice)
        sid, obs = nxt["search_id"], nxt["observation"]
    return RESULT_DRAW  # cap hit — treat as draw, per ADR-004 timeout rule


def _select_move(
    node: InfoSetNode,
    available: list[tuple[MoveKey, list[int]]],
    maximize: bool,
    c: float,
) -> tuple[MoveKey, list[int]]:
    """Subset-armed UCB1 over the available moves; sign flips at
    opponent nodes so their choices minimize the root's value."""
    best, best_score = None, float("-inf")
    for key, indices in available:
        child = node.children[key]
        signed_total = child.total_reward if maximize else -child.total_reward
        score = ucb1_score(signed_total, child.visits, child.availability, c)
        if score > best_score:
            best_score = score
            best = (key, indices)
    assert best is not None
    return best


def _run_iteration(
    root: InfoSetNode,
    obs: dict,
    det: dict,
    root_index: int,
    c: float,
    rng: random.Random,
    rollout=None,
) -> None:
    """One MCTS iteration on `root` in the determinized world `det`.

    Reconstructs the world with `search_begin`, descends `root` with
    subset-armed UCB1 selecting only moves legal in this
    determinization, expands one unvisited move and rolls out, then
    backpropagates the terminal reward. Shared by the ISMCTS (one
    shared root, fresh `det` per call) and PIMC (one root per
    determinization) drivers.

    `rollout` is a callable ``(state, rng) -> result code``; defaults
    to the uniform-random `_rollout` (ADR-001 baseline). The guided
    policy from `evaluator/rollout.py` plugs in here (H2 arm).
    """
    if rollout is None:
        rollout = _rollout
    state = search_engine.search_begin(obs, **det)
    node, path = root, [root]
    while True:
        cur = state["observation"]["current"]
        if cur["result"] != RESULT_IN_PROGRESS:
            reward = _terminal_reward(cur["result"], root_index)
            break
        available = enumerate_moves(state["observation"]["select"])
        node.mark_available(key for key, _ in available)
        unvisited = node.unvisited_available(key for key, _ in available)
        if unvisited:
            key = rng.choice(unvisited)
            indices = next(i for k, i in available if k == key)
            state = search_engine.search_step(state["search_id"], indices)
            child = node.children[key]
            path.append(child)
            result = rollout(state, rng)
            reward = _terminal_reward(result, root_index)
            break
        maximize = cur["yourIndex"] == root_index
        key, indices = _select_move(node, available, maximize, c)
        state = search_engine.search_step(state["search_id"], indices)
        node = node.children[key]
        path.append(node)
    for visited in path:
        visited.update(reward)


def _map_key_to_indices(
    best_key: MoveKey, root_moves: list[tuple[MoveKey, list[int]]]
) -> list[int]:
    for key, indices in root_moves:
        if key == best_key:
            return indices
    # The best edge should always exist among the real observation's
    # moves (our own options don't depend on hidden state at the root).
    raise RuntimeError("best root move not found in real observation")


def decide(
    obs: dict,
    my_deck_list: list[int],
    opponent_deck_list: list[int] | None,
    rng: random.Random,
    iterations: int = 1000,
    c: float = DEFAULT_C,
    filler_card: int | None = None,
    rollout_policy=None,
) -> list[int]:
    """Run SO-ISMCTS for one decision; return option indices to play.

    One shared information-set tree; each iteration re-samples a fresh
    determinization, so statistics from every sampled world accumulate
    in the same nodes (Cowling's key idea). Root action = max visit
    count.

    Args:
        obs: The real observation (with ``search_begin_input``).
        my_deck_list: Our 60-card list.
        opponent_deck_list: Theirs when known (local matches).
        rng: Seeded RNG.
        iterations: Simulations for this decision.
        c: UCB1 exploration constant.
        filler_card: Fallback for unknown opponent lists (ladder).
        rollout_policy: ``(state, rng) -> result``; None = uniform
            random (ADR-001 baseline). Guided policy = H2 arm.

    Returns:
        Option indices for the real observation's option array.
    """
    root_index = obs["current"]["yourIndex"]
    root = InfoSetNode()
    root_moves = enumerate_moves(obs["select"])

    for _ in range(iterations):
        det = sample_determinization(
            obs, my_deck_list, opponent_deck_list, rng, filler_card
        )
        _run_iteration(root, obs, det, root_index, c, rng,
                       rollout=rollout_policy)

    search_engine.search_end()
    return _map_key_to_indices(root.best_action_by_visits(), root_moves)
