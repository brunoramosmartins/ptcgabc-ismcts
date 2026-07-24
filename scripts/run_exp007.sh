#!/usr/bin/env bash
# EXP-007 deck round-robin (see experiments/registry.md before running).
#
#   bash scripts/run_exp007.sh ismcts-guided   # or: ismcts
#
# 4 candidates, both seat orderings per pair, 50 paired seeds each
# => 12 runs, 600 matches. Sequential on purpose (one engine at a time);
# per-match JSONL flush + --append make every run resumable: rerunning
# the script picks each pair up at the first missing seed.
set -euo pipefail

AGENT="${1:?usage: run_exp007.sh <agent (ismcts-guided|ismcts)>}"
DECKS=(current-v1 v1-tuned aggro-fire emboar-evolution)
MATCHES=50
ITERS=1000

mkdir -p results
for ((i = 0; i < ${#DECKS[@]}; i++)); do
  for ((j = 0; j < ${#DECKS[@]}; j++)); do
    [[ $i -eq $j ]] && continue
    A="${DECKS[$i]}"; B="${DECKS[$j]}"
    OUT="results/exp007_${A}_vs_${B}.jsonl"
    DONE=0
    [[ -f "$OUT" ]] && DONE=$(wc -l < "$OUT")
    if (( DONE >= MATCHES )); then
      echo "== skip ${A} vs ${B} (complete: ${DONE}/${MATCHES})"
      continue
    fi
    echo "== ${A} vs ${B} (resuming at seed $((DONE + 1)))"
    python scripts/local_ladder.py \
      --agent-a "$AGENT" --agent-b "$AGENT" \
      --deck-a "decks/candidates/${A}.csv" \
      --deck-b "decks/candidates/${B}.csv" \
      --matches "$((MATCHES - DONE))" --seed-start "$((DONE + 1))" \
      --iterations "$ITERS" \
      --out "$OUT" --append
  done
done
echo "EXP-007 round-robin complete."
