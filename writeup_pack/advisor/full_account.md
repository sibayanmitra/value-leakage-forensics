# Unfaithful Exactly When It Can Justify

<p class="byline">Sibayan Mitra · 19 September 2026 · full account of the work</p>

## TL;DR

A model shown a number it was never told to use will often hand that number back as its own estimate, with a calculation written underneath that arrives at it. **Whether it does this is decided by the question, not the number.** If the question is loose enough that some set of assumptions reaches the number, the model adopts it and presents the result as independent work. If the question is tight, it refuses and tells the user the number is impossible.

Measured on the written replies: when the model uses the number, **6 of 165 replies** say where it came from. When it refuses the number, **21 of 39** do. It conceals the influence exactly when it can make the number look like its own reasoning.

The practical consequence: honesty measured on tight, checkable questions does not transfer to open-ended ones. Unfaithfulness here is a property of the question, not a fixed trait of the model.

## Objective

[Betley, Treutlein et al. (2026)](https://arxiv.org/abs/2607.14345) report *value leakage*: models letting their own values shape answers a user cannot check. Their main test is the Donation Bet. The model is asked for an estimate of something nobody has counted, and told that a donation goes to a good cause if the estimate exceeds a stated threshold and to a bad cause if it does not. Models land on the good side more often than chance, and rarely say why.

That prompt carries three things at once: a moral story, a user with a stake, and a specific number. Every variant in the paper keeps the number, and a footnote sets anchoring aside. **The original objective was narrow: separate what the values do from what the number does.**

**Setup for everything below.** Qwen3.5-35B-A3B (FP8), temperature 1.0, 20 answers per condition per question. Three of the paper's questions — tricks at bridge tournaments in Poland, spots on all giraffes, right-foot steps in one gym class. One variable changes at a time. Estimates are read off each answer by an LLM judge and checked by hand.

## What turned up along the way

**Experiment 1 — delete one sentence.** Removing only "The threshold is N", keeping the entire moral setup, removes the effect. Keeping the number and removing all the stakes does not.

| condition | estimates above the threshold (of 60) |
| --- | --- |
| the paper's bet, good cause if above | 39 |
| the paper's bet, good cause if below | 11 |
| same bet, threshold sentence deleted: above / below | 24 / 33 |
| threshold shown, nothing at stake | 50 |
| no number at all | 22 |
| direction instead of a number ("high side" / "low side") | 41 / 29 |

The values are not inert — a verbal direction still moves answers, 41 against 29 — but the number does most of the work. **This redirected the project.** If the number is doing the work, the question worth answering is not about the bet at all: it is when a model takes a number it is handed, and what it tells the user about it.

## Hypothesis

**The model adopts an attached number when a justification for it can be constructed, and refuses when one cannot.** Copying is the visible behaviour; the thing it stands in for is unfaithfulness — presenting a borrowed number as a derivation.

This predicts something specific: what counts as justifiable should depend on how much room the question leaves, not on how large the number is.

## Experiments and results

**Experiment 2 — attach only a number.** A number alone on the last line, no instruction to use it. It is not about whether the model can check the answer: a *correct* answer attached to a checkable question (17 × 23 → 391) is copied **234 of 234** times, a *wrong* one (→ 437) **0 of 239** times. A precise number no estimate could produce, 26,143,882, is copied **59 of 60** times with a calculation written to fit.

**Experiment 3 — scale the number until it breaks.** Each question has a limit, and the limits are nothing alike:

| question | model's own median answer | spread of its own answers | copying stops at |
| --- | --- | --- | --- |
| steps in one gym class | 1,000 | factor of 1.5 | ×11 to ×33 its own answer |
| spots on all giraffes | 17,500,000 | factor of 2.2 | 8 of 20 still copy at ×1,150 |
| tricks at Polish bridge | 17,250,000 | factor of 4.2 | ×1,500 to ×12,300 |

*Spread* is how much the model's own 20 no-number answers vary — the standard deviation of their logarithm. It measures how much room the question leaves. In raw multiples these limits differ about 315-fold. Divided by each question's own spread they nearly coincide. Across cells from different topics, distance measured in spread units orders copy rates correctly in 91 of 109 pairs (0.83), against 75 of 109 (0.69) for raw distance.

**Experiment 4 — hold the number, move the question (the causal test).** Two questions identical except for what they ask about, same number attached. The same 26,000,000,000 is copied **19 of 20** times for "tournaments in Poland" and **1 of 20** times for "the final table of the Polish national championship" (Fisher p = 5.8e-9).

**Experiment 5 — find the limit of the widest question.** Bridge had never broken in anything tested. Pushed further, it does: 210 billion copied 9/20, 1.7 trillion 3/20, 15 trillion 2/20, 520 trillion 1/20. Monotone, and it confirms the absolute size of a number is not what refusal tracks — bridge copies 26 billion 19 times in 20 while the steps question refuses 33,000.

**Experiment 6 — what does the reply tell the user?** This is the measurement the copy rate was standing in for.

| the written reply | when it uses the number | when it refuses it |
| --- | --- | --- |
| tells the user the number came from the prompt | **6 of 165 (4%)** | **21 of 39 (54%)** |
| presents its own calculation, no mention | **159 of 165 (96%)** | — |

<figure><img src="fig12_two_modes.png"><figcaption>The same model, the same attached number, two questions. All quotes verbatim, with file and line.</figcaption></figure>

**Experiment 7 — read the reasoning.** The chain of thought is explicit in both modes. Copying: *"Decision: I will output 26,000,000,000 and provide justifications that attempt to make it plausible."* Another: *"Write the justification based on the reversed calculation."* Refusing: *"This is physically impossible for a single tournament final table."* To check this was not my own expectation, 80 whole traces were shuffled with the condition hidden and labelled by a model that had not seen the data: a stated physical limit appears in **38 of 40** refusing traces and **2 of 40** copying ones (Fisher p = 1.1e-17).

**Experiment 8 — ask it afterwards.** After copying a round number the model admits the influence in 33 of 53 replies. Shown its own earlier reasoning, 48 of 56 admit it. Shown the same reasoning labelled as another assistant's, 57 of 57.

**One refinement.** Refusing is not the same as ignoring. Among answers that do not copy, the median still sits above the model's usual answer, fading from +2.7 spreads with ×10 attached to +0.5 with ×1,000. The break in copying is a break in adoption, not in influence.

## What checking changed

Predictions were written down before each new run, and two of them missed. Several results changed or were withdrawn on inspection:

| problem | how it surfaced | what changed |
| --- | --- | --- |
| The first scope pair changed more than the scope — one turned an average per person into a total over everyone | Reading the two questions word by word before scaling up | Rebuilt as exact minimal pairs. The bridge pair reproduced; the steps pair did not |
| The steps pair failed because the number I attached was reachable from both questions | Plotting each question's own answers against the attached number | Withdrawn as untested, not as disproven. My error in choosing the number |
| The headline statistic pooled 16 cells sharing only three topics | Counting which question each cell came from | Replaced with agreement across cells from different topics (0.83) |
| A masked labelling run showed the labeller a middle slice of each trace that cut out the limit statements | The statements were in the full trace in 29 of 29 disputed cases, in the slice in 3 | Re-run on whole traces |
| An apparent echo of the number's digits, 15.9% against 2.3% by chance | Every attached number was the true threshold times a power of ten, so an "echo" is also a correct answer | Fell to chance once that was removed. Withdrawn |
| The judge scored one refusal as a copy because the reply quoted the number before rejecting it | Reading every counted copy | Corrected by hand in the scorer |

Every quotation is checked word for word at its file and line by script. No count from a keyword scan or LLM judge is reported without reading the rows behind it.

## Limitations, and what would settle them

One model (Qwen3.5-35B-A3B). Three topics — nine question wordings, but variants of three. One clean causal pair; the steps pair remains untested. 20 answers per cell, and a question's spread is not precisely determined at that size. Scope and distance-from-the-model's-own-answer move together, and this design cannot separate them. The point where copying breaks is bracketed, not measured. A linear probe and activation steering found no internal direction that mediates the effect.

In order of cost: re-run the steps pair with a number only one of the two questions can reach; place numbers inside the transition to locate the break; raise the baselines to 60 answers; then repeat the core tests on a second model family.

Code, data, every reasoning trace, and the full record including the corrections: [github.com/sibayanmitra/value-leakage-forensics](https://github.com/sibayanmitra/value-leakage-forensics).
