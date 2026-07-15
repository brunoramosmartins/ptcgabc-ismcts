# Phase 4 — Time-Budget Calibration (#27, feeds EXP-008)

Goal: choose the search budget the **submitted** agent runs at, so it
plays as strongly as possible while **never forfeiting on the clock**
under Kaggle's per-match time limit. Output: a budget policy (a fixed
iteration count *or* a per-move time cap) recorded in EXP-008 and used
by the Simulation submission (#29).

## Why this is a real problem, with evidence

The agent today is **iteration-based**: `ISMCTSAgent(iterations=1000)`
runs exactly 1000 simulations per decision regardless of how long that
takes (`search/ismcts.py::decide`, `agents/ismcts_agent.py`). Iterations
are a *fixed-work* budget; Kaggle enforces a *fixed-time* budget. The two
diverge whenever a game runs long, because

$$\text{cumulative think time} = \sum_{\text{decisions}} (\text{time per decision}),$$

and a long game has more decisions. EXP-007 measured the consequence
directly (per-match wall-clock, both seats `ismcts` @ 1000 iters):

| deck | forfeit (TIMEOUT) % | median s/match | p90 s/match |
|---|---|---|---|
| current-v1 | 0.7 % | 196 | **617** |
| v1-tuned | 11.0 % | 317 | 1069 |
| aggro-fire | 24.3 % | 530 | 1144 |
| emboar-evolution | 20.7 % | 539 | 1132 |

Even the **selected** deck's p90 (617 s) sits above the ~600 s budget:
at 1000 fixed iterations, roughly one game in ten is in forfeit range,
and against grindy fields it is one in five. A forfeit is a *loss on the
board we were winning* — the worst possible way to drop a game. This is
the open row "Per-match 10-min budget binds ISMCTS below useful sim
count" in `docs/risk-register.md`, now being closed.

## What actually binds

Kaggle's `cabt` runs under `kaggle_environments`, which enforces two
distinct limits (exact values are a **precondition** to read from
`make("cabt").configuration` — see EXP-008; the numbers below are the
documented/empirical anchors):

1. **Per-decision cap (`actTimeout`)** — a single `choose()` call that
   exceeds it forfeits that step. Binds the *slowest single decision*.
2. **Per-agent match bank (~600 s, "10-minute budget")** — cumulative
   think time across the whole game, with a small overage allowance.
   Binds the *sum* over all decisions. This is what EXP-007's TIMEOUT
   rows hit (matches died at ~550–600 s of one agent's own time).

Note: `scripts/smoke_ismcts.py` never forfeits because it drives the
engine through the raw `sim.lib` C interface, which enforces **neither**
limit. Only the `make("cabt")` path (`scripts/local_ladder.py`) enforces
them — which is why the timeouts first appeared in EXP-007, not in
1500+ prior smoke/mirror runs. Any calibration must be measured on the
enforced path.

## Cost model (the decomposition that makes this cheap)

Measuring cumulative time by running full games at every iteration level
is expensive — the slow tail (1500 iters × Fire grind) is exactly the
region we can least afford to brute-force. Instead, decompose:

$$T(\text{it}) \;\approx\; c(\text{it}) \cdot M,$$

- $c(\text{it})$ — **mean per-decision cost** at iteration budget
  $\text{it}$. Modelled linear, $c(\text{it}) = \alpha + \beta\,\text{it}$:
  $\alpha$ is fixed per-decision overhead (determinizer setup, engine
  `search_begin`/`search_end`, move mapping), $\beta$ the marginal cost
  of one simulation. Measured from per-decision timings over a few games
  per matchup at each level — hundreds of data points per level, cheap
  because we do **not** need many full games, just many decisions.
- $M$ — **decisions per agent per game**. Iteration-**independent**:
  game length is a property of the decisions taken, not of how long each
  took to compute. Measured from many *fast* low-iteration games (or by
  counting decisions in any completed game), giving its full
  distribution (median / p95 / p99).

Then the cumulative-time tail at any $\text{it}$ is **predicted**:

$$p99\big[T(\text{it})\big] \;\approx\; c(\text{it}) \cdot p99[M]$$

(treating $c$ as near-constant per decision; if per-decision time itself
has a heavy tail we carry that through by sampling $c \cdot M$ from the
empirical joint instead of multiplying point estimates — decided at
analysis time from the measured $c$ spread).

### Solving for the operating point

**Fixed-iteration policy.** Largest $\text{it}^\*$ with

$$c(\text{it}^\*)\cdot p99[M] < 540\text{ s} \quad\text{and}\quad \max_\text{decision} c(\text{it}^\*) < \texttt{actTimeout} - \text{margin}.$$

(540 s = 600 − 10 % margin.)

**Per-move anytime-cap policy.** ISMCTS is anytime — the root move is
`best_action_by_visits()` after *any* number of iterations. So cap each
decision at $t_{\text{move}}$ seconds (stop the loop when iterations
**or** wall-clock is exhausted). Pick

$$t_{\text{move}}^\* \cdot p99[M] < 540\text{ s} \quad\text{and}\quad t_{\text{move}}^\* < \texttt{actTimeout} - \text{margin},$$

with the iteration cap set high (time binds first) on fast decisions and
the clock binding on slow ones. This **bounds cumulative time by
construction** — its forfeit risk does not depend on the tail of $M$,
which is the fixed-iteration policy's failure mode.

## Policy candidates & pre-registered decision rule

| policy | forfeit safety | strength profile |
|---|---|---|
| **A. fixed iters** | safe *in expectation*; forfeits on a long-$M$ game | constant work/decision |
| **B. per-move time cap** | safe *by construction* (cumulative ≤ $t_{\text{move}}\cdot M$) | variable work; more iters on cheap decisions, fewer on expensive ones |

**Decision rule (registered in EXP-008):** among policies meeting both
hard constraints (per-decision < `actTimeout` − margin; cumulative p99 <
540 s), choose the one with the highest strength at its operating point
(win rate vs the fixed heuristic reference, supplied by #26/H3). **Prefer
B when its strength overlaps A's in Wilson 95 % CI**, because A forfeits
on a single long game whereas B cannot. Ship the winner as the #29
submission budget.

## Measurement plan

1. **Confirm the limits.** Read `actTimeout`, agent overage bank,
   `runTimeout` from `make("cabt").configuration`. Anchor the 540 s
   target to the real bank, not the documented estimate.
2. **Instrument (code, reviewed, tests not run):**
   - `scripts/exp_timing.py` — extends `smoke_ismcts.py`'s per-decision
     timer to record, per game: every ISMCTS decision time, the
     per-agent cumulative, and the decision count $M$. Runs on the
     enforced `make("cabt")` path so forfeits are observable. Writes
     one JSON line per game to `results/exp008_*.jsonl` (gitignored).
   - Optional per-move cap in `search/ismcts.py::decide` (and threaded
     through `ISMCTSAgent`): `deadline = perf_counter() + t_move`; break
     the iteration loop when reached. Zero behaviour change when
     `t_move is None` (current default), so H1–H7 results are untouched.
3. **Fit $c(\text{it})$** over iters ∈ {300, 600, 1000, 1500}, ~5
   games/matchup, all four opponent decks; report $\alpha,\beta,R^2$.
4. **Estimate $M$** from the low-iter games (fast) across the four
   matchups; report median / p95 / p99, per matchup and pooled.
5. **Predict** the safe $\text{it}^\*$ and $t_{\text{move}}^\*$; then
   **confirm** with one run at the chosen operating point over all four
   matchups, N seeds, asserting **0 forfeits** and reporting the
   realized cumulative-time p99.

## Threats to validity (to watch)

- **Local hardware ≠ Kaggle worker.** WSL2 timings are a proxy; the
  Kaggle sandbox (2 vCPU) may be slower. Mitigate by keeping the 10 %
  margin and, ideally, running the confirmation inside the Kaggle Docker
  image before #29 (cross-ref the submission-log validation step).
- **$M$ against the real ladder field is unknown.** Our four decks are a
  proxy; a pathological opponent could push $M$ higher. The per-move cap
  (B) is robust to this by construction — an argument for B beyond the
  point estimate.
- **Per-decision cost is not perfectly constant** (branching factor
  varies with board state). If the measured $c$ spread is wide, switch
  from point-estimate multiplication to sampling $c\cdot M$ from the
  empirical joint (noted in the cost-model section).

## Lessons Learned

_(pending: fill at phase close.)_

## Failed Attempts

_(pending: fill at phase close.)_
