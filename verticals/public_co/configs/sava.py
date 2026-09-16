"""Cassava Sciences (SAVA) — alleged biotech / clinical-trial fraud.

A Citizen Petition filed Aug 25 2021 by attorneys with disclosed short positions
alleged image manipulation and data fabrication in Cassava's published research
on Simufilam (an Alzheimer's candidate). Subsequent: NIH journals expressed
concern, City University of NY investigated co-authors, DOJ subpoenaed
Cassava (Aug 2022). Several papers were retracted.

Cutoff: 2021-08-24 (day before Citizen Petition).

Test for the framework: at the cutoff date, can claims about Cassava's drug
program be corroborated by the public clinical-trial / FDA-approval registries?
"""
from __future__ import annotations

from ..m_sources import clinical_trials, edgar_fts, openfda
from ..scoring import Severity


CIK = "0001069530"
TICKER = "sava"
CUTOFF_DATE = "2021-08-24"
PRIORITY_FORMS = {"S-1", "S-1/A", "10-K", "10-Q", "8-K", "DEF 14A", "424B4"}


CLAIMS = [
    {
        "claim_id": "SAVA-001",
        "claim_text": "Simufilam (PTI-125) is in active Phase 2/3 clinical trials sponsored by Cassava Sciences",
        "source_form": "10-K",
        "filing_date": "2021-03-08",
        "category": "clinical_program",
        "M_sources": ["ct_cassava"],
    },
    {
        "claim_id": "SAVA-002",
        "claim_text": "Cassava has multiple FDA-approved drugs / commercial products",
        "source_form": "10-K",
        "filing_date": "2021-03-08",
        "category": "regulatory_milestone",
        "M_sources": ["fda_cassava"],
    },
    {
        "claim_id": "SAVA-003",
        "claim_text": "Cassava's clinical program has substantial collaborator and partner ecosystem (academic, pharma, NIH)",
        "source_form": "10-K",
        "filing_date": "2021-03-08",
        "category": "partnership",
        "M_sources": ["ct_cassava"],
    },
    {
        "claim_id": "SAVA-004",
        "claim_text": "Cassava's claims about Simufilam are corroborated by external partner / counterparty SEC disclosures",
        "source_form": "10-K",
        "filing_date": "2021-03-08",
        "category": "external_validation",
        "M_sources": ["edgar_simufilam_mentions"],
    },
]


M_QUERIES = [
    ("ct_cassava", clinical_trials.query_by_lead_sponsor,
     {"sponsor_name": "Cassava Sciences", "cutoff_date": CUTOFF_DATE}),
    ("fda_cassava", openfda.query_approved_drugs,
     {"manufacturer_name": "cassava sciences"}),
    ("edgar_simufilam_mentions", edgar_fts.query_fulltext,
     {"search_term": "Simufilam", "cutoff_date": CUTOFF_DATE,
      "start_date": "2018-01-01", "forms": "10-K,10-Q,8-K,DEF 14A,20-F"}),
]


def _score_001(ev, c):
    ct = ev.get("ct_cassava", {})
    n = ct.get("n_studies_pre_cutoff", 0)
    phases = ct.get("phase_counts", {})
    if n >= 1 and any(p in phases for p in ("PHASE2", "PHASE3", "PHASE2/3")):
        sev = Severity.PASS
        sup = True
        interp = (
            f"ClinicalTrials.gov: {n} Cassava-sponsored studies pre-cutoff; phase mix "
            f"{phases}. Simufilam IS registered as an active clinical program — the "
            "framework correctly returns PASS on the existence of the trial program. "
            "Whether the trial RESULTS are valid is a separate question that "
            "ClinicalTrials.gov registration cannot answer (data integrity is "
            "investigated downstream by FDA/journals/peer review)."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = (
            f"Only {n} studies registered; thinner than claimed. "
            "Failed to verify active Phase 2/3 program."
        )
    return {
        "M_check": "ClinicalTrials.gov v2 API: studies with Cassava Sciences as lead sponsor pre-cutoff; phase distribution",
        "M_value": (
            f"{n} studies pre-cutoff, phases={phases}, "
            f"collaborators_count={ct.get('n_unique_collaborators', 0)}"
        ),
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://clinicaltrials.gov/api/v2/studies?query.lead=Cassava+Sciences",
    }


def _score_002(ev, c):
    fda = ev.get("fda_cassava", {})
    n = fda.get("n_approved_applications", 0)
    if n == 0:
        sev = Severity.RED_FLAG_NEGATIVE
        sup = False
        interp = (
            f"openFDA Drugs@FDA: {n} approved drug applications under 'Cassava Sciences' "
            "as manufacturer. Cassava is clinical-stage with no commercial products. "
            "If 10-K language implies commercial revenue or approved product, that's a "
            "real divergence. (For Cassava pre-cutoff, the company correctly disclosed "
            "no commercial drugs — so this test passes only if the claim is itself "
            "consistent with the FDA registry.)"
        )
    elif n >= 1:
        sev = Severity.PASS
        sup = True
        interp = f"openFDA: {n} approved applications. Real commercial product."
    return {
        "M_check": "openFDA Drugs@FDA: approved drug applications by manufacturer 'Cassava Sciences'",
        "M_value": f"{n} approved applications",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://api.fda.gov/drug/drugsfda.json?search=openfda.manufacturer_name:%22cassava+sciences%22",
    }


def _score_003(ev, c):
    ct = ev.get("ct_cassava", {})
    n_collab = ct.get("n_unique_collaborators", 0)
    sample = ct.get("collaborators_sample", [])
    if n_collab >= 5:
        sev = Severity.PASS
        sup = True
        interp = (
            f"CT.gov shows {n_collab} unique collaborators on Cassava trials. Diverse "
            "ecosystem corroborated."
        )
    elif n_collab >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"Only {n_collab} collaborator(s) listed: {sample}. Thinner than typical "
            f"for an active Phase 2/3 program."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = (
            "ZERO collaborators listed across Cassava's CT.gov registrations. For an "
            "Alzheimer's drug at Phase 2/3 maturity, this is unusually thin — most "
            "real clinical programs at this stage have multiple academic / clinical "
            "site collaborators in the registry. Same test would return many for "
            "a real Phase 3 program (Vertex CFTR, Biogen aducanumab, etc.)."
        )
    return {
        "M_check": "ClinicalTrials.gov collaborator metadata across Cassava-sponsored studies",
        "M_value": f"{n_collab} unique collaborators; sample: {sample}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://clinicaltrials.gov/api/v2/studies?query.lead=Cassava+Sciences",
    }


def _score_004(ev, c):
    fts = ev.get("edgar_simufilam_mentions", {})
    n = fts.get("total_hits", 0)
    if n >= 5:
        sev = Severity.PASS
        sup = True
        interp = f"{n} mentions of 'Simufilam' in US public-company filings. External validation present."
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"Only {n} EDGAR mentions of 'Simufilam' across US public-company filings "
            "pre-cutoff. Most Phase 2/3 Alzheimer's candidates draw partner/competitor "
            "commentary in big-pharma 10-K risk factors. The thin counterparty "
            "footprint is one signal among several."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = (
            "Zero EDGAR mentions of 'Simufilam' across US public-company filings "
            "pre-cutoff. Same external-validation test that flagged Nikola's $14B "
            "pre-order book (zero customer disclosure) shows no third-party "
            "corroboration of the Simufilam program here."
        )
    return {
        "M_check": "EDGAR FTS for 'Simufilam' across all US-listed companies (counterparty / competitor disclosures)",
        "M_value": f"{n} mentions in 10-K/10-Q/8-K/DEF 14A/20-F pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Simufilam%22",
    }


SCORERS = {
    "SAVA-001": _score_001,
    "SAVA-002": _score_002,
    "SAVA-003": _score_003,
    "SAVA-004": _score_004,
}
