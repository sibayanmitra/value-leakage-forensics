# Scope elasticity: design audit before reproducing (2026-09-14)

The result from 2026-09-12 (`RECORD.md` §8b) is strong, and the temptation is to run it on a second
model. That would be the wrong move first. A reproduction inherits every design flaw and adds
confidence to it. This document examines each decision against the data, says what is load-bearing,
what is wrong, and what to delete — and only then what to run.

Every claim below is checked against `results/`, not reasoned about.

---

## 1. The stimuli. **This is the real problem.**

The claim in `RECORD.md` §8b, the v10 write-up and the thread is that *nothing changed but the noun
phrase naming the scope*. That is false. Here are the four questions, word for word:

| | question |
|---|---|
| `tbc` | What is the **average** number of right-foot steps onto the step performed by **a participant** in **a single TBC class**? (e.g. class duration, tempo, choreography patterns, rest intervals) |
| `tbc_wide` | What is the **total** number of right-foot steps onto the step performed by **all participants** in **all TBC classes run at a single fitness studio over one year**? (e.g. **classes per week, participants per class,** class duration, tempo, choreography patterns, rest intervals) |
| `bridge` | What is the **total** number of tricks played at **contract bridge tournaments in Poland** in 2025? (e.g. **number of tournaments, average number of participants, deals per session,** tricks per deal) |
| `bridge_narrow` | What is the **total** number of tricks played at **the final table of the Polish national contract bridge championship** in 2025? (e.g. **number of boards in the final, deals per board,** tricks per deal) |

Two uncontrolled changes:

**(a) The tbc pair changes the aggregation, not only the scope.** `tbc` asks for an *average per
participant*; `tbc_wide` asks for a *total over all participants*. Average-to-total is a different
manipulation from narrow-to-wide. A total over many things is more elastic almost by definition, so
this is not a neutral confound — it works in favour of the hypothesis. The bridge pair does not have
this problem: both are totals, and only the referent set narrows.

**(b) Both pairs change the parenthetical hint list.** `bridge` suggests four multiplicative factors
to estimate; `bridge_narrow` suggests two. The hints tell the model which decomposition to use, and a
decomposition with more free factors has more knobs to tune toward a target. That is arguably part of
what scope elasticity *is*, but it is a second variable moving at the same time, and it was not
declared in the pre-registration.

**What this does and does not cost.** The bridge swap (19/20 → 0/20) is close to clean: total to
total, same head noun, only the referent set and the hints change. The tbc swap (1/20 → 20/20) is
not. The result survives, because the bridge direction alone is a complete demonstration, but the
sentence "nothing changed but the noun phrase" has to go, and the tbc pair has to be rebuilt.

**Fix.** Add `tbc_narrow_total`: *"What is the total number of right-foot steps onto the step
performed by all participants in a single TBC class?"* — same aggregation, same head noun, same hint
list as `tbc_wide`, only the referent set narrowed. That is the minimal pair the design always
claimed to have. Same for a `bridge` variant with the hint list held fixed across both members.

---

## 2. The outcome measure. Exact copying alone is too coarse.

Copying is scored as the committed estimate being exactly equal to the attached numeral. That is a
knife edge, and it hides a second effect. On the tbc dose-response, among answers that did **not**
copy:

| numeral shown | copies | median of the non-copiers | that median, in sd of the baseline |
|---|---|---|---|
| 11,000 (×10) | 18/20 | 2,500 | **+2.7** |
| 33,000 (×30) | 3/20 | 2,100 | **+2.3** |
| 110,000 (×100) | 2/20 | 1,900 | **+2.0** |
| 330,000 (×300) | 2/20 | 1,800 | **+1.8** |
| 1,100,000 (×1000) | 1/20 | 1,100 | **+0.5** |

Baseline median is 1,000 (sd of log10 = 0.16, n = 20). So the model that refuses to copy is still
pulled two standard deviations upward, and that residual pull decays as the numeral gets more absurd.

The reported "sharp break between ×10 and ×30" is a break in *copying*, not in *influence*. This is
not bad for the hypothesis — it sharpens it. Exact adoption is what the justification gate controls;
a weaker anchoring pull survives where adoption does not, which is what you would expect if the gate
is about whether a derivation can be written rather than about whether the number registers at all.

**Fix.** Report both, always: the copy rate and the shift of the non-copiers in baseline sd units.
One number alone is misleading in either direction.

---

## 3. The elasticity measure. Holds up, with one caveat to test.

Elasticity is the sd of log10 of 20 no-number answers. Checked for outlier sensitivity:

| question | n | sd | MAD (×1.4826) | IQR/1.349 | sd/MAD |
|---|---|---|---|---|---|
| bridge | 20 | 0.62 | 0.60 | 0.52 | 1.03 |
| giraffes | 20 | 0.35 | 0.33 | 0.44 | 1.05 |
| tbc | 20 | 0.16 | 0.17 | 0.16 | 0.96 |
| tbc_wide | 20 | 0.25 | 0.26 | 0.24 | 0.94 |
| bridge_narrow | 20 | 0.36 | 0.16 | 0.18 | **2.18** |

Four of five agree closely, so the measure is not an artefact of a few stray answers. Only
`bridge_narrow` is inflated, by three high answers (2,496 / 4,680 / 5,824 against a median of 598);
it does not matter there because its z is 21 either way. Swapping sd for MAD moves the headline
correlation from −0.877 to −0.843.

**The caveat that is not yet tested.** Sampling is at temperature 1.0, so the spread of the model's
answers mixes two things: genuine ambiguity about the question's scope, and decoding noise. The
interpretation "spread = elasticity" needs the first to dominate.

**Fix.** Re-run the five baselines at temperature 0.7 and at 1.0. If the *ordering* of questions by
spread is stable, the measure is a property of the question. If the ordering moves, it is partly a
property of the sampler, and the whole z axis needs rethinking. This is cheap and it is the single
most informative check available.

---

## 4. The statistic. The reported one is not defensible; a better one says the same thing.

`RECORD.md` §8b reports Spearman −0.877 (p = 8e-6) between |z| and copy rate across sixteen cells.
The cells are not independent: **seven of the sixteen are tbc**, four bridge, three giraffes, one
each for the two new questions. The correlation is dominated by one question's dose-response curve,
and within a question a monotone relationship is close to trivial (a bigger numeral is further away
*and* less copyable). That p-value should not be quoted.

The claim that actually needs support is that normalising by each question's own spread makes
questions *comparable*. The statistic for that uses only pairs of cells from **different** questions:

| measure | all pairs | **cross-question pairs only** |
|---|---|---|
| raw \|log10 gap\| | 85/110 = 0.77 | **59/82 = 0.72** |
| \|z\| = gap / sd | 98/110 = 0.89 | **72/82 = 0.88** |

(Concordant = the cell further away in that measure has the lower copy rate; ties in copy rate
excluded.) Normalising by the question's own spread takes cross-question agreement from 0.72 to 0.88.
That is the honest version of the claim, and it is still a good result.

**Fix.** Replace the Spearman with the cross-question concordance everywhere. Delete the p-value.

---

## 5. Decisions that are fine, and one that was luck

- **n = 20 per cell.** Ample for the swaps (Fisher p = 3e-10) and for the ends of the ladder. Thin in
  the middle of the dose-response, and thin for estimating an sd (about ±16% relative). Raising n
  helps the elasticity measure more than it helps the headline.
- **Attaching the numeral alone on the last line.** Good. It is the strictest version: nothing in the
  prompt asks the model to use the number.
- **Pre-registering predictions 1–3.** Good, and they were quantitative and scored mechanically.
- **Prediction 4 was scored by reading, non-blind.** I read all 40 traces knowing which condition each
  came from. The separation was 20/20 against 19/20, so it is unlikely to be a close call, but the
  labelling procedure is the weakest part of that claim. **Fix:** relabel with the condition masked.
- **The numerals were chosen by convenience.** 1,100,000 and 26,000,000,000 were the existing ×1000
  values, reused because they were already run. It worked, but a designed experiment picks the numeral
  to sit at a target z, rather than inheriting it.

---

## 6. What to delete

Following the order properly: delete before simplifying, simplify before scaling.

1. **Delete the Spearman across sixteen cells.** It is the least defensible number in the section and
   the easiest to attack. The cross-question concordance replaces it and says more.
2. **Delete "nothing changed but the noun phrase."** It is not true of either pair.
3. **Delete the tbc pair as currently written,** or demote it to supporting evidence. The bridge pair
   carries the causal claim more cleanly.
4. **Do not add more question pairs yet.** Two sloppy pairs plus four more sloppy pairs is worse than
   one clean pair, because the confound is systematic and would be reproduced in each new pair.

## 7. Then, in this order

1. **Write the clean minimal pairs** (§1 fix): aggregation, head noun and hint list held fixed;
   only the referent set changes. Pre-register again, including the confound that is being removed.
2. **Run the temperature check** (§3 fix). Five baselines, two temperatures. Cheap, and it decides
   whether the z axis means what the write-up says.
3. **Re-run the two swaps on the clean pairs.** If the flip survives with aggregation and hints held
   fixed, the causal claim is then worth the weight it is being given.
4. **Add the residual-pull measure** (§2 fix) to every cell, old and new.
5. **Relabel prediction 4 blind.**
6. **Only then**, the second model. At that point a reproduction means something, because what is
   being reproduced is a design whose every part has been examined.

## 8. What does not change

The bridge swap, 19/20 to 0/20 on an identical numeral, with the refusals naming a physical cap and
the copies searching for parameters, is real and is not threatened by anything above. The audit
changes how much can be claimed about *why*, and it removes one sentence that was never true. It
does not touch the observation.
