# The Number, Not the Values

A forensic study of the Donation Bet from Betley, Treutlein et al. (2026,
[arXiv:2607.14345](https://arxiv.org/abs/2607.14345)) on Qwen3.5-35B-A3B. It takes the paper's prompt
apart one sentence at a time to separate the model's values from the number in the prompt, then follows
where the model's honesty breaks: in its reasoning, its written answer, and what it says about itself
afterwards. MATS 12.0 application project (Neel Nanda's stream).

## Start here

| file | what it is |
|---|---|
| [`DRAFT_writeup_v8.md`](DRAFT_writeup_v8.md) ([PDF](writeup_pack/DRAFT_v8.pdf)) | the write-up |
| [`RECORD.md`](RECORD.md) | the canonical record: every condition, table and check |
| [`AUDIT_record_2026-09-10.md`](AUDIT_record_2026-09-10.md) | how each number and quotation was checked; the outputs it cites are in [`audit/`](audit/) |
| [`NOTE_side_choice_and_self_serving_denial.md`](NOTE_side_choice_and_self_serving_denial.md) | the side-picking and denial results in detail, with the literature |
| [`PREREG_scope_elasticity_2026-09-12.md`](PREREG_scope_elasticity_2026-09-12.md) | predictions fixed before the scope runs; scored in `RECORD.md` §8b |
| [`RUNS.log`](RUNS.log) | every generation run: model, settings, row counts, start and end times |
| [`CLAUDE.md`](CLAUDE.md) | the project's verification rule: no automated count is reported without reading the rows |

## Where the chains of thought are

Every model answer is one line of `results/<condition>.jsonl`. The fields are `question`, `direction`,
`threshold`, `reasoning` (the full chain of thought), `answer` (the written reply) and `truncated`.
"Line N" in the write-up means row N of the file, counting from 1:

```
sed -n '6p' results/above_good_26k.jsonl | python3 -m json.tool
```

| condition (names as in the write-up) | file |
|---|---|
| no number | `our_baseline.jsonl` (only the bridge, giraffes and tbc rows are used) |
| the paper's bet, good cause if above / if below | `above_good_26k.jsonl` / `below_ours.jsonl` |
| values without the number | `valence_above.jsonl`, `valence_below.jsonl` |
| number without value framing | `neutral_T_26k.jsonl` |
| only the number, attached at the end | `naked_number.jsonl`; precise numbers `precise_*.jsonl` |
| direction without a number | `verbal_high.jsonl`, `verbal_low.jsonl` |
| scope elasticity: no number, two new questions | `scope_baseline.jsonl` (`tbc_wide`, `bridge_narrow`) |
| scope elasticity: same numeral, scope moved | `scope_swap.jsonl` |
| tbc dose-response, ×30 / ×100 / ×300 | `tbc_x30.jsonl`, `tbc_x100.jsonl`, `tbc_x300.jsonl` |
| checked question with a wrong answer attached | `stray_wrong_16k.jsonl` (right answers in the matching `stray_right` files) |
| disclosure: its answer only / its own reasoning / another assistant's | `disclose3_*.jsonl` / `disclose_cot_own.jsonl` / `disclose_cot_third.jsonl` |
| rewriting the denials, whole reply / at chosen sentences | `resample_denials_p*.jsonl` / `resample_sentences.jsonl` (continuations in `cont`) |

[`RESULTS_INDEX.md`](RESULTS_INDEX.md) is an older file-by-file index (from `src/make_index.py`); it
may miss files added after it was generated.

## Labels read by hand

`configs/hand_labels/` holds one file per reading pass. Each file's `_what` field says exactly what was
read and how. These labels were produced by reading the model's text, one reader, not blind to the
condition, and the reader was the AI agent used in this project (see below). They are there to be
checked.

| file | what it labels |
|---|---|
| `valence_no_number.json` | values without the number: does the reasoning see the incentive, and act on it? |
| `verbal_direction.json` | direction without a number: the same question |
| `paperbet_side_choice.json` | the paper's bet: does the reasoning pick the side on purpose, and what does the reply say? |
| `naked_number_decision.json`, `naked_invite_*.json` | only the number attached: does it decide to use it, and how does it explain it? |
| `disclose_cot_own_denials.json` | the 8 own-reasoning denials |
| (read directly, no label file) | the 40 scope-swap traces: `audit/scope_passages_read.txt` |
| `resample_denials_no.json`, `resample_sentences_reading.json` | every rewritten denial |

## Checking a number or a quotation

```
python3 src/audit_quotes.py         # quotations in RECORD.md, at their file and line
python3 src/audit_draft_quotes.py   # quotations used in the drafts
python3 src/audit_numbers.py        # every decimal in RECORD.md must come from a script output
```

Estimates are read off each answer by an LLM judge (`src/extract.py`: `deepseek/deepseek-v4-flash-0731`
through OpenRouter, temperature 0, JSON schema `{"value": integer|null}`). Every call is cached in
`results/judge_cache/`, so re-scoring existing answers needs no API key. New answers need
`OPENROUTER_API_KEY`.

## Reproducing

Python 3.10, `pip install -r requirements.txt`, and the model `Qwen/Qwen3.5-35B-A3B-FP8` through
Hugging Face Transformers on one 48 GB GPU. Most conditions come from `src/gen_neutral.py` with a
condition name from `configs/prompts.yaml`. Each run's exact command and settings are in `RUNS.log`.
The launch scripts in `audit/launch/` still contain the original server's paths.

## Not included

- **`.venv/`**: the environment is described by `requirements.txt`.
- **`results/*.npy`**: saved activations for the probe (2.8 GB), over GitHub's file limit, and
  regenerable with the probe scripts in `src/`.
- **The paper authors' data**: their release ([TruthfulAI-research/value_leakage](https://github.com/TruthfulAI-research/value_leakage))
  shows no licence, so it is not copied here. `src/fetch_authors_data.py` downloads their Qwen3.5
  rollouts into `data/authors_qwen35/`. Several scripts read `results/authors_extracted.jsonl`, which
  is derived from that data and also not included. It supplies the thresholds: bridge 26,000,000,
  giraffes 20,200,000, tbc 1,100.

## Notes

- The `FINDING*`, `FINDINGS*`, `RESULTS*`, `VERDICT_*` and `DESIGN_*` files are working notes from
  earlier in the project, and some of their numbers were later superseded. `RECORD.md` and the v8
  write-up are canonical.
- The code, runs, counts and draft text were produced with an AI coding agent (Claude Code), under
  the verification rule in `CLAUDE.md`. The write-up's "What I checked" section and
  `AUDIT_record_2026-09-10.md` list the errors that rule caught.
