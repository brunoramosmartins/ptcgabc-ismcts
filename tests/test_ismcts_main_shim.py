"""Tests for the Policy-C budget in submissions/ismcts_main.py.

The shim ships `search/` but not `agents/`, so its budget function is a
duplicate of `ISMCTSAgent._budget_seconds`. `test_shim_budget_matches_agent`
is the pin that keeps the copies from drifting: EXP-008 measured the agent,
but the ladder runs the shim, and a silent divergence would mean the
submission runs a policy no experiment ever confirmed.

`test_missing_bank_never_returns_none` guards the sharpest failure mode:
the agent may return None (policy A, unbounded) when the bank is absent,
but the shim pairs that with a 100k iteration cap, so None there would
drain the bank and forfeit the match.
"""

from __future__ import annotations

import importlib.util
import pathlib
import random
import sys

from agents.ismcts_agent import ISMCTSAgent


def _load_shim(monkeypatch, tmp_path: pathlib.Path):
    (tmp_path / "deck.csv").write_text(
        "\n".join(str(1000 + i) for i in range(60)) + "\n"
    )
    monkeypatch.chdir(tmp_path)
    src = (
        pathlib.Path(__file__).resolve().parent.parent
        / "submissions" / "ismcts_main.py"
    )
    spec = importlib.util.spec_from_file_location("ismcts_shim", src)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ismcts_shim"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_shim_returns_deck_on_initial_call(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_shim(monkeypatch, tmp_path)
    deck = module.agent({"select": None})
    assert len(deck) == 60


def test_operating_point_is_the_registered_one(monkeypatch, tmp_path) -> None:
    # EXP-008 confirmed these exact values; the ladder must run them.
    module = _load_shim(monkeypatch, tmp_path)
    assert module.OVERAGE_RESERVE == 60.0
    assert module.BUDGET_MOVES_AHEAD == 80


def test_full_bank_budget(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_shim(monkeypatch, tmp_path)
    # (600 - 60) / 80 = 6.75s -> ~1370 iters, above the EXP-003 baseline.
    assert module.budget_seconds({"remainingOverageTime": 600.0}) == 6.75


def test_budget_decays_as_the_bank_drains(monkeypatch, tmp_path) -> None:
    module = _load_shim(monkeypatch, tmp_path)
    full = module.budget_seconds({"remainingOverageTime": 600.0})
    half = module.budget_seconds({"remainingOverageTime": 300.0})
    assert half < full
    assert half == (300.0 - 60.0) / 80


def test_budget_floors_at_the_reserve(monkeypatch, tmp_path: pathlib.Path) -> None:
    # At and below the reserve the agent still searches (t_floor), so a
    # valid root move always exists — it degrades, it does not forfeit.
    module = _load_shim(monkeypatch, tmp_path)
    assert module.budget_seconds({"remainingOverageTime": 60.0}) == module.MIN_MOVE_SECONDS
    assert module.budget_seconds({"remainingOverageTime": 1.0}) == module.MIN_MOVE_SECONDS


def test_budget_is_never_negative(monkeypatch, tmp_path: pathlib.Path) -> None:
    module = _load_shim(monkeypatch, tmp_path)
    for bank in (0.0, 10.0, 59.9, 60.0, 600.0):
        assert module.budget_seconds({"remainingOverageTime": bank}) > 0


def test_missing_bank_never_returns_none(monkeypatch, tmp_path) -> None:
    # ISMCTSAgent may return None here (policy A). The shim must not: it
    # pairs the budget with a 100k iteration cap, so None = drained bank.
    module = _load_shim(monkeypatch, tmp_path)
    budget = module.budget_seconds({})
    assert budget is not None
    assert budget == module.FALLBACK_MOVE_SECONDS


def test_fallback_cannot_overrun_the_bank(monkeypatch, tmp_path) -> None:
    # The blind fallback is Policy B sized so that a full BUDGET_MOVES_AHEAD
    # game still lands inside the bank minus the reserve.
    module = _load_shim(monkeypatch, tmp_path)
    spent = module.FALLBACK_MOVE_SECONDS * module.BUDGET_MOVES_AHEAD
    assert spent <= 600.0 - module.OVERAGE_RESERVE


def test_shim_budget_matches_agent(monkeypatch, tmp_path: pathlib.Path) -> None:
    # The pin: EXP-008 measured the agent, the ladder runs the shim.
    module = _load_shim(monkeypatch, tmp_path)
    agent = ISMCTSAgent(
        my_deck_list=list(range(60)),
        opponent_deck_list=None,
        rng=random.Random(0),
        adaptive_budget=True,
        overage_reserve=module.OVERAGE_RESERVE,
        budget_moves_ahead=module.BUDGET_MOVES_AHEAD,
    )
    for bank in (600.0, 500.0, 292.2, 120.0, 61.0, 60.0, 5.0):
        obs = {"remainingOverageTime": bank}
        assert module.budget_seconds(obs) == agent._budget_seconds(obs)
