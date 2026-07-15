# Risk Register

**Status:** initial (Phase 0). Grows as risks materialize.

| Risk | Likelihood | Impact | Mitigation | Status |
|---|---|---|---|---|
| SDK access delay past Week 1 | Low | Blocks everything | Verify Day 1 of Phase 0; pull the Kaggle Docker image | open |
| Per-match 10-min budget binds ISMCTS below useful sim count | Medium | Reduces H3 signal; **materialized** — EXP-007 forfeited 11–24% vs grindy fields, even current-v1 p90 617 s | EXP-008 (#27): calibrate budget policy (fixed iters vs per-move anytime cap), `notes/phase4-time-budget-calibration.md` | in progress |
| Pre-registered hypothesis rejected close to Sep 13 | Medium | Writeup scramble | Report null findings as findings | open |
| Statistical machinery overengineered vs sample size | Medium | Time drain | `ex05` sample-size analysis first | open |
| Only 2 most recent submissions are active on the ladder | Medium | A broken upload burns an active slot | Always run `main.py` in the Docker image before uploading; Validation Episode is not the first line of defense | open |
| Simulator ≠ official PTCG rules in some behaviors | Medium | Agent learns wrong dynamics | Enumerate differences in `docs/rules-summary.md` during Phase 0 (cross-ref "differences" link on the comp page) | open |
| Entry deadline (Aug 9) missed for either competition | Low | Cannot submit at all | Accept competition rules for both comps by Phase 0 end | open |
| pip install spec for `cg` / `cabt` unresolved | Medium | Blocks local iteration | Inspect Kaggle Docker image; check the `cabt` GitHub Pages docs | open |
