"""Clinical-trial referral quality detector for diagnostics/biotech DD.

FIRES when a diagnostics company claims "actionable treatment leads" from its
molecular profiling, but those claims don't map to enrolling clinical trials
the patient is actually eligible for.

## Background

This detector was built after the Valius DD (2026-05-28) surfaced the
"action vs administration gap" Mode B finding: the deck claimed
"in every case, Valius has identified actionable treatment leads," but of
5 detailed cases, only 1 (mucosal melanoma / PRAME TCR-T) had a realistic
near-term trial pathway. Two had histology exclusions (GD2 CAR-T for
spindle cell sarcoma; PRAME TCR-T cutaneous-only); one was IND-pending
(STEAP1 for Ewing); one was off-label-only (Imdelltra GBM); the GBM/DLL3
case had an undisclosed biomarker stratification (IDH-mutant only).

## How it operates

Input: list of company's claimed treatment leads. Each lead has:
  - target_biomarker: gene / protein / antigen (e.g., "DLL3", "PRAME", "GD2")
  - patient_indication: cancer type + stage + key biomarkers (e.g., "IDH-WT GBM")
  - therapeutic_class: drug name or mechanism (e.g., "Imdelltra (tarlatamab) BiTE")

The detector classifies each lead into one of 6 buckets:
  - ENROLLING_MATCH (LOW severity): trial open, patient histology + biomarker eligible
  - HISTOLOGY_MISMATCH (MEDIUM): trial open for target but excludes patient histology
  - BIOMARKER_GAP (MEDIUM): trial open but requires biomarker not disclosed for patient
  - APPROVED_DRUG_OFF_LABEL (MEDIUM): drug approved for different indication; off-label is legal but not validated
  - OFF_LABEL_ONLY (HIGH): no enrolling trial; off-label / compassionate use only
  - NO_TARGET_TRIAL (HIGH): no enrolling trials for the target at all (speculative)

FIRES when:
  - ≥50% of claims fall into HIGH severity buckets, OR
  - 0 claims fall into ENROLLING_MATCH (no real lead at all)

## Public data source

clinicaltrials_gov_v2 API (https://clinicaltrials.gov/api/v2/studies).
Free, no rate limit issues for DD-scale queries (~5-50 lookups per company).
Catalog channel: `clinicaltrials_gov_v2` in knowledge_graph/signal_channels.json.

## Data shape

{
  "company_name": "Valius",
  "claimed_leads": [
    {
      "case_id": "Mark_GBM",
      "target_biomarker": "DLL3",
      "patient_indication": "Glioblastoma (IDH status undisclosed)",
      "therapeutic_class": "Imdelltra (tarlatamab) BiTE",
      "_undisclosed_stratification": "IDH-mutant required per published evidence + open trial",
      "trial_lookup_result": "HISTOLOGY_MISMATCH" or "BIOMARKER_GAP" etc.
    }
  ],
  "as_of_date": "2026-05-28",
  "source_urls": [...]
}
"""
from __future__ import annotations

APPLIES_TO = {
    # SIC restricted to diagnostics / clinical-lab business; sponsor-pharma SIC
    # (2834/2836) and biotech-research SIC (8731) explicitly excluded — they
    # produce trivially-positive results because sponsors match their own trials
    # (Parabilis 2026-05-28 observation: 8/9 ENROLLING_MATCH from self-trial echo).
    # For sponsor-developer biotechs, use competitor_trial_omission instead.
    "sic_codes": [3841, 3845, 8071],
    "sic_prefixes": ["384", "807"],
    "issuer_features": [
        "diagnostics_or_lab_business",
        "molecular_profiling_business",
        "patient_referral_business",
    ],
    # Hard-YES gate: any of these features must be set on the issuer profile.
    # any-of semantics handles patient-navigator companies (without a lab) too.
    "must_have_any_feature": [
        "diagnostics_or_lab_business",
        "molecular_profiling_business",
        "patient_referral_business",
    ],
    # NOTE: `anti_features: ["sponsor_developer_biotech"]` was removed 2026-05-29
    # as redundant + over-restrictive. must_have_any_feature is the gate;
    # hybrid issuers (diagnostics arm + clinical pipeline) should still match.
    "asset_classes": ["corporate_ipo_dd", "diagnostics_biotech_dd"],
    "applies_universally": False,
    "summary": "Diagnostics-referral 'action-vs-administration' gap (Valius archetype). NOT for pure sponsor-developer biotechs — use competitor_trial_omission for those.",
}

HIGH_SEVERITY_BUCKETS = {"OFF_LABEL_ONLY", "NO_TARGET_TRIAL"}
MEDIUM_SEVERITY_BUCKETS = {"HISTOLOGY_MISMATCH", "BIOMARKER_GAP", "APPROVED_DRUG_OFF_LABEL"}
LOW_SEVERITY_BUCKETS = {"ENROLLING_MATCH"}

DEFAULT_HIGH_RATIO_FIRE_THRESHOLD = 0.50  # ≥50% of claims in HIGH = fire


def evaluate(obligor_name: str, data: dict) -> dict:
    """Score a diagnostics company's claimed treatment leads against
    actual ClinicalTrials.gov enrollment status.
    """
    claims = data.get("claimed_leads") or []
    if not isinstance(claims, list) or not claims:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Tally bucket distribution
    bucket_counts = {
        "ENROLLING_MATCH": 0,
        "HISTOLOGY_MISMATCH": 0,
        "BIOMARKER_GAP": 0,
        "APPROVED_DRUG_OFF_LABEL": 0,
        "OFF_LABEL_ONLY": 0,
        "NO_TARGET_TRIAL": 0,
        "UNVERIFIABLE": 0,
    }
    valid_claims = []
    for c in claims:
        if not isinstance(c, dict):
            continue
        bucket = c.get("trial_lookup_result")
        if bucket in bucket_counts:
            bucket_counts[bucket] += 1
            valid_claims.append(c)
        else:
            bucket_counts["UNVERIFIABLE"] += 1

    n_total = sum(bucket_counts.values())
    if n_total == 0:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    n_high = sum(bucket_counts[b] for b in HIGH_SEVERITY_BUCKETS)
    n_med = sum(bucket_counts[b] for b in MEDIUM_SEVERITY_BUCKETS)
    n_low = sum(bucket_counts[b] for b in LOW_SEVERITY_BUCKETS)
    n_evaluable = n_high + n_med + n_low

    if n_evaluable == 0:
        return {
            "fires": False,
            "reason": "ALL_UNVERIFIABLE",
            "evidence": {"bucket_counts": bucket_counts},
        }

    high_ratio = n_high / n_evaluable
    enrolling_match_count = bucket_counts["ENROLLING_MATCH"]

    threshold = data.get("high_ratio_fire_threshold", DEFAULT_HIGH_RATIO_FIRE_THRESHOLD)

    # FIRE conditions
    if enrolling_match_count == 0 and n_evaluable >= 2:
        return {
            "fires": True,
            "reason": "ZERO_ENROLLING_MATCHES",
            "severity": "HIGH",
            "evidence": {
                "n_claims": n_total,
                "bucket_counts": bucket_counts,
                "high_severity_ratio": round(high_ratio, 2),
                "interpretation": "Company has claimed actionable leads but NONE map to a trial the patient is eligible for. Suggests target identification is being conflated with patient-on-therapy."
            },
        }

    if high_ratio >= threshold and n_evaluable >= 2:
        return {
            "fires": True,
            "reason": "HIGH_SEVERITY_RATIO_EXCEEDED",
            "severity": "HIGH" if high_ratio >= 0.75 else "MEDIUM",
            "evidence": {
                "n_claims": n_total,
                "bucket_counts": bucket_counts,
                "high_severity_ratio": round(high_ratio, 2),
                "threshold_used": threshold,
                "interpretation": (
                    f"{n_high} of {n_evaluable} evaluable claims fall into "
                    "HIGH-severity buckets (NO_TARGET_TRIAL or OFF_LABEL_ONLY). "
                    "Action-vs-administration gap is material."
                ),
            },
        }

    return {
        "fires": False,
        "reason": "REFERRAL_QUALITY_ADEQUATE",
        "evidence": {
            "n_claims": n_total,
            "bucket_counts": bucket_counts,
            "high_severity_ratio": round(high_ratio, 2),
            "enrolling_matches": enrolling_match_count,
        },
    }
