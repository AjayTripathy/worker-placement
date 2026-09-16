"""ChargePoint Holdings (CHPT) — EV charging network operator. ALIVE.

ChargePoint is NOT a vehicle OEM — it operates DC fast chargers and a charging
software network. The right M-source is NREL alt-fuel stations (the same
registry we used for Rivian Adventure Network), not NHTSA vehicle types.

This is exactly the case where the generic screen mis-applied NHTSA. With
LLM-driven M-source selection, the right test gets picked.

Cutoff: 2021-08-30 (~6 months post-deSPAC Feb 2021).
"""
from __future__ import annotations

from ..m_sources import edgar_fts, nrel_fuel
from ..scoring import Severity


CIK = "0001777393"
TICKER = "chpt"
CUTOFF_DATE = "2021-08-30"
PRIORITY_FORMS = {"S-4", "424B4", "10-K", "10-Q", "8-K"}


CLAIMS = [
    {"claim_id": "CHPT-001", "claim_text": "ChargePoint operates a network of 100,000+ EV charging ports",
     "source_form": "10-K", "filing_date": "2021-04-30", "category": "fueling_infrastructure",
     "M_sources": ["nrel_chargepoint"]},
    {"claim_id": "CHPT-002", "claim_text": "ChargePoint is widely disclosed in SEC filings as a charging-station operator",
     "source_form": "10-K", "filing_date": "2021-04-30", "category": "external_validation",
     "M_sources": ["edgar_chargepoint_external"]},
]


M_QUERIES = [
    ("nrel_chargepoint", nrel_fuel.query_alt_fuel_stations,
     {"fuel_type": "ELEC", "cutoff_date": CUTOFF_DATE, "name_filter": "ChargePoint"}),
    ("edgar_chargepoint_external", edgar_fts.query_fulltext,
     {"search_term": "ChargePoint", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"}),
]


def _score_001(ev, c):
    n = ev.get("nrel_chargepoint", {}).get("matching_stations_count", 0) or 0
    if n >= 100:
        sev = Severity.PASS; sup = True
        interp = f"NREL DOE alt-fuel registry shows {n} ChargePoint-named stations pre-cutoff. Real network presence in authoritative federal registry."
    elif n >= 10:
        sev = Severity.PASS; sup = True; interp = f"{n} ChargePoint stations in NREL — operational network."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"Only {n} stations — thin."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "Zero ChargePoint stations in NREL."
    return {"M_check": "NREL alt-fuel stations: ChargePoint-named EV stations",
            "M_value": f"{n} stations pre-cutoff", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("edgar_chargepoint_external", {}).get("total_hits", 0) or 0
    if n >= 50:
        sev = Severity.PASS; sup = True; interp = f"{n} external EDGAR mentions of ChargePoint."
    elif n >= 5:
        sev = Severity.PASS; sup = True; interp = f"{n} mentions — adequate footprint."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"{n} external mentions — thin."
    return {"M_check": "EDGAR FTS for 'ChargePoint' across US filings",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"CHPT-001": _score_001, "CHPT-002": _score_002}
