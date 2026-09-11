#!/bin/bash
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
# wait for both halves of the powered E2 to finish
while pgrep -f resample_forced.py >/dev/null; do sleep 60; done
echo "E2 done $(date) - restarting neutral_T with a larger token budget"
VLF_GPU=0 .venv/bin/python src/gen_neutral.py --n 20 --batch 5 --max-new 12500 \
  --questions bridge,crochet,giraffes,maiden,orangecars \
  --out results/neutral_a.jsonl > logs/neutral_a2.log 2>&1 &
P1=$!
VLF_GPU=2 .venv/bin/python src/gen_neutral.py --n 20 --batch 5 --max-new 12500 \
  --questions tbc,turns,windowdays,zills \
  --out results/neutral_b.jsonl > logs/neutral_b2.log 2>&1 &
P2=$!
wait $P1 $P2
echo "neutral_T v2 done $(date)"
