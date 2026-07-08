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
  [`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md).
- **Synthesis prompts** that compare Browne, Cowling, and S&B live in
  [`phase2-synthesis.md`](phase2-synthesis.md), not at the end of this
  file. Cross-source questions belong there so answers stay in one
  place.

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

Before the introduction of Monte Carlo Tree Search (MCTS), game-playing
agents were primarily based on minimax search combined with
$\alpha$-$\beta$ pruning and handcrafted evaluation functions. This
approach worked well in games such as Chess, where intermediate
positions can be evaluated accurately using domain-specific heuristics
(material balance, king safety, piece activity).

However, this paradigm reached its limits in games like Go. Although Go
has a much larger branching factor and significantly deeper search
trees than Chess, the main obstacle was the lack of a reliable
heuristic evaluation function. Classical minimax relies on estimating
the value of non-terminal positions, and when these estimates are poor,
deeper search provides little benefit.

MCTS addressed this limitation by replacing handcrafted state
evaluation with statistical estimation through Monte Carlo simulations.
Instead of asking "How good is this position?", MCTS asks "What happens
if I repeatedly play games from this position?". By averaging the
outcomes of many simulated games, the algorithm estimates the value of
actions without requiring an explicit evaluation function.

Another key innovation is that MCTS does not explore the search tree
uniformly. By combining Monte Carlo sampling with a bandit-based tree
policy (UCT), it concentrates computational effort on the most
promising regions of the search tree while still exploring uncertain
alternatives. This property enabled a dramatic improvement in
Go-playing strength and established MCTS as the dominant search
paradigm for domains where heuristic evaluation is difficult or
unavailable.

**Refined write-up.**

Although Go's enormous branching factor and search depth contributed to
the difficulty of the domain, the survey emphasizes that the
fundamental limitation of classical minimax was its dependence on
accurate heuristic evaluation functions. MCTS shifted the paradigm from
heuristic evaluation to statistical estimation through simulation,
making it practical to search domains where reliable evaluation
functions were unavailable.

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

MCTS is considered a breakthrough because it fundamentally changed how
search algorithms estimate the quality of decisions. Instead of relying
on handcrafted heuristic evaluation functions, it estimates action
values through repeated simulations. This made it possible to apply
search effectively in domains where designing reliable heuristics is
extremely difficult.

Another important contribution is that MCTS naturally balances
exploration and exploitation through the Upper Confidence bounds
applied to Trees (UCT). Rather than expanding the search tree
uniformly, the algorithm allocates computational resources adaptively,
concentrating simulations on promising branches while still exploring
uncertain alternatives.

Finally, MCTS is an anytime algorithm. Even with a limited
computational budget it produces a valid decision, and as more
simulations are performed, the quality of its estimates generally
improves. This scalability made MCTS practical across a wide range of
decision-making problems, from board games to planning and
optimization.

**Refined write-up.**

Monte Carlo Tree Search is considered a breakthrough because it
replaced handcrafted heuristic evaluation with statistical estimation
through simulation. Instead of attempting to evaluate positions
directly, MCTS estimates the quality of actions by observing the
outcomes of many simulated games. Its integration of Monte Carlo
sampling with UCT provides an effective balance between exploration
and exploitation, allowing computational effort to be focused on the
most informative regions of the search tree. Furthermore, its anytime
property enables progressively better decisions as additional
computation becomes available, making MCTS both theoretically elegant
and highly practical across a broad range of sequential
decision-making problems.

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

The basic Monte Carlo Tree Search algorithm is composed of four
iterative phases: Selection, Expansion, Simulation, and
Backpropagation. Each iteration improves the search tree by collecting
additional statistical evidence about the quality of available actions.

During Selection, the algorithm starts from the root node and
repeatedly selects child nodes according to the tree policy, typically
UCT, until reaching a node that is not fully expanded.

During Expansion, one or more previously unexplored child nodes are
added to the search tree, increasing the portion of the state space
represented by the tree.

During Simulation (or rollout), the algorithm performs a simulated game
from the newly expanded node until reaching a terminal state. The
outcome of this simulation provides an estimate of the state's value.

Finally, Backpropagation propagates the simulation result back through
all nodes visited during the iteration, updating statistics such as
visit counts and average rewards. Repeating this cycle thousands of
times gradually improves the quality of the search tree.

**Refined write-up.**

A basic Monte Carlo Tree Search iteration consists of four sequential
phases: Selection, Expansion, Simulation, and Backpropagation.
Selection traverses the existing tree using a tree policy such as UCT
to identify the most promising leaf node. Expansion introduces one or
more previously unexplored child nodes into the tree. Simulation
performs a rollout from the newly expanded node to obtain an estimate
of the outcome. Finally, Backpropagation updates the statistics of
every node visited during the iteration using the simulation result.
Repeating this process allows the search tree to concentrate
computational effort on increasingly promising regions of the state
space.

> **Reviewer's note (Claude).** The current answer is a good overview
> of the whole four-phase loop but does not directly address the
> tree-policy vs default-policy distinction the prompt asks about. When
> you revisit, focus on: (i) does S&B use "tree policy" and "default
> policy" as separate terms? (ii) why is separating them useful — what
> concretely breaks if a single UCB1 policy is used both inside the
> tree and past the leaf? The current answer implicitly assumes they
> differ but never says so explicitly.

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

_(pending — the current draft in this slot was actually about UCT /
selection, not expansion. Moved to §3.1 as material to build on.
When you refill this prompt, focus specifically on the expansion
policies enumerated in the survey: expand-one-child-per-iteration,
expand-all-children-at-once, expand-only-on-second-visit, and the
trade-offs between them.)_

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

The Simulation phase is responsible for estimating the value of newly
expanded nodes. Since these nodes initially contain little or no
statistical information, MCTS cannot determine whether they represent
promising decisions based solely on the existing tree.

A rollout consists of simulating a complete game from the expanded node
until reaching a terminal state. The outcome of this simulation
provides an estimate of the expected reward associated with that state.
This estimate is then propagated back through the tree during the
Backpropagation phase.

The quality of the rollout policy directly influences the quality of
the value estimates. While the original MCTS algorithm often uses
random simulations, many practical implementations replace purely
random rollouts with heuristic or learned policies to produce more
realistic evaluations and reduce simulation noise.

**Refined write-up.**

The Simulation phase provides the statistical evidence required to
evaluate newly expanded nodes. By performing a rollout from the current
state to a terminal state, MCTS estimates the expected outcome of
choosing that branch. Without this step, the algorithm would have no
information to propagate during Backpropagation, making it impossible
to distinguish promising actions from poor ones. Consequently, the
effectiveness of MCTS depends strongly on the quality of its rollout
policy, which is why many modern implementations replace purely random
simulations with heuristic or learned policies.

> **Reviewer's note (Claude).** The prompt has three sub-questions and
> the current answer covers the general "simulations matter" story but
> not the specifics. When you revisit, aim to answer: (i) how does the
> survey define "uniformly random"? (ii) what's the paper's "light vs
> heavy rollout" trade-off argument? (iii) **most important for us**:
> where does the survey say heuristic rollouts *hurt*? This is the
> passage that pre-registers H2 (heuristic vs random rollouts) in a
> non-trivial way — H2 is defensible precisely because the survey
> acknowledges the outcome could go either direction.

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

The Backpropagation phase is responsible for updating the statistical
information stored in the search tree after each simulation. Once a
rollout reaches a terminal state, its outcome is propagated back
through every node visited during that iteration.

Rather than updating model parameters as in neural networks, MCTS
backpropagation updates simple statistics such as visit counts and
average rewards. These statistics become the basis for future Selection
decisions, allowing the algorithm to progressively improve its
estimates as more simulations are performed.

Without Backpropagation, each simulation would be independent, and the
search tree would never accumulate knowledge from previous experiences.

**Refined write-up.**

Backpropagation transforms individual simulation outcomes into
accumulated knowledge. After each rollout reaches a terminal state, the
observed reward is propagated through every node visited during that
iteration, updating statistics such as visit counts and average
rewards. Unlike neural network backpropagation, this process does not
involve gradients or parameter optimization; it simply accumulates
statistical evidence that guides future exploration. As a result, each
simulation improves the quality of subsequent decisions by making the
search tree progressively more informative.

> **Reviewer's note (Claude).** The general treatment is good. The
> prompt has two specific sub-questions still open: (i) does the survey
> cover weighted backup variants (depth-decaying, importance-sampled)?
> and (ii) does it discuss backprop under imperfect-info? Both matter
> for Phase 3 architectural choices — the first informs whether we
> should use anything fancier than the sample-average $\alpha = 1/n$
> update we derived in
> [`phase2-rl-foundations.md`](phase2-rl-foundations.md) §2.2; the
> second is where Cowling picks up the story.

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

_(pending — an earlier draft in this slot was about backpropagation
and has been moved to §2.4. Also, there was a partial UCT/selection
discussion in §2.2 that's better developed here. When you fill this
prompt, focus on the nested-bandit non-stationarity story specifically,
building on the intuition from `phase2-rl-foundations.md` §2.5.)_

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

_(pending — an earlier draft in this slot was about RAVE and has been
moved to §4.2, where the RAVE prompt lives. When you fill this prompt,
focus on empirical convergence rate, which nodes stabilize first, and
what that implies for our sims-per-decision budget.)_

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

An enhancement in Browne et al.'s taxonomy is a technique that improves
the practical performance of Monte Carlo Tree Search without modifying
its fundamental four-phase search loop (Selection, Expansion,
Simulation, and Backpropagation). Unlike algorithmic variations such as
RAVE or Progressive Widening, enhancements focus on improving
efficiency, memory usage, or computational throughput while preserving
the underlying algorithm.

Representative enhancements from the survey:

| Enhancement | Compatible with ISMCTS? | Comments |
|---|---|---|
| Transposition Tables | Partially | Applicable when equivalent information sets can be identified. More difficult than in perfect-information games because hidden information complicates state equivalence. Detailed in §4.5 below. |
| Root Parallelization | Yes | Multiple independent MCTS trees run in parallel and their statistics are combined. Independent of the underlying game representation. |
| Leaf Parallelization | Yes | Multiple rollouts launched from the same leaf node. Fully compatible with imperfect-information search. |
| Tree Parallelization | Yes | Multiple workers share the same search tree. Requires synchronization but does not depend on perfect information. |
| Solver Nodes | Limited | Works well in deterministic perfect-information games but is generally harder to apply in imperfect-information domains because game-theoretic values are often unknown. |

For our Pokémon TCG project, parallelization techniques appear to be
the most promising exploratory enhancements, since they directly
increase the number of simulations within a fixed time budget without
changing the search algorithm itself. Transposition Tables may also be
interesting, although defining equivalence between information sets is
considerably more challenging than in perfect-information games — this
line is developed as a candidate idea in
[`open-ideas.md`](open-ideas.md) under *transposition-tables-for-info-sets*.

**Refined write-up.**

Among the surveyed enhancements, parallelization offers the highest
implementation value for our project. It is conceptually simple,
preserves the core MCTS algorithm, and scales almost linearly with the
available computational resources. Transposition Tables are also
attractive, but correctly identifying equivalent information sets in
Pokémon TCG is substantially more complex due to hidden information;
that line has been captured as a candidate Phase 5 exploratory
experiment in [`open-ideas.md`](open-ideas.md).

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

Both RAVE (Rapid Action Value Estimation) and MAST (Move-Average
Sampling Technique) are based on the idea that useful statistical
information can be reused beyond the exact path traversed during a
simulation. Rather than learning only from simulations that pass
through a specific node, they exploit information gathered from any
rollout in which an action appears.

RAVE was proposed to accelerate learning during the early stages of
MCTS. In the standard algorithm, a node only receives information from
simulations that pass directly through it, so newly expanded nodes
often suffer from high variance due to low visit counts. RAVE addresses
this by sharing information between different branches: if an action
appears in a successful rollout, RAVE assumes that this action may also
be valuable in similar contexts, allowing its estimated value to be
updated even when it was not selected at the exact position where it
appears in the tree.

The primary trade-off is the classic bias–variance trade-off. Standard
MCTS estimates have low bias but high variance when visit counts are
small. RAVE intentionally introduces bias by assuming that an action
performing well in one context is likely to perform well in similar
contexts. In return, it dramatically reduces variance during the early
stages of the search, allowing value estimates to converge much faster.
As more simulations accumulate, the algorithm gradually relies less on
RAVE estimates and more on the direct statistics gathered by standard
MCTS.

This assumption becomes problematic when the quality of an action
depends strongly on the surrounding state. In highly tactical positions
or domains with strong context dependence, reusing action statistics
across different states may produce misleading estimates.

In imperfect-information games, this limitation becomes even more
significant. The same action may correspond to very different hidden
game states (determinizations), meaning that statistics collected in
one rollout may not generalize to another. Applying RAVE directly to
ISMCTS therefore requires care, as the underlying assumption that "the
same move has a similar value" may no longer hold. This is precisely
the observation that motivates the candidate
*archetype-conditioned-rave* idea in [`open-ideas.md`](open-ideas.md):
condition RAVE statistics on the inferred opponent archetype so the
"same-move-same-value" assumption is applied only *within* archetypes,
where it is much more likely to hold.

**Refined write-up.**

RAVE accelerates value estimation by sharing action statistics across
different parts of the search tree, intentionally trading increased
bias for reduced variance during the early stages of the search. This
assumption is beneficial when similar actions tend to have similar
values across related states, allowing useful information to be reused
before sufficient node-specific statistics are available. However, RAVE
becomes less effective when action quality is highly context-dependent,
as transferring statistics between dissimilar states can produce
misleading value estimates. This limitation is even more pronounced in
imperfect-information games, where the same action may correspond to
different hidden states (determinizations), weakening the assumption
that action values are transferable across rollouts. A promising
adaptation for our domain is to condition RAVE statistics on the
inferred opponent archetype (see
*archetype-conditioned-rave* in [`open-ideas.md`](open-ideas.md)).

---

### 4.3 — Progressive Bias

**Prompt.** Progressive Bias adds a heuristic term to the selection
score that dominates early (when visit counts are low) and fades as
node-specific statistics accumulate.

- What is the formal form of the bias term in the survey?
- What kind of heuristic can serve as the bias — evaluator output,
  domain rules, learned prior?
- When does Progressive Bias fail, and how is that distinguished from
  RAVE's failure mode?

**My take.**

Progressive Bias was introduced to incorporate domain knowledge into
MCTS without permanently overriding the statistical evidence gathered
during search. In the early stages, newly expanded nodes contain very
little information, making the search policy highly uncertain.
Progressive Bias addresses this by temporarily incorporating heuristic
evaluations into the selection policy, helping guide the search toward
actions that are believed to be promising according to expert
knowledge.

As the number of visits increases, the influence of the heuristic
gradually decreases. Eventually, the decision process becomes dominated
by the empirical statistics collected through simulations, preserving
the asymptotic behavior of the original MCTS algorithm while improving
its performance during the initial search phase.

**Refined write-up.**

Progressive Bias incorporates heuristic domain knowledge into the
selection policy of Monte Carlo Tree Search. Because newly expanded
nodes initially contain little statistical information, heuristic
evaluations provide useful guidance during the early search phase.
Unlike fixed heuristic search methods, the influence of these
heuristics progressively decreases as more simulations are performed,
allowing empirical statistics to dominate the decision process. This
approach combines the benefits of expert knowledge with the long-term
accuracy of simulation-based learning. In our project, Progressive Bias
is a natural companion to the Phase 4 evaluator (ADR-003), since the
evaluator can serve directly as the bias term without additional
engineering work.

---

### 4.4 — Progressive Widening

**Prompt.** Progressive Widening (PW) limits the number of children of
a node as a function of its visit count: at $v$ visits, at most
$\lceil c \cdot v^\alpha \rceil$ children are expanded.

- What is the formal form of the widening schedule in the survey?
- Which parameters are tunable and what do they trade off?
- In our high-branching-factor setting, is PW a Phase 3 baseline
  addition or a Phase 5 exploratory add-on?

**My take.**

Progressive Widening was introduced to address search problems with
extremely large branching factors. In the standard MCTS algorithm,
expanding every legal action as soon as a node is visited can quickly
become computationally infeasible, especially in domains with hundreds
or thousands of possible actions.

Instead of expanding all children immediately, Progressive Widening
limits the number of child nodes that can be created based on the
number of visits to the parent node. As more simulations are performed,
additional actions are gradually introduced into the search tree. This
strategy allows MCTS to allocate computational resources more
efficiently by focusing on the most promising actions first while still
guaranteeing that less explored actions can eventually be considered
if sufficient computational budget is available.

**Refined write-up.**

Progressive Widening addresses the challenge of extremely large action
spaces by controlling how quickly the search tree expands. Rather than
generating all possible child nodes immediately, the algorithm
gradually introduces new actions as the parent node receives more
visits. This allows computational effort to be concentrated on
evaluating the most promising actions first while preventing the search
from being overwhelmed by an excessive branching factor. As additional
computation becomes available, the search space naturally widens to
include more alternatives. Combined with an action-ranking function
(see *progressive-widening-with-action-ranking* in
[`open-ideas.md`](open-ideas.md)), this becomes a strong candidate for
Phase 5 exploratory work in our high-branching-factor domain.

---

### 4.5 — Transposition Tables

**Prompt.** Transposition Tables let different tree paths that lead to
the same state share statistics.

- What is the survey's formal treatment of the correctness condition
  (when is sharing legitimate)?
- Are Transposition Tables cheaper or more expensive than they look —
  what is the hashing/comparison cost per node?
- Does the survey acknowledge the difficulty of extending Transposition
  Tables to imperfect-information games? Where?

**My take.**

Transposition Tables are used to avoid storing duplicate representations
of the same game state. In many sequential decision problems, different
sequences of actions can lead to exactly the same state. A standard
tree representation would create multiple nodes for these equivalent
states, wasting both memory and computational effort.

A Transposition Table stores previously explored states using a unique
representation (typically a hash). Before creating a new node, the
algorithm checks whether the corresponding state has already been
visited. If so, the existing node is reused instead of creating a
duplicate.

By sharing statistics across equivalent states, Transposition Tables
improve memory efficiency and reduce redundant simulations, allowing
computational resources to be focused on genuinely unexplored parts of
the search space.

**Refined write-up.**

Transposition Tables eliminate redundant representations of identical
states reached through different action sequences. By storing
previously explored states in a hash table, MCTS can reuse existing
nodes instead of creating duplicates whenever the same state is
encountered again. This sharing of statistical information improves
memory efficiency, reduces redundant simulations, and allows
computational effort to be directed toward unexplored regions of the
search space. In imperfect-information games such as PTCG, the
correctness of transpositions depends on equivalence of information
sets rather than states, which is substantially harder to check.
[`open-ideas.md`](open-ideas.md) captures a candidate approach under
*transposition-tables-for-info-sets*.

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

The survey highlights several domains where Monte Carlo Tree Search
achieved remarkable success, particularly in games with enormous search
spaces and weak heuristic evaluation functions. Among the most notable
examples are Go, Hex, Amazons, and General Game Playing, where MCTS
significantly outperformed traditional minimax-based approaches. These
games share common characteristics: very large branching factors, deep
search trees, and the absence of reliable handcrafted evaluation
functions.

On the other hand, MCTS achieved more limited success in domains such
as Chess and Checkers, where decades of research had already produced
highly optimized heuristic evaluation functions and $\alpha$-$\beta$
search techniques. In these games, classical search algorithms remained
highly competitive because strong domain knowledge was available.

Regarding card games, the survey discusses applications to
imperfect-information games such as Poker and Bridge, demonstrating
that MCTS can be extended beyond perfect-information domains. However,
these applications required additional techniques to handle hidden
information and stochasticity. The survey does not discuss Magic: The
Gathering or Pokémon-style trading card games, although these domains
naturally share many of the same challenges, including hidden
information, randomness, and large action spaces.

Looking back from today's perspective, the survey correctly anticipated
that MCTS would become a general framework rather than merely a
Go-playing algorithm. It also recognized the importance of integrating
domain knowledge and improving rollout policies. However, because it
predates AlphaGo (2016), it could not foresee how deeply neural
networks would transform MCTS. The survey largely assumes that stronger
search comes from better simulations and search enhancements, whereas
modern systems obtain much of their strength from learned policy and
value networks.

**Refined write-up.**

The survey demonstrates that MCTS achieved its greatest success in
games such as Go, Hex, Amazons, and General Game Playing, all
characterized by enormous search spaces and the absence of strong
heuristic evaluation functions. Conversely, its advantages were less
pronounced in Chess and Checkers, where highly optimized $\alpha$-$\beta$
search combined with expert-crafted heuristics remained extremely
effective. The survey also discusses imperfect-information games,
particularly Poker and Bridge, but does not address modern trading card
games such as Magic: The Gathering or Pokémon TCG, despite their
similar characteristics. In retrospect, the survey correctly identified
MCTS as a general planning framework and anticipated many future
research directions, including improved rollout policies and
domain-specific enhancements. However, published before AlphaGo, it did
not anticipate that learned policy and value networks would eventually
replace many of the handcrafted enhancements proposed throughout the
survey. Perhaps the survey's greatest prediction was recognizing MCTS
as a flexible planning framework rather than merely another search
algorithm; what it could not anticipate was that many of the heuristic
components it discusses — rollout policies, search biases — would
eventually be learned automatically by deep neural networks,
fundamentally changing the role of MCTS in modern game-playing systems.

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

The survey recognizes imperfect-information games as one of the major
extensions of Monte Carlo Tree Search beyond deterministic
perfect-information domains. It explicitly discusses applications to
games such as Poker and Bridge, where players must reason under
uncertainty because the complete game state is not observable.

Rather than proposing a single solution, the survey presents
determinization as the dominant approach used by existing algorithms.
In this framework, hidden information is sampled to generate one or
more fully observable game states, allowing standard MCTS to operate on
each sampled determinization. The survey discusses determinization as
an established technique but largely defers implementation details and
sampling strategies to the cited literature rather than advocating a
particular method.

The survey also highlights that determinization introduces important
limitations because different sampled states may recommend incompatible
actions. This observation motivates later developments such as ISMCTS,
which reasons directly over information sets instead of individual
determinizations.

Regarding the literature, Browne et al. reference several works on
imperfect-information MCTS, including Long et al. (2010). They also
cite Cowling, Powley, and Whitehouse (2012), introducing Information
Set Monte Carlo Tree Search as a promising direction for handling
hidden information without relying exclusively on determinization.

**Refined write-up.**

The survey identifies imperfect-information games as an important
frontier for Monte Carlo Tree Search and discusses applications in
domains such as Poker and Bridge. It describes determinization as the
prevailing strategy, where hidden information is sampled to create
fully observable states on which conventional MCTS can be applied.
Rather than prescribing a specific sampling method, the survey refers
readers to the existing literature for implementation details. At the
same time, it acknowledges the fundamental limitations of
determinization, particularly the possibility that different sampled
states lead to inconsistent action recommendations. These observations
naturally motivate Information Set Monte Carlo Tree Search (ISMCTS),
and the survey explicitly references the work of Cowling et al. (2012)
alongside earlier contributions such as Long et al. (2010).

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

The survey does not explicitly use the term strategy fusion, which was
introduced by Frank & Basin (1998). However, it acknowledges the
fundamental limitations of applying standard MCTS to
imperfect-information games through determinization-based approaches.

Rather than naming the phenomenon directly, Browne et al. discuss the
practical shortcomings of determinization, particularly the fact that
different sampled determinizations may produce inconsistent or
conflicting action recommendations. The survey presents this as one of
the motivations for newer approaches such as ISMCTS.

The vocabulary used throughout the survey focuses on concepts such as
determinization, imperfect-information games, information sets, and the
limitations of applying perfect-information search methods to partially
observable environments. The survey generally defers the formal
discussion of strategy fusion to the referenced literature instead of
introducing the term itself.

This observation is useful for Exercise 02.4 because it shows that the
survey recognizes the underlying problem while framing it as a
limitation of determinization rather than explicitly discussing
strategy fusion.

**Refined write-up.**

Browne et al. do not explicitly use the term strategy fusion, but they
clearly acknowledge the underlying problem as a limitation of
determinization-based MCTS. The survey discusses how different
determinizations may lead to inconsistent action recommendations and
presents this as one of the motivations for ISMCTS. Rather than
adopting the terminology introduced by Frank & Basin (1998), the survey
frames the issue using concepts such as determinization, information
sets, and the challenges of extending MCTS to imperfect-information
games.

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

In its concluding section, the survey identifies several research
directions that remained open at the time. Among the most important:

- **Imperfect-information games.** While MCTS had achieved remarkable
  success in perfect-information domains, extending it to games with
  hidden information remained a major challenge. Existing
  determinization-based methods suffered from well-known limitations,
  motivating the development of ISMCTS and related approaches.
- **Improved simulation policies.** The survey recognized that the
  quality of rollouts strongly influenced search performance. Random
  simulations were often sufficient for simple domains but became
  increasingly ineffective in complex games. The authors anticipated
  that better simulation policies would be an important direction for
  future research.
- **Scalability to larger and more complex domains.** The survey
  highlighted challenges related to large branching factors,
  computational efficiency, parallelization, and memory usage. Several
  enhancements had already been proposed, but no general solution
  existed.

Looking back from today's perspective, some of these challenges have
been substantially addressed. The integration of deep neural networks
with MCTS, introduced by AlphaGo and later refined in AlphaZero,
largely replaced handcrafted rollout policies and dramatically improved
search quality. Parallel implementations and search optimizations have
also matured considerably.

However, imperfect-information planning remains an active research
area. Games involving hidden information, stochastic events, and
opponent modeling continue to require specialized algorithms such as
ISMCTS, belief-state planning, and modern POMDP methods. These
challenges remain directly relevant to Pokémon TCG, where uncertainty
about the opponent's hand, deck order, and future draws fundamentally
shapes the decision-making process.

**Refined write-up.**

Browne et al. identified several important open problems in 2012,
including extending MCTS to imperfect-information games, improving
rollout policies, and scaling the algorithm to increasingly complex
decision spaces. Since then, many of these challenges have been
substantially addressed through the integration of deep neural
networks, particularly in AlphaGo and AlphaZero, which largely replaced
handcrafted rollout policies with learned policy and value functions.
Nevertheless, planning under imperfect information remains an active
research problem. Hidden information, stochastic transitions, and
opponent modeling continue to motivate algorithms such as ISMCTS and
belief-state planning, making these topics directly relevant to our
Pokémon TCG project. One of the most interesting aspects of the survey
is that many of its research directions anticipated the evolution of
modern game-playing AI: while deep learning solved several challenges
related to heuristic evaluation and rollout quality, its discussion of
imperfect-information games remains remarkably relevant, and for
projects such as ours these open problems continue to define the state
of the art.

---

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled if any come up during the read-through.)_
