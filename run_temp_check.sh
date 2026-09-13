#!/usr/bin/env bash
# PLAN_2026-09-14_minimal_pairs.md §5, run 2 (GPU 1).
# Is the baseline spread a property of the question or of the sampler? Same five questions as
# the temperature-1.0 baselines, resampled at 0.7 / top-p 0.95.
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
export CUDA_VISIBLE_DEVICES=1
PY=.venv/bin/python
log() { echo "$(date -Is) | $*" >> RUNS.log; }

S=$(date -Is)
$PY src/gen_neutral.py --condition baseline --questions bridge,giraffes,tbc,tbc_wide,bridge_narrow \
    --temperature 0.7 --top-p 0.95 --n 20 \
    --max-new 26000 --batch 10 --out results/baseline_t07.jsonl
log "baselines at temperature 0.7 (spread check) | results/baseline_t07.jsonl | model=Qwen/Qwen3.5-35B-A3B-FP8 GPU1 cap=26000 n=20x5 temperature=0.7 top_p=0.95 | rows=$(wc -l < results/baseline_t07.jsonl) | started=$S"
