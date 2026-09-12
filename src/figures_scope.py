"""Figure 9: the scope-elasticity test (PREREG_scope_elasticity_2026-09-12.md).

Left: the same numeral on a wide and a narrow version of the same question.
Right: every attached-numeral cell, plotted against the numeral's distance from the
model's own no-number answers for that question, in units of that question's own spread.
"""
import json, math, re, sys
import numpy as np
sys.path.insert(0, "src")
from figures_v2 import plt, PercentFormatter, BLUE, ORANGE, AQUA, INK, INK2, MUTED, PAD
from figures_v5 import wilson, cbars, note, above
from extract import extract_answer

JUDGE_FIX = {("results/scope_swap.jsonl", 29): 1560.0}   # see src/score_scope.py


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
        out.append(JUDGE_FIX.get((path, i), v))
    return [v for v in out if v is not None]


def base(path, q):
    v = [e for e in ests(path, q) if e > 0]
    lg = np.log10(v)
    return lg.mean(), lg.std(ddof=1)


B = {q: base("results/our_baseline.jsonl", q) for q in ("bridge", "giraffes", "tbc")}
B.update({q: base("results/scope_baseline.jsonl", q) for q in ("tbc_wide", "bridge_narrow")})

SWAP = [("steps in ONE\nclass  (narrow)", "results/naked_hi1000.jsonl", "tbc", 1.1e6, ORANGE),
        ("a STUDIO's classes\nfor a year  (wide)", "results/scope_swap.jsonl", "tbc_wide", 1.1e6, BLUE),
        ("ALL Polish\ntournaments  (wide)", "results/naked_hi1000.jsonl", "bridge", 26e9, BLUE),
        ("ONE final\ntable  (narrow)", "results/scope_swap.jsonl", "bridge_narrow", 26e9, ORANGE)]

ALL = [("bridge", "results/naked_number.jsonl", "bridge", 26e6), ("bridge", "results/naked_hi10.jsonl", "bridge", 26e7),
       ("bridge", "results/naked_hi1000.jsonl", "bridge", 26e9), ("bridge", "results/naked_lo1000.jsonl", "bridge", 26e3),
       ("giraffes", "results/naked_number.jsonl", "giraffes", 20.2e6), ("giraffes", "results/naked_hi1000.jsonl", "giraffes", 20.2e9),
       ("giraffes", "results/naked_lo1000.jsonl", "giraffes", 20200.0),
       ("tbc", "results/naked_number.jsonl", "tbc", 1100.0), ("tbc", "results/naked_hi10.jsonl", "tbc", 11000.0),
       ("tbc", "results/tbc_x30.jsonl", None, 33000.0), ("tbc", "results/tbc_x100.jsonl", None, 110000.0),
       ("tbc", "results/tbc_x300.jsonl", None, 330000.0), ("tbc", "results/naked_hi1000.jsonl", "tbc", 1.1e6),
       ("tbc", "results/naked_lo1000.jsonl", "tbc", 1.1),
       ("tbc_wide", "results/scope_swap.jsonl", "tbc_wide", 1.1e6),
       ("bridge_narrow", "results/scope_swap.jsonl", "bridge_narrow", 26e9)]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.6, 4.5), gridspec_kw={"width_ratios": [1, 1.25]})

ks, ns = [], []
for lab, path, q, shown, col in SWAP:
    e = ests(path, q)
    ks.append(sum(x == shown for x in e)); ns.append(len(e))
xs = np.arange(4)
for i, (lab, path, q, shown, col) in enumerate(SWAP):
    cbars(axL, [xs[i]], [ks[i]], [ns[i]], col, 0.62)
axL.set_xticks(xs)
axL.set_xticklabels([s[0] for s in SWAP], fontsize=7.8)
axL.set_ylim(0, 1.30); axL.set_yticks([0, .2, .4, .6, .8, 1.0])
axL.yaxis.set_major_formatter(PercentFormatter(1.0))
axL.set_ylabel("answers that give the attached number")
axL.set_title("Same number, scope moved", fontsize=10.5, color=INK, loc="left")
axL.axvline(1.5, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)
axL.text(0.5, 1.17, "1,100,000 attached", ha="center", fontsize=8.2, color=INK2, style="italic")
axL.text(2.5, 1.17, "26,000,000,000 attached", ha="center", fontsize=8.2, color=INK2, style="italic")
for x0, x1 in ((-0.42, 1.42), (1.58, 3.42)):
    axL.plot([x0, x1], [1.12, 1.12], color=MUTED, lw=0.8, clip_on=False)

COL = {"bridge": BLUE, "giraffes": AQUA, "tbc": ORANGE, "tbc_wide": "#7b4fd1", "bridge_narrow": "#c0392b"}
seen = set()
for q, path, qq, shown in ALL:
    e = ests(path, qq)
    if not e:
        continue
    k, n = sum(x == shown for x in e), len(e)
    mu, sd = B[q]
    z = (math.log10(shown) - mu) / sd
    lo, hi = wilson(k, n)
    axR.errorbar(z, k / n, yerr=[[k / n - lo], [hi - k / n]], fmt="o", ms=6.5, lw=1.1,
                 color=COL[q], ecolor=COL[q], alpha=0.92,
                 label=q if q not in seen else None, zorder=3)
    seen.add(q)
axR.axhline(0.5, color=MUTED, lw=0.8, ls=(0, (3, 3)))
axR.set_ylim(-0.05, 1.1); axR.set_xlim(-21, 24)
axR.yaxis.set_major_formatter(PercentFormatter(1.0))
axR.set_xlabel("how far the attached number sits from the model's own answers\n"
               "for that question, in units of that question's own spread (z)", fontsize=8.6)
axR.set_ylabel("answers that give the attached number")
axR.set_title("Every cell, on one axis", fontsize=10.5, color=INK, loc="left")
axR.legend(frameon=False, fontsize=8, loc="lower left", ncol=2)
axR.annotate("tbc_wide: the number is now\nBELOW the model's own median",
             xy=(-3.0, 1.0), xytext=(-19.5, 0.72), fontsize=7.4, color=INK2,
             arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8))
axR.annotate("bridge_narrow: same 26 billion\nit copied 19/20 when wide",
             xy=(21.1, 0.0), xytext=(6.5, 0.30), fontsize=7.4, color=INK2,
             arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.8))

note(fig, "Qwen3.5-35B-A3B, temperature 1.0, 20 answers per cell; bars and points are Wilson 95% "
          "intervals. Baselines for the two new questions are 20 no-number answers each.")
fig.tight_layout(rect=[0, 0.04, 1, 1])
fig.savefig("figures/fig9_scope.png", dpi=200)
print("wrote figures/fig9_scope.png")
