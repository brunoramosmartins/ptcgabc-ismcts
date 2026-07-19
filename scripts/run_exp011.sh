#!/usr/bin/env bash
# EXP-011 deck re-evaluation vs the real field (see experiments/registry.md
# BEFORE running — the entry pre-registers the selection rule and branches).
#
#   bash scripts/run_exp011.sh
#
# Our seat: ismcts-selfdeck (the exact shipping condition after EXP-010)
# piloting each homemade challenger. Opponent: heuristic piloting each of
# the four official starter decks. The current-v1 rows are NOT rerun —
# EXP-010's selfdeck arm is cell-identical (same agent, seeds, iterations,
# opponents) and the registry entry commits to reusing it:
#
#   results/exp010_ismcts-selfdeck_vs_<opp>.jsonl  ==  current-v1 cells
#
# Paired seeds per cell, so challenger-vs-incumbent contrasts are
# McNemar-ready on shared (opponent, seed) instances. Trajectory corpus
# stays on. Per-match JSONL flush + --append make every cell resumable.
set -euo pipefail

CHALLENGERS=(v1-tuned aggro-fire emboar-evolution)
OPPS=(iono dragapult-ex mega-abomasnow-ex-official mega-lucario-ex)
N="${EXP011_N:-50}"
ITERS="${EXP011_ITERS:-1000}"

mkdir -p results

# Resume a cell: run only the seeds still missing from $OUT.
run_cell() {
  local deck="$1" opp="$2"
  local out="results/exp011_${deck}_vs_${opp}.jsonl"
  local traj="results/exp011_traj_${deck}_vs_${opp}.jsonl.gz"
  local done=0
  [[ -f "$out" ]] && done=$(wc -l < "$out")
  if (( done >= N )); then
    echo "== skip $(basename "$out") (complete: ${done}/${N})"
    return 0
  fi
  echo "== $(basename "$out") (resuming at seed $((1 + done)))"
  python scripts/local_ladder.py \
    --agent-a ismcts-selfdeck --agent-b heuristic \
    --deck-a "decks/candidates/${deck}.csv" \
    --deck-b "decks/candidates/${opp}.csv" \
    --matches "$((N - done))" --seed-start "$((1 + done))" \
    --iterations "$ITERS" \
    --out "$out" --append \
    --log-trajectories "$traj"
}

for deck in "${CHALLENGERS[@]}"; do
  for opp in "${OPPS[@]}"; do
    run_cell "$deck" "$opp"
  done
done

echo "EXP-011 complete. current-v1 cells come from EXP-010's selfdeck arm."
echo "Fill the Actual column in experiments/registry.md before touching"
echo "ADR-002 or decks/selected/."
