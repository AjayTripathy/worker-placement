"""
FINRA BrokerCheck firm registration lookup.

Authoritative public registry of all FINRA-member broker-dealers in the
United States. Adjudicates claims that a named entity is "a registered
broker-dealer regulated by the SEC and FINRA" — returns the firm's CRD,
SEC#, registration status (Approved / Withdrawn / Suspended), and other
member names.

API: https://api.brokercheck.finra.org/search/firm
Auth: none
Cost: free
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["62"],
    "issuer_features": ["broker_dealer_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "FINRA BrokerCheck registry; adjudicates 'registered broker-dealer' claims with CRD status.",
}

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}
BASE = "https://api.brokercheck.finra.org/search"


def query_firm(firm_name: str, limit: int = 5) -> dict:
    """Look up a broker-dealer firm by name.

    Returns:
      {
        "query":   "<input firm_name>",
        "n_total": <int>,
        "matches": [
          {
            "firm_name":       "...",
            "crd":             "44158",
            "sec_number":      "8-50561",
            "registered":      true/false,
            "registration_statuses": ["FINRA", "SEC"],
            "other_names":     [...],
          }, ...
        ]
      }
    """
    if not firm_name:
        return {"error": "firm_name required"}
    params = {
        "query":  firm_name,
        "hl":     "true",
        "nrows":  max(1, min(limit, 25)),
        "start":  0,
        "r":      25,
        "sort":   "score+desc",
    }
    try:
        with httpx.Client(headers=HEADERS, timeout=20, follow_redirects=True) as c:
            r = c.get(f"{BASE}/firm", params=params)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}", "body": r.text[:200]}
            j = r.json()
    except httpx.HTTPError as e:
        return {"error": f"http: {e}"}

    # FINRA returns total either as an int (older shape) or {"value": ...}
    raw_total = j.get("hits", {}).get("total", 0)
    total = raw_total.get("value", 0) if isinstance(raw_total, dict) else int(raw_total or 0)
    hits = j.get("hits", {}).get("hits", []) or []
    matches = []
    for h in hits:
        src = h.get("_source", {})
        matches.append({
            "firm_name":   src.get("firm_name", ""),
            "crd":         src.get("firm_source_id", ""),
            "sec_number":  src.get("firm_bd_full_sec_number") or src.get("firm_bd_sec_number") or "",
            "ia_sec_number": src.get("firm_ia_full_sec_number") or src.get("firm_ia_sec_number") or "",
            "registered":  bool(src.get("firm_active") or src.get("firm_bd_active") or src.get("firm_ia_active")),
            "is_bd":       bool(src.get("firm_bd_active")),
            "is_ia":       bool(src.get("firm_ia_active")),
            "other_names": src.get("firm_other_names", []),
        })
    return {
        "query":   firm_name,
        "n_total": total,
        "matches": matches,
    }


if __name__ == "__main__":
    import json
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Capital One Securities"
    print(json.dumps(query_firm(name), indent=2, default=str))
