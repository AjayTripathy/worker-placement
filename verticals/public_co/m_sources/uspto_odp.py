"""USPTO Open Data Portal (ODP) patent applications search.

Drop-in replacement for the Google Patents source — Google rate-limits aggressively
(returns 503 on most calls) and PatentsView is decommissioned in favor of ODP.

Auth: free API key from https://data.uspto.gov/, saved to ~/.uspto_api_key
(0600). Header: X-API-KEY.

Endpoint: POST https://api.uspto.gov/api/v1/patent/applications/search
Returns counts and a sample of records, matching the schema of google_patents
so the recipe library can substitute one for the other.

Notes on what this measures:
- ODP indexes patent APPLICATIONS (file wrappers), not granted-patents-only.
- We return BOTH total applications and the granted subset (status = 'Patented Case').
- For categorization we substring-match keywords against `inventionTitle`. CPC
  classifications (cpcClassificationBag) are also available but require a
  separate keyword→CPC mapping; titles are good enough for the framework's
  divergence test.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["patent_portfolio_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "USPTO Open Data Portal application search; verifies claimed patent portfolios (Google Patents replacement).",
}

from pathlib import Path
import httpx

ENDPOINT = "https://api.uspto.gov/api/v1/patent/applications/search"
KEY_FILE = Path("~/.uspto_api_key").expanduser()
PAGE_SIZE = 100  # ODP max per request appears to be a few hundred; 100 is safe

# Reasonable cap so a wildly prolific assignee doesn't blow up the call budget.
# We mainly care about the count + a sample of titles for categorization.
MAX_FETCH = 500


def _key() -> str | None:
    if not KEY_FILE.exists():
        return None
    k = KEY_FILE.read_text().strip()
    return k or None


def _fetch_page(client: httpx.Client, q: str, fields: list[str], offset: int, limit: int) -> dict:
    body = {"q": q, "fields": fields, "pagination": {"offset": offset, "limit": limit}}
    r = client.post(ENDPOINT, json=body, timeout=30)
    if r.status_code == 404:
        return {"count": 0, "patentFileWrapperDataBag": []}
    r.raise_for_status()
    return r.json()


def query_assignee(assignee_name: str, cutoff_date: str,
                   categorize: dict[str, list[str]] | None = None) -> dict:
    """Patent applications by assignee with filing date before cutoff.

    Returns a dict with the same keys as google_patents.query_assignee
    (assignee_searched, total_granted_patents_pre_cutoff, patents,
    category_counts) plus extra ODP-only fields:
      - n_total_applications (all apps incl. pending)
      - n_granted (subset with applicationStatusDescriptionText='Patented Case')
      - source = 'uspto_odp'

    categorize: {bucket_name: [keyword, ...]} — counts patents whose title
    contains any keyword (case-insensitive). First match wins; remainder
    bucketed as 'other'.
    """
    key = _key()
    if not key:
        return {"error": "no_uspto_api_key", "hint": f"create {KEY_FILE} (mode 0600) with your USPTO ODP API key"}

    # ODP's q is Lucene-flavored. Multi-word names MUST be wrapped in quotes,
    # otherwise the parser treats the second word as a separate clause and the
    # match becomes a substring on either token (e.g. unquoted 'Desktop Metal'
    # matches 94k records on 'Desktop' or 'Metal' anywhere; quoted matches 498
    # records on the exact firstApplicantName phrase).
    safe_assignee = assignee_name.split(",")[0].strip()
    quoted = f'"{safe_assignee}"' if " " in safe_assignee else safe_assignee

    q_total = (
        f"applicationMetaData.firstApplicantName:{quoted}"
        f" AND applicationMetaData.filingDate:[* TO {cutoff_date}]"
    )
    q_granted = q_total + ' AND applicationMetaData.applicationStatusDescriptionText:"Patented Case"'

    fields = [
        "applicationNumberText",
        "applicationMetaData.firstApplicantName",
        "applicationMetaData.filingDate",
        "applicationMetaData.applicationStatusDescriptionText",
        "applicationMetaData.inventionTitle",
        "applicationMetaData.patentNumber",
        "applicationMetaData.grantDate",
        "applicationMetaData.cpcClassificationBag",
    ]

    headers = {
        "User-Agent": "Signal OS Research backtest@signalos.local",
        "X-API-KEY": key,
        "Content-Type": "application/json",
    }
    try:
        with httpx.Client(headers=headers) as c:
            # First page (also gives us the total count)
            page1 = _fetch_page(c, q_total, fields, 0, PAGE_SIZE)
            total = int(page1.get("count", 0))
            records = list(page1.get("patentFileWrapperDataBag", []) or [])

            # Pull more pages up to MAX_FETCH so categorization has enough titles
            target = min(total, MAX_FETCH)
            while len(records) < target:
                more = _fetch_page(c, q_total, fields, len(records),
                                   min(PAGE_SIZE, target - len(records)))
                batch = more.get("patentFileWrapperDataBag", []) or []
                if not batch:
                    break
                records.extend(batch)

            # Granted-only count (single page is enough — we only need the count)
            granted_page = _fetch_page(c, q_granted, ["applicationNumberText"], 0, 1)
            n_granted = int(granted_page.get("count", 0))
    except httpx.HTTPStatusError as e:
        return {"error": f"status_{e.response.status_code}", "detail": e.response.text[:300]}
    except Exception as e:
        return {"error": str(e)[:300]}

    patents = []
    for r in records:
        amd = r.get("applicationMetaData", {}) or {}
        patents.append({
            "patent_id": amd.get("patentNumber") or r.get("applicationNumberText"),
            "application_number": r.get("applicationNumberText"),
            "title": (amd.get("inventionTitle") or "").strip(),
            "filing_date": amd.get("filingDate"),
            "grant_date": amd.get("grantDate"),
            "status": amd.get("applicationStatusDescriptionText"),
            "applicant": amd.get("firstApplicantName"),
            "cpc": (amd.get("cpcClassificationBag") or [])[:8],
        })

    out = {
        "source": "uspto_odp",
        "assignee_searched": assignee_name,
        "cutoff_date": cutoff_date,
        "n_total_applications": total,
        "n_granted": n_granted,
        # Use the same key name as google_patents so existing recipe-scoring
        # interpretations don't have to change. NOTE: this counts applications,
        # not strictly grants, so the absolute number can be higher than what
        # the old source would have returned.
        "total_granted_patents_pre_cutoff": n_granted,
        "patents": patents[:15],
    }
    if categorize is not None:
        cat_counts = {b: 0 for b in categorize}
        cat_counts["other"] = 0
        for p in patents:
            t = p["title"].lower()
            matched = False
            for bucket, keywords in categorize.items():
                if any(k.lower() in t for k in keywords):
                    cat_counts[bucket] += 1
                    matched = True
                    break
            if not matched:
                cat_counts["other"] += 1
        out["category_counts"] = cat_counts
    return out
