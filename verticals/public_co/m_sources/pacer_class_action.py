"""Federal class-action docket scanner — CourtListener-backed.

WHY THIS EXISTS

Federal class actions are a meaningful drag for certain IJR clusters:
  - Wage-hour class actions for staffing (RHI, KFY) and retail
  - Securities 10b-5 class actions (often telegraph accounting issues
    that precede restatement)
  - Product-liability mass torts (chemicals, devices, food)
  - ADA accessibility suits (retail, restaurants)

CourtListener (Free Law Project) maintains RECAP — a free index of
PACER federal docket data. Their REST API is free with rate limits
(no auth required for low-volume; API key for higher-throughput).

  https://www.courtlistener.com/api/rest/v3/dockets/?party_name={name}

We query by party_name with court filters limited to federal district
+ multi-district + appellate. Pull docket entries since cutoff-2y.

OUTPUT

  signal: CLEAN | ROUTINE | ELEVATED | SEVERE_LITIGATION | UNVERIFIABLE
  metrics: {n_dockets_24m, n_securities_suits, n_class_actions,
            n_recent_filings}

THRESHOLDS

  - 0 federal cases as defendant in 24m       → CLEAN
  - 1-5 cases, no securities suit              → ROUTINE
  - 6-15 cases OR 1 securities suit            → ELEVATED
  - >15 cases OR >=2 securities suits          → SEVERE_LITIGATION

CAVEATS

  - CourtListener party-name search has substring tolerance but
    needs disambiguation for common-name defendants (Bank of America
    has hundreds of cases that may not all be the public company).
  - This is a coverage-heavy / precision-medium m-source — use the
    severity-tier signal, not the exact case list, for the IJR
    composite.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "m_source",
    "summary": "CourtListener federal class-action docket scan; wage-hour/10b-5/product classes as a drag/tell for any issuer.",
}

import os
from datetime import date, timedelta
from typing import Any, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# CourtListener now requires API auth on all endpoints (policy change 2025).
# Free tier: register at https://www.courtlistener.com/sign-in/ → API token
# in profile. Set env var COURTLISTENER_API_TOKEN before calling.
API_TOKEN_ENV = "COURTLISTENER_API_TOKEN"

_SEVERITY_MAP = {
    "CLEAN":              "PASS",
    "ROUTINE":            "PASS",
    "ELEVATED":           "MODERATE_UNDERDELIVERY",
    "SEVERE_LITIGATION":  "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE":       "UNVERIFIABLE",
}

# CourtListener nature-of-suit codes for securities + class actions
NOS_SECURITIES = {"850"}  # Securities/Commodities/Exchange
NOS_LABOR = {"710", "720", "730", "740", "751", "790", "791"}
NOS_PRODUCT_LIABILITY = {"365", "367", "368"}
NOS_OTHER_CLASS_HEAVY = {"410", "470"}  # antitrust, racketeering


def _api_url(party_name: str, filed_after: date) -> str:
    # CourtListener v3 dockets API supports `party_name` and `date_filed__gte`.
    from urllib.parse import urlencode
    qs = urlencode({
        "party_name":       party_name,
        "date_filed__gte":  filed_after.isoformat(),
        "court__jurisdiction": "FD",  # Federal District
        "page_size":        50,
    })
    return f"https://www.courtlistener.com/api/rest/v4/dockets/?{qs}"


def _fetch_dockets(party_name: str, filed_after: date) -> tuple[list[dict], Optional[str]]:
    """Returns (dockets, error_note). error_note is non-None on auth/HTTP failure."""
    token = os.environ.get(API_TOKEN_ENV)
    if not token:
        return [], (
            f"CourtListener requires API auth. Set ${API_TOKEN_ENV} "
            "(free token at https://www.courtlistener.com/sign-in/)."
        )
    url = _api_url(party_name, filed_after)
    headers = {**HEADERS, "Authorization": f"Token {token}"}
    out: list[dict] = []
    last_err: Optional[str] = None
    try:
        with httpx.Client(headers=headers, timeout=45) as c:
            while url:
                r = c.get(url)
                if r.status_code == 401:
                    return [], "CourtListener returned 401 — token invalid."
                if r.status_code == 429:
                    return out, "CourtListener returned 429 — rate-limited; partial results."
                if r.status_code != 200:
                    last_err = f"status_{r.status_code}"
                    break
                j = r.json()
                out.extend(j.get("results", []) or [])
                url = j.get("next") or ""
                if len(out) >= 200:
                    break
    except httpx.HTTPError as e:
        last_err = f"http: {e}"
    return out, last_err


def query_class_action_exposure(
    company_name: str,
    cutoff_date: str,
    *,
    lookback_years: int = 2,
) -> dict[str, Any]:
    """Scan CourtListener for federal dockets where company is a party.

    Args:
      company_name: full legal name to match in party_name field.
      cutoff_date: ISO YYYY-MM-DD upper bound on date_filed.
      lookback_years: window size for the docket scan.
    """
    try:
        cutoff = date.fromisoformat(cutoff_date[:10])
    except (ValueError, TypeError):
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": f"bad cutoff {cutoff_date}"}

    filed_after = cutoff - timedelta(days=365 * lookback_years)
    dockets, fetch_err = _fetch_dockets(company_name, filed_after)

    if fetch_err and not dockets:
        return {
            "company_name": company_name,
            "cutoff_date":  cutoff_date,
            "signal":       "UNVERIFIABLE",
            "severity":     _SEVERITY_MAP["UNVERIFIABLE"],
            "direction":    "neutral",
            "metrics":      {"n_dockets_24m": 0},
            "_note":        fetch_err,
        }

    # Discard dockets filed after cutoff
    pre_cutoff = []
    for d in dockets:
        df = d.get("date_filed")
        if df:
            try:
                if date.fromisoformat(df[:10]) > cutoff:
                    continue
            except (ValueError, TypeError):
                pass
        pre_cutoff.append(d)

    n_total = len(pre_cutoff)
    securities = []
    labor = []
    product_liability = []
    class_actions = []
    recent_year = []

    one_year_floor = cutoff - timedelta(days=365)

    for d in pre_cutoff:
        nos_code = str((d.get("nature_of_suit") or "")).strip()
        case_name = d.get("case_name") or ""
        cn_lower = case_name.lower()

        if nos_code in NOS_SECURITIES:
            securities.append(d)
        if nos_code in NOS_LABOR:
            labor.append(d)
        if nos_code in NOS_PRODUCT_LIABILITY:
            product_liability.append(d)

        # Class-action heuristic: cause name often contains 'class action'
        # or 'putative class' or starts with 'in re'.
        if "class action" in cn_lower or "in re " in cn_lower:
            class_actions.append(d)

        df = d.get("date_filed")
        if df:
            try:
                if date.fromisoformat(df[:10]) >= one_year_floor:
                    recent_year.append(d)
            except (ValueError, TypeError):
                pass

    n_securities = len(securities)
    if n_total == 0:
        signal = "CLEAN"
    elif n_securities >= 2 or n_total > 15:
        signal = "SEVERE_LITIGATION"
    elif n_securities >= 1 or n_total >= 6:
        signal = "ELEVATED"
    else:
        signal = "ROUTINE"

    direction = (
        "positive" if signal == "CLEAN"
        else "neutral" if signal == "ROUTINE"
        else "negative"
    )

    return {
        "company_name":  company_name,
        "cutoff_date":   cutoff_date,
        "signal":        signal,
        "severity":      _SEVERITY_MAP[signal],
        "direction":     direction,
        "metrics": {
            "n_dockets_24m":           n_total,
            "n_dockets_trailing_12m":  len(recent_year),
            "n_securities_suits":      n_securities,
            "n_labor_employment":      len(labor),
            "n_product_liability":     len(product_liability),
            "n_class_actions_named":   len(class_actions),
        },
        "securities_sample": [
            {"case_name": d.get("case_name"), "date_filed": d.get("date_filed"),
             "court": (d.get("court") or "").rsplit("/", 1)[-1].rstrip("/")}
            for d in securities[:5]
        ],
        "_note": (
            f"{n_total} federal docket(s) in {lookback_years}y where "
            f"'{company_name}' is a party; {n_securities} securities, "
            f"{len(labor)} labor, {len(product_liability)} product liability."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Wells Fargo"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_class_action_exposure(name, cutoff), indent=2, default=str))
