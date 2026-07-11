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

## Failed Attempts

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
