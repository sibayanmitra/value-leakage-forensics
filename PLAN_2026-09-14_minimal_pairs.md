# Plan, 2026-09-14: fix the scope-elasticity design, then reproduce

Written after [`DESIGN_scope_elasticity_v2.md`](DESIGN_scope_elasticity_v2.md), which found two
overclaims in published text and one measure that was too coarse. Order follows delete → simplify →
run → only then scale. Predictions for the new runs are fixed in §4 **before** they start.

---

## 1. What exists (verified 2026-09-14, not remembered)

| thing | state |
|---|---|
| 5 baselines at temperature 1.0 | `results/our_baseline.jsonl` (bridge, giraffes, tbc), `results/scope_baseline.jsonl` (tbc_wide, bridge_narrow), 20 each |
| the scope swap | `results/scope_swap.jsonl`, 40 rows, 1,100,000 → tbc_wide and 26,000,000,000 → bridge_narrow |
| tbc dose-response | `results/tbc_x{30,100,300}.jsonl`, 20 each, plus the older ×1, ×10, ×1000 |
| the 16-cell ladder | spread across `naked_number`, `naked_hi10`, `naked_hi1000`, `naked_lo1000` |
| scoring | `src/score_scope.py` (with the one documented judge correction), `audit/scope_elasticity.txt` |
| figure | `figures/fig9_scope.png` from `src/figures_scope.py` |
| CoT reading | all 40 swap traces, `audit/scope_passages_read.txt` |
| GPUs | all four free at 02:20 IST |

## 2. What does not exist

| missing | why it matters |
|---|---|
| baselines at any temperature but 1.0 | the elasticity axis assumes the spread is a property of the question, not the sampler. Untested. |
| minimal pairs | the tbc pair changed an average into a total; both pairs changed the hint list (audit §1) |
| a residual-pull measure in the scorer | exact copying hides a graded pull of up to +2.7 sd (audit §2) |
| blind labels for prediction 4 | I read all 40 traces knowing the condition |
| any second model | the caveat in every version of the write-up |

## 3. Built today, before any run

- `src/gen_neutral.py`: `--temperature` and `--top-p` flags, defaulting to 1.0/1.0 so every earlier
  run is reproduced exactly. Both values are now written into each output row.
- `configs/questions.yaml`: four new questions forming two true minimal pairs. Checked by diffing
  the pairs word by word; the only difference within each pair is the referent phrase.

| pair | wide member | narrow member | the only difference |
|---|---|---|---|
| steps | `tbc_wide_h` | `tbc_narrow_total` | "all TBC classes run at a single fitness studio over one year" vs "a single TBC class" |
| tricks | `bridge_wide_h` | `bridge_narrow_h` | "tournaments in Poland" vs "the final table of the Polish national championship" |

Aggregation ("total ... all participants"), head noun, and the parenthetical hint list are now
identical within each pair. The hint list is phrased so it is coherent for both members ("number of
classes", not "classes per week").

## 4. Predictions, fixed before the runs

**A. Temperature check.** Rank the five existing questions by the spread of their no-number answers
at temperature 1.0: tbc (0.16) < tbc_wide (0.25) < giraffes (0.35) ≈ bridge_narrow (0.36) < bridge
(0.62). At temperature 0.7 every spread should shrink, but **the rank order should be preserved**,
specifically tbc < giraffes < bridge. If the order scrambles, the spread is substantially a property
of the sampler and the z axis in `RECORD.md` §8b has to be rebuilt or dropped.

**B. The clean swap.** With aggregation and hints held fixed:
1. `tbc_narrow_total` + 1,100,000 is copied **≤ 5/20**.
2. `tbc_wide_h` + 1,100,000 is copied **≥ 15/20**.
3. `bridge_wide_h` + 26,000,000,000 is copied **≥ 12/20**.
4. `bridge_narrow_h` + 26,000,000,000 is copied **≤ 5/20**.

**What would falsify.** If the narrow members now copy at rates similar to the wide members, then
the original result was carried by the aggregation change or the hint list rather than by scope, and
the causal claim in `RECORD.md` §8b must be withdrawn.

**C. Residual pull.** In the cells that refuse, the non-copiers' median should still sit above their
own baseline. Predicted, from the existing dose-response: between +0.5 and +3 sd.

## 5. Order of runs

Baselines must finish before the swaps, because the swap numerals are scored against them.

| # | run | GPU | rows | needs |
|---|---|---|---|---|
| 1 | 4 new questions, no number, temp 1.0 | 0 | 80 | — |
| 2 | 5 old questions, no number, temp 0.7 | 1 | 100 | — |
| 3 | clean swap: 1,100,000 → both steps questions | 0 | 40 | run 1 |
| 4 | clean swap: 26,000,000,000 → both tricks questions | 1 | 40 | run 1 |

Two GPUs, per the shared-box rule. Runs 1 and 2 are independent and start together.

## 6. Analysis to write while the runs are going

- `src/score_scope.py`: add the residual-pull column (median of non-copiers, in sd of that
  question's baseline) to every cell, old and new.
- Replace the Spearman with cross-question concordance in the scorer output, matching the correction
  already made to `RECORD.md`.
- A blind relabelling pass for prediction 4: strip the condition, shuffle, label, then unblind.

## 7. Only after all of the above

The second model (Qwen3.5-9B, already gated and shown to copy a bare numeral 58/60 against 0/60).
Reproducing a design before §3–§6 are settled would give the flaws a larger sample and more
confidence, which is the thing to avoid.
