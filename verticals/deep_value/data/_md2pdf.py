"""md -> styled HTML -> PDF via headless Chrome. Self-contained, no LaTeX/weasyprint needed."""
import sys, subprocess, tempfile, os
import markdown

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { margin: 1.6cm 1.8cm; }
body { font: 11pt/1.45 -apple-system,'Helvetica Neue',Arial,sans-serif; color:#1a1a1a; max-width:none; }
h1 { font-size:19pt; border-bottom:2px solid #333; padding-bottom:4px; margin-top:0; }
h2 { font-size:14pt; color:#1a3a5a; border-bottom:1px solid #ccc; padding-bottom:2px; margin-top:18px; }
h3 { font-size:12pt; color:#333; }
table { border-collapse:collapse; width:100%; margin:10px 0; font-size:9.5pt; }
th,td { border:1px solid #bbb; padding:4px 7px; text-align:left; vertical-align:top; }
th { background:#eef2f6; }
code { background:#f3f3f3; padding:1px 4px; border-radius:3px; font-size:9.5pt; }
em { color:#444; }
strong { color:#000; }
blockquote { border-left:3px solid #ccc; margin:8px 0; padding:2px 12px; color:#555; }
li { margin:2px 0; }
hr { border:none; border-top:1px solid #ccc; margin:14px 0; }
"""

def convert(md_path):
    md = open(md_path).read()
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    pdf_path = os.path.splitext(md_path)[0] + ".pdf"
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as t:
        t.write(html); html_path = t.name
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", f"file://{html_path}"],
                   check=True, capture_output=True)
    os.unlink(html_path)
    return pdf_path

if __name__ == "__main__":
    for p in sys.argv[1:]:
        out = convert(p)
        print(f"  {out}  ({os.path.getsize(out)//1024} KB)")
