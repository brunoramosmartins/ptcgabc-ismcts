"""Abstract base class shared by every agent variant.

The Kaggle-facing contract is a top-level `agent(obs_dict) -> list[int]` function
(reference: `kaggle_environments/envs/cabt/cabt.py::random_agent`). Our internal
Agent class wraps it so we can swap random / heuristic / ISMCTS logic without
touching the shim.

Observation shape (dict, not wrapper class — `cg.api` no longer exists):
    obs["select"] is None on the initial call (deck submission).
    Otherwise:
        obs["select"]["option"]   — list of legal options
        obs["select"]["minCount"] — min items to return
        obs["select"]["maxCount"] — max items to return
"""

from __future__ import annotations


class Agent:
    """Base interface for every agent variant.

    Subclasses implement `choose` — the shim handles the deck-submission
    special case (obs["select"] is None) separately.
    """

    def choose(self, obs: dict) -> list[int]:
        """Return option indices into `obs["select"]["option"]`.

        Length in `[obs["select"]["minCount"], obs["select"]["maxCount"]]`, no
        duplicates. Callers ensure this is only invoked when `obs["select"]` is
        not None.
        """
        raise NotImplementedError
