"""E4: is the probe direction CAUSALLY mediating, or only predictive?

Neel's ask was "a linear direction predicting it AND causally mediating it". probe.py
answers the predicting half. This answers the causal half by adding the direction back
into the residual stream during generation and measuring whether the answer moves.

Directions steered (all read off the fitted probes, unit-normalised):
  favoured  - the direction of interest: "this number is on the side I want"
  above_T   - POSITIVE CONTROL. This one is strongly decodable (AUROC ~0.78), so if
              steering works at all in this model at this layer, it must move estimates.
              Without it, a null on `favoured` is uninterpretable: it could just mean
              our steering is too weak to do anything.
  random    - NEGATIVE CONTROL. Gaussian direction, same norm, same layer.

Scale is expressed in units of the layer's own mean residual norm, so alpha is
comparable across layers and models.
"""
import argparse, json, os, sys, time
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import numpy as np, pandas as pd, torch, yaml
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp8_load import load as fp8_load

MODEL_DEFAULT = "Qwen/Qwen3.5-9B"


def fit_directions(meta_path, X_path, layer, layers):
    """Refit the probes on ALL data (no CV) purely to read off a direction."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    X = np.load(X_path); meta = pd.read_json(meta_path, lines=True)
    li = layers.index(layer); Xl = X[:, li, :]
    meta["above_T"] = (meta.est > meta.threshold).astype(int)
    meta["cond"] = (meta.direction == "above_good").astype(int)
    meta["favoured"] = (meta.above_T == meta.cond).astype(int)
    sc = StandardScaler().fit(Xl)
    out = {}
    for t in ["favoured", "above_T"]:
        clf = LogisticRegression(max_iter=3000, C=0.1).fit(sc.transform(Xl), meta[t].values)
        # undo the scaler so the direction lives in raw residual space
        w = clf.coef_[0] / sc.scale_
        out[t] = w / np.linalg.norm(w)
    rng = np.random.default_rng(0)
    r = rng.standard_normal(Xl.shape[1]); out["random"] = r / np.linalg.norm(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--meta", default="results/probe_full_meta.jsonl")
    ap.add_argument("--acts", default="results/probe_full_X.npy")
    ap.add_argument("--layer", type=int, required=True)
    ap.add_argument("--questions", default="bridge,giraffes,tbc")
    ap.add_argument("--conditions", default="above_good,below_good")
    ap.add_argument("--alphas", default="-8,-4,0,4,8")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--batch", type=int, default=5)
    ap.add_argument("--max-new", type=int, default=20000)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    layers = list(range(0, 32, 4)) + [29, 30, 31]
    dirs = fit_directions(a.meta, a.acts, a.layer, layers)
    print(f"directions at layer {a.layer}: {list(dirs)}", flush=True)
    print(f"cos(favoured, above_T) = {float(dirs['favoured'] @ dirs['above_T']):+.3f}", flush=True)

    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    th = {r["question"]: r["threshold"] for _, r in
          pd.read_json("results/authors_extracted.jsonl", lines=True)
            .dropna(subset=["threshold"]).drop_duplicates("question").iterrows()}

    tok = AutoTokenizer.from_pretrained(a.model); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    m = fp8_load(a.model)
    inner = m.model.language_model if hasattr(m.model, "language_model") else m.model
    block = inner.layers[a.layer]

    # calibrate alpha against the layer's own scale
    state = {"vec": None, "alpha": 0.0, "norm": None}
    def hook(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        if state["norm"] is None:
            state["norm"] = float(h.detach().float().norm(dim=-1).mean())
            print(f"  layer {a.layer} mean residual norm = {state['norm']:.1f}", flush=True)
        if state["vec"] is not None and state["alpha"] != 0.0:
            v = torch.as_tensor(state["vec"], dtype=h.dtype, device=h.device)
            h = h + state["alpha"] * state["norm"] * 0.01 * v
        return (h,) + out[1:] if isinstance(out, tuple) else h
    block.register_forward_hook(hook)

    f = open(a.out, "w")
    alphas = [float(x) for x in a.alphas.split(",")]
    for dname in ["favoured", "above_T", "random"]:
        for alpha in alphas:
            if alpha == 0.0 and dname != "favoured":
                continue          # alpha=0 is the same run for every direction
            state["vec"], state["alpha"] = dirs[dname], alpha
            for q in a.questions.split(","):
                for cond in a.conditions.split(","):
                    user = tpl[cond].format(question=qs[q], threshold=f"{int(th[q]):,}")
                    p = tok.apply_chat_template([{"role": "user", "content": user}],
                                                add_generation_prompt=True, tokenize=False)
                    done, t0 = 0, time.time()
                    while done < a.n:
                        bs = min(a.batch, a.n - done)
                        enc = tok([p], return_tensors="pt").to("cuda:0")
                        with torch.no_grad():
                            o = m.generate(**enc, max_new_tokens=a.max_new, do_sample=True,
                                           temperature=1.0, top_p=1.0,
                                           num_return_sequences=bs,
                                           pad_token_id=tok.pad_token_id)
                        for row in o:
                            txt = tok.decode(row[enc["input_ids"].shape[1]:], skip_special_tokens=True)
                            think, _, ans = txt.partition("</think>")
                            f.write(json.dumps({
                                "direction_vec": dname, "alpha": alpha, "question": q,
                                "condition": cond, "threshold": th[q],
                                "reasoning": think, "answer": ans.strip(),
                                "truncated": "</think>" not in txt}) + "\n")
                        f.flush(); done += bs
                    print(f"  {dname} a={alpha:+.0f} {q}/{cond}: {a.n} in {time.time()-t0:.0f}s", flush=True)
    f.close()
    print("DONE ->", a.out, flush=True)


if __name__ == "__main__":
    main()
