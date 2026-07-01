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
| EXP-001 | 0 | baseline | Establish the Kaggle-ladder floor and validate the end-to-end submission pipeline (bundle → upload → Validation Episode → rating). | Agent: `RandomAgent` (uniform over `obs["select"]["option"]`, `maxCount` draws). Deck: `decks/selected/deck.csv` (Phase 0 placeholder — Kaggle sample deck). Git tag at submission: `v0.1-setup`. Seeds: RNG in `main.py` unseeded (Kaggle worker RNG). N matches: as awarded by the ladder scheduler. Hardware: Kaggle sandbox (2 vCPU, 12.2 GiB). | Rating stabilizes below the heuristic baseline that arrives in Phase 1 (EXP-002). Concrete Phase 0 target: `Validation Episode` passes; ladder rating settles in the µ₀ = 600 neighborhood within the first week — no strong prior on the exact number. | Validation Episode: **Complete** (2026-07-01, ~27 min after upload). Post-validation rating: 600.0 → **373.7** (public score after ~3h of real ladder matches; drift of −226 from μ₀). This is the ladder floor every subsequent submission must beat. Pipeline verified end-to-end. Full trace in `docs/submission-log.md` row #1. |
| EXP-002a | 1 | baseline | Local head-to-head: does the deterministic HeuristicAgent (first-`maxCount` selector) beat RandomAgent by a Wilson-CI-separated margin under the benchmark protocol? | Agents: `HeuristicAgent` (A) vs `RandomAgent` (B). Deck: `decks/selected/deck.csv` (Phase 0 placeholder). N = 200 matches, K = 1 replication (Phase 1 quick-iteration budget per `docs/benchmark-protocol.md`). Match seeds 1..200; agent seed = match seed. Deterministic engine seeding via `configuration={"randomSeed": seed}`. Hardware: local WSL2 (see `docs/engineering.md`). Runner: `scripts/local_ladder.py --agent-a heuristic --agent-b random --matches 200 --seed-start 1`. | Heuristic win rate above 0.5 with Wilson 95% CI strictly above 0.5 (i.e., lower endpoint > 0.5). If the CI covers 0.5, the DoD for Issue #8 is not met and we iterate on the heuristic before submission. | **DoD met.** N = 200. Wins / Draws / Losses = **151 / 0 / 49**. Win rate $\hat p$ = **0.755**. Wilson 95% CI = **[0.691, 0.809]** — lower endpoint 19.1 pp above 0.5. Zero draws: the `cabt` engine resolves this deck/ruleset to a decisive outcome. Interpretation: the engine's option ordering is not random — index 0 is systematically stronger — so a deterministic first-`maxCount` selector already dominates uniform sampling by a wide margin. Log: `results/heuristic_vs_random.jsonl`. Run date: 2026-07-01. |
| EXP-002b | 1 | baseline | Kaggle ladder: does the heuristic reach a higher stabilized TrueSkill rating than the random submission (EXP-001)? | Agent: heuristic shim (`submissions/heuristic_main.py`). Deck: `decks/selected/deck.csv` (unchanged from EXP-001). Git tag at submission: `v0.2-baselines`. Bundle via `python scripts/submit.py --main submissions/heuristic_main.py --out submission-heuristic.tar.gz`. | Stabilized rating > 600.0 (EXP-001 μ₀) by a margin that exceeds the ladder's per-match noise. No pre-registered threshold — this is directional. | _pending — filled once ladder rating stabilizes; see `docs/submission-log.md` row #2._ |
