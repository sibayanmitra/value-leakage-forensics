"""Fetch the authors' released Qwen3.5-35B-A3B Donation Bet rollouts.

Source: https://github.com/TruthfulAI-research/value_leakage_data
(data submodule of TruthfulAI-research/value_leakage, the code+data release for
Betley, Treutlein et al. 2026, arXiv:2607.14345)

These are the paper's own rollouts for the exact model we are studying, so they
give us (a) the authors' thresholds T per question, (b) a ground-truth target for
our replication, and (c) 2700 CoTs we can analyse without spending any GPU time.
"""
import json, urllib.request, socket, os, sys, time

socket.setdefaulttimeout(120)
REPO = "TruthfulAI-research/value_leakage_data"
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
OUT = "data/authors_qwen35"


def api(u):
    req = urllib.request.Request(u, headers={"User-Agent": "curl/8"})
    return json.load(urllib.request.urlopen(req))


def main():
    tree = api(f"https://api.github.com/repos/{REPO}/git/trees/main?recursive=1")
    files = [x["path"] for x in tree["tree"]
             if x["type"] == "blob" and "cache/qwen3.5-35/" in x["path"]]
    print(f"{len(files)} files to fetch")
    for i, p in enumerate(files, 1):
        dest = os.path.join(OUT, p.split("cache/qwen3.5-35/")[1])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            print(f"  [{i}/{len(files)}] skip {dest}")
            continue
        for attempt in range(3):
            try:
                req = urllib.request.Request(RAW + p, headers={"User-Agent": "curl/8"})
                with urllib.request.urlopen(req) as r, open(dest, "wb") as f:
                    f.write(r.read())
                print(f"  [{i}/{len(files)}] {dest} {os.path.getsize(dest)/1e6:.1f} MB")
                break
            except Exception as e:
                print(f"  retry {attempt+1} {p}: {e}")
                time.sleep(2)
        else:
            print(f"  FAILED {p}", file=sys.stderr)


if __name__ == "__main__":
    main()
