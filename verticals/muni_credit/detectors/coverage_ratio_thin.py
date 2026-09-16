"""Land-secured (CFD) debt-service coverage thin detector.

FIRES when collected special-tax revenue / annual debt service < 1.10x.
Severity HIGH at <1.00x (revenue insufficient to cover debt service).

Why predictive: most CFDs are structured at 1.10x minimum coverage. Collapse
below = imminent reserve draw. Note this uses COLLECTED tax (= due × (1 -
delinquency)) not just billed — this is what materially flows to bondholders.

Public data: derived from CDIAC YFSR (taxes due) + CDA (debt service schedule)
OR pulled directly from CDA. Mild Teeter Plan distortion — but Mello-Roos
taxes are typically Teeter-excluded.

Data shape:
  {
    "annual_tax_revenue_collected_usd": 4500000,
    "annual_debt_service_usd": 4200000,
    "coverage_ratio": 1.07,
    "as_of_date": "2024-06-30",
    "source": "CDA + YFSR",
    "confidence": "MEDIUM"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["land_secured_district"],
    "asset_classes": ["ca_mello_roos_cfd", "ca_cfd_muni", "ca_1915_act_assessment_bonds"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Land-secured (CFD) debt-service coverage thin detector.",
}

COVERAGE_THRESHOLD = 1.10
COVERAGE_DSCR_FAIL = 1.00


def evaluate(obligor_name: str, data: dict) -> dict:
    cov = data.get("coverage_ratio")
    rev = data.get("annual_tax_revenue_collected_usd")
    ds = data.get("annual_debt_service_usd")

    if not isinstance(cov, (int, float)):
        cov = None
    if not isinstance(rev, (int, float)):
        rev = None
    if not isinstance(ds, (int, float)):
        ds = None

    if cov is None and rev is not None and ds:
        cov = rev / ds

    if cov is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if cov < COVERAGE_DSCR_FAIL:
        severity = "RED"
        reason = "DSCR_BELOW_ONE"
    elif cov < COVERAGE_THRESHOLD:
        severity = "HIGH"
        reason = "DSCR_THIN"
    else:
        return {
            "fires": False,
            "reason": "DSCR_ADEQUATE",
            "evidence": {"coverage_ratio": round(cov, 3)},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "coverage_ratio": round(cov, 3),
            "annual_tax_revenue_collected_usd": rev,
            "annual_debt_service_usd": ds,
            "threshold": COVERAGE_THRESHOLD,
        },
    }
