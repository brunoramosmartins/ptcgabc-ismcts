# Phase 4 — Deck Selection Process (feeds ADR-002)

Goal: replace the Phase-0 placeholder deck with a deliberately chosen
list before the Simulation deadline (Aug 16-17), using local evidence
rather than internet meta. Output: `decks/selected/deck.csv` (v2) plus
`docs/adr/adr-002-deck-selection.md` recording the decision.

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

Register the experiment in `experiments/registry.md` BEFORE running
(EXP-007, objective: select deck v2). Then, for every ordered pair
(A, B) of candidates:

```
python scripts/local_ladder.py \
    --agent-a ismcts-guided --agent-b ismcts-guided \
    --deck-a decks/candidates/A.csv --deck-b decks/candidates/B.csv \
    --matches 100 --seed-start 1 --iterations 1000 \
    --out results/exp007_A_vs_B.jsonl
```

Protocol notes:

- **Same agent both seats** — we are measuring decks, not agents.
  Both agents receive both true lists (`AgentBuilder` contract), so
  determinization consistency holds in asymmetric matchups.
- **Both orderings** (A-vs-B and B-vs-A) to cancel any seat/first-move
  advantage; paired seeds within each ordering.
- 100 matches per ordered pair keeps a 4-candidate round-robin at
  12 runs ≈ manageable wall-clock; report each cell as win rate with
  Wilson 95% CI.
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

- Write `docs/adr/adr-002-deck-selection.md` (context, candidates,
  round-robin table with CIs, decision, consequences).
- Update `decks/selected/deck.csv` + `rationale.md`.
- Note the interaction with EXP-006/H2: any experiment comparing
  agents ACROSS the deck change is invalid; re-baseline the heuristic
  matchup on deck v2 before further agent experiments.

## Appendix — pool analysis output

_(pending: paste `python scripts/analyze_card_pool.py` output here)_

## Lessons Learned

_(pending: fill at phase close)_

## Failed Attempts

_(pending: fill at phase close)_
