"""Audit 2026-09-10: every decimal in RECORD.md must appear in the output of some script run during
the audit. Prints each number that does not, with its line, so it can be classified by hand
(a deliberately stale value in the §0 table, a value labelled as from RESULTS.md, or an error).

usage: audit_numbers.py DIR_OF_AUDIT_OUTPUTS [DOC.md]   (DOC defaults to RECORD.md)
"""
import re, sys, glob
from pathlib import Path
norm = lambda s: s.replace("−", "-").replace("–", "-")
corpus = norm("\n".join(Path(f).read_text(errors="ignore") for f in glob.glob(f"{sys.argv[1]}/*.txt")))
TOK = re.compile(r"(?<![\w.])[+-]?\d+\.\d{2,3}(?!\d)")
def found(t):
    bare = t.lstrip("+-")
    return any(v in corpus for v in {t, bare, "+" + bare, "-" + bare})
sec, miss, n = "", [], 0
DOC = sys.argv[2] if len(sys.argv) > 2 else "RECORD.md"
for i, line in enumerate(Path(DOC).read_text().split("\n"), 1):
    if line.startswith("## "): sec = line[3:40]
    for t in TOK.findall(norm(line)):
        n += 1
        if not found(t): miss.append((i, sec, t, line.strip()[:110]))
print(f"{n} decimals checked, {len(miss)} not found in any audit output\n")
for i, sec, t, l in miss: print(f"  line {i:4d}  [{sec[:28]:28s}] {t:>8s}  | {l}")
