# Phase 3 — Implementation Plan (ISMCTS Core)

Working note for Phase 3 (Issues #16–#22, tag `v0.4-ismcts-core`).
Started while Phase 2's final items (synthesis answers, H1–H4 lock)
mature — see the pre-registration guardrail below for why this is
safe.

## Pre-registration guardrail

Phase 2's lock (`v0.3-hypotheses`) must land **before EXP-003 runs**,
not before Phase 3 code is written. Implementing `search/`, tests, and
the feasibility spike does not test H1. The binding rule until the
lock:

- **Allowed:** writing search/agent code, unit tests, smoke tests
  ("plays one full match without error"), engine timing measurements.
- **Not allowed:** accumulating ISMCTS-vs-heuristic win rates under
  the benchmark protocol, or any result that could tempt a
  hypothesis rewrite. If a smoke test happens to produce outcomes,
  they are not recorded anywhere.

## The critical unknown: how do we simulate inside the search?

ISMCTS needs a forward model: given a determinized state, play
simulated actions to a terminal outcome. Inspection of the bundled
engine (`kaggle_environments/envs/cabt/cg/`) found:

- `game.battle_start(deck0, deck1)` / `battle_select(indices)` /
  `battle_finish()` — a full step API over a native library, so local
  simulation is possible in principle.
- The native functions take an explicit `battle_ptr`, so **multiple
  concurrent battles look feasible** with manual pointer bookkeeping
  (the `Battle` class's global pointer is just a convenience).
- Every observation carries **`obs["search_begin_input"]`** — a
  serialized blob the Kaggle interpreter explicitly forwards to the
  agent at each decision. The name strongly suggests an
  organizer-provided hook for reconstructing a battle mid-game to
  search from. No wrapper in `game.py` consumes it; the question is
  whether the native library exports an entry point that does.

Three scenarios, decided by `scripts/explore_cg_api.py` (the spike):

| Scenario | Meaning | Phase 3 shape |
|---|---|---|
| A. A native export consumes `search_begin_input` | Engine-native mid-game reconstruction (possibly with built-in determinization) | Determinize + simulate via engine; `search/determinize.py` is a thin wrapper |
| B. No such export, but concurrent battles work | Rollouts must replay from turn 1 or approximate | Slower sims; budget math changes; determinization is ours to build |
| C. Neither | No usable forward model | Redesign discussion — flag immediately |

Timing also comes from the spike (section 4): ms per decision and per
full random game. This replaces the 1–2 ms/sim guess in
`phase2-mcts-fundamentals.md` §3.2 with a measurement.

## Order of work

1. **Spike** — author runs `python scripts/explore_cg_api.py`, pastes
   output. Everything downstream branches on the scenario. ✅ script
   written.
2. **`search/node.py`** — info-set node with visits / total reward /
   availability counts (subset-armed bandit, Cowling §4.1). ✅ written,
   tests in `tests/test_search.py`.
3. **`search/ucb.py`** — UCB1 with availability counts. ✅ written,
   tested.
4. **`search/determinize.py`** — shape depends on the spike.
5. **Four-phase loop + `agents/ismcts_agent.py`** — wiring; action
   keying by canonical option content (indices are not stable across
   determinizations).
6. **Smoke test** — one full match vs heuristic without error
   (Issue #19 DoD). No win-rate bookkeeping.
7. — **Phase 2 lock happens here at the latest** (`v0.3-hypotheses`) —
8. **EXP-003 registration** (Issue #20), then the **H1 run**
   (Issue #21) under the benchmark protocol.
9. **Diagnostic ladder** — PIMC + Cheating UCT arms on the same seeds
   (see `open-ideas.md`: *pimc-baseline-determinized-uct*,
   *oracle-baseline-cheating-uct*). Gates the Phase 5 belief work.
10. **Ladder submission** (Issue #22), tag `v0.4-ismcts-core`.

## Design decisions already fixed by ADRs

- SO-ISMCTS variant (ADR-001); uniform determinization in the
  baseline; random rollout policy (heuristic arrives in Phase 4 as
  H2's treatment arm).
- Terminal-only reward $r_T \in \{-1, 0, +1\}$, sample-average backup
  (ADR-004).
- Root action selection by max visit count (Cowling's convention).

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled as they occur.)_
