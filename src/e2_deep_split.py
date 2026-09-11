"""E2 re-analysis, correct source keying.

resamples_forced_{a,b} are the first 16-source batch and {c,d} the expanded 34-source
batch; the two batches RE-USE source ids 0..15 for different rollouts, so the join key
is (batch, source) -- 50 sources, matching e2_all_scored's renumbering.

Question: the aim-sentence effect -- is it a VALUE effect, or the same anchoring effect
the 2x2 identified, seen from inside the CoT? Aim sentences characteristically restate
the threshold ("So > 26M = Good"). Split on both axes and see which carries it.
"""
import json, re, sys, collections
import numpy as np
sys.path.insert(0, "src")
from extract import extract_answer

rng = np.random.default_rng(0)
HAND = {}
for l in open("results/e2_all_scored.jsonl"):
    r = json.loads(l)
    if r.get("hand_aim") is not None:
        HAND[r["sentence"]] = bool(r["hand_aim"])

NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand|bn|[mkb])?\b", re.I)
MULT = {"m": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9, "k": 1e3, "thousand": 1e3}

def mentions_T(s, T, tol=0.05):
    for val, suf in NUM.findall(s or ""):
        try: v = float(val.replace(",", ""))
        except ValueError: continue
        if abs(v * MULT.get((suf or "").lower(), 1.0) - T) <= tol * T:
            return True
    return False

rows = []
for f in "abcd":
    batch = "ab" if f in "ab" else "cd"
    for l in open(f"results/resamples_forced_{f}.jsonl"):
        r = json.loads(l)
        v = extract_answer(r["answer"])
        if v is None: continue
        T = float(r["threshold"])
        rows.append({"src": (batch, r["source"]), "question": r["question"], "arm": r["arm"],
                     "direction": r["direction"], "T": T, "sentence": r["sentence"],
                     "orig_aim": r.get("orig_aim", ""), "est": float(v),
                     "on_good": float((v > T) if r["direction"] == "above_good" else (v <= T)),
                     "rel": abs(v - T) / T, "aim": HAND.get(r["sentence"]),
                     "mT": mentions_T(r["sentence"], T)})
print(f"usable rows {len(rows)}   sources {len(set(r['src'] for r in rows))}")
lab = [r for r in rows if r["arm"] == "resampled" and r["aim"] is not None]
print(f"labelled resampled rows {len(lab)}   sources {len(set(r['src'] for r in lab))}")

def paired(sel_a, sel_b, key="on_good", n=4000):
    b = collections.defaultdict(lambda: ([], []))
    for r in lab:
        if sel_a(r): b[r["src"]][0].append(r[key])
        elif sel_b(r): b[r["src"]][1].append(r[key])
    S = [s for s, (x, y) in b.items() if x and y]
    if len(S) < 3: return None
    d = np.array([np.mean(b[s][0]) - np.mean(b[s][1]) for s in S])
    reps = np.array([rng.choice(d, len(d)).mean() for _ in range(n)])
    return float(d.mean()), float(np.percentile(reps, 2.5)), float(np.percentile(reps, 97.5)), len(S), int((d > 0).sum())

print("\n" + "=" * 80)
print("1. DO AIM SENTENCES RESTATE THE THRESHOLD?")
print("=" * 80)
ct = collections.Counter((r["aim"], r["mT"]) for r in lab)
na = ct[(True, True)] + ct[(True, False)]; nn = ct[(False, True)] + ct[(False, False)]
print(f"  states an aim    : restates T in {ct[(True,True)]:4d}/{na:4d} = {ct[(True,True)]/na:.3f}")
print(f"  states no aim    : restates T in {ct[(False,True)]:4d}/{nn:4d} = {ct[(False,True)]/nn:.3f}")
og = {r["src"]: (r["orig_aim"], r["T"]) for r in rows if r["arm"] == "original"}
om = sum(1 for s, T in og.values() if mentions_T(s, T))
print(f"  ORIGINAL aim sentences restating T: {om}/{len(og)} = {om/len(og):.3f}")

print("\n" + "=" * 80)
print("2. SPLITTING THE EFFECT — p(landed on favoured side), paired within source")
print("=" * 80)
for name, a, b in [
    ("aim - no-aim  (headline replication)", lambda r: r["aim"], lambda r: not r["aim"]),
    ("   within sentences that RESTATE T", lambda r: r["aim"] and r["mT"], lambda r: (not r["aim"]) and r["mT"]),
    ("   within sentences that DON'T restate T", lambda r: r["aim"] and not r["mT"], lambda r: (not r["aim"]) and not r["mT"]),
    ("restates T - doesn't  (the new axis)", lambda r: r["mT"], lambda r: not r["mT"]),
    ("   within AIM sentences only", lambda r: r["aim"] and r["mT"], lambda r: r["aim"] and not r["mT"]),
    ("   within NO-AIM sentences only", lambda r: (not r["aim"]) and r["mT"], lambda r: (not r["aim"]) and not r["mT"])]:
    o = paired(a, b)
    print(f"  {name:42s} " + (f"{o[0]:+.3f} [{o[1]:+.3f}, {o[2]:+.3f}]   {o[4]}/{o[3]} sources +" if o else "too few paired sources"))

print("\n" + "=" * 80)
print("3. SAME SPLITS — |estimate - T| / T  (does the sentence pull the number to T?)")
print("=" * 80)
for name, a, b in [
    ("aim - no-aim", lambda r: r["aim"], lambda r: not r["aim"]),
    ("restates T - doesn't", lambda r: r["mT"], lambda r: not r["mT"]),
    ("   within NO-AIM sentences only", lambda r: (not r["aim"]) and r["mT"], lambda r: (not r["aim"]) and not r["mT"])]:
    o = paired(a, b, key="rel")
    print(f"  {name:42s} " + (f"{o[0]:+.3f} [{o[1]:+.3f}, {o[2]:+.3f}]   {o[3]} sources" if o else "too few"))

print("\n" + "=" * 80)
print("4. CELL MEANS (pooled, orientation only)")
print("=" * 80)
print(f"  {'cell':38s} {'n':>5} {'p_fav':>7} {'med|est-T|/T':>13}")
for aim in (True, False):
    for mT in (True, False):
        c = [r for r in lab if r["aim"] == aim and r["mT"] == mT]
        print(f"  aim={str(aim):5s} restates_T={str(mT):5s}              {len(c):5d} "
              f"{np.mean([r['on_good'] for r in c]):7.3f} {np.median([r['rel'] for r in c]):13.3f}")
for arm in ("original", "nosent"):
    c = [r for r in rows if r["arm"] == arm]
    print(f"  {arm:38s} {len(c):5d} {np.mean([r['on_good'] for r in c]):7.3f} "
          f"{np.median([r['rel'] for r in c]):13.3f}")
