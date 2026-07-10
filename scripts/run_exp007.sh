#!/usr/bin/env bash
# EXP-007 deck round-robin (see experiments/registry.md before running).
#
#   bash scripts/run_exp007.sh ismcts-guided   # or: ismcts
#
# 4 candidates, both seat orderings per pair, 50 paired seeds each
# => 12 runs, 600 matches. Sequential on purpose (one engine at a time);
# per-match JSONL flush makes every run resumable by rerunning only the
# missing pair (delete its partial file first).
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
    if [[ -s "$OUT" ]]; then
      echo "== skip ${A} vs ${B} (exists: $OUT)"
      continue
    fi
    echo "== ${A} vs ${B}"
    python scripts/local_ladder.py \
      --agent-a "$AGENT" --agent-b "$AGENT" \
      --deck-a "decks/candidates/${A}.csv" \
      --deck-b "decks/candidates/${B}.csv" \
      --matches "$MATCHES" --seed-start 1 --iterations "$ITERS" \
      --out "$OUT"
  done
done
echo "EXP-007 round-robin complete."
