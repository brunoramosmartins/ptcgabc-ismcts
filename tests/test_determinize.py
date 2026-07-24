"""Tests for search/determinize.py (pure accounting logic).

The synthetic observations below mimic the engine's shapes: card dicts
carry ``id`` + ``playerIndex``; face-down cards have no integer id.
"""

from __future__ import annotations

import itertools
import random
from collections import Counter

import pytest

from search.determinize import (
    DeterminizationError,
    sample_determinization,
    visible_cards,
)

ME, OPP = 0, 1
_serials = itertools.count(1)


def _card(cid: int, owner: int) -> dict:
    return {"id": cid, "serial": next(_serials), "playerIndex": owner}


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


def test_context_card_in_select_is_swept() -> None:
    # A Trainer being resolved lives in select.contextCard — in no
    # board zone. Missing it made the hidden pool one card too large
    # (the off-by-one the EXP-003 pilot exposed).
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=2, my_prize_count=1,
        opp_discard=[], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    obs["select"] = {"contextCard": _card(99, ME), "option": []}
    mine, _ = visible_cards(obs)
    assert mine[99] == 1

    # And the pool accounting closes with the limbo card excluded:
    my_list = [1, 10, 99, 20, 21, 22]      # visible: 1, 10, 99 → pool 3
    opp_list = [50, 30, 31, 32, 33]
    det = sample_determinization(obs, my_list, opp_list, random.Random(4))
    assert sorted(det["my_deck"] + det["my_prize"]) == [20, 21, 22]


def test_same_serial_counted_once_across_current_and_select() -> None:
    # The same physical card can appear on the board AND as a
    # reference inside select (e.g. an ability's source). Serial
    # dedupe must count it once, or the pool comes up short.
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=2, my_prize_count=1,
        opp_discard=[], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    active_card = obs["current"]["players"][ME]["active"][0]
    obs["select"] = {"contextCard": dict(active_card), "option": []}
    mine, _ = visible_cards(obs)
    assert mine[active_card["id"]] == 1   # not 2


def test_select_deck_is_not_swept() -> None:
    # Cards shown by a deck-search effect (select.deck) are still
    # counted in deckCount; sweeping them double-counts the deck
    # (pilot v2 signature: "pool has 6, visible=54").
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=3, my_prize_count=1,
        opp_discard=[], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    obs["select"] = {
        "contextCard": None,
        "deck": [_card(20, ME), _card(21, ME), _card(22, ME)],
        "option": [],
    }
    mine, _ = visible_cards(obs)
    assert 20 not in mine and 21 not in mine and 22 not in mine

    my_list = [10, 20, 21, 22, 3]          # visible: active(10) only
    opp_list = [50, 30, 31, 32, 33]
    det = sample_determinization(obs, my_list, opp_list, random.Random(6))
    # deck-browse cards stay in the hidden pool (they ARE the deck)
    assert len(det["my_deck"]) == 3
    assert len(det["my_prize"]) == 1
    assert sorted(det["my_deck"] + det["my_prize"]) == [3, 20, 21, 22]


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
    det = sample_determinization(obs, my_list, opp_list, random.Random(3),
                                 basic_ids={40, 41, 42, 43})
    assert len(det["enemy_active"]) == 1
    assert sorted(det["enemy_deck"] + det["enemy_prize"]
                  + det["enemy_hand"] + det["enemy_active"]) == [40, 41, 42, 43]


def test_hidden_active_must_be_a_basic() -> None:
    # Only card 43 is a Basic — the unrevealed active must be it,
    # regardless of the RNG (an Energy in the active slot is the
    # invalid state behind SearchBegin error 2).
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=1,
        opp_active_hidden=True,
    )
    my_list = [10, 3, 3]
    opp_list = [40, 41, 42, 43]
    for seed in range(5):
        det = sample_determinization(obs, my_list, opp_list,
                                     random.Random(seed), basic_ids={43})
        assert det["enemy_active"] == [43]


def test_no_basic_available_for_hidden_active_raises() -> None:
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=1,
        opp_active_hidden=True,
    )
    with pytest.raises(DeterminizationError, match="Basic"):
        sample_determinization(obs, [10, 3, 3], [40, 41, 42, 43],
                               random.Random(1), basic_ids={999})


def test_pool_slack_tolerates_one_limbo_card() -> None:
    # Pool has need+1 candidates (e.g. our face-down setup active or a
    # Trainer mid-resolution is unidentifiable). Sampling must succeed
    # and use only pool cards.
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=2, my_prize_count=1,
        opp_discard=[], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    my_list = [1, 10, 20, 21, 22, 23]      # pool {20,21,22,23}, need 3
    opp_list = [50, 30, 31, 32, 33]        # pool exactly 4 = need
    det = sample_determinization(obs, my_list, opp_list, random.Random(2))
    mine = det["my_deck"] + det["my_prize"]
    assert len(mine) == 3
    assert set(mine) <= {20, 21, 22, 23}


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


def test_accounting_mismatch_beyond_slack_raises() -> None:
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=10, my_prize_count=6,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=1,
    )
    my_list = _deck_for([1, 10], 3)        # pool of 3, engine needs 16
    with pytest.raises(DeterminizationError, match="my side"):
        sample_determinization(obs, my_list, _deck_for([50], 3),
                               random.Random(1))


def test_pool_excess_beyond_slack_raises() -> None:
    # need+3 exceeds POOL_SLACK — a systematic sweep bug must still
    # fail loud instead of silently sampling.
    obs = _obs(
        my_hand=[1], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=0,
    )
    my_list = [1, 10, 20, 21, 22, 23, 24]  # pool of 5, need 2, excess 3
    with pytest.raises(DeterminizationError, match="slack"):
        sample_determinization(obs, my_list, [50, 3, 3], random.Random(1))


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


# --- assumed opponent list (EXP-010, `ismcts-selfdeck` condition) --------


def test_assumed_list_tolerates_foreign_visible_cards() -> None:
    # The opponent's active (50) and discard (7) are NOT in the assumed
    # list. Strict mode raises on the first revealed foreign card —
    # which is every non-mirror game on the ladder; assumed mode must
    # sample from the guess instead.
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[7], opp_deck_count=2, opp_prize_count=1, opp_hand_count=1,
    )
    assumed = [30, 31, 32, 33]             # need 4 hidden, none visible
    det = sample_determinization(
        obs, [10, 3, 3], assumed, random.Random(1),
        opponent_list_is_assumed=True,
    )
    hidden = det["enemy_deck"] + det["enemy_prize"] + det["enemy_hand"]
    assert sorted(hidden) == [30, 31, 32, 33]


def test_assumed_list_subtracts_overlapping_visible_copies() -> None:
    # Where the guess overlaps reality, the constraint still binds: the
    # single copy of 7 in the assumed list is in the discard, so no
    # sampled world may hold a second one.
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[7], opp_deck_count=2, opp_prize_count=1, opp_hand_count=0,
    )
    assumed = [7, 30, 31, 32]              # 7 visible; need 3 hidden
    det = sample_determinization(
        obs, [10, 3, 3], assumed, random.Random(1),
        opponent_list_is_assumed=True,
    )
    hidden = det["enemy_deck"] + det["enemy_prize"] + det["enemy_hand"]
    assert sorted(hidden) == [30, 31, 32]


def test_assumed_list_tolerates_pool_excess_beyond_slack() -> None:
    # Foreign visible cards subtract nothing, so the assumed pool is
    # oversized in every real game — far beyond POOL_SLACK. The strict
    # excess check must not apply on the assumed side.
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=0,
    )
    assumed = [30 + i for i in range(10)]  # pool 10, need 2, excess 8
    det = sample_determinization(
        obs, [10, 3, 3], assumed, random.Random(1),
        opponent_list_is_assumed=True,
    )
    assert len(det["enemy_deck"]) == 1
    assert len(det["enemy_prize"]) == 1
    assert set(det["enemy_deck"] + det["enemy_prize"]) <= set(assumed)


def test_assumed_list_hidden_active_is_still_a_basic() -> None:
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[7], opp_deck_count=1, opp_prize_count=1, opp_hand_count=1,
        opp_active_hidden=True,
    )
    for seed in range(5):
        det = sample_determinization(
            obs, [10, 3, 3], [40, 41, 42, 43], random.Random(seed),
            basic_ids={43}, opponent_list_is_assumed=True,
        )
        assert det["enemy_active"] == [43]


def test_assumed_pool_shortage_raises() -> None:
    # Oversize is expected; undershoot is not — a guess that cannot even
    # populate the board must fail loud, not sample a partial world.
    obs = _obs(
        my_hand=[], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=3, opp_prize_count=2, opp_hand_count=2,
    )
    with pytest.raises(DeterminizationError, match="assumed"):
        sample_determinization(
            obs, [10, 3, 3], [30, 31], random.Random(1),
            opponent_list_is_assumed=True,
        )


def test_assumed_mode_keeps_our_side_strict() -> None:
    # The relaxation is opponent-side only: our own accounting is
    # ground truth and a mismatch there is still a bug, not a guess.
    obs = _obs(
        my_hand=[99], my_discard=[], my_deck_count=1, my_prize_count=1,
        opp_discard=[], opp_deck_count=1, opp_prize_count=1, opp_hand_count=0,
    )
    with pytest.raises(DeterminizationError, match="not in the deck list"):
        sample_determinization(
            obs, [10, 3, 3], [30, 31, 32], random.Random(1),
            opponent_list_is_assumed=True,
        )
