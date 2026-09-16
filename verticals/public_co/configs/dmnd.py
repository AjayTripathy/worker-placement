"""Diamond Foods (DMND) — accounting fraud (walnut payments improperly deferred).

DMND treated walnut grower "momentum/continuity" payments as future-period costs
to pump current-period earnings. WSJ raised questions Sep 2011; audit committee
investigated, fired CEO + CFO Feb 2012; restatement Nov 2012; SEC charged the
company in Jan 2014. Pringles acquisition collapsed; Snyder's-Lance later acquired.

Cutoff: 2011-08-31 (before WSJ inquiry).

The framework's M-sources (EPA FRS, EDGAR FTS, supplier disclosures) won't
detect the specific accounting-fraud pattern (which surfaces only via
restatement filings or auditor change). What they CAN detect: Diamond's real
production footprint, supplier counterparty disclosures, etc. Useful test of
how the framework calibrates on "real operations + cooked books."
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs
from ..scoring import Severity


CIK = "0001320947"
TICKER = "dmnd"
CUTOFF_DATE = "2011-08-31"
PRIORITY_FORMS = {"10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {
        "claim_id": "DMND-001",
        "claim_text": "Diamond Foods operates real walnut processing facilities in California",
        "source_form": "10-K",
        "filing_date": "2010-10-12",
        "category": "physical_facility",
        "M_sources": ["epa_frs_diamond_ca"],
    },
    {
        "claim_id": "DMND-002",
        "claim_text": "Diamond Foods has supplier/customer relationships disclosed in counterparty US filings",
        "source_form": "10-K",
        "filing_date": "2010-10-12",
        "category": "customer_pipeline",
        "M_sources": ["edgar_diamond_mentions"],
    },
    {
        "claim_id": "DMND-003",
        "claim_text": "Diamond Foods' auditor (Deloitte & Touche) provides clean opinions and audit committee oversight",
        "source_form": "10-K / DEF 14A",
        "filing_date": "2010-12-22",
        "category": "audit_quality",
        "M_sources": ["edgar_auditor_mentions"],
    },
]


M_QUERIES = [
    ("epa_frs_diamond_ca", epa_frs.query_facilities,
     {"facility_name": "Diamond Foods", "state_abbr": "CA"}),
    ("edgar_diamond_mentions", edgar_fts.query_fulltext,
     {"search_term": "Diamond Foods", "cutoff_date": CUTOFF_DATE,
      "start_date": "2008-01-01", "forms": "10-K,10-Q,8-K"}),
    ("edgar_auditor_mentions", edgar_fts.query_fulltext,
     {"search_term": "Deloitte", "cutoff_date": CUTOFF_DATE, "cik": CIK,
      "start_date": "2008-01-01", "forms": "10-K,DEF 14A"}),
]


def _score_001(ev, c):
    frs = ev.get("epa_frs_diamond_ca", {})
    n = frs.get("n_facilities", 0)
    sample = [f.get("facility_name") for f in frs.get("facilities", [])][:5]
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = (
            f"EPA FRS shows {n} Diamond Foods facilities in CA: {sample}. The "
            "operational facilities are real — the fraud was in HOW walnut payments "
            "were accounted for, not WHETHER walnuts were processed. Framework "
            "correctly returns PASS on the physical-existence claim. The accounting "
            "fraud (deferred-cost capitalization) is invisible to FRS by design."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = "Zero EPA FRS facilities — would suggest no real operations."
    return {
        "M_check": "EPA Facility Registry Service: Diamond Foods CA facilities",
        "M_value": f"{n} facilities in CA: {sample}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?facility_name=Diamond+Foods&state_abbr=CA",
    }


def _score_002(ev, c):
    fts = ev.get("edgar_diamond_mentions", {})
    n = fts.get("total_hits", 0)
    if n >= 10:
        sev = Severity.PASS
        sup = True
        interp = f"{n} EDGAR mentions of Diamond Foods — real counterparty footprint."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"{n} mentions — thinner than expected."
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = "No counterparty mentions."
    return {
        "M_check": "EDGAR FTS for 'Diamond Foods' across US public companies",
        "M_value": f"{n} mentions",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


def _score_003(ev, c):
    aud = ev.get("edgar_auditor_mentions", {})
    n = aud.get("total_hits", 0)
    if n >= 5:
        sev = Severity.PASS
        sup = True
        interp = (
            f"{n} mentions of Deloitte across DMND own filings — long-tenured auditor "
            "documented. Auditor change (the post-fraud signal) didn't happen "
            "pre-cutoff. Framework returns PASS — limitation: accounting-fraud "
            "patterns surface only after restatement/auditor change."
        )
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = f"{n} mentions — sparse audit-committee disclosure."
    return {
        "M_check": "EDGAR FTS for Deloitte mentions in DMND filings (auditor stability)",
        "M_value": f"{n} mentions in 10-K/DEF 14A pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


SCORERS = {
    "DMND-001": _score_001,
    "DMND-002": _score_002,
    "DMND-003": _score_003,
}
