"""Generate RESULTS_INDEX.md: every result file with its wall-clock time, size and meaning.

Written so that during the write-up you can go from "which file has the 2x2 numbers?" to a
path in one look, and from a path back to the document that quotes it.
"""
import json, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path

R = Path("results")

# curated: file -> (experiment group, what it is, which doc quotes it)
DESC = {
 "our_baseline":      ("2x2 grid", "baseline: no number, no values", "FINDING_resists_values_not_numbers.md"),
 "neutral_ours3":     ("2x2 grid", "neutral_T: number stated, nothing at stake", "FINDING_resists_values_not_numbers.md"),
 "neutral_T_26k":     ("2x2 grid", "neutral_T REGENERATED at cap 26000 (fixes truncation dropout)", "—"),
 "above_ours3":       ("2x2 grid", "above_good: the paper's condition", "FINDING_resists_values_not_numbers.md"),
 "above_good_26k":    ("2x2 grid", "above_good REGENERATED at cap 26000 (fixes truncation dropout)", "—"),
 "below_ours":        ("2x2 grid", "below_good: the paper's condition, mirrored", "FINDING_resists_values_not_numbers.md"),
 "valence_above":     ("2x2 grid", "the bet, number sentence DELETED, above-is-good", "FINDING_resists_values_not_numbers.md"),
 "valence_below":     ("2x2 grid", "the bet, number sentence DELETED, below-is-good", "FINDING_resists_values_not_numbers.md"),
 "naked_number":      ("answer key", "bare numeral only: 59/60 exact copies", "FINDING_answer_key.md"),
 "naked_hi10":        ("answer key", "numeral x10 too large", "FINDING_answer_key.md"),
 "naked_hi1000":      ("answer key", "numeral x1000 too large", "FINDING_answer_key.md"),
 "naked_lo1000":      ("answer key", "numeral /1000 too small", "FINDING_answer_key.md"),
 "bare_number_full":  ("answer key", "number mentioned casually in conversation, all 3 questions (n=60)", "RECORD.md"),
 "bare_number":       ("answer key", "PILOT, superseded by bare_number_full: bridge only, n=20", "—"),
 "stray_number":      ("generalisation", "verifiable questions + stray numeral: does copying cost accuracy?", "—"),
 "warned_anchor":     ("turn it off", "above_good + 'do not let the number anchor you'", "VERDICT_anchoring.md"),
 "warned_values":     ("turn it off", "above_good + 'do not let the bet influence you'", "VERDICT_anchoring.md"),
 "warned_placebo":    ("turn it off", "above_good + 'do not let my phrasing influence you' (PLACEBO arm)", "—"),
 "disclose3_naked_number": ("disclose", "influence CERTAIN; two-phase forced verdict", "—"),
 "disclose3_above_good":   ("disclose", "the paper's condition; two-phase forced verdict", "—"),
 "disclose3_baseline":     ("disclose", "no number ever shown: false-positive control", "—"),
 "precise_bridge":    ("presentation", "B precise numeral 26,143,882 (gate for DESIGN_unfaithful_presentation.md)", "FINDING_precise_numeral_2026-09-10.md"),
 "precise_giraffes":  ("presentation", "B precise numeral 20,311,706", "FINDING_precise_numeral_2026-09-10.md"),
 "precise_tbc":       ("presentation", "B precise numeral 1,106 (weak rung: only 4 digits)", "FINDING_precise_numeral_2026-09-10.md"),
 "naked_invite":      ("presentation", "naked_number + explicit invitation to disclose (S2 artifact test)", "FINDING_precise_numeral_2026-09-10.md"),
 "disclose3_precise": ("presentation", "S3 direct question on the precise arm: admits 0.983 among copies", "FINDING_precise_numeral_2026-09-10.md"),
 "disclose_cot_own":   ("disclose", "naked_number replay WITH its turn-1 reasoning shown as its own; src/score_disclose_cot.py", "RECORD.md"),
 "disclose_cot_third": ("disclose", "same reasoning shown as another assistant's (third-party attribution); src/score_disclose_cot.py", "RECORD.md"),
 "resample_denials_p0": ("resampling", "own-frame denials + matched admissions resampled from the start of turn 2, part 0 (GPU1); src/score_resample_denials.py", "RECORD.md"),
 "resample_denials_p1": ("resampling", "same, part 1 (GPU2)", "RECORD.md"),
 "resample_sentences": ("resampling", "step 2: reliable deniers resampled before/after chosen sentences (configs/resample_positions.json); src/score_resample_sentences.py", "RECORD.md"),
 "steer_dm":          ("steering", "35B difference-of-means steering, 4 arms (positive control FAILED)", "FINDINGS_backstop_2026-09-07.md"),
 "e2_all_scored":     ("resampling", "aim-sentence resampling, scored, with hand labels", "FINDINGS_e2_deep_2026-09-07.md"),
 "sweep_src1":        ("resampling", "position sweep, source 1: spread positions, full continuations", "FINDINGS_position_sweep_2026-09-10.md"),
 "sweep_src5":        ("resampling", "position sweep, source 5: spread positions, full continuations", "FINDINGS_position_sweep_2026-09-10.md"),
 "sweep_src6":        ("resampling", "position sweep, source 6: spread positions, full continuations", "FINDINGS_position_sweep_2026-09-10.md"),
 "sweep_rev1":        ("resampling", "source 1 COMMITMENT sentence resampled: +0.000, 15/15 still copy", "FINDINGS_position_sweep_2026-09-10.md"),
 "sweep_rev5":        ("resampling", "source 5 COMMITMENT sentence resampled: +0.000, 15/15 still copy", "FINDINGS_position_sweep_2026-09-10.md"),
 "sweep_rev6":        ("resampling", "source 6 objection sentence resampled: +0.000, 15/15 still copy", "FINDINGS_position_sweep_2026-09-10.md"),
 "authors_extracted": ("source data", "the authors' released rollouts, answers extracted", "RESULTS.md"),
}
SUPERSEDED = {
 "disclose_naked_number": "700-token cap: 0/59 replies reached a verdict. UNUSABLE.",
 "disclose_above_good":   "700-token cap: 0/53 replies reached a verdict. UNUSABLE.",
 "disclose_baseline":     "700-token cap: 0/100 replies reached a verdict. UNUSABLE.",
 "disclose2_naked_number":"4000-token cap, no </think> delimiter: only fast repliers parsed. UNUSABLE.",
 "disclose2_above_good":  "4000-token cap, same defect. UNUSABLE.",
 "disclose2_baseline":    "killed mid-run, same defect. UNUSABLE.",
 "neutral_a_TRUNCATED_FAILED": "86% truncated at cap 9000. Kept as a record.",
 "neutral_b_TRUNCATED_FAILED": "86% truncated at cap 9000. Kept as a record.",
}

def stamp(p):
    return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

def rows(p):
    try:
        return sum(1 for _ in open(p))
    except Exception:
        return "-"

def main():
    groups = {}
    for stem, (grp, what, doc) in DESC.items():
        p = R / f"{stem}.jsonl"
        if p.exists():
            groups.setdefault(grp, []).append((stamp(p), stem, rows(p), what, doc))
    out = ["# Results index",
           "",
           f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
           "Times are file modification time, i.e. when the run finished writing.",
           "", "Regenerate with `.venv/bin/python src/make_index.py`.", ""]
    for grp in ["2x2 grid", "answer key", "generalisation", "turn it off", "disclose",
                "resampling", "presentation", "steering", "source data"]:
        if grp not in groups:
            continue
        out += [f"## {grp}", "",
                "| finished | file | rows | what it is | quoted in |",
                "|---|---|---|---|---|"]
        for t, stem, n, what, doc in sorted(groups[grp]):
            out.append(f"| {t} | `results/{stem}.jsonl` | {n} | {what} | {doc} |")
        out.append("")
    out += ["## Superseded / unusable — kept deliberately", "",
            "| finished | file | rows | why it is not used |", "|---|---|---|---|"]
    for stem, why in sorted(SUPERSEDED.items()):
        p = R / f"{stem}.jsonl"
        if p.exists():
            out.append(f"| {stamp(p)} | `results/{stem}.jsonl` | {rows(p)} | {why} |")
    out += ["", "## Write-ups", ""]
    for md in sorted(Path(".").glob("*.md")):
        if md.name == "RESULTS_INDEX.md":
            continue
        out.append(f"- **{md.name}** — last edited {stamp(md)}")
    Path("RESULTS_INDEX.md").write_text("\n".join(out) + "\n")
    print(f"wrote RESULTS_INDEX.md ({len(out)} lines)")

if __name__ == "__main__":
    main()
