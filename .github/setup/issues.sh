#!/usr/bin/env bash
# .github/setup/issues.sh
# Seed the 42 roadmap issues (#1..#42) mapped to milestones and labels.
#
# Requires: gh CLI, authenticated (uses gh's built-in `-q`, not the jq binary).
# Labels and milestones must already exist (run labels.sh and milestones.sh first).
# Idempotent: an issue with an identical title is skipped rather than duplicated.
#
# Usage:
#   bash .github/setup/issues.sh

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not installed." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh not authenticated." >&2
  exit 1
fi

# Snapshot titles that already exist so we can skip duplicates.
existing_titles="$(gh issue list --state all --limit 500 --json title -q '.[].title')"

# mk_issue TITLE MILESTONE LABELS_CSV  <<'EOF' body EOF
mk_issue() {
  local title="$1" milestone="$2" labels="$3"
  local body
  body="$(cat)"

  if grep -Fxq "$title" <<<"$existing_titles"; then
    printf "  skip  %s\n" "$title"
    return
  fi

  gh issue create \
    --title "$title" \
    --milestone "$milestone" \
    --label "$labels" \
    --body "$body" >/dev/null
  printf "  ok    %s\n" "$title"
}

M0="Phase 0 — Setup & Reconnaissance"
M1="Phase 1 — Environment Formalization & Baselines"
M2="Phase 2 — Study & Hypothesis Pre-Registration"
M3="Phase 3 — ISMCTS Core"
M4="Phase 4 — Evaluator + Deck + Sim Submission"
M5="Phase 5 — Hypothesis Testing, Sensitivity & Statistical Rigor"
M6="Phase 6 — Strategy Writeup & Submission"

echo "Creating issues..."

# ============================================================================
# Phase 0 (Issues #1..#5)
# ============================================================================

mk_issue "[Phase 0] Verify Kaggle access and install SDK" \
  "$M0" "phase:0,type:chore" <<'EOF'
## Context
Roadmap: Phase 0, Issue #1. Unblock everything downstream — no SDK, no work.

## Tasks
- [ ] Register for the PTCG AI Battle Challenge on Kaggle.
- [ ] Complete Kaggle identity verification.
- [ ] Install `kaggle-environments` and the `cabt` SDK; confirm `import cabt` works locally.
- [ ] Note install steps in `docs/engineering.md`.

## Definition of Done
- [ ] SDK importable from a fresh Python session.
- [ ] Install steps captured in `docs/engineering.md`.

## References
- Roadmap: `roadmap-ptcgabc-ismcts-v2.md` — Phase 0
EOF

mk_issue "[Phase 0] Learn PTCG basics" \
  "$M0" "phase:0,type:research" <<'EOF'
## Context
Roadmap: Phase 0, Issue #2. Enough game knowledge to reason about strategy.

## Tasks
- [ ] Read official Pokémon TCG rules.
- [ ] Play a few matches (online or paper) to internalize turn structure.
- [ ] Write `docs/game-primer.md` (author-facing narrative primer).
- [ ] Write `docs/rules-summary.md` (rigorous, terse rules reference).

## Definition of Done
- [ ] Can explain turn structure, energy, damage resolution, prize cards, and win conditions from memory.
- [ ] Both docs committed with real content (not just headings).

## References
- Roadmap: Phase 0
EOF

mk_issue "[Phase 0] Scaffold repository and research infrastructure" \
  "$M0" "phase:0,type:chore" <<'EOF'
## Context
Roadmap: Phase 0, Issue #3. The v2 skeleton — every folder, every research doc.

## Tasks
- [ ] Confirm all directories exist per `Repository Structure` in the roadmap.
- [ ] `docs/research.md`, `docs/engineering.md`, `docs/benchmark-protocol.md` (skeleton), `docs/submission-log.md`, `docs/risk-register.md`.
- [ ] `experiments/registry.md` (empty template).
- [ ] `docs/adr/` folder present with ADR skeletons.
- [ ] `.claude/CLAUDE.md` v2 present.
- [ ] `.github/` templates and setup scripts present.

## Definition of Done
- [ ] Every path listed in the roadmap's `Repository Structure` exists.
- [ ] `pyproject.toml`, `requirements.txt`, `LICENSE`, `.gitignore` at repo root.

## References
- Roadmap: Phase 0, `Repository Structure` section
EOF

mk_issue "[Phase 0] Draft ADR-001, ADR-003, ADR-004" \
  "$M0" "phase:0,type:docs" <<'EOF'
## Context
Roadmap: Phase 0, Issue #4. ADR-002 (deck) is deferred to Phase 4.

## Tasks
- [ ] Fill `docs/adr/adr-001-why-ismcts.md` — motivate ISMCTS over MCTS / CFR / RL.
- [ ] Fill `docs/adr/adr-003-heuristic-not-learned-evaluator.md` — why heuristic over learned.
- [ ] Fill `docs/adr/adr-004-terminal-reward-not-shaped.md` — why terminal reward, no shaping.

## Definition of Done
- [ ] Each ADR has all four sections filled (Context, Decision, Consequences, Alternatives).
- [ ] Each ADR references relevant literature.

## References
- Roadmap: Phase 0
EOF

mk_issue "[Phase 0] Ship random agent to the Kaggle ladder" \
  "$M0" "phase:0,type:submission,type:feat" <<'EOF'
## Context
Roadmap: Phase 0, Issue #5. First ladder submission — establishes the pipeline.

## Tasks
- [ ] Implement `agents/random_agent.py`.
- [ ] Implement `scripts/submit.py` (bundle + upload).
- [ ] Register EXP-001 in `experiments/registry.md` BEFORE the submission run.
- [ ] Log submission in `docs/submission-log.md` BEFORE upload.
- [ ] Submit; wait for initial rating to stabilize; record actual rating in the log.

## Definition of Done
- [ ] Random agent visible on the Kaggle ladder.
- [ ] `docs/submission-log.md` entry with git tag `v0.1-setup`, commit hash, initial rating.
- [ ] `writeup/decision-journal.md` initialized with a Phase 0 entry.

## References
- Roadmap: Phase 0
- Tag on completion: `v0.1-setup`
EOF

# ============================================================================
# Phase 1 (Issues #6..#10)
# ============================================================================

mk_issue "[Phase 1] Formalize the environment" \
  "$M1" "phase:1,type:docs,type:research" <<'EOF'
## Context
Roadmap: Phase 1, Issue #6. Rigorous MDP-style formalization of the imperfect-information game.

## Tasks
- [ ] Define state space $S$: public + private components; mark unobservables.
- [ ] Define action space $A(s)$; encoding scheme.
- [ ] Define reward $R$: terminal-only (see ADR-004).
- [ ] Define information sets $I(s)$; prove policies must be $I$-measurable.
- [ ] Render both diagrams in `docs/mdp-formalization.md`: logical flow + software pipeline.

## Definition of Done
- [ ] `docs/mdp-formalization.md` complete with both diagrams.
- [ ] Formal definitions match the code in `env/`.

## References
- Roadmap: Phase 1
- Exercises: `exercises/ex01_environment.md`
EOF

mk_issue "[Phase 1] Finalize benchmark protocol" \
  "$M1" "phase:1,type:docs" <<'EOF'
## Context
Roadmap: Phase 1, Issue #7. The reference every hypothesis test respects.

## Tasks
- [ ] Choose N matches per comparison (respect sample-size analysis in `ex05`).
- [ ] Choose K seeds; pin RNG seed policy.
- [ ] Pin deck version convention (git tag on `decks/selected/deck.json`).
- [ ] Document hardware and per-match wall-clock budget (10 min).
- [ ] Reporting rules: Wilson CIs, paired bootstrap, McNemar, Bonferroni.

## Definition of Done
- [ ] `docs/benchmark-protocol.md` finalized (no TBDs left).
- [ ] Every value justified in one line.

## References
- Roadmap: Phase 1
- Exercises: `exercises/ex05_statistical_inference.md`
EOF

mk_issue "[Phase 1] Implement heuristic baseline agent" \
  "$M1" "phase:1,type:feat" <<'EOF'
## Context
Roadmap: Phase 1, Issue #8. Baseline that beats random; comparison target for ISMCTS.

## Tasks
- [ ] Implement `agents/heuristic_agent.py`.
- [ ] Implement `scripts/local_ladder.py` (round-robin runner).
- [ ] Add unit tests in `tests/test_agents.py`.

## Definition of Done
- [ ] Heuristic beats random by a Wilson-CI-separated margin.
- [ ] Results in `experiments/registry.md` (EXP-002).

## References
- Roadmap: Phase 1
EOF

mk_issue "[Phase 1] Register EXP-001 and EXP-002 in the experiment registry" \
  "$M1" "phase:1,type:experiment" <<'EOF'
## Context
Roadmap: Phase 1, Issue #9. Backfill the registry with the baselines.

## Tasks
- [ ] EXP-001: random agent baseline — configuration, expected result, actual result.
- [ ] EXP-002: heuristic agent baseline — configuration, expected result, actual result.

## Definition of Done
- [ ] Two rows in `experiments/registry.md`, both fully populated.

## References
- Roadmap: Phase 1
EOF

mk_issue "[Phase 1] Submit heuristic to the ladder; log submission" \
  "$M1" "phase:1,type:submission" <<'EOF'
## Context
Roadmap: Phase 1, Issue #10.

## Tasks
- [ ] Log submission in `docs/submission-log.md` BEFORE upload.
- [ ] Submit heuristic agent; record initial rating.

## Definition of Done
- [ ] Heuristic live on the ladder.
- [ ] Log entry: git tag `v0.2-baselines`, commit hash, rating.

## References
- Roadmap: Phase 1
- Tag on completion: `v0.2-baselines`
EOF

# ============================================================================
# Phase 2 (Issues #11..#15)
# ============================================================================

mk_issue "[Phase 2] Study Sutton & Barto + MCTS/ISMCTS papers" \
  "$M2" "phase:2,type:research" <<'EOF'
## Context
Roadmap: Phase 2, Issue #11. Dedicated study week — no new agent code.

## Tasks
- [ ] Sutton & Barto Ch 1-3 and Ch 8.
- [ ] Browne et al. (2012) — MCTS survey.
- [ ] Cowling, Powley, Whitehouse (2012) — ISMCTS.
- [ ] Optional: Long et al. (2010) — determinization.

## Definition of Done
- [ ] Reading log entries in `notes/phase2-*.md`.

## References
- Roadmap: Phase 2
EOF

mk_issue "[Phase 2] Write phase-2 study notes" \
  "$M2" "phase:2,type:docs,type:research" <<'EOF'
## Context
Roadmap: Phase 2, Issue #12.

## Tasks
- [ ] `notes/phase2-mcts-fundamentals.md` — MCTS four phases, UCB1, convergence.
- [ ] `notes/phase2-ismcts-paper-notes.md` — determinization, strategy fusion, algorithm.

## Definition of Done
- [ ] Both files end with `## Lessons Learned` and `## Failed Attempts` sections.

## References
- Roadmap: Phase 2
EOF

mk_issue "[Phase 2] Complete exercises ex02_mcts_derivations" \
  "$M2" "phase:2,type:research" <<'EOF'
## Context
Roadmap: Phase 2, Issue #13.

## Tasks
- [ ] Derive UCB1 from Chernoff-Hoeffding; identify $\sqrt{2\ln t/n_a}$.
- [ ] State MCTS asymptotic consistency (perfect information); sketch proof.
- [ ] Explain the ISMCTS extension and $a^* = \arg\max_a \mathbb{E}_{h \sim P(h \mid I)}[Q(I,a,h)]$.
- [ ] Toy example of strategy fusion.
- [ ] Estimate branching factor at a representative mid-game state.

## Definition of Done
- [ ] `exercises/ex02_mcts_derivations.md` all 5 exercises answered.

## References
- Roadmap: Phase 2
EOF

mk_issue "[Phase 2] Lock hypotheses H1-H4 in docs/research.md" \
  "$M2" "phase:2,type:hypothesis,type:docs,hypothesis:h1,hypothesis:h2,hypothesis:h3,hypothesis:h4" <<'EOF'
## Context
Roadmap: Phase 2, Issue #14. **Pre-registration commit** — git tag proves the timestamp.

## Tasks
- [ ] Finalize H1..H4 wording in `docs/research.md` (no ambiguity in metric/test).
- [ ] Mark hypotheses LOCKED after review.
- [ ] Commit is later tagged `v0.3-hypotheses` by the author.

## Definition of Done
- [ ] `docs/research.md` H1-H4 rows are frozen — no future edits without a research-log entry.
- [ ] Verdict column shows `_pending_` for all four.

## References
- Roadmap: Phase 2
- Tag on completion: `v0.3-hypotheses`
EOF

mk_issue "[Phase 2] Draft TIL #1 — MDPs vs info-set games" \
  "$M2" "phase:2,type:docs,type:research" <<'EOF'
## Context
Roadmap: Phase 2, Issue #15.

## Tasks
- [ ] Draft `tils/til-01-mdp-vs-info-set-games.md`.
- [ ] Format: Hook / Insight / Example / Takeaway.

## Definition of Done
- [ ] TIL draft committed (polish happens in Phase 7).

## References
- Roadmap: Phase 2
EOF

# ============================================================================
# Phase 3 (Issues #16..#22)
# ============================================================================

mk_issue "[Phase 3] Implement information-set tree node structure" \
  "$M3" "phase:3,type:feat,type:test" <<'EOF'
## Context
Roadmap: Phase 3, Issue #16.

## Tasks
- [ ] Implement `search/node.py` with info-set-aware fields (visits, cumulative value, children by action).
- [ ] Unit tests in `tests/test_search.py`.

## Definition of Done
- [ ] Node supports insert / lookup by action; visits and value updates work.
- [ ] Tests written (author runs `pytest tests/`).

## References
- Roadmap: Phase 3
EOF

mk_issue "[Phase 3] Implement determinization sampling" \
  "$M3" "phase:3,type:feat,type:test" <<'EOF'
## Context
Roadmap: Phase 3, Issue #17. Sample a hidden state $h$ compatible with the information set $I$.

## Tasks
- [ ] Implement `search/determinize.py`.
- [ ] Validate sampled distribution respects the prior $P(h \mid I)$.
- [ ] Unit tests.

## Definition of Done
- [ ] Sampled hidden states pass known-state consistency checks.
- [ ] Tests written.

## References
- Roadmap: Phase 3
- Cowling et al. (2012)
EOF

mk_issue "[Phase 3] Implement UCB1 selection and the MCTS four-phase loop" \
  "$M3" "phase:3,type:feat" <<'EOF'
## Context
Roadmap: Phase 3, Issue #18. The core loop.

## Tasks
- [ ] Implement `search/ucb.py`.
- [ ] Wire Selection / Expansion / Rollout / Backpropagation.
- [ ] Respect a simulations-per-decision budget.

## Definition of Done
- [ ] Loop runs to budget without crash; visit counts on the root are sensible.

## References
- Roadmap: Phase 3
EOF

mk_issue "[Phase 3] Wire ISMCTS agent to the environment wrapper" \
  "$M3" "phase:3,type:feat" <<'EOF'
## Context
Roadmap: Phase 3, Issue #19.

## Tasks
- [ ] Implement `agents/ismcts_agent.py` integrating search + env + random rollout.
- [ ] Confirm end-to-end match runs vs the heuristic baseline.

## Definition of Done
- [ ] ISMCTS agent plays a full match without error.

## References
- Roadmap: Phase 3
EOF

mk_issue "[Phase 3] Register EXP-003 (ISMCTS random rollout) in the registry" \
  "$M3" "phase:3,type:experiment" <<'EOF'
## Context
Roadmap: Phase 3, Issue #20. Register BEFORE running the H1 test.

## Tasks
- [ ] Add EXP-003 row: objective, configuration, expected result.

## Definition of Done
- [ ] Row present in `experiments/registry.md` before EXP-003 executes.

## References
- Roadmap: Phase 3
EOF

mk_issue "[Phase 3] Run H1 test — ISMCTS-random vs heuristic" \
  "$M3" "phase:3,type:hypothesis,type:experiment,type:statistics,hypothesis:h1" <<'EOF'
## Context
Roadmap: Phase 3, Issue #21. First controlled test of a pre-registered hypothesis.

## Tasks
- [ ] Run under the benchmark protocol (N matches, K seeds, deck pinned).
- [ ] Compute win-rate difference with Wilson 95% CI.
- [ ] Paired bootstrap p-value on shared match seeds.
- [ ] Record verdict (supported / rejected / inconclusive) in `docs/research.md`.

## Definition of Done
- [ ] H1 row in `docs/research.md` has a verdict + specific CI/p-value.
- [ ] EXP-003 result column filled in the registry.

## References
- Roadmap: Phase 3
- `docs/benchmark-protocol.md`
EOF

mk_issue "[Phase 3] Submit ISMCTS v0 to the Kaggle ladder" \
  "$M3" "phase:3,type:submission" <<'EOF'
## Context
Roadmap: Phase 3, Issue #22.

## Tasks
- [ ] Log submission in `docs/submission-log.md` BEFORE upload.
- [ ] Bundle and submit ISMCTS v0.

## Definition of Done
- [ ] ISMCTS v0 live on the ladder.
- [ ] Log entry with git tag `v0.4-ismcts-core`, commit hash.

## References
- Roadmap: Phase 3
- Tag on completion: `v0.4-ismcts-core`
EOF

# ============================================================================
# Phase 4 (Issues #23..#29)
# ============================================================================

mk_issue "[Phase 4] Design the heuristic evaluator (features + weights)" \
  "$M4" "phase:4,type:feat" <<'EOF'
## Context
Roadmap: Phase 4, Issue #23.

## Tasks
- [ ] Choose feature set (board value, prize progress, hand quality, etc.).
- [ ] Choose weights (justified — this is the target of H4 ablation).
- [ ] Implement `evaluator/heuristic.py`.

## Definition of Done
- [ ] Evaluator produces a scalar value for any observed state.
- [ ] Design documented in `notes/phase4-evaluator-design.md`.

## References
- Roadmap: Phase 4
EOF

mk_issue "[Phase 4] Replace random rollout with heuristic-guided rollout" \
  "$M4" "phase:4,type:feat" <<'EOF'
## Context
Roadmap: Phase 4, Issue #24. Prepares H2 test.

## Tasks
- [ ] Implement heuristic-guided rollout in `evaluator/rollout.py`.
- [ ] Preserve the random-rollout code path (H2 ablation compares them).

## Definition of Done
- [ ] Both rollout policies selectable via config.

## References
- Roadmap: Phase 4
EOF

mk_issue "[Phase 4] Select the meta deck; write ADR-002" \
  "$M4" "phase:4,type:feat,type:docs" <<'EOF'
## Context
Roadmap: Phase 4, Issue #25. Deck concept = 20% of the Strategy score.

## Tasks
- [ ] Evaluate candidate decks in `decks/candidates/`.
- [ ] Pick one; save to `decks/selected/deck.json` + `decks/selected/rationale.md`.
- [ ] Write `docs/adr/adr-002-why-this-deck.md`.

## Definition of Done
- [ ] Deck pinned and referenced in the benchmark protocol.
- [ ] ADR-002 all four sections filled.

## References
- Roadmap: Phase 4
EOF

mk_issue "[Phase 4] Tune hyperparameters (sims, c, determinizations)" \
  "$M4" "phase:4,type:experiment" <<'EOF'
## Context
Roadmap: Phase 4, Issue #26.

## Tasks
- [ ] Sweep simulations/decision within the 10-min match budget.
- [ ] Sweep UCB1 exploration constant $c$.
- [ ] Sweep determinizations per decision.
- [ ] Register each sweep in the experiment registry.

## Definition of Done
- [ ] Chosen values written into config with one-line justification.
- [ ] `figures/hyperparameter-sensitivity.png` (draft).

## References
- Roadmap: Phase 4
EOF

mk_issue "[Phase 4] Time-budget calibration (10-min match limit)" \
  "$M4" "phase:4,type:experiment" <<'EOF'
## Context
Roadmap: Phase 4, Issue #27.

## Tasks
- [ ] Measure wall-clock per decision under chosen hyperparameters.
- [ ] Confirm worst-case matches stay under 10 min.
- [ ] Add safety margin.

## Definition of Done
- [ ] Calibration numbers in `notes/phase4-evaluator-design.md`.

## References
- Roadmap: Phase 4
EOF

mk_issue "[Phase 4] Final local tournament vs internal baselines" \
  "$M4" "phase:4,type:experiment" <<'EOF'
## Context
Roadmap: Phase 4, Issue #28.

## Tasks
- [ ] Register the tournament in `experiments/registry.md`.
- [ ] Run vs random and heuristic baselines under benchmark protocol.
- [ ] Report Wilson CIs on win rates.

## Definition of Done
- [ ] Results written to the registry.
- [ ] `notes/phase4-evaluator-design.md` ends with `## Lessons Learned` + `## Failed Attempts`.

## References
- Roadmap: Phase 4
EOF

mk_issue "[Phase 4] SUBMIT SIMULATION CATEGORY (deadline 16-17 Aug 2026)" \
  "$M4" "phase:4,type:submission" <<'EOF'
## Context
Roadmap: Phase 4, Issue #29. **🚩 HARD DEADLINE: 16-17 August 2026.**

## Tasks
- [ ] Log submission in `docs/submission-log.md` BEFORE upload.
- [ ] Bundle final Simulation Category agent.
- [ ] Submit; wait for confirmation.
- [ ] Tag `v0.5-sim-submission` after acceptance.
- [ ] Create pre-release from the tag.

## Definition of Done
- [ ] Submission accepted by Kaggle.
- [ ] `docs/submission-log.md` fully updated.
- [ ] Pre-release published on GitHub.

## References
- Roadmap: Phase 4
- Tag on completion: `v0.5-sim-submission`
EOF

# ============================================================================
# Phase 5 (Issues #30..#38)
# ============================================================================

mk_issue "[Phase 5] Finalize stats module (wilson, bootstrap, paired_tests)" \
  "$M5" "phase:5,type:feat,type:statistics,type:test" <<'EOF'
## Context
Roadmap: Phase 5, Issue #30.

## Tasks
- [ ] Full implementation of `stats/wilson.py`.
- [ ] Full implementation of `stats/bootstrap.py` (paired).
- [ ] Full implementation of `stats/paired_tests.py` (McNemar + paired sign).
- [ ] `tests/test_stats.py` covering known cases.

## Definition of Done
- [ ] All three modules pass tests (author runs `pytest tests/`).

## References
- Roadmap: Phase 5
- `exercises/ex05_statistical_inference.md`
EOF

mk_issue "[Phase 5] Test H2 — heuristic vs random rollouts" \
  "$M5" "phase:5,type:hypothesis,type:experiment,type:statistics,hypothesis:h2" <<'EOF'
## Context
Roadmap: Phase 5, Issue #31.

## Tasks
- [ ] Register the experiment in `experiments/registry.md` BEFORE running.
- [ ] Run `scripts/exp_ablation_rollout.py`.
- [ ] Paired test on shared match seeds.
- [ ] Record H2 verdict in `docs/research.md`.

## Definition of Done
- [ ] H2 row in `docs/research.md` has a verdict + p-value + CI.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Test H3 — sensitivity to simulations/decision" \
  "$M5" "phase:5,type:hypothesis,type:experiment,type:statistics,hypothesis:h3" <<'EOF'
## Context
Roadmap: Phase 5, Issue #32.

## Tasks
- [ ] Register the experiment BEFORE running.
- [ ] Run `scripts/exp_sensitivity_simulations.py`.
- [ ] Identify the breakpoint where the time budget binds.
- [ ] Record H3 verdict in `docs/research.md`.

## Definition of Done
- [ ] H3 row filled with breakpoint and monotonicity finding.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Test H4 — per-feature evaluator ablation" \
  "$M5" "phase:5,type:hypothesis,type:experiment,type:statistics,hypothesis:h4" <<'EOF'
## Context
Roadmap: Phase 5, Issue #33.

## Tasks
- [ ] Register the experiment BEFORE running.
- [ ] Run `scripts/exp_ablation_evaluator.py` — drop each feature in turn.
- [ ] Paired tests per feature; Bonferroni correction across k features.
- [ ] Record per-feature verdicts in `docs/research.md`.

## Definition of Done
- [ ] H4 row filled with per-feature $\Delta$ + raw and corrected p-values.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Exploratory sensitivity to exploration constant c" \
  "$M5" "phase:5,type:experiment" <<'EOF'
## Context
Roadmap: Phase 5, Issue #34. Exploratory — no pre-registered hypothesis.

## Tasks
- [ ] Register the experiment BEFORE running.
- [ ] Run `scripts/exp_sensitivity_c.py`.
- [ ] Produce a figure for the writeup.

## Definition of Done
- [ ] Figure in `figures/`; registry row filled.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Exploratory sensitivity to determinizations per decision" \
  "$M5" "phase:5,type:experiment" <<'EOF'
## Context
Roadmap: Phase 5, Issue #35. Exploratory.

## Tasks
- [ ] Register the experiment BEFORE running.
- [ ] Run `scripts/exp_sensitivity_determinizations.py`.
- [ ] Produce a figure.

## Definition of Done
- [ ] Figure in `figures/`; registry row filled.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Seed stability — 20 seeds × N matches" \
  "$M5" "phase:5,type:experiment,type:statistics" <<'EOF'
## Context
Roadmap: Phase 5, Issue #36. Measure variance so we know what signal size is credible.

## Tasks
- [ ] Register the experiment BEFORE running.
- [ ] Run `scripts/exp_seed_stability.py`.
- [ ] Interpret variance via Wilson.

## Definition of Done
- [ ] Rating variance reported with a bound; result in the registry.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Register all six Phase-5 experiments" \
  "$M5" "phase:5,type:experiment" <<'EOF'
## Context
Roadmap: Phase 5, Issue #37. Hygiene issue — proof of pre-registration for every P5 experiment.

## Tasks
- [ ] Confirm EXP rows exist for: H2, H3, H4, sensitivity-c, sensitivity-determinizations, seed-stability.
- [ ] Each row filled BEFORE the corresponding run.

## Definition of Done
- [ ] Six rows in `experiments/registry.md` with configuration + expected result BEFORE actual result.

## References
- Roadmap: Phase 5
EOF

mk_issue "[Phase 5] Draft TIL #3 — Wilson vs normal approximation" \
  "$M5" "phase:5,type:docs,type:research" <<'EOF'
## Context
Roadmap: Phase 5, Issue #38. TIL #3 topic per v2: "When Wilson beats the normal approximation, and why the writeup uses it."

## Tasks
- [ ] Draft `tils/til-03-*.md` in Hook/Insight/Example/Takeaway format.

## Definition of Done
- [ ] TIL draft committed (polish in Phase 7).

## References
- Roadmap: Phase 5
EOF

# ============================================================================
# Phase 6 (Issues #39..#42)
# ============================================================================

mk_issue "[Phase 6] Compress decision journal into writeup sections 1-5" \
  "$M6" "phase:6,type:docs" <<'EOF'
## Context
Roadmap: Phase 6, Issue #39. ~1350 words.

## Tasks
- [ ] Section 1: Problem framing (200 words).
- [ ] Section 2: Research question + hypotheses (200 words).
- [ ] Section 3: Approach — ISMCTS + heuristic (300 words).
- [ ] Section 4: Deck concept and rationale (350 words).
- [ ] Section 5: Evaluator design (300 words).

## Definition of Done
- [ ] Draft sections 1-5 in `writeup/writeup.md`.

## References
- Roadmap: Phase 6
EOF

mk_issue "[Phase 6] Assemble sections 6-8 (results + ToV + takeaway)" \
  "$M6" "phase:6,type:docs" <<'EOF'
## Context
Roadmap: Phase 6, Issue #40. ~650 words.

## Tasks
- [ ] Section 6: Experimental results — H1-H4 verdicts with Wilson CIs (400 words).
- [ ] Section 7: Threats to Validity — internal / construct / external / statistical (200 words).
- [ ] Section 8: What we learned — answer to the research question (50 words).

## Definition of Done
- [ ] Draft sections 6-8 in `writeup/writeup.md`.

## References
- Roadmap: Phase 6
EOF

mk_issue "[Phase 6] Polish word count; verify traceability" \
  "$M6" "phase:6,type:docs" <<'EOF'
## Context
Roadmap: Phase 6, Issue #41.

## Tasks
- [ ] Cut to ≤2000 words.
- [ ] Verify every comparative claim links to a specific figure, ADR, or registry entry.
- [ ] Proofread.

## Definition of Done
- [ ] Word count check passes.
- [ ] No unbacked comparative claims.

## References
- Roadmap: Phase 6
EOF

mk_issue "[Phase 6] SUBMIT STRATEGY CATEGORY (deadline 13 Sep 2026)" \
  "$M6" "phase:6,type:submission" <<'EOF'
## Context
Roadmap: Phase 6, Issue #42. **🚩 HARD DEADLINE: 13 September 2026.**

## Tasks
- [ ] Log submission in `docs/submission-log.md` BEFORE upload.
- [ ] Submit `writeup/writeup.md` and media attachments to Kaggle.
- [ ] Tag `v1.0.0` after acceptance.
- [ ] Create stable release from the tag.

## Definition of Done
- [ ] Submission accepted by Kaggle.
- [ ] `v1.0.0` stable release published.

## References
- Roadmap: Phase 6
- Tag on completion: `v1.0.0`
EOF

echo "Done."
