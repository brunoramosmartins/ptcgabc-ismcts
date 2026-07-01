"""Local round-robin runner for internal baselines (Phase 1+).

Pits two agents against each other for N matches on paired seeds, records
one row per match, and reports the win rate with a Wilson 95% CI. Used to
gate the "heuristic beats random by a CI-separated margin" Phase 1
Definition of Done and to smoke-test any future agent before Kaggle
upload.

The runner respects `docs/benchmark-protocol.md`:

- Match seed and agent seed are pinned together (paired matches).
- Deterministic agents (HeuristicAgent) receive the seed but ignore it.
- Wilson CI is computed via `stats.wilson.wilson_interval`.

Example:

    python scripts/local_ladder.py \\
        --agent-a heuristic \\
        --agent-b random \\
        --matches 200 \\
        --seed-start 1 \\
        --out results/heuristic_vs_random.jsonl

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
from agents.random_agent import RandomAgent  # noqa: E402
from stats.wilson import wilson_interval  # noqa: E402


AgentFactory = Callable[[int], Agent]


def _random_factory(seed: int) -> Agent:
    return RandomAgent(rng=random.Random(seed))


def _heuristic_factory(seed: int) -> Agent:
    del seed  # deterministic; parameter kept for a uniform factory signature
    return HeuristicAgent()


AGENT_REGISTRY: dict[str, AgentFactory] = {
    "random": _random_factory,
    "heuristic": _heuristic_factory,
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
    factory_a: AgentFactory,
    factory_b: AgentFactory,
    deck: list[int],
    seed: int,
) -> dict:
    """Play one match; return {seed, reward_a, reward_b, outcome_for_a}.

    outcome_for_a ∈ {-1, 0, +1} follows sign of (reward_a - reward_b).
    """
    from kaggle_environments import make

    env = make("cabt", debug=False, configuration={"randomSeed": seed})
    agent_a = _wrap_for_cabt(factory_a(seed), deck)
    agent_b = _wrap_for_cabt(factory_b(seed), deck)

    env.run([agent_a, agent_b])

    reward_a = env.state[0]["reward"]
    reward_b = env.state[1]["reward"]
    return {
        "seed": seed,
        "reward_a": reward_a,
        "reward_b": reward_b,
        "outcome_for_a": _sign(reward_a - reward_b),
    }


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
    p.add_argument(
        "--deck",
        type=pathlib.Path,
        default=REPO_ROOT / "decks" / "selected" / "deck.csv",
    )
    p.add_argument(
        "--out",
        type=pathlib.Path,
        default=None,
        help="JSONL path for per-match rows (optional).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    deck = _load_deck(args.deck)
    factory_a = AGENT_REGISTRY[args.agent_a]
    factory_b = AGENT_REGISTRY[args.agent_b]

    rows: list[dict] = []
    for offset in range(args.matches):
        seed = args.seed_start + offset
        row = run_match(factory_a, factory_b, deck, seed)
        row["agent_a"] = args.agent_a
        row["agent_b"] = args.agent_b
        rows.append(row)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")

    summary = summarize(rows)
    print(json.dumps({"agent_a": args.agent_a, "agent_b": args.agent_b, **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
