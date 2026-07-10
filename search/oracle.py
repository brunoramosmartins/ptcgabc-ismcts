"""Cheating-UCT oracle (EXP-005) — LOCAL DIAGNOSTIC ONLY, never submitted.

The oracle plays with the TRUE hidden state instead of a sampled
determinization. `W_cheat − W_ISMCTS = Δ_ceiling` is the cost of
imperfect information and the headroom available to belief-based ideas
(`notes/open-ideas.md`). Feeding the truth into the perfect-information
UCT collapses the info-set tree into a plain game tree — same
`_run_iteration` engine, one fixed world.

Ground truth source (probe 2026-07-09): `visualize_data()` — the
renderer payload — exposes both players' full ordered decks, prizes,
and hands with card ids, one snapshot per decision. The engine appends
a snapshot at each `GetBattleData`, so the LAST entry corresponds to
the current decision.

Compliance: this agent reads omniscient data and violates competition
rules if ever submitted. `scripts/submit.py` refuses any bundle whose
main mentions "oracle".
"""

from __future__ import annotations

import json
import random
from typing import Any

from env import search_engine
from env.search_engine import expected_counts
from search.ismcts import _map_key_to_indices, _run_iteration, enumerate_moves
from search.node import InfoSetNode
from search.ucb import DEFAULT_C


class OracleError(RuntimeError):
    """Raised when the ground truth cannot be extracted or doesn't
    match the sizes the engine will demand."""


def _ids(cards: list | None) -> list[int]:
    out = []
    for c in cards or []:
        cid = c.get("id") if isinstance(c, dict) else None
        if not isinstance(cid, int):
            raise OracleError(f"card without integer id in truth: {c!r}")
        out.append(cid)
    return out


def true_determinization(obs: dict, vis_payload: str | list) -> dict[str, list[int]]:
    """Extract the true hidden assignment for the CURRENT decision.

    Args:
        obs: The acting player's normal observation (sizes come from
            here via `expected_counts` — the engine reconstructs the
            state from the obs blob and reads array lengths from it).
        vis_payload: `visualize_data()` output — JSON string or the
            already-parsed list of per-decision snapshots.

    Returns:
        Keyword arguments for `search_begin`, containing the TRUE
        deck orders, prizes, opponent hand, and (when hidden in obs)
        the opponent's active.

    Raises:
        OracleError: On parse failure or any size mismatch with what
            the engine expects — fail loud, never silently degrade to
            a partial oracle.
    """
    if isinstance(vis_payload, str):
        try:
            vis = json.loads(vis_payload)
        except json.JSONDecodeError as exc:
            raise OracleError(f"visualize_data is not JSON: {exc}") from exc
    else:
        vis = vis_payload
    if not isinstance(vis, list) or not vis:
        raise OracleError("visualize_data payload empty or not a list")

    snap = vis[-1]  # snapshot appended at the current GetBattleData
    players: list[dict[str, Any]] = snap["current"]["players"]
    me = obs["current"]["yourIndex"]
    mine, theirs = players[me], players[1 - me]

    want = expected_counts(obs)
    det = {
        "my_deck": _ids(mine.get("deck")),
        "my_prize": _ids(mine.get("prize")),
        "enemy_deck": _ids(theirs.get("deck")),
        "enemy_prize": _ids(theirs.get("prize")),
        "enemy_hand": _ids(theirs.get("hand")),
        "enemy_active": (_ids(theirs.get("active"))
                         if want["enemy_active"] > 0 else []),
    }
    got = {k: len(v) for k, v in det.items()}
    need = {"my_deck": want["my_deck"], "my_prize": want["my_prize"],
            "enemy_deck": want["enemy_deck"],
            "enemy_prize": want["enemy_prize"],
            "enemy_hand": want["enemy_hand"],
            "enemy_active": want["enemy_active"]}
    if got != need:
        raise OracleError(
            f"truth sizes {got} != engine expectation {need} "
            f"(vis snapshot may be out of sync with the obs)"
        )
    return det


def fetch_vis_payload() -> str:
    """Read the renderer payload from the engine's current battle.

    Local-only: relies on the `Battle.battle_ptr` global that the cabt
    interpreter maintains during `env.run`.
    """
    from kaggle_environments.envs.cabt.cg import game
    return game.visualize_data()


def decide_oracle(
    obs: dict,
    rng: random.Random,
    iterations: int = 1000,
    c: float = DEFAULT_C,
    truth: dict[str, list[int]] | None = None,
) -> list[int]:
    """Plain UCT on the true world; return option indices to play.

    Args:
        obs: The real observation for this decision.
        rng: Seeded RNG (rollout randomness only — the world is fixed).
        iterations: Simulations for this decision.
        c: UCB1 exploration constant.
        truth: The true hidden assignment; fetched from the visualizer
            when None (injectable for tests).

    Returns:
        Option indices, chosen by max root visit count.
    """
    if truth is None:
        truth = true_determinization(obs, fetch_vis_payload())
    root_index = obs["current"]["yourIndex"]
    root = InfoSetNode()
    root_moves = enumerate_moves(obs["select"])

    for _ in range(iterations):
        _run_iteration(root, obs, truth, root_index, c, rng)

    search_engine.search_end()
    return _map_key_to_indices(root.best_action_by_visits(), root_moves)
