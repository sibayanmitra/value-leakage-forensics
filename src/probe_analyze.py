"""Re-analysis of the saved probe activations with the controls the first run lacked.

Fixes four problems found by auditing the first run:

1. POSITION CONFOUND. `favoured` is predictable from position in the CoT alone at
   AUC 0.546 (favoured rate climbs 0.517 -> 0.619 across CoT quartiles), and the
   residual stream trivially encodes position. The first run's favoured AUC of 0.568
   is barely above what position alone buys. Every target is therefore reported three
   ways: activations, position alone, and activations after residualising position out.

2. WRONG TARGET FOR THE ASK. Neel asked for a direction predicting the biased
   OUTCOME. `favoured` is a property of the current candidate, not of the outcome.
   `final_side` is added: from the activation at an in-CoT estimate, does the FINAL
   answer land on the favoured side? That is the thing a steering intervention would
   have to move.

3. NO ANCHOR TARGET. E1e says the effect is largely anchoring on T. `near_T` tests
   whether the model linearly represents proximity to the anchor, which is the
   variable the behavioural result points at.

4. ROW-LEVEL CIs. 47% of rows repeat a value already in the same rollout and there
   are only 198 rollouts. CIs bootstrap over ROLLOUTS, not rows.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
sys.path.insert(0, str(Path(__file__).resolve().parent))

LAYERS = list(range(0, 32, 4)) + [29, 30, 31]


def add_targets(meta, rollouts_path):
    meta = meta.copy()
    meta["above_T"]  = (meta.est > meta.threshold).astype(int)
    meta["cond"]     = (meta.direction == "above_good").astype(int)
    meta["favoured"] = (meta.above_T == meta.cond).astype(int)
    # anchoring target: is this candidate within 10% (in log space) of the anchor?
    meta["near_T"]   = (np.abs(np.log10(meta.est.clip(lower=1) / meta.threshold)) < 0.0414).astype(int)
    # outcome target: which side did the FINAL answer land on?
    src = pd.read_json(rollouts_path, lines=True)
    from extract import extract_answer
    fin = {}
    for i, r in src.iterrows():
        if r.get("truncated") or not str(r.get("answer", "")).strip():
            continue
        v = extract_answer(r["answer"])
        if v is None:
            continue
        fin[i] = int((v > r["threshold"]) == (r["direction"] == "above_good"))
    meta["final_side"] = meta.rollout.map(fin)
    return meta


def resid_out_position(X, frac):
    """Remove the component of every activation dim that is linear in CoT position."""
    F = np.c_[frac, frac ** 2]
    return X - LinearRegression().fit(F, X).predict(F)


def evaluate(meta, X, target, rng, resid=False, n_boot=2000):
    """Leave-one-question-out CV. Returns per-question AUC and a rollout-bootstrap CI."""
    ok = meta[target].notna().values
    m, Xl = meta[ok], X[ok]
    y = m[target].values.astype(int)
    if len(np.unique(y)) < 2:
        return None
    if resid:
        Xl = resid_out_position(Xl, m.frac.values)
    per, pooled_scores, pooled_y, pooled_roll = {}, [], [], []
    for q in m.question.unique():
        tr, te = (m.question != q).values, (m.question == q).values
        if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
            continue
        sc = StandardScaler().fit(Xl[tr])
        clf = LogisticRegression(max_iter=2000, C=0.1).fit(sc.transform(Xl[tr]), y[tr])
        s = clf.predict_proba(sc.transform(Xl[te]))[:, 1]
        per[q] = roc_auc_score(y[te], s)
        pooled_scores.append(s); pooled_y.append(y[te]); pooled_roll.append(m.rollout.values[te])
    if not per:
        return None
    # CI must bootstrap the SAME estimand as the point estimate: the mean of the
    # per-question AUCs. Pooling the folds and bootstrapping that gives a different
    # quantity, and the two disagreed badly (final_side: 0.584 with a "CI" of
    # [0.394, 0.562], which does not contain its own point estimate). Resample
    # ROLLOUTS within each question, recompute that question's AUC, then average.
    perq = []
    for sc_, yy_, rr_ in zip(pooled_scores, pooled_y, pooled_roll):
        u = np.unique(rr_)
        perq.append((sc_, yy_, rr_, u, {v: np.where(rr_ == v)[0] for v in u}))
    bs = []
    for _ in range(n_boot):
        vals = []
        for sc_, yy_, rr_, u, idx in perq:
            sel = np.concatenate([idx[v] for v in rng.choice(u, len(u))])
            if len(np.unique(yy_[sel])) < 2:
                continue
            vals.append(roc_auc_score(yy_[sel], sc_[sel]))
        if vals:
            bs.append(np.mean(vals))
    bs = np.array(bs)
    yy = np.concatenate(pooled_y); uniq = np.unique(np.concatenate(pooled_roll))
    return dict(target=target, resid=resid, auc=float(np.mean(list(per.values()))),
                lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)),
                n_rows=int(len(yy)), n_rollouts=int(len(uniq)),
                per_q={k: round(v, 3) for k, v in per.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default="results/probe_full_meta.jsonl")
    ap.add_argument("--acts", default="results/probe_full_X.npy")
    ap.add_argument("--rollouts", default="results/traj9b.jsonl")
    ap.add_argument("--layers", default="12,16,20")
    ap.add_argument("--out", default="results/probe_controlled.csv")
    a = ap.parse_args()

    meta = add_targets(pd.read_json(a.meta, lines=True), a.rollouts)
    X = np.load(a.acts, mmap_mode="r")
    rng = np.random.default_rng(0)
    meta["shuffled"] = rng.permutation(meta.favoured.values)

    print(f"rows {len(meta)}  rollouts {meta.rollout.nunique()}  questions {meta.question.nunique()}")
    print("target base rates / coverage:")
    for t in ["favoured", "above_T", "cond", "near_T", "final_side"]:
        v = meta[t]
        print(f"  {t:11s} base={v.mean():.3f}  labelled rows={int(v.notna().sum())} "
              f"rollouts={meta.loc[v.notna(),'rollout'].nunique()}")

    print("\nposition-only baselines (no activations):")
    for t in ["favoured", "above_T", "near_T", "final_side"]:
        ok = meta[t].notna()
        print(f"  AUC({t} | CoT position) = {roc_auc_score(meta[t][ok], meta.frac[ok]):.3f}")

    res = []
    for L in [int(x) for x in a.layers.split(",")]:
        Xl = np.asarray(X[:, LAYERS.index(L), :])
        for t in ["favoured", "above_T", "cond", "near_T", "final_side", "shuffled"]:
            for resid in (False, True):
                r = evaluate(meta, Xl, t, rng, resid=resid)
                if r:
                    r["layer"] = L; res.append(r)
                    tag = "resid-pos" if resid else "raw      "
                    print(f"  L{L:<2} {t:11s} {tag} AUC={r['auc']:.3f} [{r['lo']:.3f},{r['hi']:.3f}] "
                          f"rows={r['n_rows']} rollouts={r['n_rollouts']}", flush=True)
    pd.DataFrame(res).to_csv(a.out, index=False)
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
