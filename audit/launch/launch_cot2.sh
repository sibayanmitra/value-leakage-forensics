#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
VLF_GPU=1 .venv/bin/python src/disclose_cot.py --frame own --tok-budget 27500 --out results/disclose_cot_own.jsonl > logs/disclose_cot_own.log 2>&1 &
sleep 150
VLF_GPU=2 .venv/bin/python src/disclose_cot.py --frame third --tok-budget 27500 --out results/disclose_cot_third.jsonl > logs/disclose_cot_third.log 2>&1 &
wait
echo "[cot] both arms finished $(date -Is)"
