#!/usr/bin/env bash
# Extended budget, resequenced. Steering is now on the 35B -- the SAME model as every
# behavioural result -- so the 9B anchoring check is no longer needed (it only existed to
# justify reading the 9B probe across to the 35B). Dropped.
#
#   07:30  hard stop on the 2x2
#   then   GPU2 -> warned_anchor    GPU3 -> warned_values     ("can you turn it off?", prompt)
#          GPU0 -> steer_dm                                    ("can you turn it off?", causal)
#   after  GPU0 -> the three disclosure runs (short generations, fast)
set -u
cd /home/sibayan_mitra_2024/neel/value-leakage-forensics
END=$(date -d "07:30" +%s); [ $END -lt $(date +%s) ] && END=$(date -d "tomorrow 07:30" +%s)
while [ $(date +%s) -lt $END ]; do
  alive=0; for p in 3991259 3991260 3991261; do kill -0 $p 2>/dev/null && alive=1; done
  [ $alive -eq 0 ] && { echo "[stage0] 2x2 finished early $(date -Is)"; break; }
  sleep 120
done
for p in 3991259 3991260 3991261; do kill -0 $p 2>/dev/null && { echo "[stage0] stopping $p"; kill $p; }; done
sleep 45; pkill -f "max-new 18000" 2>/dev/null; sleep 25
echo "[stage0] 2x2 rows:"; wc -l results/below_ours.jsonl results/valence_above.jsonl results/valence_below.jsonl

for spec in "2 warned_anchor" "3 warned_values"; do
  set -- $spec
  nohup env VLF_GPU=$1 .venv/bin/python src/gen_neutral.py --n 20 --batch 20 --max-new 18000 \
    --condition $2 --questions bridge,giraffes,tbc --out results/$2.jsonl > logs/$2.log 2>&1 &
  echo "[stage1] GPU$1 $2 pid $!"
done

VLF_GPU=0 .venv/bin/python src/steer_dm.py --questions bridge,giraffes,tbc \
  --alphas 0,6,12 --n 12 --batch 12 --max-new 18000 \
  --out results/steer_dm.jsonl > logs/steer_dm.log 2>&1
echo "[stage2] steering done $(date -Is)"

for spec in "naked_number naked_number" "above_good above_ours3" "baseline our_baseline"; do
  set -- $spec
  VLF_GPU=0 .venv/bin/python src/disclose.py --rollouts results/$2.jsonl \
    --condition $1 --out results/disclose_$1.jsonl >> logs/disclose.log 2>&1
  echo "[stage3] disclose_$1 done $(date -Is)"
done
echo "[backstop] ALL DONE $(date -Is)"
