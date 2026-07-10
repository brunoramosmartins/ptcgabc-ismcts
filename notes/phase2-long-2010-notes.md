# Phase 2 — Long et al. 2010 Notes (Understanding PIMC)

Reading-companion prompts for **Long, J., Sturtevant, N.R., Buro, M., &
Furtak, T. (2010).** *Understanding the Success of Perfect Information
Monte Carlo Sampling in Game Tree Search.* AAAI Conference on
Artificial Intelligence.

Purpose: give targeted questions to answer while reading. This paper
is shorter and more focused than the Browne survey and the Cowling
ISMCTS paper, so this file has fewer prompts. Read after Cowling — the
paper's framing assumes you know what PIMC (Perfect Information Monte
Carlo, i.e., naive determinization) is and why it's theoretically
suspect.

Two reasons this paper became important during Phase 2:

1. **Cowling cites Long directly** ([`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md) §6.2).
   Cowling's argument is that ISMCTS improves *on* PIMC; Long's is
   that PIMC works *at all* despite the theoretical objections
   (strategy fusion, non-locality). Reading Long clarifies what
   Cowling is improving on and by how much.
2. **The `oracle-baseline-cheating-uct` idea in [`open-ideas.md`](open-ideas.md) derives from
   this paper's methodology.** Long uses a cheating oracle as an
   upper-bound reference throughout their analysis. Reading Long
   calibrates our own oracle experiment: what shape of gap should we
   expect, what does the gap mean, and what implementation choices
   affect its interpretation?

Template: **Prompt** → **My take** → **Refined write-up**. Same
convention as the other Phase-2 note files.

Living document; ends with `## Lessons Learned` and `## Failed Attempts`
at merge time.

---

## §1 — The puzzle: why does PIMC work?

### 1.1 — The theoretical objections vs the empirical successes

**Prompt.** The paper opens with a paradox. Naive PIMC (sample a
determinization, solve with perfect-info search, act) is theoretically
compromised by *strategy fusion* (Frank & Basin 1998) and
*non-locality* (Long's earlier work).

- Restate the theoretical objections in your own words. What
  specifically should go wrong under the naive approach?
- What are the empirical successes the paper cites (Bridge, Skat,
  Klondike, etc.)? Cross-check with Cowling §1.2, which cites the same
  history.
- What is the specific research question the paper poses in this
  tension?

**My take.**

PIMC presents an interesting paradox. From a theoretical perspective, it is fundamentally flawed because it treats each determinization as an independent perfect-information game. This leads to strategy fusion, where the agent incorrectly assumes it can choose different actions depending on hidden information it does not actually possess, and non-locality, where the value of a decision may depend on information outside the current subtree. These problems are structural and cannot be eliminated simply by increasing the number of sampled determinizations.

Despite these theoretical objections, PIMC achieved remarkable practical success in games such as Bridge, Skat, and Hearts, where it reached expert-level performance. This apparent contradiction motivates the central question of the paper.

Rather than asking whether PIMC is theoretically correct, the authors ask why it performs well in practice. Their hypothesis is that the effectiveness of PIMC depends on measurable properties of the game itself rather than on the mere existence of imperfect information. Understanding these properties can help predict when naive determinization is sufficient and when more sophisticated approaches, such as ISMCTS, become necessary.

**Refined write-up.**

The paper addresses a long-standing discrepancy between theory and practice in imperfect-information game search. Previous work by Frank and Basin demonstrated that Perfect Information Monte Carlo (PIMC) suffers from two fundamental weaknesses: strategy fusion, which assumes different optimal actions can be selected for indistinguishable states, and non-locality, where the optimal value of a decision may depend on information outside the explored subtree. These limitations are inherent to the determinization approach and cannot be resolved by increasing the number of simulations.

However, PIMC has produced highly competitive agents in several imperfect-information games, including Bridge, Skat, and Hearts. This empirical evidence suggests that the theoretical deficiencies do not necessarily translate into poor practical performance.

The central contribution of the paper is to shift the research question from evaluating whether PIMC is theoretically sound to understanding under which game characteristics it becomes an effective approximation. The authors hypothesize that a small set of measurable domain properties explains when the errors introduced by determinization have little impact on decision quality, providing a principled framework for predicting the suitability of PIMC in new domains.

---

## §2 — The three properties that predict PIMC success

### 2.1 — Leaf correlation

**Prompt.** The paper identifies **leaf correlation** as the first key
property. If, across the different worlds consistent with the current
information set, the *ranking* of actions at the leaves tends to
agree, PIMC will act consistently even though each determinization is
solved independently.

- Give the paper's formal definition of leaf correlation.
- What does high leaf correlation look like intuitively? What does low
  correlation look like?
- Bridge has high leaf correlation — the same tricks-and-tempo logic
  applies in most world states. What's the analog for PTCG? At mid-game,
  do the same actions dominate across most hidden-hand realizations,
  or do actions shuffle dramatically based on the specific hidden
  configuration?

**My take.**

The paper defines **leaf correlation** as the probability that sibling terminal nodes have the same payoff. In the synthetic trees, correlated leaf pairs receive identical outcomes, while anti-correlated pairs receive opposite outcomes. This property measures how sensitive the final result is to small differences in the search tree.

High leaf correlation means that different actions often lead to similar outcomes. Even if PIMC makes different decisions across determinizations because of hidden information, those decisions are likely to have similar values, reducing the practical impact of strategy fusion. Low leaf correlation has the opposite effect: small differences in the hidden state can completely change which action is optimal, making determinization errors much more costly.

For Pokémon TCG, I suspect leaf correlation is not constant throughout the game. During the opening turns, many setup actions remain strong regardless of the opponent's exact hidden hand, suggesting relatively high correlation. As the game progresses and resource management becomes more critical, hidden information is more likely to change the ranking of actions, reducing leaf correlation. This suggests that the effectiveness of PIMC-style search may vary across different phases of a match rather than being determined by a single global property.

**Refined write-up.**

Leaf correlation is defined as the probability that sibling terminal nodes share the same payoff. In the synthetic game model, correlated leaf pairs are assigned identical outcomes, whereas anti-correlated pairs receive opposite outcomes. This metric captures how robust the value of an action is to small variations in the underlying game state.

The experiments identify leaf correlation as the strongest predictor of PIMC performance. When correlation is high, many actions remain similarly valuable across different determinizations, so solving each sampled world independently rarely changes the final decision. Consequently, the structural errors introduced by strategy fusion have limited practical impact. Conversely, low leaf correlation implies that small changes in hidden information frequently alter the optimal action, amplifying the consequences of determinization errors and significantly degrading PIMC performance.

For Pokémon TCG, leaf correlation is likely state-dependent rather than a fixed property of the domain. Early-game positions may exhibit relatively high correlation because multiple setup actions remain effective across many plausible hidden states. In contrast, late-game positions, where hidden resources and precise tactical decisions become decisive, are expected to exhibit lower correlation. This suggests that the suitability of determinization-based search may change dynamically throughout a match.

---

### 2.2 — Bias

**Prompt.** The second property, **bias**, is how systematically one
player's expected outcome deviates from 50/50 in the underlying game.

- What does the paper mean by bias precisely?
- Their finding: bias affects the *absolute* win rate but not the
  *relative* comparison between PIMC and the cheating oracle. Confirm
  from the paper.
- Is PTCG biased? Same deck used by both players in Phase 3, so
  probably symmetric — but the ladder pool aggregates over many
  matchups. Note whether bias matters for interpreting our oracle
  baseline experiment.

**My take.**

The paper defines **bias** as the probability that a correlated pair of terminal nodes favors one player over the other. In the synthetic trees, bias only affects correlated leaf pairs: when two sibling leaves receive the same outcome, bias determines whether that shared value is +1 or -1. A bias of 0.5 represents a balanced game, while values closer to 0 or 1 indicate that large portions of the game tree systematically favor one player.

The experiments show that bias has only a modest effect on PIMC performance compared to leaf correlation. Strong bias slightly improves PIMC's absolute performance because many regions of the tree already favor the same player, making decision errors less costly. However, the relative advantage of PIMC over stronger search methods changes much less than with variations in leaf correlation or disambiguation.

For Pokémon TCG, I expect bias to depend on the evaluation setting. In Phase 3, where both players use the same deck under symmetric rules, the game should be approximately unbiased. In contrast, a ladder environment containing many different deck matchups naturally introduces bias through deck strength rather than search quality. Therefore, when comparing our agent against an oracle baseline, the performance gap is likely to be more informative than the absolute win rate, since it better isolates the contribution of the search algorithm from the underlying matchup advantage.

**Refined write-up.**

Bias measures the probability that correlated terminal nodes favor one player rather than the other. Within the synthetic tree model, it is applied only to correlated sibling leaf pairs, determining whether they jointly receive a payoff of +1 or -1. A bias of 0.5 corresponds to a balanced game, whereas increasingly extreme values create large homogeneous regions in which the same player is likely to win regardless of the precise sequence of actions.

The experimental results indicate that bias influences the absolute performance of PIMC, but its impact is considerably smaller than that of leaf correlation. As the game becomes more biased, PIMC tends to perform slightly better because favorable outcomes become more common across the search space. However, bias alone does not explain the success or failure of determinization-based search, and it has a much weaker effect on the relative comparison with stronger reference players than the structural properties captured by leaf correlation and disambiguation.

For the Pokémon TCG AI Challenge, bias should be interpreted carefully. Under a symmetric evaluation protocol where both players use the same deck, the domain is expected to exhibit little inherent bias. In broader ladder evaluations, however, deck composition and matchup diversity introduce systematic advantages unrelated to search quality. Consequently, oracle-based evaluations should emphasize the performance gap between agents rather than absolute win rates, reducing the influence of domain-specific bias on the interpretation of results.

---

### 2.3 — Disambiguation factor

**Prompt.** The third and most important property is
**disambiguation**: how quickly the information set shrinks as the
game progresses (through observed actions, revealed cards, forced
plays, etc.).

- Give the paper's operational definition of disambiguation.
- What is the connection between high disambiguation and PIMC's
  success? Intuitively: if the information set collapses quickly, each
  determinization is "close to reality" for most of the search, so
  even an incorrect world model produces sensible plans.
- PTCG: the discard pile grows every turn, revealed Trainers narrow
  the deck, and evolution reveals imply parts of the deck line. Is our
  disambiguation "fast" like Bridge (each trick reveals a lot) or
  "slow" like Poker (many turns pass with little revealed)?

**My take.**

The paper defines **disambiguation** as the rate at which a player's information set shrinks as the game progresses. In the synthetic trees, this is modeled by recursively splitting information sets with probability *df* whenever the player moves. In real games, it corresponds to how much hidden uncertainty is eliminated after observing new actions or revealed information.

High disambiguation strongly benefits PIMC because hidden uncertainty disappears quickly. Even if the initial determinization does not match the true hidden state, different determinizations become increasingly similar as more information is revealed. As a result, the incorrect assumptions made at the root affect only a relatively small portion of the search tree, allowing PIMC to produce decisions close to those of a full-information search.

I expect Pokémon TCG to exhibit a moderate-to-high disambiguation factor. Every turn reveals additional public information through the discard pile, revealed Trainer effects, deck searches, evolutions, attached Energy, and the complete action history. These observations continuously reduce the number of plausible hidden states. While this information is probably revealed more slowly than in Bridge, where every played card dramatically reduces uncertainty, it is also much faster than in Poker, where hidden information remains largely unchanged until the end of the hand. This suggests that Pokémon TCG may occupy an intermediate position, potentially making determinization-based search more effective than theoretical objections alone would suggest.

**Refined write-up.**

The disambiguation factor quantifies how quickly a player's information set contracts during the course of a game. In the synthetic game model, information sets are recursively partitioned with probability *df* whenever the player acts, representing the gradual elimination of hidden uncertainty. In real domains, the same concept is measured by comparing the reduction in the number of states consistent with a player's observations after successive actions.

Among the three proposed domain properties, disambiguation provides the clearest explanation for why PIMC succeeds in many practical games. When hidden information is revealed rapidly, independently sampled determinizations progressively converge because fewer hidden configurations remain consistent with the observed history. Consequently, the planning errors introduced by an incorrect initial determinization influence only the early portion of the search, while later decisions are made under increasingly similar world models. Conversely, games with little or no disambiguation preserve uncertainty throughout the search, allowing determinization errors to propagate and significantly reducing PIMC's effectiveness.

Pokémon TCG appears to exhibit an intermediate-to-high level of disambiguation. Public information accumulates throughout the game via discarded cards, revealed search effects, evolutions, attached Energy, and observable action sequences, progressively restricting the set of plausible hidden states. Although this process is unlikely to be as rapid as in trick-taking games such as Bridge, it is substantially faster than in Poker, where private information remains hidden for almost the entire game. This suggests that the domain possesses characteristics that may naturally favor determinization-based search methods, although this hypothesis should ultimately be validated through empirical measurement.

---

## §3 — The synthetic domain and the cheating oracle

### 3.1 — Why they built a synthetic tree game

**Prompt.** The paper's key methodological move is constructing a
synthetic tree game where leaf correlation, bias, and disambiguation
can be controlled *independently*. Real games entangle all three.

- What does the synthetic domain look like? (Structural sketch:
  branching, depth, hidden information, action semantics.)
- Why isn't it enough to just study Bridge or Skat empirically?
- What kind of claim does the synthetic-domain result support that
  real-game analysis cannot?

**My take.**

The synthetic domain was designed to isolate the effects of the three proposed game properties: leaf correlation, bias, and disambiguation. It consists of a simplified two-player, zero-sum, imperfect-information game with alternating moves, a chance node at the root generating multiple possible worlds, explicitly defined information sets, fixed tree depth, binary payoffs (+1/-1), and controlled branching. Unlike real games, every important parameter can be varied independently.

Studying only real games such as Bridge or Skat would not be sufficient because these domains naturally combine several properties at once. For example, Bridge exhibits both high leaf correlation and relatively fast disambiguation. If PIMC performs well, it is impossible to determine which property is actually responsible or whether the observed performance results from their interaction.

The synthetic domain enables a much stronger experimental claim. Rather than observing correlations between domain characteristics and PIMC performance, the authors can manipulate a single property while keeping every other aspect of the game fixed. This allows them to identify causal relationships between individual game properties and the effectiveness of determinization-based search, something that empirical observations on real games alone cannot provide.

**Refined write-up.**

To investigate why PIMC succeeds despite its theoretical limitations, the authors construct a synthetic imperfect-information game in which the structural properties of the search space can be controlled independently. The domain consists of a two-player, zero-sum game with alternating turns, a root chance node defining multiple hidden worlds, explicitly represented information sets, fixed-depth binary game trees, and configurable branching. The three proposed properties—leaf correlation, bias, and disambiguation—are incorporated directly into the tree generation process, allowing each to be varied independently while all remaining characteristics remain unchanged.

This methodology addresses a fundamental limitation of empirical studies on real games. Domains such as Bridge, Hearts, and Skat simultaneously exhibit high leaf correlation, moderate-to-high disambiguation, and specific bias values, making it impossible to determine which property is primarily responsible for PIMC's observed performance. Real-game evaluations therefore reveal correlations but cannot isolate individual causal factors.

By employing a controlled synthetic domain, the authors can experimentally evaluate the effect of each property in isolation. This strengthens the paper's central claim by demonstrating that variations in specific domain characteristics directly influence the effectiveness of determinization-based search. Consequently, the synthetic experiments provide causal evidence supporting the proposed explanation for PIMC's practical success, while the subsequent analysis of real games serves as external validation of those findings.

---

### 3.2 — The cheating oracle as reference 🔄

**Prompt.** Throughout the paper, the authors compare PIMC against a
**cheating** perfect-information search that has access to the true
hidden state. This is exactly the methodology captured in the
`oracle-baseline-cheating-uct` candidate idea in
[`open-ideas.md`](open-ideas.md).

- How does the paper implement the cheating oracle? Is it a
  perfect-info UCT or a full minimax search?
- What is the exact quantity they report as the "cost of imperfect
  information"? Match this against our formulation
  $\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{PIMC}}$
  (or $W_{\text{ISMCTS}}$ in our case).
- In their experiments, what ranges of $\Delta_{\text{ceiling}}$ do
  they observe? What does "small" vs "large" look like empirically?
  This calibrates the decision thresholds in our
  *oracle-baseline-cheating-uct* entry.

**My take.**

Although the paper does not explicitly implement a "cheating UCT" oracle, it follows the same methodological principle. In the synthetic experiments, PIMC is compared against a reference player computed with Counterfactual Regret Minimization (CFR), which approximates a Nash-equilibrium strategy under complete knowledge of the game model. In Kuhn Poker, the authors additionally evaluate PIMC against a best-response player to study exploitability.

The reported performance gap represents the practical cost of solving an imperfect-information game with determinization rather than with an ideal game-theoretic solution. This closely matches our proposed metric

$$
\Delta_{\text{ceiling}} = W_{\text{oracle}} - W_{\text{agent}},
$$

where the oracle is implemented as a cheating search with access to the true hidden state.

The experiments show that this gap strongly depends on the domain properties. In games such as Skat and Hearts, where leaf correlation is high and information is revealed relatively quickly, the performance gap is small and has little practical impact. In contrast, games with low leaf correlation and little or no disambiguation, such as Kuhn Poker, exhibit substantially larger gaps, indicating that imperfect information becomes a dominant source of decision error. For our Pokémon TCG project, this suggests that measuring the oracle gap provides a principled way to estimate how much performance is fundamentally limited by hidden information and how much can still be recovered through improved search and belief modeling.

**Refined write-up.**

The paper employs an idealized reference player to quantify the performance loss introduced by imperfect-information search. In the synthetic domains, this reference is obtained through Counterfactual Regret Minimization (CFR), which approximates a Nash-equilibrium strategy, while additional experiments in Kuhn Poker compare PIMC against an explicit best-response player to evaluate exploitability. Although this differs from a cheating perfect-information UCT search, both approaches serve the same methodological purpose: establishing an upper performance bound assuming complete knowledge of the hidden state.

The reported performance difference can therefore be interpreted as the empirical cost of imperfect information. This directly motivates the oracle-gap metric proposed for our project,

$$
\Delta_{\text{ceiling}} = W_{\text{oracle}} - W_{\text{ISMCTS}},
$$

where the oracle is implemented using the true hidden state instead of an inferred belief state.

The experimental results demonstrate that this gap is highly domain-dependent. Games with high leaf correlation and substantial disambiguation exhibit only small performance losses relative to the ideal reference, whereas domains with persistent hidden information and weak action correlation produce much larger gaps. Consequently, the oracle gap should not be interpreted as a universal property of imperfect-information search, but rather as a domain-specific indicator of how costly hidden information is for decision quality. This provides a natural calibration framework for evaluating future Pokémon TCG agents and determining whether additional modeling complexity is justified.

---

## §4 — Implications for real games

### 4.1 — Bridge, Skat, and why PIMC worked there

**Prompt.** The paper closes by mapping their three properties onto
the games where PIMC has been empirically successful.

- Where do Bridge and Skat sit on the leaf-correlation and
  disambiguation axes?
- Their explanation for PIMC's success: high correlation + fast
  disambiguation reduces the theoretical damage to a manageable
  level. Do they claim the theoretical objections disappear, or just
  that they're empirically small?
- Any games they cite where PIMC *doesn't* work well, and why?

**My take.**

The paper places Bridge, Skat, and Hearts in the region of the parameter space characterized by high leaf correlation and relatively high disambiguation. In these games, many actions remain similarly valuable across different hidden-world realizations, and hidden information is progressively revealed as the game unfolds. As a result, independently sampled determinizations tend to converge during search, making the practical impact of determinization errors relatively small.

Importantly, the authors do not argue that the theoretical problems of PIMC disappear. Strategy fusion and non-locality remain fundamental limitations of the algorithm. Their conclusion is instead that, in domains with favorable structural properties, these errors rarely change the final decision enough to significantly affect playing strength.

The contrast is Kuhn Poker, which exhibits low leaf correlation and essentially no disambiguation because hidden cards remain unknown until the end of the hand. In this setting, determinization errors persist throughout the search, making PIMC substantially more exploitable and less competitive than game-theoretic approaches. For Pokémon TCG, my current hypothesis is that the game lies somewhere between these two extremes: it gradually reveals public information like trick-taking games, yet still preserves important hidden information throughout much of the match.

**Refined write-up.**

The experimental analysis places Bridge, Skat, and Hearts in a region of the proposed parameter space where PIMC is expected to perform well. These games exhibit high leaf correlation, meaning that many actions retain similar values across different hidden-state realizations, together with substantial disambiguation, as each observed action progressively reduces uncertainty about the hidden state. According to the synthetic experiments, this combination naturally limits the practical impact of determinization errors.

A key conclusion of the paper is that these favorable properties do not invalidate the theoretical criticisms of PIMC. Strategy fusion and non-locality remain inherent consequences of independently solving determinizations. However, when domain characteristics cause different determinizations to converge or produce similar action rankings, the resulting planning errors become empirically small, allowing PIMC to achieve competitive performance despite its theoretical shortcomings.

The opposite behavior is observed in Kuhn Poker, where hidden information remains almost entirely unresolved throughout the game. Its low leaf correlation and negligible disambiguation amplify the effects of determinization errors, making PIMC significantly more vulnerable to exploitation. These findings suggest that the suitability of determinization-based search depends primarily on measurable structural properties of the domain rather than on the mere presence of imperfect information. This perspective is particularly relevant for Pokémon TCG, which appears to combine characteristics of both trick-taking games and poker, motivating an empirical characterization of its domain properties before selecting the most appropriate search algorithm.

---

### 4.2 — Predicting where PTCG will fall 🔄

**Prompt.** Take the three properties (correlation, bias,
disambiguation) and *predict* where PTCG will sit on each axis before
running the oracle baseline experiment.

- Leaf correlation: register a prior.
- Bias: register a prior.
- Disambiguation: register a prior.
- Combined prediction: a prior on
  $\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{ISMCTS}}$ —
  small (< 5 pp), medium (5-15 pp), or large (> 15 pp)?

Write this down before the experiment runs. Compare with the actual
result later; the value is in registering the prediction, not in
being right.

**My take.**

Before running the oracle baseline experiment, my expectation is that Pokémon TCG occupies an intermediate position between trick-taking games such as Bridge and hidden-information games such as Poker.

- **Leaf correlation:** Moderately high. Early-game setup actions are often robust across many plausible opponent hands, although correlation is expected to decrease in tactical late-game positions where hidden resources can change the optimal move.

- **Bias:** Approximately neutral (≈ 0.5) under the Phase 3 evaluation protocol, where both players use the same deck. Any strong bias is more likely to arise from deck matchups than from the game mechanics themselves.

- **Disambiguation:** Moderately high. Every turn reveals additional public information through discarded cards, revealed searches, attached Energy, evolutions, and the observable action history. Hidden uncertainty decreases steadily throughout the game, although probably not as quickly as in Bridge.

Based on these priors, I expect the oracle advantage

$$
\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{ISMCTS}}
$$

to be **medium (5–15 percentage points)**. My expectation is that perfect hidden-state knowledge provides a measurable advantage, but not one large enough to justify arbitrarily complex belief models unless later experiments demonstrate otherwise.

**Refined write-up.**

**Prior hypothesis before experimentation**

Based on the framework proposed by Long et al. (2010), I expect Pokémon TCG to exhibit structural properties that are more favorable to determinization-based search than poker-like domains, but less favorable than classic trick-taking games.

- **Leaf correlation:** Moderately high. Many strategic setup actions are expected to remain effective across multiple plausible hidden states, although action rankings should become more sensitive to hidden information during late-game tactical positions.

- **Bias:** Approximately neutral under the competition setting, since both players operate under symmetric rules using identical decks. Consequently, bias is unlikely to be a major factor when interpreting oracle-based evaluations.

- **Disambiguation:** Moderately high. Public information accumulates continuously through discarded cards, revealed search effects, attached Energy, evolutions, and observable game history, progressively reducing the uncertainty over hidden states.

Taken together, these priors suggest that imperfect information imposes a meaningful but not overwhelming limitation on search quality. Therefore, I predict a **medium oracle gap (5–15 percentage points)**,

$$
\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{ISMCTS}},
$$

indicating that belief modeling should improve performance, but that much of the remaining decision quality may already be captured by a well-designed ISMCTS. This prediction will be evaluated empirically through the oracle baseline experiment.

**Prediction vs reality (EXP-004/005, 2026-07-10).**

- **ISMCTS-over-PIMC gap: predicted small → measured +3.8 pp,
  McNemar n.s. (p = 0.176). Correct.** The §5.1 implication chain
  (moderately high correlation/disambiguation ⇒ little headroom for
  the info-set tree over plain determinization) held exactly.
- **Δ_ceiling: predicted medium (5–15 pp) → measured +4.8 pp,
  McNemar p = 0.070 (n.s.).** Narrowly missed — the true cost of
  hidden information in mirror play sits just *below* the medium
  band. Direction right, magnitude overestimated: the domain is even
  more PIMC-friendly than the priors assumed, i.e. leaf correlation /
  disambiguation are at the high end of the guessed range.
- Combined reading: in this domain (this deck, mirror), **search
  quality ≫ information quality**. Consistent determinization already
  captures nearly everything a perfect belief model could; the
  remaining ~5 pp is the entire prize for any belief work — in the
  mirror setting. The *ladder* deficit (unknown opponent list ⇒
  filler determinization) is a different variable that this
  experiment deliberately did not measure.

---

## §5 — Bridge to Cowling: what does ISMCTS add on top?

### 5.1 — The Long → Cowling relationship 🔄

**Prompt.** Cowling et al. (2012) cite Long et al. (2010) explicitly
and position ISMCTS as an improvement over PIMC. But Long's argument
is that PIMC *isn't as broken as theory suggests*. So what does
ISMCTS actually improve, and by how much?

- Restate Long's contribution in one line.
- Restate Cowling's contribution in one line.
- The relationship between the two contributions: does Cowling
  disprove Long, refine Long, or extend Long?
- If the answer is "refine", the practical implication is that ISMCTS
  helps *most* on games where Long's properties fail (low correlation
  and/or slow disambiguation). If PTCG turns out to be a high-
  correlation and/or fast-disambiguation game, ISMCTS's headroom over
  vanilla PIMC will be small, and *informed-determinization* has
  even less headroom on top of that. Chain the implication out.

**My take.**

**Long et al. (2010):** The practical effectiveness of PIMC is determined more by the structural properties of the domain than by the mere presence of imperfect information.

**Cowling et al. (2012):** ISMCTS improves determinization-based search by performing tree search directly over information sets, reducing structural errors such as strategy fusion and non-locality while retaining many of PIMC's practical advantages.

Rather than contradicting each other, the two papers are complementary. Long explains *why* naive determinization often works surprisingly well, while Cowling explains *how* to improve it when its theoretical weaknesses become practically important. In this sense, ISMCTS refines and extends the conclusions of Long rather than replacing them.

This relationship has an important implication for Pokémon TCG. If the game exhibits relatively high leaf correlation and moderately fast disambiguation, Long's analysis predicts that vanilla PIMC should already perform reasonably well. Consequently, the performance gain obtained by moving from PIMC to ISMCTS may be limited. If that improvement is already small, then additional complexity—such as informed determinizations or sophisticated belief models—is likely to produce diminishing returns. Conversely, if Pokémon exhibits lower correlation or slower disambiguation than expected, ISMCTS and improved belief modeling should provide substantially greater benefits. This makes the empirical characterization of the domain a prerequisite for deciding how much algorithmic complexity is justified.

**Refined write-up.**

Long et al. (2010) and Cowling et al. (2012) address different aspects of the same problem. Long demonstrates that the practical success of Perfect Information Monte Carlo (PIMC) cannot be explained solely by its theoretical shortcomings. Instead, its effectiveness depends on measurable structural properties of the game, particularly leaf correlation and disambiguation. In favorable domains, the practical consequences of strategy fusion and non-locality become relatively small.

Building on this observation, Cowling et al. introduce Information Set Monte Carlo Tree Search (ISMCTS), which performs search directly over information sets rather than independently sampled determinizations. This design substantially reduces the structural errors inherent to PIMC while preserving its computational advantages for large imperfect-information games.

Consequently, the relationship between the two papers is one of refinement rather than contradiction. Long identifies the domain characteristics under which naive determinization is already an effective approximation, whereas Cowling provides a more principled search algorithm for domains where those favorable conditions no longer hold.

For Pokémon TCG, this leads to a testable engineering hypothesis. If empirical measurements indicate moderately high leaf correlation and substantial disambiguation, the performance difference between PIMC and ISMCTS should remain relatively small, implying limited headroom for increasingly sophisticated belief models and informed determinizations. Conversely, if the domain exhibits persistent uncertainty and highly state-dependent action rankings, ISMCTS and advanced belief modeling should provide significantly larger improvements. Therefore, empirical domain characterization should precede architectural decisions regarding search complexity.

---

## Lessons Learned

- Theoretical correctness and practical performance are not equivalent. Although PIMC suffers from strategy fusion and non-locality, these theoretical flaws do not necessarily produce poor empirical performance.

- The suitability of a search algorithm depends on measurable domain properties rather than simply on whether the game contains hidden information.

- Three domain properties explain much of PIMC's practical behavior:
  - **Leaf Correlation** determines how sensitive action quality is to hidden information.
  - **Disambiguation** determines how quickly hidden uncertainty disappears during play.
  - **Bias** affects absolute performance but has a relatively small influence compared to the other two properties.

- Synthetic domains are valuable because they isolate causal effects that cannot be disentangled in real games. Controlled experiments provide stronger evidence than empirical observations alone.

- Long et al. explain *why* naive determinization often works surprisingly well. Cowling et al. explain *how* to improve determinization when those favorable domain properties no longer hold. The two papers are complementary rather than contradictory.

- For Pokémon TCG, architectural decisions should be guided by empirical domain characterization rather than assumptions. Measuring leaf correlation, disambiguation, and the oracle performance gap should precede adding increasingly sophisticated belief models.

- The proposed oracle baseline is not simply a stronger agent; it is an experimental tool for estimating the practical cost of imperfect information within a specific domain.

## Failed Attempts

- Initially, I viewed imperfect information itself as the primary obstacle for search quality. After this paper, I realized that hidden information alone is a poor predictor of algorithm performance.

- Before reading Long et al., I implicitly assumed that improving the belief model would always produce meaningful gains. I now believe that the benefit of more sophisticated belief modeling depends on the structural properties of the domain, particularly leaf correlation and disambiguation.

- I originally interpreted PIMC's success as evidence that the theoretical objections were weaker than previously believed. The paper instead argues that the objections remain valid; their practical impact simply varies across domains.

- During the first reading, I tended to treat games as having fixed global properties. A more accurate perspective is that properties such as leaf correlation and disambiguation may vary substantially across different phases of a game, an observation that may be particularly relevant for Pokémon TCG.
