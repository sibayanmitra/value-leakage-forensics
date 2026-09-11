#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f gen_neutral.py >/dev/null; do sleep 60; done
echo "neutral_T finished $(date) - starting E2 half C on GPU0"
VLF_SOURCES=results/aim_sentences_new34.jsonl VLF_GPU=0 .venv/bin/python src/resample_forced.py \
  --n-resamples 20 --batch 4 --src-start 0 --src-end 17 \
  --out results/resamples_forced_c.jsonl > logs/resample_c.log 2>&1
echo "E2 half C finished $(date)"
