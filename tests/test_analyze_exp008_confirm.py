"""Tests for the EXP-008 confirmation analyzer.

The load-bearing ones are the integrity guards: `bad_status_rows`
(a file of `status=ERROR` rows reports "0 forfeits" and is pure noise)
and `operating_points` (a resume launched with different `CONF_*` env
vars appends a second operating point to the same file, and pooling
those is meaningless).
"""

from __future__ import annotations

import importlib.util
import pathlib

_SPEC = importlib.util.spec_from_file_location(
    "analyze_exp008_confirm",
    pathlib.Path(__file__).resolve().parent.parent
    / "scripts" / "analyze_exp008_confirm.py",
)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


def _row(**over) -> dict:
    row = {
        "seed": 1,
        "policy": "C",
        "overage_reserve": 60,
        "moves_ahead": 80,
        "my_decisions": 3,
        "my_decision_times": [1.0, 2.0, 3.0],
        "my_cumulative": 6.0,
        "my_final_overage": 597.0,  # bank read before the last 3.0s decision
        "reward_0": 1,
        "status_0": "DONE",
        "status_1": "DONE",
        "forfeit": False,
    }
    row.update(over)
    return row


def test_clean_rows_have_no_status_complaints() -> None:
    assert mod.bad_status_rows([_row(), _row(status_0="TIMEOUT")]) == []


def test_error_rows_are_flagged() -> None:
    # Regression for the getfullargspec bug: whole files of status=ERROR
    # look like a clean 0-forfeit result.
    bad = _row(status_0="ERROR", status_1="ERROR", my_decisions=0)
    assert mod.bad_status_rows([_row(), bad]) == [bad]


def test_missing_status_is_flagged() -> None:
    assert len(mod.bad_status_rows([_row(status_1=None)])) == 1


def test_single_operating_point() -> None:
    assert mod.operating_points([_row(), _row(seed=2)]) == {("C", 60, 80)}


def test_mixed_operating_points_are_visible() -> None:
    # A resume with CONF_MOVES=40 appended to a moves-ahead=80 file.
    rows = [_row(), _row(seed=2, moves_ahead=40)]
    assert mod.operating_points(rows) == {("C", 60, 80), ("C", 60, 40)}


def test_bank_residual_excludes_the_final_decision() -> None:
    # Drawdown 600-597=3.0; measured-minus-last 6.0-3.0=3.0 -> residual 0.
    assert mod.bank_residual(_row(), 600.0) == 0.0


def test_bank_residual_detects_uncharged_time() -> None:
    # Engine charged 10s (600->590) where we only measured 3s of it.
    assert mod.bank_residual(_row(my_final_overage=590.0), 600.0) == 7.0


def test_bank_residual_none_without_a_reading() -> None:
    assert mod.bank_residual(_row(my_final_overage=None), 600.0) is None
    assert mod.bank_residual(_row(my_decision_times=[]), 600.0) is None


def test_summarize_cell_counts_forfeits_and_headroom() -> None:
    rows = [
        _row(my_cumulative=100.0),
        _row(seed=2, my_cumulative=520.0, forfeit=True, reward_0=-1),
    ]
    s = mod.summarize_cell(rows, 540.0)
    assert s["n"] == 2
    assert s["forfeits"] == 1
    assert s["cum_max"] == 520.0
    assert s["headroom"] == 20.0
    assert s["win_rate"] == 0.5


def test_summarize_cell_reports_the_bank_floor() -> None:
    rows = [_row(), _row(seed=2, my_final_overage=123.4)]
    assert mod.summarize_cell(rows, 540.0)["bank_floor"] == 123.4
