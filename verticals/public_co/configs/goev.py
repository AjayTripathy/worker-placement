"""Canoo (GOEV) — multi-purpose EV platform / Lifestyle Vehicle. Bankrupt 2025-01.

Cutoff: 2021-06-30 (~6 months post-deSPAC Dec 2020).
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001750153"
TICKER = "goev"
CUTOFF_DATE = "2021-06-30"
PRIORITY_FORMS = {"S-1", "S-4", "424B4", "10-K", "10-Q", "8-K"}


CLAIMS = [
    {"claim_id": "GOEV-001", "claim_text": "Canoo will deliver Lifestyle Vehicle production starting 2022",
     "source_form": "10-K", "filing_date": "2021-03-31", "category": "production_volume",
     "M_sources": ["nhtsa_canoo"]},
    {"claim_id": "GOEV-002", "claim_text": "Canoo is building manufacturing facility in Pryor, Oklahoma (and Bentonville)",
     "source_form": "10-K", "filing_date": "2021-03-31", "category": "physical_facility",
     "M_sources": ["epa_frs_canoo_ok"]},
    {"claim_id": "GOEV-003", "claim_text": "Canoo has external counterparty disclosures consistent with a real auto OEM",
     "source_form": "10-K", "filing_date": "2021-03-31", "category": "external_validation",
     "M_sources": ["edgar_canoo_external"]},
]


M_QUERIES = [
    ("nhtsa_canoo", nhtsa.query_manufacturer, {"name": "Canoo"}),
    ("epa_frs_canoo_ok", epa_frs.query_facilities, {"facility_name": "Canoo", "state_abbr": "OK"}),
    ("edgar_canoo_external", edgar_fts.query_fulltext,
     {"search_term": "Canoo Inc", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_canoo", {})
    types: list = []
    matched = []
    for m in n.get("manufacturers", []):
        nm = (m.get("mfr_name") or "").upper()
        if "CANOO" in nm:
            matched.append(m)
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    is_complete = any(t in types for t in ("truck", "passenger car", "multipurpose passenger vehicle (mpv)"))
    if is_complete:
        sev = Severity.PASS; sup = True; interp = f"NHTSA complete-vehicle ({types})."
    elif "incomplete vehicle" in types:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = f"NHTSA Incomplete Vehicle ({types})."
    elif not matched:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = "NHTSA: no Canoo registration."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"NHTSA atypical: {types}"
    return {"M_check": "NHTSA vPIC", "M_value": f"matches={len(matched)} types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("epa_frs_canoo_ok", {}).get("n_facilities", 0)
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"EPA FRS: {n} Canoo facility/ies in OK."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = "EPA FRS: zero Canoo OK facilities. Pre-construction or paper-claim."
    return {"M_check": "EPA FRS Canoo OK", "M_value": f"{n} facilities",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    n = ev.get("edgar_canoo_external", {}).get("total_hits", 0) or 0
    if n >= 10:
        sev = Severity.PASS; sup = True; interp = f"{n} external EDGAR mentions."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"{n} external mentions — thin."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "Zero external mentions."
    return {"M_check": "EDGAR FTS for 'Canoo Inc' across US filings",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"GOEV-001": _score_001, "GOEV-002": _score_002, "GOEV-003": _score_003}
