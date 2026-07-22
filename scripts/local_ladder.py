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
import copy
import gzip
import json
import pathlib
import random
import sys
from collections.abc import Callable, Iterable

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

# Pinned to submissions/ismcts_main.py::FILLER_CARD. The `ismcts-filler`
# arm only means something if it fills hidden zones with the same card the
# ladder agent does; tests/test_local_ladder.py asserts they agree.
LADDER_FILLER_CARD = 1072  # Snorlax — a Basic, legal in the active slot


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


def _ismcts_filler_builder(seed: int, my_deck: list[int],
                           opp_deck: list[int], iterations: int) -> Agent:
    """ISMCTS under the *deployment* condition: opponent list unknown.

    Identical to `_ismcts_builder` in every respect except one — hidden
    opponent zones are filled with `LADDER_FILLER_CARD` instead of being
    sampled from their real list. That is exactly what
    `submissions/ismcts_main.py` does on the ladder, where we never see
    the opponent's deck.

    The point of the arm is the contrast: `ismcts` minus `ismcts-filler`
    on shared seeds is the price of not knowing the opponent's list
    (EXP-009). `opp_deck` is discarded on purpose — discarding it *is*
    the treatment, so the unused argument is the experiment, not an
    oversight.
    """
    del opp_deck  # the treatment: pretend we never saw it
    return ISMCTSAgent(
        my_deck_list=my_deck,
        opponent_deck_list=None,
        iterations=iterations,
        rng=random.Random(seed),
        filler_card=LADDER_FILLER_CARD,
    )


def _ismcts_selfdeck_builder(seed: int, my_deck: list[int],
                             opp_deck: list[int], iterations: int) -> Agent:
    """ISMCTS assuming the opponent plays *our own* deck (EXP-010 arm).

    Like `ismcts-filler`, the real opponent list is discarded — this is
    a deployable condition, no hidden knowledge. Unlike the filler, the
    hidden zones are modeled with a legal, coherent 60-card list (ours),
    so the simulated opponent has energy, trainers and attackers, and
    the search plans against a board that fights back. Wrong against a
    real field, but wrong-and-alive; EXP-009 showed impossible-and-dead
    costs ~30 pp. `opponent_list_is_assumed=True` relaxes opponent-side
    accounting so revealed foreign cards don't blow up the sampler.
    """
    del opp_deck  # deployable condition: we never see the real list
    return ISMCTSAgent(
        my_deck_list=my_deck,
        opponent_deck_list=list(my_deck),
        opponent_list_is_assumed=True,
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
    "ismcts-filler": _ismcts_filler_builder,   # EXP-009: deployment condition
    "ismcts-selfdeck": _ismcts_selfdeck_builder,  # EXP-010: assumed own list
    "ismcts-guided": _ismcts_guided_builder,   # H2 treatment arm
    "pimc": _pimc_builder,
    "oracle": _oracle_builder,   # LOCAL DIAGNOSTIC ONLY — never submit
}


def _load_deck(deck_path: pathlib.Path) -> list[int]:
    lines = deck_path.read_text().splitlines()
    return [int(lines[i]) for i in range(60)]


class TrajectoryRecorder:
    """Per-seat log of (observation, chosen action) for every real decision.

    Feeds the self-play training corpus (see `notes/open-ideas.md`,
    *trajectory-corpus*): with the terminal reward appended by
    `run_match`, each decision becomes one (obs, action, outcome) sample —
    the labelled data whose absence ADR-003 cited. Observations are
    deep-copied at record time because the engine may mutate the dict it
    hands the agent.

    Costs real serialization time per decision, so it must stay OFF for
    any experiment where wall-clock is part of the measurement (EXP-008
    style timing runs).
    """

    __slots__ = ("decisions",)

    def __init__(self) -> None:
        self.decisions: list[dict] = []

    def record(self, obs_dict: dict, action: list[int]) -> None:
        self.decisions.append(
            {"obs": copy.deepcopy(obs_dict), "action": list(action)}
        )


def _wrap_for_cabt(
    agent: Agent,
    deck: list[int],
    recorder: TrajectoryRecorder | None = None,
) -> Callable[[dict], list[int]]:
    """Bind an Agent to the `cabt`-facing `agent(obs) -> list[int]` contract.

    The deck-submission step is never recorded — it is not a decision.
    """

    def _fn(obs_dict: dict) -> list[int]:
        if obs_dict["select"] is None:
            return deck
        choice = agent.choose(obs_dict)
        if recorder is not None:
            recorder.record(obs_dict, choice)
        return choice

    return _fn


def _raise_overage_bank(env: object, overage_bank: float) -> None:
    """Raise the per-seat overage bank on a freshly made ``cabt`` env.

    Writing ``env.state`` or ``env.specification`` alone is NOT enough:
    ``env.run()`` always calls ``reset()`` on a fresh env, and the reset
    rebuilds each seat's state from per-position schema caches
    (``__state_schema_0``/``__state_schema_1``) that were built at
    ``make()`` time with the spec's 600 s default — silently restoring
    the old bank (EXP-011's second false start: TIMEOUT rows at ~600 s
    with the bank nominally raised to 100000). So this patches the live
    spec AND drops those caches, forcing the reset to regenerate them
    from the patched spec. The current state is patched too for
    completeness (any pre-reset reader sees the same value).

    In the in-memory spec ``remainingOverageTime`` is a full
    property-spec object (description/shared/type/minimum/default), not
    the bare number seen in ``cabt.json`` — the bank goes under its
    ``default`` key. Assigning a bare number replaces the object and
    corrupts the schema: the rebuild then fails metaschema validation
    (``100000.0 is not of type 'object'``), which is exactly how the
    first version of this fix died in the validation probe.
    """
    env.specification["observation"]["remainingOverageTime"]["default"] = overage_bank
    for position in range(len(env.state)):
        # Environment.__get_state caches via setattr with a literal
        # string, so the attribute name is NOT mangled.
        key = f"__state_schema_{position}"
        if hasattr(env, key):
            delattr(env, key)
    for side in env.state:
        side["observation"]["remainingOverageTime"] = overage_bank


def _make_cabt_env(seed: int, overage_bank: float) -> object:
    """Make the ``cabt`` env for one match.

    With the default 600 s bank the env is ladder-faithful and left
    untouched. A raised bank also unbinds ``runTimeout`` — the engine's
    2000 s wall-clock cap on the whole episode, enforced by
    ``Environment.run`` raising ``DeadlineExceeded`` (which aborts the
    sweep without writing a row, unlike the bank's TIMEOUT-loss path).
    EXP-011's third false start was this second limit: grindy
    emboar-evolution matches crossed 2000 s. Unlike the bank,
    ``runTimeout`` is honored from ``env.configuration`` directly, so
    passing it at ``make()`` time suffices — no schema-cache surgery.

    Args:
        seed: Engine ``randomSeed`` for the match.
        overage_bank: Per-seat thinking-time bank in seconds.

    Returns:
        A freshly made ``cabt`` environment.
    """
    from kaggle_environments import make

    configuration: dict[str, float | int] = {"randomSeed": seed}
    if overage_bank != 600.0:
        # The 600 s bank and the 2000 s runTimeout are *deployment*
        # constraints: the shipped agent budgets under them (Policy C)
        # and cannot overrun them by construction. The local
        # fixed-iteration arms never read the clock, so the defaults
        # can only kill long games by accident — TIMEOUT losses (bank)
        # or aborted sweeps (runTimeout) — never change a decision:
        # search is iteration-bounded and seeded. Two banks' worth
        # covers both seats, plus the original episode allowance.
        configuration["runTimeout"] = 2 * overage_bank + 2000.0
    env = make("cabt", debug=False, configuration=configuration)
    if overage_bank != 600.0:
        _raise_overage_bank(env, overage_bank)
    return env


def run_match(
    builder_a: AgentBuilder,
    builder_b: AgentBuilder,
    deck_a: list[int],
    deck_b: list[int],
    seed: int,
    iterations: int,
    record_trajectories: bool = False,
    overage_bank: float = 600.0,
) -> dict:
    """Play one match; returns per-match row including fallback details.

    With ``record_trajectories=True`` the row carries a ``_traj`` key
    (full per-decision observations and actions for both seats). The
    caller writes it to the trajectory sink and strips it before the
    row reaches the summary JSONL — the two files serve different
    consumers and must not be mixed.

    ``overage_bank`` is the per-seat thinking-time bank in seconds
    (default 600, the ladder's value). See ``--overage-bank`` in the CLI
    for when to raise it.
    """
    import time

    env = _make_cabt_env(seed, overage_bank)
    agent_a = builder_a(seed, deck_a, deck_b, iterations)
    agent_b = builder_b(seed, deck_b, deck_a, iterations)
    rec_a = TrajectoryRecorder() if record_trajectories else None
    rec_b = TrajectoryRecorder() if record_trajectories else None

    t0 = time.perf_counter()
    env.run([
        _wrap_for_cabt(agent_a, deck_a, rec_a),
        _wrap_for_cabt(agent_b, deck_b, rec_b),
    ])
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
    if record_trajectories:
        row["_traj"] = {
            "decisions_a": rec_a.decisions,
            "decisions_b": rec_b.decisions,
        }
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
    p.add_argument(
        "--log-trajectories",
        type=pathlib.Path,
        default=None,
        help="Gzipped JSONL sink for full per-decision trajectories "
             "(one line per match: every obs + chosen action for both "
             "seats + final rewards). Training-data collection for the "
             "learned-evaluator idea (open-ideas: trajectory-corpus). "
             "Adds serialization cost per decision — leave OFF for any "
             "timing-sensitive experiment. Honors --append.",
    )
    p.add_argument(
        "--overage-bank",
        type=float,
        default=600.0,
        help="Per-seat thinking-time bank in seconds (default 600 — the "
             "ladder's value; keep it for any ladder-faithful or "
             "timing-sensitive run). The fixed-iteration arms never read "
             "the clock, so under the default a slow cell can hit "
             "TIMEOUT and score an artifact loss; raise the bank (e.g. "
             "100000) for iteration-bounded experiments (EXP-011).",
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
    traj_file = None
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out_file = args.out.open("a" if args.append else "w")
    if args.log_trajectories is not None:
        args.log_trajectories.parent.mkdir(parents=True, exist_ok=True)
        # Append mode writes one gzip member per match; concatenated
        # members are a valid gzip stream, so resume works like --out.
        # Opened conditionally and closed in the `finally` below — a
        # `with` block cannot express the optional sink.
        traj_file = gzip.open(  # noqa: SIM115
            args.log_trajectories, "ab" if args.append else "wb"
        )
    try:
        for offset in range(args.matches):
            seed = args.seed_start + offset
            row = run_match(builder_a, builder_b, deck_a, deck_b, seed,
                            args.iterations,
                            record_trajectories=traj_file is not None,
                            overage_bank=args.overage_bank)
            row["agent_a"] = args.agent_a
            row["agent_b"] = args.agent_b
            traj = row.pop("_traj", None)
            if traj_file is not None and traj is not None:
                traj_line = {
                    "seed": seed,
                    "agent_a": args.agent_a,
                    "agent_b": args.agent_b,
                    "deck_a": deck_a,
                    "deck_b": deck_b,
                    "iterations": args.iterations,
                    "reward_a": row["reward_a"],
                    "reward_b": row["reward_b"],
                    **traj,
                }
                traj_file.write((json.dumps(traj_line) + "\n").encode())
                traj_file.flush()
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
        if traj_file is not None:
            traj_file.close()

    summary = summarize(rows)
    print(json.dumps(
        {"agent_a": args.agent_a, "agent_b": args.agent_b,
         "iterations": args.iterations, **summary},
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
