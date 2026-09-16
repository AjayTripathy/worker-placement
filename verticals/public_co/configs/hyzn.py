"""Hyzon Motors (HYZN) — hydrogen fuel-cell trucks, alleged fraud.

Blue Orca Capital report 2021-09-28 alleged: claimed 87 truck deliveries to
Hong Kong / Total / Hyundai customers were largely paper deliveries to
related-party shell entities; revenue recognition fraud. SEC charged Hyzon
2024; bankruptcy 2024-12.

Cutoff: 2022-01-15. (Already at +6mo post-deSPAC; pre-Wolfpack-style cleanup
period.)
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs, nhtsa
from ..scoring import Severity


CIK = "0001716583"
TICKER = "hyzn"
CUTOFF_DATE = "2022-01-15"
PRIORITY_FORMS = {"S-1", "S-4", "S-4/A", "424B4", "10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {
        "claim_id": "HYZN-001",
        "claim_text": "Hyzon delivered 87 hydrogen fuel-cell trucks to customers in 2021 (revenue-generating)",
        "source_form": "10-K / 8-K", "filing_date": "2021-08-15",
        "category": "production_volume",
        "M_sources": ["nhtsa_hyzon"],
    },
    {
        "claim_id": "HYZN-002",
        "claim_text": "Hyzon has named major customers: Total Energies, Hyundai Glovis, ANA Group",
        "source_form": "10-K / S-4", "filing_date": "2021-08-15",
        "category": "customer_pipeline",
        "M_sources": ["edgar_total_hyzon"],
    },
    {
        "claim_id": "HYZN-003",
        "claim_text": "Hyzon operates manufacturing facilities in Rochester, NY and Bolingbrook, IL",
        "source_form": "10-K", "filing_date": "2021-08-15",
        "category": "physical_facility",
        "M_sources": ["epa_frs_hyzon_ny", "epa_frs_hyzon_il"],
    },
]


M_QUERIES = [
    ("nhtsa_hyzon", nhtsa.query_manufacturer, {"name": "Hyzon"}),
    ("edgar_total_hyzon", edgar_fts.query_fulltext,
     {"search_term": "Hyzon", "cutoff_date": CUTOFF_DATE,
      "cik": "0000879764", "start_date": "2020-01-01"}),  # TotalEnergies CIK
    ("epa_frs_hyzon_ny", epa_frs.query_facilities,
     {"facility_name": "Hyzon", "state_abbr": "NY"}),
    ("epa_frs_hyzon_il", epa_frs.query_facilities,
     {"facility_name": "Hyzon", "state_abbr": "IL"}),
]


def _score_001(ev, c):
    n = ev.get("nhtsa_hyzon", {})
    n_match = sum(1 for m in n.get("manufacturers", []) if "HYZON" in (m.get("mfr_name") or "").upper())
    types: list = []
    for m in n.get("manufacturers", []):
        if "HYZON" in (m.get("mfr_name") or "").upper():
            types.extend((t or "").lower() for t in m.get("vehicle_types", []))
    if n_match >= 1 and any(t in types for t in ("truck", "incomplete vehicle")):
        sev = Severity.PASS
        sup = True
        interp = f"NHTSA registered as manufacturer with types {types}. Existence of registration corroborated."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = f"NHTSA registration thin or missing: matches={n_match}, types={types}. For 87 truck deliveries, expected complete-vehicle registration."
    return {"M_check": "NHTSA vPIC manufacturer registration", "M_value": f"matches={n_match}, types={types}",
            "M_supports_claim": sup, "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    e = ev.get("edgar_total_hyzon", {})
    n = e.get("total_hits", 0) or 0
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"TotalEnergies SEC filings mention Hyzon {n} times pre-cutoff. Real customer-side disclosure."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = "Zero mentions of Hyzon in TotalEnergies SEC filings pre-cutoff. Same counterparty test that flagged Nikola/AB InBev. Hydrogen-truck supply commitment of this scale would normally appear in customer's 10-K."
    return {"M_check": "EDGAR FTS for 'Hyzon' in TotalEnergies (CIK 0000879764) filings",
            "M_value": f"{n} mentions pre-cutoff", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


def _score_003(ev, c):
    ny = ev.get("epa_frs_hyzon_ny", {}).get("n_facilities", 0)
    il = ev.get("epa_frs_hyzon_il", {}).get("n_facilities", 0)
    total = ny + il
    if total >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"EPA FRS shows {ny} NY + {il} IL Hyzon facilities. Real industrial footprint."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = "Zero EPA FRS facilities in either claimed state. Real hydrogen-truck assembly would be regulated under EPA programs."
    return {"M_check": "EPA FRS Hyzon facilities in NY and IL",
            "M_value": f"NY: {ny}, IL: {il}", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"HYZN-001": _score_001, "HYZN-002": _score_002, "HYZN-003": _score_003}
