"""Kaggle entry point for the PTCG AI Battle Challenge.

The `cabt` engine calls a top-level `agent(obs_dict: dict) -> list[int]`
function. On the first invocation `obs["select"] is None` and we must return
the 60 card IDs of our deck. On every subsequent call we return a list of
integer indices into `obs["select"]["option"]`, with length in
`[obs["select"]["minCount"], obs["select"]["maxCount"]]` and no duplicates.

Phase 0 variant: random selection over the presented legal options. Mirrors
the reference `random_agent` from `kaggle_environments/envs/cabt/cabt.py`.
Kept self-contained (no internal package imports) so the submission bundle is
just `main.py` + `deck.csv`.

Runtime file layout (Kaggle): `/kaggle_simulations/agent/main.py` and
`/kaggle_simulations/agent/deck.csv`.
"""

from __future__ import annotations

import os
import random


def read_deck_csv() -> list[int]:
    """Load a 60-card deck from `deck.csv` at the submission root.

    Falls back to `/kaggle_simulations/agent/deck.csv` when the file is not
    at the current working directory (Kaggle runtime layout).
    """
    path = "deck.csv"
    if not os.path.exists(path):
        path = "/kaggle_simulations/agent/deck.csv"
    with open(path) as f:
        lines = f.read().split("\n")
    return [int(lines[i]) for i in range(60)]


_rng = random.Random()


def agent(obs_dict: dict) -> list[int]:
    """Kaggle-facing entry point."""
    if obs_dict["select"] is None:
        return read_deck_csv()
    n_options = len(obs_dict["select"]["option"])
    max_count = obs_dict["select"]["maxCount"]
    return _rng.sample(range(n_options), max_count)
