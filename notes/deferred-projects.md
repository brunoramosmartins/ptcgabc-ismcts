# Deferred Projects — Post-Competition Portfolio Extensions

Ideas surfaced during the PTCG project that intentionally sit **outside**
the roadmap scope (Fase 0–6) but are worth building **after** the Sep 13
Strategy submission, as portfolio companions.

The competition deadlines (Aug 16–17 Simulation, Sep 13 Strategy) drive
everything on the roadmap. Anything here is a "after the ladder rating
stops mattering" activity. Documented so the intent doesn't get lost.

---

## Board-game teaching artifacts — RL from scratch on simpler boards

The tic-tac-toe example in S&B Ch 1 is *the* motivating case study for
state-value learning. Building it end-to-end with visualization is the
most direct way to solidify Chapters 1–3 and to demonstrate the concepts
outside the PTCG domain, where the strategic complexity dominates.

Motivation:

- I already implemented tic-tac-toe with minimax in an earlier AI course.
  Reimplementing it with the RL techniques from this project produces a
  clean side-by-side comparison of "game-tree search" vs "value
  learning" on the same problem — good writeup material.
- Simpler board games (tic-tac-toe, checkers/damas, Connect 4) let me
  isolate individual algorithmic ideas (UCB1, temporal-difference
  learning, MCTS, α-β pruning) in a setting where the game rules are
  not competing with the algorithm for cognitive budget.
- Visual dynamic updates of $V(s)$ or $Q(s, a)$ ("watch the value
  function learn") make abstract concepts concrete for anyone reading
  the portfolio.

### Proposed artifacts (in order of scope)

1. **`notebooks/tic-tac-toe-rl.ipynb`** — port the S&B Ch 1 example.
   Human-vs-AI and AI-vs-AI self-play modes. Two panels: current board
   on the left, live $V(s)$ heatmap of the current position + successors
   on the right. Counters for games played, win rate, and $V$ of the
   initial state (should converge to $\approx 0.5$ under symmetric
   self-play). Deliberately uses **state-value** learning to stay
   faithful to the book. **~1–2 evenings.**
2. **`notebooks/tic-tac-toe-minimax.ipynb`** — port the earlier
   coursework, run against the RL agent from artifact #1. Provides the
   comparison "search-based agent vs value-based agent, same rules".
   **~1 evening if the coursework code is recoverable.**
3. **`notebooks/checkers-mcts.ipynb`** (damas) — MCTS on a mid-complexity
   board. Perfect-information setting → no determinization → the
   Cowling paper machinery is not needed here, but everything else from
   Phase 3 (UCB1, four-phase loop, backpropagation) applies. Good
   bridge between the tic-tac-toe artifact and the PTCG project.
   **~1 weekend.**
4. **(Stretch) `notebooks/connect-four-mcts-vs-alphabeta.ipynb`** —
   Connect 4 has a solved game-theoretic value but a big enough tree
   that MCTS behaves interestingly. Comparison of MCTS convergence rate
   against α-β pruning as a function of decision-time budget. **~1
   weekend if pursued.**

### Guardrails (learned from the PTCG competition)

- One notebook per artifact. **No** Streamlit / Gradio / Dash. Live
  updates via `matplotlib` + `IPython.display.clear_output`.
- **No** cross-notebook shared state. Each is self-contained.
- **No** attempt to make it a Kaggle submission or a web app.
- All artifacts land **after** `v1.0.0` (Strategy submission on Sep 13).

### Portfolio placement

Each notebook doubles as a TIL. Suggested TIL entries:

- `tils/til-XX-value-learning-vs-game-tree-search.md` — the tic-tac-toe
  comparison.
- `tils/til-XX-mcts-on-perfect-information.md` — the checkers artifact
  (isolates the classical MCTS half of what we did in PTCG).

TIL numbering will follow whatever exists at the time; not reserving
slots now.

---

## Other deferred ideas (parking lot)

- **Learned evaluator ablation** (ADR-003 alternative): retrain the
  heuristic evaluator from PTCG as a small neural net on self-play
  data. Directly extends H4. Deferred because ADR-003 explicitly
  rejects this within the competition timeline.
- **CFR / MCCFR comparison** (ADR-001 alternative): implement a scaled-
  down CFR on a simplified poker variant to make the "why not CFR?"
  argument in ADR-001 more concrete. Deferred because CFR needs an
  explicit game tree that `cabt` doesn't expose.
- **AlphaZero-style self-play loop** on tic-tac-toe or Connect 4:
  smallest possible AZ implementation, purely as a teaching artifact.
  Deferred because a real AZ implementation on PTCG is out of scope
  (see ADR-003).

These are captured to keep the "what could come next" surface
documented; no commitment implied.

---

## Post-competition reading track — neural MCTS lineage

Surfaced during Phase 2 study discussions as a natural continuation of
the Browne → Cowling → Long arc, but **deliberately excluded from the
competition roadmap**: it conflicts with ADR-003 (no learned
evaluator within the competition), with the hard deadlines (Aug 16-17
Simulation, Sep 13 Strategy), and with the Kaggle worker constraints
(no GPU). Reading order for after `v1.0.0`:

1. **Kocsis & Szepesvári (2006)** — the original UCT paper. The
   derivations in `exercises/ex02_mcts_derivations.md` already cover
   the core results; reading the original closes the loop on the
   proofs sketched there.
2. **AlphaGo (Silver et al. 2016)** — policy/value networks + PUCT.
   The first "learned components replace handcrafted rollouts" system.
3. **AlphaZero (Silver et al. 2017)** — removes domain knowledge and
   human data; pure self-play.
4. **MuZero (Schrittwieser et al. 2020)** — removes the explicit
   simulator; learns dynamics, reward, and representation.

Each pairs naturally with a small artifact from the board-game track
above (e.g., AlphaZero-style tic-tac-toe already sits in the parking
lot). If pursued, one reading-companion note per paper following the
Phase 2 template.
