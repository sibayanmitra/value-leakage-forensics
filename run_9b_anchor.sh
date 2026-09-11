#!/usr/bin/env bash
# Does the 9B show the ANCHORING effect, not just the bias?
#
# Load-bearing check. The Number Ladder was measured on the 35B; the probe runs on the
# 9B. If the 9B's bias is valence-driven while the 35B's is anchor-driven, the probe has
# been answering a question about a different phenomenon. 40-45 min per condition.
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while kill -0 3991259 2>/dev/null; do sleep 60; done
echo "[queue] below_good done, GPU0 free $(date -Is)"
sleep 30
for c in baseline neutral_T; do
  VLF_GPU=0 .venv/bin/python src/gen_neutral.py --model Qwen/Qwen3.5-9B \
    --n 20 --batch 10 --max-new 20000 --condition $c \
    --questions bridge,giraffes,tbc --out results/9b_$c.jsonl
  echo "[queue] 9b_$c done $(date -Is)"
done
