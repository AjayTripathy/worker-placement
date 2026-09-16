"""Fisker (FSR) — Ocean SUV. Bankrupt 2024-06.

Cutoff: 2021-04-30 (~6 months post-deSPAC Oct 2020).
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001720990"
TICKER = "fsr"
CUTOFF_DATE = "2021-04-30"
PRIORITY_FORMS = {"S-1", "S-4", "424B4", "10-K", "10-Q", "8-K"}


CLAIMS = [
    {"claim_id": "FSR-001", "claim_text": "Fisker Ocean is a production vehicle scheduled for delivery in 2022",
     "source_form": "10-K", "filing_date": "2021-03-30", "category": "production_volume",
     "M_sources": ["nhtsa_fisker"]},
    {"claim_id": "FSR-002", "claim_text": "Fisker has a manufacturing partnership with Magna International (MGA) for the Ocean",
     "source_form": "10-K", "filing_date": "2021-03-30", "category": "partnership",
     "M_sources": ["edgar_magna_fisker"]},
    {"claim_id": "FSR-003", "claim_text": "Fisker has counterparty disclosure consistent with a real auto OEM",
     "source_form": "10-K", "filing_date": "2021-03-30", "category": "external_validation",
     "M_sources": ["edgar_fisker_external"]},
]


M_QUERIES = [
    ("nhtsa_fisker", nhtsa.query_manufacturer, {"name": "Fisker"}),
    ("edgar_magna_fisker", edgar_fts.query_fulltext,
     {"search_term": "Fisker", "cutoff_date": CUTOFF_DATE,
      "cik": "0001072627", "start_date": "2019-01-01"}),  # Magna CIK
    ("edgar_fisker_external", edgar_fts.query_fulltext,
     {"search_term": "Fisker Inc", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_fisker", {})
    types: list = []
    matched = []
    for m in n.get("manufacturers", []):
        nm = (m.get("mfr_name") or "").upper()
        if "FISKER" in nm:
            matched.append(m)
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    is_complete = any(t in types for t in ("truck", "passenger car", "multipurpose passenger vehicle (mpv)"))
    if is_complete:
        sev = Severity.PASS; sup = True; interp = f"NHTSA: complete-vehicle manufacturer ({types})."
    elif "incomplete vehicle" in types:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = f"NHTSA: Incomplete Vehicle ({types})."
    elif not matched:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = "NHTSA: no Fisker manufacturer entry — production claim implies registration."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"NHTSA atypical: {types}"
    return {"M_check": "NHTSA vPIC", "M_value": f"matches={len(matched)} types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("edgar_magna_fisker", {}).get("total_hits", 0) or 0
    if n >= 3:
        sev = Severity.PASS; sup = True; interp = f"Magna's SEC filings mention Fisker {n} times — partnership disclosed by counterparty."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = f"Only {n} Magna mention(s) — thinner than expected for a strategic manufacturing partnership."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = "Zero Magna SEC mentions of Fisker. Same counterparty test that flagged Nikola/AB InBev."
    return {"M_check": "EDGAR FTS for 'Fisker' in Magna (CIK 0001072627) filings",
            "M_value": f"{n} mentions pre-cutoff", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    n = ev.get("edgar_fisker_external", {}).get("total_hits", 0) or 0
    if n >= 10:
        sev = Severity.PASS; sup = True; interp = f"{n} external EDGAR mentions — real footprint."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"{n} external mentions — thin."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "Zero external mentions."
    return {"M_check": "EDGAR FTS for 'Fisker Inc' across US filings",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"FSR-001": _score_001, "FSR-002": _score_002, "FSR-003": _score_003}
