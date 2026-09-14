"""The elasticity limit of each question, two ways (one figure).

Left: copy rate against how many times the model's own answer the attached numeral is. The three
questions break in completely different places, so raw size does not explain the behaviour.
Right: the same points with the x axis divided by each question's own spread. They collapse onto
one curve, and the break lands in the same place for all three.
"""
import json, math, re, sys
import numpy as np
sys.path.insert(0, "src")
from figures_v2 import plt, PercentFormatter, BLUE, ORANGE, AQUA, INK, INK2, MUTED, PAD
from figures_v5 import wilson
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
    return out

CELLS = {
 "tbc": [("÷1000","results/naked_lo1000.jsonl",1.1),("×1","results/naked_number.jsonl",1100.0),
         ("×10","results/naked_hi10.jsonl",11000.0),("×30","results/tbc_x30.jsonl",33000.0),
         ("×100","results/tbc_x100.jsonl",110000.0),("×300","results/tbc_x300.jsonl",330000.0),
         ("×1000","results/naked_hi1000.jsonl",1.1e6)],
 "giraffes": [("÷1000","results/naked_lo1000.jsonl",20200.0),("×1","results/naked_number.jsonl",20.2e6),
              ("×1000","results/naked_hi1000.jsonl",20.2e9)],
 "bridge": [("÷1000","results/naked_lo1000.jsonl",26e3),("×1","results/naked_number.jsonl",26e6),
            ("×10","results/naked_hi10.jsonl",26e7),("×1000","results/naked_hi1000.jsonl",26e9)]}
LABEL = {"tbc": "steps in one gym class", "giraffes": "spots on all giraffes",
         "bridge": "tricks at Polish bridge"}
COL = {"tbc": ORANGE, "giraffes": AQUA, "bridge": BLUE}

D = {}
for q in CELLS:
    v = [e for e in ests("results/our_baseline.jsonl", q) if e > 0]
    lg = np.log10(v); mu, sd, med = lg.mean(), lg.std(ddof=1), np.median(v)
    pts = []
    for lab, path, shown in CELLS[q]:
        e = ests(path, q); k = sum(x == shown for x in e)
        pts.append((lab, shown, math.log10(shown) - mu, (math.log10(shown) - mu) / sd, k, len(e)))
    D[q] = dict(med=med, sd=sd, pts=pts)

fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.6, 5.1), sharey=True)
for q in ("bridge", "giraffes", "tbc"):
    d = D[q]; c = COL[q]
    for ax, idx in ((axL, 2), (axR, 3)):
        xs = [p[idx] for p in d["pts"]]; ys = [p[4] / p[5] for p in d["pts"]]
        lo = [y - wilson(p[4], p[5])[0] for y, p in zip(ys, d["pts"])]
        hi = [wilson(p[4], p[5])[1] - y for y, p in zip(ys, d["pts"])]
        ax.errorbar(xs, ys, yerr=[lo, hi], fmt="-o", ms=6, lw=1.7, color=c, ecolor=c,
                    elinewidth=1.1, capsize=2.5, alpha=.95,
                    label=f"{LABEL[q]}  (spread {d['sd']:.2f})" if idx == 3 else None, zorder=3)

axR.axvspan(6.7, 8.4, color="#c0392b", alpha=.13, zorder=1, linewidth=0)
axR.text(7.55, 1.10, "steps and giraffes\nbreak in here", fontsize=8.2, color="#c0392b",
         ha="center", va="top")
axR.annotate("bridge never gets this far:\neven ×1500 is only 5 spreads out",
             xy=(5.0, .95), xytext=(-17.5, .70), fontsize=8, color=BLUE,
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))
for ax in (axL, axR):
    ax.axhline(.5, color=MUTED, lw=.9, ls=(0, (3, 3)), zorder=1)
    ax.set_ylim(-.06, 1.12); ax.yaxis.set_major_formatter(PercentFormatter(1.0))
axL.set_ylabel("answers that give back the attached number")
axL.set_xlabel("how far the number is from the model's own answer\n(orders of magnitude)", fontsize=9)
axR.set_xlabel("the same distance, divided by that question's own spread", fontsize=9)
axL.set_title("Raw size: the three break in different places", fontsize=10.5, color=INK, loc="left")
axR.set_title("Same data, in each question's own units: they collapse",
              fontsize=10.5, color=INK, loc="left")
axL.set_xticks(range(-3, 4))
axL.set_xticklabels(["÷1000", "÷100", "÷10", "its own\nanswer", "×10", "×100", "×1000"], fontsize=8)
axR.legend(frameon=False, fontsize=8.4, loc="lower left", bbox_to_anchor=(0.02, 0.10))

axL.annotate("steps gives up\njust after ×11", xy=(1.32, .52), xytext=(-2.95, .58), fontsize=8,
             color=ORANGE, arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1))
axL.annotate("bridge still copying at ×1500", xy=(3.05, .92), xytext=(0.60, .30), fontsize=8,
             color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))
fig.text(0.012, 0.015,
         "Each point is 20 answers with that numeral attached and nothing else changed; bars are Wilson 95% intervals.\n"
         "A question's spread is the sd of log10 of its 20 no-number answers — how wide a range of honest answers it admits.\n"
         "Qwen3.5-35B-A3B, temperature 1.0. The break band on the right is bounded by measurement, not fitted: copying is\n"
         "0.90 at 6.7 and 0.40 at 8.4, with nothing measured in between.",
         fontsize=7.2, color=MUTED)
fig.tight_layout(rect=[0, 0.13, 1, 1])
fig.savefig("figures/fig11_elasticity.png", dpi=200)
print("wrote figures/fig11_elasticity.png")
