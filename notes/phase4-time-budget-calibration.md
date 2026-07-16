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

## Confirm results (2026-07-16) — Policy C passes both gates

80 games (4 opponents × 20 paired seeds, iters-cap 100 000 so wall-clock
and not iterations binds, opponent `ismcts` at 1000 fixed iters), 1454
decisions, analysed with `analyze_exp008_confirm.py`:

| opponent | n | forfeits | cum p99 | bank floor | $M$ max | per-dec median | win |
|---|---:|---:|---:|---:|---:|---:|---:|
| aggro-fire | 20 | 0 | 310.7 s | 292.2 s | 68 | 5.96 s | 0.85 |
| v1-tuned | 20 | 0 | 283.1 s | 320.1 s | 59 | 5.95 s | 0.70 |
| emboar-evolution | 20 | 0 | 188.0 s | 416.4 s | 34 | 6.03 s | 0.90 |
| current-v1 (mirror) | 20 | 0 | 165.1 s | 439.6 s | 29 | 6.26 s | 0.75 |

- **Gate 1 — 0 forfeits: PASS** (0/80).
- **Gate 2 — cumulative p99 < 540 s: PASS** (310.7 s). At $n = 80$ the
  nearest-rank p99 *is* the maximum, so 310.7 s is the literal worst game,
  not an interpolated quantile — 229.3 s of headroom.
- **The pre-registered guess held.** Pooled max $M$ = 68, just under the
  $\hat m = 80$ chosen from the fit stage's observed max of 69. Had the
  ladder produced a 90-move game, Policy C would have shrunk its per-move
  budget rather than forfeited — which is the entire point of C over A/B.
- **The bank model is exact.** Engine drawdown minus measured think-time
  has median *and* worst-case residual of **+0.00 s across all 80 games**.
  Every second we spend thinking is charged to the bank, and nothing else
  is. This retires the "what if the engine charges for something we don't
  measure" worry outright.
- **Per-decision cost sits at the cap.** Medians of 5.95–6.26 s against
  the full-bank ceiling of $(600-60)/80 = 6.75$ s: early decisions spend
  the cap and later ones taper as the bank drains, exactly the graceful
  decay C was designed for. (The observed per-decision max of 6.758 s
  overshoots the cap by 8 ms because `decide()` checks the deadline
  *between* iterations — expected, not a leak.)

**Descriptive strength signal, and why it is not a verdict.** In the
mirror cell both seats play `current-v1`, so the sole difference is the
budget policy: Policy C (≈1370 iters at full bank, decaying) against a
fixed 1000 iters. C wins 0.75, Wilson 95 % CI [0.53, 0.89] — lower bound
above 0.5. Read literally, the adaptive budget buys *strength*, not just
forfeit-immunity. Read honestly, this is $n = 20$, was not pre-registered,
and seat order is unbalanced, so first-player advantage is an uncontrolled
confound sitting in the same direction. It is a lead for #26/H3, not a
result.

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

- **Read the config before designing around it.** The first draft of
  EXP-008 registered "per-decision cost < `actTimeout` − margin" as a hard
  constraint. `actTimeout` is **0** — there is no per-decision cap, and the
  constraint was vacuous. An entire branch of the protocol was optimizing a
  limit that does not exist. The same five-minute check paid for itself
  twice over: it also surfaced that `remainingOverageTime` is delivered in
  the agent's own observation, which is what made Policy C possible. The
  check that deleted a constraint is the one that produced the answer.
- **An observable constraint beats a predicted one.** Policies A and B both
  need $p99[M]$ — a prediction about a ladder field we have never seen.
  Policy C reads the live bank and needs no prediction at all. The fit
  stage's real payoff was not the number it produced ($\text{it}^\* \approx
  1591$) but the proof that the number could not be trusted. We ran a
  quantitative stage and its most valuable output was a *disqualification*.
- **Point estimates hide joint tails.** $c_\text{mean} \cdot p99[M]$ said
  1591 iters was safe; EXP-007 had already forfeited at 1000. Multiplying a
  mean cost by a marginal quantile silently assumes the two are
  independent, when a forfeit specifically requires a long game **and**
  expensive decisions *in the same game*. The correct object is the
  quantile of the product, not the product of the summaries.
- **Zero events in a small sample is not evidence of safety.** The fit
  stage reported 0/76 forfeits and it meant nothing — only 3 games per
  opponent ran at the high-iteration levels, which is where forfeits live.
  A null needs its sample size attached or it is decoration. The same rule
  in reverse: 4 log lines from one opponent are not the tail either; an
  early read of the confirm data suggested ~19 % budget utilization, and
  the true worst case over all 80 games is 58 %.
- **Decomposition beat brute force.** $T \approx c(\text{it}) \cdot M$ with
  $M$ iteration-independent let us measure $c$ from a handful of games
  (each yielding dozens of decisions) and $M$ from many cheap low-iter
  games, then *predict* the expensive tail instead of running it.
  Brute-forcing high-iteration full games directly would have cost days of
  wall-clock we did not have.
- **The conservatism has a price, and it is worth naming.** Because
  `budget_moves_ahead` is a *constant* 80, the divisor never shrinks as a
  game progresses: even the 68-move worst case ended with 292 s unspent,
  and the median game leaves roughly 80 % of the bank on the table. That is
  the correct trade for #29 — a forfeit is a certain loss, unspent seconds
  are only foregone strength — but it is a real lever. A decaying estimate
  of *remaining* moves would spend more of the bank for the same safety
  guarantee, which is a Phase-5 idea rather than a pre-deadline one.
- **A resumable runner needs a whole-corpus analyzer.** `exp_timing.py`
  prints a summary of the games *it* just ran; after a resume that was 9
  games, not the 80 in the files. Read as a verdict it would have reported
  p99 = 183.6 s instead of 310.7 s. Resumability and reporting are separate
  concerns and must not share a code path.

## Failed Attempts

- **The timing wrapper as a callable class (2026-07-15) — cost: one full
  collection run.** `_TimedSeat` was an object with `__call__`.
  `kaggle_environments` introspects agents with
  `inspect.getfullargspec`, which raises `TypeError` on class instances, so
  both seats errored before taking a single decision. Every row of all 76
  fit games and 30 confirm games came back `status=ERROR`, `M=0`,
  `my_final_overage=None` — and the data *looked plausible* at a glance.
  The tell was a per-decision median of 0.000 s. Two compounding failures
  made it survive as long as it did: the forfeit check searched for
  `TIMEOUT` and the status was `ERROR`, so "0 forfeits" was a **false
  positive** — a check that cannot distinguish *passed* from *never ran* is
  not a check; and `run_cell` resumes by counting lines, so the poisoned
  files would have been skipped as "complete" forever. They had to be
  deleted by hand. Fixed with a plain closure (`_timed_fn`), a regression
  test that runs `getfullargspec` on the wrapper
  (`tests/test_exp_timing.py`), and an integrity guard in
  `analyze_exp008_confirm.py` that fails loudly on any non-outcome status.
  `local_ladder.py` was never affected — it already returned a closure.
- **The `actTimeout` constraint (registered, then dropped as vacuous).**
  See Lessons Learned. Recorded here rather than quietly deleted because
  the registry showed a hard constraint that never existed, and the
  correction is only visible if the mistake stays on the record.
- **Fixed-iteration budgets (A), rejected after being fitted.** The whole
  $c(\text{it})$ regression was run to size a fixed budget, and its answer
  was discarded — not because the fit was wrong ($R^2 = 0.536$ over 1960
  decisions is a clean trend) but because the quantity it estimates is the
  wrong one for a forfeit question. Kept as a registered negative result:
  the fit is what makes the case against fixed budgets quantitative rather
  than hand-waved.
