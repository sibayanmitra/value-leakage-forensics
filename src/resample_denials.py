"""Step 1 of resampling the own-frame denials (Thought Anchors-style): are they stable?

`results/disclose_cot_own.jsonl` has 8 rollouts (among copies) that deny influence with their own
turn-1 reasoning in view. That run was greedy: one sample each. Here every one of them is resampled
from the START of turn 2, n times, with sampling on, and so is a question-matched control set of
own-frame ADMISSIONS. The outcome is the same as the original run: up to --max-new tokens of
reasoning, then `Final answer (YES or NO):` appended and the verdict forced greedily.

Reading: if the denials deny in most samples and the controls rarely do, the denial is a property of
those rollouts (prompt + its own reasoning), not a greedy accident. If both deny at a similar low
rate, "8 of 57 deny" is mostly sampling noise.

Prompts are built by `disclose_cot.build` itself, so they are identical to the original run.
--check-greedy regenerates the first tokens of one denial greedily, alone, and compares them with
the saved reply, as a check that the prompt really is the same.

Runs in parts (--part/--nparts) so two GPUs can share it; each part gets half the denials and half
the controls. Resumable: rows already in --out are skipped.
"""
import argparse, json, os, random, re, sys, time, collections
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch, yaml, pandas as pd
from transformers import AutoTokenizer, GenerationConfig
from disclose_cot import build, CUE, MODEL

CLEAN = re.compile(r"^\W*\b(YES|NO)\b", re.I)


def select(seed):
    """Denials = every own-frame copy with a strict NO. Controls = own-frame copies with a strict YES,
    the same number per question as the denials, drawn with random.Random(seed)."""
    src = {i + 1: json.loads(l) for i, l in enumerate(open("results/naked_number.jsonl"))}
    cp = lambda ln: f"{int(src[ln]['threshold']):,}" in src[ln]["answer"] or str(int(src[ln]["threshold"])) in src[ln]["answer"]
    own = [json.loads(l) for l in open("results/disclose_cot_own.jsonl")]
    v = lambda r: (m.group(1).upper() if (m := CLEAN.match((r.get("forced") or "").strip())) else None)
    den = sorted([r["source_line"] for r in own if cp(r["source_line"]) and v(r) == "NO"])
    yes = collections.defaultdict(list)
    for r in own:
        if cp(r["source_line"]) and v(r) == "YES": yes[r["question"]].append(r["source_line"])
    need = collections.Counter(src[ln]["question"] for ln in den)
    rng = random.Random(seed)
    ctl = sorted(ln for q, k in sorted(need.items()) for ln in rng.sample(sorted(yes[q]), k))
    return src, den, ctl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--nparts", type=int, default=1)
    ap.add_argument("--n", type=int, default=10, help="samples per rollout")
    ap.add_argument("--temp", type=float, default=0.6)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--top-k", type=int, default=0, help="0 = off")
    ap.add_argument("--max-new", type=int, default=2000)
    ap.add_argument("--force-tokens", type=int, default=8)
    ap.add_argument("--tok-budget", type=int, default=27500)
    ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--check-greedy", type=int, default=48, help="tokens to compare greedily; 0 = skip")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    qs = yaml.safe_load(open("configs/questions.yaml")); tpl = yaml.safe_load(open("configs/prompts.yaml"))
    src, den, ctl = select(a.seed)
    mine = [(ln, "denial") for ln in den[a.part::a.nparts]] + [(ln, "control") for ln in ctl[a.part::a.nparts]]
    print(f"denials {den}\ncontrols {ctl}\npart {a.part}/{a.nparts}: {mine}", flush=True)
    own = {json.loads(l)["source_line"]: json.loads(l) for l in open("results/disclose_cot_own.jsonl")}

    tok = AutoTokenizer.from_pretrained(MODEL); tok.padding_side = "left"
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    prompt = {}
    for ln, _ in mine:
        r = src[ln]; shown = f"{int(r['threshold']):,}"
        user1 = tpl["naked_number"].format(question=qs[r["question"]], threshold=shown)
        prompt[ln] = build(tok, "own", user1, r["reasoning"], r["answer"].strip(), shown)
    lens = {ln: len(tok(t).input_ids) for ln, t in prompt.items()}
    print("prompt tokens:", lens, flush=True)
    gc = GenerationConfig.from_pretrained(MODEL)
    print(f"model generation_config: temperature={gc.temperature} top_p={gc.top_p} top_k={gc.top_k} "
          f"-> using temperature={a.temp} top_p={a.top_p} top_k={a.top_k or 'off'}", flush=True)

    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l); done.add((r["source_line"], r["sample"]))
    jobs = [(ln, g, s) for ln, g in mine for s in range(a.n) if (ln, s) not in done]
    jobs.sort(key=lambda j: (lens[j[0]], j[0], j[2]))
    batches, cur = [], []
    for j in jobs:
        if cur and (len(cur) + 1 > a.batch or (len(cur) + 1) * lens[j[0]] > a.tok_budget):
            batches.append(cur); cur = []
        cur.append(j)
    if cur: batches.append(cur)
    print(f"{len(jobs)} samples to run ({len(done)} already done), {len(batches)} batches, sizes {[len(b) for b in batches]}", flush=True)
    if a.dry_run:
        return

    from fp8_load import load as fp8_load
    m = fp8_load(MODEL)

    if a.check_greedy and mine:
        ln = mine[0][0]
        enc = tok([prompt[ln]], return_tensors="pt").to("cuda:0")
        with torch.no_grad():
            o = m.generate(**enc, max_new_tokens=a.check_greedy, do_sample=False, pad_token_id=tok.pad_token_id)
        new = tok.decode(o[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
        saved = own[ln]["full"]
        ok = saved.startswith(new)
        print(f"GREEDY CHECK rollout {ln}: {'MATCH' if ok else 'MISMATCH'}\n  regenerated: {new!r}\n  saved:       {saved[:len(new) + 20]!r}", flush=True)

    f = open(a.out, "a"); t0 = time.time(); n_done = 0
    for bi, idx in enumerate(batches):
        seed = a.seed * 100003 + a.part * 1009 + bi + len(done)
        torch.manual_seed(seed)
        chunk = [prompt[ln] for ln, _, _ in idx]
        enc = tok(chunk, return_tensors="pt", padding=True).to("cuda:0")
        # top_k must be passed as 0 to switch it off: None falls back to the model's generation_config
        # (top_k=20 for this checkpoint). Thought Anchors reports temperature 0.6, top-p 0.95, no top-k.
        kw = dict(do_sample=True, temperature=a.temp, top_p=a.top_p, top_k=a.top_k)
        with torch.no_grad():
            o = m.generate(**enc, max_new_tokens=a.max_new, pad_token_id=tok.pad_token_id, **kw)
        gen = o[:, enc["input_ids"].shape[1]:]
        ntok = [int((g != tok.pad_token_id).sum()) for g in gen]
        p1 = [tok.decode(x, skip_special_tokens=True) for x in gen]
        e2 = tok([c + p + CUE for c, p in zip(chunk, p1)], return_tensors="pt", padding=True).to("cuda:0")
        with torch.no_grad():
            o2 = m.generate(**e2, max_new_tokens=a.force_tokens, do_sample=False, pad_token_id=tok.pad_token_id)
        forced = [tok.decode(x, skip_special_tokens=True).strip() for x in o2[:, e2["input_ids"].shape[1]:]]
        for (ln, g, s), p, fo, nt in zip(idx, p1, forced, ntok):
            f.write(json.dumps({"source_line": ln, "question": src[ln]["question"], "group": g, "sample": s,
                                "seed": seed, "batch": bi, "temperature": a.temp, "top_p": a.top_p,
                                "top_k": a.top_k or None, "max_new": a.max_new, "new_tokens": nt,
                                "finished": "</think>" in p, "full": p, "forced": fo}) + "\n")
        f.flush(); n_done += len(idx)
        print(f"  {n_done}/{len(jobs)} in {time.time() - t0:.0f}s", flush=True)
    f.close(); print("DONE ->", a.out, flush=True)


if __name__ == "__main__":
    main()
