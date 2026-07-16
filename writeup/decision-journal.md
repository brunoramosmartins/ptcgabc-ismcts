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

---

## Week 2 (7 Jul – 13 Jul 2026) — Phase 1

### 2026-07-01 — Phase 1 kickoff: formalization, benchmark, heuristic baseline

Closed all five Phase 1 deliverables in one sitting.

**What landed.**

- `docs/mdp-formalization.md` — formal $S$, $A(s)$, $R$, $I(s)$ with the
  two required Mermaid diagrams (logical flow + software pipeline).
- `exercises/ex01_environment.md` — the four exercises answered, feeding
  the formalization.
- `docs/benchmark-protocol.md` — finalized. N = 200 (Phase 1–4 iteration),
  N = 500 (Phase 5 hypothesis tests), K = 20, paired match seeds.
- `agents/heuristic_agent.py` — deterministic first-`maxCount` selector
  with an overridable `score` hook.
- `submissions/heuristic_main.py` — standalone Kaggle shim mirroring the
  internal heuristic. Bundle command lives in the file docstring.
- `scripts/local_ladder.py` — head-to-head runner with Wilson CI
  reporting; lazy-imports `kaggle_environments`.
- `stats/wilson.py` — closed-form Wilson interval; brought forward from
  Phase 3/5 because EXP-002a needs it now.
- Tests: `test_agents.py`, `test_wilson.py`, `test_local_ladder.py`,
  `test_heuristic_shim.py`.
- EXP-002a (local head-to-head) and EXP-002b (Kaggle ladder) registered
  in `experiments/registry.md`. Row #2 pending upload in
  `docs/submission-log.md`.
- `notes/phase1-baseline-analysis.md` with the metrics-to-hit checklist.

**Key non-trivial decisions this week.**

- **Heuristic = deterministic first-`maxCount`**, not a semantic scorer.
  Reason: minimizes coupling with the Phase 4 evaluator (ADR-003) that
  will do the real feature engineering. If EXP-002a fails to beat random
  by a CI-separated margin, the fallback is a two-line string-match
  scorer over option names — but that's a response to evidence, not the
  initial design. Cheaper to test the "engine option order is not random"
  hypothesis first with a zero-feature baseline.
- **Wilson interval implemented in Phase 1, not Phase 5.** The scaffold
  scheduled it for later, but EXP-002a needs it this week and the
  implementation is 15 lines. The Phase 5 exercise (`ex05`) still owns
  the *derivation* — we just brought the code forward.
- **Provisional N = 200 for Phase 1–4, N = 500 for Phase 5.** Justified
  by Wilson half-width table in `docs/benchmark-protocol.md`; may
  tighten once `ex05` sample-size analysis lands. Amendment policy is
  documented in the protocol itself so future changes stay traceable.
- **Match seed = agent seed** (paired seeds). Diagonalizes cross-agent
  comparisons on shared environment realizations for paired bootstrap
  variance reduction. Written into the protocol.

**Pending (still Phase 1):**

- Author runs `pytest tests/` and `ruff check .`.
- Author runs `python scripts/local_ladder.py --agent-a heuristic --agent-b random --matches 200 --seed-start 1`, back-fills EXP-002a Actual column.
- If Wilson lo > 0.5: bundle heuristic, upload to Kaggle, back-fill row #2 of `docs/submission-log.md`, tag `v0.2-baselines`.
- If Wilson lo ≤ 0.5: iterate on the heuristic (log the failure below)
  before submitting.

## Failed Attempts

_(filled if any come up during Phase 1.)_

---

## Week 3 (14 Jul – 20 Jul 2026) — Phase 2 & 3

### 2026-07-09 — H1 pre-registered and tested; the validity flag paid off

Phase 2 closed (hypotheses H1–H4 LOCKED, tag `v0.3-hypotheses`) and the
SO-ISMCTS core shipped. Then the first pre-registered hypothesis went to
test.

**Result.** EXP-003 (ISMCTS vs heuristic, N = 500 paired seeds, 1000
iterations/decision): **390W–110L, win rate 0.780, Wilson 95% CI
[0.742, 0.814]**. H1 SUPPORTED — lower bound clears 0.5 by ~24 pp.

**Why this result is trustworthy, and it nearly wasn't.** The
determinizer's fail-loud accounting plus the agent's fallback counter
(both built before the experiment) caught a real defect the pilot runs
surfaced: our determinization was systematically off by one card
whenever a Trainer was mid-resolution or our own active was face-down
during setup, and the unrevealed enemy active could be sampled as an
illegal non-Basic. Three instrumented pilots (fallbacks 29 → 15 → 0)
diagnosed and fixed all of it. Had we skipped the validity flag and run
straight to N = 500, we'd have measured an ISMCTS/heuristic hybrid and
never known — 6 hours of invalid data presented as a clean result. The
research infrastructure was not overhead; it was the difference between
a real finding and a fake one. (This is the concrete instance of the
synthesis Lessons-Learned claim that "research infrastructure is part
of the contribution.")

**What the result does NOT say.** This is a local head-to-head, not the
Kaggle ladder, and it does not explain *why* ISMCTS wins — is it the
value of search per se, the shared info-set tree specifically, or
something the heuristic simply lacks? That decomposition is the
diagnostic ladder's job (PIMC + oracle arms), next up.

**Operational note.** The run survived two mid-execution reboots
losslessly because the local ladder flushes one JSON line per match.
Resumed by pointing `--seed-start` at the next seed and merging the
parts. Also logged a personal error worth remembering: I cannot check a
WSL process's liveness with `ps` from the Windows-side shell — different
process namespaces; only the growing output file proves the run is
alive.

### 2026-07-10 — The diagnostic ladder closed; the decomposition speaks

Three 500-match runs on the same paired seeds, all with zero fallbacks:

| Rung | Win rate vs heuristic | Increment |
|---|---|---|
| Heuristic | 0.500 | — |
| PIMC (Determinized UCT) | 0.742 | **+24.2 pp — search itself** |
| SO-ISMCTS | 0.780 | +3.8 pp — info-set tree (McNemar n.s., p=0.176) |
| Oracle (true state) | 0.828 | +4.8 pp — perfect information (n.s., p=0.070) |

The story the numbers tell: **in this domain, search quality dwarfs
information quality.** Any consistent-determinization tree search
captures ~87% of the oracle's total edge over the heuristic; the
info-set-tree refinement and even perfect knowledge of hidden cards
add margins that N=500 cannot statistically resolve. Both registered
predictions from the Long reading were directionally right (the
ISMCTS-over-PIMC gap prediction exactly; the Δ_ceiling prediction
missed its 5–15 pp band by 0.2 pp on the low side).

Consequence, executed per the pre-registered gate: **belief modeling
beyond consistency is dropped for mirror play** (≤ ~5 pp total prize).
The sharper question it leaves for Phase 5: on the *ladder* the agent
runs filler determinization because the opponent's list is unknown —
and the interim ladder ratings (ISMCTS ≈ heuristic there, vs +28 pp
locally) suggest that gap is where the real recoverable value sits.
Deck/archetype *identification* — recovering consistency, not
refining beliefs — is the follow-up worth funding.

Also: watching ladder replays surfaced the mirror-only limitation of
our local experiments (opponents run diverse decks); registered as
*deck-diversity-local-pool* in open-ideas, feeding Phase 4's deck
selection.

### 2026-07-10 — Deck selection: pool-first, maximin, control included

With EXP-006 running, Phase 4's second thread started: replacing the
Phase-0 placeholder deck (ADR-002). Decisions made today:

1. **Internet meta rejected as a source.** The competition is a
   *Limited Card Battle* on a curated ~1267-card pool; public
   Standard lists assume cards this pool may not have, and card
   strength is pool-relative. Sources are the pool itself
   (`scripts/analyze_card_pool.py`) and ladder replays; the meta is
   at most archetype inspiration.
2. **Four candidates spanning the design space**, not four attempts
   at the best deck: `current-v1` (control), `v1-tuned` (same core,
   fixed ratios — isolates "archetype vs ratios"), `aggro-fire`
   (big basics, zero setup), `emboar-evolution` (Stage-2 ceiling,
   also a live probe of whether F3+search can pilot a setup deck).
3. **Selection rule pre-registered in EXP-007 before any match:**
   maximin over matchup rows (robustness against an unknown opponent
   pool beats average edge), replacement only if the winner beats
   `current-v1` with Wilson lower bound > 0.5.
4. **Ladder runner extended for asymmetric decks** — builder contract
   now passes both true lists, so determinization consistency holds
   off-mirror. This was the cheap half of *deck-diversity-local-pool*;
   the Phase-5 exploratory half (per-matchup H1 check) stays open.

### 2026-07-11 — H2 not supported; the pre-registered rule applied as written

EXP-006 (guided rollouts, N = 500 on EXP-003's seeds): 0.810 vs 0.780,
Δ = +3.0 pp, McNemar exact p = 0.279. The pre-registered criterion was
p < 0.05 — **H2 is NOT SUPPORTED**, our first null result on a locked
hypothesis. It is also the *expected* null after the diagnostic
ladder: plain ISMCTS was already within 4.8 pp of the omniscient
ceiling, so a rollout-policy change had almost no room to show a
detectable effect at this N. The honest headline stays "search
dominates; refinements are marginal here."

Two consequences decided today:

1. **EXP-007 runs with `ismcts`, not `ismcts-guided`.** The registry
   rule said "guided iff H2 holds"; it didn't. The temptation was
   real — guided is Pareto non-inferior (+3 pp point estimate) and
   ~18% faster — but editing a pre-registered decision rule after
   seeing the data is exactly the practice the registry exists to
   prevent. Recorded in the EXP-007 row before any match ran.
2. **The speed observation is promoted to the H3/time-budget thread,
   where it legitimately belongs.** Guided rollouts end games sooner
   (median 25.6 s vs 31.4 s per match at fixed 1000 iterations). H2
   tested strength at fixed *iterations*; Kaggle's regime is fixed
   *time*, where faster rollouts buy more iterations. Whether
   guided-at-time-budget beats random-at-time-budget is a different,
   testable question — it goes into the Phase 4 tuning work (#26/#27)
   rather than being smuggled into the H2 verdict.

### 2026-07-15 — Deck selected (ADR-002): the control won, on two axes

EXP-007 finished: 600 matches, 0 fallbacks, 0 draws. By the
pre-registered maximin rule, **`current-v1` (the Phase-0 sample list) is
the selected deck** — worst-case matchup 0.66 vs 0.34 / 0.09 / 0.13 for
the three designed candidates, and it dominates all of them head-to-head.
No candidate cleared the replacement gate (best challenger 34/100 vs
current-v1), so the deck is unchanged. Written up in
`docs/adr/adr-002-why-this-deck.md`.

Three things worth recording as decisions, not just results:

1. **Accepting a null-change outcome without moving the goalposts.**
   The tempting narrative for a "deck selection phase" is that it must
   *produce a new deck*. It didn't, and that is the correct result:
   the control was included precisely so the phase could conclude "the
   placeholder is actually good" with evidence. The dividend is concrete
   — because the deck is unchanged, EXP-002–006 need no re-baselining.
2. **A second, independent axis (compute cost) is allowed to reinforce,
   not launder, the decision.** `current-v1` is both the maximin winner
   *and* the cheapest to pilot (0.7 % timeout / 196 s median vs 20–24 % /
   ~530 s for the Fire decks). Under Kaggle's fixed-*time* budget the
   cost axis matters on its own, but I recorded it as *corroborating* the
   maximin choice rather than as the primary criterion — the primary
   criterion was fixed before the run and I'm not swapping it now that a
   second signal happens to agree.
3. **Timeouts logged as a finding and routed to #27, not written off.**
   The env-error rows are engine per-match TIMEOUTs (forfeit, valid),
   concentrated in the slow Fire matchups. They are the first hard
   evidence that iteration count must be *time*-calibrated so a slow
   board never forfeits — exactly the H3/time-budget question. Filed
   against #27 rather than buried in the deck verdict.

### 2026-07-16 — Submission budget locked: adaptive, not fixed (EXP-008, #27)

EXP-008 closed. The #29 submission will run `adaptive_budget=True`,
`overage_reserve=60`, `budget_moves_ahead=80`. Confirmed over 80 games
(4 opponents × 20 seeds): **0 forfeits, cumulative p99 310.7 s** against
the pre-registered 540 s gate. The risk-register row that EXP-007 had
marked *materialized* is now mitigated.

**Key non-trivial decisions.**

1. **Check the environment's real limits before designing around them.**
   The first draft registered "per-decision cost < `actTimeout` − margin"
   as a hard constraint. `actTimeout` is **0** — no per-decision cap
   exists, and a whole branch of the protocol was sizing a limit that is
   not there. The same check found `remainingOverageTime` sitting in our
   own observation, which is what made an adaptive policy possible at all.
   The check that deleted a constraint is the one that produced the answer.
2. **Adaptive (C) over fixed iterations (A), for a structural reason
   rather than a measured margin.** A and B both need $p99[M]$ — a
   prediction about a ladder field we have never seen. C reads the live
   bank and cannot deplete it by construction, so an unexpectedly long
   game costs *strength* instead of the match. This is the same shape of
   argument as ADR-002's maximin: prefer the option whose worst case is
   bounded over the one whose average is better.
3. **The fit stage's headline number was computed and then discarded.**
   $c_\text{mean} \cdot p99[M]$ says 1591 fixed iterations is "safe";
   EXP-007 had already forfeited at 1000. Multiplying a mean by a marginal
   quantile assumes independence, but a forfeit needs a long game **and**
   costly decisions *in the same game*. The regression's real value was
   making the case against fixed budgets quantitative — a registered
   negative result, not wasted work.
4. **Operating point pre-registered before the confirmation run.**
   `reserve=60`, `moves-ahead=80` went into the registry and the protocol
   note on 2026-07-15, before a single confirm game ran. It held: pooled
   max $M$ came in at 68, just under the 80. Choosing it afterwards would
   have been fitting the guard to the data it was meant to guard against.
5. **The mirror result logged as a lead, not a finding.** In the mirror
   cell both seats play `current-v1`, so the only difference is Policy C
   vs fixed 1000 iters — C wins 0.75, Wilson [0.53, 0.89]. Tempting to
   claim the adaptive budget buys strength. But $n = 20$, it was not
   pre-registered, and seat order is unbalanced, so first-player advantage
   confounds it in the same direction. Routed to #26/H3 to be tested
   properly instead of banked as a result.
6. **Accepting a policy that leaves most of the bank unspent.** Because
   `budget_moves_ahead` is constant, the divisor never shrinks: the worst
   game finished with 292 s unused and the median leaves ~80 %. That is the
   right trade before a deadline — a forfeit is a certain loss, unspent
   seconds are only foregone strength — but it is recorded as a Phase-5
   lever (a decaying estimate of *remaining* moves would spend more at the
   same safety), not as a tuning job for August.

## Failed Attempts

- **"Up to N" selects crashed EXP-007 (seed 37, current-v1 vs
  aggro-fire).** Card effects like Cyrano ("search for *up to 3*
  Pokémon ex") emit selects whose `maxCount` can exceed the options
  actually present — and `random.sample(range(n), maxCount)` raises
  `ValueError`, which the agent fallback (scoped to
  `SearchApiError`/`DeterminizationError`) did not catch; the env
  scored the side as errored (`reward=None`) and the runner, not
  expecting that, died mid-round-robin. 1,500+ mirror matches on the
  placeholder deck never hit this because that deck rarely thins its
  ex count below 3 — the bug was *deck-dependent*, which is exactly
  why the candidate pool exists. Fixed with `min(maxCount, n)` clamps
  at every choice site (enumerate_moves, both rollouts, RandomAgent,
  agent fallbacks), `env_error` rows instead of runner death, and
  true resume (`--append`) in the runner. Root cause confirmed by
  rerunning seed 37 under identical RNG: completes cleanly with the
  clamps, crashed without. Also exposed: the wall-clock estimate for
  asymmetric matchups was ~6× optimistic (median 106–258 s/match vs
  ~30 s mirror — longer games, more decisions per game).
- **v1-tuned's "obvious" fixes backfired (final EXP-007: 34/100 vs
  current-v1).** Cutting energy 35→27 to add trainers weakened
  exactly what makes the sample deck work: Hammer-lanche's damage
  scales with deck energy *density* (discard 6 from top, 100× per
  {W} found). The sample deck is better designed than it looks;
  candidate design must respect a deck's scaling engine, not generic
  deckbuilding lore.
- **Determinizer off-by-one (contextCard / limbo cards).** First fix
  swept the whole `select` subtree, which over-corrected by
  double-counting `select.deck` (deck-browse effects). Narrowed to
  `select.contextCard` only, plus a `POOL_SLACK = 2` tolerance for
  genuinely unidentifiable limbo cards (our face-down setup active; a
  Trainer mid-resolution). Fixed across pilots v1–v4.
- **Illegal enemy active (SearchBegin error 2).** The unrevealed
  opponent active was sampled uniformly and could land on an
  Energy/Trainer — an invalid board state the engine rejected. Fixed by
  filtering that slot to Basic Pokémon via the engine's `AllCard`
  database.
- **ISMCTS submission failed validation — `__file__` undefined, and a
  validation test that was theatre.** The Kaggle worker runs `main.py`
  via `exec(code, env)`, where `__file__` is not defined; the shim's
  `sys.path` bootstrap used `os.path.abspath(__file__)` and crashed at
  import, before any decision. Two submission slots burned before we
  read the agent logs. Worse: the local bundle validator I wrote to
  prevent exactly this missed it, because it loaded the agent via
  `import main` (where `__file__` *is* defined) instead of by path
  (which makes kaggle-environments `exec` it, as the worker does). Lesson,
  now baked into `validate_bundle.py`'s docstring: **a validation
  harness that doesn't load the artifact the way production loads it is
  theatre.** Fix: guard the `__file__` use with try/except (fall back to
  `/kaggle_simulations/agent` + CWD); validator now loads by path and
  reproduces the exec. Timing was never the problem — self-play is ~45 s
  local, worker banks 600 s overage/agent/episode.
- **EXP-008's timing wrapper was a callable class — one full collection
  run lost, and the check that should have caught it reported success.**
  `_TimedSeat` implemented `__call__`; `kaggle_environments` introspects
  agents with `inspect.getfullargspec`, which raises `TypeError` on class
  instances, so both seats errored before taking a single decision. All 76
  fit games and 30 confirm games came back `status=ERROR`, `M=0`,
  `my_final_overage=None`. The output looked plausible — the only tell was
  a per-decision median of 0.000 s. What let it survive was the same
  disease as the `__file__` incident above, in a new organ: the forfeit
  check searched for `TIMEOUT` while the status was `ERROR`, so it printed
  **"forfeits 0/30" — a false pass**. A check that cannot distinguish
  *passed* from *never ran* is not a check. Compounding it, `run_cell`
  resumes by counting lines, so the poisoned files would have been skipped
  as "complete" forever; they had to be deleted by hand. Fixed with a plain
  closure, a regression test that runs `getfullargspec` on the wrapper
  (`tests/test_exp_timing.py`), and an integrity guard in
  `analyze_exp008_confirm.py` that fails loudly on any non-outcome status
  before it evaluates a single gate. `local_ladder.py` was never affected —
  it already returned a closure, which is why 1,500+ prior matches ran
  clean and gave no warning.
- **Reading a tail from the first four lines of a running log.** An early
  read of the confirm output put budget utilization at ~19 % and prompted a
  "we're leaving strength on the table" claim. Over all 80 games the worst
  case is 58 %. The four visible lines were one opponent's fast seeds; the
  expensive matchup (aggro-fire, $M$ up to 68) had not printed yet. Same
  error as the fit stage's reassuring 0/76 forfeits — a tail statistic read
  off a sample that structurally cannot contain the tail.
