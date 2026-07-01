"""Tests for the agent variants: RandomAgent, HeuristicAgent."""

from __future__ import annotations

import random

from agents.heuristic_agent import HeuristicAgent
from agents.random_agent import RandomAgent


def _obs(options: list[object], max_count: int = 1, min_count: int = 1) -> dict:
    return {
        "select": {
            "option": options,
            "minCount": min_count,
            "maxCount": max_count,
        }
    }


def test_random_agent_returns_maxcount_distinct_indices() -> None:
    agent = RandomAgent(rng=random.Random(42))
    obs = _obs(options=[{"id": i} for i in range(6)], max_count=3)
    choice = agent.choose(obs)
    assert len(choice) == 3
    assert len(set(choice)) == 3
    assert all(0 <= i < 6 for i in choice)


def test_random_agent_is_reproducible_under_seed() -> None:
    obs = _obs(options=[{"id": i} for i in range(10)], max_count=4)
    a = RandomAgent(rng=random.Random(123)).choose(obs)
    b = RandomAgent(rng=random.Random(123)).choose(obs)
    assert a == b


def test_heuristic_default_picks_first_maxcount() -> None:
    agent = HeuristicAgent()
    obs = _obs(options=[{"id": i} for i in range(5)], max_count=2)
    assert agent.choose(obs) == [0, 1]


def test_heuristic_is_deterministic() -> None:
    agent = HeuristicAgent()
    obs = _obs(options=[{"id": i} for i in range(7)], max_count=3)
    assert agent.choose(obs) == agent.choose(obs)


def test_heuristic_uses_score_override() -> None:
    class ReverseHeuristic(HeuristicAgent):
        def score(self, option: object, index: int) -> float:
            return float(index)  # prefer LATER options

    agent = ReverseHeuristic()
    obs = _obs(options=[{"id": i} for i in range(5)], max_count=2)
    assert agent.choose(obs) == [4, 3]


def test_heuristic_maxcount_equals_option_count() -> None:
    agent = HeuristicAgent()
    obs = _obs(options=[{"id": i} for i in range(3)], max_count=3)
    assert sorted(agent.choose(obs)) == [0, 1, 2]


def test_heuristic_stable_tiebreak_by_index() -> None:
    class ConstantScore(HeuristicAgent):
        def score(self, option: object, index: int) -> float:
            return 0.0  # every option tied

    agent = ConstantScore()
    obs = _obs(options=[{"id": i} for i in range(4)], max_count=2)
    # Ties broken by ascending index → first two options
    assert agent.choose(obs) == [0, 1]
