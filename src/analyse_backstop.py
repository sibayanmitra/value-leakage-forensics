"""Corrected: balanced bias uses the favoured side per direction, not p(>T) for both."""
import json, re, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer

QS = ["bridge", "giraffes", "tbc"]
PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng = np.random.default_rng(0)
clean = lambda s: PAD.sub("", s or "").strip()

def load(path):
    out, drop_empty, drop_none = collections.defaultdict(list), 0, 0
    for l in open(f"results/{path}.jsonl"):
        r = json.loads(l)
        if r["question"] not in QS: continue
        a = clean(r["answer"])
        if not a: drop_empty += 1; continue
        v = extract_answer(a)
        if v is None: drop_none += 1; continue
        out[r["question"]].append((v, r["threshold"]))
    return out, drop_empty, drop_none

def outcome(cells, fn):
    return {q: np.array([fn(v, t) for v, t in rows], float) for q, rows in cells.items()}

def boot(per, n=4000):
    pt = float(np.mean([p.mean() for p in per.values()]))
    bs = np.array([np.mean([rng.choice(p, len(p)).mean() for p in per.values()]) for _ in range(n)])
    return pt, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), sum(len(p) for p in per.values())

def bias(below_cells, above_cells, n=4000):
    """p_fav(below_good: <=T) + p_fav(above_good: >T) - 1, equal question weight."""
    b = outcome(below_cells, lambda v, t: v <= t)
    a = outcome(above_cells, lambda v, t: v > t)
    ks = [q for q in b if q in a]
    pt = float(np.mean([b[q].mean() + a[q].mean() - 1.0 for q in ks]))
    bs = np.array([np.mean([rng.choice(b[q], len(b[q])).mean() + rng.choice(a[q], len(a[q])).mean() - 1.0
                            for q in ks]) for _ in range(n)])
    return pt, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

C, D = {}, {}
for name in ["our_baseline", "neutral_T_26k", "above_good_26k", "below_ours", "valence_above",
             "valence_below", "naked_number", "warned_anchor", "warned_values"]:
    C[name], e, nn = load(name)
    D[name] = (e, nn)

alias = {"baseline": "our_baseline", "neutral_T": "neutral_T_26k", "above_good": "above_good_26k",
         "below_good": "below_ours", "valence_above": "valence_above",
         "valence_below": "valence_below", "naked_number": "naked_number",
         "warned_anchor": "warned_anchor", "warned_values": "warned_values"}

print("=" * 78)
print("EXTRACTION DROPOUT (rows lost before any statistic)")
print("=" * 78)
for k, f in alias.items():
    e, nn = D[f]; n = sum(len(v) for v in C[f].values())
    print(f"  {k:15s} kept {n:3d}/60   empty_answer={e}  judge_returned_null={nn}")

print("\n" + "=" * 78)
print("BALANCED BIAS  =  p(<=T | below_good) + p(>T | above_good) - 1")
print("  0 = threshold rule ignored.  +1 = it decides the answer every time.")
print("=" * 78)
b1 = bias(C["below_ours"], C["above_good_26k"])
b2 = bias(C["valence_below"], C["valence_above"])
print(f"  number GIVEN    (below_good + above_good):        {b1[0]:+.3f} [{b1[1]:+.3f}, {b1[2]:+.3f}]")
print(f"  number WITHHELD (valence_below + valence_above):  {b2[0]:+.3f} [{b2[1]:+.3f}, {b2[2]:+.3f}]")
ks = [q for q in C["below_ours"] if q in C["above_good_26k"]]
d = np.array([np.mean([rng.choice(outcome(C["below_ours"], lambda v,t: v<=t)[q], len(C["below_ours"][q])).mean()
                       + rng.choice(outcome(C["above_good_26k"], lambda v,t: v>t)[q], len(C["above_good_26k"][q])).mean()
                       - rng.choice(outcome(C["valence_below"], lambda v,t: v<=t)[q], len(C["valence_below"][q])).mean()
                       - rng.choice(outcome(C["valence_above"], lambda v,t: v>t)[q], len(C["valence_above"][q])).mean()
                       for q in ks]) for _ in range(4000)])
print(f"  difference (given - withheld):                    {b1[0]-b2[0]:+.3f} "
      f"[{np.percentile(d,2.5):+.3f}, {np.percentile(d,97.5):+.3f}]")

print("\n" + "=" * 78)
print("EXACT-MATCH: p(estimate == T exactly)")
print("=" * 78)
for k in ["baseline", "neutral_T", "above_good", "below_good", "naked_number",
          "warned_anchor", "warned_values"]:
    p, lo, hi, n = boot(outcome(C[alias[k]], lambda v, t: v == t))
    print(f"  {k:15s} {p:.3f} [{lo:.3f}, {hi:.3f}]  n={n}")

print("\n" + "=" * 78)
print("MEDIAN |estimate - T| / T  (how close the estimate sits to the anchor)")
print("=" * 78)
for k in ["baseline", "neutral_T", "above_good", "warned_anchor", "warned_values"]:
    rel = [abs(v - t) / t for rows in C[alias[k]].values() for v, t in rows]
    print(f"  {k:15s} median {np.median(rel):.3f}   n={len(rel)}")
