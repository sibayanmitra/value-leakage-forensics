#!/usr/bin/env bash
# PREREG_gate_generalisation_2026-10-16.md, Phase 1: no-number baselines, one GPU per call.
# Usage: bash run_gate_phase1.sh <gpu> "<n>:<q1,q2,...>" ["<n>:<q,...>" ...]
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
GPU=$1; shift
export CUDA_VISIBLE_DEVICES=$GPU
PY=.venv/bin/python
log() { echo "$(date -Is) | $*" >> RUNS.log; }
k=0
for spec in "$@"; do
  N=${spec%%:*}; Q=${spec#*:}
  OUT=results/gate_base_g${GPU}_${k}.jsonl
  S=$(date -Is)
  $PY src/gen_neutral.py --condition baseline --questions $Q --n $N \
      --max-new 26000 --batch 10 --out $OUT
  log "gate phase 1 baselines (no number) | $OUT | questions=$Q | model=Qwen/Qwen3.5-35B-A3B-FP8 GPU$GPU cap=26000 n=$N temperature=1.0 top_p=1.0 src/gen_neutral.py | rows=$(wc -l < $OUT) truncated=$(grep -c '"truncated": true' $OUT || true) | started=$S"
  k=$((k+1))
done
