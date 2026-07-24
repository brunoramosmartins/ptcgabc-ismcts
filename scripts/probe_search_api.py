"""Probe the native search API end-to-end (v2 — schema confirmed).

v1 discovered the payload schema:
``{"error": code, "state": {"observation": {...}, "searchId": id}}``
and proved SearchBegin injects the caller's determinization (the
sampled prizes appeared verbatim in the returned state). v2 runs
against the normalized wrapper in `env/search_engine.py` and answers
the two remaining questions automatically:

1. ms per `search_step` — the number that budgets simulations per
   decision (H3).
2. Does the real battle survive a search session untouched?

Run and paste the full output:

    python scripts/probe_search_api.py
"""

from __future__ import annotations

import ctypes
import json
import pathlib
import random
import statistics
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kaggle_environments.envs.cabt.cg import sim  # noqa: E402

from env.search_engine import (  # noqa: E402
    expected_counts,
    search_begin,
    search_end,
    search_step,
)

SNORLAX, BASIC_ENERGY = 1072, 1
rng = random.Random(11)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def read_obs(ptr: int) -> dict:
    sd = sim.lib.GetBattleData(ptr)
    o = json.loads(sd.json.decode())
    o["search_begin_input"] = ctypes.string_at(sd.data, sd.count).decode("ascii")
    return o


def crude_determinization(obs: dict, deck: list[int]) -> dict:
    """Notebook-style filler — schema/timing probe only, not our sampler."""
    c = expected_counts(obs)
    return {
        "my_deck": rng.sample(deck, c["my_deck"]),
        "my_prize": rng.sample(deck, c["my_prize"]),
        "enemy_deck": [SNORLAX] * c["enemy_deck"],
        "enemy_prize": [BASIC_ENERGY] * c["enemy_prize"],
        "enemy_hand": [BASIC_ENERGY] * c["enemy_hand"],
        "enemy_active": [SNORLAX] * c["enemy_active"],
    }


def rollout_to_terminal(state: dict, cap: int = 3000) -> tuple[int, float, int]:
    """Random rollout inside the search; returns (steps, seconds, result)."""
    sid, obs = state["search_id"], state["observation"]
    steps = 0
    t0 = time.perf_counter()
    while steps < cap:
        cur = obs["current"]
        if cur["result"] != -1:
            return steps, time.perf_counter() - t0, cur["result"]
        sel = obs["select"]
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        nxt = search_step(sid, choice)
        sid, obs = nxt["search_id"], nxt["observation"]
        steps += 1
    return steps, time.perf_counter() - t0, -1


def main() -> int:
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]
    cards = deck + deck
    arg = (ctypes.c_int * len(cards))(*cards)
    ptr = sim.lib.BattleStart(arg).battlePtr

    section("1. Advance the real battle a few random steps")
    for _ in range(6):
        o = read_obs(ptr)
        if o["current"]["result"] != -1 or o.get("select") is None:
            break
        sel = o["select"]
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        c_arr = (ctypes.c_int * len(choice))(*choice)
        sim.lib.Select(ptr, c_arr, len(choice))
    o = read_obs(ptr)
    real_turn = o["current"]["turn"]
    print(f"turn={real_turn}  yourIndex={o['current']['yourIndex']}  "
          f"blob_len={len(o['search_begin_input'])}")
    print(f"expected counts: {expected_counts(o)}")

    section("2. SearchBegin — normalized wrapper")
    state = search_begin(o, **crude_determinization(o, deck))
    print(f"search_id: {state['search_id']}")
    inner = state["observation"]
    print(f"observation keys: {sorted(inner.keys())}")
    print(f"select options: {len(inner['select']['option'])}, "
          f"turn={inner['current']['turn']}, "
          f"result={inner['current']['result']}")

    section("3. Rollouts to terminal inside one search session")
    rollouts = []
    for i in range(5):
        st = search_begin(o, **crude_determinization(o, deck)) if i else state
        steps, dt, result = rollout_to_terminal(st)
        per = dt / steps * 1000 if steps else float("nan")
        print(f"  rollout {i}: {steps:4d} steps, {dt:6.3f}s "
              f"({per:5.2f} ms/step), result={result}")
        rollouts.append((steps, dt))
    good = [(s, d) for s, d in rollouts if s > 0]
    if good:
        med_steps = statistics.median(s for s, _ in good)
        med_ms = statistics.median(d / s * 1000 for s, d in good)
        med_s = statistics.median(d for _, d in good)
        print(f"  median: {med_steps} steps/rollout, {med_ms:.2f} ms/step, "
              f"{med_s:.3f} s/rollout")
        print(f"  → rollouts per 10s decision budget: ~{10 / med_s:.0f}")

    search_end()
    print("SearchEnd ok")

    section("4. Is the REAL battle intact after searching?")
    o2 = read_obs(ptr)
    print(f"turn={o2['current']['turn']} (was {real_turn}), "
          f"result={o2['current']['result']} — "
          f"{'INTACT' if o2['current']['turn'] == real_turn else 'CORRUPTED'}")
    sim.lib.BattleFinish(ptr)

    section("DONE — paste everything above back into the chat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
