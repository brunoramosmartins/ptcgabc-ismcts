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

A third condition sits between those two: pass a full 60-card list
with ``opponent_list_is_assumed=True`` to model the opponent with a
*guess* (e.g. our own list — the `ismcts-selfdeck` arm, EXP-010).
The guess is wrong against a real field, but it is a legal, coherent
deck the simulated opponent can actually pilot, whereas the filler
produces a board no game could reach. Strict accounting is relaxed on
the opponent's side only; our side stays exact.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Any

from env.search_engine import expected_counts


class DeterminizationError(RuntimeError):
    """Raised when the visible-card accounting does not close."""


# The observation can hide up to this many of our/their cards in
# unidentifiable "limbo": our own face-down active during setup, and a
# Trainer card mid-resolution (removed from hand, not yet discarded,
# exposed nowhere — pilot v3 census). When the hidden pool exceeds the
# engine's requirement by at most this slack, we sample `need` cards
# uniformly from the pool: the true hidden set is a subset of the
# pool, so most determinizations are fully consistent and the rest
# carry a single-card inconsistency the engine tolerates.
POOL_SLACK = 2

_BASIC_IDS_CACHE: set[int] | None = None


def basic_pokemon_ids() -> set[int]:
    """Card ids that may legally sit in the active slot (Basic Pokémon).

    Loaded once from the engine's card database. The enemy_active
    segment of a determinization must be a Basic — sampling an Energy
    or Trainer there produces an invalid state the engine rejects
    (SearchBegin error 2, pilot v3 hypothesis).

    Raises:
        RuntimeError: If the database schema doesn't match any known
            key layout — the message embeds a sample entry so the
            detection can be extended in one line.
    """
    global _BASIC_IDS_CACHE
    if _BASIC_IDS_CACHE is not None:
        return _BASIC_IDS_CACHE

    import json

    from env.search_engine import all_card

    cards = all_card()
    if not isinstance(cards, list) or not cards:
        raise RuntimeError(f"AllCard returned unexpected payload: {type(cards)}")

    def is_basic(entry: dict) -> bool | None:
        """True/False when determinable; None when schema is unknown."""
        # Pokémon check + stage-0 check across plausible key layouts.
        for stage_key in ("stage", "evolveStage", "evolutionStage", "grade"):
            if stage_key in entry:
                stage = entry[stage_key]
                # hp > 0 distinguishes Pokémon from Trainers/Energy when
                # no explicit category key exists.
                hp = entry.get("hp") or entry.get("maxHp") or 0
                return stage == 0 and hp > 0
        if "evolvesFrom" in entry or "preEvolution" in entry:
            pre = entry.get("evolvesFrom") or entry.get("preEvolution")
            hp = entry.get("hp") or entry.get("maxHp") or 0
            return not pre and hp > 0
        return None

    ids: set[int] = set()
    undetectable = True
    for entry in cards:
        if not isinstance(entry, dict):
            continue
        verdict = is_basic(entry)
        if verdict is None:
            continue
        undetectable = False
        if verdict:
            cid = entry.get("cardId", entry.get("id"))
            if isinstance(cid, int):
                ids.add(cid)
    if undetectable or not ids:
        sample = json.dumps(cards[0])[:400]
        raise RuntimeError(
            "could not detect Basic Pokémon in the card database; "
            f"first entry: {sample}"
        )
    _BASIC_IDS_CACHE = ids
    return ids


def _walk_cards(node: Any, out: list[tuple[int, int, Any]]) -> None:
    """Collect (card_id, player_index, serial) for every card-like dict."""
    if isinstance(node, dict):
        card_id = node.get("id")
        owner = node.get("playerIndex")
        if isinstance(card_id, int) and isinstance(owner, int):
            out.append((card_id, owner, node.get("serial")))
        for value in node.values():
            _walk_cards(value, out)
    elif isinstance(node, list):
        for item in node:
            _walk_cards(item, out)


def visible_cards(obs: dict) -> tuple[Counter, Counter]:
    """Multisets of visible card ids for (our player, opponent).

    Walks ``current`` plus exactly one field of ``select``:
    ``contextCard`` — the card being resolved right now (e.g. a
    Trainer played from hand), which sits in no board zone and would
    otherwise leave the hidden pool one card too large.

    ``select.deck`` is deliberately NOT swept: cards shown by a
    deck-search effect are still counted in ``deckCount``, so sweeping
    them double-counts the deck (pilot v2 signature:
    "pool has 6, visible=54"). Face-down cards carry no integer id and
    are skipped automatically.

    Cards are deduplicated by their unique ``serial``: the same
    physical card can appear both on the board and as the select's
    context reference, and must be counted once. Entries without a
    serial are counted as-is.
    """
    me = obs["current"]["yourIndex"]
    found: list[tuple[int, int, Any]] = []
    _walk_cards(obs["current"], found)
    _walk_cards((obs.get("select") or {}).get("contextCard"), found)
    mine: Counter = Counter()
    theirs: Counter = Counter()
    seen_serials: set = set()
    for card_id, owner, serial in found:
        if serial is not None:
            if serial in seen_serials:
                continue
            seen_serials.add(serial)
        (mine if owner == me else theirs)[card_id] += 1
    return mine, theirs


def _zone_census(obs: dict) -> str:
    """Compact per-zone census embedded in accounting errors.

    Turns every DeterminizationError into a self-diagnosing report:
    the zone whose count disagrees with the sweep is visible directly
    in the message, no reproduction needed.
    """
    cur = obs["current"]
    me = cur["yourIndex"]
    sel = obs.get("select") or {}

    def player_zones(p: dict) -> str:
        active = p.get("active") or []
        active_repr = [a.get("id") if isinstance(a, dict) else a for a in active]
        hand = p.get("hand") or []
        return (
            f"hand={len(hand)}/{p.get('handCount')} "
            f"deckCount={p.get('deckCount')} "
            f"prize={len(p.get('prize') or [])} "
            f"discard={len(p.get('discard') or [])} "
            f"active={active_repr} "
            f"bench={len(p.get('bench') or [])}"
        )

    ctx = sel.get("contextCard")
    ctx_repr = ctx.get("id") if isinstance(ctx, dict) else ctx
    looking = cur.get("looking")
    return (
        f"me[{player_zones(cur['players'][me])}] "
        f"opp[{player_zones(cur['players'][1 - me])}] "
        f"stadium={len(cur.get('stadium') or [])} "
        f"looking={len(looking) if looking else 0} "
        f"select.type={sel.get('type')} select.contextCard={ctx_repr} "
        f"select.deck={len(sel.get('deck') or []) if sel.get('deck') else 0} "
        f"turn={cur.get('turn')}"
    )


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


def _hidden_pool_assumed(deck_list: list[int], visible: Counter) -> list[int]:
    """Hidden pool under an *assumed* (possibly wrong) opponent list.

    Visible opponent cards that do exist in the assumed list consume
    their copies (the sampled worlds stay consistent with what we have
    seen where the assumption overlaps reality); visible cards outside
    the list are simply not subtracted — they sit on the board, not in
    a hidden zone, so they impose no constraint on what we imagine the
    hidden zones contain. ``Counter.elements()`` drops non-positive
    counts, which is exactly the clamp we want.
    """
    pool = Counter(deck_list)
    pool.subtract(visible)
    return list(pool.elements())


def _draw(pool: list[int], need: int, label: str, obs: dict,
          rng: random.Random) -> list[int]:
    """Shuffle and take `need` cards from the pool, tolerating up to
    POOL_SLACK unidentifiable limbo cards; fail loud beyond that."""
    excess = len(pool) - need
    if excess < 0 or excess > POOL_SLACK:
        raise DeterminizationError(
            f"{label}: hidden pool has {len(pool)} cards, engine needs "
            f"{need} (slack {POOL_SLACK}) | census: {_zone_census(obs)}"
        )
    rng.shuffle(pool)
    return pool[:need]


def sample_determinization(
    obs: dict,
    my_deck_list: list[int],
    opponent_deck_list: list[int] | None,
    rng: random.Random,
    filler_card: int | None = None,
    basic_ids: set[int] | None = None,
    opponent_list_is_assumed: bool = False,
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
        basic_ids: Card ids legal in the active slot. ``None`` loads
            the engine card database lazily (`basic_pokemon_ids`).
            Only consulted when the opponent's active is unrevealed.
        opponent_list_is_assumed: Treat ``opponent_deck_list`` as a
            guess rather than ground truth. Strict accounting is
            relaxed on the opponent's side only: visible cards outside
            the assumed list no longer raise (they are just not
            subtracted), and the hidden pool may exceed the needed
            count (the surplus is left undrawn). Our own side keeps
            strict accounting either way.

    Returns:
        Keyword arguments for `env.search_engine.search_begin`.

    Raises:
        DeterminizationError: If the card accounting does not close
            within ``POOL_SLACK`` (strict mode), the assumed pool
            cannot cover the hidden zones (assumed mode), or no Basic
            is available for an unrevealed enemy active.
    """
    want = expected_counts(obs)
    vis_mine, vis_theirs = visible_cards(obs)

    # --- our side: hidden pool = deck + prizes (+ limbo slack) ---------
    pool = _hidden_pool(my_deck_list, vis_mine, "my side")
    need = want["my_deck"] + want["my_prize"]
    drawn = _draw(pool, need, "my side", obs, rng)
    my_deck = drawn[: want["my_deck"]]
    my_prize = drawn[want["my_deck"]:]

    # --- opponent side: deck + prizes + hand + hidden active -----------
    need_opp = (want["enemy_deck"] + want["enemy_prize"]
                + want["enemy_hand"] + want["enemy_active"])
    if opponent_deck_list is not None:
        if opponent_list_is_assumed:
            pool_opp = _hidden_pool_assumed(opponent_deck_list, vis_theirs)
        else:
            pool_opp = _hidden_pool(opponent_deck_list, vis_theirs, "opponent")

        # The unrevealed active must be a Basic Pokémon — an Energy or
        # Trainer there is an invalid state the engine rejects
        # (SearchBegin error 2). Pick actives first, from the Basics
        # in the pool, then draw the rest.
        enemy_active: list[int] = []
        if want["enemy_active"] > 0:
            if basic_ids is None:
                basic_ids = basic_pokemon_ids()
            basics_in_pool = [c for c in pool_opp if c in basic_ids]
            if len(basics_in_pool) < want["enemy_active"]:
                raise DeterminizationError(
                    f"opponent: need {want['enemy_active']} Basic(s) for "
                    f"the unrevealed active but pool has "
                    f"{len(basics_in_pool)} | census: {_zone_census(obs)}"
                )
            enemy_active = rng.sample(basics_in_pool, want["enemy_active"])
            for card in enemy_active:
                pool_opp.remove(card)

        rest_need = need_opp - want["enemy_active"]
        if opponent_list_is_assumed:
            # An assumed list is generally *larger* than the hidden
            # need (foreign visible cards subtract nothing), so the
            # strict excess check would reject every non-mirror game.
            # Undershoot still fails loud: it means the assumption
            # cannot even populate the board the engine requires.
            if len(pool_opp) < rest_need:
                raise DeterminizationError(
                    f"opponent (assumed list): pool has {len(pool_opp)} "
                    f"cards, engine needs {rest_need} | census: "
                    f"{_zone_census(obs)}"
                )
            rng.shuffle(pool_opp)
            drawn_opp = pool_opp[:rest_need]
        else:
            drawn_opp = _draw(pool_opp, rest_need, "opponent", obs, rng)
    else:
        if filler_card is None:
            raise DeterminizationError(
                "opponent deck list unknown and no filler_card given"
            )
        enemy_active = [filler_card] * want["enemy_active"]
        drawn_opp = [filler_card] * (need_opp - want["enemy_active"])

    a = want["enemy_deck"]
    b = a + want["enemy_prize"]
    return {
        "my_deck": my_deck,
        "my_prize": my_prize,
        "enemy_deck": drawn_opp[:a],
        "enemy_prize": drawn_opp[a:b],
        "enemy_hand": drawn_opp[b:],
        "enemy_active": enemy_active,
    }
