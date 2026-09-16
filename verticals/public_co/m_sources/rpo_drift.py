"""SaaS Remaining-Performance-Obligation (RPO) drift detector.

WHY THIS EXISTS

For subscription/SaaS issuers, the most reliable forward indicator of
revenue trouble is RPO (remaining performance obligation) / current-RPO
growing slower than reported revenue. RPO captures committed contract
value not yet recognized; cRPO is the subset expected within 12 months.

When RPO YoY growth decelerates more than revenue YoY growth — or worse,
goes negative — the company is consuming bookings faster than it's
adding them. Twilio, Asana, ZScaler, MongoDB, and Atlassian have all
had clean RPO-inflection signals 1-3 quarters before guidance cuts.

INPUTS (via xbrl_panel)

  Total RPO:
    us-gaap:RevenueRemainingPerformanceObligation
  Revenue:
    us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax |
    us-gaap:Revenues
  (cRPO is rarely tagged as a discrete fact in companyfacts — most
   filers disclose it in narrative MD&A. We compute a deceleration
   signal from total RPO alone.)

OUTPUT

  signal: ACCELERATING | STABLE | DECELERATING | INVERTED | UNVERIFIABLE
  metrics: {rpo_yoy_pct, revenue_yoy_pct, decel_spread_pp}

THRESHOLDS

  decel_spread = revenue_yoy_pct - rpo_yoy_pct  (high = bookings underperforming sales)
  decel_spread < -5         → ACCELERATING (RPO outgrowing rev — healthy)
  -5 <= spread < 5          → STABLE
  5 <= spread < 15          → DECELERATING (warning)
  spread >= 15 OR rpo_yoy < 0 → INVERTED (the catastrophe pattern)

Only fires when issuer reports the RPO tag — non-SaaS filers won't,
which is fine. ~25-30 IJR names should have it (TECH_SOFTWARE_SERVICES
plus IT services where contracts are multi-year).
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["737"],
    "issuer_features": ["saas_subscription_model"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "SaaS RPO/cRPO growth vs revenue growth; committed-backlog deceleration leads revenue trouble.",
}

from typing import Any, Optional

from . import xbrl_panel


_SEVERITY_MAP = {
    "ACCELERATING":  "PASS",
    "STABLE":        "PASS",
    "DECELERATING":  "MODERATE_UNDERDELIVERY",
    "INVERTED":      "SEVERE_UNDERDELIVERY",
    "NOT_APPLICABLE": "PASS",
    "UNVERIFIABLE":  "UNVERIFIABLE",
}

RPO_TAGS = ("us-gaap:RevenueRemainingPerformanceObligation",)
REVENUE_TAGS = (
    "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "us-gaap:Revenues",
)


def _latest(series: list[dict]) -> Optional[float]:
    return series[-1].get("val") if series else None


def _value_n_q_ago(series: list[dict], n: int) -> Optional[float]:
    if len(series) < n + 1:
        return None
    return series[-(n + 1)].get("val")


def _ttm(quarterly: list[dict]) -> Optional[float]:
    if len(quarterly) < 4:
        return None
    vals = [o.get("val") for o in quarterly[-4:]]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def _ttm_prev(quarterly: list[dict]) -> Optional[float]:
    if len(quarterly) < 8:
        return None
    vals = [o.get("val") for o in quarterly[-8:-4]]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def _pct_change(now: Optional[float], then: Optional[float]) -> Optional[float]:
    if now is None or then is None or then == 0:
        return None
    return 100.0 * (now - then) / then


def query_rpo_drift(cik: str, cutoff_date: str) -> dict[str, Any]:
    p = xbrl_panel.panel(
        cik,
        tags=[RPO_TAGS, REVENUE_TAGS],
        cutoff_date=cutoff_date,
    )
    if "error" in p:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": p["error"]}

    tags = p.get("tags") or {}
    rpo_q = xbrl_panel.quarterly_series(tags.get(RPO_TAGS[0], []))
    rev_q = xbrl_panel.quarterly_series(tags.get(REVENUE_TAGS[0], []))

    if not rpo_q:
        # Non-SaaS — RPO tag not reported. Not a failure, just N/A.
        return {
            "cik": p.get("cik"),
            "entity_name": p.get("entity_name"),
            "cutoff_date": cutoff_date,
            "signal": "NOT_APPLICABLE",
            "severity": _SEVERITY_MAP["NOT_APPLICABLE"],
            "direction": "neutral",
            "metrics": {},
            "_note": "Issuer does not report us-gaap:RevenueRemainingPerformanceObligation; skip.",
        }

    rpo_now = _latest(rpo_q)
    rpo_prev = _value_n_q_ago(rpo_q, 4)
    rev_ttm_now = _ttm(rev_q)
    rev_ttm_prev = _ttm_prev(rev_q)

    rpo_yoy = _pct_change(rpo_now, rpo_prev)
    rev_yoy = _pct_change(rev_ttm_now, rev_ttm_prev)

    if rpo_yoy is None or rev_yoy is None:
        return {
            "cik": p.get("cik"),
            "entity_name": p.get("entity_name"),
            "signal": "UNVERIFIABLE",
            "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": "Insufficient history for YoY comparison.",
        }

    decel_spread = rev_yoy - rpo_yoy

    if rpo_yoy < 0:
        signal = "INVERTED"
    elif decel_spread >= 15:
        signal = "INVERTED"
    elif decel_spread >= 5:
        signal = "DECELERATING"
    elif decel_spread >= -5:
        signal = "STABLE"
    else:
        signal = "ACCELERATING"

    direction = (
        "positive" if signal == "ACCELERATING"
        else "negative" if signal in ("DECELERATING", "INVERTED")
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
            "rpo_latest_usd":     rpo_now,
            "rpo_yoy_pct":        round(rpo_yoy, 2),
            "revenue_ttm_usd":    rev_ttm_now,
            "revenue_yoy_pct":    round(rev_yoy, 2),
            "decel_spread_pp":    round(decel_spread, 2),
        },
        "_note": (
            f"RPO ${rpo_now/1e6:.0f}M (YoY {rpo_yoy:+.1f}%) vs "
            f"Rev TTM ${rev_ttm_now/1e6:.0f}M (YoY {rev_yoy:+.1f}%); "
            f"spread {decel_spread:+.1f}pp → {signal}."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001092699"  # SPSC
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_rpo_drift(cik, cutoff), indent=2, default=str))
