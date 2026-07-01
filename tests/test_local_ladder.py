"""Tests for scripts/local_ladder.py.

The `run_match` function talks to `kaggle_environments`, which we do not
exercise here (that lives in the manual local-ladder run). These tests
cover the pure-Python surface: agent factories, summarize(), sign helper.
"""

from __future__ import annotations

import pathlib

import pytest

from scripts.local_ladder import (
    AGENT_REGISTRY,
    _load_deck,
    _sign,
    _wrap_for_cabt,
    summarize,
)


def test_agent_registry_has_random_and_heuristic() -> None:
    assert "random" in AGENT_REGISTRY
    assert "heuristic" in AGENT_REGISTRY


def test_sign_helper() -> None:
    assert _sign(1.5) == 1
    assert _sign(-2.0) == -1
    assert _sign(0) == 0


def test_wrap_for_cabt_returns_deck_on_initial_call() -> None:
    agent = AGENT_REGISTRY["heuristic"](seed=1)
    deck = [1000 + i for i in range(60)]
    fn = _wrap_for_cabt(agent, deck)
    assert fn({"select": None}) == deck


def test_wrap_for_cabt_delegates_to_choose() -> None:
    agent = AGENT_REGISTRY["heuristic"](seed=1)
    deck = [1000 + i for i in range(60)]
    fn = _wrap_for_cabt(agent, deck)
    obs = {"select": {"option": [{"x": 0}, {"x": 1}, {"x": 2}], "minCount": 1, "maxCount": 2}}
    assert fn(obs) == [0, 1]


def test_summarize_empty_rows() -> None:
    s = summarize([])
    assert s["n"] == 0
    assert s["win_rate"] == 0.0


def test_summarize_counts_and_wilson() -> None:
    rows = [
        {"outcome_for_a": 1},
        {"outcome_for_a": 1},
        {"outcome_for_a": 1},
        {"outcome_for_a": 0},
        {"outcome_for_a": -1},
    ]
    s = summarize(rows)
    assert s["n"] == 5
    assert s["wins"] == 3
    assert s["draws"] == 1
    assert s["losses"] == 1
    assert s["win_rate"] == pytest.approx(0.6)
    assert 0.0 <= s["wilson_lo"] <= s["win_rate"] <= s["wilson_hi"] <= 1.0


def test_load_deck_reads_60_lines(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "deck.csv"
    p.write_text("\n".join(str(1000 + i) for i in range(60)) + "\n")
    deck = _load_deck(p)
    assert len(deck) == 60
    assert deck[0] == 1000
    assert deck[59] == 1059
