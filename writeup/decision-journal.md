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

### 2026-07-16 — The ladder disagrees with the benchmark, and it is not noise

Submitted the adaptive-budget agent (row #4, Validation passed). Then the
ladder numbers landed and reframed the phase.

**The finding.** Measured simultaneously today: heuristic **497.8**, our
ISMCTS **475.4** — the heuristic leads by 22.4. Every prior simultaneous
read agrees (536.0 vs 522.3 at the last one). Three reads, one direction.
Our ISMCTS loses to our own heuristic baseline on the ladder while beating
it 78 % locally (EXP-003, H1 supported, Wilson [0.742, 0.814], n = 500).

**H1 is not refuted, and saying so would be sloppy.** H1 was stated and
tested under a mirror-deck condition, and it holds there. What we have is a
**construct-validity gap**: the local benchmark grants the agent the
opponent's list, and the deployment environment does not. The benchmark
measures a quantity the ladder never pays for. That belongs in Threats to
Validity as a first-class item, not as a caveat.

**The mechanism was already registered, which is the encouraging part.**
On the ladder, hidden zones are filled with `FILLER_CARD`, so the search
plans deep inside a counterfactual board — and depth against a wrong model
is not neutral, it is confidently wrong. EXP-004 found search itself
carries the value (+24 pp) while the info-set tree adds little (+3.8 pp,
n.s.); EXP-005 found the belief-refinement ceiling is only +4.8 pp and
explicitly separated "better belief model" from "we don't know their
list", flagging the second as open. The ladder is now pointing at exactly
the item that analysis left open.

**Key non-trivial decisions.**

1. **Measure the noise floor before claiming a gap.** Row #2's agent is
   deterministic and its code never changed, yet its rating moved
   527.9 → 536.0 → 497.8. That ~38-point swing is the *ladder's*
   non-stationarity, not ours, and it is the first honest scale for any
   ladder claim. Consequence adopted: **absolute ratings are not comparable
   across dates; only simultaneous differences are.** Every ladder claim in
   the writeup must be a same-instant comparison.
2. **Let row #4 be the experiment rather than pausing for one.** Rows #3
   and #4 are active together on the same deck and stack, differing only in
   budget policy — the one ladder comparison pool drift cannot confound.
   Its three outcomes are registered in the submission log *before* any
   rating arrives, read against the 38-point floor: #4 − #3 > +38 means
   depth was underprovisioned; ≈ means budget is not the constraint; **< 0
   means deeper search into filler is actively harmful**, which would be
   the strongest evidence yet that determinization quality binds and would
   redirect #29 away from "more search".
3. **Do not reorder Phase 4 on a 7-day-old rating.** The tempting move is
   to drop #26 and chase informed determinization now. Rejected: #26
   answers rollout policy and $c$ at the time budget regardless of how the
   determinization question resolves, it costs CPU we are not otherwise
   using, and row #4 needs days to converge anyway. Run them in parallel
   and let #4 decide #29's shape. We are ~3 weeks ahead of the roadmap;
   this is exactly the slack that buys the right to wait for evidence.
4. **Logged the submission after upload and said so.** The rule is log
   before. It was not followed. Recorded as a deviation in the log's new
   Process notes rather than back-dated — pre-registration whose timestamps
   are negotiable is not pre-registration.

### 2026-07-16 — The measured field arrives, and corrects my correction

Read the public leaderboard meta snapshot
(`myso1987/ptcg-ai-battle-leaderboard-deck-meta-by-score-band`, snapshot
23:35 UTC, 595 teams, 100 % retrieval and classification coverage this
run, zero API errors). First deck-field evidence in this project that we
did not author ourselves.

**What it shows.** Alakazam — a community deck around a *non-ex*
attacker, not one of the four starters — is first in every band above
700 and 47 % of the 900–999 band. The starter decks sink with altitude:
Mega Lucario is 24–25 % of the two lowest bands and fades upward; Iono is
nearly absent. **Our archetype ("Other / Mega Abomasnow ex") appears only
in the two lowest bands — 5 % at 500–599, 4 % at 600–699 — and never
above 700.** Nine teams in the whole sample.

**Key non-trivial decisions.**

1. **My own correction was wrong, and this is the fourth iteration.**
   Yesterday's erratum killed ADR-002's "the field cannot be enumerated"
   and I replaced it with "the field ≈ the four starter decks." That was
   still an *authored* premise. The measured field is ~20 archetypes,
   mostly custom; in our nearest band the starters we hold cover ~39 %
   and the other ~60 % (Starmie, Crustle, Alakazam, Marnie) are decks we
   have never simulated. The pattern is now four for four: H1's mirror,
   EXP-009's filler, ADR-002's homemade pool, and my starter-kit guess.
   **Every authored test condition has diverged from deployment.** That is
   the Threats-to-Validity finding, and the discipline it implies is
   simple: import the condition, never invent it.
2. **Usage is not strength, and I will not read it as such.** The table
   measures where *teams* playing a deck sit, not what the deck is worth,
   and the author says so. Alakazam's shape is suspicious in a specific
   way: it peaks at 47 % in 900–999 and *falls* in the bands above. That
   is the signature of public-notebook forks converging on identical
   ratings — a Kaggle sociology artifact, not a meta measurement. Deck and
   pilot are fully confounded: a starter sitting low may reflect its stock
   rule-based agent. Our Abomasnow never clearing 700 may mean "weak deck"
   or "only beginners play it"; we would be the first Abomasnow with real
   search. This dataset cannot separate those.
3. **Deck risk flagged, deliberately not acted on.** Joining the meta
   table with the starter agents' `prize_count` gives the first *mechanical*
   candidate explanation for our archetype's ceiling: a Mega ex concedes
   **3 prizes** on a Knock Out, and the top meta is a 1-prize Alakazam and
   Crustle walls. The exchange math is brutal — they need ~2 KOs, we need
   ~6. Compelling, and still not enough to move: Megas are tanks, EXP-007
   saw none of these decks, and the evidence is confounded per (2). It
   goes to the writeup's deck-risk section and raises the priority of
   testing `current-v1` against a *real* Alakazam list — before we spend
   four weeks polishing an agent around a deck that may have a structural
   ceiling.
4. **Mine the lists; do not transcribe them by eye.** The replay schema
   puts the 60-card deck in `steps[1][seat]["action"]` — the deck
   submission is the agent's first action — so a public replay yields the
   exact list for both seats. Hand-marking cards from a watched match
   would recover perhaps half of one and guess the rest: an authored
   proxy wearing a measured costume, which is precisely the failure this
   entry is about. Scoped as `replay-deck-mining` in `open-ideas.md`,
   gated on EXP-009 (if filler is not the constraint, the determinization
   half evaporates) and on a Competition Rules check.
5. **Nothing here is edge, and that is fine.** The snapshot is public, so
   everyone contra-metaing the top is reading it too. We are not using it
   competitively; we are using it for **validity**. It is not gold — it is
   floor.

**Caveats recorded with the data.** Five bands show exactly 100 teams
because that is the stratified sampler's cap, so band-internal shares are
computable (±~5 pp at n = 100) but ladder-wide shares are not. The bands
start at 500 and we sit at 475/497 — we are literally off the map, and
500–599 is a proxy for our field, not our field. And it is a snapshot of a
moving target: our own frozen heuristic drifted 38 points in 11 days, so
this should be re-pulled near the deadline.

### 2026-07-17 — EXP-009 lands early; EXP-010 re-scoped to the determinization

**Decisions made:**

1. **The EXP-009 interim was read at n = 113, and this is recorded.** The
   pre-registered verdict remains N = 500, but with the run resumable and
   the effect predicted large, a peek costs nothing *provided the decision
   rule does not move afterward* — so the peek and its non-effect on the
   protocol are logged here: filler 0.47 vs informed 0.81 on the shared
   seeds, paired Δ ≈ −35 pp, McNemar p ≈ 1.5e-07 with 57 discordant pairs.
   This is branch (a) of the registration, and not marginally: knowing the
   opponent's list was carrying essentially the entire H1 margin. The
   ladder was right and the benchmark was measuring a condition the ladder
   never offers — construct-validity gap number five, and the largest.
2. **EXP-010 is now the determinization comparison; the deck
   re-evaluation is renumbered EXP-011.** Two reasons, one pre-committed
   and one methodological. Pre-committed: EXP-009's branch (a) consequence
   ("informed determinization is promoted to a Phase-4 candidate") was
   registered before the run. Methodological: EXP-007 ranked decks using
   the agent as the measuring instrument, under informed-mirror
   conditions; the determinization lever (~30 pp) is about twice the
   largest deck effect EXP-007 measured (~16 pp), so re-ranking decks
   before fixing the instrument would measure the delusion, not the
   decks. ADR-002's erratum gate and `rationale.md` now point at EXP-011.
3. **The candidate fix is the cheapest deployable one: assume the
   opponent plays our own list.** The filler board is not merely
   imprecise, it is *impossible* — 60× Snorlax has no energy, no
   trainers, no attacker, so the search optimizes against an opponent
   that cannot act, and the real one punishes the plans that result. A
   self-deck assumption is wrong against the real field but coherent: the
   simulated opponent fights back. Wrong-and-alive vs impossible-and-dead
   is an empirical question, and it ships without any inference
   machinery. Archetype inference (replay mining) stays a Phase-5
   candidate, priced by EXP-010's informed-minus-selfdeck gap.
4. **The determinizer got an `opponent_list_is_assumed` mode instead of a
   silent relaxation.** Strict accounting raises on the first revealed
   opponent card that is not in the assumed list — which is every
   non-mirror game — so assumed mode clamps the subtraction and tolerates
   an oversized pool, *on the opponent's side only*; our side stays
   exact, and an assumed pool that cannot cover the board still fails
   loud. The strict path is byte-identical, so EXP-003–009 semantics are
   untouched (`tests/test_determinize.py` pins both properties).
5. **The informed arm rides along as a ceiling, never as a candidate.**
   `ismcts` with the true list cannot ship (the ladder hides the list);
   it is in EXP-010 to price what perfect inference would buy. The gap
   informed − selfdeck is the budget line for Phase-5 inference work: if
   it is small, replay mining is not worth its scope risk.
6. **Trajectory recording turns on with EXP-010, per the gate.** First
   corpus run; acceptable because EXP-010 estimates no timing quantity.
   Provenance is the registry entry plus `scripts/run_exp010.sh`.

**Why it matters for the writeup:** the H1 story now has its honest arc —
supported in the mirror-informed condition, erased under deployment
determinization, and (pending EXP-010) partially recoverable by an
assumption that costs nothing. That arc *is* the research question's
answer taking shape: the value of ISMCTS in PTCG is not search depth, it
is the quality of $P(h \mid I)$.

### 2026-07-17 — A knowledge-heavy public agent triangulates EXP-009

**Decisions made:**

1. **A public notebook (Mega Lucario ex agent, above us on the public
   ladder) was analyzed and distilled into `open-ideas.md` as
   `threat-aware-evaluator` — and deliberately nothing else.** Its
   architecture answers the hidden-information problem by *not
   simulating the opponent at all*: a dense hand-crafted policy, a
   1-ply verification search that stops at the agent's own turn
   boundary, and a static evaluator carrying an aggregate threat model
   ("assume +1 energy, compute max damage, penalize lethal exposure
   weighted by prizes conceded"). Read next to EXP-009 (−27.4 pp from
   simulating the opponent *badly*), it is independent evidence for the
   same conclusion from the opposite direction. Its differential is
   game knowledge — archetype detection over revealed board IDs,
   prize-trade management including the 3-prize Mega concession,
   deck-out defense — not computation: it spends ~1.5 s/decision
   against our adaptive ~6.75 s.
2. **No project change follows from it now.** EXP-010 is mid-run and
   its protocol does not move; the threat-term concept is queued for
   Issue #23 (evaluator design) where H4's pre-registered ablation can
   price it like any other feature. Concepts transfer; constants do
   not — nothing was copied, the same restraint applied to the meta
   notebook and mined decklists.
3. **The attribution caveat is recorded with the observation:** the
   public score attaches to the team, drifts on a non-stationary ladder,
   and may reflect submissions other than the shared notebook. It is
   directional evidence that knowledge-heavy shallow search is
   competitive here — not a measured comparison against us.

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

### 2026-07-19 — EXP-010 closes on branch (a): the self-deck assumption ships

**Decisions made:**

1. **The pre-registered ship gate was applied mechanically and it
   passed.** Pooled paired selfdeck−filler on shared seeds: **+11.0 pp,
   McNemar exact p = 0.023**; per-deck guard clean (selfdeck nominally
   better in all four cells, Wilson-separated worse in none). As
   pre-committed in the registry, `ismcts-selfdeck` replaces the filler
   condition in `submissions/ismcts_main.py` — #29 ships the assumed
   own-list determinization, not "more search". No judgment call was
   exercised at read time; the rule decided.
2. **Phase-5 archetype inference is priced low and the number is
   written down now.** The diagnostic ceiling informed − selfdeck is
   **+5.0 pp, p = 0.24, n.s.** — the same shape as EXP-005's mirror
   ceiling (+4.8 pp): once determinizations are *coherent*, knowing the
   true list buys little. Consequence: `informed-determinization` and
   `replay-deck-mining` stay parked as Phase-5 ideas with a measured
   ≲ 5 pp headroom attached; the threat-aware evaluator term (#23, H4
   ablation) is now the higher-expected-value knowledge investment.
3. **An anomaly is recorded without interpretation: zero losses in 600
   games.** Every non-win against the four starter decks is a draw
   (8–21 per cell). Win rates treat draws as non-wins, so the gate
   numbers are conservative; but the mechanism (turn-cap ties? starter
   decks unable to close?) is queued for the Phase-4 note before any
   claim leans on cross-deck win rates — EXP-011 in particular.
4. **The analysis lives in the repo, not in chat** —
   `scripts/exp010_analysis.py` reproduces every number in the registry
   entry from the gitignored JSONLs, keeping the claim → script → data
   chain auditable.
