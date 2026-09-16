"""Arrival (ARVL) — UK-HQ EV vans / microfactory model. Bankrupt 2024-02.

UPS announced 10,000 EV van order. Cutoff: 2021-09-30 (~6 months post-deSPAC March 2021).
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001835059"
TICKER = "arvl"
CUTOFF_DATE = "2021-09-30"
PRIORITY_FORMS = {"S-1", "S-4", "F-1", "F-4", "20-F", "10-K", "10-Q", "8-K", "6-K"}


CLAIMS = [
    {"claim_id": "ARVL-001", "claim_text": "UPS placed an order for up to 10,000 Arrival electric delivery vans",
     "source_form": "F-4 / 20-F", "filing_date": "2021-03-31", "category": "customer_pipeline",
     "M_sources": ["edgar_ups_arrival"]},
    {"claim_id": "ARVL-002", "claim_text": "Arrival operates microfactory in Charlotte, NC for production",
     "source_form": "20-F", "filing_date": "2021-03-31", "category": "physical_facility",
     "M_sources": ["epa_frs_arrival_nc"]},
    {"claim_id": "ARVL-003", "claim_text": "Arrival has external counterparty disclosures consistent with a real auto OEM",
     "source_form": "20-F", "filing_date": "2021-03-31", "category": "external_validation",
     "M_sources": ["edgar_arrival_external"]},
]


M_QUERIES = [
    ("edgar_ups_arrival", edgar_fts.query_fulltext,
     {"search_term": "Arrival", "cutoff_date": CUTOFF_DATE,
      "cik": "0001090727", "start_date": "2020-01-01"}),  # UPS CIK
    ("epa_frs_arrival_nc", epa_frs.query_facilities, {"facility_name": "Arrival", "state_abbr": "NC"}),
    ("edgar_arrival_external", edgar_fts.query_fulltext,
     {"search_term": "Arrival", "cutoff_date": CUTOFF_DATE,
      "start_date": "2020-01-01", "forms": "10-K,10-Q,8-K"}),
]


def _score_001(ev, c):
    n = ev.get("edgar_ups_arrival", {}).get("total_hits", 0) or 0
    if n >= 3:
        sev = Severity.PASS; sup = True; interp = f"UPS SEC filings mention 'Arrival' {n} times — order disclosed by counterparty."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = f"Only {n} UPS mention(s). Note: 'Arrival' is a common word in SEC filings; some matches may be false positives."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = "Zero UPS mentions of 'Arrival' pre-cutoff. 10,000-vehicle order should appear in capital commitments."
    return {"M_check": "EDGAR FTS for 'Arrival' in UPS (CIK 0001090727) filings",
            "M_value": f"{n} mentions pre-cutoff (note: 'Arrival' is a common word — some FPs likely)",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("epa_frs_arrival_nc", {}).get("n_facilities", 0)
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"EPA FRS: {n} Arrival facility/ies in NC."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = "EPA FRS: zero Arrival NC facilities — pre-construction or thin."
    return {"M_check": "EPA FRS Arrival NC", "M_value": f"{n} facilities",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    n = ev.get("edgar_arrival_external", {}).get("total_hits", 0) or 0
    sev = Severity.PASS if n >= 10 else (Severity.MODERATE_UNDERDELIVERY if n >= 1 else Severity.SEVERE_UNDERDELIVERY)
    sup = True if n >= 10 else False
    interp = f"{n} external EDGAR mentions of 'Arrival' (common-word inflation likely)."
    return {"M_check": "EDGAR FTS for 'Arrival'", "M_value": f"{n} mentions",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


SCORERS = {"ARVL-001": _score_001, "ARVL-002": _score_002, "ARVL-003": _score_003}
