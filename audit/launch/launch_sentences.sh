#!/bin/bash
# Step 2: sentence-level resampling of the 4 reliable deniers (11, 1, 24, 55), GPU1 only (GPU2 is in use by another user).
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')
if [ "$used" -gt 2000 ]; then echo "[sentences] GPU1 busy (${used} MiB used), not starting $(date -Is)"; exit 1; fi
echo "[sentences] start $(date -Is) on GPU1 (${used} MiB used before start)"
VLF_GPU=1 .venv/bin/python src/resample_sentences.py --n 5 --out results/resample_sentences.jsonl > logs/resample_sentences.log 2>&1
echo "[sentences] finished $(date -Is) exit=$?"
