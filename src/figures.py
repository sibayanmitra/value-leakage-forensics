"""Figures for the write-up. Every panel carries n, CIs, and the control it rests on."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import extract_answer
from load_authors import load

OUT = Path("figures"); OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
C = {"base": "#8c8c8c", "num": "#1f77b4", "val": "#d62728", "naked": "#2ca02c"}
rng = np.random.default_rng(0)
QS = ["bridge", "giraffes", "tbc"]
df = load(); T = {q: float(df[(df.question == q) & df.threshold.notna()].threshold.iloc[0]) for q in QS}


def cells(path, fn):
    """Per-question arrays of a 0/1 outcome, for equal-weight bootstrap."""
    rows = [json.loads(l) for l in open(path)]
    out = {}
    for r in rows:
        if r["question"] not in QS: continue
        v = extract_answer(r["answer"])
        if v is not None:
            out.setdefault(r["question"], []).append(fn(v, T[r["question"]]))
    return {q: np.array(v, float) for q, v in out.items()}


def boot(per, n=4000):
    pt = np.mean([p.mean() for p in per.values()])
    bs = np.array([np.mean([rng.choice(p, len(p)).mean() for p in per.values()]) for _ in range(n)])
    return pt, np.percentile(bs, 2.5), np.percentile(bs, 97.5), sum(len(p) for p in per.values())


# ---------------------------------------------------------------- Fig 1: Number Ladder
def fig_ladder():
    above = lambda v, t: v > t
    exact = lambda v, t: v == t
    specs = [("no number\nin the prompt", "results/our_baseline.jsonl", C["base"]),
             ("the number,\nno good/bad", "results/neutral_ours3.jsonl", C["num"]),
             ("the full bet\n(above = good)", "results/above_ours3.jsonl", C["val"])]
    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.2), gridspec_kw={"width_ratios": [2.1, 1]})
    for i, (lab, path, col) in enumerate(specs):
        pt, lo, hi, n = boot(cells(path, above))
        ax[0].bar(i, pt, 0.62, color=col)
        ax[0].errorbar(i, pt, yerr=[[pt - lo], [hi - pt]], fmt="none", ecolor="k", capsize=4, lw=1.2)
        ax[0].text(i, hi + .04, f"{pt:.2f}", ha="center", fontweight="bold")
        ax[0].text(i, .03, f"n={n}", ha="center", color="w", fontsize=7.5)
    ax[0].axhline(.5, ls=":", c="k", lw=.8)
    ax[0].set_xticks(range(3)); ax[0].set_xticklabels([s[0] for s in specs])
    ax[0].set_ylabel("P(estimate above the threshold)"); ax[0].set_ylim(0, 1.30)
    ax[0].set_title("Showing the number does as much as the whole moral setup", fontsize=9.5, loc="left")
    ax[0].annotate("", xy=(2, 1.02), xytext=(1, 1.02), arrowprops=dict(arrowstyle="<->", color="k", lw=1))
    ax[0].text(1.5, 1.06, "difference +0.02  [-0.15, +0.17]\n(indistinguishable)", ha="center", fontsize=7.5)
    for i, (lab, path, col) in enumerate([("no number", "results/our_baseline.jsonl", C["base"]),
                                          ("bare number\nappended", "results/naked_number.jsonl", C["naked"])]):
        pt, lo, hi, n = boot(cells(path, exact))
        ax[1].bar(i, pt, 0.55, color=col)
        ax[1].errorbar(i, pt, yerr=[[pt - lo], [hi - pt]], fmt="none", ecolor="k", capsize=4, lw=1.2)
        ax[1].text(i, hi + .04, f"{pt:.2f}", ha="center", fontweight="bold")
    ax[1].set_xticks([0, 1]); ax[1].set_xticklabels(["no number", "bare number\nappended"])
    ax[1].set_ylabel("P(answer is $exactly$ the number)"); ax[1].set_ylim(0, 1.30)
    ax[1].set_title("...and a bare number\nis copied outright", fontsize=9.5, loc="left")
    fig.text(0, -.06, "Qwen3.5-35B-A3B-FP8, our generation throughout. 3 questions, n=20/cell, "
             "equal question weight, 4000-resample bootstrap over questions. Control: our setup runs "
             "slightly LOW vs the authors' API (-0.09 [-0.20, +0.02]), so it cannot invent an upward effect.",
             fontsize=6.6, va="top")
    fig.savefig(OUT / "fig1_number_ladder.png"); plt.close(fig); print("fig1")


# ------------------------------------------------------ Fig 2: First Guess + Lock-In
def fig_when():
    fig, ax = plt.subplots(1, 2, figsize=(7.6, 3.0))
    pts, vals = ["first\nnumber", "last\nnumber", "final\nanswer"], [0.028, 0.615, 0.623]
    los, his = [-0.064, 0.547, 0.557], [0.118, 0.682, 0.687]
    ax[0].bar(range(3), vals, .6, color=[C["base"], C["val"], C["val"]])
    ax[0].errorbar(range(3), vals, yerr=[np.array(vals) - los, np.array(his) - vals],
                   fmt="none", ecolor="k", capsize=4, lw=1.2)
    ax[0].axhline(0, c="k", lw=.8); ax[0].set_xticks(range(3)); ax[0].set_xticklabels(pts)
    ax[0].set_ylabel("bias score"); ax[0].set_ylim(-.15, .8)
    ax[0].text(0, .16, "indistinguishable\nfrom zero", ha="center", fontsize=7.5)
    ax[0].set_title("The first number is unbiased", fontsize=9.5, loc="left")
    x = [0, .25, .5, .75, 1.0]; y = [0.576, 0.694, 0.797, 0.881, 0.957]
    ax[1].plot(x, y, "o-", color=C["val"], lw=2, ms=5)
    ax[1].axhline(.5, ls=":", c="k", lw=.8); ax[1].set_ylim(.45, 1.0)
    ax[1].set_xlabel("position through the reasoning"); ax[1].set_ylabel("AUROC for the final side")
    ax[1].set_title("...and the answer locks in gradually", fontsize=9.5, loc="left")
    ax[1].annotate("coin flip", (0, .52), fontsize=7.5); ax[1].annotate("near-certain", (.62, .93), fontsize=7.5)
    fig.text(0, -.04, "Qwen3.5-35B-A3B, authors' rollouts, our pipeline. 444 traces, 9 questions. "
             "Bias 0 = the bet changes nothing, +1 = the bet decides the answer every time.", fontsize=6.6, va="top")
    fig.savefig(OUT / "fig2_when.png"); plt.close(fig); print("fig2")


# ---------------------------------------------------------------- Fig 3: probe
def fig_probe(csv="results/probe_controlled.csv"):
    if not Path(csv).exists(): print("skip fig3 (analysis still running)"); return
    d = pd.read_csv(csv)
    # pick the layer where the descriptive controls peak - the best case for the probe
    best = d[(d.target=="above_T")&(d.resid)].sort_values("auc").layer.iloc[-1]
    L = best; d = d[d.layer == L]
    names = {"cond": "which side\nis good\n(in the prompt)", "above_T": "is it above\nthe threshold",
             "near_T": "how close to\nthe threshold", "final_side": "the final\nanswer's side",
             "favoured": "is it on\nmy side\n(valence)", "shuffled": "shuffled\nlabels\n(null)"}
    order = ["cond", "above_T", "near_T", "final_side", "favoured", "shuffled"]
    d = d[d.target.isin(order)]
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    w, xs = .38, np.arange(len(order))
    for j, (resid, col, lab) in enumerate([(False, "#c6c6c6", "raw"),
                                           (True, C["num"], "position removed")]):
        s = d[d.resid == resid].set_index("target").reindex(order)
        ax.bar(xs + (j - .5) * w, s.auc, w, color=col, label=lab,
               yerr=[s.auc - s.lo, s.hi - s.auc], error_kw=dict(ecolor="k", capsize=2.5, lw=.9))
    ax.axhline(.5, ls=":", c="k", lw=.9)
    ax.set_xticks(xs); ax.set_xticklabels([names[o] for o in order], fontsize=7.5)
    for i,o in enumerate(order):
        for j,resid in enumerate([False,True]):
            r=d[(d.resid==resid)&(d.target==o)]
            if len(r): ax.text(i+(j-.5)*w, float(r.hi.iloc[0])+.014, f"{float(r.auc.iloc[0]):.2f}", ha="center", fontsize=6.8)
    ax.set_ylabel(f"decoding AUROC (layer {L})"); ax.set_ylim(.4, 1.0); ax.legend(frameon=False, fontsize=8)
    ax.set_title("What the model actually writes down — and what it doesn't", fontsize=9.5, loc="left")
    fig.text(0, -.075, "Qwen3.5-9B, 11,265 candidate numbers from 198 rollouts, leave-one-question-out CV; "
             "CIs resample rollouts, not rows. Position in the reasoning is trivially encoded by the residual "
             "stream, so read the blue bars.\nOnly what the prompt states or trivially implies survives the "
             "control. Anchor-proximity collapses to chance at layer 20 (0.86 -> 0.50); valence is weak but "
             "detectable; the OUTCOME is not reliably decodable.", fontsize=6.6, va="top")
    fig.savefig(OUT / "fig3_probe.png"); plt.close(fig); print("fig3")


if __name__ == "__main__":
    fig_ladder(); fig_when(); fig_probe()
