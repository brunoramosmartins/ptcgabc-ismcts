r"""EXP-008 analysis: fit c(it), summarize M, derive the safe operating point.

Reads the fit-stage JSONL (`results/exp008_fit_*.jsonl`, written by
`scripts/exp_timing.py`) and reports exactly what the EXP-008 decision
rule needs (see `notes/phase4-time-budget-calibration.md`):

- the fitted per-decision cost model $c(\text{it}) = \alpha + \beta\,\text{it}$
  with $R^2$, plus per-level median / p95;
- the decisions-per-game distribution $M$ (median / p95 / p99, pooled and
  per opponent);
- the derived forfeit-safe operating points under a 540 s budget:
  largest fixed $\text{it}^\*$ (policy A/B) and the Policy-C sanity check
  (is `budget_moves_ahead` >= p99[M], and the full-bank per-move budget).

Pure, no engine, no SDK — reads files and prints a report.

    python scripts/analyze_exp008.py [--glob 'results/exp008_fit_*.jsonl'] \\
        [--budget 540] [--reserve 60] [--moves-ahead 40] [--full-bank 600]
"""

from __future__ import annotations

import argparse
import glob
import json
import pathlib
from collections import defaultdict


def fit_linear(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Ordinary least squares for ``y = alpha + beta * x``.

    Returns ``(alpha, beta, r2)``. ``r2`` is 0.0 when ``y`` has no
    variance (degenerate) and when there are fewer than two points.
    """
    n = len(xs)
    if n < 2:
        return (ys[0] if ys else 0.0, 0.0, 0.0)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = sxy / sxx if sxx else 0.0
    alpha = my - beta * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (alpha + beta * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
    return (alpha, beta, r2)


def pct(xs: list[float], q: float) -> float | None:
    """Nearest-rank percentile (q in [0, 1]); ``None`` for empty input."""
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def largest_safe_iters(alpha: float, beta: float, p99_m: float,
                       budget: float) -> float:
    """Largest it with c(it)*p99[M] <= budget, i.e. it <= (budget/p99M - alpha)/beta."""
    if p99_m <= 0 or beta <= 0:
        return float("inf")
    return (budget / p99_m - alpha) / beta


def load_rows(pattern: str) -> list[dict]:
    rows: list[dict] = []
    for path in glob.glob(pattern):
        opp = pathlib.Path(path).stem.split("_vs_")[-1]
        for line in open(path):
            r = json.loads(line)
            r["_opp"] = opp
            rows.append(r)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="EXP-008 fit analysis")
    ap.add_argument("--glob", default="results/exp008_fit_*.jsonl")
    ap.add_argument("--budget", type=float, default=540.0,
                    help="Cumulative per-agent budget (600 - margin).")
    ap.add_argument("--reserve", type=float, default=60.0)
    ap.add_argument("--moves-ahead", type=int, default=40)
    ap.add_argument("--full-bank", type=float, default=600.0)
    args = ap.parse_args()

    rows = load_rows(args.glob)
    if not rows:
        print(f"No rows matched {args.glob!r}. Run the fit stage first.")
        return 1

    # --- per-decision cost: fit c(it) over all (iters, decision_time) ---
    xs: list[float] = []
    ys: list[float] = []
    per_level: dict[int, list[float]] = defaultdict(list)
    for r in rows:
        it = r["iterations"]
        for t in r["my_decision_times"]:
            xs.append(float(it))
            ys.append(float(t))
            per_level[it].append(float(t))
    alpha, beta, r2 = fit_linear(xs, ys)

    print("=== per-decision cost c(it) = alpha + beta*it ===")
    print(f"alpha={alpha*1000:.2f} ms   beta={beta*1000:.4f} ms/iter   "
          f"R^2={r2:.3f}   (n={len(xs)} decisions)")
    print(f"{'iters':>7} {'median_s':>9} {'p95_s':>8} {'n_dec':>7}")
    for it in sorted(per_level):
        d = per_level[it]
        print(f"{it:>7} {pct(d, 0.5):>9.3f} {pct(d, 0.95):>8.3f} {len(d):>7}")

    # --- M (decisions/agent/game) ---
    ms = [float(r["my_decisions"]) for r in rows]
    p99_m = pct(ms, 0.99)
    print("\n=== M = decisions/agent/game ===")
    print(f"pooled: median={pct(ms,0.5):.0f} p95={pct(ms,0.95):.0f} "
          f"p99={p99_m:.0f} max={int(max(ms))} (n={len(ms)} games)")
    by_opp: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_opp[r["_opp"]].append(float(r["my_decisions"]))
    for opp in sorted(by_opp):
        d = by_opp[opp]
        print(f"  vs {opp:<18} median={pct(d,0.5):.0f} p95={pct(d,0.95):.0f} "
              f"p99={pct(d,0.99):.0f}")

    # --- derived safe operating points ---
    print("\n=== safe operating point (budget "
          f"{args.budget:.0f}s, p99[M]={p99_m:.0f}) ===")
    it_star = largest_safe_iters(alpha, beta, p99_m, args.budget)
    print(f"A/B fixed: largest safe it* = {it_star:.0f}  "
          f"(=> t_move* = {args.budget / p99_m:.2f}s per decision)")
    forfeits = sum(1 for r in rows if r.get("forfeit"))
    print(f"observed forfeits in fit data: {forfeits}/{len(rows)} "
          "(expected > 0 at high iters — that's the problem being fixed)")

    print("\n=== Policy C sanity (adaptive) ===")
    per_move_full = (args.full_bank - args.reserve) / max(args.moves_ahead, 1)
    conservative = args.moves_ahead >= (p99_m or 0)
    print(f"full-bank per-move budget = ({args.full_bank:.0f}-{args.reserve:.0f})"
          f"/{args.moves_ahead} = {per_move_full:.2f}s")
    print(f"moves-ahead {args.moves_ahead} {'>=' if conservative else '<'} "
          f"p99[M] {p99_m:.0f}  -> "
          f"{'conservative (safe)' if conservative else 'RAISE moves-ahead'}")
    print("Policy C cannot deplete the bank by construction; the check above"
          " only asks whether the early-game per-move budget is generous.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
