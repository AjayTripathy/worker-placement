"""Payor concentration detector.

FIRES when Medicaid (or any single payor) > 65% of net patient revenue.

Why predictive: Single-payor concentration creates structural fragility.
A 65%+ Medicaid hospital is exposed to:
  - State Medicaid reimbursement cuts (DSH, supplemental payment programs)
  - Eligibility changes (e.g., Medicaid expansion rollbacks, work requirements)
  - State budget pressure during downturns
  - Lower commercial cross-subsidy

Lead time vs rating action: typically 18-36 months — agencies treat
concentration as a structural risk factor that compounds with any negative
state policy event.

Data shape:
  {
    "medicaid_pct_of_npr": 0.72,
    "medicare_pct_of_npr": 0.21,
    "commercial_pct_of_npr": 0.07,
    "fiscal_year": "FY2024",
    "source_url": "..."
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["hospital_obligor", "nursing_home_obligor", "ccrc_obligor"],
    "asset_classes": ["ca_hospital_muni", "healthcare_muni", "ca_chffa_hospital_conduit", "ca_nh_muni", "ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Payor concentration detector.",
}

CRITICAL_THRESHOLD = 0.65  # 65% of NPR from a single payor
WATCH_THRESHOLD = 0.55


def evaluate(obligor_name: str, data: dict) -> dict:
    medicaid = data.get("medicaid_pct_of_npr")
    medicare = data.get("medicare_pct_of_npr")

    if medicaid is None and medicare is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    payors = {"medicaid": medicaid, "medicare": medicare}
    max_payor, max_share = max(payors.items(), key=lambda kv: kv[1] or 0)
    if max_share is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if max_share >= CRITICAL_THRESHOLD:
        return {
            "fires": True,
            "reason": f"PAYOR_CONCENTRATION_CRITICAL_{max_payor.upper()}",
            "severity": "HIGH",
            "evidence": {
                "dominant_payor": max_payor,
                "share_of_npr": max_share,
                "threshold": CRITICAL_THRESHOLD,
                "full_mix": payors,
            },
        }
    elif max_share >= WATCH_THRESHOLD:
        return {
            "fires": False,  # YELLOW — concentration risk but not at exclusion threshold
            "reason": "PAYOR_CONCENTRATION_WATCH",
            "severity": "MEDIUM",
            "evidence": {
                "dominant_payor": max_payor,
                "share_of_npr": max_share,
            },
        }
    return {
        "fires": False,
        "reason": "PAYOR_MIX_DIVERSIFIED",
        "evidence": {"dominant_payor": max_payor, "share_of_npr": max_share},
    }
