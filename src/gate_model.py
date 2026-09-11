"""Phase 3 gate: does a candidate model show the Donation Bet bias at all?

The probe has nothing to find if the effect is absent. Runs above_good/below_good
on a few questions and reports the bias with a CI, using the same metric as E0.
"""
import argparse, json, os, sys, time
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU","0"))
import torch
import pandas as pd, yaml
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp8_load import load as fp8_load   # applies both FP8 workarounds

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--max-new", type=int, default=12000)
    ap.add_argument("--questions", default="giraffes,bridge,tbc,orangecars")
    ap.add_argument("--out", required=True)
    a=ap.parse_args()
    qs=yaml.safe_load(open("configs/questions.yaml")); tpl=yaml.safe_load(open("configs/prompts.yaml"))
    th={r["question"]:r["threshold"] for _,r in
        pd.read_json("results/authors_extracted.jsonl",lines=True)
          .dropna(subset=["threshold"]).drop_duplicates("question").iterrows()}
    tok=AutoTokenizer.from_pretrained(a.model); tok.padding_side="left"
    if tok.pad_token is None: tok.pad_token=tok.eos_token
    t0=time.time()
    m=fp8_load(a.model)
    print(f"{a.model} loaded {time.time()-t0:.0f}s", flush=True)
    f=open(a.out,"w")
    for q in a.questions.split(","):
        for d in ["above_good","below_good"]:
            user=tpl[d].format(question=qs[q], threshold=f"{int(th[q]):,}")
            p=tok.apply_chat_template([{"role":"user","content":user}],add_generation_prompt=True,tokenize=False)
            done=0; t1=time.time()
            while done<a.n:
                bs=min(a.batch,a.n-done)
                enc=tok([p],return_tensors="pt").to("cuda:0")
                with torch.no_grad():
                    o=m.generate(**enc,max_new_tokens=a.max_new,do_sample=True,temperature=1.0,
                                 top_p=1.0,num_return_sequences=bs,pad_token_id=tok.pad_token_id)
                for row in o[:,enc.input_ids.shape[1]:]:
                    txt=tok.decode(row,skip_special_tokens=False).replace("<|im_end|>","")
                    cot,ans=(txt.split("</think>",1) if "</think>" in txt else (txt,""))
                    f.write(json.dumps({"model":a.model,"question":q,"direction":d,
                        "threshold":float(th[q]),"reasoning":cot,"answer":ans.strip(),
                        "truncated":"</think>" not in txt})+"\n")
                f.flush(); done+=bs
            print(f"  {q}/{d}: {done} in {time.time()-t1:.0f}s", flush=True)
    f.close(); print(f"DONE {time.time()-t0:.0f}s -> {a.out}", flush=True)

if __name__=="__main__": main()
