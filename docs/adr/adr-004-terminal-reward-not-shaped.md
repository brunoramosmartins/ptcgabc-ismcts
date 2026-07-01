# ADR-004 — Terminal Reward, No Shaping

**Status:** Accepted (Phase 0).

## Context

MCTS-family algorithms backpropagate a scalar return from each rollout up
the tree. Two families of return signal are standard:

1. **Terminal reward.** The rollout runs to the end of the episode and
   returns $r \in \{-1, 0, +1\}$ (loss / draw / win). No intermediate
   reward is emitted.
2. **Shaped reward.** Intermediate quantities — prize cards taken, damage
   dealt, cards drawn — are added to the return, either as
   potential-based shaping $F(s, s') = \gamma \Phi(s') - \Phi(s)$
   (Ng, Harada & Russell 1999) or as unprincipled bonuses.

The Kaggle Simulation Category scoring is TrueSkill-style over
win/loss/draw episodes: only the terminal outcome matters for the ladder.

## Decision

Backpropagate the **terminal reward only**:
$$G_t \;=\; r_T \in \{-1, 0, +1\},$$
with $r_T = +1$ if our agent wins, $-1$ if it loses, $0$ if the match ends
in a draw or timeout tie. No intermediate shaping, no discount factor
$\gamma < 1$, no per-turn bonus.

The heuristic evaluator from ADR-003 is used to *guide the rollout policy*
and (optionally) to bootstrap truncated leaves — but its output does **not**
enter the backpropagated return. UCB1 statistics at internal nodes are
means of terminal $r_T$ values, not of shaped intermediates.

## Consequences

**Positive.**

- The value we optimize matches the value the ladder scores us on. This
  eliminates one degree of freedom in every experiment — no ambiguity about
  whether an ISMCTS improvement is "real" (win-rate) or "shaping-fitted"
  (proxy metric that doesn't transfer).
- Potential-based shaping is only *policy-invariant* if the potential
  $\Phi$ is a true value function; a wrong $\Phi$ biases the policy
  (Ng et al. 1999). We do not have a true value function; a wrong
  shaping schedule would silently degrade play in ways H1–H4 would not
  isolate.
- Comparisons across H1–H4 all use the same $\{-1, 0, +1\}$ scale.
  Wilson intervals on a Bernoulli win indicator are straightforward;
  bootstrap CIs on shaped returns would need a variance estimate we don't
  currently have.
- Simplifies the implementation: no reward buffer, no per-transition
  hook in the env wrapper.

**Negative.**

- **High variance per rollout.** A single random rollout returns one of
  three values, so the UCB1 mean estimate at an internal node needs many
  visits before the confidence bound is informative. This is the primary
  cost of the decision and directly motivates H3 (sensitivity to
  simulations/decision) — see `docs/research.md`.
- **Long credit-assignment horizon.** A poor decision on turn 3 might not
  register in the terminal reward for another 20 turns. ISMCTS relies on
  UCB1 concentration to eventually surface such regressions; the heuristic
  evaluator (ADR-003) partially compensates by biasing the rollout policy
  toward positions the heuristic ranks well.
- Truncated rollouts (if we later find them necessary for the 10-minute
  budget) will bootstrap from the heuristic, importing its bias. If Phase 5
  seed-stability numbers show unusable variance, revisit — but only as an
  amendment ADR referencing this one, per the research-log rule.

## Alternatives Considered

- **Prize-card differential as shaped return.** Attractive because prizes
  are the game's own progress meter. Rejected: it correlates with winning
  but is not equal to it (a knock-out that draws two prizes but leaves
  our active with 10 HP against a full-board opponent is often losing).
  Using it would import a small but persistent bias.
- **Potential-based shaping with $\Phi$ = heuristic evaluator.** Formally
  policy-invariant (Ng et al. 1999) *if* $\Phi$ is bounded and consistent.
  Rejected because (i) we have no external argument that our heuristic is
  the true value function, (ii) it would collapse the ADR-003 / ADR-004
  boundary — the evaluator would enter *both* the rollout policy *and* the
  return signal, making H2 and H4 harder to disentangle.
- **Discounted terminal reward** $\gamma^{T-t}$ **for** $\gamma < 1$.
  Rejected: PTCG episodes are short and finite, and a discount would
  distort minimax equivalence with the ladder's win/loss scoring for no
  algorithmic gain.
- **Reward normalization to $[0, 1]$** rather than $\{-1, 0, +1\}$.
  Rejected as premature — the UCB1 exploration constant $c$ can absorb
  this scaling, and we prefer to keep the reward space aligned with the
  ladder outcome semantics.

## References

- Ng, Harada & Russell (1999). *Policy Invariance Under Reward
  Transformations: Theory and Application to Reward Shaping.* ICML.
- Kocsis & Szepesvári (2006). *Bandit based Monte-Carlo Planning.* ECML —
  UCB1 concentration under bounded rewards.
- Browne et al. (2012). *A Survey of Monte Carlo Tree Search Methods.*
  IEEE TCIAIG.
- Sutton & Barto (2018), 2nd ed. — Chapter 3 (returns) and Chapter 17.4
  (reward-signal design).
- ADR-001 (this repo) — the algorithm receiving this reward.
- ADR-003 (this repo) — the evaluator that shapes rollouts but not returns.
