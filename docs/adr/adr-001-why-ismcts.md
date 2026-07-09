# ADR-001 — Why ISMCTS

**Status:** Accepted (Phase 0).

## Context

The Pokémon TCG is a two-player zero-sum sequential game with three properties
that jointly constrain the choice of decision-making algorithm:

1. **Imperfect information.** At any state $s$, each player observes an
   *information set* $I \subseteq S$ — the set of world states consistent with
   what they have seen so far. The opponent's hand, the order of both players'
   decks, and cards under prize cards are hidden. Any admissible policy
   $\pi$ must be $I$-measurable: $\pi(a \mid s) = \pi(a \mid s')$ whenever
   $s, s' \in I$.
2. **Stochastic transitions.** Draws, coin flips, and shuffle effects mean the
   transition kernel $P(s' \mid s, a)$ is genuinely non-deterministic even
   conditional on $I$.
3. **Large but tractable branching factor.** Per-decision option counts are in
   the low tens for most turns (attach energy, play supporter, choose attack,
   respond to Trainer effects); enough to defeat exhaustive search but far
   below Go-scale.

The competition also imposes a **10-minute per-match wall-clock budget** and a
Kaggle sandbox with 2 vCPUs and 12.2 GiB RAM — no GPU, no persistent training
state between matches, and no access to the opponent's model.

We need an algorithm that (a) respects information-set structure, (b) tolerates
stochasticity, (c) runs anytime within a small per-decision budget, and
(d) requires no pre-training pipeline (our timeline is 10 weeks with a hard
Aug 16-17 Simulation deadline).

## Decision

Use **Information-Set Monte Carlo Tree Search (ISMCTS)** — specifically the
"single-observer" variant from Cowling, Powley & Whitehouse (2012) — with

- UCB1 selection at information-set nodes,
- **determinization**: at each iteration, sample a hidden state
  $h \sim P(h \mid I)$ compatible with the root information set, then simulate
  as if the game were perfect-information. $P$ is **uniform** over $I$ in
  the baseline (this ADR); an informed non-uniform variant using public
  evidence (deck lists, discard, board state) is a candidate Phase-5
  exploratory experiment or post-competition amendment — see
  [`../../notes/open-ideas.md`](../../notes/open-ideas.md) under
  *informed-determinization*.
- random rollouts in Phase 3; heuristic-guided rollouts added in Phase 4 (see
  ADR-003),
- terminal reward only (see ADR-004),
- anytime execution — the budget is simulations-per-decision, not depth.

Choosing $a$ at the root:
$$a^{*} = \arg\max_{a} \; \mathbb{E}_{h \sim P(h \mid I)}\!\left[Q(I, a, h)\right].$$

## Consequences

**Positive.**

- Information sets are first-class: sibling world states $s, s' \in I$ share
  visit statistics, so we cannot condition on hidden information the agent
  should not see. This structurally prevents *strategy fusion*, the failure
  mode of naively re-planning with a perfect-information solver over sampled
  determinizations (Frank & Basin 1998; Long et al. 2010).
- Anytime property fits the 10-minute match budget: we set a simulations
  budget per decision and the search returns the best action found so far.
- No training loop, no reward model, no policy network — the entire pipeline
  is deterministic given a seed. This makes the four pre-registered
  hypotheses (H1–H4) cleanly falsifiable and the writeup reproducible.
- Well-understood theory: UCB1 regret bounds carry over to MCTS asymptotic
  consistency (Kocsis & Szepesvári 2006) in the perfect-information limit;
  ISMCTS inherits this on the marginalized value estimate.

**Negative.**

- Determinization sampling ignores the fact that our own action reveals
  information to the opponent. The single-observer form does *not* model the
  opponent's belief update; it treats the opponent as playing against a
  perfect-information version of us. This is the *non-locality* limitation
  identified in the ISMCTS paper.
- Branching over stochastic Trainer effects (coin flips, random draws) is
  handled by chance-node determinization, which increases variance in the
  value estimate and demands more simulations for a stable UCB1 signal.
- The heuristic evaluator (Phase 4) is a hand-crafted approximation; poor
  weights degrade the rollout policy without a learning signal to correct
  them. H4 exists precisely to audit this.

## Alternatives Considered

- **Plain MCTS / UCT with perfect-information determinization at the root.**
  Rejected: strategy fusion. The agent computes different plans in different
  determinized worlds and averages the *actions*, not the *values*, which is
  incorrect. ISMCTS averages values under $P(h \mid I)$ instead.
- **Counterfactual Regret Minimization (CFR / MCCFR).** State of the art for
  imperfect-information games (Zinkevich et al. 2008; Brown & Sandholm 2018).
  Rejected on two grounds: (i) the natural formulation requires an explicit
  game tree with defined information partitions, which we do not have — the
  `cabt` engine only exposes the observation dict at each decision point;
  (ii) CFR needs many self-play iterations of tabular/abstracted state
  tracking, incompatible with our 10-week timeline and no-training-loop
  constraint. A worthy Phase-7 follow-up, not a Phase-3 baseline.
- **Model-free reinforcement learning (DQN / PPO / actor-critic).**
  Rejected: no GPU on the Kaggle worker, no time to build a self-play
  training loop that would beat a heuristic baseline, and the observation
  dict is not vector-shaped without substantial featurization work that
  competes for the same weeks. Aligned with ADR-003.
- **Belief-space POMCP** (Silver & Veness 2010). Closest cousin to ISMCTS;
  requires an explicit particle filter over hidden states. `cabt` does not
  expose the transition model in a form that makes particle reweighting
  cheap. ISMCTS's determinization sidesteps this at the cost of the
  non-locality issue noted above.

## References

- Cowling, Powley & Whitehouse (2012). *Information Set Monte Carlo Tree
  Search.* IEEE TCIAIG.
- Long, Sturtevant, Buro & Furtak (2010). *Understanding the Success of
  Perfect Information Monte Carlo Sampling in Game Tree Search.* AAAI.
- Frank & Basin (1998). *Search in games with incomplete information: A case
  study using Bridge card play.* Artificial Intelligence.
- Kocsis & Szepesvári (2006). *Bandit based Monte-Carlo Planning.* ECML.
- Browne et al. (2012). *A Survey of Monte Carlo Tree Search Methods.* IEEE
  TCIAIG.
- Zinkevich et al. (2008). *Regret Minimization in Games with Incomplete
  Information.* NeurIPS.
