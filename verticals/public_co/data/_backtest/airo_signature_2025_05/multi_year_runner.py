"""Multi-year AIRO-signature backtest.

For each entry date in {2022-05-15, 2023-05-15, 2024-05-15, 2025-05-15}:
  1. Screen EDGAR fulltext for "stock for services" AND "material weakness"
     in 10-K filings dated entry_date-13mo to entry_date-1mo.
  2. For each unique tickered hit:
     - Fetch yfinance price history covering entry → entry+12mo
     - Compute mcap at entry (shares × price)
     - Filter to $100M-$500M mcap band
     - Compute 12-month return
  3. For each in-band name:
     - Auto-classify sector via yfinance.info.sector + .industry
     - Map to sector ETF (XLB/XLC/XLE/XLF/XLI/XLK/XLP/XLRE/XLU/XLV/XBI/SMH/XLY)
     - Compute pair P&L = sector_R - name_R
  4. Aggregate per-year + cross-year.

This file is the runner; results land in this directory as JSON + a
summary printed to stdout.
"""
from __future__ import annotations

import json
import re
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import httpx
import pandas as pd
import yfinance as yf

HERE = Path(__file__).parent
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


# yfinance sector → preferred ETF. Biotech industry routes to XBI.
SECTOR_TO_ETF = {
    "Communication Services":  "XLC",
    "Consumer Cyclical":       "XLY",
    "Consumer Defensive":      "XLP",
    "Energy":                  "XLE",
    "Financial Services":      "XLF",
    "Healthcare":              "XLV",
    "Industrials":             "XLI",
    "Technology":              "XLK",
    "Utilities":               "XLU",
    "Real Estate":             "XLRE",
    "Basic Materials":         "XLB",
}
BIOTECH_INDUSTRIES = {
    "Biotechnology",
    "Drug Manufacturers - Specialty & Generic",
    "Drug Manufacturers - General",
    "Diagnostics & Research",
}
SEMI_INDUSTRIES = {"Semiconductors", "Semiconductor Equipment & Materials"}


def fetch_edgar_hits(start_dt: str, end_dt: str) -> list[dict]:
    url = "https://efts.sec.gov/LATEST/search-index"
    out = []
    seen = set()
    for from_idx in [0, 100, 200, 300]:
        params = {
            "q": '"stock for services" "material weakness"',
            "dateRange": "custom",
            "startdt": start_dt,
            "enddt":   end_dt,
            "forms":   "10-K",
            "from": from_idx,
        }
        try:
            r = httpx.get(url, params=params, headers=HEADERS, timeout=30)
            data = r.json()
        except Exception:
            break
        page = data.get("hits", {}).get("hits", [])
        if not page:
            break
        for h in page:
            acc = h.get("_id")
            if acc in seen:
                continue
            seen.add(acc)
            src = h.get("_source", {})
            names = src.get("display_names", [])
            if not names:
                continue
            full = names[0]
            m_cik = re.search(r"CIK\s+(\d+)", full)
            m_tk  = re.search(r"\(([A-Z]{1,6})\)\s*\(CIK", full)
            company = re.sub(r"\s*\(CIK.*", "", full).strip()
            company = re.sub(r"\s*\([A-Z]{1,6}\)\s*$", "", company).strip()
            out.append({
                "filing_date": src.get("file_date"),
                "form":        src.get("form"),
                "company":     company,
                "ticker":      m_tk.group(1) if m_tk else None,
                "cik":         m_cik.group(1).lstrip("0") if m_cik else None,
                "accession":   acc,
            })
        time.sleep(0.3)
    return out


def fetch_ticker_data(tk: str, entry_dt: str, exit_dt: str) -> dict:
    """Pull price, mcap, sector for one ticker around entry_dt → exit_dt."""
    out = {"ticker": tk}
    try:
        t = yf.Ticker(tk)
        hist = t.history(
            start=(pd.Timestamp(entry_dt) - pd.Timedelta(days=30)).strftime("%Y-%m-%d"),
            end=(pd.Timestamp(exit_dt) + pd.Timedelta(days=30)).strftime("%Y-%m-%d"),
            auto_adjust=True,
        )
        if hist.empty:
            out["status"] = "no_data"
            return out
        e_idx = hist.index.get_indexer([pd.Timestamp(entry_dt, tz=hist.index.tz)], method="nearest")[0]
        x_idx = hist.index.get_indexer([pd.Timestamp(exit_dt, tz=hist.index.tz)], method="nearest")[0]
        p_entry = float(hist.iloc[e_idx]["Close"])
        p_exit  = float(hist.iloc[x_idx]["Close"])
        # Sanity: ensure exit_dt is actually covered (no mid-window delisting)
        last_dt = hist.index[-1]
        days_short = (pd.Timestamp(exit_dt, tz=last_dt.tz) - last_dt).days
        info = {}
        try:
            info = t.info or {}
        except Exception:
            info = {}
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        sector   = info.get("sector")
        industry = info.get("industry")
        out.update({
            "status":     "alive" if days_short <= 14 else f"truncated_{days_short}d",
            "price_entry": p_entry,
            "price_exit":  p_exit,
            "return":      (p_exit / p_entry) - 1,
            "mcap_entry":  (p_entry * shares) if shares else None,
            "shares":      shares,
            "sector":      sector,
            "industry":    industry,
        })
    except Exception as e:
        out["status"] = f"error_{type(e).__name__}"
    return out


def classify_etf(sector: str | None, industry: str | None) -> str:
    if industry in BIOTECH_INDUSTRIES:
        return "XBI"
    if industry in SEMI_INDUSTRIES:
        return "SMH"
    if not sector:
        return "IWM"
    return SECTOR_TO_ETF.get(sector, "IWM")


def fetch_etf_returns(etfs: set[str], entry_dt: str, exit_dt: str) -> dict[str, float]:
    out = {}
    for etf in etfs:
        try:
            h = yf.Ticker(etf).history(
                start=(pd.Timestamp(entry_dt) - pd.Timedelta(days=30)).strftime("%Y-%m-%d"),
                end=(pd.Timestamp(exit_dt) + pd.Timedelta(days=30)).strftime("%Y-%m-%d"),
                auto_adjust=True,
            )
            if h.empty:
                out[etf] = None; continue
            e = h.index.get_indexer([pd.Timestamp(entry_dt, tz=h.index.tz)], method="nearest")[0]
            x = h.index.get_indexer([pd.Timestamp(exit_dt, tz=h.index.tz)], method="nearest")[0]
            out[etf] = (float(h.iloc[x]["Close"]) / float(h.iloc[e]["Close"])) - 1
        except Exception:
            out[etf] = None
    return out


def run_year(entry_dt: str) -> dict:
    entry  = pd.Timestamp(entry_dt)
    exit_  = entry + pd.Timedelta(days=365)
    # Screen window: 10-Ks filed roughly entry-13mo to entry-1mo
    screen_start = (entry - pd.Timedelta(days=395)).strftime("%Y-%m-%d")
    screen_end   = (entry - pd.Timedelta(days=15 )).strftime("%Y-%m-%d")
    print(f"=== entry {entry_dt}  screen {screen_start} → {screen_end} ===")

    hits = fetch_edgar_hits(screen_start, screen_end)
    by_tk = {}
    for h in hits:
        tk = h["ticker"]
        if not tk: continue
        if tk not in by_tk or h["filing_date"] < by_tk[tk]["filing_date"]:
            by_tk[tk] = h
    print(f"  EDGAR raw hits: {len(hits)}   unique tickered: {len(by_tk)}")

    # Pull price + sector for each ticker
    rows = []
    for i, (tk, h) in enumerate(by_tk.items()):
        d = fetch_ticker_data(tk, entry_dt, exit_.strftime("%Y-%m-%d"))
        rows.append({**h, **d})
        if (i+1) % 25 == 0:
            print(f"    progress: {i+1}/{len(by_tk)}")
        time.sleep(0.05)

    # Filter to in-band
    in_band = [r for r in rows
               if r.get("mcap_entry") is not None
               and 100e6 <= (r["mcap_entry"] or 0) < 500e6
               and r.get("return") is not None]
    print(f"  In-band ($100M-$500M): {len(in_band)}")

    # Sector ETF returns for those in-band
    etfs = set()
    for r in in_band:
        r["etf"] = classify_etf(r.get("sector"), r.get("industry"))
        etfs.add(r["etf"])
    etf_ret = fetch_etf_returns(etfs, entry_dt, exit_.strftime("%Y-%m-%d"))

    pair_rows = []
    for r in in_band:
        e = r["etf"]
        sr = etf_ret.get(e)
        if sr is None: continue
        pair_pnl = sr - r["return"]
        pair_rows.append({
            **r,
            "etf_return": sr,
            "pair_pnl":   pair_pnl,
        })
    pair_rows.sort(key=lambda x: -x["pair_pnl"])
    return {
        "entry_dt":       entry_dt,
        "exit_dt":        exit_.strftime("%Y-%m-%d"),
        "n_hits":         len(by_tk),
        "n_in_band":      len(in_band),
        "n_priced":       len(pair_rows),
        "rows":           pair_rows,
        "etf_returns":    etf_ret,
    }


def summarize(results: list[dict]):
    import statistics
    print()
    print("=" * 80)
    print("MULTI-YEAR SUMMARY")
    print("=" * 80)
    for r in results:
        rows = r["rows"]
        if not rows:
            print(f"\n--- {r['entry_dt']} → {r['exit_dt']}: NO DATA ---")
            continue
        pair_rets = [x["pair_pnl"] for x in rows]
        no_biotech = [x for x in rows if x["etf"] != "XBI"]
        nb_rets = [x["pair_pnl"] for x in no_biotech]
        hit_rate = sum(1 for p in pair_rets if p > 0) / len(pair_rets)
        nb_hit_rate = sum(1 for p in nb_rets if p > 0) / len(nb_rets) if nb_rets else 0
        print(f"\n--- {r['entry_dt']} → {r['exit_dt']} ---")
        print(f"  EDGAR unique tickered: {r['n_hits']}   in-band: {r['n_in_band']}   priced: {r['n_priced']}")
        print(f"  All-pairs:   mean={statistics.mean(pair_rets)*100:+6.2f}%  median={statistics.median(pair_rets)*100:+6.2f}%  hit={hit_rate*100:.0f}%  (n={len(pair_rets)})")
        if nb_rets:
            print(f"  Ex-biotech:  mean={statistics.mean(nb_rets)*100:+6.2f}%  median={statistics.median(nb_rets)*100:+6.2f}%  hit={nb_hit_rate*100:.0f}%  (n={len(nb_rets)})")
        print(f"  Top 5 pairs:")
        for x in rows[:5]:
            print(f"    {x['ticker']:5s} {x['etf']:5s} sec={x['etf_return']*100:+6.1f}% name={x['return']*100:+8.1f}% pair={x['pair_pnl']*100:+8.1f}%  ({x.get('sector','?')[:18] if x.get('sector') else '?':18s})")
        if len(rows) > 5:
            print(f"  Bottom 3 pairs:")
            for x in rows[-3:]:
                print(f"    {x['ticker']:5s} {x['etf']:5s} sec={x['etf_return']*100:+6.1f}% name={x['return']*100:+8.1f}% pair={x['pair_pnl']*100:+8.1f}%  ({x.get('sector','?')[:18] if x.get('sector') else '?':18s})")


def main():
    entries = ["2022-05-15", "2023-05-15", "2024-05-15"]
    results = []
    for ent in entries:
        r = run_year(ent)
        results.append(r)
        # Persist incrementally
        (HERE / f"multi_year_{ent.replace('-','_')}.json").write_text(
            json.dumps(r, indent=2, default=str)
        )

    summarize(results)
    (HERE / "multi_year_all.json").write_text(
        json.dumps(results, indent=2, default=str)
    )


if __name__ == "__main__":
    main()
