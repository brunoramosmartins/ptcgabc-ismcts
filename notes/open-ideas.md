# Open Ideas

Substantive ideas surfaced during the project that are **not** part of
the pre-registered roadmap (H1–H4) but are candidate amendments,
exploratory experiments, or post-competition extensions. Distinct
from:

- [`deferred-projects.md`](deferred-projects.md) — mini-projects that
  live *outside* this project (tic-tac-toe, checkers) and share only
  the author.
- [`../docs/research.md`](../docs/research.md) — the pre-registered
  hypotheses locked at tag `v0.3-hypotheses` (end of Phase 2). Nothing
  here can enter H1–H4 after the lock without an amendment recorded in
  the research log.
- [`../experiments/registry.md`](../experiments/registry.md) — real
  experiments, each with a fixed configuration and expected result.
  Ideas here become registry entries only when they graduate to being
  run.

## Schema per idea

Each entry follows this template. Copy it verbatim when adding a new
idea; don't skip fields (a missing field usually means the idea isn't
sharp enough yet — sharpen it before adding).

```
### <name> — <one-line summary>

**Motivation.**
_(What did we notice? Why is this worth investigating?)_

**Formal statement.**
_(Restate the idea as a modification to the algorithm/design, in the
notation of this repo.)_

**Literature.**
_(1–3 references that show this is on solid ground and/or has been
attempted before. Cite specific paper + section when possible.)_

**Where in the roadmap.**
_(Which phase can test this? Why not earlier / later?)_

**Risk to scope.**
_(What does adding this cost? What can we descope if it eats time?)_

**Status.**
_(idea | scoped | in progress | completed | rejected — plus a date on
each status change.)_
```

---

## Ideas

### informed-determinization — Non-uniform $P(h \mid I)$ using public information

**Motivation.**

Vanilla ISMCTS (per Cowling et al. 2012 and our own
[ADR-001](../docs/adr/adr-001-why-ismcts.md)) samples hidden states
uniformly from the information set: $h \sim P(h \mid I)$, with $P$
uniform over $I$. But PTCG exposes a large amount of *public*
information that constrains what the hidden state can be:

- Deck contents are published (both players' 60-card lists are
  visible before the game).
- Cards seen in play or in the discard pile are not in the hidden
  hand, deck, or prizes.
- Basic Pokémon in play imply their evolution lines are somewhere in
  hidden state, weighted by the standard deck-building patterns
  (Charmander → likely Charizard, not Blastoise).
- Trainer effects have observable residues (an Iono cast on turn 3
  invalidates prior inference about hand composition; a Professor's
  Research reveals the discard state).

An informed prior would concentrate the sampling on hidden states
consistent with this public evidence and starve simulations from
implausible states. This is exactly the argument S&B Ch 8 §8.6 makes
about sample updates and skewed distributions (see
[`phase2-rl-foundations.md`](phase2-rl-foundations.md) §8.3): the more
skewed the true posterior, the more efficient sample-based planning
becomes.

Analog from classical AI: the *Clue / Detetive* solver. Given a set of
accusations and denials, a constraint satisfaction algorithm
(constraint propagation + arc consistency + backtracking) narrows the
candidate card assignments to a single consistent solution. PTCG has
a weaker but non-trivial version of the same CSP: some hidden-state
assignments are impossible (cards seen in discard cannot be in hand),
some are unlikely (a deck registered with Charizard line is more
likely to have Charizard in the hidden portion than a deck without).

**Formal statement.**

Replace uniform sampling with an informed distribution:

$$
h \;\sim\; P\!\bigl(h \mid I,\; \text{public evidence}\bigr).
$$

Two concrete construction paths:

1. **Deterministic constraint refinement.** Compute the *refined info
   set* $\tilde I \subseteq I$ by removing all $h$ inconsistent with
   deck lists, discard, board, and prize count. Then sample uniformly
   from $\tilde I$. Strict subset of $I$; strictly reduces variance
   without introducing bias.
2. **Probabilistic belief update.** Assign non-uniform weights over
   $\tilde I$ using a domain-specific model of deck-building
   likelihoods (e.g., "Charmander implies Charizard with high
   probability"). This introduces model-dependent bias but potentially
   large variance reduction. A specific instantiation is
   **archetype-based priors**: classify the opponent's deck into a
   small set of known meta archetypes (e.g., Charizard-ex, Gardevoir,
   Lost Box) using the first few turns' visible plays, then condition
   $P(h \mid I)$ on the inferred archetype. This is much sharper than
   a fully independent card-by-card belief and is the natural
   companion to *archetype-conditioned-rave* below.

The action-selection rule remains

$$
a^* \;=\; \arg\max_a \; \mathbb{E}_{h \sim P(h \mid I,\, \text{ev})}\!\left[ Q(I, a, h) \right],
$$

where the expectation is now over the informed distribution.

**Literature.**

- **Ginsberg, M. (1999).** *GIB: Steps Toward an Expert-Level
  Bridge-Playing Program.* Ginsberg's GIB samples hands consistent
  with the observed bidding — direct analog of what we're proposing
  for PTCG using observable play. Cited as the canonical worked
  example of informed determinization in imperfect-info games.
- **Cowling, Powley & Whitehouse (2012)** §2.2 explicitly notes that
  $P(h \mid I)$ can be any distribution over $I$; their experiments
  use uniform for simplicity but do not argue it's optimal.
- **Sturtevant & Bowling (2006), *Robust Game Play Against Unknown
  Opponents*.** Considers opponent modeling and its effect on
  determinization-based search.
- **Long, Sturtevant, Buro & Furtak (2010),** cited in ADR-001,
  characterizes when uniform determinization is *sufficient* — implies
  the interesting regime is precisely where public information
  constrains the info set substantially.

**Where in the roadmap.**

- **Prerequisite: `oracle-baseline-cheating-uct` (below).** Do not
  implement this idea until the ceiling gap
  $\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{ISMCTS}}$
  is measured. If $\Delta_{\text{ceiling}} \lesssim 5$ pp, the
  imperfect-information penalty is small and belief refinement has
  too little headroom to justify the implementation cost. Drop the
  idea and revisit only if the reference opponent or deck changes.
  If $\Delta_{\text{ceiling}} \gtrsim 15$ pp, proceed with confidence.
  Middle range: ship option 1 (deterministic constraint refinement)
  only.
- **Not Phase 3** — Phase 3 tests H1 (ISMCTS random-rollout vs
  heuristic baseline). Adding informed sampling in Phase 3 would
  confound H1: any observed lift could come from ISMCTS itself *or*
  from the informed prior. Baseline must be vanilla ISMCTS.
- **Phase 5 exploratory** is the natural home, gated on the oracle
  baseline. Compare uniform vs informed sampling on the same match
  set, report Wilson CI on the win-rate delta.
- **Post-competition portfolio extension:** if the Phase 5
  experiment shows lift, this becomes an **amendment ADR** (proposed
  name: ADR-001a — informed sampling variant) and a candidate TIL
  ("belief refinement in imperfect-info MCTS").

**Risk to scope.**

- **Cost:** implementing the constraint refinement (option 1) is
  probably ~1 day of code (subset construction over the deck ↔
  discard ↔ hand accounting). The probabilistic belief update
  (option 2) is a bigger project — requires a model of deck
  composition patterns, which is another 2–3 days of work plus a
  meta-experiment to validate the model.
- **Descope path:** Phase 5 exploratory experiments are already
  time-boxed. If informed sampling eats more than its slot, drop the
  probabilistic version (option 2) and ship only the deterministic
  refinement (option 1). The deterministic version alone is a
  publishable result.
- **Confounding risk:** the H1 pre-registered test must remain on
  uniform ISMCTS. Any code change must preserve a uniform baseline
  path for reproducibility.
- **Headroom risk:** the ceiling gap measured by
  *oracle-baseline-cheating-uct* caps the achievable lift. Even a
  perfect belief update cannot outperform the oracle. If the
  ceiling is close to vanilla ISMCTS, this idea is fundamentally
  capped regardless of implementation quality — hence the
  prerequisite above.

**Status.**

- **idea** — 2026-07 (Bruno raised during Phase 2 study; captured
  during Cowling reading).
- **gated** — 2026-07 (Bruno added the *oracle-baseline-cheating-uct*
  prerequisite after further Cowling reading; now blocked on
  measuring $\Delta_{\text{ceiling}}$).

---

### archetype-conditioned-rave — RAVE statistics conditioned on inferred opponent archetype

**Motivation.**

Standard RAVE (Rapid Action Value Estimation, per Browne §4.2) accelerates
early-search estimates by sharing action statistics across nodes: an action
$a$ that worked well in one rollout gets partial credit at every node
$a$ was considered. This trades bias for variance and is known to hurt
when the underlying "same action, different value" assumption breaks
(Cowling §4.2 notes this failure mode for imperfect-info games).

In PTCG, action semantics depend strongly on the **opponent's deck
archetype**. `Boss's Orders` targeting a benched Charizard is a
completely different action than the same card targeting a benched
Comfey — the value of the action collapses to "did we KO the
right target?" which depends on what the opponent is building toward.
Global RAVE statistics across a search that mixes rollouts against a
Charizard determinization and a Gardevoir determinization would average
out signal.

The proposal: keep RAVE, but **condition the statistics on the
opponent's inferred archetype** (see `informed-determinization` above,
archetype-based prior instantiation). Within an archetype bucket, RAVE's
"same action similar value" assumption holds much better; across
buckets, it doesn't. Buckets can start global and progressively
disaggregate as archetype confidence rises during the match.

**Formal statement.**

Maintain per-archetype RAVE tables $Q_{\text{RAVE}}(a \mid \text{arch})$
instead of a single global $Q_{\text{RAVE}}(a)$. The tree-policy scoring
function at node $n$ with visit count $n_a$ and RAVE visit count
$\tilde n_a$ becomes

$$
\text{score}(a) \;=\; \beta(\tilde n_a, n_a)\, Q_{\text{RAVE}}(a \mid \hat{\text{arch}}) \;+\; \bigl(1 - \beta(\tilde n_a, n_a)\bigr)\, Q(a) \;+\; c\sqrt{\frac{\ln t}{n_a}},
$$

where $\hat{\text{arch}}$ is the archetype MAP estimate at the current
information set and $\beta$ is the standard RAVE decay (fully global
early, fully MCTS-native late). When archetype confidence is low,
$Q_{\text{RAVE}}(a \mid \hat{\text{arch}})$ can be a mixture across
plausible archetypes weighted by the posterior.

**Literature.**

- **Gelly & Silver (2011).** *Monte-Carlo tree search and rapid action
  value estimation in computer Go.* Canonical RAVE reference cited by
  Browne §4.2. Discusses the RAVE assumption and its failure regimes.
- **Browne et al. (2012)** §4.2 (RAVE) and §4.2 (MAST) — the survey's
  own treatment.
- **Cowling et al. (2012)** §4.2 or wherever RAVE is discussed in the
  ISMCTS context — the survey acknowledges that RAVE-style techniques
  need adaptation for imperfect information, but doesn't develop the
  archetype-conditioning approach.

**Where in the roadmap.**

- **Prerequisite (transitive): `oracle-baseline-cheating-uct`.** Since
  archetype-conditioned RAVE inherits *informed-determinization*'s
  archetype-inference module, and *informed-determinization* is
  itself gated on the ceiling measurement, this idea is
  transitively gated. If $\Delta_{\text{ceiling}}$ is small, drop
  both.
- **Not Phase 3, not Phase 4.** Depends on both (a) working ISMCTS
  (Phase 3) and (b) an archetype-inference module (which itself
  depends on `informed-determinization`). Both prerequisites must
  be in place.
- **Phase 5 exploratory or post-competition.** Naturally paired with
  `informed-determinization` — the same archetype-inference module
  serves both.
- **Amendment ADR candidate:** if this lifts win rate on the ladder,
  it's material for ADR-001b (RAVE variant) alongside the
  ADR-001a informed-sampling variant.

**Risk to scope.**

- **Cost:** ~2–3 days on top of the informed-determinization work.
  RAVE has a well-known implementation pattern; the delta from
  standard RAVE to archetype-conditioned is one extra dictionary
  lookup per update.
- **Descope path:** ship plain (unconditioned) RAVE first as a Phase 5
  exploratory. If that beats vanilla ISMCTS, adding the archetype
  condition is the next iteration. If RAVE alone doesn't help, drop
  both.
- **Confounding risk:** RAVE and informed-determinization each move
  win rate independently. Any comparison must use factorial design
  (2×2: {uniform, informed} × {no RAVE, RAVE}) or the effects will
  entangle.

**Status.**

- **idea** — 2026-07 (captured after Browne §4.2 reading; hybrid with
  `informed-determinization`).

---

### progressive-widening-with-action-ranking — Rank actions before search, expand progressively

**Motivation.**

Browne §4 covers Progressive Widening (PW): control how quickly
the tree fans out by allowing $\lceil c \cdot n^\alpha \rceil$ children
at a node with $n$ visits, for tuned $c, \alpha$. In domains with
large branching factors — hundreds of legal moves at some PTCG
turns, once Trainers and abilities are counted — expanding all
children immediately wastes simulations on obviously-weak actions.

Standard PW picks the "next child to expand" in whatever order the
engine emits actions. The proposal: **rank actions before search
begins** using a cheap heuristic (attack damage, prize-value payoff,
`Boss's Orders`-style disruption priority) and let PW expand them in
rank order. The first few simulations then land on plausible actions
by construction, before UCB1 has had a chance to converge.

This is a specific and testable variant of the general "action
prior" idea used implicitly by AlphaZero-family agents, but
without needing a learned policy — the ranking is hand-crafted
(same tier as our Phase 4 evaluator per ADR-003).

**Formal statement.**

At each internal node $n$ with visit count $v(n)$:

1. Compute $r: A(s) \to \mathbb{R}$, a rank score per legal action,
   using a fixed ranking function (subclass of ADR-003's evaluator).
2. Sort actions by $r$ (descending).
3. Allow at most $k(v) = \lceil c \cdot v^\alpha \rceil$ children,
   choosing the top-$k$ in ranked order.
4. UCB1 selection operates only over the expanded children.

As $v \to \infty$, $k \to |A(s)|$ and the algorithm reduces to
standard ISMCTS. For finite $v$, computation concentrates on
top-ranked actions.

**Literature.**

- **Coulom (2007), *Efficient Selectivity...*** — original PW
  paper. Browne §4 cites this.
- **Browne et al. (2012)** §4 (Progressive Strategies).
- **Chaslot et al. (2008), *Progressive Strategies for Monte-Carlo
  Tree Search.*** Broader treatment of both PW and Progressive Bias.

**Where in the roadmap.**

- **Not Phase 3 baseline** — same reasoning as informed-determinization.
- **Phase 5 exploratory** — testable independently of informed-
  determinization, so cleaner factorial design. Report as a separate
  EXP with its own registry row.
- **Interacts with ADR-003 evaluator** — the ranking function reuses
  the Phase 4 evaluator features. If the evaluator is good, ranking
  is good.

**Risk to scope.**

- **Cost:** ~1 day if we reuse the Phase 4 evaluator as the ranking
  function. Independent of informed-determinization implementation.
- **Descope path:** if PW alone lifts win rate, ship as an amendment
  ADR (ADR-002-search-widening). If not, closed as "no lift".
- **Interaction risk with H4:** the ranking uses the evaluator, so
  ablating an evaluator feature could break the ranking. Any PW
  experiment must run after H4 ablation is complete, or the ranking
  must be pinned during H4.

**Status.**

- **idea** — 2026-07 (Browne §4 reflection).

---

### transposition-tables-for-info-sets — Hash-based sharing across equivalent information sets

**Motivation.**

Browne §4 (enhancements) covers transposition tables: many search
trees revisit the same underlying state via different action
sequences; storing statistics keyed by state hash instead of by tree
path lets those revisits share data.

In imperfect-info games this is harder because two nodes are
"equivalent" only if the information sets agree, and info-set
equality depends on the full observation history (deck lists,
discard, board, prize count, and any Trainer effects that shuffled
either hand). Cowling §4 briefly discusses the difficulty.

However, PTCG has a specific structure that makes a subset of
transpositions cheap: **many turns produce identical observable
outcomes via commuting sub-decisions**. If we play `Nest Ball` and
then `Ultra Ball`, or `Ultra Ball` then `Nest Ball`, the resulting
board and hand states are often identical. The tree normally treats
these as distinct paths.

The proposal: hash the *canonical observable state* (a normalized
representation of $S^{\text{pub}} \cup H_i$ that ignores intra-turn
action order) and share statistics across nodes with the same hash.
Not all pairs of nodes are hash-equal — some Trainer effects do
depend on order — but enough are that the savings are real.

**Formal statement.**

Define a canonicalizer $\text{canon}: S \to \mathbb{Z}$ that maps
each state to a hash respecting:

- Same info-set (observable) content → same hash.
- Different observable content → different hash (up to collision).

Maintain a global table $T: \mathbb{Z} \to (\text{visits}, Q)$. When
selection or backpropagation touches node $n$ with state $s$, update
$T[\text{canon}(s)]$ instead of a node-local statistic. Selection
reads $T$ for UCB1 scoring.

**Literature.**

- **Browne et al. (2012)** §4 discusses transposition tables for
  perfect-info MCTS.
- **Cowling et al. (2012)** — briefly notes the imperfect-info
  extension is harder; unclear whether they attempt it in the
  empirical section.
- **Childs, Brodeur & Kocsis (2008), *Transpositions and Move Groups
  in MCTS*.** Broader analysis of when transpositions help vs hurt.

**Where in the roadmap.**

- **Phase 5 exploratory** — pure implementation optimization, not a
  research question. Report as an EXP with a "simulations per second"
  metric alongside win-rate.
- **Post-competition:** if the speedup lets us push simulations-per-
  decision materially higher within the 10-min budget, this becomes
  a candidate ADR (ADR-004-transpositions).

**Risk to scope.**

- **Cost:** medium (~2–3 days). The canonicalizer is where the
  difficulty lives. If designed poorly, incorrect hashes cause
  incorrect sharing and silently break the search. Requires unit
  tests on hand-crafted state pairs.
- **Descope path:** ship a very conservative canonicalizer (identity
  hash — only exact copies transpose) as a working baseline, then
  progressively relax equivalence classes.
- **Correctness risk:** unlike the other ideas, this one can silently
  corrupt statistics. Requires extra test coverage and possibly a
  "transpositions off" mode for debugging.

**Status.**

- **idea** — 2026-07 (Browne §4 enhancements reflection).

---

### oracle-baseline-cheating-uct — Upper-bound diagnostic: give UCT the true state

**Motivation.**

Before investing implementation effort in *informed-determinization*,
*archetype-conditioned-rave*, or any other opponent-modeling technique,
we need to know whether opponent-side information gain is even a
promising axis. The clean way to test this is a *cheating* baseline:
an agent that receives the full game state $s$ instead of the
information set $I(s)$ and runs standard perfect-information UCT (no
determinization, no belief modeling). Its win rate against a fixed
reference opponent gives an *upper bound* on what any
imperfect-information algorithm can achieve, because no algorithm
without oracle access can outperform one with it, all else equal.

The gap $\Delta_{\text{ceiling}} = W_{\text{cheat}} - W_{\text{ISMCTS}}$
is exactly the headroom that informed determinization, archetype
priors, and RAVE variants have to work with:

- **Small gap (say $\lesssim$ 5 pp).** The imperfect-information penalty
  is small; even a perfect belief update can only recover a few
  points. Not worth 3–5 days per idea.
- **Large gap (say $\gtrsim$ 15 pp).** There is real value to unlock;
  proceed with informed-determinization in earnest.
- **Medium gap.** Ship the cheap option first (informed-determinization
  option 1 — deterministic constraint refinement, ~1 day) and gate
  the more expensive options on its result.

This is not a candidate for submission — cheating UCT violates the
Kaggle rules by accessing opponent's private state. It's a
*measurement instrument* that tells us where to spend engineering
budget.

**Formal statement.**

Define two variants:

- **Vanilla ISMCTS** (baseline, per ADR-001): observes $I(s)$, samples
  $h \sim P(h \mid I)$ uniformly, runs the four-phase MCTS loop with
  UCB1 at info-set nodes.
- **Cheating UCT** (this idea): observes the true $s$ directly, runs
  the four-phase MCTS loop on the true state — no determinization
  layer, no info-set nodes, no sampling. Otherwise identical
  (same UCB1 constant $c$, same rollout policy, same
  simulations/decision budget).

Both play against a fixed reference opponent (initially the heuristic
baseline from EXP-002a) on a benchmark match set of $N = 200$ paired
seeds per the benchmark protocol. Report:

$$
W_{\text{cheat}},\quad W_{\text{ISMCTS}},\quad \Delta_{\text{ceiling}}
\;=\; W_{\text{cheat}} - W_{\text{ISMCTS}},
$$

each with Wilson 95% CI, plus a paired-bootstrap CI on
$\Delta_{\text{ceiling}}$ using the shared seeds.

**Literature.**

- **Long, Sturtevant, Buro & Furtak (2010).** Uses cheating PIMC
  (Perfect-Information Monte Carlo with oracle access) as the
  reference against which their non-cheating PIMC is measured. Same
  methodological role.
- **Cowling et al. (2012).** Their empirical section likely
  uses this construction as a reference; confirm the exact framing
  during a second-pass read of the paper.
- **Frank & Basin (1998).** Original strategy-fusion analysis
  measures imperfect-info methods against the perfect-information
  minimax solution — an oracle reference of the same shape.

**Where in the roadmap.**

- **Phase 3 addendum.** Requires working ISMCTS (Phase 3 Issue #19)
  and the local ladder (Phase 1). No further dependencies. Fits
  naturally as a new issue between H1 (Issue #21) and the ISMCTS
  ladder submission (Issue #22), or immediately after Issue #22.
- **Gates all downstream inference work.** The result determines
  whether *informed-determinization*, *archetype-conditioned-rave*,
  and any future belief-based idea are pursued in Phase 5.
- **Cannot be a submission.** Cheating UCT violates competition rules;
  it never leaves the local ladder.

**Risk to scope.**

- **Cost:** ~1 day. The implementation reuses the ISMCTS four-phase
  loop; the only change is "skip determinization, use the true state".
  Requires an env-level toggle to expose $s$ instead of $I(s)$ —
  small addition to `env/wrapper.py`.
- **Descope path:** none needed. This is the least risky idea in the
  file precisely because it's diagnostic, not architectural.
- **Interpretation risk:** the ceiling depends on the reference
  opponent. Measuring against the heuristic baseline gives the ceiling
  for beating the heuristic; measuring against another ISMCTS instance
  gives a different (usually smaller) number. Pin the reference in
  the registry entry and be consistent when interpreting downstream
  experiments.
- **Compliance risk:** cheating UCT must never be bundled and
  uploaded to Kaggle. Enforce with a code-level assertion in
  `scripts/submit.py` that rejects any main.py using the oracle
  path (add a magic string check).

**Status.**

- **idea** — 2026-07 (raised after Cowling reading; direct
  consequence of "measure headroom before optimizing" methodology
  from Long et al. 2010).

---

_(Next idea goes here — copy the schema block above.)_
