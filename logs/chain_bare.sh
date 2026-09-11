#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f "gate_model.py --model Qwen/Qwen3.5-9B --out results/gate_qwen9b" >/dev/null; do sleep 60; done
echo "9b gate done $(date) - starting bare_number on GPU2"
VLF_GPU=2 .venv/bin/python src/gen_neutral.py --n 20 --batch 5 --max-new 14000 \
  --condition bare_number --questions bridge,crochet,giraffes,tbc,zills \
  --out results/bare_number.jsonl > logs/bare_number.log 2>&1
echo "bare_number done $(date)"
