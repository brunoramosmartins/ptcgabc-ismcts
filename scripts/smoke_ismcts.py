"""Smoke test: one full ISMCTS-vs-heuristic match (Issue #19 DoD).

Verifies the whole stack end-to-end — determinize → search_begin →
four-phase loop → move mapping back to the real observation — by
playing exactly ONE local match. Prints per-decision wall time.

Pre-registration guardrail: this is a smoke test, not an experiment.
One match, outcome printed for debugging only, nothing recorded
anywhere. H1's benchmark run (EXP-003) happens only after the
`v0.3-hypotheses` lock.

    python scripts/smoke_ismcts.py [iterations]
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

from agents.heuristic_agent import HeuristicAgent  # noqa: E402
from agents.ismcts_agent import ISMCTSAgent  # noqa: E402


def read_obs(ptr: int) -> dict:
    sd = sim.lib.GetBattleData(ptr)
    o = json.loads(sd.json.decode())
    o["search_begin_input"] = ctypes.string_at(sd.data, sd.count).decode("ascii")
    o["_select_player"] = sd.selectPlayer
    return o


def main() -> int:
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]

    ismcts_seat = 0
    ismcts = ISMCTSAgent(
        my_deck_list=deck,
        opponent_deck_list=deck,          # mirror match: list known
        iterations=iterations,
        rng=random.Random(42),
    )
    heuristic = HeuristicAgent()

    cards = deck + deck
    arg = (ctypes.c_int * len(cards))(*cards)
    ptr = sim.lib.BattleStart(arg).battlePtr

    decision_times: list[float] = []
    decisions = 0
    while decisions < 3000:
        o = read_obs(ptr)
        if o["current"]["result"] != -1:
            break
        acting = o["_select_player"]
        if acting == ismcts_seat:
            t0 = time.perf_counter()
            choice = ismcts.choose(o)
            decision_times.append(time.perf_counter() - t0)
        else:
            choice = heuristic.choose(o)
        c_arr = (ctypes.c_int * len(choice))(*choice)
        err = sim.lib.Select(ptr, c_arr, len(choice))
        if err != 0:
            print(f"Select error {err} at decision {decisions} "
                  f"(acting={acting}, choice={choice})")
            break
        decisions += 1

    o = read_obs(ptr)
    result = o["current"]["result"]
    sim.lib.BattleFinish(ptr)

    print(f"\nmatch completed: {decisions} total decisions, "
          f"{len(decision_times)} by ISMCTS")
    print(f"result code: {result} (0/1 = winner seat, 2 = draw) "
          f"— smoke only, not recorded")
    print(f"fallbacks: {len(ismcts.fallback_events)}")
    for event in ismcts.fallback_events[:10]:
        print(f"  {event}")
    if decision_times:
        print(f"ISMCTS per-decision wall time @ {iterations} iterations:")
        print(f"  median {statistics.median(decision_times):.2f}s   "
              f"max {max(decision_times):.2f}s   "
              f"total {sum(decision_times):.1f}s")
        budget = 600 - 60  # 10-min match budget minus safety margin
        est = budget / max(statistics.median(decision_times), 1e-9)
        print(f"  → at this cost, ~{est:.0f} ISMCTS decisions fit in "
              f"a 9-minute budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
