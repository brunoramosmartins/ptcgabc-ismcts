#!/usr/bin/env bash
# .github/setup/milestones.sh
# Create one GitHub milestone per roadmap phase (0..7) with due dates.
#
# Requires: gh CLI (uses gh's built-in `-q` jq expression, not the jq binary).
# Idempotent: skips titles that already exist on the repo.
#
# Usage:
#   bash .github/setup/milestones.sh

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not installed. See https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Target repo: $REPO"

existing="$(gh api "repos/$REPO/milestones?state=all&per_page=100" -q '.[].title')"

create_milestone() {
  local title="$1" description="$2" due="$3"

  if grep -Fxq "$title" <<<"$existing"; then
    printf "  skip  %s (already exists)\n" "$title"
    return
  fi

  if [[ -n "$due" ]]; then
    gh api "repos/$REPO/milestones" -X POST \
      -f title="$title" \
      -f description="$description" \
      -f due_on="${due}T23:59:59Z" >/dev/null
  else
    gh api "repos/$REPO/milestones" -X POST \
      -f title="$title" \
      -f description="$description" >/dev/null
  fi
  printf "  ok    %s\n" "$title"
}

echo "Creating milestones..."

create_milestone \
  "Phase 0 — Setup & Reconnaissance" \
  "30 Jun – 6 Jul 2026. Verify SDK access, scaffold repo, ship random agent to the ladder." \
  "2026-07-06"

create_milestone \
  "Phase 1 — Environment Formalization & Baselines" \
  "7 Jul – 13 Jul 2026. Formalize env; finalize benchmark protocol; heuristic baseline shipped." \
  "2026-07-13"

create_milestone \
  "Phase 2 — Study & Hypothesis Pre-Registration" \
  "14 Jul – 20 Jul 2026. Study MCTS/ISMCTS; lock hypotheses H1–H4." \
  "2026-07-20"

create_milestone \
  "Phase 3 — ISMCTS Core" \
  "21 Jul – 3 Aug 2026. ISMCTS with random rollouts; first H1 test; v0 submission." \
  "2026-08-03"

create_milestone \
  "Phase 4 — Evaluator + Deck + Sim Submission" \
  "4 Aug – 17 Aug 2026. Heuristic evaluator, meta deck, Simulation Category final submission." \
  "2026-08-17"

create_milestone \
  "Phase 5 — Hypothesis Testing, Sensitivity & Statistical Rigor" \
  "18 Aug – 7 Sep 2026. Test H2/H3/H4; finalize statistical apparatus." \
  "2026-09-07"

create_milestone \
  "Phase 6 — Strategy Writeup & Submission" \
  "8 Sep – 13 Sep 2026. Compress writeup ≤2000 words; Strategy Category final submission." \
  "2026-09-13"

create_milestone \
  "Phase 7 — Portfolio Polish" \
  "14 Sep 2026 onward. Long-form article, TIL series, extended README, optional learned evaluator." \
  ""

echo "Done."
