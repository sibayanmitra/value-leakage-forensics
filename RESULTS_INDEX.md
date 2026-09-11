# Results index

Generated 2026-09-11 12:12. Times are file modification time, i.e. when the run finished writing.

Regenerate with `.venv/bin/python src/make_index.py`.

## 2x2 grid

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-06 21:25 | `results/our_baseline.jsonl` | 100 | baseline: no number, no values | FINDING_resists_values_not_numbers.md |
| 2026-09-06 22:45 | `results/neutral_ours3.jsonl` | 60 | neutral_T: number stated, nothing at stake | FINDING_resists_values_not_numbers.md |
| 2026-09-06 22:46 | `results/above_ours3.jsonl` | 60 | above_good: the paper's condition | FINDING_resists_values_not_numbers.md |
| 2026-09-07 03:23 | `results/valence_above.jsonl` | 60 | the bet, number sentence DELETED, above-is-good | FINDING_resists_values_not_numbers.md |
| 2026-09-07 03:36 | `results/valence_below.jsonl` | 60 | the bet, number sentence DELETED, below-is-good | FINDING_resists_values_not_numbers.md |
| 2026-09-07 03:52 | `results/below_ours.jsonl` | 60 | below_good: the paper's condition, mirrored | FINDING_resists_values_not_numbers.md |
| 2026-09-08 05:29 | `results/neutral_T_26k.jsonl` | 60 | neutral_T REGENERATED at cap 26000 (fixes truncation dropout) | — |
| 2026-09-08 08:39 | `results/above_good_26k.jsonl` | 60 | above_good REGENERATED at cap 26000 (fixes truncation dropout) | — |

## answer key

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-06 18:24 | `results/bare_number.jsonl` | 20 | PILOT, superseded by bare_number_full: bridge only, n=20 | — |
| 2026-09-06 18:46 | `results/naked_number.jsonl` | 60 | bare numeral only: 59/60 exact copies | FINDING_answer_key.md |
| 2026-09-08 01:14 | `results/naked_hi10.jsonl` | 60 | numeral x10 too large | FINDING_answer_key.md |
| 2026-09-08 01:23 | `results/naked_lo1000.jsonl` | 60 | numeral /1000 too small | FINDING_answer_key.md |
| 2026-09-08 01:28 | `results/naked_hi1000.jsonl` | 60 | numeral x1000 too large | FINDING_answer_key.md |
| 2026-09-08 20:34 | `results/bare_number_full.jsonl` | 60 | number mentioned casually in conversation, all 3 questions (n=60) | RECORD.md |

## generalisation

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-08 07:13 | `results/stray_number.jsonl` | 720 | verifiable questions + stray numeral: does copying cost accuracy? | — |

## turn it off

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-07 05:18 | `results/warned_anchor.jsonl` | 60 | above_good + 'do not let the number anchor you' | VERDICT_anchoring.md |
| 2026-09-07 05:32 | `results/warned_values.jsonl` | 60 | above_good + 'do not let the bet influence you' | VERDICT_anchoring.md |
| 2026-09-08 04:01 | `results/warned_placebo.jsonl` | 60 | above_good + 'do not let my phrasing influence you' (PLACEBO arm) | — |

## disclose

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-08 03:00 | `results/disclose3_naked_number.jsonl` | 59 | influence CERTAIN; two-phase forced verdict | — |
| 2026-09-08 03:26 | `results/disclose3_above_good.jsonl` | 53 | the paper's condition; two-phase forced verdict | — |
| 2026-09-08 04:08 | `results/disclose3_baseline.jsonl` | 100 | no number ever shown: false-positive control | — |
| 2026-09-11 00:52 | `results/disclose_cot_third.jsonl` | 59 | same reasoning shown as another assistant's (third-party attribution); src/score_disclose_cot.py | RECORD.md |
| 2026-09-11 01:09 | `results/disclose_cot_own.jsonl` | 59 | naked_number replay WITH its turn-1 reasoning shown as its own; src/score_disclose_cot.py | RECORD.md |

## resampling

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-06 03:51 | `results/e2_all_scored.jsonl` | 3960 | aim-sentence resampling, scored, with hand labels | FINDINGS_e2_deep_2026-09-07.md |
| 2026-09-09 21:28 | `results/sweep_src1.jsonl` | 60 | position sweep, source 1: spread positions, full continuations | FINDINGS_position_sweep_2026-09-10.md |
| 2026-09-09 21:41 | `results/sweep_src6.jsonl` | 60 | position sweep, source 6: spread positions, full continuations | FINDINGS_position_sweep_2026-09-10.md |
| 2026-09-09 21:59 | `results/sweep_src5.jsonl` | 90 | position sweep, source 5: spread positions, full continuations | FINDINGS_position_sweep_2026-09-10.md |
| 2026-09-10 08:34 | `results/sweep_rev1.jsonl` | 30 | source 1 COMMITMENT sentence resampled: +0.000, 15/15 still copy | FINDINGS_position_sweep_2026-09-10.md |
| 2026-09-10 08:38 | `results/sweep_rev5.jsonl` | 30 | source 5 COMMITMENT sentence resampled: +0.000, 15/15 still copy | FINDINGS_position_sweep_2026-09-10.md |
| 2026-09-10 09:02 | `results/sweep_rev6.jsonl` | 30 | source 6 objection sentence resampled: +0.000, 15/15 still copy | FINDINGS_position_sweep_2026-09-10.md |
| 2026-09-11 04:13 | `results/resample_denials_p0.jsonl` | 80 | own-frame denials + matched admissions resampled from the start of turn 2, part 0 (GPU1); src/score_resample_denials.py | RECORD.md |
| 2026-09-11 04:13 | `results/resample_denials_p1.jsonl` | 80 | same, part 1 (GPU2) | RECORD.md |
| 2026-09-11 12:06 | `results/resample_sentences.jsonl` | 130 | step 2: reliable deniers resampled before/after chosen sentences (configs/resample_positions.json); src/score_resample_sentences.py | RECORD.md |

## presentation

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-10 15:27 | `results/precise_bridge.jsonl` | 20 | B precise numeral 26,143,882 (gate for DESIGN_unfaithful_presentation.md) | FINDING_precise_numeral_2026-09-10.md |
| 2026-09-10 15:28 | `results/precise_tbc.jsonl` | 20 | B precise numeral 1,106 (weak rung: only 4 digits) | FINDING_precise_numeral_2026-09-10.md |
| 2026-09-10 15:39 | `results/precise_giraffes.jsonl` | 20 | B precise numeral 20,311,706 | FINDING_precise_numeral_2026-09-10.md |
| 2026-09-10 16:02 | `results/disclose3_precise.jsonl` | 60 | S3 direct question on the precise arm: admits 0.983 among copies | FINDING_precise_numeral_2026-09-10.md |
| 2026-09-10 17:25 | `results/naked_invite.jsonl` | 60 | naked_number + explicit invitation to disclose (S2 artifact test) | FINDING_precise_numeral_2026-09-10.md |

## steering

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-07 18:15 | `results/steer_dm.jsonl` | 324 | 35B difference-of-means steering, 4 arms (positive control FAILED) | FINDINGS_backstop_2026-09-07.md |

## source data

| finished | file | rows | what it is | quoted in |
|---|---|---|---|---|
| 2026-09-04 23:51 | `results/authors_extracted.jsonl` | 2700 | the authors' released rollouts, answers extracted | RESULTS.md |

## Superseded / unusable — kept deliberately

| finished | file | rows | why it is not used |
|---|---|---|---|
| 2026-09-08 02:14 | `results/disclose2_above_good.jsonl` | 53 | 4000-token cap, same defect. UNUSABLE. |
| 2026-09-08 02:31 | `results/disclose2_baseline.jsonl` | 96 | killed mid-run, same defect. UNUSABLE. |
| 2026-09-08 02:15 | `results/disclose2_naked_number.jsonl` | 59 | 4000-token cap, no </think> delimiter: only fast repliers parsed. UNUSABLE. |
| 2026-09-07 18:31 | `results/disclose_above_good.jsonl` | 53 | 700-token cap: 0/53 replies reached a verdict. UNUSABLE. |
| 2026-09-07 18:43 | `results/disclose_baseline.jsonl` | 100 | 700-token cap: 0/100 replies reached a verdict. UNUSABLE. |
| 2026-09-07 18:23 | `results/disclose_naked_number.jsonl` | 59 | 700-token cap: 0/59 replies reached a verdict. UNUSABLE. |
| 2026-09-06 00:53 | `results/neutral_a_TRUNCATED_FAILED.jsonl` | 150 | 86% truncated at cap 9000. Kept as a record. |
| 2026-09-06 00:03 | `results/neutral_b_TRUNCATED_FAILED.jsonl` | 120 | 86% truncated at cap 9000. Kept as a record. |

## Write-ups

- **AUDIT_against_neel.md** — last edited 2026-09-08 11:50
- **AUDIT_record_2026-09-10.md** — last edited 2026-09-11 12:12
- **CLAUDE.md** — last edited 2026-09-10 20:51
- **COT_bet_without_number.md** — last edited 2026-09-10 21:05
- **COT_disclosure.md** — last edited 2026-09-08 11:20
- **DESIGN_unfaithful_presentation.md** — last edited 2026-09-10 17:27
- **DRAFT_writeup.md** — last edited 2026-09-08 22:09
- **DRAFT_writeup_v2.md** — last edited 2026-09-11 12:10
- **FINDINGS.md** — last edited 2026-09-07 15:44
- **FINDINGS_backstop_2026-09-07.md** — last edited 2026-09-07 15:44
- **FINDINGS_e2_deep_2026-09-07.md** — last edited 2026-09-10 07:40
- **FINDINGS_position_sweep_2026-09-10.md** — last edited 2026-09-10 09:03
- **FINDING_answer_key.md** — last edited 2026-09-10 18:24
- **FINDING_one_sided.md** — last edited 2026-09-06 14:21
- **FINDING_precise_numeral_2026-09-10.md** — last edited 2026-09-10 21:00
- **FINDING_resists_values_not_numbers.md** — last edited 2026-09-10 18:24
- **METHODS.md** — last edited 2026-09-06 01:43
- **NEELS_QUESTIONS.md** — last edited 2026-09-10 18:24
- **RECORD.md** — last edited 2026-09-11 12:12
- **RESULTS.md** — last edited 2026-09-06 22:52
- **VERDICT_anchoring.md** — last edited 2026-09-10 18:24
- **VERIFY.md** — last edited 2026-09-10 19:55
- **WRITEUP_MATERIALS.md** — last edited 2026-09-11 12:11
- **WRITEUP_SKELETON.md** — last edited 2026-09-08 18:31
