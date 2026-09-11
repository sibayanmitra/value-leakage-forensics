"""The 2x2 with the direction-without-a-number column added (figures/v5_1b_direction.png).

Same style as src/figures_v5.py: bars at k/n pooled over the three questions, Wilson whiskers,
labelled "k/n". Direction answers are read off by the same cached LLM judge (src/extract.py).

usage: python src/figures_verbal.py
"""
import json, sys
import numpy as np
sys.path.insert(0, "src")
from figures_v5 import plt, pct, cbars, note, above, BLUE, ORANGE, AQUA, INK
from extract import extract_answer

T = {"bridge": 26_000_000, "giraffes": 20_200_000, "tbc": 1_100}


def above_verbal(f):
    k = n = 0
    for l in open(f"results/{f}.jsonl"):
        r = json.loads(l); a = (r.get("answer") or "").strip()
        v = extract_answer(a) if a else None
        if v is not None: k += v > T[r["question"]]; n += 1
    return k, n


rows = [("nothing at stake", ["our_baseline", None, "neutral_T_26k"], BLUE),
        ("good cause if above / on the high side", ["valence_above", "verbal_high", "above_good_26k"], ORANGE),
        ("good cause if below / on the low side", ["valence_below", "verbal_low", "below_ours"], AQUA)]
fig, ax = plt.subplots(figsize=(7.0, 3.8)); W = 0.24
for i, (lab, files, col) in enumerate(rows):
    xs, ks, ns = [], [], []
    for j, f in enumerate(files):
        if f is None: continue
        k, n = above_verbal(f) if f.startswith("verbal") else above(f)
        xs.append(j + (i - 1) * (W + 0.02)); ks.append(k); ns.append(n)
    cbars(ax, np.array(xs), ks, ns, col, W, label=lab)
ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["no number", "a direction only\n(\"high side\" / \"low side\")", "the number"])
ax.set_ylabel("estimates above the threshold"); ax.set_ylim(0, 1.05)
ax.yaxis.set_major_formatter(pct); ax.grid(axis="x", visible=False)
ax.legend(frameon=False, fontsize=8, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.2))
ax.set_title("A direction gives the stakes some grip; the number gives much more", loc="left", fontsize=11.5, color=INK)
note(fig, "Each bar: estimates above the threshold, out of 60 (3 questions × 20). Whiskers: 95% interval. "
          "High vs low side: 41 vs 29 (Fisher p = 0.041). With the number: 39 vs 11.", y=-0.1)
fig.tight_layout(); fig.savefig("figures/v5_1b_direction.png"); plt.close(fig); print("wrote figures/v5_1b_direction.png")
