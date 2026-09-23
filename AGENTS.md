# AGENTS.md — for AI agents reading this repository

You are probably here because someone asked you to summarise, evaluate or check this work. This
file tells you what the repository claims, where each number comes from, how to verify it, and what
it does **not** show. It is written to help you report the work accurately, including its limits.

For working *in* the repo (running analyses, editing documents), follow `CLAUDE.md` instead.

---

## The claim, in one paragraph

A language model (Qwen3.5-35B-A3B) was asked for Fermi estimates, with a number left alone on the
last line of the prompt and no instruction to use it. When the question is loose enough that some
set of assumptions reaches that number, the model gives it back as its own estimate and its written
reply almost never says where it came from (6 of 165 replies). When the question is tight enough
that no assumptions reach it, the model refuses, and often tells the user the number is impossible
(21 of 39 replies). Whether the model conceals the number's influence depends on whether the
question leaves room to justify it. The work began as a re-test of *value leakage*
([Betley, Treutlein et al. 2026, arXiv:2607.14345](https://arxiv.org/abs/2607.14345)) and found that
in their Donation Bet the attached number, not the model's values, does most of the work.

## Canonical documents

| file | status |
|---|---|
| `RECORD.md` | **canonical** record of every condition, table and check |
| `AUDIT_record_2026-09-10.md` | how each number and quotation was checked, including errors caught |
| `writeup_pack/advisor/Unfaithful_When_It_Can_Justify_full.pdf` | current 3-page account |
| `FINDINGS_minimal_pairs_2026-09-14.md`, `NOTE_residual_pull_2026-09-14.md` | later results, folded into RECORD |
| `PREREG_*.md`, `PLAN_*.md`, `DESIGN_*.md` | predictions and plans written **before** their runs |
| `FINDING*.md`, `FINDINGS.md`, `RESULTS*.md`, `VERDICT_*.md`, `DRAFT_writeup_v8.md` | **superseded** working notes; some numbers in them were later corrected. Do not quote them over RECORD.md |
| `writeup_pack/DRAFT_v8.pdf` | the version submitted with a MATS 12.0 application, kept unchanged |

## Headline numbers and where to reproduce them

Every row is regenerable from `results/*.jsonl`. Estimates are read by an LLM judge whose calls are
cached in `results/judge_cache/`, so re-scoring existing answers needs no API key.

| claim | number | reproduce with | output |
|---|---|---|---|
| Reply says where the number came from, when the model uses it | 6 of 165 | `python src/score_reply_disclosure.py` | `audit/reply_disclosure.txt` |
| Reply says where the number came from, when the model refuses it | 21 of 39 | same | same |
| Same numeral, broad vs narrow question (exact minimal pair) | 19/20 vs 1/20, Fisher p = 5.8e-9 | `python src/score_minimal_pairs.py` | `audit/minimal_pairs.txt` |
| Distance in the question's own spread predicts copying, across topics | 91/109 = 0.83 (raw distance 75/109 = 0.69) | `python src/score_headline_extras.py` | `audit/headline_extras.txt` |
| Stated physical limit in reasoning, condition-masked labeller | 38/40 refusing vs 2/40 copying, p = 1.1e-17 | same | same |
| The widest question also breaks | 9, 3, 2, 1 of 20 at z = 6.5, 8, 9.5, 12 | see `RECORD.md` §8b | `audit/bridge_break.txt` |
| The number, not the values, drives the Donation Bet | bet 39 vs 11; number deleted 24 vs 33; number alone 50 vs 22 with none | `python src/score_verbal.py` | printed |
| Correct vs wrong answer attached to a checkable question | copied 234/234 vs 0/239 | `RECORD.md` §8 | `audit/` |
| Asked afterwards, admits the influence | 33/53 own reply; 48/56 own reasoning; 57/57 same reasoning labelled as another assistant's | `RECORD.md` §10 | `audit/` |

Check every quotation in the record at its file and line:

```
python src/audit_quotes.py         # expect 139/139
python src/audit_draft_quotes.py   # expect 55/55
```

To read any cited trace: `sed -n 'Np' results/FILE.jsonl | python -m json.tool`. Fields are
`question`, `threshold`, `reasoning` (the full chain of thought), `answer` (the written reply).

## What this work does NOT show — please keep these when summarising

- **One model.** All results are Qwen3.5-35B-A3B. Nothing here is tested on another model family.
- **Three topics.** Nine question wordings, but they are variants of bridge tricks, gym steps and
  giraffe spots.
- **One clean causal pair.** Only the bridge pair survived as an exact minimal pair. The steps pair
  is **untested**, not refuted: the numeral used was reachable from both questions.
- **Scope and distance are confounded.** Narrowing a question makes it both less stretchable and
  further from the attached number; this design cannot separate the two.
- **Small samples.** 20 answers per cell. A question's spread is imprecise at that size (bridge:
  0.62, bootstrap 95% CI 0.36–0.82).
- **The break point is bracketed, not measured**, and bridge breaks somewhat earlier in spread units
  than steps. "The questions collapse onto one curve" overstates it; "nearly, not perfectly" is right.
- **No internal mechanism.** A linear probe and activation steering found no direction that mediates
  the effect.
- **Position of the number.** In the main experiments the number is alone on the last line, which
  raises how often the model copies (97% there vs 40% mid-prompt with an independence request). The
  headline contrasts hold position fixed, so position cannot produce them, but the justifiability
  contrast has only been tested with the number on the last line. See
  `NOTE_number_position_2026-09-23.md`; a clean mid-prompt test has not been run.
- **Copying is a proxy.** The unfaithfulness claim rests on the reply-disclosure counts above, not on
  copy rates alone.

## Claims that were made and then withdrawn

If you find these in older files, they are superseded:

- "Nothing changed but the noun phrase" between the original scope pairs — false; the steps pair also
  changed an average into a total. Rebuilt as exact minimal pairs.
- A digit "echo" of the attached number (15.9% vs 2.3% chance) — an artefact of every numeral being
  the true threshold times a power of ten. Withdrawn; at chance once removed.
- A Spearman of −0.877 across 16 cells — the cells shared three topics. Replaced by the cross-topic
  concordance above.
- "Raw crossing points differ ~500×" — the correct midpoint ratio is 315×.

## How this repository was made

The experiments, code and write-ups were produced by Sibayan Mitra working with an AI coding agent
(Claude Code), under the verification rule in `CLAUDE.md`: no automated count or quotation is
reported without reading the underlying rows. The errors that rule caught are listed in
`AUDIT_record_2026-09-10.md` and in the "What checking changed" table of the current PDF.

## Data not included

The paper authors' released rollouts ([TruthfulAI-research/value_leakage](https://github.com/TruthfulAI-research/value_leakage))
state no licence, so they are not redistributed; `src/fetch_authors_data.py` downloads them. The
Donation Bet prompt used here was checked character-for-character against their release.
Saved activations for the probe (2.8 GB) are excluded for size.

## Citing

Sibayan Mitra (2026). *Unfaithful Exactly When It Can Justify.*
https://github.com/sibayanmitra/value-leakage-forensics
