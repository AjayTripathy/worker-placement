"""QuantumScape (QS) — solid-state lithium-metal battery R&D. ALIVE.

Scorpion Capital report April 2021 alleged the cell technology doesn't work
at commercial scale. QS pushed back; framework can't verify physics, but can
verify: patent portfolio depth and the Volkswagen partnership.

Cutoff: 2021-05-31 (~6 months post-deSPAC Nov 2020, post-Scorpion is fine —
the question is what M-sources said pre-deSPAC vs the claim).
"""
from __future__ import annotations

from ..m_sources import edgar_fts, google_patents
from ..scoring import Severity


CIK = "0001811414"
TICKER = "qs"
CUTOFF_DATE = "2021-05-31"
PRIORITY_FORMS = {"S-4", "424B4", "10-K", "10-Q", "8-K"}

QS_PATENT_CATS = {
    "battery": ["battery", "cell"],
    "solid_state": ["solid-state", "solid state", "lithium metal", "anode"],
    "manufacturing": ["manufacturing", "fabrication"],
}


CLAIMS = [
    {"claim_id": "QS-001", "claim_text": "QuantumScape has substantial patent portfolio in solid-state lithium-metal batteries",
     "source_form": "10-K", "filing_date": "2021-03-30", "category": "technology",
     "M_sources": ["uspto_qs"]},
    {"claim_id": "QS-002", "claim_text": "QuantumScape has a strategic JV with Volkswagen for production cell development",
     "source_form": "10-K", "filing_date": "2021-03-30", "category": "partnership",
     "M_sources": ["edgar_vw_qs"]},
]


M_QUERIES = [
    ("uspto_qs", google_patents.query_assignee,
     {"assignee_name": "QuantumScape", "cutoff_date": CUTOFF_DATE,
      "categorize": QS_PATENT_CATS}),
    ("edgar_vw_qs", edgar_fts.query_fulltext,
     {"search_term": "QuantumScape", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "20-F,6-K,10-K,8-K"}),
]


def _score_001(ev, c):
    p = ev.get("uspto_qs", {})
    n_total = p.get("total_granted_patents_pre_cutoff", 0) or 0
    cats = p.get("category_counts", {}) or {}
    n_solid = cats.get("solid_state", 0)
    n_battery = cats.get("battery", 0)
    if n_total >= 20 and (n_solid + n_battery) >= 5:
        sev = Severity.PASS; sup = True
        interp = f"USPTO: {n_total} pre-cutoff patents; solid-state/battery: {n_solid + n_battery}. Strong portfolio in claimed area."
    elif n_total >= 5:
        sev = Severity.PASS; sup = True; interp = f"{n_total} patents — adequate."
    elif "error" in p:
        sev = Severity.UNVERIFIABLE; sup = None; interp = "Google Patents rate-limited — UNVERIFIABLE."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = f"Only {n_total} patents."
    return {"M_check": "USPTO Google Patents for QuantumScape, solid-state category",
            "M_value": f"total={n_total}, cats={cats}", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


def _score_002(ev, c):
    n = ev.get("edgar_vw_qs", {}).get("total_hits", 0) or 0
    if n >= 5:
        sev = Severity.PASS; sup = True; interp = f"{n} mentions in 20-F/6-K/10-K (foreign-issuer + US-side)."
    elif n >= 1:
        sev = Severity.PASS; sup = True; interp = f"{n} mentions — partnership disclosed."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY; sup = False; interp = "Zero mentions."
    return {"M_check": "EDGAR FTS for 'QuantumScape' across 20-F/6-K/10-K",
            "M_value": f"{n} mentions", "M_supports_claim": sup,
            "interpretation": interp, "severity": sev}


SCORERS = {"QS-001": _score_001, "QS-002": _score_002}
