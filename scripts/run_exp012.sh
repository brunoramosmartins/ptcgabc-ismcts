#!/usr/bin/env bash
# EXP-012 final validation tournament (#28) — see experiments/registry.md
# BEFORE running; the entry pre-registers the consistency gate and branches.
#
#   bash scripts/run_exp012.sh
#
# Our seat: ismcts-main — the SHIPPING configuration end-to-end
# (selfdeck determinization + Policy C adaptive time budget, constants
# pinned to submissions/ismcts_main.py) piloting current-v1. Opponent:
# heuristic piloting each official starter. Seeds 1..50 match
# EXP-010/011's current-v1 cells, so the fixed-1000-iterations
# instrument vs the shipping clock is a paired contrast on shared
# (opponent, seed) instances.
#
# DELIBERATELY ladder-faithful — three differences from run_exp011.sh:
#   * NO --overage-bank: Policy C budgets under the default 600 s bank
#     by construction; proving that under the real clock is part of the
#     validation. A TIMEOUT here is a FINDING (gate failure), not an
#     artifact to raise away.
#   * NO --log-trajectories: recording overhead would contaminate the
#     per-match seconds this run reads operationally.
#   * NO --iterations flag: the arm ignores it; the clock binds.
set -euo pipefail

OPPS=(iono dragapult-ex mega-abomasnow-ex-official mega-lucario-ex)
N="${EXP012_N:-50}"

mkdir -p results

run_cell() {
  local opp="$1"
  local out="results/exp012_ismcts-main_vs_${opp}.jsonl"
  local done=0
  [[ -f "$out" ]] && done=$(wc -l < "$out")
  if (( done >= N )); then
    echo "== skip $(basename "$out") (complete: ${done}/${N})"
    return 0
  fi
  echo "== $(basename "$out") (resuming at seed $((1 + done)))"
  python scripts/local_ladder.py \
    --agent-a ismcts-main --agent-b heuristic \
    --deck-a "decks/selected/deck.csv" \
    --deck-b "decks/candidates/${opp}.csv" \
    --matches "$((N - done))" --seed-start "$((1 + done))" \
    --out "$out" --append
}

for opp in "${OPPS[@]}"; do
  run_cell "$opp"
done

echo "EXP-012 complete. Apply the pre-registered gate via the analysis"
echo "script and fill the Actual column in experiments/registry.md"
echo "BEFORE touching submissions/ or the submission log."
