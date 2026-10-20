#!/usr/bin/env bash
# PREREG_gate_generalisation_2026-10-16.md, Phase 2: each question at z = 2, 4, 6, 8, 10, numerals
# from configs/gate_phase2_numerals.json (written by src/gate_phase1.py). One GPU per call.
# Usage: bash run_gate_phase2.sh <gpu> <q1> [q2 ...]
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
GPU=$1; shift
export CUDA_VISIBLE_DEVICES=$GPU
PY=.venv/bin/python
CFG=configs/gate_phase2_numerals.json
log() { echo "$(date -Is) | $*" >> RUNS.log; }
for Q in "$@"; do
  EXP=$($PY -c "import json; print(json.load(open('$CFG'))['$Q']['experiment'].lower())")
  for Z in 2 4 6 8 10; do
    N=$($PY -c "import json; print(next(g['numeral'] for g in json.load(open('$CFG'))['$Q']['grid'] if g['z_target']==$Z))")
    OUT=results/gate_${EXP}_${Q}_z${Z}.jsonl
    if [ -s "$OUT" ] && [ "$(wc -l < $OUT)" -ge 20 ]; then continue; fi
    S=$(date -Is)
    $PY src/gen_neutral.py --condition naked_number --questions $Q --n 20 \
        --numerals $Q=$N --max-new 26000 --batch 10 --out $OUT
    log "gate phase 2 ${EXP^^} | $OUT | question=$Q z=$Z numeral=$N | model=Qwen/Qwen3.5-35B-A3B-FP8 GPU$GPU cap=26000 n=20 temperature=1.0 top_p=1.0 src/gen_neutral.py | rows=$(wc -l < $OUT) truncated=$(grep -c '"truncated": true' $OUT || true) | started=$S"
  done
done
