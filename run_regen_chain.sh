#!/usr/bin/env bash
# Regenerate above_good and neutral_T at a higher token cap.
#
# WHY: at --max-new 18000 these two conditions lost 7/60 and 5/60 rollouts to the cap,
# while every other condition lost 0/60. Truncated rollouts are longer, and longer
# reasoning correlates with LOWER bias, so dropping them biases both p(>T) figures
# UPWARD. This is the fourth time a length cap has distorted a result in this project.
# 26000 gives ~45% more headroom than the runs that truncated.
#
# GPU2 takes above_good after stray_number; GPU0 takes neutral_T after warned_placebo.
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
GPU="$1"; COND="$2"; OUT="$3"; WAITFOR="$4"

while pgrep -f "python.*$WAITFOR" > /dev/null; do sleep 60; done
START=$(date -Is)
echo "[regen] $COND starting $START on GPU$GPU (waited for: $WAITFOR)"
VLF_GPU=$GPU CUDA_VISIBLE_DEVICES=$GPU .venv/bin/python src/gen_neutral.py \
  --condition "$COND" --questions bridge,giraffes,tbc \
  --n 20 --batch 20 --max-new 26000 --out "results/$OUT.jsonl" \
  > "logs/$OUT.log" 2>&1
END=$(date -Is)
ROWS=$(wc -l < "results/$OUT.jsonl")
TRUNC=$(python3 -c "import json;print(sum(json.loads(l)['truncated'] for l in open('results/$OUT.jsonl')))")
printf '%s | %s | %s | cap=26000 n=20x3 | rows=%s truncated=%s | started=%s finished=%s\n' \
  "$END" "$COND" "results/$OUT.jsonl" "$ROWS" "$TRUNC" "$START" "$END" >> RUNS.log
echo "[regen] $COND done $END rows=$ROWS truncated=$TRUNC"
