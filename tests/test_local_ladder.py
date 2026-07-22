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
    TrajectoryRecorder,
    _load_deck,
    _parse_args,
    _sign,
    _wrap_for_cabt,
    run_match,
    summarize,
)

DECK = [1000 + i for i in range(60)]
DECK_B = [2000 + i for i in range(60)]


def test_agent_registry_has_all_arms() -> None:
    assert "random" in AGENT_REGISTRY
    assert "heuristic" in AGENT_REGISTRY
    assert "ismcts" in AGENT_REGISTRY
    assert "ismcts-filler" in AGENT_REGISTRY
    assert "ismcts-selfdeck" in AGENT_REGISTRY


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


def test_ismcts_selfdeck_discards_the_real_opponent_list() -> None:
    # Like the filler arm, self-deck is a *deployable* condition: it
    # must not peek at the real list. A leak here would make EXP-010's
    # self-deck arm an informed arm in disguise and overstate what we
    # can actually ship.
    agent = AGENT_REGISTRY["ismcts-selfdeck"](1, DECK, DECK_B, 10)
    assert agent.opponent_deck_list == DECK
    assert agent.opponent_deck_list is not agent.my_deck_list  # own copy
    assert agent.opponent_list_is_assumed is True
    assert agent.filler_card is None


def test_ismcts_selfdeck_differs_from_filler_only_in_opponent_model() -> None:
    filler = AGENT_REGISTRY["ismcts-filler"](1, DECK, DECK_B, 10)
    selfdeck = AGENT_REGISTRY["ismcts-selfdeck"](1, DECK, DECK_B, 10)
    # EXP-010 compares these two arms; everything except the imagined
    # opponent must be held fixed.
    assert selfdeck.my_deck_list == filler.my_deck_list
    assert selfdeck.iterations == filler.iterations
    assert selfdeck.rollout_policy is filler.rollout_policy
    assert selfdeck.adaptive_budget == filler.adaptive_budget
    assert selfdeck.max_seconds_per_move == filler.max_seconds_per_move
    assert filler.opponent_list_is_assumed is False


class _ScriptedAgent:
    """Returns a fixed action; lets the wrapper tests stay engine-free."""

    def __init__(self, action: list[int]) -> None:
        self.action = action

    def choose(self, obs: dict) -> list[int]:
        return self.action


def test_wrapper_records_real_decisions_only() -> None:
    rec = TrajectoryRecorder()
    fn = _wrap_for_cabt(_ScriptedAgent([2, 0]), DECK, rec)
    assert fn({"select": None}) == DECK          # deck step: not a decision
    assert rec.decisions == []
    obs = {"select": {"option": [{}, {}, {}], "maxCount": 2}}
    assert fn(obs) == [2, 0]
    assert len(rec.decisions) == 1
    assert rec.decisions[0]["action"] == [2, 0]


def test_recorder_deep_copies_the_observation() -> None:
    # The engine may mutate the obs dict it hands the agent between
    # steps; a shallow reference would silently rewrite history and the
    # training corpus would be states that never co-occurred.
    rec = TrajectoryRecorder()
    obs = {"select": {"option": [{}]}, "current": {"turn": 3}}
    rec.record(obs, [0])
    obs["current"]["turn"] = 99
    assert rec.decisions[0]["obs"]["current"]["turn"] == 3


def test_wrapper_without_recorder_is_unchanged() -> None:
    fn = _wrap_for_cabt(_ScriptedAgent([1]), DECK)
    assert fn({"select": {"option": [{}, {}], "maxCount": 1}}) == [1]


def test_official_candidate_decks_have_60_cards() -> None:
    base = pathlib.Path(__file__).resolve().parent.parent / "decks" / "candidates"
    for name in ("iono", "dragapult-ex", "mega-abomasnow-ex-official",
                 "mega-lucario-ex"):
        deck = _load_deck(base / f"{name}.csv")
        assert len(deck) == 60, name


def test_filler_arm_is_the_frozen_exp009_condition() -> None:
    # Until EXP-010's ship gate this test pinned the arm to the live
    # shim. The shim now ships self-deck determinization (pinned by
    # tests/test_ismcts_main_shim.py), and the filler arm survives as
    # the *historical* EXP-009/-010 condition: the constant stays frozen
    # at the value those experiments measured, and the shim must not
    # grow a filler back without a registered experiment.
    from scripts.local_ladder import LADDER_FILLER_CARD

    shim = (
        pathlib.Path(__file__).resolve().parent.parent
        / "submissions" / "ismcts_main.py"
    ).read_text()
    assert LADDER_FILLER_CARD == 1072
    assert "\nFILLER_CARD =" not in shim


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


def test_overage_bank_default_is_ladder_faithful() -> None:
    # EXP-003..010 all ran under the ladder's 600 s bank; the default
    # must stay 600 so past and future ladder-faithful runs share the
    # same condition, and raising it must be an explicit opt-in.
    import inspect

    args = _parse_args(["--agent-a", "random", "--agent-b", "random"])
    assert args.overage_bank == 600.0
    sig = inspect.signature(run_match)
    assert sig.parameters["overage_bank"].default == 600.0


def test_overage_bank_patch_survives_env_reset() -> None:
    # EXP-011's second false start: the first patch wrote env.state and
    # env.specification, but env.run() always resets a fresh env, and
    # the reset rebuilds state from per-position schema caches built at
    # make() time — silently restoring the 600 s bank (TIMEOUT rows at
    # ~600 s with the bank nominally raised to 100000). The fix must
    # survive a reset, so that is exactly what this test does.
    kaggle_environments = pytest.importorskip("kaggle_environments")

    from scripts.local_ladder import _raise_overage_bank

    env = kaggle_environments.make("cabt", debug=False)
    _raise_overage_bank(env, 100000.0)
    env.reset(2)
    for side in env.state:
        assert side["observation"]["remainingOverageTime"] == 100000.0
