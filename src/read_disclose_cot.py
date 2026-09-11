"""Reading aid for the CoT-visible disclosure runs. Not a scorer.

For every rollout that copied, prints the forced verdict, whether the reasoning finished, the
LAST explicit decision sentence in the reasoning ("I will say NO", "Let's go with YES", ...), and
the last ~700 characters. The decision regex is a pointer to where to read, not a label: per
CLAUDE.md, each verdict is checked by reading the tail, and the hand reading goes in
configs/hand_labels/disclose_cot_{frame}.json.

usage: python src/read_disclose_cot.py own [--only-no] [--only-cut]
"""
import json, re, sys

frame = sys.argv[1]
only_no, only_cut = "--only-no" in sys.argv, "--only-cut" in sys.argv
CLEAN = re.compile(r"^\W*\b(YES|NO)\b", re.I)
DEC = re.compile(r"(?:I will|I'll|I am going to|Let's|let's|I should|I must|Decision:|decide to|choose|go with|stick with|say)"
                 r"[^.\n]{0,40}?\b(YES|NO)\b")
norm = lambda s: " ".join((s or "").split())

src = {i + 1: json.loads(l) for i, l in enumerate(open("results/naked_number.jsonl"))}
copied = lambda ln: f"{int(src[ln]['threshold']):,}" in src[ln]["answer"] or str(int(src[ln]["threshold"])) in src[ln]["answer"]

for r in map(json.loads, open(f"results/disclose_cot_{frame}.jsonl")):
    ln = r["source_line"]
    if not copied(ln): continue
    m = CLEAN.match((r["forced"] or "").strip()); v = m.group(1).upper() if m else None
    fin = "</think>" in r["full"]
    if only_no and v != "NO": continue
    if only_cut and fin: continue
    reasoning = r["full"].split("</think>")[0]
    decs = DEC.findall(reasoning)
    print(f"\n=== {frame} line {ln} {r['question']} | forced {v} | {'finished' if fin else 'CUT OFF'} | "
          f"decision pointers {len(decs)}, last 5: {decs[-5:]}")
    print("   …" + norm(reasoning)[-700:])
    if fin: print("   WRITTEN: " + norm(r["full"].split("</think>", 1)[1])[:250])
