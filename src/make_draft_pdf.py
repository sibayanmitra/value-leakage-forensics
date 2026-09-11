"""The draft write-up on its own, as a PDF: DRAFT_writeup_vN.md -> writeup_pack/DRAFT_vN.pdf.

usage: python3 src/make_draft_pdf.py [N]   (N defaults to 4)

Same styling as the other PDFs (src/make_pdf.CSS). Figures resolve to absolute paths.
Run with system python3 (markdown + weasyprint CLI), like src/make_master_pdf.py.
"""
import shutil
import re, subprocess, sys
from pathlib import Path
import markdown
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_pdf import CSS

ROOT = Path(__file__).resolve().parent.parent
V = sys.argv[1] if len(sys.argv) > 1 else "4"
SRC, OUT = ROOT / f"DRAFT_writeup_v{V}.md", ROOT / "writeup_pack" / f"DRAFT_v{V}.pdf"


def main():
    text = SRC.read_text().replace("](figures/", f"]({ROOT}/figures/")
    html = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"]).convert(text)
    # the title and the executive summary share page 1; every later top-level section starts a page
    html = html.replace("<h1>Executive Summary</h1>", '<h1 class="nobreak">Executive Summary</h1>', 1)
    css = CSS + ("\nh1 { page-break-before: always; }\nh1:first-of-type, h1.nobreak { page-break-before: avoid; }\n"
                 "img { max-width: 100%; }\n")
    page = f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{html}</body></html>"
    tmp = ROOT / "writeup_pack" / f"_draft_v{V}.html"; tmp.write_text(page)
    subprocess.run([(shutil.which("weasyprint") or "weasyprint"), str(tmp), str(OUT)], check=True)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
