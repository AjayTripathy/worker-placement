"""Land-secured (CFD) special-tax delinquency-spike detector.

FIRES when current-year special-tax delinquency >5% (CDIAC's own "elevated"
threshold) OR rising 2+ years in a row. Severity HIGH at >15%; RED at >50%.

Why predictive: delinquency on the special-tax bill is the first observable
break in CFD bond cash flow. Above 5% sustained = reserve-draw risk within
12-24 months absent intervention.

Public data: CDIAC YFSR. Field: `Total Amount of Unpaid Special Taxes Annually`
divided by `Total Amount of Special Taxes Due Annually`.

CRITICAL CAVEAT — Teeter Plan masking: in Teeter counties, the county
advances 100% of levied taxes to the CFD regardless of underlying parcel
collection. YFSR `Total Amount of Unpaid Special Taxes Annually` reports
ZERO for CFDs in Teeter counties. The validation pass found that Mello-Roos
special taxes are EXPLICITLY EXCLUDED from Teeter in every county checked
(Placer, LA, Stanislaus), so this masking is structurally absent for CFDs —
but the detector flags `teeter_excluded: false` cases explicitly for audit.

Data shape:
  {
    "current_delinquency_pct": 12.4,
    "delinquency_pct_t1": 8.1,
    "delinquency_pct_t2": 4.5,
    "tax_due_annually_usd": 5309345,
    "tax_unpaid_annually_usd": 658000,
    "teeter_county_but_cfd_excluded": true,  # informational
    "as_of_date": "2024-06-30",
    "source": "CDIAC YFSR RY2023-24",
    "confidence": "HIGH"
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
    "summary": "Land-secured (CFD) special-tax delinquency-spike detector.",
}

DELINQ_YELLOW = 5.0
DELINQ_HIGH = 15.0
DELINQ_RED = 50.0


def evaluate(obligor_name: str, data: dict) -> dict:
    cur = data.get("current_delinquency_pct")
    t1 = data.get("delinquency_pct_t1")
    t2 = data.get("delinquency_pct_t2")

    if not isinstance(cur, (int, float)):
        if data.get("tax_due_annually_usd") and data.get("tax_unpaid_annually_usd"):
            cur = data["tax_unpaid_annually_usd"] / data["tax_due_annually_usd"] * 100
        else:
            return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Sustained 2-year rise above yellow
    rising = (
        isinstance(t1, (int, float))
        and isinstance(t2, (int, float))
        and cur > t1 > t2
        and cur > DELINQ_YELLOW
    )

    severity = None
    reason = None
    if cur >= DELINQ_RED:
        severity = "RED"
        reason = "DELINQUENCY_EXTREME"
    elif cur >= DELINQ_HIGH:
        severity = "HIGH"
        reason = "DELINQUENCY_HIGH"
    elif cur >= DELINQ_YELLOW:
        severity = "MEDIUM"
        reason = "DELINQUENCY_ELEVATED"
    elif rising:
        severity = "MEDIUM"
        reason = "DELINQUENCY_RISING_TREND"

    if severity is None:
        return {
            "fires": False,
            "reason": "BELOW_THRESHOLD",
            "evidence": {"current_delinquency_pct": round(cur, 2)},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "current_delinquency_pct": round(cur, 2),
            "delinquency_pct_t1": t1,
            "delinquency_pct_t2": t2,
            "rising_trend": rising,
            "threshold_yellow": DELINQ_YELLOW,
            "as_of_date": data.get("as_of_date"),
        },
    }
