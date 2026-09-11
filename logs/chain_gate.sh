#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f gen_neutral.py >/dev/null; do sleep 60; done
echo "neutral_T done $(date) - starting Phase 3 gates"
VLF_GPU=0 .venv/bin/python src/gate_model.py --model Qwen/Qwen3.8-27B-FP8 \
  --out results/gate_qwen38.jsonl > logs/gate_38.log 2>&1 &
P1=$!
VLF_GPU=2 .venv/bin/python src/gate_model.py --model Qwen/Qwen3.5-9B \
  --out results/gate_qwen9b.jsonl > logs/gate_9b.log 2>&1 &
P2=$!
wait $P1 $P2
echo "gates done $(date)"
