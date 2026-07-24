"""Engine option-type codes used by the move scorer.

CONFIRMED by `scripts/probe_option_types.py` (30 random games,
2026-07-10) — every code below was either directly observed with its
field signature or is marked as never-observed. If the engine version
changes, re-run the probe.

Observed signatures:

| code | fields                                       | meaning        |
|------|----------------------------------------------|----------------|
| 0    | number                                       | NUMBER pick    |
| 1    | (bare)  — setup Yes/No selects               | YES            |
| 2    | (bare)                                       | NO             |
| 3    | area, index, playerIndex                     | CARD pick      |
| 6    | area, index, playerIndex, energyIndex, count | ENERGY pick    |
| 7    | index                                        | PLAY from hand |
| 8    | area, index, inPlayArea, inPlayIndex         | ATTACH energy  |
| 9    | area, index, inPlayArea, inPlayIndex         | EVOLVE         |
| 12   | (bare) — midgame, ~once per turn             | RETREAT        |
| 13   | attackId                                     | ATTACK         |
| 14   | (bare) — the "proceed/pass" option           | END            |

ABILITY was never observed with the Phase-0 placeholder deck (it may
simply have no activatable abilities); no scorer rule keys on it.
"""

from __future__ import annotations

NUMBER = 0         # CONFIRMED
YES = 1            # CONFIRMED
NO = 2             # CONFIRMED
CARD = 3           # CONFIRMED
ENERGY = 6         # CONFIRMED (energy pick in sub-selects, NOT attack)
PLAY = 7           # CONFIRMED
ATTACH = 8         # CONFIRMED
EVOLVE = 9         # CONFIRMED
RETREAT = 12       # CONFIRMED
ATTACK = 13        # CONFIRMED (carries "attackId")
END = 14           # CONFIRMED
