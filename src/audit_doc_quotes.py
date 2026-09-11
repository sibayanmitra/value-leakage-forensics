"""Audit 2026-09-10: check every quotation in a markdown doc against the raw data.

Parsing: blockquote markers ("> ") are stripped first, then quotes are taken from the cleaned
text as (a) inline *"..."* spans, which may wrap across lines, and (b) plain "..." spans inside a
blockquote. Each quote is paired with the citation `results/FILE.jsonl` line N found in the same
paragraph (or the line just before it), nearest by position. Each quote is split at ellipses into
fragments; a fragment must appear at the cited row when there is a citation, or anywhere in
results/ when there is none.

Normalisation, both sides, formatting only: the model writes "* " bullets and double quotes where
docs drop bullets and use single quotes; "*" or "×" for multiplication; "->" or "→"; markdown
emphasis and escapes are dropped.

usage: audit_doc_quotes.py DOC.md [DOC.md ...]
"""
import json, re, sys, glob
from pathlib import Path

PAD = re.compile(r"(<\|endoftext\|>|<\|im_end\|>|<\|im_start\|>)")
FIELDS = ("reasoning", "answer", "reply", "full", "forced", "sentence")
CITE = re.compile(r"results/([\w.\-]+\.jsonl)`?,?\s+line\s+(\d+)")


def norm(s):
    s = PAD.sub("", s or "")
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("−", "-"), ("\\", ""),
                 ("*", " "), ("×", " "), ("→", " "), ("->", " "), ('"', "'"), ("`", "")):
        s = s.replace(a, b)
    s = " ".join(s.split())
    s = re.sub(r"\s+([,.;:!?)\]])", r"\1", s)
    return re.sub(r"([(\[])\s+", r"\1", s).lower()


ROWS = {}
def rows_of(fn):
    if fn not in ROWS:
        ROWS[fn] = [norm(" ".join(str(json.loads(l).get(k, "")) for k in FIELDS))
                    for l in open(f"results/{fn}", errors="ignore")]
    return ROWS[fn]


corpus = "\n".join(t for f in glob.glob("results/*.jsonl") for t in rows_of(Path(f).name))


def extract(doc_text):
    """yield (line_no, quote, citation_or_None)"""
    lines = doc_text.split("\n")
    is_bq = [l.lstrip().startswith(">") for l in lines]
    clean = [re.sub(r"^\s*>\s?", "", l) for l in lines]
    text = "\n".join(clean)
    starts = [0]
    for l in clean: starts.append(starts[-1] + len(l) + 1)
    line_of = lambda pos: next(i for i in range(len(lines)) if starts[i + 1] > pos) + 1
    # paragraphs: split on blank lines in the cleaned text
    paras = [(m.start(), m.end()) for m in re.finditer(r"(?:[^\n]*\S[^\n]*\n?)+", text)]
    def citation(pos):
        for a, b in paras:
            if a <= pos < b:
                lo = starts[max(0, line_of(a) - 2)]          # include the line before the paragraph
                cands = [(abs(m.start() + lo - pos), m) for m in CITE.finditer(text[lo:b])]
                if cands:
                    m = min(cands, key=lambda x: x[0])[1]
                    return m.group(1), int(m.group(2))
                # a blockquote's citation often sits in the next paragraph of the same blockquote
                nxt = text[b:b + 200]
                m = CITE.search(nxt.split("\n\n")[0]) if nxt else None
                return (m.group(1), int(m.group(2))) if m else None
        return None
    taken = []
    for m in re.finditer(r'\*"(.+?)"\*', text, re.S):
        taken.append((m.start(), m.end()))
        yield line_of(m.start()), m.group(1), citation(m.start())
    for m in re.finditer(r'"([^"\n][^"]{28,}?)"', text, re.S):
        if not is_bq[line_of(m.start()) - 1]: continue
        if any(a <= m.start() < b for a, b in taken): continue
        yield line_of(m.start()), m.group(1), citation(m.start())


for doc in sys.argv[1:]:
    n, miss, wrong = 0, [], []
    for ln, q, cite in extract(Path(doc).read_text()):
        for frag in re.split(r"…|\.\.\.", q):
            f = norm(frag).strip(" .,;:'()")
            if len(f) < 18: continue
            n += 1
            if cite:
                fn, row = cite
                try:
                    rs = rows_of(fn)
                    if row - 1 < len(rs) and f in rs[row - 1]: continue
                    wrong.append((ln, f, cite, [k + 1 for k, t in enumerate(rs) if f in t][:5]))
                    continue
                except FileNotFoundError:
                    pass
            if f not in corpus: miss.append((ln, f))
    print(f"=== {doc}: {n} fragments | {len(miss)} not in the data | {len(wrong)} not at the cited line")
    for ln, f in miss: print(f"   NOT FOUND  line {ln:4d}: {f[:170]!r}")
    for ln, f, (fn, row), where in wrong:
        print(f"   WRONG LINE line {ln:4d}: cites {fn}:{row}; found at {where or 'nowhere in that file'}: {f[:120]!r}")
    print()
