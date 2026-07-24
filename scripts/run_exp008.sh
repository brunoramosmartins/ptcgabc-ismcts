#!/usr/bin/env bash
# EXP-008 time-budget calibration (see experiments/registry.md and
# notes/phase4-time-budget-calibration.md BEFORE running).
#
#   bash scripts/run_exp008.sh fit       # measure c(it) and the M distribution
#   bash scripts/run_exp008.sh confirm   # Policy-C confirmation run (0 forfeits)
#
# Our deck is the selected list (current-v1); the opponent ranges over
# all four candidates so game length M spans fast mirrors to slow Fire
# grinds. Sequential on purpose (one engine at a time). Per-game JSONL
# flush + --append make every cell resumable: rerunning picks each cell
# up at the first missing seed.
#
# Tunables via env vars (defaults chosen for a sane local wall-clock):
#   FIT_PLAN="iters:games ..."   levels for the fit stage
#   CONF_ITERS / CONF_RESERVE / CONF_MOVES / CONF_N   Policy-C confirm params
set -euo pipefail

STAGE="${1:?usage: run_exp008.sh <fit|confirm>}"
MYDECK="decks/candidates/current-v1.csv"
OPPS=(current-v1 v1-tuned aggro-fire emboar-evolution)

mkdir -p results

# Resume a cell: run only the seeds still missing from $OUT.
# Args: OUT target-count seed-base -- extra exp_timing.py flags...
run_cell() {
  local out="$1" target="$2" base="$3"; shift 3
  local done=0
  [[ -f "$out" ]] && done=$(wc -l < "$out")
  if (( done >= target )); then
    echo "== skip $(basename "$out") (complete: ${done}/${target})"
    return 0
  fi
  echo "== $(basename "$out") (resuming at seed $((base + done)))"
  python scripts/exp_timing.py \
    --my-deck "$MYDECK" \
    --matches "$((target - done))" --seed-start "$((base + done))" \
    --out "$out" --append "$@"
}

if [[ "$STAGE" == "fit" ]]; then
  # Stage 1: fit c(it)=alpha+beta*it and estimate M.
  # More games at the cheap 300-iter level (M needs a good tail; M is
  # iteration-independent), fewer at the expensive high-iter levels
  # (c needs many *decisions*, not many games — each game yields dozens).
  FIT_PLAN="${FIT_PLAN:-300:10 600:3 1000:3 1500:3}"
  for pair in $FIT_PLAN; do
    iters="${pair%%:*}"; games="${pair##*:}"
    for opp in "${OPPS[@]}"; do
      out="results/exp008_fit_A${iters}_v1_vs_${opp}.jsonl"
      run_cell "$out" "$games" 1 \
        --opp-deck "decks/candidates/${opp}.csv" \
        --policy A --iterations "$iters" --opp-iterations "$iters"
    done
  done
  echo "EXP-008 fit stage complete. Analyze c(it) and M, then set"
  echo "CONF_* and run: bash scripts/run_exp008.sh confirm"

elif [[ "$STAGE" == "confirm" ]]; then
  # Stage 2: Policy-C confirmation at the chosen operating point.
  # High iteration cap so the wall-clock (not iterations) binds. Assert
  # 0 forfeits and cumulative p99 < 540s in the printed summaries.
  CONF_ITERS="${CONF_ITERS:-100000}"
  CONF_RESERVE="${CONF_RESERVE:-60}"
  CONF_MOVES="${CONF_MOVES:-40}"
  CONF_N="${CONF_N:-30}"
  echo "Policy C: iters-cap=${CONF_ITERS} reserve=${CONF_RESERVE}s "\
"moves-ahead=${CONF_MOVES} games=${CONF_N}/opp"
  for opp in "${OPPS[@]}"; do
    out="results/exp008_confirmC_v1_vs_${opp}.jsonl"
    run_cell "$out" "$CONF_N" 1 \
      --opp-deck "decks/candidates/${opp}.csv" \
      --policy C --iterations "$CONF_ITERS" \
      --overage-reserve "$CONF_RESERVE" --moves-ahead "$CONF_MOVES" \
      --opp-agent ismcts --opp-iterations 1000
  done
  echo "EXP-008 confirm stage complete. Check every summary: forfeits 0,"
  echo "cumulative p99 < 540s. Then fill the EXP-008 Actual + ADR/notes."

else
  echo "unknown stage '${STAGE}' (want: fit | confirm)" >&2
  exit 1
fi
