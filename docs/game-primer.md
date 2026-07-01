# Pokémon TCG — Author's Game Primer

Narrative walkthrough of the Pokémon Trading Card Game for the author (and
for future readers approaching the codebase without card-game context).
Complementary to [`docs/rules-summary.md`](rules-summary.md), which is the
terse rigorous reference. This document is prose; the rules-summary is a
lookup table.

## What kind of game is it

Two players, each with a **60-card deck**, take alternating turns trying to
reach one of three win conditions:

1. **Take all your prize cards** (six by default; the simulator uses the
   same convention). Prizes are drawn when you knock out an opponent's
   Pokémon.
2. **Knock out all the opponent's Pokémon in play** simultaneously.
3. **Opponent cannot draw at the start of their turn** (deck-out).

The interesting strategic tension is that (1) is the "normal" win path and
(2)/(3) are shortcuts you can build a deck around. Turn-to-turn play
revolves around which prize card you're chasing next.

## Card types

- **Pokémon.** The units. They have HP, one or more **attacks** with an
  energy cost and a damage value, a **type** (Fire/Water/etc.), a
  **weakness** and **resistance**, and a **retreat cost**. Some are
  *Basic* (can be played from hand directly), others are *Stage 1 / 2*
  (evolutions of a Basic; you play them on top of a Basic already in play,
  after it's been on the field for one turn).
- **Energy.** Powers attacks. You may attach **one energy per turn** to
  one of your Pokémon. This is the game's tempo throttle — the whole
  strategic layer sits on top of the energy-per-turn constraint.
- **Trainers.** One-shot effects. Three subtypes: *Item* (any number per
  turn, usually cheap card draw / search / disruption), *Supporter* (one
  per turn — the "big" effects: draw 7, search deck for anything, force
  opponent to shuffle their hand), and *Stadium* (a persistent field
  effect; new stadium replaces old).

## Turn structure

Each turn proceeds in roughly this order:

1. **Draw** one card. (Failing to draw here loses you the game — win
   condition #3.)
2. **Main phase.** In any order and any number of times:
   - Play Basic Pokémon from hand to your bench.
   - Evolve Pokémon in play (subject to the "in play for one turn" rule).
   - Attach up to **one** energy for the turn.
   - Play Item Trainers (unlimited), one Supporter, one Stadium.
   - Use Pokémon **abilities** (passive/triggered effects distinct from
     attacks).
   - Retreat your active Pokémon (paying its retreat cost in energy from
     itself); at most once per turn.
3. **Attack.** Declare one attack from your active Pokémon. Its energy
   cost must be satisfied. Damage is applied to the opponent's active,
   modified by weakness / resistance / effects. If HP drops to 0, the
   Pokémon is **knocked out (KO'd)** — the attacker draws one prize
   (some Pokémon draw more, e.g. `ex` / VMAX drew multiple in past
   standard rotations). The KO'd Pokémon and everything attached go to
   the **discard pile**.
4. **End of turn.** Status effects (poison, burn, sleep, paralysis, etc.)
   resolve. Play passes.

The first player of the game **skips their attack step on turn 1** in
current standard rules.

## The board

- **Active spot** — exactly one Pokémon at a time, the one that attacks
  and is attacked.
- **Bench** — up to five Pokémon in reserve, not directly attackable by
  most attacks. Damage counters can be moved here by specific effects.
- **Hand, Deck, Discard, Prize pile, Lost Zone** — the five card
  reservoirs. The Lost Zone is a "removed from game" zone used by certain
  cards.

## Where the strategy lives

- **Deck building.** 60 cards, at most 4 copies of any non-basic-energy
  card. The interaction between Pokémon lines (Basic → Stage 1 → Stage 2),
  energy count, and Trainer density is where most metagame tuning happens.
  In our project the deck is **fixed** — Phase 4 selects a single meta
  deck (see `docs/adr/adr-002-why-this-deck.md`, drafted in Phase 4) and
  every experiment uses that deck. The agent does not build the deck; it
  only *plays* it.
- **Prize trade.** Whoever is "ahead on prizes" (has drawn more) is
  generally winning, but a deck's whole plan can be to accept an early
  prize deficit and win a race back.
- **Energy attachment sequencing.** One-per-turn means the *order* in
  which you power up Pokémon determines when each becomes a threat.
  Choosing which Pokémon to attach to on turn 2 is often the highest-
  leverage decision of the match.
- **Bench management.** A benched Pokémon that is not fully evolved is
  vulnerable but essential — if your only remaining Pokémon are all in the
  active spot lineage and it gets KO'd, you may have nothing to promote
  and you lose to condition (2).
- **Supporter management.** One Supporter per turn — spending it on a
  draw effect ("Professor's Research", "Iono", etc.) versus a search
  effect ("Boss's Orders") versus a healing effect is a per-turn budget
  problem.

## Hidden information

For our agent (see `docs/mdp-formalization.md`, Phase 1), the sources of
hidden information are:

- **Opponent's hand.** Fully hidden.
- **Both players' deck orders.** Public deck *contents* (you can count
  what's in each opponent's discard); hidden *order*.
- **Prize cards.** Face down; you know the count taken so far, but not
  which cards are set aside as prizes until you draw them.
- **Face-down effects.** Some cards flip coins or reveal cards from the
  top of the deck — the RNG outcomes are only observed once resolved.

## Stochasticity

- **Shuffles and draws.** Every draw / search / shuffle-in interaction is
  a hypergeometric draw from the current deck composition.
- **Coin flips.** Attacks and abilities frequently have "flip a coin, if
  heads $X$" effects. These are proper Bernoulli(0.5) rolls in the
  simulator.
- **Prize distribution.** At game start, six cards are placed face down as
  prizes uniformly at random from the shuffled deck.

## Why this matters for the algorithm

The combination "hidden hands + shuffled decks + coin flips + long
credit-assignment horizon" is exactly the environment ISMCTS is designed
for (ADR-001). Random rollouts are cheap because the simulator resolves
all stochasticity for us; determinization is well-defined because
$P(h \mid I)$ has an explicit combinatorial form (uniform over
permutations of unseen cards consistent with the public record). No
component of PTCG requires the more expensive machinery — perfect
recall, private-observation abstraction — that CFR-style solvers demand.

## What the primer intentionally does not cover

- Specific card lists, rotations, or metagame decks. Those change
  between Kaggle releases; the Phase-4 ADR-002 will pin the deck used
  for our submission.
- Deviations between the simulator and the official rulebook. Those
  belong in `docs/rules-summary.md` under "Simulator vs. Official Rules"
  and are the Phase-0 deliverable for issue #2.
