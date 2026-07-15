"""Tests for ISMCTSAgent's time-budget policy (#27 / EXP-008).

Covers ``_budget_seconds`` — the pure per-decision budget selector — for
the three policies:

- A (default): no cap → ``None`` (pure fixed-iteration search).
- B (fixed cap): the configured ``max_seconds_per_move``.
- C (adaptive): ``(remainingOverageTime - reserve) / moves_ahead``,
  floored at ``MIN_MOVE_SECONDS`` and re-read every decision so the bank
  cannot go negative.

These do not touch the engine, so they run without the SDK.
"""

from __future__ import annotations

from agents.ismcts_agent import MIN_MOVE_SECONDS, ISMCTSAgent


def _agent(**kwargs) -> ISMCTSAgent:
    return ISMCTSAgent(my_deck_list=[1] * 60, **kwargs)


def _obs(overage: float | None) -> dict:
    obs: dict = {"select": {"option": [{}], "minCount": 1, "maxCount": 1}}
    if overage is not None:
        obs["remainingOverageTime"] = overage
    return obs


# --- Policy A (default) -----------------------------------------------------

def test_policy_a_default_returns_none() -> None:
    agent = _agent()
    assert agent._budget_seconds(_obs(600)) is None


# --- Policy B (fixed cap) ---------------------------------------------------

def test_policy_b_returns_fixed_cap() -> None:
    agent = _agent(max_seconds_per_move=5.0)
    # Fixed cap ignores the bank entirely.
    assert agent._budget_seconds(_obs(600)) == 5.0
    assert agent._budget_seconds(_obs(30)) == 5.0


# --- Policy C (adaptive) ----------------------------------------------------

def test_policy_c_splits_spendable_bank() -> None:
    agent = _agent(adaptive_budget=True, overage_reserve=60.0,
                   budget_moves_ahead=40)
    # (600 - 60) / 40 = 13.5
    assert agent._budget_seconds(_obs(600)) == 13.5


def test_policy_c_shrinks_as_bank_drains() -> None:
    agent = _agent(adaptive_budget=True, overage_reserve=60.0,
                   budget_moves_ahead=40)
    early = agent._budget_seconds(_obs(600))   # 13.5
    late = agent._budget_seconds(_obs(200))    # (200-60)/40 = 3.5
    assert late < early
    assert late == 3.5


def test_policy_c_floors_at_min_when_bank_hits_reserve() -> None:
    agent = _agent(adaptive_budget=True, overage_reserve=60.0,
                   budget_moves_ahead=40)
    # Bank exactly at reserve → spendable 0 → floor, never 0 or negative.
    assert agent._budget_seconds(_obs(60)) == MIN_MOVE_SECONDS


def test_policy_c_floors_when_bank_below_reserve() -> None:
    agent = _agent(adaptive_budget=True, overage_reserve=60.0,
                   budget_moves_ahead=40)
    # Below reserve → negative spendable → still floored, so the loop
    # runs min_iterations and the bank cannot be pushed negative.
    assert agent._budget_seconds(_obs(30)) == MIN_MOVE_SECONDS


def test_policy_c_falls_back_when_overage_absent() -> None:
    # Raw sim.lib harness has no remainingOverageTime; adaptive C then
    # falls back to the fixed cap (here None → pure iterations).
    agent = _agent(adaptive_budget=True, max_seconds_per_move=None)
    assert agent._budget_seconds(_obs(None)) is None
    agent_b = _agent(adaptive_budget=True, max_seconds_per_move=4.0)
    assert agent_b._budget_seconds(_obs(None)) == 4.0
