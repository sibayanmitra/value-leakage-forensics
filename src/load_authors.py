"""Load the authors' released Qwen3.5-35B-A3B rollouts into a tidy DataFrame.

File layout (per question dir):
  v1_<question>_accurate/{baseline,above_good,below_good}_<hash>.jsonl
Line 0 is a meta record: {"hash","model_name","prompt_key","direction",
                          "n"/"n_per_threshold","thresholds"}
Lines 1..n are rollouts: {"reasoning","answer","prompt"}

Estimates come from the LLM judge only (see src/extract.py). Judge calls are
disk-cached, so repeated loads cost nothing after the first pass.
"""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import extract_answer
from metrics import on_good_side

ROOT = Path(__file__).resolve().parent.parent / "data" / "authors_qwen35"


def load(include_eval_note=False, workers=32):
    rows = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir():
            continue
        if not include_eval_note and d.name.endswith("_eval_note_test"):
            continue
        question = re.sub(r"^v1_|_accurate.*$", "", d.name)
        for f in sorted(d.glob("*.jsonl")):
            lines = f.read_text().strip().split("\n")
            meta = json.loads(lines[0])
            T = (meta.get("thresholds") or [None])[0]
            for i, ln in enumerate(lines[1:]):
                r = json.loads(ln)
                rows.append({
                    "question": question,
                    "prompt_key": meta["prompt_key"],
                    "direction": meta["direction"],
                    "threshold": T,
                    "idx": i,
                    "reasoning": r.get("reasoning", ""),
                    "answer": r.get("answer", ""),
                    "prompt": r.get("prompt", ""),
                })
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    with ThreadPoolExecutor(max_workers=workers) as ex:
        df["est"] = list(ex.map(extract_answer, df["answer"].tolist()))

    df["on_good_side"] = [
        on_good_side(e, t, d) if (pd.notna(e) and pd.notna(t) and d != "baseline") else None
        for e, t, d in zip(df.est, df.threshold, df.direction)
    ]
    df["n_reasoning_chars"] = df["reasoning"].str.len()

    # Truncated rollouts: the model hit the token cap mid-reasoning, so the API
    # never closed the thinking block. These come back with reasoning == "" and
    # the raw chain-of-thought dumped into `answer` (~50k chars, ending
    # mid-sentence). They have no committed final answer, so extracting a number
    # from them would be reading a number out of incomplete reasoning.
    df["truncated"] = df["n_reasoning_chars"] == 0
    return df


if __name__ == "__main__":
    df = load()
    print(f"rows: {len(df)}  questions: {df.question.nunique()}  "
          f"null estimates: {df.est.isna().mean():.2%}")
    print(df.groupby(["question", "direction"]).size().unstack(fill_value=0))
