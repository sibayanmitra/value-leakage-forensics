#!/usr/bin/env bash
# PREREG_bridge_break_2026-09-14.md, arms B and D (GPU 3).
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
export CUDA_VISIBLE_DEVICES=3
PY=.venv/bin/python
log() { echo "$(date -Is) | $*" >> RUNS.log; }
for spec in "B 1700000000000 z8.0" "D 520000000000000 z12.0"; do
  set -- $spec
  S=$(date -Is)
  $PY src/gen_neutral.py --condition naked_number --questions bridge --n 20 \
      --numerals bridge=$2 --max-new 26000 --batch 10 --out results/bridge_$3.jsonl
  log "bridge break arm $1 ($3) | results/bridge_$3.jsonl | numeral=$2 GPU3 cap=26000 n=20 temperature=1.0 top_p=1.0 | rows=$(wc -l < results/bridge_$3.jsonl) | started=$S"
done
