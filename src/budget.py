"""Real OpenRouter balance, and a hard gate for any paid run.

IMPORTANT: /auth/key's `limit_remaining` is the KEY'S MONTHLY RATE LIMIT, not money.
Reading it as a balance once led to a $36 figure when only $5.56 actually remained.
The real balance is /credits -> total_credits - total_usage. Use balance() only.
"""
import json, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secrets_util import get_key

# Never let automated spending drive the balance below this.
RESERVE_USD = 2.50


def balance():
    req = urllib.request.Request("https://openrouter.ai/api/v1/credits",
                                 headers={"Authorization": f"Bearer {get_key()}"})
    d = json.load(urllib.request.urlopen(req, timeout=40))["data"]
    return d["total_credits"] - d["total_usage"]


def require(est_cost, label=""):
    """Abort unless est_cost fits with RESERVE_USD left over."""
    bal = balance()
    print(f"  balance ${bal:.2f} | est. cost ${est_cost:.2f} | reserve ${RESERVE_USD:.2f}",
          flush=True)
    if est_cost > bal - RESERVE_USD:
        print(f"ABORT {label}: would leave ${bal - est_cost:.2f}, "
              f"below the ${RESERVE_USD:.2f} reserve.")
        sys.exit(1)
    return bal


if __name__ == "__main__":
    print(f"balance: ${balance():.2f}")
