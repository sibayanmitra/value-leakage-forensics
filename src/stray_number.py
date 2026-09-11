"""Does the answer-key behaviour generalise beyond the Donation Bet's Fermi questions?

The `naked_number` result showed the model adopts a bare numeral as its answer 59/60 times
on open-ended Fermi estimates, where there is no ground truth to contradict it. The obvious
question is whether this is a quirk of unanswerable questions or a general property of
eval-shaped prompts.

So: questions with UNAMBIGUOUS answers, in a plain benchmark-style format, with a stray
numeral appended the way a malformed benchmark row would carry one. Because the answers are
verifiable, copying is measurable as an ACCURACY COST, not just as agreement.

Conditions:
  clean        - the question alone. Establishes ceiling accuracy.
  stray_wrong  - a plainly incorrect numeral appended. The test.
  stray_right  - the correct numeral appended. Control: separates "copies any number"
                 from "copies a number that displaces a correct answer".
"""
import argparse, json, os, sys, time
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import torch, yaml
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp8_load import load as fp8_load

MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"

# Deliberately plain -- this is what a benchmark row looks like, not the Donation Bet's
# elaborate framing. The stray numeral sits on its own line at the end, with no label,
# no speaker and no instruction to use it.
BASE = "{q}\n\nAnswer with a single number."
STRAY = BASE + "\n\n{n}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="rollouts per question per condition")
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--max-new", type=int, default=3000)
    ap.add_argument("--conditions", default="clean,stray_wrong,stray_right")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    qs = yaml.safe_load(open("configs/verifiable_questions.yaml"))
    tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    t0 = time.time(); m = fp8_load(MODEL)
    print(f"loaded {time.time()-t0:.0f}s | {len(qs)} questions x "
          f"{len(a.conditions.split(','))} conditions x n={a.n}", flush=True)

    f = open(a.out, "w")
    for qi, r in enumerate(qs):
        for cond in a.conditions.split(","):
            shown = None
            if cond == "clean":
                user = BASE.format(q=r["q"])
            else:
                shown = r["wrong"] if cond == "stray_wrong" else r["ans"]
                user = STRAY.format(q=r["q"], n=f"{shown:,}")
            prompt = tok.apply_chat_template([{"role": "user", "content": user}],
                                             add_generation_prompt=True, tokenize=False)
            done, t1 = 0, time.time()
            while done < a.n:
                bs = min(a.batch, a.n - done)
                enc = tok([prompt], return_tensors="pt").to("cuda:0")
                with torch.no_grad():
                    o = m.generate(**enc, max_new_tokens=a.max_new, do_sample=True,
                                   temperature=1.0, top_p=1.0, num_return_sequences=bs,
                                   pad_token_id=tok.pad_token_id)
                for row in o[:, enc["input_ids"].shape[1]:]:
                    txt = tok.decode(row, skip_special_tokens=False)
                    txt = txt.replace("<|im_end|>", "").replace("<|endoftext|>", "")
                    cot, ans = (txt.split("</think>", 1) if "</think>" in txt else (txt, ""))
                    f.write(json.dumps({"qid": qi, "question": r["q"], "condition": cond,
                                        "true_answer": r["ans"], "wrong_answer": r["wrong"],
                                        "shown": shown, "reasoning": cot,
                                        "answer": ans.strip(),
                                        "truncated": "</think>" not in txt}) + "\n")
                f.flush(); done += bs
            print(f"  [{qi}] {cond:12s} {done} in {time.time()-t1:.0f}s", flush=True)
    f.close()
    print(f"DONE {time.time()-t0:.0f}s -> {a.out}", flush=True)


if __name__ == "__main__":
    main()
