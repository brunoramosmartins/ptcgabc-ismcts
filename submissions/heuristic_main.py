"""Kaggle submission shim — heuristic variant (Phase 1).

Bundled by:

    python scripts/submit.py \\
        --main submissions/heuristic_main.py \\
        --out submission-heuristic.tar.gz

Self-contained by design: mirrors `agents/heuristic_agent.py` so the
Kaggle bundle stays two files (main.py + deck.csv). Any change to the
heuristic scoring rule lands here AND in `agents/heuristic_agent.py`
in the same commit — the tests in `tests/test_agents.py` guard the
internal variant; smoke tests via `scripts/local_ladder.py` guard the
end-to-end behavior before bundling.
"""

from __future__ import annotations

import os


def read_deck_csv() -> list[int]:
    path = "deck.csv"
    if not os.path.exists(path):
        path = "/kaggle_simulations/agent/deck.csv"
    with open(path) as f:
        lines = f.read().split("\n")
    return [int(lines[i]) for i in range(60)]


def _score(option: object, index: int) -> float:
    """Prefer earlier indices (deterministic first-`maxCount` selector)."""
    return -float(index)


def agent(obs_dict: dict) -> list[int]:
    if obs_dict["select"] is None:
        return read_deck_csv()
    options = obs_dict["select"]["option"]
    max_count = obs_dict["select"]["maxCount"]
    ranked = sorted(
        range(len(options)),
        key=lambda i: (-_score(options[i], i), i),
    )
    return ranked[:max_count]
