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
- [`open-ideas.md`](open-ideas.md) — candidate ideas motivated by
  observations in this paper (informed determinization; oracle baseline).

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

Initially, I thought the main limitation of naive determinization was
that it could sample an incorrect hidden state. After studying the
paper, I realized that this is not the fundamental issue. The real
problem is that each determinization builds a policy assuming that the
sampled hidden information is the true game state. As a consequence,
different determinizations produce different optimal actions for
situations that are actually indistinguishable to the player. At
decision time, however, the player only observes an Information Set
and cannot condition its action on hidden information. This phenomenon
is known as Strategy Fusion. Although the paper also discusses
non-locality, Strategy Fusion is presented as the primary motivation
for introducing ISMCTS.

**Refined write-up.**

The paper identifies the primary weakness of naive determinization as
**Strategy Fusion**. In the standard determinization approach, a
complete hidden state is sampled and treated as if it were the true
game state, allowing a conventional UCT search to be performed.
Repeating this process over multiple determinizations creates
independent search trees, each learning a policy conditioned on a
different hidden state.

The resulting policy is fundamentally flawed because the player never
knows which determinization corresponds to reality. Instead of learning
a policy over the player's Information Set, naive determinization
implicitly learns policies over fully observable game states. This
allows the search to exploit hidden information that the real player
will never observe, violating the requirement that actions must depend
only on the information available to the acting player.

The paper also discusses **Non-locality** as another limitation of
determinization, highlighting that future observations can change the
value of current decisions. However, Strategy Fusion is the central
motivation for introducing Information Set Monte Carlo Tree Search
(ISMCTS). Although the authors do not explicitly use the terminology of
$I$-measurable policies, their argument is conceptually equivalent:
decision policies should depend only on the player's Information Set
rather than on the underlying hidden state.

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

I found it interesting that the paper does not present ISMCTS as a
replacement for determinization. Instead, it acknowledges that Perfect
Information Monte Carlo (PIMC) had already achieved strong results in
games such as Bridge and Skat. The authors recognize these successes
but argue that determinization suffers from fundamental issues such as
Strategy Fusion, Non-locality, and duplicated search effort across
independent trees. Their contribution is therefore evolutionary rather
than revolutionary: they preserve the idea of sampling determinizations,
but replace multiple independent search trees with a single Information
Set tree that shares statistics across compatible hidden states.

**Refined write-up.**

The paper places ISMCTS within the existing line of research on
**Perfect Information Monte Carlo (PIMC)** methods rather than
presenting it as a completely new paradigm. Previous successful
applications of determinization include Ginsberg's **GIB** system for
Bridge, which samples multiple card deals consistent with the current
information and solves each using a perfect-information ("double
dummy") search. Similar determinization-based approaches were also
state-of-the-art for **Skat**, while variants such as Sparse UCT and
HOP-UCT extended the same general idea to games like **Klondike
Solitaire**.

The paper distinguishes these approaches from work on **Poker**, where
belief distributions and opponent modeling play a much more prominent
role than naive determinization. Poker is therefore cited as motivation
for probabilistic inference rather than as a successful PIMC
application.

Rather than rejecting determinization, the authors argue that its
practical success should be preserved while addressing its fundamental
weaknesses. ISMCTS retains the idea of sampling determinizations, but
replaces multiple independent search trees with a single tree of
Information Sets. This allows search statistics to be shared across
compatible determinizations, reducing duplicated computation while
mitigating Strategy Fusion and providing a decision model that more
closely matches the information actually available to the player.

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

Before reading the paper, I thought of an Information Set simply as
the collection of states that produce the same observation for a
player, i.e., $I_i(s) = \{s' : O_i(s') = O_i(s)\}$. After studying the
formal definition, I realized that the paper adopts a richer
game-theoretic perspective. Information Sets are defined as
equivalence classes of states that a player cannot distinguish, and
these classes form a partition of the state space. Although the paper
does not explicitly define an observation function, the concept is
implicitly captured by the indistinguishability relation. Another
important aspect is that Information Sets evolve consistently with the
observed history of the game, making them closer to the formulation
used in extensive-form games than to the simplified observation-function
view commonly used in reinforcement learning.

**Refined write-up.**

The paper defines an **Information Set** as the set of game states
that are indistinguishable from the perspective of a given player.
Formally, each player is associated with a partition of the state
space, where every state belongs to exactly one Information Set. This
definition is conceptually equivalent to the observation-based
formulation

$$
I_i(s) = \{\, s' : O_i(s') = O_i(s) \,\},
$$

provided that the observation function induces the same equivalence
relation over states. However, the paper adopts the language of
extensive-form games rather than explicitly introducing an observation
function.

Compared with the formulation in `mdp-formalization.md`, the main
conceptual additions are the explicit treatment of Information Sets as
partitions of the state space and the fact that they evolve
consistently with the player's observation history. As the game
progresses and new information becomes available, impossible states
are eliminated and the current Information Set is refined. This
historical consistency is essential for ISMCTS, since search nodes
represent Information Sets rather than individual game states.

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

Initially, I viewed determinization as an attempt to guess the
opponent's hidden cards. After studying the paper, I realized that
this is not its purpose. A determinization is simply one complete game
state that is consistent with the current Information Set. The search
does not rely on a single "best guess"; instead, it repeatedly samples
plausible hidden states and uses them to perform simulations. The
paper assumes a simple sampling process, which is effectively uniform
over all compatible determinizations, but it also acknowledges that
better belief models could provide more realistic samples. This
distinction became particularly relevant when thinking about Pokémon
TCG, where the discard pile, revealed cards, and previous actions
provide strong evidence that should influence the sampling
distribution.

**Refined write-up.**

Formally, a **determinization** is a fully specified game state that
belongs to the player's current Information Set. If $I$ denotes the
Information Set, then any determinization satisfies

$$
h \in I,
$$

meaning that it is completely consistent with everything the player
has observed so far. During ISMCTS, each iteration samples one such
determinization, performs a standard MCTS simulation on the resulting
fully observable state, and updates the shared Information Set tree.

The paper assumes a simple sampling strategy that is effectively
uniform over all determinizations compatible with the current
Information Set. It does not introduce an explicit probabilistic
belief model or derive a posterior distribution over hidden states.
Instead, uniform sampling is treated as a practical baseline for the
proposed algorithm.

The authors acknowledge, however, that this assumption is often
unrealistic. In many imperfect-information games, previous observations
provide evidence that changes the posterior probability of hidden
states. For example, actions taken by an opponent, revealed cards, or
previously observed events can make some determinizations much more
likely than others. Although the paper does not propose a method for
belief estimation, it explicitly leaves room for more sophisticated
sampling strategies. This observation is particularly relevant for
Pokémon TCG, where information from the discard pile, revealed cards,
and game history naturally defines a non-uniform posterior over the
opponent's hidden hand. This is exactly the observation that motivated
the *informed-determinization* candidate idea in
[`open-ideas.md`](open-ideas.md) — the paper explicitly notes the door
is open here, but does not propose an algorithm to walk through it.

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

Before studying ISMCTS, I thought the algorithm simply averaged the
results of many determinizations. After reading the paper, I realized
that this is not what happens. The important difference is not that
multiple determinizations are sampled, but that all of them contribute
to a single Information Set tree. As a result, the algorithm evaluates
each action across many compatible hidden states before selecting the
best action. Conceptually, ISMCTS first averages the value estimates
over possible determinizations and only then applies the decision rule.
This is fundamentally different from naive determinization, which
independently finds the best action for each sampled state and
effectively averages policies rather than values.

**Refined write-up.**

The paper does not explicitly formulate ISMCTS using an expectation
over determinizations. Instead, it presents the algorithm procedurally:
each iteration samples a determinization compatible with the current
Information Set, performs one MCTS iteration using that fully
observable state, and updates a single shared Information Set tree.
After the computational budget is exhausted, the selected action is
the child of the root with the highest visit count.

Nevertheless, the behavior of the algorithm can be interpreted
mathematically as approximating

$$
a^* \;=\; \arg\max_a \; \mathbb{E}_{h \sim P(h \mid I)}\!\left[ Q(I, a, h) \right],
$$

where the expectation is taken over determinizations compatible with
the current Information Set.

This interpretation highlights the fundamental distinction between
ISMCTS and naive Perfect Information Monte Carlo (PIMC). In naive
determinization, each sampled hidden state independently computes its
own optimal action, which is conceptually equivalent to

$$
\mathbb{E}_h\!\left[ \arg\max_a Q(h, a) \right].
$$

In contrast, ISMCTS accumulates search statistics for each action
across many determinizations before making a single decision,
corresponding conceptually to

$$
\arg\max_a \; \mathbb{E}_h\!\left[ Q(I, a, h) \right].
$$

Although the paper does not express the algorithm in this probabilistic
notation, the shared Information Set tree implements exactly this
behavior by aggregating evidence before selecting an action. The swap
between $\arg\max$ and $\mathbb{E}$ is the mathematical core of what
distinguishes ISMCTS from naive PIMC and explains why ISMCTS mitigates
Strategy Fusion while naive PIMC does not.

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

SO-ISMCTS keeps the overall structure of classical MCTS but changes
the meaning of the search tree. Instead of representing fully
observable game states, each node corresponds to an Information Set
from the perspective of a single player — the root player making the
current decision. At the beginning of each iteration, one
determinization is sampled, and all four MCTS phases operate on that
hidden-state hypothesis.

Selection uses a bandit algorithm only over actions that are legal in
the sampled determinization, requiring the availability-count mechanism
introduced by the subset-armed bandit formulation. Expansion,
simulation, and backpropagation remain conceptually identical to
standard MCTS, except that statistics are accumulated in Information
Set nodes rather than state nodes.

The main limitation of SO-ISMCTS is that it models only the root
player's uncertainty. It does not explicitly represent the opponent's
Information Set or how the opponent's beliefs evolve after observing
actions. This limitation motivates the more advanced ISMCTS variants
introduced later in the paper.

**Refined write-up.**

**SO-ISMCTS (Single-Observer Information Set Monte Carlo Tree Search)**
constructs a single search tree from the perspective of the player
making the current decision. Every node represents one of that
player's Information Sets rather than a fully observable game state.
At the beginning of each iteration, a determinization compatible with
the current Information Set is sampled, and the search proceeds using
only actions that are legal in that determinization.

The four phases of MCTS remain structurally unchanged:

- **Selection:** descend the Information Set tree using UCB (or
  another bandit algorithm), considering only actions available in
  the sampled determinization. Because the set of legal actions may
  vary across determinizations, SO-ISMCTS introduces **availability
  counts** through the subset-armed bandit formulation.
- **Expansion:** when a compatible legal action has no corresponding
  child node, create a new Information Set node.
- **Simulation:** perform a rollout from the resulting determinized
  state using the sampled hidden information.
- **Backpropagation:** propagate the simulation reward through the
  visited Information Set nodes while updating both visit counts and
  availability counts.

The principal limitation of SO-ISMCTS is that it models only the root
player's uncertainty. Opponent Information Sets are not explicitly
represented, and the algorithm assumes that opponent actions are
fully observable from the root player's perspective. Consequently,
SO-ISMCTS cannot model how the opponent updates its own beliefs after
observing actions, motivating the introduction of SO-ISMCTS+POM and
MO-ISMCTS later in the paper.

Our ADR-001 commits Phase 3 to **SO-ISMCTS** for the baseline
implementation. The rationale is timeline-driven: SO-ISMCTS is the
smallest algorithmic step from classical MCTS to information-set
search, keeps the implementation load manageable within the Aug 16-17
deadline, and directly tests H1. MO-ISMCTS becomes a candidate
extension only if H1 succeeds and time remains.

---

### 3.2 — MO-ISMCTS (Multiple-Observer)

**Prompt.** The paper introduces MO-ISMCTS as a more accurate model.

- What does MO-ISMCTS model that SO-ISMCTS doesn't? (Concretely: the
  opponent has their own information set and their own tree, and moves
  reveal information to the opponent.)
- What's the computational cost of MO-ISMCTS vs SO-ISMCTS?
- Note the paper's empirical comparison: which one wins on which games?

**My take.**

MO-ISMCTS extends the algorithm by maintaining a separate Information
Set tree for each player rather than modeling the game only from the
root player's perspective. Each tree represents the corresponding
player's own uncertainty about the true game state, so opponents are
no longer assumed to see the full determinization the way SO-ISMCTS
implicitly assumes.

The practical consequence is that when a player takes an action, the
tree structure updates coherently across all trees, but each tree
receives only the information observable to its own player. This makes
opponent modeling explicit: the opponent's Information Set changes as
observable actions accumulate, and the search rewards actions that
account for what the opponent will and will not learn.

The cost is roughly a factor of $k$ (number of players) more
bookkeeping — separate trees, separate statistics, and coordination
between them at each iteration. In two-player games this is a $2\times$
overhead, which is significant but far from prohibitive.

**Refined write-up.**

**MO-ISMCTS (Multiple-Observer Information Set Monte Carlo Tree
Search)** replaces the single tree of SO-ISMCTS with one tree per
player, each representing that player's own uncertainty about the
true game state. When a player takes an action, the trees update
coherently: the acting player observes their own move fully, while
opponents update their own trees using only whatever is observable to
them. This structure makes opponent modeling explicit rather than
implicit — the opponent's beliefs are represented and evolve during
search, so decisions can be rewarded for the information they reveal
or withhold from the opponent.

The computational cost scales roughly linearly with the number of
players: two trees for a two-player game, three for three-player, and
so on. Each tree requires its own selection, expansion, and
backpropagation, and the coordination between trees adds constant
overhead. For our two-player PTCG setting, this is roughly a $2\times$
cost multiplier over SO-ISMCTS.

Empirically, the paper reports mixed results across games:

- In **Lord of the Rings: The Confrontation**, MO-ISMCTS consistently
  outperforms both SO-ISMCTS and Determinized UCT. The authors
  attribute the improvement to more accurate opponent modeling.
- In **Phantom (4,4,4)**, MO-ISMCTS again achieves the strongest
  performance among non-oracle algorithms, particularly in
  information-asymmetric configurations.
- In **Dou Di Zhu**, MO-ISMCTS does not consistently beat SO-ISMCTS.
  The paper attributes this to the extreme branching factor of the
  game, which limits how deeply either algorithm can search regardless
  of opponent-model quality.

The overall pattern is that MO-ISMCTS wins when opponent belief
updates carry decision-relevant information *and* the branching factor
allows the search to exploit that information. In branching-limited
regimes, the additional cost of maintaining multiple trees is not
recovered by better opponent modeling.

For Pokémon TCG, the relevant question is whether opponent belief
updates carry enough decision-relevant information to justify the
$2\times$ cost. This is captured in
[`open-ideas.md`](open-ideas.md) as a candidate Phase 5 or
post-competition extension — MO-ISMCTS is a natural amendment ADR
candidate if H1 succeeds and time permits.

---

### 3.3 — SO-ISMCTS+POM (Partially Observable Moves)

**Prompt.** The third variant refines SO-ISMCTS by recognizing that
some opponent moves are only partially observable to the root player.

- What problem does SO-ISMCTS+POM fix over plain SO-ISMCTS?
- How does the paper argue this reduces effective branching from the
  root player's perspective?
- How does its cost compare with MO-ISMCTS?

**My take.**

SO-ISMCTS treats opponent moves as fully observable — the root
player's tree contains a distinct child for every legal opponent
action. But in many real games this overcounts: several opponent
actions may look identical from the root player's viewpoint. If the
opponent plays "a Trainer card face-down" and the root player only
sees that a card was played (not which one), then multiple concrete
opponent actions all correspond to the same observed event.

SO-ISMCTS+POM (Partially Observable Moves) groups opponent actions by
their observable equivalence class from the root player's perspective.
The tree now has one child per observable class rather than one child
per concrete action, which reduces the effective branching factor
without needing the full MO-ISMCTS machinery.

The idea is elegant: capture much of the correctness benefit of
MO-ISMCTS (respecting what the opponent's move actually reveals to the
root player) at a much smaller cost, since only one tree is
maintained.

**Refined write-up.**

**SO-ISMCTS+POM (Partially Observable Moves)** is an extension of
SO-ISMCTS that recognizes when opponent actions are only partially
observable to the root player. In plain SO-ISMCTS, each concrete
opponent action creates a distinct child of the current
Information-Set node. This overcounts when multiple concrete actions
appear identical from the root player's perspective — for example,
when the opponent plays a face-down card and the root player observes
only that a card was played, not which one.

SO-ISMCTS+POM introduces an equivalence relation on opponent actions
based on what the root player can observe. Actions that produce
identical observations are grouped into a single **observable move**
class, and the tree branches on these classes rather than on concrete
actions. During determinization, the concrete action within each
observable class is sampled from the compatible hidden states.

The computational cost is modest — a single tree is maintained, the
same as SO-ISMCTS, so the overhead is limited to the equivalence-class
lookup during selection and expansion. Compared with MO-ISMCTS,
SO-ISMCTS+POM captures a substantial fraction of the "respect
partial observability" benefit without the multi-tree bookkeeping
overhead.

Our ADR-001 commits Phase 3 to plain SO-ISMCTS, but SO-ISMCTS+POM is
the natural first refinement to consider if Phase 3 succeeds and time
allows before the Sep 13 deadline. In PTCG, most opponent actions are
fully observable (attacks, energy attachments, card plays are all
visible), so the effective gain from SO-ISMCTS+POM may be smaller than
in the paper's card games — this is worth flagging as an empirical
question rather than assuming the paper's results transfer.

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

At first, I assumed that ISMCTS simply reused the same UCB1 rule from
classical MCTS. After studying the algorithm, I realized that the
exploration formula itself is almost unchanged, but the statistics
behind it are different. Since not every action is available in every
determinization, ISMCTS replaces the parent's visit count with an
availability count, ensuring that actions are compared only when they
could actually have been selected.

This also made me realize that the reward distribution seen by a node
is not perfectly stationary. Different determinizations may produce
different outcomes for the same action during a single search, making
the problem closer to a contextual or non-stationary bandit than to
the original UCB1 setting. The paper addresses this pragmatically
through availability counts, but it does not provide a formal proof
that ISMCTS converges to the optimal policy.

**Refined write-up.**

ISMCTS preserves the exploration principle of **UCB1**, but adapts the
statistics used by the selection rule to account for imperfect
information. Instead of using only the parent visit count as in
classical UCT, the algorithm introduces an **availability count**,
which records how many times an action was actually available for
selection across sampled determinizations. This modification follows
directly from the subset-armed bandit formulation introduced earlier
in the paper.

Because each iteration samples a different determinization, the
empirical reward associated with a given action is aggregated over
many compatible hidden states. Consequently, the reward distribution
observed by a node is not strictly stationary during a single search.
Although the paper does not frame this as a contextual or
non-stationary bandit problem, the underlying assumptions of classical
UCB1 are no longer satisfied exactly. The availability-count mechanism
is introduced as a practical correction for this setting rather than
as a theoretically derived optimal solution.

Unlike UCT, the paper does **not** provide a proof of asymptotic
consistency or convergence for ISMCTS. Instead, the authors validate
the algorithm empirically across several imperfect-information games
and explicitly acknowledge that stronger theoretical analysis remains
an open research direction.

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

One aspect of ISMCTS that I initially found confusing was how a single
Information Set tree could handle determinizations with different
legal actions. The key insight is that the tree is shared, but action
selection is always performed using the currently sampled
determinization. During each iteration, only actions that are legal in
that determinization participate in UCB selection, while unavailable
actions are ignored. This is exactly why the algorithm maintains
availability counts separately from visit counts.

Expansion follows the same idea. A child node is created only when
the corresponding action is legal in the sampled determinization. As
different determinizations are explored over time, the shared
Information Set tree gradually acquires children corresponding to
different legal actions.

For Pokémon TCG, this idea transfers naturally, but the legal-action
generator is considerably more complex because action legality depends
not only on hidden information, such as the cards in hand, but also on
public board state and game-specific rules.

**Refined write-up.**

In SO-ISMCTS, different determinizations belonging to the same
Information Set may expose different sets of legal actions. The
algorithm handles this by evaluating only the actions that are legal
in the currently sampled determinization. During selection, unavailable
actions simply do not participate in the UCB comparison, and the
**availability count** introduced by the subset-armed bandit
formulation ensures that exploration statistics remain unbiased across
determinizations.

Expansion is likewise defined relative to the sampled determinization
rather than to the Information Set as a whole. When the search
encounters a legal action that has no corresponding child node, a new
Information Set node is created. As additional determinizations are
sampled over successive iterations, new legal actions may become
available, causing the shared tree to expand progressively.

This mechanism transfers naturally to Pokémon TCG, where many legal
actions depend on hidden information such as the player's hand or
future card draws. However, the game introduces additional constraints
that are not emphasized in the paper. The legality of Trainer cards,
evolutions, and other actions often depends simultaneously on hidden
information, public board state, and game-specific rules. Consequently,
a practical Pokémon implementation would likely require a dedicated
**Legal Action Generator** capable of evaluating action legality for
each sampled determinization before the ISMCTS selection step.

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

I initially expected the experimental section to evaluate ISMCTS on a
large collection of games. Instead, I realized that each selected
game isolates a different challenge of imperfect-information search.
Lord of the Rings: The Confrontation evaluates planning under moderate
hidden information, Phantom (4,4,4) exposes the weaknesses of naive
determinization through severe information uncertainty, and Dou Di Zhu
stresses the algorithm with an extremely large branching factor.

Rather than comparing against weak baselines such as random agents,
the paper compares several closely related search algorithms,
including Determinized UCT (PIMC), SO-ISMCTS, SO-ISMCTS+POM,
MO-ISMCTS, and an oracle-like Cheating UCT. This experimental design
isolates the contribution of Information Set search itself.

For Pokémon TCG, I believe Dou Di Zhu is structurally the closest
domain because both games suffer from a very large action space.
However, Pokémon also shares important characteristics with Phantom
through hidden information and with Lord of the Rings through
long-term strategic planning.

**Refined write-up.**

The paper evaluates ISMCTS on three imperfect-information games, each
emphasizing a different computational challenge.

- **Lord of the Rings: The Confrontation** features moderate hidden
  information, relatively low branching factor, and strong strategic
  planning. It serves as a controlled environment for comparing
  search algorithms.
- **Phantom (4,4,4)** is almost entirely characterized by hidden
  information while maintaining a small branching factor. This
  domain exposes the shortcomings of naive determinization,
  particularly Strategy Fusion.
- **Dou Di Zhu** combines imperfect information with a very large
  branching factor and three-player interactions, making action-space
  complexity the dominant challenge rather than hidden information
  alone.

The experimental baselines are other MCTS-based search methods rather
than trivial opponents. Specifically, the paper compares **Cheating
UCT** (an oracle upper bound with full state information),
**Determinized UCT (Perfect Information Monte Carlo)**, **SO-ISMCTS**,
**SO-ISMCTS+POM**, and **MO-ISMCTS**. This design isolates the effect
of representing Information Sets while keeping the underlying search
framework largely unchanged.

**This directly validates our own methodology.** The
*oracle-baseline-cheating-uct* candidate idea in
[`open-ideas.md`](open-ideas.md) proposes exactly the Cheating UCT
baseline that this paper already uses. Cowling et al. treat it as an
upper-bound reference; we should treat it identically. The paper
establishes precedent for using Cheating UCT as a diagnostic
instrument, not as a competitor.

None of the evaluated games perfectly matches Pokémon TCG. However,
**Dou Di Zhu** is arguably the closest from an algorithmic
perspective because both domains exhibit a large branching factor and
require efficient action selection. Pokémon TCG also shares important
properties with **Phantom**, due to hidden information, and with
**Lord of the Rings**, due to long-term strategic planning.
Consequently, the architecture developed for Pokémon should combine
insights from all three experimental domains rather than relying on a
single analogy.

---

### 5.2 — Metrics and statistical rigor

**Prompt.** Compare their reporting standards with our
[`../docs/benchmark-protocol.md`](../docs/benchmark-protocol.md).

- Do they report win rates with confidence intervals? Which family?
- Do they use paired testing on shared match seeds?
- How many matches per comparison? Is it consistent with our $N = 500$
  target for Phase 5 hypothesis tests, or lower?

**My take.**

One aspect that impressed me is that the paper does not rely only on
raw win rates. The authors consistently report **95% confidence
intervals**, using **Clopper–Pearson intervals** by treating each game
as a Bernoulli trial. This already represents good experimental
practice for its time.

However, compared to a modern benchmarking protocol, the statistical
methodology is still relatively lightweight. The paper does not
explicitly describe paired evaluations using shared random seeds or
matched initial conditions as a formal statistical design, even
though it often controls player positions and starting configurations.

The number of evaluation games varies across experiments, typically
ranging from about **500 to 1000 games**, which is remarkably close to
the $N = 500$ target adopted in our benchmark protocol. For our
Pokémon TCG project, I would keep a similar sample size but complement
it with paired tests, effect sizes, and more modern confidence
interval estimators.

**Refined write-up.**

The paper reports experimental performance primarily in terms of
**win rate**, accompanied by **95% confidence intervals**. The authors
explicitly state that these intervals are **Clopper–Pearson confidence
intervals**, treating each game outcome as an independent Bernoulli
trial. This provides an appropriate measure of uncertainty for binary
win/loss outcomes and represents good experimental practice for the
time.

The experimental methodology controls several important factors, such
as alternating player positions and, in some experiments, repeating
evaluations under both fixed and randomized initial configurations.
However, the paper does not explicitly describe a paired statistical
design based on shared random seeds or matched game instances, nor
does it report paired hypothesis tests or effect sizes.

The number of evaluation games varies across experiments rather than
being fixed globally. Representative values include approximately
**500 games** for several pairwise comparisons, **750 games** for some
Lord of the Rings experiments, and **1000 games** for Dou Di Zhu
evaluations and comparisons against the commercial AI.

Compared with our `benchmark-protocol.md`, the paper is broadly
aligned regarding sample size — the commonly used range of 500-1000
games is consistent with our target of $N = 500$ for hypothesis
testing. Our protocol, however, proposes a more modern evaluation
methodology by additionally recommending paired experiments with
shared seeds, explicit hypothesis tests, effect-size reporting, and
more robust confidence interval estimators where appropriate.

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

The experimental results changed my understanding of ISMCTS. I
initially expected the paper to conclude that ISMCTS universally
outperforms Determinized UCT. Instead, the evidence is much more
nuanced. ISMCTS clearly outperforms determinization in domains where
Information Set search reduces Strategy Fusion and where concentrating
the computational budget on a single shared tree enables deeper
planning. However, these advantages disappear when the branching
factor becomes too large.

The Dou Di Zhu experiments are particularly important because they
demonstrate that the larger Information Set tree may become a
liability. When each Information Set accumulates too many legal
actions from different determinizations, the search spends much of
its budget expanding new branches rather than exploiting promising
ones. This suggests that controlling tree growth is as important as
improving belief modeling.

For Pokémon TCG, this implies that the research question should not
be whether ISMCTS is universally better than PIMC, but under which
structural conditions ISMCTS becomes superior.

**Refined write-up.**

The paper does not claim that ISMCTS universally outperforms Perfect
Information Monte Carlo (Determinized UCT). Instead, its empirical
results demonstrate that the effectiveness of ISMCTS depends strongly
on the structural properties of the game domain.

In **Lord of the Rings: The Confrontation**, MO-ISMCTS consistently
outperforms Determinized UCT, with statistically significant
improvements. The authors attribute this to two complementary effects:
reduced Strategy Fusion and deeper search resulting from concentrating
the entire computational budget on a single Information Set tree
rather than distributing it across multiple independent determinizations.

In **Phantom (4,4,4)**, MO-ISMCTS again achieves the strongest
performance among the non-oracle algorithms. The benefits arise
primarily from more faithfully representing players' information and
reducing Strategy Fusion. However, the simpler SO-ISMCTS variant does
not consistently outperform Determinized UCT, highlighting the
importance of opponent modeling in highly information-asymmetric
games.

In **Dou Di Zhu**, the overall performance of ISMCTS is approximately
equal to Determinized UCT. The paper argues that the advantage of
searching a single Information Set tree is largely offset by the
dramatically larger branching factor created by the union of legal
actions across many determinizations. Consequently, the search spends
much of its computational budget expanding previously unseen actions
instead of exploiting promising ones. The authors explicitly identify
controlling branching factor as an important direction for future work.

These results suggest that ISMCTS is **not** universally superior to
PIMC. Rather, its advantages emerge when the game permits sufficiently
deep search and when the benefits of sharing information across
determinizations outweigh the additional complexity introduced by
Information Set trees. This observation directly motivates our
project hypothesis: in Pokémon TCG, ISMCTS should outperform
Determinized UCT only if mechanisms such as Progressive Widening and
effective action prioritization successfully control the branching
factor.

The Dou Di Zhu result is worth flagging in the Phase 6 writeup's
Threats to Validity: if PTCG's effective branching factor at mid-game
approaches Dou Di Zhu's, we should expect ISMCTS's advantage over
Determinized UCT to shrink accordingly. This is a testable prediction
and belongs alongside H1 as an interpretive caveat.

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

One of the main lessons I took from this paper is that ISMCTS should
not be viewed as a complete solution for imperfect-information games.
The authors explicitly acknowledge several situations in which its
performance degrades. The most important is the rapid growth of the
branching factor caused by combining legal actions from many
compatible determinizations. As the tree becomes larger, more
computational effort is spent expanding new actions instead of
refining existing value estimates.

The paper also treats belief sampling as an external component rather
than part of the algorithm itself. While ISMCTS can search efficiently
over sampled determinizations, its performance ultimately depends on
the quality of those samples. Likewise, the algorithm does not
explicitly learn opponent-specific strategies and provides no
theoretical convergence guarantees comparable to those available for
UCT.

For Pokémon TCG, these limitations are directly relevant. A large
branching factor, imperfect belief estimation, and the absence of
opponent modeling are likely to be among the main challenges of a
practical implementation.

**Refined write-up.**

Cowling et al. explicitly acknowledge that ISMCTS is **not** a
universal solution for imperfect-information games. The most
significant limitation identified in the paper is the growth of the
branching factor. Because a single Information Set tree must
accommodate the union of legal actions arising from many compatible
determinizations, nodes near the root can become substantially larger
than in Determinized UCT. As demonstrated in the Dou Di Zhu
experiments, this reduces search efficiency by allocating an
increasing fraction of the computational budget to expanding new
actions rather than exploiting promising ones.

The paper also assumes relatively simple belief sampling.
Determinizations are generated externally to the search algorithm,
and no explicit probabilistic model is proposed for estimating
posterior distributions over hidden states. The authors acknowledge
that richer belief models could improve search quality, but this
problem remains outside the scope of the paper.

Additional limitations include the lack of explicit opponent modeling
and the absence of theoretical convergence guarantees comparable to
those established for UCT. The evaluation is therefore primarily
empirical rather than theoretical.

These limitations are directly relevant to Pokémon TCG. Large
branching factors, uncertainty over hidden cards, and computational
budget constraints are central characteristics of the domain.
Consequently, they should be explicitly acknowledged as **Threats to
Validity** in the project write-up. In particular, internal validity
depends on a correct simulator and legal-action generator, construct
validity depends on the quality of the belief model and rollout
policy, and external validity depends on the diversity of decks, game
situations, and metagame environments used during evaluation.

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

When I first encountered the discussion on Non-locality, I expected
ISMCTS to solve it together with Strategy Fusion. After studying the
paper more carefully, I realized that this is not the authors' claim.
ISMCTS primarily addresses Strategy Fusion by searching over
Information Sets rather than independent determinizations. However,
it does not fully model how players update their beliefs after
observing each other's actions, meaning that Non-locality remains an
open challenge.

The paper acknowledges this limitation rather than claiming to
eliminate it. Even MO-ISMCTS provides a better representation of
different players' perspectives, but it is not presented as a complete
solution to belief updating in imperfect-information games.

I also found it interesting that the authors cite Long et al. (2010),
who argue that Non-locality does not necessarily invalidate
determinization-based approaches. Instead of contradicting this view,
Cowling et al. position ISMCTS as an improvement that mitigates
important weaknesses of determinization without claiming to solve
every limitation of imperfect-information search.

**Refined write-up.**

The paper does **not** claim that ISMCTS completely resolves the
problem of **Non-locality**. Instead, the authors focus primarily on
mitigating **Strategy Fusion** by replacing independent determinization
trees with a shared Information Set tree. While this substantially
improves decision making under hidden information, it does not fully
capture how players update their beliefs after observing one another's
actions. Consequently, Non-locality remains an open challenge rather
than a solved problem.

This limitation is particularly evident in **SO-ISMCTS**, where the
search is constructed entirely from the root player's perspective.
Opponents do not maintain explicit Information Sets, nor do they
update their beliefs during the simulation. Although **MO-ISMCTS**
introduces separate Information Sets for multiple players and better
represents differing perspectives, the paper does not present it as a
complete solution to belief updating or Non-locality.

The paper explicitly cites **Long et al. (2010)**, who argue that
Non-locality does not necessarily invalidate determinization-based
search methods under all circumstances. Cowling et al. adopt a
consistent position: rather than rejecting determinization entirely,
they acknowledge its practical success while introducing ISMCTS as an
approach that alleviates some of its most important weaknesses —
especially Strategy Fusion — without claiming to eliminate every
limitation associated with imperfect-information search.

For a fuller treatment of the Long argument and its implications for
where PTCG will land on the "PIMC works well vs badly" axis, see
[`phase2-long-2010-notes.md`](phase2-long-2010-notes.md), which
covers the three properties (leaf correlation, bias, disambiguation)
Long uses to predict PIMC's effectiveness.

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

This paper fundamentally changed how I think about Monte Carlo Tree
Search in imperfect-information games. Before studying ISMCTS, I
viewed hidden information primarily as a state-estimation problem.
The paper showed that the more fundamental issue is the representation
of the search tree itself. Rather than building separate trees for
individual determinizations, ISMCTS searches directly over Information
Sets, allowing experience to be shared across multiple compatible
hidden states.

Several implementation insights emerged from this study. First, belief
modeling should be treated as a separate component responsible for
generating plausible determinizations rather than predicting a single
hidden state. Second, action legality must be evaluated separately for
each sampled determinization, making a dedicated legal-action
generator a natural architectural component. Third, controlling the
branching factor appears to be essential for large card games such as
Pokémon TCG, suggesting that Progressive Widening and action priors
should be considered core components rather than optional
optimizations.

Perhaps the most important lesson is that ISMCTS is not a universal
replacement for Perfect Information Monte Carlo. Its advantages depend
strongly on the structure of the domain, particularly the relationship
between hidden information, branching factor, and available
computational budget. This observation directly motivates the central
research hypothesis of the Pokémon TCG project.

## Failed Attempts

No implementation failures occurred during the reading process.
However, several initial assumptions were revised as the study
progressed.

- Initially, determinization was interpreted as an attempt to predict
  the opponent's hidden cards. The paper clarified that determinization
  is simply a sampled game state consistent with the current
  Information Set.
- Initially, ISMCTS appeared to be a straightforward extension of
  classical MCTS. The study revealed that its primary innovation is
  changing the search representation from fully observable states to
  Information Sets.
- Initially, I expected ISMCTS to solve all major issues associated
  with determinization. Instead, the paper demonstrates that it mainly
  addresses Strategy Fusion, while Non-locality, belief modeling, and
  large branching factors remain important open problems.
- Initially, I viewed branching factor as an implementation concern.
  After studying the experimental results, it became clear that
  branching factor is one of the dominant factors determining when
  ISMCTS outperforms Determinized UCT.
