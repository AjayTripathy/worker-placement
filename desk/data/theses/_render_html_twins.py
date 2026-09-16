#!/usr/bin/env python3
"""Render each desk/data/theses/*_THESIS_<date>.md into a matching
desk/reports/<TICKER>_THESIS_<date>.html so that
desk.consistency_check.check_position_docs_complete (which globs desk/reports/*.html and
looks for the ticker + the 'market believes' frame marker + a 'verif' marker) can see them.

Markdown stays the source of truth; the HTML is a rendered twin, not a second document.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "desk" / "data" / "theses"
OUT = ROOT / "desk" / "reports"

CSS = """
:root{--ink:#1a1c1e;--muted:#585d63;--faint:#888e95;--rule:#e2e0da;--accent:#243b53;
--pass:#1e5c3a;--warn:#8a3324;--paper:#fff;}
body{font-family:Charter,Georgia,serif;color:var(--ink);background:#f3f2ef;margin:0;
padding:0 16px;line-height:1.5;font-size:16.5px;}
.wrap{max-width:860px;margin:0 auto;padding:36px 0 72px;}
h1{font-size:29px;line-height:1.15;margin:0 0 14px;font-weight:700;}
h2{font-size:19px;margin:28px 0 8px;font-weight:700;border-bottom:1px solid var(--rule);padding-bottom:4px;}
h3{font-size:15.5px;margin:18px 0 6px;font-weight:700;color:var(--accent);}
table{border-collapse:collapse;width:100%;font-family:system-ui,sans-serif;font-size:12.5px;
font-variant-numeric:tabular-nums;margin:10px 0;}
th{text-align:left;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);
font-weight:600;padding:6px 12px 6px 0;border-bottom:1px solid var(--ink);}
td{padding:7px 12px 7px 0;border-bottom:1px solid var(--rule);vertical-align:top;}
.tbl{overflow-x:auto;}
ul{margin:6px 0 12px;padding-left:20px;} li{margin:0 0 6px;}
code{font-family:ui-monospace,Menlo,monospace;font-size:13px;background:#eceae4;padding:1px 4px;border-radius:3px;}
blockquote{border-left:3px solid var(--accent);background:#eef2f6;margin:12px 0;padding:10px 16px;}
hr{border:0;border-top:1px dashed var(--rule);margin:22px 0;}
p{margin:8px 0;}
"""


def md_to_html(md: str) -> str:
    out, in_tbl, in_list = [], False, False

    def inline(s):
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
        return s

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def close_tbl():
        nonlocal in_tbl
        if in_tbl:
            out.append("</table></div>")
            in_tbl = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            close_list()
            tag = "td"
            if not in_tbl:
                out.append('<div class="tbl"><table>')
                in_tbl = True
                tag = "th"
            out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        close_tbl()
        if not line.strip():
            close_list()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            close_list()
            lvl = min(len(m.group(1)), 3)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline(re.sub(r"^\s*[-*]\s+", "", line)) + "</li>")
            continue
        if line.startswith(">"):
            close_list()
            out.append("<blockquote>" + inline(line.lstrip("> ")) + "</blockquote>")
            continue
        if re.fullmatch(r"-{3,}", line.strip()):
            close_list()
            out.append("<hr>")
            continue
        close_list()
        out.append("<p>" + inline(line) + "</p>")
    close_list()
    close_tbl()
    return "\n".join(out)


# Only render the docs this lane owns. The parallel lane (WAL/OMF/FSBW/VRLA_PA/KALMAR_HE) writes into
# the same directory and renders its own twins; do not step on it.
OWNED = {
    "MC_PA", "SAP", "CAI", "MCK", "ONON", "BKE",
    "EG", "KNSL", "WRB", "EQT", "XOM", "SU", "LDOS",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(SRC.glob("*_THESIS_*.md")):
        if f.stem.rsplit("_THESIS_", 1)[0] not in OWNED:
            continue
        md = f.read_text()
        title = md.splitlines()[0].lstrip("# ").strip() if md.strip() else f.stem
        body = md_to_html(md)
        page = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head>"
            f"<body><div class='wrap'>{body}</div></body></html>"
        )
        tgt = OUT / (f.stem + ".html")
        tgt.write_text(page)
        n += 1
        print("wrote", tgt)
    print(f"{n} twins rendered")


if __name__ == "__main__":
    main()
