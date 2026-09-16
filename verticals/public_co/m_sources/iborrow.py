"""
iborrowdesk.com — public scrape of Interactive Brokers daily securities-
lending data. Indicative borrow fee (annualized %) and shares-available
inventory at IBKR. Most other broker-dealers track IBKR loosely.

API: https://iborrowdesk.com/api/ticker/<TICKER>
Auth: none
Cost: free
Caveats:
  - Data is IBKR-specific; other brokers can have different fees / borrow
    availability (Prime Brokerage rates can be lower for institutional
    accounts; retail rates at other brokers can be higher).
  - "Available" is shares; multiply by price for $-availability.
  - "fee" is annualized %.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "m_source",
    "summary": "IBKR securities-lending borrow fee / availability via iborrowdesk; positioning plumbing for any ticker.",
}

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 Signal OS Research backtest@signalos.local"}


def get_borrow_rate(ticker: str) -> dict:
    """Return latest IBKR borrow fee + availability for a ticker.

    Returns:
      {
        "ticker":            "IREN",
        "latest_date":       "2026-05-16",
        "fee_pct":           0.50,            # annualized %
        "available_shares":  2_600_000,
        "rebate_pct":        3.80,
        "data_points":       365,             # how many daily samples we have
        "fee_30d_avg":       0.52,            # 30-day moving avg of fee
        "fee_30d_max":       1.10,
        "fee_trend":         "stable" | "rising" | "falling",
      }
    """
    url = f"https://iborrowdesk.com/api/ticker/{ticker.upper()}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            return {"ticker": ticker, "error": f"status_{r.status_code}"}
        j = r.json()
    except Exception as e:
        return {"ticker": ticker, "error": f"http: {e}"}

    daily = j.get("daily") or []
    if not daily:
        return {"ticker": ticker, "error": "no_data"}

    latest = daily[-1]
    last_30 = [d for d in daily[-30:] if d.get("fee") is not None]
    fees_30 = [d["fee"] for d in last_30]
    fee_30_avg = sum(fees_30) / len(fees_30) if fees_30 else None
    fee_30_max = max(fees_30) if fees_30 else None

    trend = "stable"
    if len(fees_30) >= 20:
        early = sum(fees_30[:5]) / 5
        late  = sum(fees_30[-5:]) / 5
        if late > early * 1.5:
            trend = "rising"
        elif late < early * 0.67:
            trend = "falling"

    return {
        "ticker":           ticker.upper(),
        "latest_date":      latest.get("date"),
        "fee_pct":          latest.get("fee"),
        "available_shares": latest.get("available"),
        "rebate_pct":       latest.get("rebate"),
        "data_points":      len(daily),
        "fee_30d_avg":      round(fee_30_avg, 4) if fee_30_avg is not None else None,
        "fee_30d_max":      round(fee_30_max, 4) if fee_30_max is not None else None,
        "fee_trend":        trend,
    }


def get_many(tickers: list[str]) -> dict[str, dict]:
    out = {}
    for t in tickers:
        out[t.upper()] = get_borrow_rate(t)
    return out


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(get_borrow_rate(sys.argv[1]), indent=2, default=str))
    else:
        print(json.dumps(get_borrow_rate("IREN"), indent=2, default=str))
