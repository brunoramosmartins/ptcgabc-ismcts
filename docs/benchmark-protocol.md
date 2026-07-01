# Benchmark Protocol

**Status:** skeleton (Phase 0) — finalized in Phase 1.

Reference against which every hypothesis test in Phase 3 and Phase 5 is evaluated.

## Match Set

- **N matches per comparison:** _TBD (Phase 1, respecting the sample-size analysis in `exercises/ex05_statistical_inference.md`)._
- **K seeds:** _TBD._
- **Opponent pool:** _TBD._

## Determinism and Seeding

- RNG seed policy: _TBD._
- Deck version pinning: `decks/selected/deck.json` tagged with the git tag at experiment time.

## Hardware

- Machine: _TBD._
- Wall-clock budget per match: 10 minutes (competition limit).

## Reporting

- Win rates: Wilson 95% CI, not bare proportion.
- Agent comparisons on shared seeds: paired bootstrap or McNemar's test.
- Multiple comparisons (H4): Bonferroni correction.
