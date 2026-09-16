"""Share-count drift detector — silent dilution telegraph.

WHY THIS EXISTS

ATM (at-the-market) equity offerings and quiet S-3 issuance show up as
share-count drift before they're called out in earnings narratives.
For dev-stage and stressed issuers, sustained share-count drift >10%/yr
is the surest signal that the company is funding itself by selling
equity into weakness.

INPUTS (via xbrl_panel)

  Diluted share count (preferred — captures effective dilution):
    us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding |
    us-gaap:WeightedAverageNumberOfSharesOutstandingBasic
  Common shares issued (stock-concept cross-check):
    us-gaap:CommonStockSharesIssued |
    us-gaap:CommonStockSharesOutstanding

OUTPUT

  signal: STABLE | MODEST | DILUTING | SEVERE_DILUTION | UNVERIFIABLE
  metrics: {shares_yoy_pct, shares_2y_pct, latest_shares}

THRESHOLDS (annualized share count growth)

  < 2%   → STABLE
  2-5%   → MODEST (normal SBC vesting)
  5-15%  → DILUTING (above-trend; likely ATM or secondary)
  > 15%  → SEVERE_DILUTION (emergency raise pattern)
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Share-count drift >10%/yr detection; silent ATM/S-3 dilution telegraph for any issuer.",
}

from typing import Any, Optional

from . import xbrl_panel


_SEVERITY_MAP = {
    "STABLE":           "PASS",
    "MODEST":           "PASS",
    "DILUTING":         "MODERATE_UNDERDELIVERY",
    "SEVERE_DILUTION":  "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE":     "UNVERIFIABLE",
}

DILUTED_TAGS = (
    "us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding",
    "us-gaap:WeightedAverageNumberOfSharesOutstandingBasic",
)
ISSUED_TAGS = (
    "us-gaap:CommonStockSharesIssued",
    "us-gaap:CommonStockSharesOutstanding",
)


def _latest(series: list[dict]) -> Optional[float]:
    return series[-1].get("val") if series else None


def _value_n_quarters_ago(quarterly: list[dict], n: int) -> Optional[float]:
    if len(quarterly) < n + 1:
        return None
    return quarterly[-(n + 1)].get("val")


def _pct_change(now: Optional[float], then: Optional[float]) -> Optional[float]:
    if now is None or then is None or then == 0:
        return None
    return 100.0 * (now - then) / then


def query_share_count_drift(cik: str, cutoff_date: str) -> dict[str, Any]:
    p = xbrl_panel.panel(
        cik,
        tags=[DILUTED_TAGS, ISSUED_TAGS],
        cutoff_date=cutoff_date,
        units_priority=["shares", "pure"],
    )
    if "error" in p:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": p["error"]}

    tags = p.get("tags") or {}
    diluted_q = xbrl_panel.quarterly_series(tags.get(DILUTED_TAGS[0], []))
    issued_q  = xbrl_panel.quarterly_series(tags.get(ISSUED_TAGS[0], []))

    # Prefer issued-shares series (stock concept) for drift; fall back to diluted (flow).
    series = issued_q if issued_q else diluted_q
    label = "common_shares_issued" if issued_q else "diluted_weighted_avg"

    if not series:
        return {
            "cik": p.get("cik"),
            "signal": "UNVERIFIABLE",
            "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": "No share-count facts available.",
            "missing_tags": p.get("missing_tags"),
        }

    latest = _latest(series)
    one_year_ago = _value_n_quarters_ago(series, 4)
    two_years_ago = _value_n_quarters_ago(series, 8)

    yoy_pct = _pct_change(latest, one_year_ago)
    twoy_pct = _pct_change(latest, two_years_ago)

    if yoy_pct is None:
        signal = "UNVERIFIABLE"
    elif yoy_pct < 2:
        signal = "STABLE"
    elif yoy_pct < 5:
        signal = "MODEST"
    elif yoy_pct < 15:
        signal = "DILUTING"
    else:
        signal = "SEVERE_DILUTION"

    direction = (
        "positive" if signal in ("STABLE", "MODEST")
        else "negative" if signal in ("DILUTING", "SEVERE_DILUTION")
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
            "series_used":         label,
            "latest_shares":       latest,
            "shares_yoy_pct":      round(yoy_pct, 2) if yoy_pct is not None else None,
            "shares_2y_pct":       round(twoy_pct, 2) if twoy_pct is not None else None,
        },
        "_note": (
            f"{label} {latest:,.0f}; YoY {yoy_pct:+.1f}%"
            + (f", 2y {twoy_pct:+.1f}%" if twoy_pct is not None else "")
            if yoy_pct is not None
            else "Insufficient history for YoY drift."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001507605"  # MARA — known diluter
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_share_count_drift(cik, cutoff), indent=2, default=str))
