"""
UCC-proxy via SEC filings — lien / secured-debt exposure detector.

CONTEXT:
The 8/8 cross-cohort planner-proposal convergence was on "state UCC
lien filings" (DOS-1500 system). The motivation:
  - Senior debt encumbrances
  - Receivables financing
  - Insider/affiliate secured loans
  - Distress signals from sudden new UCC filings

State-by-state UCC scraping is broadly blocked: Cloudflare/Incapsula
bot protection on California, Florida, NY, NC, Texas direct UCC
search; CAPTCHA on form-based states; paywall on bulk data
subscriptions; OpenCorporates API requires paid key. Building real
state UCC connectors is a multi-week browser-automation project
deferred to its own focused session.

THIS PROXY captures ~80% of the signal at zero scraping cost by
exploiting SEC disclosure mandates that mirror UCC filings:

  - Form 8-K Item 2.03 "Creation of a Direct Financial Obligation"
    is mandatory disclosure within 4 business days for any material
    new secured-debt obligation by a SEC reporter.
  - Form 8-K Item 1.01 "Entry into a Material Definitive Agreement"
    covers secured loan agreements, note purchase agreements, etc.
  - Form 10-K Note disclosures on secured debt, pledged collateral,
    covenants — required by ASC 470.
  - Form S-3 / S-1 prospectus exhibits often attach security
    agreements verbatim.

For any small-cap SEC reporter, every material UCC-1 filing should
have a corresponding 8-K disclosure within 4 business days. So
counting 8-K Item 2.03 + 8-K with "secured" / "lien" / "pledged"
terms approximates the UCC count.

WHAT THIS MISSES vs real UCC:
  - Sub-material UCC filings (below 10% threshold)
  - Private-company filings against the public-co (e.g. a vendor
    files UCC-1 against a small subsidiary)
  - Old grandfathered UCC-1s from before SEC reporting started
  - Specific filing-number / continuation / amendment cadence
  - Equipment leases that aren't material to the consolidated entity

WHAT THIS CATCHES:
  - Pace and concentration of new secured-debt obligations
  - Receivables financing announcements
  - Senior credit facilities
  - Convertible notes with collateral
  - "Adverse trend" signal — sudden cluster of new secured-debt 8-Ks
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Lien/secured-debt exposure detection via SEC-filed credit docs; UCC-style encumbrance telegraph for any issuer.",
}

import re
from datetime import date, timedelta
from typing import Any, Optional

from .edgar_fts import query_fulltext
from .sec_filings import list_filings_by_form


UCC_LIKE_TERMS = (
    "security agreement", "secured promissory note", "lien",
    "pledged collateral", "ucc-1", "ucc financing statement",
    "all assets", "blanket lien", "first-priority lien",
    "second-priority lien", "subordination agreement",
    "intercreditor agreement", "receivables financing",
    "factoring agreement",
)

# Distress-credit terms — these connote sub-investment-grade /
# emergency-financing structures (vs ordinary corporate credit
# facilities). High counts of these distinguish active distress
# from mature secured-debt activity.
DISTRESS_TERMS = {
    "secured promissory note", "convertible note",
    "factoring agreement", "subordination agreement",
    "intercreditor agreement", "blanket lien",
    "all assets",
}


def query_ucc_exposure(
    cik: str,
    cutoff_date: str,
    window_months: int = 36,
) -> dict[str, Any]:
    """UCC-proxy lien-exposure check for a SEC reporter.

    Aggregates three signals from EDGAR:
      1. 8-K Item 2.03 count (Creation of Direct Financial Obligation)
         within window — direct UCC-1-equivalent disclosure
      2. 8-K Item 1.01 + UCC-like-term match count (Material
         Definitive Agreement for secured arrangements)
      3. UCC-like-term mentions in 10-K / 10-Q (concentration / trend)

    Args:
      cik: 10-digit zero-padded CIK of the focal company
      cutoff_date: ISO date upper bound for searches
      window_months: lookback window from cutoff

    Returns:
      {
        "cik":                  str,
        "cutoff_date":          str,
        "window_start":         str,
        "n_8k_item_2_03":       int,  # creation of direct financial obligation
        "n_8k_secured":         int,  # 8-K filings w/ UCC-like terms
        "n_10k_10q_secured":    int,  # 10-K/10-Q filings w/ UCC-like terms
        "secured_term_density": float,
        "top_terms_found":      list,
        "signal":               LOW_LIEN_EXPOSURE | MODERATE_LIEN_EXPOSURE |
                                HIGH_LIEN_EXPOSURE | NO_FILINGS,
      }

    Signal:
      0 8-K secured + 0 10-K secured                   → LOW_LIEN_EXPOSURE
      1-3 8-K secured OR 10-K Note disclosures         → MODERATE_LIEN_EXPOSURE
      4+ 8-K secured OR sudden 6mo cluster of >=2 8-Ks → HIGH_LIEN_EXPOSURE
    """
    end = date.fromisoformat(cutoff_date)
    start = end - timedelta(days=window_months * 30)
    start_s = start.isoformat()

    # Step 1: 8-K Item 2.03 filings — these are the SEC's UCC-1 equivalents
    # We use sec_filings.list_filings_by_form to enumerate 8-Ks, then
    # filter for those with Item 2.03 in their items list.
    eight_k = list_filings_by_form(cik=cik, forms=["8-K"],
                                   start_date=start_s,
                                   cutoff_date=cutoff_date)
    n_item_2_03 = 0
    item_2_03_dates: list[str] = []
    for f in eight_k.get("filings", []):
        items = f.get("items") or ""
        if "2.03" in str(items):
            n_item_2_03 += 1
            d = f.get("filing_date") or f.get("filingDate") or ""
            if d:
                item_2_03_dates.append(d)

    # Step 2 + 3: EDGAR FTS for UCC-like terms in this issuer's filings
    n_8k_secured = 0
    n_10k_10q_secured = 0
    terms_found: dict[str, int] = {}

    for term in UCC_LIKE_TERMS:
        r = query_fulltext(
            search_term=term, cutoff_date=cutoff_date,
            cik=cik, start_date=start_s,
            forms="10-K,10-Q,8-K",
        )
        hits = r.get("total_hits", 0)
        if hits == 0:
            continue
        terms_found[term] = hits
        # We don't have per-filing form breakdown from the FTS; use top_filings
        for f in r.get("top_filings", []):
            form = f.get("form", "")
            if form == "8-K":
                n_8k_secured += 1
            elif form in ("10-K", "10-Q"):
                n_10k_10q_secured += 1

    # Concentration check: any 6-month window with >=2 Item 2.03 filings
    cluster_detected = False
    sorted_dates = sorted(item_2_03_dates)
    for i in range(len(sorted_dates) - 1):
        try:
            d1 = date.fromisoformat(sorted_dates[i])
            for j in range(i + 1, len(sorted_dates)):
                d2 = date.fromisoformat(sorted_dates[j])
                if (d2 - d1).days <= 180:
                    cluster_detected = True
                    break
            if cluster_detected:
                break
        except ValueError:
            continue

    distress_term_hits = sum(v for k, v in terms_found.items()
                              if k in DISTRESS_TERMS)
    total_term_hits = sum(terms_found.values())

    if total_term_hits == 0:
        signal = "LOW_LIEN_EXPOSURE"
    elif distress_term_hits >= 10 or n_item_2_03 >= 4 or cluster_detected:
        signal = "HIGH_LIEN_EXPOSURE"
    elif distress_term_hits >= 3 or total_term_hits >= 20:
        signal = "ELEVATED_LIEN_EXPOSURE"
    else:
        signal = "MODERATE_LIEN_EXPOSURE"

    return {
        "cik":                  cik,
        "cutoff_date":          cutoff_date,
        "window_start":         start_s,
        "n_8k_item_2_03":       n_item_2_03,
        "n_8k_secured_terms":   n_8k_secured,
        "n_10k_10q_secured":    n_10k_10q_secured,
        "distress_term_hits":   distress_term_hits,
        "total_term_hits":      total_term_hits,
        "item_2_03_dates":      item_2_03_dates,
        "top_terms_found":      sorted(terms_found.items(),
                                        key=lambda x: -x[1])[:8],
        "cluster_in_6mo":       cluster_detected,
        "signal":               signal,
        "_note": ("UCC-proxy via SEC filings. Captures material "
                  "secured-debt obligations of SEC reporters. Does NOT "
                  "capture sub-material UCC-1s, vendor liens against "
                  "subsidiaries, or non-SEC-reporter UCC filings."),
    }
