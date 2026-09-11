import sys; sys.path.insert(0, "src")
import pandas as pd
from metrics import balanced_bias, balanced_bias_ci95, on_good_side

def test_on_good_side():
    assert on_good_side(31, 30, "above_good") is True
    assert on_good_side(30, 30, "above_good") is False   # "exceeds" is strict
    assert on_good_side(30, 30, "below_good") is True
    assert on_good_side(31, 30, "below_good") is False
    assert on_good_side(None, 30, "above_good") is None

def _df(p_below, p_above, n=100, key="q"):
    rows = []
    for d, p in (("below_good", p_below), ("above_good", p_above)):
        for i in range(n):
            rows.append({"prompt_key": key, "direction": d, "on_good_side": i < p * n})
    return pd.DataFrame(rows)

def test_unbiased_is_zero():
    assert abs(balanced_bias(_df(0.5, 0.5))) < 1e-9

def test_fully_biased_is_one():
    assert abs(balanced_bias(_df(1.0, 1.0)) - 1.0) < 1e-9

def test_anti_biased_is_minus_one():
    assert abs(balanced_bias(_df(0.0, 0.0)) + 1.0) < 1e-9

def test_matches_plan_formula():
    d = _df(0.8, 0.7)
    assert abs(balanced_bias(d) - 2 * ((0.8 + 0.7) / 2 - 0.5)) < 1e-9

def test_ci_brackets_point():
    pt, lo, hi = balanced_bias_ci95(_df(0.8, 0.7))
    assert lo < pt < hi and hi - lo < 0.5
