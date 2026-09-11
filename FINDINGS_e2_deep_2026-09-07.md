# E2 re-analysis — is the aim sentence anchoring in disguise, and where does it act?

Written 2026-09-07. Follows `FINDINGS_backstop_2026-09-07.md`, which showed the Donation Bet
effect is carried by the threshold **number**, not by the value framing. That raised an
obvious threat to E2: aim sentences characteristically restate the number
(*"So > 26M = Good"*, *"If I say 30m -> Good Cause"*). If so, E2's +0.087 might be the same
anchoring effect seen from inside the CoT rather than a separate value mechanism.

**It is not. The aim effect survives the anchoring explanation.** §2 also read it as
concentrated early in the reasoning; that positional reading is **retracted as of 2026-09-10**
(see the update in §2). The headline contrast is unaffected.

Scripts: `src/e2_deep_split.py`, `src/e2_position.py`.
Raw output: `results/snapshots/2026-09-07T1454/E2_DEEP.txt`.
All answers came from the existing judge cache — zero new spend.

---

## 0. Pipeline check: the headline replicates exactly

Rebuilt from `results/resamples_forced_{a,b,c,d}.jsonl` independently of
`analyze_resamples.py`, using the hand labels and a paired within-source bootstrap:

| | reported in `RESULTS.md` | this re-analysis |
|---|---|---|
| resampled_AIM − resampled_NOAIM | +0.087 [+0.020, +0.158], 28/49 | **+0.087 [+0.018, +0.158], 28/49** |

3,785 usable rows, 50 sources, 1,273 hand-labelled resampled rows. Independent
reconstruction, same answer.

### A keying trap worth recording

`resamples_forced_{a,b}` (the first 16-source batch) and `{c,d}` (the expanded 34-source
batch) **re-use source ids 0–15 for different rollouts.** Grouping by `source` alone silently
merges two unrelated rollouts and collapses 50 sources to 34; the headline contrast then reads
+0.078 [−0.025, +0.176] and appears not to replicate. The join key must be
`(batch, source)`. `e2_all_scored.jsonl` already handles this by renumbering the second batch
to 1000+. Anything joining back to the raw files must do the same.

---

## 1. The aim effect is not number-restatement  `Supported`

Aim sentences do restate the threshold far more often than non-aim ones — the confound is
real and large:

| sentence type | restates T (within 5%, any notation) |
|---|---|
| states an aim | **421/624 = 0.675** |
| states no aim | **182/649 = 0.280** |
| the *original* aim sentences | 35/50 = 0.700 |

But restating the number is not what carries the effect:

| contrast (paired within source) | Δ p(favoured side) |
|---|---|
| aim − no-aim, **all** | **+0.087 [+0.018, +0.158]**, 28/49 |
| aim − no-aim, **within sentences that restate T** | +0.020 [−0.123, +0.157], 12/32 |
| aim − no-aim, **within sentences that don't restate T** | **+0.122 [+0.006, +0.239]**, 17/32 |
| **restates T − doesn't** (the new axis, all sentences) | **+0.043 [−0.015, +0.098]**, 24/49 |
| restates T − doesn't, within aim sentences | +0.021 [−0.076, +0.126] |
| restates T − doesn't, within no-aim sentences | +0.026 [−0.109, +0.162] |

**Reading.** The number axis does nothing on its own (+0.043, CI spans zero). The aim effect
is intact — indeed only resolvable — among sentences that never mention the number. So E2 is
measuring something the 2x2 does not: a genuine effect of *stating a target side*, separate
from the anchoring that dominates the prompt-level result.

**Do not call this an interaction.** The difference between the two strata is
+0.155 [−0.047, +0.352] (n=19 sources with all four cells) — it spans zero. The correct claim
is "the effect is not explained by number-restatement", not "the effect is bigger without
the number".

**Why the null on the number axis makes sense.** In this design the threshold is already in
the prompt of every row. The model has been anchored before the aim sentence exists.
Re-mentioning the number inside one sentence adds no new anchor, so it should do nothing —
and it does nothing. The anchoring result and the aim-sentence result are about different
moments, and they do not compete.

---

## 2. Where the unfaithfulness sits: early aim statements look causal, late ones do not

*(Retracted 2026-09-10 — see the update at the end of this section.)*

The aim sentence lands **early**: median 23.6% through the reasoning by character offset
(IQR 0.17–0.42), 33.5% by sentence index. Splitting sources at the median position:

| | aim − no-aim | original − nosent (deleting the sentence outright) |
|---|---|---|
| **aim sentence EARLY** (first ~24%) | **+0.123 [+0.015, +0.236]** n=24 | **+0.086 [+0.028, +0.149]** n=24 |
| **aim sentence LATE** | +0.054 [−0.028, +0.138] n=23 | **−0.004 [−0.060, +0.050]** n=23 |

corr(position, aim effect) = −0.272 [−0.524, +0.060], n=47.

**Reading.** The second column is the sharp one. Removing the aim sentence entirely changes
the answer when it appears early (+0.086, clears zero) and does **nothing at all** when it
appears late (−0.004, tightly centred on zero). An aim stated early has ~6,700 tokens of
reasoning left to steer. An aim stated late is a *report* of a decision already taken — it
reads like the moment of motivated reasoning, but removing it costs nothing.

This is the natural companion to E1d: the answer's side goes from AUROC 0.576 at the first
estimate to 0.881 by 75% through. The aim sentence is load-bearing exactly where the outcome
is still open.

**The confound that must be stated.** Answers here are *forced* immediately after the edited
position. For a late aim sentence, the forced answer is taken late, when the estimate is
largely settled anyway — so "removing a late sentence does nothing" may reflect *when the
answer was forced* rather than the sentence's causal role. The two explanations are not
separated by this data. The full-continuation run (`METHODS.md` §11, still not run) is what
would separate them, and this result makes that run more valuable than it looked.

**Update 2026-09-10: retracting the reading above.** The full-continuation run has now been
done, as a position sweep on `naked_number`/bridge
(`FINDINGS_position_sweep_2026-09-10.md`, `results/sweep_*.jsonl`). Under full continuations,
seven positions spread through three traces all read zero, including the sentence that says
the supplied number out loud. That is a different condition and a different outcome variable,
so it does not test the aim sentence directly. What it removes is my confidence that the
early/late gradient in this section is about the sentence rather than about when the answer
was forced, which is the confound stated in the paragraph above. **Read this section as
unresolved, not as a positional result.** The headline contrast in §1 is unaffected: it holds
position fixed within source, so position cancels out of it.

**Also post-hoc.** The median split was chosen after seeing the position distribution, the
two halves' CIs overlap, and the correlation CI crosses zero. Treat as a strong lead, not an
established result.

---

## 3. What this adds to the story

The project's two causal results are now about **two different moments**, and they no longer
conflict:

| | what moves the answer | how big |
|---|---|---|
| **in the prompt** | the threshold *number*. The value framing with the number deleted does nothing (bias −0.150). | the whole effect (+0.485) |
| **in the reasoning** | *stating a target side*, early. Not re-mentioning the number. | modest (+0.087 to +0.123 on a rate) |

So: the number sets the anchor, and then a smaller, genuinely value-shaped step happens
inside the CoT — and it is only load-bearing while the answer is still open. That is a more
defensible claim than either "it is all anchoring" or the paper's "the values bias the
answer", and both halves rest on hand labels and a control that could have killed them.

## 4. Not done

- The `deny` marker was **not** joined to these 50 sources. The natural next question — does
  the early-aim effect persist in rollouts that explicitly promise impartiality? — needs the
  E1c marker recomputed over the source traces, and that regex is not in `src/`.
- The four-way disclosure taxonomy stays rejected and was not used here.
- Full-continuation validation (see §2 confound) still not run.
