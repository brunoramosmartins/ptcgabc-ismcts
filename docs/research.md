# Research

## Research Question

> When is Information-Set Monte Carlo Tree Search a good choice for imperfect-information card games with hidden state and stochastic transitions?

## Pre-Registered Hypotheses

> **Status: LOCKED 2026-07-09** (tag `v0.3-hypotheses` on the merge
> commit of the lock PR). No edits to H1–H4 after this point without a
> research-log entry recording what changed and why. Verdicts are
> filled exclusively by the registered experiments named in each row.

| ID | Statement | Test | Metric | Verdict |
|---|---|---|---|---|
| **H1** | SO-ISMCTS with uniform consistent determinization and random rollouts beats the deterministic heuristic baseline in head-to-head play. | EXP-003: `scripts/local_ladder.py --agent-a ismcts --agent-b heuristic`, N = 500 paired seeds | ISMCTS win rate with Wilson 95% CI; **supported** iff the lower CI bound exceeds 0.5 | **SUPPORTED** (2026-07-09). 390W–0D–110L, win rate 0.780, Wilson 95% CI [0.742, 0.814]; lower bound 0.742 > 0.5. Zero fallbacks (valid). See EXP-003 in the registry. |
| **H2** | Heuristic-guided rollouts outperform random rollouts within ISMCTS. | EXP-006: `scripts/local_ladder.py --agent-a ismcts-guided --agent-b heuristic`, N = 500, same paired seeds as EXP-003 | Win-rate Δ + paired test (McNemar / paired bootstrap) on shared seeds | **NOT SUPPORTED** (2026-07-11). Guided 405W–0D–95L, win rate 0.810, Wilson 95% CI [0.773, 0.842] vs random-rollout 0.780. Paired on the 500 shared seeds: guided-only wins 91, random-only 76 → Δ = +3.0 pp, McNemar exact p = 0.279 (n.s. at 5%). Zero fallbacks (valid). Descriptive side-result: guided matches are ~18% faster (median 25.6 s vs 31.4 s — guided rollouts end games sooner). See EXP-006 in the registry. |
| **H3** | Local head-to-head win rate against the fixed heuristic reference improves monotonically with iterations/decision until the per-decision time budget binds; the breakpoint lies in the hundreds-to-low-thousands range (root-convergence floor ≈ $k \cdot b$, ex02.5). | `scripts/exp_sensitivity_simulations.py`, sweep {30, 100, 300, 1000, 3000} iterations | Win rate per level with Wilson 95% CI; monotonic-trend check + breakpoint identification | _pending_ |
| **H4** | Every feature in the final heuristic evaluator contributes non-trivially. | `scripts/exp_ablation_evaluator.py` | Per-feature Δ + raw and Bonferroni-corrected paired p-values | _pending_ |

Lock-time refinements (recorded here for transparency; all made
*before* any hypothesis-testing experiment ran):

- **H1** — algorithm variant, determinization policy, opponent, and
  decision rule pinned. "Outperforms" operationalized as
  Wilson-lower-bound > 0.5 in direct head-to-head, the same criterion
  EXP-002a used.
- **H3** — primary metric moved from Kaggle ladder rating to local
  win rate versus the fixed heuristic reference. The ladder pool is
  uncontrolled and non-stationary (opponents enter and leave daily);
  a monotonicity claim is only testable against a fixed opponent.
  Ladder rating remains a secondary, descriptive observation. The
  sweep grid crosses the measured affordability point (~2,000
  iterations/decision, `notes/phase3-implementation-plan.md`) from
  both sides.

## Methodology

See `docs/benchmark-protocol.md` for the fixed match-set, seed, and hardware protocol every hypothesis test respects. See `experiments/registry.md` for the full experiment ledger.

## Exploratory extensions (not pre-registered)

Ideas that surfaced during study but are **not** part of the H1–H4
lock. Candidates for Phase 5 exploratory experiments or
post-competition portfolio extensions. See
[`../notes/open-ideas.md`](../notes/open-ideas.md) for the full
schema and rationale per idea.

- **oracle-baseline-cheating-uct** — diagnostic upper bound: give UCT
  the true state (no determinization) to measure the ceiling that any
  imperfect-information algorithm can achieve. Gates every belief-
  based idea below. Phase 3 addendum.
- **pimc-baseline-determinized-uct** — PIMC (independent per-
  determinization UCT + vote) as a fourth arm in the same Phase 3
  diagnostic run. Decomposes the gap: $W_{\text{ISMCTS}} -
  W_{\text{PIMC}}$ measures the value of the shared info-set tree
  (Cowling's claim) in PTCG specifically. Interpretive, not gating.
- **informed-determinization** — replace uniform $P(h \mid I)$ with a
  distribution informed by public evidence (deck lists, discard,
  board state). Gated on the oracle baseline: pursue only if the
  ceiling gap $\gtrsim$ 5 pp. Candidate Phase 5 exploratory or post-
  competition amendment. See
  [`../notes/open-ideas.md`](../notes/open-ideas.md) under
  *informed-determinization*.
- **archetype-conditioned-rave** — RAVE statistics conditioned on the
  inferred opponent archetype. Transitively gated on the oracle
  baseline (via *informed-determinization*'s archetype module). See
  [`../notes/open-ideas.md`](../notes/open-ideas.md).
- **progressive-widening-with-action-ranking** — heuristic action
  ranking + progressive widening for the high-branching-factor
  setting. Independent of the belief-based line. Phase 5 exploratory.
  See [`../notes/open-ideas.md`](../notes/open-ideas.md).
- **transposition-tables-for-info-sets** — hash-based sharing of
  statistics across equivalent info-sets. Pure speedup, not a
  research question. Phase 5 exploratory or post-competition.
