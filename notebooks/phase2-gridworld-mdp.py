# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
# ---

# %% [markdown]
# # Phase 2 — GridWorld MDP
#
# Reinforces Sutton & Barto Ch 3 in code. Three exercises adapted from
# *AI Engineering from Scratch — Phase 9 / Lesson 1* (see
# `notes/phase2-rl-foundations.md`).
#
# Cross-refs into this repo:
# - [`exercises/sutton-barto-ch03.md`](../exercises/sutton-barto-ch03.md) —
#   §3.14 (numerical Bellman) and §3.24 (optimal gridworld value).
# - [`notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) —
#   §3.1 (4-arg $p$), §3.4 (discount vs horizon), §3.5 (info sets).
# - [`exercises/ex01_environment.md`](../exercises/ex01_environment.md) —
#   §4 (linearity of expectation).
#
# Format: jupytext `py:percent`. Open as a notebook in VS Code / PyCharm,
# or run directly with `python notebooks/phase2-gridworld-mdp.py`. Convert
# to `.ipynb` with `jupytext --to ipynb notebooks/phase2-gridworld-mdp.py`
# if you prefer.
#
# Author fills in every `_( implement )_` block. Don't remove the cross-refs
# in the markdown cells — they anchor the artifact to the rest of the
# study notes.

# %% [markdown]
# ## Setup

# %%
from __future__ import annotations

import random

import matplotlib.pyplot as plt
import numpy as np

GRID = 4
TERMINAL = (GRID - 1, GRID - 1)
ACTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def all_states() -> list[tuple[int, int]]:
    """All cells of the 4x4 grid, including the terminal."""
    return [(r, c) for r in range(GRID) for c in range(GRID)]


# %% [markdown]
# ## Step 1 — The MDP
#
# **Task.** Implement the deterministic step function. Signature:
#
# ```
# step(state: tuple[int, int], action: str) -> (next_state, reward, done)
# ```
#
# Rules:
# - Terminal state absorbs: `step(TERMINAL, *) == (TERMINAL, 0.0, True)`.
# - Any other state: apply the action delta from `ACTIONS`, clip to the
#   grid bounds, reward `-1.0`, `done` is True iff the next state is
#   `TERMINAL`.

# %%
def step(state: tuple[int, int], action: str) -> tuple[tuple[int, int], float, bool]:
    """Deterministic 4x4 GridWorld transition."""
    # _( implement )_
    raise NotImplementedError


# %% [markdown]
# ## Step 2 — Policy and rollout
#
# **Task.** Implement `uniform_policy(state)` (returns a dict mapping each
# action to $0.25$) and `rollout(policy, max_steps=200)` (returns
# `(total_return, steps)`).
#
# The rollout should sample from the policy's action distribution using
# the standard-library `random.choices` — a small helper `sample_action`
# is provided.

# %%
def sample_action(policy_dist: dict[str, float], rng: random.Random) -> str:
    """Sample one action from a discrete distribution."""
    actions, probs = zip(*policy_dist.items())
    return rng.choices(actions, weights=probs, k=1)[0]


def uniform_policy(state: tuple[int, int]) -> dict[str, float]:
    """Uniform-random policy over the four cardinal actions."""
    # _( implement )_
    raise NotImplementedError


def rollout(
    policy: callable,
    max_steps: int = 200,
    rng: random.Random | None = None,
    start: tuple[int, int] = (0, 0),
) -> tuple[float, int]:
    """Roll out a policy from `start` until termination or max_steps.

    Returns:
        total_return: sum of undiscounted rewards along the trajectory.
        steps: number of environment steps taken.
    """
    rng = rng or random.Random()
    # _( implement )_
    raise NotImplementedError


# %% [markdown]
# ## Exercise Easy — 10,000 rollouts
#
# **Task.** Run 10,000 rollouts of the uniform-random policy. Report:
#
# - mean total return
# - standard deviation of total return
# - mean episode length (steps)
#
# Compare against the theoretical optimum. For a 4×4 grid with step
# penalty $-1$, the optimal path length from `(0, 0)` to `(3, 3)` is
# 6 steps (three rights + three downs, any interleaving), so the
# optimal return is $-6$.
#
# **Prompt to reflect on** (write your answer below the run):
# What does the gap between random and optimal tell you about the value
# of *any* policy, even a trivial one, over uniform random?

# %%
# _( run 10_000 rollouts, print mean / std / mean-steps, compare with -6 )_

# %% [markdown]
# **Reflection.** _( fill in )_

# %% [markdown]
# ## Step 3 — Iterative policy evaluation
#
# **Task.** Implement iterative policy evaluation for the Bellman
# expectation equation:
#
# $$
# V^\pi(s) \;=\; \sum_a \pi(a \mid s) \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, V^\pi(s') \bigr].
# $$
#
# For a deterministic MDP, $p(s', r \mid s, a) = 1$ for the unique
# $(s', r)$ pair returned by `step`, so the inner sum collapses to a
# single term.
#
# Loop over states until the max update magnitude falls below `tol`.

# %%
def policy_evaluation(
    policy: callable,
    gamma: float = 0.99,
    tol: float = 1e-6,
    max_iters: int = 10_000,
) -> dict[tuple[int, int], float]:
    """Iterative policy evaluation for a deterministic MDP."""
    V = {s: 0.0 for s in all_states()}
    # _( implement — loop until max delta < tol, or max_iters )_
    raise NotImplementedError
    return V


def v_to_grid(V: dict[tuple[int, int], float]) -> np.ndarray:
    """Convert V (dict) into a (GRID, GRID) numpy array for display."""
    grid = np.zeros((GRID, GRID))
    for (r, c), v in V.items():
        grid[r, c] = v
    return grid


# %% [markdown]
# ## Exercise Medium — γ ∈ {0.5, 0.9, 0.99}
#
# **Task.** Run `policy_evaluation(uniform_policy, gamma=g)` for the
# three values of $\gamma$. Print $V$ as a 4×4 grid (numeric or heatmap
# via `matplotlib.pyplot.imshow`) for each.
#
# **Prompt to reflect on** (write your answer below):
# Why do state values near the terminal grow faster with larger $\gamma$?
# Connect this to the effective-horizon interpretation
# $\text{H}_{\text{eff}} \approx 1 / (1 - \gamma)$ from
# [`notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) §3.4.

# %%
# _( evaluate for three gammas, plot heatmaps side by side )_

# %% [markdown]
# **Reflection.** _( fill in )_

# %% [markdown]
# ## Step 4 — Stochastic step (slip)
#
# **Task.** Implement a stochastic variant of `step` where the intended
# action succeeds with probability $1 - p_{\text{slip}}$, and with
# probability $p_{\text{slip}}$ the agent instead moves in one of the
# other three cardinal directions (uniformly among them, so each
# non-intended direction has probability $p_{\text{slip}} / 3$).
#
# The transition kernel now has $|s'| = 4$ possible successors per
# `(state, action)` pair, in contrast to the deterministic version's
# $|s'| = 1$. Update `policy_evaluation_stochastic` accordingly — it
# must marginalize over successors:
#
# $$
# V^\pi(s) \;=\; \sum_a \pi(a \mid s) \sum_{s'} p(s' \mid s, a)\, \bigl[ r(s, a, s') + \gamma\, V^\pi(s') \bigr].
# $$

# %%
P_SLIP = 0.1


def step_stochastic(
    state: tuple[int, int],
    action: str,
    rng: random.Random,
    p_slip: float = P_SLIP,
) -> tuple[tuple[int, int], float, bool]:
    """Stochastic step: intended action w.p. (1 - p_slip), else uniform slip."""
    # _( implement )_
    raise NotImplementedError


def policy_evaluation_stochastic(
    policy: callable,
    gamma: float = 0.99,
    tol: float = 1e-6,
    p_slip: float = P_SLIP,
    max_iters: int = 10_000,
) -> dict[tuple[int, int], float]:
    """Iterative policy evaluation for the slippery GridWorld.

    Enumerates all four possible successor states per (s, a) instead of
    following a single sampled transition.
    """
    V = {s: 0.0 for s in all_states()}
    # _( implement — expand p(s'|s,a) explicitly per action, marginalize )_
    raise NotImplementedError
    return V


# %% [markdown]
# ## Exercise Hard — V under slip
#
# **Task.** Run `policy_evaluation_stochastic(uniform_policy, gamma=0.99,
# p_slip=0.1)`. Print the resulting $V$ grid and compare it side-by-side
# with the deterministic version from Exercise Medium (with the same
# $\gamma$).
#
# **Prompt to reflect on** (write your answer below):
# Does $V[\text{start}]$ (i.e. $V[(0, 0)]$) get better or worse under
# slip, holding $\gamma$ fixed? Why?
#
# Hint: think about how a uniform-random policy is affected by transition
# noise. Under uniform-random *and* deterministic transitions, the agent
# already wanders. Adding slip introduces additional wandering on top of
# an already-random policy. Which direction should $V[\text{start}]$
# move?

# %%
# _( evaluate stochastic, plot deterministic vs stochastic side by side )_

# %% [markdown]
# **Reflection.** _( fill in )_

# %% [markdown]
# ## Bridge to the PTCG project
#
# **Task.** Fill in the following comparison table with one-line
# observations from what you built above. This is where GridWorld
# earns its keep as a study artifact — the table below is what
# distinguishes "did an RL exercise" from "understood *why* PTCG needs
# a different algorithm."

# %% [markdown]
# | Dimension | GridWorld (this notebook) | Pokémon TCG (this project) | Consequence for algorithm choice |
# |---|---|---|---|
# | Observability | Fully observed (state = cell) | _( fill in )_ | _( fill in )_ |
# | Transition determinism | _( fill in )_ | Stochastic (coin flips, card draws) | _( fill in — link to §8.3 sample vs expected updates )_ |
# | Reward density | Dense (-1 every step) | _( fill in )_ | _( fill in )_ |
# | State-space size | $16$ cells | _( fill in — cite `ex01_environment.md` §3 )_ | _( fill in )_ |
# | Right family of algorithms | Value iteration, Q-learning | _( fill in — cite ADR-001 )_ | _( fill in )_ |

# %% [markdown]
# **Final reflection.** _( 3-5 lines: what did coding this shift in your
# understanding vs just reading Ch 3? )_
