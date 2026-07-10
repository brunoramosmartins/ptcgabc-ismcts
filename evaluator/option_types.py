"""Engine option-type codes used by the move scorer.

PROVISIONAL — confirmed vs inferred. The engine encodes each legal
option as ``{"type": <int>, ...}``. Codes marked CONFIRMED were
directly observed in probe payloads; the rest are inferred from the
public notebook's OptionType case ordering and MUST be verified by
`scripts/probe_option_types.py` before any H2 experiment runs. If the
probe disagrees, fix the constants here — every consumer imports from
this module.

Observed evidence (probe_search_api / debug_search_begin, 2026-07):
- setup Yes/No select → options {"type": 1} / {"type": 2}
- hand energies → {"type": 8, "area": 2, "index": i, "inPlayArea": 4,
  "inPlayIndex": 0} (attach from HAND to ACTIVE)
- hand trainers → {"type": 7, "index": i} (play from hand)
- lone proceed option → {"type": 14}
"""

from __future__ import annotations

YES = 1            # CONFIRMED (setup Yes/No)
NO = 2             # CONFIRMED
ATTACK = 6         # INFERRED — verify (should carry "attackId")
PLAY = 7           # CONFIRMED (play a card from hand; "index" only)
ATTACH = 8         # CONFIRMED (energy: area/index → inPlayArea/inPlayIndex)
EVOLVE = 9         # INFERRED — verify (same field shape as ATTACH)
ABILITY = 10       # INFERRED — verify
RETREAT = 12       # INFERRED — verify (likely bare {"type": N})
END = 14           # CONFIRMED-ish (lone proceed option) — verify
