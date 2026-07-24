"""Tests for search/ismcts.py against a fake engine.

The fake replaces `search_begin`/`search_step`/`search_end` with a
tiny deterministic game so the four-phase loop can be verified without
the native library: two root moves, one always winning for the root
player and one always losing. ISMCTS must concentrate visits on the
winning move and return its indices.
"""

from __future__ import annotations

import random

import pytest

import search.ismcts as ismcts_mod
from search.ismcts import decide, enumerate_moves

WIN_OPT = {"type": 1, "tag": "win"}
LOSE_OPT = {"type": 1, "tag": "lose"}


def _root_obs() -> dict:
    return {
        "search_begin_input": "blob",
        "select": {"option": [WIN_OPT, LOSE_OPT], "minCount": 1, "maxCount": 1},
        "current": {
            "yourIndex": 0,
            "result": -1,
            "players": [
                {"deckCount": 0, "prize": [], "handCount": 0,
                 "active": [], "bench": [], "hand": [], "discard": []},
                {"deckCount": 0, "prize": [], "handCount": 0,
                 "active": [], "bench": [], "hand": [], "discard": []},
            ],
        },
    }


class FakeEngine:
    """Depth-1 game: picking WIN_OPT ends with result 0 (root wins),
    LOSE_OPT with result 1 (root loses)."""

    def __init__(self) -> None:
        self.begin_calls = 0
        self.end_calls = 0

    def search_begin(self, obs, **det):
        self.begin_calls += 1
        return {"search_id": 100, "observation": _root_obs()}

    def search_step(self, search_id, select):
        result = 0 if select == [0] else 1
        return {
            "search_id": search_id + 1,
            "observation": {
                "select": None,
                "current": {"yourIndex": 0, "result": result, "players": []},
            },
        }

    def search_end(self):
        self.end_calls += 1


@pytest.fixture()
def fake_engine(monkeypatch):
    fake = FakeEngine()
    monkeypatch.setattr(ismcts_mod.search_engine, "search_begin",
                        fake.search_begin)
    monkeypatch.setattr(ismcts_mod.search_engine, "search_step",
                        fake.search_step)
    monkeypatch.setattr(ismcts_mod.search_engine, "search_end",
                        fake.search_end)
    monkeypatch.setattr(ismcts_mod, "sample_determinization",
                        lambda *a, **kw: {})
    return fake


def test_decide_picks_the_winning_move(fake_engine) -> None:
    choice = decide(
        _root_obs(), my_deck_list=[], opponent_deck_list=[],
        rng=random.Random(0), iterations=40,
    )
    assert choice == [0]


def test_one_determinization_per_iteration_and_end_called(fake_engine) -> None:
    decide(_root_obs(), my_deck_list=[], opponent_deck_list=[],
           rng=random.Random(0), iterations=25)
    assert fake_engine.begin_calls == 25
    assert fake_engine.end_calls == 1


# --- anytime wall-clock cap (#27 / EXP-008) ---------------------------------

def test_max_seconds_none_runs_full_iterations(fake_engine) -> None:
    # Default path: no time cap → exactly `iterations` simulations,
    # byte-identical to pre-#27 behaviour (protects H1–H7 results).
    decide(_root_obs(), my_deck_list=[], opponent_deck_list=[],
           rng=random.Random(0), iterations=30, max_seconds=None)
    assert fake_engine.begin_calls == 30


def test_max_seconds_zero_stops_after_min_iterations(fake_engine) -> None:
    # An already-expired budget must still run `min_iterations` so the
    # root has visited children and returns a valid move.
    choice = decide(
        _root_obs(), my_deck_list=[], opponent_deck_list=[],
        rng=random.Random(0), iterations=1000,
        max_seconds=0.0, min_iterations=3,
    )
    assert fake_engine.begin_calls == 3
    assert fake_engine.end_calls == 1        # engine still cleaned up
    assert choice in ([0], [1])              # valid, if possibly weaker


def test_generous_budget_does_not_cut_iterations(fake_engine) -> None:
    # A budget far larger than the (trivial fake) work must not trigger.
    decide(_root_obs(), my_deck_list=[], opponent_deck_list=[],
           rng=random.Random(0), iterations=20,
           max_seconds=60.0, min_iterations=1)
    assert fake_engine.begin_calls == 20


# --- enumerate_moves (pure) -------------------------------------------------

def test_enumerate_moves_single_pick() -> None:
    select = {"option": [WIN_OPT, LOSE_OPT], "minCount": 1, "maxCount": 1}
    moves = enumerate_moves(select)
    assert [indices for _, indices in moves] == [[0], [1]]
    keys = [key for key, _ in moves]
    assert len(set(keys)) == 2


def test_enumerate_moves_keys_are_content_based() -> None:
    # Same option contents in swapped positions must produce the same
    # key set — that's what makes tree edges stable across
    # determinizations with different option orderings.
    a = enumerate_moves({"option": [WIN_OPT, LOSE_OPT],
                         "minCount": 1, "maxCount": 1})
    b = enumerate_moves({"option": [LOSE_OPT, WIN_OPT],
                         "minCount": 1, "maxCount": 1})
    assert {k for k, _ in a} == {k for k, _ in b}


def test_enumerate_moves_pairs_and_cap() -> None:
    options = [{"type": 1, "n": i} for i in range(20)]
    select = {"option": options, "minCount": 2, "maxCount": 2}
    moves = enumerate_moves(select)
    assert len(moves) == 64                      # capped (C(20,2) = 190)
    assert all(len(idx) == 2 for _, idx in moves)
    assert all(len(key) == 2 for key, _ in moves)


def test_enumerate_moves_max_count_exceeds_options() -> None:
    # "Search for up to 3 ..." selects can offer fewer options than
    # maxCount (e.g. only 2 matching cards left in deck); the only
    # legal move is taking everything available. Regression for the
    # EXP-007 seed-37 crash.
    select = {"option": [WIN_OPT, LOSE_OPT], "minCount": 0, "maxCount": 3}
    moves = enumerate_moves(select)
    assert len(moves) == 1
    assert moves[0][1] == [0, 1]
