#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
VLF_GPU=1 .venv/bin/python src/disclose_cot.py --frame own   --out results/disclose_cot_own.jsonl   > logs/disclose_cot_own.log 2>&1
VLF_GPU=1 .venv/bin/python src/disclose_cot.py --frame third --out results/disclose_cot_third.jsonl > logs/disclose_cot_third.log 2>&1
echo "[cot] both arms done $(date -Is)"
