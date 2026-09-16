"""
Fetch Exhibit 21 (List of Subsidiaries) from a company's most recent 10-K.

Public companies must file an Exhibit 21 with each 10-K listing every
material subsidiary. This is the canonical structured source for resolving
"company X" → all the names X could appear under in a contract / J-Book.

Output schema:
  {
    "cik": "0001824920",
    "filing_accession": "0001824920-25-000018",
    "filing_date": "2025-03-15",
    "exhibit_url": "...",
    "subsidiaries": [
      {"name": "IonQ Subsidiary, Inc.", "jurisdiction": "Delaware"},
      ...
    ],
    "n_subsidiaries": int,
    "raw_text": "..."  // first 5000 chars for LLM context
  }

Limitations:
- Some companies file Exhibit 21 as plain-text, others as HTML tables,
  others as image-only PDFs. We extract from HTML/text. PDF-only exhibits
  return subsidiaries=[] with raw_text empty.
- The parser is best-effort: it greps for indented company-name lines
  and parenthetical jurisdiction patterns. Won't capture deeply-nested
  org structures.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Reuse the same throttle as insider_vs_calendar
_MIN_GAP_SEC = 0.15
_last_request_ts = 0.0


def _throttled_get(url: str, max_retries: int = 3) -> Optional[httpx.Response]:
    global _last_request_ts
    backoff = 1.5
    for _ in range(max_retries + 1):
        gap = time.time() - _last_request_ts
        if gap < _MIN_GAP_SEC:
            time.sleep(_MIN_GAP_SEC - gap)
        try:
            r = httpx.get(url, headers=HEADERS, timeout=30,
                          follow_redirects=True)
            _last_request_ts = time.time()
        except Exception:
            return None
        if r.status_code == 429:
            time.sleep(min(backoff, 30))
            backoff *= 2
            continue
        return r
    return None


def _find_latest_10k(cik: str) -> Optional[dict]:
    """Return {accession, filing_date, primary_document, docs:[{name, type}]}."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    r = _throttled_get(url)
    if r is None or r.status_code != 200:
        return None
    j = r.json()
    recent = j.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accs = recent.get("accessionNumber", [])
    pris = recent.get("primaryDocument", [])
    for i, f in enumerate(forms):
        if f != "10-K":
            continue
        return {
            "accession":  accs[i] if i < len(accs) else "",
            "filing_date": dates[i] if i < len(dates) else "",
            "primary_document": pris[i] if i < len(pris) else "",
        }
    return None


def _list_filing_documents(cik: str, accession: str) -> list[dict]:
    """List all documents within a filing via the index.json."""
    cik_int = int(cik)
    acc_no_dashes = accession.replace("-", "")
    idx_url = (f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
               f"&CIK={cik_int}&type=10-K&dateb=&owner=include&count=10")
    # Use filing index JSON
    idx_url = (f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
               f"{acc_no_dashes}/index.json")
    r = _throttled_get(idx_url)
    if r is None or r.status_code != 200:
        return []
    try:
        j = r.json()
    except Exception:
        return []
    return j.get("directory", {}).get("item", []) or []


def _find_exhibit_21_url(cik: str, accession: str, docs: list[dict]) -> Optional[str]:
    """Find the Exhibit 21 attachment in a filing's doc list."""
    cik_int = int(cik)
    acc_no_dashes = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no_dashes}/"

    # Strategy 1: name contains "ex21" / "ex-21" / "ex_21" (with or without
    # suffix like _1, _2, _01). Be permissive but not greedy — don't match
    # ex210 etc.
    for d in docs:
        name = (d.get("name") or "").lower()
        if (re.search(r"ex[_\-]?21(?:[_\-]\d+)?\.(htm|html|txt)$", name)
            or re.search(r"exhibit[_\-]?21", name)):
            return base + d["name"]

    # Strategy 2: fall back to filing-index FilingSummary.xml for typed attachments
    return None


# US states / common jurisdictions used in Exhibit 21 listings.
_JURISDICTIONS = (
    "Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|"
    "District of Columbia|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|"
    "Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|"
    "Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|"
    "New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|"
    "Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|"
    "Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|"
    "Puerto Rico|"
    "Australia|Austria|Belgium|Brazil|British Columbia|Canada|"
    "Cayman Islands|China|Denmark|England|Finland|France|Germany|Hong Kong|"
    "India|Ireland|Israel|Italy|Japan|Korea|Luxembourg|Mexico|Netherlands|"
    "New Zealand|Norway|Ontario|Quebec|Singapore|South Korea|Spain|Sweden|"
    "Switzerland|Taiwan|United Kingdom|UK"
)
_JUR_RE = re.compile(rf"\b({_JURISDICTIONS})\b")
_ENTITY_SUFFIX = r"(?:Inc|Inc\.|Corp|Corp\.|Corporation|LLC|L\.L\.C\.|Ltd|Ltd\.|Limited|Holdings|Company|Co\.|S\.A\.|GmbH|N\.V\.|PLC|Pty|Pty\.|AG|AB)"
# Match "Name <suffix> <Jurisdiction>" anywhere — works on inline (table-flattened) text
_TABLE_ROW_RE = re.compile(
    rf"([A-Z][A-Za-z0-9\.\,\&\-\'\s]{{2,120}}?\s*{_ENTITY_SUFFIX})\s+"
    rf"({_JURISDICTIONS})\b",
    re.DOTALL,
)


def _parse_subsidiary_text(text: str) -> list[dict]:
    """Heuristic parse: extract (name, jurisdiction) pairs.

    Handles two shapes:
      1. Line-formatted: each subsidiary on its own line, name + jurisdiction
      2. Table-flattened: all subs run together on one line after HTML strip

    Strategy: find every (name-with-corporate-suffix, jurisdiction) match
    in the text via a regex over the whole blob, then de-dup by name."""
    out = []
    seen = set()
    for m in _TABLE_ROW_RE.finditer(text):
        name = m.group(1).strip().rstrip(",").strip()
        # Re-trim if name ends with parent-company prefix accidentally captured
        # (e.g., "Delaware Rocket Lab USA, Inc." → strip leading jurisdiction)
        name = _JUR_RE.sub("", name).strip()
        juris = m.group(2).strip()
        key = name.lower()
        if not name or key in seen or len(name) > 200:
            continue
        # Reject obvious header noise
        if re.search(r"\b(exhibit|list of|subsidiaries of|company name|"
                       r"jurisdiction|registrant|table of contents)\b",
                      name, re.IGNORECASE):
            # Try recovering the trailing company name only (e.g., header text
            # got captured before "Rocket Lab USA, Inc."). Look for the LAST
            # name-with-suffix substring in the captured string.
            tail = re.findall(
                r"([A-Z][A-Za-z0-9\.\,\&\-\'\s]{2,120}?\s+" + _ENTITY_SUFFIX + r")",
                name,
            )
            if tail:
                cleaned = tail[-1].strip().rstrip(",").strip()
                cleaned = re.sub(r"\s+", " ", cleaned)
                # Strip leading "Name Jurisdiction" / "Company Name" headers
                cleaned = re.sub(
                    r"^(?:Name|Jurisdiction|Company|Company\s+Name)\s+",
                    "", cleaned, flags=re.IGNORECASE,
                )
                ckey = cleaned.lower()
                if ckey and ckey not in seen:
                    seen.add(ckey)
                    out.append({"name": cleaned, "jurisdiction": juris})
            continue
        # Collapse multiple spaces in valid names
        name = re.sub(r"\s+", " ", name)
        seen.add(key)
        out.append({"name": name, "jurisdiction": juris})
    return out


def fetch_exhibit_21(cik: str) -> dict:
    """Find + fetch + parse Exhibit 21 for a CIK."""
    result: dict = {"cik": cik, "subsidiaries": [], "n_subsidiaries": 0,
                    "raw_text": "", "error": None}
    filing = _find_latest_10k(cik)
    if not filing:
        result["error"] = "no_10k_found"
        return result
    result["filing_accession"] = filing["accession"]
    result["filing_date"] = filing["filing_date"]
    docs = _list_filing_documents(cik, filing["accession"])
    if not docs:
        result["error"] = "no_filing_docs"
        return result
    ex21_url = _find_exhibit_21_url(cik, filing["accession"], docs)
    if not ex21_url:
        result["error"] = "no_exhibit_21_attachment"
        return result
    result["exhibit_url"] = ex21_url
    r = _throttled_get(ex21_url)
    if r is None or r.status_code != 200:
        result["error"] = f"exhibit_fetch_failed_{r.status_code if r else 'none'}"
        return result
    raw_html = r.text
    # Strategy 1: parse HTML tables directly when present. Each <tr> is one
    # subsidiary row → much more reliable than regex over flattened text.
    subs: list[dict] = []
    if "<table" in raw_html.lower():
        subs = _parse_subsidiary_html_tables(raw_html)

    # Strategy 2: fall back to text parsing if table extraction yielded
    # nothing (some filings render Ex-21 as a plain-text list, not a table).
    text = raw_html
    if "<html" in text.lower() or "<body" in text.lower() or "<p" in text.lower():
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#160;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    result["raw_text"] = text[:8000]
    if not subs:
        subs = _parse_subsidiary_text(text)
    result["subsidiaries"] = subs
    result["n_subsidiaries"] = len(subs)
    return result


def _parse_subsidiary_html_tables(html: str) -> list[dict]:
    """Use BeautifulSoup to walk every <tr>/<td> in the document.

    For each row with >=2 non-empty cells, treat the first cell as name and
    look for a jurisdiction in the remaining cells. Skip header rows."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []
    soup = BeautifulSoup(html, "html.parser")
    out = []
    seen = set()
    for tr in soup.find_all("tr"):
        cells = [(td.get_text(" ", strip=True) or "") for td in tr.find_all(["td", "th"])]
        cells = [c for c in cells if c.strip()]
        if len(cells) < 2:
            continue
        name_candidate = cells[0].strip()
        # Reject header rows
        if re.search(r"^(subsidiar|company name|name|jurisdiction|"
                       r"exhibit|list of)", name_candidate, re.IGNORECASE):
            continue
        # Require a corporate suffix or a clear company-like form
        if not re.search(rf"\b{_ENTITY_SUFFIX}\b|^[A-Z]", name_candidate):
            continue
        # Find jurisdiction cell
        juris = ""
        for c in cells[1:]:
            if re.search(rf"\b{_JURISDICTIONS}\b", c, re.IGNORECASE):
                m = re.search(rf"\b({_JURISDICTIONS})\b", c, re.IGNORECASE)
                juris = m.group(1)
                break
        # If no jurisdiction found, still emit if name has a clear suffix
        if not juris and not re.search(rf"\b{_ENTITY_SUFFIX}\b", name_candidate):
            continue
        # Clean trailing punctuation, normalize whitespace
        name = re.sub(r"\s+", " ", name_candidate).strip().rstrip(",")
        if len(name) > 200 or not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, "jurisdiction": juris})
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cik")
    args = ap.parse_args()
    r = fetch_exhibit_21(args.cik)
    print(json.dumps(r, indent=2, default=str))


if __name__ == "__main__":
    main()
