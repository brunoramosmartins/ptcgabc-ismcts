"""Opponent-threat model — the F7 feature (open-ideas: threat-aware-evaluator).

Models the opponent in the *evaluator* instead of the simulation: for an
observation with opposing board $B$, the aggregate threat is

    T(obs) = max_{p in B} D(p, e_p + 1),

where $D(p, e)$ is the maximum printed damage Pokemon $p$ deals among
its moves whose energy cost is at most $e$, and $e_p$ is the energy
currently attached to $p$. Everything here is public information: card
moves come from the card CSV, board state from the observation. No
hidden zones are read.

Per the descope rule recorded in `notes/open-ideas.md`, this module
feeds exactly ONE scorer rule (F7 in `evaluator/heuristic.py`) with ONE
weight; constants are derived from our own card data, never transcribed
from public notebooks.

In-play entry schema (`{"id", "hp", "maxHp", "energies", ...}`, where
`hp` is REMAINING hit points and `len(energies)` is the attached count)
is confirmed against the EXP-010 trajectory corpus by
`scripts/probe_inplay_schema.py` — re-run it if the engine version
changes.

Two approximations with OPPOSITE directions, both accepted (exercise 4
of `exercises/ex04_evaluator_math.md` derives them):

- damage axis, floor: variable-damage moves ("100x", "50+") parse at
  their printed base, so T can miss part of a real threat;
- cost axis, ceiling: costs are counted color-blind, so a move whose
  colors the attached energy cannot actually pay may be admitted, and
  T can flag a threat that is not live next turn.

T is therefore a heuristic threat signal, not a bound. That is fine
for a preference rule with one weight — its net value is measured by
the H4 ablation, not assumed from the model being exact.
"""

from __future__ import annotations

import csv
import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_CSV = _REPO_ROOT / "data" / "kaggle" / "cards" / "EN_Card_Data.csv"

# Prize value by the CSV "Rule" label (canonical game rules: a plain
# Pokemon concedes 1 prize, an ex 2, a Mega ex 3).
_PRIZES_BY_RULE = {
    "Pokémon ex": 2,
    "Mega Pokémon ex": 3,
}


def _first_int(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else 0


def _cost_count(s: str) -> int:
    return len(re.findall(r"\{[A-Z+]\}", s or ""))


def load_threat_db(csv_path: pathlib.Path | str = DEFAULT_CSV) -> dict[int, dict]:
    """Load the per-card threat table from the Kaggle card CSV.

    The CSV is multi-row per card (one row per move). Parsing mirrors
    `scripts/analyze_card_pool.py::load_cards`, kept independent so the
    evaluator package never imports from `scripts/` (the submission
    bundle ships `evaluator/` without it).

    Args:
        csv_path: Path to `EN_Card_Data.csv`.

    Returns:
        Mapping card id -> {"prizes": int, "moves": [(cost, damage)]}.
        Cards without moves (Trainers, Energies) still get an entry with
        an empty move list, so lookups never distinguish "no card" from
        "no attack" incorrectly.
    """
    db: dict[int, dict] = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = _first_int(row["Card ID"])
            if cid not in db:
                db[cid] = {
                    "prizes": _PRIZES_BY_RULE.get(row["Rule"].strip(), 1),
                    "moves": [],
                }
            move = (row.get("Move Name") or "").strip()
            if move and move != "n/a":
                db[cid]["moves"].append(
                    (_cost_count(row.get("Cost", "")),
                     _first_int(row.get("Damage", "")))
                )
    return db


class ThreatModel:
    """Worst-case next-turn damage from the opponent's visible board.

    Args:
        db: Threat table as returned by `load_threat_db` (injectable so
            tests run on a tiny in-memory table).
    """

    def __init__(self, db: dict[int, dict]) -> None:
        self.db = db

    @classmethod
    def from_csv(cls, csv_path: pathlib.Path | str = DEFAULT_CSV) -> "ThreatModel":
        """Build the model from the card CSV (the production path)."""
        return cls(load_threat_db(csv_path))

    def max_damage(self, card_id: int, energies: int) -> int:
        r"""Maximum printed damage of ``card_id`` with ``energies`` attached.

        Parameters
        ----------
        card_id : int
            Card id of the in-play Pokemon.
        energies : int
            Number of attached energy cards (any type — costs are
            counted, not color-matched, which again over-admits and so
            keeps the threat estimate worst-case on the cost axis).

        Returns
        -------
        int
            :math:`D(p, e) = \max \{d : (c, d) \in \text{moves}(p),\; c \le e\}`,
            or 0 when no move is affordable or the card is unknown.
        """
        entry = self.db.get(card_id)
        if not entry:
            return 0
        affordable = [d for c, d in entry["moves"] if c <= energies]
        return max(affordable, default=0)

    def threat(self, obs: dict) -> int:
        r"""Aggregate threat :math:`T(\text{obs})` from the opposing board.

        Assumes every opposing in-play Pokemon attaches one more energy
        (the one-attachment-per-turn ceiling), takes the max over active
        and bench — worst case over their possible promotions.
        """
        cur = obs["current"]
        opp = cur["players"][1 - cur["yourIndex"]]
        best = 0
        for entry in (opp.get("active") or []) + (opp.get("bench") or []):
            if not isinstance(entry, dict):
                continue
            e_p = len(entry.get("energies") or [])
            best = max(best, self.max_damage(entry.get("id"), e_p + 1))
        return best

    def active_prizes(self, obs: dict) -> int:
        """Prizes our current active concedes if Knocked Out (1, 2 or 3)."""
        cur = obs["current"]
        mine = cur["players"][cur["yourIndex"]]
        active = mine.get("active") or []
        if not active or not isinstance(active[0], dict):
            return 1
        entry = self.db.get(active[0].get("id"))
        return entry["prizes"] if entry else 1

    def under_lethal_threat(self, obs: dict) -> bool:
        """True when our active's remaining HP is within T(obs).

        Remaining HP is the in-play entry's ``hp`` field (confirmed
        remaining, not max, by the corpus probe). No active — e.g.
        mid-promotion selects — reads as not threatened.
        """
        cur = obs["current"]
        mine = cur["players"][cur["yourIndex"]]
        active = mine.get("active") or []
        if not active or not isinstance(active[0], dict):
            return False
        hp = active[0].get("hp")
        if not isinstance(hp, int) or hp <= 0:
            return False
        return self.threat(obs) >= hp
