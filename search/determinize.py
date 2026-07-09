"""Consistent uniform determinization sampling (SO-ISMCTS baseline).

Samples a hidden-state assignment $h \\sim P(h \\mid I)$ uniform over the
information set, per ADR-001. "Consistent" means every sampled card
respects the public evidence: cards visible anywhere (hand, discard,
board, attachments, stadium) are excluded from the hidden pools. This
is the differentiator over the public-baseline approach of filling the
opponent with dummy cards (see `notes/open-ideas.md`,
*informed-determinization*, competitive-landscape note).

Accounting model
----------------
For each player, the 60-card list partitions into *visible* cards
(anything the observation shows with a card id and that player's
``playerIndex``) and the *hidden pool*. The hidden pool must then be
exactly the size the engine will demand:

- ours:   ``deckCount + len(prize)``
- theirs: ``deckCount + len(prize) + handCount + hiddenActive``

The sampler shuffles each pool once and slices it into the segments
`search_begin` expects. If the accounting doesn't close (a zone we
didn't anticipate, e.g. cards under a ``looking`` effect), it raises
``DeterminizationError`` loudly rather than sampling an inconsistent
world — fail-loud is deliberate during Phase 3 bring-up.

Opponent deck list: locally we know it (mirror matches, or both lists
are ours to set). On the Kaggle ladder the opponent's list is unknown;
callers may pass ``opponent_deck_list=None`` together with a
``filler_card`` id to fall back to the public-notebook strategy for
the unknown remainder. The baseline experiments never use the filler
path.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

from env.search_engine import expected_counts


class DeterminizationError(RuntimeError):
    """Raised when the visible-card accounting does not close."""


def _walk_cards(node: Any, out: list[tuple[int, int]]) -> None:
    """Collect (card_id, player_index) for every card-like dict."""
    if isinstance(node, dict):
        card_id = node.get("id")
        owner = node.get("playerIndex")
        if isinstance(card_id, int) and isinstance(owner, int):
            out.append((card_id, owner))
        for value in node.values():
            _walk_cards(value, out)
    elif isinstance(node, list):
        for item in node:
            _walk_cards(item, out)


def visible_cards(obs: dict) -> tuple[Counter, Counter]:
    """Multisets of visible card ids for (our player, opponent).

    Walks the whole ``current`` state recursively, so hands, discards,
    boards, attached energies/tools, pre-evolutions, stadium, and any
    revealed zones are all swept uniformly. Face-down cards carry no
    integer id and are skipped automatically.
    """
    me = obs["current"]["yourIndex"]
    found: list[tuple[int, int]] = []
    _walk_cards(obs["current"], found)
    mine: Counter = Counter()
    theirs: Counter = Counter()
    for card_id, owner in found:
        (mine if owner == me else theirs)[card_id] += 1
    return mine, theirs


def _hidden_pool(
    deck_list: list[int], visible: Counter, label: str
) -> list[int]:
    pool = Counter(deck_list)
    pool.subtract(visible)
    negative = {k: v for k, v in pool.items() if v < 0}
    if negative:
        raise DeterminizationError(
            f"{label}: visible cards not in the deck list: {negative}"
        )
    return list(pool.elements())


def sample_determinization(
    obs: dict,
    my_deck_list: list[int],
    opponent_deck_list: list[int] | None,
    rng: random.Random,
    filler_card: int | None = None,
) -> dict[str, list[int]]:
    """Sample a hidden assignment consistent with the observation.

    Args:
        obs: Observation dict (must include ``current``).
        my_deck_list: Our 60-card list.
        opponent_deck_list: Their 60-card list when known (local
            matches); ``None`` on the ladder, requiring ``filler_card``.
        rng: Seeded RNG (benchmark-protocol pairing).
        filler_card: Card id used for the opponent's hidden zones when
            their list is unknown. Ignored when the list is given.

    Returns:
        Keyword arguments for `env.search_engine.search_begin`.

    Raises:
        DeterminizationError: If the card accounting does not close.
    """
    want = expected_counts(obs)
    vis_mine, vis_theirs = visible_cards(obs)

    # --- our side: hidden pool = deck + prizes -------------------------
    pool = _hidden_pool(my_deck_list, vis_mine, "my side")
    need = want["my_deck"] + want["my_prize"]
    if len(pool) != need:
        raise DeterminizationError(
            f"my side: hidden pool has {len(pool)} cards, engine needs "
            f"{need} (deck {want['my_deck']} + prize {want['my_prize']}); "
            f"visible={sum(vis_mine.values())}"
        )
    rng.shuffle(pool)
    my_deck = pool[: want["my_deck"]]
    my_prize = pool[want["my_deck"]:]

    # --- opponent side: deck + prizes + hand + hidden active -----------
    need_opp = (want["enemy_deck"] + want["enemy_prize"]
                + want["enemy_hand"] + want["enemy_active"])
    if opponent_deck_list is not None:
        pool_opp = _hidden_pool(opponent_deck_list, vis_theirs, "opponent")
        if len(pool_opp) != need_opp:
            raise DeterminizationError(
                f"opponent: hidden pool has {len(pool_opp)} cards, engine "
                f"needs {need_opp}; visible={sum(vis_theirs.values())}"
            )
        rng.shuffle(pool_opp)
    else:
        if filler_card is None:
            raise DeterminizationError(
                "opponent deck list unknown and no filler_card given"
            )
        pool_opp = [filler_card] * need_opp

    a = want["enemy_deck"]
    b = a + want["enemy_prize"]
    c = b + want["enemy_hand"]
    return {
        "my_deck": my_deck,
        "my_prize": my_prize,
        "enemy_deck": pool_opp[:a],
        "enemy_prize": pool_opp[a:b],
        "enemy_hand": pool_opp[b:c],
        "enemy_active": pool_opp[c:],
    }
