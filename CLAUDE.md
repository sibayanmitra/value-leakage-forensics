# Working rules for this project

## Do not trust regex or classifiers. Read the data yourself.

*Set by the project owner, 2026-09-10. Applies to every analysis, document and write-up here.*

- A regex, keyword count, embedding filter or LLM judge is a **pointer, not a measurement**. Never
  report a count from one without reading the rows it matched, and a sample of the rows it did not.
- Before any number or quote goes into a document: open the underlying rows
  (`sed -n 'Np' results/FILE.jsonl | python3 -m json.tool`) and check, by reading, that they say what
  the claim says. Quote verbatim, with `results/FILE.jsonl` line N.
- State the check beside the number: "regex count, 20/20 hand-checked", "hand-labelled, one reader",
  or "not hand-checked". Never let an unchecked automated count read like a measurement.
- Substring counts are especially unsafe in this data. The model quotes the prompt back ("estimate a
  *specific* quantity"), writes bullets and emphasis, and argues both sides inside one trace, so a
  word appearing is not the model asserting it.
- A forced or extracted verdict is also a classifier. Check a sample against what the text actually
  concludes.

**Why.** Automated labels were wrong here several times, and each was caught only by reading: a regex
for "the CoT acknowledges the number" matched 60/60 baseline rollouts that never saw one; a "57/57
replies mention specificity" count was the prompt being quoted back; two quotations in finding
documents did not exist in the data; a hardcoded per-question figure came from superseded runs.

**Tools.** `src/audit_quotes.py` (exact quote check at the cited line), `src/audit_numbers.py` (every
decimal in RECORD.md must come from a script output), `src/audit_doc_quotes.py` (approximate; confirm
each flag by reading the row).
