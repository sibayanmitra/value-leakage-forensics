"""Load API keys from disk at call time.

The key is never printed, logged, or written into results. Nothing in this repo
should ever echo the value - only ever report whether a key was FOUND.
"""
import os
from pathlib import Path

# Searched in order; first hit wins.
ENV_FILES = [
    Path(__file__).resolve().parent.parent / ".env",
    Path.home() / "CAISc" / ".env",
    Path.home() / ".env",
]


def _parse_env_file(path):
    out = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def get_key(name="OPENROUTER_API_KEY"):
    """Return the key, or raise with a message that does not leak any value."""
    if os.environ.get(name):
        return os.environ[name]
    for p in ENV_FILES:
        if p.exists():
            v = _parse_env_file(p).get(name)
            if v:
                return v
    raise RuntimeError(
        f"{name} not found. Looked in $%s and: %s"
        % (name, ", ".join(str(p) for p in ENV_FILES))
    )


def report():
    """Print which key names are available and where - never the values."""
    for p in ENV_FILES:
        if not p.exists():
            print(f"  {p}  (absent)")
            continue
        keys = sorted(_parse_env_file(p))
        print(f"  {p}  -> {len(keys)} vars: {', '.join(keys) if keys else '(none)'}")


if __name__ == "__main__":
    report()
