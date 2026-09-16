"""Mini free price feed for muni-credit pair-trade backtesting.

WHAT IT DOES

Combines TWO free public data sources to enable approximate pair-trade P&L
on hospital muni credit signals:

  1. Yahoo Finance ETF total-return prices  → sector-level benchmark
     - MUB  (iShares National Muni Bond ETF) — broad AA-tier muni baseline
     - HYD  (VanEck High Yield Muni) — high yield / distressed muni proxy
     - VTEB (Vanguard Tax-Exempt) — alt broad muni cross-check

  2. MSRB BVAL AAA Callable yield curve at specific dates
     - Authoritative AAA muni benchmark
     - Pulled by hand from MSRB Year-in-Review / Market Summary PDFs
     - Storage: data/bval_aaa_yields.json

WHAT IT DOES NOT DO

  - Individual bond CUSIP-level trade data — EMMA blocks programmatic access
    (CUSIP interstitial + opaque GUID URLs + explicit anti-scrape TOU).
    For per-bond yields at specific dates we fall back to literature-anchored
    spread proxies layered on top of the verified AAA benchmark.

  - Real-time data — Yahoo lag is 15-min during market hours; BVAL is end-of-day.

  - Bid/ask spreads — assume retail ~15-25 bps round-trip on muni; subtract from
    gross P&L for net.

PRIMARY USE — back-test a sector-neutral pair trade

  >>> from muni_credit.price_feed.feed import pair_trade_pnl
  >>> result = pair_trade_pnl(
  ...     short_obligors=[
  ...         {"name": "Ascension", "duration": 8.0, "estimated_spread_widening_bps": 10},
  ...         {"name": "UPMC",      "duration": 8.0, "estimated_spread_widening_bps": 5},
  ...         {"name": "Trinity",   "duration": 8.0, "estimated_spread_widening_bps": 0},
  ...     ],
  ...     long_benchmark="MUB",
  ...     start_date="2022-12-30",
  ...     end_date="2025-03-31",
  ... )

DATA QUALITY DISCLAIMER

  - ETF data: HIGH confidence (Yahoo Finance public REST, free, no auth)
  - BVAL AAA: HIGH confidence (MSRB published PDFs, agent-verified)
  - Per-bond spread widening: MEDIUM-LOW confidence (literature estimates,
    typically 5-15 bps for outlook revision, 20-50 bps for 1-notch downgrade,
    50-150 bps for multi-notch)

  This is NOT a replacement for bond-level trade data. It is a pilot-quality
  feed for sanity-checking signal alpha before paying for institutional data.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
BVAL_FILE = HERE.parent / "data" / "bval_aaa_yields.json"


# -- Yahoo Finance ETF prices -------------------------------------------------

def fetch_yahoo_etf(ticker: str, start_date: str, end_date: str,
                    cache_dir: Optional[Path] = None) -> dict:
    """Fetch Yahoo Finance chart data for a muni ETF.

    Returns dict with 'timestamps', 'adjclose' (total return), and metadata.

    Cache: writes to cache_dir/{ticker}_{start}_{end}.json on first fetch.
    Re-reads from cache on subsequent calls.
    """
    cache_path = None
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{ticker}_{start_date}_{end_date}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text())

    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={start_ts}&period2={end_ts}&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = json.loads(r.read().decode())

    result = raw["chart"]["result"][0]
    out = {
        "ticker": ticker,
        "timestamps": result["timestamps"] if "timestamps" in result else result["timestamp"],
        "adjclose": result["indicators"]["adjclose"][0]["adjclose"],
        "close": result["indicators"]["quote"][0]["close"],
        "currency": result["meta"].get("currency"),
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "source_url": url,
    }
    if cache_path is not None:
        cache_path.write_text(json.dumps(out, indent=2))
    return out


def etf_total_return(ticker: str, start_date: str, end_date: str,
                     cache_dir: Optional[Path] = None) -> dict:
    """Total return for a muni ETF between two dates (uses adjclose).

    Returns the actual ETF price at the closest trading day to each target,
    plus the implied total return.
    """
    data = fetch_yahoo_etf(ticker, "2020-01-01", "2026-12-31", cache_dir=cache_dir)
    ts = data["timestamps"]
    adj = data["adjclose"]

    def closest(target_date_str):
        target = datetime.strptime(target_date_str, "%Y-%m-%d").timestamp()
        idx = min(range(len(ts)), key=lambda i: abs(ts[i] - target))
        actual = datetime.fromtimestamp(ts[idx]).strftime("%Y-%m-%d")
        return idx, actual, adj[idx]

    si, sd, sp = closest(start_date)
    ei, ed, ep = closest(end_date)

    return {
        "ticker": ticker,
        "start_date_requested": start_date,
        "start_date_actual": sd,
        "start_price_adj": sp,
        "end_date_requested": end_date,
        "end_date_actual": ed,
        "end_price_adj": ep,
        "total_return": (ep / sp) - 1.0,
    }


# -- BVAL AAA benchmark -------------------------------------------------------

def load_bval_aaa() -> dict:
    """Load the curated BVAL AAA snapshot file."""
    if not BVAL_FILE.exists():
        raise FileNotFoundError(
            f"{BVAL_FILE} missing — see data/bval_aaa_yields.json schema"
        )
    return json.loads(BVAL_FILE.read_text())


def bval_aaa_yield(date_str: str, tenor_years: int = 10) -> dict:
    """Get the BVAL AAA Callable yield at a specific date / tenor.

    Returns dict with yield_pct and source citation.
    """
    bval = load_bval_aaa()
    for snap in bval["snapshots"]:
        if snap["date"] == date_str:
            tenor_key = f"yield_pct_{tenor_years}y"
            if tenor_key in snap:
                return {
                    "date": snap["date"],
                    "yield_pct": snap[tenor_key],
                    "source_url": snap["source_url"],
                    "citation": snap.get("citation_text", ""),
                }
    raise ValueError(f"No BVAL snapshot for {date_str} / {tenor_years}Y in {BVAL_FILE}")


# -- Pair trade computation ---------------------------------------------------

def pair_trade_pnl(short_obligors: list[dict], long_benchmark: str,
                   start_date: str, end_date: str,
                   transaction_cost_bps: int = 20,
                   cache_dir: Optional[Path] = None) -> dict:
    """Compute approximate pair trade P&L.

    short_obligors: list of {name, duration, estimated_spread_widening_bps}
    long_benchmark: ETF ticker (typically "MUB" for AA muni baseline)

    Returns dict with per-name and aggregate P&L estimates.
    """
    bench = etf_total_return(long_benchmark, start_date, end_date, cache_dir=cache_dir)
    bench_tr = bench["total_return"]

    per_name = []
    for o in short_obligors:
        # Approximate the obligor's bond total return as:
        #   benchmark_TR - duration * (estimated_spread_widening) / 10000
        # i.e., the obligor underperforms benchmark by duration * spread move
        widening_bps = o.get("estimated_spread_widening_bps", 0)
        duration = o["duration"]
        own_tr = bench_tr - (duration * widening_bps / 10000.0)
        pair_pnl_gross = bench_tr - own_tr
        per_name.append({
            "obligor": o["name"],
            "duration": duration,
            "estimated_spread_widening_bps": widening_bps,
            "benchmark_total_return": bench_tr,
            "own_total_return_est": own_tr,
            "pair_pnl_gross": pair_pnl_gross,
        })

    avg_pair_pnl_gross = sum(p["pair_pnl_gross"] for p in per_name) / max(1, len(per_name))
    avg_pair_pnl_net = avg_pair_pnl_gross - (transaction_cost_bps / 10000.0)

    # Annualize
    days = (datetime.strptime(end_date, "%Y-%m-%d") -
            datetime.strptime(start_date, "%Y-%m-%d")).days
    years = days / 365.25
    annualized_gross = (1 + avg_pair_pnl_gross) ** (1 / years) - 1
    annualized_net = (1 + avg_pair_pnl_net) ** (1 / years) - 1

    return {
        "benchmark": long_benchmark,
        "benchmark_start_date": bench["start_date_actual"],
        "benchmark_end_date": bench["end_date_actual"],
        "benchmark_total_return": bench_tr,
        "n_short_obligors": len(short_obligors),
        "per_name": per_name,
        "avg_pair_pnl_gross_pct": avg_pair_pnl_gross * 100,
        "avg_pair_pnl_net_pct": avg_pair_pnl_net * 100,
        "transaction_cost_bps": transaction_cost_bps,
        "years": years,
        "annualized_gross_pct": annualized_gross * 100,
        "annualized_net_pct": annualized_net * 100,
        "DATA_QUALITY_NOTE": (
            "Per-obligor returns are ESTIMATED from sector benchmark minus "
            "literature-derived spread widening proxy. NOT measured from "
            "bond-level trade data. See feed.py docstring."
        ),
    }


if __name__ == "__main__":
    import sys
    cache_dir = HERE.parent / "data" / "_price_cache"

    # Sanity check: print MUB / HYD / VTEB total returns over the backtest window
    for sym in ["MUB", "HYD", "VTEB"]:
        r = etf_total_return(sym, "2022-12-30", "2025-03-31", cache_dir=cache_dir)
        print(f"{sym}: {r['start_date_actual']} ${r['start_price_adj']:.2f} → "
              f"{r['end_date_actual']} ${r['end_price_adj']:.2f} = "
              f"{r['total_return']*100:+.2f}% TR")
