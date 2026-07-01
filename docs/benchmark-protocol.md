# Benchmark Protocol

The reference every hypothesis test in Phase 3 and Phase 5 respects.
Every experiment in [`experiments/registry.md`](../experiments/registry.md)
declares whether it follows this protocol and, if it deviates, why.

## Match Set

- **N = 200 matches per comparison** (Phase 1–4 quick-iteration budget).
- **N = 500 matches per comparison** (Phase 5 hypothesis tests H1–H4).
- **K = 20 seeds per experiment.**
- **Opponent pool:** the immediately preceding agent in the roadmap
  (heuristic vs random, ISMCTS vs heuristic, etc.), plus internal
  ablation variants when applicable.

### Why these numbers

Under a Bernoulli win-indicator with true win rate $p$ near 0.5, the
Wilson 95% confidence interval half-width is approximately

$$
\text{HW}_{95}(p, N) \;\approx\; 1.96 \cdot \sqrt{\frac{p(1-p)}{N}}.
$$

At $p = 0.5$:

| $N$ | Wilson half-width |
|---|---|
| 100 | ≈ 9.8 % |
| 200 | ≈ 6.9 % |
| 500 | ≈ 4.4 % |
| 1000 | ≈ 3.1 % |

We want the ISMCTS-vs-heuristic gap in Phase 5 to be at least twice the
half-width for a "CI-separated" claim. Empirical MCTS-vs-heuristic gaps
in card-game literature run 8–15 percentage points; $N = 500$ gives
≈ 4.4 % half-width, comfortable for that regime. $N = 200$ is the local
budget for Phase 1–4 iteration, where we want fast feedback and a
looser but still informative interval.

**Provisional pending Phase 5 sample-size analysis.** These numbers may
tighten once `exercises/ex05_statistical_inference.md` is written. Any
change lands as an amendment to this file with a research-log entry.

## Determinism and Seeding

### Seed policy

Every match has three independent seeds:

- **Match seed** $s_{\text{match}} \in \{1, \dots, N\}$ — pinned per match,
  used to seed the `kaggle_environments` env RNG.
- **Agent seed** $s_{\text{agent}} = s_{\text{match}}$ — passed to the
  agent's internal RNG (RandomAgent, ISMCTS rollout policy, etc.). Using
  the same value keeps paired comparisons diagonal: on match seed 17, both
  the "A vs B" and "A vs C" runs face the same environment realization,
  so paired tests (bootstrap, McNemar) get their variance-reduction benefit.
- **Comparison seed** $s_{\text{cmp}} \in \{1, \dots, K\}$ — pins the
  choice of the $N$ match seeds. Repeating an experiment with a different
  $s_{\text{cmp}}$ produces an independent replication.

Across all $K$ replications of an experiment, we run $K \cdot N$ matches;
Wilson CIs pool them, paired bootstrap resamples matches within a
$s_{\text{cmp}}$ (not across).

### Deck version pinning

Every experiment records the git commit hash of `decks/selected/deck.csv`
active at experiment time. Phase 1–3 use the Phase 0 placeholder deck; Phase
4 replaces it once and every subsequent experiment records the new hash.

## Hardware

- **Machine:** local WSL2 Ubuntu on Windows 11 host, Python 3.11 venv
  (see [`docs/engineering.md`](engineering.md)). Kaggle sandbox spec
  (2 vCPU, 12.2 GiB, no GPU) is the ceiling — experiments that finish
  locally must also fit in the ladder budget.
- **Wall-clock per match:** 10 minutes (Kaggle competition limit). Local
  matches typically resolve in seconds for random/heuristic; ISMCTS
  budget is set in Phase 4 to stay under this ceiling with safety margin.
- **Concurrency:** experiments run single-process by default; the ladder
  runs one match at a time. Any parallel local execution must record
  in the registry that concurrency was used (it changes CPU-time-per-decision
  budgets).

## Reporting

Every result reports:

1. **Point estimate** — win rate $\hat p = k / N$.
2. **Wilson 95% CI** — half-width and both endpoints. Never a bare
   proportion, never a normal-approximation CI (Wilson dominates near 0
   and 1 and never leaves $[0, 1]$).
3. **Paired test for agent comparisons on shared seeds** — paired bootstrap
   on the match-level win indicator, or McNemar's test for binary
   outcomes. The paired test respects the seed pinning above.
4. **Multiple comparisons correction** — Bonferroni. Applies whenever an
   experiment tests more than one hypothesis simultaneously (Phase 5 H4
   drops one feature at a time — corrects across features).

Reporting artifacts:

- `experiments/registry.md` — one row per experiment, with Wilson CI +
  paired p-value + verdict in the Actual column.
- `docs/research.md` — H1–H4 verdicts.
- `figures/` — one PNG per exploratory sensitivity sweep.

## Amendment policy

Changes to $N$, $K$, seed policy, or reporting rules require:

1. An entry in [`writeup/decision-journal.md`](../writeup/decision-journal.md)
   explaining the change.
2. An updated `experiments/registry.md` row for any experiment that ran
   under the old protocol, noting the amendment date.
3. If the change is post-Phase-2 (i.e. after the H1–H4 lock at tag
   `v0.3-hypotheses`), the change must not alter the tests of those
   pre-registered hypotheses without a Threats-to-Validity note in the
   Phase 6 writeup.

## References

- [`docs/research.md`](research.md) — the four hypotheses this protocol tests.
- [`exercises/ex05_statistical_inference.md`](../exercises/ex05_statistical_inference.md)
  — sample-size derivation (Phase 5; may tighten the N above).
- [`docs/adr/adr-004-terminal-reward-not-shaped.md`](adr/adr-004-terminal-reward-not-shaped.md) — reward signal this protocol scores.
