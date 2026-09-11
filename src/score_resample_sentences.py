"""Score step 2 (results/resample_sentences.jsonl): does each chosen sentence move the verdict?

For each reliable denier and each chosen sentence k (configs/resample_positions.json):
  P(NO | resampled)  samples cut at the start of sentence k (the model writes its own sentence k)
  P(NO | kept)       samples cut at the start of sentence k+1 (sentence k kept)
  importance(k) = P(NO | kept) - P(NO | resampled)
Also reported: the same with only replacements that are not near-copies of the original sentence
(difflib ratio < 0.8), and each rollout's trajectory of P(NO) along its reply, starting from step 1's
samples from the very start of the reply (results/resample_denials_p*.jsonl).

The forced verdict is a classifier (CLAUDE.md): --read prints every sample's first new sentence and
the end of its reasoning next to its verdict, to be read before any number is reported.
"""
import collections, glob, json, re, sys
import numpy as np

CLEAN = re.compile(r"^\W*\b(YES|NO)\b", re.I)
verdict = lambda f: (m.group(1).upper() if (m := CLEAN.match((f or "").strip())) else None)
norm = lambda s: " ".join((s or "").split())
SIM = 0.8

rows = [json.loads(l) for l in open("results/resample_sentences.jsonl")]
cfg = json.load(open("configs/resample_positions.json"))["rollouts"]
step1 = collections.defaultdict(list)
for f in sorted(glob.glob("results/resample_denials_p*.jsonl")):
    for l in open(f):
        r = json.loads(l)
        if r["group"] == "denial": step1[r["source_line"]].append(verdict(r["forced"]))
by_cut = collections.defaultdict(list)
for r in rows: by_cut[(r["source_line"], r["cut"])].append(r)
print(f"{len(rows)} samples over {len(by_cut)} cuts; settings {sorted({(r['temperature'], r['top_p'], r['top_k'], r['cap']) for r in rows})}")

def rate(rs, keep=lambda r: True):
    v = [verdict(r["forced"]) for r in rs if keep(r)]
    n = sum(x is not None for x in v)
    return v.count("NO"), n, v.count(None)

print("\nTRAJECTORY: share of samples that deny, cut by cut along each greedy reply (the greedy reply itself ended NO)")
for ro in sorted(map(int, cfg)):
    s1 = step1[ro]
    line = [f"start {s1.count('NO')}/{sum(x is not None for x in s1)}"]
    for (r0, cut), rs in sorted(by_cut.items()):
        if r0 != ro: continue
        no, n, u = rate(rs)
        line.append(f"s{rs[0]['next_idx']} {no}/{n}" + (f"(+{u}?)" if u else ""))
    print(f"  rollout {ro:2d}: " + "  ->  ".join(line))

print("\nPER SENTENCE: P(NO) with the sentence resampled vs kept")
print(f"  {'rollout':>7s} {'role':4s} {'sent':>4s}  {'resampled':>9s} {'kept':>6s} {'importance':>10s}   {'resampled, replacement differs (sim<0.8)':>40s}   sentence")
imp = collections.defaultdict(list)
for ro in sorted(map(int, cfg)):
    cuts = {rs[0]["next_idx"]: rs for rs in (v for (r0, _), v in by_cut.items() if r0 == ro)}
    for p in cfg[str(ro)]:
        k = p["idx"]
        if k not in cuts or k + 1 not in cuts: print(f"  {ro:7d} {p['role']:4s} {k:4d}  (missing samples)"); continue
        a_no, a_n, _ = rate(cuts[k]); b_no, b_n, _ = rate(cuts[k + 1])
        d_no, d_n, _ = rate(cuts[k], lambda r: r["sim"] < SIM)
        i = b_no / max(b_n, 1) - a_no / max(a_n, 1)
        imp[p["role"]].append((ro, i))
        print(f"  {ro:7d} {p['role']:4s} {k:4d}  {a_no:>4d}/{a_n:<4d} {b_no:>3d}/{b_n:<2d} {i:>+10.2f}   {d_no:>4d}/{d_n:<4d} of the replacements that differ {'':12s}  {cuts[k][0]['orig_next'][:70]!r}")
print("\nBY ROLE (mean importance over rollouts): " + ", ".join(f"{r} {np.mean([x for _, x in v]):+.2f} (n={len(v)})" for r, v in sorted(imp.items())))

if "--read" in sys.argv:
    print("\n################ every sample: cut, first new sentence (sim to original), end of reasoning, verdict")
    for i, r in enumerate(rows, 1):
        print(f"\n[line {i}] rollout {r['source_line']} cut s{r['next_idx']} sample {r['sample']} | {'finished' if r['finished'] else 'CUT OFF'} | forced {r['forced'][:30]!r}"
              f"\n   new first sentence (sim {r['sim']}): {r['new_next'][:140]!r}\n   …{norm(r['cont'].split('</think>')[0])[-260:]}")
