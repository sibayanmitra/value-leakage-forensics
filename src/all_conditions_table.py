"""Every condition we ran, with n and all three measures side by side."""
import json, re, sys, collections
import numpy as np
sys.path.insert(0,"src")
from extract import extract_answer
QS=["bridge","giraffes","tbc"]; PAD=re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng=np.random.default_rng(0)
def cells(f,cond=None):
    o=collections.defaultdict(list); miss=0
    for l in open(f"results/{f}.jsonl"):
        r=json.loads(l)
        if cond and r.get("condition")!=cond: continue
        q=r.get("question", r.get("qid"))
        if "question" in r and r["question"] not in QS: continue
        a=PAD.sub("",r["answer"] or "").strip()
        if not a: miss+=1; continue
        v=extract_answer(a)
        if v is None: miss+=1; continue
        t=float(r.get("threshold", r.get("shown") or 0) or 0)
        o[q].append((float(v),t))
    return o,miss
def agg(c,fn):
    per={q:np.array([fn(v,t) for v,t in rs]) for q,rs in c.items() if rs}
    if not per: return float("nan")
    return float(np.mean([p.mean() for p in per.values()]))
def med(c):
    per={q:np.array([abs(v-t)/t for v,t in rs]) for q,rs in c.items() if rs and rs[0][1]}
    if not per: return float("nan")
    return float(np.mean([np.median(p) for p in per.values()]))

ROWS=[("baseline","our_baseline",None,"no number, no bet"),
      ("neutral_T","neutral_T_26k",None,"number, framed as a threshold, nothing at stake"),
      ("above_good","above_good_26k",None,"the paper: number + above-is-good"),
      ("below_good","below_ours",None,"the paper: number + below-is-good"),
      ("valence_above","valence_above",None,"bet + above-good, NUMBER SENTENCE DELETED"),
      ("valence_below","valence_below",None,"bet + below-good, NUMBER SENTENCE DELETED"),
      ("bare_number","bare_number_full",None,"number mentioned casually, all 3 questions (the 20-row bridge-only pilot is superseded)"),
      ("naked_number","naked_number",None,"bare numeral, no sentence at all"),
      ("naked ×10","naked_hi10",None,"bare numeral, 10x too large"),
      ("naked ×1000","naked_hi1000",None,"bare numeral, 1000x too large"),
      ("naked ÷1000","naked_lo1000",None,"bare numeral, 1000x too small"),
      ("warned_anchor","warned_anchor",None,"above_good + 'ignore the number'"),
      ("warned_values","warned_values",None,"above_good + 'ignore the bet'"),
      ("warned_placebo","warned_placebo",None,"above_good + 'ignore my phrasing'"),
      ("9B naked_number","gate9b_naked_number",None,"9B model, bare numeral"),
      ("9B baseline","gate9b_baseline",None,"9B model, no number")]
print(f"{'condition':17s} {'n':>4s} {'drop':>4s} {'p(>T)':>7s} {'p(==T)':>8s} {'med|est-T|/T':>13s}   what it is")
for lab,f,cond,desc in ROWS:
    try: c,miss=cells(f,cond)
    except FileNotFoundError: continue
    n=sum(len(v) for v in c.values())
    print(f"{lab:17s} {n:4d} {miss:4d} {agg(c,lambda v,t: float(v>t)):7.3f} "
          f"{agg(c,lambda v,t: float(v==t)):8.3f} {med(c):13.3f}   {desc}")
print()
print("verifiable-question set (different questions, so p(>T) is meaningless there):")
for f,cond,desc in [("stray_number","clean","no numeral"),
                    ("stray_right_16k","stray_right","the CORRECT answer appended"),
                    ("stray_wrong_16k","stray_wrong","a WRONG answer appended")]:
    rows=[]
    for l in open(f"results/{f}.jsonl"):
        r=json.loads(l)
        if r["condition"]!=cond: continue
        a=PAD.sub("",r["answer"]).strip()
        if not a: continue
        v=extract_answer(a)
        if v is not None: rows.append((v,r))
    per=collections.defaultdict(list); acc=collections.defaultdict(list)
    for v,r in rows:
        if r["shown"] is not None: per[r["qid"]].append(float(v)==r["shown"])
        acc[r["qid"]].append(float(v)==r["true_answer"])
    cp=np.mean([np.mean(x) for x in per.values()]) if per else float("nan")
    print(f"  {cond:14s} n={len(rows):4d}  copies numeral {cp:.3f}   accuracy "
          f"{np.mean([np.mean(x) for x in acc.values()]):.3f}   {desc}")
