"""Tests for evaluator/heuristic.py and evaluator/rollout.py."""

from __future__ import annotations

import random

import pytest

import evaluator.rollout as rollout_mod
from evaluator import option_types as ot
from evaluator.heuristic import FEATURES, MoveScorer
from evaluator.rollout import make_guided_rollout

BASIC = 721


def _obs(energy_attached: bool = False, bench_n: int = 0,
         hand_ids: list[int] | None = None) -> dict:
    hand = [{"id": c, "serial": i, "playerIndex": 0}
            for i, c in enumerate(hand_ids or [])]
    return {
        "current": {
            "yourIndex": 0,
            "energyAttached": energy_attached,
            "players": [
                {"bench": [{}] * bench_n, "hand": hand},
                {"bench": [], "hand": []},
            ],
        },
    }


# --- individual rules --------------------------------------------------------

def test_f1_prefers_attack_via_attack_id() -> None:
    s = MoveScorer()
    assert s.score({"type": 99, "attackId": 5}, _obs()) > 0
    assert s.score({"type": ot.ATTACK}, _obs()) > 0


def test_f2_attach_only_before_energy_this_turn() -> None:
    s = MoveScorer()
    opt = {"type": ot.ATTACH, "area": 2, "index": 1}
    assert s.score(opt, _obs(energy_attached=False)) > 0
    assert s.score(opt, _obs(energy_attached=True)) == 0


def test_f3_prefers_evolve() -> None:
    assert MoveScorer().score({"type": ot.EVOLVE}, _obs()) > 0


def test_f4_play_basic_only_when_bench_thin() -> None:
    s = MoveScorer(basic_ids={BASIC})
    play_basic = {"type": ot.PLAY, "index": 0}
    obs_thin = _obs(bench_n=1, hand_ids=[BASIC])
    obs_full = _obs(bench_n=3, hand_ids=[BASIC])
    assert s.score(play_basic, obs_thin) > 0
    assert s.score(play_basic, obs_full) == 0
    # playing a non-Basic scores nothing even with a thin bench
    obs_trainer = _obs(bench_n=0, hand_ids=[1145])
    assert s.score({"type": ot.PLAY, "index": 0}, obs_trainer) == 0


def test_f5_end_penalized_only_when_value_available() -> None:
    s = MoveScorer()
    end = {"type": ot.END}
    attack = {"type": ot.ATTACK, "attackId": 1}
    scores = s.score_all([attack, end], _obs())
    assert scores[0] > 0 and scores[1] < 0
    # END alone (nothing better) is not penalized
    assert s.score_all([end], _obs()) == [0.0]


def test_f6_penalizes_retreat() -> None:
    assert MoveScorer().score({"type": ot.RETREAT}, _obs()) < 0


# --- ablation (the H4 knob) --------------------------------------------------

def test_disabling_a_feature_removes_its_effect() -> None:
    s = MoveScorer(disabled={"F1"})
    assert s.score({"type": ot.ATTACK, "attackId": 1}, _obs()) == 0


def test_every_feature_is_individually_disablable() -> None:
    for f in FEATURES:
        MoveScorer(disabled={f})  # must not raise


def test_unknown_feature_rejected() -> None:
    with pytest.raises(ValueError, match="unknown"):
        MoveScorer(disabled={"F9"})


# --- guided rollout on a fake engine ----------------------------------------

class FakeEngine:
    """Depth-1: picking the ATTACK option wins (result 0), END loses."""

    def search_step(self, search_id, select):
        result = 0 if select == [0] else 1
        return {
            "search_id": search_id + 1,
            "observation": {
                "select": None,
                "current": {"yourIndex": 0, "result": result, "players": []},
            },
        }


def _rollout_state() -> dict:
    return {
        "search_id": 1,
        "observation": {
            "select": {
                "option": [{"type": ot.ATTACK, "attackId": 1},
                           {"type": ot.END}],
                "minCount": 1, "maxCount": 1,
            },
            "current": {
                "yourIndex": 0, "result": -1, "energyAttached": False,
                "players": [{"bench": [], "hand": []},
                            {"bench": [], "hand": []}],
            },
        },
    }


def test_guided_rollout_picks_scored_move(monkeypatch) -> None:
    fake = FakeEngine()
    monkeypatch.setattr(rollout_mod.search_engine, "search_step",
                        fake.search_step)
    guided = make_guided_rollout(MoveScorer(), eps=0.0)  # pure greedy
    results = [guided(_rollout_state(), random.Random(i)) for i in range(20)]
    assert all(r == 0 for r in results)   # always attacks, always wins


def test_guided_rollout_eps_explores(monkeypatch) -> None:
    fake = FakeEngine()
    monkeypatch.setattr(rollout_mod.search_engine, "search_step",
                        fake.search_step)
    guided = make_guided_rollout(MoveScorer(), eps=1.0)  # pure random
    results = {guided(_rollout_state(), random.Random(i)) for i in range(30)}
    assert results == {0, 1}              # both moves get explored
