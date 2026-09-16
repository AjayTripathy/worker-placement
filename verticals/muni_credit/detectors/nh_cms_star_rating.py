"""Nursing home CMS 5-Star Rating detector.

FIRES when CMS overall star rating ≤ 2 (below average / much below average).

Why predictive: CMS 5-Star Rating is the composite quality measure that
directly affects:
  - Census (referral patterns from hospitals, ACOs, payers)
  - Medicare/Medicaid certification standing
  - Insurance contract eligibility
  - Litigation risk
  - Eventual financial distress

CMS Star Ratings change quarterly; persistent 1-2 star = structural
operational dysfunction. ~12-18 month lead time before muni rating action.

Public data: CMS Care Compare (downloadable CSV).
Update frequency: quarterly.

Data shape:
  {
    "overall_star_rating": 1,  # 1-5 stars
    "health_inspection_rating": 2,
    "staffing_rating": 1,
    "qm_rating": 3,
    "rating_date": "2024-Q4",
    "source_url": "https://www.medicare.gov/care-compare/...",
    "confidence": "HIGH"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["nursing_home_obligor", "ccrc_obligor"],
    "asset_classes": ["ca_nh_muni", "ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Nursing home CMS 5-Star Rating detector.",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    star = data.get("overall_star_rating")
    if star is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    try:
        star = int(star)
    except (ValueError, TypeError):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if star <= 2:
        return {
            "fires": True,
            "reason": "CMS_STAR_BELOW_AVERAGE",
            "severity": "HIGH" if star == 1 else "MEDIUM",
            "evidence": {
                "overall_star": star,
                "health_inspection": data.get("health_inspection_rating"),
                "staffing": data.get("staffing_rating"),
                "qm": data.get("qm_rating"),
                "rating_date": data.get("rating_date"),
            },
        }
    return {
        "fires": False,
        "reason": "CMS_STAR_AVERAGE_OR_BETTER",
        "evidence": {"overall_star": star},
    }
