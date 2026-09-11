# Recompute RESULTS.md E2 paired contrasts with e2_deep_split.py's loader and bootstrap (4000, seed 0).
import json, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
rng = np.random.default_rng(0)
HAND = {}
for l in open("results/e2_all_scored.jsonl"):
    r = json.loads(l)
    if r.get("hand_aim") is not None: HAND[r["sentence"]] = bool(r["hand_aim"])
print(f"unique hand-labelled sentences: {len(HAND)}   stating an aim: {sum(HAND.values())}")
rows = []
for f in "abcd":
    batch = "ab" if f in "ab" else "cd"
    for l in open(f"results/resamples_forced_{f}.jsonl"):
        r = json.loads(l); v = extract_answer(r["answer"])
        if v is None: continue
        T = float(r["threshold"])
        arm = r["arm"]
        if arm == "resampled":
            a = HAND.get(r["sentence"])
            if a is None: continue
            arm = "AIM" if a else "NOAIM"
        rows.append(((batch, r["source"]), arm, float((v > T) if r["direction"] == "above_good" else (v <= T))))
print(f"rows used {len(rows)}   arms {collections.Counter(a for _, a, _ in rows)}")
by = collections.defaultdict(lambda: collections.defaultdict(list))
for s, a, y in rows: by[s][a].append(y)
def paired(A, B, n=4000):
    S = [s for s in by if by[s][A] and by[s][B]]
    d = np.array([np.mean(by[s][A]) - np.mean(by[s][B]) for s in S])
    reps = np.array([rng.choice(d, len(d)).mean() for _ in range(n)])
    return f"{d.mean():+.3f} [{np.percentile(reps,2.5):+.3f}, {np.percentile(reps,97.5):+.3f}]  {int((d>0).sum())}/{len(S)} sources +"
for A, B in [("AIM","NOAIM"),("original","NOAIM"),("original","AIM"),("nosent","NOAIM"),("original","nosent")]:
    print(f"  {A:8s} - {B:8s}  {paired(A,B)}")

# The keying trap: grouping by `source` alone merges two batches that reuse ids 0-15.
wrong = collections.defaultdict(lambda: collections.defaultdict(list))
for (batch, src), a, y in rows:
    if a in ("AIM", "NOAIM"): wrong[src][a].append(y)
S = [s for s in wrong if wrong[s]["AIM"] and wrong[s]["NOAIM"]]
d = np.array([np.mean(wrong[s]["AIM"]) - np.mean(wrong[s]["NOAIM"]) for s in S])
rng2 = np.random.default_rng(0)
reps = np.array([rng2.choice(d, len(d)).mean() for _ in range(4000)])
print(f"  WRONG KEY (source only): {len(wrong)} sources; AIM - NOAIM {d.mean():+.3f} [{np.percentile(reps,2.5):+.3f}, {np.percentile(reps,97.5):+.3f}]")
