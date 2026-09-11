"""Significance pass on the anchoring claim: CIs, per-question breakdown, and the
question-level generalisation problem stated explicitly."""
import json, re, sys, collections
import numpy as np
sys.path.insert(0,"src")
from extract import extract_answer
QS=["bridge","giraffes","tbc"]; PAD=re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng=np.random.default_rng(0)

def cells(f):
    out=collections.defaultdict(list)
    for l in open(f"results/{f}.jsonl"):
        r=json.loads(l)
        if r["question"] not in QS: continue
        a=PAD.sub("",r["answer"]).strip()
        if not a: continue
        v=extract_answer(a)
        if v is not None: out[r["question"]].append((float(v),float(r["threshold"])))
    return out
C={n:cells(f) for n,f in [("baseline","our_baseline"),("neutral_T","neutral_ours3"),
    ("above_good","above_ours3"),("below_good","below_ours"),("valence_above","valence_above"),
    ("valence_below","valence_below"),("naked","naked_number"),
    ("warned_anchor","warned_anchor"),("warned_values","warned_values")]}

above=lambda v,t: float(v>t)
def out(c,fn): return {q:np.array([fn(v,t) for v,t in rs]) for q,rs in c.items()}
def boot(per,n=8000):
    pt=np.mean([p.mean() for p in per.values()])
    b=np.array([np.mean([rng.choice(p,len(p)).mean() for p in per.values()]) for _ in range(n)])
    return pt,np.percentile(b,2.5),np.percentile(b,97.5)
def diff(a,b,n=8000):
    ks=[q for q in a if q in b]
    pt=np.mean([a[q].mean() for q in ks])-np.mean([b[q].mean() for q in ks])
    d=np.array([np.mean([rng.choice(a[q],len(a[q])).mean() for q in ks])
               -np.mean([rng.choice(b[q],len(b[q])).mean() for q in ks]) for _ in range(n)])
    return pt,np.percentile(d,2.5),np.percentile(d,97.5),float((d<=0).mean())

P={k:out(v,above) for k,v in C.items()}
print("="*80); print("KEY CONTRASTS — p(estimate > T), equal question weight, 8000 bootstraps")
print("="*80)
tests=[("neutral_T - baseline        [NUMBER, no values]", "neutral_T","baseline"),
       ("above_good - baseline       [number + values]","above_good","baseline"),
       ("neutral_T - above_good      [adding values to a number]","neutral_T","above_good"),
       ("valence_above - baseline    [VALUES, no number]","valence_above","baseline"),
       ("valence_below - baseline    [VALUES, no number, other way]","valence_below","baseline"),
       ("warned_anchor - above_good  [warn about the number]","warned_anchor","above_good"),
       ("warned_values - above_good  [warn about the bet]","warned_values","above_good")]
for lab,a,b in tests:
    d=diff(P[a],P[b])
    star="***" if (d[1]>0 or d[2]<0) else "  n.s."
    print(f"  {lab:52s} {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}] {star}")

print()
print("="*80); print("PER-QUESTION — the bootstrap averages 3 fixed questions; here they are")
print("="*80)
print(f"  {'condition':16s}" + "".join(f"{q:>12s}" for q in QS) + f"{'spread':>10s}")
for k in ["baseline","neutral_T","above_good","below_good","valence_above","valence_below","warned_anchor","warned_values"]:
    vals=[P[k][q].mean() if q in P[k] else np.nan for q in QS]
    print(f"  {k:16s}" + "".join(f"{v:12.3f}" for v in vals) + f"{max(vals)-min(vals):10.3f}")
print()
print("  key contrast per question (neutral_T - baseline):")
for q in QS:
    print(f"    {q:10s} {P['neutral_T'][q].mean()-P['baseline'][q].mean():+.3f}   "
          f"(n={len(P['neutral_T'][q])} vs {len(P['baseline'][q])})")
print("  key contrast per question (valence_above - baseline):")
for q in QS:
    print(f"    {q:10s} {P['valence_above'][q].mean()-P['baseline'][q].mean():+.3f}")

print()
print("="*80); print("ANCHOR PULL — median |est - T|/T, mean of per-question medians")
print("="*80)
def relboot(c,n=8000):
    per={q:np.array([abs(v-t)/t for v,t in rs]) for q,rs in c.items()}
    pt=np.mean([np.median(p) for p in per.values()])
    b=np.array([np.mean([np.median(rng.choice(p,len(p))) for p in per.values()]) for _ in range(n)])
    return pt,np.percentile(b,2.5),np.percentile(b,97.5)
for k in ["baseline","valence_above","valence_below","neutral_T","above_good","naked"]:
    r=relboot(C[k]); print(f"  {k:16s} {r[0]:.3f} [{r[1]:.3f}, {r[2]:.3f}]")
