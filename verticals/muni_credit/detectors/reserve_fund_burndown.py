"""Land-secured (CFD) reserve-fund-burndown detector.

FIRES when reserve fund balance has DECLINED meaningfully over the last 1-2
years without a corresponding default event yet. Catches distress 2-3 years
BEFORE bondholders see a default — the missing leading-indicator detector
identified by the validation pass on Northstar CSD CFD 1 (3 reserve draws
in single year, no bondholder default yet).

Severity: MEDIUM at >10% YoY decline; HIGH at >25% YoY decline; RED at
>50% YoY decline. Distinct from reserve_fund_drawn which fires on actual
draws — this fires on the velocity of decline before a draw.

Why predictive: reserve burndown is the most sensitive leading indicator.
By the time a draw is filed with CDIAC, the cash flow stress has been
building for 12-24 months. Watching balance velocity captures the slope.

Public data: CDIAC YFSR `Reserve Fund Balance` field, year-over-year.

Data shape:
  {
    "reserve_balance_current_usd": 2100000,
    "reserve_balance_t1_usd": 3200000,
    "reserve_balance_t2_usd": 3500000,
    "reserve_minimum_usd": 3500000,
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
    "summary": "Land-secured (CFD) reserve-fund-burndown detector.",
}

BURNDOWN_MEDIUM = 0.10
BURNDOWN_HIGH = 0.25
BURNDOWN_RED = 0.50


def evaluate(obligor_name: str, data: dict) -> dict:
    cur = data.get("reserve_balance_current_usd")
    t1 = data.get("reserve_balance_t1_usd")
    t2 = data.get("reserve_balance_t2_usd")
    minimum = data.get("reserve_minimum_usd")

    if not isinstance(cur, (int, float)) or not isinstance(t1, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    # Skip if reserve was already zero (use reserve_fund_drawn instead)
    if t1 <= 0:
        return {"fires": False, "reason": "NO_PRIOR_BALANCE", "evidence": {}}

    yoy_decline = (t1 - cur) / t1

    # Also check 2-year cumulative decline if t2 available
    cum_decline = None
    if isinstance(t2, (int, float)) and t2 > 0:
        cum_decline = (t2 - cur) / t2

    decline = max(yoy_decline, cum_decline or 0)

    if decline < BURNDOWN_MEDIUM:
        return {
            "fires": False,
            "reason": "RESERVE_STABLE",
            "evidence": {"yoy_decline_pct": round(yoy_decline * 100, 1)},
        }

    if decline >= BURNDOWN_RED:
        severity = "RED"
    elif decline >= BURNDOWN_HIGH:
        severity = "HIGH"
    else:
        severity = "MEDIUM"

    return {
        "fires": True,
        "reason": "RESERVE_BURNDOWN",
        "severity": severity,
        "evidence": {
            "reserve_balance_current_usd": cur,
            "reserve_balance_t1_usd": t1,
            "reserve_balance_t2_usd": t2,
            "yoy_decline_pct": round(yoy_decline * 100, 1),
            "cumulative_2yr_decline_pct": round((cum_decline or 0) * 100, 1),
            "below_minimum": isinstance(minimum, (int, float)) and cur < minimum,
        },
    }
