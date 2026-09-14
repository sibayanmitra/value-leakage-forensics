"""Why the clean steps swap did not discriminate (FINDINGS_minimal_pairs_2026-09-14.md).

Each steps question's own no-number answers, on a log scale, with the attached numeral and the
region where that question starts refusing.

The refusal region is drawn as a BAND, not a line. On the 16 cells that existed before these four
questions were written, copy rate is 0.90 at z = 6.7 and 0.40 at z = 8.4 and nothing was measured
between, so the transition is bracketed, not located. A rule fit on those 16 alone (refuse above
z = 7.5) predicts all four new cells correctly, which is the out-of-sample check that this figure
is not circular.
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

fig, ax = plt.subplots(figsize=(11.4, 5.6))
for i, (q, path, lab, rate, col) in enumerate(ROWS):
    y = len(ROWS) - 1 - i
    v = ests(path, q); lg = np.log10(v)
    mu, sd = lg.mean(), lg.std(ddof=1)
    ax.scatter(lg, np.full(len(lg), y) + np.random.default_rng(0).normal(0, .045, len(lg)),
               s=16, color=col, alpha=.45, zorder=3, linewidths=0)
    ax.plot([mu - sd, mu + sd], [y, y], color=col, lw=3.2, solid_capstyle="round", zorder=4)
    ax.plot([mu], [y], "|", color=INK, ms=16, mew=2, zorder=5)
    # The transition is NOT measured: on the original 16 cells nothing lies between z = 6.7
    # (copied 0.90) and z = 8.4 (copied 0.40). Draw the interval, not a line.
    lo_c, hi_c = mu + 6.7 * sd, mu + 8.4 * sd
    ax.fill_between([lo_c, hi_c], y - .17, y + .17, color="#c0392b", alpha=.16,
                    linewidth=0, zorder=2)
    for xc in (lo_c, hi_c):
        ax.plot([xc, xc], [y - .17, y + .17], color="#c0392b", lw=1.2, alpha=.65, zorder=3)
    cut = hi_c
    if cut > 9.0:
        ax.text(lo_c - .18, y - .02, "starts refusing in here", fontsize=7.4, color="#c0392b",
                va="center", ha="right")
    else:
        ax.text(cut + .18, y - .02, "starts refusing in here", fontsize=7.4, color="#c0392b",
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
fig.text(0.012, 0.015,
         "Dots are the 20 no-number answers; the bar is \u00b11 sd of their spread, the tick is the centre.\n"
         "The red band is 6.7 to 8.4 spreads above the centre. On the 16 cells that existed before these four\n"
         "questions were written, copying is 0.90 at 6.7 and 0.40 at 8.4 and nothing was measured in between,\n"
         "so the band is where refusing must begin, not a fitted line. 1,100,000 clears it only for the\n"
         "ORIGINAL narrow question \u2014 the only one of the four that refuses.",
         fontsize=7.2, color=MUTED)
fig.tight_layout(rect=[0.04, 0.20, 1, 1])
fig.savefig("figures/fig10_steps_failure.png", dpi=200)
print("wrote figures/fig10_steps_failure.png")
