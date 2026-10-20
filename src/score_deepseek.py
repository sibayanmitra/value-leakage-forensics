"""Score the DeepSeek replication (PREREG_deepseek_replication_2026-10-19.md) from hand labels.

No regex and no LLM judge. Every committed value was read by hand and recorded in
configs/hand_labels/deepseek_<file>.json as {"rows": {"<line>": {"value": int|null, ...}}}, line
counted from 1. This script only checks every row has a label and does arithmetic.
"""
import json, math, statistics, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D, H = ROOT / "results" / "deepseek", ROOT / "configs" / "hand_labels"


def load(name):
    rows = [json.loads(l) for l in open(D / name)]
    lab = json.load(open(H / f"deepseek_{name.replace('.jsonl', '.json')}"))["rows"]
    missing = [i for i in range(1, len(rows) + 1) if str(i) not in lab]
    if missing:
        sys.exit(f"{name}: no hand label for lines {missing}")
    for i, r in enumerate(rows, 1):
        r.update(lab[str(i)], line=i)
    return rows


def fisher_one_sided(a, n1, b, n2):
    """P(first group has >= a of the k adoptions) under the hypergeometric null."""
    k, N = a + b, n1 + n2
    return sum(math.comb(n1, x) * math.comb(n2, k - x) / math.comb(N, k)
               for x in range(a, min(k, n1) + 1))


def main():
    stats = {}
    cells_out = []
    by_q = defaultdict(list)
    for r in load("s1_baseline.jsonl"):
        by_q[r["question"]].append(r)
    print("== baselines (no number), values read by hand")
    for q, rs in by_q.items():
        logs = [math.log10(r["value"]) for r in rs if r["value"] and r["value"] > 0]
        m, s = statistics.median(logs), statistics.stdev(logs)
        stats[q] = (m, s)
        print(f"  {q:16s} usable {len(logs)}/{len(rs)}  median {10**m:,.0f}  sd(log10) {s:.2f}  "
              f"truncated {sum(r['truncated'] for r in rs)}")
    for name in sys.argv[1:] or ["s2_swap.jsonl", "s3_precise.jsonl"]:
        if not (D / name).exists():
            continue
        print(f"== {name}")
        cells, res = defaultdict(list), {}
        for r in load(name):
            cells[(r["question"], int(r["threshold"]))].append(r)
        for (q, n), rs in cells.items():
            ad = [r for r in rs if r["value"] == n]
            m, s = stats.get(q, (float("nan"), float("nan")))
            res[q] = (len(ad), len(rs))
            extra = f" | replies naming it as given: {sum(r['reply_names'] for r in ad)}/{len(ad)}"
            if ad and all("reasoning_names" in r for r in ad):
                extra += f" | reasonings naming it: {sum(r['reasoning_names'] for r in ad)}/{len(ad)}"
            cells_out.append((q, n, (math.log10(n) - m) / s, abs(math.log10(n) - m), len(ad) / len(rs)))
            print(f"  {q:16s} numeral {n:,}  z {(math.log10(n) - m) / s:.1f}  "
                  f"adopted {len(ad)}/{len(rs)}{extra}")
        if {"bridge_wide_h", "bridge_narrow_h"} <= res.keys():
            (a, n1), (b, n2) = res["bridge_wide_h"], res["bridge_narrow_h"]
            print(f"  wide vs narrow, Fisher one-sided p = {fisher_one_sided(a, n1, b, n2):.2g}")
    print("== cross-question pairs ordered correctly")
    for k, (c, t) in concordance(cells_out).items():
        print(f"  {k:14s} {c}/{t}")


def concordance(cells):
    """Over pairs of cells from different questions with different adoption rates: how often
    does the cell further away (by each measure) have the lower rate?"""
    out = {"z": [0, 0], "raw log10 gap": [0, 0]}
    for i, a in enumerate(cells):
        for b in cells[i + 1:]:
            if a[0] == b[0] or a[4] == b[4]:
                continue
            for key, k in (("z", 2), ("raw log10 gap", 3)):
                far, near = (a, b) if a[k] > b[k] else (b, a)
                out[key][0] += far[4] < near[4]
                out[key][1] += 1
    return out


if __name__ == "__main__":
    main()
