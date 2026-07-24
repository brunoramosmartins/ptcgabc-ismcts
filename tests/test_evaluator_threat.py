"""Tests for evaluator/threat.py and the F7 rule in evaluator/heuristic.py.

In-play entry shapes mirror the EXP-010 trajectory corpus (confirmed by
scripts/probe_inplay_schema.py): {"id", "hp", "maxHp", "energies", ...}
with hp = REMAINING hit points and len(energies) = attached count.
"""

from __future__ import annotations

import pytest

from evaluator import option_types as ot
from evaluator.heuristic import MoveScorer
from evaluator.threat import DEFAULT_CSV, ThreatModel, load_threat_db

# Tiny in-memory threat table: ids are arbitrary, not real cards.
#   901 — plain attacker: 1-cost 30, 2-cost 90 (concedes 1 prize)
#   902 — Mega ex wall: 2-cost 100 (concedes 3 prizes)
#   903 — no moves at all
_DB = {
    901: {"prizes": 1, "moves": [(1, 30), (2, 90)]},
    902: {"prizes": 3, "moves": [(2, 100)]},
    903: {"prizes": 1, "moves": []},
}


def _inplay(cid: int, hp: int, max_hp: int, energies: int) -> dict:
    return {"id": cid, "hp": hp, "maxHp": max_hp,
            "energies": [3] * energies, "energyCards": [], "tools": []}


def _obs(my_active: dict | None, opp_active: dict | None,
         opp_bench: list[dict] | None = None) -> dict:
    return {
        "current": {
            "yourIndex": 0,
            "energyAttached": False,
            "players": [
                {"active": [my_active] if my_active else [],
                 "bench": [], "hand": []},
                {"active": [opp_active] if opp_active else [],
                 "bench": opp_bench or [], "hand": []},
            ],
        },
    }


# --- ThreatModel: D(p, e) ----------------------------------------------------

def test_max_damage_gates_on_energy_cost() -> None:
    tm = ThreatModel(_DB)
    assert tm.max_damage(901, 0) == 0
    assert tm.max_damage(901, 1) == 30
    assert tm.max_damage(901, 2) == 90
    assert tm.max_damage(901, 5) == 90


def test_max_damage_unknown_or_moveless_card_is_zero() -> None:
    tm = ThreatModel(_DB)
    assert tm.max_damage(903, 4) == 0
    assert tm.max_damage(999999, 4) == 0


# --- ThreatModel: T(obs) -----------------------------------------------------

def test_threat_assumes_one_more_energy() -> None:
    tm = ThreatModel(_DB)
    # 901 with 1 attached: with the +1 assumption its 2-cost 90 is live.
    obs = _obs(_inplay(901, 100, 100, 0), _inplay(901, 100, 100, 1))
    assert tm.threat(obs) == 90


def test_threat_is_max_over_active_and_bench() -> None:
    tm = ThreatModel(_DB)
    obs = _obs(
        _inplay(901, 100, 100, 0),
        _inplay(901, 100, 100, 0),                 # active: 30 with +1
        opp_bench=[_inplay(902, 200, 200, 1)],     # bench Mega: 100 with +1
    )
    assert tm.threat(obs) == 100


def test_under_lethal_threat_compares_remaining_hp() -> None:
    tm = ThreatModel(_DB)
    opp = _inplay(902, 200, 200, 1)  # threatens 100
    hurt = _obs(_inplay(902, 80, 350, 5), opp)    # 80 remaining <= 100
    fresh = _obs(_inplay(902, 350, 350, 5), opp)  # 350 remaining > 100
    assert tm.under_lethal_threat(hurt)
    assert not tm.under_lethal_threat(fresh)


def test_no_active_reads_as_not_threatened() -> None:
    tm = ThreatModel(_DB)
    assert not tm.under_lethal_threat(_obs(None, _inplay(902, 200, 200, 5)))


def test_active_prizes_from_rule_label() -> None:
    tm = ThreatModel(_DB)
    assert tm.active_prizes(_obs(_inplay(901, 50, 50, 0), None)) == 1
    assert tm.active_prizes(_obs(_inplay(902, 50, 200, 0), None)) == 3


# --- F7 in the MoveScorer ----------------------------------------------------

def _retreat_and_attack_scores(scorer: MoveScorer, obs: dict) -> tuple[float, float]:
    return (scorer.score({"type": ot.RETREAT}, obs),
            scorer.score({"type": ot.ATTACK, "attackId": 1}, obs))


def test_f7_mega_active_retreats_out_of_lethal() -> None:
    s = MoveScorer(threat=ThreatModel(_DB))
    obs = _obs(_inplay(902, 80, 350, 5), _inplay(902, 200, 200, 1))
    retreat, attack = _retreat_and_attack_scores(s, obs)
    # F6 (-1) + F7 (+3 prizes) = +2 beats ATTACK's +1.
    assert retreat > attack


def test_f7_plain_active_still_trades() -> None:
    s = MoveScorer(threat=ThreatModel(_DB))
    obs = _obs(_inplay(901, 20, 100, 1), _inplay(902, 200, 200, 1))
    retreat, attack = _retreat_and_attack_scores(s, obs)
    # F6 (-1) + F7 (+1 prize) = 0: a 1-prize attacker keeps attacking.
    assert attack > retreat


def test_f7_inert_without_threat_or_when_disabled() -> None:
    obs = _obs(_inplay(902, 80, 350, 5), _inplay(902, 200, 200, 1))
    no_model = MoveScorer()
    disabled = MoveScorer(threat=ThreatModel(_DB), disabled={"F7"})
    for s in (no_model, disabled):
        assert s.score({"type": ot.RETREAT}, obs) == -1.0  # F6 only


def test_f7_silent_when_no_lethal_threat() -> None:
    s = MoveScorer(threat=ThreatModel(_DB))
    obs = _obs(_inplay(902, 350, 350, 5), _inplay(902, 200, 200, 1))
    assert s.score({"type": ot.RETREAT}, obs) == -1.0  # F6 only


# --- CSV loader against the real pool ---------------------------------------

def test_load_threat_db_real_csv() -> None:
    if not DEFAULT_CSV.exists():
        pytest.skip("card CSV not present")
    db = load_threat_db()
    mega_abomasnow = db[723]  # Mega Abomasnow ex — our own active
    assert mega_abomasnow["prizes"] == 3
    # Hammer-lanche: {W}{W} for printed base 100 (the "100x" floor).
    assert (2, 100) in mega_abomasnow["moves"]
    # Basic {W} Energy (id 3): no moves, 1 prize, present in the table.
    assert db[3]["moves"] == []
    assert db[3]["prizes"] == 1
