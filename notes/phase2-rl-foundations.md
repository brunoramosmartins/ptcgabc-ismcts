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

---

## Ch 1 — Introduction

### 1.1 — The agent–environment boundary is a design choice

**Prompt.** S&B Ex 3.3 uses driving to argue that the boundary between
"agent" and "environment" is not fundamental — it's a modeling decision.
For our project:

- Where did we draw the boundary in [`../env/`](../env/)?
- Is there any place where the boundary "leaks" (e.g., the deck submission
  is technically an action of the agent, but it happens on turn 1 before
  the game starts)?
- Would drawing the boundary *inside* the `cabt` engine (say, treating a
  full turn's worth of decisions as one action) change anything about the
  formalism?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 1.2 — State-value vs. action-value learning

**Prompt.** The tic-tac-toe example in Ch 1 learns state values $V(s)$, not
action values $Q(s, a)$.

- Why does the book choose $V$ here?
- What would need to change to learn $Q$ instead in the same setup?
- Our project uses $Q(I, a, h)$ internally in ISMCTS. Why not $V$?
- General trade-off: when is $V$ enough, and when do you need $Q$?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## Ch 2 — Multi-armed Bandits

### 2.1 — Four flavors of exploration

**Prompt.** $\epsilon$-greedy, softmax, UCB, and optimistic initial values
are four ways to parameterize the exploration–exploitation trade-off.

- What does each one say about *what* to explore?
- Which one does UCB1 (the algorithm ISMCTS uses at internal nodes)
  belong to? Why is UCB1 preferred for MCTS?
- Would any of the other three fit better in an imperfect-information
  setting? (Think about what changes when the reward distribution is
  non-stationary because the tree grows below.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.2 — Deriving the running-mean formula

**Prompt.** The sample-average update
$Q_{n+1} = Q_n + \tfrac{1}{n}(R_n - Q_n)$ (S&B eq 2.3) can be derived from
the definition $Q_n = \tfrac{1}{n}\sum_{k=1}^{n} R_k$.

- Do the derivation step by step.
- Generalize to variable step size $\alpha_n$.
- MCTS visit counts implement effectively this update with $\alpha_n = 1/n$.
  What does that imply for the variance of $Q$ estimates at MCTS nodes?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.3 — Exponential recency-weighted average

**Prompt.** For constant step size $\alpha$, the update
$Q_{n+1} = Q_n + \alpha(R_n - Q_n)$ produces (S&B eq 2.6):

$$
Q_n \;=\; (1-\alpha)^n Q_0 \;+\; \sum_{k=1}^{n} \alpha (1-\alpha)^{n-k} R_k.
$$

- Expand the recurrence to show this identity.
- Why does constant $\alpha$ "forget" old rewards?
- When would we *want* forgetting in an ISMCTS setting? (Hint: rewards
  are terminal Bernoulli in our case — probably never. Argue precisely.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

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
- Show that this gives $\epsilon \sim \sqrt{\ln t / n_a}$.
- What is $c$ in the final expression? (Answer: $\sqrt{2}$ in the
  standard derivation.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 2.5 — Bandits at every MCTS node

**Prompt.** Each internal node of an MCTS tree is a $k$-armed bandit over
its children.

- What is the "reward" seen at that bandit? (Answer: the eventual rollout
  outcome that propagates back up.)
- UCB1's regret bound was proven for *stationary* bandits. MCTS bandits
  are non-stationary — the reward distribution changes as the subtree
  grows and its values sharpen. So why does UCB1 still work?
- Cite Kocsis & Szepesvári (2006) for the answer, but in your own words
  — what's the intuition for the asymptotic consistency?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

## Ch 3 — Finite MDPs

### 3.1 — Why the 4-arg $p(s', r \mid s, a)$ is fundamental

**Prompt.** S&B introduces $p(s', r \mid s, a)$ (eq 3.2) as the
fundamental dynamics primitive.

- Show explicitly that $r(s, a)$ (eq 3.5) and $p(s' \mid s, a)$ (eq 3.4)
  are marginals of the 4-arg form.
- Why doesn't the book use the classical "transition + reward function"
  split from the RL literature?
- What would our MDP formalization for PTCG
  ([`../docs/mdp-formalization.md`](../docs/mdp-formalization.md)) look
  like if we insisted on the split? Any information loss?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

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
- Do the same for $q_\pi$.
- Why is it useful to have both forms? (Think about ISMCTS: we operate
  on $q$-values because actions are the object of choice.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 3.3 — Reward-translation invariance and ADR-004

**Prompt.** S&B Ex 3.15 proves that adding a constant $c$ to all rewards
translates $v_\pi$ by $c/(1-\gamma)$, so relative values (and therefore
$\pi^*$) are preserved *in continuing tasks*.

- Do the proof.
- Ex 3.16: show this fails in *episodic* tasks. Why?
- Connect to
  [`../docs/adr/adr-004-terminal-reward-not-shaped.md`](../docs/adr/adr-004-terminal-reward-not-shaped.md):
  our reward is $\{-1, 0, +1\}$ terminal in a finite-horizon MDP. Is
  translation invariance broken for us? What does that imply for the
  choice of scale?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 3.4 — Discounting vs episodic termination as two horizon knobs

**Prompt.** Both discounting ($\gamma < 1$) and episodic termination
($T < \infty$) bound the return. They can be combined.

- What's the return in each of the four combinations?
  ($\gamma < 1$ or $\gamma = 1$) × (episodic or continuing).
- Which combination fits PTCG? (Answer: episodic $T < \infty$, $\gamma = 1$
  suffices because episodes always terminate.)
- Why does the 10-min wall-clock budget *look* like a discount factor
  even though we don't set $\gamma < 1$?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 3.5 — Information sets partition $S$

**Prompt.** In our project we defined
$I_i(s) = \{s' \in S : O_i(s') = O_i(s)\}$ (see
[`../docs/mdp-formalization.md`](../docs/mdp-formalization.md)). This is
an equivalence relation, so the $I_i$ partition $S$.

- Why doesn't S&B's Ch 3 framework need this? (Answer: full observability
  assumption.)
- What breaks if we naively apply an MDP algorithm — say, Q-learning — to
  our observation dict directly?
- How does ISMCTS bypass the break? (One-line answer expected;
  full detail comes from Cowling et al. 2012 in the next section.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

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
- The "model" in Dyna is learned; in MCTS, what is the model?
- In our PTCG project, is the model *learned*, *given*, or *sampled*?
  (Distinct answers depending on which piece — the engine, the
  determinization, and the rollout policy.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 8.2 — Dyna-Q+ and exploration under change

**Prompt.** Dyna-Q+ adds a bonus $\kappa \sqrt{\tau}$ (where $\tau$ is
time since last visit) to $Q$-values to encourage revisiting stale
$(s, a)$ pairs.

- Compare to UCB1's $c \sqrt{\ln t / n_a}$ — structurally similar, but
  what's the semantic difference?
- Does anything in ISMCTS play the role of Dyna-Q+? Argue why or why not.
  (Hint: our tree is rebuilt each decision, so "stale" is a strange
  notion.)
- Ex 8.4 asks about moving the bonus from updates to action selection —
  that's exactly what UCB1 does. Note the parallel in the write-up.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 8.3 — Sample vs. expected updates and MCTS

**Prompt.** Section 8.5 argues sample updates beat expected updates when
branching is high (roughly, $b > 10$ or so).

- Restate the argument in terms of "compute per update".
- MCTS is *pure* sample updates — no expected form ever computed. Why is
  this the right call for PTCG? (Cite the branching factor estimate from
  our project — where does that come from? [`../exercises/ex01_environment.md`](../exercises/ex01_environment.md) §3
  bounds the info set size, which is different but relates.)
- Ex 8.6 asks about skewed distributions. Does the answer strengthen or
  weaken the case for MCTS in PTCG?

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 8.4 — Rollout algorithms are the MCTS ancestor

**Prompt.** Section 8.10 introduces *rollout algorithms* — one-step
lookahead with Monte Carlo returns from a base policy.

- Show that a rollout algorithm with tree depth 0 = MCTS with zero
  simulations = Monte Carlo policy evaluation.
- What does MCTS add on top of a plain rollout algorithm? (Selection
  policy at internal nodes; tree memory across simulations.)
- Section 8.11's MCTS description matches Browne et al. (2012). Any
  significant divergence between S&B's presentation and the survey?
  (Reserve this question for after reading Browne.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 8.5 — Bridge from Ch 8 to Cowling et al. (2012)

**Prompt.** The final section (8.11) is where S&B connects to what this
project actually builds.

- Restate the "MCTS four-phase loop" (selection / expansion / rollout /
  backpropagation) as S&B presents it.
- Where does information-set structure enter the loop?
- What does Cowling et al. (2012) change to accommodate hidden
  information? (Preview — full answer in `notes/phase2-ismcts-paper-notes.md`
  after reading the paper.)

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

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
