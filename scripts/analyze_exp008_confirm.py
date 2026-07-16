r"""EXP-008 confirmation analysis: does Policy C clear the registered gates?

Reads the confirmation-stage JSONL (`results/exp008_confirmC_*.jsonl`,
written by `scripts/exp_timing.py --policy C`) and applies the decision
rule registered in `experiments/registry.md` /
`notes/phase4-time-budget-calibration.md` **before** the run:

    GATE 1: 0 forfeits (seat-0 status == TIMEOUT)
    GATE 2: cumulative per-agent time p99 < 540 s (600 s bank - 10% margin)

Both gates are evaluated pooled *and* per opponent, since a policy that
only forfeits against the Fire grinds would pass a pooled p99 and still
lose games on the ladder.

Three integrity checks run first, because a green report on broken data
is worse than a red one:

- **no ERROR/None seat status** — the `getfullargspec` bug produced whole
  files of `status=ERROR`, `M=0`, which look like "0 forfeits";
- **homogeneous operating point** — every row in the analysis must share
  one (policy, overage_reserve, budget_moves_ahead). A resumed run
  launched with different `CONF_*` env vars silently appends a *second*
  operating point to the same file, and pooling those is meaningless;
- **bank-model residual** — the engine's drawdown of the bank should
  match our measured decision times. `my_final_overage` is read at the
  *start* of the last decision, so the expected drawdown is
  $\text{cumulative} - t_{\text{last}}$, not $\text{cumulative}$. A large
  residual means the bank is charging for something we do not measure.

Pure, no engine, no SDK — reads files and prints a report. Exit code 0
iff every integrity check and both gates pass.

    python scripts/analyze_exp008_confirm.py \\
        [--glob 'results/exp008_confirmC_*.jsonl'] [--budget 540] [--bank 600]
"""

from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from analyze_exp008 import pct  # noqa: E402
from stats.wilson import wilson_interval  # noqa: E402

_OK_STATUS = {"DONE", "TIMEOUT", "ACTIVE", "INACTIVE"}


def load_rows(pattern: str) -> list[dict]:
    """Load every confirm-stage row, tagging each with its opponent."""
    rows: list[dict] = []
    for path in sorted(glob.glob(pattern)):
        opp = pathlib.Path(path).stem.split("_vs_")[-1]
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            r["_opp"] = opp
            rows.append(r)
    return rows


def bad_status_rows(rows: list[dict]) -> list[dict]:
    """Rows whose seat status is missing or not a real engine outcome.

    Guards the `status=ERROR` failure mode, where no decision ever ran and
    the zeros masquerade as a clean, forfeit-free result.
    """
    return [
        r for r in rows
        if r.get("status_0") not in _OK_STATUS
        or r.get("status_1") not in _OK_STATUS
    ]


def operating_points(rows: list[dict]) -> set[tuple]:
    """The distinct (policy, reserve, moves_ahead) tuples present."""
    return {
        (r.get("policy"), r.get("overage_reserve"), r.get("moves_ahead"))
        for r in rows
    }


def bank_residual(row: dict, bank: float) -> float | None:
    """Signed seconds the engine charged beyond what we measured.

    The bank reading is taken at the start of the final decision, so the
    drawdown it reflects excludes that decision's cost:

    $$\\text{residual} = (\\text{bank} - R_{\\text{final}})
        - (\\text{cumulative} - t_{\\text{last}}).$$

    Returns ``None`` when the row has no bank reading or no decisions.
    """
    final = row.get("my_final_overage")
    times = row.get("my_decision_times") or []
    if final is None or not times:
        return None
    drawdown = bank - float(final)
    measured = float(row["my_cumulative"]) - float(times[-1])
    return drawdown - measured


def summarize_cell(rows: list[dict], budget: float) -> dict:
    """Per-opponent (or pooled) stats the decision rule needs."""
    cumulative = [float(r["my_cumulative"]) for r in rows]
    ms = [float(r["my_decisions"]) for r in rows]
    times = [float(t) for r in rows for t in r["my_decision_times"]]
    banks = [float(r["my_final_overage"]) for r in rows
             if r.get("my_final_overage") is not None]
    wins = sum(1 for r in rows if r["reward_0"] == 1)
    lo, hi = wilson_interval(wins, len(rows)) if rows else (0.0, 0.0)
    return {
        "n": len(rows),
        "forfeits": sum(1 for r in rows if r.get("forfeit")),
        "cum_median": pct(cumulative, 0.5),
        "cum_p99": pct(cumulative, 0.99),
        "cum_max": max(cumulative) if cumulative else None,
        "headroom": budget - max(cumulative) if cumulative else None,
        "bank_floor": min(banks) if banks else None,
        "m_median": pct(ms, 0.5),
        "m_max": max(ms) if ms else None,
        "dec_median": pct(times, 0.5),
        "dec_max": max(times) if times else None,
        "win_rate": wins / len(rows) if rows else None,
        "wilson": (lo, hi),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="EXP-008 confirmation analysis")
    ap.add_argument("--glob", default="results/exp008_confirmC_*.jsonl")
    ap.add_argument("--budget", type=float, default=540.0,
                    help="Registered cumulative gate (600 bank - 10%% margin).")
    ap.add_argument("--bank", type=float, default=600.0,
                    help="Starting remainingOverageTime, for the residual check.")
    args = ap.parse_args()

    rows = load_rows(args.glob)
    if not rows:
        print(f"No rows matched {args.glob!r}. Run the confirm stage first.")
        return 1

    ok = True
    print("=== integrity ===")

    bad = bad_status_rows(rows)
    if bad:
        ok = False
        seen = sorted({(r.get("status_0"), r.get("status_1")) for r in bad})
        print(f"FAIL  {len(bad)}/{len(rows)} rows with non-outcome status: {seen}")
        print("      (status=ERROR means no decision ever ran — delete and rerun)")
    else:
        print(f"ok    {len(rows)} rows, all seats reached a real outcome")

    points = operating_points(rows)
    if len(points) != 1:
        ok = False
        print(f"FAIL  {len(points)} distinct operating points pooled: "
              f"{sorted(points, key=str)}")
        print("      (a resume used different CONF_* — split or rerun the cell)")
    else:
        policy, reserve, moves = next(iter(points))
        print(f"ok    single operating point: policy={policy} "
              f"reserve={reserve}s moves-ahead={moves}")
        if policy != "C":
            ok = False
            print("FAIL  confirmation must be Policy C")

    residuals = [r for r in (bank_residual(x, args.bank) for x in rows)
                 if r is not None]
    if residuals:
        worst = max(residuals, key=abs)
        print(f"ok    bank-model residual: median={pct(residuals, 0.5):+.2f}s "
              f"worst={worst:+.2f}s over {len(residuals)} games")
        print("      (engine drawdown vs measured decision time; ~0 confirms "
              "every second of thinking is charged to the bank)")

    print(f"\n=== per opponent (gate: 0 forfeits, cumulative p99 < "
          f"{args.budget:.0f}s) ===")
    header = (f"{'opponent':<18} {'n':>3} {'ff':>3} {'cum_med':>8} {'cum_p99':>8} "
              f"{'cum_max':>8} {'bank_min':>9} {'M_med':>6} {'M_max':>6} "
              f"{'dec_med':>8} {'win':>5}")
    print(header)
    by_opp: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_opp[r["_opp"]].append(r)
    for opp in sorted(by_opp):
        s = summarize_cell(by_opp[opp], args.budget)
        print(f"{opp:<18} {s['n']:>3} {s['forfeits']:>3} {s['cum_median']:>8.1f} "
              f"{s['cum_p99']:>8.1f} {s['cum_max']:>8.1f} {s['bank_floor']:>9.1f} "
              f"{s['m_median']:>6.0f} {s['m_max']:>6.0f} {s['dec_median']:>8.2f} "
              f"{s['win_rate']:>5.2f}")
        if s["forfeits"] or s["cum_p99"] >= args.budget:
            ok = False

    print("\n=== win rate, Wilson 95% CI (descriptive: Policy C vs 1000-iter "
          "ISMCTS) ===")
    for opp in sorted(by_opp):
        s = summarize_cell(by_opp[opp], args.budget)
        lo, hi = s["wilson"]
        print(f"  vs {opp:<18} {s['win_rate']:.2f}  [{lo:.2f}, {hi:.2f}]  "
              f"(n={s['n']})")

    pooled = summarize_cell(rows, args.budget)
    print("\n=== pooled + registered gates ===")
    print(f"games={pooled['n']}  decisions={sum(r['my_decisions'] for r in rows)}")
    g1 = pooled["forfeits"] == 0
    g2 = pooled["cum_p99"] < args.budget
    print(f"GATE 1  forfeits == 0            : {pooled['forfeits']}/{pooled['n']}"
          f"   {'PASS' if g1 else 'FAIL'}")
    print(f"GATE 2  cumulative p99 < {args.budget:.0f}s     : "
          f"{pooled['cum_p99']:.1f}s   {'PASS' if g2 else 'FAIL'}")
    print(f"        worst game               : {pooled['cum_max']:.1f}s "
          f"({pooled['headroom']:.1f}s headroom, bank floor "
          f"{pooled['bank_floor']:.1f}s)")
    ok = ok and g1 and g2

    util = pooled["cum_max"] / args.budget if pooled["cum_max"] else 0.0
    print(f"\nBudget utilization (worst game / {args.budget:.0f}s): {util:.0%}. "
          "Low utilization is not\nfree safety — it is strength left on the "
          "table: the bank is per *episode*, so\nseconds unspent are seconds "
          "burned. Weigh against #26/H3 before locking #29.")

    print(f"\nVERDICT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
