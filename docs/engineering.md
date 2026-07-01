# Engineering

Architecture, testing, CI, and reproducibility notes. Companion to `docs/research.md`.

## Competition SDK

The simulator engine is called **`cabt`** (per the Simulation Category overview: "Battles are run on the cabt Engine"). API docs live at **<https://matsuoinstitute.github.io/cabt/>** — no install instructions there, but the API structure is documented.

The `cabt` **environment** is registered inside the `kaggle-environments` package at `kaggle_environments/envs/cabt/`. It ships with a `cg/` subpackage that provides the native engine (`.so`/`.dll`/`.dylib` + Python wrappers in `cg/game.py` and `cg/sim.py`).

**Version note:** The Simulation Category overview says "as of kaggle-environments 1.14.10", but the `cabt` env was **not** actually shipped at that version — 1.14.11 (the closest available on PyPI) does not contain a `cabt` folder. Use the latest release (>= 1.30) which does bundle it.

### The `cg.api` wrapper is gone — the API is now plain dicts

The Kaggle-provided `data/kaggle/sample_submission/main.py` opens with:

```python
from cg.api import Observation, to_observation_class
```

**That import no longer exists.** The `cg/__init__.py` in kaggle-environments 1.30.2 is empty; there is no `api` submodule. The sample was written for an earlier SDK snapshot that had a wrapper class, and the sample has not been updated.

The **current** API is dict indexing, as used by the reference agents inside `kaggle_environments/envs/cabt/cabt.py`:

```python
def random_agent(obs: dict) -> list[int]:
    if obs["select"] is None:
        return deck  # 60 card IDs, the deck submission
    return random.sample(
        list(range(len(obs["select"]["option"]))),
        obs["select"]["maxCount"],
    )
```

We follow the dict form throughout our code. The `data/kaggle/sample_submission/` files are kept as historical reference only — do not treat them as canonical.

## Agent Interface

The Kaggle entry point is a top-level `agent(obs_dict: dict) -> list[int]` function, not a class method. Conventions (all dict-indexed):

- On the very first call `obs["select"] is None` — the agent returns the 60 card IDs of its deck (the initial "deck submission").
- On subsequent calls the agent returns a list of integer indices into `obs["select"]["option"]`.
- The returned list length is in `[obs["select"]["minCount"], obs["select"]["maxCount"]]`, no duplicates.
- The engine only ever presents legal options — no need to filter.

The observation also carries `obs["logs"]` (game log) and `obs["current"]` (turn context, including `yourIndex` and `result`).

Our internal `agents/` classes wrap this contract so search / heuristic / random logic can be swapped without touching the Kaggle-facing shim.

## Deck Format

Plain CSV — 60 lines, one integer card ID per line. Reference: `data/kaggle/sample_submission/deck.csv`. Our deck lives at `decks/selected/deck.csv`.

## Submission Bundle

Kaggle expects a `.tar.gz` archive with `main.py` and `deck.csv` at the top level (no nesting):

```bash
tar -czvf submission.tar.gz main.py deck.csv
```

Upload under the "My Submissions" tab. Runtime constraints:

| Limit | Value |
|---|---|
| Bundle size | ≤ 197.7 MiB |
| Daily submissions | 5 |
| Active submissions per team | 2 most recent |
| Runtime file location | `/kaggle_simulations/agent/` |
| Runtime HDD / RAM / vCPUs | 11.8 GiB / 12.2 GiB / 2 |
| Per-match wall clock | 10 min |

**Rating dynamics:**
- Initial estimate: $\mu_0 = 600$, Gaussian $\mathcal{N}(\mu, \sigma^2)$ (TrueSkill-style).
- Validation Episode runs first (agent plays copies of itself). Failure → submission marked `Error`; download logs to debug.
- Only your 2 most recent submissions receive new episodes — older ones still exist but don't play.
- Only your best-scoring active submission shows on the leaderboard.

## Local Development

### Recommended: WSL2 + Python 3.11 venv

Python 3.11 with a normal virtualenv is enough for local iteration. **Docker is not required** for Phase 0–3.

### Install recipe (avoiding the `vec_noise` trap)

`kaggle-environments` declares `vec_noise==1.1.4` as a hard dependency. That package (last released 2019, unmaintained) has a `setup.py` that uses the Python 2 `__builtins__.__NUMPY_SETUP__` pattern, which raises `AttributeError` on any `setuptools >= 60`. The bug is in `vec_noise`'s own source, not in our toolchain — no combination of pip/uv/setuptools flags fixes it.

`vec_noise` is only used by the Halite env (procedural ocean generation). PTCG (`cabt`) does not touch it. Skip it by installing `kaggle-environments` without dependency resolution, and then adding back only the deps `cabt` actually needs:

```bash
# Fresh venv:
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip

# Our project deps (kaggle-environments not listed here on purpose):
pip install -r requirements.txt

# Kaggle SDK, no deps (skips the broken vec_noise):
pip install --no-deps kaggle-environments

# Runtime deps that the cabt env actually needs:
pip install requests flask jsonschema

# Verify PTCG env is registered:
python -c "from kaggle_environments import make; env = make('cabt'); print(type(env))"
```

**Note on the env name:** The make key is `cabt` (matching the engine and the folder name inside `kaggle_environments/envs/`), **not** `ptcg-ai-battle` (that's the Kaggle competition URL slug).

**On `cg.api`:** Don't `import cg.api` — it doesn't exist in 1.30.2. The sample submission Kaggle provides uses that import but it's a stale template. Use the dict API instead (see "Agent Interface" above).

### Wrong-package trap: `pip install cg`

There is an unrelated package `cg` on PyPI (a clinical genomics tool) that pulls in 50+ heavy deps (SQLAlchemy, cryptography, Flask-Admin, PyMySQL, etc.). **Do not `pip install cg`.** The right `cg` is bundled with `kaggle-environments`.

If your venv was polluted by an accidental `pip install cg`, the cleanest fix is a fresh venv rather than trying to unpin the ~50 unrelated packages.

## Rules ↔ Simulator Differences

The overview flags that "there are a few differences between the official Pokémon TCG rules and the simulator behavior." Phase 0 deliverable: enumerate them in `docs/rules-summary.md` under a dedicated section, by cross-referencing the "differences" link on the competition page.

## Architecture

- `env/` — adapter over `cg.api`; exposes observations and legal actions.
- `agents/` — dispatch layer + variants (random, heuristic, ISMCTS).
- `search/` — MCTS four-phase loop with information-set-aware nodes.
- `evaluator/` — heuristic and rollout evaluators.
- `stats/` — Wilson intervals, paired bootstrap, McNemar's test.
- `scripts/` — one entry point per experiment (`exp_*.py`) + submission tooling.
- `data/kaggle/` — reference material shipped with the competition (see `data/kaggle/README.md`).

The full software-pipeline diagram lands in `docs/mdp-formalization.md` during Phase 1.

## Testing

- Unit tests live in `tests/`.
- Author runs `pytest tests/` and `ruff check .` locally — Claude Code never runs either.

## Reproducibility

Every experiment pins: git tag, RNG seed set, deck version, hardware notes. See `docs/benchmark-protocol.md`.
