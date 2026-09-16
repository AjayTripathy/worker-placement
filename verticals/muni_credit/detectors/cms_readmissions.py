"""CMS Hospital Readmissions Reduction Program (HRRP) penalty detector.

FIRES when:
  - For a single-hospital obligor: hospital is at MAX 3.00% HRRP penalty
  - For a multi-hospital system: ≥30% of constituent hospitals are at max penalty
    OR weighted-average penalty across system > 2.00%

Why predictive: CMS reduces ALL Medicare inpatient payments by up to 3% for
hospitals with worst-quartile 30-day readmission rates. Medicare is 30-50%
of hospital revenue, so 3% × 40% = ~1.2% of total revenue eliminated. Penalty
is announced August, effective October 1.

Quality dimension: persistent worst-quartile readmissions correlates with
broader operational dysfunction. Lead time vs rating action: 6-18 months.

Data shape:
  {
    "obligor_type": "single_hospital" | "multi_hospital_system",
    "cms_penalty_pct": 3.00,  # for single hospital
    "n_constituent_hospitals_tracked": 12,  # for system
    "n_at_max_penalty": 5,
    "weighted_avg_penalty_pct": 1.85,
    "fiscal_year": "FY2024",
    "source_url": "...",
    "confidence": "HIGH"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["hospital_obligor", "nursing_home_obligor"],
    "asset_classes": ["ca_hospital_muni", "healthcare_muni", "ca_chffa_hospital_conduit", "ca_nh_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "CMS Hospital Readmissions Reduction Program (HRRP) penalty detector.",
}

MAX_PENALTY_PCT = 3.00
SINGLE_HOSPITAL_FIRE_PCT = 3.00  # only fires at the max
SYSTEM_SHARE_AT_MAX_THRESHOLD = 0.30  # ≥30% of constituent hospitals at max
SYSTEM_WEIGHTED_AVG_THRESHOLD = 2.00  # OR weighted-avg ≥2%


def evaluate(obligor_name: str, data: dict) -> dict:
    obligor_type = data.get("obligor_type")
    if obligor_type is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if obligor_type == "single_hospital":
        penalty = data.get("cms_penalty_pct")
        if penalty is None:
            return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
        if penalty >= SINGLE_HOSPITAL_FIRE_PCT:
            return {
                "fires": True,
                "reason": "CMS_HRRP_MAX_PENALTY",
                "severity": "HIGH",
                "evidence": {
                    "penalty_pct": penalty,
                    "fiscal_year": data.get("fiscal_year"),
                },
            }
        return {
            "fires": False,
            "reason": "CMS_HRRP_BELOW_MAX",
            "evidence": {"penalty_pct": penalty},
        }

    # Multi-hospital system
    n_tracked = data.get("n_constituent_hospitals_tracked")
    n_at_max = data.get("n_at_max_penalty")
    avg = data.get("weighted_avg_penalty_pct")

    if n_tracked is None or n_tracked == 0:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    share_at_max = (n_at_max or 0) / n_tracked
    if share_at_max >= SYSTEM_SHARE_AT_MAX_THRESHOLD:
        return {
            "fires": True,
            "reason": "SYSTEM_HEAVILY_PENALIZED",
            "severity": "HIGH",
            "evidence": {
                "n_at_max": n_at_max,
                "n_tracked": n_tracked,
                "share_at_max": share_at_max,
                "weighted_avg_penalty_pct": avg,
            },
        }
    if avg is not None and avg >= SYSTEM_WEIGHTED_AVG_THRESHOLD:
        return {
            "fires": True,
            "reason": "SYSTEM_HIGH_AVG_PENALTY",
            "severity": "MEDIUM",
            "evidence": {
                "weighted_avg_penalty_pct": avg,
                "n_at_max": n_at_max,
                "n_tracked": n_tracked,
            },
        }
    return {
        "fires": False,
        "reason": "PENALTY_BELOW_THRESHOLD",
        "evidence": {"share_at_max": share_at_max, "weighted_avg_penalty_pct": avg},
    }
