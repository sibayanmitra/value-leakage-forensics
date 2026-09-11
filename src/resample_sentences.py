"""Step 2 of resampling the own-frame denials (Thought Anchors-style): which sentences move the verdict?

For each reliable denier from step 1 (results/resample_denials_p*.jsonl) and each chosen sentence k
of its greedy own-frame reply (configs/resample_positions.json), two arms:

  resampled  the reply up to the START of sentence k is kept; the model writes its own sentence k and
             everything after it
  kept       the reply through sentence k (up to the start of sentence k+1) is kept; the model writes
             everything after it

importance(k) = P(NO | kept) - P(NO | resampled). A "cut" is a sentence start; kept(k) and
resampled(k+1) are the same cut, so each distinct cut is sampled once and every position that uses it
reads the same samples.

CUTS FALL ON THE REPLY'S OWN TOKEN BOUNDARIES. The first version cut the text at the sentence's first
character and re-tokenized it; the prefix then ended in a whitespace token the model never produced
(e.g. four spaces before a bullet), and its greedy continuation dropped the bullet marker. Now the
reply is tokenized once with offsets, each cut is snapped back to the last token boundary at or before
the sentence start, and the model receives prompt ids + the reply's own ids up to that boundary. The
kept prefix is asserted to contain the whole of sentence k, and the resampled prefix none of it.

Same prompt as step 1 and the original run (built by `disclose_cot.build`), same sampling (temperature
0.6, top-p 0.95, top-k off), and the same 2,000-token cap on the WHOLE reply, counted from its start:
each continuation gets 2,000 minus the reply tokens already in the prefix. Rows in a batch can have
different budgets; the batch generates to the largest and each row is cut back to its own budget,
which leaves each row's distribution unchanged. The verdict is then forced exactly as in every other
disclosure run (text + `Final answer (YES or NO):`, 8 greedy tokens).

For the resampled arm, the first sentence the model writes is recorded next to the original sentence
with a string similarity (difflib ratio), so replacements that merely repeat the original can be set
aside, as Thought Anchors does with its own similarity filter.
"""
import argparse, collections, difflib, json, os, re, sys, time
from pathlib import Path
os.environ.setdefault("CUDA_VISIBLE_DEVICES", os.environ.get("VLF_GPU", "0"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import torch, yaml
from transformers import AutoTokenizer
from disclose_cot import build, CUE, MODEL

SENT = re.compile(r"(?<=[.!?])\s+|\n+")


def sentences(t):
    """(char_offset, sentence) pairs; same splitter as src/resample_sweep.py."""
    out, pos = [], 0
    for part in SENT.split(t):
        if part.strip():
            off = t.find(part, pos); out.append((off, part)); pos = off + len(part)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--positions", default="configs/resample_positions.json")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--nparts", type=int, default=1)
    ap.add_argument("--n", type=int, default=5, help="samples per cut")
    ap.add_argument("--temp", type=float, default=0.6)
    ap.add_argument("--top-p", type=float, default=0.95)
    ap.add_argument("--top-k", type=int, default=0, help="0 = off (None would fall back to the checkpoint's top-k 20)")
    ap.add_argument("--cap", type=int, default=2000, help="token cap on the whole reply, counted from its start")
    ap.add_argument("--force-tokens", type=int, default=8)
    ap.add_argument("--tok-budget", type=int, default=27500)
    ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--check-greedy", type=int, default=32)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = json.load(open(a.positions))["rollouts"]
    qs = yaml.safe_load(open("configs/questions.yaml")); tpl = yaml.safe_load(open("configs/prompts.yaml"))
    src = {i + 1: json.loads(l) for i, l in enumerate(open("results/naked_number.jsonl"))}
    own = {json.loads(l)["source_line"]: json.loads(l) for l in open("results/disclose_cot_own.jsonl")}
    tok = AutoTokenizer.from_pretrained(MODEL)
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    ros = sorted(map(int, cfg))[a.part::a.nparts]
    prompt, pids, rids, cuts = {}, {}, {}, {}
    for ro in ros:
        r = src[ro]; shown = f"{int(r['threshold']):,}"
        user1 = tpl["naked_number"].format(question=qs[r["question"]], threshold=shown)
        prompt[ro] = build(tok, "own", user1, r["reasoning"], r["answer"].strip(), shown)
        pids[ro] = tok(prompt[ro]).input_ids
        full = own[ro]["full"]
        enc = tok(full, add_special_tokens=False, return_offsets_mapping=True)
        rids[ro], offs = enc["input_ids"], enc["offset_mapping"]
        print(f"rollout {ro}: reply {len(rids[ro])} tokens; decode(ids) == saved text: {tok.decode(rids[ro]) == full}", flush=True)
        snap = lambda c: sum(1 for (_, e) in offs if e <= c)          # tokens that end at or before char c
        S = sentences(full); starts = {off: j for j, (off, _) in enumerate(S)}
        for p in cfg[str(ro)]:
            k = p["idx"]; off, s = S[k]
            assert s.strip().startswith(p["starts"]), (ro, k, s[:80], p["starts"])
            for arm, c in (("resampled", off), ("kept", S[k + 1][0])):
                j = snap(c); text = tok.decode(rids[ro][:j])
                if arm == "kept": assert text.rstrip().endswith(s.strip()), (ro, k, "kept prefix lacks the sentence", text[-80:])
                else: assert s.strip()[:20] not in text[-len(s) - 5:], (ro, k, "resampled prefix contains the sentence")
                cc = cuts.setdefault((ro, j), {"uses": [], "orig_next": S[starts[c]][1].strip(), "next_idx": starts[c],
                                               "char": offs[j - 1][1] if j else 0, "sent_char": c})
                cc["uses"].append([p["role"], k, arm])
    for (ro, j), c in cuts.items():
        c["prefix_tokens"] = j; c["budget"] = a.cap - j; c["len"] = len(pids[ro]) + j
        assert c["budget"] > 0
    for (ro, j), c in sorted(cuts.items()):
        print(f"rollout {ro:2d} cut tok {j:4d} (char {c['char']:5d}, sentence {c['next_idx']:3d} starts at {c['sent_char']:5d}) budget {c['budget']:4d}, "
              f"input {c['len']:5d} | uses {c['uses']} | tail {own[ro]['full'][max(0, c['char'] - 25):c['char']]!r}", flush=True)

    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l); done.add((r["source_line"], r["cut_tok"], r["sample"]))
    jobs = [(ro, j, s) for (ro, j) in cuts for s in range(a.n) if (ro, j, s) not in done]
    jobs.sort(key=lambda x: (cuts[(x[0], x[1])]["len"], x[0], x[1], x[2]))
    batches, cur = [], []
    for jb in jobs:
        L = cuts[(jb[0], jb[1])]["len"]
        if cur and (len(cur) + 1 > a.batch or (len(cur) + 1) * L > a.tok_budget):
            batches.append(cur); cur = []
        cur.append(jb)
    if cur: batches.append(cur)
    print(f"{len(cuts)} cuts, {len(jobs)} samples to run ({len(done)} already done), {len(batches)} batches, sizes {[len(b) for b in batches]}", flush=True)
    if a.dry_run:
        return

    def left_pad(seqs):
        L = max(len(x) for x in seqs)
        ids = torch.tensor([[pad] * (L - len(x)) + x for x in seqs], device="cuda:0")
        att = torch.tensor([[0] * (L - len(x)) + [1] * len(x) for x in seqs], device="cuda:0")
        return ids, att

    from fp8_load import load as fp8_load
    m = fp8_load(MODEL)

    if a.check_greedy:
        for ro, j in [next(k for k, c in sorted(cuts.items()) if any(u[2] == "kept" for u in c["uses"])),
                      next(k for k, c in sorted(cuts.items()) if any(u[2] == "resampled" for u in c["uses"]))]:
            ids, att = left_pad([pids[ro] + rids[ro][:j]])
            with torch.no_grad():
                o = m.generate(input_ids=ids, attention_mask=att, max_new_tokens=a.check_greedy, do_sample=False, pad_token_id=pad)
            new = o[0, ids.shape[1]:].tolist()
            ok = new == rids[ro][j:j + len(new)]
            print(f"GREEDY CHECK rollout {ro} cut tok {j}: {'MATCH (token ids identical)' if ok else 'MISMATCH'}\n"
                  f"  regenerated: {tok.decode(new)!r}\n  saved:       {tok.decode(rids[ro][j:j + len(new)])!r}", flush=True)

    f = open(a.out, "a"); t0 = time.time(); n_done = 0
    for bi, idx in enumerate(batches):
        seed = 7_000_003 + a.seed * 100003 + a.part * 1009 + bi + len(done)
        torch.manual_seed(seed)
        budgets = [cuts[(ro, j)]["budget"] for ro, j, _ in idx]
        ids, att = left_pad([pids[ro] + rids[ro][:j] for ro, j, _ in idx])
        with torch.no_grad():
            o = m.generate(input_ids=ids, attention_mask=att, max_new_tokens=max(budgets), do_sample=True,
                           temperature=a.temp, top_p=a.top_p, top_k=a.top_k, pad_token_id=pad)
        gen = o[:, ids.shape[1]:]
        conts, ntoks = [], []
        for g, b in zip(gen, budgets):
            g = g[:b]; ntoks.append(int((g != pad).sum())); conts.append(tok.decode(g, skip_special_tokens=True))
        pres = [tok.decode(rids[ro][:j]) for ro, j, _ in idx]
        e2 = tok([prompt[ro] + pre + p + CUE for (ro, _, _), pre, p in zip(idx, pres, conts)], return_tensors="pt", padding=True,
                 padding_side="left").to("cuda:0")
        with torch.no_grad():
            o2 = m.generate(**e2, max_new_tokens=a.force_tokens, do_sample=False, pad_token_id=pad)
        forced = [tok.decode(x, skip_special_tokens=True).strip() for x in o2[:, e2["input_ids"].shape[1]:]]
        for (ro, j, s), p, fo, nt in zip(idx, conts, forced, ntoks):
            c = cuts[(ro, j)]
            first = next((x.strip() for _, x in sentences(p)), "")
            f.write(json.dumps({"source_line": ro, "question": src[ro]["question"], "cut_tok": j, "cut": c["char"],
                                "next_idx": c["next_idx"], "uses": c["uses"], "sample": s, "seed": seed, "batch": bi,
                                "temperature": a.temp, "top_p": a.top_p, "top_k": a.top_k, "cap": a.cap,
                                "prefix_tokens": j, "budget": c["budget"], "new_tokens": nt,
                                "finished": "</think>" in p, "orig_next": c["orig_next"], "new_next": first,
                                "sim": round(difflib.SequenceMatcher(None, first, c["orig_next"]).ratio(), 3),
                                "cont": p, "forced": fo}) + "\n")
        f.flush(); n_done += len(idx)
        print(f"  {n_done}/{len(jobs)} in {time.time() - t0:.0f}s", flush=True)
    f.close(); print("DONE ->", a.out, flush=True)


if __name__ == "__main__":
    main()
