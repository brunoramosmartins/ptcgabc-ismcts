# Decision Journal

Every non-trivial decision logged the day it is made. Never reconstructed later.

Weekly, add a `## Failed Attempts` section under the current week's heading.

---

## Week 1 (30 Jun – 6 Jul 2026) — Phase 0

### 2026-07-01 — Phase 0 kickoff: docs, ADRs, and the random-agent pipeline

Scope closed on Phase 0 issues #2, #4, and #5 in one sitting (issues #1 and
#3 were already done by prior work — SDK recipe in `docs/engineering.md`
and the repo scaffold).

**What landed.**

- ADRs 001, 003, 004 drafted with all four sections and literature refs.
  ADR-002 stays deferred to Phase 4 per the roadmap.
- `docs/game-primer.md` written as an author-facing narrative.
- `docs/rules-summary.md` written as the terse reference, with a
  "Simulator vs. Official Rules" section seeded with three confirmed
  divergences and four to-enumerate items for Phase 1.
- Top-level `main.py` created — Kaggle-facing shim that mirrors our
  internal `RandomAgent`, self-contained so the bundle is just
  `main.py` + `deck.csv`.
- `scripts/submit.py` implemented — validates the entry point + deck
  and produces a flat `.tar.gz`. Tests in `tests/test_submit.py` and
  `tests/test_main_shim.py`.
- Placeholder `decks/selected/deck.csv` seeded from
  `data/kaggle/sample_submission/deck.csv`, with `rationale.md` noting
  that Phase 4 replaces it.
- EXP-001 registered in `experiments/registry.md`; first row in
  `docs/submission-log.md` populated with the pending upload.

**Key non-trivial decisions this week.**

- **Keep `main.py` self-contained** rather than importing our internal
  `agents/` package. Reason: the submission bundle stays 2 files, no
  Python-path gymnastics on the Kaggle worker, and the shim never needs
  to change when we swap agents — every new agent variant becomes a new
  standalone `main.py` for its submission. Trade-off is minor code
  duplication between `main.py` and `agents/random_agent.py`; accepted.
- **Ship a placeholder deck** rather than block EXP-001 on Phase 4 deck
  selection. Reason: EXP-001 exists to validate the pipeline, not the
  deck. The random agent's rating is not meaningfully sensitive to deck
  choice — the point is that the bundle uploads and a Validation Episode
  passes. Explicitly documented in `decks/selected/rationale.md`.
- **Terminal-only reward** locked in ADR-004 before any ISMCTS code
  lands. Reason: keeps H1–H4 comparisons on the same $\{-1, 0, +1\}$
  scale the ladder scores us on, and prevents a shaped-return regime
  from silently biasing Phase 3 results.

**Pending (still Phase 0):**

- Author runs `pytest tests/` and `ruff check .` on the new tests.
- Author runs `python scripts/submit.py`, uploads the archive to
  Kaggle, tags `v0.1-setup`, and back-fills the commit hash + actual
  rating in `docs/submission-log.md`.

## Failed Attempts

_None this week — the Phase 0 issues were mechanical. Track here if the
Kaggle Validation Episode rejects the bundle._

---

## Week 2 (7 Jul – 13 Jul 2026) — Phase 1

### 2026-07-01 — Phase 1 kickoff: formalization, benchmark, heuristic baseline

Closed all five Phase 1 deliverables in one sitting.

**What landed.**

- `docs/mdp-formalization.md` — formal $S$, $A(s)$, $R$, $I(s)$ with the
  two required Mermaid diagrams (logical flow + software pipeline).
- `exercises/ex01_environment.md` — the four exercises answered, feeding
  the formalization.
- `docs/benchmark-protocol.md` — finalized. N = 200 (Phase 1–4 iteration),
  N = 500 (Phase 5 hypothesis tests), K = 20, paired match seeds.
- `agents/heuristic_agent.py` — deterministic first-`maxCount` selector
  with an overridable `score` hook.
- `submissions/heuristic_main.py` — standalone Kaggle shim mirroring the
  internal heuristic. Bundle command lives in the file docstring.
- `scripts/local_ladder.py` — head-to-head runner with Wilson CI
  reporting; lazy-imports `kaggle_environments`.
- `stats/wilson.py` — closed-form Wilson interval; brought forward from
  Phase 3/5 because EXP-002a needs it now.
- Tests: `test_agents.py`, `test_wilson.py`, `test_local_ladder.py`,
  `test_heuristic_shim.py`.
- EXP-002a (local head-to-head) and EXP-002b (Kaggle ladder) registered
  in `experiments/registry.md`. Row #2 pending upload in
  `docs/submission-log.md`.
- `notes/phase1-baseline-analysis.md` with the metrics-to-hit checklist.

**Key non-trivial decisions this week.**

- **Heuristic = deterministic first-`maxCount`**, not a semantic scorer.
  Reason: minimizes coupling with the Phase 4 evaluator (ADR-003) that
  will do the real feature engineering. If EXP-002a fails to beat random
  by a CI-separated margin, the fallback is a two-line string-match
  scorer over option names — but that's a response to evidence, not the
  initial design. Cheaper to test the "engine option order is not random"
  hypothesis first with a zero-feature baseline.
- **Wilson interval implemented in Phase 1, not Phase 5.** The scaffold
  scheduled it for later, but EXP-002a needs it this week and the
  implementation is 15 lines. The Phase 5 exercise (`ex05`) still owns
  the *derivation* — we just brought the code forward.
- **Provisional N = 200 for Phase 1–4, N = 500 for Phase 5.** Justified
  by Wilson half-width table in `docs/benchmark-protocol.md`; may
  tighten once `ex05` sample-size analysis lands. Amendment policy is
  documented in the protocol itself so future changes stay traceable.
- **Match seed = agent seed** (paired seeds). Diagonalizes cross-agent
  comparisons on shared environment realizations for paired bootstrap
  variance reduction. Written into the protocol.

**Pending (still Phase 1):**

- Author runs `pytest tests/` and `ruff check .`.
- Author runs `python scripts/local_ladder.py --agent-a heuristic --agent-b random --matches 200 --seed-start 1`, back-fills EXP-002a Actual column.
- If Wilson lo > 0.5: bundle heuristic, upload to Kaggle, back-fill row #2 of `docs/submission-log.md`, tag `v0.2-baselines`.
- If Wilson lo ≤ 0.5: iterate on the heuristic (log the failure below)
  before submitting.

## Failed Attempts

_(filled if any come up during Phase 1.)_
