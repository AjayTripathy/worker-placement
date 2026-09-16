"""Helper for querying ClinicalTrials.gov v2 API.

Used by clinical_trial_referral_quality detector. Bucket-classifies each
claimed lead by querying enrolling-trial status.

Public API: https://clinicaltrials.gov/api/v2/studies
- Free, no auth required
- Rate limit ~50 req/min (DD scale is fine)
- Returns enrolling studies + sponsor + eligibility criteria
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

APPLIES_TO = {
    "sic_codes": [2834, 2836, 8731, 3841, 3845],
    "sic_prefixes": ["283", "384", "873"],
    "issuer_features": ["clinical_trial_program"],
    "asset_classes": ["corporate_ipo_dd", "diagnostics_biotech_dd"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "ClinicalTrials.gov v2 API helper — used by other biotech detectors.",
}


CTGOV_API = "https://clinicaltrials.gov/api/v2/studies"


def fetch_trials_for_target(target: str, max_studies: int = 50) -> list[dict]:
    """Query CTGov for active studies mentioning a biomarker/target.

    Returns list of trial dicts (subset of full protocol section).
    """
    params = {
        "query.term": target,
        "filter.overallStatus": "RECRUITING|ACTIVE_NOT_RECRUITING|ENROLLING_BY_INVITATION",
        "pageSize": str(max_studies),
        "fields": (
            "NCTId,BriefTitle,LeadSponsorName,OverallStatus,Phase,"
            "Condition,EligibilityCriteria,MinimumAge,MaximumAge,Gender,"
            "EnrollmentCount,InterventionName,InterventionType,StudyType"
        ),
    }
    url = f"{CTGOV_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SignalOS/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data.get("studies", [])
    except Exception as e:
        return [{"_error": str(e)}]


def classify_lead(target: str, indication: str, biomarker_stratification: str | None = None,
                  drug_class: str | None = None) -> dict:
    """Classify a single claimed treatment lead into one of 6 buckets.

    Returns dict with:
      - bucket: one of the 6 enums
      - trials_matched: list of matching NCT IDs + brief reasoning
      - n_target_trials: count of enrolling trials for the target
      - n_histology_match: count enrolling the patient's histology
    """
    trials = fetch_trials_for_target(target)
    if not trials or (len(trials) == 1 and trials[0].get("_error")):
        return {
            "bucket": "UNVERIFIABLE",
            "reason": f"CTGov API error: {trials[0].get('_error') if trials else 'no response'}",
            "trials_matched": [],
            "n_target_trials": 0,
        }

    n_target = len(trials)
    if n_target == 0:
        return {
            "bucket": "NO_TARGET_TRIAL",
            "reason": f"Zero enrolling trials found for target '{target}'",
            "trials_matched": [],
            "n_target_trials": 0,
        }

    # Histology matching (simple string match in Condition field — caller can refine)
    indication_lc = indication.lower()
    indication_tokens = set(t for t in indication_lc.split() if len(t) >= 4)
    histology_matches = []
    for t in trials:
        proto = t.get("protocolSection", {})
        cond_module = proto.get("conditionsModule", {})
        conditions = " ".join(cond_module.get("conditions") or []).lower()
        # Match if any token from indication appears in conditions
        if any(tok in conditions for tok in indication_tokens):
            id_mod = proto.get("identificationModule", {})
            histology_matches.append({
                "nct": id_mod.get("nctId"),
                "title": id_mod.get("briefTitle"),
                "conditions": cond_module.get("conditions"),
            })

    n_hist = len(histology_matches)

    if n_hist == 0:
        return {
            "bucket": "HISTOLOGY_MISMATCH",
            "reason": (
                f"{n_target} enrolling trials for target '{target}' but NONE "
                f"enroll patient's histology '{indication}'"
            ),
            "trials_matched": [],
            "n_target_trials": n_target,
            "n_histology_match": 0,
            "available_trials_sample": [
                {
                    "nct": t.get("protocolSection", {}).get("identificationModule", {}).get("nctId"),
                    "conditions": t.get("protocolSection", {}).get("conditionsModule", {}).get("conditions"),
                }
                for t in trials[:5]
            ],
        }

    if biomarker_stratification:
        # Caller indicated a biomarker requirement; check eligibility criteria
        biomarker_lc = biomarker_stratification.lower()
        biomarker_match_count = 0
        for tm in histology_matches:
            proto = next(
                (t.get("protocolSection", {}) for t in trials
                 if t.get("protocolSection", {}).get("identificationModule", {}).get("nctId") == tm["nct"]),
                {}
            )
            elig = (proto.get("eligibilityModule", {}).get("eligibilityCriteria") or "").lower()
            if biomarker_lc in elig:
                biomarker_match_count += 1
        if biomarker_match_count == 0:
            return {
                "bucket": "BIOMARKER_GAP",
                "reason": (
                    f"{n_hist} trials enroll patient's histology but none mention "
                    f"required biomarker '{biomarker_stratification}'. Eligibility uncertain."
                ),
                "trials_matched": histology_matches,
                "n_target_trials": n_target,
                "n_histology_match": n_hist,
            }

    return {
        "bucket": "ENROLLING_MATCH",
        "reason": f"{n_hist} of {n_target} trials enroll patient's histology",
        "trials_matched": histology_matches,
        "n_target_trials": n_target,
        "n_histology_match": n_hist,
    }


def score_company(company_name: str, claimed_leads: list[dict]) -> dict:
    """Run the lookup on each claimed lead and produce input shape for the detector.

    claimed_leads: list of dicts with keys:
      - case_id, target_biomarker, patient_indication, therapeutic_class
      - (optional) biomarker_stratification

    Returns the detector-input shape with each lead enriched with trial_lookup_result.
    """
    enriched = []
    for c in claimed_leads:
        result = classify_lead(
            target=c["target_biomarker"],
            indication=c["patient_indication"],
            biomarker_stratification=c.get("biomarker_stratification"),
            drug_class=c.get("therapeutic_class"),
        )
        enriched.append({
            **c,
            "trial_lookup_result": result["bucket"],
            "trial_lookup_reason": result["reason"],
            "trial_lookup_evidence": {
                "n_target_trials": result.get("n_target_trials"),
                "n_histology_match": result.get("n_histology_match"),
                "trials_matched": result.get("trials_matched", [])[:5],
                "available_trials_sample": result.get("available_trials_sample"),
            },
        })

    return {
        "company_name": company_name,
        "claimed_leads": enriched,
        "as_of_date": "2026-05-28",
        "source_urls": [CTGOV_API],
    }
