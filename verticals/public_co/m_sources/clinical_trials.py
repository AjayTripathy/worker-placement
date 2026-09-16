"""ClinicalTrials.gov v2 REST API — public registry of all NIH-registered trials.

A real biotech with active drug development should appear here as a lead
sponsor on multiple trials, with diverse phase distributions and credible
collaborators. A fraudulent or thin biotech will have a sparse footprint.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["283", "384", "873"],
    "issuer_features": ["clinical_trial_program"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "ClinicalTrials.gov v2 registry footprint check; thin/sparse sponsorship contradicts an active-pipeline narrative.",
}

import urllib.parse

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def query_by_lead_sponsor(sponsor_name: str, cutoff_date: str | None = None) -> dict:
    """List trials where the named entity is lead sponsor."""
    qs = urllib.parse.urlencode({
        "query.lead": sponsor_name,
        "pageSize": 100,
        "format": "json",
        "countTotal": "true",
    })
    url = f"https://clinicaltrials.gov/api/v2/studies?{qs}"
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
            data = r.json()
    except Exception as e:
        return {"error": str(e)}

    studies = []
    phase_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    collaborators: set[str] = set()
    for s in data.get("studies", []):
        pm = s.get("protocolSection", {})
        idm = pm.get("identificationModule", {})
        sm = pm.get("statusModule", {})
        sp = pm.get("sponsorCollaboratorsModule", {})
        dm = pm.get("designModule", {})
        start = sm.get("startDateStruct", {}).get("date")
        if cutoff_date and start and start > cutoff_date:
            continue
        nct = idm.get("nctId")
        status = sm.get("overallStatus")
        phases = dm.get("phases") or []
        studies.append({
            "nct_id": nct,
            "title": idm.get("briefTitle"),
            "status": status,
            "start_date": start,
            "phases": phases,
            "lead_sponsor": (sp.get("leadSponsor") or {}).get("name"),
        })
        for ph in phases:
            phase_counts[ph] = phase_counts.get(ph, 0) + 1
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1
        for co in sp.get("collaborators", []) or []:
            nm = co.get("name")
            if nm:
                collaborators.add(nm)

    return {
        "sponsor_searched": sponsor_name,
        "cutoff_date": cutoff_date,
        "total_in_registry": data.get("totalCount"),
        "n_studies_pre_cutoff": len(studies),
        "phase_counts": phase_counts,
        "status_counts": status_counts,
        "n_unique_collaborators": len(collaborators),
        "collaborators_sample": sorted(collaborators)[:10],
        "studies_sample": studies[:5],
    }
