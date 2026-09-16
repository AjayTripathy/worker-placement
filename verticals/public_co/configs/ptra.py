"""Proterra (PTRA) — battery + electric buses + drivetrains. Bankrupt 2023-08.

Cutoff: 2021-12-31 (~6 months post-deSPAC June 2021).
Real customers: Daimler Truck (drivetrain supply); various transit agencies.
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001820630"
TICKER = "ptra"
CUTOFF_DATE = "2021-12-31"
PRIORITY_FORMS = {"S-4", "424B4", "10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {"claim_id": "PTRA-001", "claim_text": "Proterra produces complete electric transit buses (Catalyst, ZX5)",
     "source_form": "10-K", "filing_date": "2021-08-13", "category": "production_volume",
     "M_sources": ["nhtsa_proterra"]},
    {"claim_id": "PTRA-002", "claim_text": "Proterra has battery + powertrain supply contracts with Daimler Truck",
     "source_form": "10-K", "filing_date": "2021-08-13", "category": "customer_pipeline",
     "M_sources": ["edgar_daimler_proterra"]},
    {"claim_id": "PTRA-003", "claim_text": "Proterra operates manufacturing facilities in Greenville, SC and Burlingame, CA",
     "source_form": "10-K", "filing_date": "2021-08-13", "category": "physical_facility",
     "M_sources": ["epa_frs_proterra_sc", "epa_frs_proterra_ca"]},
]


M_QUERIES = [
    ("nhtsa_proterra", nhtsa.query_manufacturer, {"name": "Proterra"}),
    ("edgar_daimler_proterra", edgar_fts.query_fulltext,
     {"search_term": "Proterra", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "20-F,6-K,10-K"}),
    ("epa_frs_proterra_sc", epa_frs.query_facilities, {"facility_name": "Proterra", "state_abbr": "SC"}),
    ("epa_frs_proterra_ca", epa_frs.query_facilities, {"facility_name": "Proterra", "state_abbr": "CA"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_proterra", {})
    types: list = []
    matched = []
    for m in n.get("manufacturers", []):
        if "PROTERRA" in (m.get("mfr_name") or "").upper():
            matched.append(m)
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    if "bus" in types:
        sev = Severity.PASS; sup = True; interp = f"NHTSA: registered as Bus ({types})."
    elif "incomplete vehicle" in types:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = f"NHTSA: Incomplete Vehicle ({types}) — drivetrain manufacturer rather than complete bus OEM. Consistent with their actual product mix."
    elif not matched:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "NHTSA: no Proterra registration."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"NHTSA atypical ({types})."
    return {"M_check": "NHTSA vPIC", "M_value": f"matches={len(matched)} types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("edgar_daimler_proterra", {}).get("total_hits", 0) or 0
    if n >= 5:
        sev = Severity.PASS; sup = True; interp = f"{n} mentions in 20-F/6-K/10-K (foreign private issuers + Daimler-equivalent disclosures)."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"Only {n} foreign-issuer mentions of Proterra."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "No counterparty mentions."
    return {"M_check": "EDGAR FTS for 'Proterra' in 20-F/6-K/10-K (Daimler etc.)",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    sc = ev.get("epa_frs_proterra_sc", {}).get("n_facilities", 0)
    ca = ev.get("epa_frs_proterra_ca", {}).get("n_facilities", 0)
    if (sc + ca) >= 1:
        sev = Severity.PASS; sup = True; interp = f"EPA FRS: {sc} SC + {ca} CA Proterra facilities."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False; interp = "EPA FRS: zero facilities in either state."
    return {"M_check": "EPA FRS Proterra SC + CA", "M_value": f"SC: {sc}, CA: {ca}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


SCORERS = {"PTRA-001": _score_001, "PTRA-002": _score_002, "PTRA-003": _score_003}
