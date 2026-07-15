"""Tests for the timing wrapper in scripts/exp_timing.py.

The load-bearing one is ``test_timed_fn_is_introspectable`` — it
reproduces what ``kaggle_environments`` does to an agent
(``inspect.getfullargspec``), which raises ``TypeError`` on a callable
*class instance* and silently turned every EXP-008 game into
``status=ERROR``. The agent must be a plain closure.
"""

from __future__ import annotations

import importlib.util
import inspect
import pathlib

_SPEC = importlib.util.spec_from_file_location(
    "exp_timing",
    pathlib.Path(__file__).resolve().parent.parent / "scripts" / "exp_timing.py",
)
exp_timing = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(exp_timing)


class _FakeAgent:
    def __init__(self) -> None:
        self.calls = 0

    def choose(self, obs: dict) -> list[int]:
        self.calls += 1
        return [0]


def _select_obs(overage: float) -> dict:
    return {
        "select": {"option": [{}], "minCount": 1, "maxCount": 1},
        "remainingOverageTime": overage,
    }


def test_timed_fn_is_introspectable_by_getfullargspec() -> None:
    # Regression for the status=ERROR bug: env.run introspects the agent
    # with getfullargspec, which rejects callable class instances.
    fn = exp_timing._timed_fn(_FakeAgent(), [1, 2], exp_timing._Record())
    spec = inspect.getfullargspec(fn)  # must not raise
    assert spec.args == ["obs"]


def test_deck_submission_step_is_not_timed() -> None:
    rec = exp_timing._Record()
    fn = exp_timing._timed_fn(_FakeAgent(), [7, 8], rec)
    assert fn({"select": None, "remainingOverageTime": 600}) == [7, 8]
    assert rec.times == []            # deck step is not a decision
    assert rec.last_overage == 600    # but the bank is still recorded


def test_real_decision_is_timed_and_bank_tracked() -> None:
    rec = exp_timing._Record()
    agent = _FakeAgent()
    fn = exp_timing._timed_fn(agent, [7, 8], rec)
    out = fn(_select_obs(590.0))
    assert out == [0]
    assert agent.calls == 1
    assert len(rec.times) == 1
    assert rec.times[0] >= 0.0
    assert rec.last_overage == 590.0
