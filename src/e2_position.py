"""Where in the CoT does the aim sentence sit, and does that change how much it matters?"""
import json, re, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
rng = np.random.default_rng(0)

HAND = {}
for l in open("results/e2_all_scored.jsonl"):
    r = json.loads(l)
    if r.get("hand_aim") is not None: HAND[r["sentence"]] = bool(r["hand_aim"])
NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand|bn|[mkb])?\b", re.I)
MULT = {"m":1e6,"million":1e6,"b":1e9,"bn":1e9,"billion":1e9,"k":1e3,"thousand":1e3}
def mentions_T(s,T,tol=.05):
    for v,suf in NUM.findall(s or ""):
        try: x=float(v.replace(",",""))
        except ValueError: continue
        if abs(x*MULT.get((suf or "").lower(),1.)-T)<=tol*T: return True
    return False

# source metadata: row order in the aim-sentence file == source id
META = {}
for batch, path in [("ab","results/aim_sentences.jsonl"), ("cd","results/aim_sentences_v2_strict.jsonl")]:
    for i, l in enumerate(open(path)):
        m = json.loads(l)
        META[(batch, i)] = m

rows = []
for f in "abcd":
    batch = "ab" if f in "ab" else "cd"
    for l in open(f"results/resamples_forced_{f}.jsonl"):
        r = json.loads(l)
        v = extract_answer(r["answer"])
        if v is None: continue
        T = float(r["threshold"])
        rows.append({"src": (batch, r["source"]), "arm": r["arm"], "T": T,
                     "on_good": float((v>T) if r["direction"]=="above_good" else (v<=T)),
                     "aim": HAND.get(r["sentence"]), "mT": mentions_T(r["sentence"], T),
                     "direction": r["direction"]})

def per_source(sel_a, sel_b):
    b = collections.defaultdict(lambda: ([], []))
    for r in rows:
        if sel_a(r): b[r["src"]][0].append(r["on_good"])
        elif sel_b(r): b[r["src"]][1].append(r["on_good"])
    return {s: np.mean(x) - np.mean(y) for s,(x,y) in b.items() if x and y}

def boot(v, n=4000):
    v = np.asarray(v)
    reps = np.array([rng.choice(v, len(v)).mean() for _ in range(n)])
    return v.mean(), np.percentile(reps,2.5), np.percentile(reps,97.5)

AIM  = lambda r: r["arm"]=="resampled" and r["aim"] is True
NOAIM= lambda r: r["arm"]=="resampled" and r["aim"] is False
d_aim = per_source(AIM, NOAIM)
d_on  = per_source(lambda r: r["arm"]=="original", lambda r: r["arm"]=="nosent")

print("=" * 78)
print("WHERE THE AIM SENTENCE SITS")
print("=" * 78)
pos = {}
for s in d_aim:
    m = META.get(s)
    if not m or not m.get("n_reasoning_chars"): continue
    off, nch = m.get("aim_off"), m["n_reasoning_chars"]
    if off is None: continue
    pos[s] = float(off) / float(nch)
p = np.array(list(pos.values()))
print(f"  n={len(p)} sources   relative position (chars): median {np.median(p):.3f}  "
      f"IQR {np.percentile(p,25):.3f}-{np.percentile(p,75):.3f}  min {p.min():.3f} max {p.max():.3f}")
si = np.array([META[s]["aim_idx"]/META[s]["n_sent"] for s in pos if META[s].get("n_sent")])
print(f"  by sentence index:              median {np.median(si):.3f}  "
      f"IQR {np.percentile(si,25):.3f}-{np.percentile(si,75):.3f}")

print("\n" + "=" * 78)
print("DOES POSITION PREDICT HOW MUCH THE SENTENCE MATTERS?")
print("=" * 78)
common = [s for s in pos if s in d_aim]
x = np.array([pos[s] for s in common]); y = np.array([d_aim[s] for s in common])
r = np.corrcoef(x, y)[0,1]
reps = np.array([np.corrcoef(*np.array([[x[i],y[i]] for i in rng.integers(0,len(x),len(x))]).T)[0,1]
                 for _ in range(4000)])
print(f"  corr(position, aim effect) = {r:+.3f} [{np.percentile(reps,2.5):+.3f}, {np.percentile(reps,97.5):+.3f}]  n={len(x)}")
med = np.median(x)
for lab, m in [("EARLY half (before median)", x <= med), ("LATE half", x > med)]:
    v = y[m]; b = boot(v)
    print(f"  aim effect, {lab:26s} {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]  n={len(v)}")

common2 = [s for s in pos if s in d_on]
x2 = np.array([pos[s] for s in common2]); y2 = np.array([d_on[s] for s in common2])
print(f"\n  corr(position, original-nosent) = {np.corrcoef(x2,y2)[0,1]:+.3f}  n={len(x2)}")
for lab, m in [("EARLY half", x2 <= np.median(x2)), ("LATE half", x2 > np.median(x2))]:
    b = boot(y2[m]); print(f"  original - nosent, {lab:20s} {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]  n={m.sum()}")

print("\n" + "=" * 78)
print("INTERACTION: is the aim effect really different in T-restating sentences?")
print("=" * 78)
dA = per_source(lambda r: AIM(r) and r["mT"],      lambda r: NOAIM(r) and r["mT"])
dB = per_source(lambda r: AIM(r) and not r["mT"],  lambda r: NOAIM(r) and not r["mT"])
sh = [s for s in dA if s in dB]
diff = np.array([dB[s] - dA[s] for s in sh])
b = boot(diff)
print(f"  (aim effect | no T restated) - (aim effect | T restated)")
print(f"    = {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]   n={len(sh)} sources with all four cells")
print("  -> CI spans zero: the two strata are NOT shown to differ. Report the split as")
print("     'the effect is not explained by number-restatement', not as an interaction.")
