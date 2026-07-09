"""Kaggle submission shim — SO-ISMCTS variant (Phase 3).

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
2. **Conservative iteration budget.** `ITERATIONS = 500` (half of
   EXP-003). The 10-minute per-match wall clock must cover *every*
   decision in the match; a long game can have 100+ decisions, and the
   Kaggle worker (2 vCPU) is likely slower than the dev machine. 500
   keeps a ~2x safety margin against timeout, which would mark the
   submission as Error and burn an active slot. A future submission can
   raise this once the first run's timing on-worker is observed.

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

ITERATIONS = 500
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
            iterations=ITERATIONS,
            filler_card=FILLER_CARD,
        )
    except (SearchApiError, DeterminizationError):
        return list(range(obs_dict["select"]["maxCount"]))
