import markdown, subprocess, shutil, sys
from pathlib import Path
here = Path(__file__).resolve().parent
size = sys.argv[1] if len(sys.argv) > 1 else "9.4"
body = markdown.Markdown(extensions=["tables", "sane_lists"]).convert((here / "advisor_summary.md").read_text())
css = f"""
@page {{ size: A4; margin: 12mm 14mm 12mm 14mm;
  @bottom-right {{ content: counter(page) " / " counter(pages); font: 7.5pt 'DejaVu Sans'; color: #888; }} }}
body {{ font-family: 'DejaVu Serif', Georgia, serif; font-size: {size}pt; line-height: 1.34; color: #1a1a1a; }}
h1 {{ font-family: 'DejaVu Sans', sans-serif; font-size: 17pt; margin: 0 0 1mm; letter-spacing: -.2pt; }}
.byline {{ font-family: 'DejaVu Sans', sans-serif; font-size: 8pt; color: #666; margin: 0 0 3mm; }}
h2 {{ font-family: 'DejaVu Sans', sans-serif; font-size: 10.6pt; margin: 3.4mm 0 1.2mm; color: #0b2e59;
      border-bottom: .4pt solid #c9d3e0; padding-bottom: .6mm; break-after: avoid; }}
p {{ margin: 0 0 1.7mm; text-align: left; }}
ul {{ margin: 0 0 1.7mm; padding-left: 4.5mm; }} li {{ margin: 0 0 .8mm; }}
table {{ border-collapse: collapse; width: 100%; margin: 1mm 0 2mm; font-size: {float(size)-1.1:.1f}pt;
         font-family: 'DejaVu Sans', sans-serif; line-height: 1.25; }}
tr {{ break-inside: avoid; }}
th {{ text-align: left; background: #eef2f7; font-weight: 600; }}
th, td {{ border: .4pt solid #cfd6df; padding: .9mm 1.4mm; vertical-align: top; }}
blockquote {{ margin: 1.2mm 0 1.4mm; padding: .6mm 3mm; border-left: 1.6pt solid #0b2e59;
              background: #f5f7fa; font-style: italic; break-inside: avoid; }}
blockquote p {{ margin: 0; }}
code {{ font-family: 'DejaVu Sans Mono', monospace; font-size: 85%; }}
figure {{ margin: 1.5mm 0 2mm; break-inside: avoid; }} img {{ width: 90%; display: block; margin: 0 auto; }}
figcaption {{ font-family: 'DejaVu Sans', sans-serif; font-size: 7.6pt; color: #555; margin-top: .6mm; }}
a {{ color: #0b4f9c; text-decoration: none; }}
strong {{ color: #111; }}
"""
html = here / "_advisor.html"
html.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>It Copies What It Can Justify</title><style>{css}</style></head><body>{body}</body></html>")
out = here / "It_Copies_What_It_Can_Justify.pdf"
subprocess.run([shutil.which("weasyprint"), str(html), str(out)], check=True, capture_output=True)
print(out)
