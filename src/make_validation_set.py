"""Build the 30-trace hand-validation set for trajectory extraction.

The E1 finding rests on FIRST and LAST in-CoT estimate identification, so those are
what gets checked rigorously: for each trace we print the located character offset,
the verbatim text around it, and what the judge claimed. Stratified to oversample
the traces the finding depends on most (first estimate on the bad side).
"""
import json, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_authors import load
from metrics import on_good_side

OUT = Path("samples")


def main():
    traj = pd.read_json("results/trajectories.jsonl", lines=True)
    traj = traj[traj.n_est >= 1].copy()
    full = load()[["question", "direction", "idx", "reasoning"]]
    df = traj.merge(full, on=["question", "direction", "idx"], how="left")

    df["first_est"] = df.estimates.map(lambda e: e[0])
    df["last_est"] = df.estimates.map(lambda e: e[-1])
    df["first_good"] = [on_good_side(v, t, d) for v, t, d in
                        zip(df.first_est, df.threshold, df.direction)]
    df["final_good"] = [on_good_side(v, t, d) for v, t, d in
                        zip(df.est, df.threshold, df.direction)]
    df["flipped"] = (~df.first_good.astype(bool)) & (df.final_good.astype(bool))

    # Stratify: 15 flipped (bad->good, the pattern H-backtrack predicts),
    # 10 non-flipped, 5 random. One per question where possible.
    flip = df[df.flipped].groupby("question", group_keys=False).apply(
        lambda g: g.sample(min(2, len(g)), random_state=1)).head(15)
    noflip = df[~df.flipped].groupby("question", group_keys=False).apply(
        lambda g: g.sample(min(2, len(g)), random_state=1)).head(10)
    rest = df.drop(index=flip.index.union(noflip.index)).sample(5, random_state=1)
    samp = pd.concat([flip, noflip, rest]).head(30).reset_index(drop=True)

    OUT.mkdir(exist_ok=True)
    lines = []
    for i, r in samp.iterrows():
        txt = r.reasoning[:48000]
        def ctx(off, width=95):
            if off is None or off < 0:
                return "<<UNLOCATED>>"
            return ("..." + txt[max(0, off - width):off + 28].replace("\n", " ") + "...")
        lines.append({
            "i": int(i), "question": r.question, "direction": r.direction,
            "threshold": r.threshold, "n_est": int(r.n_est),
            "first_est": int(r.first_est), "first_offset": int(r.offsets[0]),
            "first_ctx": ctx(r.offsets[0]),
            "last_est": int(r.last_est), "last_offset": int(r.offsets[-1]),
            "last_ctx": ctx(r.offsets[-1]),
            "final_answer": None if pd.isna(r.est) else int(r.est),
            "first_good": bool(r.first_good), "final_good": bool(r.final_good),
            "flipped": bool(r.flipped),
            "estimates": [int(x) for x in r.estimates],
        })
    (OUT / "trajectory_validation_30.json").write_text(json.dumps(lines, indent=1))
    samp[["question", "direction", "idx"]].to_json(
        OUT / "trajectory_validation_30_ids.jsonl", orient="records", lines=True)
    print(f"wrote {len(lines)} traces to samples/trajectory_validation_30.json")
    print(f"  flipped (bad->good): {samp.flipped.sum()}")


if __name__ == "__main__":
    main()
