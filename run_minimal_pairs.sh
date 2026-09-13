#!/usr/bin/env bash
# PLAN_2026-09-14_minimal_pairs.md §5, runs 1, 3 and 4 (GPU 0).
# Baselines for the four minimal-pair questions, then both clean swaps against them.
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
export CUDA_VISIBLE_DEVICES=0
PY=.venv/bin/python
log() { echo "$(date -Is) | $*" >> RUNS.log; }
Q=tbc_wide_h,tbc_narrow_total,bridge_wide_h,bridge_narrow_h

S=$(date -Is)
$PY src/gen_neutral.py --condition baseline --questions $Q --n 20 \
    --max-new 26000 --batch 10 --out results/mp_baseline.jsonl
log "minimal-pair baselines (no number) | results/mp_baseline.jsonl | model=Qwen/Qwen3.5-35B-A3B-FP8 GPU0 cap=26000 n=20x4 temperature=1.0 top_p=1.0 | rows=$(wc -l < results/mp_baseline.jsonl) | started=$S"

S=$(date -Is)
$PY src/gen_neutral.py --condition naked_number --questions tbc_wide_h,tbc_narrow_total --n 20 \
    --numerals tbc_wide_h=1100000,tbc_narrow_total=1100000 \
    --max-new 26000 --batch 10 --out results/mp_swap_steps.jsonl
log "clean swap, steps pair, 1,100,000 both | results/mp_swap_steps.jsonl | GPU0 cap=26000 n=20x2 temperature=1.0 top_p=1.0 | rows=$(wc -l < results/mp_swap_steps.jsonl) | started=$S"

S=$(date -Is)
$PY src/gen_neutral.py --condition naked_number --questions bridge_wide_h,bridge_narrow_h --n 20 \
    --numerals bridge_wide_h=26000000000,bridge_narrow_h=26000000000 \
    --max-new 26000 --batch 10 --out results/mp_swap_tricks.jsonl
log "clean swap, tricks pair, 26,000,000,000 both | results/mp_swap_tricks.jsonl | GPU0 cap=26000 n=20x2 temperature=1.0 top_p=1.0 | rows=$(wc -l < results/mp_swap_tricks.jsonl) | started=$S"
