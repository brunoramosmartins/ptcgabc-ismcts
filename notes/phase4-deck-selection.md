# Phase 4 — Deck Selection Process (feeds ADR-002)

Goal: replace the Phase-0 placeholder deck with a deliberately chosen
list before the Simulation deadline (Aug 16-17), using local evidence
rather than internet meta. Output: `decks/selected/deck.csv` plus
`docs/adr/adr-002-why-this-deck.md` recording the decision.

## Why not the internet meta

The competition runs a **Limited Card Battle** format on a curated
pool (~2100 CSV rows; the engine's `AllCard` table is ground truth for
legality). Public PTCG meta decks assume the full Standard card pool —
staple trainers and attackers may simply not exist here, and pool-
relative card strength shifts when the pool shrinks. Internet lists
are useful only as *archetype inspiration* (what roles a deck needs);
every concrete card choice must come from:

1. **The pool itself** — `python scripts/analyze_card_pool.py`
   (families by end-stage damage, standalone basics, rule-box cards,
   trainer roles).
2. **Ladder replays** — what opposing decks actually run and what
   loses to what (watch 5-10 replays of high-rated agents).

## Deck-validity constraints (engine-enforced)

- Exactly 60 cards.
- ≤ 4 copies per card *name* (basic Energy exempt).
- ≥ 1 Basic Pokémon (a mulligan-proof count in practice: 8+).
- ≤ 1 Ace Spec card.

## Process

### Step 1 — Pool analysis

Run the analyzer, paste the tables into this note (see Appendix), and
shortlist: 2-3 attacker cores (evolution families or big basics),
consistency trainers (draw + deck search), and tech (switch/heal/
disruption) that the pool actually offers.

### Step 2 — Candidate design (3-5 decks)

Each candidate lives in `decks/candidates/<name>.csv` (60 lines, one
card id per line — same format as `decks/selected/deck.csv`) with a
`<name>.md` beside it: archetype, core cards, energy count rationale,
expected strength/weakness. Candidate archetypes to cover the design
space, not to all be good:

- **aggro-basic** — standalone big basics, minimal evolution, low
  energy curve; fastest to set up, ceiling limited.
- **evolution-midrange** — best S1/S2 family from the analyzer +
  consistency trainers; higher ceiling, setup risk.
- **current-v1** — the Phase-0 placeholder as control. Every candidate
  must beat it convincingly or the change isn't justified.
- (optional) **rule-box** — multi-prize attacker risk/reward, only if
  the pool table shows a standout.
- (optional) **disruption** — only if the trainer shortlist supports it.

### Step 3 — Round-robin evaluation

Registered as **EXP-007** in `experiments/registry.md`. One command
runs the full round-robin (12 ordered pairs, resumable — completed
pairs are skipped):

```
bash scripts/run_exp007.sh ismcts-guided    # or: ismcts, per EXP-006
```

Protocol notes:

- **Same agent both seats** — we are measuring decks, not agents.
  Both agents receive both true lists (`AgentBuilder` contract), so
  determinization consistency holds in asymmetric matchups. The
  variant (`ismcts-guided` vs `ismcts`) follows the EXP-006 verdict
  and is recorded in the registry before the run.
- **Both orderings** (A-vs-B and B-vs-A) to cancel any seat/first-move
  advantage; paired seeds 1..50 within each ordering, pooled to 100
  matches per matchup; report each matchup as win rate with Wilson
  95% CI. Total 600 matches ≈ 5 h at 1000 iterations.
- Fallback counts must stay at 0 per cell — a nonzero count means the
  determinizer mis-handles some card in a candidate list (new card
  effects can create new limbo states); investigate before trusting
  the cell.
- Multiple comparisons: the selection claim in ADR-002 reports raw
  and Bonferroni-corrected intervals across the cells it cites.

### Step 4 — Selection criterion

Pick the candidate with the best **worst-case** matchup (maximin over
row cells), not the best average — the ladder opponent pool is unknown,
so robustness beats average edge. Tie-break: fewer fallbacks, then
faster median match time (search budget stretches further).

### Step 5 — Record and switch

- Write `docs/adr/adr-002-why-this-deck.md` (context, candidates,
  round-robin table with CIs, decision, consequences).
- Update `decks/selected/deck.csv` + `rationale.md`.
- Note the interaction with EXP-006/H2: any experiment comparing
  agents ACROSS the deck change is invalid; re-baseline the heuristic
  matchup on deck v2 before further agent experiments.

## Candidates (designed 2026-07-10)

Four lists in `decks/candidates/`, each with a rationale `.md` beside
it. They span the design space deliberately:

| candidate | archetype | core | basics | energy |
|---|---|---|---|---|
| `current-v1` | control | Snover → Mega Abomasnow ex + Kyogre | 6 | 35 {W} |
| `v1-tuned` | same core, fixed ratios | + Ursaluna, rebuilt trainers, 27 energy | 8 | 27 {W} |
| `aggro-fire` | big basics, no evolution | Gouging Fire ex + Ursaluna + Latias pivot | 11 | 25 {R} |
| `emboar-evolution` | Stage-2 ceiling | Tepig(70HP) → Mega Emboar ex 320/380HP | 7 | 23 {R} |

Cross-candidate skeleton: Cyrano / Mega Signal as search engines,
Lacey (+ Billy & O'Nare) as draw, Boss's Orders as gust, Switch,
Bloodmoon Ursaluna ex as the colorless splash attacker. A dragon
archetype (Mega Dragonite ex 330, dual {W}{L}) was considered and
dropped: dual-type energy plus a Stage-2 line stacks two consistency
taxes, and the design space cell it would occupy (setup ceiling) is
already covered by emboar-evolution.

## Appendix — pool analysis output (2026-07-10)

`python scripts/analyze_card_pool.py`, engine-legal pool:

- **POOL: 1267 cards** — Pokémon 1056 (Basic 595, S1 345, S2 116),
  Item 77, Supporter 61, Tool 27, Stadium 26, Special Energy 12,
  Basic Energy 8 (ids 1-8: G,R,W,L,P,F,D,M).
- **Top damage**: Mega Dragonite ex 330 (S2, {W}{L}{L}), Mega Emboar
  ex 320 (S2, {R}{R}{C}, 380 HP), Salamence ex 300, Mega Latias ex
  300 (Basic!), Pikachu ex 300 (Basic, {G}{L}{M} — 3-type cost).
- **Top standalone basics**: Mega Latias ex (280 HP, 1-cost Strafe
  40+switch), Mega Mawile ex 260, Gouging Fire ex 260 ({R}{R}{C},
  230 HP), Black Kyurem ex 250, Bloodmoon Ursaluna ex 240
  (all-colorless, self-discounting).
- **Rule-box Pokémon: 151** (multi-prize).
- **Trainers**: draw n=24 (Lacey, Carmine, Billy & O'Nare, Morty's),
  search-deck n=39 (Cyrano→ex, Mega Signal→Mega ex, Buddy-Buddy
  Poffin→Basics ≤70 HP, Love Ball, Hyper Aroma [Ace Spec]→S1),
  energy-accel n=12, disruption n=16 (Prime Catcher [Ace Spec],
  Boss's Orders), heal n=13 (Potion, Super Potion), switch n=13.
- Notable engine-side ability: Emboar 569's Inferno Fandango
  (unlimited {R} attach from hand) — an energy-accel engine if a
  future candidate wants it.

## Result (2026-07-15)

EXP-007 complete: 600 matches, 0 fallbacks, 0 draws. **`current-v1`
selected** by the pre-registered maximin rule — worst-case matchup
**0.66** (vs v1-tuned), against 0.34 / 0.09 / 0.13 for the others; it
also dominates all three rivals head-to-head. The ranking is robust to
timeout handling (0.66 / 0.34 / 0.08 / 0.11 excluding timeout rows).
No candidate beats `current-v1` (replacement gate never fires), so the
selected deck is unchanged. Full write-up in
`docs/adr/adr-002-why-this-deck.md`.

## Lessons Learned

- **The control won — and that is a clean, defensible outcome, not a
  wasted phase.** Three deliberately designed candidates each lost to
  the Phase-0 sample list. Including `current-v1` as a control (rather
  than assuming any designed deck must beat a placeholder) is what let
  the round-robin *prove* the sample deck is good rather than replace it
  on faith. It also means EXP-002–006 stay valid on the unchanged deck —
  no agent re-baselining needed.
- **Maximin is the right criterion for an unknown opponent field, and it
  changed nothing vs "best average" here — but that is luck, not
  vindication.** `current-v1` happened to be both the most robust and the
  strongest on average. The rule earns its keep only when those diverge;
  keeping it pre-registered means the next deck decision can't be
  rationalized after the fact.
- **A second, independent axis (compute cost) pointed at the same deck.**
  Kaggle scores at fixed *time*; `current-v1` runs at 196 s median vs
  530 s for the Fire decks and forfeits 0.7 % of games vs 20–24 %. When
  the robustness winner is also the cheapest to pilot, confidence in the
  choice is much higher than either signal alone.
- **Card scaling engines dominate generic deckbuilding intuition.**
  v1-tuned's energy cut looked like textbook consistency improvement and
  backfired because it starved Hammer-lanche's density scaling. Read what
  the deck's key attack actually multiplies before "fixing" its ratios.

## Failed Attempts

- **v1-tuned: "fixing" the ratios weakened the core (34/100 vs
  current-v1).** Cutting {W} energy 35 → 27 to fit more trainers reduced
  Hammer-lanche's damage (Mega Abomasnow ex scales 100× per {W} in the
  top 6 discarded), the exact engine that makes the sample list work.
  The intended lesson — "isolate archetype vs ratios" — landed, just in
  the opposite direction to the design hypothesis.
- **aggro-fire: zero setup did not buy consistency (worst-case 0.09).**
  The hypothesis was that skipping evolution trades ceiling for a stable
  floor. Instead it posted the worst worst-case in the field and a
  24.3 % timeout rate — fast to *set up* is not fast to *close*, and the
  grindy Fire mirror is where the time-budget forfeits pile up.
- **emboar-evolution: highest ceiling, worst practical floor.** Mega
  Emboar ex has the pool's top damage (320/380 HP) but the Stage-2 line's
  setup tax gives it worst-case 0.13 and a 20.7 % timeout rate. Exactly
  the profile the maximin rule exists to reject.
- **Wall-clock estimate was ~6× optimistic.** The "≈ 5 h" figure in Step
  3 was extrapolated from mirror timings; asymmetric matchups run far
  longer (the Fire cells hit the per-match TIMEOUT at ~1000–1200 s), so
  the real round-robin took the better part of a day, resumed across
  sessions. The resumable runner (`--append`, skip-completed) made this a
  non-issue operationally, but the estimate itself was wrong — asymmetric
  games are longer *and* more variable than mirrors.
