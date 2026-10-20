"""Generate rollouts from an API model through OpenRouter, under a hard spending cap.

Same prompts and output fields as gen_neutral.py (question, direction, threshold, reasoning,
answer, truncated), plus the model id and the call's billed cost. Every call's cost is appended
to logs/openrouter_spend.jsonl; before each call the running total is checked against --budget
plus a worst-case cost for that call, so the cap holds even if a reply runs to max_tokens.
"""
import argparse, json, sys, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secrets_util import get_key

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "logs" / "openrouter_spend.jsonl"
PRICE = {  # USD per token, from openrouter.ai/api/v1/models on 2026-10-19
    "deepseek/deepseek-v4.1-flash-1017": (0.05e-6, 0.15e-6),  # Relace endpoint, pinned below
    "deepseek/deepseek-v4-flash-0731": (0.15e-6, 0.15e-6),
}
PROVIDER = "Relace"
_lock = threading.Lock()


def spent():
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l)["cost"] for l in LEDGER.read_text().splitlines() if l.strip())


def call(model, user, temperature, max_tokens, budget, tag):
    p_in, p_out = PRICE[model]
    worst = 400 * p_in + max_tokens * p_out
    with _lock:
        if spent() + worst > budget:
            raise RuntimeError(f"budget: spent {spent():.4f} + worst {worst:.4f} > {budget}")
    payload = {"model": model, "messages": [{"role": "user", "content": user}],
               "temperature": temperature, "max_tokens": max_tokens,
               "reasoning": {"enabled": True}, "usage": {"include": True}}
    if PROVIDER:  # pin one endpoint: cheapest, and every row served the same way
        payload["provider"] = {"order": [PROVIDER], "allow_fallbacks": False}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {get_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        body = json.load(r)
    u = body.get("usage", {})
    cost = u.get("cost")
    if cost is None:  # fall back to list price if the API omits the billed cost
        cost = u.get("prompt_tokens", 0) * p_in + u.get("completion_tokens", 0) * p_out
    with _lock:
        with open(LEDGER, "a") as f:
            f.write(json.dumps({"t": time.strftime("%FT%T"), "model": model, "tag": tag,
                                "provider": body.get("provider"),
                                "cost": cost, "usage": u}) + "\n")
    ch = body["choices"][0]
    msg = ch["message"]
    return {"reasoning": msg.get("reasoning") or "", "answer": (msg.get("content") or "").strip(),
            "truncated": ch.get("finish_reason") == "length", "finish_reason": ch.get("finish_reason"),
            "completion_tokens": u.get("completion_tokens"), "cost": cost,
            "provider": body.get("provider")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek/deepseek-v4.1-flash-1017")
    ap.add_argument("--condition", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--numerals", default="", help="q=numeral,... shown as {threshold}")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--max-tokens", type=int, default=16000)
    ap.add_argument("--budget", type=float, required=True, help="hard cap on the ledger total, USD")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    qs = yaml.safe_load(open(ROOT / "configs/questions.yaml"))
    tpl = yaml.safe_load(open(ROOT / "configs/prompts.yaml"))
    nums = {k: int(v) for k, v in (kv.split("=") for kv in a.numerals.split(",") if kv)}
    jobs = []
    for q in a.questions.split(","):
        shown = nums.get(q, 0)
        user = tpl[a.condition].format(question=qs[q], threshold=f"{shown:,}")
        jobs += [(q, shown, user)] * a.n

    out = open(a.out, "a")
    def run(job):
        q, shown, user = job
        r = call(a.model, user, a.temperature, a.max_tokens, a.budget, f"{a.condition}:{q}")
        row = {"question": q, "direction": a.condition, "threshold": float(shown),
               "model": a.model, "temperature": a.temperature, **r}
        with _lock:
            out.write(json.dumps(row) + "\n"); out.flush()
        return r
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(lambda j: _safe(run, j), jobs))
    ok = [r for r in res if isinstance(r, dict)]
    print(f"{len(ok)}/{len(jobs)} rows | {time.time()-t0:.0f}s | run cost "
          f"{sum(r['cost'] for r in ok):.4f} | ledger total {spent():.4f}", flush=True)
    for r in res:
        if not isinstance(r, dict):
            print("FAILED:", r)


def _safe(f, j):
    try:
        return f(j)
    except Exception as e:  # noqa: BLE001 - report, keep other rows
        return f"{type(e).__name__}: {str(e)[:200]}"


if __name__ == "__main__":
    main()
