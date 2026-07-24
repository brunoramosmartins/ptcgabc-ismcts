"""Move scorer — the H2/H4 evaluator (design: notes/phase4-evaluator-design.md).

Scores a legal option directly from its content (move-prior scoring,
architecture (b) in the design note). Seven ablatable rules F1..F7,
uniform weights 1.0 (author decision, cleaner H4 interpretation). The
H4 ablation drops rules via the `disabled` set.

F7 (added 2026-07-23, design note "F7 intake" section) is the
threat-aware rule from `notes/open-ideas.md::threat-aware-evaluator`:
prefer RETREAT out of a worst-case lethal threat, weighted by the
prizes our active would concede. It is the one v1 exception to the
"no damage math" rule — the math lives in `evaluator/threat.py` and
uses public card data only.

Type codes come from `evaluator/option_types.py` (confirmed by
`scripts/probe_option_types.py`). Where a field signature is decisive
we prefer it over the numeric code (ATTACK via "attackId").
"""

from __future__ import annotations

from evaluator import option_types as ot
from evaluator.threat import ThreatModel

FEATURES = ("F1", "F2", "F3", "F4", "F5", "F6", "F7")

_W = 1.0  # uniform v1 weights per design decision 3


class MoveScorer:
    """Weighted rule-based option scoring; rules ablatable for H4.

    Args:
        basic_ids: Card ids of Basic Pokémon (for F4); reuse
            `search.determinize.basic_pokemon_ids()`. Empty set
            disables F4's Basic check gracefully.
        disabled: Feature names ("F1".."F7") to drop — the H4 knob.
        threat: `ThreatModel` for F7. ``None`` leaves F7 inert (same
            graceful degradation as an empty ``basic_ids`` for F4).
    """

    def __init__(
        self,
        basic_ids: set[int] | None = None,
        disabled: set[str] | None = None,
        threat: ThreatModel | None = None,
    ) -> None:
        self.basic_ids = basic_ids or set()
        self.disabled = disabled or set()
        self.threat = threat
        unknown = self.disabled - set(FEATURES)
        if unknown:
            raise ValueError(f"unknown features to disable: {unknown}")

    def _on(self, feature: str) -> bool:
        return feature not in self.disabled

    def score(self, option: dict, obs: dict) -> float:
        """Score one option in the context of the observation."""
        cur = obs["current"]
        me = cur["yourIndex"]
        mine = cur["players"][me]
        t = option.get("type")
        s = 0.0

        # F1 — prefer ATTACK (attackId is the decisive signature).
        if self._on("F1") and ("attackId" in option or t == ot.ATTACK):
            s += _W

        # F2 — prefer ATTACH while no energy attached this turn.
        if self._on("F2") and t == ot.ATTACH and not cur.get("energyAttached"):
            s += _W

        # F3 — prefer EVOLVE.
        if self._on("F3") and t == ot.EVOLVE:
            s += _W

        # F4 — prefer PLAYing a Basic from hand while bench is thin.
        if self._on("F4") and t == ot.PLAY and len(mine.get("bench") or []) < 2:
            hand = mine.get("hand") or []
            idx = option.get("index")
            if isinstance(idx, int) and 0 <= idx < len(hand):
                card = hand[idx]
                cid = card.get("id") if isinstance(card, dict) else None
                if cid in self.basic_ids:
                    s += _W

        # F6 — penalize RETREAT by default.
        if self._on("F6") and t == ot.RETREAT:
            s -= _W

        # F7 — prefer RETREAT out of a worst-case lethal threat, scaled
        # by the prizes our active concedes (1/2/3). With F6 active the
        # net is prizes−1: a plain attacker still trades (attack keeps
        # winning the tie), an ex/Mega ex active retreats — the
        # prize-trade management the rule exists for. Gated on RETREAT
        # first so the threat computation runs at most once per select.
        if (self._on("F7") and t == ot.RETREAT and self.threat is not None
                and self.threat.under_lethal_threat(obs)):
            s += _W * self.threat.active_prizes(obs)

        return s

    def score_all(self, options: list[dict], obs: dict) -> list[float]:
        """Scores for every option; applies F5 (END penalty) globally.

        F5: END scores -1 when any other option has a positive score —
        passing with value on the table is the classic random-rollout
        failure the rule exists to prevent.
        """
        scores = [self.score(o, obs) for o in options]
        if self._on("F5"):
            any_positive = any(
                sc > 0 for o, sc in zip(options, scores, strict=True)
                if o.get("type") != ot.END
            )
            if any_positive:
                for i, o in enumerate(options):
                    if o.get("type") == ot.END:
                        scores[i] -= _W
        return scores
