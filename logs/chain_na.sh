#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f "src-start 0 " >/dev/null; do sleep 30; done
echo "E2 half c done $(date); starting neutral_T half A on GPU0"
VLF_GPU=0 .venv/bin/python src/gen_neutral.py --n 20 --batch 5 --max-new 12500 \
  --questions bridge,crochet,giraffes,maiden,orangecars --out results/neutral_a.jsonl > logs/neutral_a2.log 2>&1
echo "neutral A done $(date)"
