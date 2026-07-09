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

Timing also comes from the spike: ms per decision and per full random
game. This replaces the 1–2 ms/sim guess in
`phase2-mcts-fundamentals.md` §3.2 with a measurement.

### Spike v1 verdict (2026-07): Scenario A — confirmed and better

The native lib exports a **complete search API**: `SearchBegin`,
`SearchStep`, `SearchEnd`, `SearchRelease` (plus `AgentStart`,
`AllCard`, `AllAttack` for the card database). The cabt docs
(matsuoinstitute.github.io/cabt/api.html) document the Python wrappers:

```
search_begin(agent_observation,
             your_deck, your_prize,
             opponent_deck, opponent_prize,
             opponent_hand, opponent_active,
             manual_coin=False) -> SearchState   # {observation, searchId}
search_step(search_id: int, select: list[int]) -> SearchState
search_end() -> None          # ends search, memory reused next search
search_release(search_id) -> None  # frees one specific search state
```

The design maps one-to-one onto ISMCTS: **the caller supplies the
determinization** (deck orders, prizes, opponent hand) and the engine
reconstructs a playable simulation from the current observation.
`search_release(search_id)` implies multiple concurrent search states.
`manual_coin` suggests chance outcomes can be controlled externally —
relevant for chance-node handling later.

Also confirmed in v1: two concurrent battles coexist under manual
`battle_ptr` bookkeeping, and the observation exposes per-player
`deckCount`, `handCount`, `discard`, `prize` (counts), our own `hand`,
and full board state — the inputs determinization needs.

### Remaining unknown: the native ctypes marshalling

kaggle-environments 1.30.2 ships the native symbols but **not**
`cg/api.py` (the Python wrappers above). Blind-probing `SearchBegin`
signatures risks segfaults, so we acquire the real wrapper instead.
Two acquisition paths, either suffices:

1. **Kaggle runtime (definitive).** The competition's own sample
   submission does `from cg.api import ...`, so the full package
   exists on the Kaggle image. In a Kaggle notebook attached to the
   competition run:
   ```python
   import inspect, cg.api, cg.sim
   print(inspect.getsource(cg.sim))
   print(inspect.getsource(cg.api))
   ```
   Save the outputs; we then vendor a minimal wrapper (with
   attribution note) or mirror the marshalling in our own module.
2. **Older kaggle-environments releases.** Some earlier release may
   have shipped `cg/api.py` before it was trimmed. Hunt locally:
   ```bash
   for v in 1.16.0 1.17.6 1.18.0 1.20.0 1.22.0 1.25.0 1.28.0 1.29.0 1.30.0 1.30.1; do
     pip download kaggle-environments==$v --no-deps -q -d /tmp/ke-$v 2>/dev/null \
       && unzip -l /tmp/ke-$v/*.whl 2>/dev/null | grep -q "cg/api.py" \
       && echo "FOUND in $v"
   done
   ```

Once `api.py` is in hand, `search/determinize.py` becomes: sample a
hidden assignment consistent with the observation (uniform per
ADR-001), call `search_begin`, and hand the `SearchState` to the
four-phase loop.

### Ground truth from Export.cpp (2026-07)

The competition data ships the engine's C++ source
(`ptcg_engine/ptcgProgram 22/`, LicenseRef-PTCG-ABC-Competition-Use-Only
— local reference only, never committed). `Export.cpp` gives the exact
native surface, transcribed into our own bindings at
[`env/search_engine.py`](../env/search_engine.py):

- **`AgentStart()` creates the search handle** (`apiDataType == 2`).
  Battle handles from `BattleStart` are type 1 and reject all Search*
  calls with error 30. Mystery of the extra export solved.
- **`SearchBegin(handle, blob, blobLen, myDeck*, myPrize*, enemyDeck*,
  enemyPrize*, enemyHand*, enemyActive*, manualCoin)` → JSON string.**
  `SetBattleData(handle, blob, len)` reconstructs the state from the
  `search_begin_input` blob; the arrays are then read with lengths
  taken from that state (`deckCount`, `len(prize)`, `handCount` …), so
  the caller must size them exactly — our wrapper validates against
  the observation before calling. `myDeck` is skipped during the
  deck-selection phase; `enemyActive` only read when the opponent's
  active is unrevealed. Card IDs validated against the card table
  (error 1); internal exceptions surface as error 99; wrong handle
  type as error 30.
- **`SearchStep(handle, long long searchId, select*, count)` → JSON.**
- **`SearchEnd(handle)`** ends the search and recycles memory;
  **`SearchRelease(handle, searchId)`** frees one state.
- **`AllCard()` / `AllAttack()` return `char*` JSON directly** (not
  SerialData — spike v2's probe corrected accordingly).

Remaining unknown: the exact JSON key layout of the SearchBegin/Step
payload (documented Python API wraps it as
`SearchState{observation, searchId}`). `scripts/probe_search_api.py`
confirms it empirically and also measures ms/step inside the search —
the number that actually budgets H3.

### Findings from the top public notebook (2026-07)

The most-voted public notebook on the competition confirmed everything
and added specifics:

- **`cg-lib` location.** The full `cg` package (including `api.py`,
  typed classes `Observation`/`Card`/`Pokemon`/`PlayerState`, enums
  `AreaType`/`OptionType`/`SelectContext`) ships as a Kaggle dataset
  named `cg-lib`, attached via
  `sys.path.append(glob.glob('/kaggle/input/**/cg-lib', ...)[0])`.
  The **submission runtime has `cg.api` natively** (the sample
  submission imports it), so nothing extra goes in our bundle; only
  local development needs the vendored copy.
- **`search_begin` in practice** matches the documented signature.
  Critically, **the engine does not validate the determinization
  against the true state** — the notebook fills the opponent's deck
  with Snorlax (`[1072] * deckCount`) and hand with Basic Energy and
  the search runs fine. The determinizer therefore has full freedom;
  consistency is our responsibility, not the engine's.
- **Result codes confirmed:** `-1` in progress, `0`/`1` winner index,
  `2` draw. `battle_start` deck-validation `errorType`: 1 invalid ID,
  2 >4 copies of a name, 3 no Basic Pokémon, 4 >1 Ace Spec.
- **`opponent_active`** fills unrevealed active Pokémon
  (`active[0] == None` during setup).
- **Competitive landscape.** The top public approach is an
  AlphaZero-lite: transformer policy+value net over sparse features,
  PUCT with policy priors, self-play training in-notebook,
  `SEARCH_COUNT = 10` simulations per decision, reaching ~76% vs
  random after 5 training iterations. Its determinization is crude
  (uniform `random.sample` over the full 60-card list, ignoring
  already-seen cards; dummy opponent). Two implications: (i) our
  constraint-consistent determinization is differentiated from the
  public baseline, strengthening *informed-determinization* in
  `open-ideas.md`; (ii) their 10-sims-per-decision suggests per-step
  search cost via `search_step` is non-trivial — measure before
  assuming thousands of sims fit the budget.

### Timing bug in spike v1

`current.result` is `-1` while the game is in progress (an int, not
None/"none"), so v1's termination check ended every game at step 0.
Fixed in spike v2, which also checks whether `search_begin_input`
evolves across turns, censuses result codes, and probes
`AllCard`/`AllAttack` in isolated subprocesses.

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
