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
| 2 — Study & Hypothesis Pre-Registration | Sutton & Barto Ch 1–3, 8; MCTS survey; H1–H4 lock | 🔄 in progress | `v0.3-hypotheses` |
| 3 — ISMCTS Core | Search, determinization, UCB1, H1 test | ⏳ | `v0.4-ismcts-core` |
| 4 — Evaluator + Deck + Sim Submission | Heuristic evaluator, deck selection | ⏳ | `v0.5-sim-submission` |
| 5 — Hypothesis Testing & Statistical Rigor | H2–H4 tests, sensitivity sweeps | ⏳ | — |
| 6 — Strategy Writeup & Submission | Strategy category deliverable | ⏳ | `v1.0.0` |

**Hard deadlines:** Simulation category **16–17 Aug 2026**, Strategy
category **13 Sep 2026**.

Kaggle submissions so far:

| # | Agent | Tag | Public score | Notes |
|---|---|---|---|---|
| 1 | RandomAgent | `v0.1-setup` | 373.7 | Ladder floor. |
| 2 | HeuristicAgent (first-`maxCount` selector) | `v0.2-baselines` | pending stabilization | Beats random locally at 0.755 win rate (Wilson 95% CI [0.691, 0.809], N = 200). |

## Approach

Full rationale lives in [`docs/adr/`](docs/adr/):

- [ADR-001 — Why ISMCTS](docs/adr/adr-001-why-ismcts.md) — over MCTS / CFR / RL.
- [ADR-002 — Why This Deck](docs/adr/adr-002-why-this-deck.md) — pending Phase 4.
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
decks/         selected deck (Phase 0 placeholder; Phase 4 replaces)
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
