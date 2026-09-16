"""Extract proposed deal size (Proposed Maximum Aggregate Offering Price)
from each S-1 / F-1 cover page.

Used to rank the IPO queue by deal size before dispatching deep DD agents.

The reg-fee table on S-1 / F-1 cover pages discloses the proposed maximum
aggregate offering price (PMAOP) — the registration-statement upper bound on
proceeds. For DRS / DRS/A (confidential), PMAOP may not yet be public; falls
back to "amount being registered" or returns None.

Extraction strategy (tried in order):
1. Find an HTML <table> containing "Proposed Maximum Aggregate Offering Price"
   and parse the dollar amount on the same row.
2. Find prose "Proposed maximum aggregate offering price" : "$X" pattern.
3. Find "amount being registered" + per-unit price (multiply to get PMAOP).
4. Return None — confidential or non-standard form.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Optional

EDGAR_FILING_INDEX = "https://www.sec.gov/cgi-bin/browse-edgar"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/"

# SEC fair-access policy requires UA to include company name + admin email
# Without this, Archives/edgar/data/* paths return 403 (data.sec.gov is more lenient)
HEADERS = {
    "User-Agent": "Signal OS DD Pipeline ajay@example.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov",
}


def _accession_no_dashes(acc: str) -> str:
    """Convert 0001234567-26-012345 -> 000123456726012345"""
    return acc.replace("-", "")


def _http_get(url: str, timeout: int = 30, retries: int = 3) -> Optional[bytes]:
    import time
    delay = 1.0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                return raw
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if e.code == 404:
                return None
            print(f"  HTTP error {url[:80]}: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  HTTP error {url[:80]}: {e}", file=sys.stderr)
            return None
    return None


def get_filing_index_url(cik: str, accession: str) -> str:
    """Build the EDGAR filing index URL for a given (CIK, accession)."""
    cik_int = int(cik.lstrip("0") or "0")
    # accession may be "0001234567-26-012345:formname.htm" — strip suffix
    acc = accession.split(":")[0] if ":" in accession else accession
    acc_nodash = _accession_no_dashes(acc)
    return ARCHIVES.format(cik=cik_int, acc_nodash=acc_nodash)


def find_main_filing_doc(base_url: str) -> Optional[str]:
    """Use the index.json sibling to identify the main S-1/F-1/DRS document.
    Returns the LARGEST non-exhibit, non-fees, non-graphic .htm file."""
    json_url = base_url.rstrip("/") + "/index.json"
    raw = _http_get(json_url)
    if not raw:
        return None
    try:
        d = json.loads(raw)
    except Exception:
        return None
    items = d.get("directory", {}).get("item", [])
    candidates = []
    for it in items:
        name = it.get("name", "")
        if not name.endswith((".htm", ".html")):
            continue
        try:
            size = int(it.get("size") or 0)
        except (ValueError, TypeError):
            size = 0
        lower = name.lower()
        # Skip exhibits, indexes, header files, filing-fees, R-files (XBRL reports)
        if lower.startswith(("exhibit", "ex-", "ex_", "ex.", "r")) or any(
            k in lower for k in ("index", "header", "filingfees", "filing_fees", "107")):
            continue
        candidates.append((size, name))
    if not candidates:
        for it in items:
            name = it.get("name", "")
            if name.endswith((".htm", ".html")):
                try:
                    sz = int(it.get("size") or 0)
                except (ValueError, TypeError):
                    sz = 0
                candidates.append((sz, name))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    main_name = candidates[0][1]
    return base_url.rstrip("/") + "/" + main_name


_NUMBER_RE = re.compile(
    r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(?:(million|billion)\b)?",
    re.IGNORECASE,
)


def _parse_dollar_amount(s: str) -> Optional[float]:
    """Parse '$1,200,000,000' or '$1.2 billion' or '1,200' to a float USD."""
    m = _NUMBER_RE.search(s)
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    try:
        val = float(raw)
    except ValueError:
        return None
    multiplier = (m.group(2) or "").lower()
    if multiplier == "billion":
        val *= 1_000_000_000
    elif multiplier == "million":
        val *= 1_000_000
    return val


def extract_proposed_proceeds(html: str) -> Optional[float]:
    """Extract Proposed Maximum Aggregate Offering Price from S-1 / F-1 HTML.

    Returns proceeds in USD, or None if not found.
    """
    # Strategy 1: HTML table row containing PMAOP
    # Looks for "Proposed Maximum Aggregate Offering Price" cell with adjacent $ cell
    table_rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)
    for row in table_rows:
        if "proposed maximum aggregate" in row.lower() and "offering" in row.lower():
            # Same row likely has the dollar cell after the label
            # Strip HTML tags from row, then look for the largest dollar amount
            text = re.sub(r"<[^>]+>", " ", row)
            text = re.sub(r"\s+", " ", text).strip()
            # Skip if this IS the header row (no dollar amounts)
            if "$" not in text and not re.search(r"\d{1,3}(?:,\d{3})+", text):
                continue
            # Pick the LAST dollar amount on the row (PMAOP is usually last col)
            matches = list(_NUMBER_RE.finditer(text))
            if matches:
                last = matches[-1]
                val = _parse_dollar_amount(last.group(0))
                if val and val >= 1_000_000:  # filter parsing noise
                    return val

    # Strategy 2: search for the row in a different layout — sometimes PMAOP
    # is in its own cell adjacent to a label cell in the next row
    for row in table_rows:
        text = re.sub(r"<[^>]+>", " ", row)
        text = re.sub(r"\s+", " ", text).strip().lower()
        if "aggregate offering price" in text:
            matches = list(_NUMBER_RE.finditer(text))
            if matches:
                vals = [_parse_dollar_amount(m.group(0)) for m in matches]
                vals = [v for v in vals if v and v >= 1_000_000]
                if vals:
                    return max(vals)

    # Strategy 3: prose form
    m = re.search(
        r"(?:proposed\s+)?maximum\s+aggregate\s+offering\s+price[^\.\n\$]{0,80}"
        r"(\$[\d,]+(?:\.[0-9]+)?(?:\s*(?:million|billion))?)",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return _parse_dollar_amount(m.group(1))

    # Strategy 4: "estimated proceeds" / "we expect to raise"
    m = re.search(
        r"(?:we\s+expect\s+to\s+raise|estimated\s+(?:net\s+)?proceeds[^\.\n\$]{0,80})"
        r"(\$[\d,]+(?:\.[0-9]+)?(?:\s*(?:million|billion))?)",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return _parse_dollar_amount(m.group(1))

    return None


def find_filing_fees_docs(base_url: str) -> list[str]:
    """Return ALL plausible EX-FILING FEES document URLs in the accession folder,
    in priority order (filingfees-named first, then 107-named, then other small htms).
    """
    json_url = base_url.rstrip("/") + "/index.json"
    raw = _http_get(json_url)
    if not raw:
        return []
    try:
        d = json.loads(raw)
    except Exception:
        return []
    items = d.get("directory", {}).get("item", [])
    primary, secondary = [], []
    for it in items:
        name = it.get("name", "")
        if not name.endswith((".htm", ".html")):
            continue
        lower = name.lower()
        if "filingfees" in lower or "filing_fees" in lower or "filing-fees" in lower:
            primary.append(name)
        elif "107" in lower or "ex107" in lower or "ex-107" in lower:
            secondary.append(name)
    out = primary + secondary
    return [base_url.rstrip("/") + "/" + n for n in out]


_IX_VALUE_RE = re.compile(
    r"<ix:nonFraction\b[^>]*>([\d,]+\.\d{2})</ix:nonFraction>",
    re.IGNORECASE,
)


def extract_pmaop_from_filing_fees(html: str) -> Optional[float]:
    """Parse all <ix:nonFraction> dollar-formatted values from the filing-fees
    doc; the PMAOP is the largest aggregated value > $1M.

    Filing-fee tables typically include (in order):
      - per-row Maximum Aggregate Offering Price (e.g. $1,110,526,300.00)
      - per-row Filing Fee (e.g. $153,363.68)
      - Total Maximum Aggregate Offering Price (e.g. $1,210,526,300.00)
      - Total Filing Fee

    We want the LARGEST value, which is the total PMAOP. We use a $10M floor to
    avoid mistaking the per-share price or fee for proceeds.
    """
    matches = _IX_VALUE_RE.findall(html)
    if not matches:
        return None
    vals = []
    for m in matches:
        try:
            v = float(m.replace(",", ""))
            vals.append(v)
        except ValueError:
            continue
    big = [v for v in vals if v >= 10_000_000]
    if not big:
        return None
    return max(big)


def _try_extract_from_accession(cik: str, accession: str) -> Optional[dict]:
    """Try EX-FILING-FEES extraction on a single accession. Returns dict on success, None otherwise."""
    base_url = get_filing_index_url(cik, accession)
    for ff_url in find_filing_fees_docs(base_url):
        raw = _http_get(ff_url)
        if raw:
            p = extract_pmaop_from_filing_fees(raw.decode("utf-8", errors="ignore"))
            if p:
                return {"proposed_proceeds_usd": p, "source_url": ff_url, "method": "ex107_ixbrl",
                        "accession": accession}
    return None


def extract_proceeds_for_filing(cik: str, accession: str) -> Optional[dict]:
    """For (CIK, accession), extract PMAOP from the EX-FILING-FEES doc.

    If the given accession is exhibit-only (no fees doc), walks back through all
    S-1 / F-1 history for this CIK in reverse-chronological order until one yields
    proceeds. Returns {"proposed_proceeds_usd": float, "source_url": str,
    "method": str, "accession": str}.
    """
    # Strategy 1: try the given accession
    r = _try_extract_from_accession(cik, accession)
    if r:
        return r

    # Strategy 2: walk back through all S-1 history for this CIK
    try:
        sub_url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
        req = urllib.request.Request(sub_url, headers={"User-Agent": "Signal OS DD ajay@example.com"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read())
        rec = d.get("filings", {}).get("recent", {})
        forms = rec.get("form", [])
        accs = rec.get("accessionNumber", [])
        for i, f in enumerate(forms):
            if f in ("S-1", "S-1/A", "F-1", "F-1/A", "DRS", "DRS/A"):
                a = accs[i]
                if a == accession:
                    continue  # already tried
                r = _try_extract_from_accession(cik, a)
                if r:
                    return r
    except Exception:
        pass

    return {"proposed_proceeds_usd": None, "source_url": get_filing_index_url(cik, accession),
            "method": "not_found", "accession": accession}


def main():
    """Stdin: JSON list of {cik, accession, company_name}; stdout: enriched with proceeds."""
    items = json.load(sys.stdin)
    out = []
    for i, item in enumerate(items):
        print(f"  Extracting {i+1}/{len(items)}: {item.get('company_name','?')[:50]}", file=sys.stderr)
        res = extract_proceeds_for_filing(item["cik"], item.get("accession") or item.get("_accession") or "")
        out.append({**item, "proceeds_extraction": res})
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
