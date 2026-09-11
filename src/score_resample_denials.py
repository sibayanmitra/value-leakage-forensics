"""Score step 1 of resampling the own-frame denials (results/resample_denials_p*.jsonl).

Per rollout: how often it denies (strict forced NO) across its samples, and how often its reasoning
finished inside the cap. Groups: the 8 greedy denials and 8 question-matched greedy admissions.
Group difference: mean P(NO) over rollouts; bootstrap resamples rollouts within group and samples
within rollout, 8000 resamples, seed 0.

The forced verdict is a classifier (CLAUDE.md): every sampled NO is printed with the end of its
reasoning, and a seeded sample of YES, to be read before any number is reported.
"""
import json, re, glob, collections, random
import numpy as np

CLEAN = re.compile(r"^\W*\b(YES|NO)\b", re.I)
verdict = lambda r: (m.group(1).upper() if (m := CLEAN.match((r.get("forced") or "").strip())) else None)
norm = lambda s: " ".join((s or "").split())

rows = [json.loads(l) for f in sorted(glob.glob("results/resample_denials_p*.jsonl")) for l in open(f)]
by = collections.defaultdict(list)
for r in rows: by[(r["group"], r["source_line"])].append(r)
print(f"{len(rows)} samples, {len(by)} rollouts; settings: "
      f"{sorted({(r['temperature'], r['top_p'], r['top_k'], r['max_new']) for r in rows})}\n")

print(f"{'group':8s} {'rollout':>7s} {'question':9s} {'n':>3s} {'NO':>3s} {'YES':>4s} {'unp':>4s} {'P(NO)':>6s} {'finished':>8s}")
P = collections.defaultdict(list)
for (g, ln), rs in sorted(by.items(), key=lambda kv: (kv[0][0] != "denial", kv[0][1])):
    v = [verdict(r) for r in rs]; n = sum(x is not None for x in v)
    p = v.count("NO") / max(n, 1); P[g].append(np.array([x == "NO" for x in v if x], float))
    print(f"{g:8s} {ln:7d} {rs[0]['question']:9s} {len(rs):3d} {v.count('NO'):3d} {v.count('YES'):4d} {v.count(None):4d} "
          f"{p:6.2f} {sum(r['finished'] for r in rs):5d}/{len(rs)}")

rng = np.random.default_rng(0)
def boot(arrs):
    return [np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in (arrs[i] for i in rng.integers(0, len(arrs), len(arrs)))])
            for _ in range(8000)]
print()
B = {}   # one set of draws per group (denial first, rollouts in source_line order), reused for the difference
for g in ("denial", "control"):
    if P[g]:
        B[g] = b = boot(P[g]); print(f"{g:8s} mean P(NO) {np.mean([a.mean() for a in P[g]]):.3f} [{np.percentile(b,2.5):.3f}, {np.percentile(b,97.5):.3f}]  rollouts={len(P[g])}")
if P["denial"] and P["control"]:
    d = np.array(B["denial"]) - np.array(B["control"])
    print(f"difference denial - control {np.mean([a.mean() for a in P['denial']]) - np.mean([a.mean() for a in P['control']]):+.3f} "
          f"[{np.percentile(d,2.5):+.3f}, {np.percentile(d,97.5):+.3f}]")

print("\n################ every sampled NO: end of reasoning (read these)")
for r in rows:
    if verdict(r) == "NO":
        print(f"\n[{r['group']} rollout {r['source_line']} sample {r['sample']} {'finished' if r['finished'] else 'CUT OFF'}] "
              f"forced={r['forced'][:30]!r}\n   …{norm(r['full'].split('</think>')[0])[-450:]}")
        if r["finished"]: print("   WRITTEN: " + norm(r["full"].split("</think>", 1)[1])[:200])
print("\n################ 12 random sampled YES (seed 0): end of reasoning")
yes = [r for r in rows if verdict(r) == "YES"]
for r in random.Random(0).sample(yes, min(12, len(yes))):
    print(f"\n[{r['group']} rollout {r['source_line']} sample {r['sample']} {'finished' if r['finished'] else 'CUT OFF'}] …{norm(r['full'].split('</think>')[0])[-300:]}")
unp = [r for r in rows if verdict(r) is None]
print(f"\n################ unparsed ({len(unp)})")
for r in unp: print(f"[{r['group']} rollout {r['source_line']} sample {r['sample']}] forced={r['forced']!r}")
