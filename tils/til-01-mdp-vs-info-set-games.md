# TIL #1 — MDPs, POMDPs, and Games of Imperfect Information

**Status:** draft (Phase 2). Polished for portfolio in Phase 7.

Format: Hook / Insight / Example / Takeaway.

---

## Hook

The Bellman equations in Sutton & Barto Chapter 3 assume the agent
observes the full state $s$. That single assumption quietly rules out
every card game where the opponent has a hand you cannot see. Applying
Q-learning to a partially observed dict is not "approximately right" —
it violates the property that makes Q-learning converge at all.

## Insight

Three related but distinct frameworks live in that space, each with a
different answer to "what does the agent observe?":

- **MDP** (fully observable). The state $s$ satisfies the Markov
  property: the future is conditionally independent of the past given
  $s$. Every classical RL algorithm — value iteration, Q-learning, SARSA
  — is defined here. $V(s)$ and $Q(s, a)$ are well-defined functions of
  the state.
- **POMDP** (partially observable). The agent sees an observation
  $o = O(s)$, not $s$ itself. The Markov property fails on $o$: two
  different underlying $s, s'$ can produce the same $o$ with different
  futures. The classical fix is to condition on the *belief state* — a
  distribution over $s$ given the observation history — which is
  itself Markov but lives in the infinite-dimensional simplex over
  $s$. Belief-based value functions exist but are expensive.
- **Imperfect-information game** (two-player, observation-based). Same
  observation problem as POMDP, but now there are *two* agents whose
  observations differ, and the opponent's policy conditions on their
  own observation. The right primitive is the **information set** —
  the equivalence class $I(s) = \{s' : O(s') = O(s)\}$ of states the
  agent cannot distinguish. Every admissible policy is
  $I$-measurable: it depends on the information set, not on the
  underlying state.

The three frameworks share the same underlying MDP but disagree on what
the policy is *allowed* to condition on. Q-learning on a POMDP or on
an imperfect-info game with observations-as-states silently violates the
$I$-measurability requirement — it lets the policy differ across states
in the same information set, which is not implementable by an agent that
only sees observations.

ISMCTS resolves this by making the search tree indexed by information
sets rather than states. Determinization samples a compatible hidden
state at simulation time, runs the standard MCTS four-phase loop on that
world, and *averages* $Q$-values across sampled worlds. The averaging is
what enforces $I$-measurability.

## Example

Consider a stripped-down PTCG turn where the agent must choose between
two attacks. The opponent has one card face-down in front of them.
Suppose:

- If the face-down card is Fire-type, attack A wins the exchange (KO on
  weakness), attack B trades neutrally.
- If the face-down card is Water-type, attack A trades neutrally,
  attack B wins the exchange.

The agent has no way to see which card it is; both are consistent with
the observed information set $I$. Suppose our prior $P(h \mid I)$
assigns 50/50.

- **Naive perfect-information determinization.** Sample $h$, solve the
  resulting perfect-info game, act. If $h$ = Fire, output A. If $h$ =
  Water, output B. Aggregate across sampled determinizations: the agent
  *believes* it should sometimes play A and sometimes play B, driven by
  worlds it cannot actually distinguish. This is **strategy fusion** —
  the argmax operator does not commute with the expectation.
- **ISMCTS.** For each action, compute
  $\mathbb{E}_{h \sim P(h \mid I)}[Q(I, a, h)]$ by averaging simulation
  outcomes over sampled $h$. Both A and B come out to the same
  neutral-plus-half-win value; the search may prefer a third,
  hedge-type action (attack C) that is neutral in *both* worlds but has
  no downside — the correct answer under uncertainty.

The perfect-info determinization picked between A and B *within each
world* before averaging; ISMCTS averaged *the value of each action*
across worlds and then picked. The two orderings — argmax-then-expect
vs expect-then-argmax — give different answers whenever the argmax is
sensitive to the hidden state, which is exactly the interesting regime.

## Takeaway

The framework you pick determines what policies are even *available* to
learn. MDPs assume full observability; POMDPs use beliefs; imperfect-
information games use information sets. Q-learning belongs to the first
framework and misbehaves in the other two.

For our PTCG project, this insight is not academic. The `cabt` engine
hands the agent a dict of observations, not a state. Treating that dict
as if it were a state — feeding it directly to Q-learning or to naive
determinized MCTS — would produce a policy that conditions on
information the agent doesn't have. ISMCTS is the smallest algorithmic
change that respects the constraint, which is why it's Phase 3 (per
ADR-001).

Read next: Cowling, Powley & Whitehouse (2012) for the formal
information-set MCTS algorithm; Long, Sturtevant, Buro & Furtak (2010)
for why perfect-information determinization sometimes works despite
strategy fusion (spoiler: when the argmax is *not* sensitive to the
hidden state, both approaches converge to the same answer).
