"""Competitor-trial omission detector for biotech / pharma sponsor IPO DD.

Sister detector to clinical_trial_referral_quality (which is for diagnostics co's).

The Parabilis live test surfaced that clinical_trial_referral_quality returns
8/9 ENROLLING_MATCH for drug-sponsor biotechs (because their claims naturally
match their own trials). The structural value-add for sponsor-developers is
catching what the S-1 competitive landscape OMITS.

FIRES when ClinicalTrials.gov surfaces enrolling competitor trials targeting the
same biomarker / indication that are NOT mentioned in the company's S-1
"Competition" section.

Severity:
- HIGH: 3+ omitted competitors at advanced stages (Phase 2/3) targeting the same
        primary indication
- MEDIUM: 1-2 omitted competitors at Phase 2/3
- LOW: omitted competitors at Phase 1 / preclinical only

Live catch (2026-05-28 Parabilis): S-1 only names GSI competitors (Ogsiveo,
varegacestat); omits Tegavivint (NCT04851119, TBL1/Wnt antagonist) +
ALN-BCAT (NCT06600321, Alnylam siRNA against CTNNB1 in HCC).

## Data shape

{
  "company_name": "Parabilis Medicines",
  "primary_indication": "desmoid tumors",
  "primary_target": "beta-catenin / Wnt pathway",
  "competitors_named_in_s1": ["Ogsiveo (nirogacestat)", "varegacestat"],
  "competitors_found_on_ctgov_omitted": [
    {"name": "Tegavivint", "nct": "NCT04851119", "target": "TBL1/Wnt", "phase": "Phase 2",
     "sponsor": "Iterion Therapeutics"},
    {"name": "ALN-BCAT", "nct": "NCT06600321", "target": "CTNNB1 siRNA",
     "phase": "Phase 1", "sponsor": "Alnylam"},
  ],
  "as_of_date": "2026-05-28",
  "source_url": "Parabilis S-1 Competition + ClinicalTrials.gov target search"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [2834, 2836, 8731, 3841, 3845],
    "sic_prefixes": ["283", "384", "873"],
    "issuer_features": ["clinical_trial_program"],
    "asset_classes": ["corporate_ipo_dd", "diagnostics_biotech_dd"],
    "applies_universally": False,
    "summary": "ClinicalTrials.gov surfaces enrolling competitor trials omitted from S-1 Competition.",
}

ADVANCED_PHASES = {"Phase 2", "Phase 3", "Phase 2/3", "Phase 2/Phase 3"}


def evaluate(obligor_name: str, data: dict) -> dict:
    omitted = data.get("competitors_found_on_ctgov_omitted") or []
    if not isinstance(omitted, list):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    advanced_omitted = [o for o in omitted if (o.get("phase") or "") in ADVANCED_PHASES]
    n_advanced = len(advanced_omitted)
    n_total = len(omitted)

    if n_total == 0:
        return {
            "fires": False,
            "reason": "NO_OMITTED_COMPETITORS",
            "evidence": {"competitors_named_in_s1": data.get("competitors_named_in_s1", [])},
        }

    if n_advanced >= 3:
        severity, reason = "HIGH", "MULTIPLE_ADVANCED_COMPETITORS_OMITTED"
    elif n_advanced >= 1:
        severity, reason = "MEDIUM", "ADVANCED_COMPETITORS_OMITTED"
    else:
        severity, reason = "LOW", "EARLY_STAGE_COMPETITORS_OMITTED"

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "n_omitted_total": n_total,
            "n_omitted_advanced_phase": n_advanced,
            "omitted_competitors": omitted[:5],
            "primary_indication": data.get("primary_indication"),
            "primary_target": data.get("primary_target"),
        },
    }
