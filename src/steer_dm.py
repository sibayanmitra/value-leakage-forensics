"""Difference-of-means steering: build a clean direction, then test whether it CAUSES.

Why not the logistic probe. The XOR probe reached only 0.58 after controls, and steering a
0.58 direction gives a null you cannot interpret -- indistinguishable from the intervention
being too weak. That is not the direction's fault so much as the instrument's: a logistic
fit on a noisy per-token label is the weakest way to find a direction. The standard tool
(CAA / ActAdd, and Gilg et al.) is a difference of means between PAIRED prompts, which is
what we have.

    valence = mean(above_good) - mean(below_good)   # prompts differ ONLY by good/bad swap
    anchor  = mean(neutral_T)  - mean(baseline)     # differ ONLY by the number's presence

Both are exact minimal pairs, so each difference isolates one variable by construction.
Directions are built LEAVE-ONE-QUESTION-OUT: the direction used on question q never saw q.

Three steering arms, each answering a different question:

  anchor -> baseline      Does the anchor direction CAUSE the pull? This is the positive
                          control for the whole method: if adding "there is a number here"
                          to a prompt with no number does not raise estimates, no null in
                          the other arms means anything.

  -valence -> above_good  Can we TURN THE EFFECT OFF by editing activations? (Neel's third
                          ask, causally rather than by prompting.)

  valence -> neutral_T    Inject a side-preference where the prompt states none. If our
                          reading is right (the number does the work), this should move the
                          answer far less than the anchor arm does.

  random                  Norm-matched Gaussian. Negative control.

alpha is in units of the layer's own mean residual norm, so it is comparable across layers.
"""
import argparse, json, os, sys, time
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import numpy as np, pandas as pd, torch, yaml
from transformers import AutoTokenizer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fp8_load import load as fp8_load

MODEL = "Qwen/Qwen3.5-35B-A3B-FP8"


def prompt_for(tok, tpl, qs, th, cond, q):
    user = tpl[cond].format(question=qs[q], threshold=f"{int(th[q]):,}")
    return tok.apply_chat_template([{"role": "user", "content": user}],
                                   add_generation_prompt=True, tokenize=False)


def collect_prompt_acts(m, tok, texts, layers, inner):
    """Residual stream at the LAST prompt token, per layer. One forward pass per prompt."""
    store, out = {}, []
    hooks = [inner.layers[L].register_forward_hook(
        lambda mod, i, o, L=L: store.__setitem__(L, (o[0] if isinstance(o, tuple) else o).detach()))
        for L in layers]
    try:
        for t in texts:
            enc = tok(t, return_tensors="pt").to("cuda:0")
            with torch.no_grad():
                m(**enc)
            out.append(np.stack([store[L][0, -1].float().cpu().numpy() for L in layers]))
    finally:
        for h in hooks:
            h.remove()
    return np.stack(out)                      # (n_prompts, n_layers, d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", default="bridge,giraffes,tbc")
    ap.add_argument("--layer", type=int, default=None, help="default: 40% depth")
    ap.add_argument("--alphas", default="0,6,12")
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--batch", type=int, default=15)
    ap.add_argument("--max-new", type=int, default=18000)
    ap.add_argument("--reps", type=int, default=8, help="prompt samples per (cond,question)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    QS = a.questions.split(",")
    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    th = {r["question"]: r["threshold"] for _, r in
          pd.read_json("results/authors_extracted.jsonl", lines=True)
            .dropna(subset=["threshold"]).drop_duplicates("question").iterrows()}

    tok = AutoTokenizer.from_pretrained(MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    m = fp8_load(MODEL)
    inner = m.model.language_model if hasattr(m.model, "language_model") else m.model
    nL = len(inner.layers)
    L = a.layer if a.layer is not None else int(nL * 0.4)
    print(f"{nL} layers; steering at layer {L}", flush=True)

    # ---- build directions, leave-one-question-out -------------------------------
    conds = ["above_good", "below_good", "neutral_T", "baseline"]
    acts = {}
    for c in conds:
        A = collect_prompt_acts(m, tok, [prompt_for(tok, tpl, qs, th, c, q) for q in QS], [L], inner)
        acts[c] = A[:, 0, :]                                        # (n_questions, d)
    dirs = {}
    for i, q in enumerate(QS):
        keep = [j for j in range(len(QS)) if j != i]
        v = acts["above_good"][keep].mean(0) - acts["below_good"][keep].mean(0)
        an = acts["neutral_T"][keep].mean(0) - acts["baseline"][keep].mean(0)
        rng = np.random.default_rng(0); r = rng.standard_normal(v.shape)
        dirs[q] = {"valence": v / np.linalg.norm(v),
                   "anchor":  an / np.linalg.norm(an),
                   "random":  r / np.linalg.norm(r)}
    c0 = np.mean([float(dirs[q]["valence"] @ dirs[q]["anchor"]) for q in QS])
    print(f"mean cos(valence, anchor) = {c0:+.3f}", flush=True)
    for q in QS:
        print(f"  {q}: |valence|-normalised, held out from its own direction", flush=True)

    # ---- steering hook -----------------------------------------------------------
    state = {"vec": None, "alpha": 0.0, "norm": None}
    def hook(mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        if state["norm"] is None:
            state["norm"] = float(h.detach().float().norm(dim=-1).mean())
            print(f"  layer {L} mean residual norm {state['norm']:.1f}", flush=True)
        if state["vec"] is not None and state["alpha"] != 0.0:
            v = torch.as_tensor(state["vec"], dtype=h.dtype, device=h.device)
            h = h + (state["alpha"] * 0.01 * state["norm"]) * v
        return (h,) + tuple(out[1:]) if isinstance(out, tuple) else h
    inner.layers[L].register_forward_hook(hook)

    ARMS = [("anchor",  "baseline",   +1),   # positive control: does the anchor cause the pull?
            ("valence", "above_good", -1),   # can we turn it off?
            ("valence", "neutral_T",  +1),   # inject a side where none is stated
            ("random",  "above_good", -1)]   # negative control

    f = open(a.out, "w")
    alphas = [float(x) for x in a.alphas.split(",")]
    for dname, cond, sign in ARMS:
        for alpha in alphas:
            if alpha == 0.0 and (dname, cond) != ARMS[0][:2]:
                continue                      # alpha=0 for a given prompt is arm-independent
            for q in QS:
                state["vec"] = dirs[q][dname] * sign
                state["alpha"] = alpha
                p = prompt_for(tok, tpl, qs, th, cond, q)
                done, t0 = 0, time.time()
                while done < a.n:
                    bs = min(a.batch, a.n - done)
                    enc = tok([p], return_tensors="pt").to("cuda:0")
                    with torch.no_grad():
                        o = m.generate(**enc, max_new_tokens=a.max_new, do_sample=True,
                                       temperature=1.0, top_p=1.0, num_return_sequences=bs,
                                       pad_token_id=tok.pad_token_id)
                    for row in o[:, enc["input_ids"].shape[1]:]:
                        txt = tok.decode(row, skip_special_tokens=False).replace("<|im_end|>", "")
                        cot, ans = (txt.split("</think>", 1) if "</think>" in txt else (txt, ""))
                        f.write(json.dumps({"direction": dname, "sign": sign, "condition": cond,
                                            "alpha": alpha, "layer": L, "question": q,
                                            "threshold": float(th[q]), "reasoning": cot,
                                            "answer": ans.strip(),
                                            "truncated": "</think>" not in txt}) + "\n")
                    f.flush(); done += bs
                print(f"  {dname}{'+' if sign>0 else '-'} -> {cond} a={alpha:g} {q}: "
                      f"{done} in {time.time()-t0:.0f}s", flush=True)
    f.close()
    print("DONE ->", a.out, flush=True)


if __name__ == "__main__":
    main()
