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
| 1 | 2026-07-01 | v0.1-setup | a47e97c | RandomAgent (top-level `main.py` shim, uniform over `obs["select"]["option"]`) | Phase 0 placeholder (`decks/selected/deck.csv`, copy of Kaggle sample) | RNG unseeded on worker | No (superseded by row #2 in the 2-active slot pool) | Complete (passed) | Establishes the ladder floor and validates the bundle → Validation Episode → rating pipeline (EXP-001). No prior on the exact rating; expected in the µ₀ = 600 neighborhood. | **364.6** (stabilized public score after ~4 days on ladder; drifted −235 from μ₀ = 600). This is the ladder floor to beat. |
| 2 | 2026-07-01 | v0.2-baselines | _pending merge_ | HeuristicAgent (`submissions/heuristic_main.py` — first-`maxCount` deterministic selector) | Phase 0 placeholder (unchanged from row #1) | Deterministic; no RNG | Yes | Complete (passed) | Beats the random baseline on the ladder (EXP-002b). Directional — no pre-registered threshold; the target is a stabilized rating strictly above EXP-001's 364.6. | **527.9** (stabilized public score after ~4 days on ladder; +163.3 above random, ≈75 below μ₀ = 600). Confirms local head-to-head result (75.5% win rate vs random, EXP-002a). |
