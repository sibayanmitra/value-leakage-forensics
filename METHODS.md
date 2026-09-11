# Methods and decision log

Running record of *what was done and why*, including choices that were reversed. Numbers live
in `RESULTS.md`; this file is the reasoning behind the pipeline.

Project: where in the chain of thought does Donation Bet value leakage enter?
Paper under study: Betley, Treutlein et al. (2026), *Value Leakage*, [arXiv:2607.14345](https://arxiv.org/abs/2607.14345).
Related: Gilg, Beckmann, Paleka & Butlin (2026), *Probing Persona-Dependent Preferences*, [arXiv:2605.13339](https://arxiv.org/abs/2605.13339);
Bogdan, Macar, Nanda & Conmy (2025), *Thought Anchors*, [arXiv:2506.19143](https://arxiv.org/abs/2506.19143).

---

## 1. Model: Qwen3.5-35B-A3B (FP8)

**Chosen because** the paper reports it as its *most biased* open model, giving the best
signal-to-noise for every downstream measurement, and because the FP8 checkpoint (37.5 GB) fits
on a single 48 GB RTX 6000 Ada.

Rejected alternatives:
- **Qwen3.6-27B dense** — the plan's original pick. The paper never evaluates *any* dense Qwen
  (zero occurrences of "27B"), so the effect was unverified there and Phase 0 could have failed
  after hours of work.
- **unsloth 8-bit** — does not exist for CUDA. Their MLX-8bit is Apple-only, NVFP4 needs
  Blackwell (sm_100+; this box is sm_89), and GGUF-Q8 has no residual-stream hooks, which would
  kill Phase 3. `unsloth/Qwen3.6-27B` is just a BF16 mirror.
- **bitsandbytes int8** — quantises at load time *from* BF16, so it would still require the
  55.6 GB BF16 download; no saving over FP8.

**Single GPU** (device 0) throughout: the box is shared, GPU 1 carries another user's process,
and RTX 6000 Ada has no NVLink, so tensor-parallel all-reduces would cross PCIe.

## 2. We analyse the authors' released rollouts, not only our own

The Value Leakage data repo ships `final_data/cache/qwen3.5-35/` — 9 questions x
{baseline, above_good, below_good} x 100 rollouts, with full CoT and the thresholds in each
file's meta line. Using it means Phase 0 is a *validation* of our pipeline against a known
answer rather than a gamble, and Phase 1 needs no GPU at all.

Our prompt templates reproduce theirs **byte-for-byte** (verified against the `prompt` field,
em-dash included), so anything we generate stays comparable.

## 3. Extraction is judge-only

A regex-first pass reported a 0% *miss* rate, which measured the wrong thing: a regex always
returns *a* number, just not the right one. Reading 20 random CoTs found an `orangecars` answer
opening *"approximately 1.4 to 1.5 billion..."* extracted as `1`. Measured regex/judge
disagreement was 10.44%. **The regex was deleted.**

Three further bugs, all found by looking at data rather than at summary statistics:
- `response_format: json_object` guarantees valid JSON but not the right *keys*. The judge
  emitted `{"": "I want to be a data point..."}` for the answer `"812"`, so `.get("value")`
  silently returned `None`, and that got cached — inflating a fake 2.78% "refusal" rate. Fixed
  with a strict `json_schema` plus a `_valid()` gate driven by the schema's `required` keys.
- `except Exception: return None` in `extract_answer` let transport errors masquerade as
  refusals. Removed; it now raises.
- The disk cache was written non-atomically, so concurrent workers produced torn files. Fixed
  with tempfile + `os.replace` and tolerant reads.

After all three: 0 of 2700 rollouts fail extraction.

## 4. Truncated rollouts are excluded

4.19% of the authors' rollouts (113/2700) have `reasoning == ""` and ~50k characters of raw CoT
dumped into `answer`, ending mid-sentence: the model hit the token cap before closing its
thinking block. These have no committed answer, so extracting a number from them means reading
one out of incomplete reasoning. Rates are near-symmetric across intervention directions
(4.78% / 5.11%) so this is not differential dropout, but interventions truncate ~2x more than
baseline, which independently corroborates the paper's report that the donation note lengthens
reasoning.

## 5. Two judges, chosen by measurement

| task | model | reasoning | why |
|---|---|---|---|
| answer extraction, classification | `deepseek/deepseek-v4-flash-0731` | off | cheap, reliable at short extraction |
| CoT trajectory enumeration | `meta/muse-spark-1.3-contributor` | **on** | the only one that can actually do it |

On one 22k-char trace with ~50 hand-counted estimates:

```
muse-spark-1.3-contributor, reasoning ON   -> 50 estimates   $0.0017   32s
deepseek-v4-flash-0731,     reasoning OFF  ->  1 estimate    $0.0009    3s
deepseek-v4-flash-0731,     reasoning ON   -> malformed JSON after 243s
```

DeepSeek was not attempting the enumeration — it returned 21 on one call and 1 on an identical
re-run at temperature 0, emitting ~$0.0003 of output. Exhaustive enumeration over a long trace
needs a reasoning model. This deviates from the instruction to run the judge with reasoning off,
and is documented here because the deviation is load-bearing.

An intermediate two-stage design (deterministic numeric scan proposing candidates, judge
classifying them) was built and then discarded once Muse Spark could do it directly.

## 6. Budget discipline

OpenRouter credits are prepaid and cannot be topped up. **The balance is
`/credits` -> `total_credits - total_usage`; `/auth/key` -> `limit_remaining` is a rate limit,
not money** — misreading it once produced a $36 figure when $5.56 remained. `src/budget.py`
reads the real balance and aborts any run that would breach a $2.50 reserve.

~$1.40 was wasted launching a full 2,587-trace extraction on DeepSeek and *then* running the
model comparison. The rule now: benchmark on 3-5 items before committing, and freeze the prompt
first, since cache keys hash the prompt text and every edit silently re-bills the dataset.

Trajectory extraction therefore runs on a **balanced 25-per-cell subsample** (450 traces, seed 0,
chosen before extraction). Cache from the killed run could not be reused: it was concentrated in
5 of 18 cells, and reusing it would have broken the equal-question weighting the bias metric
depends on.

## 7. Infrastructure: vLLM abandoned

vLLM >= 0.27 pins `torch==2.13.0` (CUDA 13, driver >= 580); this box runs driver 570 / CUDA 12.8.
vLLM 0.26.0 pins torch 2.11.0 which *does* have a cu128 wheel, but its compiled extension
`_C_stable_libtorch` still links `libcudart.so.13`. Unfixable without sudo. **HF transformers
carries both phases**, which Phase 3 needed anyway for hooks.

Four fixes were required to make HF work:
- broken `torchaudio` aborted transformers' import chain -> uninstalled
- `accelerate` missing -> installed
- transformers 5.16.1 bug: `FineGrainedFP8HfQuantizer.update_tp_plan` crashes on this MoE config
  (no `base_model_tp_plan`) -> monkeypatched to fall through, harmless single-GPU
- FP8 path needs `kernels==0.16.0` -> installed

Also: `ulimit -v` is 100 GB here, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` changes
CUDA's virtual-address reservations enough to breach it, causing `mmap: Cannot allocate memory`
on model load. **Do not set expandable_segments on this machine.**

## 8. Phase 2 follows Thought Anchors, not the original plan

The original plan was to *delete* the aim sentence and patch the resulting off-distribution
prefix with two controls (random-sentence deletion, no-deletion truncation). Thought Anchors'
method is better controlled: **resample** the sentence, letting the model write its own
replacement, so the prefix stays on-distribution and the base condition *is* the control. Filter
resamples by semantic difference from the original (cosine < 0.8, `all-MiniLM-L6-v2`).

**Forced answers, not full continuations.** Measured on our 16 sources, the aim sentence sits a
median 22% through the reasoning, so a natural continuation needs a median of **6,760** further
tokens (p90 8,107, max 11,880). At the measured 56 tok/s (batch 8, real 4.9k-token prefix), 40
full continuations x 16 sources is ~4.5M tokens, roughly 22-25 hours, and would likely OOM.
Forced answers — append `</think>` and let the model answer immediately — cost ~150 tokens
instead of ~7,000, making n=40 affordable at ~30-60 minutes.

The forced-answer limitation is stated in the paper (Sec 2.3): a sentence can be necessary for
some answer yet be reliably reproduced later anyway, making earlier steps look unimportant. So
the full-continuation version is run on a subset as a check rather than skipped.

Three arms share each prefix: `original` (with the aim sentence, sampling noise only),
`resampled` (model's own replacement, bucketed by semantic difference), and `nosent` (nothing at
that position — the floor).

**Sources are chosen before any generation** and logged: rollouts showing the flip pattern E1
identified (first in-CoT estimate on the bad side, final answer on the good side), stratified
across all 9 questions and both directions. Aim sentences were located by judge over numbered
sentences, found in 16/18 (89%), above the plan's 80% precision bar.

## 9. Throughput reference (measured, single RTX 6000 Ada)

| setting | tok/s |
|---|---|
| batch 1, short prompt | 5.1 |
| batch 32, short prompt (~30 tok) | 126.9 |
| batch 4, real 4.9k-token prefix | 29 |
| batch 8, real 4.9k-token prefix | 56 (peak 45.3 GB of 47.4) |

The short-prompt figure is misleading for this workload: KV cache scales with prefix length, and
real prefixes are 1,230-6,870 tokens. Batch 8 is the ceiling for the longest prefixes.

## 10. Phase 3 uses a smaller DENSE model, not the MoE

The behavioural work (E0-E2) runs on Qwen3.5-35B-A3B because it is the paper's most
biased open model. The mechanistic arm does not, because MoE is the wrong substrate
for a causal handle: Gilg et al. App. F.4 found single-direction steering **nearly
inert on a Qwen MoE** (probe r = 0.95, but steering swing ~15x smaller than on dense
Gemma-3-27B). Probing the MoE and finding no steering effect would produce a null we
could not attribute - inert direction, or inert method?

**Chosen: `Qwen/Qwen3.5-9B`** (19.3 GB, dense).
- Same family and generation as the behavioural model, so most likely to exhibit the
  same bias - the probe is meaningless if the effect is absent.
- Dense, so linear steering has a real prior.
- Small enough that a layer sweep and a steering-coefficient sweep are cheap.

Rejected: **Gemma-3-27B**, the model Gilg actually steered successfully. Different
family, Donation Bet effect unverified there, and 2.8x larger. Held as the fallback
if 9B fails its gate.

**Gate before any probe work:** run the same Donation Bet measurement on 9B and
report the bias. If the effect is absent or weak there, the probe has nothing to
find and we switch models rather than reporting an uninterpretable null.

## 11. Known artifact in the forced-answer arm (accepted, not fixed)

Interim data shows `original` with *lower* p_fav than `resampled`. The likely cause
is that forced answers are anchored by numbers appearing in the immediately preceding
sentence: the original aim sentence for source 0 reads "If I provide a conservative
number (e.g., **15M**), it triggers the Bad Cause", and forcing an answer straight
after it pulls toward 15M (below T = 26M), whereas replacements like "So > 26M = Good"
name the threshold and pull up.

So the forced-answer measure is partly reading "what number did the last sentence
mention" rather than "what did that sentence do to the reasoning". This is accepted as
part of the experiment and reported, not silently corrected. The full-continuation run
on a subset is what tests whether it distorts the conclusion - which makes that run
load-bearing rather than a nice-to-have.

## 12. Resampling cannot remove the aim sentence

87.5% of resampled replacements (70/80 on the first two sources) still state an aim,
despite a median cosine of 0.459 to the original - far below the 0.8 "semantically
different" threshold. The model re-derives the aim in different words
("So > 26m = Good.", "High Number = Good.", "Estimate > 26M -> Good Cause.").

Consequences:
- Embedding cosine is the **wrong bucketing** for this question. It measures lexical
  similarity; we need "does this sentence state a target side". Primary bucketing is
  therefore a judge call on exactly that, with cosine retained as the paper-faithful
  secondary split.
- The counterfactual bucket we most want (no aim stated) is the one the model is least
  willing to produce: ~12.5% of resamples, ~80 rows across 16 sources.
- This is itself a result. It is Thought Anchors Sec 2.3's stated limitation observed
  directly: the aim statement is robustly generated at that position, not incidental
  phrasing.

## 13. Two threshold errors, both ours

**Cosine threshold.** Thought Anchors' 0.8 is their dataset's *median* original-vs-resampled
similarity, not a fixed criterion. Ours is 0.485. Applying 0.8 literally produced an unbalanced
split (108/498) that separated nothing; calibrating to our own median gives 303/303 and does
separate. Lesson: when a paper reports a threshold, check whether it is a constant or a statistic
of their data.

**Generation cap.** neutral_T was first run at max_new=9000 and 86% of rollouts truncated - these
traces need ~9,500 tokens. Worse, truncation is length-biased and longer reasoning correlates with
lower bias, so the 37 survivors were a systematically high-bias subsample and could not be used
even as a preliminary. Re-run at 12,500. Thought Anchors did not face this: they used MATH, whose
CoTs are far shorter than these Fermi traces (25-30k characters).

## 14. Hand labels replaced the judge for E2's split

All 524 unique replacement sentences (median 40 characters) were read and labelled by hand:
does this sentence relate the model's own candidate answer to a side of the threshold? 237 (45%)
do. This removed both the embedding filter and the `states_aim` judge from E2's critical path.

It was worth it. The judge scored F1 0.82 against hand labels, and its errors were correlated
with the outcome: the one E2 contrast that cleared zero under judge labels (+0.110) does not
under hand labels (+0.075, CI spanning zero). E2 is null at current power.

**General rule this suggests:** when the items to be labelled are short and the count is in the
hundreds, read them. An automated labeller is for when reading is infeasible, not a default. The
cost here was ~8 rounds of reading; the benefit was overturning a false positive.
