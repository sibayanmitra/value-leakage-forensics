# Pre-registration: where does the bridge question break? (2026-09-14, written before the run)

## Why

`figures/fig11_elasticity.png` shows steps and giraffes breaking between 6.7 and 8.4 spreads from
the model's own answers. **Bridge never breaks in anything tested**: its largest numeral,
26,000,000,000, is 1,507× the threshold and still copied 19/20, because bridge's own answers are so
spread out (sd 0.62, one spread = a factor of 4.2) that ×1,507 is only **5.0** spreads away.

So the account is untested at the high end for the one question with the widest spread. If it is
right, bridge should break too — just at an enormous numeral. If bridge instead breaks at roughly the
same *absolute* absurdity as the other questions, then spread is not what transfers and the collapse
in that figure is a coincidence of three questions.

## Design

`naked_number` on `bridge`, numeral alone on the last line, nothing else changed. Same model and
settings as every other cell: Qwen3.5-35B-A3B FP8, temperature 1.0, top-p 1.0, 20 answers per cell.
Baseline centre 10^7.290 = 19,503,856; spread 0.619.

| arm | numeral | z | × the bet's threshold |
|---|---|---|---|
| A | 210,000,000,000 | 6.5 | ×8,077 |
| B | 1,700,000,000,000 | 8.0 | ×65,385 |
| C | 15,000,000,000,000 | 9.5 | ×576,923 |
| D | 520,000,000,000,000 | 12.0 | ×20,000,000 |

## Predictions

1. **A (z = 6.5) is copied ≥ 12/20.** It sits below the break band, and bridge copies 19/20 at z = 5.
2. **C (z = 9.5) is copied ≤ 6/20.**
3. **D (z = 12.0) is copied ≤ 3/20.**
4. **The ordering is monotone: A ≥ B ≥ C ≥ D.**
5. B (z = 8.0) sits inside the band and no prediction is made for it; it is there to locate the break.

## What would falsify the account

If **C and D are still copied ≥ 12/20**, then bridge does not break where its own spread says it
should, the collapse in `fig11_elasticity.png` does not generalise, and the claim that distance in a
question's own units is what gates copying must be withdrawn for the high end.

The competing account — that refusal tracks *absolute* absurdity rather than distance in the
question's own units — is already weak, because bridge copies 26,000,000,000 at 19/20 while steps
refuses 33,000. Prediction 1 tests it again directly: 210 billion is only 8× larger than a numeral
bridge already copies almost every time.

## Note on a smaller point

Bridge's spread is the least robust of the three: its sd (0.62) is inflated by three high answers
(117M, 208M, 917M) against a median of 17,250,000. MAD gives 0.60, so the two agree here, but the
numerals above were chosen from the sd and a reader should know the choice depends on it.

---

## Addendum, 14:45, before any of the four arms had written a row

The question came up of whether to drop the largest baseline answer (917,000,000) as an outlier.
**The answer is no, and the reason is not a judgement call — it is what the estimators say.**

Bridge's baseline scale, on the log10 answers, estimated six ways, with bootstrap 95% intervals
(4,000 resamples):

| estimator | scale | bootstrap 95% CI | z of 26,000,000,000 (copied 19/20) |
|---|---|---|---|
| classical sd | 0.62 | [0.36, 0.82] | 5.0 |
| MAD × 1.4826 | 0.60 | [0.21, 0.91] | 5.2 |
| IQR ÷ 1.349 | 0.52 | [0.26, 0.94] | 6.1 |
| 10% trimmed sd | 0.46 | [0.28, 0.77] | 6.8 |
| 10% winsorized sd | 0.52 | [0.31, 0.88] | 6.0 |
| **Qn (Rousseeuw–Croux 1993)** | **0.71** | [0.27, 0.92] | **4.4** |

Three things follow.

**1. The outlier is not inflating the estimate.** Qn — 50% breakdown, 82% efficiency at the
Gaussian, the standard robust scale estimator — returns **0.71**, *higher* than the classical 0.62.
MAD returns 0.60, essentially the same as sd. An estimator built to ignore tails does not find
bridge narrower. Bridge is wide because its bulk is wide: excluding the top three answers entirely,
the remaining seventeen still run from 2,500,000 to 45,000,000, a factor of 18.

**2. Deleting the point would not be a robustness check, it would be a choice with a direction.**
Dropping 917M alone takes sd from 0.62 to 0.49; dropping the top three takes it to 0.36, which would
put the already-published ×1000 cell at z = 9.2 — past the break band, while it is copied 19/20.
So the deletion that "cleans" the data is the one that breaks the account. That is exactly the
situation in which post-hoc exclusion should not be done.

**3. The real problem is n = 20, not the outlier.** Every interval above is enormous: the classical
sd is 0.62 but the data are consistent with anything from 0.36 to 0.82. No estimator fixes that;
only more samples do. At n = 60 these intervals would be roughly half as wide.

**Adopted procedure, fixed here before results:** keep every answer, report the classical sd as the
headline with Qn and MAD beside it as a sensitivity row, and treat any conclusion that flips between
them as unsupported. On the present data the conclusion does not flip for five of the six estimators:
26,000,000,000 sits below the 6.7–8.4 break band and is copied 19/20. Under the 10% trimmed estimator
it sits at 6.8, just inside the band, which is a genuine tension and is recorded as one.

**This also makes arm A sharper than intended.** 210,000,000,000 is at z = 6.5 under the classical
sd and z = 8.4 if the outlier is dropped. So arm A now discriminates between the two ways of
estimating the spread: copying at ≥ 12/20 favours keeping the full sample, refusing favours the
trimmed estimate.
