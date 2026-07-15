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

## What actually binds (confirmed 2026-07-15 from `make("cabt")`)

The precondition check read the real config, and it simplifies the
problem to a **single** binding constraint:

```
configuration: { episodeSteps: 1e7, actTimeout: 0, runTimeout: 2000 }
observation:   { remainingOverageTime: 600 (per-agent, not shared), step, ... }
```

- **`actTimeout: 0`** — there is **no per-decision cap**. A single
  `choose()` may take arbitrarily long without forfeiting that step. The
  "per-decision < actTimeout" constraint the first draft registered is
  therefore **vacuous** and is dropped.
- **`remainingOverageTime`: default 600, per-agent** — the spec states:
  *"agent is disqualified with TIMEOUT status when this drops below 0."*
  Because `actTimeout = 0`, there is no free per-step time, so **every
  second of thinking is drawn from this 600 s bank**. When it hits 0 the
  agent forfeits. This is the single limit that binds, and it matches
  EXP-007 exactly (matches died at ~550–600 s of one agent's own time).
- **`runTimeout: 2000`** — a secondary hard cap on the *whole episode*
  wall-clock ("not necessarily DONE"). In practice the per-agent 600 s
  bank binds first (EXP-007 forfeits fired at ~1100 s total match time,
  well under 2000), so we calibrate to 600 s and treat 2000 s as a
  backstop.

**The key enabler:** `remainingOverageTime` is in the agent's own
observation every decision (`shared: false`). So the agent can read its
*live* remaining budget and allocate accordingly — this makes an
**adaptive, budget-aware** policy (C below) possible, not just a fixed
guess. Confirmed: the obs our `choose()` receives carries
`remainingOverageTime` and `step` alongside `select` / `current` /
`search_begin_input`.

Note: `scripts/smoke_ismcts.py` never forfeits because it drives the
engine through the raw `sim.lib` C interface, which enforces **neither**
limit and exposes no overage field. Only the `make("cabt")` path
(`scripts/local_ladder.py`) enforces the bank — which is why the
timeouts first appeared in EXP-007, not in 1500+ prior smoke/mirror
runs. Any calibration must be measured on the enforced path.

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

Since `actTimeout = 0`, only the cumulative constraint remains
(540 s = 600 − 10 % margin):

**A. Fixed-iteration policy.** Largest $\text{it}^\*$ with

$$c(\text{it}^\*)\cdot p99[M] < 540\text{ s}.$$

**B. Per-move anytime-cap policy.** ISMCTS is anytime — the root move is
`best_action_by_visits()` after *any* number of iterations. Cap each
decision at $t_{\text{move}}$ seconds (stop the loop when iterations
**or** wall-clock is exhausted). Pick

$$t_{\text{move}}^\* \cdot p99[M] < 540\text{ s},$$

with a high iteration cap so the clock binds on expensive decisions and
iterations bind on cheap ones. Cumulative time $\le t_{\text{move}}\cdot M$
**by construction** — forfeit risk no longer depends on the tail of $M$,
which is A's failure mode. Still needs a *predicted* $p99[M]$, which we
only measured against our own four decks, not the real ladder field.

**C. Adaptive budget-aware policy (recommended).** The agent reads its
live bank $R = \texttt{remainingOverageTime}$ each decision and allocates

$$t_{\text{move}} = \max\!\Big(t_{\text{floor}},\ \frac{R - R_{\text{reserve}}}{\hat m}\Big),$$

where $\hat m$ is a conservative estimate of decisions remaining and
$R_{\text{reserve}}$ (e.g. 60 s) is a never-spend cushion. Re-reading $R$
every move makes this **self-correcting**: if $\hat m$ is too low and the
agent overspends early, $R$ shrinks and later budgets shrink with it, so
the bank **cannot go negative** regardless of true game length or
hardware speed. As $R \to R_{\text{reserve}}$ the per-move budget decays
to $t_{\text{floor}}$ (search collapses toward the heuristic-speed floor)
— graceful degradation instead of a forfeit. Crucially, C needs **no
prediction of $M$**: it measures its own remaining budget live, so the
"unknown ladder $M$" threat that limits A and B disappears.

## Policy candidates & pre-registered decision rule

| policy | forfeit safety | needs $M$ prediction? | strength profile |
|---|---|---|---|
| **A. fixed iters** | safe *in expectation*; forfeits on a long-$M$ game | yes | constant work/decision |
| **B. per-move time cap** | safe *by construction* ($\le t_{\text{move}} M$) | yes (for $t_{\text{move}}^\*$) | more iters on cheap decisions |
| **C. adaptive (budget-aware)** | safe *by construction*; cannot deplete the bank | **no** — reads live $R$ | most iters early, decays as bank drains |

**Decision rule (registered in EXP-008):** among policies whose measured
cumulative **p99 < 540 s** with **0 forfeits** in the confirmation run,
choose the highest strength at the operating point (win rate vs the fixed
heuristic reference, from #26/H3). **Prefer C, then B, over A when
strengths overlap in Wilson 95 % CI** — C and B are safe by construction
where A forfeits on a single long game, and C additionally needs no $M$
prediction, making it robust to the unknown ladder field. Ship the winner
as the #29 submission budget.

## Measurement plan

1. **Confirm the limits.** ✅ Done 2026-07-15: `actTimeout = 0`,
   `runTimeout = 2000`, per-agent `remainingOverageTime = 600`. Target
   anchored to the real 600 s bank (540 s with 10 % margin); the
   per-decision constraint is dropped (`actTimeout = 0`).
2. **Instrument (code, reviewed, tests not run):**
   - `search/ismcts.py::decide` gains an optional `max_seconds` (anytime
     stop: break the loop when `iterations` **or** the wall-clock
     deadline is hit, always running ≥ `min_iterations` so a valid root
     move exists). Zero behaviour change when `max_seconds is None`
     (current default) → H1–H7 results untouched.
   - `ISMCTSAgent` gains the budget policy: `max_seconds_per_move` (B)
     and `adaptive_budget` + `overage_reserve` + `budget_moves_ahead`
     (C, reads `obs["remainingOverageTime"]`). Default = neither → pure
     iterations (A).
   - `scripts/exp_timing.py` — extends `smoke_ismcts.py`'s per-decision
     timer to record, per game: every ISMCTS decision time, the
     per-agent cumulative, the final `remainingOverageTime`, and the
     decision count $M$. Runs on the enforced `make("cabt")` path so
     forfeits are observable. Writes one JSON line per game to
     `results/exp008_*.jsonl` (gitignored).
3. **Fit $c(\text{it})$** over iters ∈ {300, 600, 1000, 1500}, ~5
   games/matchup, all four opponent decks; report $\alpha,\beta,R^2$.
4. **Estimate $M$** from the low-iter games (fast) across the four
   matchups; report median / p95 / p99, per matchup and pooled.
5. **Predict** the safe $\text{it}^\*$ and $t_{\text{move}}^\*$; then
   **confirm** with one run at the chosen operating point over all four
   matchups, N seeds, asserting **0 forfeits** and reporting the
   realized cumulative-time p99.

## Fit results (2026-07-15)

76 games via `run_exp008.sh fit`, analysed with `analyze_exp008.py`:

- **Cost model:** $c(\text{it}) = 101\text{ ms} + 4.85\text{ ms}\cdot\text{it}$
  ($R^2 = 0.536$). Per-decision median: 1.56 / 2.80 / 4.32 / 7.93 s at
  300 / 600 / 1000 / 1500 iters. The moderate $R^2$ is the per-decision
  spread (board complexity) the model warned about — the *trend* is
  clean but any single decision can be well above the mean.
- **$M$ (decisions/agent/game):** pooled median 23, observed max 69;
  per opponent p99 ≈ 65 (aggro-fire), 69 (emboar), 63 (v1-tuned), 40
  (mirror). Long games come from the Fire grinds, as expected.
- **Fixed-iteration is rejected.** The naive $c_\text{mean}\cdot p99[M]$
  bound says it* ≈ 1591 is "safe", yet EXP-007 forfeited at **1000**
  fixed iters. The gap is the joint tail: a forfeit needs a long game
  **and** costly decisions in the *same* game, which multiplying a mean
  cost by a marginal $p99[M]$ misses. The fit's 0/76 forfeits only
  reflect too-few games at the high-iter levels, not safety. This is the
  concrete case for the adaptive policy over any fixed budget.
- **Chosen operating point (Policy C), pre-registered before the confirm
  run:** `overage_reserve = 60`, `budget_moves_ahead = 80`. Rationale:
  80 > observed max $M$ (69) with margin for a longer ladder game; the
  full-bank per-move budget is $(600-60)/80 = 6.75$ s ≈ 1370 iters,
  above the EXP-003 1000-iter baseline, and it decays gracefully as the
  bank drains. The bank cannot go negative by construction, so this is
  safe even if Kaggle's hardware is slower than local WSL (slower
  hardware costs *strength*, never a forfeit).

## Threats to validity (to watch)

- **Local hardware ≠ Kaggle worker.** WSL2 timings are a proxy; the
  Kaggle sandbox (2 vCPU) may be slower. Mitigate by keeping the 10 %
  margin and, ideally, running the confirmation inside the Kaggle Docker
  image before #29 (cross-ref the submission-log validation step).
- **$M$ against the real ladder field is unknown.** Our four decks are a
  proxy; a pathological opponent could push $M$ higher, breaking A's and
  B's $p99[M]$-based safety margins. **Policy C removes this threat
  entirely** — it allocates from the live bank and never predicts $M$, so
  an unexpectedly long game just shrinks its per-move budget. This is the
  decisive argument for C over A/B beyond any point estimate.
- **Per-decision cost is not perfectly constant** (branching factor
  varies with board state). If the measured $c$ spread is wide, switch
  from point-estimate multiplication to sampling $c\cdot M$ from the
  empirical joint (noted in the cost-model section).

## Lessons Learned

_(pending: fill at phase close.)_

## Failed Attempts

_(pending: fill at phase close.)_
