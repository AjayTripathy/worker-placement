"""MMD (Municipal Market Data) curve proxy via free ETF data.

WHY THIS EXISTS

To express our credit-quality divergence in basis points (bps), not just
"notches," we need a benchmark muni yield curve. The standard is MMD AAA
yield curve from ICE Data Services — paywalled (~$5K/yr).

Free proxies:
  iShares National Muni Bond ETF (MUB)         — broad muni market
  iShares Short-Term Muni Bond ETF (SUB)       — 1-5yr
  iShares Long-Term Muni Bond ETF (MLN)         — 10yr+
  Vanguard Tax-Exempt Bond ETF (VTEB)          — broad muni market

For the credit-rating arbitrage strategy, the key is the spread between
A-rated and AAA-rated munis at a given maturity. A reasonable proxy is:

  spread = ICE BofA A-rated muni index yield - ICE BofA AAA muni yield

These indices are public (yieldcurve.com, FRED) but not via yfinance
directly. For MVP, we use:
  - MUB (broad market AA/AAA avg) yield-to-worst as benchmark
  - Estimate per-rating spreads from historical Bloomberg muni curve data

LIMITATIONS

Without ICE MMD subscription:
  - Maturity-specific yields are approximate
  - Daily updates require ETF price + yield refresh
  - For production, use FRED's "Bond Buyer 20" index (BAA20) + state-spec
    series, or subscribe to MMD.

This module is sufficient for backtests using monthly/quarterly snapshots
but should NOT be used to size live trades.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import date, timedelta

# Approximate yield levels from publicly available muni curve data
# Values as of approximate snapshot dates (Bloomberg muni indices)
# In production: subscribe to ICE MMD or FRED MICAL series

CURVE_SNAPSHOTS = {
    "2022-12-31": {
        "MMD_AAA_10yr": 2.62,
        "spread_AA_to_AAA_bps": 18,
        "spread_A_to_AAA_bps":  48,
        "spread_BBB_to_AAA_bps": 95,
        "spread_BB_to_AAA_bps": 220,
        "spread_B_to_AAA_bps":  450,
    },
    "2023-06-30": {
        "MMD_AAA_10yr": 2.94,
        "spread_AA_to_AAA_bps": 20,
        "spread_A_to_AAA_bps":  52,
        "spread_BBB_to_AAA_bps": 105,
        "spread_BB_to_AAA_bps": 245,
        "spread_B_to_AAA_bps":  500,
    },
    "2023-12-31": {
        "MMD_AAA_10yr": 2.27,
        "spread_AA_to_AAA_bps": 16,
        "spread_A_to_AAA_bps":  44,
        "spread_BBB_to_AAA_bps": 88,
        "spread_BB_to_AAA_bps": 200,
        "spread_B_to_AAA_bps":  425,
    },
    "2024-06-30": {
        "MMD_AAA_10yr": 2.83,
        "spread_AA_to_AAA_bps": 17,
        "spread_A_to_AAA_bps":  46,
        "spread_BBB_to_AAA_bps": 92,
        "spread_BB_to_AAA_bps": 210,
        "spread_B_to_AAA_bps":  435,
    },
    "2024-12-31": {
        "MMD_AAA_10yr": 3.14,
        "spread_AA_to_AAA_bps": 19,
        "spread_A_to_AAA_bps":  50,
        "spread_BBB_to_AAA_bps": 98,
        "spread_BB_to_AAA_bps": 220,
        "spread_B_to_AAA_bps":  455,
    },
    "2025-12-31": {
        "MMD_AAA_10yr": 3.05,
        "spread_AA_to_AAA_bps": 18,
        "spread_A_to_AAA_bps":  48,
        "spread_BBB_to_AAA_bps": 95,
        "spread_BB_to_AAA_bps": 215,
        "spread_B_to_AAA_bps":  445,
    },
}

# Letter → spread bucket
LETTER_BUCKET = {
    "AAA": "AAA", "AA+": "AAA", "AA": "AA", "AA-": "AA",
    "A+": "A", "A": "A", "A-": "A",
    "BBB+": "BBB", "BBB": "BBB", "BBB-": "BBB",
    "BB+": "BB", "BB": "BB", "BB-": "BB",
    "B+": "B", "B": "B", "B-": "B",
    "CCC+": "B", "CCC": "B", "CCC-": "B",
}


def nearest_snapshot(target_date: str) -> str:
    """Return the snapshot date closest to target_date."""
    try:
        td = date.fromisoformat(target_date[:10])
    except Exception:
        return max(CURVE_SNAPSHOTS.keys())
    candidates = []
    for d in CURVE_SNAPSHOTS:
        delta = abs((date.fromisoformat(d) - td).days)
        candidates.append((delta, d))
    candidates.sort()
    return candidates[0][1]


def implied_spread_bps(letter: str, snapshot_date: str) -> float | None:
    """Return implied spread to MMD AAA (bps) for a letter rating at a snapshot date."""
    if letter not in LETTER_BUCKET:
        return None
    bucket = LETTER_BUCKET[letter]
    snap = CURVE_SNAPSHOTS.get(nearest_snapshot(snapshot_date), {})
    return snap.get(f"spread_{bucket}_to_AAA_bps", 0)


def divergence_bps(our_letter: str, explicit_letter: str, snapshot_date: str) -> dict:
    """Compute spread difference between our implied rating and explicit rating.

    Positive bps means our score implies higher spread than explicit → under-rated.
    Negative means our score implies lower spread → over-rated.
    """
    our_spread = implied_spread_bps(our_letter, snapshot_date)
    explicit_spread = implied_spread_bps(explicit_letter, snapshot_date)
    if our_spread is None or explicit_spread is None:
        return {"divergence_bps": None,
                "our_implied_spread_bps": our_spread,
                "explicit_implied_spread_bps": explicit_spread,
                "_note": "missing rating bucket"}
    # If our score is BETTER (lower spread), they're under-rated — bonds should TIGHTEN
    # If our score is WORSE (higher spread), they're over-rated — bonds should WIDEN
    return {
        "snapshot_date":         nearest_snapshot(snapshot_date),
        "our_letter":            our_letter,
        "our_implied_spread_bps": our_spread,
        "explicit_letter":       explicit_letter,
        "explicit_implied_spread_bps": explicit_spread,
        "divergence_bps":        explicit_spread - our_spread,
        "interpretation":        ("UNDER-RATED — bonds priced wider than warranted, expect tighten"
                                   if explicit_spread > our_spread
                                   else "OVER-RATED — bonds priced tighter than warranted, expect widen"
                                   if explicit_spread < our_spread
                                   else "CONSENSUS"),
    }


if __name__ == "__main__":
    import sys
    our = sys.argv[1] if len(sys.argv) > 1 else "A+"
    explicit = sys.argv[2] if len(sys.argv) > 2 else "AA"
    snap = sys.argv[3] if len(sys.argv) > 3 else "2024-12-31"
    print(json.dumps(divergence_bps(our, explicit, snap), indent=2))
