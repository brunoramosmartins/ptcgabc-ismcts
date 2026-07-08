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

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

---

### 4.2 — Predicting where PTCG will fall 🔄

**Prompt.** Take the three properties (correlation, bias,
disambiguation) and *predict* where PTCG will sit on each axis before
running the oracle baseline experiment.

- Leaf correlation: my prior — _(fill in)_
- Bias: my prior — _(fill in)_
- Disambiguation: my prior — _(fill in)_
- Combined prediction: my priors on
  $\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{ISMCTS}}$ —
  small (< 5 pp), medium (5-15 pp), or large (> 15 pp)?

Write this down before the experiment runs. Compare with the actual
result later; the value is in registering the prediction, not in
being right.

**My take.**

_(fill in)_

**Refined write-up.**

_(pending)_

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

_(fill in)_

**Refined write-up.**

_(pending)_

---

## Lessons Learned

_(filled at merge time.)_

## Failed Attempts

_(filled if any come up during the read-through.)_
