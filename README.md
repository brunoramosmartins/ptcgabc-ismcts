# ptcgabc-ismcts

Portfolio-grade research project exploring decision-making under
uncertainty through **Information-Set Monte Carlo Tree Search
(ISMCTS)**. Developed for the Kaggle **Pokémon TCG AI Battle Challenge**
with emphasis on reproducibility, experimentation, and scientific
reporting.

The project frames the competition as an investigation of one research
question — *when is ISMCTS a good choice for imperfect-information card
games?* — tested via four pre-registered hypotheses (H1–H4).

## Status

| Phase | Focus | Status | Tag |
|---|---|---|---|
| 0 — Setup & Reconnaissance | SDK, scaffold, random agent submitted | ✅ | `v0.1-setup` |
| 1 — Environment & Baselines | MDP formalization, benchmark protocol, heuristic baseline | ✅ | `v0.2-baselines` |
| 2 — Study & Hypothesis Pre-Registration | Sutton & Barto Ch 1–3, 8; MCTS survey; H1–H4 lock | ✅ | `v0.3-hypotheses` |
| 3 — ISMCTS Core | Search, determinization, UCB1, H1 test, diagnostic ladder | ✅ | `v0.4-ismcts-core` |
| 4 — Evaluator + Deck + Sim Submission | Deck selection, time budget, determinization comparison | 🔄 in progress | `v0.5-sim-submission` |
| 5 — Hypothesis Testing & Statistical Rigor | H3/H4 tests, sensitivity sweeps (H2 tested early, in Phase 4) | ⏳ | — |
| 6 — Strategy Writeup & Submission | Strategy category deliverable | ⏳ | `v1.0.0` |

**Hard deadlines:** Simulation category **16–17 Aug 2026**, Strategy
category **13 Sep 2026**.

## Findings so far

Full evidence in [`experiments/registry.md`](experiments/registry.md)
(EXP-001 … EXP-010); each claim below names its experiment.

- **H1 supported — under the condition it was stated for.** With the
  opponent's list known (mirror), SO-ISMCTS at 1000 iterations beats the
  deterministic heuristic 0.780, Wilson 95% CI [0.742, 0.814], N = 500
  (EXP-003). The diagnostic ladder attributes the value mostly to search
  itself (PIMC +24 pp over heuristic; the shared info-set tree adds
  +3.8 pp, n.s.; the perfect-information ceiling is only +4.8 pp above
  ISMCTS — EXP-004/005).
- **The central finding to date is a construct-validity gap.** On the
  Kaggle ladder the opponent's list is hidden; filling hidden zones with
  a dummy card erases the entire search advantage: 0.506, Wilson
  [0.462, 0.550] on the same 500 seeds — a paired −27.4 pp, McNemar
  p = 1.2e-17 (EXP-009). Deep search against a wrong opponent model is
  not neutral, it is confidently wrong. EXP-010 (running) prices the
  cheapest deployable fix: assume the opponent plays our own list.
- **H2 not supported.** Heuristic-guided rollouts did not beat random
  rollouts at a fixed iteration budget (paired McNemar p = 0.279,
  EXP-006); the pre-registered rule kept random rollouts.
- **Deck and budget are settled (provisionally).** `current-v1` won a
  four-candidate round-robin on the pre-registered maximin rule
  (EXP-007; ADR-002, with a recorded erratum — revision gated on
  EXP-011), and the submission runs an adaptive per-move time budget
  derived from the live overage bank: 0 forfeits, cumulative p99
  310.7 s against a 540 s target (EXP-008).

## Kaggle submissions

Details in [`docs/submission-log.md`](docs/submission-log.md). Ladder
caveat, measured on our own frozen heuristic (drift 527.9 → 536.0 →
497.8 over 11 days): **absolute ratings are not comparable across
dates** — only differences read simultaneously are.

| # | Agent | Public score | Notes |
|---|---|---|---|
| 1 | RandomAgent | 364.5 (final, inactive) | Ladder floor; validated the pipeline. |
| 2 | HeuristicAgent (first-`maxCount` selector) | 497.8 (final, inactive) | Its own drift measures the ladder's non-stationarity. |
| 3 | SO-ISMCTS, 500 fixed iters, filler determinization | 475.4 (7 d) | **Loses to our own heuristic on the ladder** while winning 78% locally — the gap EXP-009 then reproduced and priced locally. |
| 4 | SO-ISMCTS + adaptive time budget (Policy C) | converging | Same deck and stack as #3, differing only in budget policy — a drift-immune A/B read. |

## Approach

Full rationale lives in [`docs/adr/`](docs/adr/):

- [ADR-001 — Why ISMCTS](docs/adr/adr-001-why-ismcts.md) — over MCTS / CFR / RL.
- [ADR-002 — Why This Deck](docs/adr/adr-002-why-this-deck.md) — accepted (EXP-007), with a recorded erratum; revision gated on EXP-011.
- [ADR-003 — Hand-crafted heuristic evaluator, not learned](docs/adr/adr-003-heuristic-not-learned-evaluator.md).
- [ADR-004 — Terminal reward, no shaping](docs/adr/adr-004-terminal-reward-not-shaped.md).

Formal environment specification: [`docs/mdp-formalization.md`](docs/mdp-formalization.md).

Research question, hypotheses, and verdicts: [`docs/research.md`](docs/research.md).

Statistical protocol every hypothesis test respects:
[`docs/benchmark-protocol.md`](docs/benchmark-protocol.md).

## Repository layout

```
agents/        random / heuristic / ISMCTS variants — plus a Kaggle-facing shim
env/           adapter over the cabt engine (obs dict interface)
search/        ISMCTS four-phase loop + determinization (Phase 3)
evaluator/     heuristic evaluator + rollout policies (Phase 4)
stats/         Wilson, paired bootstrap, McNemar
scripts/       local_ladder, submit, per-experiment exp_*.py
submissions/   standalone Kaggle main.py variants (one per submitted agent)
decks/         candidates (incl. the 4 official starters) + selected `current-v1`
notebooks/     study notebooks (GridWorld MDP) + experiment analysis
tests/         author runs `pytest tests/` — Claude Code never runs tests
docs/          research.md, engineering.md, mdp-formalization.md, benchmark-protocol.md,
               rules-summary.md, game-primer.md, submission-log.md, risk-register.md,
               adr/*
experiments/   registry.md — every experiment logged BEFORE running
exercises/     per-phase mathematical exercises (ex01_environment, sutton-barto-ch01/02/03/08)
notes/         per-phase working notes (Lessons Learned / Failed Attempts sections)
writeup/       decision-journal.md, outline.md, writeup.md (Strategy submission ≤ 2000 words)
tils/          "Today I Learned" drafts (Hook / Insight / Example / Takeaway)
results/       per-match JSONL logs (gitignored except .gitkeep)
figures/       PNG/PDF outputs (gitignored except .gitkeep)
data/kaggle/   competition-provided CSVs and reference material
```

## Getting started

Python 3.11 on WSL2 (Ubuntu on Windows 11 host). Install recipe in
[`docs/engineering.md`](docs/engineering.md) — note the `vec_noise`
work-around for `kaggle-environments`.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install --no-deps kaggle-environments
pip install requests flask jsonschema

# Verify the PTCG env is registered:
python -c "from kaggle_environments import make; print(type(make('cabt')))"
```

Run the local head-to-head runner:

```bash
python scripts/local_ladder.py \
    --agent-a heuristic \
    --agent-b random \
    --matches 200 \
    --seed-start 1 \
    --out results/heuristic_vs_random.jsonl
```

Build a Kaggle submission bundle:

```bash
python scripts/submit.py \
    --main submissions/heuristic_main.py \
    --out submission-heuristic.tar.gz
```

## Research hygiene

Three rules are enforced across the project:

1. Every experiment is registered in
   [`experiments/registry.md`](experiments/registry.md) **before** it
   runs.
2. Every Kaggle submission is logged in
   [`docs/submission-log.md`](docs/submission-log.md) **before** upload.
3. Every phase note ends with `## Lessons Learned` and `## Failed
   Attempts`. These feed the writeup's Threats-to-Validity section.

Win rates always report with Wilson 95% CIs; paired agent comparisons
use paired bootstrap or McNemar's test; multiple comparisons carry
Bonferroni-corrected p-values.

## Future work (post-competition)

Board-game teaching artifacts and other portfolio extensions deliberately
outside the roadmap live in [`notes/deferred-projects.md`](notes/deferred-projects.md).
Includes an S&B-Ch1 tic-tac-toe port with live value-function
visualization and a checkers/damas MCTS artifact.

## License

MIT — see [LICENSE](LICENSE).
