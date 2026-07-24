"""EXP-010 analysis — apply the pre-registered ship gate.

Run from the project root, after ``bash scripts/run_exp010.sh`` completes:

    .venv/bin/python scripts/exp010_analysis.py

Reads ``results/exp010_<arm>_vs_<deck>.jsonl`` (12 cells, N = 50 paired
seeds each) and reports, in registry order:

1. Per-cell win rates with Wilson 95 % CIs, raw and Bonferroni-corrected
   (m = 4 deck cells), plus fallback counts and median match time.
2. Pooled win rate per arm (n = 200).
3. The three paired McNemar contrasts on shared seeds
   (selfdeck−filler = the ship gate; informed−selfdeck = the inference
   ceiling; informed−filler = the reference gap).
4. The ship-gate check: pooled selfdeck>filler significance AND the
   per-deck Wilson-separation guard.
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

from scipy.stats import binomtest, norm

ARMS = ["ismcts-filler", "ismcts-selfdeck", "ismcts"]
DECKS = ["iono", "dragapult-ex", "mega-abomasnow-ex-official", "mega-lucario-ex"]
RESULTS_DIR = Path("results")
N_PER_CELL = 50


def wilson_ci(wins: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Parameters
    ----------
    wins : int
        Number of successes.
    n : int
        Number of trials.
    alpha : float
        Significance level (0.05 -> 95 % interval).

    Returns
    -------
    tuple[float, float]
        Lower and upper interval bounds.
    """
    z = norm.ppf(1 - alpha / 2)
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    halfwidth = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - halfwidth, center + halfwidth


def load_cell(arm: str, deck: str) -> dict[int, dict]:
    """Load one cell's JSONL keyed by seed, asserting completeness."""
    rows: dict[int, dict] = {}
    path = RESULTS_DIR / f"exp010_{arm}_vs_{deck}.jsonl"
    with open(path) as fh:
        for line in fh:
            record = json.loads(line)
            rows[record["seed"]] = record
    expected = set(range(1, N_PER_CELL + 1))
    assert set(rows) == expected, f"{path}: seeds {sorted(expected - set(rows))} missing"
    return rows


def mcnemar_contrast(data: dict, arm_a: str, arm_b: str) -> None:
    """Print the pooled paired contrast arm_a vs arm_b on shared seeds."""
    both = only_a = only_b = neither = 0
    per_deck: dict[str, tuple[int, int]] = {}
    for deck in DECKS:
        pa = pb = 0
        for seed in range(1, N_PER_CELL + 1):
            win_a = data[(arm_a, deck)][seed]["outcome_for_a"] == 1
            win_b = data[(arm_b, deck)][seed]["outcome_for_a"] == 1
            if win_a and win_b:
                both += 1
            elif win_a:
                only_a += 1
                pa += 1
            elif win_b:
                only_b += 1
                pb += 1
            else:
                neither += 1
        per_deck[deck] = (pa, pb)
    discordant = only_a + only_b
    p_value = binomtest(only_a, discordant, 0.5).pvalue if discordant else float("nan")
    delta = (only_a - only_b) / (4 * N_PER_CELL)
    print(f"{arm_a} vs {arm_b}:")
    print(
        f"  both={both}  only-{arm_a}={only_a}  only-{arm_b}={only_b}  "
        f"neither={neither}"
    )
    print(
        f"  Delta={delta:+.3f} ({delta * 100:+.1f} pp)  "
        f"McNemar exact p={p_value:.3g}  (discordant={discordant})"
    )
    for deck, (pa, pb) in per_deck.items():
        print(f"    {deck:28s} only-A={pa:2d}  only-B={pb:2d}")


def main() -> None:
    data = {(arm, deck): load_cell(arm, deck) for arm in ARMS for deck in DECKS}

    print("=" * 78)
    print("Per-cell results (N=50; Wilson 95% raw + Bonferroni m=4 -> 98.75%)")
    print("=" * 78)
    cell_ci: dict[tuple[str, str], tuple[float, float]] = {}
    for arm in ARMS:
        pooled_wins = 0
        for deck in DECKS:
            rows = data[(arm, deck)]
            outcomes = [rows[s]["outcome_for_a"] for s in range(1, N_PER_CELL + 1)]
            # Producer encoding (local_ladder._sign): 1 win, 0 draw, -1
            # loss. A first version of this script guessed the encoding
            # and misfiled the -1 losses as draws — read, don't assume.
            wins = sum(1 for o in outcomes if o == 1)
            draws = sum(1 for o in outcomes if o == 0)
            fallbacks = sum(rows[s]["fallbacks_a"] for s in range(1, N_PER_CELL + 1))
            median_s = statistics.median(
                rows[s]["seconds"] for s in range(1, N_PER_CELL + 1)
            )
            lo, hi = wilson_ci(wins, N_PER_CELL)
            blo, bhi = wilson_ci(wins, N_PER_CELL, alpha=0.05 / 4)
            cell_ci[(arm, deck)] = (lo, hi)
            pooled_wins += wins
            print(
                f"{arm:16s} vs {deck:28s} {wins:2d}W {draws}D "
                f"{N_PER_CELL - wins - draws:2d}L  wr={wins / N_PER_CELL:.2f}  "
                f"95%[{lo:.3f},{hi:.3f}]  Bonf[{blo:.3f},{bhi:.3f}]  "
                f"fb={fallbacks}  med={median_s:.0f}s"
            )
        n_pooled = 4 * N_PER_CELL
        lo, hi = wilson_ci(pooled_wins, n_pooled)
        print(
            f"{arm:16s} POOLED {pooled_wins}/{n_pooled}  "
            f"wr={pooled_wins / n_pooled:.3f}  Wilson95 [{lo:.3f},{hi:.3f}]"
        )
        print("-" * 78)

    print()
    print("Paired contrasts (shared seeds within each deck cell, pooled n=200)")
    print("=" * 78)
    mcnemar_contrast(data, "ismcts-selfdeck", "ismcts-filler")
    mcnemar_contrast(data, "ismcts", "ismcts-selfdeck")
    mcnemar_contrast(data, "ismcts", "ismcts-filler")

    print()
    print("Ship-gate per-deck guard (selfdeck worse by Wilson-separated margin?)")
    print("=" * 78)
    for deck in DECKS:
        s_lo, s_hi = cell_ci[("ismcts-selfdeck", deck)]
        f_lo, f_hi = cell_ci[("ismcts-filler", deck)]
        separated_worse = s_hi < f_lo
        print(
            f"  {deck:28s} selfdeck[{s_lo:.3f},{s_hi:.3f}]  "
            f"filler[{f_lo:.3f},{f_hi:.3f}]  worse-separated: {separated_worse}"
        )


if __name__ == "__main__":
    main()
