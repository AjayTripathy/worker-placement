"""
SEC EDGAR submissions API — list filings by CIK and form type.

Complements edgar_fts (fulltext search across the whole index) with a
CIK-anchored filing-list query: "given this issuer, return all of its
filings of form X within a date range". Adjudicates claims of the form
"company Y filed N ABS-15G disclosures since date Z" or "company Y is
a sponsor of ABS-EE pool reports".

API: https://data.sec.gov/submissions/CIK{10-digit}.json
Auth: none (must send a User-Agent identifying contact)
Cost: free
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "m_source",
    "summary": "SEC EDGAR submissions API; CIK-anchored filing lists by form type for any US filer.",
}

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def list_filings_by_form(
    cik: str,
    forms: str | list[str],
    *,
    cutoff_date: str | None = None,
    start_date: str = "2018-01-01",
    limit: int = 50,
) -> dict:
    """Return all filings of a given form type for a CIK within a date range.

    Args:
      cik: 10-digit padded CIK (e.g., "0001647639") or shorter form.
      forms: a single form name ("ABS-15G") or a list (["ABS-15G","ABS-EE"]).
      cutoff_date: ISO date 'YYYY-MM-DD' as the upper bound.
      start_date: ISO date lower bound.
      limit: max number of filings to return.

    Returns:
      {
        "cik":      "0001647639",
        "company":  "Upstart Holdings, Inc.",
        "forms":    ["ABS-15G","ABS-EE"],
        "n_total":  <int>,
        "filings":  [
          {"form":"ABS-15G","filing_date":"2024-02-15","accession":"...","primary_doc":"..."}, ...
        ]
      }
    """
    cik_padded = str(cik).zfill(10) if not str(cik).startswith("CIK") else str(cik)[3:].zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}", "cik": cik_padded}
            j = r.json()
    except httpx.HTTPError as e:
        return {"error": f"http: {e}", "cik": cik_padded}

    company = j.get("name", "")
    recent = j.get("filings", {}).get("recent", {}) or {}
    form_list = recent.get("form", [])
    date_list = recent.get("filingDate", [])
    acc_list  = recent.get("accessionNumber", [])
    pri_list  = recent.get("primaryDocument", [])

    wanted = {forms} if isinstance(forms, str) else set(forms or [])
    out = []
    for i, f in enumerate(form_list):
        if f not in wanted:
            continue
        d = date_list[i] if i < len(date_list) else ""
        if cutoff_date and d > cutoff_date:
            continue
        if start_date and d < start_date:
            continue
        out.append({
            "form":         f,
            "filing_date":  d,
            "accession":    acc_list[i] if i < len(acc_list) else "",
            "primary_doc":  pri_list[i] if i < len(pri_list) else "",
        })
        if len(out) >= limit:
            break

    return {
        "cik":      cik_padded,
        "company":  company,
        "forms":    sorted(wanted),
        "n_total":  len(out),
        "filings":  out,
    }


if __name__ == "__main__":
    import json
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001647639"
    forms = sys.argv[2] if len(sys.argv) > 2 else "ABS-15G,ABS-EE,10-D,424B5"
    cutoff = sys.argv[3] if len(sys.argv) > 3 else "2026-05-16"
    print(json.dumps(list_filings_by_form(cik, forms.split(","), cutoff_date=cutoff), indent=2, default=str))
