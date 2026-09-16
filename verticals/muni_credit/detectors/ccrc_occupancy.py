"""CCRC Independent Living occupancy detector.

FIRES when Independent Living (IL) occupancy < 85% — the leading indicator
of CCRC distress. IL units are the cash engine: entrance fees (large lump
sums) come from new IL residents. Persistent IL occupancy < 85% signals:
  - Market saturation
  - Lower-than-expected wave of new residents
  - Slowing entrance fee inflows → liquidity pressure
  - Eventual downgrade or covenant breach

Lead time vs rating action: typically 12-24 months.

Data shape:
  {
    "il_occupancy_pct": 82.5,  # current IL occupancy rate
    "al_occupancy_pct": 88.0,  # assisted living (less critical)
    "snf_occupancy_pct": 91.0,  # skilled nursing
    "fiscal_year": "FY2024",
    "source_url": "...",
    "confidence": "HIGH|MEDIUM|LOW"
  }
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
    "summary": "CCRC Independent Living occupancy detector.",
}

CRITICAL_IL_OCCUPANCY = 85.0  # below this, fire
WATCH_IL_OCCUPANCY = 90.0     # below this, warn


def evaluate(obligor_name: str, data: dict) -> dict:
    il = data.get("il_occupancy_pct")
    if il is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}
    if il < CRITICAL_IL_OCCUPANCY:
        return {
            "fires": True,
            "reason": "IL_OCCUPANCY_CRITICAL",
            "severity": "HIGH",
            "evidence": {
                "il_occupancy_pct": il,
                "threshold": CRITICAL_IL_OCCUPANCY,
                "al_occupancy_pct": data.get("al_occupancy_pct"),
                "snf_occupancy_pct": data.get("snf_occupancy_pct"),
            },
        }
    if il < WATCH_IL_OCCUPANCY:
        return {
            "fires": False,
            "reason": "IL_OCCUPANCY_WATCH",
            "severity": "MEDIUM",
            "evidence": {"il_occupancy_pct": il, "threshold": WATCH_IL_OCCUPANCY},
        }
    return {
        "fires": False,
        "reason": "IL_OCCUPANCY_HEALTHY",
        "evidence": {"il_occupancy_pct": il},
    }
