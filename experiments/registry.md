# Experiment Registry

Every experiment MUST be registered here BEFORE running. One row per experiment.

## Schema

| Field | Meaning |
|---|---|
| ID | `EXP-XXX` (zero-padded, monotonically increasing) |
| Phase | Which roadmap phase requested it |
| Hypothesis | H1 / H2 / H3 / H4 / exploratory / variance |
| Objective | One sentence — what question does it answer? |
| Configuration | Agents, seeds, N matches, deck version, git tag |
| Expected result | What outcome would confirm/reject the hypothesis? |
| Actual result | Filled in after the run — Wilson CI, p-value, verdict |

## Ledger

| ID | Phase | Hypothesis | Objective | Configuration | Expected | Actual |
|---|---|---|---|---|---|---|
| EXP-001 | 0 | baseline | Establish the Kaggle-ladder floor and validate the end-to-end submission pipeline (bundle → upload → Validation Episode → rating). | Agent: `RandomAgent` (uniform over `obs["select"]["option"]`, `maxCount` draws). Deck: `decks/selected/deck.csv` (Phase 0 placeholder — Kaggle sample deck). Git tag at submission: `v0.1-setup`. Seeds: RNG in `main.py` unseeded (Kaggle worker RNG). N matches: as awarded by the ladder scheduler. Hardware: Kaggle sandbox (2 vCPU, 12.2 GiB). | Rating stabilizes below the heuristic baseline that arrives in Phase 1 (EXP-002). Concrete Phase 0 target: `Validation Episode` passes; ladder rating settles in the µ₀ = 600 neighborhood within the first week — no strong prior on the exact number. | Validation Episode: **Complete** (2026-07-01, ~27 min after upload). Post-validation rating: **600.0** — unchanged from Kaggle's initial μ₀ (agent-vs-self validation does not move rating). Pipeline end-to-end verified; real ladder matches pending scheduler. Full rating stabilization tracked in `docs/submission-log.md` row #1. |
