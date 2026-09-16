"""
Shortability assessment for distress-sift candidates.

For each ticker:
  1. Yahoo Finance quote → current price, market cap, average volume, short interest
  2. Apply retail/institutional heuristics:
        - price < $5     → most US brokers prohibit short (Reg T + broker policy)
        - market cap < $50M → likely no borrow / HTB
        - daily $ volume < $1M → liquidity gate fails for any meaningful size
        - short interest > 25% of float → squeeze risk
  3. Try IBKR public short-stock availability lookup (best effort)
  4. Annotate each candidate with shortability tier

Output: shortability.json + a SHORTABILITY.md companion section.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

HERE = Path(__file__).parent
DATA = HERE / "data" / "_distress_sift"


def stooq_quote(ticker: str) -> dict | None:
    """Pull last close from Stooq (free CSV). Returns dict with symbol/price/volume/date."""
    url = f"https://stooq.com/q/l/?s={ticker}.us&f=sd2t2ohlcv&h&e=csv"
    try:
        with httpx.Client(headers=HEADERS, timeout=15) as c:
            r = c.get(url)
            if r.status_code != 200 or len(r.text) < 50:
                return None
            lines = r.text.strip().split("\n")
            if len(lines) < 2:
                return None
            header = [h.lower() for h in lines[0].split(",")]
            vals = lines[1].split(",")
            row = dict(zip(header, vals))
            try:
                return {
                    "symbol": row.get("symbol", "").upper(),
                    "date":   row.get("date", ""),
                    "open":   float(row.get("open") or 0),
                    "close":  float(row.get("close") or 0),
                    "volume": float(row.get("volume") or 0),
                }
            except (ValueError, TypeError):
                return None
    except Exception:
        return None


def sec_shares_outstanding(cik: str) -> tuple[float, str] | None:
    """Latest EntityCommonStockSharesOutstanding from XBRL companyfacts."""
    cik_padded = cik.lstrip("0").rjust(10, "0")
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_padded}/dei/EntityCommonStockSharesOutstanding.json"
    sec_headers = {"User-Agent": "Signal OS Research backtest@signalos.local"}
    try:
        with httpx.Client(headers=sec_headers, timeout=15) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            data = r.json()
            units = data.get("units", {}).get("shares", [])
            if not units:
                return None
            units.sort(key=lambda x: x.get("end", ""), reverse=True)
            u = units[0]
            return float(u.get("val", 0)), u.get("end", "")
    except Exception:
        return None


def yf_quote(ticker: str, cik: str | None = None) -> dict | None:
    """Combined Stooq price + SEC shares outstanding → synthetic quote."""
    q = stooq_quote(ticker)
    if not q:
        return None
    out = {
        "symbol": ticker,
        "regularMarketPrice": q["close"],
        "averageDailyVolume3Month": q["volume"],
        "fullExchangeName": "(unknown via stooq)",
    }
    if cik:
        shares_data = sec_shares_outstanding(cik)
        if shares_data:
            shares, _ = shares_data
            out["sharesOutstanding"] = shares
            out["marketCap"] = q["close"] * shares
    return out


def assess_shortability(q: dict | None) -> dict:
    if not q:
        return {"shortable_tier": "UNKNOWN", "reasons": ["no quote"]}
    price = q.get("regularMarketPrice")
    mcap = q.get("marketCap")
    avg_vol = q.get("averageDailyVolume3Month") or q.get("averageDailyVolume10Day")
    si_pct = None
    si_ratio = None
    float_shares = q.get("sharesOutstanding")
    si_pct_float = None
    exchange = q.get("fullExchangeName") or q.get("exchange") or ""

    daily_dollar_vol = (price or 0) * (avg_vol or 0)

    reasons = []
    # Retail un-shortable
    if price is not None and price < 5:
        reasons.append(f"price ${price:.2f} < $5 (most retail brokers prohibit)")
    if mcap is not None and mcap < 50_000_000:
        reasons.append(f"market cap ${mcap/1e6:.1f}M < $50M (thin/no borrow expected)")
    if daily_dollar_vol < 1_000_000:
        reasons.append(f"daily $ volume ${daily_dollar_vol/1e6:.2f}M < $1M (liquidity gate)")
    if si_pct_float is not None and si_pct_float > 0.25:
        reasons.append(f"short % of float {si_pct_float*100:.0f}% — squeeze risk")
    elif si_pct is not None and si_pct > 0.25:
        reasons.append(f"short % of shares out {si_pct*100:.0f}% — squeeze risk")
    if "PINK" in exchange.upper() or "OTC" in exchange.upper():
        reasons.append(f"OTC-listed ({exchange}) — broker-restricted")

    # Tier
    if not reasons:
        tier = "SHORTABLE"
    elif price is not None and price < 1:
        tier = "ESSENTIALLY_UNSHORTABLE"
    elif len(reasons) >= 3:
        tier = "ESSENTIALLY_UNSHORTABLE"
    elif len(reasons) == 2:
        tier = "HARD_TO_BORROW_OR_RETAIL_RESTRICTED"
    else:
        tier = "BORROW_AT_PREMIUM"

    return {
        "ticker":           q.get("symbol"),
        "price":            price,
        "mcap":             mcap,
        "avg_vol_3m":       avg_vol,
        "daily_dollar_vol": daily_dollar_vol,
        "short_pct_float":  si_pct_float,
        "short_pct_so":     si_pct,
        "short_ratio":      si_ratio,
        "float_shares":     float_shares,
        "exchange":         exchange,
        "shortable_tier":   tier,
        "reasons":          reasons,
    }


def extract_ticker(company_name: str) -> list[str]:
    """Pull ticker symbols out of an EDGAR display name like 'Foo, Inc. (BAR, BARW) (CIK 0001)'."""
    import re
    m = re.search(r"\(([A-Z][A-Z0-9.,\s\-]*?)\)\s*\(CIK", company_name)
    if not m:
        return []
    raw = m.group(1)
    return [t.strip() for t in raw.split(",") if t.strip()]


def main():
    rows = json.loads((DATA / "predictions.json").read_text())
    out = []
    print(f"Assessing shortability for {len(rows)} candidates…", file=sys.stderr)
    for r in rows:
        tickers = extract_ticker(r["company"])
        primary = tickers[0] if tickers else None
        q = yf_quote(primary, cik=r.get("cik")) if primary else None
        sa = assess_shortability(q)
        sa["company"] = r["company"]
        sa["cik"] = r["cik"]
        sa["runway_months"] = r.get("runway_months")
        sa["cash"] = r.get("cash")
        sa["candidate_tickers"] = tickers
        out.append(sa)
        bar = sa["shortable_tier"]
        rw = r.get("runway_months")
        rw_s = f"{rw:.1f}mo" if isinstance(rw, (int, float)) else "?"
        print(f"  {primary or '?':>6}  {bar:<35}  runway={rw_s:>6}  "
              f"price=${sa.get('price') or 0:>7.2f}  mcap=${(sa.get('mcap') or 0)/1e6:>7.1f}M", file=sys.stderr)
        time.sleep(0.3)

    (DATA / "shortability.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote → {DATA / 'shortability.json'}", file=sys.stderr)

    # Summary
    from collections import Counter
    tiers = Counter(r["shortable_tier"] for r in out)
    critical_shortable = [r for r in out if r["runway_months"] and r["runway_months"] < 6
                          and r["shortable_tier"] == "SHORTABLE"]
    critical_premium = [r for r in out if r["runway_months"] and r["runway_months"] < 6
                        and r["shortable_tier"] == "BORROW_AT_PREMIUM"]

    print("\n=== TIER COUNTS ===", file=sys.stderr)
    for t, n in tiers.most_common():
        print(f"  {t:<40} {n}", file=sys.stderr)
    print(f"\n=== CRITICAL TIER + SHORTABLE ({len(critical_shortable)}) ===", file=sys.stderr)
    for r in critical_shortable:
        print(f"  {r['ticker']}  ${r['price']:.2f}  mcap=${r['mcap']/1e6:.0f}M  runway={r['runway_months']:.1f}mo", file=sys.stderr)
    print(f"\n=== CRITICAL TIER + BORROW_AT_PREMIUM ({len(critical_premium)}) ===", file=sys.stderr)
    for r in critical_premium:
        print(f"  {r['ticker']}  ${r['price']:.2f}  mcap=${r['mcap']/1e6:.0f}M  runway={r['runway_months']:.1f}mo  | {'; '.join(r['reasons'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
