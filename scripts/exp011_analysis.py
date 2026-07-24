"""EXP-011 analysis — apply the pre-registered deck-selection rule.

Run from the project root:

    .venv/bin/python scripts/exp011_analysis.py            # full: verdict
    .venv/bin/python scripts/exp011_analysis.py --interim  # peek: no verdict

The `current-v1` row is NOT in the exp011 files: the registry entry
commits (at registration time) to reusing EXP-010's selfdeck arm, which
is cell-identical (same agent, deck, seeds, iterations, opponents):

    results/exp010_ismcts-selfdeck_vs_<opp>.jsonl == current-v1 cells

Selection rule (pre-registered in experiments/registry.md, EXP-011): a
challenger replaces `current-v1` iff it beats it on the pooled paired
contrast across the field (shared (opponent, seed) instances, McNemar
exact, p < 0.05 Bonferroni-corrected for m = 3 challengers) AND is not
worse than `current-v1` in any single opponent cell by Wilson-separated
margin. The incumbent wins ties. Branches: (a) nobody separates ⇒
`current-v1` survives; (b) exactly one ⇒ ship it; (c) several ⇒ ship
the one with the higher pooled rate.

`--interim` tolerates missing/incomplete cells and prints descriptive
numbers only — the rule is applied exclusively on the complete grid, so
a peek cannot turn into an early verdict. Any peek must still be logged
in the decision journal (EXP-009 precedent).

Validity guards, before any number is printed: no `env_error` rows
anywhere (heal first — see EXP-011 amendment 2), and the producer's
outcome encoding is read, not assumed: `outcome_for_a ∈ {1, 0, −1}` =
win/draw/loss (`local_ladder._sign`) — W/D/L is reported per cell.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from scipy.stats import binomtest, norm

INCUMBENT = "current-v1"
CHALLENGERS = ["v1-tuned", "aggro-fire", "emboar-evolution"]
OPPS = ["iono", "dragapult-ex", "mega-abomasnow-ex-official", "mega-lucario-ex"]
RESULTS_DIR = Path("results")
N_PER_CELL = 50
M_CHALLENGERS = 3  # Bonferroni family: the three pooled challenger contrasts


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


def cell_path(deck: str, opp: str) -> Path:
    """Path of one (our deck, opponent deck) cell's JSONL."""
    if deck == INCUMBENT:
        return RESULTS_DIR / f"exp010_ismcts-selfdeck_vs_{opp}.jsonl"
    return RESULTS_DIR / f"exp011_{deck}_vs_{opp}.jsonl"


def load_cell(deck: str, opp: str, interim: bool) -> dict[int, dict] | None:
    """Load one cell keyed by seed; None if absent and ``interim``.

    Hard-fails on any ``env_error`` row (poisoned cell — run
    scripts/heal_exp011_env_errors.sh first) and, unless ``interim``,
    on an incomplete seed set.
    """
    path = cell_path(deck, opp)
    if not path.exists():
        if interim:
            return None
        raise SystemExit(f"{path} missing — the grid is incomplete; use --interim to peek")
    rows: dict[int, dict] = {}
    with open(path) as fh:
        for line in fh:
            record = json.loads(line)
            if record.get("env_error"):
                raise SystemExit(
                    f"{path}: seed {record['seed']} has env_error — poisoned cell, "
                    "run scripts/heal_exp011_env_errors.sh before analyzing"
                )
            rows[record["seed"]] = record
    missing = set(range(1, N_PER_CELL + 1)) - set(rows)
    if missing and not interim:
        raise SystemExit(f"{path}: seeds {sorted(missing)} missing; use --interim to peek")
    return rows


def print_cells(data: dict[tuple[str, str], dict[int, dict] | None]) -> dict:
    """Print per-cell W/D/L + Wilson CIs; return the raw CI per cell."""
    print("=" * 78)
    print("Per-cell results (N=50; Wilson 95% raw + Bonferroni m=4 -> 98.75%)")
    print("=" * 78)
    cell_ci: dict[tuple[str, str], tuple[float, float]] = {}
    for deck in [INCUMBENT, *CHALLENGERS]:
        pooled_wins = pooled_n = 0
        for opp in OPPS:
            rows = data[(deck, opp)]
            if not rows:
                print(f"{deck:18s} vs {opp:28s} -- pending --")
                continue
            outcomes = [rows[s]["outcome_for_a"] for s in sorted(rows)]
            # Producer encoding (local_ladder._sign): 1 win, 0 draw, -1
            # loss — read from the producer, not assumed (EXP-010's
            # false-draw alarm).
            n = len(outcomes)
            wins = sum(1 for o in outcomes if o == 1)
            draws = sum(1 for o in outcomes if o == 0)
            fallbacks = sum(rows[s]["fallbacks_a"] for s in rows)
            median_s = statistics.median(rows[s]["seconds"] for s in rows)
            lo, hi = wilson_ci(wins, n)
            blo, bhi = wilson_ci(wins, n, alpha=0.05 / 4)
            cell_ci[(deck, opp)] = (lo, hi)
            pooled_wins += wins
            pooled_n += n
            partial = "" if n == N_PER_CELL else f"  [PARTIAL n={n}]"
            print(
                f"{deck:18s} vs {opp:28s} {wins:2d}W {draws}D {n - wins - draws:2d}L  "
                f"wr={wins / n:.2f}  95%[{lo:.3f},{hi:.3f}]  "
                f"Bonf[{blo:.3f},{bhi:.3f}]  fb={fallbacks}  med={median_s:.0f}s{partial}"
            )
        if pooled_n:
            lo, hi = wilson_ci(pooled_wins, pooled_n)
            print(
                f"{deck:18s} POOLED {pooled_wins}/{pooled_n}  "
                f"wr={pooled_wins / pooled_n:.3f}  Wilson95 [{lo:.3f},{hi:.3f}]"
            )
        print("-" * 78)
    return cell_ci


def paired_contrast(
    data: dict[tuple[str, str], dict[int, dict] | None], challenger: str
) -> tuple[int, int, float] | None:
    """Pooled paired McNemar of challenger vs the incumbent.

    Pairs are shared (opponent, seed) instances; only seeds present in
    BOTH cells enter (relevant under --interim). Returns
    (only_challenger, only_incumbent, raw exact p), or None if no cell
    overlaps.
    """
    only_c = only_i = both = neither = 0
    per_opp: dict[str, tuple[int, int]] = {}
    for opp in OPPS:
        rows_c = data[(challenger, opp)]
        rows_i = data[(INCUMBENT, opp)]
        if not rows_c or not rows_i:
            continue
        pc = pi = 0
        for seed in sorted(set(rows_c) & set(rows_i)):
            win_c = rows_c[seed]["outcome_for_a"] == 1
            win_i = rows_i[seed]["outcome_for_a"] == 1
            if win_c and win_i:
                both += 1
            elif win_c:
                only_c += 1
                pc += 1
            elif win_i:
                only_i += 1
                pi += 1
            else:
                neither += 1
        per_opp[opp] = (pc, pi)
    total = both + only_c + only_i + neither
    if not total:
        return None
    discordant = only_c + only_i
    p_raw = binomtest(only_c, discordant, 0.5).pvalue if discordant else float("nan")
    delta = (only_c - only_i) / total
    print(f"{challenger} vs {INCUMBENT} (paired, n={total}):")
    print(f"  both={both}  only-{challenger}={only_c}  "
          f"only-{INCUMBENT}={only_i}  neither={neither}")
    print(
        f"  Delta={delta:+.3f} ({delta * 100:+.1f} pp)  McNemar exact "
        f"p={p_raw:.3g}  Bonferroni(m={M_CHALLENGERS}) p={min(1.0, M_CHALLENGERS * p_raw):.3g}"
    )
    for opp, (pc, pi) in per_opp.items():
        print(f"    {opp:28s} only-challenger={pc:2d}  only-incumbent={pi:2d}")
    return only_c, only_i, p_raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interim",
        action="store_true",
        help="Tolerate missing/partial cells; descriptive output only, NO verdict.",
    )
    args = parser.parse_args()

    data = {
        (deck, opp): load_cell(deck, opp, args.interim)
        for deck in [INCUMBENT, *CHALLENGERS]
        for opp in OPPS
    }

    cell_ci = print_cells(data)

    print()
    print("Paired contrasts vs the incumbent (shared (opponent, seed) instances)")
    print("=" * 78)
    contrasts = {c: paired_contrast(data, c) for c in CHALLENGERS}

    print()
    print("Per-cell guard (challenger worse than incumbent by Wilson separation?)")
    print("=" * 78)
    separated_worse: dict[str, list[str]] = {c: [] for c in CHALLENGERS}
    for challenger in CHALLENGERS:
        for opp in OPPS:
            ci_c = cell_ci.get((challenger, opp))
            ci_i = cell_ci.get((INCUMBENT, opp))
            if not ci_c or not ci_i:
                print(f"  {challenger:18s} vs {opp:28s} -- pending --")
                continue
            worse = ci_c[1] < ci_i[0]
            if worse:
                separated_worse[challenger].append(opp)
            print(
                f"  {challenger:18s} vs {opp:28s} challenger[{ci_c[0]:.3f},{ci_c[1]:.3f}]  "
                f"incumbent[{ci_i[0]:.3f},{ci_i[1]:.3f}]  worse-separated: {worse}"
            )

    if args.interim:
        print()
        print("INTERIM PEEK — descriptive only. The pre-registered rule is applied")
        print("exclusively on the complete 4x4 grid; log this peek in the journal.")
        return

    print()
    print("Pre-registered selection rule")
    print("=" * 78)
    winners: list[str] = []
    for challenger in CHALLENGERS:
        only_c, only_i, p_raw = contrasts[challenger]
        p_bonf = min(1.0, M_CHALLENGERS * p_raw)
        beats = only_c > only_i and p_bonf < 0.05
        guard_ok = not separated_worse[challenger]
        verdict = "REPLACES" if beats and guard_ok else "rejected"
        print(
            f"  {challenger:18s} beats-pooled(p_bonf<0.05): {beats}  "
            f"no-worse-cell: {guard_ok}"
            + (f" (worse vs {', '.join(separated_worse[challenger])})" if not guard_ok else "")
            + f"  -> {verdict}"
        )
        if beats and guard_ok:
            winners.append(challenger)

    print()
    if not winners:
        print(f"BRANCH (a): no challenger separates — `{INCUMBENT}` survives; "
              "ADR-002 reaffirmed on real-field evidence.")
    elif len(winners) == 1:
        print(f"BRANCH (b): `{winners[0]}` replaces `{INCUMBENT}` — revise ADR-002.")
    else:
        rates = {}
        for challenger in winners:
            wins = sum(
                1
                for opp in OPPS
                for s in data[(challenger, opp)]
                if data[(challenger, opp)][s]["outcome_for_a"] == 1
            )
            rates[challenger] = wins
        best = max(rates, key=rates.get)
        print(f"BRANCH (c): several separate ({', '.join(winners)}) — pre-committed "
              f"tie-break picks the higher pooled rate: `{best}`.")


if __name__ == "__main__":
    main()
