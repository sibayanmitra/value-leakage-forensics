#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f "src-start 17" >/dev/null; do sleep 30; done
echo "E2 half d done $(date); starting neutral_T half B on GPU2"
VLF_GPU=2 .venv/bin/python src/gen_neutral.py --n 20 --batch 5 --max-new 12500 \
  --questions tbc,turns,windowdays,zills --out results/neutral_b.jsonl > logs/neutral_b2.log 2>&1
echo "neutral B done $(date)"
