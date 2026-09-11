import json, re, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
QS = ["bridge", "giraffes", "tbc"]
PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng = np.random.default_rng(0)
clean = lambda s: PAD.sub("", s or "").strip()

def cells_from(rows):
    out = collections.defaultdict(list)
    for r in rows:
        if r["question"] not in QS: continue
        a = clean(r["answer"])
        if not a: continue
        v = extract_answer(a)
        if v is not None: out[r["question"]].append((v, r["threshold"]))
    return out

def rel_boot(cells, n=4000):
    """median |est-T|/T, equal question weight (mean of per-question medians)."""
    per = {q: np.array([abs(v - t) / t for v, t in rs]) for q, rs in cells.items()}
    pt = float(np.mean([np.median(p) for p in per.values()]))
    bs = np.array([np.mean([np.median(rng.choice(p, len(p))) for p in per.values()]) for _ in range(n)])
    return pt, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

def p_boot(cells, fn, n=4000):
    per = {q: np.array([fn(v, t) for v, t in rs], float) for q, rs in cells.items()}
    pt = float(np.mean([p.mean() for p in per.values()]))
    bs = np.array([np.mean([rng.choice(p, len(p)).mean() for p in per.values()]) for _ in range(n)])
    return pt, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))

print("=" * 78)
print("ANCHOR PULL: median |estimate - T| / T, equal question weight")
print("=" * 78)
for k, f in [("baseline", "our_baseline"), ("neutral_T", "neutral_T_26k"), ("above_good", "above_good_26k"),
             ("below_good", "below_ours"), ("warned_anchor", "warned_anchor"), ("warned_values", "warned_values"),
             ("valence_above", "valence_above"), ("valence_below", "valence_below")]:
    c = cells_from([json.loads(l) for l in open(f"results/{f}.jsonl")])
    r = rel_boot(c)
    print(f"  {k:15s} {r[0]:.3f} [{r[1]:.3f}, {r[2]:.3f}]")

print("\n" + "=" * 78)
print("STEERING — does the intervention move ANYTHING? (anchor pull + side)")
print("=" * 78)
S = collections.defaultdict(list)
for l in open("results/steer_dm.jsonl"):
    r = json.loads(l); S[(r["direction"], r["sign"], r["condition"], r["alpha"])].append(r)
for k in sorted(S, key=lambda x: (x[0], x[2], x[3])):
    c = cells_from(S[k])
    if not c: continue
    rel = rel_boot(c); p = p_boot(c, lambda v, t: v > t)
    name = f"{k[0]}{'+' if k[1] > 0 else '-'}->{k[2]} a={k[3]:g}"
    print(f"  {name:30s} |est-T|/T {rel[0]:.3f} [{rel[1]:.3f}, {rel[2]:.3f}]   p(>T) {p[0]:.3f} [{p[1]:.3f}, {p[2]:.3f}]")
