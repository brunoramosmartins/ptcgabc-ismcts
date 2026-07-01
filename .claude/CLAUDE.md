# Project Rules — PTCG ABC ISMCTS Agent (v2)

## What This Project Is

A Kaggle competition entry for the Pokémon TCG AI Battle Challenge, entering
both Simulation and Strategy categories. Approach: Information-Set MCTS with
a hand-crafted heuristic evaluator on a fixed meta deck. Goal is portfolio
and learning — NOT top-8. Framed as an investigation of a research question
(see docs/research.md) via four pre-registered hypotheses. Deadlines are hard
(Aug 16-17 for Simulation, Sep 13 for Strategy) and drive everything.

## Development Rules

### Git & GitHub — CRITICAL RULES

1. NEVER commit directly. Present the commit message and changed files
   in chat for author validation.
2. NEVER create branches. Author creates all branches manually.
3. NEVER create PRs automatically. Present PR details in chat.
4. NEVER push to any branch.
5. Follow Conventional Commits.

### Testing & Linting — CRITICAL

- Create tests in `tests/` but NEVER run them.
- NEVER run `ruff`.
- After creating tests, say: "Tests created. Please run `pytest tests/` and
  `ruff check .` and share any failures."

### Code Style

- Python 3.10+ syntax
- Type hints on all function signatures
- Google-style docstrings on public functions
- numpy-style docstrings for mathematical functions

### Mathematical Content

- All derivations step-by-step with no skipped algebra
- LaTeX-compatible: $$...$$ for display, $...$ for inline
- Every algorithm: pseudocode → complexity analysis → implementation
- Exercises go in `exercises/`, one file per substantive phase

### Research Hygiene (new in v2)

- Every experiment MUST be registered in `experiments/registry.md` BEFORE
  running. The registry entry includes: ID, objective, hypothesis tested
  (if applicable), configuration, expected result.
- Every Kaggle submission MUST be logged in `docs/submission-log.md`
  BEFORE upload. The log entry includes: submission number, git tag,
  commit hash, agent variant, deck version, key parameters, expected
  effect, actual rating (filled in later).
- Every phase note file MUST end with two sections:
  ## Lessons Learned
  ## Failed Attempts
  These sections feed the writeup and the "Threats to Validity" section
  directly.

### Writeup and TIL Content

- The Strategy writeup lives in `writeup/writeup.md`, max 2000 words.
- Every non-trivial decision is logged in `writeup/decision-journal.md`
  the day it is made, never reconstructed later.
- Weekly, add a `## Failed Attempts` section to the decision journal
  entry — this is where experiments that did not work are captured.
- TIL drafts live in `tils/`. Format is Hook / Insight / Example / Takeaway.

### Statistical Reporting

- Win rates: always report with Wilson 95% confidence interval, not the
  bare proportion.
- Agent comparisons on shared match sets: use paired bootstrap or paired
  sign test (McNemar's).
- Multiple comparisons (e.g., per-feature ablation): report both raw
  and Bonferroni-corrected p-values.
- Every claim in the writeup that involves a comparison must reference
  a specific statistical result from `experiments/registry.md`.
