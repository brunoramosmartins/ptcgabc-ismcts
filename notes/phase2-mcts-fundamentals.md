# Phase 2 — MCTS Fundamentals (Browne et al. 2012 survey)

Reading-companion prompts for **Browne, C.B., Powley, E., Whitehouse, D.,
Lucas, S.M., Cowling, P.I., Rohlfshagen, P., Tavener, S., Perez, D.,
Samothrakis, S., & Colton, S. (2012).** *A Survey of Monte Carlo Tree
Search Methods.* IEEE Transactions on Computational Intelligence and AI
in Games, 4(1), 1–43.

Purpose: give you targeted questions to answer *while* reading the
survey. Fill each prompt as you encounter the material — don't try to
answer top-to-bottom before finishing the paper. Some prompts require
synthesis across sections; those are marked 🔄.

Template: **Prompt** → **My take** (your notes) → **Refined write-up**
(we co-produce later). Same convention as
[`phase2-rl-foundations.md`](phase2-rl-foundations.md).

Complementary references:
- S&B Ch 8 §8.11 covers MCTS — much shorter than Browne, useful to
  contrast the two presentations (Ex 8.4 in
  [`phase2-rl-foundations.md`](phase2-rl-foundations.md)).
- The Cowling ISMCTS paper is the next reading — walkthrough in
  [`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md). Some
  prompts here forward-reference that paper.

Living document during Phase 2; ends with `## Lessons Learned` and
`## Failed Attempts` at merge time.

---

## §1 — Introduction and framing

### 1.1 — What problem was MCTS invented to solve?

**Prompt.** The abstract and introduction motivate MCTS as an answer to
something specific.

- What was the state of the art in *game tree search* before MCTS?
- What made minimax + $\alpha$-$\beta$ hit a wall — was it the branching
  factor, the depth, or something about heuristic quality?
- The paper frames MCTS as the enabling algorithm for Go strength going
  from "amateur" to "professional". What specifically did MCTS do that
  minimax couldn't?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 1.2 — MCTS's positioning between exact and approximate methods

**Prompt.** In the taxonomy the survey lays out early on (dynamic
programming, best-first heuristic search, Monte Carlo methods), where
does MCTS sit?

- What does MCTS borrow from bandits (Ch 2 of S&B)?
- What does it borrow from Monte Carlo evaluation (dice/rollouts)?
- What does it borrow from tree search (best-first exploration)?
- Which pieces are genuinely novel to MCTS — i.e. what wasn't in any of
  the three prior families?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §2 — The MCTS algorithm (four-phase loop)

### 2.1 — Selection: tree policy vs. default policy 🔄

**Prompt.** Browne distinguishes between the *tree policy* (used inside
the built tree) and the *default policy* (used during rollout, in the
unexplored region).

- Compare the paper's definitions with S&B Ch 8 §8.11's presentation.
  Does S&B use both terms? If not, which does it implicitly assume?
- Why is it useful to separate the two? What could go wrong if you used
  the same policy for both phases?
- Preview for Phase 3: our project uses UCB1 as the tree policy (per
  ADR-001) and random rollout as the default policy (per Phase 3), with
  a Phase 4 pivot to heuristic-guided default (per ADR-003 and H2). Note
  where in the survey each of these choices is discussed.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.2 — Expansion policies

**Prompt.** The survey enumerates several expansion strategies (expand
one child per iteration, expand all children at once, expand only on
second visit, etc.).

- What is Browne's default recommendation and why?
- Which strategy would waste the most search budget in PTCG's high-
  branching-factor setting? Justify (link back to
  [`phase2-rl-foundations.md`](phase2-rl-foundations.md) §8.3 on
  sample-vs-expected updates).

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.3 — Simulation / rollout policies

**Prompt.** The rollout / simulation phase runs from the newly expanded
leaf to a terminal state. The survey covers many rollout policy
variants.

- What is a "uniformly random" rollout, and where does the survey say
  it's sufficient versus insufficient?
- What are "heavy" rollouts (light rollouts have no domain knowledge;
  heavy rollouts do)? What are the trade-offs?
- The paper likely discusses when a heuristic-guided rollout *hurts*
  performance. Find that passage. Why does adding "smart" domain
  knowledge sometimes make MCTS worse? (This is critical for H2 in our
  project — we're testing exactly this claim.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.4 — Backpropagation: what gets updated, and how

**Prompt.** In the backpropagation phase, statistics on every node
visited during selection get updated with the rollout's terminal value.

- Is the update always a simple running average, or does the survey
  cover weighted variants (e.g. depth-decaying, importance-sampled)?
- Note whether the survey discusses backpropagation under
  imperfect-information settings. If it does, does it commit to a
  particular convention, or defer?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §3 — UCT (Upper Confidence bounds applied to Trees)

### 3.1 — From UCB1 to UCT: what changes when the bandits are nested?

**Prompt.** UCT is UCB1 applied at every internal node. But UCB1 was
proven for a *stationary* bandit — the true expected reward per arm
doesn't change over time.

- How does the survey acknowledge the non-stationarity issue (link back
  to [`phase2-rl-foundations.md`](phase2-rl-foundations.md) §2.5)?
- Where does the paper cite Kocsis & Szepesvári (2006) for asymptotic
  consistency? What conditions does the theorem require?
- The paper likely discusses the choice of the exploration constant
  $c$. What does it say about tuning $c$ for different domains?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 3.2 — Convergence in practice vs in theory

**Prompt.** Theoretical consistency is $N \to \infty$. In practice, the
search runs for a finite budget.

- What does the survey say about the practical rate of convergence?
- Which nodes converge fastest — root children? Deep nodes? Nodes with
  the highest branching factor?
- The implication for our project: how many simulations at the root are
  "enough" before we should trust the argmax? Compare with
  [`../exercises/ex02_mcts_derivations.md`](../exercises/ex02_mcts_derivations.md)
  Ex 02.5 (branching factor at a mid-game PTCG state).

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §4 — Variations and enhancements

### 4.1 — What is an "enhancement" in the survey's taxonomy? 🔄

**Prompt.** Browne separates *variations* of MCTS (algorithmic changes)
from *enhancements* (add-ons that don't change the core loop).

- List 3-5 enhancements the survey covers.
- For each, note whether it's compatible with an imperfect-information
  setting (i.e. does it survive when tree nodes are indexed by
  information sets rather than states?).
- Any of them worth considering for our Phase 5 exploratory work? (H1-H4
  don't cover enhancements — those are Phase 5 "exploratory" experiments
  per [`../docs/research.md`](../docs/research.md).)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 4.2 — RAVE, MAST, and the "all-moves-as-first" idea

**Prompt.** The survey covers RAVE (Rapid Action Value Estimation) and
MAST (Move-Average Sampling Technique) at some length. Both share a
core idea: use information from *any* rollout that visited a state, not
just those where the search reached that state.

- What is the trade-off RAVE is trying to buy — bias for variance?
- Under what conditions does RAVE hurt?
- Does RAVE make sense in an imperfect-information game where "the same
  move" means different things in different determinizations? (Preview
  for Cowling.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §5 — Applications

### 5.1 — Which games has MCTS worked well on?

**Prompt.** The applications section is a laundry list of MCTS successes
and failures across game domains.

- List 3-4 games where MCTS clearly won, and 1-2 where it hasn't. What
  are the common properties of each group?
- Where do card games appear (or fail to appear) in the survey?
  Specifically: do they discuss any of Bridge, Poker, Magic: The
  Gathering, or Pokémon-style games?
- The paper predates AlphaGo (2016). Does it anticipate what would
  come next? What did the survey get right, and what did it miss?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §6 — Imperfect information (setup for Cowling)

### 6.1 — What does the survey say about hidden information? 🔄

**Prompt.** This is the direct bridge to your next reading (Cowling).

- Find every passage in the survey that mentions hidden information,
  imperfect information, or partial observability.
- Does the survey discuss determinization? If yes, does it commit to a
  particular sampling strategy, or defer to the referenced papers?
- Does it cite Cowling (2012) or Long et al. (2010)? If the paper is
  2012 and Cowling is 2012, one may reference the other — check who
  cites whom.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 6.2 — Strategy fusion — is it named as such in the survey? 🔄

**Prompt.** The term *strategy fusion* is coined in Frank & Basin (1998)
and central to
[`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md).

- Does Browne use the term? If not, does the survey discuss the
  underlying phenomenon under a different name?
- If the survey acknowledges the problem without naming it, what
  vocabulary does it use? (E.g. "policy commitment across
  determinizations", "belief-state aggregation".)
- Note this for Ex 02.4 (toy example of strategy fusion) — the survey's
  framing may sharpen the toy example.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## §7 — Open problems and outlook

### 7.1 — What did Browne think was open in 2012?

**Prompt.** The final section usually lists open problems.

- What are 2-3 problems the survey flagged as "not yet solved"?
- Which of those have been solved since? (Just note which, no need to
  research — the state-of-the-art shift after AlphaGo is well-known.)
- Any open problems that are *still* open and *relevant* to our
  Pokémon-TCG project?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## Synthesis prompts (fill after finishing the survey)

### S.1 — Sutton & Barto's MCTS vs Browne's MCTS

**Prompt.** Compare S&B Ch 8 §8.11 with the corresponding sections in
Browne.

- Which one is more mathematically precise?
- Which is more useful as an *implementation reference*?
- Which sections of Browne would you skip if re-reading only for
  implementation guidance vs conceptual understanding?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### S.2 — What Browne does *not* prepare you for

**Prompt.** Before opening the Cowling paper, write down what you
*expect* Cowling to add on top of Browne. This is the "prediction
before reading" exercise that makes the next paper stick.

- What algorithmic modification do you expect for imperfect information?
- What experimental setup would you expect them to use (game, baseline,
  metric)?
- What theoretical guarantee (if any) do you expect them to prove?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending — compare against your predictions after reading Cowling.)_

---

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled if any come up during the read-through.)_
