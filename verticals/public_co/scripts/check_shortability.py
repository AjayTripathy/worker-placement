"""
Shortability check for the forward-test SHORT basket.

For each ticker, pull from yfinance:
  - Market cap (proxy for general borrow availability)
  - Short interest as % of float (high → expensive borrow)
  - Short ratio / days to cover
  - Average daily volume (liquidity for entry/exit)
  - Exchange listing (US vs ADR)

Flag names with:
  - Market cap < $1B → potentially hard-to-borrow micro/small-cap
  - Short % of float > 20% → already crowded short, expensive borrow
  - ADV in $ < $20M/day → liquidity risk
  - ADR / foreign filer → restricted borrow availability
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yfinance as yf

DATA = Path("verticals/public_co/data")
FORWARD = json.loads((DATA / "_jbook_exposure_cohort" /
                       "forward_test_FY27_FY28.json").read_text())


def _safe_get(info: dict, *keys):
    for k in keys:
        v = info.get(k)
        if v is not None:
            return v
    return None


def check_one(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
    except Exception as e:
        return {"ticker": ticker, "error": str(e)}

    market_cap   = _safe_get(info, "marketCap")
    shares_short = _safe_get(info, "sharesShort")
    short_ratio  = _safe_get(info, "shortRatio")  # days to cover
    short_pct    = _safe_get(info, "shortPercentOfFloat",
                              "sharesShortPriorMonth", "shortPercentFloat")
    float_shares = _safe_get(info, "floatShares", "sharesOutstanding")
    avg_vol      = _safe_get(info, "averageVolume", "averageDailyVolume10Day")
    price        = _safe_get(info, "currentPrice", "regularMarketPrice", "previousClose")
    exchange     = _safe_get(info, "exchange") or ""
    quote_type   = _safe_get(info, "quoteType") or ""
    country      = _safe_get(info, "country") or ""
    long_name    = _safe_get(info, "longName", "shortName") or ""

    adv_usd = (avg_vol or 0) * (price or 0)
    short_pct_calc = None
    if shares_short and float_shares:
        short_pct_calc = shares_short / float_shares * 100

    # Score it
    flags = []
    if market_cap and market_cap < 1_000_000_000:
        flags.append("micro_cap")
    if market_cap and market_cap < 300_000_000:
        flags.append("very_small")
    if short_pct_calc is not None and short_pct_calc > 20:
        flags.append("crowded_short")
    if adv_usd and adv_usd < 20_000_000:
        flags.append("low_liquidity")
    if "ADR" in long_name or "American Depositary" in long_name:
        flags.append("ADR")
    if country and country not in ("United States",) and country:
        flags.append(f"foreign:{country}")

    return {
        "ticker":           ticker,
        "name":             long_name[:40],
        "exchange":         exchange,
        "quote_type":       quote_type,
        "country":          country,
        "price":            price,
        "market_cap_M":     (market_cap or 0) / 1e6,
        "short_pct_float":  short_pct_calc,
        "short_ratio_days": short_ratio,
        "avg_daily_vol":    avg_vol,
        "avg_daily_vol_USD_M": (adv_usd or 0) / 1e6,
        "flags":            flags,
    }


def main():
    print("\n" + "=" * 110)
    print("SHORT BASKET SHORTABILITY CHECK (9 names)")
    print("=" * 110)
    print(f"{'TICKER':<6} {'NAME':<32} {'MCAP $M':>9} "
          f"{'SHORT %FLT':>10} {'D2COVER':>8} {'ADV $M':>8}  FLAGS")
    print("-" * 110)
    rows = []
    for t in FORWARD["short_basket"]:
        r = check_one(t["ticker"])
        rows.append(r)
        flags_str = ", ".join(r.get("flags", [])) or "ok"
        print(f"{r['ticker']:<6} {r.get('name','')[:32]:<32} "
              f"{r.get('market_cap_M',0):>9,.0f} "
              f"{(r.get('short_pct_float') or 0):>9.1f}% "
              f"{(r.get('short_ratio_days') or 0):>7.1f} "
              f"{r.get('avg_daily_vol_USD_M',0):>7.1f}  {flags_str}")

    print("\n" + "=" * 110)
    print("LONG BASKET LIQUIDITY CHECK (9 names — confirm tradeable for entry/exit)")
    print("=" * 110)
    print(f"{'TICKER':<6} {'NAME':<32} {'MCAP $M':>9} "
          f"{'ADV $M':>8}  FLAGS")
    print("-" * 110)
    for t in FORWARD["long_basket"]:
        r = check_one(t["ticker"])
        flags_str = ", ".join(r.get("flags", [])) or "ok"
        print(f"{r['ticker']:<6} {r.get('name','')[:32]:<32} "
              f"{r.get('market_cap_M',0):>9,.0f} "
              f"{r.get('avg_daily_vol_USD_M',0):>7.1f}  {flags_str}")

    out = DATA / "_jbook_exposure_cohort" / "shortability_check.json"
    out.write_text(json.dumps(rows, indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
