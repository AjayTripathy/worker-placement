"""SEC EDGAR fulltext search."""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "m_source",
    "summary": "SEC EDGAR full-text search; core primary-source query surface for any US filer.",
}

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def query_fulltext(
    search_term: str,
    cutoff_date: str,
    cik: str | None = None,
    start_date: str = "2018-01-01",
    forms: str = "10-K,10-Q,8-K,DEF 14A,20-F,40-F",
) -> dict:
    url = "https://efts.sec.gov/LATEST/search-index"
    params: dict = {
        "q": f'"{search_term}"',
        "dateRange": "custom",
        "startdt": start_date,
        "enddt": cutoff_date,
        "forms": forms,
    }
    if cik:
        params["ciks"] = cik
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url, params=params)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
            data = r.json()
    except Exception as e:
        return {"error": str(e)}

    hits = data.get("hits", {}).get("hits", [])
    return {
        "search_term": search_term,
        "cik": cik,
        "total_hits": data.get("hits", {}).get("total", {}).get("value", 0),
        "top_filings": [
            {
                "form": h.get("_source", {}).get("form"),
                "filing_date": h.get("_source", {}).get("file_date"),
                "accession": h.get("_id"),
                "company": h.get("_source", {}).get("display_names", []),
            }
            for h in hits[:10]
        ],
    }
