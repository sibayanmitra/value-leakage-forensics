"""E2.1 - counterfactual importance of the aim sentence (forced-answer variant).

Method: Bogdan, Macar, Nanda & Conmy, "Thought Anchors: Which LLM Reasoning Steps
Matter?" (arXiv:2506.19143), Sec 2.2 (forced answer) + 3.2 (semantic filtering).

Three arms per source, all sharing the same prefix (the CoT truncated immediately
before the aim sentence):

  ORIGINAL  prefix + the original aim sentence  -> force answer
            The "with S_i" condition. Sampling noise only.
  RESAMPLED prefix -> model writes its own next sentence -> force answer
            The "without S_i" condition. Bucketed post hoc by whether the
            replacement is semantically different from the original
            (cosine < 0.8 on all-MiniLM-L6-v2, the paper's threshold).
  NOSENT    prefix + nothing -> force answer immediately
            Floor: what the model answers with no sentence at that position at all.

"Force answer" means appending the end-of-thinking token and letting the model emit
its answer directly, instead of generating the ~6,760 further reasoning tokens a
natural continuation needs. That is a ~45x saving and is what makes n=40 affordable.
Its known limitation (paper Sec 2.3) is that a sentence necessary for some answer
may be reliably produced later anyway, which makes earlier steps look unimportant -
so src/resample_full.py runs the full-continuation version on a subset as a check.
"""
import argparse, json, os, re, sys, time
from pathlib import Path

# GPU chosen by caller. The box is shared: GPU 1 carries another user's process,
# so only 0/2/3 are ours. Two independent processes (one per GPU, sources split)
# rather than tensor parallel - these cards have no NVLink, so sharding would put
# an all-reduce on PCIe every layer.
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import torch
from transformers.quantizers import quantizer_finegrained_fp8 as qfp8

_orig_tp = qfp8.FineGrainedFP8HfQuantizer.update_tp_plan
def _safe_tp(self, config):
    try:
        return _orig_tp(self, config)
    except AttributeError:          # transformers 5.16.1 bug on this MoE config
        return config
qfp8.FineGrainedFP8HfQuantizer.update_tp_plan = _safe_tp

import pandas as pd, yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"
END_THINK = "\n</think>\n\n"
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def first_sentence(text):
    for p in SENT_SPLIT.split(text.strip()):
        if p and p.strip():
            return p.strip()
    return ""


def gen(model, tok, prompts, max_new, temperature, n_return=1):
    """Generate continuations.

    When every prompt is identical, pass a single prompt with n_return>1: the
    prefix is then encoded once and expanded, instead of being re-prefilled per
    batch element. Prefixes here are 1.2k-6.9k tokens, so that prefill dominates.
    """
    enc = tok(prompts, return_tensors="pt", padding=True).to("cuda:0")
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new,
            do_sample=temperature > 0, temperature=temperature or None,
            top_p=1.0 if temperature > 0 else None,
            num_return_sequences=n_return,
            pad_token_id=tok.pad_token_id)
    new = out[:, enc.input_ids.shape[1]:]
    return [tok.decode(r, skip_special_tokens=True) for r in new]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-resamples", type=int, default=40)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--sent-tokens", type=int, default=90)
    ap.add_argument("--ans-tokens", type=int, default=160)
    ap.add_argument("--out", default="results/resamples_forced.jsonl")
    ap.add_argument("--src-start", type=int, default=0)
    ap.add_argument("--src-end", type=int, default=999)
    args = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    src = pd.read_json(os.environ.get("VLF_SOURCES", "results/aim_sentences.jsonl"), lines=True)
    src = src[src.aim_idx.notna()].reset_index(drop=True)
    src = src.iloc[args.src_start:args.src_end].copy()
    src["_sid"] = range(args.src_start, args.src_start + len(src))
    src = src.reset_index(drop=True)
    from load_authors import load
    full = load()[["question", "direction", "idx", "reasoning"]]
    src = src.merge(full, on=["question", "direction", "idx"], how="left")

    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype="auto",
                                                 device_map="cuda:0")
    model.eval()
    print(f"model loaded {time.time()-t0:.0f}s | {len(src)} sources "
          f"x {args.n_resamples} resamples x 3 arms", flush=True)

    out_f = open(args.out, "w")
    for si, r in src.iterrows():
        user = tpl[r.direction].format(question=qs[r.question],
                                       threshold=f"{int(r.threshold):,}")
        head = tok.apply_chat_template([{"role": "user", "content": user}],
                                       add_generation_prompt=True, tokenize=False)
        prefix = head + r.reasoning[:int(r.aim_off)]
        t1 = time.time()

        # --- RESAMPLED: model writes its own replacement sentence
        sents = []
        for s in range(0, args.n_resamples, args.batch):
            bs = min(args.batch, args.n_resamples - s)
            sents += [first_sentence(x) for x in
                      gen(model, tok, [prefix], args.sent_tokens, 1.0, n_return=bs)]

        # --- force an answer for every arm
        rows = []
        arms = ([("resampled", prefix + s + END_THINK, s) for s in sents]
                + [("original", prefix + r.aim_sent + END_THINK, r.aim_sent)]
                  * args.n_resamples
                + [("nosent", prefix + END_THINK, "")] * args.n_resamples)
        arms.sort(key=lambda c: len(c[1]))          # minimise padding waste
        for s in range(0, len(arms), args.batch):
            chunk = arms[s:s + args.batch]
            answers = gen(model, tok, [c[1] for c in chunk], args.ans_tokens, 1.0)
            for (arm, _, sent), ans in zip(chunk, answers):
                rows.append({"source": int(r._sid), "question": r.question,
                             "direction": r.direction,
                             "threshold": float(r.threshold),
                             "arm": arm, "orig_aim": r.aim_sent,
                             "sentence": sent, "answer": ans.strip()[:1200]})
        for row in rows:
            out_f.write(json.dumps(row) + "\n")
        out_f.flush()
        print(f"  [{r._sid}] {r.question}/{r.direction} "
              f"{len(rows)} rows in {time.time()-t1:.0f}s", flush=True)
    out_f.close()
    print(f"DONE {time.time()-t0:.0f}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
