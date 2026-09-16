"""Working-capital drift detector — DSI / DSO / DPO inflection.

WHY THIS EXISTS

Inventory overhang is the canonical small-cap catastrophe pattern:
  - AAP (Advance Auto Parts) — DSI bled from ~165 to ~210 days before
    the 2023 guidance reset and >50% drawdown
  - VFC / KTB style apparel rolloffs — inventory days swelling 30% YoY
    while revenue flatlined
  - Semis cycle write-downs — inventory days that lead the revenue cliff
  - Builders' spec-home overhang — inventory/revenue rising into rate hikes

DSO bleed (receivables stretching) and DPO stretch (paying suppliers
slower) are corroborating signals — DPO stretch concurrent with a
covenant amendment is especially predictive of distress.

INPUTS (XBRL tags pulled via xbrl_panel)

  Inventory:
    us-gaap:InventoryNet | us-gaap:Inventory
  Receivables:
    us-gaap:AccountsReceivableNetCurrent
  Payables:
    us-gaap:AccountsPayableCurrent | us-gaap:AccountsPayable
  Revenue:
    us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
    us-gaap:Revenues | us-gaap:SalesRevenueNet
  COGS:
    us-gaap:CostOfGoodsAndServicesSold | us-gaap:CostOfRevenue |
    us-gaap:CostOfGoodsSold

OUTPUT

  signal: CLEAN | DRIFTING | SEVERE | UNVERIFIABLE
  metrics: {dsi_latest, dsi_yoy_delta_days, dso_latest, dso_yoy_delta_days,
            dpo_latest, dpo_yoy_delta_days}

THRESHOLDS

  DSI YoY delta:
    < +5 days   → CLEAN
    +5 to +20   → DRIFTING
    > +20 days  → SEVERE
  DSO YoY delta:
    < +3 days   → CLEAN
    +3 to +10   → DRIFTING
    > +10 days  → SEVERE
  DPO YoY delta (positive = stretching, paying slower):
    < +5 days   → CLEAN
    +5 to +15   → DRIFTING
    > +15 days  → SEVERE

Worst tier across the three axes wins. Tiered with no peer benchmarks
because the YoY delta is self-normalizing — a stable company has
single-digit deltas in any sector. The SEVERE cutoffs are calibrated
against AAP, VFC, and BBBY pre-blowup observations.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "DSI/DSO/DPO inflection detection; inventory-days swell leads the guidance reset.",
}

from typing import Any, Optional

from . import xbrl_panel


_TIER_RANK = {"CLEAN": 0, "DRIFTING": 1, "SEVERE": 2, "UNVERIFIABLE": -1}
_TIER_BY_RANK = {0: "CLEAN", 1: "DRIFTING", 2: "SEVERE"}

# Map to composite-recompute severity vocab
_SEVERITY_MAP = {
    "CLEAN":         "PASS",
    "DRIFTING":      "MODERATE_UNDERDELIVERY",
    "SEVERE":        "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE":  "UNVERIFIABLE",
}

_THRESH = {
    "dsi": (5, 20),
    "dso": (3, 10),
    "dpo": (5, 15),
}

INVENTORY_TAGS = ("us-gaap:InventoryNet", "us-gaap:Inventory")
AR_TAGS        = ("us-gaap:AccountsReceivableNetCurrent",
                  "us-gaap:ReceivablesNetCurrent")
AP_TAGS        = ("us-gaap:AccountsPayableCurrent", "us-gaap:AccountsPayable")
REVENUE_TAGS   = ("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
                  "us-gaap:Revenues", "us-gaap:SalesRevenueNet")
COGS_TAGS      = ("us-gaap:CostOfGoodsAndServicesSold",
                  "us-gaap:CostOfRevenue", "us-gaap:CostOfGoodsSold")


def _classify(value: Optional[float], thresholds: tuple[float, float]) -> str:
    if value is None:
        return "UNVERIFIABLE"
    drift_lo, severe = thresholds
    if value < drift_lo:
        return "CLEAN"
    if value < severe:
        return "DRIFTING"
    return "SEVERE"


def _latest_value(series: list[dict]) -> Optional[float]:
    if not series:
        return None
    return series[-1].get("val")


def _value_one_year_ago(quarterly: list[dict]) -> Optional[float]:
    """Quarterly series — return value from 4 quarters back."""
    if len(quarterly) < 5:
        return None
    return quarterly[-5].get("val")


def _trailing_4q_sum(quarterly: list[dict]) -> Optional[float]:
    """Sum the most recent 4 quarterly observations.

    Caller is responsible for ensuring this is appropriate (i.e., revenue
    or COGS — flow concepts, not stock concepts like inventory).
    Companyfacts revenue facts are usually presented as period-cumulative
    via the FY observation, but the Q1/Q2/Q3/Q4 split for trailing-twelve
    requires the quarterly values. We use the simpler approximation:
    sum the last 4 quarterly observations.
    """
    if len(quarterly) < 4:
        return None
    vals = [o.get("val") for o in quarterly[-4:]]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def _ttm_one_year_ago(quarterly: list[dict]) -> Optional[float]:
    if len(quarterly) < 8:
        return None
    vals = [o.get("val") for o in quarterly[-8:-4]]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def query_working_capital_drift(cik: str, cutoff_date: str) -> dict[str, Any]:
    """Compute DSI/DSO/DPO YoY drift signal.

    Returns:
      {
        "cik": "...",
        "signal": CLEAN | DRIFTING | SEVERE | UNVERIFIABLE,
        "severity": composite-vocab string,
        "direction": "negative" if SEVERE/DRIFTING else "positive" if CLEAN,
        "metrics": {dsi_latest, dsi_yoy_delta_days, ...},
        "_note": human explainer,
      }
    """
    p = xbrl_panel.panel(
        cik,
        tags=[INVENTORY_TAGS, AR_TAGS, AP_TAGS, REVENUE_TAGS, COGS_TAGS],
        cutoff_date=cutoff_date,
    )
    if "error" in p:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": p["error"]}

    tags = p.get("tags") or {}
    inv_q = xbrl_panel.quarterly_series(tags.get(INVENTORY_TAGS[0], []))
    ar_q  = xbrl_panel.quarterly_series(tags.get(AR_TAGS[0], []))
    ap_q  = xbrl_panel.quarterly_series(tags.get(AP_TAGS[0], []))
    rev_q = xbrl_panel.quarterly_series(tags.get(REVENUE_TAGS[0], []))
    cog_q = xbrl_panel.quarterly_series(tags.get(COGS_TAGS[0], []))

    # Latest TTM revenue / COGS for denominator
    ttm_rev_now  = _trailing_4q_sum(rev_q)
    ttm_rev_prev = _ttm_one_year_ago(rev_q)
    ttm_cog_now  = _trailing_4q_sum(cog_q)
    ttm_cog_prev = _ttm_one_year_ago(cog_q)

    # DSI: inventory / (ttm_cogs / 365)
    def _dsi(inv_val, ttm_cog):
        if inv_val is None or not ttm_cog:
            return None
        return inv_val / (ttm_cog / 365.0)

    # DSO: receivables / (ttm_revenue / 365)
    def _dso(ar_val, ttm_rev):
        if ar_val is None or not ttm_rev:
            return None
        return ar_val / (ttm_rev / 365.0)

    # DPO: payables / (ttm_cogs / 365)
    def _dpo(ap_val, ttm_cog):
        if ap_val is None or not ttm_cog:
            return None
        return ap_val / (ttm_cog / 365.0)

    dsi_now  = _dsi(_latest_value(inv_q), ttm_cog_now)
    dsi_prev = _dsi(_value_one_year_ago(inv_q), ttm_cog_prev)
    dso_now  = _dso(_latest_value(ar_q), ttm_rev_now)
    dso_prev = _dso(_value_one_year_ago(ar_q), ttm_rev_prev)
    dpo_now  = _dpo(_latest_value(ap_q), ttm_cog_now)
    dpo_prev = _dpo(_value_one_year_ago(ap_q), ttm_cog_prev)

    def _delta(now, prev):
        if now is None or prev is None:
            return None
        return now - prev

    dsi_delta = _delta(dsi_now, dsi_prev)
    dso_delta = _delta(dso_now, dso_prev)
    dpo_delta = _delta(dpo_now, dpo_prev)

    dsi_tier = _classify(dsi_delta, _THRESH["dsi"])
    dso_tier = _classify(dso_delta, _THRESH["dso"])
    dpo_tier = _classify(dpo_delta, _THRESH["dpo"])

    ranks = [_TIER_RANK[t] for t in (dsi_tier, dso_tier, dpo_tier)
             if _TIER_RANK[t] >= 0]
    if not ranks:
        signal = "UNVERIFIABLE"
    else:
        signal = _TIER_BY_RANK[max(ranks)]

    direction = (
        "negative" if signal in ("SEVERE", "DRIFTING")
        else "positive" if signal == "CLEAN"
        else "neutral"
    )

    return {
        "cik": p.get("cik"),
        "entity_name": p.get("entity_name"),
        "cutoff_date": cutoff_date,
        "signal": signal,
        "severity": _SEVERITY_MAP[signal],
        "direction": direction,
        "metrics": {
            "dsi_latest_days":   round(dsi_now, 1) if dsi_now is not None else None,
            "dsi_yoy_delta_days": round(dsi_delta, 1) if dsi_delta is not None else None,
            "dsi_tier":          dsi_tier,
            "dso_latest_days":   round(dso_now, 1) if dso_now is not None else None,
            "dso_yoy_delta_days": round(dso_delta, 1) if dso_delta is not None else None,
            "dso_tier":          dso_tier,
            "dpo_latest_days":   round(dpo_now, 1) if dpo_now is not None else None,
            "dpo_yoy_delta_days": round(dpo_delta, 1) if dpo_delta is not None else None,
            "dpo_tier":          dpo_tier,
        },
        "_note": (
            f"DSI {dsi_now:.0f}d ({dsi_delta:+.0f} YoY); "
            f"DSO {dso_now:.0f}d ({dso_delta:+.0f} YoY); "
            f"DPO {dpo_now:.0f}d ({dpo_delta:+.0f} YoY)."
            if all(v is not None for v in (dsi_now, dsi_delta, dso_now, dso_delta, dpo_now, dpo_delta))
            else "Partial XBRL coverage; some metrics UNVERIFIABLE."
        ),
        "missing_tags": p.get("missing_tags"),
    }


if __name__ == "__main__":
    import json
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001158449"  # AAP — known inventory blowup
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2023-08-15"
    print(json.dumps(query_working_capital_drift(cik, cutoff), indent=2, default=str))
