# Phase 2 — Cross-Source Synthesis

Central file for questions that cut across multiple readings (Sutton &
Barto, Browne survey, Cowling ISMCTS paper) and for the emerging
target-architecture picture. Kept separate from the per-paper walkthroughs
so answers that draw on the full corpus don't get pinned to a single
source.

Cross-refs:
- [`phase2-rl-foundations.md`](phase2-rl-foundations.md) — S&B Ch 1–3, 8
  concept notes and prompts.
- [`phase2-mcts-fundamentals.md`](phase2-mcts-fundamentals.md) — Browne
  survey walkthrough.
- [`phase2-ismcts-paper-notes.md`](phase2-ismcts-paper-notes.md) —
  Cowling walkthrough.
- [`../docs/adr/adr-001-why-ismcts.md`](../docs/adr/adr-001-why-ismcts.md)
  — the architectural decision this synthesis stress-tests.
- [`open-ideas.md`](open-ideas.md) — capture point for anything the
  synthesis surfaces as a testable idea.

Prompts here fill *after* their prerequisite readings finish, not while
reading. Template as usual: **Prompt** → **My take** → **Refined
write-up**.

Living document; ends with `## Lessons Learned` and `## Failed Attempts`
at Phase-2 merge time.

---

## Prerequisites

Fill each row as you finish the corresponding reading.

| Reading | Status |
|---|---|
| S&B Ch 1–3, 8 | ✅ answered in `phase2-rl-foundations.md` |
| Browne (2012) survey | in progress in `phase2-mcts-fundamentals.md` |
| Cowling et al. (2012) | in progress in `phase2-ismcts-paper-notes.md` |
| Long, Sturtevant, Buro & Furtak (2010) | *(optional; jot findings under §CS.3 below if pursued)* |

---

## Cross-source prompts

### CS.1 — Sutton & Barto's MCTS vs Browne's MCTS

**Prompt.** Compare S&B Ch 8 §8.11 with the corresponding sections in
Browne.

- Which one is more mathematically precise?
- Which is more useful as an *implementation reference*?
- Which sections of Browne would you skip if re-reading only for
  implementation guidance vs conceptual understanding?

**My take.**

_(fill in after finishing Browne)_

**Refined write-up.**

_(pending)_

---

### CS.2 — What Browne does *not* prepare you for

**Prompt.** Before opening the Cowling paper, write down what you
*expect* Cowling to add on top of Browne. This is the "prediction
before reading" exercise that makes the next paper stick.

- What algorithmic modification do you expect for imperfect information?
- What experimental setup would you expect them to use (game, baseline,
  metric)?
- What theoretical guarantee (if any) do you expect them to prove?

**My take.**

_(fill in before starting Cowling — deliberately incomplete after; the
value is in the prediction, not the accuracy)_

**Refined write-up.**

_(pending)_

---

### CS.3 — Cowling's variant choice for PTCG

**Prompt.** The Cowling paper offers SO-ISMCTS, MO-ISMCTS, and possibly
a third variant.

- Restate the trade-off between the three variants for our specific
  Kaggle constraints (10-min per-match budget, 2 vCPUs, no persistent
  state).
- Which does ADR-001 commit us to? Is the argument still valid after
  reading the paper, or does the paper suggest a different choice?
- If the paper's argument changes our mind, propose an amendment ADR.

**My take.**

_(fill in after Cowling §3)_

**Refined write-up.**

_(pending)_

---

### CS.4 — What Cowling leaves for the implementer

**Prompt.** Before writing any ISMCTS code (Phase 3, Issue #16),
enumerate what the paper leaves as an implementation exercise.

- Data structures for the search tree — is the paper prescriptive or
  does it leave this open?
- The rollout policy — the paper likely assumes it's given. What
  choices does that leave us? (Answer: random or heuristic, per Phase
  3 vs Phase 4.)
- Handling of chance nodes (coin flips, random card effects) —
  explicit modeling vs implicit sampling through the engine.

**My take.**

_(fill in after Cowling)_

**Refined write-up.**

_(pending)_

---

### CS.5 — Predictions vs reality

**Prompt.** Go back to §CS.2 above and look at what you predicted before
reading Cowling.

- Which predictions were right?
- Which were wrong, and what surprised you?
- What does this tell you about your own model of "what's hard about
  imperfect-information games"?

**My take.**

_(fill in after Cowling)_

**Refined write-up.**

_(pending)_

---

## Target architecture (post-survey sketch)

After reading Browne, you sketched a candidate architecture combining
several ideas from the survey (belief inference, action ranking,
progressive widening, UCT, guided rollouts). Captured here as a
snapshot — it will not be implemented as-is in Phase 3, but it's the
right document for the "what would the full system look like" picture
that motivates each individual EXP in Phases 3–5.

### Sketch

```
                Current State
                     │
                     ▼
         Belief State Generator
    (infer opponent deck archetype;
     see open-ideas informed-determinization)
                     │
                     ▼
           Action Generator
       (legal actions at this turn)
                     │
                     ▼
            Action Ranking
    (heuristic scorer; reuses ADR-003 evaluator;
     see open-ideas progressive-widening-with-action-ranking)
                     │
                     ▼
         Progressive Widening
       (top-k children as v grows)
                     │
                     ▼
              UCT Selection
         (UCB1 over expanded children;
          ADR-001 baseline)
                     │
                     ▼
          Guided Rollout Policy
      (random in Phase 3, heuristic in Phase 4;
       ADR-003, H2)
                     │
                     ▼
             Backpropagation
       (sample-average, α = 1/n;
        phase2-rl-foundations §2.2)
                     │
                     ▼
            Best action found
```

### Which pieces are baseline (ADR-locked)

- **UCT Selection** — locked by [ADR-001](../docs/adr/adr-001-why-ismcts.md).
- **Guided Rollout Policy (random → heuristic)** — locked by
  [ADR-001](../docs/adr/adr-001-why-ismcts.md) and
  [ADR-003](../docs/adr/adr-003-heuristic-not-learned-evaluator.md);
  tested by H2.
- **Backpropagation as sample-average** — implied by
  [ADR-004](../docs/adr/adr-004-terminal-reward-not-shaped.md) and the
  Phase 3 architectural choice.

### Which pieces are candidate (in `open-ideas.md`)

- **Belief State Generator** → *informed-determinization* (both
  constraint refinement and archetype-based priors). **Gated on
  `oracle-baseline-cheating-uct`** — measure the imperfect-information
  ceiling before implementing the belief pipeline.
- **Action Ranking + Progressive Widening** →
  *progressive-widening-with-action-ranking*. Independent of the
  belief-based line; can proceed regardless of the ceiling.
- **Transposition Table (not shown in sketch)** →
  *transposition-tables-for-info-sets*. Pure speedup, not gated.
- **RAVE with per-archetype conditioning (not shown in sketch, but a
  natural layer on top of Backpropagation)** →
  *archetype-conditioned-rave*. Transitively gated (depends on the
  archetype module from *informed-determinization*).

### The diagnostic that gates everything

Before any of the Belief State Generator work, run
*oracle-baseline-cheating-uct* to measure

$$
\Delta_{\text{ceiling}} \;=\; W_{\text{cheat}} - W_{\text{ISMCTS}}.
$$

The ceiling gap tells us how much headroom belief-based ideas have.
Small gap → drop the belief pipeline entirely, focus Phase 5 on
Progressive Widening and Transposition Tables (which don't depend on
opponent modeling). Large gap → the target architecture above becomes
worth implementing.

### What the sketch is missing

The sketch is a decision-time pipeline; it doesn't show:

- Chance nodes for coin flips and random card effects (Cowling
  §4 material — check whether the paper models these as explicit
  branching or delegates to the engine).
- Opponent's tree in MO-ISMCTS (SO-ISMCTS is per ADR-001; if Cowling
  argues we should upgrade, revisit).
- Match-level state that persists across decisions (e.g., updated
  archetype posterior). ISMCTS itself rebuilds the tree each decision,
  but the Belief State Generator can maintain state across turns.

Revisit this sketch after finishing Cowling and before starting Phase 3
implementation. The pieces that survive the reading become the Phase 3
plan; the pieces that don't move to a proper `notes/deferred-projects.md`
entry or stay in `open-ideas.md`.

---

## Lessons Learned

_(filled at Phase-2 merge time.)_

## Failed Attempts

_(filled if any come up during synthesis.)_
