"""Tests for search/pimc.py against the same fake engine as ISMCTS.

Reuses the depth-1 game from test_ismcts (WIN_OPT ends result 0, root
wins; LOSE_OPT ends result 1, root loses). PIMC must vote for the
winning move and split its budget across K trees.
"""

from __future__ import annotations

import random

import pytest

import search.ismcts as ismcts_mod
import search.pimc as pimc_mod
from search.pimc import decide_pimc

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
    # decide_pimc calls _run_iteration (in ismcts_mod) and search_end
    # (imported into pimc_mod); patch both module references.
    for mod in (ismcts_mod, pimc_mod):
        monkeypatch.setattr(mod.search_engine, "search_begin", fake.search_begin)
        monkeypatch.setattr(mod.search_engine, "search_step", fake.search_step)
        monkeypatch.setattr(mod.search_engine, "search_end", fake.search_end)
    monkeypatch.setattr(ismcts_mod, "sample_determinization",
                        lambda *a, **kw: {})
    monkeypatch.setattr(pimc_mod, "sample_determinization",
                        lambda *a, **kw: {})
    return fake


def test_pimc_votes_for_the_winning_move(fake_engine) -> None:
    choice = decide_pimc(
        _root_obs(), my_deck_list=[], opponent_deck_list=[],
        rng=random.Random(0), iterations=40, k=4,
    )
    assert choice == [0]


def test_pimc_splits_budget_across_k_trees(fake_engine) -> None:
    # 40 iterations / K=4 = 10 per tree = 40 begin calls total; one
    # shared search_end at the end.
    decide_pimc(_root_obs(), my_deck_list=[], opponent_deck_list=[],
                rng=random.Random(0), iterations=40, k=4)
    assert fake_engine.begin_calls == 40
    assert fake_engine.end_calls == 1


def test_pimc_k_one_still_works(fake_engine) -> None:
    choice = decide_pimc(_root_obs(), my_deck_list=[], opponent_deck_list=[],
                         rng=random.Random(0), iterations=20, k=1)
    assert choice == [0]
    assert fake_engine.begin_calls == 20
