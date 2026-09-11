"""Phase 1: extract in-CoT estimate trajectories for a fixed subsample.

Budget-guarded: reports cached-vs-billable up front, enforces a hard ceiling, and
prints spend before/after. Subsample is seeded so it is reproducible and is chosen
BEFORE any extraction, never after seeing results.
"""
import argparse, json, sys, time, urllib.request
from pathlib import Path
import pandas as pd, yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_authors import load
from trajectories import run, TRAJ_PROMPT, extract_trajectory
from extract import _cache_path, TRAJ_MODEL, TRAJ_SCHEMA
from secrets_util import get_key


from budget import balance, require


def spend():
    """Money actually left. NOT auth/key's limit_remaining, which is a rate limit."""
    return balance()


def is_cached(row, questions):
    cp = _cache_path(TRAJ_PROMPT.replace("{question}", questions[row.question]),
                     row.reasoning[:48000], TRAJ_SCHEMA["name"], TRAJ_MODEL)
    return cp.exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=50,
                    help="rollouts per (question, direction)")
    ap.add_argument("--max-spend", type=float, default=0.60,
                    help="hard ceiling in USD for this run")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml"))
    df = load()
    pool = df[(~df.truncated) & (df.direction != "baseline")]
    sub = (pool.groupby(["question", "direction"], group_keys=False)
               .apply(lambda g: g.sample(min(args.per_cell, len(g)),
                                         random_state=args.seed)))
    sub = sub.reset_index(drop=True)

    cached = sub.apply(lambda r: is_cached(r, qs), axis=1)
    n_bill = int((~cached).sum())
    est_cost = n_bill * 0.0017
    print(f"subsample: {len(sub)} traces ({args.per_cell}/question/direction)", flush=True)
    print(f"  already cached (free): {int(cached.sum())}", flush=True)
    print(f"  billable             : {n_bill}  ~= ${est_cost:.2f}", flush=True)
    if est_cost > args.max_spend:
        print(f"ABORT: estimate ${est_cost:.2f} exceeds ceiling ${args.max_spend:.2f}")
        sys.exit(1)
    require(est_cost, "trajectories")

    s0 = spend(); t0 = time.time()
    sub = run(sub, qs, workers=24)
    s1 = spend()
    sub.drop(columns=["reasoning", "prompt"]).to_json(
        "results/trajectories.jsonl", orient="records", lines=True)
    print(f"DONE in {time.time()-t0:.0f}s   actual spend ${s0-s1:.2f}   balance now ${s1:.2f}", flush=True)
    print(f"  n_est  : mean={sub.n_est.mean():.1f} median={sub.n_est.median():.0f} "
          f"min={sub.n_est.min()} max={sub.n_est.max()}", flush=True)
    print(f"  zero   : {(sub.n_est==0).sum()} ({(sub.n_est==0).mean():.2%})", flush=True)
    print(f"  >=2 est: {(sub.n_est>=2).mean():.2%}  (paper's criterion)", flush=True)
    print(f"  range-filter drops: {sub.n_dropped.sum()}", flush=True)
    print(f"  traces needing reorder: {(sub.n_reordered>0).mean():.1%}", flush=True)


if __name__ == "__main__":
    main()
