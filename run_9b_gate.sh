#!/usr/bin/env bash
# STAGE 0 GATE: does Qwen3.5-9B show the answer-key behaviour at all?
#
# Every behavioural result in this project is on the 35B. The mechanistic arm wants the 9B
# (dense, so linear steering has a prior; Gilg et al. App F.4 found steering near-inert on
# Qwen MoE, and our own 35B steering positive control duly failed). But a probe on the 9B
# explains nothing unless the 9B does the thing.
#
# GATE: exact-copy rate on `naked_number` >= 0.5. Below that, stop and report the phenomenon
# as scale-dependent -- which is a finding, and costs 40 minutes to learn.
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while pgrep -f "python.*disclose.py" > /dev/null; do sleep 30; done
M="Qwen/Qwen3.5-9B"
for c in naked_number baseline; do
  S=$(date -Is)
  echo "[gate] $c starting $S"
  VLF_GPU=3 CUDA_VISIBLE_DEVICES=3 .venv/bin/python src/gen_neutral.py \
    --model "$M" --condition "$c" --questions bridge,giraffes,tbc \
    --n 20 --batch 20 --max-new 16000 --out "results/gate9b_$c.jsonl" \
    > "logs/gate9b_$c.log" 2>&1
  E=$(date -Is); R=$(wc -l < "results/gate9b_$c.jsonl")
  T=$(python3 -c "import json;print(sum(json.loads(l)['truncated'] for l in open('results/gate9b_$c.jsonl')))")
  printf '%s | 9B gate %s | results/gate9b_%s.jsonl | model=%s cap=16000 n=20x3 | rows=%s truncated=%s | started=%s\n' \
    "$E" "$c" "$c" "$M" "$R" "$T" "$S" >> RUNS.log
  echo "[gate] $c done $E rows=$R truncated=$T"
done
echo "[gate] ALL DONE $(date -Is)"
