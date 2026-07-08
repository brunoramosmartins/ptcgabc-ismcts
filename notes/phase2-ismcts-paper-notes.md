# Phase 2 — ISMCTS Paper Notes (Cowling et al. 2012)

Reading-companion prompts for **Cowling, P.I., Powley, E.J., &
Whitehouse, D. (2012).** *Information Set Monte Carlo Tree Search.*
IEEE Transactions on Computational Intelligence and AI in Games, 4(2),
120–143.

This is *the* paper for our project. Everything Phase 3 builds is a
direct implementation of what these authors describe. Read it after
finishing the Browne survey — the notation and framing assume you
already know classical MCTS.

Purpose: give you targeted questions to answer while reading. Same
template as [`phase2-rl-foundations.md`](phase2-rl-foundations.md) and
[`phase2-mcts-fundamentals.md`](phase2-mcts-fundamentals.md).

Cross-refs used throughout:
- [`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md)
  — our justification for choosing this algorithm.
- [`../docs/mdp-formalization.md`](../docs/mdp-formalization.md) — our
  formalization of PTCG as an imperfect-information game.
- [`../exercises/ex01_environment.md`](../exercises/ex01_environment.md)
  — information-set formalism used in this project.
- [`../exercises/ex02_mcts_derivations.md`](../exercises/ex02_mcts_derivations.md)
  — the five derivations, three of which (02.2, 02.3, 02.4) draw
  directly on this paper.

Prompts marked 🔄 require synthesis with Browne or with earlier readings.

**Cross-source questions** (which variant for PTCG, what Cowling leaves
for the implementer, predictions vs reality) live in
[`phase2-synthesis.md`](phase2-synthesis.md) — not at the end of this
file. When a prompt here forward-refs a cross-source question, it
points there.

Living document during Phase 2; ends with `## Lessons Learned` and
`## Failed Attempts` at merge time.

---

## §1 — Motivation

### 1.1 — Why isn't naive determinization enough? 🔄

**Prompt.** The paper opens by arguing that a naive
"sample-a-determinization-and-solve-with-MCTS" approach fails on
imperfect-information games.

- What is the specific failure mode they identify — is it strategy
  fusion (Frank & Basin 1998), non-locality (Long et al. 2010), or
  something else they name distinctly?
- In their own words, what property of the naive approach violates the
  requirement that the agent's action can't depend on hidden
  information?
- Connect to
  [`../exercises/ex01_environment.md`](../exercises/ex01_environment.md)
  §2: their argument should be a restatement of "policies must be
  $I$-measurable". Do they use this vocabulary explicitly?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 1.2 — The Bridge / Skat / other card-game history

**Prompt.** The paper is motivated by card games. It likely cites a
history of MCTS attempts on Bridge, Skat, and possibly Poker.

- Which prior card-game applications does the paper cite as motivating?
- Which of those applications used PIMC (Perfect-Information Monte
  Carlo, i.e. naive determinization)? Which used something else?
- How does the paper position its contribution relative to those prior
  attempts?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §2 — Formal setup

### 2.1 — Information sets, formally 🔄

**Prompt.** The paper defines the information set for player $i$ at
state $s$.

- Write down their exact definition. Compare with the one in
  [`../docs/mdp-formalization.md`](../docs/mdp-formalization.md) —
  $I_i(s) = \{s' : O_i(s') = O_i(s)\}$. Are they the same, or does the
  paper require anything extra (e.g. reachability, non-emptiness)?
- The paper likely defines an observation function, a partition, and
  possibly a *history* alongside states. Note what they add on top of
  the vanilla definition.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.2 — Determinization: what does it mean formally?

**Prompt.** A *determinization* is a specific concrete game state
compatible with the observation.

- Give the paper's formal definition — likely something like "a
  determinization $h$ of an information set $I$ is a state $h \in I$".
- What is the sampling distribution $P(h \mid I)$ they assume? Is it
  uniform over $I$, or something more sophisticated?
- Do they discuss how the sampling distribution should be chosen when
  the prior on hidden information is not uniform (e.g. when we know
  something about the opponent's likely hand)? PTCG has this: after
  many turns, the discard pile reveals cards, changing the posterior.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.3 — The ISMCTS action-selection rule

**Prompt.** The core equation of ISMCTS at the root is

$$
a^* \;=\; \arg\max_a \; \mathbb{E}_{h \sim P(h \mid I)}\!\left[ Q(I, a, h) \right].
$$

- Find the paper's exact statement of this equation. Note the notation
  they use — it may differ from ours (they may write $V$ instead of
  $Q$, may parameterize by history instead of $I$, etc.).
- The key subtlety: the argmax is *outside* the expectation. Does the
  paper make this explicit? Compare with naive PIMC, which does
  $\arg\max_a$ *inside* the expectation.
- This is Ex 02.3 in
  [`../exercises/ex02_mcts_derivations.md`](../exercises/ex02_mcts_derivations.md).
  The canonical answer there will draw directly on this section of the
  paper.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §3 — The ISMCTS algorithm variants

### 3.1 — SO-ISMCTS (Single-Observer)

**Prompt.** The simplest ISMCTS variant.

- What does "single observer" mean — whose perspective?
- Restate the four MCTS phases (selection, expansion, rollout,
  backpropagation) for SO-ISMCTS, calling out where the information-set
  structure enters vs where the classical MCTS description applies
  unchanged.
- What does SO-ISMCTS *not* model that a more sophisticated variant
  could? (Hint: the opponent's belief update.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 3.2 — MO-ISMCTS (Multiple-Observer)

**Prompt.** The paper introduces MO-ISMCTS as a more accurate model.

- What does MO-ISMCTS model that SO-ISMCTS doesn't? (Concretely: the
  opponent has their own information set and their own tree, and moves
  reveal information to the opponent.)
- What's the computational cost of MO-ISMCTS vs SO-ISMCTS?
- Note the paper's empirical comparison: which one wins on which games?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 3.3 — MO-ISMCTS with subjective belief updates (MO-ISMCTS+SEL or similar)

**Prompt.** The third variant refines MO-ISMCTS with subjective belief
updates about opponent moves.

- What problem does this variant fix over MO-ISMCTS?
- Does the paper argue this is always worth the cost, or is it
  situational?
- Which variant does ADR-001 in this project commit to? (Answer:
  SO-ISMCTS. Note the paper's argument for or against that choice given
  our timeline.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §4 — Selection policy at information-set nodes

### 4.1 — UCB1 on information sets

**Prompt.** At each information-set node, ISMCTS uses UCB1 to select
among children.

- Confirm that the paper uses standard UCB1, or a modified form.
- The visit count $n_a$ at an information-set node aggregates across
  many sampled determinizations. Does this raise any convergence
  concerns? (Non-stationarity within a single ISMCTS search is a
  candidate — compare with
  [`phase2-rl-foundations.md`](phase2-rl-foundations.md) §2.5.)
- Does the paper prove or discuss asymptotic consistency of ISMCTS?
  Cite the argument.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 4.2 — Legal-action mismatch across determinizations

**Prompt.** In imperfect-information games, the *legal actions* at an
observed state may depend on hidden information (e.g. can I play this
Trainer? Depends on my hand, which I know; but at future nodes, the
legality depends on the *opponent's* future draws, which are hidden).

- How does the paper handle nodes where the legal actions differ
  across determinizations sampled for the same information set?
- Related: what does "expansion" mean at an information-set node when
  different determinizations expose different children?
- This is critical for PTCG — Trainer legality depends on many hidden
  variables. Note whether the paper's approach is directly transferable
  or needs adaptation.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §5 — Experimental validation

### 5.1 — Which games did they test on?

**Prompt.** The paper validates ISMCTS on specific games.

- Which games? Note their properties (partial observability level,
  stochasticity, branching factor).
- What baselines do they compare against — random? PIMC? Domain-
  specific hand-crafted agents?
- Which of the tested games is closest in structure to PTCG?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 5.2 — Metrics and statistical rigor

**Prompt.** Compare their reporting standards with our
[`../docs/benchmark-protocol.md`](../docs/benchmark-protocol.md).

- Do they report win rates with confidence intervals? Which family?
- Do they use paired testing on shared match seeds?
- How many matches per comparison? Is it consistent with our $N = 500$
  target for Phase 5 hypothesis tests, or lower?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 5.3 — Results and how much they generalize

**Prompt.** The headline result.

- What's the point estimate of the improvement over PIMC (or over the
  best baseline)?
- Do they see the same qualitative result on every game, or does
  ISMCTS shine on some and not others?
- The paper's claim: does ISMCTS *always* beat PIMC, or only when the
  game has a specific structure? Note the caveat carefully — it directly
  informs H1 in our project (see
  [`../docs/research.md`](../docs/research.md)).

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §6 — Limitations acknowledged by the authors

### 6.1 — Where does ISMCTS fail?

**Prompt.** Every paper's honest section is where they say when the
method won't work.

- What limitations do Cowling et al. acknowledge?
- Which are relevant to PTCG?
- Any that we should preemptively cite in the writeup's
  "Threats to Validity" section (which is Phase 6, but the material
  originates here)?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 6.2 — Non-locality — do they claim to solve it or acknowledge it as open? 🔄

**Prompt.** *Non-locality* is the phenomenon where an ISMCTS agent's
action reveals information to the opponent, so the opponent's
subsequent play is not modeled by the SO-ISMCTS assumption of
"opponent plays a perfect-info game".

- Do the authors claim ISMCTS resolves non-locality, or do they
  acknowledge it as an outstanding problem?
- Long et al. (2010) supposedly proves non-locality is *not* fatal to
  determinization-based methods under certain conditions. Cross-check:
  does Cowling cite Long? If yes, what's the relationship?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## Synthesis prompts — moved

Cross-source questions (which variant for PTCG, what Cowling leaves for
the implementer, predictions vs reality) live in
[`phase2-synthesis.md`](phase2-synthesis.md) as §CS.3, §CS.4, and §CS.5.
They fill after this paper is finished; the cross-source file is where
they belong so answers that pull from Browne, Cowling, and S&B stay in
one place.

---

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled if any come up during the read-through.)_
