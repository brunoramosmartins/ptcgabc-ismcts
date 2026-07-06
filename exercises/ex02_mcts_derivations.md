# Exercise 02 — MCTS Derivations

Phase 2 exercises companion to `notes/phase2-mcts-fundamentals.md` and
`notes/phase2-ismcts-paper-notes.md` (both drafted after reading the
Browne survey and the Cowling paper).

Focus: five rigorous derivations that form the theoretical backbone of
Phase 3. Some derivations overlap with material already worked out in
[`../notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md);
cross-refs are noted per exercise to avoid duplication — the answer here
should be the **canonical, publishable** version, and the RL-foundations
note the **exploratory** one.

Template: **statement** → **initial thoughts** → **answer** → **notes**.

---

## Exercise 02.1 — Derive UCB1 from Chernoff–Hoeffding

**Statement.** Derive the UCB1 selection rule
$$
a^* \;=\; \arg\max_a \left[ Q(a) + c\, \sqrt{\frac{\ln t}{n_a}} \right]
$$
starting from the Chernoff–Hoeffding inequality for bounded random
variables $X \in [0, 1]$:
$$
\Pr\!\bigl(\lvert \hat X - \mu \rvert > \epsilon\bigr) \;\le\; 2\, e^{-2 n \epsilon^2}.
$$
Identify precisely where the $\sqrt{2 \ln t / n_a}$ form comes from and
what the constant $c$ collects.

**Initial thoughts.**

_(fill in — or point to `notes/phase2-rl-foundations.md` §2.4 for the
first pass.)_

**Answer.**

_(pending — the canonical version. Existing draft in
[`../notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) §2.4
should be tightened and moved here, with:
(a) explicit statement of the per-arm-per-time confidence level
    $1/t^{\alpha}$ and the choice $\alpha = 4$ from Auer et al. 2002,
(b) the drop of the $\ln 2$ constant justified as $O(1)$ vs the growing
    $\ln t$ term,
(c) the identification of $c = \sqrt{\alpha / 2} = \sqrt{2}$ under
    Auer's choice.)_

**Notes.** Cross-ref:
[`../notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) §2.4.
References: Auer, Cesa-Bianchi & Fischer (2002), "Finite-time analysis
of the multiarmed bandit problem."

---

## Exercise 02.2 — MCTS asymptotic consistency (perfect information)

**Statement.** State the MCTS asymptotic consistency result of Kocsis &
Szepesvári (2006) for perfect-information games. Sketch the argument
in enough detail to identify the two ingredients:

1. Every action is sampled infinitely often as the number of simulations
   $N \to \infty$.
2. The failure probability of choosing a sub-optimal action at the root
   decays super-polynomially in $N$.

**Initial thoughts.**

_(fill in — the intuition is in
[`../notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) §2.5.)_

**Answer.**

_(pending — this is the rigorous version. Should include:
(a) exact statement of the theorem: "the probability of selecting the
    optimal action at the root converges to 1 as $N \to \infty$",
(b) sketch: infinite-visitation of every arm via UCB1's exploration
    term + concentration of the empirical $Q$ around the true $q^*$,
(c) the super-polynomial decay rate cited from Kocsis-Szepesvári.)_

**Notes.** Cross-ref:
[`../notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) §2.5.
Main reference: Kocsis & Szepesvári (2006), "Bandit-based Monte-Carlo
planning."

---

## Exercise 02.3 — ISMCTS extension and the info-set action selector

**Statement.** Extend the MCTS argmax rule to the information-set case.
Show that the ISMCTS decision rule at the root is
$$
a^* \;=\; \arg\max_a \; \mathbb{E}_{h \sim P(h \mid I)}\!\left[ Q(I, a, h) \right],
$$
where $I$ is the information set at the current observation, $h$ is a
determinized hidden state consistent with $I$, and $Q(I, a, h)$ is the
search's action-value estimate on the world where the hidden state is
$h$. Explain why the expectation is over $P(h \mid I)$ rather than any
$P(h)$ prior.

**Initial thoughts.**

_(fill in — connect to
[`../notes/phase2-rl-foundations.md`](../notes/phase2-rl-foundations.md) §3.5
where information sets are defined.)_

**Answer.**

_(pending — the derivation. Should include:
(a) definition of an information set as an equivalence class under the
    observation function, per
    [`../docs/mdp-formalization.md`](../docs/mdp-formalization.md),
(b) the $I$-measurability requirement for admissible policies
    ([`ex01_environment.md`](ex01_environment.md) §2),
(c) the argument that expectation over $P(h \mid I)$ is the unique
    $I$-measurable functional that respects the imperfect-information
    constraint,
(d) contrast with naive determinization, which computes
    $\mathbb{E}_h[\arg\max_a Q(I, a, h)]$ — the swap of argmax and
    expectation, i.e. strategy fusion.)_

**Notes.** Cross-ref: [`ex01_environment.md`](ex01_environment.md) §2,
[`../docs/mdp-formalization.md`](../docs/mdp-formalization.md),
[`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md).
Main reference: Cowling, Powley & Whitehouse (2012), "Information Set
Monte Carlo Tree Search."

---

## Exercise 02.4 — Toy example of strategy fusion

**Statement.** Construct a small imperfect-information game (2–3 actions,
2 hidden states) where naive perfect-information determinization gives
a *strictly worse* policy than ISMCTS. The example must illustrate
strategy fusion: the naive approach picks the best action *per
determinization* and averages the choices, while the correct approach
picks the action with the best *expected value across
determinizations*.

**Initial thoughts.**

_(fill in — the game should be small enough to solve by hand and large
enough to make the swap of argmax and expectation visible.)_

**Answer.**

_(pending — the toy example. Suggested structure:
(a) two hidden states $h_1, h_2$ with $P(h_1) = P(h_2) = 0.5$
    consistent with the observed information set,
(b) three actions $a_1, a_2, a_3$ with $Q(I, a, h)$ table where the
    argmax differs between $h_1$ and $h_2$, but the marginal argmax
    (over expected $Q$) points at a third, "safe" action,
(c) computation showing that per-determinization argmax gives worse
    expected return than the ISMCTS marginal argmax.)_

**Notes.** This exercise doubles as figure material for the writeup's
Threats-to-Validity section (per
[`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md),
strategy fusion is the honest limitation of naive PIMC that ISMCTS
resolves). References: Frank & Basin (1998), Long et al. (2010).

---

## Exercise 02.5 — Branching factor at a mid-game PTCG state

**Statement.** Estimate the effective branching factor of the PTCG game
tree at a representative mid-game decision point. Then estimate the
number of ISMCTS simulations needed to visit every first-turn action at
least $k = 30$ times (a standard rule-of-thumb visit threshold before
UCB1's estimate is considered informative).

**Initial thoughts.**

_(fill in — draw on
[`ex01_environment.md`](ex01_environment.md) §3 for the info-set-size
argument, but note that branching factor is a *different* quantity:
it's the number of *actions available* at a given decision, not the
number of *hidden states* consistent with the observation.)_

**Answer.**

_(pending — estimation. Suggested approach:
(a) identify the branching sources: cards playable from hand, energy
    attachments, retreat, Trainer effects — each roughly a size-3 to
    size-10 category, plus stochastic branching over draws and coin
    flips,
(b) give a range: mid-game branching factor $b \in [10, 50]$ as a
    plausible interval, justified per category,
(c) compute simulations needed: $N \ge k \cdot b$ per the UCB1
    infinite-visitation floor gives ~300–1500 sims for the first
    turn's arms alone, before deeper exploration,
(d) compare to the 10-min per-match Kaggle budget — how many decisions
    per match? each decision gets what fraction of the budget?)_

**Notes.** This exercise directly informs the Phase 4 hyperparameter
sweep (Issue #26) — the range chosen here becomes the lower bound of
the simulations-per-decision sweep. Also feeds H3 (sensitivity to
simulations/decision) since the theoretical minimum here is where we
expect the H3 curve to start responding.

Cross-ref: [`ex01_environment.md`](ex01_environment.md) §3,
[`../docs/benchmark-protocol.md`](../docs/benchmark-protocol.md) §Hardware.
