#!/usr/bin/env bash
# Dose-response: where does copying break for tbc? (pre-registered 2026-09-12)
set -e
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
export CUDA_VISIBLE_DEVICES=2
PY=.venv/bin/python
for mult in 30 100 300; do
  N=$((1100 * mult))
  S=$(date -Is)
  $PY src/gen_neutral.py --condition naked_number --questions tbc --n 20 \
      --numerals tbc=$N --max-new 26000 --batch 10 --out results/tbc_x$mult.jsonl
  echo "$(date -Is) | tbc dose-response x$mult | results/tbc_x$mult.jsonl | numeral=$N GPU2 cap=26000 n=20 temperature=1.0 top_p=1.0 | rows=$(wc -l < results/tbc_x$mult.jsonl) | started=$S" >> RUNS.log
done
