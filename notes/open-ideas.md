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
   large variance reduction.

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

- **Not Phase 3** — Phase 3 tests H1 (ISMCTS random-rollout vs
  heuristic baseline). Adding informed sampling in Phase 3 would
  confound H1: any observed lift could come from ISMCTS itself *or*
  from the informed prior. Baseline must be vanilla ISMCTS.
- **Phase 5 exploratory** is the natural home. Compare uniform vs
  informed sampling on the same match set, report Wilson CI on the
  win-rate delta (analogous to Phase 5's other exploratory sweeps for
  $c$ and determinizations-per-decision).
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

**Status.**

- **idea** — 2026-07 (Bruno raised during Phase 2 study; captured
  during Cowling reading).

---

_(Next idea goes here — copy the schema block above.)_
