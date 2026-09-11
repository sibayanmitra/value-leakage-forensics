#!/bin/bash
# Direction without a number (verbal_high / verbal_low): answers "deleting the number only removed the
# model's ability to act on its values". Same generator and settings as the other conditions:
# src/gen_neutral.py, 20 per question, bridge/giraffes/tbc, temperature 1.0, top-p 1.0, 26,000-token cap.
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
unset PYTORCH_CUDA_ALLOC_CONF
for c in verbal_high verbal_low; do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 1 | tr -d ' ')
  if [ "$used" -gt 2000 ]; then echo "[verbal] GPU1 busy (${used} MiB), not starting $c $(date -Is)"; exit 1; fi
  s=$(date -Is); echo "[verbal] $c start $s"
  VLF_GPU=1 .venv/bin/python src/gen_neutral.py --condition $c --n 20 --questions bridge,giraffes,tbc \
      --max-new 26000 --batch 10 --out results/$c.jsonl > logs/$c.log 2>&1
  rc=$?; f=$(date -Is); rows=$(wc -l < results/$c.jsonl 2>/dev/null); trunc=$(grep -c '"truncated": true' results/$c.jsonl 2>/dev/null)
  echo "[verbal] $c finished $f exit=$rc rows=$rows truncated=$trunc"
  [ $rc -eq 0 ] && echo "$f | $c (direction without a number) | results/$c.jsonl | model=Qwen/Qwen3.5-35B-A3B-FP8 GPU1 cap=26000 n=20x3 batch=10 temperature=1.0 top_p=1.0 src/gen_neutral.py | rows=$rows truncated=$trunc | started=$s" >> RUNS.log
done
