#!/usr/bin/env bash
# Queued behind our_baseline (pid 3914261) on GPU0.
# Regenerates the Qwen3.5-9B probe corpus. The existing gate run
# (results/gate_qwen9b.jsonl) is unusable for the probe: 93/200 = 47% truncated,
# and truncation is question-correlated (bridge 74%, tbc 16%), which is the same
# length-bias failure that killed the first neutral_T run. Raising max_new to
# 24000 and widening to 6 questions fixes both.
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while kill -0 3914261 2>/dev/null; do sleep 60; done
echo "[queue] our_baseline exited $(date -Is)"
sleep 30
VLF_GPU=0 .venv/bin/python src/gate_model.py \
  --model Qwen/Qwen3.5-9B --n 30 --batch 10 --max-new 24000 \
  --questions bridge,giraffes,tbc,orangecars,crochet,maiden \
  --out results/probe9b_rollouts.jsonl
echo "[queue] done $(date -Is)"
