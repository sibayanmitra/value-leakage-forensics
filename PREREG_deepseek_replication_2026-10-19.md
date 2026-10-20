# Pre-registration: does the justifiability gate replicate on a second model?

*Written 2026-10-19, before any counted run. Changes go in the log at the bottom, dated.*

## Why

Every result so far comes from one model (Qwen3.5-35B-A3B). The framing doc's H1–H3 are tested
here on `deepseek/deepseek-v4.1-flash-1017` through OpenRouter, with a hard spending cap of
US$0.50 for everything (generation and judge). This is a replication on a second model, not a new
claim.

## Fixed settings

`src/gen_openrouter.py`, temperature 1.0, reasoning enabled (provider default effort),
`max_tokens` 32000, provider pinned to Relace with no fallback ($0.05/M in, $0.15/M out). Prompts
and questions verbatim from `configs/prompts.yaml` and `configs/questions.yaml`. The 2-row pilot
(`results/deepseek/pilot_unpinned_provider.jsonl`) was served by a different provider and is not
pooled.

## Stage 1 (spend cap: ledger total ≤ $0.25)

| cell | template | question(s) | numeral | n |
|---|---|---|---|---|
| S1 baselines | `baseline` | bridge, tbc, giraffes, bridge_wide_h, bridge_narrow_h, tbc_wide_h, tbc_narrow_total | none | 30 each |
| S2 minimal pair (H1) | `naked_number` | bridge_wide_h, bridge_narrow_h | 26,000,000,000 both | 30 each |
| S3 precise numeral (tier A, H2/H3) | `naked_number` | bridge | 26,143,882 | 30 |

## Stage 2 (only if Stage 1 ends under $0.25; cap $0.45)

RQ2, distance or scope: on bridge_wide_h and bridge_narrow_h, numerals at z = 2, 4, 6, 8, 10 from
**DeepSeek's own** S1 baselines, using the rule in `PREREG_gate_generalisation_2026-10-16.md`
(n = m·10^(z·s), two significant figures, z recomputed from the rounded numeral). 20 per cell.
Cut to z = 2, 6, 10 if the remaining budget does not cover all five.

## Outcome and reading

Adoption = the judge-extracted answer equals the numeral exactly. Every counted adoption is read,
and a sample of non-adoptions. Reply disclosure (H2) and reasoning mention (H3) are read by hand,
one reader (the AI agent), not blind; these are pointers until human labels exist.

## Predictions

- **P1 (H1).** S2: bridge_wide_h adopts more often than bridge_narrow_h, Fisher one-sided p < 0.01.
  Falsified if the narrow member adopts as often or more.
- **P2.** S3: at least 20/30 adopt 26,143,882 exactly. (Qwen: 59/60.) Less than 10/30 counts
  against generality of the precise-numeral result.
- **P3 (H3).** Among adopting S3 rollouts, the reasoning names the numeral in at least 90%.
- **P4 (H2).** Among adopting S3 rollouts, the reply names the numeral as given by the user in
  fewer than half.
- **P5 (RQ2, stage 2).** Exploratory. If adoption at equal z is the same for the wide and narrow
  question, z accounts for the scope effect on this model.

A model that adopts nothing, or adopts everything, makes P1 uninformative, and that will be
reported as such rather than as a failure or success.

## Log

- 2026-10-19: pilot (2 rows) showed ~2.7k completion tokens per rollout, answers committed,
  reasoning returned. Not pooled.
- 2026-10-19, before any counted run: on the pinned Relace endpoint, rollouts are much longer
  (4 probe rows: 8,011–14,747 completion tokens, all finished; one earlier tbc row hit a 16,000 cap
  with no answer). So `max_tokens` goes to 32,000 and the cells shrink to fit the cap (~$0.0016
  per rollout): S1 baselines only for bridge, bridge_wide_h, bridge_narrow_h, 20 each; S2 and S3,
  20 per cell; Stage 2 at z = 2, 6, 10 only, 15 per cell. P2 becomes "at least 13/20". Probe rows
  (`probe_len.jsonl`) are not pooled.
- 2026-10-19, at the user's instruction: **no regex and no LLM judge.** Every committed answer is
  read and recorded by hand into `configs/hand_labels/deepseek_*.json` (one reader, the AI agent,
  not blind); scripts only do arithmetic on those labels.
