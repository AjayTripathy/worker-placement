"""CCRC-specific days cash on hand detector.

FIRES when days cash on hand < 200 days. CCRCs need higher cash floors than
hospitals because:
  - Refundable entrance fees create contingent liability that must be
    matched with liquid reserves
  - State CCRC regulators (CA DSS, OR DCBS, etc.) impose minimum liquid-
    reserve requirements
  - Refund obligations during occupancy turnover are significant

Industry-typical CCRC days cash: 300-500. Below 200 = material distress.

Lead time vs rating action: typically 6-12 months.
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["ccrc_obligor"],
    "asset_classes": ["ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "CCRC-specific days cash on hand detector.",
}

CRITICAL_DAYS_CASH = 200
WATCH_DAYS_CASH = 300


def evaluate(obligor_name: str, data: dict) -> dict:
    dcoh = data.get("days_cash_on_hand")
    if dcoh is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if dcoh < CRITICAL_DAYS_CASH:
        return {
            "fires": True,
            "reason": "CCRC_DAYS_CASH_CRITICAL",
            "severity": "HIGH",
            "evidence": {"days_cash": dcoh, "threshold": CRITICAL_DAYS_CASH},
        }
    if dcoh < WATCH_DAYS_CASH:
        return {
            "fires": False,
            "reason": "CCRC_DAYS_CASH_WATCH",
            "severity": "MEDIUM",
            "evidence": {"days_cash": dcoh, "threshold": WATCH_DAYS_CASH},
        }
    return {
        "fires": False,
        "reason": "CCRC_DAYS_CASH_HEALTHY",
        "evidence": {"days_cash": dcoh},
    }
