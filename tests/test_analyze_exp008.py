"""Tests for the pure helpers in scripts/analyze_exp008.py."""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "analyze_exp008",
    pathlib.Path(__file__).resolve().parent.parent / "scripts" / "analyze_exp008.py",
)
analyze = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(analyze)


# --- fit_linear -------------------------------------------------------------

def test_fit_linear_recovers_a_perfect_line() -> None:
    xs = [0.0, 1.0, 2.0, 3.0, 4.0]
    ys = [2.0 + 3.0 * x for x in xs]
    alpha, beta, r2 = analyze.fit_linear(xs, ys)
    assert alpha == pytest.approx(2.0)
    assert beta == pytest.approx(3.0)
    assert r2 == pytest.approx(1.0)


def test_fit_linear_single_point_is_degenerate() -> None:
    alpha, beta, r2 = analyze.fit_linear([5.0], [9.0])
    assert (alpha, beta, r2) == (9.0, 0.0, 0.0)


def test_fit_linear_flat_target_has_zero_slope_and_r2() -> None:
    alpha, beta, r2 = analyze.fit_linear([1.0, 2.0, 3.0], [7.0, 7.0, 7.0])
    assert beta == pytest.approx(0.0)
    assert alpha == pytest.approx(7.0)
    assert r2 == 0.0


def test_fit_linear_positive_slope_on_noisy_data() -> None:
    xs = [300.0, 600.0, 1000.0, 1500.0]
    ys = [0.35, 0.62, 1.05, 1.55]  # roughly linear-in-iters cost
    alpha, beta, r2 = analyze.fit_linear(xs, ys)
    assert beta > 0
    assert r2 > 0.99


# --- pct --------------------------------------------------------------------

def test_pct_empty_is_none() -> None:
    assert analyze.pct([], 0.5) is None


def test_pct_nearest_rank() -> None:
    xs = list(range(1, 101))  # 1..100
    assert analyze.pct(xs, 0.5) == 51      # nearest-rank index int(0.5*100)=50 -> 51
    assert analyze.pct(xs, 0.99) == 100
    assert analyze.pct(xs, 0.0) == 1


# --- largest_safe_iters -----------------------------------------------------

def test_largest_safe_iters_solves_the_budget_equation() -> None:
    # c(it) = 0.1 + 0.001*it ; budget 540 ; p99[M] = 60
    # per-decision budget = 540/60 = 9.0 s ; it* = (9.0 - 0.1)/0.001 = 8900
    it_star = analyze.largest_safe_iters(0.1, 0.001, 60.0, 540.0)
    assert it_star == pytest.approx(8900.0)


def test_largest_safe_iters_unbounded_when_no_cost_growth() -> None:
    assert analyze.largest_safe_iters(0.1, 0.0, 60.0, 540.0) == float("inf")
    assert analyze.largest_safe_iters(0.1, 0.001, 0.0, 540.0) == float("inf")
