"""Teacher-forced check of the step-2 prefixes (src/resample_sentences.py).

The greedy check there regenerates from a mid-reply cut and compares with the saved reply. It
reproduced the first 7-10 tokens and then diverged at a word where two continuations are plausible.
The saved replies were generated one token at a time inside a left-padded batch; the step-2 inputs
feed the same token ids in one prefill pass, alone. Different kernels (chunked prefill vs recurrent
decode in the gated-delta layers) on an FP8 model can flip a near-tie, after which greedy paths part.

This check separates that from a wrong input. For every cut, it feeds prompt ids + the saved reply's
ids through the cut and the next --k saved tokens, and reports for each of those tokens whether it is
the model's top choice, its probability, and the top choice's probability. With the right input the
saved tokens should be the top choice almost everywhere, and at the greedy divergence the two
candidates should be close. As a contrast, the same is computed with the saved tokens shifted by one
position (each compared with the prediction for the token before it), which a correct input should
fail badly.

usage: VLF_GPU=1 python src/check_prefix_likelihood.py [--k 32]
"""
import argparse, json, os, sys
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch, yaml
from transformers import AutoTokenizer
from disclose_cot import build, MODEL


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--k", type=int, default=32); a = ap.parse_args()
    qs = yaml.safe_load(open("configs/questions.yaml")); tpl = yaml.safe_load(open("configs/prompts.yaml"))
    src = {i + 1: json.loads(l) for i, l in enumerate(open("results/naked_number.jsonl"))}
    own = {json.loads(l)["source_line"]: json.loads(l) for l in open("results/disclose_cot_own.jsonl")}
    cuts = sorted({(r["source_line"], r["cut_tok"]) for r in map(json.loads, open("results/resample_sentences.jsonl"))})
    tok = AutoTokenizer.from_pretrained(MODEL)
    from fp8_load import load as fp8_load
    m = fp8_load(MODEL)
    tot = agree = shift_agree = 0
    for ro, j in cuts:
        r = src[ro]; shown = f"{int(r['threshold']):,}"
        prompt = build(tok, "own", tpl["naked_number"].format(question=qs[r["question"]], threshold=shown),
                       r["reasoning"], r["answer"].strip(), shown)
        pids = tok(prompt).input_ids; rids = tok(own[ro]["full"], add_special_tokens=False).input_ids
        ids = torch.tensor([pids + rids[:j + a.k]], device="cuda:0")
        with torch.no_grad():                                      # logits only for the last k+1 positions (full vocab x 9k tokens does not fit)
            logp = torch.log_softmax(m(input_ids=ids, logits_to_keep=a.k + 1).logits[0].float(), -1)
        base = 0                                                   # index 0 = the position predicting reply token j
        rows, first_div = [], None
        for t in range(a.k):
            lp = logp[base + t]; saved = rids[j + t]; top = int(lp.argmax())
            ok = top == saved; agree += ok; tot += 1
            shift_agree += int(logp[base + t].argmax()) == rids[j + t - 1]
            if not ok and first_div is None:
                first_div = (t, tok.decode([saved]), float(lp[saved].exp()), tok.decode([top]), float(lp[top].exp()))
            rows.append(ok)
        print(f"rollout {ro:2d} cut tok {j:4d}: saved token is the top choice {sum(rows):2d}/{a.k}"
              + (f"; first miss at +{first_div[0]}: saved {first_div[1]!r} p={first_div[2]:.3f} vs top {first_div[3]!r} p={first_div[4]:.3f}" if first_div else ""),
              flush=True)
    print(f"\nALL CUTS: saved token = top choice in {agree}/{tot} ({agree / tot:.3f}); shifted-by-one contrast {shift_agree}/{tot} ({shift_agree / tot:.3f})")


if __name__ == "__main__":
    main()
