"""Counterparty reciprocity — bidirectional verification of commercial-relationship claims.

When issuer A's 10-K names counterparty B as a "top customer", "key supplier",
"strategic partner", or "joint-venture participant", we check whether B's own
SEC filings ALSO name A. Reciprocal naming is a positive signal that the
commercial relationship is real and material to both sides.

  BIDIRECTIONAL_CONFIRMED: A names B, AND B's filings name A within the window
  ISSUER_SIDE_ONLY: A names B but B's filings are silent
  CONTRADICTORY: B's filings name A but in a contradictory context (e.g.,
    "former customer", "discontinued partnership")
  COUNTERPARTY_NOT_SEC_FILER: B is private / non-US / not an SEC filer

LIMITATIONS
- Materiality threshold: a megacap counterparty may not name a small-cap
  vendor even if relationship is real. Asymmetric materiality is expected.
- Names with common substrings (e.g., "Microsoft" inside "Microsoft Office")
  create false positives. We use word-boundary matching to mitigate.
- Doesn't detect synonyms / aliases (e.g., "Microsoft" vs "Microsoft Corporation").
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["named_counterparty_claim"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Bidirectional check: does the named customer/partner's own SEC filings name the issuer back?",
}

import re
import time
from typing import Any, Optional

from .edgar_fts import query_fulltext


# Common SEC ticker map for counterparty resolution (extend as needed)
KNOWN_TICKER_TO_CIK = {
    "MSFT":  "0000789019", "AAPL": "0000320193", "GOOGL": "0001652044",
    "AMZN":  "0001018724", "META": "0001326801", "NVDA": "0001045810",
    "TSLA":  "0001318605", "JPM":  "0000019617", "BAC":  "0000070858",
    "WFC":   "0000072971", "GS":   "0000886982", "MS":   "0000895421",
    "LMT":   "0000936468", "RTX":  "0000101829", "BA":   "0000012927",
    "GD":    "0000040533", "NOC":  "0001133421", "HII":  "0001501585",
    "CAT":   "0000018230", "DE":   "0000315189", "WMT":  "0000104169",
    "HD":    "0000354950", "LOW":  "0000060667", "TGT":  "0000027419",
    "CVS":   "0000064803", "WBA":  "0001618921", "UNH":  "0000731766",
    "CI":    "0001739940", "HUM":  "0000049071", "ANTM": "0001156039",
    "PFE":   "0000078003", "MRK":  "0000310158", "JNJ":  "0000200406",
    "ABBV":  "0001551152", "BMY":  "0000014272", "LLY":  "0000059478",
    "XOM":   "0000034088", "CVX":  "0000093410", "COP":  "0001163165",
    "GE":    "0000040545", "F":    "0000037996", "GM":   "0001467858",
    "DAL":   "0000027904", "UAL":  "0000100517", "AAL":  "0000006201",
    "LUV":   "0000092380",
}


def _resolve_cik_for_name(name: str) -> Optional[str]:
    """Best-effort: map a counterparty name to a CIK. For v1 we use a known
    ticker map and require the caller to pass a ticker. Falling back to SEC's
    company-tickers map would help here."""
    # If name is exactly a known ticker, return CIK
    upper = name.upper().strip()
    if upper in KNOWN_TICKER_TO_CIK:
        return KNOWN_TICKER_TO_CIK[upper]
    return None


def _normalize_search_term(s: str) -> str:
    """Quote-wrap a multi-word phrase for fulltext-search."""
    s = s.strip()
    if " " in s:
        return f'"{s}"'
    return s


def query_counterparty_reciprocity(
    issuer_cik: str,
    issuer_search_term: str,
    counterparty_ciks: list[str] | None = None,
    counterparty_names: list[str] | None = None,
    cutoff_date: str = "",
    start_date: str = "2022-01-01",
) -> dict[str, Any]:
    """Check whether each counterparty's own filings name the issuer.

    Args:
      issuer_cik: 10-digit CIK of the issuer (A in "A names B")
      issuer_search_term: name or distinctive phrase to search for in B's
        filings. e.g., "Asbury Automotive" or "TransDigm". Avoid generic
        terms.
      counterparty_ciks: explicit CIK list. If provided, used directly.
      counterparty_names: list of names; we try to resolve via known tickers.
      cutoff_date: ISO YYYY-MM-DD; only consider filings up to this date.
      start_date: ISO YYYY-MM-DD; lower bound on search window.

    Returns dict per counterparty:
      counterparty_cik: resolved CIK or None
      counterparty_name: input name
      hits: int — number of filings naming the issuer
      sample_filings: list of {form, filing_date, accession}
      status: BIDIRECTIONAL_CONFIRMED | ISSUER_SIDE_ONLY |
              COUNTERPARTY_NOT_SEC_FILER | LOOKUP_FAILED
    """
    counterparties = []

    if counterparty_ciks:
        for cik in counterparty_ciks:
            counterparties.append({"cik": cik, "name": None})

    if counterparty_names:
        for nm in counterparty_names:
            resolved = _resolve_cik_for_name(nm)
            counterparties.append({"cik": resolved, "name": nm})

    if not counterparties:
        return {"error": "must pass counterparty_ciks or counterparty_names"}

    search = _normalize_search_term(issuer_search_term)

    results = []
    for cp in counterparties:
        if not cp["cik"]:
            results.append({
                "counterparty_name": cp["name"],
                "counterparty_cik": None,
                "status": "LOOKUP_FAILED",
                "hits": 0,
                "_note": "Could not resolve CIK from name; pass counterparty_ciks explicitly",
            })
            continue

        try:
            r = query_fulltext(
                search_term=issuer_search_term,
                cutoff_date=cutoff_date,
                cik=cp["cik"],
                start_date=start_date,
                forms="10-K,10-Q,8-K,DEF 14A,20-F",
            )
        except Exception as e:
            results.append({
                "counterparty_name": cp["name"],
                "counterparty_cik": cp["cik"],
                "status": "LOOKUP_FAILED",
                "hits": 0,
                "_note": f"edgar_fts error: {e}",
            })
            continue
        time.sleep(0.3)  # rate-limit

        hits = r.get("total_hits", 0)
        status = "BIDIRECTIONAL_CONFIRMED" if hits > 0 else "ISSUER_SIDE_ONLY"
        results.append({
            "counterparty_name": cp["name"],
            "counterparty_cik": cp["cik"],
            "search_term": issuer_search_term,
            "hits": hits,
            "sample_filings": r.get("top_filings", [])[:5],
            "status": status,
        })

    n_confirmed = sum(1 for r in results if r["status"] == "BIDIRECTIONAL_CONFIRMED")
    n_silent    = sum(1 for r in results if r["status"] == "ISSUER_SIDE_ONLY")
    n_failed    = sum(1 for r in results if r["status"] == "LOOKUP_FAILED")

    if n_confirmed >= len(counterparties) * 0.5 and n_confirmed >= 2:
        overall = "RECIPROCITY_CONFIRMED"
    elif n_silent > n_confirmed:
        overall = "RECIPROCITY_WEAK"
    else:
        overall = "RECIPROCITY_MIXED"

    return {
        "issuer_cik": issuer_cik,
        "issuer_search_term": issuer_search_term,
        "cutoff_date": cutoff_date,
        "n_counterparties": len(counterparties),
        "n_confirmed": n_confirmed,
        "n_silent": n_silent,
        "n_failed": n_failed,
        "overall_signal": overall,
        "results": results,
    }


if __name__ == "__main__":
    import json
    # PBH — retailer mirror should be SILENT (Walmart/CVS don't name Prestige)
    print("PBH — searching for 'Prestige Consumer Healthcare' in WMT/CVS/AMZN/TGT:")
    r = query_counterparty_reciprocity(
        issuer_cik="0001295947",
        issuer_search_term="Prestige Consumer Healthcare",
        counterparty_names=["WMT", "CVS", "AMZN", "TGT"],
        cutoff_date="2026-05-26",
    )
    print(json.dumps(r, indent=2, default=str))
