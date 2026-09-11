"""Counterfactual importance across positions, on a few traces.

Thought Anchors' shape: sweep positions within a trace and ask, at each one, how much the final
answer distribution moves when the sentence is resampled. Two departures from our earlier E2 work,
both deliberate:

  - FULL CONTINUATION, not a forced answer. Their paper says forced-answer importance cannot
    separate positions ("forced answer accuracy will be low for all sentences that occur before"),
    and comparing positions is the whole point here.
  - The outcome is near-deterministic. `naked_number` on bridge answers exactly 26,000,000 in
    20/20 rollouts, so any drop in the copy rate is a real effect rather than a shift in a noisy
    rate. E2 was chasing 0.09 against a baseline of 0.5.

Positions include the REVERSAL: every one of the 20 rollouts first resolves to ignore the numeral
and then commits to using it. That reversal is an uncertainty-management sentence, which is the
category their paper identifies as anchors.

Arms per position k:
  original   prefix through sentence k, kept intact, continued to completion
  resampled  prefix through k-1, model writes its own replacement for k, continued to completion
"""
import argparse, json, os, re, sys, time
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import numpy as np, pandas as pd, torch, yaml
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp8_load import load as fp8_load

MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"
SENT = re.compile(r"(?<=[.!?])\s+|\n+")
USE = re.compile(r"(I will use it|I'll use it|I will output 26|use the (number|provided)|"
                 r"align with it|I will write 26|decision: 26)", re.I)


def sentences(text):
    """(sentence, char_offset) pairs."""
    out, pos = [], 0
    for part in SENT.split(text):
        if part.strip():
            off = text.find(part, pos)
            out.append((part, off)); pos = off + len(part)
    return out


def first_sentence(t):
    for p in SENT.split(t.strip()):
        if p.strip():
            return p.strip()
    return t.strip()[:200]


def gen(m, tok, prompts, max_new, n_return=1, temp=1.0):
    enc = tok(prompts, return_tensors="pt", padding=True).to("cuda:0")
    with torch.no_grad():
        o = m.generate(**enc, max_new_tokens=max_new, do_sample=True, temperature=temp,
                       top_p=1.0, num_return_sequences=n_return, pad_token_id=tok.pad_token_id)
    return [tok.decode(r, skip_special_tokens=False)
            .replace("<|im_end|>", "").replace("<|endoftext|>", "")
            for r in o[:, enc["input_ids"].shape[1]:]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="1,5,6", help="1-based row numbers in naked_number.jsonl (bridge)")
    ap.add_argument("--positions", default="0.15,0.30,0.45,0.70,0.85",
                    help="fractions through the CoT; the reversal is always added")
    ap.add_argument("--n", type=int, default=15, help="resamples per position per arm")
    ap.add_argument("--batch", type=int, default=15)
    ap.add_argument("--sent-tokens", type=int, default=90)
    ap.add_argument("--max-new", type=int, default=18000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    th = {r["question"]: r["threshold"] for _, r in
          pd.read_json("results/authors_extracted.jsonl", lines=True)
            .dropna(subset=["threshold"]).drop_duplicates("question").iterrows()}
    rows = [json.loads(l) for l in open("results/naked_number.jsonl")
            if json.loads(l)["question"] == "bridge"]
    src_ids = [int(x) for x in a.sources.split(",")]
    fracs = [] if a.positions.strip().lower() in ("", "none") else [float(x) for x in a.positions.split(",")]

    tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    t0 = time.time(); m = fp8_load(MODEL)
    print(f"loaded {time.time()-t0:.0f}s | sources {src_ids} | {len(fracs)}+1 positions | n={a.n}", flush=True)

    user = tpl["naked_number"].format(question=qs["bridge"], threshold=f"{int(th['bridge']):,}")
    head = tok.apply_chat_template([{"role": "user", "content": user}],
                                   add_generation_prompt=True, tokenize=False)
    f = open(a.out, "w")
    for sid in src_ids:
        cot = rows[sid - 1]["reasoning"]
        sents = sentences(cot)
        rev = USE.search(cot)
        want = [(fr, "spread") for fr in fracs]
        if rev: want.append((rev.start() / len(cot), "REVERSAL"))
        for frac, kind in sorted(want):
            # nearest sentence boundary to that fraction
            target = frac * len(cot)
            k = min(range(len(sents)), key=lambda i: abs(sents[i][1] - target))
            sent, off = sents[k]
            pre_k   = head + cot[:off]                      # everything before sentence k
            with_k  = head + cot[:off + len(sent)]           # sentence k kept intact
            t1 = time.time(); wrote = 0

            # arm A: original kept, continue
            for s in range(0, a.n, a.batch):
                bs = min(a.batch, a.n - s)
                for txt in gen(m, tok, [with_k], a.max_new, n_return=bs):
                    cot2, ans = (txt.split("</think>", 1) if "</think>" in txt else (txt, ""))
                    f.write(json.dumps({"source": sid, "frac": round(frac,3), "kind": kind,
                                        "sent_idx": k, "arm": "original", "sentence": sent,
                                        "answer": ans.strip()[:1500],
                                        "truncated": "</think>" not in txt}) + "\n"); wrote += 1
            # arm B: model writes its own replacement, then continue
            reps = []
            for s in range(0, a.n, a.batch):
                bs = min(a.batch, a.n - s)
                reps += [first_sentence(x) for x in gen(m, tok, [pre_k], a.sent_tokens, n_return=bs)]
            # Batch the continuations. Each resample has a different prefix, so they go in as a
            # padded batch rather than one at a time. Batch 1 runs at ~5 tok/s against ~56 at
            # batch 8 on this box (METHODS.md 9), and continuations are the dominant cost here.
            for _s in range(0, len(reps), a.batch):
                chunk = reps[_s:_s + a.batch]
                outs = gen(m, tok, [pre_k + r for r in chunk], a.max_new, n_return=1)
                for rep, txt in zip(chunk, outs):
                    cot2, ans = (txt.split("</think>", 1) if "</think>" in txt else (txt, ""))
                    f.write(json.dumps({"source": sid, "frac": round(frac,3), "kind": kind,
                                        "sent_idx": k, "arm": "resampled", "sentence": rep,
                                        "answer": ans.strip()[:1500],
                                        "truncated": "</think>" not in txt}) + "\n"); wrote += 1
            f.flush()
            print(f"  [src {sid}] frac {frac:.2f} ({kind}) sent {k}: {wrote} rows "
                  f"in {time.time()-t1:.0f}s", flush=True)
    f.close()
    print(f"DONE {time.time()-t0:.0f}s -> {a.out}", flush=True)


if __name__ == "__main__":
    main()
