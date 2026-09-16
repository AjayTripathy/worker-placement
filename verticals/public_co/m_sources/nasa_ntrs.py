"""
NASA Technical Reports Server (NTRS) connector.

NTRS is NASA's open archive of technical reports, papers, presentations,
and program documents — including funded-research authorship, center
attributions, and funding-number references.

Use it as a CORROBORATION source for any small-cap claim involving
NASA technology, contracts, or collaborations. NASA TechPort + NTRS
are the two complementary registries:
  - TechPort: active funded projects + transitions
  - NTRS:     published technical outputs from those projects

Signal interpretation:
  - PRESENT (n_results > 0) → NASA published collaboration corroborated
  - ABSENT  (n_results == 0) → no NASA-published evidence
  - Asymmetric: presence is strong corroboration; absence is moderate
    (NASA work can be ITAR/EAR-restricted and not posted publicly)

API endpoint:
  https://ntrs.nasa.gov/api/citations/search?q={query}&size={n}

Free, public, no key. Rate limit: ~500 req per hour.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["372", "381", "366", "873"],
    "issuer_features": ["mentions_nasa_program"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "NASA NTRS archive corroboration for claimed NASA technology/contract/collaboration.",
}

import re
from typing import Any, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local",
           "Accept": "application/json"}
BASE = "https://ntrs.nasa.gov/api/citations/search"


def query_ntrs(
    query: str,
    size: int = 25,
    after_year: Optional[int] = None,
    match_mode: str = "word_boundary",
) -> dict[str, Any]:
    """Search NASA NTRS for citations matching `query`.

    By default applies a word-boundary post-filter on the entity name
    appearing in title or abstract — same fix we applied to USAspending
    + OSHA + DOL (NTRS substring matches are noisy for short names).

    Returns:
      {
        "query":         echo,
        "total":         int (NASA's reported total),
        "n_filtered":    int (after our word-boundary post-filter),
        "results":       list of {title, published, center, funding_numbers,
                         authors_count, document_type},
        "by_center":     {center_name: count, ...},
        "by_funding":    {funding_number: count, ...},
        "signal":        NASA_PUBLISHED | NASA_NO_FOOTPRINT,
      }
    """
    params: dict = {"q": query, "size": size, "sort": "published desc"}
    if after_year:
        params["dateAcquiredFrom"] = f"{after_year}-01-01"
    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r = c.get(BASE, params=params)
            if r.status_code != 200:
                return {"error": f"ntrs_status_{r.status_code}",
                        "results": [], "total": 0}
            data = r.json()
    except httpx.HTTPError as e:
        return {"error": f"ntrs_http: {e}", "results": [], "total": 0}

    raw = data.get("results", [])
    total = data.get("stats", {}).get("total", 0)

    # Word-boundary post-filter on title + abstract
    if match_mode == "word_boundary":
        pat = re.compile(r"\b" + re.escape(query) + r"\b", re.IGNORECASE)
        def _ok(r: dict) -> bool:
            return bool(pat.search((r.get("title") or "") + " " +
                                    (r.get("abstract") or "")))
    elif match_mode == "exact":
        def _ok(r: dict) -> bool:
            return query.lower() in (r.get("title") or "").lower()
    else:
        def _ok(r: dict) -> bool:
            return True

    filtered = [r for r in raw if _ok(r)]
    by_center: dict[str, int] = {}
    by_funding: dict[str, int] = {}
    out = []
    for r in filtered:
        center = (r.get("center") or {}).get("name") or "?"
        by_center[center] = by_center.get(center, 0) + 1
        for fn in (r.get("fundingNumbers") or []):
            num = (fn or {}).get("number")
            if num:
                by_funding[num] = by_funding.get(num, 0) + 1
        out.append({
            "title":           (r.get("title") or "")[:200],
            "published":       r.get("published"),
            "center":          center,
            "document_type":   r.get("documentType"),
            "funding_numbers": [(fn or {}).get("number") for fn in
                                 (r.get("fundingNumbers") or [])
                                 if fn and (fn or {}).get("number")],
            "authors_count":   len(r.get("authorAffiliations") or []),
        })

    n_filtered = len(filtered)
    if n_filtered == 0:
        signal = "NASA_NO_FOOTPRINT"
    else:
        signal = "NASA_PUBLISHED"

    return {
        "query":      query,
        "total":      total,
        "n_filtered": n_filtered,
        "results":    out[:size],
        "by_center":  dict(sorted(by_center.items(), key=lambda x: -x[1])[:10]),
        "by_funding": dict(sorted(by_funding.items(), key=lambda x: -x[1])[:10]),
        "signal":     signal,
        "match_mode": match_mode,
    }
