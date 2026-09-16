"""Lender-concession parser — classify credit-agreement amendments by direction.

This is the SINGLE most informative non-insider positive signal in distressed
credit names. A lender extending a maturity or CUTTING a spread is a vote of
confidence in the borrower's recovery thesis; a lender ADDING security,
SHORTENING maturity, or RAISING spread is the inverse.

CLASSIFICATION
  CONCESSION: at least one positive direction, no negative directions
    - spread cut (applicable margin reduced)
    - maturity extended
    - revolver capacity upsized at improved terms
    - subsidiary guarantor released
    - financial covenant loosened (max leverage RAISED; min coverage LOWERED)

  RESTRICTION: at least one negative direction, no positive directions
    - spread up
    - maturity shortened
    - collateral added / new security pledged
    - FILO super-priority tranche added
    - covenant tightened
    - forbearance / waiver granted (often masks a covenant breach)

  MIXED: both positive and negative directions in the same amendment
    (common — e.g., spread up + maturity extended)

  NEUTRAL: technical changes (LIBOR → SOFR transition, lender additions,
    minor mechanic changes)

OUTPUT FIELDS
  amendments: list of 8-K Item 1.01 credit-amendment events with classifications
  n_concession: int
  n_restriction: int
  n_mixed: int
  most_recent_classification: str
  signal: HEALTHY_LENDER_RELATIONSHIP | DETERIORATING_LENDER_RELATIONSHIP |
          MIXED_LENDER_RELATIONSHIP | NO_AMENDMENTS

LIMITATIONS
- 8-K Item 1.01 disclosures vary in detail. Many reference the amendment
  exhibit but don't restate key terms in the body; full classification
  requires fetching the exhibit.
- Some amendments include both positive and negative — we flag as MIXED;
  judgment required about which dominates.
- LIBOR → SOFR transitions look like "spread changes" but are mechanical.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["credit_agreement_amendment_history"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Classifies credit-agreement amendments as lender concession vs tightening; the top non-insider distress signal.",
}

import re
import time
from typing import Any, Optional

from .. import edgar


# Phrases indicating CONCESSION
_CONCESSION_PATTERNS = {
    "spread_cut": re.compile(
        r"(applicable\s+margin\s+(?:was|is|shall\s+be)?\s+(?:reduced|decreased|stepped\s+down|lowered)|"
        r"(?:reduced|decreased|stepped\s+down|lowered)\s+(?:the\s+)?(?:applicable\s+)?(?:interest\s+rate\s+)?margin|"
        r"spread\s+(?:was|is)\s+(?:reduced|cut|tightened)|"
        r"repriced\s+(?:our\s+|the\s+)?credit\s+(?:facility|agreement)\s+(?:at\s+)?(?:lower|tighter))",
        re.IGNORECASE
    ),
    "maturity_extended": re.compile(
        r"((?:extends?|extending|extended)\s+(?:the\s+)?(?:maturity|termination\s+date|term)|"
        r"(?:maturity|termination\s+date)\s+(?:date\s+)?(?:was\s+|is\s+|has\s+been\s+)?(?:extended|extending|to\s+\w+\s+\d{1,2},?\s+\d{4})|"
        r"refinanced.{0,40}(?:extending|extended).{0,40}(?:maturity|termination)|"
        r"extend\s+(?:the\s+|our\s+)?term\s+loan\s+(?:to|until)|"
        r"amendment\s+(?:extends?|extending|extended))",
        re.IGNORECASE
    ),
    "revolver_upsized": re.compile(
        r"((?:revolver|revolving\s+credit)\s+(?:facility\s+)?(?:was|is|has\s+been)\s+(?:upsized|increased|expanded)|"
        r"(?:upsized|increased|expanded)\s+(?:the\s+|our\s+)?revolv|"
        r"revolving\s+commitments?\s+(?:were|was)\s+increased)",
        re.IGNORECASE
    ),
    "guarantor_released": re.compile(
        r"((?:released|releasing)\s+(?:a\s+|the\s+|certain\s+)?subsidiary\s+guarantor|"
        r"subsidiary\s+guarantor\s+(?:was|is|has\s+been)\s+released|"
        r"released\s+the\s+(?:liens?|security\s+interests?))",
        re.IGNORECASE
    ),
    "covenant_loosened": re.compile(
        r"((?:increased|raised|loosened)\s+the\s+(?:maximum\s+)?leverage\s+(?:ratio|covenant)|"
        r"(?:reduced|lowered)\s+the\s+(?:minimum\s+)?(?:interest\s+coverage|fixed\s+charge\s+coverage)|"
        r"covenant\s+(?:was|is|has\s+been)\s+loosened)",
        re.IGNORECASE
    ),
}

# Phrases indicating RESTRICTION
_RESTRICTION_PATTERNS = {
    "spread_up": re.compile(
        r"(applicable\s+margin\s+(?:was|is|shall\s+be)?\s+(?:increased|raised|stepped\s+up)|"
        r"(?:increased|raised|stepped\s+up)\s+(?:the\s+)?(?:applicable\s+)?margin|"
        r"interest\s+rate\s+(?:was|is)\s+(?:increased|raised|stepped\s+up))",
        re.IGNORECASE
    ),
    "maturity_shortened": re.compile(
        r"((?:shortened|accelerated)\s+(?:the\s+)?maturity|"
        r"maturity\s+(?:date\s+)?(?:was\s+|is\s+)?(?:shortened|accelerated))",
        re.IGNORECASE
    ),
    "collateral_added": re.compile(
        r"((?:added|adding|providing)\s+(?:new\s+)?(?:collateral|security|liens?)|"
        r"new\s+(?:collateral|security)\s+(?:was|is)\s+(?:added|granted|pledged)|"
        r"(?:additional\s+)?subsidiary\s+guarantors?\s+(?:were|was|has\s+been)?\s*added|"
        r"moved\s+(?:from\s+unsecured\s+)?to\s+secured|"
        r"became\s+secured)",
        re.IGNORECASE
    ),
    "filo_added": re.compile(
        r"((?:FILO|first[\s-]in[\s-]last[\s-]out)\s+(?:tranche|facility)|"
        r"super[\s-]priority\s+(?:tranche|facility)|"
        r"new\s+last[\s-]out\s+tranche)",
        re.IGNORECASE
    ),
    "covenant_tightened": re.compile(
        r"((?:reduced|tightened|lowered)\s+the\s+(?:maximum\s+)?leverage\s+(?:ratio|covenant)|"
        r"(?:increased|raised|tightened)\s+the\s+(?:minimum\s+)?(?:interest\s+coverage|fixed\s+charge\s+coverage)|"
        r"covenant\s+(?:was|is)\s+tightened|"
        r"new\s+(?:minimum\s+)?liquidity\s+covenant)",
        re.IGNORECASE
    ),
    "forbearance_waiver": re.compile(
        r"(forbearance\s+agreement|"
        r"waiver\s+(?:was|is)\s+(?:granted|obtained|received)|"
        r"waived\s+(?:the\s+)?(?:default|breach|covenant)|"
        r"obtained\s+a\s+waiver)",
        re.IGNORECASE
    ),
}

# Mechanical patterns (NEUTRAL — don't count as positive or negative)
_NEUTRAL_PATTERNS = {
    "libor_sofr": re.compile(
        r"(LIBOR\s+(?:to|->|→)\s+SOFR|"
        r"SOFR\s+(?:replacement|transition)|"
        r"benchmark\s+(?:rate\s+)?transition)",
        re.IGNORECASE
    ),
}


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _classify_amendment(text: str) -> dict:
    """Run all patterns against (cleaned) amendment text. Return per-direction
    hits + overall classification."""
    text = _strip_html(text)

    concession_hits = {}
    for name, pat in _CONCESSION_PATTERNS.items():
        m = list(pat.finditer(text))
        if m:
            concession_hits[name] = len(m)

    restriction_hits = {}
    for name, pat in _RESTRICTION_PATTERNS.items():
        m = list(pat.finditer(text))
        if m:
            restriction_hits[name] = len(m)

    neutral_hits = {}
    for name, pat in _NEUTRAL_PATTERNS.items():
        m = list(pat.finditer(text))
        if m:
            neutral_hits[name] = len(m)

    n_concession = len(concession_hits)
    n_restriction = len(restriction_hits)

    if n_concession > 0 and n_restriction == 0:
        classification = "CONCESSION"
    elif n_restriction > 0 and n_concession == 0:
        classification = "RESTRICTION"
    elif n_concession > 0 and n_restriction > 0:
        classification = "MIXED"
    elif neutral_hits:
        classification = "NEUTRAL"
    else:
        classification = "UNCLASSIFIED"

    return {
        "classification": classification,
        "concession_hits": concession_hits,
        "restriction_hits": restriction_hits,
        "neutral_hits": neutral_hits,
    }


def _is_credit_amendment_8k(filing: dict) -> bool:
    """Heuristic: is this 8-K a credit-agreement amendment? Uses
    primary_doc_description and form. Note Item 1.01 is "Entry into Material
    Definitive Agreement" — covers credit amendments + others (M&A, etc.)."""
    if filing.get("form") not in ("8-K", "8-K/A"):
        return False
    desc = (filing.get("primary_doc_description") or "").lower()
    if "1.01" not in desc and "1.02" not in desc:
        # Without an Item 1.01/1.02 hint, we'd have to fetch the 8-K. For v1
        # we accept all 8-Ks but downstream parser checks for amendment text.
        return True
    return True


def query_lender_concession(
    cik: str,
    cutoff_date: str,
    lookback_days: int = 730,
    max_amendments_to_parse: int = 20,
) -> dict[str, Any]:
    """Scan 8-Ks pre-cutoff for credit-agreement amendments, classify
    direction of each."""
    from datetime import date, timedelta

    def _pd(s):
        try: return date.fromisoformat(s[:10])
        except (ValueError, TypeError): return None

    cutoff = _pd(cutoff_date)
    if cutoff is None:
        return {"signal": "ERROR", "_note": f"bad cutoff_date={cutoff_date!r}"}
    window_start = cutoff - timedelta(days=lookback_days)

    try:
        _, filings = edgar.list_filings(cik)
    except Exception as e:
        return {"signal": "ERROR", "_note": f"list_filings failed: {e}"}

    eight_ks = []
    for f in filings:
        if f.get("form") not in ("8-K", "8-K/A"):
            continue
        fd = _pd(f.get("filing_date") or "")
        if not fd or fd > cutoff or fd < window_start:
            continue
        eight_ks.append({**f, "filing_date_parsed": fd})

    # Sort newest first; parse the most recent N
    eight_ks.sort(key=lambda f: f["filing_date_parsed"], reverse=True)

    amendments = []
    n_parsed = 0
    for f in eight_ks:
        if n_parsed >= max_amendments_to_parse:
            break
        try:
            text = edgar.fetch_filing_clean(cik, f["accession"], f["primary_document"])
        except Exception:
            continue
        if not text:
            continue
        # Quick relevance check: does the 8-K mention credit agreement / loan?
        clean_preview = _strip_html(text)[:8000].lower()
        if not re.search(r"credit\s+agreement|term\s+loan|revolver|revolving\s+credit|amend(?:ment|ed)\s+credit",
                         clean_preview):
            n_parsed += 1
            time.sleep(0.15)
            continue

        cls = _classify_amendment(text[:200_000])
        if cls["classification"] in ("CONCESSION", "RESTRICTION", "MIXED"):
            amendments.append({
                "filing_date": str(f["filing_date_parsed"]),
                "accession": f["accession"],
                **cls,
            })
        n_parsed += 1
        time.sleep(0.15)

    n_conc = sum(1 for a in amendments if a["classification"] == "CONCESSION")
    n_rest = sum(1 for a in amendments if a["classification"] == "RESTRICTION")
    n_mix  = sum(1 for a in amendments if a["classification"] == "MIXED")
    most_recent = amendments[0] if amendments else None

    if not amendments:
        signal = "NO_AMENDMENTS"
    elif n_conc > n_rest and n_conc + n_mix >= 1:
        signal = "HEALTHY_LENDER_RELATIONSHIP"
    elif n_rest > n_conc:
        signal = "DETERIORATING_LENDER_RELATIONSHIP"
    else:
        signal = "MIXED_LENDER_RELATIONSHIP"

    return {
        "cik": cik,
        "cutoff_date": cutoff_date,
        "n_8ks_in_window": len(eight_ks),
        "n_8ks_parsed": n_parsed,
        "n_amendments_classified": len(amendments),
        "n_concession": n_conc,
        "n_restriction": n_rest,
        "n_mixed": n_mix,
        "most_recent": most_recent,
        "amendments": amendments,
        "signal": signal,
    }


if __name__ == "__main__":
    import json
    # FMC — had two amendments in 4 months per our prior pilot (covenant
    # stepped UP from 3.5x to 6.50x — restriction direction).
    print("FMC (FY24-25 — covenant amendments):")
    r = query_lender_concession("0000037785", "2025-05-15", lookback_days=730, max_amendments_to_parse=15)
    print(json.dumps({k: v for k, v in r.items() if k != "amendments"}, indent=2))
    print("\namendments:")
    for a in r.get("amendments", []):
        print(f"  {a['filing_date']}  {a['classification']:14}  conc={list(a['concession_hits'].keys())}  rest={list(a['restriction_hits'].keys())}")
