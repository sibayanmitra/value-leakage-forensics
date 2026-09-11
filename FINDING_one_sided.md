# The counter-intuitive finding: value leakage in this task is **one-sided**

Status: **provisional — one confound is still being tested** (see §4). Written 2026-09-06.

---

## 1. What everyone assumes, including us until now

The Donation Bet result is usually stated as: *the model shifts its estimate toward the
"good side" of the threshold.* That phrasing implies a symmetric mechanism — pushed up when up
is good, pushed down when down is good. Our own E1 write-up said exactly this.

## 2. What the control shows instead

Adding a condition the paper does not have — `neutral_T`, where the threshold is stated but
**nothing depends on which side the estimate lands** — separates two things that are otherwise
inseparable:

- **framing**: does merely naming a threshold move estimates?
- **valence**: does the good/bad label move them further?

Fraction of final answers **above T**, equal weight per question:

| condition | fraction above T | what it is |
|---|---|---|
| `baseline` (no threshold at all) | **0.503** | sanity check: T *is* the baseline median, so 0.5 is correct |
| `neutral_T` (threshold, no valence) | **0.702** | framing alone |
| `above_good` (good if > T) | **0.709** | framing + valence |
| `below_good` (good if <= T) | **0.094** | framing + valence |

**Merely mentioning the threshold moves estimates up by ~0.2. Adding "and above is good" moves
them a further 0.007 — i.e. nothing.**

Decomposition against the framing baseline:

| condition | expected under pure framing | observed | deviation |
|---|---|---|---|
| p_fav(above_good) | 0.702 | 0.709 | **+0.007** |
| p_fav(below_good) | 0.298 | 0.906 | **+0.608** |

So the **entire** measured bias of +0.615 comes from `below_good`. When the favoured side is
*up*, the model was already going up for reasons unrelated to the donation.

## 3. Why this matters

- The symmetric bias metric is **still valid**: a pure framing shift cancels in
  `p_below + p_above − 1` (expected bias under pure framing = exactly 0.000). So the headline
  number is not wrong.
- But the **mechanism claim** was wrong. It is not "push toward the favoured side". It is
  **"push down when down is favoured"** — plus a valence-independent upward pull from the
  threshold's presence.
- This reframes what the model is doing. A plausible reading: naming a large specific number
  anchors the model upward (or makes it reluctant to look like it is lowballing), and the
  donation valence only bites when it must fight that pull. That is a *different* story from
  motivated reasoning toward a preferred outcome, and it is only visible with the neutral control.

## 4. Sanity checks

**Passed:**
- `baseline` = 0.503, exactly the 0.5 it must be by construction (T is defined as the baseline
  median). If our pipeline were broken this would not land on 0.5.
- Permutation null: shuffling direction labels gives bias +0.004 [−0.080, +0.088] over 200
  shuffles; the real +0.623 is far outside.
- Estimate-order integrity: 0/444 traces have first-estimate offset later than last.

**Known problems, both weakening the finding:**

1. **Truncation biases `neutral_T` upward.** 37.8% of neutral_T rollouts hit the token cap and
   were dropped. Truncated rollouts are longer (37.7k vs 30.3k chars) and
   `corr(reasoning length, above-T) = −0.150`; the kept shorter half sits at 0.732 vs 0.679 for
   the longer half. Including the truncated ones would likely put neutral_T nearer **0.65–0.68**,
   not 0.702. The qualitative conclusion survives (still far above baseline 0.503, still close to
   above_good 0.709) but the exact number is inflated.

2. **A generation confound, still under test.** `neutral_T` is **our** local FP8 generation;
   `baseline`, `above_good`, `below_good` are the **authors'** API rollouts on unquantised
   weights. If our setup simply produces higher estimates, that alone manufactures the +0.2
   "framing" effect and the finding collapses. **We are currently generating `baseline` on our
   own setup to test exactly this.** Until that lands, treat §2 as provisional.

3. Per-question n is small and variable after truncation (windowdays n=3, maiden n=6, zills
   n=20) and the per-question spread is wide (0.33 to 1.00).

## 5. What made it visible

Nothing clever — a control the original work did not run. `neutral_T` costs one extra prompt
condition and it is the only thing that separates "the number in the prompt moved the estimate"
from "the value moved the estimate". Every experiment before it (E0, E1, E1c, E1d, E2) was
measuring the sum of the two and attributing all of it to valence.

The general lesson for the write-up: the symmetric bias metric was *designed* to cancel
anchoring, and it does — which made it easy to believe anchoring had been handled. It cancels
anchoring in the **aggregate statistic** while leaving the **mechanism story** wrong.
