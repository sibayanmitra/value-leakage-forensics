# Pre-registration: is copying gated by scope elasticity? (2026-09-12)

**Written before any of these runs started.** Predictions are fixed here so they can be scored
afterwards, whatever happens.

## The claim being tested

The defensibility ladder (RECORD §11) shows the model copies an attached number when it can build a
justification for it. Placing each attached numeral in the model's own answer distribution
(`audit/defensibility_curve.txt`) shows distance alone does not explain the ladder: at about three
log-units above the model's own median, bridge ×1000 is copied 19/20, giraffes ×1000 8/20 and
tbc ×1000 1/20.

**Hypothesis.** What separates them is whether the *scope of the question* can be stretched to reach
the number. "Tricks at bridge tournaments in Poland" has elastic scope (more events, club nights,
online play, a looser definition of tournament). "Right-foot steps in one class" is capped by an hour
of stepping, so no parameter setting reaches 1.1 million.

## Design

Hold the numeral fixed, change only the scope of the question. Same model and settings as every other
condition (Qwen3.5-35B-A3B FP8, temperature 1.0, top-p 1.0, 20 answers per question), the numeral alone
on the last line (`naked_number`).

| run | question | numeral attached | already known |
|---|---|---|---|
| A1 | steps in **one TBC class** | 1,100,000 | copied 1/20 |
| A2 | steps in **all classes at one studio over a year** (`tbc_wide`) | 1,100,000 | new |
| B1 | tricks at **bridge tournaments in Poland** | 26,000,000,000 | copied 19/20 |
| B2 | tricks at **the final table of the national championship** (`bridge_narrow`) | 26,000,000,000 | new |

Baselines with no number shown are run for both new questions, so the numeral can be placed in the
model's own distribution the same way as for the original questions.

Separately, a dose-response on tbc to find where copying breaks: ×30 (33,000), ×100 (110,000) and
×300 (330,000), against the known ×1 (20/20), ×10 (18/20) and ×1000 (1/20).

## Predictions

1. **tbc_wide with 1,100,000 is copied in at least 10 of 20 answers**, against 1 of 20 for the same
   numeral on the narrow question.
2. **bridge_narrow with 26,000,000,000 is copied in at most 5 of 20 answers**, against 19 of 20 for the
   same numeral on the wide question.
3. The tbc dose-response is monotone, and copying falls below half somewhere between ×10 and ×1000.
4. In the reasoning of the refusing cells, the model will name a physical or definitional cap (a class
   is an hour, one table plays a fixed number of boards). In the copying cells it will widen scope
   (more events, more participants, a longer year).

**What would falsify the hypothesis.** If the numeral is copied at about the same rate whether the
scope is wide or narrow, then scope elasticity is not what gates copying, and the ladder is about
something else, most likely the raw size of the number or the question's identity.
