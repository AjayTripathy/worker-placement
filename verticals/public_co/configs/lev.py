"""Lion Electric (LEV) — Canadian electric school buses + trucks. Bankrupt 2024-12.

Cutoff: 2021-11-30 (~6 months post-deSPAC May 2021).
Major customer: Amazon ordered 2,500 trucks.
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001834974"
TICKER = "lev"
CUTOFF_DATE = "2021-11-30"
PRIORITY_FORMS = {"S-4", "F-4", "F-1", "20-F", "10-K", "10-Q", "8-K", "6-K"}


CLAIMS = [
    {"claim_id": "LEV-001", "claim_text": "Lion Electric manufactures complete electric trucks and school buses",
     "source_form": "20-F", "filing_date": "2021-04-30", "category": "production_volume",
     "M_sources": ["nhtsa_lion"]},
    {"claim_id": "LEV-002", "claim_text": "Amazon committed to purchase 2,500 Lion electric trucks",
     "source_form": "20-F", "filing_date": "2021-04-30", "category": "customer_pipeline",
     "M_sources": ["edgar_amzn_lion"]},
    {"claim_id": "LEV-003", "claim_text": "Lion is constructing a battery factory in Joliet/Mirabel area (US/Canada)",
     "source_form": "20-F", "filing_date": "2021-04-30", "category": "physical_facility",
     "M_sources": ["epa_frs_lion_il"]},
]


M_QUERIES = [
    ("nhtsa_lion", nhtsa.query_manufacturer, {"name": "Lion Electric"}),
    ("edgar_amzn_lion", edgar_fts.query_fulltext,
     {"search_term": "Lion Electric", "cutoff_date": CUTOFF_DATE,
      "cik": "0001018724", "start_date": "2020-01-01"}),  # AMZN
    ("epa_frs_lion_il", epa_frs.query_facilities, {"facility_name": "Lion Electric", "state_abbr": "IL"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_lion", {})
    types: list = []
    matched = []
    for m in n.get("manufacturers", []):
        nm = (m.get("mfr_name") or "").upper()
        if "LION" in nm:
            matched.append(m)
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    if any(t in types for t in ("bus", "truck")):
        sev = Severity.PASS; sup = True; interp = f"NHTSA registered with appropriate types ({types})."
    elif "incomplete vehicle" in types:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = f"NHTSA registers Incomplete Vehicle ({types}) — chassis-level, not complete."
    elif not matched:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "NHTSA: no Lion Electric registration."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"NHTSA atypical ({types})."
    return {"M_check": "NHTSA vPIC", "M_value": f"matches={len(matched)} types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("edgar_amzn_lion", {}).get("total_hits", 0) or 0
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"AMZN filings mention 'Lion Electric' {n} times."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = "AMZN filings: zero mentions of Lion Electric pre-cutoff. 2,500-truck order would normally appear."
    return {"M_check": "EDGAR FTS for 'Lion Electric' in AMZN (0001018724) filings",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    n = ev.get("epa_frs_lion_il", {}).get("n_facilities", 0)
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"EPA FRS: {n} Lion facility/ies in IL."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = "EPA FRS: zero Lion IL facilities (Joliet plant) — pre-construction at cutoff."
    return {"M_check": "EPA FRS Lion Electric IL", "M_value": f"{n} facilities",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


SCORERS = {"LEV-001": _score_001, "LEV-002": _score_002, "LEV-003": _score_003}
