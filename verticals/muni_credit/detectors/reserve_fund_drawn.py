"""Land-secured (CFD) reserve-fund-drawn detector.

FIRES when bond reserve fund balance has been drawn down to pay debt service
in the last 12 months, OR is currently below the reserve requirement, OR a
default has been filed.

Why predictive: reserve draw = the bond's last layer of self-protection has
been breached. CDIAC requires 10-day notification of any draw. 8 draws across
1,829 CA CFDs in RY 2023-24 (0.44%) — extremely rare, very high precision
when it fires.

Public data: CDIAC YFSR `Reserve Fund` vs `Reserve Fund Minimum Balance` +
CDIAC Default & Draw on Reserve database (separate filing).

CAVEAT: some CFDs use surety bonds rather than cash-funded reserves. In that
case YFSR `Reserve Fund Balance` will be $0 which is NORMAL; the detector
must not fire on these. Check `reserve_type` field if known.

Data shape:
  {
    "drawn_in_last_12mo": true,
    "default_in_last_12mo": true,
    "default_amount_usd": 3867139,
    "default_date": "2024-09-01",
    "reserve_balance_usd": 0,
    "reserve_minimum_usd": 3500000,
    "reserve_type": "cash",  # or "surety" — if surety, skip balance-check arm
    "as_of_date": "2024-12-31",
    "source": "CDIAC Default Reports",
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
    "summary": "Land-secured (CFD) reserve-fund-drawn detector.",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    drawn = data.get("drawn_in_last_12mo")
    defaulted = data.get("default_in_last_12mo")
    reserve_balance = data.get("reserve_balance_usd")
    reserve_min = data.get("reserve_minimum_usd")
    reserve_type = (data.get("reserve_type") or "cash").lower()

    # Check shortfall only for cash reserves (surety reserves show $0 as normal)
    shortfall = False
    if reserve_type == "cash" and isinstance(reserve_balance, (int, float)) and isinstance(reserve_min, (int, float)):
        shortfall = reserve_balance < reserve_min * 0.95

    if drawn is None and defaulted is None and reserve_balance is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if defaulted:
        return {
            "fires": True,
            "reason": "DEFAULT_FILED",
            "severity": "RED",
            "evidence": {
                "default_amount_usd": data.get("default_amount_usd"),
                "default_date": data.get("default_date"),
            },
        }
    if drawn:
        return {
            "fires": True,
            "reason": "RESERVE_DRAWN",
            "severity": "HIGH",
            "evidence": {
                "as_of_date": data.get("as_of_date"),
            },
        }
    if shortfall:
        return {
            "fires": True,
            "reason": "RESERVE_BELOW_MINIMUM",
            "severity": "HIGH",
            "evidence": {
                "reserve_balance_usd": reserve_balance,
                "reserve_minimum_usd": reserve_min,
            },
        }
    return {
        "fires": False,
        "reason": "RESERVE_INTACT",
        "evidence": {"reserve_balance_usd": reserve_balance, "reserve_minimum_usd": reserve_min},
    }
