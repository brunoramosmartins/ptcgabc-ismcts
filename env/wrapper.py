"""Adapter between `kaggle_environments` (the cabt engine) and our Agent classes.

The Kaggle entry point is a top-level `agent(obs_dict: dict) -> list[int]`. This
module owns the two conventions defined by the engine's reference random_agent
(see `kaggle_environments/envs/cabt/cabt.py`):

- If `obs["select"] is None`, return the 60 card IDs of the deck (read from
  `deck.csv` at submission root or `/kaggle_simulations/agent/deck.csv`).
- Otherwise, return a list of integer indices into `obs["select"]["option"]`,
  length in `[obs["select"]["minCount"], obs["select"]["maxCount"]]`, no
  duplicates.

Phase 1 wires this shim into the concrete agents.
"""

from __future__ import annotations

import os


def read_deck_csv(path: str = "deck.csv") -> list[int]:
    """Read a 60-card deck from CSV (one integer card ID per line).

    Falls back to `/kaggle_simulations/agent/deck.csv` when the file is not
    present at the working directory (Kaggle runtime layout).
    """
    if not os.path.exists(path):
        path = "/kaggle_simulations/agent/" + path
    with open(path) as f:
        lines = f.read().split("\n")
    return [int(lines[i]) for i in range(60)]
