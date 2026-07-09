"""Probe the native search API end-to-end with real signatures.

Signatures come from the engine's Export.cpp (see
`env/search_engine.py`); the one remaining unknown is the JSON schema
returned by SearchBegin/SearchStep. This script starts a battle, plays
a few random moves, opens a search with a notebook-style crude
determinization (own cards sampled from the deck list, opponent filled
with dummies — schema discovery only, NOT our real determinizer), and
prints everything.

Run and paste the full output:

    python scripts/probe_search_api.py
"""

from __future__ import annotations

import ctypes
import json
import pathlib
import random
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kaggle_environments.envs.cabt.cg import sim  # noqa: E402

from env.search_engine import (  # noqa: E402
    expected_counts, search_begin, search_end, search_step,
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


def main() -> int:
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]
    cards = deck + deck
    arg = (ctypes.c_int * len(cards))(*cards)
    ptr = sim.lib.BattleStart(arg).battlePtr

    section("1. Advance the real battle a few random steps")
    for i in range(6):
        o = read_obs(ptr)
        if o["current"]["result"] != -1 or o.get("select") is None:
            break
        sel = o["select"]
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        c_arr = (ctypes.c_int * len(choice))(*choice)
        sim.lib.Select(ptr, c_arr, len(choice))
    o = read_obs(ptr)
    print(f"turn={o['current']['turn']}  yourIndex={o['current']['yourIndex']}  "
          f"blob_len={len(o['search_begin_input'])}")
    counts = expected_counts(o)
    print(f"expected determinization counts: {counts}")

    section("2. SearchBegin with a crude (schema-probe) determinization")
    payload = search_begin(
        o,
        my_deck=rng.sample(deck, counts["my_deck"]),
        my_prize=rng.sample(deck, counts["my_prize"]),
        enemy_deck=[SNORLAX] * counts["enemy_deck"],
        enemy_prize=[BASIC_ENERGY] * counts["enemy_prize"],
        enemy_hand=[BASIC_ENERGY] * counts["enemy_hand"],
        enemy_active=[SNORLAX] * counts["enemy_active"],
    )
    print(f"top-level keys: {sorted(payload.keys())}")
    print("raw payload (first 1500 chars):")
    print(json.dumps(payload)[:1500])

    def find_search_id(d: dict):
        for k in ("searchId", "search_id", "id"):
            if k in d:
                return d[k], k
        return None, None

    sid, key = find_search_id(payload)
    print(f"\nsearch id: {sid} (key: {key!r})")
    sel = payload.get("select") or (payload.get("observation") or {}).get("select")
    print(f"select present: {sel is not None}; "
          f"options: {len(sel['option']) if sel else 'n/a'}")

    if sid is None or sel is None:
        section("ABORT — schema differs from expectation; paste output")
        return 1

    section("3. SearchStep x3 + timing")
    t0 = time.perf_counter()
    steps = 0
    for _ in range(3):
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        payload = search_step(sid, choice)
        sid2, _ = find_search_id(payload)
        sel = payload.get("select") or (payload.get("observation") or {}).get("select")
        cur = payload.get("current") or (payload.get("observation") or {}).get("current")
        result = cur["result"] if cur else "?"
        print(f"  step: id {sid} -> {sid2}, result={result}, "
              f"options={len(sel['option']) if sel else None}")
        steps += 1
        if sid2 is None or sel is None:
            break
        sid = sid2
    dt = time.perf_counter() - t0
    print(f"  {steps} steps in {dt * 1000:.2f} ms "
          f"({dt / max(steps, 1) * 1000:.2f} ms/step)")

    section("4. Rollout to terminal inside the search + timing")
    t0 = time.perf_counter()
    n = 0
    while n < 2000:
        cur = payload.get("current") or (payload.get("observation") or {}).get("current")
        sel = payload.get("select") or (payload.get("observation") or {}).get("select")
        if cur and cur["result"] != -1:
            print(f"  terminal after {n} steps: result={cur['result']}")
            break
        if sel is None:
            print(f"  select=None at step {n} (non-terminal?) — paste output")
            break
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        payload = search_step(sid, choice)
        sid, _ = find_search_id(payload)
        n += 1
    dt = time.perf_counter() - t0
    print(f"  rollout: {n} steps in {dt:.3f}s "
          f"({dt / max(n, 1) * 1000:.2f} ms/step)")

    search_end()
    print("SearchEnd ok")

    section("5. Is the REAL battle still intact after searching?")
    o2 = read_obs(ptr)
    print(f"real battle readable: turn={o2['current']['turn']}, "
          f"result={o2['current']['result']} (should match section 1)")
    sim.lib.BattleFinish(ptr)

    section("DONE — paste everything above back into the chat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
