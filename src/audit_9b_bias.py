"""Audit 2026-09-10: the 9B balanced bias quoted in FINDINGS.md had no script. Recomputed here."""
import json, collections, numpy as np
rows = [json.loads(l) for l in open("results/gate_qwen9b_scored.jsonl")]
rows = [r for r in rows if r.get("est") is not None and not r.get("truncated")]
per = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows: per[r["question"]][r["direction"]].append(float(bool(r["on_good_side"])))
qs = [q for q in per if per[q]["above_good"] and per[q]["below_good"]]
print("cells:", {q: {d: len(v) for d, v in per[q].items()} for q in qs})
rng = np.random.default_rng(0)
pt = np.mean([np.mean(per[q]["above_good"]) + np.mean(per[q]["below_good"]) - 1 for q in qs])
bs = [np.mean([np.mean(rng.choice(per[q]["above_good"], len(per[q]["above_good"]))) +
               np.mean(rng.choice(per[q]["below_good"], len(per[q]["below_good"]))) - 1 for q in qs]) for _ in range(8000)]
print(f"9B balanced bias {pt:+.3f} [{np.percentile(bs,2.5):+.3f}, {np.percentile(bs,97.5):+.3f}], equal weight over {qs}")
