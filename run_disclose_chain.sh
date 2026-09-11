#!/usr/bin/env bash
# Runs the remaining two disclosure arms on GPU3 after naked_number finishes.
# Two-phase design: bounded reasoning, then a forced YES/NO verdict.
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f "disclose.py --rollouts results/naked_number.jsonl" > /dev/null; do sleep 60; done
echo "[chain] naked_number done $(date -Is)"
for spec in "above_good above_ours3" "baseline our_baseline"; do
  set -- $spec
  VLF_GPU=3 CUDA_VISIBLE_DEVICES=3 .venv/bin/python src/disclose.py \
    --rollouts results/$2.jsonl --condition $1 --batch 12 --max-new 2000 \
    --out results/disclose3_$1.jsonl > logs/disclose3_$1.log 2>&1
  echo "[chain] disclose3_$1 done $(date -Is) rows=$(wc -l < results/disclose3_$1.jsonl)"
done
echo "[chain] ALL DISCLOSURE DONE $(date -Is)"
