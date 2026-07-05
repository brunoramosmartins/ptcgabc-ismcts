# Phase 2 — RL Foundations (Sutton & Barto Ch 1–3)

Working notes and self-derived material extending the exercises in
[`../exercises/sutton-barto-ch01.md`](../exercises/sutton-barto-ch01.md),
[`../exercises/sutton-barto-ch02.md`](../exercises/sutton-barto-ch02.md),
and [`../exercises/sutton-barto-ch03.md`](../exercises/sutton-barto-ch03.md).

Distinction from the exercise files: the exercise files answer the book's
questions verbatim. This file explores concepts that come up while reading
but aren't asked about directly — derivations, connections to the ISMCTS
project, and questions worth flagging for later.

Living document during Phase 2; ends with `## Lessons Learned` and
`## Failed Attempts` at merge time.

---

## Ch 1 — Introduction

### Concept: The agent–environment boundary is a design choice

_(placeholder — connects Ex 3.3 to our own boundary in
[`../docs/mdp-formalization.md`](../docs/mdp-formalization.md))_

### Concept: Value function vs. policy — two ways to say the same thing

_(placeholder — the tic-tac-toe example uses state-value learning;
contrast with action-value or direct policy parameterization)_

### Open questions

- _(fill in during reading)_

---

## Ch 2 — Multi-armed Bandits

### Concept: The exploration–exploitation trade-off

_(placeholder — how $\epsilon$-greedy, softmax, UCB, and optimistic
initial values each parameterize the same trade-off differently)_

### Derivation: Sample-average as a running mean (equation 2.3)

_(placeholder — the $Q_{n+1} = Q_n + \frac{1}{n}(R_n - Q_n)$ recurrence
and its immediate generalization to $\alpha_n$)_

### Derivation: Exponential recency-weighted average (equation 2.6)

_(placeholder — the full expansion showing how a constant $\alpha$
produces a weighted average where recent rewards dominate)_

### Concept: Why UCB1's confidence bound looks the way it does

_(placeholder — Chernoff-Hoeffding sketch, ties to Phase 2 Ex 2.8 and
to `exercises/ex02_mcts_derivations.md` in the roadmap)_

### Bridge to the project: bandits at every MCTS node

_(placeholder — every internal node of an MCTS tree is a bandit
problem; the UCB1 form is the same equation)_

### Open questions

- _(fill in during reading)_

---

## Ch 3 — Finite MDPs

### Concept: Why the four-argument $p(s', r \mid s, a)$ is the fundamental primitive

_(placeholder — everything else (rewards, transitions, values) is a
marginal or expectation of it)_

### Derivation: State-value ↔ action-value equivalence

_(placeholder — the pair of Bellman equations, one rooted at state and
one rooted at action, and how they mutually determine each other)_

### Derivation: Policy invariance under reward translation (equation 3.8)

_(placeholder — Ex 3.15 formalizes this; also underpins the
"no-shaping" decision in
[`../docs/adr/adr-004-terminal-reward-not-shaped.md`](../docs/adr/adr-004-terminal-reward-not-shaped.md))_

### Concept: Discounting vs. episodic termination

_(placeholder — why the book treats them as two forms of the same
underlying "how much of the future do we care about" question; ties
to Ex 3.5, 3.6, 3.16)_

### Bridge to the project: PTCG as a finite-horizon MDP-in-disguise

_(placeholder — PTCG episodes are guaranteed finite (deck-out
condition), so the "continuing" vs. "episodic" distinction collapses.
The 10-min wall-clock is the practical horizon.)_

### Bridge to the project: ISMCTS's information sets are a partition of $S$, not new state space

_(placeholder — connects Ch 3's MDP formalism to our environment
formalization in
[`../docs/mdp-formalization.md`](../docs/mdp-formalization.md))_

### Open questions

- _(fill in during reading)_

---

## Cross-chapter connections

### Bandits (Ch 2) are the "one-state MDP" (Ch 3)

_(placeholder — the bandit is a degenerate MDP with $|S| = 1$; the
distinction is that Ch 2 has no state to condition on)_

### Value iteration ≠ policy iteration (peek forward to Ch 4)

_(placeholder — Ch 3 sets up Bellman equations but doesn't solve them;
Ch 4 will)_

---

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled if any come up during the read-through.)_
