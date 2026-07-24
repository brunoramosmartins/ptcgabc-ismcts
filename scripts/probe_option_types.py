"""Confirm the engine's option-type codes before any H2 experiment.

`evaluator/option_types.py` holds provisional numeric codes; the move
scorer misfires silently if they're wrong. This probe plays random
games and prints, per distinct type code: occurrence count, the field
signatures seen, one sample payload, and game-phase context — enough
to lock every constant by inspection.

    python scripts/probe_option_types.py
"""

from __future__ import annotations

import ctypes
import json
import pathlib
import random
import sys
from collections import Counter, defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kaggle_environments.envs.cabt.cg import sim  # noqa: E402

rng = random.Random(5)
GAMES = 30


def main() -> int:
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]
    cards = deck + deck

    counts: Counter = Counter()
    fields: dict[int, set] = defaultdict(set)
    samples: dict[int, dict] = {}
    contexts: dict[int, Counter] = defaultdict(Counter)

    for _ in range(GAMES):
        arg = (ctypes.c_int * len(cards))(*cards)
        ptr = sim.lib.BattleStart(arg).battlePtr
        for _step in range(3000):
            sd = sim.lib.GetBattleData(ptr)
            o = json.loads(sd.json.decode())
            cur = o["current"]
            if cur["result"] != -1 or o.get("select") is None:
                break
            sel = o["select"]
            for opt in sel["option"]:
                t = opt.get("type")
                counts[t] += 1
                fields[t].add(tuple(sorted(k for k in opt if k != "type")))
                samples.setdefault(t, opt)
                phase = "setup" if cur["turn"] == 0 else "midgame"
                contexts[t][f"{phase}/sel.type={sel.get('type')}"] += 1
            ch = rng.sample(range(len(sel["option"])), sel["maxCount"])
            sim.lib.Select(ptr, (ctypes.c_int * len(ch))(*ch), len(ch))
        sim.lib.BattleFinish(ptr)

    print(f"{GAMES} random games; distinct option types: {sorted(counts)}\n")
    for t in sorted(counts):
        print(f"type {t}:  n={counts[t]}")
        for sig in sorted(fields[t]):
            print(f"    fields: {list(sig)}")
        print(f"    sample: {json.dumps(samples[t])[:160]}")
        top = contexts[t].most_common(3)
        print(f"    contexts: {top}")
        print()
    print("Compare against evaluator/option_types.py and fix any "
          "mismatch there before running EXP-006.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
