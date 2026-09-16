"""Executive turnover detector (multi-factor).

FIRES when BOTH the CEO and CFO have changed within the last 12 months
AND the obligor's days cash on hand is < 100.

Why predictive: Single C-suite changes happen routinely (retirement,
better offer). BOTH within 12 months at a financially-thin obligor is a
governance crisis signal — typically indicates board action in response
to operational/financial concerns the public hasn't seen yet.

Lead time vs rating action: typically 6-15 months. The board sees what
the agencies haven't yet — they're firing leadership before the numbers
catch up.

The DCOH < 100 filter is important: at large well-capitalized systems
(DCOH > 200), exec turnover may be strategic; at thin-cash obligors, it's
almost always crisis-driven.

Data shape:
  {
    "ceo_change_in_last_12mo": true,
    "ceo_change_date": "2025-03-15",
    "cfo_change_in_last_12mo": true,
    "cfo_change_date": "2024-11-20",
    "days_cash_on_hand": 67,
    "source_urls": [...]
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Executive turnover detector (multi-factor).",
}

DCOH_THRESHOLD = 100


def evaluate(obligor_name: str, data: dict) -> dict:
    ceo_changed = data.get("ceo_change_in_last_12mo")
    cfo_changed = data.get("cfo_change_in_last_12mo")
    dcoh = data.get("days_cash_on_hand")

    if ceo_changed is None or cfo_changed is None or dcoh is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if ceo_changed and cfo_changed and dcoh < DCOH_THRESHOLD:
        return {
            "fires": True,
            "reason": "CEO_CFO_TURNOVER_AT_THIN_CASH",
            "severity": "HIGH",
            "evidence": {
                "ceo_change_date": data.get("ceo_change_date"),
                "cfo_change_date": data.get("cfo_change_date"),
                "dcoh": dcoh,
                "dcoh_threshold": DCOH_THRESHOLD,
            },
        }
    return {
        "fires": False,
        "reason": ("BOTH_CHANGES_BUT_ADEQUATE_CASH" if (ceo_changed and cfo_changed)
                   else "PARTIAL_CHANGE_ONLY"),
        "evidence": {
            "ceo_changed": ceo_changed,
            "cfo_changed": cfo_changed,
            "dcoh": dcoh,
        },
    }
