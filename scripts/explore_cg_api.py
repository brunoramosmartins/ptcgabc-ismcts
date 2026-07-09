"""Phase 3 feasibility spike v2: probe the cg engine's search API.

Spike v1 findings (2026-07):

- The native lib exports a full search API: ``SearchBegin``,
  ``SearchStep``, ``SearchEnd``, ``SearchRelease`` — plus ``AgentStart``,
  ``AllCard``, ``AllAttack``.
- The cabt docs (matsuoinstitute.github.io/cabt/api.html) document the
  Python-level wrappers:
  ``search_begin(agent_observation, your_deck, your_prize,
  opponent_deck, opponent_prize, opponent_hand, opponent_active,
  manual_coin=False) -> SearchState`` — i.e. the CALLER supplies the
  determinization and the engine reconstructs a playable battle.
  ``search_step(search_id, select) -> SearchState``.
- Those Python wrappers (``cg/api.py``) are NOT shipped in
  kaggle-environments 1.30.2; only the native symbols are. The exact
  ctypes marshalling is the remaining unknown — acquired separately
  (see notes/phase3-implementation-plan.md), not blind-probed here,
  because a wrong signature can segfault.
- Two concurrent battles via manual ptr bookkeeping: confirmed working.
- v1's timing section had a bug: ``current.result`` is ``-1`` while the
  game is in progress (not None/"none"), so every game "ended" at step
  0. Fixed here.

Run and paste the full output:

    python scripts/explore_cg_api.py
"""

from __future__ import annotations

import ctypes
import json
import pathlib
import random
import statistics
import subprocess
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

RESULT_IN_PROGRESS = -1


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def load_deck() -> list[int]:
    return [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]


def main() -> int:  # noqa: PLR0915 - linear reconnaissance script
    section("0. Imports")
    from kaggle_environments.envs.cabt.cg import sim  # noqa: PLC0415

    lib = sim.lib
    print(f"loaded native lib: {sim.lib_path}")

    deck = load_deck()
    cards = deck + deck

    def new_battle() -> int:
        arg = (ctypes.c_int * len(cards))(*cards)
        return lib.BattleStart(arg).battlePtr

    def read_obs(ptr: int) -> dict:
        sd = lib.GetBattleData(ptr)
        o = json.loads(sd.json.decode())
        o["search_begin_input"] = ctypes.string_at(sd.data, sd.count).decode("ascii")
        o["_select_player"] = sd.selectPlayer
        return o

    section("1. Full random games — timing (v1 bug fixed)")
    rng = random.Random(7)

    def play_random_game(collect_blobs: bool = False):
        ptr = new_battle()
        steps = 0
        blobs: list[str] = []
        t0 = time.perf_counter()
        while True:
            o = read_obs(ptr)
            if o["current"]["result"] != RESULT_IN_PROGRESS:
                break
            sel = o.get("select")
            if sel is None:
                print(f"  select=None mid-game at step {steps} (unexpected)")
                break
            if collect_blobs:
                blobs.append(o["search_begin_input"])
            k = sel["maxCount"]
            n = len(sel["option"])
            choice = rng.sample(range(n), k)
            c_arr = (ctypes.c_int * len(choice))(*choice)
            err = lib.Select(ptr, c_arr, len(choice))
            if err != 0:
                print(f"  Select error {err} at step {steps}")
                break
            steps += 1
            if steps > 3000:
                print("  step cap hit")
                break
        dt = time.perf_counter() - t0
        result = read_obs(ptr)["current"]["result"]
        lib.BattleFinish(ptr)
        return steps, dt, result, blobs

    games = [play_random_game() for _ in range(10)]
    for i, (steps, dt, result, _) in enumerate(games):
        per = (dt / steps * 1000) if steps else float("nan")
        print(f"  game {i}: {steps:4d} decisions, {dt:6.3f}s "
              f"({per:6.2f} ms/decision), result={result}")
    ok = [(s, d) for s, d, _, _ in games if s > 0]
    if ok:
        print(f"  median decisions/game: {statistics.median(s for s, _ in ok)}")
        print(f"  median s/full-game:    {statistics.median(d for _, d in ok):.3f}")
        print(f"  median ms/decision:    "
              f"{statistics.median(d / s * 1000 for s, d in ok):.2f}")

    section("2. Does search_begin_input evolve during the game?")
    steps, _, _, blobs = play_random_game(collect_blobs=True)
    uniq = len(set(blobs))
    print(f"  {steps} decisions, {len(blobs)} blobs collected, {uniq} unique")
    if blobs:
        lens = sorted({len(b) for b in blobs})
        print(f"  blob lengths seen: {lens[:10]}")
        print(f"  first blob : {blobs[0][:80]!r}")
        if len(blobs) > 1:
            print(f"  last blob  : {blobs[-1][:80]!r}")

    section("3. Result-code census (what values does result take?)")
    results = [r for _, _, r, _ in games]
    print(f"  results across 10 games: {sorted(set(results))} "
          f"(counts: {[ (v, results.count(v)) for v in sorted(set(results)) ]})")

    section("4. AllCard / AllAttack probes (char* returns, per Export.cpp)")
    probe_template = r"""
import ctypes, json, sys
from kaggle_environments.envs.cabt.cg import sim
lib = sim.lib
lib.{fn}.restype = ctypes.c_char_p
lib.{fn}.argtypes = []
raw = lib.{fn}()
data = json.loads(raw.decode("utf-8"))
kind = type(data).__name__
size = len(data) if hasattr(data, '__len__') else 'n/a'
print(f"{fn}: json parsed ok, type={{kind}}, len={{size}}")
if isinstance(data, list) and data:
    print("first entry:", json.dumps(data[0])[:300])
"""
    for fn in ("AllCard", "AllAttack"):
        code = probe_template.replace("{fn}", fn)
        r = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=60,
        )
        status = "ok" if r.returncode == 0 else f"rc={r.returncode} (segfault if -11)"
        print(f"  {fn}: {status}")
        for line in (r.stdout or "").splitlines():
            print(f"    {line}")
        if r.returncode != 0 and r.stderr:
            print(f"    stderr: {r.stderr.splitlines()[-1][:200]}")

    section("5. Hidden-info surface at a mid-game decision")
    ptr = new_battle()
    for _ in range(20):
        o = read_obs(ptr)
        if o["current"]["result"] != RESULT_IN_PROGRESS or o.get("select") is None:
            break
        sel = o["select"]
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        c_arr = (ctypes.c_int * len(choice))(*choice)
        lib.Select(ptr, c_arr, len(choice))
    o = read_obs(ptr)
    me = o["current"]["yourIndex"]
    for label, p in (("me", o["current"]["players"][me]),
                     ("opp", o["current"]["players"][1 - me])):
        keys = {k: (len(v) if isinstance(v, list) else v)
                for k, v in p.items() if k in
                ("deckCount", "handCount", "hand", "prize", "discard",
                 "active", "bench")}
        print(f"  {label}: {keys}")
    lib.BattleFinish(ptr)

    section("DONE — paste everything above back into the chat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
