"""Generate the neutral_T anchoring control.

THE control this project was missing. E1 shows estimates start unbiased and drift to the
favoured side of T during reasoning. The obvious objection is that T is simply a number sitting
in the prompt and estimates drift toward it regardless of valence - i.e. anchoring, not values.

neutral_T is identical to the intervention prompts except the good/bad framing is removed: the
threshold is present, nothing depends on which side the estimate lands. Running the identical
trajectory analysis on it separates anchoring from valence. The paper has no such condition;
this is ours.

Prediction if E1's reading is right: first-estimate bias ~0 AND final-answer bias ~0 under
arbitrary side-labels, because there is no favoured side to drift toward.
"""
import argparse, json, os, sys, time
from pathlib import Path

os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import torch
from transformers.quantizers import quantizer_finegrained_fp8 as qfp8
_o = qfp8.FineGrainedFP8HfQuantizer.update_tp_plan
def _s(self, c):
    try:
        return _o(self, c)
    except AttributeError:
        return c
qfp8.FineGrainedFP8HfQuantizer.update_tp_plan = _s

import pandas as pd, yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30, help="rollouts per question")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--max-new", type=int, default=9000)
    ap.add_argument("--questions", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--condition", default="neutral_T")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--scale", type=float, default=1.0,
                    help="multiply T by this before showing it. Tests whether the model latches "
                         "onto ANY number or only a plausible one. Scoring keeps the true T too.")
    ap.add_argument("--numerals", default="",
                    help="explicit numeral per question, e.g. bridge=26143882,tbc=1106. Overrides "
                         "--scale for those questions. Used for the precise-numeral arm of "
                         "DESIGN_unfaithful_presentation.md: same magnitude as T, no round digits.")
    args = ap.parse_args()
    override = {k: float(v) for k, v in (kv.split("=") for kv in args.numerals.split(",") if kv)}

    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    # thresholds: the authors' T for each question, so neutral_T is directly
    # comparable to above_good/below_good on the same scale
    th = {r["question"]: r["threshold"] for _, r in
          pd.read_json("results/authors_extracted.jsonl", lines=True)
            .dropna(subset=["threshold"]).drop_duplicates("question").iterrows()}
    names = [q for q in (args.questions.split(",") if args.questions else sorted(qs))]

    tok = AutoTokenizer.from_pretrained(args.model)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype="auto", device_map="cuda:0")
    model.eval()
    print(f"loaded {time.time()-t0:.0f}s | questions: {names} | n={args.n}", flush=True)

    out_f = open(args.out, "w")
    for q in names:
        shown = override[q] if q in override else th.get(q, 0.0) * args.scale   # the number the model actually sees (0 when the condition shows none)
        user = tpl[args.condition].format(question=qs[q], threshold=f"{int(shown):,}")
        prompt = tok.apply_chat_template([{"role": "user", "content": user}],
                                         add_generation_prompt=True, tokenize=False)
        done, t1 = 0, time.time()
        while done < args.n:
            bs = min(args.batch, args.n - done)
            enc = tok([prompt], return_tensors="pt").to("cuda:0")
            with torch.no_grad():
                o = model.generate(**enc, max_new_tokens=args.max_new, do_sample=True,
                                   temperature=1.0, top_p=1.0,
                                   num_return_sequences=bs, pad_token_id=tok.pad_token_id)
            for row in o[:, enc.input_ids.shape[1]:]:
                txt = tok.decode(row, skip_special_tokens=False)
                txt = txt.replace("<|im_end|>", "").replace("<|endoftext|>", "")
                cot, ans = (txt.split("</think>", 1) if "</think>" in txt else (txt, ""))
                out_f.write(json.dumps({
                    "question": q, "direction": args.condition,
                    "threshold": float(shown), "threshold_true": float(th.get(q, shown)),
                    "scale": args.scale, "reasoning": cot,
                    "answer": ans.strip(), "truncated": "</think>" not in txt}) + "\n")
            out_f.flush()
            done += bs
        print(f"  {q}: {done} rollouts in {time.time()-t1:.0f}s", flush=True)
    out_f.close()
    print(f"DONE {time.time()-t0:.0f}s -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
