"""Audit 2026-09-10: recompute E0 (authors' rollouts) and E1 (first/last/final bias, first/last AUROC)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "src")
import metrics
from sklearn.metrics import roc_auc_score
df = pd.read_json("results/authors_extracted.jsonl", lines=True)
d = df[(~df.truncated.astype(bool)) & df.est.notna()]
print("E0 per question (metrics.balanced_bias_ci95):")
for k in sorted(d.prompt_key.unique()):
    b = metrics.balanced_bias_ci95(d[d.prompt_key == k]); print(f"  {k:28s} {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]")
b = metrics.balanced_bias_ci95(d); print(f"  POOLED {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]  interventions n={int((d.direction!='baseline').sum())}")
t = pd.read_json("results/trajectories.jsonl", lines=True)
t = t[t.estimates.apply(lambda e: isinstance(e, list) and len(e) > 0)]
side = lambda v, T, dn: (v > T) if dn == "above_good" else (v <= T)
print(f"\nE1, {len(t)} traces with >=1 estimate")
for lab, fn in [("first", lambda e: e[0]), ("last", lambda e: e[-1])]:
    x = t.copy(); x["on_good_side"] = [side(fn(e), T, dn) for e, T, dn in zip(x.estimates, x.threshold, x.direction)]
    b = metrics.balanced_bias_ci95(x); print(f"  bias at {lab:5s} estimate {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]")
x = t.copy(); x["on_good_side"] = [side(v, T, dn) for v, T, dn in zip(x.est, x.threshold, x.direction)]
b = metrics.balanced_bias_ci95(x); print(f"  bias at final answer   {b[0]:+.3f} [{b[1]:+.3f}, {b[2]:+.3f}]")
y = np.array([side(v, T, dn) for v, T, dn in zip(t.est, t.threshold, t.direction)])
for lab, fn in [("first", lambda e: e[0]), ("last", lambda e: e[-1])]:
    f = np.array([(fn(e) - T) / T * (1 if dn == "above_good" else -1) for e, T, dn in zip(t.estimates, t.threshold, t.direction)])
    print(f"  lock-in AUROC at {lab:5s} estimate {roc_auc_score(y, f):.3f}")
