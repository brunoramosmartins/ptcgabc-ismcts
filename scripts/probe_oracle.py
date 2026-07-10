"""Probe: can we recover the TRUE hidden state for a cheating oracle?

The oracle-baseline-cheating-uct arm needs to feed the *real* hidden
assignment (opponent deck order, prizes, hand; our own deck order and
prizes) into `search_begin`, instead of a sampled determinization.
Before implementing it we must confirm we can actually obtain ground
truth locally. Two candidate sources:

1. Reading the *other* seat's observation via GetBattleData — during
   the game, does the engine let us read the opponent's private obs
   (their hand)? And do deck/prize orders appear anywhere?
2. visualize_data() — the renderer payload. Does it expose full deck
   orders and prize identities, or only the public log?

This script starts a battle, advances a few steps, and dumps what each
source reveals about the normally-hidden zones. Read the output to
decide whether a true oracle is feasible, or whether we can only build
a *partial* oracle (knows the opponent's hand+active but still samples
deck/prize order) — which would still be a useful upper-ish bound,
just not the pure Δ_ceiling.

    python scripts/probe_oracle.py
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

rng = random.Random(3)


def section(t: str) -> None:
    print(f"\n{'=' * 60}\n{t}\n{'=' * 60}")


def read_obs(ptr: int) -> dict:
    sd = sim.lib.GetBattleData(ptr)
    o = json.loads(sd.json.decode())
    o["_select_player"] = sd.selectPlayer
    return o


def hidden_summary(players: list, label: str) -> None:
    for i, p in enumerate(players):
        hand = p.get("hand") or []
        hand_ids = [c.get("id") for c in hand if isinstance(c, dict)]
        prize = p.get("prize") or []
        prize_ids = [c.get("id") for c in prize if isinstance(c, dict)]
        print(f"  {label} player[{i}]: handCount={p.get('handCount')} "
              f"hand_ids={hand_ids} | prize_n={len(prize)} "
              f"prize_ids_revealed={[x for x in prize_ids if x is not None]} "
              f"| deckCount={p.get('deckCount')}")


def main() -> int:
    deck = [int(x) for x in
            (REPO_ROOT / "decks" / "selected" / "deck.csv")
            .read_text().splitlines()[:60]]
    cards = deck + deck
    arg = (ctypes.c_int * len(cards))(*cards)
    ptr = sim.lib.BattleStart(arg).battlePtr

    for _ in range(8):
        o = read_obs(ptr)
        if o["current"]["result"] != -1 or o.get("select") is None:
            break
        sel = o["select"]
        ch = rng.sample(range(len(sel["option"])), sel["maxCount"])
        sim.lib.Select(ptr, (ctypes.c_int * len(ch))(*ch), len(ch))

    o = read_obs(ptr)
    active_seat = o["_select_player"]
    me = o["current"]["yourIndex"]

    section("1. The ACTIVE seat's observation — what's hidden?")
    print(f"  select_player={active_seat}  yourIndex={me}")
    hidden_summary(o["current"]["players"], "active-obs")
    print("  → In a normal obs: own hand has ids, opponent hand is "
          "count-only, prizes are face-down, deck order absent.")

    section("2. Does deck ORDER appear anywhere in the obs?")
    dump = json.dumps(o["current"])
    print(f"  current payload length: {len(dump)} chars")
    print(f"  contains 'deck' key with a list? "
          f"{'deck' in o['current'].get('players', [{}])[0]}")
    for i, p in enumerate(o["current"]["players"]):
        print(f"  player[{i}] keys: {sorted(p.keys())}")

    section("3. visualize_data() — renderer payload")
    sim.lib.VisualizeData.restype = ctypes.c_char_p
    sim.lib.VisualizeData.argtypes = [ctypes.c_void_p]
    raw = sim.lib.VisualizeData(ptr)
    if raw:
        vis = raw.decode("utf-8", errors="replace")
        print(f"  length: {len(vis)} chars")
        print(f"  first 600 chars:\n{vis[:600]}")
        # Does it carry deck-order or prize identities?
        for token in ("deck", "prize", "order", "hand"):
            print(f"  mentions {token!r}: {token in vis.lower()}")
    else:
        print("  VisualizeData returned NULL")

    section("4. Verdict inputs")
    print("  A TRUE oracle needs, for BOTH players: full deck order,")
    print("  prize identities, and (for opponent) the hand. Check")
    print("  above which of these is recoverable. If deck order is")
    print("  nowhere, a pure oracle isn't buildable from the obs —")
    print("  we'd need engine-internal access or a partial oracle.")

    sim.lib.BattleFinish(ptr)
    section("DONE — paste everything above back into the chat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
