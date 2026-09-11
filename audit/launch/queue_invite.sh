#!/bin/bash
# naked_invite waits for precise_bridge (pid 2264979) to free GPU 0. GPU 3 stays free by request.
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while kill -0 2264979 2>/dev/null; do sleep 30; done
unset PYTORCH_CUDA_ALLOC_CONF
VLF_GPU=0 .venv/bin/python src/gen_neutral.py --condition naked_invite --questions bridge,giraffes,tbc --n 20 --batch 10 --max-new 18000 --out results/naked_invite.jsonl > logs/naked_invite.log 2>&1
