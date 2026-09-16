"""EHang Holdings (EH) — alleged drone/eVTOL fraud (Wolfpack Feb 2021).

Wolfpack Research's "EHang: A Stock Promotion Destined to Crash and Burn"
(2021-02-16) alleged: fabricated "Shanghai Kunxiang" customer (74% of revenue
from a sham buyer), inflated AAV deliveries, no real CAAC certification path.

Like Luckin, EHang's fraud is internal to Chinese commercial records — the
discriminating M-sources (China AIC registry, CAAC filings, Shanghai bank-
statement reality checks) aren't in this connector toolkit. EDGAR mainly
exposes ADR-side filings (20-F, 6-K), not the Chinese substrate.

Cutoff: 2021-02-15 (day before Wolfpack).
"""
from __future__ import annotations

from ..m_sources import edgar_fts
from ..scoring import Severity


CIK = "0001759783"
TICKER = "eh"
CUTOFF_DATE = "2021-02-15"
PRIORITY_FORMS = {"F-1", "F-1/A", "424B4", "20-F", "6-K", "8-K"}


CLAIMS = [
    {
        "claim_id": "EH-001",
        "claim_text": "EHang has commercial customer commitments worth meaningful revenue (Shanghai Kunxiang as named major customer)",
        "source_form": "20-F / 6-K",
        "filing_date": "2020-04-30",
        "category": "customer_pipeline",
        "M_sources": ["edgar_kunxiang_mentions"],
    },
    {
        "claim_id": "EH-002",
        "claim_text": "EHang has delivered 200+ EH216 autonomous aerial vehicles to customers",
        "source_form": "20-F",
        "filing_date": "2020-04-30",
        "category": "production_volume",
        "M_sources": ["edgar_eh216_mentions"],
    },
    {
        "claim_id": "EH-003",
        "claim_text": "EHang has the institutional ownership / SC 13G disclosures of a real public company",
        "source_form": "SC 13G",
        "filing_date": "2020-12-31",
        "category": "governance",
        "M_sources": ["edgar_sc13_filings"],
    },
]


M_QUERIES = [
    ("edgar_kunxiang_mentions", edgar_fts.query_fulltext,
     {"search_term": "Shanghai Kunxiang", "cutoff_date": CUTOFF_DATE,
      "start_date": "2018-01-01"}),
    ("edgar_eh216_mentions", edgar_fts.query_fulltext,
     {"search_term": "EH216", "cutoff_date": CUTOFF_DATE,
      "start_date": "2018-01-01"}),
    ("edgar_sc13_filings", edgar_fts.query_fulltext,
     {"search_term": "EHang", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-12-01", "forms": "SC 13G,SC 13G/A,SC 13D,SC 13D/A"}),
]


def _score_001(ev, c):
    fts = ev.get("edgar_kunxiang_mentions", {})
    n = fts.get("total_hits", 0)
    if n == 0:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = (
            "Zero EDGAR mentions of 'Shanghai Kunxiang' — but the framework cannot "
            "distinguish 'fake counterparty' from 'real Chinese counterparty not "
            "filing with SEC' here. Wolfpack's actual signal came from registry "
            "checks at China AIC + visiting the claimed Kunxiang office and finding "
            "an empty room. UNVERIFIABLE via current US-only M-sources; would need "
            "China AIC connector to produce a real signal."
        )
    elif n >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"{n} EDGAR mentions of 'Shanghai Kunxiang' across US public-company filings."
    return {
        "M_check": "EDGAR FTS for 'Shanghai Kunxiang' across US-listed companies (counterparty disclosure)",
        "M_value": f"{n} mentions in US filings pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Shanghai+Kunxiang%22",
    }


def _score_002(ev, c):
    fts = ev.get("edgar_eh216_mentions", {})
    n = fts.get("total_hits", 0)
    return {
        "M_check": "EDGAR FTS for 'EH216' across US-listed companies (operator/customer disclosure)",
        "M_value": f"{n} mentions in US filings pre-cutoff",
        "M_supports_claim": None,
        "interpretation": (
            f"{n} EDGAR mentions. Like Luckin's store count, the verifying registry "
            "(CAAC type-certificate holders, China civil aviation operators) isn't "
            "in the US toolkit. UNVERIFIABLE via current connectors — would need "
            "CAAC + FAA UAS database additions."
        ),
        "severity": Severity.UNVERIFIABLE,
    }


def _score_003(ev, c):
    sc = ev.get("edgar_sc13_filings", {})
    n = sc.get("total_hits", 0)
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"{n} institutional ownership filings naming EHang. Real public-company disclosure infrastructure."
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "No SC 13G filings found."
    return {
        "M_check": "EDGAR SC 13G/D for EHang institutional ownership",
        "M_value": f"{n} filings pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


SCORERS = {
    "EH-001": _score_001,
    "EH-002": _score_002,
    "EH-003": _score_003,
}
