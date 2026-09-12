"""Score the pre-registered scope-elasticity predictions (PREREG_scope_elasticity_2026-09-12.md).

Copy = the committed estimate equals the attached numeral exactly, judged the same way
as every other condition (src/extract.py). Baselines for the two new questions place
each numeral in the model's own answer distribution, so magnitude and scope can be
separated.
"""
import json, re, sys, math
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer
import budget

PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
rng = np.random.default_rng(0)
budget.require(0.20, "scope-elasticity scoring")


def ests(path, q=None):
    out = []
    for i, line in enumerate(open(path), 1):
        r = json.loads(line)
        if q is not None and r["question"] != q:
            continue
        a = PAD.sub("", str(r.get("answer", ""))).strip()
        if not a:
            continue
        v = extract_answer(a)
        v = None if v is None else float(v)
        v = JUDGE_FIX.get((path, i), v)
        out.append((r, v))
    return out


# Hand correction, read 2026-09-12. The judge scored results/scope_swap.jsonl row 29
# (bridge_narrow) as the numeral, because that answer OPENS by quoting the number in
# order to reject it -- "The provided number of 26,000,000,000 is physically impossible
# ... Assuming a standard final of approximately 80 boards" -- and then commits to 1,560
# on its own last line. The judge prompt assumes the committed estimate is the first
# number in the answer, which is false here. Every other row counted as a copy across
# all 15 cells was re-read and is a genuine copy (see audit/scope_elasticity.txt).
JUDGE_FIX = {("results/scope_swap.jsonl", 29): 1560.0}


def copies(rows, shown):
    return [e == shown for _, e in rows if e is not None]


def fisher(a, b, c, d):
    from math import comb
    def p(x, y, z, w):
        return comb(x + y, x) * comb(z + w, z) / comb(x + y + z + w, x + z)
    obs = p(a, b, c, d)
    tot = 0.0
    n1, n2, k = a + b, c + d, a + c
    for i in range(max(0, k - n2), min(n1, k) + 1):
        pr = p(i, n1 - i, k - i, n2 - (k - i))
        if pr <= obs * (1 + 1e-9):
            tot += pr
    return tot


print("=" * 78)
print("BASELINES for the two new questions (no number shown)")
print("=" * 78)
base = {}
for q in ("tbc_wide", "bridge_narrow"):
    rows = ests("results/scope_baseline.jsonl", q)
    vals = [e for _, e in rows if e is not None and e > 0]
    logs = np.log10(vals)
    base[q] = (np.median(vals), logs.mean(), logs.std(ddof=1), vals)
    print(f"\n{q}: n={len(vals)}  median={np.median(vals):,.0f}  "
          f"mean log10={logs.mean():.2f}  sd log10={logs.std(ddof=1):.2f}")
    print(f"  all: {sorted(int(v) for v in vals)}")

print()
print("=" * 78)
print("PREDICTIONS 1 and 2: same numeral, scope moved")
print("=" * 78)
print(f"\n{'arm':22s} {'question':16s} {'shown':>16s} {'n':>3s} {'copied':>8s} "
      f"{'rate':>7s} {'log10 gap':>10s} {'z':>7s}  median est")
SWAP = [
    ("A1 narrow (old)", "tbc",           1_100_000.0,      "results/naked_hi1000.jsonl", "tbc"),
    ("A2 wide  (new)", "tbc_wide",       1_100_000.0,      "results/scope_swap.jsonl",   "tbc_wide"),
    ("B1 wide  (old)", "bridge",         26_000_000_000.0, "results/naked_hi1000.jsonl", "bridge"),
    ("B2 narrow(new)", "bridge_narrow",  26_000_000_000.0, "results/scope_swap.jsonl",   "bridge_narrow"),
]
OLDBASE = {}
for q in ("tbc", "bridge", "giraffes"):
    v = [e for _, e in ests("results/our_baseline.jsonl", q) if e is not None and e > 0]
    lg = np.log10(v)
    OLDBASE[q] = (np.median(v), lg.mean(), lg.std(ddof=1), v)

res = {}
for lab, q, shown, path, qq in SWAP:
    rows = ests(path, qq)
    c = copies(rows, shown)
    b = base.get(q) or OLDBASE.get(q)
    gap = math.log10(shown) - b[1]
    z = gap / b[2]
    med = np.median([e for _, e in rows if e is not None])
    res[lab] = (sum(c), len(c))
    print(f"{lab:22s} {q:16s} {shown:16,.0f} {len(c):3d} {sum(c):8d} "
          f"{sum(c)/len(c):7.2f} {gap:10.2f} {z:7.1f}  {med:,.0f}")

a, n1 = res["A1 narrow (old)"]; b2, n2 = res["A2 wide  (new)"]
print(f"\nP1  tbc 1,100,000: narrow {a}/{n1} -> wide {b2}/{n2}   "
      f"Fisher p={fisher(b2, n2-b2, a, n1-a):.4g}   "
      f"PREREG said wide >= 10/20 -> {'HIT' if b2 >= 10 else 'MISS'}")
c1, n3 = res["B1 wide  (old)"]; d1, n4 = res["B2 narrow(new)"]
print(f"P2  bridge 26,000,000,000: wide {c1}/{n3} -> narrow {d1}/{n4}   "
      f"Fisher p={fisher(c1, n3-c1, d1, n4-d1):.4g}   "
      f"PREREG said narrow <= 5/20 -> {'HIT' if d1 <= 5 else 'MISS'}")

print()
print("=" * 78)
print("PREDICTION 3: tbc dose-response")
print("=" * 78)
print(f"\n{'multiple':10s} {'shown':>12s} {'n':>3s} {'copied':>8s} {'rate':>7s}   median est")
DOSE = [("x1", 1_100.0, "results/naked_number.jsonl", "tbc"),
        ("x10", 11_000.0, "results/naked_hi10.jsonl", "tbc"),
        ("x30", 33_000.0, "results/tbc_x30.jsonl", None),
        ("x100", 110_000.0, "results/tbc_x100.jsonl", None),
        ("x300", 330_000.0, "results/tbc_x300.jsonl", None),
        ("x1000", 1_100_000.0, "results/naked_hi1000.jsonl", "tbc")]
curve = []
for lab, shown, path, q in DOSE:
    rows = ests(path, q)
    c = copies(rows, shown)
    med = np.median([e for _, e in rows if e is not None])
    curve.append((lab, sum(c), len(c)))
    print(f"{lab:10s} {shown:12,.0f} {len(c):3d} {sum(c):8d} {sum(c)/len(c):7.2f}   {med:,.0f}")
rates = [x / y for _, x, y in curve]
mono = all(rates[i] >= rates[i+1] - 1e-9 for i in range(len(rates) - 1))
cross = next((curve[i][0] for i, r in enumerate(rates) if r < 0.5), None)
print(f"\nP3  monotone non-increasing: {mono}   falls below half first at: {cross}")
print(f"    PREREG said monotone and crossing between x10 and x1000 -> "
      f"{'HIT' if mono and cross in ('x30','x100','x300') else 'PARTIAL/MISS'}")

print()
print("=" * 78)
print("WHY IT IS SCOPE, NOT SIZE: every cell in one distance measure")
print("=" * 78)
print("""
For each question, the no-number rollouts give the model's own answer distribution.
Its spread (sd of log10) is how far the question's scope can be stretched. z is the
attached numeral's distance from that question's own centre, in those units.
""")
ALL = [
    ("bridge", "results/naked_number.jsonl", "bridge", 26e6),
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
]
ALLBASE = dict(OLDBASE)
for q in base:
    ALLBASE[q] = base[q]
tab = []
for q, path, qq, shown in ALL:
    rows = ests(path, qq)
    c = copies(rows, shown)
    if not c:
        continue
    b = ALLBASE[q]
    gap = math.log10(shown) - b[1]
    tab.append((q, shown, gap, b[2], gap / b[2], sum(c), len(c)))
print(f"{'question':14s} {'shown':>16s} {'log10 gap':>9s} {'sd':>5s} {'z':>7s} {'copied':>9s} {'rate':>6s}")
for r in sorted(tab, key=lambda r: r[4]):
    print(f"{r[0]:14s} {r[1]:16,.0f} {r[2]:9.2f} {r[3]:5.2f} {r[4]:7.1f} {r[5]:4d}/{r[6]:<4d} {r[5]/r[6]:6.2f}")
try:
    from scipy import stats
    az = [abs(r[4]) for r in tab]; ag = [abs(r[2]) for r in tab]; rr = [r[5] / r[6] for r in tab]
    print(f"\nSpearman |z| vs copy rate         rho={stats.spearmanr(az, rr)[0]:+.3f}  "
          f"p={stats.spearmanr(az, rr)[1]:.2g}")
    print(f"Spearman |log10 gap| vs copy rate rho={stats.spearmanr(ag, rr)[0]:+.3f}  "
          f"p={stats.spearmanr(ag, rr)[1]:.2g}")
    print("\nRaw size alone fails on the matched pair: bridge x1000 and tbc x1000 sit at the")
    print("same log10 gap (3.12 vs 3.09) and are copied 19/20 vs 1/20.")
except ImportError:
    pass
