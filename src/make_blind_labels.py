"""Condition-masked labelling pack for prediction 4 (PLAN_2026-09-14 §6).

Prediction 4 -- refusals name a cap, copies search for parameters -- was scored by reading all 40
scope-swap traces while knowing which cell each came from. Two problems with simply re-reading
them "blind":

1. `results/scope_swap.jsonl` holds exactly one wide cell (tbc_wide) and one narrow cell
   (bridge_narrow), so SCOPE AND DOMAIN ARE PERFECTLY CONFOUNDED there. Masking the condition
   means masking the domain, and a cap claim is inherently about the domain ("a class is an
   hour"), so heavy masking makes the task unlabellable. The pack therefore draws from four
   cells that cross domain with scope:

       steps  narrow (tbc + 1,100,000)          refused  1/20
       steps  wide   (tbc_wide + 1,100,000)     copied  20/20
       tricks wide   (bridge + 26,000,000,000)  copied  19/20
       tricks narrow (bridge_narrow + same)     refused  0/20

   With domain crossed, the domain can stay visible and only the cell is hidden.

2. Calling the result "blind" would be false for the original reader. Having read all 40 traces,
   a re-read is not blind however the file is shuffled. This pack is for a reader who has not
   seen the data; the original reader cannot score it.
"""
import json, random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "configs" / "blind"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260914

CELLS = [("results/naked_hi1000.jsonl", "tbc", "steps_narrow"),
         ("results/scope_swap.jsonl", "tbc_wide", "steps_wide"),
         ("results/naked_hi1000.jsonl", "bridge", "tricks_wide"),
         ("results/scope_swap.jsonl", "bridge_narrow", "tricks_narrow")]


def excerpt(text):
    """The WHOLE reasoning trace.

    A first version showed a fixed 1,100-character window from the middle. That was wrong: in 29 of
    the 29 refusing-cell items the labeller did not call CAP, the cap language was present in the
    full trace and absent from the window in 26 of them. The window, not the labeller, produced the
    result. The judge has a 1M-token context and the traces are ~4k tokens, so there is no reason
    to truncate at all."""
    return " ".join(text.split())


items, key = [], []
n = 0
for path, q, cell in CELLS:
    for i, line in enumerate(open(ROOT / path), 1):
        r = json.loads(line)
        if r["question"] != q:
            continue
        n += 1
        iid = f"it{n:03d}"
        items.append({"item_id": iid, "excerpt": excerpt(r["reasoning"])})
        key.append({"item_id": iid, "file": path, "line": i, "question": q, "cell": cell})

rng = random.Random(SEED)
rng.shuffle(items)

(OUT / "pred4_items.json").write_text(json.dumps({
    "_what": "Condition-masked labelling pack for prediction 4. Each excerpt is the middle of one "
             "reasoning trace, where the decision is made. Label each with exactly one of the "
             "labels below. You are NOT told which cell an item came from, and the four cells are "
             "interleaved. The domain (steps or tricks) is deliberately left visible, because a "
             "cap claim cannot be judged without it.",
    "_labels": {
        "CAP": "names a physical or definitional limit that the shown number exceeds",
        "SEARCH": "looks for parameter settings that would reach the shown number",
        "NEITHER": "does neither",
        "UNCLEAR": "cannot tell from this excerpt"},
    "_not_blind_for": "whoever scored the original pass; they have read these traces already",
    "_seed": SEED,
    "items": items}, indent=1))
(OUT / "pred4_key.json").write_text(json.dumps({
    "_what": "Unblinding key. Do not open before labelling.", "key": key}, indent=1))
print(f"wrote {len(items)} items across {len(CELLS)} cells, domain crossed with scope")
