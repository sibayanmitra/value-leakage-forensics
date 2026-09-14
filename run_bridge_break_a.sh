#!/usr/bin/env bash
# PREREG_bridge_break_2026-09-14.md, arms A and C (GPU 1).
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
export CUDA_VISIBLE_DEVICES=1
PY=.venv/bin/python
log() { echo "$(date -Is) | $*" >> RUNS.log; }
for spec in "A 210000000000 z6.5" "C 15000000000000 z9.5"; do
  set -- $spec
  S=$(date -Is)
  $PY src/gen_neutral.py --condition naked_number --questions bridge --n 20 \
      --numerals bridge=$2 --max-new 26000 --batch 10 --out results/bridge_$3.jsonl
  log "bridge break arm $1 ($3) | results/bridge_$3.jsonl | numeral=$2 GPU1 cap=26000 n=20 temperature=1.0 top_p=1.0 | rows=$(wc -l < results/bridge_$3.jsonl) | started=$S"
done
