"""Counterfactual importance across positions in a single naked_number trace.

Importance at position k = |p(answer == 26,000,000 | sentence k kept)
                          - p(answer == 26,000,000 | sentence k resampled)|.

The outcome is the copy rate rather than a KL over answer buckets, because
`naked_number` on bridge is near-deterministic: 20/20 rollouts answer exactly
26,000,000, so any movement is signal rather than resampling noise.
"""
import json, glob, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
import budget

TARGET = 26_000_000
rng = np.random.default_rng(0)

rows = []
for f in sorted(glob.glob("results/sweep_src*.jsonl") + glob.glob("results/sweep_rev*.jsonl")):
    for l in open(f):
        rows.append(json.loads(l))

budget.require(0.15, "sweep scoring")

for r in rows:
    v = extract_answer(r["answer"])
    r["est"] = None if v is None else int(v)
    r["copied"] = int(r["est"] == TARGET)


def ci(x, n=8000):
    x = np.asarray(x, float)
    if len(x) == 0: return (float("nan"),) * 3
    b = np.array([rng.choice(x, len(x)).mean() for _ in range(n)])
    return x.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)


def diff_ci(a, b, n=8000):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = np.array([rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean()
                  for _ in range(n)])
    return a.mean() - b.mean(), np.percentile(d, 2.5), np.percentile(d, 97.5)


by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    by[(r["source"], r["frac"], r["kind"], r["sent_idx"])][r["arm"]].append(r["copied"])

print(f"\n{len(rows)} rows | {sum(r['est'] is None for r in rows)} with no committed number\n")
print(f"{'src':>4} {'frac':>6} {'kind':>9} {'sent':>5}  {'p(copy) kept':>14}  {'p(copy) resampled':>19}  {'importance (kept - resampled)':>30}")
for k in sorted(by):
    a = by[k]
    o, ol, oh = ci(a["original"]); s, sl, sh = ci(a["resampled"])
    d, dl, dh = diff_ci(a["original"], a["resampled"])
    print(f"{k[0]:>4} {k[1]:>6.2f} {k[2]:>9} {k[3]:>5}  {o:>5.3f} n={len(a['original']):<2}   "
          f"{s:>5.3f} n={len(a['resampled']):<2}      {d:>+7.3f} [{dl:+.3f}, {dh:+.3f}]")

print("\nsentence that was replaced, per position:")
for k in sorted(by):
    sent = next(r["sentence"] for r in rows
                if (r["source"], r["frac"], r["kind"], r["sent_idx"]) == k and r["arm"] == "original")
    print(f"  src{k[0]} frac {k[1]:.2f} {k[2]} sent {k[3]}: {sent.strip()[:110]!r}")

print("\nevery answer that was NOT 26,000,000:")
for r in rows:
    if not r["copied"]:
        print(f"  src{r['source']} frac {r['frac']:.2f} {r['arm']:>9}: est={r['est']}")
