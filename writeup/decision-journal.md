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
