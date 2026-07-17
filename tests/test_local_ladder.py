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


DECK = [1000 + i for i in range(60)]
DECK_B = [2000 + i for i in range(60)]


def test_agent_registry_has_all_arms() -> None:
    assert "random" in AGENT_REGISTRY
    assert "heuristic" in AGENT_REGISTRY
    assert "ismcts" in AGENT_REGISTRY
    assert "ismcts-filler" in AGENT_REGISTRY


def test_ismcts_filler_discards_the_opponent_list() -> None:
    # EXP-009's entire treatment is *not* knowing the opponent's deck. If
    # this arm leaked opp_deck through, the experiment would silently be a
    # rerun of EXP-003, report "no gap", and we would conclude the exact
    # opposite of the truth about filler determinization.
    agent = AGENT_REGISTRY["ismcts-filler"](1, DECK, DECK_B, 10)
    assert agent.opponent_deck_list is None
    assert agent.filler_card is not None


def test_ismcts_filler_differs_from_ismcts_only_in_determinization() -> None:
    informed = AGENT_REGISTRY["ismcts"](1, DECK, DECK_B, 10)
    filler = AGENT_REGISTRY["ismcts-filler"](1, DECK, DECK_B, 10)
    # The control knows the list; the treatment does not. Everything the
    # comparison is meant to hold fixed must actually be fixed.
    assert informed.opponent_deck_list == DECK_B
    assert filler.opponent_deck_list is None
    assert filler.my_deck_list == informed.my_deck_list
    assert filler.iterations == informed.iterations
    assert filler.rollout_policy is informed.rollout_policy  # both random
    assert filler.adaptive_budget == informed.adaptive_budget
    assert filler.max_seconds_per_move == informed.max_seconds_per_move


def test_filler_card_is_pinned_to_the_submission_shim() -> None:
    # The arm reproduces the ladder only if it fills with the same card the
    # ladder agent fills with. A drift here would make EXP-009 measure a
    # condition nothing is actually deployed under.
    import re

    from scripts.local_ladder import LADDER_FILLER_CARD

    shim = (
        pathlib.Path(__file__).resolve().parent.parent
        / "submissions" / "ismcts_main.py"
    ).read_text()
    match = re.search(r"^FILLER_CARD = (\d+)", shim, re.MULTILINE)
    assert match, "submissions/ismcts_main.py no longer defines FILLER_CARD"
    assert int(match.group(1)) == LADDER_FILLER_CARD


def test_sign_helper() -> None:
    assert _sign(1.5) == 1
    assert _sign(-2.0) == -1
    assert _sign(0) == 0


def test_wrap_for_cabt_returns_deck_on_initial_call() -> None:
    agent = AGENT_REGISTRY["heuristic"](1, DECK, DECK, 10)
    fn = _wrap_for_cabt(agent, DECK)
    assert fn({"select": None}) == DECK


def test_wrap_for_cabt_delegates_to_choose() -> None:
    agent = AGENT_REGISTRY["heuristic"](1, DECK, DECK, 10)
    fn = _wrap_for_cabt(agent, DECK)
    obs = {"select": {"option": [{"x": 0}, {"x": 1}, {"x": 2}], "minCount": 1, "maxCount": 2}}
    assert fn(obs) == [0, 1]


def test_ismcts_builder_wires_config() -> None:
    agent = AGENT_REGISTRY["ismcts"](7, DECK, DECK, 123)
    assert agent.my_deck_list == DECK
    assert agent.opponent_deck_list == DECK   # mirror match
    assert agent.iterations == 123
    assert agent.fallback_events == []


def test_ismcts_builder_asymmetric_decks() -> None:
    agent = AGENT_REGISTRY["ismcts"](7, DECK, DECK_B, 123)
    assert agent.my_deck_list == DECK
    assert agent.opponent_deck_list == DECK_B


def test_pimc_builder_asymmetric_decks() -> None:
    agent = AGENT_REGISTRY["pimc"](7, DECK, DECK_B, 123)
    assert agent.my_deck_list == DECK
    assert agent.opponent_deck_list == DECK_B


def test_summarize_empty_rows() -> None:
    s = summarize([])
    assert s["n"] == 0
    assert s["win_rate"] == 0.0


def test_summarize_counts_and_wilson() -> None:
    rows = [
        {"outcome_for_a": 1, "fallbacks_a": 0, "fallbacks_b": 0},
        {"outcome_for_a": 1, "fallbacks_a": 2, "fallbacks_b": 0},
        {"outcome_for_a": 1, "fallbacks_a": 0, "fallbacks_b": 0},
        {"outcome_for_a": 0, "fallbacks_a": 0, "fallbacks_b": 1},
        {"outcome_for_a": -1, "fallbacks_a": 0, "fallbacks_b": 0},
    ]
    s = summarize(rows)
    assert s["n"] == 5
    assert s["wins"] == 3
    assert s["draws"] == 1
    assert s["losses"] == 1
    assert s["win_rate"] == pytest.approx(0.6)
    assert 0.0 <= s["wilson_lo"] <= s["win_rate"] <= s["wilson_hi"] <= 1.0
    assert s["fallbacks_a_total"] == 2
    assert s["fallbacks_b_total"] == 1
    assert s["matches_with_fallbacks"] == 2


def test_load_deck_reads_60_lines(tmp_path: pathlib.Path) -> None:
    p = tmp_path / "deck.csv"
    p.write_text("\n".join(str(1000 + i) for i in range(60)) + "\n")
    deck = _load_deck(p)
    assert len(deck) == 60
    assert deck[0] == 1000
    assert deck[59] == 1059
