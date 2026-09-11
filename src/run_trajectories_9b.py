"""Phase 3 input: enumerate in-CoT estimates for the local Qwen3.5-9B rollouts.

Differs from run_trajectories.py in two ways.

1. Reads a local generation file instead of the authors' released rollouts.

2. **Does not skip truncated traces.** run_trajectories.py drops them because the
   Phase-1 analysis compares first-vs-final estimate, and a truncated trace has no
   final. The probe has no such dependence: it labels each in-CoT estimate token by
       favoured = (est > T) == (direction == above_good)
   and both T and direction come from the prompt, so the label is well defined no
   matter where the trace stops. 93/200 of the 9B gate rollouts hit the 12000-token
   cap; discarding them would throw away 47% of the data for no gain, and would
   itself bias the sample toward short traces.
"""
import argparse, json, sys, time
from pathlib import Path
import pandas as pd, yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trajectories import extract_trajectory, TRAJ_PROMPT
from extract import _cache_path, TRAJ_MODEL, TRAJ_SCHEMA
from budget import balance, require
from concurrent.futures import ThreadPoolExecutor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-spend", type=float, default=0.60)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml"))
    df = pd.read_json(a.rollouts, lines=True)
    df = df[df.reasoning.astype(bool)].reset_index(drop=True)

    cached = df.apply(lambda r: _cache_path(
        TRAJ_PROMPT.replace("{question}", qs[r.question]),
        r.reasoning[:48000], TRAJ_SCHEMA["name"], TRAJ_MODEL).exists(), axis=1)
    n_bill = int((~cached).sum())
    est = n_bill * 0.0017
    print(f"traces: {len(df)}   cached(free): {int(cached.sum())}   billable: {n_bill} ~= ${est:.2f}", flush=True)
    if est > a.max_spend:
        sys.exit(f"ABORT: ${est:.2f} > ceiling ${a.max_spend:.2f}")
    require(est, "trajectories_9b")

    s0, t0 = balance(), time.time()

    def one(row):
        try:
            return extract_trajectory(row.reasoning, qs[row.question], qkey=row.question)
        except Exception as e:
            print(f"  FAIL {row.question}/{row.direction}: {type(e).__name__}", flush=True)
            return None, None, 0, 0

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(one, [r for _, r in df.iterrows()]))

    df["estimates"] = [r[0] for r in res]
    df["offsets"]   = [r[1] for r in res]
    df["n_est"]     = [len(r[0]) if r[0] else 0 for r in res]
    df["n_dropped"] = [r[2] for r in res]
    df["n_reordered"]= [r[3] for r in res]
    df.to_json(a.out, orient="records", lines=True)

    ok = df.n_est > 0
    print(f"\ndone in {time.time()-t0:.0f}s  spent ${s0-balance():.3f}", flush=True)
    print(f"  traces with >=1 estimate: {int(ok.sum())}/{len(df)}", flush=True)
    print(f"  total estimate tokens   : {int(df.n_est.sum())}", flush=True)
    print(f"  median per trace        : {df.n_est[ok].median():.0f}", flush=True)
    print(f"  located (offset found)  : {sum(sum(1 for o in (r or []) if o is not None and o>=0) for r in df.offsets)}", flush=True)
    print(f"  dropped / reordered     : {int(df.n_dropped.sum())} / {int(df.n_reordered.sum())}", flush=True)

if __name__ == "__main__":
    main()
