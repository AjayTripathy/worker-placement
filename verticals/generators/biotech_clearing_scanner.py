"""biotech_clearing_scanner — Stage 0b generator: FRESH 13D/13D-A filings by the biotech cash-box
CLEARING HOUSES (Tang/Concentra, BML Capital, Sarissa...) surfaced within days (the latency edge).

DOCTRINE (theme 2026-07-04): the below-cash residue at any moment is ADVERSELY SELECTED (the clearing
machine resolves clean names in 3-9mo and skips the traps) — so the edge is NOT screening for wide
discounts (wide = red flag) but catching the clearing machine's FRESH engagements and applying three
forensic gates BEFORE entry: (1) no debt/claims ahead of common [IOBT went to ZERO in Ch.7],
(2) US/Delaware domicile [foreign holdback tails], (3) the 8-K/PR says 'return capital / evaluate
sale', never 'advance our pivot' [the PLRX tell]. Realized capture = net-cash-at-close minus the
buyer's buffer, partly via illiquid CVR — never the screen discount. Seeds route to the pipeline
same-week; the scanner proposes, the pipeline disposes.

  python3 verticals/generators/biotech_clearing_scanner.py [--days 7]
Writes data/BIOTECH_CLEARING.json. READ-ONLY.
"""
from __future__ import annotations
import json, datetime, argparse, urllib.request, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "BIOTECH_CLEARING.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
# the clearing-house filers (EDGAR full-text search by filer name; CIKs drift across entities)
FILERS = ["Tang Capital", "Concentra Biosciences", "BML Capital", "BML Investment",
          "Sarissa Capital", "XOMA"]


def _efts(q: str, forms: str, days: int) -> list[dict]:
    start = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    url = ("https://efts.sec.gov/LATEST/search-index?q=%s&dateRange=custom&startdt=%s&forms=%s"
           % (urllib.parse.quote(f'"{q}"'), start, forms))
    url = ("https://efts.sec.gov/LATEST/search-index?q=%s&startdt=%s&enddt=%s&forms=%s"
           % (urllib.parse.quote(f'"{q}"'), start, datetime.date.today().isoformat(), forms))
    try:
        req = urllib.request.Request(url.replace("search-index", "search-index"), headers=HDRS)
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return d.get("hits", {}).get("hits", [])
    except Exception:
        return []


def scan(days: int) -> dict:
    rows = []
    for f in FILERS:
        for h in _efts(f, "SC 13D,SC 13D/A,SC 13G", days):
            src = h.get("_source", {})
            rows.append({"filer_query": f,
                         "subject": src.get("display_names", ["?"])[0] if src.get("display_names") else "?",
                         "form": src.get("file_type"), "filed": src.get("file_date"),
                         "accession": h.get("_id", "")})
    # dedupe
    seen, uniq = set(), []
    for r in rows:
        k = (r["subject"], r["filed"], r["form"])
        if k not in seen:
            seen.add(k); uniq.append(r)
    return {"asof": datetime.date.today().isoformat(), "window_days": days, "hits": uniq,
            "gates": "on ANY fresh hit: (1) debt/claims ahead of common? (2) US Delaware? "
                     "(3) 8-K language return-capital vs pivot? ALL THREE pass -> pipeline same-week",
            "note": "empty windows are normal — the edge is being FIRST in the 3-9mo takeout arc when a hit lands"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    res = scan(a.days)
    print(f"=== BIOTECH CLEARING-MACHINE SCANNER  {res['asof']}  ({len(res['hits'])} filings, {a.days}d window) ===")
    for r in res["hits"]:
        print(f"  >>> FLAG CLEARING-13D: {r['filed']} {r['form']:<9} {r['subject'][:60]}  [{r['filer_query']}]")
    if not res["hits"]:
        print("  no fresh clearing-house filings in the window (normal — the watch exists for the day one lands)")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
