#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
NUM="bridge=26143882,giraffes=20311706,tbc=1106"
VLF_GPU=0 .venv/bin/python src/gen_neutral.py --condition naked_number --numerals $NUM --questions bridge   --n 20 --batch 10 --max-new 18000 --out results/precise_bridge.jsonl   > logs/precise_bridge.log 2>&1 &
sleep 150
VLF_GPU=1 .venv/bin/python src/gen_neutral.py --condition naked_number --numerals $NUM --questions giraffes --n 20 --batch 10 --max-new 18000 --out results/precise_giraffes.jsonl > logs/precise_giraffes.log 2>&1 &
sleep 150
VLF_GPU=2 .venv/bin/python src/gen_neutral.py --condition naked_number --numerals $NUM --questions tbc      --n 20 --batch 10 --max-new 18000 --out results/precise_tbc.jsonl      > logs/precise_tbc.log 2>&1 &
sleep 150
VLF_GPU=3 .venv/bin/python src/gen_neutral.py --condition naked_invite --questions bridge,giraffes,tbc --n 20 --batch 10 --max-new 18000 --out results/naked_invite.jsonl > logs/naked_invite.log 2>&1 &
wait
