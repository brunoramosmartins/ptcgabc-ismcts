"""Tests for stats.wilson."""

from __future__ import annotations

import math

import pytest

from stats.wilson import wilson_interval


def test_no_trials_returns_trivial_interval() -> None:
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_all_wins_upper_bound_below_one() -> None:
    lo, hi = wilson_interval(10, 10)
    assert 0.0 < lo < 1.0
    assert hi == pytest.approx(1.0) or hi < 1.0
    assert lo < hi


def test_all_losses_lower_bound_above_zero() -> None:
    lo, hi = wilson_interval(0, 10)
    assert lo >= 0.0
    assert 0.0 < hi < 1.0


def test_half_half_symmetric_around_half() -> None:
    lo, hi = wilson_interval(50, 100)
    center = (lo + hi) / 2
    assert center == pytest.approx(0.5, abs=1e-3)


def test_interval_narrows_as_n_grows() -> None:
    _, hi_small = wilson_interval(50, 100)
    lo_small = 1 - hi_small
    _, hi_large = wilson_interval(500, 1000)
    lo_large = 1 - hi_large
    assert (hi_large - lo_large) < (hi_small - lo_small)


def test_interval_endpoints_are_in_unit_interval() -> None:
    for k in (0, 1, 5, 10, 50, 100):
        lo, hi = wilson_interval(k, 100)
        assert 0.0 <= lo <= hi <= 1.0


def test_known_value_50_100() -> None:
    """Match a textbook reference value for 50/100 at z=1.96."""
    lo, hi = wilson_interval(50, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3)
    assert hi == pytest.approx(0.5962, abs=1e-3)


def test_negative_successes_rejected() -> None:
    with pytest.raises(ValueError):
        wilson_interval(-1, 10)


def test_successes_over_trials_rejected() -> None:
    with pytest.raises(ValueError):
        wilson_interval(11, 10)


def test_no_nan_in_edge_cases() -> None:
    lo, hi = wilson_interval(0, 1)
    assert not math.isnan(lo) and not math.isnan(hi)
    lo, hi = wilson_interval(1, 1)
    assert not math.isnan(lo) and not math.isnan(hi)
