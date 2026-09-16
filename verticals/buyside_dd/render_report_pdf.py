"""Render a markdown analyst report to a styled PDF.

Primary path: headless Google Chrome print-to-PDF (full CSS, correct pagination — no
page-break fill artifacts). Footer + page numbers stamped with PyMuPDF afterward.
Fallback: PyMuPDF Story (used only if Chrome isn't found).

Usage: python3 render_report_pdf.py <input.md> <output.pdf> ["Title"] ["Footer"]
"""
import os
import subprocess
import sys
import tempfile
import markdown
import fitz  # PyMuPDF

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: letter; margin: 0.7in 0.72in 0.9in 0.72in; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
* { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; box-sizing: border-box; }
body { font-size: 10.5px; color: #232a31; line-height: 1.45; margin: 0; }
h1 { font-size: 22px; color: #15233f; margin: 0 0 2px 0; }
h2 { font-size: 14.5px; color: #15233f; margin: 17px 0 6px 0; padding-bottom: 3px;
     border-bottom: 1.5px solid #c9a14a; page-break-after: avoid; }
h3 { font-size: 12px; color: #2c3e50; margin: 11px 0 3px 0; page-break-after: avoid; }
p  { margin: 5px 0; }
strong { color: #15233f; }
em { color: #4a5560; }
hr { border: none; border-top: 1px solid #d4d9df; margin: 13px 0; }
ul, ol { margin: 4px 0 6px 0; padding-left: 20px; }
li { margin: 3px 0; }
a { color: #15233f; text-decoration: none; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 9.3px; color: #7a4d12;
       background-color: #f4f1ea; padding: 0 2px; border-radius: 2px; }
table { width: 100%; border-collapse: collapse; margin: 9px 0; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background-color: #15233f; color: #ffffff; font-weight: bold; padding: 6px 7px;
     text-align: left; font-size: 9.8px; border: 0.5px solid #15233f; }
td { padding: 4px 7px; border: 0.5px solid #cdd3da; font-size: 9.8px; vertical-align: top; }
tbody tr:nth-child(even) { background-color: #f6f7f9; }
"""

def _html(md_path):
    text = open(md_path).read()
    body = markdown.markdown(text, extensions=["tables", "sane_lists", "fenced_code", "attr_list"])
    return f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def _stamp_footer(pdf_path, footer):
    doc = fitz.open(pdf_path)
    W = doc[0].rect.width
    H = doc[0].rect.height
    for i, page in enumerate(doc):
        page.draw_line(fitz.Point(52, H - 40), fitz.Point(W - 52, H - 40),
                       color=(0.83, 0.85, 0.87), width=0.5)
        page.insert_text(fitz.Point(52, H - 28), footer, fontsize=7.5,
                         color=(0.45, 0.5, 0.55), fontname="helv")
        page.insert_text(fitz.Point(W - 96, H - 28), f"Page {i+1} of {len(doc)}",
                         fontsize=7.5, color=(0.45, 0.5, 0.55), fontname="helv")
    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()


def render(md_path, pdf_path, title=None,
           footer="Confidential — for the addressee's internal use only"):
    html = _html(md_path)
    if os.path.exists(CHROME):
        import time
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(html)
            html_path = f.name
        prof = tempfile.mkdtemp()
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
        # --virtual-time-budget forces headless to finish & write; Chrome may then hang on
        # exit, so Popen + poll the output to stability + terminate (the PDF is already written).
        proc = subprocess.Popen(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--disable-dev-shm-usage", "--no-first-run", "--no-default-browser-check",
             "--run-all-compositor-stages-before-draw", "--virtual-time-budget=8000",
             "--no-pdf-header-footer", f"--user-data-dir={prof}",
             f"--print-to-pdf={pdf_path}", f"file://{html_path}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        last = -1
        for _ in range(40):  # up to ~40s
            if proc.poll() is not None:
                break
            if os.path.exists(pdf_path):
                sz = os.path.getsize(pdf_path)
                if sz > 0 and sz == last:
                    break
                last = sz
            time.sleep(1)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        os.unlink(html_path)
        if not (os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0):
            raise RuntimeError("Chrome failed to produce a PDF")
        engine = "chrome"
    else:  # fallback: PyMuPDF Story
        MEDIA = fitz.paper_rect("letter")
        WHERE = MEDIA + (56, 58, -56, -54)
        writer = fitz.DocumentWriter(pdf_path)
        story = fitz.Story(html=html, user_css=CSS)
        more = 1
        while more:
            dev = writer.begin_page(MEDIA)
            more, _ = story.place(WHERE)
            story.draw(dev)
            writer.end_page()
        writer.close()
        engine = "pymupdf-story"
    _stamp_footer(pdf_path, footer)
    n = fitz.open(pdf_path).page_count
    print(f"[wrote {pdf_path} — {n} pages, engine={engine}]")


if __name__ == "__main__":
    md, pdf = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else None
    footer = sys.argv[4] if len(sys.argv) > 4 else "Confidential — for the addressee's internal use only"
    render(md, pdf, title, footer)
