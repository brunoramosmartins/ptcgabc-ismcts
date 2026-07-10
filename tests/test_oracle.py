"""Tests for search/oracle.py — the ground-truth extractor.

Synthetic visualize_data payloads mirror the probed shape: a list of
per-decision snapshots whose `current.players[i]` carry full `deck`,
`prize`, and `hand` arrays with card ids.
"""

from __future__ import annotations

import pytest

from search.oracle import OracleError, true_determinization


def _card(cid: int, owner: int) -> dict:
    return {"id": cid, "serial": cid * 10 + owner, "playerIndex": owner}


def _obs(me: int, my_deck: int, my_prize: int, opp_deck: int,
         opp_prize: int, opp_hand: int, opp_active_hidden: bool = False) -> dict:
    players = [
        {"deckCount": 0, "prize": [], "handCount": 0, "active": []},
        {"deckCount": 0, "prize": [], "handCount": 0, "active": []},
    ]
    players[me] = {"deckCount": my_deck, "prize": [{}] * my_prize,
                   "handCount": 3, "active": [_card(10, me)]}
    players[1 - me] = {
        "deckCount": opp_deck, "prize": [{}] * opp_prize,
        "handCount": opp_hand,
        "active": [None] if opp_active_hidden else [_card(50, 1 - me)],
    }
    return {"current": {"yourIndex": me, "players": players}}


def _vis(me: int, my_deck: list[int], my_prize: list[int],
         opp_deck: list[int], opp_prize: list[int], opp_hand: list[int],
         opp_active: list[int]) -> list:
    players = [{}, {}]
    players[me] = {
        "deck": [_card(c, me) for c in my_deck],
        "prize": [_card(c, me) for c in my_prize],
        "hand": [_card(9, me)] * 3,
        "active": [_card(10, me)],
    }
    players[1 - me] = {
        "deck": [_card(c, 1 - me) for c in opp_deck],
        "prize": [_card(c, 1 - me) for c in opp_prize],
        "hand": [_card(c, 1 - me) for c in opp_hand],
        "active": [_card(c, 1 - me) for c in opp_active],
    }
    return [{"current": {"players": players}}]


def test_extracts_true_assignment_in_order() -> None:
    obs = _obs(me=0, my_deck=3, my_prize=2, opp_deck=2, opp_prize=1,
               opp_hand=2)
    vis = _vis(me=0, my_deck=[21, 22, 23], my_prize=[31, 32],
               opp_deck=[41, 42], opp_prize=[43], opp_hand=[44, 45],
               opp_active=[50])
    det = true_determinization(obs, vis)
    assert det["my_deck"] == [21, 22, 23]      # order preserved
    assert det["my_prize"] == [31, 32]
    assert det["enemy_deck"] == [41, 42]
    assert det["enemy_prize"] == [43]
    assert det["enemy_hand"] == [44, 45]
    assert det["enemy_active"] == []           # active visible in obs


def test_hidden_opponent_active_comes_from_truth() -> None:
    obs = _obs(me=1, my_deck=1, my_prize=1, opp_deck=1, opp_prize=1,
               opp_hand=1, opp_active_hidden=True)
    vis = _vis(me=1, my_deck=[21], my_prize=[31], opp_deck=[41],
               opp_prize=[43], opp_hand=[44], opp_active=[77])
    det = true_determinization(obs, vis)
    assert det["enemy_active"] == [77]


def test_uses_last_snapshot() -> None:
    obs = _obs(me=0, my_deck=1, my_prize=0, opp_deck=1, opp_prize=0,
               opp_hand=0)
    stale = _vis(me=0, my_deck=[99, 98], my_prize=[], opp_deck=[97],
                 opp_prize=[], opp_hand=[], opp_active=[50])[0]
    fresh = _vis(me=0, my_deck=[21], my_prize=[], opp_deck=[41],
                 opp_prize=[], opp_hand=[], opp_active=[50])[0]
    det = true_determinization(obs, [stale, fresh])
    assert det["my_deck"] == [21]


def test_size_mismatch_fails_loud() -> None:
    obs = _obs(me=0, my_deck=5, my_prize=2, opp_deck=2, opp_prize=1,
               opp_hand=2)
    vis = _vis(me=0, my_deck=[21], my_prize=[31, 32],   # deck 1 != 5
               opp_deck=[41, 42], opp_prize=[43], opp_hand=[44, 45],
               opp_active=[50])
    with pytest.raises(OracleError, match="sizes"):
        true_determinization(obs, vis)


def test_bad_payload_fails_loud() -> None:
    obs = _obs(me=0, my_deck=1, my_prize=0, opp_deck=1, opp_prize=0,
               opp_hand=0)
    with pytest.raises(OracleError):
        true_determinization(obs, "not json {{")
    with pytest.raises(OracleError):
        true_determinization(obs, [])
