# TIL #2 — The Three Clocks of `kaggle_environments`

**Status:** draft (Phase 4). Polished for portfolio in Phase 7.

Format: Hook / Insight / Example / Takeaway.

---

## Hook

Our deck-selection experiment crashed or corrupted itself three times
before producing a single valid verdict — and every failure was a
*different clock*. The engine we ran on (`kaggle_environments`, `cabt`
env) enforces three separate time controls, each living in a different
layer, each failing with a different signature, and each requiring a
different fix. Nothing in the documentation lists the three side by
side. Twelve hours of match data were poisoned learning this.

## Insight

The three clocks, in the order we met them:

| clock | scope | enforcement | failure signature |
|---|---|---|---|
| `actTimeout` (0 in `cabt`) | per step | harness deadline per act | disabled here — a decoy |
| `remainingOverageTime` (600 s) | per seat, per episode | bank drained by thinking time; seat status → `TIMEOUT` | **a row IS written** — the game is scored as a forfeit loss |
| `runTimeout` (2000 s) | whole episode | `env.run()` checks `perf_counter()` each step and **raises** `DeadlineExceeded` | **no row is written** — the sweep process dies |

Two properties matter more than the numbers:

1. **They fail into your data differently.** The bank produces
   *poisoned rows* — plausible-looking losses that silently bias a
   result (in our case, only against the slow-deck challengers: an
   anti-challenger bias in a selection experiment). The episode cap
   produces *absent rows* — loud, unmissable, and therefore harmless
   to validity. The dangerous clock is the quiet one.
2. **They are deployment constraints, not instrument constraints.**
   The shipped agent must budget under the bank (ours reads the live
   bank from its own observation and allocates per move — it cannot
   deplete it by construction). But a *local* experiment arm that is
   iteration-bounded and never reads the clock gains nothing from the
   limits — for the instrument they only inject artifacts into slow
   cells. Raising them locally changes no decision of a seeded,
   iteration-bounded agent; it only stops the engine from shooting
   the measurement.

The fixes were as different as the failures: the bank had to be
patched *through* the engine's per-seat schema caches (a naive patch
of the live state is silently rebuilt from cached defaults on
`env.run()`'s internal reset — our first fix validated green and then
poisoned 11 more cells); the episode cap, by contrast, is honored
directly from the `make()`-time configuration — one line.

## Example

The bank bias, concretely. EXP-011 compared three challenger decks
against an incumbent, reusing the incumbent's rows from a previous
run. The incumbent's games were fast and never touched the 600 s bank;
two challengers grind long games and hit it repeatedly — 14 artifact
`TIMEOUT` losses, all on the challenger side of the ledger. Left in
place, the instrument itself would have voted for the incumbent. The
recovery kept every clean row: with seeded, iteration-bounded arms,
the bank cannot change the outcome of a game that *completed*, so only
the poisoned seeds were rerun — and two of the healed seeds flipped to
challenger wins, confirming the bias direction was real.

## Takeaway

Before running any experiment on someone else's game harness,
enumerate every clock in the stack and answer two questions per clock:
*what does it write into my data when it fires* (a row, a poisoned
row, or nothing), and *is it a property of deployment or of my
instrument*. Deployment constraints belong in the shipped agent's
budget logic; instrument runs should neutralize them explicitly and
say so in the experiment registration. And validate any fix on an
input *known to trigger the failure* — our first bank fix passed its
probe because the probe seed never timed out in the first place.

Read next: `experiments/registry.md` EXP-011 amendments 1–3 for the
full forensic trail, and `notes/phase4-time-budget-calibration.md` for
how the shipped agent turns the bank from a hazard into a budget.
