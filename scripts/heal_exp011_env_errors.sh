#!/usr/bin/env bash
# EXP-011 recovery: drop rows poisoned by the ineffective overage-bank
# patch (registry amendment 2026-07-20) and rerun exactly those seeds
# under the fixed patch (scripts/local_ladder.py::_raise_overage_bank).
#
#   bash scripts/heal_exp011_env_errors.sh
#
# Clean rows are kept as-is: the arms are iteration-bounded and seeded,
# so the bank cannot change any decision in a game that completed — it
# can only kill a long one. Healing only the TIMEOUT seeds therefore
# yields the exact cell a full rerun would, minus the rerun cost.
#
# Idempotent and interruption-safe: each pass drops env_error rows and
# any truncated trailing line, then reruns every seed missing from
# 1..max(seed) — a gap left by an interrupted heal is picked up on the
# next pass. After healing, cell files are seed-complete again, so
# run_exp011.sh's line-count resume stays valid.
#
# Trajectory sinks keep the aborted TIMEOUT lines (reward null) next to
# the healed ones — the corpus is diagnostic, keyed by seed, and
# consumers must prefer the row with non-null rewards.
set -euo pipefail

ITERS="${EXP011_ITERS:-1000}"
BANK="${EXP011_BANK:-100000}"

shopt -s nullglob
for out in results/exp011_*_vs_*.jsonl; do
  base="${out##*/}"
  base="${base%.jsonl}"
  base="${base#exp011_}"
  deck="${base%%_vs_*}"
  opp="${base##*_vs_}"

  # Drop poisoned/truncated rows in place; print the seeds to rerun.
  mapfile -t seeds < <(python - "$out" <<'PY'
import json
import os
import sys

path = sys.argv[1]
rows: list[dict] = []
raw_lines = 0
with open(path) as fh:
    for line in fh:
        if not line.strip():
            continue
        raw_lines += 1
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            # A Ctrl-C can truncate the final line; drop it — its seed
            # becomes a gap and is rerun below.
            continue
        if not row.get("env_error"):
            rows.append(row)

if raw_lines == 0:
    sys.exit()
if len(rows) != raw_lines:
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    os.replace(tmp, path)

have = {row["seed"] for row in rows}
top = max(have) if have else raw_lines
for seed in sorted(set(range(1, top + 1)) - have):
    print(seed)
PY
  )
  ((${#seeds[@]})) || continue
  echo "== heal ${deck} vs ${opp}: seeds ${seeds[*]}"
  for seed in "${seeds[@]}"; do
    python scripts/local_ladder.py \
      --agent-a ismcts-selfdeck --agent-b heuristic \
      --deck-a "decks/candidates/${deck}.csv" \
      --deck-b "decks/candidates/${opp}.csv" \
      --matches 1 --seed-start "$seed" \
      --iterations "$ITERS" \
      --overage-bank "$BANK" \
      --out "$out" --append \
      --log-trajectories "results/exp011_traj_${deck}_vs_${opp}.jsonl.gz"
  done
done
echo "Heal pass complete. Run 'bash scripts/run_exp011.sh' to finish the sweep."
