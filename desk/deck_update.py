"""deck_update — decks are LIVING documents (principal directive 2026-09-04, COLL gate).

When a watched event resolves — a filing-watch fire, a pack grading, a gate draining, a band
staging — the name's deck gets a dated EVENT ADDENDUM, a fresh PDF, and a re-email. The reader-
facing artifact must never lag the record it fronts ("we should make sure the pdf gets updated
when that happens").

  python3 -m desk.deck_update TICKER "headline" "body markdown"
Callable: append_and_ship(ticker, headline, body, email=True) -> pdf path or None.
Used by: session close-outs (procedural), filing_watch (automated hook on fires for tickers
holding decks). Failures never block the caller — a deck update is downstream of the event.
"""
from __future__ import annotations

import datetime
import glob
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "desk" / "reports"
CSS = ("<style>body{font:11pt -apple-system,sans-serif;max-width:7.2in;margin:0 auto;"
       "color:#111;line-height:1.5}h1{font-size:17pt;border-bottom:2px solid #333}"
       "h2{font-size:12.5pt;margin-top:16px;border-bottom:1px solid #ccc}h3{font-size:11.5pt}"
       "strong{color:#000}li{margin-bottom:4px}table{border-collapse:collapse;font-size:8.5pt;"
       "width:100%}td,th{border:1px solid #bbb;padding:3px 5px;vertical-align:top}</style>")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def latest_deck(ticker: str) -> Path | None:
    safe = ticker.replace(".", "_")
    cands = sorted(glob.glob(str(REPORTS / f"{safe}_PITCH_DECK_*.md")))
    return Path(cands[-1]) if cands else None


def render_pdf(md: Path) -> Path | None:
    html = Path("/tmp") / (md.stem + ".html")
    pdf = md.with_suffix(".pdf")
    try:
        subprocess.run(["pandoc", str(md), "-s", "-o", str(html), "-M",
                        f"pagetitle={md.stem}"], check=True, capture_output=True, timeout=120)
        txt = html.read_text()
        html.write_text(txt.replace("</head>", CSS + "</head>"))
        subprocess.run([CHROME, "--headless", "--disable-gpu",
                        f"--print-to-pdf={pdf}", "--no-pdf-header-footer", str(html)],
                       check=True, capture_output=True, timeout=180)
        return pdf
    except Exception as e:
        print(f"[deck_update] render failed for {md.name}: {type(e).__name__}: {e}")
        return None


def append_and_ship(ticker: str, headline: str, body: str, email: bool = True) -> Path | None:
    md = latest_deck(ticker)
    if md is None:
        print(f"[deck_update] {ticker}: no deck on file — nothing to update")
        return None
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%MZ")
    md.write_text(md.read_text() +
                  f"\n\n---\n\n## EVENT ADDENDUM — {stamp}\n\n**{headline}**\n\n{body}\n")
    pdf = render_pdf(md)
    if pdf and email:
        try:
            from desk.mailer import send_with_attachment
            send_with_attachment(f"{ticker} deck updated: {headline}",
                                 f"Event addendum appended to the {ticker} deck and re-rendered "
                                 f"(living-document rail, 2026-09-04).\n\n{body[:1200]}",
                                 [str(pdf)])
        except Exception as e:
            print(f"[deck_update] mail failed: {e}")
    return pdf


if __name__ == "__main__":
    import sys
    append_and_ship(sys.argv[1], sys.argv[2],
                    sys.argv[3] if len(sys.argv) > 3 else "(see record)")
