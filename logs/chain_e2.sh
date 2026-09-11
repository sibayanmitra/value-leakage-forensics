#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
# wait for neutral_T to finish on both GPUs
while pgrep -f gen_neutral >/dev/null; do sleep 60; done
echo "neutral_T finished, starting powered E2 at $(date)"
# 34 new sources at 20 resamples, split across the two GPUs
VLF_SOURCES=results/aim_sentences_new34.jsonl VLF_GPU=0 .venv/bin/python src/resample_forced.py --n-resamples 20 --batch 4 \
  --src-start 0 --src-end 17 --out results/resamples_forced_c.jsonl \
  > logs/resample_c.log 2>&1 &
P1=$!
VLF_SOURCES=results/aim_sentences_new34.jsonl VLF_GPU=2 .venv/bin/python src/resample_forced.py --n-resamples 20 --batch 4 \
  --src-start 17 --src-end 34 --out results/resamples_forced_d.jsonl \
  > logs/resample_d.log 2>&1 &
P2=$!
wait $P1 $P2
echo "powered E2 finished at $(date)"
