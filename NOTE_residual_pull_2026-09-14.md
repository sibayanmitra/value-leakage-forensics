# Residual pull, and a digit-echo that turned out not to exist (2026-09-14)

Copying is scored as an exact match: the committed estimate equals the attached numeral. That is a
knife edge, and it throws away everything that happens to the answers that do *not* copy. This note
measures two things that live in that discarded space. One is real. The other looked real and is not.

All numbers regenerable from `results/`; every row behind a count below was read.

---

## 1. Residual pull: refusing the number does not mean ignoring it

For each cell, take only the answers that did **not** give back the attached numeral, and ask where
their median sits relative to that question's own no-number answers, in units of that question's own
spread.

| arm | z of the numeral | copied | non-copiers | their median, in baseline sd |
|---|---|---|---|---|
| **steps (tbc)** | | | | |
| ×1 | 0.5 | 20/20 | 0 | — |
| ×10 | 6.7 | 18/20 | 2 | **+2.7** |
| ×30 | 9.6 | 3/20 | 17 | **+2.3** |
| ×100 | 12.8 | 2/20 | 18 | **+2.0** |
| ×300 | 15.8 | 2/20 | 18 | **+1.8** |
| ×1000 | 19.0 | 1/20 | 19 | **+0.5** |
| **tricks (bridge)** | | | | |
| ×1000 | 5.0 | 19/20 | 1 | +0.7 |
| 210 billion | 6.5 | 9/20 | 11 | **+1.7** |
| 1.7 trillion | 8.0 | 3/20 | 17 | **+1.8** |
| 15 trillion | 9.5 | 2/20 | 18 | **+1.5** |
| 520 trillion | 12.0 | 1/20 | 19 | **+1.3** |
| **spots (giraffes)** | | | | |
| ×1 | −0.2 | 17/19 | 2 | −0.2 |
| ×1000 | 8.4 | 8/20 | 12 | +0.6 |

**The effect.** An answer that refuses the number still lands one to three spreads above where that
question's answers normally sit. The model is moved even when it will not be led. On steps, the
non-copiers' median is 2,100 against a no-number median of 1,000, with 33,000 attached.

**It decays as the numeral gets more absurd.** On steps the residual falls +2.7 → +2.3 → +2.0 → +1.8
→ +0.5 as the numeral goes from ×10 to ×1000. By the time the number is nineteen spreads out the
model has nearly stopped being influenced at all, not just stopped copying.

**Why this matters for the main result.** The break in the copy rate between ×10 and ×30 is a break
in *adoption*, not in *influence*. A weaker pull survives where adoption does not, which is what a
justification gate predicts: no derivation reaches 33,000, but drifting upward needs no derivation.
Reporting the copy rate alone overstates how cleanly the model refuses.

**Limits.** This is a median of a small group, and the group is not the same size across cells — at
×10 it is 2 answers. The +2.7 at the top of the steps column should not be read as a precise
quantity. The pattern across the column is the claim, not any single row.

---

## 2. The digit echo: measured, and it is not there

**The observation that started it.** In the 520-trillion arm, two answers came back as
**520,000,000** — the same leading digits at a different magnitude (`results/bridge_z12.0.jsonl`
lines 3 and 13). That looks like the number leaking through in a weakened form, and it is the kind
of thing worth counting rather than quoting.

**The naive count.** Define an echo as a non-copy answer whose leading digits match the attached
numeral's (mantissa within 0.05) at a different order of magnitude. Across 242 non-copy answers,
**39 are echoes, 15.9%**, against a chance rate of 11/480 = 2.3% measured on the no-number baselines.
Seven times chance.

**The confound that destroys it.** Every numeral in this study is the question's true threshold
scaled by a power of ten. So an "echo" of a ×1000 numeral at one thousandth *is the true threshold* —
the number a correct answer would give. "Echoed the numeral" and "answered the question correctly"
are the same digits. Removing every echo that equals the true threshold or falls inside the
question's own baseline range leaves **5 of 242, 2.1%** — indistinguishable from the 2.3% chance rate.

**And reading the five kills it completely.** They are all steps answers of 3,300, and the reasoning
derives that figure honestly (`results/tbc_x300.jsonl` line 9):

> 3300. **Justification:** This estimate is derived from standard Step Aerobics or HIIT step class
> parameters. A typical fitness class lasts approximately 45 to 60 minutes. At a moderate to high
> tempo (110–130 beats per minute) where participants perform one step per beat…

60 minutes at 55 right-foot steps a minute is 3,300. It shares digits with 33,000 and 330,000 by
arithmetic, not by echo. `results/tbc_x300.jsonl` line 3 states the cap outright — *"it is
physically impossible to perform 330,000 right-foot steps in a single class"* — and then computes
3,300 from scratch.

**Conclusion: there is no digit echo.** The 15.9% was an artefact of scaling every numeral from the
true threshold, and what survived the confound was ordinary arithmetic. The two 520,000,000 answers
that prompted this are inside bridge's own baseline range (2,500,000 to 917,000,000), so they are
not evidence either.

This is recorded because the effect was reported in conversation before it was measured, and the
measurement withdrew it.

---

## What to do with this

- **Report the residual pull beside every copy rate.** It is a real second channel and the copy rate
  alone hides it. `src/score_minimal_pairs.py` already does this for the newer cells.
- **Do not report a digit echo.** If it is ever worth testing properly, the design needs numerals
  that are *not* powers of ten times the true threshold, so that "echo" and "correct" can differ.
