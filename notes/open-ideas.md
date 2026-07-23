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

### replay-deck-mining — Recover real opponent decklists from public episode replays

**Motivation.**
Every deck condition we have ever tested was authored by us, and every
time the authored condition diverged from deployment (H1's mirror,
EXP-009's filler, ADR-002's homemade pool). The public leaderboard meta
snapshot (`myso1987/ptcg-ai-battle-leaderboard-deck-meta-by-score-band`,
2026-07-16) ends the excuse: in our nearest band (500–599) the top ten
archetypes cover 88 % of classified teams, and we hold lists for **~39 %**
of it (Mega Lucario 24 %, Dragapult 10 %, our own mirror 5 %). The other
~60 % — Mega Starmie 13 %, Crustle Wall 12 %, Alakazam 11 %, Marnie
Grimmsnarl 5 % — are decks we have never simulated once. Alakazam alone is
first in *every* band above 700 and 47 % of the 900–999 band.

**Formal statement.**
A public episode replay carries the submitted decks verbatim: the deck
submission is the agent's **first action**, so `steps[1][seat]["action"]`
is the 60-card list (schema confirmed by reading the meta notebook's
`extract_decks`, with a `visualize`-based fallback for older replays).
For each target archetype $k$, mine $n_k$ lists from replays of teams the
published marker rules classify as $k$, and store them under
`decks/candidates/mined/<archetype>-<band>-<i>.csv`, validated by
`battle_start` exactly as the starter decks were. Two consumers:

1. **EXP-011's opponent pool** (deck re-evaluation) — replace "the four
   starter decks" (an assumption) with an empirical field weighted by
   band share, plus an honest statement of what the residual tail leaves
   uncovered.
2. **[[informed-determinization]]** — the marker rules *are* a
   classifier over ~10–20 archetypes. Observing the opponent's public
   cards in play induces a posterior over archetypes; determinizing from
   the inferred list replaces `FILLER_CARD = 1072` (Snorlax, adopted from
   an official sample whose own comment reads "There is no deep meaning").
   The hypothesis space is enumerable, which is what makes this tractable
   at all.

**Two things this does NOT license.**
Piloting is confounded with the deck in the meta table: a starter deck
sitting low may reflect its stock rule-based agent, not the list. Mining
a list lets us *strip* that confound by piloting every deck with our own
agent (EXP-007's design) — it does not let us read deck strength off the
leaderboard. Second, the meta notebook deliberately publishes aggregates
only and no decklists; that restraint should carry into our artifacts —
mined lists are simulation inputs under `vendor/`-style hygiene, and the
writeup cites archetype *shares*, never another team's list.

**Rules check required before running.** The technique reads Kaggle's
public replay interface and the well-received meta notebook does exactly
this, but "does the competition permit mining opponent decks" is a
question for the Competition Rules, not for our inference. Confirm before
the first collection run.

**Literature.**
- Cowling, Powley & Whitehouse 2012, §4: ISMCTS determinizes by sampling
  $h \sim P(h \mid I)$; the prior's quality is the whole game, and ours is
  currently a constant.
- [PTCG Replay Data Miner](https://www.kaggle.com/code/llccqq624/ptcg-replay-data-miner)
  — credited by the meta notebook as the source of the extraction approach.
- The meta snapshot itself, for band weights and the marker rules.

**Where in the roadmap.**
Gated on EXP-009: if filler determinization is *not* what costs us
(branch c), the determinization consumer evaporates and only the EXP-011
pool argument survives. Collection is API-bound, not CPU-bound, so it can
overlap any running experiment.

**Risk to scope.**
Kaggle API pacing dominates: the meta run needed 1,717 requests at ≥1 s
spacing with 60 s cooldowns per 100, ~30+ min for 595 teams. Mining a
handful of lists per archetype is far smaller. HTTP 429 is not retried by
that codebase's own policy — copy the pacer, don't fight it. Real risk is
scope creep into a data-engineering project a month before the deadline;
descope to *one* list per top-5 archetype if it grows.

**Status.**
idea (2026-07-16), gated on EXP-009's verdict and a Competition Rules
check.

### trajectory-corpus — Log full self-play trajectories as future training data

**Motivation.**
ADR-003 rejected a learned evaluator on four grounds, one of which — "no
labelled training data exists" — has been false since 2026-07-09: every
experiment since EXP-003 is instrumented self-play whose outcome we know,
and ~3,600 matches (~50–60 h of CPU) were reduced to 788 KB of win/loss
rows because nothing recorded the decisions. The scoreboard was the right
thing to keep for EXP-003–009 (every hypothesis was about win rate), but
we now have questions the scoreboard cannot answer, and every future
CPU-hour that runs unlogged is unrecoverable. The marginal cost of
recording is near zero when the games are being played anyway.

**Formal statement.**
`scripts/local_ladder.py --log-trajectories PATH.jsonl.gz` (implemented
2026-07-16) wraps each seat's agent so every real decision appends
$(o_t, a_t)$, and the match row appends the terminal reward $r_T$ — one
gzip member per match, so resume composes with `--append`. Each decision
becomes one supervised sample $(o_t, a_t, r_T)$: enough for a value head
$\hat V(o)$ trained on outcome regression (the ADR-003 stretch design)
and for behavioral cloning of the search's move choices. Recording is
opt-in and must stay OFF for timing-sensitive runs (it serializes a
deep-copied obs per decision, and EXP-008-style measurements would absorb
that cost into $c(\text{it})$).

**Honest volume math (author's own caveat, 2026-07-16).** At $M \approx
23$ decisions/agent/game, EXP-010-scale runs (~500 games) yield ~23k
decisions per seat — two to three orders of magnitude below AlphaZero-style
regimes. A corpus that *matters* needs either many more games (cheap
low-iteration self-play generates data fastest) or a deliberately modest
target: a small value head to replace random rollout evaluation does not
need millions of samples to beat "nothing". Map the corpus size honestly
before promising a Phase-7 result on it.

**Literature.**
- Silver et al. 2016 (AlphaGo), §Methods: value network trained on
  self-play outcome regression — the shape of the label we are storing.
- Anthony, Tian & Barber 2017 (ExIt): expert iteration — the search is
  the expert, the net clones it; exactly the $(o_t, a_t)$ half.
- The competition's own RL sample (Kaggle starter kit): transformer over
  sparse obs encodings reaches 76 % vs random after 5 self-play epochs —
  a calibration point, since our zero-training heuristic scores 75.5 %.

**Where in the roadmap.**
Collection starts with EXP-010 (its registration must name
`--log-trajectories` in the configuration, both so the corpus provenance
is recorded and so the timing caveat is visible). Training is **Phase 7
stretch only** (roadmap: "Optional (Phase 7 only): PyTorch"), after the
Strategy deadline — ADR-003's other three grounds (deadline, no GPU on
the worker, H4 confounding) still stand and are not up for relitigation
here.

**Risk to scope.**
Near zero at collection time (a flag on runs that happen anyway; results/
is gitignored, and ~500 games ≈ 0.5–1 GB uncompressed shrinks ~10× under
gzip). The real risk is the temptation to *train* before Phase 7 — the
mitigation is this entry's explicit gate.

**Status.**
scoped (2026-07-16): collection implemented, first use gated on EXP-010's
registration; training gated on Phase 7.

### threat-aware-evaluator — Model the opponent in the evaluator, not in the simulation

**Motivation.**
A public notebook analyzed 2026-07-17 (a Mega Lucario ex agent — the #1
archetype of our score band) sits above us on the public ladder while
doing **no opponent determinization at all**. Its architecture is a
hand-crafted move-scoring policy, a 1-ply UCB1 verification search that
rolls out only to the end of the agent's *own* turn, and a static
evaluator that models the opponent as an aggregate threat: assume each
opposing Pokémon attaches one more energy, compute the maximum damage it
could then deal, and penalize states where our active dies to it
(weighted by the prizes we would concede — it explicitly manages the
3-prize Mega ex trade, including counter-play keyed to *our* archetype's
visible board IDs). This is a third answer to the hidden-information
problem, and it triangulates EXP-009 from the other side:

| condition | opponent model | evidence |
|---|---|---|
| filler (ours, deployed) | impossible-and-inert, simulated deep | −27.4 pp (EXP-009) |
| self-deck (ours, EXP-010) | wrong-but-coherent, simulated deep | pending |
| threat-aware (theirs) | none simulated; worst-case aggregate in $V(s)$ | above us publicly |

The differential of that agent is **game knowledge, not computation**:
archetype detection by set membership over revealed card IDs, prize-trade
math, deck-out defense, matchup-specific constants. It spends ~1.5 s per
decision against our adaptive ~6.75 s and wins anyway.

**Attribution caveat (recorded with the observation).** The public score
attaches to the *team*, updates continuously on a non-stationary ladder
(our own frozen heuristic drifted 38 points in 11 days), and cannot be
pinned to this exact notebook version — the author may have stronger
private submissions. Directional evidence only; nothing here is a
measured comparison.

**Formal statement.**
Add an opponent-threat term to the Phase-4 evaluator (Issue #23) instead
of (or alongside) simulating the opponent's hidden hand. For a state $s$
with our active $a$ and opposing board $B$:

$$
T(s) \;=\; \max_{p \in B} \; D\!\bigl(p,\; e_p + 1\bigr),
$$

where $D(p, e)$ is the maximum damage Pokémon $p$ deals with $e$
energies (computable from public card data — no hidden information
required), and the evaluator takes a penalty $-\lambda \cdot
\text{prizes}(a) \cdot \mathbb{1}\{T(s) \ge \text{hp}(a)\}$ plus a
proportional term below lethal. Two consumers, in order of fit:

1. **A feature in the evaluator/MoveScorer** — which makes it one more
   column in H4's pre-registered per-feature ablation (Phase 5), so its
   value gets measured, not assumed.
2. **Truncated-rollout evaluation** — roll out $d$ plies then apply
   $V(s)$ instead of playing to terminal, sidestepping the opponent-turn
   simulation that EXP-009 showed is worthless under a bad hidden-state
   model. This is a deeper change to the search and is post-EXP-010
   material at the earliest.

The concept transfers; the constants must not — every weight we adopt
gets derived from our own card data and ablated, not transcribed from a
public notebook.

**Literature.**
- Browne et al. 2012, §6.1 (evaluation-enhanced MCTS): truncating
  rollouts into a static evaluator is standard where full playouts are
  noisy or expensive — Lorentz's Amazons results are the canonical win.
- Sheppard 2002 (*World-championship-caliber Scrabble*): shallow
  simulation plus a knowledge-heavy static evaluation beating deeper but
  less-informed search — the closest architectural ancestor of the
  observed agent.
- Sturtevant & Bowling 2006: opponent modeling folded into search
  values rather than explicit hidden-state sampling.

**Where in the roadmap.**
Issue #23 (Phase 4, evaluator design) is the natural intake for the
threat term as a *feature*; H4 (Phase 5) then ablates it with the same
Bonferroni-corrected paired machinery as every other feature — no
amendment to the pre-registered hypotheses needed. The truncated-rollout
consumer waits on EXP-010's verdict: if self-deck recovers most of the
gap, deep simulation stays; if not, evaluation-based truncation becomes
the live alternative. Also a candidate Phase-5 diagnostic arm
("1-ply + evaluator" control) to place deep search against a
shallow-knowledge baseline — same role the PIMC arm played for the tree.

**Risk to scope.**
The observed agent embodies hundreds of hand-tuned constants; chasing
that is a tuning rabbit hole with no experimental story and directly
conflicts with our differential (registered, measured comparisons).
Descope rule: the threat term enters as **one feature with one weight**,
measured by H4, or it does not enter at all.

**Status.**
idea (2026-07-17), distilled from a public-notebook analysis (chat
record); no code or constants copied, per the same restraint rule as
[[replay-deck-mining]].

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

Competitive-landscape note (2026-07): the top public notebook on the
competition determinizes crudely — `random.sample` over the full
60-card list ignoring already-seen cards, opponent deck filled with
dummy Snorlax. Even *option 1 below* (plain consistency) is already
differentiated from the public baseline; the engine accepts arbitrary
determinizations without validation, so consistency is entirely the
caller's edge to build (see
[`phase3-implementation-plan.md`](phase3-implementation-plan.md),
"Findings from the top public notebook").

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
- **resolved: dropped for the mirror context** — 2026-07-10. EXP-005
  measured $\Delta_{\text{ceiling}} = +4.8$ pp (McNemar p = 0.070,
  n.s.), below the pre-registered ≲ 5 pp drop threshold. Even a
  perfect belief model buys ≤ ~5 pp over consistent uniform
  determinization in mirror play — options 1-beyond-consistency and 2
  are not worth their cost here. **What survives:** the *ladder*
  problem is different — there the deficit is not belief refinement
  but the unknown opponent *list* (filler ≪ consistent). Inferring
  the opponent's deck/archetype to *recover consistency* on the
  ladder remains open and is now the sharper Phase-5 question (see
  EXP-005 in the registry).

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

- **Long, Sturtevant, Buro & Furtak (2010).** Methodological
  precedent for the *shape* of the experiment, with one nuance found
  on close reading: Long's reference player is a **CFR-approximated
  equilibrium** (plus a best-response player in Kuhn Poker), not a
  cheating UCT. Both constructions serve the same role — an upper
  bound assuming the hidden-information problem is solved — but the
  implementation differs. Long's real contribution to our experiment
  is the three properties (leaf correlation, bias, disambiguation)
  that *predict* how large the gap will be. Reading companion in
  [`phase2-long-2010-notes.md`](phase2-long-2010-notes.md); §3.2 and
  §4.2 register the calibration and our priors (prediction: medium
  gap, 5–15 pp).
- **Cowling et al. (2012).** The ISMCTS paper's experimental section
  uses Cheating UCT as an oracle upper bound
  ([`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md)
  §5.1), directly validating this idea's methodology.
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
  small addition to `env/wrapper.py`. Implementation hint: locally
  the engine's `visualize_data()` returns the full board state for
  the renderer, and `search_begin` accepts arbitrary hidden
  assignments without validation — so the oracle can be built by
  feeding the *true* hidden state (recovered from the visualizer
  data or from driving both seats ourselves) into the same
  `search_begin` path the ISMCTS agent uses. No separate engine mode
  needed.
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

### pimc-baseline-determinized-uct — PIMC as a fourth experimental arm

**Motivation.**

Our current diagnostic ladder has four agents: Random → Heuristic →
ISMCTS → Oracle (cheating UCT). It is missing the one arm that
directly tests Cowling's central claim in *our* domain: **PIMC
(Determinized UCT)** — sample $K$ determinizations, run an independent
perfect-information UCT on each, and pick the action by majority vote
or averaged root statistics.

With PIMC in the ladder, the total gap decomposes into three
interpretable pieces:

- $W_{\text{PIMC}} - W_{\text{heuristic}}$ — the value of *search*
  (any tree search over none).
- $W_{\text{ISMCTS}} - W_{\text{PIMC}}$ — the value of the *shared
  information-set tree* specifically. This is Cowling's contribution,
  measured in PTCG. Per Cowling's own Dou Di Zhu result, this delta
  can be $\approx 0$ when branching is high — so this is a genuine
  empirical question, not a formality.
- $W_{\text{cheat}} - W_{\text{ISMCTS}}$ — the remaining cost of
  hidden information ($\Delta_{\text{ceiling}}$, the quantity the
  oracle-baseline entry defines).

Per Long's framework, if PTCG has high leaf correlation and fast
disambiguation, the middle delta will be small — and knowing that
*before* Phase 5 prevents us from over-investing in info-set-specific
machinery. Registered prediction (Long notes §4.2): medium
disambiguation, moderately high correlation, so the middle delta is
expected to be positive but modest.

**Formal statement.**

PIMC agent: at each decision, sample $K$ determinizations
$h_1, \dots, h_K \sim P(h \mid I)$ (uniform). For each $h_k$, run an
independent perfect-information UCT with budget $B/K$ (so total budget
$B$ matches the ISMCTS arm). Select the action

$$
a^* \;=\; \operatorname*{arg\,max}_a \; \sum_{k=1}^{K} n_k(a),
$$

the action with the highest total root visit count across the $K$
trees (visit-count voting). All other components (UCB1 constant,
rollout policy, reward) identical to the ISMCTS arm.

**Literature.**

- **Cowling et al. (2012)** — Determinized UCT is precisely the
  baseline the paper compares ISMCTS against; see
  [`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md) §5.1
  and §5.3 (Dou Di Zhu: ISMCTS ≈ PIMC under extreme branching).
- **Long et al. (2010)** — predicts when this arm will be close to
  ISMCTS (high correlation / fast disambiguation) — see
  [`phase2-long-2010-notes.md`](phase2-long-2010-notes.md) §5.1.
- **Ginsberg (1999)** — GIB is the canonical PIMC success story.

**Where in the roadmap.**

- **Phase 3 addendum, same experiment as the oracle baseline.** Once
  ISMCTS exists, PIMC is nearly free: it reuses the UCT loop and the
  determinization sampler; the only new code is the "K independent
  trees + vote" wrapper (~half a day). Run all four arms (heuristic
  reference, PIMC, ISMCTS, cheating UCT) on the same 200 paired seeds
  in one experiment.
- Does **not** gate anything (unlike the oracle arm) — it's
  interpretive. But it shares the run, so bundling costs nothing.
- **Not a submission candidate** in Phase 3–4 (ISMCTS is the
  committed algorithm per ADR-001). If the middle delta turns out
  negative (PIMC beats ISMCTS in PTCG!), that's an important negative
  result for the writeup and would trigger an amendment discussion.

**Risk to scope.**

- **Cost:** ~0.5 day on top of the oracle-baseline work.
- **Descope path:** if Phase 3 runs late, drop this arm and run only
  ISMCTS vs oracle; the middle decomposition is lost but the gating
  decision (ceiling gap) survives.
- **Budget-splitting caveat:** $B/K$ per tree vs one tree with budget
  $B$ is itself a design choice that affects the comparison. Pin $K$
  in the registry entry (Cowling uses comparable constructions;
  choose $K \in \{10, 20, 40\}$ after measuring per-simulation cost).

**Status.**

- **idea** — 2026-07 (surfaced while consolidating the Phase 2
  reading synthesis; completes the experimental ladder suggested by
  the Long/Cowling pairing).

---

### deck-diversity-local-pool — Test agents across matchups, not just mirrors

**Motivation.**

Every local experiment so far (EXP-002a/003/004) is a mirror match:
both seats play `decks/selected/deck.csv`. That cleanly isolates the
*algorithm* but measures nothing about *matchup robustness* — while
the Kaggle ladder, where ratings actually accrue, is all cross-matchup
(observed while watching replays: every opponent runs a different
list). This is an external-validity gap already flagged in the Cowling
notes (§6.1): our conclusions are about mirror play on one placeholder
deck.

**Formal statement.**

Build a small local deck pool (3–5 archetype-distinct legal lists —
Phase 4's ADR-002 candidate decks are the natural source). Extend
`scripts/local_ladder.py` to accept per-seat deck paths
(`--deck-a` / `--deck-b`) and run the round-robin: agent × deck-pair.
Report win rate per matchup cell plus the pooled rate, all with Wilson
CIs. Note ISMCTS's determinizer already supports asymmetric lists
(`my_deck_list` ≠ `opponent_deck_list`).

**Literature.**

- Long et al. (2010) — domain properties (leaf correlation,
  disambiguation) may differ by matchup; a mirror measures one point
  of that space.
- Cowling et al. (2012) §6.1 notes (our reading) — external validity
  depends on deck/situation diversity.

**Where in the roadmap.**

- Natural companion to **Phase 4's deck selection (ADR-002)**: the
  candidate-deck evaluation already requires cross-matchup local
  play, so the runner extension pays for itself there.
- As an *experiment*, Phase 5 exploratory (per-matchup H1-style
  check: does ISMCTS's edge over the heuristic hold across
  matchups?).

**Risk to scope.**

- Runner extension ~0.5 day. The cost is match volume: a 4-deck pool
  is 10 pairings × N matches. Mitigate with N = 100/cell for
  directional reads, reserving N = 500 for the chosen deck.

**Status.**

- **idea** — 2026-07 (raised by Bruno after watching ladder replays:
  "o deck dos adversários é diferente — exploramos outros decks?").
- **in progress (Phase 4)** — 2026-07-10: `scripts/local_ladder.py`
  now takes `--deck-a` / `--deck-b` (builder contract passes both true
  lists, so consistency holds in asymmetric matchups);
  `scripts/analyze_card_pool.py` surveys the pool. Round-robin process
  documented in `notes/phase4-deck-selection.md`. The Phase-5
  exploratory question (per-matchup H1 check) remains open.

---

### official-starter-as-candidate — Test the official Mega Abomasnow starter list as *our* deck

**Motivation.**
ADR-002's erratum identified the official Mega Abomasnow ex starter as
"the most informative candidate available" — same archetype as
`current-v1`, but a support suite The Pokémon Company tuned a rule-based
agent around, differing in 11 of 60 cards. EXP-011 paid the erratum's
re-evaluation debt with the official lists on the *opponent* side only;
no experiment has ever piloted that list from our seat. One suggestive
but confounded data point exists: `ismcts-selfdeck` piloting
`current-v1` beats `heuristic` piloting the official list 36–14
(EXP-010/011 shared cell) — but that mixes the agent gap with the deck
gap.

**Formal statement.**
Add `official-abomasnow` as a fifth candidate row to the EXP-011 design:
`ismcts-selfdeck` (1000 iters) piloting the official list vs `heuristic`
on the four official starters, N = 50 paired seeds 1..50 — cell-identical
protocol, directly comparable to the existing grid. Same selection rule
as EXP-011 (pooled paired McNemar vs `current-v1` on shared seeds,
worse-cell Wilson guard, tie to the incumbent).

**Literature.**
None needed — this is a candidate-set completion of EXP-007/EXP-011, not
a new method. The construct-validity framing is already recorded in
ADR-002's erratum and the registry.

**Where in the roadmap.**
Phase 5 at the earliest, and only if the ladder shows `current-v1`
underperforming its local numbers. EXP-011's margins (the incumbent beat
every tested challenger; the two Fire decks are significantly worse)
make this exploration, not a gate — it must not displace #28/#29 or the
threat-aware-evaluator work.

**Risk to scope.**
~200 matches ≈ 7–20 h of CPU at observed paces. Zero code: the runner
already takes `--deck-a`. The real cost is attention this close to the
Simulation deadline; descope by simply not running it before Aug 16.

**Status.**

- **idea** — 2026-07-23 (named as the honest residual in ADR-002's
  Reaffirmation: EXP-011 closed on branch (a) without ever testing the
  erratum's "most informative missing candidate" from our seat).

---

_(Next idea goes here — copy the schema block above.)_
