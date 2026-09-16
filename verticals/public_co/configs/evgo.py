"""EVgo (EVGO) — EV fast-charging network operator. ALIVE.

Cutoff: 2022-01-31 (~6 months post-deSPAC July 2021). Like CHPT, the right
M-source is NREL stations not NHTSA vehicles.
"""
from __future__ import annotations

from ..m_sources import edgar_fts, nrel_fuel
from ..scoring import Severity


CIK = "0001821159"
TICKER = "evgo"
CUTOFF_DATE = "2022-01-31"
PRIORITY_FORMS = {"S-4", "424B4", "10-K", "10-Q", "8-K"}


CLAIMS = [
    {"claim_id": "EVGO-001", "claim_text": "EVgo operates 800+ fast-charging stations across 30+ US states",
     "source_form": "10-K", "filing_date": "2021-11-15", "category": "fueling_infrastructure",
     "M_sources": ["nrel_evgo"]},
    {"claim_id": "EVGO-002", "claim_text": "EVgo has strategic partnerships with major auto OEMs (GM, Subaru) and ride-share (Uber)",
     "source_form": "10-K", "filing_date": "2021-11-15", "category": "partnership",
     "M_sources": ["edgar_gm_evgo"]},
]


M_QUERIES = [
    ("nrel_evgo", nrel_fuel.query_alt_fuel_stations,
     {"fuel_type": "ELEC", "cutoff_date": CUTOFF_DATE, "name_filter": "EVgo"}),
    ("edgar_gm_evgo", edgar_fts.query_fulltext,
     {"search_term": "EVgo", "cutoff_date": CUTOFF_DATE,
      "cik": "0001467858", "start_date": "2020-01-01"}),  # GM
]


def _score_001(ev, c):
    n = ev.get("nrel_evgo", {}).get("matching_stations_count", 0) or 0
    if n >= 100:
        sev = Severity.PASS; sup = True; interp = f"NREL: {n} EVgo stations pre-cutoff. Real network."
    elif n >= 10:
        sev = Severity.PASS; sup = True; interp = f"{n} stations — operational footprint."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"{n} stations — thin."
    return {"M_check": "NREL EV stations: EVgo-named", "M_value": f"{n} stations",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("edgar_gm_evgo", {}).get("total_hits", 0) or 0
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"GM SEC filings mention EVgo {n} times — partnership corroborated."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = "Zero GM mentions of EVgo."
    return {"M_check": "EDGAR FTS for 'EVgo' in GM (CIK 0001467858) filings",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"EVGO-001": _score_001, "EVGO-002": _score_002}
