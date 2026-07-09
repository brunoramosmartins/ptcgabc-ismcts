# Phase 2 — Cross-Source Synthesis

Central file for questions that cut across multiple readings (Sutton &
Barto, Browne survey, Cowling ISMCTS paper) and for the emerging
target-architecture picture. Kept separate from the per-paper walkthroughs
so answers that draw on the full corpus don't get pinned to a single
source.

Cross-refs:
- [`phase2-rl-foundations.md`](phase2-rl-foundations.md) — S&B Ch 1–3, 8
  concept notes and prompts.
- [`phase2-mcts-fundamentals.md`](phase2-mcts-fundamentals.md) — Browne
  survey walkthrough.
- [`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md) —
  Cowling walkthrough.
- [`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md)
  — the architectural decision this synthesis stress-tests.
- [`open-ideas.md`](open-ideas.md) — capture point for anything the
  synthesis surfaces as a testable idea.

Prompts here fill *after* their prerequisite readings finish, not while
reading. Template as usual: **Prompt** → **My take** → **Refined
write-up**.

Living document; ends with `## Lessons Learned` and `## Failed Attempts`
at Phase-2 merge time.

---

## Prerequisites

Fill each row as you finish the corresponding reading.

| Reading | Status |
|---|---|
| S&B Ch 1–3, 8 | ✅ answered in `phase2-rl-foundations.md` |
| Browne (2012) survey | ✅ answered in `phase2-mcts-fundamentals.md` |
| Cowling et al. (2012) | ✅ answered in `phase2-ismcts-paper-notes.md` |
| Long, Sturtevant, Buro & Furtak (2010) | ✅ answered in `phase2-long-2010-notes.md` |

---

## Cross-source prompts

### CS.1 — Sutton & Barto's MCTS vs Browne's MCTS

**Prompt.** Compare S&B Ch 8 §8.11 with the corresponding sections in
Browne.

- Which one is more mathematically precise?
- Which is more useful as an *implementation reference*?
- Which sections of Browne would you skip if re-reading only for
  implementation guidance vs conceptual understanding?

**My take.**

Sutton & Barto and Browne present MCTS from complementary rather than competing perspectives.

Sutton & Barto provide the theoretical foundations, explaining MCTS as an online planning algorithm built upon Monte Carlo estimation and the UCB framework from multi-armed bandits. Their presentation is mathematically coherent and emphasizes why the algorithm works, but intentionally omits many implementation details.

Browne et al., in contrast, focus on the engineering of competitive MCTS systems. The survey covers rollout policies, tree policies, Progressive Widening, transposition tables, parallelization, and many practical variants that arise when applying MCTS to complex domains.

For implementation purposes, Browne is by far the more valuable reference. For conceptual understanding and connecting MCTS to reinforcement learning, Sutton & Barto remain unmatched.

If revisiting Browne solely to implement an agent, I would concentrate on the core MCTS phases, rollout policies, Progressive Widening, transposition tables, and practical enhancements. For conceptual review, I would instead prioritize the historical motivation, taxonomy of variants, and discussions of strengths and limitations.

Taken together, the two works illustrate an important progression: Sutton & Barto explain why online Monte Carlo planning is principled, while Browne explains how to make it effective in practice.

**Refined write-up.**

Sutton & Barto (Chapter 8) and Browne et al. address Monte Carlo Tree Search at different levels of abstraction. Sutton & Barto frame MCTS within the reinforcement learning paradigm, presenting it as an online planning algorithm that combines Monte Carlo estimation with UCB-based exploration. Their treatment is mathematically rigorous in establishing the algorithm's theoretical foundations but intentionally avoids implementation-specific optimizations.

Browne et al. complement this perspective by surveying the design space of practical MCTS systems. Rather than deriving the algorithm from first principles, the survey examines the numerous engineering decisions required for high-performance implementations, including rollout policies, tree policies, Progressive Widening, transposition tables, parallelization strategies, and domain-specific enhancements.

Consequently, the two references serve distinct purposes. Sutton & Barto are the preferred source for understanding the theoretical relationship between planning, reinforcement learning, and Monte Carlo estimation. Browne is the primary implementation reference, offering practical guidance for constructing competitive search agents.

From the perspective of this project, Browne would be the document to revisit during implementation, while Sutton & Barto would remain the conceptual foundation. Together, they establish a coherent progression from the theory of online planning to the engineering of efficient Monte Carlo search systems, which is subsequently extended by ISMCTS for imperfect-information domains and later by neural-guided planning methods such as AlphaGo, AlphaZero, and MuZero.

---

### CS.2 — What Browne does *not* prepare you for

**Prompt.** Before opening the Cowling paper, write down what you
*expect* Cowling to add on top of Browne. This is the "prediction
before reading" exercise that makes the next paper stick.

- What algorithmic modification do you expect for imperfect information?
- What experimental setup would you expect them to use (game, baseline,
  metric)?
- What theoretical guarantee (if any) do you expect them to prove?

**My take.**

After finishing Browne, I expected that adapting MCTS to imperfect-information games would primarily require sampling plausible hidden states before running the search. I imagined an architecture where each search iteration would begin by generating a complete world consistent with the player's observations, followed by a standard MCTS execution on that sampled state.

I also expected the paper to introduce some form of belief distribution over hidden information, although I assumed the search tree itself would still be indexed by fully observable game states. In retrospect, this was the main misconception: Cowling's key contribution is not merely better sampling but redefining the search tree around information sets rather than true states.

Experimentally, I expected evaluations on classic imperfect-information games such as Poker or Whist, comparing the proposed algorithm against standard MCTS using metrics like win rate, computation time, and simulation budget.

Theoretically, I expected only limited guarantees, such as consistency with standard MCTS in fully observable games or preservation of UCT-like behavior under certain assumptions. I did not expect strong optimality guarantees for imperfect-information domains.

**Refined write-up.**

Browne's survey thoroughly explains how to engineer efficient Monte Carlo Tree Search algorithms but largely assumes perfect state observability. Consequently, before reading Cowling et al., the natural expectation is that extending MCTS to imperfect-information games would involve sampling plausible hidden states and executing standard MCTS over each sampled world.

This prediction correctly anticipates the importance of belief generation but underestimates the conceptual shift introduced by ISMCTS. Rather than modifying only the sampling procedure, Cowling fundamentally changes the search representation by constructing the tree over information sets instead of true game states. This redesign addresses limitations of naive determinization while preserving the overall MCTS framework.

From an experimental perspective, one would expect comparisons against standard MCTS or determinization-based approaches on classical imperfect-information games, using win rate and computational efficiency as primary evaluation metrics. Likewise, only modest theoretical guarantees would be expected, such as compatibility with standard MCTS under full observability, rather than optimality results for imperfect-information planning.

This transition illustrates how the sequence of papers progressively elevates the level of abstraction. Browne focuses on optimizing search within a known state, whereas Cowling redefines what constitutes the search state itself, laying the foundation for planning under uncertainty.

---

### CS.3 — Cowling's variant choice for PTCG

**Prompt.** The Cowling paper offers SO-ISMCTS, MO-ISMCTS, and possibly
a third variant.

- Restate the trade-off between the three variants for our specific
  Kaggle constraints (10-min per-match budget, 2 vCPUs, no persistent
  state).
- Which does ADR-001 commit us to? Is the argument still valid after
  reading the paper, or does the paper suggest a different choice?
- If the paper's argument changes our mind, propose an amendment ADR.

**My take.**

For the constraints of the Kaggle Pokémon TCG Challenge, SO-ISMCTS provides the best balance between search quality, computational efficiency, and implementation complexity.

SO-ISMCTS maintains a single search tree rooted at the acting player's information set, allowing the search budget to be concentrated on optimizing the current decision. SO-ISMCTS with a Predictive Opponent Model (POM) could improve simulation quality by producing more realistic opponent actions, but it introduces additional modeling complexity that is difficult to justify before establishing a strong baseline. MO-ISMCTS offers a richer representation by maintaining separate trees for multiple players, but its higher computational and memory costs make it less attractive under a limited CPU budget.

ADR-001's decision to adopt SO-ISMCTS remains valid after reading Cowling et al. However, the rationale becomes stronger and more principled. The primary justification is no longer implementation simplicity alone, but the observation that the agent's objective is to optimize decisions from its own information set. SO-ISMCTS directly matches this objective while preserving a favorable computation-to-search ratio.

I would therefore keep ADR-001 unchanged in terms of architectural choice, but amend its motivation to emphasize problem formulation rather than implementation convenience. Future work should first evaluate the empirical value of opponent modeling before considering POM or MO-ISMCTS.

**Refined write-up.**

Cowling et al. present three progressively richer approaches for applying Monte Carlo Tree Search to imperfect-information games: SO-ISMCTS, SO-ISMCTS with a Predictive Opponent Model (POM), and MO-ISMCTS. These variants differ primarily in how they represent uncertainty and model the decisions of other players.

Given the computational constraints of the Pokémon TCG AI Challenge—limited CPU resources, a fixed per-match time budget, and no persistent search state—SO-ISMCTS provides the most appropriate baseline. It concentrates the search budget on optimizing the acting player's decisions while avoiding the computational overhead associated with maintaining multiple search trees or learning explicit opponent policies.

Reading Cowling strengthens rather than overturns ADR-001. The original decision to adopt SO-ISMCTS remains appropriate, but the underlying rationale becomes more rigorous. The key insight is that the search should be rooted in the acting player's information set, since action selection is conditioned on the information currently available to that player. This makes SO-ISMCTS not only computationally efficient but also conceptually aligned with the planning problem itself.

Accordingly, ADR-001 should be amended only to clarify its motivation. Opponent modeling and MO-ISMCTS should be treated as future extensions whose value must be demonstrated empirically rather than assumed a priori. This staged progression is also consistent with the broader philosophy established by Long et al.: characterize the domain first, then introduce additional algorithmic complexity only when experiments justify it.

---

### CS.4 — What Cowling leaves for the implementer

**Prompt.** Before writing any ISMCTS code (Phase 3, Issue #16),
enumerate what the paper leaves as an implementation exercise.

- Data structures for the search tree — is the paper prescriptive or
  does it leave this open?
- The rollout policy — the paper likely assumes it's given. What
  choices does that leave us? (Answer: random or heuristic, per Phase
  3 vs Phase 4.)
- Handling of chance nodes (coin flips, random card effects) —
  explicit modeling vs implicit sampling through the engine.

**My take.**

Cowling et al. define the logical structure of ISMCTS but intentionally leave many engineering decisions to the implementer.

The paper specifies the statistics maintained at each node (visits, rewards, availability counts, children) but does not prescribe any concrete data structure, memory layout, hashing strategy, or software architecture. Likewise, the representation of an information set is treated as domain-specific, leaving the implementer responsible for defining how observations are encoded and how equivalent information sets are identified.

The rollout policy is also intentionally abstract. For the Pokémon TCG project, this naturally suggests a staged approach: begin with purely random rollouts in the baseline implementation (Phase 3) and later replace them with heuristic-guided rollouts (Phase 4), following the recommendations from Browne et al.

Finally, Cowling assumes that stochastic events can be simulated correctly but does not discuss explicit chance nodes. Since the Kaggle game engine already models deck shuffling, card draws, and coin flips, the simplest and most efficient implementation is to rely on implicit sampling performed by the environment rather than explicitly representing chance nodes in the search tree.

Overall, Cowling specifies the search algorithm but not the software architecture. Bridging that gap is the primary implementation challenge of Phase 3.

**Refined write-up.**

Cowling et al. describe the algorithmic principles of Information Set Monte Carlo Tree Search while deliberately leaving several implementation details unspecified. The paper defines the information that each search node must maintain, such as visit counts, accumulated rewards, availability statistics, and child links, but does not prescribe concrete data structures, memory management strategies, or interfaces for representing the search tree.

Similarly, the representation of information sets is treated as a domain-dependent design choice. For Pokémon TCG, this requires defining a canonical encoding of all publicly observable information together with a mechanism for generating plausible determinizations consistent with that observation.

The rollout policy is intentionally left open. A practical implementation strategy is to begin with random rollouts to validate the search framework and subsequently introduce heuristic-guided simulations to improve evaluation quality, consistent with Browne et al.'s recommendations regarding informed simulation policies.

Finally, although ISMCTS operates in stochastic environments, Cowling does not advocate explicit chance nodes. Given that the Pokémon TCG engine already resolves random events internally, implicit sampling through the environment provides a simpler and computationally efficient solution.

These implementation decisions illustrate the distinction between an algorithm specification and a complete software architecture. ISMCTS defines how search should operate over information sets; designing efficient data structures, state representations, rollout policies, and engine integration remains the responsibility of the implementer.

---

### CS.5 — Predictions vs reality

**Prompt.** Go back to §CS.2 above and look at what you predicted before
reading Cowling.

- Which predictions were right?
- Which were wrong, and what surprised you?
- What does this tell you about your own model of "what's hard about
  imperfect-information games"?

**My take.**

Most of my predictions before reading Cowling were directionally correct but underestimated the depth of the proposed solution.

I correctly anticipated that the algorithm would rely on sampling plausible hidden states, compare against determinization-based methods, and provide only limited theoretical guarantees. I also expected belief generation to play an important role.

My main mistake was assuming that the search tree would still be organized around complete game states. Instead, Cowling's central insight is that the search tree itself should be indexed by information sets. This shifts the problem from estimating the true hidden state to optimizing decisions conditioned on the information actually available to the player.

The biggest surprise was realizing that imperfect-information planning is fundamentally a representation problem rather than a prediction problem. The goal is not to infer the opponent's exact hand but to reason consistently across all plausible worlds compatible with current observations.

This changed my own understanding of what makes imperfect-information games difficult. I initially viewed hidden information as an inference challenge. After reading Cowling, I see it primarily as a planning problem under uncertainty, where the quality of the representation of available information is more important than perfectly reconstructing the hidden state.

**Refined write-up.**

Comparing my predictions with Cowling's actual contribution reveals that my intuition was largely correct regarding the need for hidden-state sampling, but incomplete regarding the nature of the search representation. I expected ISMCTS to extend conventional MCTS by adding a belief-generation stage before search. Instead, Cowling fundamentally redefines the search tree itself by indexing nodes with information sets rather than fully observable game states.

This distinction proved to be the most important conceptual lesson of the paper. The core challenge of imperfect-information planning is not accurately predicting hidden information, but making robust decisions given incomplete observations. Belief generation serves only to produce plausible determinizations that support planning; it is not an end in itself.

This realization significantly changed my own mental model of imperfect-information games. I initially framed the problem as one of state inference. After studying ISMCTS, I now view it as a problem of planning under uncertainty, where the central design question becomes how to represent and exploit the information actually available to the agent. This shift directly influenced the architecture adopted in this project, placing the Information Set at the center of the planning process rather than the hidden true state.

---

## Target architecture (post-survey sketch)

After reading Browne, you sketched a candidate architecture combining
several ideas from the survey (belief inference, action ranking,
progressive widening, UCT, guided rollouts). Captured here as a
snapshot — it will not be implemented as-is in Phase 3, but it's the
right document for the "what would the full system look like" picture
that motivates each individual EXP in Phases 3–5.

### Sketch

```
                Current State
                     │
                     ▼
         Belief State Generator
    (infer opponent deck archetype;
     see open-ideas informed-determinization)
                     │
                     ▼
           Action Generator
       (legal actions at this turn)
                     │
                     ▼
            Action Ranking
    (heuristic scorer; reuses ADR-003 evaluator;
     see open-ideas progressive-widening-with-action-ranking)
                     │
                     ▼
         Progressive Widening
       (top-k children as v grows)
                     │
                     ▼
              UCT Selection
         (UCB1 over expanded children;
          ADR-001 baseline)
                     │
                     ▼
          Guided Rollout Policy
      (random in Phase 3, heuristic in Phase 4;
       ADR-003, H2)
                     │
                     ▼
             Backpropagation
       (sample-average, α = 1/n;
        phase2-rl-foundations §2.2)
                     │
                     ▼
            Best action found
```

### Which pieces are baseline (ADR-locked)

- **UCT Selection** — locked by [ADR-001](../docs/adr/adr-001-why-ismcts.md).
- **Guided Rollout Policy (random → heuristic)** — locked by
  [ADR-001](../docs/adr/adr-001-why-ismcts.md) and
  [ADR-003](../docs/adr/adr-003-heuristic-not-learned-evaluator.md);
  tested by H2.
- **Backpropagation as sample-average** — implied by
  [ADR-004](../docs/adr/adr-004-terminal-reward-not-shaped.md) and the
  Phase 3 architectural choice.

### Which pieces are candidate (in `open-ideas.md`)

- **Belief State Generator** → *informed-determinization* (both
  constraint refinement and archetype-based priors). **Gated on
  `oracle-baseline-cheating-uct`** — measure the imperfect-information
  ceiling before implementing the belief pipeline.
- **Action Ranking + Progressive Widening** →
  *progressive-widening-with-action-ranking*. Independent of the
  belief-based line; can proceed regardless of the ceiling.
- **Transposition Table (not shown in sketch)** →
  *transposition-tables-for-info-sets*. Pure speedup, not gated.
- **RAVE with per-archetype conditioning (not shown in sketch, but a
  natural layer on top of Backpropagation)** →
  *archetype-conditioned-rave*. Transitively gated (depends on the
  archetype module from *informed-determinization*).

### The diagnostic that gates everything

Before any of the Belief State Generator work, run
*oracle-baseline-cheating-uct* to measure

$$
\Delta_{\text{ceiling}} \;=\; W_{\text{cheat}} - W_{\text{ISMCTS}}.
$$

The ceiling gap tells us how much headroom belief-based ideas have.
Small gap → drop the belief pipeline entirely, focus Phase 5 on
Progressive Widening and Transposition Tables (which don't depend on
opponent modeling). Large gap → the target architecture above becomes
worth implementing.

### The experimental ladder (research architecture)

The measurement layer matters as much as the agent. Consolidated after
the Long reading: the Phase 3 diagnostic experiment runs **four agents
on the same 200 paired seeds** against the fixed heuristic reference,
decomposing the total gap into interpretable pieces.

```
Random ── floor sanity check (EXP-001, done: 364.6 ladder)
   │
Heuristic ── reference opponent (EXP-002, done: 527.9 ladder, 75.5% local)
   │
PIMC (Determinized UCT) ──┐
   │                      │  W_ISMCTS − W_PIMC = value of the shared
ISMCTS (SO, ADR-001) ─────┘  info-set tree (Cowling's claim, in PTCG)
   │
Cheating UCT (oracle) ── W_cheat − W_ISMCTS = Δ_ceiling
                          (cost of hidden information; gates the
                           belief pipeline)
```

Entries in [`open-ideas.md`](open-ideas.md):
*pimc-baseline-determinized-uct* and *oracle-baseline-cheating-uct*.
Long's three properties (leaf correlation, bias, disambiguation)
predict both deltas before the run — priors registered in
[`phase2-long-2010-notes.md`](phase2-long-2010-notes.md) §4.2
(prediction: medium $\Delta_{\text{ceiling}}$, 5–15 pp).

### What the sketch is missing

The sketch is a decision-time pipeline; it doesn't show:

- Chance nodes for coin flips and random card effects (Cowling
  §4 material — check whether the paper models these as explicit
  branching or delegates to the engine).
- Opponent's tree in MO-ISMCTS (SO-ISMCTS is per ADR-001; if Cowling
  argues we should upgrade, revisit).
- Match-level state that persists across decisions (e.g., updated
  archetype posterior). ISMCTS itself rebuilds the tree each decision,
  but the Belief State Generator can maintain state across turns.

Revisit this sketch after finishing Cowling and before starting Phase 3
implementation. The pieces that survive the reading become the Phase 3
plan; the pieces that don't move to a proper `notes/deferred-projects.md`
entry or stay in `open-ideas.md`.

---

## Lessons Learned

The main outcome of Phase 2 was not selecting a particular search algorithm, but developing a better mental model of planning under uncertainty.

The project initially approached the problem from an algorithm-centric perspective ("How should MCTS be adapted to Pokémon TCG?"). After studying Sutton & Barto, Browne, Cowling, and Long et al., the central question became:

> "How can an agent make the best possible decision given only the information currently available?"

This shift changed almost every architectural decision.

Major lessons learned:

- **Planning and learning are distinct problems.** MCTS is fundamentally an online planning algorithm rather than a reinforcement learning algorithm, despite borrowing concepts such as Monte Carlo estimation and UCB.

- **The search representation matters as much as the search algorithm.** Cowling showed that replacing states with Information Sets is a deeper change than simply adding belief sampling.

- **Belief models are not predictors.** Their purpose is not to reconstruct the opponent's hidden hand, but to generate plausible determinizations consistent with current observations.

- **Domain properties determine algorithm choice.** Long et al. demonstrated that the usefulness of sophisticated imperfect-information methods depends on measurable domain characteristics (Leaf Correlation, Bias, and Disambiguation Factor), not merely on the presence of hidden information.

- **Complexity should be experimentally justified.** Rather than implementing every published enhancement, each additional architectural component should earn its place through measurable improvements.

- **Research infrastructure is part of the contribution.** Oracle baselines, PIMC baselines, paired-seed experiments, and explicit hypotheses are as important as the final agent itself.

The resulting philosophy for the remainder of the project is:

> Characterize the domain first. Measure the value of information. Only then increase algorithmic complexity.

## Failed Attempts

Several early assumptions were revised during Phase 2.

### 1. Treating hidden information primarily as a prediction problem

Initially, the project focused on estimating the opponent's hidden hand.

After studying ISMCTS, this was replaced by a planning perspective: the objective is not to predict the true hidden state, but to optimize decisions over all plausible states consistent with current observations.

---

### 2. Assuming the search tree should be built over true game states

Before reading Cowling, the expected architecture was:

Observation
→ Sample World
→ Standard MCTS

ISMCTS showed that the search tree itself should instead be indexed by Information Sets.

---

### 3. Assuming more sophisticated algorithms are always better

The original roadmap implicitly favored adding increasingly sophisticated techniques (belief inference, opponent modeling, neural components).

Long et al. demonstrated that additional complexity is only justified if the domain actually benefits from it.

This motivated the Oracle baseline experiment and the Δ_ceiling diagnostic before implementing belief-based methods.

---

### 4. Viewing implementation as a direct translation of the papers

Initially, the expectation was that the papers would specify a nearly complete implementation.

Instead, Browne and Cowling define algorithmic principles while leaving many critical engineering decisions open, including data structures, Information Set representation, rollout policies, and integration with the game engine.

These implementation choices became explicit architectural decisions documented through ADRs.

---

No implementation work was discarded during Phase 2, since this phase was entirely conceptual. The failed attempts were therefore conceptual models that were replaced by more accurate formulations after studying the literature.
