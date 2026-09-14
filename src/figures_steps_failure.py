"""Why the clean steps swap did not discriminate (FINDINGS_minimal_pairs_2026-09-14.md).

Each steps question's own no-number answers, on a log scale, with the attached numeral and the
point at which that question starts refusing (z = 8, read off the 20-cell ladder).
"""
import json, math, re, sys
import numpy as np
sys.path.insert(0, "src")
from figures_v2 import plt, BLUE, ORANGE, AQUA, INK, INK2, MUTED, PAD
from extract import extract_answer

def ests(path, q):
    out = []
    for l in open(path):
        r = json.loads(l)
        if r["question"] != q: continue
        a = PAD.sub("", str(r.get("answer", ""))).strip()
        if not a: continue
        v = extract_answer(a)
        if v: out.append(float(v))
    return [v for v in out if v > 0]

ROWS = [("tbc", "results/our_baseline.jsonl",
         "ORIGINAL narrow\naverage per person, one class", "1/20", ORANGE),
        ("tbc_narrow_total", "results/mp_baseline.jsonl",
         "NEW narrow\ntotal for all, one class", "20/20", ORANGE),
        ("tbc_wide_h", "results/mp_baseline.jsonl",
         "NEW wide\ntotal for all, a studio-year", "20/20", BLUE),
        ("tbc_wide", "results/scope_baseline.jsonl",
         "ORIGINAL wide\ntotal for all, a studio-year", "20/20", BLUE)]
SHOWN = 1_100_000.0

fig, ax = plt.subplots(figsize=(11.4, 4.9))
for i, (q, path, lab, rate, col) in enumerate(ROWS):
    y = len(ROWS) - 1 - i
    v = ests(path, q); lg = np.log10(v)
    mu, sd = lg.mean(), lg.std(ddof=1)
    ax.scatter(lg, np.full(len(lg), y) + np.random.default_rng(0).normal(0, .045, len(lg)),
               s=16, color=col, alpha=.45, zorder=3, linewidths=0)
    ax.plot([mu - sd, mu + sd], [y, y], color=col, lw=3.2, solid_capstyle="round", zorder=4)
    ax.plot([mu], [y], "|", color=INK, ms=16, mew=2, zorder=5)
    cut = mu + 8 * sd                     # z = 8, where refusing starts on the 20-cell ladder
    ax.plot([cut], [y], "v", color="#c0392b", ms=9, zorder=6)
    ax.plot([mu, cut], [y - .22, y - .22], color=MUTED, lw=.9, ls=(0, (3, 3)), zorder=2)
    if cut > 9.0:
        ax.text(cut - .18, y - .02, "refuses beyond here", fontsize=7.4, color="#c0392b",
                va="center", ha="right")
    else:
        ax.text(cut + .18, y - .02, "refuses beyond here", fontsize=7.4, color="#c0392b",
                va="center")
    ax.text(-0.6, y, lab, fontsize=8.4, color=INK2, ha="right", va="center")
    ax.text(11.7, y, rate, fontsize=10, color=col, ha="right", va="center", weight="bold")

ax.axvline(math.log10(SHOWN), color=INK, lw=1.6, zorder=1)
ax.text(math.log10(SHOWN), 3.62, "  the number shown: 1,100,000", fontsize=9, color=INK, va="bottom")
ax.set_xlim(-1.2, 12.0); ax.set_ylim(-0.75, 3.9)
ax.set_yticks([]); ax.spines[["left", "right", "top"]].set_visible(False)
ax.set_xticks(range(0, 12, 2))
ax.set_xticklabels([f"$10^{{{t}}}$" for t in range(0, 12, 2)])
ax.set_xlabel("the model's own answer when shown no number (log scale)", fontsize=9)
ax.text(11.7, 3.62, "copied", fontsize=8.6, color=INK2, ha="right", va="bottom")
fig.text(0.005, 0.015,
         "Dots are the 20 no-number answers; the bar is ±1 sd of their spread and the tick is the centre. "
         "The red marker is 8 spreads above the centre, where refusing begins on the 20-cell ladder. "
         "1,100,000 clears that line only for the ORIGINAL narrow question, which is the only one that refuses.",
         fontsize=7.2, color=MUTED)
fig.tight_layout(rect=[0.04, 0.06, 1, 1])
fig.savefig("figures/fig10_steps_failure.png", dpi=200)
print("wrote figures/fig10_steps_failure.png")
