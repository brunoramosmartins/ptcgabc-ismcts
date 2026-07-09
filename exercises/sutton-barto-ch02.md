# Sutton & Barto — Chapter 2 (Multi-armed Bandits) Exercises

Reference: Sutton & Barto, *Reinforcement Learning: An Introduction*, 2nd ed.
(2018), Chapter 2.

Template per exercise: **statement (verbatim)** → **initial thoughts** →
**answer** → **notes**.

Exercises marked with 🔖 reference a figure / equation / example from the
book — likely useful to have the book open while writing the final answer.

---

## Exercise 2.1

**Statement.** In $\epsilon$-greedy action selection, for the case of two
actions and $\epsilon = 0.5$, what is the probability that the greedy
action is selected?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.**

_(open questions)_

---

## Exercise 2.2 — Bandit example

**Statement.** Consider a $k$-armed bandit problem with $k = 4$ actions,
denoted $1, 2, 3, 4$. Consider applying to this problem a bandit algorithm
using $\epsilon$-greedy action selection, sample-average action-value
estimates, and initial estimates of $Q_1(a) = 0$ for all $a$. Suppose the
initial sequence of actions and rewards is
$A_1 = 1, R_1 = -1$;
$A_2 = 2, R_2 = 1$;
$A_3 = 2, R_3 = -2$;
$A_4 = 2, R_4 = 2$;
$A_5 = 3, R_5 = 0$.
On some of these time steps the $\epsilon$ case may have occurred, causing
an action to be selected at random. On which time steps did this
**definitely** occur? On which time steps could this **possibly** have
occurred?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.**

_(open questions)_

---

## Exercise 2.3 🔖

**Statement.** In the comparison shown in Figure 2.2, which method will
perform best in the long run in terms of cumulative reward and probability
of selecting the best action? How much better will it be? Express your
answer quantitatively.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Figure 2.2 (10-armed testbed, $\epsilon$-greedy at
$\epsilon \in \{0, 0.01, 0.1\}$).

---

## Exercise 2.4 🔖

**Statement.** If the step-size parameters $\alpha_n$ are not constant,
then the estimate $Q_n$ is a weighted average of previously received
rewards with a weighting different from that given by (2.6). What is the
weighting on each prior reward for the general case, analogous to (2.6),
in terms of the sequence of step-size parameters?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Equation (2.6) is the exponential recency-weighted average
derivation for constant $\alpha$.

---

## Exercise 2.5 — programming 🔖

**Statement.** Design and conduct an experiment to demonstrate the
difficulties that sample-average methods have for nonstationary problems.
Use a modified version of the 10-armed testbed in which all the $q_*(a)$
start out equal and then take independent random walks (say by adding a
normally distributed increment with mean zero and standard deviation
$0.01$ to all the $q_*(a)$ on each step). Prepare plots like Figure 2.2
for an action-value method using sample averages, incrementally computed,
and another action-value method using a constant step-size parameter,
$\alpha = 0.1$. Use $\epsilon = 0.1$ and longer runs, say of $10\,000$
steps.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — programming; deliverable is code + plot, not prose.)_

**Notes.** Programming exercise. Deliverable will be a Jupyter notebook
under `notebooks/` (or a script under `scripts/`), producing a PNG in
`figures/`.

---

## Exercise 2.6 — Mysterious Spikes 🔖

**Statement.** The results shown in Figure 2.3 should be quite reliable
because they are averages over $2000$ individual, randomly chosen 10-armed
bandit tasks. Why, then, are there oscillations and spikes in the early
part of the curve for the optimistic method? In other words, what might
make this method perform particularly better or worse, on average, on
particular early steps?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Figure 2.3 (optimistic initial values, $Q_1 = 5$,
sample averages, $\epsilon = 0$).

---

## Exercise 2.7 — Unbiased Constant-Step-Size Trick 🔖

**Statement.** In most of this chapter we have used sample averages to
estimate action values because sample averages do not produce the initial
bias that constant step sizes do (see the analysis leading to (2.6)).
However, sample averages are not a completely satisfactory solution
because they may perform poorly on nonstationary problems. Is it possible
to avoid the bias of constant step sizes while retaining their advantages
on nonstationary problems? One way is to use a step size of

$$
\beta_n \;\dot=\; \alpha / \bar{o}_n, \qquad (2.8)
$$

to process the $n$-th reward for a particular action, where $\alpha > 0$
is a conventional constant step size, and $\bar{o}_n$ is a trace of one
that starts at $0$:

$$
\bar{o}_n \;\dot=\; \bar{o}_{n-1} + \alpha \,(1 - \bar{o}_{n-1}), \qquad
n \ge 0, \qquad \bar{o}_0 \;\dot=\; 0. \qquad (2.9)
$$

Carry out an analysis like that in (2.6) to show that $Q_n$ is an
**exponential recency-weighted average without initial bias**.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Multi-step derivation. Likely deserves display equations and a
step-by-step expansion.

---

## Exercise 2.8 — UCB Spikes 🔖

**Statement.** In Figure 2.4 the UCB algorithm shows a distinct spike in
performance on the 11th step. Why is this? Note that for your answer to be
fully satisfactory it must explain both why the reward **increases** on the
11th step and why it **decreases** on the subsequent steps. Hint: if
$c = 1$, then the spike is less prominent.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Figure 2.4 (UCB with $c = 2$ on the 10-armed testbed).

---

## Exercise 2.9

**Statement.** Show that in the case of two actions, the soft-max
distribution is the same as that given by the logistic, or sigmoid,
function often used in statistics and artificial neural networks.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Standard result; concise derivation.

---

## Exercise 2.10

**Statement.** Suppose you face a 2-armed bandit task whose true action
values change randomly from time step to time step. Specifically, suppose
that, for any time step, the true values of actions $1$ and $2$ are
respectively $0.1$ and $0.2$ with probability $0.5$ (case A), and $0.9$
and $0.8$ with probability $0.5$ (case B). If you are not able to tell
which case you face at any step, what is the best expectation of success
you can achieve and how should you behave to achieve it? Now suppose that
on each step you are told whether you are facing case A or case B
(although you still don't know the true action values). This is an
**associative search task**. What is the best expectation of success you
can achieve in this task, and how should you behave to achieve it?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Two-part exercise; each part deserves an explicit computation.

---

## Exercise 2.11 — programming 🔖

**Statement.** Make a figure analogous to Figure 2.6 for the nonstationary
case outlined in Exercise 2.5. Include the constant-step-size
$\epsilon$-greedy algorithm with $\alpha = 0.1$. Use runs of $200\,000$
steps and, as a performance measure for each algorithm and parameter
setting, use the average reward over the last $100\,000$ steps.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — programming.)_

**Notes.** Same setup as Ex 2.5 + Ex 2.7 baselines; combines
$\epsilon$-greedy, gradient bandit, UCB, and optimistic initial values.
