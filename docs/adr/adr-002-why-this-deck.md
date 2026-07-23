# ADR-002 — Why This Deck

**Status:** accepted (2026-07-15), with a material erratum of 2026-07-16
(see Erratum below; formal revision was gated on EXP-011 — the deck
re-evaluation originally slated as EXP-010, renumbered 2026-07-17 when
EXP-010 was claimed by the determinization comparison EXP-009 branch (a)
pre-committed). **Reaffirmed 2026-07-23 on real-field evidence: EXP-011
closed on branch (a) — see Reaffirmation below; the provisional status is
lifted.** Supersedes the Phase-0 placeholder note in
`decks/selected/rationale.md`.
**Decision:** keep the Phase-0 sample list, now promoted to a deliberate
choice under the name **`current-v1`**, as `decks/selected/deck.csv`.
**Evidence:** EXP-007 (`experiments/registry.md`); process in
`notes/phase4-deck-selection.md`.

## Erratum (2026-07-16)

Kaggle's own competition-launch post and the four starter-kit agent
notebooks falsified two things this ADR asserted. Recorded here rather
than edited into the text above, because an ADR that silently repairs its
own reasoning stops being a record of how the decision was actually made.

**1. The deck is misidentified throughout this document.** This ADR calls
`current-v1` "the Kaggle sample list" and concludes that "the sample deck
is better engineered than it looks". It is *not* the official **Mega
Abomasnow ex starter deck**. `decks/selected/deck.csv` came from
`data/kaggle/sample_submission/deck.csv` — the sample *submission* list.
The two share only the Pokémon core and one Supporter; **11 of 60 cards
differ**:

| | `current-v1` (ours) | Official Mega Abomasnow ex starter |
|---|---|---|
| Shared | Kyogre ×2, Snover ×4, Mega Abomasnow ex ×4, Lillie's Determination ×4 | same |
| Energy | Basic {W} ×**35** | Basic {W} ×**34** |
| Support | Mega Signal ×4, Maximum Belt ×1, Cyrano ×2, Waitress ×4 | Ultra Ball ×4, Precious Trolley ×1, Carmine ×4, Surfing Beach ×3 |

So the praise for the list's engineering was aimed at the wrong artifact.
The **actual** starter deck — same archetype, a support suite The Pokémon
Company tuned a rule-based agent around — **has never played a single game
against ours**. It is the most informative candidate available and it was
missing from the pool. (Incidental confirmation: EXP-007's "up to N" crash
came from **Cyrano**, card 1205 — a card in *our* list and not in the
official one.)

**2. The premise behind the maximin rule is falsified.** The Context below
argues: *"Unknown opponent pool. The ladder runs diverse decks we cannot
enumerate in advance."* The competition **publishes four sample decks**
(Iono, Dragapult ex, Mega Abomasnow ex, Mega Lucario ex), each with a
ready-made agent notebook, and the starter kit is where most entrants
begin. The field is not enumerable with certainty, but it is far from
unknowable — which weakens the case for maximin over optimizing against a
known field.

**3. Consequently the evidence base is a proxy, not the meta.** Three of
EXP-007's four candidates (`v1-tuned`, `aggro-fire`, `emboar-evolution`)
were built by us. The pool shares exactly one deck with the likely real
field, and that one is ours. The matchup matrix has a hole precisely where
the meta belongs.

**What survives.** The *decision* may well be correct: the replacement gate
never fired, `current-v1` dominated all three challengers head-to-head, and
the cost-axis argument (0.7 % timeout vs 11–24 % for the Fire decks) is
independent of the pool's composition. The `v1-tuned` lesson — that cutting
energy 35 → 27 breaks Hammer-lanche's deck-density scaling — also survives,
and the official list running 34 energy corroborates it. What does *not*
survive is the claim that this deck was validated against the field.

**Gate.** EXP-011 runs `current-v1` against the four official decks,
including the real Mega Abomasnow ex list. This ADR is revised or
superseded on that evidence, not before. It runs *after* EXP-010 settles
the determinization condition, because a deck ranking is only as valid as
the agent that measures it — EXP-009 showed the determinization moves the
agent by ~30 pp, roughly double the largest deck effect EXP-007 saw.

**Pattern worth naming.** This is the third construct-validity gap found in
one week: H1 was measured under a mirror-deck condition the ladder never
offers; EXP-009 is pricing a filler determinization the ladder forces on
us; and now the deck was selected against a pool we invented. Every time we
*authored* the test condition instead of importing it from the deployment
environment, the two diverged. That belongs in Threats to Validity as a
methodological finding, not as three separate footnotes.

## Reaffirmation (2026-07-23)

EXP-011 ran the gate the Erratum demanded: the exact shipping condition
(`ismcts-selfdeck`, 1000 iterations — the instrument EXP-010 fixed first,
because a deck ranking is only as valid as the agent that measures it)
piloting all four EXP-007 candidates against `heuristic` on the four
official starter decks, including the real Mega Abomasnow ex list this
document once confused with ours. N = 50 paired seeds per cell; full
numbers and validity flags in `experiments/registry.md` (EXP-011).

| candidate | pooled wr (Wilson 95 %) | paired Δ vs `current-v1` | McNemar p (Bonf m = 3) | worse-separated cells |
|---|---|---|---|---|
| **`current-v1`** | **0.795** [0.734, 0.845] | — | — | — |
| `v1-tuned` | 0.765 [0.702, 0.818] | −3.0 pp | 0.55 (1.0) | 0 |
| `aggro-fire` | 0.670 [0.602, 0.731] | −12.5 pp | 0.0035 (0.011) | 1 |
| `emboar-evolution` | 0.385 [0.320, 0.454] | −41.0 pp | 1.1e-18 (3.3e-18) | 3 |

The pre-registered replacement gate never fires: the only challenger not
significantly worse (`v1-tuned`) is statistically indistinguishable, and
ties go to the incumbent by rule. Three findings close the Erratum's
three points:

1. **The proxy pool gave the right answer anyway.** EXP-007's ranking
   (`current-v1` > `v1-tuned` > `aggro-fire` > `emboar-evolution`) is
   reproduced in exactly the same order by the real field. The
   construct-validity hole was real — but immaterial to this particular
   decision, which is itself a finding about when homemade pools suffice.
2. **Maximin is vindicated against the actual field.** `aggro-fire`
   sweeps dragapult-ex 50–0 and collapses 9–41 against the official
   Abomasnow starter — the high-average, fragile-floor profile the
   selection rule was built to reject, now demonstrated on real
   opponents rather than argued from a homemade matrix.
3. **One residual, named honestly.** The Erratum's "most informative
   missing candidate" — the official Abomasnow starter *as our deck* —
   was outside EXP-011's registered candidate set (it appears on the
   opponent side only) and remains untested. Parked in
   `notes/open-ideas.md` (official-starter-as-candidate); not a blocker
   for #29 given `current-v1`'s margin over every tested alternative.

**Decision unchanged: `current-v1` ships in #29.**

## Context

Phase 0 shipped a placeholder deck (the Kaggle sample list) purely to
validate the submission pipeline, with an explicit note that Phase 4
would replace it before the Simulation deadline (Aug 16-17). Phase 4's
deck thread had to answer: **is any deliberately designed list better
than the placeholder under our own agent, and if so which?**

Two constraints shaped the method:

1. **Limited Card Battle format.** The pool is curated (~1267
   engine-legal cards); public Standard meta lists assume cards this
   pool may not have, and card strength is pool-relative. Internet meta
   is at most archetype inspiration — every concrete card choice came
   from `scripts/analyze_card_pool.py` and ladder replays (see the
   process note).
2. **Unknown opponent pool.** The ladder runs diverse decks we cannot
   enumerate in advance. So the selection criterion is **maximin** —
   best worst-case matchup — not best average edge. A deck that is
   great on average but folds to one archetype is a liability against
   an unknown field.

## Decision

**Keep `current-v1`** (the Phase-0 sample list) as the selected deck.
It is the maximin winner of the four-candidate round-robin **and** the
cheapest to pilot under a fixed time budget.

Candidate space (designed to span archetypes, not to all be good):

| candidate | archetype | core | basics | energy |
|---|---|---|---|---|
| **`current-v1`** | control | Snover → Mega Abomasnow ex + Kyogre | 6 | 35 {W} |
| `v1-tuned` | same core, "fixed" ratios | + Ursaluna, rebuilt trainers | 8 | 27 {W} |
| `aggro-fire` | big basics, no evolution | Gouging Fire ex + Ursaluna + Latias pivot | 11 | 25 {R} |
| `emboar-evolution` | Stage-2 ceiling | Tepig(70HP) → Mega Emboar ex | 7 | 23 {R} |

### Evidence (EXP-007)

Round-robin, both seat orderings pooled to **100 games per unordered
matchup**, `ismcts` at 1000 iterations both seats (agent held fixed —
this measures decks, not agents), 600 matches total, **0 fallbacks,
0 draws** (validity flag clean).

Matchup matrix — row deck's win rate vs column deck (all rows;
timeout = forfeit loss, see Consequences):

| deck ↓ vs → | current-v1 | v1-tuned | aggro-fire | emboar-evo | **worst-case** |
|---|---|---|---|---|---|
| **current-v1** | — | 0.66 | 0.91 | 0.87 | **0.66** |
| v1-tuned | 0.34 | — | 0.87 | 0.83 | 0.34 |
| aggro-fire | 0.09 | 0.13 | — | 0.28 | 0.09 |
| emboar-evolution | 0.13 | 0.17 | 0.72 | — | 0.13 |

**Maximin:** `current-v1` at **0.66** dwarfs the next-best worst-case
(v1-tuned, 0.34) and it dominates all three rivals head-to-head. The
ranking is **robust to how timeouts are scored** — excluding the
timeout rows entirely gives 0.66 / 0.34 / 0.08 / 0.11, same order.

Cited cells (current-v1 row), raw Wilson 95% / Bonferroni-corrected
(m = 3 comparisons, z = 2.394) — the pre-registered multiple-comparison
report:

| matchup | wins/n | raw Wilson 95% | Bonferroni (m=3) |
|---|---|---|---|
| current-v1 vs v1-tuned | 66/100 | [0.563, 0.745] | [0.541, 0.762] |
| current-v1 vs aggro-fire | 91/100 | [0.838, 0.952] | [0.818, 0.958] |
| current-v1 vs emboar-evolution | 87/100 | [0.790, 0.922] | [0.769, 0.931] |

Every lower bound clears 0.5 even after Bonferroni correction.

**Replacement gate (pre-registered):** a candidate replaces `current-v1`
only if its pooled rate *vs* `current-v1` has Wilson lower bound > 0.5.
The best challenger, v1-tuned, scores just 34/100 against it — the gate
never fires. `current-v1` stays.

### Second axis: computational cost

Kaggle scores at a fixed **time** budget, not fixed iterations. The
two Fire decks grind long games that blow the ISMCTS time budget at
1000 iters and forfeit:

| deck | timeout % | median s/match | p90 s/match |
|---|---|---|---|
| **current-v1** | **0.7 %** | **196** | 617 |
| v1-tuned | 11.0 % | 317 | 1069 |
| aggro-fire | 24.3 % | 530 | 1144 |
| emboar-evolution | 20.7 % | 539 | 1132 |

`current-v1` is not only the most robust list, it is by far the cheapest
to pilot — the Fire decks would forfeit ~1 game in 4–5 on cost alone.
This is an independent argument pointing at the same choice.

## Consequences

- **No deck change.** `decks/selected/deck.csv` already *is* `current-v1`
  (byte-identical); `decks/candidates/current-v1.csv` was a copy of it as
  the round-robin control. `decks/selected/rationale.md` is updated to
  cite this ADR instead of "placeholder, Phase 4 replaces it."
- **Because the deck is unchanged, EXP-002/003/004/005/006 remain valid.**
  Had a candidate won, every agent experiment run on the old list would
  need re-baselining on the new deck before further comparison; keeping
  `current-v1` avoids that entirely. This is a real (if unglamorous)
  benefit of the control winning.
- **Timeout rows are a finding, not noise.** They are engine per-match
  TIMEOUTs (one side DONE +1, the other TIMEOUT → forfeit — competitively
  valid outcomes), concentrated in the slow Fire matchups, not agent
  crashes (the "up to N" crash was fixed pre-run; see the process note's
  Failed Attempts). They feed the H3 / time-budget calibration work
  (#27): at a fixed *time* budget the iteration count must be tuned so a
  slow board state never forfeits.

## Alternatives Considered

- **Switch to `emboar-evolution` (Stage-2 ceiling).** Highest raw damage
  in the pool (Mega Emboar ex 320/380 HP), but worst-case 0.13 and a
  20.7 % timeout rate. The setup tax and game length sink it — exactly
  the "high ceiling, fragile floor" the maximin rule is designed to
  reject.
- **Switch to `aggro-fire` (zero-setup big basics).** The design
  hypothesis was that skipping evolution buys consistency; instead it
  posted the *worst* worst-case (0.09) and the highest timeout rate
  (24.3 %). Fast to set up did not mean fast to close.
- **"Fix" the sample list → `v1-tuned`.** Cutting energy 35 → 27 to add
  trainers looked like obvious improvement but backfired: Hammer-lanche
  (Mega Abomasnow ex) scales with deck {W} *density*, so the cut weakened
  the core. It loses to `current-v1` 34/100. The sample deck is better
  engineered than it looks; see the process note's Failed Attempts.
- **A dragon archetype (Mega Dragonite ex 330, dual {W}{L}).** Dropped at
  design time — dual-type energy plus a Stage-2 line stacks two
  consistency taxes, and its design-space cell (setup ceiling) is already
  covered by `emboar-evolution`.
