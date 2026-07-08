# Phase 2 — RL Foundations (Sutton & Barto Ch 1–3, 8)

Working notes and self-derived material extending the exercises in
[`../exercises/sutton-barto-ch01.md`](../exercises/sutton-barto-ch01.md),
[`../exercises/sutton-barto-ch02.md`](../exercises/sutton-barto-ch02.md),
[`../exercises/sutton-barto-ch03.md`](../exercises/sutton-barto-ch03.md),
and [`../exercises/sutton-barto-ch08.md`](../exercises/sutton-barto-ch08.md).

Distinction from the exercise files: the exercise files answer the book's
questions verbatim. This file explores concepts that come up while reading
but aren't asked about directly — derivations, connections to the ISMCTS
project, and questions worth flagging for later.

Every section below is a **prompt**. Fill in your interpretation first
(bullet points are fine, no LaTeX needed), then ping me to refine into
publishable form.

Living document during Phase 2; ends with `## Lessons Learned` and
`## Failed Attempts` at merge time.

## Complementary reading (non-canonical)

*AI Engineering from Scratch* (aiengineeringfromscratch.com) —
Phase 09 covers RL from a practitioner's angle. Treats the same
material as S&B but with more code-first framing and modern-LLM
context (RLHF, GRPO). Useful as a second pass or a sanity check on
S&B's more formal treatment; **not authoritative**, and the site's
own conventions (Build-Use-Ship, "skill files", MDP-refuse checklists)
are opinionated and do not map onto this project's structure. Use the
lessons and exercises; ignore the framing overlay.

Specific lessons cross-referenced in this file:
- Phase 09 · 01 — MDPs, States, Actions & Rewards → coding exercises
  adapted in [`../notebooks/phase2-gridworld-mdp.py`](../notebooks/phase2-gridworld-mdp.py).

## Pending exercises (do not lose track)

Reading:
- [ ] **Browne et al. (2012) survey** → answer prompts in
  [`phase2-mcts-fundamentals.md`](phase2-mcts-fundamentals.md).
- [ ] **Cowling et al. (2012) ISMCTS paper** → answer prompts in
  [`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md).
- [ ] *(optional)* Long, Sturtevant, Buro & Furtak (2010) — no
  companion note file; jot findings directly in the ISMCTS notes §6.2.
- [ ] Cross-source synthesis (comparisons across S&B, Browne, Cowling)
  → answer prompts in
  [`phase2-synthesis.md`](phase2-synthesis.md), *after* the individual
  readings are done.

Code / hands-on:
- [ ] **`notebooks/phase2-gridworld-mdp.py`** — fill in the three
  GridWorld exercises (Easy: 10k rollouts and gap-to-optimal; Medium:
  `policy_evaluation` with $\gamma \in \{0.5, 0.9, 0.99\}$; Hard:
  stochastic-slip variant and comparison). Wrap up with the
  PTCG-vs-GridWorld comparison table at the end of the notebook.
  ~1h of code + ~30min of reflection.

Fill-ins in this file:
- [ ] **X.1 and X.2 cross-chapter connections below** — still empty.
- [ ] **`## Lessons Learned` and `## Failed Attempts`** — populate at
  merge time.

---

## Ch 1 — Introduction

### 1.1 — The agent–environment boundary is a design choice

**Prompt.** S&B Ex 3.3 uses driving to argue that the boundary between
"agent" and "environment" is not fundamental — it's a modeling decision.
For our project:

- Where did we draw the boundary in [`../env/`](../env/)?

Our project places the boundary at the interface exposed by the `env/`
wrapper. The agent is responsible only for selecting actions based on the
current observation, while the environment (`env/` together with the
underlying `cabt` engine) is responsible for enforcing game rules,
resolving card effects, updating the game state, handling stochastic
events such as shuffling, and returning the next observation and reward.
This follows the standard reinforcement learning abstraction in which the
agent defines the policy and the environment defines the transition
dynamics.

- Is there any place where the boundary "leaks" (e.g., the deck submission
  is technically an action of the agent, but it happens on turn 1 before
  the game starts)?

Yes. A good example is deck submission, which is technically a decision
made by the agent but occurs before the first environment interaction.
Once the match begins, the deck is fixed and becomes part of the
environment's initial conditions. Similar situations include match
initialization procedures, such as determining the starting player or
shuffling the deck. These decisions influence the episode but do not
belong to the standard observe–act–transition interaction loop.

- Would drawing the boundary *inside* the `cabt` engine (say, treating a
  full turn's worth of decisions as one action) change anything about the
  formalism?

The underlying reinforcement learning formalism would remain the same. We
would still model the problem in terms of states, actions, transitions,
rewards, and policies. However, moving the boundary would change the
problem formulation itself. For example, treating an entire turn as a
single action would reduce the number of decisions made by the agent,
decreasing the branching factor and search depth while also removing
opportunities for the agent to learn fine-grained strategies. In
practice, the choice of boundary affects computational complexity and
the range of behaviors the agent can discover.

**My take.**

At first, I thought the agent–environment boundary was mostly an
implementation detail. After studying this chapter and relating it to
our Pokémon project, I realized that it is one of the most important
modeling decisions. The boundary determines which decisions the agent
is allowed to optimize and directly influences the size of the action
space, the search complexity, and the strategies the agent can learn.

A concrete example came from my own experience playing Pokémon TCG
Pocket. Initially, automatically attaching Energy seemed like a
reasonable simplification. However, some Pokémon deal damage
proportional to the Energy attached to the opponent's Active Pokémon.
In these situations, intentionally delaying an Energy attachment can be
the strategically optimal move. If Energy attachment were automated by
the environment, the agent would never have the opportunity to discover
or exploit this strategy. This example reinforced that simplifying the
environment can unintentionally remove meaningful decisions from the
learning problem.

**Refined write-up.**

The agent–environment boundary is not an intrinsic property of the
problem but a modeling decision. In our project, we place the boundary
between the decision-making algorithm (ISMCTS) and the game engine. The
agent chooses legal actions based on the current observation, while the
environment is responsible for applying game rules, updating the state,
and generating future observations.

Although different boundaries preserve the reinforcement learning
formalism, they define different optimization problems. Moving the
boundary inside the game engine — for example, treating an entire turn
as a single action — would reduce computational complexity but also
remove strategic decisions from the agent. Consequently, the choice of
boundary directly affects the search space, the strategies available to
the agent, and the overall capabilities of the learning system.

---

### 1.2 — State-value vs. action-value learning

**Prompt.** The tic-tac-toe example in Ch 1 learns state values $V(s)$, not
action values $Q(s, a)$.

- Why does the book choose $V$ here?
- What would need to change to learn $Q$ instead in the same setup?
- Our project uses $Q(I, a, h)$ internally in ISMCTS. Why not $V$?
- General trade-off: when is $V$ enough, and when do you need $Q$?

**My take.**

Initially, I thought that learning state values was simply a stepping
stone toward learning action values. After revisiting the tic-tac-toe
example, I realized that this is not the main reason Sutton introduces
$V(s)$. In tic-tac-toe, each legal action deterministically leads to a
known successor state, so evaluating the successor state's value is
enough to choose the next move. Learning $Q(s, a)$ would also work, but
it would introduce additional complexity without providing significant
benefits.

Our Pokémon project is fundamentally different. A single action may lead
to multiple possible future states because of hidden information,
stochastic effects, and the opponent's response. Instead of asking "How
good is this state?", the search algorithm asks "How good is taking this
action from the current information state?". This made it much clearer
why ISMCTS naturally estimates action values instead of state values.

**Refined write-up.**

The tic-tac-toe example uses state-value learning because the environment
is fully observable and deterministic. Each legal action produces a known
successor state, allowing the agent to evaluate all candidate moves by
comparing the values of their resulting states. In this setting, learning
$V(s)$ is sufficient to derive a policy.

Learning $Q(s, a)$ would require storing and updating values for every
state–action pair rather than for states alone. Although feasible, it
would increase the representation size without substantially improving
decision making for this task.

Our ISMCTS implementation instead estimates $Q(I, a, h)$, where $I$ is
the information state and $h$ represents the search history. Unlike
tic-tac-toe, Pokémon contains hidden information and stochastic
transitions, so a single action can produce many possible future states.
Estimating action values directly allows the search algorithm to compare
decisions under uncertainty using empirical returns gathered during
simulations.

In general, learning $V(s)$ is sufficient when successor states are
easily generated and evaluated. Learning $Q(s, a)$ becomes preferable
when actions have uncertain outcomes, hidden information, or when the
agent must compare decisions directly without enumerating deterministic
successor states.

---

## Ch 2 — Multi-armed Bandits

### 2.1 — Four flavors of exploration

**Prompt.** $\epsilon$-greedy, softmax, UCB, and optimistic initial values
are four ways to parameterize the exploration–exploitation trade-off.

- What does each one say about *what* to explore?

Each exploration strategy defines a different criterion for selecting
actions whose values are still uncertain.

- $\epsilon$-greedy explores by randomly selecting an action with
  probability $\epsilon$, regardless of its estimated value. Every action
  has a chance to be sampled.
- Softmax (Boltzmann exploration) assigns probabilities according to the
  estimated action values. Better actions are explored more often, but
  weaker actions are still sampled occasionally.
- Optimistic Initial Values encourage exploration by initially
  overestimating every action. Actions are explored because their
  estimates must be corrected through experience.
- UCB (Upper Confidence Bound) explicitly explores actions with high
  uncertainty by combining the estimated value with a confidence bonus
  that decreases as an action is sampled more frequently.

- Which one does UCB1 (the algorithm ISMCTS uses at internal nodes)
  belong to? Why is UCB1 preferred for MCTS?

ISMCTS uses UCB1, which belongs to the Upper Confidence Bound family.
Unlike $\epsilon$-greedy or Softmax, UCB1 does not explore randomly.
Instead, it explicitly balances exploitation and exploration by favoring
actions that either have high estimated value or have been sampled only
a few times.

This makes UCB1 particularly suitable for MCTS because each node in the
search tree has a limited simulation budget. Every rollout is expensive,
so exploration should be directed toward actions whose values are still
uncertain rather than allocated uniformly at random.

- Would any of the other three fit better in an imperfect-information
  setting? (Think about what changes when the reward distribution is
  non-stationary because the tree grows below.)

In general, UCB1 remains the preferred choice because it adapts naturally
as the search tree evolves. In imperfect-information games such as
Pokémon, the reward distribution observed at a node is effectively
non-stationary: deeper parts of the tree become better estimated as new
simulations are added, changing the estimated value of ancestor actions
over time.

Methods such as optimistic initialization are primarily useful during the
beginning of learning and become less relevant as the tree grows.
$\epsilon$-greedy wastes simulations on uniformly random exploration,
while Softmax may overcommit to early value estimates when uncertainty is
still high. UCB1 explicitly accounts for uncertainty through visit
counts, making it more robust for incremental tree search.

**My take.**

Before reading this chapter, I viewed exploration mainly as a mechanism
to avoid getting stuck in poor decisions. The bandit formulation changed
my perspective: exploration is fundamentally about reducing uncertainty.
UCB made the most sense for our project because it does not explore
randomly — it prioritizes actions whose estimated values are still
unreliable. This aligns naturally with ISMCTS, where every simulation is
computationally expensive and should provide as much information as
possible.

**Refined write-up.**

The four exploration strategies differ in how they prioritize
uncertainty. $\epsilon$-greedy allocates a fixed fraction of decisions
to random exploration, Softmax samples actions proportionally to their
estimated values, optimistic initialization encourages early exploration
through biased value estimates, and UCB explicitly quantifies uncertainty
using confidence bounds.

ISMCTS adopts UCB1 because tree search operates under a limited
simulation budget. Instead of exploring uniformly, UCB1 directs
simulations toward actions that are either promising or insufficiently
explored. This improves sample efficiency while maintaining theoretical
guarantees on the exploration–exploitation trade-off.

In imperfect-information games such as Pokémon TCG, value estimates
evolve continuously as the search tree expands, making the reward
distribution effectively non-stationary. Among the classical bandit
strategies, UCB1 remains the most appropriate because its exploration
bonus naturally adapts to the uncertainty associated with each action as
additional simulations are performed.

---

### 2.2 — Deriving the running-mean formula

**Prompt.** The sample-average update
$Q_{n+1} = Q_n + \tfrac{1}{n}(R_n - Q_n)$ (S&B eq 2.3) can be derived from
the definition $Q_n = \tfrac{1}{n}\sum_{k=1}^{n} R_k$.

- Do the derivation step by step.

Starting from the definition of the sample average,

$$
Q_n \;=\; \frac{1}{n} \sum_{k=1}^{n} R_k,
$$

the next estimate after observing reward $R_{n+1}$ is

$$
Q_{n+1} \;=\; \frac{1}{n+1} \sum_{k=1}^{n+1} R_k.
$$

Expanding the summation,

$$
Q_{n+1} \;=\; \frac{1}{n+1} \left( \sum_{k=1}^{n} R_k + R_{n+1} \right).
$$

Using $\sum_{k=1}^{n} R_k = n Q_n$,

$$
Q_{n+1} \;=\; \frac{n Q_n + R_{n+1}}{n+1}.
$$

Rearranging,

$$
Q_{n+1} \;=\; Q_n \;+\; \frac{1}{n+1} \bigl( R_{n+1} - Q_n \bigr),
$$

which is the incremental update rule presented in Sutton & Barto (Eq. 2.3).

- Generalize to variable step size $\alpha_n$.

Replacing the fixed learning rate $1/(n+1)$ with a generic step size
$\alpha_n$,

$$
Q_{n+1} \;=\; Q_n + \alpha_n \bigl( R_{n+1} - Q_n \bigr).
$$

The parameter $\alpha_n$ determines how much weight is assigned to the
newest observation. Constant step sizes adapt more quickly to changing
reward distributions, whereas decreasing step sizes converge to the
sample average under stationary conditions.

- MCTS visit counts implement effectively this update with $\alpha_n = 1/n$.
  What does that imply for the variance of $Q$ estimates at MCTS nodes?

Using the incremental average means that each additional simulation has
progressively less influence on the estimated value of a node. As the
visit count increases, the variance of the estimate decreases because the
average is computed from more independent samples. Consequently,
frequently visited nodes tend to have more stable value estimates, while
newly expanded nodes remain highly uncertain and therefore receive a
larger exploration bonus through UCB1.

**My take.**

Initially, I viewed the incremental update mainly as a computational
optimization to avoid storing all previous rewards. After studying its
connection to MCTS, I realized that the update also has a statistical
interpretation. As more simulations are performed, the estimated value
becomes more stable because it is based on an increasingly large sample.
This explains why heavily visited nodes are trusted more during tree
search.

**Refined write-up.**

The incremental sample-average update provides an efficient way to
estimate action values without storing the entire reward history. By
rewriting the sample mean recursively, each new reward updates the
previous estimate using only the prediction error and an adaptive
learning rate.

Generalizing the update to an arbitrary step size produces the standard
stochastic approximation rule used throughout reinforcement learning. In
MCTS, visit counts naturally implement the special case $\alpha_n = 1/n$,
causing the estimated action values to converge toward the empirical
mean of observed returns. As more simulations visit a node, the variance
of its estimate decreases, making exploitation more reliable while
allowing UCB1 to focus exploration on nodes whose values remain
uncertain.

---

### 2.3 — Exponential recency-weighted average

**Prompt.** For constant step size $\alpha$, the update
$Q_{n+1} = Q_n + \alpha(R_n - Q_n)$ produces (S&B eq 2.6):

$$
Q_n \;=\; (1-\alpha)^n Q_0 \;+\; \sum_{k=1}^{n} \alpha (1-\alpha)^{n-k} R_k.
$$

- Expand the recurrence to show this identity.

Starting from the constant step-size update,

$$
Q_{n+1} \;=\; Q_n + \alpha (R_n - Q_n),
$$

we can rewrite it as

$$
Q_{n+1} \;=\; (1 - \alpha)\, Q_n + \alpha\, R_n.
$$

Substituting recursively,

$$
Q_n \;=\; (1 - \alpha) \bigl[ (1 - \alpha)\, Q_{n-1} + \alpha\, R_{n-1} \bigr] + \alpha\, R_n,
$$

which becomes

$$
Q_n \;=\; (1 - \alpha)^2 Q_{n-1} + \alpha (1 - \alpha)\, R_{n-1} + \alpha\, R_n.
$$

Repeating this expansion until $Q_0$,

$$
Q_n \;=\; (1 - \alpha)^n Q_0 \;+\; \sum_{k=1}^{n} \alpha (1 - \alpha)^{n-k} R_k.
$$

The coefficients form a geometric sequence whose weights sum to one (up
to the remaining weight on $Q_0$).

- Why does constant $\alpha$ "forget" old rewards?

With a constant learning rate, every new observation receives the same
weight $\alpha$, while the contribution of previous rewards is
multiplied by $(1 - \alpha)$ after each update. Consequently, older
observations receive exponentially smaller weights over time. The
estimate therefore emphasizes recent experience instead of converging to
the simple sample average.

- When would we *want* forgetting in an ISMCTS setting? (Hint: rewards
  are terminal Bernoulli in our case — probably never. Argue precisely.)

In our ISMCTS implementation, forgetting is generally not desirable.
Each node estimates the expected return of a fixed information state
during a single search, and the terminal rewards are Bernoulli outcomes
(win/loss). Since the underlying reward distribution does not change
while the search is running, older simulations remain just as
informative as recent ones. Using the sample average ($\alpha = 1/n$)
therefore produces an unbiased estimate with decreasing variance as the
visit count increases.

Constant step sizes are beneficial when the reward distribution is
non-stationary — for example, when the environment changes over time or
the agent's policy evolves continuously. Those conditions do not hold
inside a standard MCTS search, making exponential forgetting unnecessary
and potentially harmful.

**My take.**

Initially, I thought constant learning rates were simply another way to
update value estimates. This chapter helped me understand that they
encode an important assumption: recent observations should be trusted
more than older ones. For our ISMCTS implementation, that assumption is
generally false because every simulation estimates the same underlying
win probability for a fixed search node. In this setting, forgetting
would only increase the variance of the estimates by discarding useful
information.

**Refined write-up.**

The exponential recency-weighted average arises naturally when the
incremental update uses a constant learning rate. Unlike the sample
average, this estimator assigns exponentially decreasing weights to
older observations, allowing the estimate to adapt quickly when the
underlying reward distribution changes.

In ISMCTS, however, each search node estimates a stationary Bernoulli
distribution corresponding to the expected outcome from a fixed
information state. Since older rollouts remain valid evidence throughout
the search, exponential forgetting offers no advantage. The
sample-average update ($\alpha = 1/n$) is therefore preferable because
it uses all available simulations and yields progressively lower-variance
estimates as the visit count increases.

---

### 2.4 — Where UCB1's confidence bound comes from

**Prompt.** UCB1 picks $a^* = \arg\max_a \bigl[ Q(a) + c\sqrt{\tfrac{\ln
t}{n_a}} \bigr]$. The $\sqrt{\ln t / n_a}$ term is not arbitrary — it
comes from Chernoff–Hoeffding:

$$
\Pr\bigl(\lvert \hat X - \mu \rvert > \epsilon\bigr) \le 2 e^{-2 n \epsilon^2}
\qquad (\text{for } X \in [0,1]).
$$

- Solve for $\epsilon$ at fixed confidence level $1/t^\alpha$
  (concentration inequality applied per arm per time).

Starting from the Chernoff–Hoeffding inequality,

$$
\Pr\bigl(\lvert \hat X - \mu \rvert > \epsilon\bigr) \le 2 e^{-2 n \epsilon^2},
$$

we choose the failure probability to decrease with time,

$$
2 e^{-2 n \epsilon^2} \;=\; \frac{1}{t^{\alpha}},
$$

where $t$ is the total number of pulls (or node visits in MCTS).

Taking natural logarithms,

$$
-2 n \epsilon^2 \;=\; -\alpha \ln t - \ln 2.
$$

Therefore,

$$
\epsilon^2 \;=\; \frac{\alpha \ln t + \ln 2}{2 n},
$$

or

$$
\epsilon \;=\; \sqrt{\frac{\alpha \ln t + \ln 2}{2 n}}.
$$

For large $t$, the constant term $\ln 2$ becomes negligible.

- Show that this gives $\epsilon \sim \sqrt{\ln t / n_a}$.

Ignoring constant factors,

$$
\epsilon \;=\; \Theta\!\left( \sqrt{\frac{\ln t}{n}} \right).
$$

This means that uncertainty decreases proportionally to $1/\sqrt{n}$,
while the confidence requirement becomes more demanding as the search
progresses through the $\ln t$ term.

- What is $c$ in the final expression? (Answer: $\sqrt{2}$ in the
  standard derivation.)

The constant $c$ collects the constant factors omitted during the
asymptotic derivation. In the canonical derivation from Auer et al.
(2002) with $\alpha = 4$, the surviving constant is

$$
c \;=\; \sqrt{2}.
$$

In practice, however, $c$ is often treated as a tunable hyperparameter
that controls the exploration–exploitation trade-off. Larger values
encourage more exploration, while smaller values prioritize actions
already considered promising.

**My take.**

Before reading the derivation, I thought the exploration bonus in UCB1
was largely heuristic. The Hoeffding analysis showed that this term has
a probabilistic interpretation: it is a confidence interval around the
estimated action value. The more an action is sampled, the narrower this
interval becomes. Conversely, actions that have been sampled only a few
times retain larger uncertainty and therefore receive a larger
exploration bonus.

**Refined write-up.**

The exploration term in UCB1 is derived from concentration inequalities
rather than chosen heuristically. Applying the Chernoff–Hoeffding bound
yields a confidence interval whose width decreases proportionally to
$\sqrt{\ln t / n_a}$. This interval quantifies how uncertain the
empirical estimate remains after $n_a$ observations.

UCB1 selects the action with the highest upper confidence bound instead
of the highest empirical mean alone. Consequently, actions are explored
not because they are random alternatives, but because their true value
is still uncertain. The exploration constant $c$ originates as
$\sqrt{2}$ in the theoretical derivation, although it is commonly tuned
in practice to match the characteristics of the search problem.

---

### 2.5 — Bandits at every MCTS node

**Prompt.** Each internal node of an MCTS tree is a $k$-armed bandit over
its children.

- What is the "reward" seen at that bandit? (Answer: the eventual rollout
  outcome that propagates back up.)

At each internal node, every legal action corresponds to one arm of a
multi-armed bandit. The reward associated with pulling an arm is not
immediate; it is the final outcome of the rollout (or simulation) that
starts from that action and propagates back through the tree during
backpropagation.

In our ISMCTS implementation, the reward is therefore the terminal
rollout result (e.g., win/loss), which is propagated upward to update
the estimated value of every action selected along the simulation path.

- UCB1's regret bound was proven for *stationary* bandits. MCTS bandits
  are non-stationary — the reward distribution changes as the subtree
  grows and its values sharpen. So why does UCB1 still work?

Strictly speaking, the reward distribution observed at each MCTS node is
not stationary. As deeper parts of the tree are expanded, rollout
policies improve and value estimates become more accurate, changing the
empirical rewards observed by ancestor nodes.

Despite this, UCB1 continues to perform well because these changes
become progressively smaller as the search grows. Over time, the
estimated values converge, making each node behave increasingly like a
stationary bandit. In practice, UCB1 continuously balances exploration
and exploitation while the estimates stabilize.

- Cite Kocsis & Szepesvári (2006) for the answer, but in your own words
  — what's the intuition for the asymptotic consistency?

The key intuition behind the asymptotic consistency of UCT is that every
action continues to receive infinitely many visits as the number of
simulations approaches infinity, although clearly suboptimal actions are
explored increasingly less often. As more simulations are performed,
value estimates become more accurate, allowing the search policy to
converge toward the optimal action. Although early estimates are noisy,
their influence diminishes over time as additional evidence is
accumulated.

This explains why UCT remains consistent despite violating the strict
stationarity assumptions required by the original UCB1 analysis.

**My take.**

This section helped me understand that each node of an MCTS tree is
essentially solving its own bandit problem. Initially, I assumed the
theoretical guarantees of UCB1 would no longer apply because the reward
distribution changes as the search tree expands. The key insight is that
the environment is only temporarily non-stationary: as more simulations
are performed, the estimates stabilize and each node gradually behaves
like a stationary bandit. This makes the asymptotic guarantees of UCT
much more intuitive.

**Refined write-up.**

Each internal node of an MCTS tree can be interpreted as an independent
multi-armed bandit problem, where each child represents one available
action. The reward associated with selecting an action is the terminal
outcome of the rollout, propagated back through the search tree during
backpropagation.

Although UCB1 was originally derived for stationary reward distributions,
MCTS violates this assumption because value estimates evolve as deeper
parts of the tree are explored. Kocsis and Szepesvári (2006) showed that
this does not prevent asymptotic consistency. As the number of
simulations increases, value estimates become increasingly accurate, the
effect of early estimation errors diminishes, and the search policy
converges toward selecting optimal actions. Consequently, each node
becomes approximately stationary in the limit, allowing UCT to retain
the desirable convergence properties of UCB1.

---

## Ch 3 — Finite MDPs

### 3.1 — Why the 4-arg $p(s', r \mid s, a)$ is fundamental

**Prompt.** S&B introduces $p(s', r \mid s, a)$ (eq 3.2) as the
fundamental dynamics primitive.

- Show explicitly that $r(s, a)$ (eq 3.5) and $p(s' \mid s, a)$ (eq 3.4)
  are marginals of the 4-arg form.

The four-argument dynamics

$$
p(s', r \mid s, a)
$$

defines the complete joint distribution of the next state and immediate
reward given the current state and action.

The transition probability is obtained by marginalizing over all possible
rewards:

$$
p(s' \mid s, a) \;=\; \sum_r p(s', r \mid s, a).
$$

Similarly, the expected immediate reward is obtained by taking the
expectation over both the next state and reward:

$$
r(s, a) \;=\; \mathbb{E}[R \mid s, a] \;=\; \sum_{s'} \sum_r r \, p(s', r \mid s, a).
$$

Therefore, both the transition function and the reward function are
derived quantities obtained from the more general joint distribution.

- Why doesn't the book use the classical "transition + reward function"
  split from the RL literature?

The classical formulation separates the environment into a transition
model $p(s' \mid s, a)$ and a reward function $r(s, a)$. Sutton & Barto
instead use $p(s', r \mid s, a)$ because it represents the complete
stochastic dynamics of the environment without assuming that rewards can
be modeled independently of the resulting state.

In many environments, different successor states may produce different
rewards, making the reward statistically dependent on the transition.
The four-argument formulation naturally captures this dependence while
remaining general enough to recover the classical formulation through
marginalization.

- What would our MDP formalization for PTCG
  ([`../docs/mdp-formalization.md`](../docs/mdp-formalization.md)) look
  like if we insisted on the split? Any information loss?

Our PTCG formalization could also be written using the classical pair
$p(s' \mid s, a)$ and $r(s, a)$. For our environment, where rewards are
terminal and deterministic ($-1, 0, +1$), this representation would not
lose information because the immediate reward depends only on the
transition outcome.

However, the four-argument formulation remains conceptually cleaner
because it treats rewards as part of the stochastic environment dynamics
rather than as a separate object. It also generalizes naturally to
environments where the reward depends jointly on the transition and the
resulting state.

**My take.**

Initially, I viewed the four-argument dynamics as simply a different
notation. After studying Chapter 3, I realized that it represents a
modeling choice rather than a mathematical convenience. The joint
distribution $p(s', r \mid s, a)$ describes the complete stochastic
behavior of the environment, while transition probabilities and expected
rewards are merely summaries obtained through marginalization.

For our Pokémon project, the classical transition-plus-reward
formulation would be sufficient because rewards are deterministic and
terminal. Nevertheless, the four-argument formulation better reflects
the underlying probabilistic model and makes fewer assumptions about how
rewards are generated.

**Refined write-up.**

The four-argument dynamics $p(s', r \mid s, a)$ is the fundamental
object of an MDP because it specifies the complete probability
distribution over both successor states and immediate rewards. The
commonly used transition model $p(s' \mid s, a)$ and expected reward
function $r(s, a)$ are simply marginals derived from this joint
distribution.

Although our Pokémon TCG formalization could equivalently be expressed
using the classical transition-plus-reward decomposition, doing so would
introduce additional assumptions about how rewards are generated. Since
terminal rewards in our environment are deterministic, no information
would be lost. Nevertheless, the joint formulation remains the most
general and mathematically complete description of the environment
dynamics.

---

### 3.2 — State-value ↔ action-value equivalence

**Prompt.** The pair

$$
v_\pi(s) \;=\; \sum_a \pi(a \mid s) \, q_\pi(s, a), \qquad
q_\pi(s, a) \;=\; \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, v_\pi(s') \bigr]
$$

fully determine each other given $p$ and $\pi$.

- Substitute one into the other to derive the Bellman equation for
  $v_\pi$ directly.

Starting from

$$
v_\pi(s) \;=\; \sum_a \pi(a \mid s)\, q_\pi(s, a),
$$

and substituting

$$
q_\pi(s, a) \;=\; \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, v_\pi(s') \bigr],
$$

we obtain

$$
v_\pi(s) \;=\; \sum_a \pi(a \mid s) \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, v_\pi(s') \bigr].
$$

Reordering the summations gives the Bellman expectation equation:

$$
\boxed{\,
v_\pi(s) \;=\; \sum_a \pi(a \mid s) \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, v_\pi(s') \bigr]\,}
$$

This equation expresses the value of a state as the expected return
obtained by following policy $\pi$.

- Do the same for $q_\pi$.

Substituting

$$
v_\pi(s') \;=\; \sum_{a'} \pi(a' \mid s')\, q_\pi(s', a')
$$

into

$$
q_\pi(s, a) \;=\; \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, v_\pi(s') \bigr],
$$

gives

$$
q_\pi(s, a) \;=\; \sum_{s', r} p(s', r \mid s, a) \left[ r + \gamma \sum_{a'} \pi(a' \mid s')\, q_\pi(s', a') \right].
$$

This is the Bellman expectation equation expressed entirely in terms of
action values.

- Why is it useful to have both forms? (Think about ISMCTS: we operate
  on $q$-values because actions are the object of choice.)

Both formulations describe the same decision process, but they emphasize
different objects.

State values $v_\pi(s)$ are useful when successor states can be
evaluated directly. This is the case in deterministic, fully observable
environments such as the tic-tac-toe example from Chapter 1.

Action values $q_\pi(s, a)$ become more natural when the agent must
compare actions explicitly. In our ISMCTS implementation, the search
algorithm repeatedly chooses among legal actions at each information
state. Therefore, estimating action values directly provides exactly the
quantity needed during tree search.

**My take.**

Initially, I viewed state values and action values as two different ways
of solving the same problem. This chapter helped me realize that they
are mathematically equivalent but computationally useful in different
situations.

The Bellman equations show that one representation completely determines
the other. The choice between $V$ and $Q$ is therefore not about
correctness, but about which quantity is more convenient for the
algorithm. Since ISMCTS repeatedly compares actions rather than isolated
states, estimating action values is the most natural representation for
our project.

**Refined write-up.**

The Bellman expectation equations demonstrate that state values and
action values are mathematically equivalent representations of the same
decision process. Given the environment dynamics and a policy, either
representation uniquely determines the other.

Despite this equivalence, the two formulations serve different
computational purposes. State values summarize the expected return of
being in a state, whereas action values evaluate the consequence of
selecting a specific action before following the policy thereafter.

This distinction is particularly relevant for ISMCTS. Tree search
operates by comparing candidate actions at each information state,
making action values the natural object of estimation. Consequently, the
search algorithm stores and updates $Q(I, a)$ estimates rather than
state values, even though both representations encode the same
underlying expected return.

---

### 3.3 — Reward-translation invariance and ADR-004

**Prompt.** S&B Ex 3.15 proves that adding a constant $c$ to all rewards
translates $v_\pi$ by $c/(1-\gamma)$, so relative values (and therefore
$\pi^*$) are preserved *in continuing tasks*.

- Do the proof.

Assume that every reward is translated by a constant $c$:

$$
R'_t \;=\; R_t + c.
$$

The discounted return becomes

$$
G'_t \;=\; \sum_{k=0}^{\infty} \gamma^k \bigl( R_{t+k+1} + c \bigr).
$$

Expanding the sum,

$$
G'_t \;=\; \sum_{k=0}^{\infty} \gamma^k R_{t+k+1} \;+\; c \sum_{k=0}^{\infty} \gamma^k.
$$

The first term is simply the original return,

$$
G_t \;=\; \sum_{k=0}^{\infty} \gamma^k R_{t+k+1},
$$

while the second term is a geometric series,

$$
\sum_{k=0}^{\infty} \gamma^k \;=\; \frac{1}{1 - \gamma}.
$$

Therefore,

$$
G'_t \;=\; G_t + \frac{c}{1 - \gamma}.
$$

Taking expectations,

$$
v'_\pi(s) \;=\; v_\pi(s) + \frac{c}{1 - \gamma}.
$$

Every state value is shifted by the same constant, so the relative
ordering of states is unchanged. Consequently, the optimal policy
remains the same.

- Ex 3.16: show this fails in *episodic* tasks. Why?

The proof above assumes an infinite discounted sum, where every
trajectory receives the same infinite geometric correction.

In episodic tasks, however, episodes terminate after different numbers
of steps. The translated return becomes

$$
G'_t \;=\; G_t + c \sum_{k=0}^{T - t - 1} \gamma^k,
$$

where the correction now depends on the remaining episode length.

As a result, trajectories with different lengths receive different
offsets. Since the added constant is no longer identical for every
policy, the relative values of states and actions may change,
potentially altering the optimal policy.

- Connect to
  [`../docs/adr/adr-004-terminal-reward-not-shaped.md`](../docs/adr/adr-004-terminal-reward-not-shaped.md):
  our reward is $\{-1, 0, +1\}$ terminal in a finite-horizon MDP. Is
  translation invariance broken for us? What does that imply for the
  choice of scale?

Our Pokémon TCG environment is a finite-horizon episodic task with
terminal rewards $\{-1, 0, +1\}$ and $\gamma = 1$. Therefore,
reward-translation invariance does **not** hold.

Adding a constant reward at every step would favor longer or shorter
games depending on the sign of the constant, introducing an unintended
optimization objective. For this reason, ADR-004 deliberately uses
sparse terminal rewards without reward shaping. The chosen reward scale
directly defines the optimization objective, making its interpretation
both meaningful and stable.

**My take.**

Before studying this exercise, I assumed that changing the reward scale
was mostly a cosmetic decision. The proof showed that this is only true
for continuing discounted tasks. In finite-horizon episodic problems
like Pokémon TCG, translating rewards changes the optimization objective
because trajectories have different lengths.

This reinforced the rationale behind ADR-004: keeping rewards sparse and
terminal avoids unintentionally encouraging longer or shorter games,
ensuring that the agent optimizes only for winning.

**Refined write-up.**

Reward-translation invariance is a property of continuing discounted
tasks, where adding a constant $c$ to every reward shifts all value
functions by the same amount, $c / (1 - \gamma)$, without changing their
relative ordering. Consequently, the optimal policy remains unchanged.

This property no longer holds in finite-horizon episodic tasks because
the accumulated translation depends on the episode length. Different
policies may terminate after different numbers of steps, causing the
added reward to alter their relative returns.

Our Pokémon TCG environment is episodic with terminal rewards and
$\gamma = 1$. Therefore, reward translation is not invariant. This
justifies ADR-004, which intentionally avoids reward shaping and uses
only sparse terminal rewards, ensuring that the optimization objective
remains aligned with maximizing the probability of winning rather than
influencing episode length.

---

### 3.4 — Discounting vs episodic termination as two horizon knobs

**Prompt.** Both discounting ($\gamma < 1$) and episodic termination
($T < \infty$) bound the return. They can be combined.

- What's the return in each of the four combinations?
  ($\gamma < 1$ or $\gamma = 1$) × (episodic or continuing).

There are four possible combinations of discounting and episode
termination.

| Setting | Return |
|---|---|
| Continuing, $\gamma < 1$ | $G_t = \sum_{k=0}^{\infty} \gamma^k R_{t+k+1}$ |
| Continuing, $\gamma = 1$ | Generally diverges unless rewards eventually vanish. |
| Episodic, $\gamma < 1$ | $G_t = \sum_{k=0}^{T-t-1} \gamma^k R_{t+k+1}$ |
| Episodic, $\gamma = 1$ | $G_t = \sum_{k=0}^{T-t-1} R_{t+k+1}$ |

Discounting guarantees convergence for continuing tasks, whereas finite
episode length guarantees convergence for episodic tasks even without
discounting.

- Which combination fits PTCG? (Answer: episodic $T < \infty$, $\gamma = 1$
  suffices because episodes always terminate.)

Pokémon TCG is naturally modeled as a finite-horizon episodic task.

Episodes always terminate because a match eventually ends when a player
satisfies one of the victory or defeat conditions. Therefore, $\gamma = 1$
is sufficient, and the return is simply

$$
G_t \;=\; \sum_{k=0}^{T-t-1} R_{t+k+1}.
$$

There is no need to artificially discount future rewards because the
finite episode length already guarantees that the return is bounded.

- Why does the 10-min wall-clock budget *look* like a discount factor
  even though we don't set $\gamma < 1$?

The 10-minute wall-clock limit is not part of the MDP definition and
therefore is **not** a discount factor.

However, it has a similar practical effect. Because the agent has a
fixed computational budget, it cannot evaluate arbitrarily deep search
trees. As the remaining computation time decreases, future consequences
become progressively harder to estimate accurately.

Unlike a discount factor, which mathematically reduces the contribution
of distant rewards to the return, the time budget limits how far ahead
the agent can realistically plan. The optimization objective remains
unchanged, but the planning horizon becomes computationally constrained.

**My take.**

Initially, I associated discounting with limiting how far into the
future an agent should reason. Chapter 3 clarified that discounting and
episodic termination solve different problems. Discounting is a
mathematical tool for ensuring finite returns in continuing tasks,
whereas finite-horizon episodes already guarantee bounded returns.

For our Pokémon project, the 10-minute time limit initially seemed
analogous to a discount factor. I now understand that it only limits
computational planning, not the optimization objective itself. The agent
still values winning at the end of the game exactly as much as winning
immediately.

**Refined write-up.**

Discounting and episodic termination are two independent mechanisms for
ensuring that returns remain finite. Discounting bounds the infinite sum
of rewards in continuing tasks, whereas finite episode length naturally
bounds the return even when $\gamma = 1$.

Pokémon TCG is appropriately modeled as a finite-horizon episodic MDP.
Since every match terminates, using $\gamma = 1$ preserves the original
objective of maximizing the probability of winning without introducing
an artificial preference for earlier rewards.

Although the competition imposes a 10-minute computation limit, this
constraint affects only the planning process. Unlike a discount factor,
it does not modify the return definition or the optimization objective.
Instead, it limits the depth and breadth of the search that can be
performed before selecting an action.

---

### 3.5 — Information sets partition $S$

**Prompt.** In our project we defined
$I_i(s) = \{s' \in S : O_i(s') = O_i(s)\}$ (see
[`../docs/mdp-formalization.md`](../docs/mdp-formalization.md)). This is
an equivalence relation, so the $I_i$ partition $S$.

- Why doesn't S&B's Ch 3 framework need this? (Answer: full observability
  assumption.)

Sutton & Barto formulate reinforcement learning using fully observable
Markov Decision Processes (MDPs). Under this assumption, the current
state $s$ contains all information required to predict future dynamics
and optimize decisions.

Because every agent observes the complete environment state, there is
no ambiguity about which state the agent occupies. Consequently, each
observation corresponds to exactly one underlying state, making
information sets unnecessary.

Information sets become necessary only when the agent cannot distinguish
between multiple underlying states that produce the same observation.

- What breaks if we naively apply an MDP algorithm — say, Q-learning — to
  our observation dict directly?

If we directly apply Q-learning to the observation dictionary, the
Markov property no longer holds.

The same observation may correspond to multiple hidden game states with
different opponent hands, deck orders, or hidden prizes. Consequently,
identical observations may have different optimal actions and different
future reward distributions.

Q-learning assumes that each state uniquely determines future dynamics.
Violating this assumption causes updates from fundamentally different
situations to be merged into the same value estimate, preventing
convergence to the true optimal action-value function.

- How does ISMCTS bypass the break? (One-line answer expected;
  full detail comes from Cowling et al. 2012 in the next section.)

Rather than treating the observation as the true state, ISMCTS samples
hidden information consistent with the current observation
(determinization) and performs tree search over complete game states.
By averaging many such simulations, it estimates action values over the
entire information set instead of a single hidden state.

**My take.**

This was the point where I finally understood why our project uses
Information Sets instead of directly applying classical reinforcement
learning algorithms.

Initially, I assumed the observation dictionary could simply be treated
as the environment state. Chapter 3 showed that this violates the Markov
assumption because hidden information makes multiple true states appear
identical to the agent.

Information Sets provide a principled way to represent this uncertainty,
while ISMCTS avoids committing to a single hidden state by averaging
decisions across many sampled determinizations. This was the clearest
connection between the theoretical MDP framework and the practical
design of our Pokémon agent.

**Refined write-up.**

The MDP framework presented in Chapter 3 assumes full observability,
meaning that every observed state satisfies the Markov property. Under
this assumption, classical value functions such as $V(s)$ and $Q(s, a)$
are well defined because each state uniquely determines the future
reward distribution.

Pokémon TCG violates this assumption due to hidden information.
Multiple underlying game states may produce the same observation while
requiring different optimal actions. Representing observations directly
as MDP states therefore breaks the Markov property and invalidates the
assumptions behind algorithms such as Q-learning.

Our project addresses this by defining information sets,

$$
I_i(s) \;=\; \{\, s' \in S : O_i(s') = O_i(s) \,\},
$$

which partition the true state space into equivalence classes of
indistinguishable states. ISMCTS then performs search over sampled
determinizations drawn from these information sets, allowing action
values to approximate expectations over hidden states rather than
assuming a fully observable environment. This provides a principled
extension of the MDP framework to imperfect-information games.

---

## Ch 8 — Planning & Learning

### 8.1 — Model-free vs. model-based vs. Dyna

**Prompt.** Ch 8 distinguishes three regimes:

- Direct RL: learn $Q$ from real experience.
- Indirect RL / planning: learn $Q$ from *simulated* experience.
- Dyna: interleave both.

Answer these:

- Where does MCTS sit on this spectrum? (Answer: pure planning — but with
  a subtlety.)

MCTS belongs primarily to the **planning** regime. Rather than learning
from real interaction with the environment, it estimates action values
by generating simulated experience through repeated rollouts from the
current state.

A subtle but important distinction is that MCTS continuously updates
action-value estimates during search. However, these estimates are
typically discarded once the search ends. Therefore, MCTS improves the
current decision without producing persistent knowledge across episodes,
distinguishing it from Direct RL.

- The "model" in Dyna is learned; in MCTS, what is the model?

In Dyna, the model is learned from real interaction with the environment
and is later used to generate simulated experience.

In MCTS, the model is not learned. Instead, it is an explicit simulator
that implements the environment dynamics. Given a state and an action,
the simulator applies the game rules, resolves stochastic events, and
generates successor states exactly according to the environment.

- In our PTCG project, is the model *learned*, *given*, or *sampled*?
  (Distinct answers depending on which piece — the engine, the
  determinization, and the rollout policy.)

The answer depends on which component of the system is considered.

- **Game engine (`cabt`):** the model is **given**. It explicitly
  implements the Pokémon TCG rules and state transition dynamics.
- **Determinization:** the hidden information is **sampled**. Since the
  opponent's hand, deck order, and other hidden variables are unknown,
  ISMCTS samples complete game states consistent with the current
  information set.
- **Rollout policy:** in Phase 3 it will be **random** (per ADR-001),
  and in Phase 4 it becomes a heuristic-guided policy (targeted by
  hypothesis H2, per ADR-003). In neither phase is it learned from
  experience.

Therefore, our project combines a given environment model with sampled
hidden information while relying on a hand-crafted (initially random,
then heuristic) rollout policy.

**My take.**

Before reading Chapter 8, I associated planning with "thinking ahead"
and learning with "improving from experience." The chapter clarified
that the real distinction lies in the source of experience.

Direct RL learns from the real environment, planning learns from a
model, and Dyna combines both. This made it clear that our ISMCTS
implementation is fundamentally a planning algorithm, even though it
continuously updates action values during search. Those updates improve
only the current decision and are discarded once the search terminates.

**Refined write-up.**

Chapter 8 classifies reinforcement learning methods according to the
source of experience used for value estimation. Direct RL relies
exclusively on real interaction with the environment, planning relies
exclusively on simulated experience generated by a model, and Dyna
interleaves both sources.

Our ISMCTS implementation belongs to the planning regime. Action values
are estimated entirely through simulations generated by the game engine,
without persistent learning across episodes. Although the search
continuously updates action-value estimates, these updates are local to
the current search tree and do not constitute long-term learning.

The notion of "model" also differs across system components. The
Pokémon TCG game engine provides an explicit environment model, hidden
information is handled through sampled determinizations, and the rollout
policy is hand-designed rather than learned. This combination allows
ISMCTS to plan effectively in an imperfect-information environment
without requiring a learned world model.

---

### 8.2 — Dyna-Q+ and exploration under change

**Prompt.** Dyna-Q+ adds a bonus $\kappa \sqrt{\tau}$ (where $\tau$ is
time since last visit) to $Q$-values to encourage revisiting stale
$(s, a)$ pairs.

- Compare to UCB1's $c \sqrt{\ln t / n_a}$ — structurally similar, but
  what's the semantic difference?

Both Dyna-Q+ and UCB1 add an exploration bonus, but they measure
different notions of uncertainty.

UCB1 uses

$$
c \sqrt{\frac{\ln t}{n_a}},
$$

where the bonus decreases as an action is sampled more frequently. The
purpose is to reduce **statistical uncertainty** about the action-value
estimate.

Dyna-Q+ instead adds

$$
\kappa \sqrt{\tau},
$$

where $\tau$ is the time since the state–action pair was last visited.
This bonus encourages revisiting actions that may have become outdated
because the environment has changed.

Therefore, UCB1 explores because an action is **poorly estimated**,
whereas Dyna-Q+ explores because previously learned information may have
become **stale**.

- Does anything in ISMCTS play the role of Dyna-Q+? Argue why or why not.
  (Hint: our tree is rebuilt each decision, so "stale" is a strange
  notion.)

Not directly.

In standard ISMCTS, the search tree is rebuilt from scratch at every
decision. Since value estimates do not persist across turns, there is
no notion of an action becoming stale over time.

Each search begins with fresh statistics, and exploration is driven
entirely by the uncertainty of the current search rather than by
changes in the environment. Consequently, ISMCTS has no mechanism
analogous to the recency bonus used in Dyna-Q+.

- Ex 8.4 asks about moving the bonus from updates to action selection —
  that's exactly what UCB1 does. Note the parallel in the write-up.

Exercise 8.4 highlights an interesting parallel between Dyna-Q+ and
UCB1.

In Dyna-Q+, the exploration bonus is incorporated into the value update
itself, modifying the estimated action values.

UCB1 instead keeps value estimates unchanged and adds the exploration
bonus only during action selection:

$$
Q(a) + c \sqrt{\frac{\ln t}{n_a}}.
$$

Separating estimation from exploration makes the interpretation of $Q$
cleaner: the value estimate remains an empirical estimate of expected
return, while exploration is handled entirely by the decision rule.

**My take.**

Initially, the exploration bonuses used by Dyna-Q+ and UCB1 appeared
almost identical because both increase the preference for certain
actions. Chapter 8 clarified that they solve different problems.

UCB1 addresses uncertainty arising from limited sampling, while Dyna-Q+
addresses uncertainty caused by environmental change. Since ISMCTS
rebuilds its search tree at every decision, it never accumulates stale
knowledge across episodes. As a result, UCB-style exploration is
appropriate, whereas Dyna-Q+'s recency bonus is unnecessary.

**Refined write-up.**

Although Dyna-Q+ and UCB1 use exploration bonuses with similar
mathematical forms, they are motivated by different sources of
uncertainty.

UCB1 compensates for statistical uncertainty caused by limited sampling.
Actions that have been explored fewer times receive larger confidence
bounds, encouraging additional sampling until their estimated values
become reliable.

Dyna-Q+, in contrast, assumes that the environment may change over time.
Its recency bonus encourages revisiting state–action pairs that have not
been experienced recently because previously learned values may no
longer be accurate.

This distinction explains why ISMCTS naturally adopts UCB-style
exploration. Since each search tree is rebuilt from scratch before every
move, value estimates never become stale across decisions. Exploration
is therefore driven by estimation uncertainty rather than environmental
change, making the UCB formulation the appropriate choice.

---

### 8.3 — Sample vs. expected updates and MCTS

**Prompt.** Section 8.5 argues sample updates beat expected updates when
branching is high (roughly, $b > 10$ or so).

- Restate the argument in terms of "compute per update".

Chapter 8 argues that the choice between expected and sample updates is
fundamentally a computational trade-off.

An expected update computes the exact expectation by evaluating every
possible successor state:

$$
\sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma\, V(s') \bigr].
$$

Its computational cost grows with the branching factor because every
possible outcome must be considered.

A sample update instead follows a single sampled transition
$(s, a) \to (s', r)$ and updates the value estimate using only that
experience.

Although each sample update contains more variance, it is significantly
cheaper. When the branching factor is large, many inexpensive sample
updates typically provide more accurate estimates per unit of
computation than a small number of exact expected updates.

- MCTS is *pure* sample updates — no expected form ever computed. Why is
  this the right call for PTCG? (Cite the branching factor estimate from
  our project — where does that come from?
  [`../exercises/ex01_environment.md`](../exercises/ex01_environment.md) §3
  bounds the info set size, which is different but relates.)

MCTS relies exclusively on sample updates. Each simulation follows a
single trajectory through the game tree, producing one terminal outcome
that is propagated back to update the visited nodes.

Computing expected updates would require enumerating every possible
hidden card, draw sequence, opponent response, and stochastic outcome
after each action. The branching factor of Pokémon TCG makes this
computationally infeasible.

Our project therefore adopts pure sample updates because they scale
naturally to large search spaces. The information-set analysis presented
in `ex01_environment.md` further illustrates that uncertainty grows
combinatorially with hidden information, reinforcing the impracticality
of expected updates.

- Ex 8.6 asks about skewed distributions. Does the answer strengthen or
  weaken the case for MCTS in PTCG?

Exercise 8.6 asks what happens to the sample-vs-expected trade-off when
the $b$ possible successor states are highly skewed instead of uniformly
distributed. The answer **strengthens** the case for sample updates —
and therefore strengthens the case for MCTS in PTCG.

An expected update evaluates every successor state, weighting each by
its transition probability. When the distribution is nearly uniform, no
single evaluation dominates the total, so the expected update is not
particularly wasteful. When the distribution is highly skewed, however,
the expected update still spends the same computation on every
successor, including the rare-outcome tail whose contribution to the
value estimate is proportional to a tiny probability.

Sample updates naturally exploit skew: they draw successor states in
proportion to their transition probabilities. The high-probability
outcomes are sampled many times and drive the estimate; the low-
probability outcomes are sampled almost never, contributing negligibly.
The computation therefore concentrates where the mass is, matching the
structure of the underlying distribution without any extra bookkeeping.

This directly favors MCTS on PTCG. Card draws, coin flips, and Trainer
effects produce transition distributions that are anything but uniform
— a small number of typical draw sequences (or heads/tails on a coin
flip) dominate the transition mass, while the combinatorial tail of
exotic sequences carries almost no probability weight. Expected updates
would waste computation traversing that tail; sample updates ignore it
proportionally. This is a second, orthogonal reason to prefer
sample-based planning here, on top of the raw branching-factor argument.

**My take.**

This section changed the way I think about Monte Carlo Tree Search.
Initially, I viewed sample updates as an approximation used because
exact computation was difficult. Chapter 8 showed that sample updates
are often the better computational strategy, not merely a necessary
approximation.

For Pokémon TCG, the enormous branching factor created by hidden
information and stochastic effects makes expected updates prohibitively
expensive. MCTS succeeds precisely because it spends computation
exploring representative trajectories instead of attempting to enumerate
every possible future.

**Refined write-up.**

Chapter 8 demonstrates that the choice between expected and sample
updates should be evaluated in terms of computation per update rather
than statistical efficiency alone. Expected updates reduce variance by
averaging over all successor states, but their computational cost
increases rapidly with the branching factor.

Monte Carlo Tree Search adopts the opposite strategy: every update is
based on a single sampled trajectory. Although individual estimates are
noisier, each update is extremely inexpensive, allowing many more
simulations within a fixed computational budget.

This trade-off is particularly favorable for Pokémon TCG. Hidden
information, stochastic card draws, and numerous legal actions produce
an enormous branching factor, making exact expectation updates
computationally impractical. Sample-based planning therefore provides a
much better use of the available search budget, which is precisely why
MCTS is well suited to this domain.

---

### 8.4 — Rollout algorithms are the MCTS ancestor

**Prompt.** Section 8.10 introduces *rollout algorithms* — one-step
lookahead with Monte Carlo returns from a base policy.

- Show that a rollout algorithm with tree depth 0 = MCTS with zero
  simulations = Monte Carlo policy evaluation.

A rollout algorithm evaluates candidate actions by simulating complete
episodes from the current state using a base policy.

When the search tree has depth zero, no internal tree is constructed.
Every simulation starts directly from the current state and follows the
rollout policy until termination.

In this setting, there is no distinction between tree search and Monte
Carlo evaluation. The estimated action value is simply the average
return obtained from independent simulations:

$$
Q(s, a) \;\approx\; \frac{1}{N} \sum_{i=1}^{N} G_i.
$$

Therefore, a depth-zero rollout algorithm is equivalent to Monte Carlo
policy evaluation. MCTS generalizes this idea by incrementally building
and reusing a search tree across simulations.

- What does MCTS add on top of a plain rollout algorithm? (Selection
  policy at internal nodes; tree memory across simulations.)

MCTS extends plain rollout algorithms in two fundamental ways.

First, it stores search statistics inside an explicit tree. Instead of
treating every simulation independently, information gathered in
previous simulations is reused during subsequent searches.

Second, MCTS introduces a selection policy (typically UCT) at internal
nodes. Rather than sampling actions uniformly, the algorithm balances
exploration and exploitation by preferentially expanding promising parts
of the search tree.

These two additions dramatically improve sample efficiency, allowing
computational effort to be concentrated on the most relevant regions of
the search space.

- Section 8.11's MCTS description matches Browne et al. (2012). Any
  significant divergence between S&B's presentation and the survey?
  (Reserve this question for after reading Browne.)

_(pending — fills in after Browne survey reading.)_

**My take.**

This section clarified that Monte Carlo Tree Search is not a completely
new algorithm but rather a systematic extension of rollout-based
planning.

Initially, I viewed rollouts and MCTS as fundamentally different
approaches. Chapter 8 showed that the key innovation of MCTS is not the
rollout itself but the reuse of information across simulations. By
storing search statistics and guiding future simulations toward
promising actions, MCTS transforms independent Monte Carlo evaluations
into an increasingly informed planning process.

**Refined write-up.**

Rollout algorithms estimate action values by simulating complete
episodes from the current state using a fixed base policy. Without an
explicit search tree, each rollout is independent and contributes only
to the current action evaluation.

Monte Carlo Tree Search builds directly upon this idea by introducing
two key mechanisms: an explicit search tree that stores statistics
across simulations and a selection policy that allocates computational
effort toward promising regions of the tree. As a result, simulations
become increasingly informative rather than repeatedly evaluating the
same actions independently.

This perspective highlights MCTS as a natural generalization of Monte
Carlo policy evaluation, combining the statistical robustness of
rollouts with adaptive search guided by accumulated experience within a
single planning episode.

---

### 8.5 — Bridge from Ch 8 to Cowling et al. (2012)

**Prompt.** The final section (8.11) is where S&B connects to what this
project actually builds.

- Restate the "MCTS four-phase loop" (selection / expansion / rollout /
  backpropagation) as S&B presents it.

Monte Carlo Tree Search iteratively improves action-value estimates
through four phases:

1. **Selection.** Starting from the root, repeatedly select child nodes
   according to the tree policy (typically UCT) until reaching a leaf
   or expandable node.
2. **Expansion.** If the selected node represents a non-terminal state
   with unexplored actions, expand the tree by creating one or more
   child nodes.
3. **Rollout (Simulation).** From the newly expanded node, simulate the
   remainder of the game using a rollout policy until reaching a
   terminal state.
4. **Backpropagation.** Propagate the terminal reward back through
   every node visited during the simulation, updating visit counts and
   action-value estimates.

Repeated simulations gradually improve the quality of the search tree,
concentrating computation on the most promising actions.

- Where does information-set structure enter the loop?

Information sets are **not** part of the four-phase MCTS loop described
by Sutton & Barto. Their presentation assumes a fully observable MDP in
which every node corresponds to a unique environment state.

In our project, information sets are introduced **before** the standard
MCTS loop begins. Rather than treating the current observation as a
complete state, ISMCTS first samples a complete hidden state (a
determinization) that is consistent with the agent's information set.

The four MCTS phases then operate on this sampled game state exactly as
in the fully observable case.

- What does Cowling et al. (2012) change to accommodate hidden
  information? (Preview — full answer in `notes/phase2-ismcts-paper-notes.md`
  after reading the paper.)

Cowling et al. (2012) extend classical MCTS to imperfect-information
games by replacing tree nodes indexed by true game states with nodes
indexed by information sets.

Instead of assuming full observability, each simulation samples a
determinization consistent with the player's current information. Tree
search then proceeds on that sampled state while accumulating statistics
over many determinizations.

This preserves the overall MCTS framework while allowing planning under
hidden information. The algorithmic details are discussed in the next
phase after studying the ISMCTS paper.

**My take.**

Chapter 8 made it clear that the core MCTS algorithm is surprisingly
simple. The four-phase loop — selection, expansion, rollout, and
backpropagation — is independent of the specific game and relies only
on having a simulator.

The main limitation is that Sutton's presentation assumes full
observability. Our Pokémon TCG project violates this assumption because
hidden information prevents the agent from observing the true game
state. This naturally motivates the transition from classical MCTS to
Information Set MCTS, which preserves the same planning loop while
changing how search states are represented.

**Refined write-up.**

Chapter 8 concludes by presenting Monte Carlo Tree Search as a planning
algorithm built around four iterative phases: selection, expansion,
rollout, and backpropagation. This framework provides a general method
for estimating action values through repeated simulations guided by an
adaptive search tree.

The presentation assumes a fully observable environment in which every
search node corresponds to a unique game state. Our Pokémon TCG project
relaxes this assumption by introducing information sets before search
begins. Rather than searching directly over observed states, ISMCTS
samples complete game states consistent with the available information
and executes the standard MCTS loop on those determinizations.

Cowling et al. (2012) therefore do not replace MCTS; they generalize it
to imperfect-information games by redefining what a search node
represents. The four-phase planning loop remains unchanged, while the
state representation becomes information-set based. This provides the
conceptual bridge between Sutton & Barto's planning framework and the
architecture implemented in our project.

---

## Cross-chapter connections

### X.1 — Bandits (Ch 2) as degenerate MDPs (Ch 3)

**Prompt.** If $|S| = 1$, the MDP is a bandit.

- Show that Ch 2's $Q(a)$ equals Ch 3's $q_\pi(s_0, a)$ under $|S| = 1$.
- What generalizes when we allow $|S| > 1$?
- What machinery does Ch 3 add that Ch 2 doesn't need?

**My take.**

_(fill in)_

---

### X.2 — Ch 4/5/6/7 preview (deferred, but flag concepts)

**Prompt.** Even though we skipped Ch 4–7, they inform Ch 8:

- Value iteration (Ch 4) is expected updates iterated to fixed point.
- Monte Carlo (Ch 5) is trajectory-sample updates without bootstrapping.
- TD (Ch 6) is one-step-sample updates with bootstrapping.
- $n$-step (Ch 7) is $n$-step-sample updates with bootstrapping.
- MCTS (Ch 8) is trajectory-sample updates on a *simulated* trajectory
  from a *tree-restricted* policy.

Fill in the fifth line yourself and check it against the book once you
read Ch 4–7 (which you may or may not, given the roadmap).

**My take.**

_(fill in)_

---

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled if any come up during the read-through.)_
