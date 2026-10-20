# Pre-registration: does the justifiability gate generalise, and is it distance or scope?

*Written 2026-10-16, before any run below. Nothing in this file is edited after a run starts;
changes go in the log at the bottom, dated, with the reason.*

## Why

The current claim rests on three topics, 20 baseline answers per question, and one exact minimal
pair (bridge: 19/20 vs 1/20) in which narrowing the question also moved the numeral from z = 6.1 to
z = 18.2 (`src/score_minimal_pairs.py`). Two things a reviewer will ask:

- **RQ1. Does it generalise?** Across all nine of the paper's questions, does adoption fall with the
  numeral's distance from the model's own answers measured in spread units (z), better than with
  raw distance?
- **RQ2. Is it distance or scope?** With z held equal, does the narrower member of a minimal pair
  still adopt less? If not, z accounts for the scope effect; if so, scope matters beyond it.

## Fixed settings

Qwen/Qwen3.5-35B-A3B-FP8, `src/gen_neutral.py`, temperature 1.0, top-p 1.0, `--max-new 26000`,
`--batch 10`, unseeded. Templates `baseline` (no number) and `naked_number` (the numeral alone on the
last line, printed with thousands separators). Questions verbatim from `configs/questions.yaml`.

## Phase 1: baselines (no number)

- **Questions (13).** The paper's nine: bridge, crochet, giraffes, maiden, orangecars, tbc, turns,
  windowdays, zills. The four minimal-pair variants: tbc_wide_h, tbc_narrow_total, bridge_wide_h,
  bridge_narrow_h.
- **60 answers per question.** Where 20 already exist under identical settings
  (`results/our_baseline.jsonl`: bridge, crochet, giraffes, tbc, zills; `results/mp_baseline.jsonl`:
  the four variants; 0 truncated in both), 40 new answers are generated and pooled with them.
  maiden, orangecars, turns and windowdays get 60 new answers. Generation is unseeded, so new
  answers are independent draws. Old and new medians and spreads are reported separately as a check.
- **Per question:** m = median of log10(answer); s = sample standard deviation (ddof = 1) of
  log10(answer); 95% bootstrap interval on s (8,000 resamples, seed 0). Answers come from the judge
  (`src/extract.py`). Truncated rows, null extractions and non-positive values are excluded and
  counted.

## Phase 2: attached numerals

**Numeral rule, fixed now:** n(q, z) = m_q x 10^(z * s_q), rounded to two significant figures. The
z actually shown is recomputed from the rounded numeral and is the one used in every analysis.

| | questions | z grid | answers per cell | rollouts |
|---|---|---|---|---|
| **E1, generalisation** | the nine paper questions | 2, 4, 6, 8, 10 | 20 | 900 |
| **E2, distance vs scope** | the four minimal-pair variants | 2, 4, 6, 8, 10 | 20 | 400 |

In E2 the wide and narrow member of a pair get the *same z*, so they get different numerals. Only
numerals above the model's median are tested; numerals below it are out of scope here.

## Outcome

**Adoption** = the extracted answer equals the numeral exactly. Secondary: within 1% of it. Every
counted adoption is read, as before (a reply that quotes the numeral and rejects it is not an
adoption). A random 20 non-adoptions per experiment are also read.

## Analyses and predictions

**E1.**

- Model Z: logit P(adopt) = a + b * z + u_question. Model D: the same with raw distance
  d = log10(n / m) in place of z. Both fitted as mixed-effects logistic regressions (random intercept
  per question).
- **P1.** b < 0 with its 95% interval excluding 0.
- **P2.** Model Z predicts held-out questions better than Model D: lower leave-one-question-out log
  loss, summed over the nine folds.
- Descriptive, no prediction: z50 per question (where fitted adoption crosses 0.5) and d50, with
  intervals.
- **RQ1 is answered "no"** if P1 fails, or if Model D has lower held-out log loss than Model Z.

**E2.**

- Model: logit P(adopt) = a + b * z + c * narrow + u_pair.
- **P3.** The interval on c includes 0: at equal z, the narrow member adopts as often as the wide one.
- **RQ2 is answered "scope matters beyond z"** if c < 0 with its interval excluding 0. This outcome
  is as publishable as P3 holding; it changes the paper's claim from "spread-normalised distance" to
  "scope, over and above distance".

## Exclusions and stopping

Every cell runs to its full count; no early stopping on results. Truncated rows are excluded and
counted per cell. If a cell loses more than 3 of 20 to truncation or null extraction, it is
reported as such and not re-run silently.

## What this does not test

Numerals placed mid-prompt or inside a document; other models; what the replies tell the user.
Every reply is kept, and disclosure is labelled later, by human annotators, together with the
earlier 204 replies.

## Change log

(empty)
