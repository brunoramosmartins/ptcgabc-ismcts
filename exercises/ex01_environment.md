# Exercise 01 — Environment Formalization

Phase 1 exercises companion to [`docs/mdp-formalization.md`](../docs/mdp-formalization.md).
Each answer is short and rigorous. When code is referenced, the code is the
source of truth — the exercise justifies *why* the code looks the way it does.

## 1. State space $S$ as a product of public and private components

Let $S = S^{\text{pub}} \times S^{\text{priv}}$, where

$$
S^{\text{pub}} = \bigl(A_1, A_2,\; B_1, B_2,\; \text{Disc}_1, \text{Disc}_2,\;
c_1^{Pr}, c_2^{Pr},\; c_1^D, c_2^D,\; \text{Stadium},\; \text{turn} \in \{1,2\},\; t \in \mathbb{N}\bigr).
$$

Reading:

- $A_i$ — active Pokémon of player $i$ (identity + HP + energies attached + status effects). Public: both players observe it.
- $B_i$ — bench (0–5 Pokémon) of player $i$, with the same per-Pokémon
  attributes. Public.
- $\text{Disc}_i$ — ordered discard of player $i$. Public.
- $c_i^{Pr}$ — **count** of prize cards remaining in $Pr_i$. Public (which
  *specific* cards are in the prize pile is private).
- $c_i^D$ — **count** of cards remaining in $D_i$. Public (order and identity
  are private).
- $\text{Stadium}$ — the active Stadium card (or $\bot$). Public.
- $\text{turn}$ — whose turn it is. $t$ — turn number.

$$
S^{\text{priv}} = \bigl(H_1, H_2,\; D_1, D_2,\; Pr_1, Pr_2,\;
\text{coin history},\; \text{deck order history}\bigr).
$$

Reading:

- $H_i$ — ordered hand of player $i$. Private *to player $i$*: player $-i$
  observes only $|H_i|$.
- $D_i$ — ordered deck of player $i$. Private *to nobody after shuffle* — the
  content list is public (deck submissions), the **order** is private.
- $Pr_i$ — the specific prize cards of player $i$. Private *to nobody* until
  drawn — set aside face-down at setup; the cards are unknown to both
  players until claimed.
- Coin flips and forced-shuffle outcomes contribute to the transition
  realization; their *outcomes* are public after the fact but their *future
  values* are pending random draws.

**Explicit unobservables from our agent's viewpoint** (player $i = \text{us}$):
$H_{-i}$, the order of $D_{-i}$, the order of $D_i$, and $Pr_1 \cup Pr_2$.
Everything else in $S^{\text{pub}}$ is observed. Our own hand $H_i$ is
observable to us but hidden from the opponent.

## 2. Information set $I(s)$ and $I$-measurability of policies

Define the observation function of player $i$ at state $s$:

$$
O_i(s) = \bigl(S^{\text{pub}}(s),\; H_i(s),\; \text{sequence of options presented so far}\bigr).
$$

The **information set** of state $s$ for player $i$ is the equivalence class

$$
I_i(s) \;=\; \bigl\{\, s' \in S \;:\; O_i(s') = O_i(s) \,\bigr\}.
$$

That is: two states are in the same information set iff player $i$ cannot
distinguish them from their observations alone.

**Claim.** Any admissible policy $\pi$ for player $i$ must be
$I_i$-measurable: for all $s, s' \in S$,
$$
I_i(s) = I_i(s') \;\Longrightarrow\; \pi(\,\cdot\, \mid s) = \pi(\,\cdot\, \mid s').
$$

**Proof sketch.** By definition of a "policy for player $i$", $\pi$ is a
function of the *observations available to $i$*, not of the underlying state.
If $I_i(s) = I_i(s')$, then $O_i(s) = O_i(s')$ — the two states produce
identical observation streams for $i$. A policy that maps identical
observations to different distributions cannot be implemented by an agent
that only sees observations (there is no measurable "select this branch"
based on hidden information). Formally, $\pi$ factors as
$\pi = \tilde\pi \circ O_i$ for some
$\tilde\pi : \text{range}(O_i) \to \Delta(A)$; this factorization is
exactly $I_i$-measurability. $\blacksquare$

**Corollary (informal).** Any search algorithm that "conditions on
$s \in I_i$ but not on $I_i$ itself" — e.g. naive MCTS on a sampled
determinization returning per-world actions — violates $I_i$-measurability.
This is *strategy fusion* and is the ISMCTS motivation (see
[`docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md)).

## 3. Upper bound on $|I_i(s)|$ mid-game

**Setup.** Mid-game state where the opponent has 4 cards in hand drawn
from 42 remaining unseen cards.

The information set (for us) is characterized by the joint choice of
- which 4 of the 42 unseen cards constitute $H_{-i}$,
- the order of the remaining $42 - 4 = 38$ cards in $D_{-i}$,
- (also the order of our own $D_i$, but we know $|D_i|$ and its
  multiset — the private part is the ordering — which is symmetric
  and can be factored out for this exercise).

For the opponent-hand-and-deck contribution alone,

$$
|I_i(s)| \;\le\; \binom{42}{4} \cdot 38! \;\cdot\; 38!
$$

if we distinguish deck orderings from prize orderings; more sharply, if
we care only about the multiset of the hand and the ordering of the
remaining deck,

$$
|I_i(s)| \;\le\; \binom{42}{4} \cdot 38! \;=\; \frac{42!}{4! \cdot 38!}\cdot 38! \;=\; \frac{42!}{4!}.
$$

Using Stirling, $\log_{10}(42!/4!) \approx 51.15 - 1.38 \approx 49.8$, i.e.
$|I_i(s)| \lesssim 10^{50}$ — astronomically large. The point is not the
exact number but that **explicit enumeration is impossible**; determinization
(sample $h \sim P(h \mid I_i)$) is the only tractable way to search.

## 4. Linearity of expectation and per-turn decomposition

**Claim.** Under a random opponent, the expected match outcome
$\mathbb{E}[r_T]$ (where $r_T \in \{-1, 0, +1\}$) can be decomposed by turn
*without* independence of turn-level outcomes.

**Reasoning.** Let $X_t \in \{-1, 0, +1\}$ be an indicator of "match
terminates at turn $t$ with sign of outcome $X_t$"; formally
$X_t = r_T \cdot \mathbf{1}[T = t]$ where $T$ is the (random) terminal turn.
Then

$$
r_T \;=\; \sum_{t=1}^{\infty} X_t,
$$

and by **linearity of expectation** — which does *not* require
independence — 

$$
\mathbb{E}[r_T] \;=\; \sum_{t=1}^{\infty} \mathbb{E}[X_t].
$$

Each term $\mathbb{E}[X_t]$ is the probability-weighted per-turn contribution:
it depends on the *joint* distribution of everything that happened up to
turn $t$, but the *sum* does not require factoring that joint into
independent parts.

**Why this matters for us.** Two consequences carry over to Phase 3 and 5
analysis:

1. When we compare two agents on shared match seeds and take
   $\Delta = r_T^{\text{ISMCTS}} - r_T^{\text{heuristic}}$, the paired
   bootstrap can decompose $\mathbb{E}[\Delta]$ by turn without assuming
   turns are independent — the bootstrap resamples matches (which
   respects turn-level joint distributions) rather than turns.
2. Any per-turn diagnostic ("ISMCTS wins more on turns > 15") is a *decomposition*
   of the mean, not a *test* of it; the test still has to happen at the
   match level to avoid overcounting correlated turns.

## References

- [`docs/mdp-formalization.md`](../docs/mdp-formalization.md) — the
  companion formal definitions.
- [`docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md) —
  strategy fusion argument.
- Cowling, Powley & Whitehouse (2012), Section III — information-set
  formalization used here.
