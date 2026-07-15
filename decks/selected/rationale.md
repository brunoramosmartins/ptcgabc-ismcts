# Selected Deck — Rationale

**Status:** selected (2026-07-15, EXP-007). See
`docs/adr/adr-002-why-this-deck.md` for the full decision record.

`deck.csv` is the list designated **`current-v1`** — a Snover → Mega
Abomasnow ex + Kyogre control deck (6 basics, 35 {W} energy). It began
as the Kaggle sample list (Phase-0 placeholder) and was **promoted to a
deliberate choice** after EXP-007 tested it as the control in a
four-candidate round-robin.

Why it was kept over three purpose-built candidates:

- **Maximin winner.** Worst-case matchup win rate **0.66**, against
  0.34 / 0.09 / 0.13 for v1-tuned / aggro-fire / emboar-evolution
  (pre-registered rule: best worst-case, for robustness against an
  unknown ladder field). It also dominates all three head-to-head.
- **Cheapest to pilot under a fixed time budget.** 0.7 % timeout rate
  and 196 s median/match, vs 11–24 % and ~320–540 s for the others —
  it almost never forfeits on the clock (Kaggle scores at fixed time).
- **No challenger cleared the replacement gate** (best was 34/100 vs
  this deck), so the deck is unchanged and EXP-002–006 stay valid on it.

The engine detail that makes the list work: Hammer-lanche (Mega
Abomasnow ex) scales with deck {W} *density* (100× per {W} in the top 6
discarded), which is why the high 35-energy count is a feature, not a
consistency flaw — see ADR-002's Alternatives (v1-tuned's energy cut
backfired for exactly this reason).
