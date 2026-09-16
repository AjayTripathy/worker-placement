"""Build the forward-test candidate pool as of 2026-05-25.

For each current SP600 + Tier 1 cohort name (union ~635 names):
  - Fetch yfinance OHLC 2025-05-01 → 2026-05-30
  - Compute drawdown_2026_05_25 (price vs trailing 52w high)
  - Filter to drawdown ≤ -25% (distressed pool)
  - Note: NO forward returns available — this is the forward test!

Output: candidate_pool.json (all priced), errors, and basic stats.

Run:
    python3 verticals/public_co/data/_forward_test/forward_2026_05_25/build_candidate_pool.py
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
TIER1_PATH = PUBLIC_CO / "data" / "_backtest" / "survivorship_2025_05" / "_unblinded" / "combined_test_set.json"

CUTOFF = date(2026, 5, 25)
HISTORY_START = CUTOFF - timedelta(days=400)
HISTORY_END = CUTOFF + timedelta(days=5)
DRAWDOWN_FLOOR = -0.25


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
    p_high = trailing_52w_high(h, CUTOFF)
    if p_cut is None or p_high is None:
        return {"error": "missing_price"}
    return {
        "price_2026_05_25": p_cut,
        "trailing_52w_high": p_high,
        "drawdown_2026_05_25": (p_cut / p_high) - 1.0,
    }


def main():
    sp600 = json.loads(SP600_PATH.read_text())
    tier1 = json.loads(TIER1_PATH.read_text())

    candidates = {}
    for s in sp600:
        candidates[s["ticker"]] = {
            "ticker": s["ticker"], "cik": s.get("cik", ""),
            "company": s.get("name", ""), "sector": s.get("sector", ""),
            "industry": s.get("industry", ""),
        }
    for t in tier1:
        tk = t["ticker"]
        if tk not in candidates:
            candidates[tk] = {
                "ticker": tk, "cik": t.get("cik", ""),
                "company": t.get("company", ""), "sector": "", "industry": "",
            }

    print(f"Pricing {len(candidates)} candidates as of {CUTOFF}...")
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
    (HERE / "candidate_pool_errors.json").write_text(json.dumps(errors, indent=2))

    import statistics
    dds = [r["drawdown_2026_05_25"] for r in results]
    distressed = [r for r in results if r["drawdown_2026_05_25"] <= DRAWDOWN_FLOOR]
    print()
    print(f"Priced: {len(results)}, errors: {len(errors)}")
    print(f"Drawdown distribution: mean={statistics.mean(dds)*100:+.1f}%, median={statistics.median(dds)*100:+.1f}%")
    print(f"Distressed pool (drawdown <= -25%): {len(distressed)}")
    print(f"Deep distress (<= -40%): {sum(1 for d in dds if d <= -0.40)}")
    print()

    # Show top-distressed names
    distressed.sort(key=lambda r: r["drawdown_2026_05_25"])
    print("Sample of distressed pool (top 20 by drawdown):")
    for r in distressed[:20]:
        print(f"  {r['ticker']:6}  {(r.get('sector') or '')[:20]:20}  dd={r['drawdown_2026_05_25']*100:+.1f}%  price=${r['price_2026_05_25']:.2f}")


if __name__ == "__main__":
    main()
