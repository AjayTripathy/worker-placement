"""Build the Tier 2 candidate pool: SP600 'boring middle' names at 2025-05-15.

For each current SP600 name (sp600_enriched.json):
  - Skip if in the Tier 1 backtest universe (66 names)
  - Fetch 1-year-pre-cutoff + cutoff-to-measurement OHLC via yfinance
  - Compute drawdown_2025_05_15 = (close_2025_05_15 / trailing_52wk_high) - 1
  - Compute forward_return = (close_2026_05_15 / close_2025_05_15) - 1
  - Keep only names with valid prices on both reference dates

OUTPUT: candidate_pool.json (all names with computed metrics)

Run:
    python3 verticals/public_co/data/_backtest/boring_middle_2025_05/build_candidate_pool.py
"""
import json
import time
import warnings
from datetime import date, timedelta
from pathlib import Path

import yfinance as yf

warnings.filterwarnings("ignore")

HERE = Path(__file__).parent
# HERE = .../verticals/public_co/data/_backtest/boring_middle_2025_05
PUBLIC_CO = HERE.parents[2]  # .../verticals/public_co
SP600_PATH = PUBLIC_CO / "data" / "_smallcap_universe" / "sp600_enriched.json"
TIER1_TEST_SET = PUBLIC_CO / "data" / "_backtest" / "survivorship_2025_05" / "_unblinded" / "combined_test_set.json"

CUTOFF = date(2025, 5, 15)
MEASUREMENT = date(2026, 5, 15)
HISTORY_START = CUTOFF - timedelta(days=400)  # need 52w trailing for drawdown
HISTORY_END = MEASUREMENT + timedelta(days=4)


def nearest_close(history, target_date):
    """Return close price for the trading day on/before target_date."""
    target = target_date
    for _ in range(7):  # walk back up to a week to find a trading day
        # history index is tz-aware; compare by date()
        for idx, row in history.iterrows():
            if idx.date() == target:
                return float(row["Close"])
        target = target - timedelta(days=1)
    return None


def trailing_52w_high(history, target_date):
    """Highest close in the 365 days before target_date."""
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
    if p_cut is None or p_meas is None or p_high is None:
        return {"error": "missing_price"}
    return {
        "price_2025_05_15": p_cut,
        "price_2026_05_15": p_meas,
        "trailing_52w_high": p_high,
        "drawdown_2025_05_15": (p_cut / p_high) - 1.0,
        "forward_return": (p_meas / p_cut) - 1.0,
    }


def main():
    sp600 = json.loads(SP600_PATH.read_text())
    tier1 = json.loads(TIER1_TEST_SET.read_text())
    tier1_tickers = {r["ticker"] for r in tier1}

    candidates_raw = [s for s in sp600 if s["ticker"] not in tier1_tickers]
    print(f"SP600 enriched: {len(sp600)}")
    print(f"Tier 1 backtest names to exclude: {len(tier1_tickers)}")
    print(f"Candidates to price: {len(candidates_raw)}")
    print()

    results = []
    errors = []
    for i, s in enumerate(candidates_raw):
        tk = s["ticker"]
        if (i + 1) % 25 == 0 or i == 0:
            print(f"  [{i+1}/{len(candidates_raw)}] {tk}")
        prices = fetch_one(tk)
        if "error" in prices:
            errors.append({"ticker": tk, "error": prices["error"]})
            continue
        results.append({
            "ticker": tk,
            "cik": s.get("cik", ""),
            "company": s.get("name", ""),
            "sector": s.get("sector", ""),
            "industry": s.get("industry", ""),
            **prices,
        })
        time.sleep(0.05)  # throttle to be nice to Yahoo

    out = HERE / "candidate_pool.json"
    out.write_text(json.dumps(results, indent=2))
    err_out = HERE / "candidate_pool_errors.json"
    err_out.write_text(json.dumps(errors, indent=2))
    print()
    print(f"Saved {len(results)} priced candidates to {out.name}")
    print(f"Skipped {len(errors)} with errors → {err_out.name}")

    # Quick distribution summary
    import statistics
    dds = [r["drawdown_2025_05_15"] for r in results]
    boring = [r for r in results if -0.25 <= r["drawdown_2025_05_15"] <= -0.10]
    print()
    print(f"Drawdown distribution (priced, n={len(results)}):")
    print(f"  mean={statistics.mean(dds)*100:+.1f}%, median={statistics.median(dds)*100:+.1f}%")
    print(f"  pct in [-25%, -10%] boring-middle: {len(boring)} ({len(boring)/len(results)*100:.0f}%)")


if __name__ == "__main__":
    main()
