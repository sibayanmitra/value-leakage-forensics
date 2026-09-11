#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
VLF_GPU=2 .venv/bin/python src/resample_sweep.py --sources 1 --positions none --n 15 --batch 6 --out results/sweep_rev1.jsonl > logs/sweep_rev1.log 2>&1 &
sleep 300
VLF_GPU=3 .venv/bin/python src/resample_sweep.py --sources 5 --positions none --n 15 --batch 6 --out results/sweep_rev5.jsonl > logs/sweep_rev5.log 2>&1 &
sleep 300
VLF_GPU=1 .venv/bin/python src/resample_sweep.py --sources 6 --positions none --n 15 --batch 6 --out results/sweep_rev6.jsonl > logs/sweep_rev6.log 2>&1 &
wait
