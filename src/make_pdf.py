"""Combine the write-up pack into one PDF, with the figures placed inline.

Uses the system python's `markdown` (3.10) and the weasyprint CLI. Run with system python3,
not the venv (the venv has neither).
"""
import shutil
import re, subprocess, sys
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = [
    ("The plan", "WRITEUP_PLAN.md", "The agreed structure: the one story, what is cut, word budgets, voice rules."),
    ("Materials — tables and examples", "WRITEUP_MATERIALS.md", "Every number recomputed from results/. The seven examples with file and line."),
    ("Skeleton", "WRITEUP_SKELETON.md", "Section scaffold with [YOU WRITE] markers."),
    ("Verify — how to check any claim", "VERIFY.md", "Each load-bearing number, its prompt, its data, and the command to recompute it."),
    ("Neel's four questions", "NEELS_QUESTIONS.md", "Each question paired with its number, figure and chain of thought."),
    ("Audit against his criteria", "AUDIT_against_neel.md", "His grading rubric and where the project stands."),
    ("Raw CoT — disclosure", "COT_disclosure.md", "Admissions and denials across the three arms."),
    ("Raw CoT — the bet without the number", "COT_bet_without_number.md", "All 120 rollouts, categorised."),
]
FIGCAP = {
    "fig1_grid.png": "The 2×2. Columns are what matters: every cell without a number sits at baseline.",
    "fig2_ladder.png": "The scaled numeral ladder, all three questions.",
    "fig3_warnings.png": "Both real warnings work. The placebo does not.",
    "fig4_disclose.png": "Asked directly, it denies being influenced.",
    "fig5_verifiable.png": "The spine: it adopts any number it can build a justification for.",
}

def place_figures(md):
    """After any line naming a figure, insert the image itself."""
    out = []
    for ln in md.split("\n"):
        out.append(ln)
        for fn, cap in FIGCAP.items():
            if fn in ln and not ln.strip().startswith("!["):
                out += ["", f"![{cap}]({ROOT}/writeup_pack/figures/{fn})", "",
                        f"*Figure — {cap}*", ""]
                break
    return "\n".join(out)

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm;
        @bottom-center { content: counter(page); font: 8pt "DejaVu Sans"; color: #888; } }
body { font: 9.7pt/1.45 "DejaVu Serif", Georgia, serif; color: #16181d; }
h1 { font: 700 19pt "DejaVu Sans", sans-serif; margin: 0 0 4pt; page-break-before: always;
     border-bottom: 2px solid #2a5f7f; padding-bottom: 4pt; color: #16181d; }
h1.first { page-break-before: avoid; }
h2 { font: 700 13pt "DejaVu Sans", sans-serif; margin: 14pt 0 4pt; color: #2a5f7f;
     page-break-after: avoid; }
h3 { font: 700 10.5pt "DejaVu Sans", sans-serif; margin: 11pt 0 3pt; page-break-after: avoid; }
p, li { orphans: 2; widows: 2; }
code { font: 8.4pt "DejaVu Sans Mono", monospace; background: #f1f2f5; padding: 0 2px;
       border-radius: 2px; word-break: break-word; }
pre { background: #f6f7f9; border-left: 2px solid #c8ccd4; padding: 6pt 8pt; margin: 6pt 0;
      page-break-inside: avoid; }
pre code { background: none; font-size: 7.9pt; line-height: 1.4; white-space: pre-wrap; }
table { border-collapse: collapse; width: 100%; margin: 7pt 0; font-size: 8.5pt;
        page-break-inside: avoid; }
th { background: #eef1f4; text-align: left; font: 700 8.2pt "DejaVu Sans", sans-serif;
     border-bottom: 1.5px solid #c8ccd4; padding: 3pt 5pt; }
td { border-bottom: 0.5px solid #e2e5ea; padding: 3pt 5pt; vertical-align: top; }
blockquote { margin: 6pt 0 6pt 8pt; padding-left: 8pt; border-left: 2px solid #2a5f7f;
             color: #3c4048; font-style: italic; }
img { max-width: 100%; margin: 6pt auto 2pt; display: block; page-break-inside: avoid; }
em { color: #52514e; }
sub { font-size: 7.4pt; color: #6b6f78; }
.lead { font-size: 9pt; color: #52514e; margin: 2pt 0 10pt; font-style: italic; }
.cover h1 { border: none; font-size: 26pt; page-break-before: avoid; }
.cover { margin-top: 40mm; }
hr { border: none; border-top: 0.5px solid #dfe1e7; margin: 10pt 0; }
"""

def main():
    parts = ['<div class="cover">',
             "<h1 class='first'>Value Leakage Forensics</h1>",
             "<p class='lead'>Write-up pack — plan, materials, verification, and raw chains of "
             "thought.<br>Qwen3.5-35B-A3B · 6,176 rollouts · assembled 2026-09-08</p>",
             "<h2>Contents</h2><ol>"]
    for title, _, blurb in DOCS:
        parts.append(f"<li><b>{title}</b> — {blurb}</li>")
    parts.append("</ol></div>")

    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    for title, fn, blurb in DOCS:
        p = ROOT / "writeup_pack" / fn
        if not p.exists():
            print(f"  skip (missing): {fn}"); continue
        text = place_figures(p.read_text())
        # drop the document's own H1 so the section title is the only one
        text = re.sub(r"^#\s+.*\n", "", text, count=1)
        md.reset()
        parts.append(f"<h1>{title}</h1><p class='lead'>{blurb} &nbsp;·&nbsp; <code>{fn}</code></p>")
        parts.append(md.convert(text))
        print(f"  added {fn} ({len(text):,} chars)")

    html = ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>" + "\n".join(parts) + "</body></html>")
    out_html = ROOT / "writeup_pack" / "_combined.html"
    out_html.write_text(html)
    out_pdf = ROOT / "writeup_pack" / "value_leakage_forensics_pack.pdf"
    subprocess.run([(shutil.which("weasyprint") or "weasyprint"),
                    str(out_html), str(out_pdf)], check=True)
    print(f"\nwrote {out_pdf}")

if __name__ == "__main__":
    main()
