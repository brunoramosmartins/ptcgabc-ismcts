"""EXP-008 time-budget calibration runner (#27).

Instruments our ISMCTS agent (seat 0) over many recorded games on the
**enforced** ``make("cabt")`` path — the only path that draws down the
per-agent ``remainingOverageTime`` bank and can therefore forfeit — and
logs, per game, everything the calibration model needs:

- ``my_decisions`` (= M, decisions/agent/game),
- ``my_decision_times`` (every ISMCTS ``choose`` wall-time → fits
  ``c(it) = alpha + beta * it``),
- ``my_cumulative`` (sum of the above),
- ``my_final_overage`` (the bank as the game ended),
- ``forfeit`` (seat-0 status == "TIMEOUT"),
- ``result`` and ``seconds``.

This is NOT an experiment verdict on its own — it is the measurement
feeding EXP-008's registered decision rule (see
``notes/phase4-time-budget-calibration.md``). Nothing here is gated;
the protocol's confirmation run asserts 0 forfeits at the chosen
operating point.

Budget policy (seat 0), matching ``ISMCTSAgent``:

- ``--policy A`` (default): fixed ``--iterations`` per decision.
- ``--policy B --max-seconds T``: fixed per-move wall-clock cap.
- ``--policy C``: adaptive — reads the live bank and spends
  ``(bank - reserve) / moves-ahead`` seconds per decision.

Example (fit c(it): sweep iterations, ismcts both seats, current-v1 vs
each candidate):

    python scripts/exp_timing.py \\
        --my-deck decks/candidates/current-v1.csv \\
        --opp-deck decks/candidates/aggro-fire.csv \\
        --policy A --iterations 1000 \\
        --matches 5 --seed-start 1 \\
        --out results/exp008_A1000_v1_vs_aggro.jsonl

    # Adaptive confirmation run:
    python scripts/exp_timing.py --policy C --iterations 100000 \\
        --overage-reserve 60 --moves-ahead 40 \\
        --my-deck decks/candidates/current-v1.csv \\
        --opp-deck decks/candidates/aggro-fire.csv \\
        --matches 30 --out results/exp008_C_v1_vs_aggro.jsonl

``kaggle_environments`` is imported lazily so unit tests run without the
SDK.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import statistics
import sys
import time
from collections.abc import Callable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.heuristic_agent import HeuristicAgent  # noqa: E402
from agents.ismcts_agent import ISMCTSAgent  # noqa: E402
from stats.wilson import wilson_interval  # noqa: E402


def _load_deck(path: pathlib.Path) -> list[int]:
    """Read the first 60 card ids from a deck CSV (one id per line)."""
    lines = path.read_text().splitlines()
    return [int(lines[i]) for i in range(60)]


def _build_seat0(args, deck: list[int], opp: list[int], seed: int) -> ISMCTSAgent:
    """Our instrumented agent, with the CLI-selected budget policy."""
    kwargs = dict(
        my_deck_list=deck,
        opponent_deck_list=opp,
        iterations=args.iterations,
        rng=random.Random(seed),
    )
    if args.policy == "B":
        kwargs["max_seconds_per_move"] = args.max_seconds
    elif args.policy == "C":
        kwargs["adaptive_budget"] = True
        kwargs["overage_reserve"] = args.overage_reserve
        kwargs["budget_moves_ahead"] = args.moves_ahead
    return ISMCTSAgent(**kwargs)


def _build_seat1(args, deck: list[int], opp: list[int], seed: int):
    """Opponent — ismcts (realistic game length) or heuristic (fast)."""
    if args.opp_agent == "heuristic":
        return HeuristicAgent()
    return ISMCTSAgent(
        my_deck_list=deck,
        opponent_deck_list=opp,
        iterations=args.opp_iterations,
        rng=random.Random(seed + 10_000),
    )


class _Record:
    """Mutable per-seat log filled by the timing closure."""

    __slots__ = ("times", "last_overage")

    def __init__(self) -> None:
        self.times: list[float] = []
        self.last_overage: float | None = None


def _timed_fn(agent, deck: list[int], rec: _Record) -> Callable[[dict], list[int]]:
    """Bind an agent to the ``cabt`` ``agent(obs) -> list[int]`` contract,
    timing each real decision into ``rec``.

    Must be a plain closure, NOT a callable object: ``kaggle_environments``
    inspects the agent with ``getfullargspec``, which rejects class
    instances (that was the EXP-008 ``status=ERROR`` bug).
    """

    def _fn(obs: dict) -> list[int]:
        rov = obs.get("remainingOverageTime")
        if rov is not None:
            rec.last_overage = rov
        if obs["select"] is None:  # deck-submission step, not a decision
            return deck
        t0 = time.perf_counter()
        choice = agent.choose(obs)
        rec.times.append(time.perf_counter() - t0)
        return choice

    return _fn


def run_match(args, deck0: list[int], deck1: list[int], seed: int) -> dict:
    from kaggle_environments import make

    env = make("cabt", debug=False, configuration={"randomSeed": seed})
    a0 = _build_seat0(args, deck0, deck1, seed)
    a1 = _build_seat1(args, deck1, deck0, seed)
    rec0, rec1 = _Record(), _Record()

    t0 = time.perf_counter()
    env.run([_timed_fn(a0, deck0, rec0), _timed_fn(a1, deck1, rec1)])
    seconds = time.perf_counter() - t0

    reward0 = env.state[0]["reward"]
    reward1 = env.state[1]["reward"]
    status0 = env.state[0].get("status")
    status1 = env.state[1].get("status")

    return {
        "seed": seed,
        "policy": args.policy,
        "iterations": args.iterations,
        "max_seconds": args.max_seconds,
        "overage_reserve": args.overage_reserve if args.policy == "C" else None,
        "moves_ahead": args.moves_ahead if args.policy == "C" else None,
        "my_decisions": len(rec0.times),         # M
        "my_decision_times": [round(t, 4) for t in rec0.times],
        "my_cumulative": round(sum(rec0.times), 3),
        "my_final_overage": rec0.last_overage,
        "opp_decisions": len(rec1.times),
        "reward_0": reward0,
        "reward_1": reward1,
        "status_0": status0,
        "status_1": status1,
        "forfeit": status0 == "TIMEOUT",
        "fallbacks": len(a0.fallback_events),
        "seconds": round(seconds, 2),
    }


def summarize(rows: list[dict]) -> dict:
    """Aggregate per-decision cost, M, cumulative tail, forfeit count."""
    all_times = [t for r in rows for t in r["my_decision_times"]]
    ms = [r["my_decisions"] for r in rows]
    cumulative = [r["my_cumulative"] for r in rows]
    forfeits = sum(1 for r in rows if r["forfeit"])

    def _pct(xs: list[float], q: float) -> float | None:
        if not xs:
            return None
        s = sorted(xs)
        return round(s[min(len(s) - 1, int(q * len(s)))], 3)

    n = len(rows)
    wl, wh = wilson_interval(sum(1 for r in rows if r["reward_0"] == 1), n) \
        if n else (0.0, 0.0)
    return {
        "n_games": n,
        "policy": rows[0]["policy"] if rows else None,
        "iterations": rows[0]["iterations"] if rows else None,
        "forfeits": forfeits,
        "per_decision_s": {
            "median": _pct(all_times, 0.5),
            "p95": _pct(all_times, 0.95),
            "max": round(max(all_times), 3) if all_times else None,
            "n": len(all_times),
        },
        "M_decisions_per_game": {
            "median": _pct([float(m) for m in ms], 0.5),
            "p95": _pct([float(m) for m in ms], 0.95),
            "max": max(ms) if ms else None,
        },
        "cumulative_s": {
            "median": _pct(cumulative, 0.5),
            "p95": _pct(cumulative, 0.95),
            "p99": _pct(cumulative, 0.99),
            "max": round(max(cumulative), 2) if cumulative else None,
        },
        "win_rate_seat0": round(sum(1 for r in rows if r["reward_0"] == 1) / n, 3)
        if n else None,
        "wilson_seat0": [round(wl, 3), round(wh, 3)],
    }


def main() -> int:
    p = argparse.ArgumentParser(description="EXP-008 time-budget calibration")
    p.add_argument("--my-deck", type=pathlib.Path,
                   default=REPO_ROOT / "decks" / "selected" / "deck.csv")
    p.add_argument("--opp-deck", type=pathlib.Path, default=None,
                   help="Opponent deck (default: mirror of --my-deck).")
    p.add_argument("--policy", choices=["A", "B", "C"], default="A")
    p.add_argument("--iterations", type=int, default=1000)
    p.add_argument("--max-seconds", type=float, default=None,
                   help="Policy B: fixed per-move wall-clock cap.")
    p.add_argument("--overage-reserve", type=float, default=60.0,
                   help="Policy C: never-spend cushion (seconds).")
    p.add_argument("--moves-ahead", type=int, default=40,
                   help="Policy C: conservative decisions-remaining estimate.")
    p.add_argument("--opp-agent", choices=["ismcts", "heuristic"],
                   default="ismcts")
    p.add_argument("--opp-iterations", type=int, default=1000)
    p.add_argument("--matches", type=int, default=5)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--append", action="store_true")
    args = p.parse_args()

    if args.policy == "B" and args.max_seconds is None:
        p.error("--policy B requires --max-seconds")

    deck0 = _load_deck(args.my_deck)
    deck1 = _load_deck(args.opp_deck) if args.opp_deck else list(deck0)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    mode = "a" if args.append else "w"
    with args.out.open(mode) as fh:
        for i in range(args.matches):
            seed = args.seed_start + i
            row = run_match(args, deck0, deck1, seed)
            rows.append(row)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            flag = " FORFEIT" if row["forfeit"] else ""
            print(
                f"[{i + 1}/{args.matches}] seed={seed} "
                f"M={row['my_decisions']} cumulative={row['my_cumulative']}s "
                f"overage_left={row['my_final_overage']} "
                f"result={row['reward_0']}{flag}",
                flush=True,
            )

    summary = summarize(rows)
    print("\n" + json.dumps(summary, indent=2))
    if summary["cumulative_s"]["p99"] is not None:
        med = statistics.median([t for r in rows for t in r["my_decision_times"]]) \
            if any(r["my_decision_times"] for r in rows) else 0.0
        print(f"\nper-decision median {med:.3f}s @ {args.iterations} iters; "
              f"cumulative p99 {summary['cumulative_s']['p99']}s "
              f"(budget 540s); forfeits {summary['forfeits']}/{summary['n_games']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
