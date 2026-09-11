"""Render DRAFT_writeup.md as a paper-style PDF, figures in place.

System python3 (has markdown 3.10) + weasyprint CLI. The venv has neither.
"""
import shutil
import re, subprocess
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "DRAFT_writeup.md"
OUT  = ROOT / "writeup_pack" / "the_number_not_the_values.pdf"

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm;
        @bottom-center { content: counter(page); font: 8pt "DejaVu Sans"; color: #999; } }
@page :first { @bottom-center { content: ""; } }

/* project-report look: left aligned, sans body, generous spacing. Not a paper. */
body { font: 10.5pt/1.55 "DejaVu Sans", Arial, sans-serif; color: #1a1a1a; text-align: left; }

.title { margin: 0 0 8mm; }
.title h1 { font: 700 23pt/1.2 "DejaVu Sans", sans-serif; margin: 0 0 3mm; border: none;
            page-break-before: avoid; }
.title .sub { font: 11pt/1.45 "DejaVu Sans", sans-serif; color: #444; margin: 0 0 4mm; }
.title .meta { font: 9pt/1.5 "DejaVu Sans", sans-serif; color: #666;
               background: #f4f5f7; padding: 3mm 4mm; border-radius: 2px; }

h1 { font: 700 16pt "DejaVu Sans", sans-serif; margin: 10mm 0 3mm; color: #1a1a1a;
     page-break-after: avoid; border: none; }
h2 { font: 700 12pt "DejaVu Sans", sans-serif; margin: 6mm 0 2mm; color: #1a1a1a;
     page-break-after: avoid; }
h3 { font: 700 10.5pt "DejaVu Sans", sans-serif; margin: 4mm 0 1.5mm; color: #333;
     page-break-after: avoid; }
p { margin: 0 0 3mm; orphans: 2; widows: 2; }
ul, ol { margin: 0 0 3.5mm; padding-left: 6mm; }
li { margin-bottom: 1.6mm; }

img { display: block; max-width: 96%; margin: 5mm auto 2mm; page-break-inside: avoid; }
.cap { font: 9pt/1.4 "DejaVu Sans", sans-serif; color: #555; text-align: left;
       margin: 0 0 6mm; page-break-before: avoid; }

table { border-collapse: collapse; width: 100%; margin: 3mm 0 5mm; font-size: 9.2pt;
        page-break-inside: avoid; }
th { background: #eef1f4; font: 700 8.6pt "DejaVu Sans", sans-serif; padding: 2mm;
     border-bottom: 1.2px solid #b9bfc9; text-align: left; }
td { padding: 1.8mm 2mm; border-bottom: 0.4px solid #e4e6ea; vertical-align: top; }

blockquote { margin: 3.5mm 0 3.5mm 3mm; padding: 2mm 0 2mm 4mm;
             border-left: 3px solid #2a5f7f; background: #f8f9fa;
             font-style: italic; color: #2c2f36; font-size: 9.8pt; page-break-inside: avoid; }
blockquote p { margin-bottom: 1.5mm; }

code { font: 8.6pt "DejaVu Sans Mono", monospace; background: #f1f2f5; padding: 0 1px;
       word-break: break-word; }
pre { background: #f6f7f9; border-left: 2px solid #c8ccd4; padding: 2mm 3mm; margin: 3mm 0;
      page-break-inside: avoid; }
pre code { background: none; font-size: 8pt; white-space: pre-wrap; }
hr { border: none; border-top: 0.5px solid #e0e2e7; margin: 7mm 0; }
em { color: #333; }
"""


def main():
    text = SRC.read_text()
    # strip the drafting note and the H1 (they become the title block)
    text = re.sub(r"^# .*?\n", "", text, count=1)
    note = re.search(r"\*Draft\..*?\*\n", text, re.S)
    note_txt = re.sub(r"^Draft\.\s*", "", note.group(0).strip("*\n ")) if note else ""
    text = text.replace(note.group(0), "") if note else text
    text = text.lstrip("-\n ")
    text = text.replace(str(ROOT) + "/", "")

    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
    body = md.convert(text)
    # captions: any <p> starting with <strong>Figure N.</strong>
    body = re.sub(r"<p>(<strong>Figure \d+\.</strong>)", r'<p class="cap">\1', body)

    title = f"""<div class="title">
      <h1>The Number, Not the Values</h1>
      <p class="sub">What the Donation Bet actually measures, and what the model does with a
      number it is shown.</p>
      <p class="meta"><b>Model:</b> Qwen3.5-35B-A3B (FP8) &nbsp;|&nbsp; <b>Rollouts:</b> 6,176
      &nbsp;|&nbsp; <b>Follows:</b> Betley, Treutlein et al. (2026), <i>Value Leakage</i>,
      arXiv:2607.14345<br><br><b>Note.</b> {note_txt}</p></div>"""

    html = ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>{title}{body}</body></html>")
    tmp = ROOT / "writeup_pack" / "_paper.html"
    tmp.write_text(html)
    subprocess.run([(shutil.which("weasyprint") or "weasyprint"),
                    "-u", str(ROOT) + "/", str(tmp), str(OUT)], check=True)
    print(f"wrote {OUT}")

if __name__ == "__main__":
    main()
