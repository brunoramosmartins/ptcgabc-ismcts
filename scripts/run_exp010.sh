#!/usr/bin/env bash
# EXP-010 determinization comparison (see experiments/registry.md BEFORE
# running — the entry pre-registers the ship gate and the branches).
#
#   bash scripts/run_exp010.sh
#
# Our seat: current-v1 under three determinization conditions —
# `ismcts-filler` (deployed today), `ismcts-selfdeck` (assume the
# opponent plays our list; deployable), `ismcts` (informed; diagnostic
# ceiling only, NEVER submitted). Opponent: heuristic piloting each of
# the four official starter decks. Paired seeds per cell, so the
# within-deck arm contrasts are McNemar-ready.
#
# First experiment with trajectory recording ON (open-ideas.md,
# trajectory-corpus): one .jsonl.gz per cell, provenance = this script.
# Per-match JSONL flush + --append make every cell resumable: rerunning
# picks each cell up at the first missing seed.
set -euo pipefail

MYDECK="decks/candidates/current-v1.csv"
ARMS=(ismcts-filler ismcts-selfdeck ismcts)
OPPS=(iono dragapult-ex mega-abomasnow-ex-official mega-lucario-ex)
N="${EXP010_N:-50}"
ITERS="${EXP010_ITERS:-1000}"

mkdir -p results

# Resume a cell: run only the seeds still missing from $OUT.
run_cell() {
  local arm="$1" opp="$2"
  local out="results/exp010_${arm}_vs_${opp}.jsonl"
  local traj="results/exp010_traj_${arm}_vs_${opp}.jsonl.gz"
  local done=0
  [[ -f "$out" ]] && done=$(wc -l < "$out")
  if (( done >= N )); then
    echo "== skip $(basename "$out") (complete: ${done}/${N})"
    return 0
  fi
  echo "== $(basename "$out") (resuming at seed $((1 + done)))"
  python scripts/local_ladder.py \
    --agent-a "$arm" --agent-b heuristic \
    --deck-a "$MYDECK" --deck-b "decks/candidates/${opp}.csv" \
    --matches "$((N - done))" --seed-start "$((1 + done))" \
    --iterations "$ITERS" \
    --out "$out" --append \
    --log-trajectories "$traj"
}

for arm in "${ARMS[@]}"; do
  for opp in "${OPPS[@]}"; do
    run_cell "$arm" "$opp"
  done
done

echo "EXP-010 complete. Fill the Actual column in experiments/registry.md"
echo "before touching submissions/ismcts_main.py."
