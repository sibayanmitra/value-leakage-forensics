"""E2.1' - counterfactual importance of the aim sentence, by resampling.

Method follows Bogdan, Macar, Nanda & Conmy, "Thought Anchors: Which LLM Reasoning
Steps Matter?" (arXiv:2506.19143), Sec 2.3 / 3.2:

  Truncate the CoT immediately before the aim sentence and let the model resample
  what comes next. Bucket continuations by whether the model's replacement sentence
  is SEMANTICALLY DIFFERENT from the original (cosine < 0.8 on all-MiniLM-L6-v2,
  their threshold), then compare the distribution of final answers across buckets.

Why this rather than deleting the sentence: resampling keeps the prefix
on-distribution, and the "model re-said something similar" bucket is a built-in
control, so no separate truncation/deletion controls are needed.

The aim sentence is the candidate thought anchor for the bias - it is where the
model relates its own candidate answer to which side of the threshold it falls on.
"""
import argparse, json, os, re, sys, time
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")   # GPU 1 belongs to another user
import torch
from transformers.quantizers import quantizer_finegrained_fp8 as qfp8

_orig_tp = qfp8.FineGrainedFP8HfQuantizer.update_tp_plan
def _safe_tp(self, config):
    try:
        return _orig_tp(self, config)
    except AttributeError:      # transformers 5.16.1 bug on this MoE config
        return config
qfp8.FineGrainedFP8HfQuantizer.update_tp_plan = _safe_tp

import pandas as pd, yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"
SIM_THRESHOLD = 0.8          # Thought Anchors' value
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def first_sentence(text):
    for p in SENT_SPLIT.split(text.strip()):
        if p and p.strip():
            return p.strip()
    return ""


def build_prefix(tok, question_text, prompt_template, threshold, reasoning, aim_off):
    user = prompt_template.format(question=question_text,
                                  threshold=f"{int(threshold):,}")
    head = tok.apply_chat_template([{"role": "user", "content": user}],
                                   add_generation_prompt=True, tokenize=False)
    return head + reasoning[:int(aim_off)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sources", type=int, default=16)
    ap.add_argument("--n-resamples", type=int, default=16)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-new", type=int, default=2200)
    ap.add_argument("--out", default="results/resamples.jsonl")
    args = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    src = pd.read_json("results/aim_sentences.jsonl", lines=True)
    src = src[src.aim_idx.notna()].head(args.n_sources).reset_index(drop=True)

    from load_authors import load
    full = load()[["question", "direction", "idx", "reasoning"]]
    src = src.merge(full, on=["question", "direction", "idx"], how="left")
    print(f"{len(src)} sources x {args.n_resamples} resamples", flush=True)

    tok = AutoTokenizer.from_pretrained(MODEL)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype="auto",
                                                 device_map="cuda:0")
    model.eval()
    print(f"model loaded in {time.time()-t0:.0f}s", flush=True)

    out_f = open(args.out, "w")
    for si, r in src.iterrows():
        prefix = build_prefix(tok, qs[r.question], tpl[r.direction],
                              r.threshold, r.reasoning, r.aim_off)
        done = 0
        t1 = time.time()
        while done < args.n_resamples:
            bs = min(args.batch, args.n_resamples - done)
            enc = tok([prefix] * bs, return_tensors="pt").to("cuda:0")
            with torch.no_grad():
                gen = model.generate(**enc, max_new_tokens=args.max_new,
                                     do_sample=True, temperature=1.0, top_p=1.0,
                                     pad_token_id=tok.pad_token_id)
            new = gen[:, enc.input_ids.shape[1]:]
            for row in new:
                txt = tok.decode(row, skip_special_tokens=False)
                txt = txt.replace("<|im_end|>", "").replace("<|endoftext|>", "")
                if "</think>" in txt:
                    cot, ans = txt.split("</think>", 1)
                else:
                    cot, ans = txt, ""
                out_f.write(json.dumps({
                    "source": int(si), "question": r.question,
                    "direction": r.direction, "threshold": float(r.threshold),
                    "orig_aim": r.aim_sent,
                    "resampled_sent": first_sentence(cot),
                    "continuation_cot": cot[:6000],
                    "answer": ans.strip()[:2500],
                    "completed": "</think>" in txt,
                }) + "\n")
            out_f.flush()
            done += bs
        print(f"  [{si+1}/{len(src)}] {r.question}/{r.direction} "
              f"{done} resamples in {time.time()-t1:.0f}s", flush=True)
    out_f.close()
    print(f"wrote {args.out} in {time.time()-t0:.0f}s total", flush=True)


if __name__ == "__main__":
    main()
