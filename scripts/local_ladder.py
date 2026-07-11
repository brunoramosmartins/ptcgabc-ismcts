"""Local head-to-head runner for internal baselines (Phase 1+).

Pits two agents against each other for N matches on paired seeds,
records one row per match, and reports the win rate with a Wilson 95%
CI. Used to gate Phase 1's "heuristic beats random" DoD (EXP-002a) and
Phase 3's H1 test (EXP-003, ISMCTS vs heuristic).

The runner respects `docs/benchmark-protocol.md`:

- Match seed and agent seed are pinned together (paired matches).
- Deterministic agents (HeuristicAgent) receive the seed but ignore it.
- Wilson CI is computed via `stats.wilson.wilson_interval`.
- ISMCTS fallback events (unsearchable decisions, see
  `agents/ismcts_agent.py`) are counted per match and summarized —
  a validity flag for any EXP that uses the ismcts arm.

Example (EXP-003 configuration):

    python scripts/local_ladder.py \\
        --agent-a ismcts \\
        --agent-b heuristic \\
        --matches 500 \\
        --seed-start 1 \\
        --iterations 1000 \\
        --out results/exp003_ismcts_vs_heuristic.jsonl

The script imports `kaggle_environments` lazily so that unit tests can
run without the SDK installed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
from typing import Callable, Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.base import Agent  # noqa: E402
from agents.heuristic_agent import HeuristicAgent  # noqa: E402
from agents.ismcts_agent import ISMCTSAgent  # noqa: E402
from agents.oracle_agent import OracleAgent  # noqa: E402
from agents.pimc_agent import PIMCAgent  # noqa: E402
from agents.random_agent import RandomAgent  # noqa: E402
from stats.wilson import wilson_interval  # noqa: E402

# Builder contract: (seed, my_deck, opp_deck, iterations) -> Agent.
# Locally BOTH lists are known (we set both seats), so search agents get
# the opponent's real list even in asymmetric matchups. Deterministic
# agents ignore what they don't need.
AgentBuilder = Callable[[int, list[int], list[int], int], Agent]


def _random_builder(seed: int, my_deck: list[int], opp_deck: list[int],
                    iterations: int) -> Agent:
    del my_deck, opp_deck, iterations
    return RandomAgent(rng=random.Random(seed))


def _heuristic_builder(seed: int, my_deck: list[int], opp_deck: list[int],
                       iterations: int) -> Agent:
    del seed, my_deck, opp_deck, iterations  # deterministic
    return HeuristicAgent()


def _ismcts_builder(seed: int, my_deck: list[int], opp_deck: list[int],
                    iterations: int) -> Agent:
    return ISMCTSAgent(
        my_deck_list=my_deck,
        opponent_deck_list=opp_deck,
        iterations=iterations,
        rng=random.Random(seed),
    )


def _pimc_builder(seed: int, my_deck: list[int], opp_deck: list[int],
                  iterations: int) -> Agent:
    return PIMCAgent(
        my_deck_list=my_deck,
        opponent_deck_list=opp_deck,
        iterations=iterations,
        rng=random.Random(seed),
    )


def _oracle_builder(seed: int, my_deck: list[int], opp_deck: list[int],
                    iterations: int) -> Agent:
    del my_deck, opp_deck  # the oracle reads the true state
    return OracleAgent(iterations=iterations, rng=random.Random(seed))


def _ismcts_guided_builder(seed: int, my_deck: list[int],
                           opp_deck: list[int], iterations: int) -> Agent:
    from evaluator.heuristic import MoveScorer
    from evaluator.rollout import make_guided_rollout
    from search.determinize import basic_pokemon_ids

    scorer = MoveScorer(basic_ids=basic_pokemon_ids())
    return ISMCTSAgent(
        my_deck_list=my_deck,
        opponent_deck_list=opp_deck,
        iterations=iterations,
        rng=random.Random(seed),
        rollout_policy=make_guided_rollout(scorer),
    )


AGENT_REGISTRY: dict[str, AgentBuilder] = {
    "random": _random_builder,
    "heuristic": _heuristic_builder,
    "ismcts": _ismcts_builder,
    "ismcts-guided": _ismcts_guided_builder,   # H2 treatment arm
    "pimc": _pimc_builder,
    "oracle": _oracle_builder,   # LOCAL DIAGNOSTIC ONLY — never submit
}


def _load_deck(deck_path: pathlib.Path) -> list[int]:
    lines = deck_path.read_text().splitlines()
    return [int(lines[i]) for i in range(60)]


def _wrap_for_cabt(agent: Agent, deck: list[int]) -> Callable[[dict], list[int]]:
    """Bind an Agent to the `cabt`-facing `agent(obs) -> list[int]` contract."""

    def _fn(obs_dict: dict) -> list[int]:
        if obs_dict["select"] is None:
            return deck
        return agent.choose(obs_dict)

    return _fn


def run_match(
    builder_a: AgentBuilder,
    builder_b: AgentBuilder,
    deck_a: list[int],
    deck_b: list[int],
    seed: int,
    iterations: int,
) -> dict:
    """Play one match; returns per-match row including fallback details."""
    import time

    from kaggle_environments import make

    env = make("cabt", debug=False, configuration={"randomSeed": seed})
    agent_a = builder_a(seed, deck_a, deck_b, iterations)
    agent_b = builder_b(seed, deck_b, deck_a, iterations)

    t0 = time.perf_counter()
    env.run([_wrap_for_cabt(agent_a, deck_a), _wrap_for_cabt(agent_b, deck_b)])
    seconds = time.perf_counter() - t0

    reward_a = env.state[0]["reward"]
    reward_b = env.state[1]["reward"]
    events_a = list(getattr(agent_a, "fallback_events", []))
    events_b = list(getattr(agent_b, "fallback_events", []))
    # A None reward means that side's agent crashed or timed out inside
    # the env (status ERROR/TIMEOUT/INVALID). Score the errored side as
    # the loser, flag the row, and keep the run alive — any errored
    # match invalidates the cell until the root cause is understood.
    if reward_a is None or reward_b is None:
        outcome = _sign((reward_b is None) - (reward_a is None))
    else:
        outcome = _sign(reward_a - reward_b)
    row = {
        "seed": seed,
        "reward_a": reward_a,
        "reward_b": reward_b,
        "outcome_for_a": outcome,
        "seconds": round(seconds, 2),
        "fallbacks_a": len(events_a),
        "fallbacks_b": len(events_b),
    }
    if reward_a is None or reward_b is None:
        row["env_error"] = True
        row["status_a"] = env.state[0].get("status")
        row["status_b"] = env.state[1].get("status")
    # Full event strings (turn + error) only when present — the
    # investigation trail for the EXP validity flag.
    if events_a:
        row["fallback_events_a"] = events_a
    if events_b:
        row["fallback_events_b"] = events_b
    return row


def _sign(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def summarize(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    n = len(rows)
    wins = sum(1 for r in rows if r["outcome_for_a"] == 1)
    draws = sum(1 for r in rows if r["outcome_for_a"] == 0)
    losses = n - wins - draws
    p_hat = wins / n if n > 0 else 0.0
    lo, hi = wilson_interval(wins, n) if n > 0 else (0.0, 0.0)
    return {
        "n": n,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": p_hat,
        "wilson_lo": lo,
        "wilson_hi": hi,
        "fallbacks_a_total": sum(r.get("fallbacks_a", 0) for r in rows),
        "fallbacks_b_total": sum(r.get("fallbacks_b", 0) for r in rows),
        "matches_with_fallbacks": sum(
            1 for r in rows
            if r.get("fallbacks_a", 0) or r.get("fallbacks_b", 0)
        ),
        "env_errors": sum(1 for r in rows if r.get("env_error")),
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--agent-a", required=True, choices=sorted(AGENT_REGISTRY))
    p.add_argument("--agent-b", required=True, choices=sorted(AGENT_REGISTRY))
    p.add_argument("--matches", type=int, default=200)
    p.add_argument("--seed-start", type=int, default=1)
    p.add_argument("--iterations", type=int, default=1000,
                   help="ISMCTS iterations per decision (ignored by "
                        "random/heuristic).")
    p.add_argument(
        "--deck",
        type=pathlib.Path,
        default=REPO_ROOT / "decks" / "selected" / "deck.csv",
        help="Deck for BOTH seats (mirror). Overridden per seat by "
             "--deck-a / --deck-b.",
    )
    p.add_argument("--deck-a", type=pathlib.Path, default=None)
    p.add_argument("--deck-b", type=pathlib.Path, default=None)
    p.add_argument(
        "--out",
        type=pathlib.Path,
        default=None,
        help="JSONL path for per-match rows (optional).",
    )
    p.add_argument(
        "--append",
        action="store_true",
        help="Append to --out instead of truncating (resume support).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    deck_a = _load_deck(args.deck_a or args.deck)
    deck_b = _load_deck(args.deck_b or args.deck)
    builder_a = AGENT_REGISTRY[args.agent_a]
    builder_b = AGENT_REGISTRY[args.agent_b]

    rows: list[dict] = []
    out_file = None
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out_file = args.out.open("a" if args.append else "w")
    try:
        for offset in range(args.matches):
            seed = args.seed_start + offset
            row = run_match(builder_a, builder_b, deck_a, deck_b, seed,
                            args.iterations)
            row["agent_a"] = args.agent_a
            row["agent_b"] = args.agent_b
            rows.append(row)
            if out_file is not None:
                out_file.write(json.dumps(row) + "\n")
                out_file.flush()
            if (offset + 1) % 25 == 0:
                s = summarize(rows)
                print(f"[{offset + 1}/{args.matches}] "
                      f"win_rate={s['win_rate']:.3f} "
                      f"wilson=[{s['wilson_lo']:.3f}, {s['wilson_hi']:.3f}] "
                      f"fallback_matches={s['matches_with_fallbacks']}",
                      flush=True)
    finally:
        if out_file is not None:
            out_file.close()

    summary = summarize(rows)
    print(json.dumps(
        {"agent_a": args.agent_a, "agent_b": args.agent_b,
         "iterations": args.iterations, **summary},
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
