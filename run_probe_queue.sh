#!/usr/bin/env bash
# Phase 3 probe, queued behind our_baseline (pid 3914261) on GPU0 and behind the
# trajectory enumeration (pid 3974169). probe.py only does forward passes to cache
# residual-stream activations at in-CoT estimate tokens -- no generation -- so it is
# minutes, not hours.
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
while kill -0 3914261 2>/dev/null || kill -0 3974169 2>/dev/null; do sleep 45; done
echo "[queue] deps clear $(date -Is)"
[ -s results/traj9b.jsonl ] || { echo "[queue] ABORT: traj9b.jsonl missing/empty"; exit 1; }
sleep 20
VLF_GPU=0 .venv/bin/python src/probe.py \
  --rollouts results/traj9b.jsonl \
  --out results/probe_results.csv
echo "[queue] done $(date -Is)"
