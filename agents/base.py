"""Abstract base class shared by every agent variant.

The Kaggle-facing contract is a top-level `agent(obs_dict) -> list[int]` function
(see `data/kaggle/sample_submission/main.py`). Our internal Agent class wraps it
so we can swap random / heuristic / ISMCTS logic without touching the shim.
"""

from __future__ import annotations

from typing import Any


class Agent:
    """Base interface for every agent variant.

    Subclasses implement `choose` — the raw dict from Kaggle is already parsed
    into an Observation by the shim.
    """

    def choose(self, obs: Any) -> list[int]:
        """Return option indices into `obs.select.option`.

        Length must be within `[obs.select.minCount, obs.select.maxCount]`, no
        duplicates. Callers handle the `obs.select is None` (deck submission)
        case separately.
        """
        raise NotImplementedError
