# ADR-003 — Heuristic, Not Learned, Evaluator

**Status:** Accepted (Phase 0).

## Context

ISMCTS uses a value estimator in two places:

1. **Rollout policy.** From an expanded leaf, some policy simulates play to
   the end of the episode and returns a terminal outcome. Random rollouts
   are the classical default; heuristic-guided rollouts trade rollout
   variance for a plausibility bias.
2. **Leaf evaluator.** If we truncate rollouts before terminal, we need a
   scalar $\hat V(s)$ approximating the true minimax value at $s$.

Both places admit either a **hand-crafted heuristic** — a linear (or small
nonlinear) combination of interpretable board features — or a **learned
model** — a neural net or gradient-boosted regressor trained on self-play
outcomes (AlphaGo-family; Silver et al. 2016, 2017).

Our constraints from Phase 0:

- 10-week calendar with the Simulation deadline at Week 6-7 (Aug 16-17).
- No GPU on the Kaggle worker (2 vCPUs, 12.2 GiB RAM); training must happen
  offline, and any learned artifact must fit in the 197.7 MiB submission
  bundle.
- Portfolio framing (see `docs/research.md`): the writeup must trace every
  claim back to a pre-registered hypothesis. A learned evaluator introduces
  a second confounding variable (feature representation *and* training
  procedure) that H4's per-feature ablation would not cleanly isolate.
- No labelled training data exists — self-play is the only source, and
  self-play needs a working agent, which needs an evaluator: a chicken-and-egg
  loop we don't have weeks to close.

## Decision

Use a **hand-crafted linear heuristic evaluator** for both rollout guidance
and (optionally) leaf evaluation. Features are interpretable board
quantities — prize-card differential, active Pokémon HP fraction, energy
attached vs. attack cost, hand quality proxy, bench threat count. Weights
are chosen by hand in Phase 4 and audited by the H4 per-feature ablation
(see `docs/research.md`).

Formally,
$$\hat V_\theta(s) \;=\; \sum_{k=1}^{K} \theta_k \, \phi_k(s), \qquad
\phi_k \in [-1, 1],\; \theta_k \in \mathbb{R}.$$
Features $\phi_k$ are scaled to $[-1, 1]$ so the sign of $\theta_k$ is the
sign of the effect and $|\theta_k|$ ranks importance.

## Consequences

**Positive.**

- Clean isolation of variables: the only moving parts in the evaluator are
  the feature set (fixed in Phase 4) and the weights (fixed in Phase 4).
  H4 drops one feature at a time and reports paired-bootstrap deltas with
  Bonferroni correction — this test is only interpretable *because* the
  evaluator is linear and hand-crafted.
- Every feature has a rules-based rationale we can write down in
  `writeup/writeup.md`. A learned evaluator would require an interpretability
  section that would eat the 2000-word budget.
- Zero training pipeline. No data, no checkpoints, no hyperparameter
  sweeps over training runs. All variance in Phase 5 experiments comes
  from ISMCTS itself, not from stochastic gradient descent.
- Bundle size stays tiny — the evaluator is ~50 lines of Python and a
  handful of floats.

**Negative.**

- Weight tuning is manual. We accept some Phase-4 iteration burning wall
  clock time.
- Cannot capture nonlinear feature interactions (e.g. "bench Pokémon $X$ is
  valuable *only if* energy $Y$ is in hand"). If H1 fails and Phase 5
  suggests the evaluator is the bottleneck, revisiting this ADR is on the
  Phase 7 backlog.
- H2 (heuristic-guided vs random rollouts) is now a test of *this specific*
  heuristic, not of the general "learned rollout" idea. Recorded as a
  scope limitation in `docs/research.md`'s Threats to Validity section.

## Alternatives Considered

- **AlphaZero-style learned value + policy net (Silver et al. 2017).**
  Rejected: needs a self-play training pipeline, GPU access, and weeks of
  compute we don't have. The competition also does not admit external
  training data. High probability of failing to converge in 10 weeks and
  ending with neither a working ISMCTS nor a working learner.
- **Gradient-boosted evaluator (e.g. LightGBM) trained on random-agent
  self-play outcomes.** Rejected: the label distribution from random
  self-play is biased toward random-friendly board states; the resulting
  evaluator would systematically overvalue positions that random beats
  itself in, which is not the target distribution during real search.
- **No evaluator — pure random rollouts to terminal (Phase 3 baseline).**
  This *is* our Phase 3 baseline and is preserved for the H2 comparison.
  Rejected as the final answer because rollout variance on 10-minute
  matches is high; H2 exists to measure the effect.
- **Rules-derived exact evaluator** (e.g. solve endgame positions with
  small state exactly). Rejected: PTCG's state space stays large right up
  to the last turn; there is no clean "endgame" phase transition to
  exploit.

## References

- Silver et al. (2016). *Mastering the game of Go with deep neural networks
  and tree search.* Nature.
- Silver et al. (2017). *Mastering the game of Go without human knowledge.*
  Nature.
- Coulom (2007). *Efficient selectivity and backup operators in Monte-Carlo
  tree search.* CG.
- Browne et al. (2012). *A Survey of Monte Carlo Tree Search Methods.* IEEE
  TCIAIG — sections on heuristic vs. random rollouts.
- ADR-001 (this repo) — motivates the algorithm this evaluator plugs into.
- ADR-004 (this repo) — complementary decision on the terminal reward
  signal.
