"""
USAspending.gov connector — verifies named federal contract / DoD claims.

USAspending aggregates federal procurement (FPDS) and financial assistance
(FAADS) data. Free public API at https://api.usaspending.gov.

Primary use: when a public-co filing claims "we have $X in DoD contracts" or
"we were awarded program Y", query the recipient's actual contract history
and compare.

UEI-anchored queries (preferred):
  resolve_recipient_ueis(name) → list of UEI matches (parent + subs)
  Then call query_recipient_contracts(uei) — passing a UEI as the
  "recipient_name" works because UEIs are unique 12-char codes and the
  recipient_search_text filter matches them exactly.

Why UEI-anchored: bare-name substring matching causes severe pollution
(e.g. "Hudson Technologies" matches 67k unrelated entities; "AIRO"
matches 119 noise hits while "Airo Group" gets 0). UEI lookup goes via
/api/v2/recipient/duns/ which returns the canonical UEI per recipient
along with parent/child structure.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["873", "737", "381", "372"],
    "issuer_features": ["mentions_dod_customer", "government_customer_concentration_above_5pct"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "USAspending obligations vs claimed federal contract awards; include the corporate family, censor by publication date.",
}

import re
import time
from typing import Any

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local",
           "Accept": "application/json",
           "Content-Type": "application/json"}
BASE = "https://api.usaspending.gov/api/v2"

CONTRACT_AWARD_CODES = ["A", "B", "C", "D"]  # contract types
GRANT_AWARD_CODES    = ["02", "03", "04", "05"]
IDV_AWARD_CODES      = ["IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", "IDV_B_C", "IDV_C",
                        "IDV_D", "IDV_E"]


def query_recipient_contracts(
    recipient_name: str,
    start_date: str = "2020-01-01",
    end_date:   str = "2026-12-31",
    awarding_agency: str | None = None,
    awarding_agency_tier: str = "toptier",
    page_size: int = 25,
) -> dict[str, Any]:
    """
    Search federal CONTRACT awards by recipient name (substring match).

    Returns dict:
        {
          "n_awards":     int (count of contract awards in window),
          "total_amount": float (sum of award amounts),
          "top_awards":   list of top page_size by amount,
          "agencies":     dict {agency_name: count},
          "query":        echo of inputs,
        }
    """
    filters: dict[str, Any] = {
        "recipient_search_text": [recipient_name],
        "award_type_codes":      CONTRACT_AWARD_CODES,
        "time_period":           [{"start_date": start_date, "end_date": end_date}],
    }
    if awarding_agency:
        filters["agencies"] = [{"type": "awarding", "tier": awarding_agency_tier, "name": awarding_agency}]

    body = {
        "filters": filters,
        "fields":  ["Award ID", "Recipient Name", "Awarding Agency",
                    "Award Amount", "Period of Performance Start Date",
                    "Period of Performance Current End Date",
                    "Description"],
        "page":    1,
        "limit":   page_size,
        "sort":    "Award Amount",
        "order":   "desc",
    }

    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r = c.post(f"{BASE}/search/spending_by_award/", json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        return {"error": f"USAspending API: {e}",
                "n_awards": 0, "total_amount": 0.0, "top_awards": [], "agencies": {}}

    results = data.get("results") or []
    agencies: dict[str, int] = {}
    total = 0.0
    for row in results:
        amt = float(row.get("Award Amount") or 0)
        total += amt
        ag = row.get("Awarding Agency") or "?"
        agencies[ag] = agencies.get(ag, 0) + 1

    # Get true count (the page can be exhausted)
    count_body = {"filters": filters, "subawards": False}
    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r2 = c.post(f"{BASE}/search/spending_by_award_count/", json=count_body)
            if r2.status_code == 200:
                counts = r2.json().get("results", {})
                n_awards = counts.get("contracts", 0)
            else:
                n_awards = len(results)
    except httpx.HTTPError:
        n_awards = len(results)

    return {
        "n_awards":     n_awards,
        "total_amount": total,
        "top_awards":   results,
        "agencies":     agencies,
        "query": {
            "recipient_name":  recipient_name,
            "start_date":      start_date,
            "end_date":        end_date,
            "awarding_agency": awarding_agency,
        },
    }


def query_dod_contracts(recipient_name: str,
                        start_date: str = "2020-01-01",
                        end_date:   str = "2026-12-31",
                        page_size: int = 25) -> dict[str, Any]:
    """Convenience: query Department of Defense contracts only."""
    return query_recipient_contracts(
        recipient_name=recipient_name,
        start_date=start_date,
        end_date=end_date,
        awarding_agency="Department of Defense",
        page_size=page_size,
    )


def query_recipient_grants(recipient_name: str,
                           start_date: str = "2020-01-01",
                           end_date:   str = "2026-12-31",
                           page_size: int = 10) -> dict[str, Any]:
    """Federal financial assistance (grants, cooperative agreements) awarded to recipient."""
    body = {
        "filters": {
            "recipient_search_text": [recipient_name],
            "award_type_codes":      GRANT_AWARD_CODES,
            "time_period":           [{"start_date": start_date, "end_date": end_date}],
        },
        "fields": ["Award ID", "Recipient Name", "Awarding Agency", "Award Amount",
                   "Period of Performance Start Date"],
        "page": 1, "limit": page_size, "sort": "Award Amount", "order": "desc",
    }
    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r = c.post(f"{BASE}/search/spending_by_award/", json=body)
            r.raise_for_status()
            results = r.json().get("results", [])
    except httpx.HTTPError as e:
        return {"error": str(e), "n_awards": 0, "total_amount": 0.0,
                "agencies": {}, "top_awards": []}
    total = 0.0
    agencies: dict[str, int] = {}
    for row in results:
        amt = row.get("Award Amount") or 0
        try: total += float(amt)
        except (TypeError, ValueError): pass
        ag = row.get("Awarding Agency")
        if ag: agencies[ag] = agencies.get(ag, 0) + 1
    return {"n_awards": len(results), "total_amount": total,
            "agencies": agencies, "top_awards": results,
            "query": {"recipient_name": recipient_name, "start_date": start_date, "end_date": end_date}}


def resolve_recipient_ueis(name: str, limit: int = 10,
                            match_mode: str = "word_boundary") -> list[dict[str, Any]]:
    """Resolve a recipient name to its UEI(s) via /api/v2/recipient/duns/.

    Returns a list of dicts with {name, uei, duns, recipient_level, amount}.
    recipient_level: P=parent, C=child/subsidiary, R=other.

    The /recipient/duns/ endpoint matches `keyword` as a server-side
    substring across all recipient names, which produces severe noise
    for short or common-fragment names (e.g. 'AIRO' matches 'KAIROS
    POWER', 'AMERICAN UNIVERSITY IN CAIRO', 'UNIVERSITY OF NAIROBI').
    We post-filter using word-boundary regex on the returned `name` so
    the search behaves like "name appears as a whole token in the
    recipient name."

      match_mode='word_boundary' (default) — keyword must appear as a
        word-boundary-delimited token in the returned name
      match_mode='substring' — legacy substring (server-side raw)
      match_mode='exact' — full case-insensitive equality

    Pass multiple subsidiary names (from 10-K Exhibit 21) via the
    higher-level query_federal_presence wrapper to cover roll-ups
    that register awards under operating-entity rather than parent
    names (e.g. AIRO Group → Coastal Defense Inc / Aspen Avionics /
    Jaunt Air Mobility).
    """
    body = {"keyword": name, "limit": max(limit, 25), "award_type": "all"}
    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r = c.post(f"{BASE}/recipient/duns/", json=body)
            r.raise_for_status()
            results = r.json().get("results", [])
    except httpx.HTTPError as e:
        return []

    if match_mode == "word_boundary":
        pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
        def _ok(nm: str) -> bool:
            return bool(pattern.search(nm or ""))
    elif match_mode == "exact":
        nm_upper = name.upper()
        def _ok(nm: str) -> bool:
            return (nm or "").upper() == nm_upper
    else:
        nm_upper = name.upper()
        def _ok(nm: str) -> bool:
            return nm_upper in (nm or "").upper()

    out = []
    seen_uei = set()
    for row in results:
        uei = row.get("uei")
        if not uei or uei in seen_uei:
            continue
        if not _ok(row.get("name") or ""):
            continue
        seen_uei.add(uei)
        out.append({
            "name": row.get("name"),
            "uei": uei,
            "duns": row.get("duns"),
            "recipient_level": row.get("recipient_level"),
            "fy_amount_snapshot": row.get("amount", 0),
        })
        if len(out) >= limit:
            break
    return out


def query_by_uei(
    uei: str,
    start_date: str = "2018-01-01",
    end_date: str = "2026-12-31",
    contracts: bool = True,
    page_size: int = 25,
) -> dict[str, Any]:
    """Exact-match query by UEI. Calls query_recipient_contracts or
    query_recipient_grants with the UEI passed as the recipient_name —
    the underlying recipient_search_text filter matches UEI strings
    exactly (12-char alphanumeric, no collisions).
    """
    fn = query_recipient_contracts if contracts else query_recipient_grants
    return fn(recipient_name=uei, start_date=start_date,
              end_date=end_date, page_size=page_size)


def query_federal_presence(
    name_variants: list[str] | str,
    start_date: str = "2018-01-01",
    end_date: str = "2026-12-31",
    include_grants: bool = True,
) -> dict[str, Any]:
    """One-shot UEI-anchored federal presence query.

    Resolves all candidate name variants → list of UEIs (parent +
    subsidiaries, deduped), then queries contracts (and optionally
    grants) per UEI, then aggregates.

    Returns:
      {
        "name_variants": [...],
        "n_ueis_resolved": int,
        "ueis": [{name, uei, recipient_level}, ...],
        "n_contracts": int,
        "contracts_amount_M": float,
        "n_grants": int,
        "grants_amount_M": float,
        "agencies": {agency_name: count, ...},
        "top_awards": [...],     # top contracts across all UEIs
        "signal": INFLATION_SUSPECT | SUB_MATERIAL_FEDERAL |
                  RECURRING_FEDERAL,
      }

    Signal mapping:
      - 0 UEIs resolved AND 0 contracts → INFLATION_SUSPECT (strong
        absence: no recipient profile exists at all)
      - Some UEIs + small amount (< $5M lifetime) → SUB_MATERIAL_FEDERAL
      - Material federal presence (> $5M lifetime) → RECURRING_FEDERAL

    Use for any claim of federal contract / DoD relationship / NASA
    work / DOE work / VA deployments / SBIR-funded program. The UEI-
    anchored approach removes the substring-noise + name-variant gaps
    of bare query_recipient_contracts and is the recommended primary
    M-source for federal counterparty claims.
    """
    if isinstance(name_variants, str):
        name_variants = [name_variants]

    # Resolve UEIs across all variants, dedup
    seen: dict[str, dict] = {}
    for nm in name_variants:
        for u in resolve_recipient_ueis(nm, limit=10):
            if u["uei"] not in seen:
                seen[u["uei"]] = u
        time.sleep(0.1)

    n_contracts = 0
    contracts_amount = 0.0
    n_grants = 0
    grants_amount = 0.0
    agencies: dict[str, int] = {}
    top_awards: list[dict] = []

    for uei in seen.keys():
        c = query_by_uei(uei, start_date=start_date, end_date=end_date,
                         contracts=True)
        n_contracts += c.get("n_awards", 0)
        contracts_amount += c.get("total_amount", 0)
        for ag, count in (c.get("agencies") or {}).items():
            agencies[ag] = agencies.get(ag, 0) + count
        top_awards.extend(c.get("top_awards", [])[:3])
        if include_grants:
            g = query_by_uei(uei, start_date=start_date, end_date=end_date,
                             contracts=False)
            n_grants += g.get("n_awards", 0)
            grants_amount += g.get("total_amount", 0)
        time.sleep(0.1)

    top_awards.sort(key=lambda r: float(r.get("Award Amount") or 0),
                    reverse=True)
    top_awards = top_awards[:10]

    lifetime_M = (contracts_amount + grants_amount) / 1e6
    # Signal discrimination is by LIFETIME AWARDS, not UEI existence.
    # A registered UEI with $0 lifetime awards is just as inflation-
    # suspect as no UEI — actually more so, because the company bothered
    # to register but has never won anything.
    # Calibration anchor: ALMU has $1.32M in real awards → SUB_MATERIAL
    # (UNVERIFIABLE). WKHS pre-2021 USPS NGDV claim had 1 UEI but $0
    # awards → must be INFLATION_SUSPECT (SEVERE), matching the eventual
    # 2024 SEC settlement.
    if lifetime_M == 0:
        signal = "INFLATION_SUSPECT"
    elif lifetime_M < 5.0:
        signal = "SUB_MATERIAL_FEDERAL"
    else:
        signal = "RECURRING_FEDERAL"

    return {
        "name_variants": name_variants,
        "n_ueis_resolved": len(seen),
        "ueis": list(seen.values()),
        "n_contracts": n_contracts,
        "contracts_amount_M": contracts_amount / 1e6,
        "n_grants": n_grants,
        "grants_amount_M": grants_amount / 1e6,
        "agencies": agencies,
        "top_awards": top_awards,
        "signal": signal,
    }
