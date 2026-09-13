"""Score the minimal-pair swap and the temperature check (PLAN_2026-09-14_minimal_pairs.md §4).

Two things the 2026-09-12 design got wrong and this fixes:
  - the pairs were not minimal (aggregation and hint list moved too), so the pairs here differ
    only in the referent phrase;
  - exact copying alone hid a graded pull, so every cell also reports where the NON-copiers
    landed, in standard deviations of that question's own baseline.
"""
import json, re, sys, math
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
import budget

PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")


def ests(path, q=None):
    out = []
    try:
        fh = open(path)
    except FileNotFoundError:
        return []
    for line in fh:
        r = json.loads(line)
        if q is not None and r["question"] != q:
            continue
        a = PAD.sub("", str(r.get("answer", ""))).strip()
        if not a:
            continue
        v = extract_answer(a)
        if v is not None:
            out.append(float(v))
    return out


def spread(vals):
    lg = np.log10([v for v in vals if v > 0])
    mad = np.median(np.abs(lg - np.median(lg))) * 1.4826
    return lg.mean(), lg.std(ddof=1), mad, np.median(lg), len(lg)


def fisher(a, b, c, d):
    from math import comb
    def p(x, y, z, w):
        return comb(x + y, x) * comb(z + w, z) / comb(x + y + z + w, x + z)
    obs = p(a, b, c, d); tot = 0.0
    n1, n2, k = a + b, c + d, a + c
    for i in range(max(0, k - n2), min(n1, k) + 1):
        pr = p(i, n1 - i, k - i, n2 - (k - i))
        if pr <= obs * (1 + 1e-9):
            tot += pr
    return tot


budget.require(0.25, "minimal-pair scoring")

print("=" * 80)
print("PREDICTION A: is the baseline spread a property of the question or the sampler?")
print("=" * 80)
QS = ["tbc", "tbc_wide", "giraffes", "bridge_narrow", "bridge"]
rows = []
for q in QS:
    p1 = "results/scope_baseline.jsonl" if q in ("tbc_wide", "bridge_narrow") else "results/our_baseline.jsonl"
    v1, v7 = ests(p1, q), ests("results/baseline_t07.jsonl", q)
    if not v1 or not v7:
        print(f"  {q}: waiting (t=1.0 n={len(v1)}, t=0.7 n={len(v7)})")
        continue
    s1, s7 = spread(v1), spread(v7)
    rows.append((q, s1[1], s7[1], s1[2], s7[2]))
if rows:
    print(f"\n{'question':15s} {'sd @1.0':>8s} {'sd @0.7':>8s} {'MAD @1.0':>9s} {'MAD @0.7':>9s}")
    for q, a, b, c, d in rows:
        print(f"{q:15s} {a:8.2f} {b:8.2f} {c:9.2f} {d:9.2f}")
    o1 = [q for q, _, _, _, _ in sorted(rows, key=lambda r: r[1])]
    o7 = [q for q, _, _, _, _ in sorted(rows, key=lambda r: r[2])]
    print(f"\n  order @1.0: {' < '.join(o1)}")
    print(f"  order @0.7: {' < '.join(o7)}")
    from scipy import stats
    rho = stats.spearmanr([r[1] for r in rows], [r[2] for r in rows])[0]
    print(f"\n  rank correlation of the two orderings: {rho:+.3f}")
    core = [q for q in o7 if q in ("tbc", "giraffes", "bridge")]
    print(f"  PREREG said tbc < giraffes < bridge must hold at 0.7 -> "
          f"{'HOLDS' if core == ['tbc','giraffes','bridge'] else 'BROKEN: ' + ' < '.join(core)}")

print()
print("=" * 80)
print("PREDICTION B: the clean swap, aggregation and hint list held fixed")
print("=" * 80)
PAIRS = [("steps  1,100,000", "results/mp_swap_steps.jsonl",
          ("tbc_wide_h", "wide", 15, "ge"), ("tbc_narrow_total", "narrow", 5, "le"), 1_100_000.0),
         ("tricks 26,000,000,000", "results/mp_swap_tricks.jsonl",
          ("bridge_wide_h", "wide", 12, "ge"), ("bridge_narrow_h", "narrow", 5, "le"), 26_000_000_000.0)]
for lab, path, wide, narrow, shown in PAIRS:
    print(f"\n--- {lab} ---")
    got = {}
    for q, side, thresh, rel in (wide, narrow):
        e = ests(path, q)
        b = ests("results/mp_baseline.jsonl", q)
        if not e or not b:
            print(f"  {q:20s} waiting (swap n={len(e)}, baseline n={len(b)})")
            continue
        mu, sd, mad, med, n = spread(b)
        k = sum(x == shown for x in e)
        nc = [x for x in e if x != shown and x > 0]
        pull = (np.log10(np.median(nc)) - mu) / sd if nc else float("nan")
        z = (math.log10(shown) - mu) / sd
        hit = (k >= thresh) if rel == "ge" else (k <= thresh)
        got[side] = (k, len(e))
        print(f"  {q:20s} {side:6s} copied {k:2d}/{len(e):<2d}  "
              f"baseline med {10**med:>14,.0f} (sd {sd:.2f}, n={n})  z={z:6.1f}  "
              f"non-copiers {pull:+.1f} sd  "
              f"[prereg {'>=' if rel=='ge' else '<='}{thresh} -> {'HIT' if hit else 'MISS'}]")
    if "wide" in got and "narrow" in got:
        (a, na), (c, nc_) = got["wide"], got["narrow"]
        print(f"  Fisher wide vs narrow: p={fisher(a, na-a, c, nc_-c):.4g}")
