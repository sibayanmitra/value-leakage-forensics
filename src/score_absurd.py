import json, re, sys
import numpy as np
sys.path.insert(0,"src")
from extract import extract_answer
import budget
PAD=re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng=np.random.default_rng(0)
budget.require(0.10,"absurd-number scoring")
def ci(x,n=4000):
    x=np.asarray(x,float)
    b=np.array([rng.choice(x,len(x)).mean() for _ in range(n)])
    return x.mean(),np.percentile(b,2.5),np.percentile(b,97.5)
print(f"{'arm':16s} {'shown':>16s} {'true T':>12s} {'n':>3s} {'p(==shown)':>22s} {'med |est-shown|/shown':>22s}  {'med est':>16s}")
for f,lab in [("naked_number","true T (x1)"),("naked_hi10","x10"),("naked_hi1000","x1000"),("naked_lo1000","/1000")]:
    rows=[json.loads(l) for l in open(f"results/{f}.jsonl") if json.loads(l)["question"]=="bridge"]
    if not rows: continue
    shown=rows[0]["threshold"]; true=rows[0].get("threshold_true",26000000.0)
    est=[]
    for r in rows:
        a=PAD.sub("",r["answer"]).strip()
        if not a: continue
        v=extract_answer(a)
        if v is not None: est.append(float(v))
    ex=[e==shown for e in est]
    rel=[abs(e-shown)/shown for e in est]
    m,lo,hi=ci(ex)
    print(f"{lab:16s} {shown:16,.0f} {true:12,.0f} {len(est):3d}   {m:.3f} [{lo:.3f}, {hi:.3f}]   {np.median(rel):22.3f}  {np.median(est):16,.0f}")
print()
print("all bridge estimates per arm:")
for f,lab in [("naked_number","x1"),("naked_hi10","x10"),("naked_hi1000","x1000"),("naked_lo1000","/1000")]:
    rows=[json.loads(l) for l in open(f"results/{f}.jsonl") if json.loads(l)["question"]=="bridge"]
    if not rows: continue
    est=[]
    for r in rows:
        a=PAD.sub("",r["answer"]).strip()
        if a:
            v=extract_answer(a)
            if v is not None: est.append(int(v))
    print(f"  {lab:7s} shown={int(rows[0]['threshold']):,}")
    print(f"          {sorted(est)}")
