#!/usr/bin/env bash
# Scope-elasticity runs (pre-registered in PREREG_scope_elasticity_2026-09-12.md)
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
export CUDA_VISIBLE_DEVICES=1
PY=.venv/bin/python
log() { echo "$(date -Is) | $*" >> RUNS.log; }

S=$(date -Is)
$PY src/gen_neutral.py --condition baseline --questions tbc_wide,bridge_narrow --n 20 \
    --max-new 26000 --batch 10 --out results/scope_baseline.jsonl
log "scope baselines (no number), tbc_wide + bridge_narrow | results/scope_baseline.jsonl | model=Qwen/Qwen3.5-35B-A3B-FP8 GPU1 cap=26000 n=20x2 temperature=1.0 top_p=1.0 src/gen_neutral.py | rows=$(wc -l < results/scope_baseline.jsonl) | started=$S"

S=$(date -Is)
$PY src/gen_neutral.py --condition naked_number --questions tbc_wide,bridge_narrow --n 20 \
    --numerals tbc_wide=1100000,bridge_narrow=26000000000 \
    --max-new 26000 --batch 10 --out results/scope_swap.jsonl
log "scope swap: same numeral, wider/narrower question | results/scope_swap.jsonl | tbc_wide=1,100,000 bridge_narrow=26,000,000,000 GPU1 cap=26000 n=20x2 | rows=$(wc -l < results/scope_swap.jsonl) | started=$S"
