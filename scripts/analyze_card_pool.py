"""Card-pool analysis for deck selection (Phase 4, ADR-002).

Parses `data/kaggle/cards/EN_Card_Data.csv` (multi-row per card: one
row per move), cross-checks ids against the engine's own card table
(`AllCard`, ground truth for legality), and prints the raw material
candidate decks are built from:

- pool totals by kind,
- top evolution FAMILIES ranked by end-stage damage/HP (the deck's
  attacker core is a family, not a card),
- top standalone Basics (HP/damage — the "no-evolution" archetype),
- rule-box cards (multi-prize risk/reward),
- trainer shortlist by effect keywords (draw / search / disruption).

    python scripts/analyze_card_pool.py

Paste the output back — candidates get designed from these tables.
"""

from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CSV_PATH = REPO_ROOT / "data" / "kaggle" / "cards" / "EN_Card_Data.csv"


def _to_int(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else 0


def _cost_count(s: str) -> int:
    return len(re.findall(r"\{[A-Z+]\}", s or ""))


def load_cards() -> dict[int, dict]:
    cards: dict[int, dict] = {}
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = _to_int(row["Card ID"])
            if cid not in cards:
                cards[cid] = {
                    "id": cid,
                    "name": row["Card Name"].strip(),
                    "kind": row["Stage (Pokémon)/Type (Energy and Trainer)"].strip(),
                    "rule": row["Rule"].strip(),
                    "prev": row["Previous stage"].strip(),
                    "hp": _to_int(row["HP"]),
                    "ptype": row["Type"].strip(),
                    "retreat": _to_int(row["Retreat"]),
                    "moves": [],
                    "effects": [],
                }
            move = row.get("Move Name", "").strip()
            if move and move != "n/a":
                cards[cid]["moves"].append({
                    "name": move,
                    "cost": _cost_count(row.get("Cost", "")),
                    "damage": _to_int(row.get("Damage", "")),
                })
            eff = (row.get("Effect Explanation") or "").strip()
            if eff:
                cards[cid]["effects"].append(eff)
    return cards


def engine_legal_ids() -> set[int] | None:
    try:
        from env.search_engine import all_card
        entries = all_card()
        ids = set()
        for e in entries:
            cid = e.get("cardId", e.get("id"))
            if isinstance(cid, int):
                ids.add(cid)
        return ids or None
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        print(f"(engine AllCard unavailable: {exc}; CSV-only mode)\n")
        return None


def best_damage(card: dict) -> tuple[int, int]:
    """(max damage, cost of that move)."""
    if not card["moves"]:
        return 0, 0
    mv = max(card["moves"], key=lambda m: m["damage"])
    return mv["damage"], mv["cost"]


def main() -> int:
    cards = load_cards()
    legal = engine_legal_ids()
    if legal is not None:
        dropped = [c for c in cards if c not in legal]
        if dropped:
            print(f"NOTE: {len(dropped)} CSV ids not in the engine table "
                  f"(first few: {sorted(dropped)[:8]}) — excluded.\n")
        cards = {k: v for k, v in cards.items() if k in legal}

    stages = ("Basic Pokémon", "Stage 1 Pokémon", "Stage 2 Pokémon")
    pokemon = {k: v for k, v in cards.items() if v["kind"] in stages}
    print(f"POOL: {len(cards)} cards | Pokémon {len(pokemon)} "
          f"(Basic {sum(1 for v in pokemon.values() if v['kind'] == stages[0])}, "
          f"S1 {sum(1 for v in pokemon.values() if v['kind'] == stages[1])}, "
          f"S2 {sum(1 for v in pokemon.values() if v['kind'] == stages[2])})")
    kinds = defaultdict(int)
    for v in cards.values():
        kinds[v["kind"]] += 1
    print("kinds:", dict(sorted(kinds.items(), key=lambda kv: -kv[1])))
    print()

    # --- evolution families ranked by end-stage punch -------------------
    by_name: dict[str, list[dict]] = defaultdict(list)
    for v in pokemon.values():
        by_name[v["name"]].append(v)

    def family_root(card: dict) -> str:
        seen = set()
        cur = card
        while cur["prev"] and cur["prev"] != "n/a" and cur["prev"] not in seen:
            seen.add(cur["prev"])
            nxt = by_name.get(cur["prev"])
            if not nxt:
                break
            cur = nxt[0]
        return cur["name"]

    families: dict[str, list[dict]] = defaultdict(list)
    for v in pokemon.values():
        families[family_root(v)].append(v)

    scored = []
    for root, members in families.items():
        top = max(members, key=lambda m: best_damage(m)[0])
        dmg, cost = best_damage(top)
        max_stage = max(stages.index(m["kind"]) for m in members)
        scored.append((dmg, top["hp"], root, top, cost, max_stage,
                       len(members)))
    scored.sort(reverse=True)

    print("TOP 12 EVOLUTION FAMILIES (by end-stage damage):")
    print(f"{'root':<18}{'top card':<22}{'stage':<8}{'dmg':>5}{'cost':>5}"
          f"{'HP':>5}  ids-in-family")
    for dmg, hp, root, top, cost, max_stage, n in scored[:12]:
        fam_ids = sorted(m["id"] for m in families[root])
        print(f"{root:<18}{top['name']:<22}{('B', 'S1', 'S2')[max_stage]:<8}"
              f"{dmg:>5}{cost:>5}{hp:>5}  {fam_ids}")
    print()

    # --- standalone basics ----------------------------------------------
    basics = [v for v in pokemon.values() if v["kind"] == stages[0]]
    basics.sort(key=lambda v: (best_damage(v)[0], v["hp"]), reverse=True)
    print("TOP 10 STANDALONE BASICS (damage, HP):")
    for v in basics[:10]:
        dmg, cost = best_damage(v)
        rule = f"  [{v['rule']}]" if v["rule"] not in ("", "n/a") else ""
        print(f"  {v['id']:>5}  {v['name']:<24} dmg {dmg:>3} cost {cost} "
              f"HP {v['hp']:>3} retreat {v['retreat']}{rule}")
    print()

    # --- rule-box cards ---------------------------------------------------
    rulebox = [v for v in pokemon.values() if v["rule"] not in ("", "n/a")]
    print(f"RULE-BOX POKÉMON: {len(rulebox)} (multi-prize risk/reward; "
          f"sample: {[v['name'] for v in rulebox[:6]]})")
    print()

    # --- trainers by role -------------------------------------------------
    trainers = {k: v for k, v in cards.items()
                if v["kind"] in ("Item", "Supporter", "Stadium",
                                 "Pokémon Tool")}
    roles = {
        "draw": r"draw ",
        "search-deck": r"search your deck",
        "energy-accel": r"attach.*energy",
        "disruption": r"(your opponent.*(shuffle|discard|switch))",
        "heal": r"heal",
        "switch": r"switch",
    }
    print("TRAINER SHORTLIST BY ROLE:")
    for role, pat in roles.items():
        hits = [v for v in trainers.values()
                if any(re.search(pat, e, re.I) for e in v["effects"])]
        names = [f"{v['name']}({v['id']},{v['kind'][:4]})" for v in hits[:8]]
        print(f"  {role:<14} n={len(hits):<3} {names}")
    print()
    print("Design candidates from these tables + your ladder-replay "
          "observations, then fill decks/candidates/ per the process "
          "note (notes/phase4-deck-selection.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
