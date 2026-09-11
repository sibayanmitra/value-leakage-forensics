"""Q3, mechanistically: does the warning that works suppress the anchor representation?

Behaviourally we know: "do not let the number anchor you" moves p(>T) by -0.233, "do not let
the bet influence you" by -0.183, and a placebo naming the phrasing by -0.090 (n.s.). What we
do not know is WHY, and without that the mitigation is an observation rather than a mechanism.

This measures one prompt-level quantity per condition: the projection of the prompt's final
residual-stream activation onto the ANCHOR direction, where

    anchor = mean(neutral_T) - mean(baseline)

i.e. the direction that isolates the presence of the number and nothing else (the two prompts
are an exact minimal pair). Directions are built leave-one-question-out, so the direction used
to score question q never saw q.

This needs no per-rollout variation -- one forward pass per prompt -- because a fixed prompt has
a fixed activation. That is exactly why it is cheap, and also why a probe at this position could
never have predicted per-rollout outcome variation; that has to be read during generation.

Prediction if the warning works by suppressing the anchor:
    baseline < warned_anchor < warned_values ~ warned_placebo < neutral_T ~ above_good
If instead all warnings sit together, the warning does not act on the anchor representation and
the mitigation works some other way -- also a result, and the one that would falsify the story.
"""
import argparse, json, os, sys
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
import numpy as np, pandas as pd, torch, yaml
from transformers import AutoTokenizer, AutoModelForCausalLM
sys.path.insert(0, str(Path(__file__).resolve().parent))

CONDS = ["baseline", "neutral_T", "above_good", "below_good",
         "warned_anchor", "warned_values", "warned_placebo"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3.5-9B")
    ap.add_argument("--questions", default="")
    ap.add_argument("--layers", default="", help="default: 20%%..80%% depth, 5 layers")
    ap.add_argument("--out", default="results/anchor_projection.csv")
    a = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml"))
    tpl = yaml.safe_load(open("configs/prompts.yaml"))
    th = {r["question"]: r["threshold"] for _, r in
          pd.read_json("results/authors_extracted.jsonl", lines=True)
            .dropna(subset=["threshold"]).drop_duplicates("question").iterrows()}
    QS = a.questions.split(",") if a.questions else [q for q in sorted(qs) if q in th]
    print(f"{len(QS)} questions: {QS}", flush=True)

    tok = AutoTokenizer.from_pretrained(a.model)
    m = AutoModelForCausalLM.from_pretrained(a.model, dtype="auto", device_map="cuda:0").eval()
    inner = m.model.language_model if hasattr(m.model, "language_model") else m.model
    nL = len(inner.layers)
    layers = ([int(x) for x in a.layers.split(",")] if a.layers
              else [int(nL * f) for f in (0.2, 0.35, 0.5, 0.65, 0.8)])
    print(f"{nL} layers; measuring at {layers}", flush=True)

    store = {}
    hooks = [inner.layers[L].register_forward_hook(
        lambda mod, i, o, L=L: store.__setitem__(L, (o[0] if isinstance(o, tuple) else o).detach()))
        for L in layers]

    def act(cond, q):
        user = tpl[cond].format(question=qs[q], threshold=f"{int(th[q]):,}")
        text = tok.apply_chat_template([{"role": "user", "content": user}],
                                       add_generation_prompt=True, tokenize=False)
        enc = tok(text, return_tensors="pt").to("cuda:0")
        with torch.no_grad():
            m(**enc)
        return {L: store[L][0, -1].float().cpu().numpy() for L in layers}

    A = {c: {q: act(c, q) for q in QS} for c in CONDS}
    print("collected", flush=True)

    rows = []
    for L in layers:
        for qi, q in enumerate(QS):
            keep = [x for x in QS if x != q]                     # leave-one-question-out
            v = (np.mean([A["neutral_T"][k][L] for k in keep], 0)
                 - np.mean([A["baseline"][k][L] for k in keep], 0))
            v = v / np.linalg.norm(v)
            for c in CONDS:
                rows.append({"layer": L, "question": q, "condition": c,
                             "proj": float(A[c][q][L] @ v)})
    df = pd.DataFrame(rows)
    df.to_csv(a.out, index=False)
    for h in hooks: h.remove()

    print("\nprojection onto the anchor direction (mean over questions, held out)\n")
    piv = df.pivot_table(index="condition", columns="layer", values="proj")
    piv = piv.reindex(CONDS)
    print(piv.round(2).to_string())
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
