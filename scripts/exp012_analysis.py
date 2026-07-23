"""EXP-012 analysis — apply the pre-registered consistency gate (#28).

Run from the project root:

    .venv/bin/python scripts/exp012_analysis.py            # full: verdict
    .venv/bin/python scripts/exp012_analysis.py --interim  # peek: no verdict

The reference arm is NOT in the exp012 files: the registry entry
commits (at registration time) to EXP-010/011's `current-v1` selfdeck
rows — the fixed-1000-iterations *instrument* condition on the same
seeds and opponents:

    results/exp010_ismcts-selfdeck_vs_<opp>.jsonl == instrument cells

Consistency gate (pre-registered in experiments/registry.md, EXP-012):
EXP-012 PASSES iff (1) env errors = 0, TIMEOUTs = 0, fallbacks = 0
across all 4 shipping cells, AND (2) the pooled paired contrast vs the
instrument rows (shared (opponent, seed) instances, McNemar exact,
single contrast — no Bonferroni family) shows the shipping
configuration is not significantly worse (p >= 0.05, or a significant
difference in its favor). Branches: (a) pass => #29 submits unchanged;
(b) significantly worse => diagnose the budget policy, #29 blocks;
(c) any TIMEOUT/env-error/fallback => artifact bug, #29 blocks.

Unlike EXP-011, an env-error row here is NOT instrument poison to heal
away: under Policy C the agent budgets beneath the deployment bank by
construction, so a TIMEOUT is the artifact genuinely failing — it
routes to branch (c) as a finding instead of aborting the analysis.

Outcome encoding read from the producer, not assumed:
`outcome_for_a in {1, 0, -1}` = win/draw/loss (`local_ladder._sign`).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from scipy.stats import binomtest, norm

SHIPPING = "ismcts-main"
INSTRUMENT = "instrument-1000it"  # EXP-010's ismcts-selfdeck rows
OPPS = ["iono", "dragapult-ex", "mega-abomasnow-ex-official", "mega-lucario-ex"]
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


def cell_path(arm: str, opp: str) -> Path:
    """Path of one (arm, opponent deck) cell's JSONL."""
    if arm == INSTRUMENT:
        return RESULTS_DIR / f"exp010_ismcts-selfdeck_vs_{opp}.jsonl"
    return RESULTS_DIR / f"exp012_ismcts-main_vs_{opp}.jsonl"


def load_cell(arm: str, opp: str, interim: bool) -> dict[int, dict] | None:
    """Load one cell keyed by seed; None if absent and ``interim``.

    Instrument cells hard-fail on env_error (they were certified clean
    when EXP-010/011 closed; a poisoned row here means the wrong file).
    Shipping cells keep env_error rows — they are gate findings.
    """
    path = cell_path(arm, opp)
    if not path.exists():
        if interim:
            return None
        raise SystemExit(f"{path} missing — run bash scripts/run_exp012.sh; --interim to peek")
    rows: dict[int, dict] = {}
    with open(path) as fh:
        for line in fh:
            record = json.loads(line)
            if record.get("env_error") and arm == INSTRUMENT:
                raise SystemExit(
                    f"{path}: seed {record['seed']} has env_error — the instrument "
                    "cells were certified clean at EXP-011 close; wrong file?"
                )
            rows[record["seed"]] = record
    missing = set(range(1, N_PER_CELL + 1)) - set(rows)
    if missing and not interim:
        raise SystemExit(f"{path}: seeds {sorted(missing)} missing; use --interim to peek")
    return rows


def print_cells(data: dict[tuple[str, str], dict[int, dict] | None]) -> dict:
    """Per-cell W/D/L, Wilson CIs and gate-1 counters; returns the counters."""
    print("=" * 78)
    print("Per-cell results (N=50; Wilson 95% raw + Bonferroni m=4 -> 98.75%)")
    print("=" * 78)
    artifacts = {"env_errors": 0, "fallbacks": 0}
    for arm in [INSTRUMENT, SHIPPING]:
        pooled_wins = pooled_n = 0
        for opp in OPPS:
            rows = data[(arm, opp)]
            if not rows:
                print(f"{arm:18s} vs {opp:28s} -- pending --")
                continue
            outcomes = [rows[s]["outcome_for_a"] for s in sorted(rows)]
            n = len(outcomes)
            wins = sum(1 for o in outcomes if o == 1)
            draws = sum(1 for o in outcomes if o == 0)
            fallbacks = sum(rows[s]["fallbacks_a"] for s in rows)
            errors = sum(1 for s in rows if rows[s].get("env_error"))
            if arm == SHIPPING:
                artifacts["fallbacks"] += fallbacks
                artifacts["env_errors"] += errors
            median_s = statistics.median(rows[s]["seconds"] for s in rows)
            lo, hi = wilson_ci(wins, n)
            blo, bhi = wilson_ci(wins, n, alpha=0.05 / 4)
            pooled_wins += wins
            pooled_n += n
            partial = "" if n == N_PER_CELL else f"  [PARTIAL n={n}]"
            print(
                f"{arm:18s} vs {opp:28s} {wins:2d}W {draws}D {n - wins - draws:2d}L  "
                f"wr={wins / n:.2f}  95%[{lo:.3f},{hi:.3f}]  Bonf[{blo:.3f},{bhi:.3f}]  "
                f"fb={fallbacks}  err={errors}  med={median_s:.0f}s{partial}"
            )
        if pooled_n:
            lo, hi = wilson_ci(pooled_wins, pooled_n)
            print(
                f"{arm:18s} POOLED {pooled_wins}/{pooled_n}  "
                f"wr={pooled_wins / pooled_n:.3f}  Wilson95 [{lo:.3f},{hi:.3f}]"
            )
        print("-" * 78)
    return artifacts


def paired_contrast(
    data: dict[tuple[str, str], dict[int, dict] | None],
) -> tuple[int, int, int, float] | None:
    """Pooled paired McNemar of shipping vs instrument on shared seeds.

    Returns (only_shipping, only_instrument, total_pairs, raw exact p),
    or None if no cell overlaps.
    """
    only_s = only_i = both = neither = 0
    per_opp: dict[str, tuple[int, int]] = {}
    for opp in OPPS:
        rows_s = data[(SHIPPING, opp)]
        rows_i = data[(INSTRUMENT, opp)]
        if not rows_s or not rows_i:
            continue
        ps = pi = 0
        for seed in sorted(set(rows_s) & set(rows_i)):
            win_s = rows_s[seed]["outcome_for_a"] == 1
            win_i = rows_i[seed]["outcome_for_a"] == 1
            if win_s and win_i:
                both += 1
            elif win_s:
                only_s += 1
                ps += 1
            elif win_i:
                only_i += 1
                pi += 1
            else:
                neither += 1
        per_opp[opp] = (ps, pi)
    total = both + only_s + only_i + neither
    if not total:
        return None
    discordant = only_s + only_i
    p_raw = binomtest(only_s, discordant, 0.5).pvalue if discordant else float("nan")
    delta = (only_s - only_i) / total
    print(f"{SHIPPING} vs {INSTRUMENT} (paired, n={total}, single contrast):")
    print(f"  both={both}  only-shipping={only_s}  only-instrument={only_i}  neither={neither}")
    print(f"  Delta={delta:+.3f} ({delta * 100:+.1f} pp)  McNemar exact p={p_raw:.3g}")
    for opp, (ps, pi) in per_opp.items():
        print(f"    {opp:28s} only-shipping={ps:2d}  only-instrument={pi:2d}")
    return only_s, only_i, total, p_raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interim",
        action="store_true",
        help="Tolerate missing/partial cells; descriptive output only, NO verdict.",
    )
    args = parser.parse_args()

    data = {
        (arm, opp): load_cell(arm, opp, args.interim)
        for arm in [INSTRUMENT, SHIPPING]
        for opp in OPPS
    }

    artifacts = print_cells(data)

    print()
    print("Paired contrast: shipping configuration vs the instrument condition")
    print("=" * 78)
    contrast = paired_contrast(data)

    if args.interim:
        print()
        print("INTERIM PEEK — descriptive only. The pre-registered gate is applied")
        print("exclusively on the complete grid; log this peek in the journal.")
        return

    print()
    print("Pre-registered consistency gate")
    print("=" * 78)
    gate1 = artifacts["env_errors"] == 0 and artifacts["fallbacks"] == 0
    print(f"  gate 1 (env errors=0, TIMEOUTs=0, fallbacks=0): {gate1}  "
          f"(errors={artifacts['env_errors']}, fallbacks={artifacts['fallbacks']})")
    only_s, only_i, _total, p_raw = contrast
    worse = only_s < only_i and p_raw < 0.05
    print(f"  gate 2 (not significantly worse, McNemar p>=0.05 or in favor): {not worse}  "
          f"(p={p_raw:.3g}, direction={'shipping' if only_s >= only_i else 'instrument'})")

    print()
    if not gate1:
        print("BRANCH (c): artifact failure (TIMEOUT/env-error/fallback) — #29 BLOCKS;"
              " fix the artifact and rerun the affected cells.")
    elif worse:
        print("BRANCH (b): shipping configuration significantly worse than the"
              " instrument — diagnose the budget policy; #29 BLOCKS until explained.")
    else:
        print("BRANCH (a): PASS — the shipping artifact reproduces the measured"
              " strength; #29 submits it unchanged (submission-log row BEFORE upload).")


if __name__ == "__main__":
    main()
