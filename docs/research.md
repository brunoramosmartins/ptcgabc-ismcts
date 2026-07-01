# Research

## Research Question

> When is Information-Set Monte Carlo Tree Search a good choice for imperfect-information card games with hidden state and stochastic transitions?

## Pre-Registered Hypotheses

> **Status:** DRAFT — hypotheses are **locked at the end of Phase 2** (see roadmap). Do not edit H1–H4 after the Phase 2 tag `v0.3-hypotheses` without recording a research-log entry.

| ID | Statement | Test | Metric | Verdict |
|---|---|---|---|---|
| **H1** | ISMCTS with random rollouts outperforms the heuristic-only baseline. | Phase 3 head-to-head (`exp_*`) | Win-rate Δ + Wilson 95% CI + paired bootstrap | _pending_ |
| **H2** | Heuristic-guided rollouts outperform random rollouts within ISMCTS. | `scripts/exp_ablation_rollout.py` | Win-rate Δ + paired test on shared seeds | _pending_ |
| **H3** | Ladder performance improves monotonically with simulations/decision until the per-match time budget binds. | `scripts/exp_sensitivity_simulations.py` | Rating vs sims, breakpoint identification | _pending_ |
| **H4** | Every feature in the final heuristic evaluator contributes non-trivially. | `scripts/exp_ablation_evaluator.py` | Per-feature Δ + Bonferroni-corrected paired tests | _pending_ |

## Methodology

See `docs/benchmark-protocol.md` for the fixed match-set, seed, and hardware protocol every hypothesis test respects. See `experiments/registry.md` for the full experiment ledger.
