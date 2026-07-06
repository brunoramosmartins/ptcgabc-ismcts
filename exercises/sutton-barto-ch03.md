# Sutton & Barto — Chapter 3 (Finite MDPs) Exercises

Reference: Sutton & Barto, *Reinforcement Learning: An Introduction*, 2nd ed.
(2018), Chapter 3.

Template per exercise: **statement (verbatim)** → **initial thoughts** →
**answer** → **notes**.

Exercises marked with 🔖 reference a figure / equation / example from the
book — likely useful to have the book open while writing the final answer.

Notation used below follows the book: $p(s', r \mid s, a)$ is the
four-argument dynamics, $p(s' \mid s, a)$ is the three-argument transition,
$r(s, a)$ is the two-argument expected reward, $v_\pi$ and $q_\pi$ are the
state- and action-value functions under policy $\pi$, and $v_*, q_*, \pi_*$
are the optimal counterparts.

**Code reinforcement.** The GridWorld notebook at
[`../notebooks/phase2-gridworld-mdp.py`](../notebooks/phase2-gridworld-mdp.py)
implements numerical Bellman evaluation on a 4×4 deterministic and
slippery grid; it materializes §3.14 (numerical Bellman check) and §3.24
(optimal gridworld value) in code with heatmaps for $\gamma \in \{0.5,
0.9, 0.99\}$.

---

## Exercise 3.1

**Statement.** Devise three example tasks of your own that fit into the
MDP framework, identifying for each its states, actions, and rewards. Make
the three examples as different from each other as possible. The framework
is abstract and flexible and can be applied in many different ways.
Stretch its limits in some way in at least one of your examples.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Portfolio-relevant: at least one example should connect to PTCG
or to a related decision-under-uncertainty task.

---

## Exercise 3.2

**Statement.** Is the MDP framework adequate to usefully represent all
goal-directed learning tasks? Can you think of any clear exceptions?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Consider imperfect-information games (link to ISMCTS
motivation in [`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md)).

---

## Exercise 3.3

**Statement.** Consider the problem of driving. You could define the
actions in terms of the accelerator, steering wheel, and brake, that is,
where your body meets the machine. Or you could define them farther out —
say, where the rubber meets the road, considering your actions to be tire
torques. Or you could define them farther in — say, where your brain meets
your body, the actions being muscle twitches to control your limbs. Or you
could go to a really high level and say that your actions are your choices
of where to drive. What is the right level, the right place to draw the
line between agent and environment? On what basis is one location of the
line to be preferred over another? Is there any fundamental reason for
preferring one location over another, or is it a free choice?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Discussion-style; ties into how we defined our own agent/env
boundary in [`../docs/mdp-formalization.md`](../docs/mdp-formalization.md).

---

## Exercise 3.4 🔖

**Statement.** Give a table analogous to that in Example 3.3, but for
$p(s', r \mid s, a)$. It should have columns for $s, a, s', r$, and
$p(s', r \mid s, a)$, and a row for every 4-tuple for which
$p(s', r \mid s, a) > 0$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Example 3.3 (recycling robot).

---

## Exercise 3.5 🔖

**Statement.** The equations in Section 3.1 are for the continuing case
and need to be modified (very slightly) to apply to episodic tasks. Show
that you know the modifications needed by giving the modified version of
(3.3).

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Equation (3.3) is $\sum_{s' \in \mathcal{S}} \sum_{r \in
\mathcal{R}} p(s', r \mid s, a) = 1$. Episodic version sums also over the
absorbing terminal(s).

---

## Exercise 3.6

**Statement.** Suppose you treated pole-balancing as an episodic task but
also used discounting, with all rewards zero except for $-1$ upon failure.
What then would the return be at each time? How does this return differ
from that in the discounted, continuing formulation of this task?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Compare with continuing-formulation return in the book (page
54-ish, standard reference).

---

## Exercise 3.7

**Statement.** Imagine that you are designing a robot to run a maze. You
decide to give it a reward of $+1$ for escaping from the maze and a reward
of zero at all other times. The task seems to break down naturally into
episodes — the successive runs through the maze — so you decide to treat
it as an episodic task, where the goal is to maximize expected total
reward (3.7). After running the learning agent for a while, you find that
it is showing no improvement in escaping from the maze. What is going
wrong? Have you effectively communicated to the agent what you want it to
achieve?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Discount factor + reward shape design issue.

---

## Exercise 3.8

**Statement.** Suppose $\gamma = 0.5$ and the following sequence of
rewards is received: $R_1 = -1, R_2 = 2, R_3 = 6, R_4 = 3, R_5 = 2$, with
$T = 5$. What are $G_0, G_1, \dots, G_5$? *Hint: Work backwards.*

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — computational.)_

**Notes.** Straightforward drill on the return recursion
$G_t = R_{t+1} + \gamma G_{t+1}$.

---

## Exercise 3.9

**Statement.** Suppose $\gamma = 0.9$ and the reward sequence is $R_1 = 2$
followed by an infinite sequence of $7$s. What are $G_1$ and $G_0$?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Geometric-series closed form for the infinite tail.

---

## Exercise 3.10 🔖

**Statement.** Prove the second equality in (3.10).

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Equation (3.10) — geometric-series identity
$\sum_{k=0}^{\infty} \gamma^k = \frac{1}{1 - \gamma}$ (used to bound the
return by $\frac{R_{\max}}{1 - \gamma}$).

---

## Exercise 3.11 🔖

**Statement.** If the current state is $S_t$, and actions are selected
according to stochastic policy $\pi$, then what is the expectation of
$R_{t+1}$ in terms of $\pi$ and the four-argument function $p$ (3.2)?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Direct marginalization exercise.

---

## Exercise 3.12

**Statement.** Give an equation for $v_\pi$ in terms of $q_\pi$ and $\pi$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** One-liner:
$v_\pi(s) = \sum_a \pi(a \mid s)\, q_\pi(s, a)$.

---

## Exercise 3.13 🔖

**Statement.** Give an equation for $q_\pi$ in terms of $v_\pi$ and the
four-argument $p$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Direct expansion of the action-value definition.

---

## Exercise 3.14 🔖

**Statement.** The Bellman equation (3.14) must hold for each state for
the value function $v_\pi$ shown in Figure 3.2 (right) of Example 3.5.
Show numerically that this equation holds for the center state, valued at
$+0.7$, with respect to its four neighboring states, valued at $+2.3,
+0.4, -0.4$, and $+0.7$. (These numbers are accurate only to one decimal
place.)

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — numerical.)_

**Notes.** References Figure 3.2 / Example 3.5 (gridworld with special
states A and B).

---

## Exercise 3.15 🔖

**Statement.** In the gridworld example, rewards are positive for goals,
negative for running into the edge of the world, and zero the rest of the
time. Are the signs of these rewards important, or only the intervals
between them? Prove, using (3.8), that adding a constant $c$ to all the
rewards adds a constant, $v_c$, to the values of all states, and thus does
not affect the relative values of any states under any policies. What is
$v_c$ in terms of $c$ and $\gamma$?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Ties directly to
[`../docs/adr/adr-004-terminal-reward-not-shaped.md`](../docs/adr/adr-004-terminal-reward-not-shaped.md)
— our reason for keeping the reward scale honest.

---

## Exercise 3.16

**Statement.** Now consider adding a constant $c$ to all the rewards in an
**episodic** task, such as maze running. Would this have any effect, or
would it leave the task unchanged as in the continuing task above? Why or
why not? Give an example.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Counterpoint to 3.15. Episode length changes → the constant
adds differently to different rollouts.

---

## Exercise 3.17 🔖

**Statement.** What is the Bellman equation for action values, that is,
for $q_\pi$? It must give the action value $q_\pi(s, a)$ in terms of the
action values, $q_\pi(s', a')$, of possible successors to the state-action
pair $(s, a)$. *Hint:* the backup diagram to the right corresponds to this
equation. Show the sequence of equations analogous to (3.14), but for
action values.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Standard action-value Bellman equation derivation.

---

## Exercise 3.18

**Statement.** The value of a state depends on the values of the actions
possible in that state and on how likely each action is to be taken under
the current policy. We can think of this in terms of a small backup
diagram rooted at the state and considering each possible action: Give
the equation corresponding to this intuition and diagram for the value at
the root node, $v_\pi(s)$, in terms of the value at the expected leaf
node, $q_\pi(s, a)$, given $S_t = s$. This equation should include an
expectation conditioned on following the policy, $\pi$. Then give a second
equation in which the expected value is written out explicitly in terms of
$\pi(a \mid s)$ such that no expected value notation appears in the
equation.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Two forms: expectation-notation and expanded-sum.

---

## Exercise 3.19

**Statement.** The value of an action, $q_\pi(s, a)$, depends on the
expected next reward and the expected sum of the remaining rewards. Again
we can think of this in terms of a small backup diagram, this one rooted
at an action (state–action pair) and branching to the possible next
states: Give the equation corresponding to this intuition and diagram for
the action value, $q_\pi(s, a)$, in terms of the expected next reward,
$R_{t+1}$, and the expected next state value, $v_\pi(S_{t+1})$, given that
$S_t = s$ and $A_t = a$. This equation should include an expectation but
not one conditioned on following the policy. Then give a second equation,
writing out the expected value explicitly in terms of $p(s', r \mid s, a)$
defined by (3.2), such that no expected value notation appears in the
equation.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Companion to 3.18 (action-rooted backup).

---

## Exercise 3.20 🔖

**Statement.** Draw or describe the optimal state-value function for the
golf example.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References the golf example from Section 3.5 / Example 3.6.

---

## Exercise 3.21 🔖

**Statement.** Draw or describe the contours of the optimal action-value
function for putting, $q_*(s, \text{putter})$, for the golf example.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Same reference as 3.20.

---

## Exercise 3.22 🔖

**Statement.** Consider the continuing MDP shown to the right. The only
decision to be made is that in the top state, where two actions are
available, left and right. The numbers show the rewards that are received
deterministically after each action. There are exactly two deterministic
policies, $\pi_\text{left}$ and $\pi_\text{right}$. What policy is optimal
if $\gamma = 0$? If $\gamma = 0.9$? If $\gamma = 0.5$?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References the small MDP diagram in the book — need the
reward numbers to compute.

---

## Exercise 3.23 🔖

**Statement.** Give the Bellman equation for $q_*$ for the recycling
robot.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Example 3.3 dynamics table (from Ex 3.4).

---

## Exercise 3.24 🔖

**Statement.** Figure 3.5 gives the optimal value of the best state of
the gridworld as $24.4$, to one decimal place. Use your knowledge of the
optimal policy and (3.8) to express this value symbolically, and then to
compute it to three decimal places.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — numerical.)_

**Notes.** Uses the gridworld from Example 3.5. Optimal policy always
moves to A (best jump), collecting $+10$ every 5 steps.

---

## Exercise 3.25

**Statement.** Give an equation for $v_*$ in terms of $q_*$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** $v_*(s) = \max_a q_*(s, a)$ — one-liner.

---

## Exercise 3.26 🔖

**Statement.** Give an equation for $q_*$ in terms of $v_*$ and the
four-argument $p$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Direct definition:
$q_*(s, a) = \sum_{s', r} p(s', r \mid s, a) \bigl[ r + \gamma v_*(s') \bigr]$.

---

## Exercise 3.27

**Statement.** Give an equation for $\pi_*$ in terms of $q_*$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Argmax; watch ties (any distribution over argmaxes is optimal).

---

## Exercise 3.28 🔖

**Statement.** Give an equation for $\pi_*$ in terms of $v_*$ and the
four-argument $p$.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Composition of 3.26 and 3.27.

---

## Exercise 3.29 🔖

**Statement.** Rewrite the four Bellman equations for the four value
functions ($v_\pi, v_*, q_\pi$, and $q_*$) in terms of the three-argument
function $p$ (3.4) and the two-argument function $r$ (3.5).

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Marginalize $r$ out of the four-argument form; useful drill.
