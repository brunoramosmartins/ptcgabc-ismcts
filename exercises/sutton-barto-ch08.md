# Sutton & Barto — Chapter 8 (Planning & Learning) Exercises

Reference: Sutton & Barto, *Reinforcement Learning: An Introduction*, 2nd ed.
(2018), Chapter 8.

Chapter 8 is the pivot from model-free RL (Ch 4–7) to the MCTS family
(Section 8.11), which is what this project builds on. Ties directly to
[`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md).

All eight exercises reference a figure or algorithm listing from the book,
so keep the PDF open when answering.

---

## Exercise 8.1 🔖

**Statement.** The nonplanning method looks particularly poor in Figure
8.3 because it is a one-step method; a method using multi-step
bootstrapping would do better. Do you think one of the multi-step
bootstrapping methods from Chapter 7 could do as well as the Dyna method?
Explain why or why not.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Figure 8.3 (Dyna planning-steps comparison) and
Chapter 7 (n-step bootstrapping).

---

## Exercise 8.2 🔖

**Statement.** Why did the Dyna agent with exploration bonus, Dyna-Q+,
perform better in the first phase as well as in the second phase of the
blocking and shortcut experiments?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References the blocking (Fig 8.4) and shortcut (Fig 8.5)
experiments. Two-phase question — address both.

---

## Exercise 8.3 🔖

**Statement.** Careful inspection of Figure 8.5 reveals that the
difference between Dyna-Q+ and Dyna-Q narrowed slightly over the first
part of the experiment. What is the reason for this?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** Subtle observational question. Focus on what happens as the
model becomes more accurate.

---

## Exercise 8.4 — programming 🔖

**Statement.** The exploration bonus described above actually changes the
estimated values of states and actions. Is this necessary? Suppose the
bonus $\kappa \sqrt{\tau}$ was used not in updates, but solely in action
selection. That is, suppose the action selected was always that for which
$Q(S_t, a) + \kappa \sqrt{\tau(S_t, a)}$ was maximal. Carry out a
gridworld experiment that tests and illustrates the strengths and
weaknesses of this alternate approach.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — programming; notebook or script deliverable.)_

**Notes.** Note the structural similarity to UCB1's exploration bonus in
action selection — this is what MCTS does. Possible connection to write up.

---

## Exercise 8.5 🔖

**Statement.** How might the tabular Dyna-Q algorithm shown on page 164 be
modified to handle stochastic environments? How might this modification
perform poorly on changing environments such as considered in this
section? How could the algorithm be modified to handle stochastic
environments and changing environments?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References the Dyna-Q algorithm listing on p. 164.
Three-part question: stochastic-only, its weakness under change,
combined fix.

---

## Exercise 8.6

**Statement.** The analysis above assumed that all of the $b$ possible
next states were equally likely to occur. Suppose instead that the
distribution was highly skewed, that some of the $b$ states were much
more likely to occur than most. Would this strengthen or weaken the case
for sample updates over expected updates? Support your answer.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References the sample-vs-expected update analysis (Section 8.5
region). Directly relevant to our design choice: MCTS uses sample updates
because the transition distribution in PTCG is highly skewed by rare
Trainer effects.

---

## Exercise 8.7 🔖

**Statement.** Some of the graphs in Figure 8.8 seem to be scalloped in
their early portions, particularly the upper graph for $b = 1$ and the
uniform distribution. Why do you think this is? What aspects of the data
shown support your hypothesis?

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending)_

**Notes.** References Figure 8.8 (trajectory sampling comparison).
Deterministic $b = 1$ is a special case — think about what "sample" and
"expected" collapse to.

---

## Exercise 8.8 — programming 🔖

**Statement.** Replicate the experiment whose results are shown in the
lower part of Figure 8.8, then try the same experiment but with $b = 3$.
Discuss the meaning of your results.

**Initial thoughts.**

_(fill in)_

**Answer.**

_(pending — programming.)_

**Notes.** Replication + extension. Pairs naturally with the notebook
from Ex 8.4.
