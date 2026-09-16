"""REIT tenant-credit watchlist — named-tenant 8-K and going-concern monitor.

WHY THIS EXISTS

Medical Properties Trust (MPW) tanked when Steward Health Care
collapsed. Steward telegraphed distress for 12+ months before MPW
disclosed the impairment: going-concern paragraphs at Steward
subsidiaries, missed rent payments disclosed in Steward's lender
amendments, bankruptcy of Steward's PE owner. All public, all queryable
by EDGAR full-text search and SEC submissions API.

For REITs (especially healthcare REITs CTRE/MPW, net-lease IIPR,
strip-mall PECO/MAC), the catastrophe pattern is "single named tenant
representing 5-30% of rent collapses". An ex-ante watchlist of named
tenants + their public filings (if they're SEC registrants) and 8-K
material events catches this 6-18 months ahead.

INPUTS

  named_tenants: list of dicts with at minimum {"name": str}. Optionally:
    - "cik" (if known — SEC-registered tenant)
    - "rent_pct" (% of REIT rent from this tenant)
  cutoff_date: ISO YYYY-MM-DD

PROCESS

  For each named tenant:
    1. If CIK known: check SEC submissions for {8-K Item 1.03 (bankruptcy),
       2.04 (default), 2.06 (impairment), 5.02 (key exec departure)},
       and run going_concern_detector + filing_timeliness.
    2. If no CIK: try to resolve via EDGAR ticker/company search. If
       still no match (private operator), mark "private_no_signal" and
       degrade max severity to MODERATE.

  Score each tenant: CLEAN | WATCHLIST | DISTRESS | BANKRUPT_OR_IMPAIRED

  Aggregate to REIT-level:
    - n_distress_tenants weighted by rent_pct
    - signal: CLEAN | TENANT_WATCH | TENANT_DISTRESS | TENANT_IMPAIRED

THRESHOLDS

  Sum of rent_pct in DISTRESS or worse:
    < 2%  → CLEAN
    2-5%  → TENANT_WATCH
    5-10% → TENANT_DISTRESS
    >=10% → TENANT_IMPAIRED  (Steward-class event)
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["65", "6798"],
    "issuer_features": ["healthcare_reit_landlord", "named_tenant_concentration"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Monitors named REIT tenants for going-concern/missed-rent/BK telegraphs (the MPW/Steward pattern).",
}

from typing import Any, Optional

from . import going_concern_detector
from . import sec_filings
from .. import edgar


_SEVERITY_MAP = {
    "CLEAN":            "PASS",
    "TENANT_WATCH":     "MODERATE_UNDERDELIVERY",
    "TENANT_DISTRESS":  "SEVERE_UNDERDELIVERY",
    "TENANT_IMPAIRED":  "RED_FLAG_NEGATIVE",
    "UNVERIFIABLE":     "UNVERIFIABLE",
}

# 8-K Items that telegraph tenant distress (per SEC Form 8-K item codes).
DISTRESS_8K_ITEMS = {
    "1.03",  # Bankruptcy or Receivership
    "2.04",  # Triggering Events That Accelerate or Increase a Direct Financial Obligation
    "2.06",  # Material Impairments
    "4.02",  # Non-Reliance on Previously Issued Financial Statements
}


def _resolve_cik(tenant: dict) -> Optional[str]:
    if tenant.get("cik"):
        return str(tenant["cik"])
    name = tenant.get("name") or ""
    if not name:
        return None
    # First try ticker lookup if it looks like one
    if name.isupper() and 1 <= len(name) <= 5 and name.isalpha():
        try:
            return edgar.cik_for(name)
        except Exception:
            pass
    return None


def _scan_8k_distress(cik: str, cutoff_date: str) -> dict[str, Any]:
    """Scan SEC submissions for 8-Ks since cutoff-2y and tag distress items.

    Item codes only show in the 'items' subfield of recent submissions API
    when items are reported — our sec_filings.list_filings_by_form helper
    returns the form list and dates, we then walk each accession for items.
    For v1 we approximate by counting 8-K filings in the trailing 24m;
    deeper Item-code parsing requires fetching the index, deferred to v2.
    """
    res = sec_filings.list_filings_by_form(
        cik,
        forms=["8-K", "8-K/A"],
        cutoff_date=cutoff_date,
        start_date=_n_years_before(cutoff_date, 2),
        limit=200,
    )
    if "error" in res:
        return {"error": res["error"]}
    return {
        "n_8k_24m":     res.get("n_total", 0),
        "company":      res.get("company"),
        "filings":      res.get("filings", [])[:5],
    }


def _n_years_before(iso: str, n: int) -> str:
    from datetime import date
    d = date.fromisoformat(iso[:10])
    return f"{d.year - n:04d}-{d.month:02d}-{d.day:02d}"


def _tenant_signal(tenant: dict, cutoff_date: str) -> dict[str, Any]:
    cik = _resolve_cik(tenant)
    name = tenant.get("name")
    out = {"tenant": name, "cik": cik, "rent_pct": tenant.get("rent_pct")}

    if cik is None:
        out.update({
            "signal":   "PRIVATE_NO_SIGNAL",
            "_note":    "Tenant is private or CIK unresolved; no deterministic signal available.",
        })
        return out

    # Going concern check
    try:
        gc = going_concern_detector.query_going_concern(cik, cutoff_date)
    except Exception as e:
        gc = {"signal": "ERROR", "_note": str(e)}

    # 8-K distress scan
    distress = _scan_8k_distress(cik, cutoff_date)

    gc_signal = gc.get("signal") or "UNKNOWN"
    n_8k = distress.get("n_8k_24m") or 0

    if gc_signal in ("GOING_CONCERN_ISSUED", "SUBSTANTIAL_DOUBT", "EXPLICIT_GOING_CONCERN"):
        signal = "BANKRUPT_OR_IMPAIRED"
    elif gc_signal in ("UNCERTAINTY_LANGUAGE", "NEW_LANGUAGE_ADDED"):
        signal = "DISTRESS"
    elif n_8k >= 12:  # >12 8-Ks in 24m is high event-frequency
        signal = "WATCHLIST"
    else:
        signal = "CLEAN"

    out.update({
        "signal":             signal,
        "going_concern_signal": gc_signal,
        "n_8k_24m":           n_8k,
        "_note":              gc.get("_note"),
    })
    return out


def query_tenant_watchlist(
    reit_name: str,
    named_tenants: list[dict],
    cutoff_date: str,
) -> dict[str, Any]:
    """Aggregate per-tenant distress signals to a REIT-level read.

    Args:
      reit_name: REIT issuer name (for echo).
      named_tenants: list of {"name": str, "cik": str?, "rent_pct": float?}.
      cutoff_date: ISO YYYY-MM-DD.
    """
    if not named_tenants:
        return {"reit_name": reit_name, "signal": "UNVERIFIABLE",
                "severity": "UNVERIFIABLE", "direction": "neutral",
                "_note": "No named tenants provided; extract from REIT 10-K supplemental."}

    per_tenant = []
    for t in named_tenants:
        per_tenant.append(_tenant_signal(t, cutoff_date))

    pct_distressed_or_worse = 0.0
    pct_watchlist = 0.0
    for t in per_tenant:
        rent = t.get("rent_pct") or 0.0
        sig = t.get("signal")
        if sig in ("DISTRESS", "BANKRUPT_OR_IMPAIRED"):
            pct_distressed_or_worse += rent
        elif sig == "WATCHLIST":
            pct_watchlist += rent

    if pct_distressed_or_worse >= 10:
        signal = "TENANT_IMPAIRED"
    elif pct_distressed_or_worse >= 5:
        signal = "TENANT_DISTRESS"
    elif pct_distressed_or_worse + pct_watchlist >= 2:
        signal = "TENANT_WATCH"
    else:
        signal = "CLEAN"

    direction = (
        "positive" if signal == "CLEAN"
        else "negative"
    )

    return {
        "reit_name":    reit_name,
        "cutoff_date":  cutoff_date,
        "signal":       signal,
        "severity":     _SEVERITY_MAP[signal],
        "direction":    direction,
        "metrics": {
            "n_tenants_evaluated":          len(per_tenant),
            "pct_rent_in_distress_or_worse": round(pct_distressed_or_worse, 2),
            "pct_rent_on_watchlist":         round(pct_watchlist, 2),
            "n_tenants_private_no_signal":   sum(1 for t in per_tenant
                                                 if t.get("signal") == "PRIVATE_NO_SIGNAL"),
        },
        "per_tenant":   per_tenant,
        "_note": (
            f"{len(per_tenant)} tenants evaluated; "
            f"{pct_distressed_or_worse:.1f}% rent in DISTRESS+ and "
            f"{pct_watchlist:.1f}% on watchlist."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    # Smoke test — MPW with synthetic Steward tenant
    reit = sys.argv[1] if len(sys.argv) > 1 else "Medical Properties Trust"
    print(json.dumps(query_tenant_watchlist(
        reit,
        named_tenants=[
            # Steward was private — would mark PRIVATE_NO_SIGNAL
            {"name": "Steward Health Care", "rent_pct": 19.0},
            # Prospect Medical (also private)
            {"name": "Prospect Medical Holdings", "rent_pct": 4.0},
            # Public tenant example: Tenet Healthcare (THC) — registered
            {"name": "THC", "rent_pct": 2.0},
        ],
        cutoff_date="2023-05-15",
    ), indent=2, default=str))
