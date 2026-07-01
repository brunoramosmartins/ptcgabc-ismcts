# Kaggle Submission Log

Every submission MUST be logged here BEFORE upload.

**Ladder mechanics (Simulation Category):**
- Every new submission starts at $\mu_0 = 600$ (TrueSkill-style Gaussian).
- **Only the 2 most recent submissions per team are active** in the matchmaking pool — older submissions still exist but no longer play new episodes.
- A **Validation Episode** (agent vs. copies of itself) runs before the submission enters the pool. Log the outcome under `Validation`.
- Only the best-scoring active submission shows on the leaderboard.
- Daily submission cap: 5.

Fill in `Actual rating` once the rating stabilizes (usually a few days after upload).

| # | Date | Git tag | Commit | Agent variant | Deck version | Key params | Active? | Validation | Expected effect | Actual rating |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-07-01 | v0.1-setup | a47e97c | RandomAgent (top-level `main.py` shim, uniform over `obs["select"]["option"]`) | Phase 0 placeholder (`decks/selected/deck.csv`, copy of Kaggle sample) | RNG unseeded on worker | Yes | Complete (passed) | Establishes the ladder floor and validates the bundle → Validation Episode → rating pipeline (EXP-001). No prior on the exact rating; expected in the µ₀ = 600 neighborhood. | 600.0 (initial μ₀; unmoved by Validation Episode — real matches pending) |
| 2 | _pending upload_ | v0.2-baselines | _pending_ | HeuristicAgent (`submissions/heuristic_main.py` — first-`maxCount` deterministic selector) | Phase 0 placeholder (unchanged from row #1) | Deterministic; no RNG | _pending_ | _pending_ | Beats the random baseline on the ladder (EXP-002b). Directional — no pre-registered threshold; the target is a stabilized rating strictly above EXP-001's. | _pending_ |
