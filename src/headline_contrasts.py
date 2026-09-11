"""Every headline number for the 2x2 and the warnings, from the CURRENT files, one convention.

Current files: `neutral_T_26k` and `above_good_26k` (regenerated at a 26,000-token cap, 0/60 rows
lost). The older `neutral_ours3` / `above_ours3` lost 5/60 and 7/60 rows to truncation and are
superseded; `analyse_backstop.py` still reads them, which is where +0.485 / +0.635 came from.

Convention: equal weight per question, rows resampled within question, 8000 resamples, seed 0.
"""
import json, re, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
import budget

PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
QS = ("bridge", "giraffes", "tbc")
N = 8000
rng = np.random.default_rng(0)
budget.require(0.05, "headline contrasts")


def cells(f):
    c = collections.defaultdict(list)
    for l in open(f"results/{f}.jsonl"):
        r = json.loads(l)
        if r["question"] not in QS: continue
        a = PAD.sub("", r["answer"]).strip()
        if not a: continue
        v = extract_answer(a)
        if v is None: continue
        c[r["question"]].append((float(v), float(r.get("threshold_true") or r["threshold"])))
    return c


def stat(c, fn, agg=np.mean, eq=True):
    """point + CI. eq=True: mean over questions of per-question agg; False: agg over pooled rows."""
    def one(sample):
        if eq: return np.mean([agg([fn(v, t) for v, t in sample[q]]) for q in QS])
        return agg([fn(v, t) for q in QS for v, t in sample[q]])
    pt = one(c)
    b = [one({q: [c[q][i] for i in rng.integers(0, len(c[q]), len(c[q]))] for q in QS}) for _ in range(N)]
    return pt, np.percentile(b, 2.5), np.percentile(b, 97.5)


def contrast(parts):
    """parts: list of (sign, cells, fn). Returns sum_q-mean of signed per-question means, with CI."""
    def one(sets):
        return np.mean([sum(s * np.mean([fn(v, t) for v, t in st[q]]) for (s, _, fn), st in zip(parts, sets)) for q in QS])
    base = [c for _, c, _ in parts]
    pt = one(base)
    b = [one([{q: [c[q][i] for i in rng.integers(0, len(c[q]), len(c[q]))] for q in QS} for c in base]) for _ in range(N)]
    return pt, np.percentile(b, 2.5), np.percentile(b, 97.5)


above = lambda v, t: float(v > t)
below = lambda v, t: float(v <= t)
F = {k: cells(f) for k, f in [
    ("baseline", "our_baseline"), ("neutral_T", "neutral_T_26k"), ("above_good", "above_good_26k"),
    ("below_good", "below_ours"), ("valence_above", "valence_above"), ("valence_below", "valence_below"),
    ("warned_anchor", "warned_anchor"), ("warned_values", "warned_values"), ("warned_placebo", "warned_placebo")]}
fmt = lambda x: f"{x[0]:+.3f} [{x[1]:+.3f}, {x[2]:+.3f}]"
fm0 = lambda x: f"{x[0]:.3f} [{x[1]:.3f}, {x[2]:.3f}]"

print("Magnitude = mean over questions of the per-question median |est-T|/T (the project's convention,")
print("as in all_conditions_table.py). Within 10% is strict: |est-T|/T < 0.10.\n")
print("CELLS                 n   p(est>T)               median|est-T|/T, eq. q weight   p(within 10% of T)   per-question medians b/g/t")
for k, c in F.items():
    n = sum(len(c[q]) for q in QS)
    pq = "/".join(f"{np.median([abs(v-t)/t for v,t in c[q]]):.3f}" for q in QS)
    print(f"  {k:16s} {n:4d}   {fm0(stat(c, above))}   {fm0(stat(c, lambda v,t: abs(v-t)/t, agg=np.median))}          "
          f"{fm0(stat(c, lambda v,t: float(abs(v-t)/t < 0.10)))}   {pq}")

print("\nCONTRASTS")
given = [(+1, F["below_good"], below), (+1, F["above_good"], above)]
withheld = [(+1, F["valence_below"], below), (+1, F["valence_above"], above)]
g = contrast(given); g = (g[0] - 1, g[1] - 1, g[2] - 1)
w = contrast(withheld); w = (w[0] - 1, w[1] - 1, w[2] - 1)
print(f"  bias, number given    (below_good + above_good - 1)      {fmt(g)}")
print(f"  bias, number withheld (valence_below + valence_above - 1) {fmt(w)}")
print(f"  difference, given - withheld                             {fmt(contrast(given + [(-1, F['valence_below'], below), (-1, F['valence_above'], above)]))}")
print(f"  neutral_T - baseline                                     {fmt(contrast([(+1, F['neutral_T'], above), (-1, F['baseline'], above)]))}")
print(f"  above_good - neutral_T                                   {fmt(contrast([(+1, F['above_good'], above), (-1, F['neutral_T'], above)]))}")
for k in ("warned_anchor", "warned_values", "warned_placebo"):
    print(f"  {k:14s} - above_good                            {fmt(contrast([(+1, F[k], above), (-1, F['above_good'], above)]))}")
