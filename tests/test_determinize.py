"""Tests for search/determinize.py (pure accounting logic).

The synthetic observations below mimic the engine's shapes: card dicts
carry ``id`` + ``playerIndex``; face-down cards have no integer id.
"""

from __future__ import annotations

import random
from collections import Counter

import pytest

from search.determinize import (
    DeterminizationError, sample_determinization, visible_cards,
)

ME, OPP = 0, 1


def _card(cid: int, owner: int) -> dict:
    return {"id": cid, "serial": 0, "playerIndex": owner}


def _obs(
    my_hand: list[int],
    my_discard: list[int],
    my_deck_count: int,
    my_prize_count: int,
    opp_discard: list[int],
    opp_deck_count: int,
    opp_prize_count: int,
    opp_hand_count: int,
    opp_active_hidden: bool = False,
) -> dict:
    my_prizes = [{"playerIndex": ME} for _ in range(my_prize_count)]
    opp_prizes = [{"playerIndex": OPP} for _ in range(opp_prize_count)]
    opp_active = [None] if opp_active_hidden else [_card(50, OPP)]
    return {
        "current": {
            "yourIndex": ME,
            "players": [
                {
                    "hand": [_card(c, ME) for c in my_hand],
                    "discard": [_card(c, ME) for c in my_discard],
                    "active": [_card(10, ME)],
                    "bench": [],
                    "deckCount": my_deck_count,
                    "prize": my_prizes,
                    "handCount": len(my_hand),
                },
                {
                    "hand": [],
                    "discard": [_card(c, OPP) for c in opp_discard],
                    "active": opp_active,
                    "bench": [],
                    "deckCount": opp_deck_count,
                    "prize": opp_prizes,
                    "handCount": opp_hand_count,
                },
            ],
            "stadium": [],
            "looking": None,
        },
    }


def _deck_for(visible: list[int], hidden_count: int, filler: int = 3) -> list[int]:
    return visible + [filler] * hidden_count


def test_visible_cards_partitions_by_owner() -> None:
    obs = _obs(
        my_hand=[1, 2], my_discard=[4], my_deck_count=5, my_prize_count=2,
        opp_discard=[7], opp_deck_count=6, opp_prize_count=1, opp_hand_count=3,
    )
    mine, theirs = visible_cards(obs)
    assert mine == Counter({1: 1, 2: 1, 4: 1, 10: 1})   # hand+discard+active
    assert theirs == Counter({7: 1, 50: 1})              # discard+active


def test_facedown_cards_are_skipped() -> None:
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=0,
        opp_active_hidden=True,
    )
    mine, theirs = visible_cards(obs)
    assert 10 in mine            # our active is visible
    assert theirs == Counter()   # their active is None, prizes have no id


def test_sample_sizes_match_engine_requirements() -> None:
    obs = _obs(
        my_hand=[1, 2], my_discard=[4], my_deck_count=5, my_prize_count=2,
        opp_discard=[7], opp_deck_count=6, opp_prize_count=2, opp_hand_count=3,
    )
    my_list = _deck_for([1, 2, 4, 10], hidden_count=7)      # 5 deck + 2 prize
    opp_list = _deck_for([7, 50], hidden_count=11)          # 6 + 2 + 3
    det = sample_determinization(obs, my_list, opp_list, random.Random(1))
    assert len(det["my_deck"]) == 5
    assert len(det["my_prize"]) == 2
    assert len(det["enemy_deck"]) == 6
    assert len(det["enemy_prize"]) == 2
    assert len(det["enemy_hand"]) == 3
    assert det["enemy_active"] == []


def test_sampled_cards_come_only_from_hidden_pool() -> None:
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=2, my_prize_count=1,
        opp_discard=[], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    my_list = [1, 10, 20, 21, 22]          # visible: 1 (hand), 10 (active)
    opp_list = [50, 30, 31, 32, 33]        # visible: 50 (active)
    det = sample_determinization(obs, my_list, opp_list, random.Random(2))
    assert sorted(det["my_deck"] + det["my_prize"]) == [20, 21, 22]
    assert sorted(det["enemy_deck"] + det["enemy_prize"]
                  + det["enemy_hand"]) == [30, 31, 32, 33]


def test_hidden_active_is_drawn_from_opponent_pool() -> None:
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=1,
        opp_active_hidden=True,
    )
    my_list = [10, 3, 3]
    opp_list = [40, 41, 42, 43]            # nothing visible; 4 hidden slots
    det = sample_determinization(obs, my_list, opp_list, random.Random(3))
    assert len(det["enemy_active"]) == 1
    assert sorted(det["enemy_deck"] + det["enemy_prize"]
                  + det["enemy_hand"] + det["enemy_active"]) == [40, 41, 42, 43]


def test_seeded_rng_is_reproducible() -> None:
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=3, my_prize_count=2,
        opp_discard=[], opp_deck_count=3, opp_prize_count=2, opp_hand_count=1,
    )
    my_list = _deck_for([1, 10], 5)
    opp_list = _deck_for([50], 6)
    a = sample_determinization(obs, my_list, opp_list, random.Random(7))
    b = sample_determinization(obs, my_list, opp_list, random.Random(7))
    assert a == b


def test_accounting_mismatch_raises() -> None:
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=10, my_prize_count=6,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=1,
    )
    my_list = _deck_for([1, 10], 3)        # pool of 3, engine needs 16
    with pytest.raises(DeterminizationError, match="my side"):
        sample_determinization(obs, my_list, _deck_for([50], 3),
                               random.Random(1))


def test_visible_card_not_in_deck_list_raises() -> None:
    obs = _obs(
        my_hand=[99], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=0,
    )
    with pytest.raises(DeterminizationError, match="not in the deck list"):
        sample_determinization(obs, [10, 3, 3], [50, 3, 3], random.Random(1))


def test_unknown_opponent_uses_filler() -> None:
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    det = sample_determinization(obs, [10, 3, 3], None, random.Random(1),
                                 filler_card=1072)
    assert det["enemy_deck"] == [1072, 1072]
    assert det["enemy_hand"] == [1072]


def test_unknown_opponent_without_filler_raises() -> None:
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=0,
    )
    with pytest.raises(DeterminizationError, match="filler_card"):
        sample_determinization(obs, [10, 3, 3], None, random.Random(1))
