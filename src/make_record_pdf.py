"""Build RECORD.pdf: the full experiment record, in order, with figures inline and raw CoT appended.

Figures are read from figures/ (the live copies), NOT writeup_pack/figures/, which holds a
pre-fix fig4. Run with system python3 (needs `markdown` and the weasyprint CLI), not the venv.
"""
import shutil
import re, subprocess, sys
from pathlib import Path
import markdown
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_pdf import CSS

ROOT = Path(__file__).resolve().parent.parent
PARTS = [
    ("RECORD.md", None),
    ("COT_disclosure.md", "Appendix A — Disclosure: the raw reasoning, all three arms"),
    ("COT_bet_without_number.md", "Appendix B — The bet without the number: all 120 chains of thought"),
]
FIG = re.compile(r"^\[\[FIG:(fig[0-9]_[a-z_]+\.png)\|(.+?)\]\]\s*$")


def figures(md):
    out = []
    for ln in md.split("\n"):
        m = FIG.match(ln.strip())
        if m:
            fn, cap = m.groups()
            out += ["", f"![{cap}]({ROOT}/figures/{fn})", "", f"*Figure `{fn}` — {cap}*", ""]
        else:
            out.append(ln)
    return "\n".join(out)


def main():
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list", "toc"])
    body = []
    for i, (fn, title) in enumerate(PARTS):
        text = figures((ROOT / fn).read_text())
        if title:
            text = re.sub(r"^#\s+.*\n", "", text, count=1)
            body.append(f"<h1>{title}</h1>")
        md.reset()
        html = md.convert(text)
        if i == 0:
            html = html.replace("<h1", "<h1 class='first'", 1)
        body.append(html)
        print(f"  added {fn} ({len(text):,} chars)")
    css = CSS + "\nh1 { page-break-before: always; }\n.toc ul { list-style: none; padding-left: 10pt; }\n"
    html = ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>" + "\n".join(body) + "</body></html>")
    (ROOT / "writeup_pack" / "_record.html").write_text(html)
    out = ROOT / "writeup_pack" / "RECORD.pdf"
    subprocess.run([(shutil.which("weasyprint") or "weasyprint"),
                    str(ROOT / "writeup_pack" / "_record.html"), str(out)], check=True)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
