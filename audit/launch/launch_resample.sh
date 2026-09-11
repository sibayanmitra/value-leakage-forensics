#!/bin/bash
# Step 1 of resampling the own-frame denials: 16 rollouts (8 denials, 8 matched admissions) x 10 samples,
# temperature 0.6, top-p 0.95, top-k off (Thought Anchors' settings), 2000 tokens then forced verdict.
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
echo "[resample] start $(date -Is)"
VLF_GPU=1 .venv/bin/python src/resample_denials.py --part 0 --nparts 2 --out results/resample_denials_p0.jsonl > logs/resample_denials_p0.log 2>&1 &
sleep 150
VLF_GPU=2 .venv/bin/python src/resample_denials.py --part 1 --nparts 2 --out results/resample_denials_p1.jsonl > logs/resample_denials_p1.log 2>&1 &
wait
echo "[resample] both parts finished $(date -Is)"
