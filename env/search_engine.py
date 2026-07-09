"""ctypes bindings for the cabt engine's native search API.

The kaggle-environments pip package ships the native library but not
the Python wrappers for the search functions. This module supplies
them. Signatures are transcribed from the competition-provided engine
source (`Export.cpp`, licensed Competition-Use-Only — kept locally
under `vendor/`, never vendored into this repo); the code below is
original project code.

Native surface (from Export.cpp):

    ApiData*      AgentStart()
    const char8*  SearchBegin(ApiData*, const char* blob, int blobLen,
                              int* myDeck, int* myPrize,
                              int* enemyDeck, int* enemyPrize,
                              int* enemyHand, int* enemyActive,
                              int manualCoin)          -> JSON
    const char8*  SearchStep(ApiData*, long long searchId,
                             int* select, int selectCount) -> JSON
    void          SearchEnd(ApiData*)
    void          SearchRelease(ApiData*, long long searchId)
    const char8*  AllCard()                            -> JSON
    const char8*  AllAttack()                          -> JSON

Semantics that the wrapper enforces (also from Export.cpp):

- Search calls require the *agent* handle from ``AgentStart()``
  (apiDataType == 2); battle handles reject them with error 30.
- Array lengths are dictated by the state reconstructed from the
  ``search_begin_input`` blob: ``myDeck`` must have exactly
  ``deckCount`` entries, ``myPrize`` exactly ``len(prize)``, and the
  enemy arrays likewise. The engine reads those counts from its own
  state, so a short array is an out-of-bounds read — this wrapper
  validates lengths against the observation before calling.
- ``enemyActive`` is only consumed when the opponent's active slot is
  unrevealed (contains null); otherwise the pointer is ignored.
- ``myDeck`` is ignored during the initial deck-selection phase (we
  never search there anyway).
- All card IDs are validated against the engine's card table;
  unknown IDs make SearchBegin return an error payload (code 1).

The JSON payload returned by SearchBegin/SearchStep carries the new
observation plus the search-state id (the documented Python API wraps
it as ``SearchState{observation, searchId}``). The exact key layout is
confirmed empirically by `scripts/probe_search_api.py`; `_parse`
returns the decoded dict untouched.
"""

from __future__ import annotations

import ctypes
import json
from typing import Any

from kaggle_environments.envs.cabt.cg import sim

lib = sim.lib

_DECLARED = False
_AGENT_HANDLE: int | None = None


def _declare() -> None:
    """Attach restype/argtypes for the search API (idempotent)."""
    global _DECLARED
    if _DECLARED:
        return
    ip = ctypes.POINTER(ctypes.c_int)
    lib.AgentStart.restype = ctypes.c_void_p
    lib.AgentStart.argtypes = []
    lib.SearchBegin.restype = ctypes.c_char_p
    lib.SearchBegin.argtypes = [
        ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int,
        ip, ip, ip, ip, ip, ip, ctypes.c_int,
    ]
    lib.SearchStep.restype = ctypes.c_char_p
    lib.SearchStep.argtypes = [
        ctypes.c_void_p, ctypes.c_longlong, ip, ctypes.c_int,
    ]
    lib.SearchEnd.restype = None
    lib.SearchEnd.argtypes = [ctypes.c_void_p]
    lib.SearchRelease.restype = None
    lib.SearchRelease.argtypes = [ctypes.c_void_p, ctypes.c_longlong]
    lib.AllCard.restype = ctypes.c_char_p
    lib.AllCard.argtypes = []
    lib.AllAttack.restype = ctypes.c_char_p
    lib.AllAttack.argtypes = []
    _DECLARED = True


def agent_handle() -> int:
    """Return the process-wide search handle, creating it on first use."""
    global _AGENT_HANDLE
    _declare()
    if _AGENT_HANDLE is None:
        _AGENT_HANDLE = lib.AgentStart()
        if not _AGENT_HANDLE:
            raise RuntimeError("AgentStart() returned NULL")
    return _AGENT_HANDLE


def _int_array(ids: list[int]) -> ctypes.Array:
    return (ctypes.c_int * max(len(ids), 1))(*(ids or [0]))


def _parse(raw: bytes | None, fn: str) -> dict[str, Any]:
    if not raw:
        raise RuntimeError(f"{fn} returned NULL")
    return json.loads(raw.decode("utf-8"))


def expected_counts(obs: dict) -> dict[str, int]:
    """Determinization array lengths implied by an observation.

    Returns:
        Mapping with keys ``my_deck``, ``my_prize``, ``enemy_deck``,
        ``enemy_prize``, ``enemy_hand``, ``enemy_active`` — the exact
        lengths `search_begin` requires for each argument.
    """
    cur = obs["current"]
    me = cur["yourIndex"]
    mine, theirs = cur["players"][me], cur["players"][1 - me]
    active = theirs.get("active") or []
    active_hidden = any(a is None for a in active)
    return {
        "my_deck": mine["deckCount"],
        "my_prize": len(mine.get("prize") or []),
        "enemy_deck": theirs["deckCount"],
        "enemy_prize": len(theirs.get("prize") or []),
        "enemy_hand": theirs["handCount"],
        "enemy_active": len(active) if active_hidden else 0,
    }


def search_begin(
    obs: dict,
    my_deck: list[int],
    my_prize: list[int],
    enemy_deck: list[int],
    enemy_prize: list[int],
    enemy_hand: list[int],
    enemy_active: list[int],
    manual_coin: bool = False,
) -> dict[str, Any]:
    """Reconstruct a determinized battle from an observation.

    Args:
        obs: The observation dict as received from the engine; must
            carry a non-empty ``search_begin_input`` blob.
        my_deck: Card IDs for our own deck order (length must equal
            our ``deckCount``).
        my_prize: Card IDs for our face-down prizes.
        enemy_deck: Card IDs for the opponent's deck order.
        enemy_prize: Card IDs for the opponent's prizes.
        enemy_hand: Card IDs for the opponent's hand.
        enemy_active: Card IDs for the opponent's unrevealed active
            slot(s); pass ``[]`` when their active is face-up.
        manual_coin: When True, coin flips become externally
            controlled (chance-node hook; unused in the baseline).

    Returns:
        The decoded JSON payload (new observation + search id).

    Raises:
        ValueError: If the blob is missing or any array length does
            not match what the reconstructed state will require.
    """
    blob = obs.get("search_begin_input")
    if not blob:
        raise ValueError("observation carries no search_begin_input blob")
    want = expected_counts(obs)
    got = {
        "my_deck": len(my_deck), "my_prize": len(my_prize),
        "enemy_deck": len(enemy_deck), "enemy_prize": len(enemy_prize),
        "enemy_hand": len(enemy_hand), "enemy_active": len(enemy_active),
    }
    if got != want:
        raise ValueError(f"determinization sizes {got} != required {want}")

    data = blob.encode("ascii")
    raw = lib.SearchBegin(
        agent_handle(), data, len(data),
        _int_array(my_deck), _int_array(my_prize),
        _int_array(enemy_deck), _int_array(enemy_prize),
        _int_array(enemy_hand), _int_array(enemy_active),
        int(manual_coin),
    )
    return _parse(raw, "SearchBegin")


def search_step(search_id: int, select: list[int]) -> dict[str, Any]:
    """Advance a search state by applying one selection."""
    _declare()
    arr = (ctypes.c_int * len(select))(*select)
    raw = lib.SearchStep(agent_handle(), search_id, arr, len(select))
    return _parse(raw, "SearchStep")


def search_end() -> None:
    """End the current search; the engine recycles its memory."""
    lib.SearchEnd(agent_handle())


def search_release(search_id: int) -> None:
    """Free one specific search state."""
    lib.SearchRelease(agent_handle(), search_id)


def all_card() -> Any:
    """Card database as decoded JSON."""
    _declare()
    return _parse(lib.AllCard(), "AllCard")


def all_attack() -> Any:
    """Attack database as decoded JSON."""
    _declare()
    return _parse(lib.AllAttack(), "AllAttack")
