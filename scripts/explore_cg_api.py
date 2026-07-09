"""Phase 3 feasibility spike: what does the cg engine expose for search?

The whole Phase 3 architecture hinges on one question: how do we
simulate PTCG matches *inside* the ISMCTS loop? Three candidate paths,
from best to worst:

  A. The engine consumes ``obs["search_begin_input"]`` — the serialized
     blob it hands the agent at every decision — to reconstruct a
     battle mid-game. If a native export like ``BattleStartFromSearchInput``
     exists, determinization + forward simulation are engine-native and
     Phase 3 collapses to wiring.
  B. No mid-game reconstruction, but multiple concurrent battles are
     possible by managing ``battle_ptr`` handles manually. Then rollouts
     must replay from turn 1 (slow but possible) or we simulate with an
     approximate model.
  C. Neither works → we need our own forward model (out of scope for
     the deadline; would force a redesign).

This script probes all three plus timing. Run it and paste the full
output back:

    python scripts/explore_cg_api.py

Read-only reconnaissance — it starts/finishes local battles via the
bundled shared library, never touches Kaggle.
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


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def main() -> int:  # noqa: PLR0915 - linear reconnaissance script
    section("0. Imports")
    from kaggle_environments.envs.cabt.cg import game, sim  # noqa: PLC0415

    lib = sim.lib
    lib_path = sim.lib_path
    print(f"loaded native lib: {lib_path}")

    section("1. Native exports — candidate search/clone symbols")
    candidates = [
        "BattleStart", "BattleFinish", "GetBattleData", "Select",
        "VisualizeData", "GameInitialize",
        # hypothetical search hooks:
        "SearchBegin", "BeginSearch", "SearchBattleStart",
        "BattleStartFromSearchInput", "BattleStartSearch", "StartSearch",
        "SearchStart", "BattleResume", "ResumeBattle", "BattleClone",
        "CloneBattle", "BattleCopy", "CopyBattle", "SetBattleData",
        "LoadBattleData", "BattleLoad", "Simulate", "SimulateBattle",
    ]
    for name in candidates:
        try:
            getattr(lib, name)
            print(f"  EXPORTED : {name}")
        except AttributeError:
            print(f"  missing  : {name}")

    section("1b. Full dynamic symbol table (nm -D), if available")
    try:
        out = subprocess.run(
            ["nm", "-D", str(lib_path)],
            capture_output=True, text=True, timeout=30,
        )
        lines = [
            ln for ln in out.stdout.splitlines()
            if " T " in ln or " t " in ln
        ]
        print(f"  {len(lines)} defined symbols:")
        for ln in lines:
            print("   ", ln)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"  nm unavailable ({exc}); rely on section 1.")

    section("2. Start a battle; inspect the observation")
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]
    obs, start = game.battle_start(deck, deck)
    print(f"battle_ptr: {hex(start.battlePtr or 0)}")
    print(f"obs keys: {sorted(obs.keys())}")
    print(f"select keys: {sorted(obs['select'].keys()) if obs.get('select') else None}")
    print(f"current keys: {sorted(obs['current'].keys()) if obs.get('current') else None}")

    sbi = obs.get("search_begin_input")
    print(f"search_begin_input: type={type(sbi).__name__}, len={len(sbi) if sbi else 0}")
    if sbi:
        print(f"  first 120 chars: {sbi[:120]!r}")
        print(f"  charset sample: {sorted(set(sbi[:2000]))[:40]}")

    section("3. Can two battles coexist? (manual ptr bookkeeping)")
    ptr_a = start.battlePtr
    cards = deck + deck
    arg = (ctypes.c_int * len(cards))(*cards)
    start_b = lib.BattleStart(arg)
    ptr_b = start_b.battlePtr
    print(f"ptr_a={hex(ptr_a or 0)}  ptr_b={hex(ptr_b or 0)}  distinct={ptr_a != ptr_b}")
    if ptr_b:
        sd_a = lib.GetBattleData(ptr_a)
        sd_b = lib.GetBattleData(ptr_b)
        obs_a = json.loads(sd_a.json.decode())
        obs_b = json.loads(sd_b.json.decode())
        same_after_reads = obs_a.get("current") is not None and obs_b.get("current") is not None
        print(f"both battles readable after interleaved GetBattleData: {same_after_reads}")
        lib.BattleFinish(ptr_b)
        print("finished battle B; checking battle A still alive...")
        sd_a2 = lib.GetBattleData(ptr_a)
        print(f"battle A still readable: {sd_a2.json is not None}")

    section("4. Timing — full random games via raw ptr calls")
    rng = random.Random(7)

    def play_random_game() -> tuple[int, float]:
        arg2 = (ctypes.c_int * len(cards))(*cards)
        sd0 = lib.BattleStart(arg2)
        ptr = sd0.battlePtr
        steps = 0
        t0 = time.perf_counter()
        while True:
            sd = lib.GetBattleData(ptr)
            o = json.loads(sd.json.decode())
            if o.get("current", {}).get("result") is not None \
                    and o["current"]["result"] != "none":
                break
            sel = o.get("select")
            if sel is None:
                break
            k = sel["maxCount"]
            n = len(sel["option"])
            choice = rng.sample(range(n), k)
            c_arr = (ctypes.c_int * len(choice))(*choice)
            err = lib.Select(ptr, c_arr, len(choice))
            if err != 0:
                print(f"  Select error {err} at step {steps}")
                break
            steps += 1
            if steps > 2000:
                print("  step cap hit")
                break
        dt = time.perf_counter() - t0
        lib.BattleFinish(ptr)
        return steps, dt

    games = [play_random_game() for _ in range(5)]
    for i, (steps, dt) in enumerate(games):
        per_step = (dt / steps * 1000) if steps else float("nan")
        print(f"  game {i}: {steps} decisions in {dt:.3f}s "
              f"({per_step:.2f} ms/decision)")
    all_steps = [s for s, _ in games if s]
    all_dt = [d for _, d in games]
    if all_steps:
        print(f"  median decisions/game: {statistics.median(all_steps)}")
        print(f"  median s/full-game:    {statistics.median(all_dt):.3f}")

    section("5. Determinization surface — what does obs reveal?")
    sel = obs.get("select")
    if sel and sel.get("option"):
        print(f"first option repr: {json.dumps(sel['option'][0])[:200]}")
    cur = obs.get("current") or {}
    for key in sorted(cur.keys()):
        val = json.dumps(cur[key])
        print(f"  current[{key!r}] = {val[:160]}{'…' if len(val) > 160 else ''}")

    game.battle_finish()
    section("DONE — paste everything above back into the chat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
