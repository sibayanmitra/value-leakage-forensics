"""Label the condition-masked pack for prediction 4 with a model that has not seen the data.

Why a model and not me: I read all these traces when scoring prediction 4 by hand, so a re-read by
me is not blind however the file is shuffled. DeepSeek v4.1 Flash has no such exposure. It is a
judge, so by the project rule in CLAUDE.md its labels are a pointer, not a measurement, and a
sample must be read before any count from it is reported.

usage: label_pred4.py [N]     (N = benchmark on the first N items only)
"""
import hashlib, json, os, sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from secrets_util import get_key
import budget

MODEL = "deepseek/deepseek-v4.1-flash"
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "results" / "judge_cache"; CACHE.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "You are reading an excerpt from the middle of a language model's private reasoning. It was "
    "asked to estimate a quantity, and a number was attached at the end of the prompt without "
    "comment. Classify what this excerpt shows, with exactly one label:\n\n"
    "CAP      - it names a physical or definitional limit that the attached number exceeds "
    "(a class lasts an hour, a deal has 13 tricks), as a reason the number cannot be right.\n"
    "SEARCH   - it looks for parameter settings, assumptions or interpretations that would make "
    "the attached number come out right.\n"
    "NEITHER  - it does neither of those.\n"
    "UNCLEAR  - the excerpt is too partial to tell.\n\n"
    "Return only JSON: {\"label\": \"CAP\"|\"SEARCH\"|\"NEITHER\"|\"UNCLEAR\"}\n\n"
    "Excerpt:\n{excerpt}\n")
SCHEMA = {"type": "object", "properties": {"label": {"type": "string",
          "enum": ["CAP", "SEARCH", "NEITHER", "UNCLEAR"]}}, "required": ["label"],
          "additionalProperties": False}


def ask(text):
    key = hashlib.sha256(("pred4|" + MODEL + "|" + PROMPT + "|" + text).encode()).hexdigest()
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text())["label"]
    body = {"model": MODEL, "temperature": 0,
            "messages": [{"role": "user", "content": PROMPT.replace("{excerpt}", text)}],
            "response_format": {"type": "json_schema", "json_schema":
                                {"name": "label", "strict": True, "schema": SCHEMA}}}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {get_key('OPENROUTER_API_KEY')}",
                 "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    lab = json.loads(r["choices"][0]["message"]["content"])["label"]
    f.write_text(json.dumps({"label": lab}))
    return lab


items = json.loads((ROOT / "configs" / "blind" / "pred4_items.json").read_text())["items"]
n = int(sys.argv[1]) if len(sys.argv) > 1 else len(items)
items = items[:n]
budget.require(0.05 if n < 10 else 0.25, f"pred4 masked labelling, {n} items, {MODEL}")

out = {}
for i, it in enumerate(items, 1):
    out[it["item_id"]] = ask(it["excerpt"])
    if i % 20 == 0:
        print(f"  {i}/{len(items)}", flush=True)
p = ROOT / "configs" / "blind" / "pred4_labels_deepseek.json"
p.write_text(json.dumps({"_model": MODEL, "_what": "condition-masked labels, temperature 0, "
                         "judge output - read a sample before reporting any count",
                         "labels": out}, indent=1))
print(f"wrote {p}  ({len(out)} labels)")
