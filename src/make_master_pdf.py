"""One PDF with everything needed to write the write-up and executive summary.

Part 1 the draft (DRAFT_writeup_v7.md) · Part 2 writing materials (WRITEUP_MATERIALS.md) · Part 3 the
full record (RECORD.md) · Part 4 the audit (AUDIT_record_2026-09-10.md) · Part 5 raw chains of thought.
Figures come from figures/ (live copies). Run with system python3 (markdown + weasyprint CLI).
"""
import shutil
import re, subprocess, sys
from pathlib import Path
import markdown
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_pdf import CSS

ROOT = Path(__file__).resolve().parent.parent
PARTS = [
    ("Part 1 — Draft write-up v7 (rewrite in your words)", "DRAFT_writeup_v7.md"),
    ("Part 2 — Writing materials: tables, prompts, verbatim examples with lines", "WRITEUP_MATERIALS.md"),
    ("Part 3 — The full record: definitions, setup, every experiment, validation, errors", "RECORD.md"),
    ("Part 4 — Audit: how every number and quotation was checked", "AUDIT_record_2026-09-10.md"),
    ("Part 5a — Raw chains of thought: disclosure", "COT_disclosure.md"),
    ("Part 5b — Raw chains of thought: the bet without the number", "COT_bet_without_number.md"),
]
FIG = re.compile(r"^\[\[FIG:(fig[0-9]_[a-z_]+\.png)\|(.+?)\]\]\s*$")


def prep(md):
    """Figures to absolute paths; every heading demoted one level (outside code fences) so that
    only the Part titles are H1 and force a page break."""
    out, fenced = [], False
    for ln in md.split("\n"):
        if ln.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"^#{1,5} ", ln):
            ln = "#" + ln
        m = FIG.match(ln.strip())
        if m:
            fn, cap = m.groups()
            out += ["", f"![{cap}]({ROOT}/figures/{fn})", "", f"*Figure `{fn}` — {cap}*", ""]
        else:
            out.append(ln.replace("](figures/", f"]({ROOT}/figures/").replace("[TOC]", ""))
    return "\n".join(out)


def main():
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    cover = ['<div class="cover"><h1 class="first">The Number, Not the Values</h1>',
             "<p class='lead'>Everything needed to write the MATS 12.0 write-up and executive summary, "
             "in one file. Qwen3.5-35B-A3B. Every number recomputed from <code>results/</code>; every "
             "quotation checked word for word at its file and line. Built 2026-09-10.</p>",
             "<h2>How to use this</h2><ol>"
             "<li><b>Part 1</b> is a draft in Ritesh's structure. Rewrite the executive summary and "
             "prose in your own words.</li>"
             "<li><b>Part 2</b> has paste-ready tables, the exact prompts, and verbatim examples, each "
             "with the command to open it.</li>"
             "<li><b>Part 3</b> is the complete record, in order, including what did not work.</li>"
             "<li><b>Part 4</b> says how each number and quote was checked, and what was corrected.</li>"
             "<li><b>Part 5</b> is raw chain of thought, for choosing your own examples.</li></ol>",
             "<h2>Contents</h2><ol>"] + [f"<li>{t}</li>" for t, _ in PARTS] + ["</ol></div>"]
    body = cover
    for title, fn in PARTS:
        text = prep((ROOT / fn).read_text())
        md.reset()
        body.append(f"<h1 class='part'>{title}</h1>")
        body.append(md.convert(text))
        print(f"  added {fn} ({len(text):,} chars)")
    css = CSS + ("\nh1 { page-break-before: always; }\n"
                 "h1.part { font-size: 22pt; color: #2a5f7f; border-bottom: 3px solid #2a5f7f; "
                 "margin-top: 60mm; }\n")
    html = ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>" + "\n".join(body) + "</body></html>")
    (ROOT / "writeup_pack" / "_master.html").write_text(html)
    out = ROOT / "writeup_pack" / "EVERYTHING_the_number_not_the_values.pdf"
    subprocess.run([(shutil.which("weasyprint") or "weasyprint"),
                    str(ROOT / "writeup_pack" / "_master.html"), str(out)], check=True)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
