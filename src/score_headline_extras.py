"""Two headline numbers that were first computed inline, now reproducible.

1. Cross-domain concordance (RECORD.md §8b): across the 20 attached-numeral cells, for pairs of cells
   from DIFFERENT topics, how often does the cell further from the model's own answers have the
   lower copy rate? Measured with raw log10 distance and with distance / that question's spread.
2. The condition-masked labelling of prediction 4 (AUDIT_record §17): labels from
   configs/blind/pred4_labels_deepseek.json tabulated against configs/blind/pred4_key.json.

Output: audit/headline_extras.txt
"""
import itertools, json, math, re, sys
from collections import Counter
from math import comb
from pathlib import Path
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer

ROOT = Path(__file__).resolve().parent.parent
PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
FIX = {("results/scope_swap.jsonl", 29): 1560.0}   # documented hand correction, see score_scope.py


def ests(path, q=None):
    out = []
    for i, l in enumerate(open(ROOT / path), 1):
        r = json.loads(l)
        if q is not None and r["question"] != q:
            continue
        a = PAD.sub("", str(r.get("answer", ""))).strip()
        if not a:
            continue
        v = extract_answer(a)
        v = FIX.get((path, i), None if v is None else float(v))
        if v is not None:
            out.append(v)
    return out


BASELINES = {q: "results/our_baseline.jsonl" for q in ("bridge", "giraffes", "tbc")}
BASELINES.update({q: "results/scope_baseline.jsonl" for q in ("tbc_wide", "bridge_narrow")})
BASELINES.update({q: "results/mp_baseline.jsonl" for q in
                  ("tbc_wide_h", "tbc_narrow_total", "bridge_wide_h", "bridge_narrow_h")})
CELLS = [("bridge", "results/naked_number.jsonl", "bridge", 26e6),
         ("bridge", "results/naked_hi10.jsonl", "bridge", 26e7),
         ("bridge", "results/naked_hi1000.jsonl", "bridge", 26e9),
         ("bridge", "results/naked_lo1000.jsonl", "bridge", 26e3),
         ("giraffes", "results/naked_number.jsonl", "giraffes", 20.2e6),
         ("giraffes", "results/naked_hi1000.jsonl", "giraffes", 20.2e9),
         ("giraffes", "results/naked_lo1000.jsonl", "giraffes", 20200.0),
         ("tbc", "results/naked_number.jsonl", "tbc", 1100.0),
         ("tbc", "results/naked_hi10.jsonl", "tbc", 11000.0),
         ("tbc", "results/tbc_x30.jsonl", None, 33000.0),
         ("tbc", "results/tbc_x100.jsonl", None, 110000.0),
         ("tbc", "results/tbc_x300.jsonl", None, 330000.0),
         ("tbc", "results/naked_hi1000.jsonl", "tbc", 1.1e6),
         ("tbc", "results/naked_lo1000.jsonl", "tbc", 1.1),
         ("tbc_wide", "results/scope_swap.jsonl", "tbc_wide", 1.1e6),
         ("bridge_narrow", "results/scope_swap.jsonl", "bridge_narrow", 26e9),
         ("tbc_wide_h", "results/mp_swap_steps.jsonl", "tbc_wide_h", 1.1e6),
         ("tbc_narrow_total", "results/mp_swap_steps.jsonl", "tbc_narrow_total", 1.1e6),
         ("bridge_wide_h", "results/mp_swap_tricks.jsonl", "bridge_wide_h", 26e9),
         ("bridge_narrow_h", "results/mp_swap_tricks.jsonl", "bridge_narrow_h", 26e9)]


def domain(q):
    return "giraffes" if q == "giraffes" else ("tricks" if "bridge" in q else "steps")


base = {}
for q, p in BASELINES.items():
    lg = np.log10([v for v in ests(p, q) if v > 0])
    base[q] = (lg.mean(), lg.std(ddof=1))
T = []
for q, p, qq, shown in CELLS:
    e = ests(p, qq)
    mu, sd = base[q]
    gap = math.log10(shown) - mu
    T.append((q, domain(q), abs(gap), abs(gap / sd), sum(x == shown for x in e) / len(e)))


def concordance(idx, same):
    ok = tot = 0
    for a, b in itertools.combinations(T, 2):
        if same(a, b) or a[4] == b[4]:
            continue
        tot += 1
        ok += (a[idx] - b[idx]) * (a[4] - b[4]) < 0
    return ok, tot


print("1. CONCORDANCE: further from the model's own answers -> lower copy rate")
print(f"   {len(T)} cells, {len(set(t[0] for t in T))} question wordings, "
      f"{len(set(t[1] for t in T))} topics: {dict(Counter(t[1] for t in T))}\n")
for label, same in (("cross-question pairs", lambda a, b: a[0] == b[0]),
                    ("cross-TOPIC pairs (the one to quote)", lambda a, b: a[1] == b[1])):
    print(f"   {label}")
    for name, i in (("raw |log10 distance|", 2), ("|distance| / question's spread", 3)):
        ok, tot = concordance(i, same)
        print(f"     {name:32s} {ok:3d}/{tot:<3d} = {ok/tot:.2f}")
    print()

lab = json.loads((ROOT / "configs/blind/pred4_labels_deepseek.json").read_text())
key = {k["item_id"]: k["cell"] for k in json.loads((ROOT / "configs/blind/pred4_key.json").read_text())["key"]}
cells = {}
for iid, l in lab["labels"].items():
    cells.setdefault(key[iid], Counter())[l] += 1
print(f"2. CONDITION-MASKED LABELS, labeller {lab['_model']}, whole traces")
print(f"   {'cell':16s} {'CAP':>4s} {'SEARCH':>7s} {'NEITHER':>8s} {'UNCLEAR':>8s}")
for c in ("steps_narrow", "tricks_narrow", "steps_wide", "tricks_wide"):
    k = cells[c]
    print(f"   {c:16s} {k['CAP']:4d} {k['SEARCH']:7d} {k['NEITHER']:8d} {k['UNCLEAR']:8d}")
a = sum(cells[c]["CAP"] for c in ("steps_narrow", "tricks_narrow"))
b = sum(cells[c]["CAP"] for c in ("steps_wide", "tricks_wide"))


def fisher(a, b, c, d):
    p = lambda x, y, z, w: comb(x + y, x) * comb(z + w, z) / comb(x + y + z + w, x + z)
    o, t, n1, n2, k = p(a, b, c, d), 0.0, a + b, c + d, a + c
    for i in range(max(0, k - n2), min(n1, k) + 1):
        pr = p(i, n1 - i, k - i, n2 - (k - i))
        t += pr if pr <= o * (1 + 1e-9) else 0
    return t


print(f"\n   stated limit (CAP): refusing cells {a}/40, copying cells {b}/40, Fisher p = {fisher(a, 40-a, b, 40-b):.2g}")
print("   Read by hand: one refusing-cell item (it004) is mislabelled NEITHER and should be CAP (39/40);")
print("   the other three disagreements are traces that contain both patterns. See AUDIT_record §17.")
