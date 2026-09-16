"""Hershey (HSY) — clean consumer-staples parallel for DMND test.

Same cutoff (2011-08-31). Tests EPA FRS, EDGAR counterparty mentions, auditor
stability for an established US food manufacturer.
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs
from ..scoring import Severity


CIK = "0000047111"
TICKER = "hsy"
CUTOFF_DATE = "2011-08-31"
PRIORITY_FORMS = {"10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {
        "claim_id": "HSY-001",
        "claim_text": "Hershey operates real chocolate-manufacturing facilities in Pennsylvania",
        "source_form": "10-K",
        "filing_date": "2011-02-22",
        "category": "physical_facility",
        "M_sources": ["epa_frs_hershey_pa"],
    },
    {
        "claim_id": "HSY-002",
        "claim_text": "Hershey is widely disclosed in counterparty/competitor SEC filings",
        "source_form": "10-K",
        "filing_date": "2011-02-22",
        "category": "customer_pipeline",
        "M_sources": ["edgar_hershey_mentions"],
    },
    {
        "claim_id": "HSY-003",
        "claim_text": "Hershey's auditor (KPMG) provides clean and continuous opinions",
        "source_form": "10-K / DEF 14A",
        "filing_date": "2011-02-22",
        "category": "audit_quality",
        "M_sources": ["edgar_auditor_mentions"],
    },
]


M_QUERIES = [
    ("epa_frs_hershey_pa", epa_frs.query_facilities,
     {"facility_name": "Hershey", "state_abbr": "PA"}),
    ("edgar_hershey_mentions", edgar_fts.query_fulltext,
     {"search_term": "Hershey", "cutoff_date": CUTOFF_DATE,
      "start_date": "2008-01-01", "forms": "10-K,10-Q,8-K"}),
    ("edgar_auditor_mentions", edgar_fts.query_fulltext,
     {"search_term": "KPMG", "cutoff_date": CUTOFF_DATE, "cik": CIK,
      "start_date": "2005-01-01", "forms": "10-K,DEF 14A"}),
]


def _score_001(ev, c):
    frs = ev.get("epa_frs_hershey_pa", {})
    n = frs.get("n_facilities", 0)
    sample = [f.get("facility_name") for f in frs.get("facilities", [])][:5]
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"EPA FRS shows {n} Hershey facilities in PA: {sample}. Real industrial operations. PASS."
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "No FRS facilities — thin coverage."
    return {
        "M_check": "EPA FRS Hershey PA facilities",
        "M_value": f"{n} facilities: {sample}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


def _score_002(ev, c):
    fts = ev.get("edgar_hershey_mentions", {})
    n = fts.get("total_hits", 0)
    if n >= 100:
        sev = Severity.PASS
        sup = True
        interp = f"{n} EDGAR mentions — extensive counterparty footprint."
    elif n >= 10:
        sev = Severity.PASS
        sup = True
        interp = f"{n} mentions — adequate counterparty footprint."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"{n} mentions — thinner than expected."
    return {
        "M_check": "EDGAR FTS for 'Hershey' in US public-company filings",
        "M_value": f"{n} mentions in 10-K/Q/8-K pre-cutoff",
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
        interp = f"{n} mentions of KPMG — long-tenured auditor."
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = f"{n} mentions — thin audit disclosure."
    return {
        "M_check": "EDGAR FTS for KPMG in HSY filings",
        "M_value": f"{n} mentions in 10-K/DEF 14A pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


SCORERS = {
    "HSY-001": _score_001,
    "HSY-002": _score_002,
    "HSY-003": _score_003,
}
