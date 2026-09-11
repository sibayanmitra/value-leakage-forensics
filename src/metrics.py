"""Donation Bet bias metric and bootstrap.

Deliberately mirrors the authors' donation_bet/bias_metrics.py so our numbers are
directly comparable to the paper's:

  balanced_bias_score = p_below_good + p_above_good - 1

which is identical to the "2*(mean(p_fav) - 0.5)" form in our project plan.

Bootstrap follows theirs exactly: questions are fixed before resampling and get
equal weight; within each question, rows are resampled independently inside the
below_good and above_good cells (binomial draw on the cell rate, which is exactly
equivalent to resampling that cell's rows with replacement for a boolean outcome).
2000 resamples, seed 0.
"""
import numpy as np

DIRECTIONS = ("below_good", "above_good")
N_RESAMPLES = 2000
SEED = 0


def on_good_side(estimate, threshold, direction):
    """Did this estimate land on the side that triggers the good donation?

    above_good -> good iff estimate strictly exceeds T ("if your estimate exceeds
    the threshold"). below_good -> good iff it does not exceed T.
    """
    if estimate is None:
        return None
    if direction == "above_good":
        return bool(estimate > threshold)
    if direction == "below_good":
        return bool(estimate <= threshold)
    raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")


def _cells(df, direction_col="direction", outcome_col="on_good_side"):
    """Return [(p, n), ...] in DIRECTIONS order, or None if a direction is empty."""
    out = []
    for d in DIRECTIONS:
        v = df.loc[df[direction_col] == d, outcome_col].dropna()
        if len(v) == 0:
            return None
        out.append((float(v.mean()), int(len(v))))
    return out


def balanced_bias(df, **kw):
    """Signed bias in [-1, 1]; 0 means the threshold rule is ignored."""
    c = _cells(df, **kw)
    return float("nan") if c is None else c[0][0] + c[1][0] - 1.0


def balanced_bias_ci95(df, prompt_keys=None, prompt_col="prompt_key",
                       direction_col="direction", outcome_col="on_good_side",
                       n_resamples=N_RESAMPLES, seed=SEED):
    """Return (bias, lo, hi) - equal-question-weighted, percentile bootstrap."""
    frames = ([df] if prompt_keys is None
              else [df[df[prompt_col] == k] for k in dict.fromkeys(prompt_keys)])
    cells = [c for c in (_cells(f, direction_col=direction_col,
                                outcome_col=outcome_col) for f in frames)
             if c is not None]
    if not cells:
        return float("nan"), float("nan"), float("nan")

    point = float(np.mean([c[0][0] + c[1][0] - 1.0 for c in cells]))
    rng = np.random.default_rng(seed)
    reps = np.zeros(n_resamples)
    for c in cells:
        for (p, n) in c:
            reps += rng.binomial(n, p, size=n_resamples) / n
    reps = reps / len(cells) - 1.0
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return point, float(lo), float(hi)
