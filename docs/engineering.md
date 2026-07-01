# Engineering

Architecture, testing, CI, and reproducibility notes. Companion to `docs/research.md`.

## Competition SDK

The simulator engine is called **`cabt`** (per the Simulation Category overview: "Battles are run on the cabt Engine"). API docs live at **<https://matsuoinstitute.github.io/cabt/>**.

The engine name and the Python import namespace are not the same — the Kaggle-provided template imports from `cg.api`:

```python
from cg.api import Observation, to_observation_class
```

Same pattern as `scikit-learn` (pip) → `import sklearn`. The pip install spec is still to be confirmed by inspecting the Kaggle Docker image (see below). Track this in Phase 0 alongside Issue #1.

The overview references `kaggle-environments == 1.14.10`, but that version is not on PyPI (release list jumps from 1.14.9 to 1.14.11 — presumably yanked). We pin **`1.14.11`** as the closest stable release. See <https://github.com/Kaggle/kaggle-environments> for the reference implementation.

## Agent Interface

The Kaggle entry point is a top-level `agent(obs_dict: dict) -> list[int]` function, not a class method. Conventions:

- The observation exposes public game state, a log, and a list of legal options.
- On the very first call `obs.select is None` — the agent returns the 60 card IDs of its deck (the initial "deck submission").
- On subsequent calls the agent returns a list of integer indices into `obs.select.option`.
- The returned list length is in `[obs.select.minCount, obs.select.maxCount]`, no duplicates.
- The engine only ever presents legal options — no need to filter.

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

The "Docker Image" link on the Simulation overview points to the **generic** [`kaggle-environments` Dockerfile](https://github.com/Kaggle/kaggle-environments/blob/master/docker/Dockerfile) — the same image used by every Kaggle env, not something PTCG-specific. It tells us:

- Base image: `gcr.io/kaggle-images/python:v163`
- Node.js 22 available
- `kaggle-environments` installed from source via `uv pip install --system .`

The engine `cg`/`cabt` is **not visible in the Dockerfile** — it is either bundled as an env plugin inside `kaggle-environments` 1.14.10 or auto-installed at first invocation. To confirm locally:

```bash
pip install kaggle-environments==1.14.11
python -c "from kaggle_environments import make; env = make('ptcg-ai-battle'); print(type(env))"
python -c "from cg.api import Observation, to_observation_class; print('cg.api OK')"
```

If both `make(...)` and `from cg.api import ...` succeed, we're set — no separate SDK install is needed. Otherwise, cross-check with <https://matsuoinstitute.github.io/cabt/> for the actual install path.

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
