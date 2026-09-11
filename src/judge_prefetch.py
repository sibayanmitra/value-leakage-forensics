"""Parallel cache fill for the judge. Writes only into results/judge_cache/ (atomic),
so the sequential analysis afterwards is pure cache hits."""
import json, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
sys.path.insert(0, "src")
from extract import extract_answer, _cache_path, ANSWER_PROMPT
import budget

QS = {"bridge", "giraffes", "tbc"}
PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
FILES = ["our_baseline", "neutral_ours3", "above_ours3", "below_ours", "valence_above",
         "valence_below", "naked_number", "warned_anchor", "warned_values", "steer_dm"]

todo, seen = [], set()
for f in FILES:
    for l in open(f"results/{f}.jsonl"):
        r = json.loads(l)
        if r["question"] not in QS:
            continue
        a = PAD.sub("", r["answer"] or "").strip()
        if not a or a in seen:
            continue
        seen.add(a)
        if not _cache_path(ANSWER_PROMPT, a, "extraction").exists():
            todo.append(a)

print(f"unique answers needing a judge call: {len(todo)}", flush=True)
print(f"total chars: {sum(len(a) for a in todo):,}", flush=True)
budget.require(0.40, "judge cache fill")

t0, done, fail = time.time(), 0, 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(extract_answer, a): a for a in todo}
    for fu in as_completed(futs):
        try:
            fu.result()
        except Exception as e:
            fail += 1
            print(f"  FAIL: {str(e)[:100]}", flush=True)
        done += 1
        if done % 25 == 0:
            print(f"  {done}/{len(todo)} in {time.time()-t0:.0f}s ({fail} failed)", flush=True)
print(f"DONE {done} calls, {fail} failed, {time.time()-t0:.0f}s", flush=True)
print(f"balance now ${budget.balance():.2f}", flush=True)
