"""Discriminate why SearchBegin returned error 2 in the smoke test.

2x2 design: {setup decision, turn-2 decision} x {crude determinization,
consistent determinization}. The probe already showed (turn-2, crude)
works; the smoke test showed (setup, consistent) fails with engine
error 2. This script fills in the other two cells:

- If BOTH setup cells fail -> search is unsupported during the setup
  phase regardless of content (agent needs a setup fallback policy).
- If only (setup, consistent) fails -> our determinizer produces
  something the engine rejects, and the diff vs crude tells us what.

Run and paste the full output:

    python scripts/debug_search_begin.py
"""

from __future__ import annotations

import ctypes
import json
import pathlib
import random
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kaggle_environments.envs.cabt.cg import sim  # noqa: E402

from env.search_engine import (  # noqa: E402
    SearchApiError,
    expected_counts,
    search_begin,
    search_end,
)
from search.determinize import (  # noqa: E402
    DeterminizationError,
    sample_determinization,
    visible_cards,
)

SNORLAX, BASIC_ENERGY = 1072, 1
rng = random.Random(11)


def read_obs(ptr: int) -> dict:
    sd = sim.lib.GetBattleData(ptr)
    o = json.loads(sd.json.decode())
    o["search_begin_input"] = ctypes.string_at(sd.data, sd.count).decode("ascii")
    return o


def crude(obs: dict, deck: list[int]) -> dict:
    c = expected_counts(obs)
    return {
        "my_deck": rng.sample(deck, c["my_deck"]),
        "my_prize": rng.sample(deck, c["my_prize"]),
        "enemy_deck": [SNORLAX] * c["enemy_deck"],
        "enemy_prize": [BASIC_ENERGY] * c["enemy_prize"],
        "enemy_hand": [BASIC_ENERGY] * c["enemy_hand"],
        "enemy_active": [SNORLAX] * c["enemy_active"],
    }


def attempt(label: str, obs: dict, det: dict) -> None:
    try:
        state = search_begin(obs, **det)
        print(f"  {label}: OK (search_id={state['search_id']})")
        search_end()
    except SearchApiError as exc:
        print(f"  {label}: ENGINE ERROR {exc.code}")
    except (DeterminizationError, ValueError) as exc:
        print(f"  {label}: LOCAL ERROR — {exc}")


def describe(obs: dict, tag: str) -> None:
    cur = obs["current"]
    sel = obs.get("select") or {}
    opts = sel.get("option") or []
    types = sorted({o.get("type") for o in opts})
    mine, theirs = visible_cards(obs)
    print(f"\n--- {tag} ---")
    print(f"  turn={cur['turn']} yourIndex={cur['yourIndex']} "
          f"blob_len={len(obs['search_begin_input'])}")
    print(f"  counts={expected_counts(obs)}")
    print(f"  option types={types} (n={len(opts)}, "
          f"min={sel.get('minCount')}, max={sel.get('maxCount')})")
    print(f"  visible: mine={sum(mine.values())} theirs={sum(theirs.values())}")
    opp = cur["players"][1 - cur["yourIndex"]]
    print(f"  opp active={opp.get('active')!r:.80} bench_n={len(opp.get('bench') or [])}")


def main() -> int:
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]
    cards = deck + deck
    arg = (ctypes.c_int * len(cards))(*cards)
    ptr = sim.lib.BattleStart(arg).battlePtr

    # --- cell 1+2: the very first decision (setup) ----------------------
    o0 = read_obs(ptr)
    describe(o0, "SETUP decision (turn 0, first select)")
    attempt("setup + crude      ", o0, crude(o0, deck))
    try:
        det = sample_determinization(o0, deck, deck, random.Random(5))
        attempt("setup + consistent ", o0, det)
    except DeterminizationError as exc:
        print(f"  setup + consistent : DETERMINIZER ERROR — {exc}")

    # --- advance to a mid-game decision ---------------------------------
    for _ in range(6):
        o = read_obs(ptr)
        if o["current"]["result"] != -1 or o.get("select") is None:
            break
        sel = o["select"]
        choice = rng.sample(range(len(sel["option"])), sel["maxCount"])
        c_arr = (ctypes.c_int * len(choice))(*choice)
        sim.lib.Select(ptr, c_arr, len(choice))

    o2 = read_obs(ptr)
    describe(o2, "MID-GAME decision (after 6 random selects)")
    attempt("turn2 + crude      ", o2, crude(o2, deck))
    try:
        det = sample_determinization(o2, deck, deck, random.Random(5))
        attempt("turn2 + consistent ", o2, det)
    except DeterminizationError as exc:
        print(f"  turn2 + consistent : DETERMINIZER ERROR — {exc}")

    sim.lib.BattleFinish(ptr)
    print("\nDONE — paste everything above back into the chat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
