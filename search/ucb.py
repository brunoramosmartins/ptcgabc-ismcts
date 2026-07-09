r"""UCB1 selection for SO-ISMCTS (subset-armed bandit form).

Derivation of the exploration term from Chernoff–Hoeffding lives in
`exercises/ex02_mcts_derivations.md` Ex 02.1; the availability-count
adaptation follows Cowling et al. (2012) — see
`notes/phase2-ismcts-paper-notes.md` §4.1.

The ISMCTS score for action $a$ at an information-set node is

$$
\text{score}(a) \;=\; \frac{w_a}{n_a} \;+\; c\,\sqrt{\frac{\ln m_a}{n_a}},
$$

where $n_a$ is the visit count, $w_a$ the cumulative reward, and
$m_a$ the availability count — how many times $a$ was legal in the
sampled determinization when its parent was visited. Classical UCT
uses the parent visit count where ISMCTS uses $m_a$; with a single
determinization the two coincide.

The theoretical constant is $c = \sqrt{2}$ for rewards in $[0, 1]$
(Auer et al. 2002). Our terminal reward spans $[-1, +1]$ (width 2),
and $c$ is swept in Phase 4 anyway (`scripts/exp_sensitivity_c.py`),
so the default here is just the anchor for that sweep.
"""

from __future__ import annotations

import math

DEFAULT_C = math.sqrt(2)


def ucb1_score(
    total_reward: float,
    visits: int,
    availability: int,
    c: float = DEFAULT_C,
) -> float:
    r"""Subset-armed UCB1 score for one action.

    Parameters
    ----------
    total_reward : float
        Cumulative backed-up reward :math:`w_a` for this action.
    visits : int
        Visit count :math:`n_a`. Zero visits returns ``inf`` so
        unvisited-but-available actions are always selected first.
    availability : int
        Availability count :math:`m_a \ge 1`. How many times the action
        was legal when its parent was visited.
    c : float, optional
        Exploration constant. Defaults to :math:`\sqrt{2}`.

    Returns
    -------
    float
        :math:`w_a / n_a + c \sqrt{\ln m_a / n_a}`, or ``inf`` when
        ``visits == 0``.

    Raises
    ------
    ValueError
        If ``availability < 1`` or ``visits < 0`` or
        ``visits > availability``.
    """
    if availability < 1:
        raise ValueError(f"availability must be >= 1, got {availability}")
    if visits < 0:
        raise ValueError(f"visits must be >= 0, got {visits}")
    if visits > availability:
        raise ValueError(
            f"visits ({visits}) cannot exceed availability ({availability})"
        )
    if visits == 0:
        return math.inf
    exploitation = total_reward / visits
    exploration = c * math.sqrt(math.log(availability) / visits)
    return exploitation + exploration


def select_action(children: dict, available: list, c: float = DEFAULT_C):
    """Pick the available action with the highest UCB1 score.

    Args:
        children: Mapping of action key -> node with ``total_reward``,
            ``visits``, and ``availability`` attributes (duck-typed;
            `search.node.InfoSetNode` satisfies it).
        available: Action keys legal in the current determinization.
            Every key must already exist in ``children`` (callers run
            ``mark_available`` first, which creates them).
        c: Exploration constant.

    Returns:
        The action key with the maximal score. Ties broken by first
        occurrence in ``available`` (deterministic given input order).

    Raises:
        ValueError: If ``available`` is empty.
    """
    if not available:
        raise ValueError("select_action with no available actions")
    best_key = None
    best_score = -math.inf
    for key in available:
        node = children[key]
        score = ucb1_score(node.total_reward, node.visits, node.availability, c)
        if score > best_score:
            best_score = score
            best_key = key
    return best_key
