# PTCG Rules — Compact Summary

Terse rules reference. Prose walkthrough lives in
[`docs/game-primer.md`](game-primer.md); this file is the lookup table.

## Notation

- Player $P_1$ moves first; $P_2$ moves second.
- $H_i$ = player $i$'s hand; $D_i$ = deck; $Pr_i$ = prize pile;
  $B_i$ = bench (0–5 Pokémon); $A_i$ = active spot (exactly 1 Pokémon
  when in play); $Disc_i$ = discard pile.
- Prizes remaining $= |Pr_i|$; starts at $6$.

## Setup

1. Shuffle $D_i$; draw 7 cards to $H_i$.
2. If $H_i$ contains no Basic Pokémon, reveal, shuffle back, redraw;
   opponent draws an extra card each time this happens (mulligan penalty).
3. Place one Basic Pokémon as $A_i$; optionally up to 5 more as $B_i$.
4. Set aside 6 top cards of $D_i$ face-down as $Pr_i$.
5. Coin flip decides who goes first (or predetermined by tournament rule
   in some formats — simulator convention documented below).

## Win conditions (checked at end of each action that could trigger one)

Player $i$ **wins** if any of:

$$
\text{(W1)}\quad |Pr_i| = 0 \quad\text{(all prizes drawn)}
$$
$$
\text{(W2)}\quad |A_{-i}| + |B_{-i}| = 0 \quad\text{(opponent has no Pokémon in play)}
$$
$$
\text{(W3)}\quad |D_{-i}| = 0 \text{ at opponent's draw step} \quad\text{(deck-out)}
$$

Draws happen only via simultaneous satisfaction (e.g. mutual KO leaves
both players with no Pokémon).

## Turn structure

Each turn of player $i$:

1. **Draw step.** Draw 1 from $D_i$. If $|D_i| = 0$, opponent wins (W3).
2. **Main phase** — any order, any legal number of times:
   - Play Basic Pokémon from $H_i$ to $B_i$ (up to 5 total on bench).
   - Evolve: replace a Pokémon in play with its evolution from $H_i$,
     provided the evolving Pokémon has been in play since **before this
     turn** (no evolving the turn it enters).
   - Attach energy: at most **1 per turn**, from $H_i$, to any Pokémon
     in play.
   - Play any number of **Item** Trainer cards.
   - Play at most **1 Supporter** Trainer card per turn.
   - Play at most **1 Stadium** Trainer card per turn (replaces existing
     Stadium if different name).
   - Use Pokémon **abilities** (limits vary per card; some are
     once-per-turn, some passive).
   - **Retreat** $A_i$ once per turn: pay $A_i$'s retreat cost by
     discarding energies from $A_i$; swap with a benched Pokémon.
3. **Attack step.** Choose an attack of $A_i$ with satisfied energy cost;
   apply damage to $A_{-i}$ modified by weakness / resistance / status;
   resolve on-hit effects. If $A_{-i}$'s remaining HP $\le 0$:
   $A_{-i}$ is knocked out. Player $i$ draws prizes equal to the KO's
   prize value (default 1; some Pokémon give multiple). Opponent
   promotes a benched Pokémon; if none available, opponent loses (W2).
4. **End step.** Resolve between-turn effects (poison damage counters,
   burn flip, sleep flip, paralysis clear, etc.).

**Turn-1 restriction:** $P_1$ may not attack on turn 1 (current standard).

## Damage resolution

Let $B$ = base attack damage, $s$ = status modifiers (e.g. muscle band
+30). Then damage $D$ dealt to $A_{-i}$ is:

$$
D \;=\; \bigl(B + s + m_{+}\bigr) \cdot w \;-\; r \;-\; m_{-},
$$

where $w \in \{1, 2\}$ is the weakness multiplier ($=2$ if attacker's
type matches defender's weakness, else $1$), $r$ is resistance (typically
$-20$ or $-30$ when applicable, capped so $D \ge 0$), and
$m_{+}, m_{-}$ are per-effect additive modifiers.

HP tracking uses **damage counters** in the physical game (each = 10 HP);
the simulator carries continuous HP as an integer.

## Status conditions

- **Asleep.** Between turns, flip; heads → recover.
- **Confused.** When attacking, flip; tails → self-damage instead.
- **Paralysed.** Cannot attack or retreat; clears at end of next turn.
- **Burned.** Between turns, take 20 damage, then flip; tails → still
  burned, heads → recover.
- **Poisoned.** Between turns, take 10 damage; persists until healed or
  Pokémon leaves active.

A Pokémon can have at most one non-poison special condition at a time;
poison stacks with one of {asleep, paralysed, confused}.

## Prizes and card values

- Default: 1 prize per KO.
- Higher-tier Pokémon (ex / V / VMAX / VSTAR in past standards) give
  **2 or 3 prizes**. The simulator encodes the value per card.

## Simulator vs. Official Rules

The Simulation Category overview flags that the `cabt` simulator diverges
from the official rulebook in a small number of places. This section is
the enumerated list; it is refined as we hit each divergence during
Phase 1 environment work.

**Confirmed divergences (as of Phase 0 reconnaissance):**

- **Deck submission format** is a plain integer-per-line CSV (60 lines),
  not a card-name list. This is a submission-format simplification, not a
  gameplay rule change.
- **Observation contract** exposes `obs["select"]["option"]` with only
  currently-legal choices; the agent never has to filter for legality
  itself. In the physical game the player is responsible for legality
  enforcement.
- **Deterministic tie-break for first-player choice.** The simulator
  handles the coin flip internally and reports the resulting turn order
  via `obs["current"]["yourIndex"]`.

**Divergences to enumerate during Phase 1** (cross-ref the "differences"
link on the Kaggle competition page; each item lands here as a bullet
with the specific rule + simulator behavior + rationale):

- (Simultaneous KO resolution — expected to be a bookkeeping order in
  the simulator; confirm.)
- (Tournament-specific rules like resource decking, coin priority — likely
  absent from `cabt`; confirm.)
- (Any card whose text refers to a "hand size" or "at random from your
  deck" resolution — check the simulator's PRNG interface.)
- (Ability trigger ordering for simultaneous triggers.)

## References

- Official Pokémon TCG rulebook: <https://www.pokemon.com/us/pokemon-tcg/rules-and-resources/>
- Kaggle Simulation Category overview (the "differences" link is on
  that page).
- `cabt` engine docs: <https://matsuoinstitute.github.io/cabt/>
