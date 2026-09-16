"""Tier 3 walk-forward — build the 2024-05-15 candidate pool.

Tests whether the Tier 1 in-cohort catastrophe-detection holds on a
DIFFERENT 12-month window where universe construction can't peek at
outcomes.

UNIVERSE construction (pure drawdown screen, point-in-time):
  - Start from union of: current SP600 enriched (~600 names) + Tier 1
    distressed cohort (32 removed names) — gives ~635 candidates with
    known CIKs and small-cap profile
  - For each, fetch yfinance OHLC 2023-05-01 → 2025-06-01
  - Compute at 2024-05-15:
      * trailing_52w_high = max close in 2023-05-15 → 2024-05-15
      * price_2024_05_15
      * drawdown_2024_05_15 = price/high - 1
      * price_2025_05_15  (or last available before delisting)
      * forward_return = price_2025/price_2024 - 1
  - Filter to drawdown <= -25%

Cutoff: 2024-05-15
Measurement: 2025-05-15

Output: candidate_pool.json (all priced) + candidate_pool_errors.json

Run:
    python3 verticals/public_co/data/_backtest/walk_forward_2024_05/build_candidate_pool.py
"""
import json
import time
import warnings
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf

warnings.filterwarnings("ignore")

HERE = Path(__file__).parent
PUBLIC_CO = HERE.parents[2]
SP600_PATH = PUBLIC_CO / "data" / "_smallcap_universe" / "sp600_enriched.json"
TIER1_TEST_SET = PUBLIC_CO / "data" / "_backtest" / "survivorship_2025_05" / "_unblinded" / "combined_test_set.json"

CUTOFF = date(2024, 5, 15)
MEASUREMENT = date(2025, 5, 15)
HISTORY_START = CUTOFF - timedelta(days=400)
HISTORY_END = MEASUREMENT + timedelta(days=14)

DRAWDOWN_FLOOR = -0.25  # keep only names worse than this


def nearest_close(history, target_date):
    target = target_date
    for _ in range(7):
        for idx, row in history.iterrows():
            if idx.date() == target:
                return float(row["Close"])
        target = target - timedelta(days=1)
    return None


def trailing_52w_high(history, target_date):
    start = target_date - timedelta(days=365)
    window = history[(history.index.date >= start) & (history.index.date <= target_date)]
    if window.empty:
        return None
    return float(window["Close"].max())


def fetch_one(ticker):
    try:
        t = yf.Ticker(ticker)
        h = t.history(start=HISTORY_START.isoformat(), end=HISTORY_END.isoformat(), auto_adjust=True)
    except Exception as e:
        return {"error": f"history_fetch: {e}"}
    if h is None or h.empty:
        return {"error": "no_history"}
    p_cut = nearest_close(h, CUTOFF)
    p_meas = nearest_close(h, MEASUREMENT)
    p_high = trailing_52w_high(h, CUTOFF)
    if p_cut is None or p_high is None:
        return {"error": "missing_pre_cutoff_price"}
    if p_meas is None:
        # Try last available close (delisted scenario)
        if h.empty:
            return {"error": "no_post_data"}
        last_close = float(h["Close"].iloc[-1])
        last_date = h.index[-1].date()
        if last_date < CUTOFF:
            return {"error": "no_post_cutoff_data"}
        p_meas = last_close
        return {
            "price_2024_05_15": p_cut,
            "price_2025_05_15": p_meas,
            "last_trade_date": last_date.isoformat(),
            "delisted_before_measurement": True,
            "trailing_52w_high": p_high,
            "drawdown_2024_05_15": (p_cut / p_high) - 1.0,
            "forward_return": (p_meas / p_cut) - 1.0,
        }
    return {
        "price_2024_05_15": p_cut,
        "price_2025_05_15": p_meas,
        "trailing_52w_high": p_high,
        "drawdown_2024_05_15": (p_cut / p_high) - 1.0,
        "forward_return": (p_meas / p_cut) - 1.0,
        "delisted_before_measurement": False,
    }


def main():
    sp600 = json.loads(SP600_PATH.read_text())
    tier1 = json.loads(TIER1_TEST_SET.read_text())

    # Union of current SP600 + Tier 1 cohort (deduplicated)
    candidates = {}
    for s in sp600:
        candidates[s["ticker"]] = {
            "ticker": s["ticker"],
            "cik": s.get("cik", ""),
            "company": s.get("name", ""),
            "sector": s.get("sector", ""),
            "industry": s.get("industry", ""),
        }
    for t in tier1:
        tk = t["ticker"]
        if tk not in candidates:
            candidates[tk] = {
                "ticker": tk,
                "cik": t.get("cik", ""),
                "company": t.get("company", ""),
                "sector": "",
                "industry": "",
            }

    print(f"Total candidates to price: {len(candidates)}")
    print()

    results = []
    errors = []
    for i, (tk, meta) in enumerate(sorted(candidates.items())):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  [{i+1}/{len(candidates)}] {tk}")
        prices = fetch_one(tk)
        if "error" in prices:
            errors.append({"ticker": tk, "error": prices["error"]})
            continue
        results.append({**meta, **prices})
        time.sleep(0.05)

    out = HERE / "candidate_pool.json"
    out.write_text(json.dumps(results, indent=2))
    err_out = HERE / "candidate_pool_errors.json"
    err_out.write_text(json.dumps(errors, indent=2))

    import statistics
    dds = [r["drawdown_2024_05_15"] for r in results]
    distressed = [r for r in results if r["drawdown_2024_05_15"] <= DRAWDOWN_FLOOR]
    print()
    print(f"Priced: {len(results)}, errors: {len(errors)}")
    print(f"Drawdown stats (priced, n={len(results)}):")
    print(f"  mean={statistics.mean(dds)*100:+.1f}%, median={statistics.median(dds)*100:+.1f}%")
    print(f"  pct <= -25% (distressed pool): {len(distressed)} ({len(distressed)/len(results)*100:.0f}%)")
    print(f"  pct <= -40%: {sum(1 for d in dds if d <= -0.40)}")
    if distressed:
        d_rets = [r["forward_return"] for r in distressed]
        print()
        print(f"Distressed pool forward return distribution (n={len(distressed)}):")
        print(f"  mean   = {statistics.mean(d_rets)*100:+.1f}%")
        print(f"  median = {statistics.median(d_rets)*100:+.1f}%")
        print(f"  catastrophes (<-40%): {sum(1 for r in d_rets if r <= -0.4)} ({sum(1 for r in d_rets if r <= -0.4)/len(d_rets)*100:.0f}%)")
        print(f"  big winners (>+50%):  {sum(1 for r in d_rets if r >= 0.5)} ({sum(1 for r in d_rets if r >= 0.5)/len(d_rets)*100:.0f}%)")


if __name__ == "__main__":
    main()
