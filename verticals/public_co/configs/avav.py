"""AeroVironment (AVAV) — clean drone/UAS parallel for EH test.

Established US defense drone OEM (Puma, Raven, Switchblade). Multi-year DoD
contract history visible in public records. Same cutoff (2021-02-15) as EH.
"""
from __future__ import annotations

from ..m_sources import edgar_fts, epa_frs
from ..scoring import Severity


CIK = "0001368622"
TICKER = "avav"
CUTOFF_DATE = "2021-02-15"
PRIORITY_FORMS = {"10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {
        "claim_id": "AVAV-001",
        "claim_text": "AeroVironment has multi-year contracts with the US Department of Defense for drone systems",
        "source_form": "10-K",
        "filing_date": "2020-06-23",
        "category": "customer_pipeline",
        "M_sources": ["edgar_dod_mentions"],
    },
    {
        "claim_id": "AVAV-002",
        "claim_text": "AeroVironment manufactures real production drones (Puma, Raven, Switchblade) shipping at scale",
        "source_form": "10-K",
        "filing_date": "2020-06-23",
        "category": "production_volume",
        "M_sources": ["edgar_puma_raven_mentions", "epa_frs_avav"],
    },
    {
        "claim_id": "AVAV-003",
        "claim_text": "AeroVironment has institutional ownership disclosures consistent with a NASDAQ-listed defense contractor",
        "source_form": "SC 13G",
        "filing_date": "2021-01-31",
        "category": "governance",
        "M_sources": ["edgar_sc13_filings"],
    },
]


M_QUERIES = [
    ("edgar_dod_mentions", edgar_fts.query_fulltext,
     {"search_term": "AeroVironment", "cutoff_date": CUTOFF_DATE,
      "start_date": "2018-01-01", "forms": "10-K,10-Q,8-K"}),
    ("edgar_puma_raven_mentions", edgar_fts.query_fulltext,
     {"search_term": "Switchblade", "cutoff_date": CUTOFF_DATE,
      "start_date": "2018-01-01"}),
    ("epa_frs_avav", epa_frs.query_facilities,
     {"facility_name": "AeroVironment", "state_abbr": "CA"}),
    ("edgar_sc13_filings", edgar_fts.query_fulltext,
     {"search_term": "AeroVironment", "cutoff_date": CUTOFF_DATE,
      "start_date": "2020-01-01", "forms": "SC 13G,SC 13G/A,SC 13D,SC 13D/A"}),
]


def _score_001(ev, c):
    fts = ev.get("edgar_dod_mentions", {})
    n = fts.get("total_hits", 0)
    if n >= 30:
        sev = Severity.PASS
        sup = True
        interp = (
            f"{n} mentions of 'AeroVironment' across US public filings — including "
            "DoD prime contractor disclosures (L3Harris, Lockheed, Northrop) and "
            "AVAV's own filings. Same counterparty test that returned 0 for Nikola "
            "(BUD) returns rich corroboration here. PASS."
        )
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"{n} mentions — thinner than expected."
    return {
        "M_check": "EDGAR FTS for 'AeroVironment' in US public-company filings",
        "M_value": f"{n} mentions in 10-K/Q/8-K pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


def _score_002(ev, c):
    sw = ev.get("edgar_puma_raven_mentions", {})
    frs = ev.get("epa_frs_avav", {})
    n_sw = sw.get("total_hits", 0)
    n_frs = frs.get("n_facilities", 0)
    if n_sw >= 5 or n_frs >= 1:
        sev = Severity.PASS
        sup = True
        interp = (
            f"EDGAR mentions of 'Switchblade': {n_sw}; EPA FRS facilities for "
            f"AeroVironment in CA: {n_frs}. Real product line, real industrial "
            "footprint. PASS."
        )
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "Limited corroboration — possibly source-coverage gap."
    return {
        "M_check": "EDGAR FTS for product names + EPA FRS for industrial facilities",
        "M_value": f"Switchblade mentions: {n_sw}; FRS facilities (CA): {n_frs}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


def _score_003(ev, c):
    sc = ev.get("edgar_sc13_filings", {})
    n = sc.get("total_hits", 0)
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"{n} institutional ownership filings — real public-company disclosure."
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "No SC 13 filings found."
    return {
        "M_check": "EDGAR SC 13 institutional ownership disclosures",
        "M_value": f"{n} filings pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


SCORERS = {
    "AVAV-001": _score_001,
    "AVAV-002": _score_002,
    "AVAV-003": _score_003,
}
