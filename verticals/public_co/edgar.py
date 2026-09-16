"""SEC EDGAR submissions API + filing-text fetcher.

Pulls all filings for a CIK, filters to pre-cutoff, and downloads the priority
forms as raw text into `out_dir/filings/<accession>_<form>.txt`.
"""
from __future__ import annotations

import functools
import json
import sys
import time
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


@functools.lru_cache(maxsize=1)
def _sec_ticker_to_cik_map() -> dict[str, str]:
    """Pull SEC's authoritative ticker → CIK map. Session-cached.

    Source: https://www.sec.gov/files/company_tickers.json — updated by the
    SEC and the only authoritative public mapping. Foreign filers, recently
    relisted tickers, and most ADRs are present.

    Returns a dict mapping uppercase ticker → 10-digit zero-padded CIK.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    r = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    r.raise_for_status()
    raw = r.json()
    out: dict[str, str] = {}
    # SEC returns either a list-of-dicts or a dict-of-dicts; both contain
    # entries with shape {ticker, cik_str, title}.
    rows = raw.values() if isinstance(raw, dict) else raw
    for entry in rows:
        tk = (entry.get("ticker") or "").upper().strip()
        cik_int = entry.get("cik_str")
        if not tk or cik_int is None:
            continue
        out[tk] = str(cik_int).zfill(10)
    return out


def cik_for(ticker: str, *, override: str | None = None) -> str:
    """Look up the CIK for a public-company ticker via SEC's authoritative map.

    Args:
      ticker: ticker symbol (case-insensitive).
      override: rare cases where SEC's map lacks the ticker (foreign filers,
                recently-delisted, special ADRs). Pass the 10-digit CIK
                explicitly; this disables the lookup.

    Raises:
      ValueError if ticker isn't found and no override provided.
    """
    if override:
        return str(override).zfill(10)
    m = _sec_ticker_to_cik_map()
    cik = m.get(ticker.upper().strip())
    if cik:
        return cik
    raise ValueError(
        f"No CIK found for ticker {ticker!r} in SEC ticker map. "
        f"Pass override= for foreign filers / edge cases."
    )


def list_filings(cik: str) -> tuple[str, list[dict]]:
    cik_padded = cik.lstrip("0").rjust(10, "0")
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    with httpx.Client(timeout=30, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        data = r.json()
    recent = data.get("filings", {}).get("recent", {})
    n = len(recent.get("accessionNumber", []))
    rows = []
    for i in range(n):
        rows.append({
            "accession": recent["accessionNumber"][i],
            "filing_date": recent["filingDate"][i],
            "report_date": recent.get("reportDate", [None] * n)[i],
            "form": recent["form"][i],
            "primary_document": recent.get("primaryDocument", [""])[i],
            "primary_doc_description": recent.get("primaryDocDescription", [""])[i],
        })
    return data.get("name", "?"), rows


def fetch_filing_text(cik: str, accession: str, primary_doc: str) -> str | None:
    cik_int = cik.lstrip("0")
    accession_clean = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{primary_doc}"
    try:
        with httpx.Client(timeout=60, headers=HEADERS) as c:
            r = c.get(url)
            if r.status_code == 200:
                return r.text
    except Exception as e:
        print(f"  fetch_filing_text error for {accession}: {e}", file=sys.stderr)
    return None


def html_to_clean_text(html: str) -> str | None:
    """bs4 clean-extract with each <table> flattened in place to 'cell | cell' lines.

    Raw SEC HTML wedges inline-XBRL tags between a trigger verb and its number
    ("accounted for <ix:..>69</ix> %"), which blinds regex AND truncates LLM slicer
    windows, and leaves table-disclosed facts invisible to any text reader. Cleaning +
    table-flattening is the single highest-leverage ingestion fix. Returns None if bs4 is
    unavailable so callers can fall back to raw fetch_filing_text."""
    try:
        import re as _re
        import warnings
        from bs4 import BeautifulSoup, NavigableString
        try:
            from bs4 import XMLParsedAsHTMLWarning
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        except Exception:
            pass
    except Exception:
        return None
    soup = BeautifulSoup(html, "lxml")
    for t in soup.find_all("table"):
        lines = []
        for tr in t.find_all("tr"):
            cells = [_re.sub(r"\s+", " ", c.get_text(" ", strip=True))
                     for c in tr.find_all(["td", "th"])]
            cells = [c for c in cells if c]
            if cells:
                lines.append(" | ".join(cells))
        t.replace_with(NavigableString("\n" + "\n".join(lines) + "\n"))
    txt = soup.get_text(" ", strip=True)
    return _re.sub(r"[ \t]+", " ", txt.replace(" ", " "))


def fetch_filing_clean(cik: str, accession: str, primary_doc: str) -> str | None:
    """Like fetch_filing_text but returns bs4-CLEANED text (tags stripped, tables
    flattened to 'cell | cell' lines). Falls back to raw fetch_filing_text when the doc
    is non-HTML or bs4 is unavailable. Prefer this over fetch_filing_text for any
    regex/LLM consumer — the tag pollution otherwise silently kills recall."""
    if primary_doc and primary_doc.lower().endswith((".htm", ".html")):
        cik_int = cik.lstrip("0")
        accession_clean = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}/{primary_doc}"
        try:
            with httpx.Client(timeout=60, headers=HEADERS) as c:
                r = c.get(url)
                if r.status_code == 200 and r.text:
                    return html_to_clean_text(r.text) or r.text
        except Exception as e:
            print(f"  fetch_filing_clean error for {accession}: {e}", file=sys.stderr)
    return fetch_filing_text(cik, accession, primary_doc)


def latest_filing(cik: str, cutoff: str | None = None,
                  forms: tuple[str, ...] = ("10-K", "10-Q")) -> dict | None:
    """The MOST RECENT filing among `forms` as of `cutoff` (point-in-time). NOT
    prefer-a-form — a just-filed 10-K carries the fuller annual disclosures, and
    preferring any quarterly would skip it for a stale 10-Q. Returns the filing row
    (dict with form/filing_date/accession/primary_document) or None."""
    try:
        _, rows = list_filings(cik)
    except Exception:
        return None
    if cutoff:
        rows = [r for r in rows if r["filing_date"] <= cutoff]
    cand = sorted((r for r in rows if r["form"] in forms),
                  key=lambda r: r["filing_date"], reverse=True)
    return cand[0] if cand else None


def fetch_form4_xml(cik: str, accession: str, primary_doc: str) -> str | None:
    """Form 4 primary_document is the HTML rendition. The structured data is in
    the same .xml file at the root of the accession folder; ownership.xml is the
    legacy fallback name."""
    cik_int = cik.lstrip("0")
    accession_clean = accession.replace("-", "")
    xml_name = primary_doc.split("/")[-1] if "/" in primary_doc else primary_doc
    if not xml_name.endswith(".xml"):
        xml_name = "ownership.xml"
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_clean}"
    try:
        with httpx.Client(timeout=20, headers=HEADERS) as c:
            r = c.get(f"{base}/{xml_name}")
            if r.status_code != 200:
                r = c.get(f"{base}/ownership.xml")
            return r.text if r.status_code == 200 else None
    except Exception:
        return None


def pull(cik: str, cutoff_date: str, priority_forms: set[str], out_dir: Path) -> list[dict]:
    """List CIK's filings, filter pre-cutoff, save index, download priority forms.

    Returns the pre-cutoff index as a list of filing dicts.
    """
    out_dir.mkdir(exist_ok=True, parents=True)
    filings_dir = out_dir / "filings"
    filings_dir.mkdir(exist_ok=True, parents=True)

    print(f"Listing filings for CIK {cik}...", file=sys.stderr)
    company_name, rows = list_filings(cik)
    print(f"  total filings: {len(rows)}", file=sys.stderr)
    pre = [r for r in rows if r["filing_date"] <= cutoff_date]
    print(f"  pre-cutoff ({cutoff_date}): {len(pre)}", file=sys.stderr)
    for r in pre:
        r["cik"] = cik
        r["company"] = company_name

    (out_dir / "filings_index.json").write_text(json.dumps(pre, indent=2))

    priority = [r for r in pre if r["form"] in priority_forms]
    print(f"Downloading {len(priority)} priority filings...", file=sys.stderr)
    for i, r in enumerate(priority):
        form_safe = r["form"].replace("/", "_").replace(" ", "_")
        out_path = filings_dir / f"{r['accession']}_{form_safe}.txt"
        if out_path.exists() and out_path.stat().st_size > 1000:
            continue
        text = fetch_filing_text(r["cik"], r["accession"], r["primary_document"])
        if text:
            out_path.write_text(text)
            print(f"  [{i+1}/{len(priority)}] {r['filing_date']}  {r['form']:<10}  {len(text)//1024} KB", file=sys.stderr)
        else:
            print(f"  [{i+1}/{len(priority)}] {r['filing_date']}  {r['form']:<10}  FETCH FAILED", file=sys.stderr)
        time.sleep(0.15)
    return pre
