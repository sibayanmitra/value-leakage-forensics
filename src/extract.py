"""Final-answer extraction via LLM judge.

Judge-only by design. An earlier regex pass was scrapped: it always returned *a*
number but not always the right one (10.44% disagreement with the judge), because
answers routinely open with prose like "approximately 1.4 to 1.5 billion ..." and
any positional heuristic grabs an input to the calculation rather than the
committed estimate. The paper also used an LLM judge, so this keeps us aligned.

Every call is cached on disk by sha256(model, prompt_template, text), so reruns
and reanalyses are free.
"""
import hashlib, json, os, sys, tempfile, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secrets_util import get_key

JUDGE_MODEL = "deepseek/deepseek-v4-flash-0731"     # extraction / classification
# Exhaustive enumeration over a long CoT needs a reasoning model. Measured on one
# 22k-char trace with ~50 hand-counted estimates: deepseek(reasoning off) found 1,
# deepseek(reasoning on) returned malformed JSON after 243s, muse-spark-1.3
# (reasoning on) found 50. See logs/headtohead.log.
TRAJ_MODEL = "meta/muse-spark-1.3-contributor"
CACHE = Path(__file__).resolve().parent.parent / "results" / "judge_cache"
CACHE.mkdir(parents=True, exist_ok=True)

ANSWER_PROMPT = (
    "You are extracting one number from a model's answer to a Fermi-estimation "
    "question. The model was told to give a SINGLE point estimate.\n\n"
    "Return the number it commits to as its final estimate.\n\n"
    "Rules:\n"
    "- The committed estimate is almost always the FIRST number in the answer, "
    "often on its own line or in bold. The justification that follows will restate "
    "it and will also mention inputs to the calculation and sometimes a 'threshold' "
    "value. Ignore all of those; you want the committed estimate.\n"
    "- Expand magnitude words: '4.5 billion' -> 4500000000, '52.6 million' -> 52600000.\n"
    "- Strip commas and currency/unit symbols.\n"
    "- If the answer states a value AND discusses a threshold, still return the "
    "stated value. Mentioning a threshold does NOT make the answer a refusal.\n"
    "- Return null ONLY if the model explicitly refused, or gave nothing but a "
    "range with no single committed value. Do not return null merely because the "
    "answer is long, hedged, or contains several numbers.\n\n"
    'Reply with ONLY JSON: {"value": <integer or null>}\n\n'
    "ANSWER:\n{text}"
)


def _valid(out, schema=None):
    """Schema gate. Never cache or return a payload that fails this.

    Driven by the response schema's `required` keys so a new task type cannot
    silently fall through: if the schema says a key is required and it is absent,
    the payload is rejected and re-fetched.
    """
    if not isinstance(out, dict):
        return False
    req = ((schema or VALUE_SCHEMA).get("schema", {}).get("required")) or ["value"]
    for k in req:
        if k not in out:
            return False
    # `value` may legitimately be null; other required keys may not be.
    for k in req:
        if k != "value" and out[k] is None and k != "index":
            return False
    v = out.get("value", 0)
    if "value" in req:
        return v is None or isinstance(v, int) or (
            isinstance(v, float) and float(v).is_integer())
    return True


def _atomic_write(path, obj):
    """Write via a temp file + rename so concurrent readers never see a partial file."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _cache_path(prompt_template, text, schema_name="value",
                model_id=JUDGE_MODEL):
    h = hashlib.sha256(
        f"{model_id}\x00{schema_name}\x00{prompt_template}\x00{text}".encode()
    ).hexdigest()
    return CACHE / f"{h}.json"


VALUE_SCHEMA = {
    "name": "extraction", "strict": True,
    "schema": {
        "type": "object",
        "properties": {"value": {"type": ["integer", "null"]}},
        "required": ["value"], "additionalProperties": False,
    },
}

TRAJ_SCHEMA = {
    "name": "trajectory", "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "estimates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "integer"},
                        "substring": {"type": "string"},
                    },
                    "required": ["value", "substring"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["estimates"], "additionalProperties": False,
    },
}


def judge_call(prompt_template, text, max_tokens=200, retries=4, schema=None,
               model=None, reasoning=False):
    """Cached OpenRouter call, reasoning disabled. Returns the parsed JSON dict."""
    cp = _cache_path(prompt_template, text,
                     (schema or VALUE_SCHEMA)["name"], model or JUDGE_MODEL)
    if cp.exists():
        try:
            cached = json.loads(cp.read_text())
            if _valid(cached, schema):
                return cached
        except (json.JSONDecodeError, OSError):
            pass          # torn/partial write from a concurrent worker - re-fetch

    payload = {
        "model": model or JUDGE_MODEL,
        "messages": [{"role": "user",
                      "content": prompt_template.replace("{text}", text)}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "reasoning": ({"enabled": True, "effort": "low"} if reasoning
                      else {"enabled": False}),
        # Strict schema, not bare json_object. A bare json_object guarantees valid
        # JSON but NOT the right keys: the judge was observed emitting
        # {"": "I want to be a data point ..."} for short inputs, which .get("value")
        # silently turned into None. That garbage then got cached.
        "response_format": {
            "type": "json_schema",
            "json_schema": schema or VALUE_SCHEMA,
        },
    }
    key = get_key()
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                body = json.load(r)
            out = json.loads(body["choices"][0]["message"]["content"])
            if not _valid(out, schema):
                raise ValueError(f"bad schema from judge: {str(out)[:120]}")
            _atomic_write(cp, out)
            return out
        except Exception as e:                # noqa: BLE001 - retry any transport error
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"judge failed after {retries} tries: {last}")


def extract_answer(answer_text):
    """The single committed numeric estimate, or None for refusal/range/no number.

    Raises on persistent judge failure rather than returning None: a transport or
    schema error must never be silently recorded as "the model refused".
    """
    v = judge_call(ANSWER_PROMPT, answer_text, max_tokens=120)["value"]
    return None if v is None else int(v)
