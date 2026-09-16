"""Mullen Automotive (MULN) — alleged EV fraud (Hindenburg 2023-04-07).

Claims: solid-state battery breakthrough (343 mi/hr fast-charge), production
EV vans/trucks, partnerships with various OEMs. Hindenburg called it "an
EV-pretender that bought used parts and slapped its name on them."

Cutoff: 2022-05-15 (~5 months after going public via reverse merger Nov 2021,
pre-Hindenburg by ~10 months).
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001499961"
TICKER = "muln"
CUTOFF_DATE = "2022-05-15"
PRIORITY_FORMS = {"S-1", "S-1/A", "10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {"claim_id": "MULN-001", "claim_text": "Mullen Automotive is a vehicle manufacturer producing the FIVE EV crossover and other production vehicles",
     "source_form": "10-K", "filing_date": "2022-01-13", "category": "production_volume",
     "M_sources": ["nhtsa_mullen"]},
    {"claim_id": "MULN-002", "claim_text": "Mullen operates production facilities in California (Brea HQ + Mullen Advanced Energy Operations)",
     "source_form": "10-K", "filing_date": "2022-01-13", "category": "physical_facility",
     "M_sources": ["epa_frs_mullen_ca"]},
    {"claim_id": "MULN-003", "claim_text": "Mullen has partner / supplier / customer relationships visible to the broader US public-company ecosystem",
     "source_form": "10-K", "filing_date": "2022-01-13", "category": "external_validation",
     "M_sources": ["edgar_mullen_external"]},
]


M_QUERIES = [
    ("nhtsa_mullen", nhtsa.query_manufacturer, {"name": "Mullen"}),
    ("epa_frs_mullen_ca", epa_frs.query_facilities, {"facility_name": "Mullen", "state_abbr": "CA"}),
    ("edgar_mullen_external", edgar_fts.query_fulltext,
     {"search_term": "Mullen Automotive", "cutoff_date": CUTOFF_DATE,
      "start_date": "2020-01-01", "forms": "10-K,10-Q,8-K"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_mullen", {})
    types: list = []
    matched = []
    for m in n.get("manufacturers", []):
        nm = (m.get("mfr_name") or "").upper()
        if "MULLEN" in nm and "AUTO" in nm:
            matched.append(m)
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    is_complete = any(t in types for t in ("truck", "passenger car", "multipurpose passenger vehicle (mpv)"))
    if is_complete:
        sev = Severity.PASS; sup = True
        interp = f"NHTSA: Mullen Auto registered with complete-vehicle types {types}."
    elif "trailer" in types or "incomplete vehicle" in types:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = f"NHTSA shows incomplete/trailer registration ({types}) — not a complete vehicle OEM."
    elif not matched:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = "NHTSA: no Mullen Automotive entry as complete-vehicle manufacturer."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = f"NHTSA: thin/atypical registration ({types})."
    return {"M_check": "NHTSA vPIC", "M_value": f"matched={len(matched)}, types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("epa_frs_mullen_ca", {}).get("n_facilities", 0)
    if n >= 1:
        sev = Severity.PASS; sup = True; interp = f"EPA FRS: {n} Mullen facilities in CA."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = "EPA FRS: zero Mullen facilities in CA. Production claims at this scale should leave a regulated footprint."
    return {"M_check": "EPA FRS Mullen CA", "M_value": f"{n} facilities",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    n = ev.get("edgar_mullen_external", {}).get("total_hits", 0) or 0
    if n >= 5:
        sev = Severity.PASS; sup = True; interp = f"{n} external EDGAR mentions of 'Mullen Automotive'."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False
        interp = f"Only {n} external mentions — thin counterparty footprint for claimed scale."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY; sup = False
        interp = "Zero external mentions in US public-company filings."
    return {"M_check": "EDGAR FTS for 'Mullen Automotive' across US filings",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"MULN-001": _score_001, "MULN-002": _score_002, "MULN-003": _score_003}
