"""Tests for search/node.py and search/ucb.py (Phase 3 core pieces)."""

from __future__ import annotations

import math

import pytest

from search.node import InfoSetNode
from search.ucb import DEFAULT_C, select_action, ucb1_score

# --- InfoSetNode -----------------------------------------------------------

def test_new_node_is_zeroed() -> None:
    n = InfoSetNode()
    assert n.visits == 0
    assert n.total_reward == 0.0
    assert n.availability == 0
    assert n.children == {}
    assert n.q() == 0.0


def test_ensure_child_is_idempotent() -> None:
    n = InfoSetNode()
    a = n.ensure_child("attack")
    b = n.ensure_child("attack")
    assert a is b
    assert len(n.children) == 1


def test_update_accumulates_visits_and_reward() -> None:
    n = InfoSetNode()
    n.update(1.0)
    n.update(-1.0)
    n.update(1.0)
    assert n.visits == 3
    assert n.total_reward == pytest.approx(1.0)
    assert n.q() == pytest.approx(1.0 / 3.0)


def test_mark_available_creates_children_and_counts() -> None:
    n = InfoSetNode()
    n.mark_available(["a", "b"])
    n.mark_available(["b", "c"])
    assert set(n.children) == {"a", "b", "c"}
    assert n.children["a"].availability == 1
    assert n.children["b"].availability == 2
    assert n.children["c"].availability == 1


def test_unvisited_available_filters_visited() -> None:
    n = InfoSetNode()
    n.mark_available(["a", "b", "c"])
    n.children["b"].update(1.0)
    assert n.unvisited_available(["a", "b", "c"]) == ["a", "c"]
    # keys absent from children count as unvisited
    assert n.unvisited_available(["d"]) == ["d"]


def test_best_action_by_visits() -> None:
    n = InfoSetNode()
    n.mark_available(["a", "b"])
    n.children["a"].update(1.0)
    n.children["b"].update(-1.0)
    n.children["b"].update(-1.0)
    assert n.best_action_by_visits() == "b"  # visits win, not value


def test_best_action_on_empty_node_raises() -> None:
    with pytest.raises(ValueError):
        InfoSetNode().best_action_by_visits()


# --- ucb1_score ------------------------------------------------------------

def test_unvisited_action_scores_infinity() -> None:
    assert ucb1_score(0.0, 0, 5) == math.inf


def test_known_value() -> None:
    # w=3, n=4, m=8, c=sqrt(2): 0.75 + sqrt(2)*sqrt(ln 8 / 4)
    expected = 0.75 + math.sqrt(2) * math.sqrt(math.log(8) / 4)
    assert ucb1_score(3.0, 4, 8) == pytest.approx(expected)


def test_c_zero_is_pure_exploitation() -> None:
    assert ucb1_score(2.0, 4, 100, c=0.0) == pytest.approx(0.5)


def test_exploration_grows_with_availability() -> None:
    low = ucb1_score(0.0, 5, 6)
    high = ucb1_score(0.0, 5, 600)
    assert high > low


def test_invalid_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        ucb1_score(0.0, 1, 0)      # availability < 1
    with pytest.raises(ValueError):
        ucb1_score(0.0, -1, 5)     # negative visits
    with pytest.raises(ValueError):
        ucb1_score(0.0, 6, 5)      # visits > availability


# --- select_action ---------------------------------------------------------

def _node(w: float, n: int, m: int) -> InfoSetNode:
    node = InfoSetNode()
    node.total_reward = w
    node.visits = n
    node.availability = m
    return node


def test_select_prefers_unvisited() -> None:
    children = {"good": _node(10.0, 10, 10), "new": _node(0.0, 0, 1)}
    assert select_action(children, ["good", "new"]) == "new"


def test_select_prefers_higher_mean_at_equal_counts() -> None:
    children = {"a": _node(5.0, 10, 20), "b": _node(2.0, 10, 20)}
    assert select_action(children, ["a", "b"]) == "a"


def test_select_ignores_unavailable_actions() -> None:
    children = {
        "best_but_illegal": _node(50.0, 10, 10),
        "ok": _node(1.0, 10, 10),
    }
    assert select_action(children, ["ok"]) == "ok"


def test_select_exploration_can_beat_exploitation() -> None:
    # same mean; the rarely-visited arm gets the bigger bonus
    children = {"often": _node(50.0, 100, 200), "rare": _node(1.0, 2, 200)}
    assert select_action(children, ["often", "rare"], c=DEFAULT_C) == "rare"


def test_select_empty_available_raises() -> None:
    with pytest.raises(ValueError):
        select_action({"a": _node(0, 1, 1)}, [])
