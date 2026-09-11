#!/usr/bin/env python3
"""Flag AI-sounding words and constructions in a draft.

Usage:  .venv/bin/python src/check_prose.py draft.md

Not a style oracle. It catches the tells listed in the write-up plan; judgement is still yours.
"""
import re, sys, collections

WORDS = """delve leverage leveraging robust underscore underscores pivotal crucial crucially
intricate nuanced landscape realm showcase showcases seamless seamlessly comprehensive testament
garner myriad plethora paradigm holistic multifaceted tapestry unlock unlocks harness harnessing
elevate fosters foster embark embarking utilise utilize utilizing meticulous profound
groundbreaking revolutionary cutting-edge state-of-the-art vibrant bustling""".split()

PHRASES = [
    (r"\bit(?:'s| is) worth noting\b", "it's worth noting"),
    (r"\bit is important to note\b", "it is important to note"),
    (r"\bnot only\b[^.]{0,60}\bbut also\b", "not only X but also Y"),
    (r"^\s*(?:Moreover|Furthermore|Additionally)\b", "paragraph opening with Moreover/Furthermore/Additionally"),
    (r"^\s*(?:Importantly|Crucially|Notably|Interestingly),", "sentence opening with Importantly/Crucially/Notably"),
    (r"\bin conclusion\b", "in conclusion"),
    (r"\boverall,? this (?:demonstrates|shows|suggests)\b", "overall this demonstrates"),
    (r"\bmay potentially\b|\bcould possibly\b|\bmight perhaps\b", "stacked hedge"),
    (r"\bdive deep(?:er)?\b|\bdeep dive\b", "deep dive"),
    (r"\ba testament to\b", "a testament to"),
    (r"\bplays a (?:key|vital|significant) role\b", "plays a key role"),
    (r"\bsheds? light on\b", "sheds light on"),
    (r"\bpave(?:s|d)? the way\b", "paves the way"),
]

def main(path):
    text = open(path).read()
    lines = text.split("\n")
    hits = collections.Counter(); detail = []

    for i, ln in enumerate(lines, 1):
        low = ln.lower()
        for wd in WORDS:
            for m in re.finditer(rf"\b{re.escape(wd)}\b", low):
                hits[wd] += 1
                detail.append((i, wd, ln.strip()[:90]))
        for pat, name in PHRASES:
            if re.search(pat, ln, re.I | re.M):
                hits[name] += 1
                detail.append((i, name, ln.strip()[:90]))

    words = len(re.findall(r"\b\w+\b", text))
    dashes = text.count("—")
    thissug = len(re.findall(r"\bthis suggests\b", text, re.I))

    print(f"{path}: {words} words, {len(lines)} lines\n")
    if detail:
        print("FLAGS")
        for i, what, ctx in detail:
            print(f"  line {i:4d}  {what:52s} | {ctx}")
    else:
        print("No banned words or constructions found.")

    print("\nRATES")
    per300 = dashes / max(words / 300, 1)
    print(f"  em-dashes            {dashes:3d}  ({per300:.1f} per 300 words; target <= 1)"
          + ("   OVER" if per300 > 1 else ""))
    print(f"  'this suggests'      {thissug:3d}  (target <= 2)" + ("   OVER" if thissug > 2 else ""))
    firsts = collections.Counter()
    for ln in lines:
        m = re.match(r"\s*[-*]\s+(\w+)", ln)
        if m: firsts[m.group(1).lower()] += 1
    rep = [(w_, c) for w_, c in firsts.items() if c >= 4]
    if rep:
        print("  bullets starting with the same word 4+ times:")
        for w_, c in sorted(rep, key=lambda x: -x[1]):
            print(f"      '{w_}' x{c}")
    print(f"\n{sum(hits.values())} flags total.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1])
