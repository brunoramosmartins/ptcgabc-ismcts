#!/usr/bin/env bash
# .github/setup/labels.sh
# Create the project's GitHub labels.
#
# Requires: gh CLI, authenticated against the target repo (gh auth status).
# Idempotent: --force overwrites color/description if a label already exists.
#
# Usage:
#   bash .github/setup/labels.sh

set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not installed. See https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

label() {
  local name="$1" color="$2" desc="$3"
  gh label create "$name" --color "$color" --description "$desc" --force >/dev/null
  printf "  ok    %s\n" "$name"
}

echo "Creating labels..."

# type: kind of work
label "type:feat"        "a2eeef" "New feature or agent code"
label "type:docs"        "0075ca" "Documentation"
label "type:test"        "cfd3d7" "Tests"
label "type:chore"       "7057ff" "Setup, config, infra"
label "type:research"    "d876e3" "Study notes, exercises, TIL drafts"
label "type:experiment"  "fbca04" "Controlled experiment (registered in experiments/registry.md)"
label "type:hypothesis"  "b60205" "Tests a pre-registered hypothesis H1-H4"
label "type:statistics"  "006b75" "Statistical apparatus (Wilson, bootstrap, McNemar)"
label "type:submission"  "0e8a16" "Kaggle ladder submission"

# phase: roadmap phase
for i in 0 1 2 3 4 5 6 7; do
  label "phase:$i" "ededed" "Phase $i roadmap work"
done

# hypothesis: which of H1-H4
for h in 1 2 3 4; do
  label "hypothesis:h$h" "f9d0c4" "Related to pre-registered hypothesis H$h"
done

# status
label "status:blocked" "b60205" "Blocked on external dependency"

echo "Done."
