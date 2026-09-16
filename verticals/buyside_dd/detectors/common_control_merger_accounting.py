"""Common-control merger accounting detector for corporate IPO DD.

FIRES when an IPO issuer has absorbed one or more related entities via a
common-control merger AND the historical financials of the absorbed entity
are NOT separately disclosed.

Common-control accounting combines historicals at carrying value (no goodwill,
no fair-value step-up), making it impossible for IPO investors to bridge the
prior acquisition price to current segment value. The absorbed entity's
operating history disappears into the consolidated entity's history.

Severity:
- RED: $10B+ absorption value with no separate financial statements; >25% of
       current revenue from absorbed entity
- HIGH: $1B+ absorption value with no separate statements
- MEDIUM: smaller absorption OR partial separate disclosure

Live catch (2026-05-28 SpaceX): Musk merged Twitter ($44B Oct 2022) → X.AI Corp
→ xAI → SpaceX between Mar 2025 and Feb 2026. S-1 explicitly states "separate
financial statements of xAI and X are not provided" (Note 1, line 33326). All
2023-2025 historicals retroactively combined at carrying value, no goodwill,
no acquisition fair-value step-up. Investor cannot bridge $44B Twitter price →
current AI segment value.

## Data shape

{
  "company_name": "Space Exploration Technologies Corp",
  "absorbed_entities": [
    {"name": "Twitter / X", "absorbed_via": "Musk-controlled merger Oct 2022 → X.AI → xAI → SpaceX",
     "original_acquisition_value_usd": 44000000000,
     "absorption_date": "2026-02-15",
     "described_as_common_control": true,
     "estimated_pct_of_current_revenue": 5,

     # Mitigating factors (DETERMINISTIC SEVERITY DOWNGRADES) per absorbed entity.
     # Default to most-conservative (no mitigation) when unknown.
     "separate_financial_statements_provided": false,        # full standalone audited financials
     "pre_combination_audited_years_provided": 0,            # int — N years of standalone history
     "pro_forma_combined_disclosure_provided": false,        # SX Article 11 pro-forma
     "carve_out_financials_provided": false},                # SX Rule 3-05 carve-out
    ...
  ],
  "as_of_date": "2026-05-28",
  "source_url": "SpaceX S-1 Note 1, line 33326"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["common_control_merger_disclosed"],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "$1B+ common-control absorption without separate financial statements.",
}


def _is_fully_mitigated(a: dict) -> bool:
    """An absorbed-entity record is FULLY mitigated when separate audited
    financials are provided (Rule 3-05 or equivalent). Other partial
    disclosures (pro-forma, pre-combination years) downgrade but don't fully
    mitigate — they're handled in the severity-tier downgrade below."""
    return bool(a.get("separate_financial_statements_provided"))


def _partial_mitigation_score(a: dict) -> int:
    """0-3 score: counts pro-forma + pre-combination years + carve-out as
    partial mitigations. Used to downgrade severity tier."""
    score = 0
    if a.get("pro_forma_combined_disclosure_provided"):
        score += 1
    if a.get("carve_out_financials_provided"):
        score += 1
    years = a.get("pre_combination_audited_years_provided") or 0
    if isinstance(years, (int, float)) and years >= 2:
        score += 1
    return score


def evaluate(obligor_name: str, data: dict) -> dict:
    absorbed = data.get("absorbed_entities") or []
    if not isinstance(absorbed, list) or not absorbed:
        return {"fires": False, "reason": "NO_ABSORBED_ENTITIES", "evidence": {}}

    suppressed = [
        a for a in absorbed
        if a.get("described_as_common_control") and not _is_fully_mitigated(a)
    ]

    if not suppressed:
        return {
            "fires": False,
            "reason": "ABSORPTIONS_DISCLOSED_SEPARATELY",
            "evidence": {"n_absorbed_total": len(absorbed),
                         "all_full_separate_financials_provided": True},
        }

    max_val = max((a.get("original_acquisition_value_usd") or 0) for a in suppressed)
    max_rev_pct = max((a.get("estimated_pct_of_current_revenue") or 0) for a in suppressed)
    # Partial mitigation score for the largest-value absorption
    largest = max(suppressed, key=lambda x: x.get("original_acquisition_value_usd") or 0)
    partial_score = _partial_mitigation_score(largest)

    if max_val >= 10_000_000_000 and max_rev_pct >= 25:
        severity, reason = "RED", "MASSIVE_COMMON_CONTROL_ABSORPTION_NO_SEPARATE_STATEMENTS"
    elif max_val >= 10_000_000_000:
        severity, reason = "HIGH", "LARGE_COMMON_CONTROL_ABSORPTION_NO_SEPARATE_STATEMENTS"
    elif max_val >= 1_000_000_000:
        severity, reason = "HIGH", "MATERIAL_COMMON_CONTROL_ABSORPTION_NO_SEPARATE_STATEMENTS"
    else:
        severity, reason = "MEDIUM", "COMMON_CONTROL_ABSORPTION_NO_SEPARATE_STATEMENTS"

    # Partial-mitigation downgrade: 2+ partial mitigations drop one tier;
    # 3 partial mitigations drop two tiers. SpaceX/Twitter case has 0 partial
    # mitigations (no pro-forma, no carve-out, no pre-combination years) → RED stays.
    if partial_score >= 3:
        severity = {"RED": "MEDIUM", "HIGH": "LOW", "MEDIUM": "LOW"}.get(severity, severity)
        reason += "__3_PARTIAL_MITIGATIONS_DOWNGRADED_TWO_TIERS"
    elif partial_score == 2:
        severity = {"RED": "HIGH", "HIGH": "MEDIUM", "MEDIUM": "LOW"}.get(severity, severity)
        reason += "__2_PARTIAL_MITIGATIONS_DOWNGRADED_ONE_TIER"

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "n_suppressed_absorptions": len(suppressed),
            "largest_absorption_value_usd": max_val,
            "largest_absorption_name": next(
                (a.get("name") for a in suppressed
                 if (a.get("original_acquisition_value_usd") or 0) == max_val),
                None,
            ),
            "estimated_pct_of_current_revenue": max_rev_pct,
            "largest_absorption_partial_mitigation_score": partial_score,
            "largest_absorption_mitigations": {
                "pro_forma_combined_disclosure_provided": bool(largest.get("pro_forma_combined_disclosure_provided")),
                "carve_out_financials_provided": bool(largest.get("carve_out_financials_provided")),
                "pre_combination_audited_years_provided": largest.get("pre_combination_audited_years_provided") or 0,
            },
        },
    }
