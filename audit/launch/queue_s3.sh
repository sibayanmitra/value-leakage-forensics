#!/bin/bash
# S3 for the precise arm: wait for precise_giraffes (pid 2265792), then ask every finished rollout
# the same direct question disclose3 asked, about the numeral THAT rollout saw. GPU 2 only; GPU 3 stays free.
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while kill -0 2265792 2>/dev/null; do sleep 30; done
cat results/precise_bridge.jsonl results/precise_giraffes.jsonl results/precise_tbc.jsonl > results/precise_all.jsonl
echo "[s3] precise_all rows: $(wc -l < results/precise_all.jsonl)  $(date -Is)"
unset PYTORCH_CUDA_ALLOC_CONF
VLF_GPU=2 CUDA_VISIBLE_DEVICES=2 .venv/bin/python src/disclose.py \
  --rollouts results/precise_all.jsonl --condition naked_number --batch 12 --max-new 2000 \
  --out results/disclose3_precise.jsonl > logs/disclose3_precise.log 2>&1
echo "[s3] done $(date -Is)"
