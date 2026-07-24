"""Confirm the in-play Pokemon entry schema that F7's threat model reads.

`evaluator/threat.py` reads three things from every in-play entry:
`id` (card id), `hp` (REMAINING hit points — not max), and `energies`
(list whose length is the attached-energy count). Those field names
were confirmed once against the EXP-010 trajectory corpus; this probe
re-verifies them across EVERY recorded decision so the confirmation is
reproducible and re-runnable after any engine update.

Unlike `probe_option_types.py` this probe needs no engine: the corpus
already holds full observations from real games (third payoff of
trajectory recording). It FAILS LOUDLY — non-zero exit — if any
assumption breaks or if no data is found, per the probe-check rule in
the registry (a check that prints OK on an empty input is worse than
no check).

    python scripts/probe_inplay_schema.py
"""

from __future__ import annotations

import glob
import gzip
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED_FIELDS = ("id", "hp", "maxHp", "energies")


def iter_inplay_entries(obs: dict):
    """Yield every in-play Pokemon entry (both seats, active + bench)."""
    cur = obs.get("current") or {}
    for player in cur.get("players") or []:
        for zone in ("active", "bench"):
            for entry in player.get(zone) or []:
                if isinstance(entry, dict):
                    yield entry


def check_entry(entry: dict) -> str | None:
    """Return a violation description, or None if the entry conforms."""
    for field in REQUIRED_FIELDS:
        if field not in entry:
            return f"missing field {field!r}: {sorted(entry)}"
    if not isinstance(entry["hp"], int) or not isinstance(entry["maxHp"], int):
        return f"non-int hp/maxHp: {entry['hp']!r}/{entry['maxHp']!r}"
    if entry["hp"] < 0 or entry["hp"] > entry["maxHp"]:
        # hp must be REMAINING points; hp > maxHp would mean it is not.
        return f"hp {entry['hp']} outside [0, maxHp={entry['maxHp']}]"
    if not isinstance(entry["energies"], list):
        return f"energies not a list: {type(entry['energies']).__name__}"
    return None


def main() -> int:
    files = sorted(glob.glob(str(REPO_ROOT / "results" / "*traj*.jsonl.gz")))
    if not files:
        print("FAIL: no trajectory corpus files under results/ — "
              "nothing was checked, which is not a pass.")
        return 1

    entries = decisions = games = 0
    damaged = 0          # entries with hp < maxHp: proof hp is remaining
    max_energies = 0
    ids: set[int] = set()
    for path in files:
        with gzip.open(path, "rt") as f:
            for line in f:
                row = json.loads(line)
                games += 1
                for side in ("decisions_a", "decisions_b"):
                    for dec in row.get(side) or []:
                        decisions += 1
                        for entry in iter_inplay_entries(dec.get("obs") or {}):
                            entries += 1
                            problem = check_entry(entry)
                            if problem:
                                print(f"FAIL: {pathlib.Path(path).name}: {problem}")
                                return 1
                            ids.add(entry["id"])
                            if entry["hp"] < entry["maxHp"]:
                                damaged += 1
                            max_energies = max(max_energies, len(entry["energies"]))

    if entries == 0:
        print(f"FAIL: {games} games scanned but 0 in-play entries found — "
              "the corpus shape itself no longer matches expectations.")
        return 1
    if damaged == 0:
        # Positive evidence required: with zero damaged entries we
        # cannot distinguish hp==remaining from hp==max.
        print(f"FAIL: {entries} entries and none with hp < maxHp — "
              "cannot confirm hp is REMAINING hit points.")
        return 1

    print(f"OK: {entries} in-play entries across {decisions} decisions "
          f"in {games} games ({len(files)} corpus files).")
    print(f"    fields {REQUIRED_FIELDS} present in all; "
          f"{damaged} damaged entries confirm hp = remaining; "
          f"max attached energies seen = {max_energies}; "
          f"{len(ids)} distinct card ids.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
