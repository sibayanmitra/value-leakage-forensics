"""Does the answer-key behaviour generalise to questions with verifiable answers?"""
import json, re, sys, collections
import numpy as np
sys.path.insert(0,"src")
from extract import extract_answer
PAD=re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng=np.random.default_rng(0)
rows=[]
for l in open("results/stray_number.jsonl"):
    r=json.loads(l); a=PAD.sub("",r["answer"]).strip()
    if not a: continue
    v=extract_answer(a)
    if v is None: continue
    rows.append({**r,"est":float(v)})
print(f"scored {len(rows)} rollouts, {len(set(r['qid'] for r in rows))} questions\n")

def per_q(sel,fn):
    d=collections.defaultdict(list)
    for r in rows:
        if sel(r): d[r["qid"]].append(float(fn(r)))
    return d
def boot(d,n=8000):
    if not d: return (float('nan'),)*3
    pt=np.mean([np.mean(v) for v in d.values()])
    b=np.array([np.mean([rng.choice(v,len(v)).mean() for v in d.values()]) for _ in range(n)])
    return pt,np.percentile(b,2.5),np.percentile(b,97.5)

print("="*76); print("ACCURACY  (answer == the true answer), equal weight per question"); print("="*76)
acc={}
for c in ["clean","stray_right","stray_wrong"]:
    d=per_q(lambda r,c=c: r["condition"]==c, lambda r: r["est"]==r["true_answer"])
    acc[c]=d; p,lo,hi=boot(d)
    print(f"  {c:13s} {p:.3f} [{lo:.3f}, {hi:.3f}]   n={sum(len(v) for v in d.values())}")
ks=[q for q in acc['clean'] if q in acc['stray_wrong']]
dd=np.array([np.mean([rng.choice(acc['stray_wrong'][q],len(acc['stray_wrong'][q])).mean() for q in ks])
            -np.mean([rng.choice(acc['clean'][q],len(acc['clean'][q])).mean() for q in ks]) for _ in range(8000)])
pt=np.mean([np.mean(acc['stray_wrong'][q]) for q in ks])-np.mean([np.mean(acc['clean'][q]) for q in ks])
print(f"\n  ACCURACY COST of a stray wrong number: {pt:+.3f} [{np.percentile(dd,2.5):+.3f}, {np.percentile(dd,97.5):+.3f}]")

print("\n"+"="*76); print("COPY RATE  (answer == the stray numeral shown)"); print("="*76)
for c in ["stray_wrong","stray_right"]:
    d=per_q(lambda r,c=c: r["condition"]==c, lambda r: r["est"]==r["shown"])
    p,lo,hi=boot(d); print(f"  {c:13s} {p:.3f} [{lo:.3f}, {hi:.3f}]")

print("\n"+"="*76); print("RESTRICTED TO QUESTIONS THE MODEL GETS RIGHT CLEAN (>=0.9)"); print("="*76)
good=[q for q,v in acc["clean"].items() if np.mean(v)>=0.9]
print(f"  {len(good)}/{len(acc['clean'])} questions qualify")
for c in ["clean","stray_wrong"]:
    d={q:v for q,v in acc[c].items() if q in good}; p,lo,hi=boot(d)
    print(f"  accuracy  {c:13s} {p:.3f} [{lo:.3f}, {hi:.3f}]")
d={q:v for q,v in per_q(lambda r: r["condition"]=="stray_wrong", lambda r: r["est"]==r["shown"]).items() if q in good}
p,lo,hi=boot(d); print(f"  copy rate stray_wrong   {p:.3f} [{lo:.3f}, {hi:.3f}]")

print("\n"+"="*76); print("PER QUESTION (clean acc -> stray_wrong acc | copy rate)"); print("="*76)
byq={}
for r in rows: byq.setdefault(r["qid"],r["question"])
for q in sorted(byq):
    ca=np.mean(acc["clean"].get(q,[np.nan])); wa=np.mean(acc["stray_wrong"].get(q,[np.nan]))
    cp=[r["est"]==r["shown"] for r in rows if r["qid"]==q and r["condition"]=="stray_wrong"]
    print(f"  {byq[q][:52]:54s} {ca:.2f} -> {wa:.2f} | {np.mean(cp) if cp else float('nan'):.2f}")
