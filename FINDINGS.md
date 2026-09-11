# FINDINGS — what we actually know

Every experiment has a plain-English name and a one-line claim. If a number is not in
this file, it is not quotable.

- `RESULTS.md` — the running lab log (chronological, includes dead ends)
- `METHODS.md` — why we did it this way
- **this file** — the ledger: what we know, and how sure we are

Last updated: 2026-09-07.

**The 2x2, the two warnings and the 35B steering run have now been analysed —
`FINDINGS_backstop_2026-09-07.md` has the numbers, the controls and what changes.
The section bodies below still describe those three as in flight.**

**Confidence key** — **Solid** = controlled, CI excludes zero, robustness checked.
**Supported** = clear result, one named gap. **Running** = in flight.
**Dead** = tried, didn't work, kept for the record.

---

## The story in five lines

1. The bias is real and we reproduce it. (**Replication**)
2. It is **not** in the model's first number — it builds up while it reasons. (**First Guess**, **Lock-In**)
3. Saying "I won't let the bet sway me" does not stop it. (**Honest Claims**)
4. **But most of it isn't about values at all.** Just *showing the model the number* moves
   the answer as much as the whole moral setup does. (**The Number Ladder**)
5. So the real question is: how much is the number, and how much is the values?
   That is the experiment now running. (**Number vs Values**)

---

## The experiments

| name | the claim in one line | confidence | old code |
|---|---|---|---|
| **Replication** | The bias is real: the bet moves the answer, hard. | Solid | E0 |
| **First Guess** | The model's *first* number is unbiased. | Solid | E1 |
| **Lock-In** | The answer gets decided gradually, not at one moment. | Solid | E1d |
| **Honest Claims** | Saying it won't be swayed doesn't stop it being swayed. | Supported | E1c |
| **The Aim Sentence** | One sentence in the reasoning carries part of the effect. | Supported | E2 |
| **The Number Ladder** | Showing the number does as much as the whole moral setup. | Solid | E1e |
| **Number vs Values** | Splits the cause into "the number" vs "the values". | **Solid** | new |
| **The Valence Probe** | Is "the side I want" written into the activations? | Solid null | E3 |
| **Turn It Off** | Can a warning stop it — and which warning? | **Supported** (null on *which*) | new |
| **Make It Disclose** | When we know it was anchored, does it admit it? | Running | new |

---

## Replication — the bias is real
**Claim: when the bet says "high is good", the model answers high, and vice versa.**

Authors' released Qwen3.5-35B-A3B rollouts, our pipeline. 9 questions x
{no bet, high-is-good, low-is-good} x 100 rollouts.

**Bias = +0.615, 95% CI [+0.580, +0.650]**, n=1,711.
(A score of 0 means the bet changes nothing; +1 means it decides the answer every time.)

*Control:* the threshold T is defined as the median no-bet answer, so recomputing it from
the authors' own no-bet rollouts tests our whole pipeline end to end. **7 of 9 match
exactly.**

---

## First Guess — the bias is not in the first number
**Claim: the model starts honest and drifts.**

450 traces, every candidate number the model writes down, in order.

| where in the reasoning | bias |
|---|---|
| **the first number it writes** | **+0.028 [-0.064, +0.118]** — indistinguishable from zero |
| the last number it writes | +0.615 [+0.547, +0.682] |
| the final answer | +0.623 [+0.557, +0.687] |

So the bias is **not** baked into an initial guess and carried along, and it is **not**
tacked on at the end (the last in-reasoning number already has all of it). It is built
during the reasoning. True for all 9 questions.

*Control:* 30 traces hand-checked, 29/30 correct, and the result survives deleting every
trace touched by the two error types we found.

---

## Lock-In — the answer is decided gradually
**Claim: there is no single moment where it flips.**

How well does the model's current number predict which side it will finally land on?

| how far through the reasoning | predictive power (AUROC) |
|---|---|
| first number | **0.576** (near coin-flip) |
| 25% | 0.694 |
| 50% | 0.797 |
| 75% | 0.881 |
| last number | **0.957** (near-certain) |

---

## Honest Claims — saying it won't cheat doesn't help
**Claim: rollouts that explicitly promise impartiality are just as biased.**

| which rollouts | n | bias in the final answer |
|---|---|---|
| all of them | 450 | +0.618 [+0.551, +0.680] |
| **the ones that say they won't be swayed** | **307** | **+0.578 [+0.498, +0.650]** |

Overlapping intervals. Promising impartiality does not reduce the effect.

*Gap:* this is a correlation. It shows the promise doesn't *predict* less bias; it doesn't
prove the promise is causally irrelevant.

*Note:* the paper's four-way "did it disclose?" labelling **does not work on this model** —
two runs of the same judge on the same data gave 91.8% vs 2% for one category. The reason
is that the categories overlap here: 62% of traces contain a steering statement, 68%
contain a no-bias promise, and **45% contain both**.

---

## The Aim Sentence — one sentence carries part of it
**Claim: the sentence where the model ties its number to a side is doing real work.**

Take 50 rollouts. Cut the reasoning right before that sentence, let the model write its own
replacement, then force an answer. Compare replacements that state an aim against ones that
don't. **All 1,107 replacement sentences were labelled by hand**, so no judge is in the
critical path.

| comparison | effect |
|---|---|
| **replacement states an aim vs doesn't** | **+0.087 [+0.020, +0.158]** |
| **original sentence vs a no-aim replacement** | **+0.072 [+0.011, +0.137]** |
| original sentence vs an aim-stating replacement | -0.016 [-0.075, +0.043] |

**The third row is what makes this believable.** The two effects compare aim-present against
aim-absent; the null compares aim-present against aim-present. So it is the sentence's *job*
that matters, not its wording and not the act of rewriting it.

*Gap:* we force the answer immediately after the edit, so this measures the sentence's
effect on an immediate answer, not on the ~6,700 tokens of reasoning that would have
followed.

---

## The Number Ladder — the number does the work, not the values
**Claim: telling the model the number, with no mention of good or bad, moves the answer
as much as the full moral setup does.**

This is the most important table in the project. All four conditions are **our own
generation on the same machine**, same 3 questions, n=20 each.

| what the prompt says | how often it answers above T |
|---|---|
| nothing about a number | 0.367 [0.250, 0.483] |
| **the number, no good/bad at all** | **0.733 [0.633, 0.833]** |
| **the full bet: above = good cause, below = bad cause** | **0.717 [0.600, 0.833]** |

**The gap between those two is +0.016 [-0.150, +0.167] — nothing.**

And with the bare number just dropped at the end of the prompt, no sentence around it:

| | how often the answer is *exactly* T |
|---|---|
| no number in the prompt | 0.033 [0.000, 0.083] |
| **bare number appended** | **0.950 [0.900, 1.000]** |

*Controls:* (a) our setup runs **slightly low** compared to the authors' API rollouts
(-0.094 [-0.204, +0.021]), so it cannot be inventing an upward effect; (b) dropping every
rollout that hit the length cap changes nothing.

---

## Number vs Values — splitting the cause  `RUNNING`
**Claim being tested: how much of the effect is the number, and how much is the values?**

The prompt has two ingredients. Remove them one at a time — a 2x2.

|  | **no number given** | **number given** |
|---|---|---|
| **no good/bad** | no bet at all ✅ | the number alone ✅ |
| **above is good** | the bet, number withheld ⏳ | the full bet ✅ |
| **below is good** | the bet, number withheld ⏳ | the full bet ⏳ |

The two new conditions are the authors' own prompt with **exactly one sentence deleted** —
"The threshold is {number}." Nothing else changes, so nothing else can explain a difference.

**What each answer would mean:**
- If the bet with no number does nothing → the effect is entirely about the number, and the
  paper's "value leakage" framing needs qualifying.
- If it works as well as the full bet → values act on their own, and our Number Ladder
  reading is too strong.

Either way we learn something. Running now, ~4-5 h.

---

## The Valence Probe — is "the side I want" in the activations?  `Solid null`
**Claim: the model does not write down "this number is on my side" in any strong way.
What it writes down is only what the prompt already says.**

Qwen3.5-9B (which does show the bias: **+0.450 [+0.252, +0.635]**). We read the internal
state at all 11,265 candidate numbers across 198 rollouts and ask what can be decoded,
leave-one-question-out. Error bars resample **rollouts**, not rows.

**Position in the reasoning is trivially encoded by the model, and several targets
correlate with it, so the right-hand column is the real result.**

| what we try to decode | raw | position removed |
|---|---|---|
| which side is good (*stated in the prompt*) | 0.734 | **0.735 [0.706, 0.764]** |
| is this number above the threshold | 0.765 | **0.767 [0.748, 0.783]** |
| how close to the threshold (*anchoring*) | 0.891 | **0.641 [0.622, 0.658]** |
| **"this number is on my side"** (*valence*) | 0.610 | **0.576 [0.554, 0.599]** |
| **the final answer's side** (*the outcome*) | 0.568 | **0.575 [0.507, 0.632]** |
| shuffled labels (*null control*) | 0.508 | 0.508 [0.498, 0.519] |

**Reading.** Only two things are solidly represented, and both are given: which side is
good (it is in the prompt) and whether the number beats the threshold (arithmetic on the
prompt). Valence is **weak but real** -- 0.576 excludes 0.50, so it is not nothing, but it
sits far below the descriptive controls. And the target that actually matters for Neel's
question, **the final answer's side, is not reliably decodable** (0.575, CI reaching down
to 0.507).

Anchor-proximity looks like the strongest signal until position is removed, and then it
collapses -- 0.891 -> 0.641 at layer 16, and **0.863 -> 0.502, exactly chance, at layer
20**. Estimates converge on T late in the reasoning, so "close to T" and "late" are nearly
the same variable. We cannot claim the model represents the anchor either.

**We are therefore not running the steering experiment.** Steering a 0.58 direction would
produce a null that could not be distinguished from the intervention simply being too weak.
That is not a result.

**This independently reproduces Gilg et al. App. F.4** (steering nearly inert on Qwen).

**Getting here took two corrections, both worth stating:**
1. The first run capped traces at 8,000 tokens. 89% are longer, so **51% of the numbers
   were dropped -- all of them the late ones**, which is exactly where Lock-In says the bias
   lives. Rerun with nothing dropped (0 outside the window).
2. An audit then found the position confound above, the wrong target (we were predicting a
   property of the current number, not the outcome), and error bars computed as if 11,265
   correlated rows were independent when there are only 198 rollouts and 47% of rows repeat
   a value from the same rollout. A CI-estimand bug was also fixed: the point estimate
   averaged per-question AUCs while the interval bootstrapped the pooled folds, which
   produced an interval not containing its own point estimate.

## Turn It Off — can a warning stop it?  `Running`
**Claim being tested: our account and the paper's make OPPOSITE predictions here.**

Take the full bet prompt and add exactly one sentence, in the same position, differing only
in what it tells the model to ignore:

- `warned_anchor` — *"do not let the number {threshold} anchor your estimate."*
- `warned_values` — *"do not let the bet or which cause gets the donation influence your estimate."*

**If the effect is anchoring, the number-warning works and the values-warning does not.
If it is value leakage, the reverse.** A real bet we can lose.

The 2x2 gives a second, stronger answer to the same question: if deleting the number kills
the effect, then removing the anchor turns it off even when every value word remains.

---

## Make It Disclose — does it know it was influenced?  `Running`
**Claim being tested: when we KNOW the answer was anchored, does the model admit it?**

The usual problem with disclosure work is that you have to guess whether an answer was
really influenced before asking whether the model admits it — so a "no" is ambiguous
between honesty and a wrong guess about ground truth.

**We avoid that.** In `naked_number` the prompt is the question plus a bare integer, and
**95% of answers come back exactly equal to that integer**. There is no other route to that
agreement. So a "no" there is a demonstrable failure of self-knowledge, not a judgement call.

Each finished rollout is replayed and asked a follow-up. The question deliberately never
says "threshold" or "bet" — it names only what was literally on the page, so we do not lead
the witness.

| arm | what it gives us |
|---|---|
| `naked_number` | influence is **certain** (answer == the number) |
| `above_good` | the paper's condition; influence probable, not certain per rollout |
| `baseline` | **false-positive control** — no number was ever shown, so any "yes" here measures how much the question itself induces admission |

## Neel's four questions — scorecard

| his question | where we are |
|---|---|
| **Why? Where do the values intervene?** | **Answered, and the answer is a surprise** — largely they don't. Showing the number does as much as the whole moral setup. Plus the timing: the first guess is unbiased and the answer locks in gradually. |
| **Can you make it disclose?** | **Running** — the `naked_number` test, where influence is certain and a denial is demonstrably false. Plus the existing negative: it does not disclose spontaneously, and promising impartiality doesn't help. |
| **Can you turn the effect off?** | **Running** — two ways: delete the number (the 2x2), or warn about the number vs warn about the bet (Turn It Off). |
| **A linear direction predicting it *and* causally mediating it** | **A documented null with working controls.** Nothing but prompt-stated facts survives the position control; the outcome itself is not reliably decodable. Steering deliberately not run — a null from a 0.58 direction is uninterpretable. Reproduces Gilg App. F.4. |

## Dead ends, kept for the record

| what | why we killed it |
|---|---|
| regex answer extraction | returned `1` for *"approximately 1.4 to 1.5 billion"*; 10% disagreement with the judge |
| four-way disclosure labels | two runs on identical data gave 91.8% vs 2% for one category |
| a "steering intent" regex | ~2-3/10 precision — it matched explicit *denials* |
| embedding-similarity bucketing | no separation (0.556 vs 0.548) where a judge split gives 0.632 vs 0.480 |
| the capped valence probe | dropped 51% of the data, all of it the late half |

---

## What could still be wrong

1. **The Number Ladder is 3 questions, n=20 per cell.** Right design, small sample.
2. **The Aim Sentence forces an answer immediately** after the edit (see its gap above).
3. **Honest Claims is correlational.**
4. **All hand-labelling was done by one person**, who also wrote the labelling instructions.
5. **The probe is on a 9B model**; the behaviour was measured on 35B. The 9B does show the
   bias, but that doesn't prove the mechanism is the same.
6. **Length caps have burned us twice** — once making a whole condition unusable, once
   silently deleting half the probe's data. Assume any cap is wrong until measured.

---

## Infrastructure worth keeping

**Qwen3.8-27B-FP8 wouldn't run — found and fixed.** Its config protects `mlp.gate` (the
router in a mixture-of-experts model). Transformers matches that name by prefix, so it also
protected `mlp.gate_proj`. This model is *dense* — it has no router — so the rule only ever
hit `gate_proj`, leaving it unquantised and crashing on the first matmul. Dropping those
entries fixes it (`src/fp8_load.py`; verified 17*23 -> 391, 29.9 GB).
**When rerunning it: use batch ~24, not 6** — it was at 4% GPU utilisation.

**This machine:** `ulimit -v` is 100 GB, so `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
fails with `mmap: Cannot allocate memory`. Don't set it. vLLM is unusable; HF transformers only.
