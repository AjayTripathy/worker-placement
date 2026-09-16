"""Faraday Future (FFIE) — luxury EV; FF 91 production. Penny stock.

Cutoff: 2022-01-30 (~6 months post-deSPAC July 2021). Long history (since 2014)
without delivering meaningful production volume.
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001805521"
TICKER = "ffie"
CUTOFF_DATE = "2022-01-30"
PRIORITY_FORMS = {"S-1", "S-4", "424B4", "10-K", "10-Q", "8-K"}


CLAIMS = [
    {"claim_id": "FFIE-001", "claim_text": "Faraday Future will begin production of FF 91 in 2022",
     "source_form": "10-K", "filing_date": "2021-11-15", "category": "production_volume",
     "M_sources": ["nhtsa_faraday"]},
    {"claim_id": "FFIE-002", "claim_text": "FF operates the Hanford, CA manufacturing facility for FF 91 production",
     "source_form": "10-K", "filing_date": "2021-11-15", "category": "physical_facility",
     "M_sources": ["epa_frs_faraday_ca"]},
    {"claim_id": "FFIE-003", "claim_text": "FF has external counterparty disclosures consistent with a real auto OEM",
     "source_form": "10-K", "filing_date": "2021-11-15", "category": "external_validation",
     "M_sources": ["edgar_faraday_external"]},
]


M_QUERIES = [
    ("nhtsa_faraday", nhtsa.query_manufacturer, {"name": "Faraday"}),
    ("epa_frs_faraday_ca", epa_frs.query_facilities, {"facility_name": "Faraday Future", "state_abbr": "CA"}),
    ("edgar_faraday_external", edgar_fts.query_fulltext,
     {"search_term": "Faraday Future", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_faraday", {})
    types: list = []
    matched = []
    for m in n.get("manufacturers", []):
        nm = (m.get("mfr_name") or "").upper()
        if "FARADAY FUTURE" in nm or "FF INC" in nm:
            matched.append(m)
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    if any(t in types for t in ("passenger car", "multipurpose passenger vehicle (mpv)")):
        sev = Severity.PASS; sup = True; interp = f"NHTSA registered ({types})."
    elif "incomplete vehicle" in types:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = f"NHTSA Incomplete Vehicle ({types})."
    elif not matched:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "NHTSA: no Faraday Future registration."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"NHTSA atypical ({types})."
    return {"M_check": "NHTSA vPIC", "M_value": f"matches={len(matched)} types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("epa_frs_faraday_ca", {}).get("n_facilities", 0)
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"EPA FRS: {n} Faraday Future CA facility/ies."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = "EPA FRS: zero Faraday Future CA facilities. For pre-production claims at Hanford, expected industrial registration."
    return {"M_check": "EPA FRS Faraday Future CA", "M_value": f"{n} facilities",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    n = ev.get("edgar_faraday_external", {}).get("total_hits", 0) or 0
    if n >= 10:
        sev = Severity.PASS; sup = True; interp = f"{n} external EDGAR mentions."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"{n} external mentions — thin."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "Zero external mentions."
    return {"M_check": "EDGAR FTS for 'Faraday Future'", "M_value": f"{n} mentions",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


SCORERS = {"FFIE-001": _score_001, "FFIE-002": _score_002, "FFIE-003": _score_003}
