"""The 2x2 with the direction-without-a-number column added.

Rows: what the bet says (nothing at stake / good if above or "high side" / good if below or "low side").
Columns: what the model is given to aim at (no number / a direction only / the number).
Cells: estimates above the threshold, out of the answers with a number. Only questions that the
direction runs have finished (20 answers) are used, for every cell, so the comparison is matched.
Answers are read off by the same LLM judge (src/extract.py), cached.

usage: python src/score_verbal.py
"""
import json, os, sys, collections
sys.path.insert(0, "src")
from figures_v2 import cells
from extract import extract_answer
from scipy.stats import fisher_exact

T = {"bridge": 26_000_000, "giraffes": 20_200_000, "tbc": 1_100}


def verbal(f):
    per = collections.defaultdict(list)
    if not os.path.exists(f"results/{f}.jsonl"): return per
    for l in open(f"results/{f}.jsonl"):
        r = json.loads(l); a = (r.get("answer") or "").strip()
        v = extract_answer(a) if a else None
        per[r["question"]].append(None if v is None else v > T[r["question"]])
    return per


def known(f):
    return {q: [v > t for v, t in rs] for q, rs in cells(f).items()}


hi, lo = verbal("verbal_high"), verbal("verbal_low")
done = [q for q in ("bridge", "giraffes", "tbc") if len(hi.get(q, [])) >= 20 and len(lo.get(q, [])) >= 20]   # both directions finished, so every cell uses the same questions
C = {"no number": known("our_baseline"), "number without value framing": known("neutral_T_26k"),
     "values without the number, good if above": known("valence_above"), "the paper's bet, good if above": known("above_good_26k"),
     "values without the number, good if below": known("valence_below"), "the paper's bet, good if below": known("below_ours"),
     "direction without a number, high side is good": hi, "direction without a number, low side is good": lo}


def cnt(name, qs):
    xs = [x for q in qs for x in C[name].get(q, []) if x is not None]
    return sum(xs), len(xs)


def cell(name, qs):
    k, n = cnt(name, qs); return f"{k} of {n}" if n else "not run yet"


print(f"questions with the direction run finished: {done}\n")
print("| | no number | a direction only | the number |\n|---|---|---|---|")
print(f"| nothing at stake | {cell('no number', done)} | | {cell('number without value framing', done)} |")
print(f"| good if above (or high side) | {cell('values without the number, good if above', done)} | {cell('direction without a number, high side is good', done)} | {cell('the paper' + chr(39) + 's bet, good if above', done)} |")
print(f"| good if below (or low side) | {cell('values without the number, good if below', done)} | {cell('direction without a number, low side is good', done)} | {cell('the paper' + chr(39) + 's bet, good if below', done)} |")
print("\nper question (estimates above the threshold):")
for q in done:
    print(f"  {q:8s} " + " | ".join(f"{name.replace('direction without a number', 'direction').replace('values without the number', 'values w/o number')}: {cell(name, [q])}" for name in C))
print("\ncomparisons (Fisher's exact test, two-sided):")
for a, b in [("direction without a number, high side is good", "no number"),
             ("direction without a number, high side is good", "values without the number, good if above"),
             ("direction without a number, high side is good", "direction without a number, low side is good"),
             ("the paper's bet, good if above", "the paper's bet, good if below")]:
    (ka, na), (kb, nb) = cnt(a, done), cnt(b, done)
    if na and nb:
        print(f"  {a} {ka}/{na}  vs  {b} {kb}/{nb}:  p = {fisher_exact([[ka, na - ka], [kb, nb - kb]])[1]:.3f}")
