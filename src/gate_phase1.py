"""Phase 1 of PREREG_gate_generalisation_2026-10-16.md: each question's own answers, and the
Phase 2 numerals they imply.

Pools the no-number baselines (old 20 + new 40, or 60 new), extracts each committed answer with
the judge, and reports per question: m = median of log10(answer), s = sample SD of log10(answer)
with a 95% bootstrap interval, old and new halves separately as a pooling check. Then applies the
pre-registered numeral rule n = m x 10^(z s), rounded to two significant figures, for
z = 2, 4, 6, 8, 10, and records the z each rounded numeral actually sits at.

Writes results/gate_phase1_summary.csv and configs/gate_phase2_numerals.json.
Run: .venv/bin/python src/gate_phase1.py   (new answers need the judge key; old ones are cached)
"""
import csv, glob, json, math, re, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, "src")
from extract import extract_answer

PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
PAPER = ["bridge", "crochet", "giraffes", "maiden", "orangecars", "tbc", "turns", "windowdays", "zills"]
PAIRS = ["tbc_wide_h", "tbc_narrow_total", "bridge_wide_h", "bridge_narrow_h"]
OLD = {"results/our_baseline.jsonl": ["bridge", "crochet", "giraffes", "tbc", "zills"],
       "results/mp_baseline.jsonl": PAIRS}
NEW = sorted(glob.glob("results/gate_base_g*_*.jsonl"))
Z_GRID = [2, 4, 6, 8, 10]


def sig2(x):
    """Round to two significant figures, never below the units digit (numerals are integers)."""
    p = max(math.floor(math.log10(x)) - 1, 0)
    return int(round(x / 10 ** p) * 10 ** p)


def load(path, keep):
    vals, excl = {}, {}
    for line in open(path):
        r = json.loads(line)
        q = r["question"]
        if q not in keep:
            continue
        vals.setdefault(q, []); excl.setdefault(q, {"truncated": 0, "null": 0, "nonpositive": 0})
        if r.get("truncated"):
            excl[q]["truncated"] += 1; continue
        a = PAD.sub("", str(r.get("answer", ""))).strip()
        v = extract_answer(a) if a else None
        if v is None:
            excl[q]["null"] += 1; continue
        if v <= 0:
            excl[q]["nonpositive"] += 1; continue
        vals[q].append(v)
    return vals, excl


def ms(v):
    lg = np.log10(np.asarray(v, dtype=float))
    return float(np.median(lg)), float(np.std(lg, ddof=1))


def main():
    allq = PAPER + PAIRS
    old, new, excl = {q: [] for q in allq}, {q: [] for q in allq}, {q: {"truncated": 0, "null": 0, "nonpositive": 0} for q in allq}
    for path, qs in OLD.items():
        v, e = load(path, qs)
        for q in v:
            old[q] += v[q]
            for k in e[q]: excl[q][k] += e[q][k]
    for path in NEW:
        v, e = load(path, allq)
        for q in v:
            new[q] += v[q]
            for k in e[q]: excl[q][k] += e[q][k]

    rng = np.random.default_rng(0)
    rows, numerals = [], {}
    print(f"{'question':18s} {'n':>3s} {'excl':>4s}  {'median':>16s} {'s':>5s} {'s 95% CI':>13s}  "
          f"{'old m / s':>22s}  {'new m / s':>22s}")
    for q in allq:
        pooled = old[q] + new[q]
        if len(pooled) < 2:
            print(f"{q:18s} not enough answers yet ({len(pooled)})"); continue
        m, s = ms(pooled)
        lg = np.log10(np.asarray(pooled, dtype=float))
        boots = [np.std(rng.choice(lg, len(lg)), ddof=1) for _ in range(8000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        om = "%.2f / %.2f" % ms(old[q]) if len(old[q]) > 1 else "-"
        nm = "%.2f / %.2f" % ms(new[q]) if len(new[q]) > 1 else "-"
        ex = sum(excl[q].values())
        print(f"{q:18s} {len(pooled):3d} {ex:4d}  {10**m:16,.0f} {s:5.2f} [{lo:4.2f}, {hi:4.2f}]  {om:>22s}  {nm:>22s}")
        grid = []
        for z in Z_GRID:
            n = sig2(10 ** (m + z * s))
            grid.append({"z_target": z, "numeral": n, "z_actual": round((math.log10(n) - m) / s, 3)})
        numerals[q] = {"experiment": "E1" if q in PAPER else "E2", "n_answers": len(pooled),
                       "median": 10 ** m, "log10_median": m, "spread": s, "grid": grid}
        rows.append({"question": q, "n_answers": len(pooled), "n_old": len(old[q]), "n_new": len(new[q]),
                     **{f"excluded_{k}": c for k, c in excl[q].items()},
                     "median": 10 ** m, "spread": s, "spread_ci_lo": lo, "spread_ci_hi": hi})

    if rows:
        with open("results/gate_phase1_summary.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        Path("configs/gate_phase2_numerals.json").write_text(json.dumps(numerals, indent=1))
        print("\nnumerals (z target -> numeral, actual z):")
        for q, d in numerals.items():
            print(f"  {q:18s} " + "  ".join(f"{g['z_target']}:{g['numeral']:,}({g['z_actual']:+.2f})" for g in d["grid"]))


if __name__ == "__main__":
    main()
