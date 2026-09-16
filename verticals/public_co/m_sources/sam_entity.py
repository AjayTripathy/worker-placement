"""
SAM.gov Entity Management API connector.

SAM.gov is the System for Award Management — the master registry of
every entity (individual, business, government) eligible to receive
federal awards. Required registration to bid on any federal contract.

The Entity Information v3 *public* endpoint returns, per UEI:

  entityRegistration: ueiSAM, cageCode, dodaac, legalBusinessName,
                      dbaName, registrationStatus,
                      registrationExpirationDate, lastUpdateDate,
                      exclusionStatusFlag
  coreData.entityInformation:   URL, fiscalYearEnd, start date
  coreData.physicalAddress:     line1, city, state, zip
  coreData.mailingAddress:      line1, city, state, zip
  coreData.generalInformation:  entityStructure, profitStructure,
                                stateOfIncorporation
  coreData.businessTypes:       For-profit / nonprofit / SBA types
  coreData.financialInformation: creditCardUsage, debtSubjectToOffset
                                (BOOLEAN ONLY — NOT employee count
                                or revenue)
  assertions.goodsAndServices:  primaryNaics + naicsList
  pointsOfContact:              registrant/admin POCs

NOT IN v3 PUBLIC TIER (requires paid extracts or FOUO access):
  - numberOfEmployees
  - annualRevenue
  - SBA size standards detail (only the entity's flagged SBA list)

So the framework's signal from SAM is:
  1. NAICS-vs-claim match (THE strongest scope check)
  2. Physical address vs claimed facility
  3. Registration status / exclusions (for federal-claim validity)
  4. CAGE code (cross-reference with usaspending awards)

A small-cap claiming "industrial drone manufacturer" should have
primary NAICS 336411 in SAM. If they declared 541330 (Engineering
Services) instead, that's a scope contradiction — the company told
the federal government one thing and the equity markets another.

API key: required, free from sam.gov/data-services. Store at
~/.sam_api_key (one line, just the key string).

API endpoint:
  https://api.sam.gov/entity-information/v3/entities
  ?ueiSAM={uei}&api_key={key}
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["mentions_dod_customer", "government_customer_concentration_above_5pct"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "SAM.gov entity registration (UEI/CAGE/exclusions); a claimed federal contractor must exist here.",
}

import time
from pathlib import Path
from typing import Any, Optional

import httpx

KEY_PATH = Path.home() / ".sam_api_key"
BASE = "https://api.sam.gov/entity-information/v3/entities"


def _load_key() -> Optional[str]:
    if not KEY_PATH.exists():
        return None
    return KEY_PATH.read_text().strip() or None


def query_entity_by_uei(uei: str, api_key: Optional[str] = None,
                          cutoff_date: Optional[str] = None) -> dict[str, Any]:
    """Look up a SAM.gov entity record by UEI (preferred).

    Returns:
        {
          "uei":                    uei,
          "legal_business_name":    str,
          "dba_name":               str | None,
          "physical_address":       dict,
          "primary_naics":          str | None,
          "all_naics":              list[str],
          "employee_count":         int | None,
          "annual_revenue":         float | None,
          "registration_status":    'Active' | 'Inactive' | 'Submitted',
          "registration_expires":   ISO date | None,
          "business_types":         list[str],
          "cage_code":              str | None,
          "raw":                    full response dict for debugging,
        }
    Or {"error": ..., "uei": uei} if lookup fails.
    """
    key = api_key or _load_key()
    if not key:
        return {"error": "no SAM.gov api_key — register at sam.gov/data-services "
                          "and place key at ~/.sam_api_key",
                "uei": uei}
    # Backoff on 429s — SAM has a low req/min limit on the free tier.
    data = None
    last_status = None
    for attempt in range(4):
        try:
            with httpx.Client(timeout=30) as c:
                r = c.get(BASE, params={"ueiSAM": uei, "api_key": key,
                                        "samRegistered": "Yes"})
                last_status = r.status_code
                if r.status_code == 200:
                    data = r.json()
                    break
                if r.status_code == 429:
                    time.sleep(2 ** attempt)  # 1, 2, 4, 8s
                    continue
                return {"error": f"sam_status_{r.status_code}",
                        "detail": r.text[:200], "uei": uei}
        except httpx.HTTPError as e:
            return {"error": f"sam_http: {e}", "uei": uei}
    if data is None:
        return {"error": f"sam_status_{last_status}_after_retries", "uei": uei}

    entities = data.get("entityData") or []
    if not entities:
        return {"error": "no_entity_found", "uei": uei}
    e = entities[0]
    reg     = e.get("entityRegistration") or {}
    core    = e.get("coreData") or {}
    address = (core.get("physicalAddress") or {})
    mailing = (core.get("mailingAddress") or {})

    # NAICS lives at assertions.goodsAndServices, NOT coreData
    gands = (e.get("assertions") or {}).get("goodsAndServices") or {}
    primary_naics = gands.get("primaryNaics")
    naics_list = gands.get("naicsList") or []
    all_naics = [(n.get("naicsCode"), n.get("naicsDescription"))
                  for n in naics_list if n.get("naicsCode")]

    business_types = [b.get("businessTypeDesc") for b in
                      (core.get("businessTypes") or {}).get("businessTypeList", [])
                      if b.get("businessTypeDesc")]
    sba_types = [s.get("sbaBusinessTypeDesc") for s in
                  (core.get("businessTypes") or {}).get("sbaBusinessTypeList", [])
                  if s.get("sbaBusinessTypeDesc")]

    # Hindsight-blinding warning. SAM API returns CURRENT registration
    # state only — there is no historical snapshot available. For
    # backtests with cutoffs more than ~6 months in the past, treat the
    # returned data as "current state" not "state at cutoff." A company
    # registered today might not have been registered at the cutoff
    # (and vice versa).
    hindsight_warning = None
    if cutoff_date:
        try:
            from datetime import date
            cd = date.fromisoformat(str(cutoff_date)[:10])
            days_stale = (date.today() - cd).days
            if days_stale > 180:
                hindsight_warning = (
                    f"SAM.gov returns CURRENT registration only; cutoff "
                    f"{cutoff_date} is {days_stale} days in the past. "
                    f"Registration / NAICS / address / status reflect "
                    f"today, NOT the cutoff. Use registration_date and "
                    f"last_update_date fields to bound retroactive validity."
                )
        except (ValueError, TypeError):
            pass

    return {
        "uei":                  uei,
        "_hindsight_warning":   hindsight_warning,
        "legal_business_name":  reg.get("legalBusinessName"),
        "dba_name":             reg.get("dbaName"),
        "physical_address":     {
            "address_line_1": address.get("addressLine1"),
            "city":           address.get("city"),
            "state":          address.get("stateOrProvinceCode"),
            "zip":            address.get("zipCode"),
            "country":        address.get("countryCode"),
        },
        "mailing_address":      {
            "city":           mailing.get("city"),
            "state":          mailing.get("stateOrProvinceCode"),
            "country":        mailing.get("countryCode"),
        },
        "primary_naics":        primary_naics,
        "all_naics":            all_naics,
        "registration_status":  reg.get("registrationStatus"),
        "registration_expires": reg.get("registrationExpirationDate"),
        "last_update_date":     reg.get("lastUpdateDate"),
        "registration_date":    reg.get("registrationDate"),
        "exclusion_flag":       reg.get("exclusionStatusFlag"),
        "business_types":       business_types,
        "sba_types":            sba_types,
        "cage_code":            reg.get("cageCode"),
        "dodaac":               reg.get("dodaac"),
        "entity_url":           (core.get("entityInformation") or {}).get("entityURL"),
        "state_of_incorporation": (core.get("generalInformation") or {}).get("stateOfIncorporationCode"),
        "raw":                  e,
    }


def query_entity_by_name(name: str, api_key: Optional[str] = None,
                          limit: int = 10) -> dict[str, Any]:
    """Search SAM.gov by legal business name. Returns multiple matches."""
    key = api_key or _load_key()
    if not key:
        return {"error": "no SAM.gov api_key", "matches": []}
    try:
        with httpx.Client(timeout=30) as c:
            r = c.get(BASE, params={
                "legalBusinessName": name, "api_key": key,
                "samRegistered": "Yes", "registrationStatus": "Active",
            })
            if r.status_code != 200:
                return {"error": f"sam_status_{r.status_code}", "matches": []}
            data = r.json()
    except httpx.HTTPError as e:
        return {"error": str(e), "matches": []}

    entities = (data.get("entityData") or [])[:limit]
    matches = []
    for e in entities:
        reg = e.get("entityRegistration") or {}
        core = e.get("coreData") or {}
        gands = (e.get("assertions") or {}).get("goodsAndServices") or {}
        matches.append({
            "uei":                 reg.get("ueiSAM"),
            "legal_business_name": reg.get("legalBusinessName"),
            "primary_naics":       gands.get("primaryNaics"),
            "physical_state":      (core.get("physicalAddress") or {}).get("stateOrProvinceCode"),
            "physical_city":       (core.get("physicalAddress") or {}).get("city"),
            "cage_code":           reg.get("cageCode"),
            "registration_status": reg.get("registrationStatus"),
        })
    return {"n_matches": len(matches), "matches": matches}
