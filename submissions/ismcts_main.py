"""Kaggle submission shim — SO-ISMCTS variant (Phase 4, adaptive budget).

Unlike the random/heuristic shims, ISMCTS is not a one-function agent:
it needs our search stack (`search/`, `env/search_engine.py`), which is
bundled alongside this file. `scripts/submit.py --with-engine` builds
the archive; the runtime layout is:

    /kaggle_simulations/agent/
        main.py            (this file)
        deck.csv
        env/search_engine.py
        search/{determinize,node,ucb,ismcts}.py

Two deliberate differences from the EXP-003 local run:

1. **Opponent deck unknown.** On the ladder we don't know the
   opponent's list, so determinization fills their hidden zones with a
   Basic-Pokémon filler (`FILLER_CARD`) rather than sampling from a
   known list. This is strictly weaker than the EXP-003 mirror setup —
   the ladder rating reflects filler-determinized ISMCTS, a lower bound
   on what informed determinization (open-ideas) could reach.

2. **Adaptive time budget (Policy C), not fixed iterations.** Chosen by
   EXP-008 (#27); see `notes/phase4-time-budget-calibration.md`. The
   engine sets `actTimeout = 0`, so there is *no* per-decision cap and no
   free per-step time: every second of thinking draws down a per-agent
   `remainingOverageTime` bank that starts at 600 s and disqualifies us
   with TIMEOUT if it goes negative. That bank is the single binding
   constraint — and it is readable from our own observation, so instead
   of guessing an iteration count we allocate from what is actually left:

       t_move = max(MIN_MOVE_SECONDS,
                    (bank - OVERAGE_RESERVE) / BUDGET_MOVES_AHEAD)

   Re-read every move, this **cannot deplete the bank by construction**:
   a longer game or a slower worker shrinks the per-move budget instead
   of overrunning it, so hardware we cannot measure costs us *strength*,
   never the match. It also needs no prediction of game length, which
   matters because the ladder field is unknown — the previous fixed
   `ITERATIONS = 500` was a guess calibrated against nothing.

   `BUDGET_MOVES_AHEAD = 80` is a deliberately conservative decisions-
   remaining estimate: EXP-007/008 observed at most 68-69 decisions per
   agent per game across the four candidate decks. It is a constant, so
   the divisor never shrinks as a game progresses — the budget stays
   conservative to the last move rather than splurging at the end.

   Confirmed over 80 games (EXP-008 confirm stage): 0 forfeits,
   cumulative p99 310.7 s against the 540 s target.

`ITERATION_CAP` exists only so `decide()` terminates if the clock somehow
never binds; at ~6.75 s/move it is never the limit. Rollouts stay uniform
random (ADR-001 baseline): EXP-006 tested guided rollouts and H2 was NOT
supported, so switching is an unregistered change — #26 re-tests them at
this *time* budget, where their ~20 % speedup buys iterations rather than
nothing, and that experiment decides what a later submission ships.

A per-decision fallback (heuristic first-`maxCount`) guards any
unsearchable decision so a single determinizer edge case never crashes
a live match.
"""

from __future__ import annotations

import os
import random
import sys

# Kaggle runs this file via exec(), where __file__ is undefined — so we
# cannot derive our directory from it. On the worker the agent always
# lives at /kaggle_simulations/agent/; locally (import or exec from the
# bundle dir) the CWD is that dir. Cover both, plus __file__ when it
# does exist (normal import, e.g. tests).
_ROOTS = ["/kaggle_simulations/agent", os.getcwd()]
try:
    _ROOTS.insert(0, os.path.dirname(os.path.abspath(__file__)))
except NameError:  # pragma: no cover - Kaggle exec() path
    pass
for _root in _ROOTS:
    if _root and _root not in sys.path:
        sys.path.insert(0, _root)

from env.search_engine import SearchApiError  # noqa: E402
from search import ismcts  # noqa: E402
from search.determinize import DeterminizationError  # noqa: E402

# Policy C parameters — pre-registered in experiments/registry.md (EXP-008)
# before the confirmation run, and unchanged by it.
OVERAGE_RESERVE = 60.0      # never-spend cushion, seconds
BUDGET_MOVES_AHEAD = 80     # conservative decisions-remaining estimate
MIN_MOVE_SECONDS = 0.05     # t_floor: always search *something*
ITERATION_CAP = 100_000     # never binds; the clock does

# Used only if the bank is missing from the observation (never seen in
# EXP-008, where it was present in all 1454 decisions). Equals the
# full-bank per-move budget, i.e. Policy B sized so that
# t_move * BUDGET_MOVES_AHEAD == 600 - OVERAGE_RESERVE.
FALLBACK_MOVE_SECONDS = (600.0 - OVERAGE_RESERVE) / BUDGET_MOVES_AHEAD

FILLER_CARD = 1072  # Snorlax — a Basic Pokémon, legal in the active slot
_RNG = random.Random()
_DECK: list[int] | None = None


def read_deck_csv() -> list[int]:
    path = "deck.csv"
    if not os.path.exists(path):
        path = "/kaggle_simulations/agent/deck.csv"
    with open(path) as f:
        lines = f.read().split("\n")
    return [int(lines[i]) for i in range(60)]


def budget_seconds(obs_dict: dict) -> float:
    """Wall-clock budget for this decision under Policy C.

    Mirrors ``agents.ismcts_agent.ISMCTSAgent._budget_seconds`` with
    ``adaptive_budget=True``; kept duplicated because the submission
    bundle ships ``search/`` but not ``agents/``. The two are pinned
    together by ``tests/test_ismcts_main_shim.py``.

    Args:
        obs_dict: The raw cabt observation. ``remainingOverageTime`` is
            our own per-agent bank in seconds (``shared: false``).

    Returns:
        Seconds this decision may spend. Never returns ``None``: an
        unbounded search here would drain the bank and forfeit.
    """
    remaining = obs_dict.get("remainingOverageTime")
    if remaining is None:
        return FALLBACK_MOVE_SECONDS
    spendable = remaining - OVERAGE_RESERVE
    per_move = spendable / BUDGET_MOVES_AHEAD
    return max(MIN_MOVE_SECONDS, per_move)


def agent(obs_dict: dict) -> list[int]:
    global _DECK
    if obs_dict["select"] is None:
        _DECK = read_deck_csv()
        return _DECK
    if _DECK is None:
        _DECK = read_deck_csv()
    try:
        return ismcts.decide(
            obs_dict,
            my_deck_list=_DECK,
            opponent_deck_list=None,   # unknown on the ladder
            rng=_RNG,
            iterations=ITERATION_CAP,
            filler_card=FILLER_CARD,
            max_seconds=budget_seconds(obs_dict),
            min_iterations=1,
        )
    except (SearchApiError, DeterminizationError):
        return list(range(obs_dict["select"]["maxCount"]))
