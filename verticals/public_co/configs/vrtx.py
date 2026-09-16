"""Vertex Pharmaceuticals (VRTX) — clean biotech parallel for SAVA test.

Vertex has a multi-decade track record of FDA-approved CFTR modulators
(Kalydeco, Orkambi, Symdeko, Trikafta) and a broad active clinical pipeline.
Same cutoff (2021-08-24) as SAVA so the same M-source tests run side-by-side.
"""
from __future__ import annotations

from ..m_sources import clinical_trials, edgar_fts, openfda
from ..scoring import Severity


CIK = "0000875320"
TICKER = "vrtx"
CUTOFF_DATE = "2021-08-24"
PRIORITY_FORMS = {"10-K", "10-Q", "8-K", "DEF 14A"}


CLAIMS = [
    {
        "claim_id": "VRTX-001",
        "claim_text": "Vertex sponsors multiple active clinical trials across its CFTR-modulator and emerging programs",
        "source_form": "10-K",
        "filing_date": "2021-02-11",
        "category": "clinical_program",
        "M_sources": ["ct_vertex"],
    },
    {
        "claim_id": "VRTX-002",
        "claim_text": "Vertex has multiple FDA-approved drugs generating commercial revenue",
        "source_form": "10-K",
        "filing_date": "2021-02-11",
        "category": "regulatory_milestone",
        "M_sources": ["fda_vertex"],
    },
    {
        "claim_id": "VRTX-003",
        "claim_text": "Vertex's clinical program has substantial collaborator and partner ecosystem",
        "source_form": "10-K",
        "filing_date": "2021-02-11",
        "category": "partnership",
        "M_sources": ["ct_vertex"],
    },
    {
        "claim_id": "VRTX-004",
        "claim_text": "Vertex's drug brands (Trikafta, Kalydeco, Orkambi, Symdeko) draw external counterparty/competitor SEC disclosures",
        "source_form": "10-K",
        "filing_date": "2021-02-11",
        "category": "external_validation",
        "M_sources": ["edgar_trikafta_mentions"],
    },
]


M_QUERIES = [
    ("ct_vertex", clinical_trials.query_by_lead_sponsor,
     {"sponsor_name": "Vertex Pharmaceuticals", "cutoff_date": CUTOFF_DATE}),
    ("fda_vertex", openfda.query_approved_drugs,
     {"manufacturer_name": "vertex pharmaceuticals"}),
    ("edgar_trikafta_mentions", edgar_fts.query_fulltext,
     {"search_term": "Trikafta", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K,DEF 14A,20-F"}),
]


def _score_001(ev, c):
    ct = ev.get("ct_vertex", {})
    n = ct.get("n_studies_pre_cutoff", 0)
    phases = ct.get("phase_counts", {})
    if n >= 20:
        sev = Severity.PASS
        sup = True
        interp = (
            f"ClinicalTrials.gov: {n} Vertex-sponsored studies pre-cutoff with diverse "
            f"phase distribution {phases}. Same registry test that returned 9 for "
            "Cassava (clinical-stage, single program) returns {n}+ for Vertex (multi-"
            "program, multi-phase). PASS."
        )
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"Only {n} studies registered."
    return {
        "M_check": "ClinicalTrials.gov v2 API: studies with Vertex Pharmaceuticals as lead sponsor",
        "M_value": f"{n} studies pre-cutoff, phases={phases}, collaborators={ct.get('n_unique_collaborators', 0)}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://clinicaltrials.gov/api/v2/studies?query.lead=Vertex+Pharmaceuticals",
    }


def _score_002(ev, c):
    fda = ev.get("fda_vertex", {})
    n = fda.get("n_approved_applications", 0)
    brands = fda.get("brand_names", [])
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = (
            f"openFDA Drugs@FDA: {n} approved drug applications under 'Vertex "
            f"Pharmaceuticals' as manufacturer. Brand names include: {brands[:5]}. "
            "Same registry that returned 0 for Cassava (clinical-stage only) "
            "returns multiple approved-drug applications for Vertex. Strong PASS."
        )
    else:
        sev = Severity.RED_FLAG_NEGATIVE
        sup = False
        interp = "Zero approved drugs — would be a major divergence from a 'commercial revenue' claim."
    return {
        "M_check": "openFDA Drugs@FDA: approved drug applications by manufacturer 'Vertex Pharmaceuticals'",
        "M_value": f"{n} approved applications; brands: {brands[:5]}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://api.fda.gov/drug/drugsfda.json?search=openfda.manufacturer_name:%22vertex+pharmaceuticals%22",
    }


def _score_003(ev, c):
    ct = ev.get("ct_vertex", {})
    n_collab = ct.get("n_unique_collaborators", 0)
    if n_collab >= 5:
        sev = Severity.PASS
        sup = True
        interp = (
            f"CT.gov shows {n_collab} unique collaborators on Vertex trials. Diverse "
            "ecosystem corroborated."
        )
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"Only {n_collab} collaborator(s)."
    return {
        "M_check": "ClinicalTrials.gov collaborator metadata across Vertex-sponsored studies",
        "M_value": f"{n_collab} unique collaborators; sample: {ct.get('collaborators_sample', [])}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
    }


def _score_004(ev, c):
    fts = ev.get("edgar_trikafta_mentions", {})
    n = fts.get("total_hits", 0)
    if n >= 10:
        sev = Severity.PASS
        sup = True
        interp = (
            f"{n} mentions of 'Trikafta' across US public-company filings pre-cutoff. "
            "Vertex's flagship CFTR product is widely discussed by competitors, "
            "payers, and partners. Same external-validation test that returned thin "
            "results for Cassava's Simufilam returns rich corroboration here."
        )
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"Only {n} mentions."
    else:
        sev = Severity.RED_FLAG_NEGATIVE
        sup = False
        interp = "Zero EDGAR mentions — would suggest no real commercial impact."
    return {
        "M_check": "EDGAR FTS for 'Trikafta' across all US-listed companies",
        "M_value": f"{n} mentions in 10-K/Q/8-K/DEF 14A/20-F pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Trikafta%22",
    }


SCORERS = {
    "VRTX-001": _score_001,
    "VRTX-002": _score_002,
    "VRTX-003": _score_003,
    "VRTX-004": _score_004,
}
