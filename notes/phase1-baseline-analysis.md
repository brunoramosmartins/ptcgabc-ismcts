# Phase 1 — Baseline Analysis

Working notes for the environment formalization + heuristic baseline
work. Living document during the week; ends with `## Lessons Learned`
and `## Failed Attempts` sections that get frozen at merge time.

## Scope of Phase 1

Five deliverables land this week:

1. [`docs/mdp-formalization.md`](../docs/mdp-formalization.md) — formal
   $S$, $A(s)$, $R$, $I(s)$ with the two diagrams.
2. [`docs/benchmark-protocol.md`](../docs/benchmark-protocol.md) —
   finalized (no TBDs).
3. [`agents/heuristic_agent.py`](../agents/heuristic_agent.py) +
   [`scripts/local_ladder.py`](../scripts/local_ladder.py) + tests.
4. EXP-002a (local) and EXP-002b (Kaggle) registered.
5. Heuristic submission logged and prepared for `v0.2-baselines`.

## Design decisions

### Heuristic as "first-`maxCount` deterministic selector"

Zero card semantics. Two arguments for taking the simplest thing that
could beat random:

1. **The `cabt` engine's option ordering is unknown-but-not-random.**
   Even a weak correlation between "option index 0" and "the sensible
   play" flips the sign of the win-rate delta vs uniform sampling.
   Deterministic first-index picking captures this cheaply.
2. **Phase 4's evaluator (ADR-003) is the real heuristic.** Anything
   more clever in Phase 1 introduces a scoring function that we would
   then need to compare against the Phase 4 replacement (EXP-004 vs
   EXP-002), doubling the design space we care about. Better to keep
   Phase 1 boring and let Phase 4 be where the interesting evaluator
   design lives.

If EXP-002a fails to beat random by a CI-separated margin, the fallback
is a two-line "prefer options with `damage` in their string repr"
scorer — but that's a *response* to evidence, not the initial design.

### `local_ladder.py` runs single-process, deterministic seeds

Concurrency multiplies the variables at stake (CPU budget per decision,
env-RNG interleaving) without buying anything for Phase 1 iteration.
The benchmark protocol lets any future experiment opt into parallel
execution *if* it records that concurrency was used.

### `stats/wilson.py` implemented now, not Phase 5

The scaffold documented Wilson as "Phase 3/5" but EXP-002a needs it
this week. The implementation is 15 lines of the standard closed form;
`exercises/ex05_statistical_inference.md` (Phase 5) will still be the
derivation reference. Bringing the code forward has zero cost.

## Open questions for Phase 2/3

- How much of `obs["current"]` and `obs["logs"]` is stable across
  matches — worth encoding into `env/observation.py`? Answer requires
  running one match with `local_ladder.py` and inspecting the dict.
- Do all option lists have `maxCount == 1`? If yes, most of the
  "select multiple" logic in `HeuristicAgent.choose` is dead code we
  can simplify. Same empirical question.

Both are Phase 2/3 blockers, not Phase 1.

## Metrics to hit before merging

- [x] `pytest tests/` — all 34 tests passing after the `_heuristic_factory`
      signature fix and the `wilson.py` raw-docstring fix.
- [ ] `ruff check .`.
- [x] `python scripts/local_ladder.py --agent-a heuristic --agent-b random --matches 200 --seed-start 1` — Wilson lo = 0.691 > 0.5.
- [x] EXP-002a Actual column back-filled with the reported numbers.
- [ ] Bundle heuristic (`submissions/heuristic_main.py`) uploaded to
      Kaggle; row #2 of `docs/submission-log.md` back-filled;
      `v0.2-baselines` tagged on the merge commit.

## Lessons Learned

- **The `cabt` engine's option ordering is informative.** EXP-002a: the
  first-`maxCount` deterministic selector wins 75.5% vs uniform random
  (Wilson 95% CI [0.691, 0.809], N = 200). No hand-crafted card
  semantics needed. Implication: any future scorer must clear this bar,
  and the Phase 4 evaluator (ADR-003) is the natural place to try. If
  Phase 4 features cannot separate CI from 0.755, they are not worth the
  complexity.
- **Zero draws in 200 matches.** The engine resolves this deck/ruleset
  to a decisive outcome. Simplifies Phase 5 paired testing (McNemar
  reduces to paired sign; paired bootstrap is unaffected but the
  variance is lower than draws-allowed assumptions predict).
- **`kaggle_environments` prints "Loading environment X failed" for
  optional plugins** (werewolf, open_spiel_env) whose deps are not
  installed. Cosmetic; `cabt` loads cleanly. Not worth suppressing.
- **Wilson brought forward from Phase 5 was the right call.** Cost:
  15 lines. Value: EXP-002a produced a defensible CI in one command.
  Don't wait to implement the reporting when a Phase 1 test needs it.

## Failed Attempts

_None during Phase 1. Track here if the Kaggle Validation Episode
rejects the heuristic bundle or the ladder rating unexpectedly sits at
or below EXP-001._
