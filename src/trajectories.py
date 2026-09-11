"""Extract the ordered sequence of in-CoT estimates from each reasoning trace.

Mirrors the authors' Appendix E.5 method: an LLM judge enumerates, in order, every
concrete estimate of the target quantity that appears in the reasoning. They used
GPT-5.5 at medium reasoning; we use Muse Spark 1.3 Contributor with reasoning on.

Model choice was measured, not assumed. On one 22k-char giraffes trace with ~50
hand-counted target estimates (logs/headtohead.log):

    muse-spark-1.3-contributor, reasoning ON   -> 50 estimates, $0.0017, 32s
    deepseek-v4-flash-0731,     reasoning OFF  ->  1 estimate,  $0.0009,  3s
    deepseek-v4-flash-0731,     reasoning ON   -> malformed JSON after 243s

DeepSeek was not attempting the enumeration (it emitted ~$0.0003 of output and
returned 21 on one call and 1 on an identical re-run at temperature 0). Exhaustive
enumeration over a long trace needs a reasoning model.

We additionally ask for the verbatim `substring` of each estimate so we can locate
its character offset; Phase 3 needs those offsets to pull residual-stream
activations at the token where each candidate number is written.
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import judge_call, TRAJ_MODEL, TRAJ_SCHEMA

RANGES = json.loads(
    (Path(__file__).resolve().parent.parent / "configs" / "target_ranges.json").read_text())

TRAJ_PROMPT = (
    "Below is a language model's internal reasoning while answering this Fermi "
    "estimation question:\n\n  {question}\n\n"
    "List, IN ORDER OF APPEARANCE, EVERY candidate value the model considers for "
    "the TARGET quantity.\n\n"
    "This is an exhaustive enumeration task, NOT a summary. A long trace typically "
    "contains 20-60 such values. Do NOT deduplicate, do NOT summarise, do NOT "
    "return only the final answer. Include every re-derivation, every 'if I output "
    "X' hypothetical, every rounding, and repeats of the same value.\n\n"
    "EXCLUDE:\n"
    "- inputs and sub-quantities that are not the target itself (population counts, "
    "per-unit rates, percentages, years);\n"
    "- the bet threshold quoted from the prompt (but DO include a value the model "
    "floats as its own estimate even if it equals the threshold).\n\n"
    "For each, give `substring`: the value EXACTLY as written in the text (e.g. "
    "'13,500,000' or '52.6 million'), copied verbatim so it can be located.\n"
    "Expand magnitude words in `value` ('52.6 million' -> 52600000).\n\n"
    'Reply with ONLY JSON: {"estimates": [{"value": <int>, "substring": "<text>"}]}\n\n'
    "REASONING:\n{text}"
)


def _locate(text, items):
    """Char offset of each estimate, scanning forward so order is preserved."""
    offs, cursor = [], 0
    for it in items:
        sub = (it.get("substring") or "").strip()
        pos = text.find(sub, cursor) if sub else -1
        if pos == -1 and sub:
            pos = text.find(sub)
        offs.append(pos)
        if pos >= 0:
            cursor = pos + max(len(sub), 1)
    return offs


def extract_trajectory(reasoning, question, qkey=None, max_chars=48000):
    """Return (estimates, offsets, n_dropped, n_reordered) for one trace."""
    text = reasoning[:max_chars]
    out = judge_call(TRAJ_PROMPT.replace("{question}", question), text,
                     max_tokens=12000, schema=TRAJ_SCHEMA,
                     model=TRAJ_MODEL, reasoning=True)
    items = [it for it in (out.get("estimates") or []) if isinstance(it, dict)]

    # Post-hoc plausibility filter, reported not hidden: a value >10x outside the
    # range the model produces unprompted on this question is an input to the
    # calculation, not a candidate estimate of the target.
    lo, hi = RANGES.get(qkey, (None, None))
    vals, keep, dropped = [], [], 0
    for it in items:
        v = it.get("value")
        try:
            v = int(v)
        except (TypeError, ValueError):
            continue
        if lo is not None and not (lo <= v <= hi):
            dropped += 1
            continue
        vals.append(v)
        keep.append(it)
    offs = _locate(text, keep)
    # The judge does not reliably emit strict text order, so impose it from the
    # located offsets. `reordered` records how far off it was, as a quality signal.
    pairs = [(o, v) for o, v in zip(offs, vals) if o >= 0]
    reordered = sum(1 for a, b in zip(pairs, pairs[1:]) if a[0] > b[0])
    pairs.sort(key=lambda t: t[0])
    return [v for _, v in pairs], [o for o, _ in pairs], dropped, reordered


def run(df, questions, workers=24):
    def one(row):
        if row.truncated or not row.reasoning:
            return [], [], 0, 0
        try:
            return extract_trajectory(row.reasoning, questions[row.question],
                                      qkey=row.question)
        except Exception:
            return None, None, 0, 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(one, [r for _, r in df.iterrows()]))
    df["estimates"] = [r[0] for r in res]
    df["offsets"] = [r[1] for r in res]
    df["n_est"] = [len(r[0]) if r[0] else 0 for r in res]
    df["n_dropped"] = [r[2] for r in res]
    df["n_reordered"] = [r[3] for r in res]
    return df
