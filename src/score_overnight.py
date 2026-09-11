"""Score the Sep-8 overnight runs: placebo warning, regenerated 2x2 cells, stray numbers."""
import json, re, sys, collections
import numpy as np
sys.path.insert(0,"src")
from extract import extract_answer
QS=["bridge","giraffes","tbc"]; PAD=re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng=np.random.default_rng(0)
clean=lambda s: PAD.sub("",s or "").strip()

def cells(f):
    o=collections.defaultdict(list); drop=0
    for l in open(f"results/{f}.jsonl"):
        r=json.loads(l)
        if r["question"] not in QS: continue
        a=clean(r["answer"])
        if not a: drop+=1; continue
        v=extract_answer(a)
        if v is None: drop+=1; continue
        o[r["question"]].append((float(v),float(r["threshold"])))
    return o,drop
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
    return pt,np.percentile(d,2.5),np.percentile(d,97.5)
above=lambda v,t: float(v>t)

C={}; D={}
for k,f in [("baseline","our_baseline"),("neutral_T","neutral_ours3"),("above_good","above_ours3"),
            ("neutral_T*","neutral_T_26k"),("above_good*","above_good_26k"),
            ("warned_anchor","warned_anchor"),("warned_values","warned_values"),
            ("warned_placebo","warned_placebo")]:
    C[k],D[k]=cells(f)
P={k:out(v,above) for k,v in C.items()}

print("="*74); print("REGENERATED CELLS  (* = cap 26000, no truncation dropout)"); print("="*74)
print(f"  {'condition':14s} {'kept':>6s}  {'p(est > T)':>26s}")
for k in ["baseline","neutral_T","neutral_T*","above_good","above_good*"]:
    p,lo,hi=boot(P[k]); n=sum(len(x) for x in P[k].values())
    print(f"  {k:14s} {n:3d}/60  {p:.3f} [{lo:.3f}, {hi:.3f}]   dropped={D[k]}")
print()
for lab,a,b in [("neutral_T* - baseline","neutral_T*","baseline"),
                ("above_good* - baseline","above_good*","baseline"),
                ("neutral_T* - above_good*","neutral_T*","above_good*")]:
    d=diff(P[a],P[b]); star="***" if (d[1]>0 or d[2]<0) else " n.s."
    print(f"  {lab:26s} {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}] {star}")

print(); print("="*74); print("TURN IT OFF — now with the PLACEBO arm"); print("="*74)
print(f"  {'condition':16s} {'p(est > T)':>24s}   vs above_good*")
for k in ["above_good*","warned_anchor","warned_values","warned_placebo"]:
    p,lo,hi=boot(P[k])
    ex=""
    if k!="above_good*":
        d=diff(P[k],P["above_good*"])
        ex=f"   {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}]"+(" ***" if (d[1]>0 or d[2]<0) else "  n.s.")
    print(f"  {k:16s} {p:.3f} [{lo:.3f}, {hi:.3f}]{ex}")
print()
for lab,a,b in [("anchor - placebo","warned_anchor","warned_placebo"),
                ("values - placebo","warned_values","warned_placebo"),
                ("anchor - values","warned_anchor","warned_values")]:
    d=diff(P[a],P[b]); print(f"  {lab:18s} {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}]"+(" ***" if (d[1]>0 or d[2]<0) else "  n.s."))
