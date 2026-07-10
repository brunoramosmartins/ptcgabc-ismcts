# Phase 4 — Evaluator Design (H2/H4 target)

Working note for Issues #23–#24. Living document; ends with
`## Lessons Learned` and `## Failed Attempts` at merge time.

## What the diagnostic ladder changed about this design

The Phase-3 decomposition (EXP-003/004/005) reframed the evaluator's
job. With search capturing ~87% of the omniscient edge already, the
evaluator is NOT here to rescue a weak search — it has exactly two
jobs, each tied to a pre-registered hypothesis:

1. **Rollout guidance (H2).** Replace uniform-random rollout moves
   with rule-guided ones, reducing rollout variance so the same
   iteration budget yields sharper $Q$ estimates. Browne's caveat
   (notes §2.3) applies in full: heavy rollouts can *hurt* via bias,
   slowdown, and over-determinism — which is why H2 is a genuine
   question.
2. **Ablation subject (H4).** Every feature must be individually
   droppable so `exp_ablation_evaluator.py` can test each one's
   contribution with Bonferroni-corrected paired tests.

## Design decision 1 — move scoring, not state evaluation

Two architectures were on the table:

- **(a) State-value evaluator** $\hat V(s)$: score the state after
  each candidate move via one-step lookahead. Rejected for the
  rollout path: lookahead requires a `search_step` per candidate per
  rollout step (~7× step cost ⇒ ~78 ms/rollout vs 11 ms), collapsing
  the iteration budget that the ladder showed is our main asset.
- **(b) Move-prior scoring** $r(\text{option})$: score each legal
  option directly from its content (type, context), no simulation.
  Near-zero overhead; the rollout stays ~0.12 ms/step.

**Chosen: (b).** The "features" of H4 are therefore *rules* — each a
reason to prefer an option class — and the ablation drops rules.
Architecture (a) stays available as a Phase-5/post-competition
extension if H2 shows guidance value worth deepening.

## Proposed feature set (v1) — REVIEW BEFORE IMPLEMENTING

Each feature maps an option to a score contribution; the rollout
policy samples among the top-scored options (softmax or ε-greedy —
decision 2 below). Option `type` codes from the engine (probed):
ATTACK, PLAY, ATTACH, EVOLVE, ABILITY, RETREAT, END, YES/NO, CARD…

| # | Feature (rule) | Rationale | Ablatable? |
|---|---|---|---|
| F1 | **Prefer ATTACK when available** | Attacking converts board state into prizes — the win condition. Random rollouts frequently skip attacks, making terminal signals noisier. | yes |
| F2 | **Prefer ATTACH (energy) early in the turn** | Energy is the tempo throttle (game-primer); un-attached turns are nearly always dominated. | yes |
| F3 | **Prefer EVOLVE** | Evolution is almost always strict improvement (more HP, stronger attacks). | yes |
| F4 | **Prefer PLAY (bench Basics) when bench < 2** | Bench depth insures against W2 loss (no Pokémon left) — rollouts that never bench lose to chip KOs. | yes |
| F5 | **Penalize END when other actions score > 0** | Passing with available value is the classic random-rollout failure. | yes |
| F6 | **Penalize RETREAT by default** | Retreat spends energy (F2's resource) without board progress; exceptions are too contextual for a v1 rule. | yes |

Deliberately NOT in v1: damage math (needs attack/card DB join),
matchup awareness, prize-race logic. Keep k=6 rules so the H4
Bonferroni correction stays at α/6.

## Design decision 2 — how the policy uses scores (pick one)

- **(i) Greedy-with-ties**: play a uniformly random choice among the
  top-scored options. Simplest; most deterministic (Browne's
  over-determinism risk highest).
- **(ii) ε-greedy** (ε ≈ 0.2): greedy among top-scored with prob
  1−ε, uniform otherwise. Keeps exploration; one tunable.
- **(iii) Softmax over scores** (temperature τ): smoothest, two
  tunables, hardest to ablate cleanly.

**Proposal: (ii) ε-greedy**, ε fixed at 0.2 for H2 (not tuned — tuning
it would contaminate the H2 comparison; a sensitivity sweep can come
later as exploratory).

## H2 experiment shape (pre-registered, for reference)

`scripts/exp_ablation_rollout.py`: ISMCTS+guided vs ISMCTS+random,
same 500 paired seeds, same 1000 iterations, vs the heuristic
reference. Paired McNemar. The random-rollout path must remain intact
and selectable (ADR-001 baseline).

Honest prior after the ladder results: **uncertain, leaning small.**
Search already extracts most available value; guided rollouts sharpen
estimates but Browne's three failure modes are real. A null H2 would
be coherent with the "search dominates" story — and is a publishable
finding.

## Implementation sketch (after design review)

- `evaluator/heuristic.py`: `MoveScorer` — pure function
  `(option, obs) -> float` as a weighted sum of F1..F6 indicator
  features; weights are named constants; `disable=` parameter for H4
  ablation.
- `evaluator/rollout.py`: `guided_rollout(state, rng, scorer, eps)` —
  drop-in replacement for `search/ismcts.py::_rollout`; wire via a
  `rollout_policy` parameter on `decide()` (default: random).
- Tests: scorer unit tests per feature; guided-rollout behavior on
  the fake engine; ablation flag coverage.

## Open questions for the author

1. Approve/adjust the F1–F6 rule set? (Each becomes an H4 claim.)
2. Approve ε-greedy with fixed ε = 0.2?
3. Weights v1: start uniform (all 1.0) or hand-ranked (e.g. F1=2.0)?
   Uniform is cleaner for H4 interpretation; ranked may help H2.

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled as they occur.)_
