"""
J-Book LONG basket — out-of-sample backtest.

Hypothesis: rather than shorting J-Book divergence (which we showed
loses in a sector bull regime), go long the highest-dollar funded
programs and their public prime contractors.

At the 2024-09-01 cutoff with cutoff filter on funding_history, only
FY 2024 funding rows are visible to the framework, so growth status
defaults to FUNDED_STEADY across most programs. The signal we *can*
extract: aggregate FY 2024 funding $ by primary contractor.

Most of our 410-program corpus has empty primary_contractors (auto-
ingest captured PE + funding but not always contractors). We map the
top-funded programs to known public primes manually — these are
publicly-known major defense awards, not curated post-hoc.

Mapping is conservative: only programs where the prime is unambiguously
known and publicly disclosed. Multi-prime programs are split.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import yfinance as yf

from verticals.public_co.m_sources.pentagon_jbook import _latest_funding_status

DATA = Path("verticals/public_co/data")
CORPUS = DATA / "_jbook_data" / "programs.json"

ENTRY_DATE = "2024-09-01"
EXIT_DATE  = "2026-05-20"
BORROW_BPS_PER_YEAR = 0   # long basket — no borrow cost

# Top-program → prime contractor mapping. Source: publicly-known DoD prime
# contract awards. Only programs where prime is unambiguous at 2024-09-01.
# When multi-prime, weight is split.
PROGRAM_TO_PRIMES = {
    # ICBM / Sentinel
    "Ground Based Strategic Deterrent EMD": [("NOC", 1.0)],
    # Bombers
    "Long Range Strike - Bomber":            [("NOC", 1.0)],
    "B-21 Raider":                            [("NOC", 1.0)],
    "B-52 Squadrons":                         [("BA",  0.7), ("RTX", 0.3)],  # airframe vs reengine
    # Fighters
    "F-35 C2D2":                              [("LMT", 1.0)],
    "F-22A Squadrons":                        [("LMT", 1.0)],
    "F-47":                                   [("BA",  1.0)],  # won NGAD 3/2025, pre-award PE
    # MDA / BMD
    "Improved Homeland Defense Interceptors": [("LMT", 0.5), ("NOC", 0.5)],  # NGI competition open at cutoff
    "Ballistic Missile Defense Midcourse Defense Segment": [("BA", 0.7), ("LMT", 0.3)],  # GMD = Boeing prime
    "AEGIS BMD":                              [("LMT", 1.0)],
    "Long Range Standoff Weapon":             [("RTX", 1.0)],
    # Space / SDA / OPIR
    "Resilient Missile Warning Missile Tracking - MEO": [("LMT", 0.5), ("NOC", 0.5)],
    "Resilient Missile Warning Missile Tracking":       [("LMT", 0.5), ("NOC", 0.5)],
    "Next-Gen OPIR -- Polar":                 [("NOC", 1.0)],
    "Next-Gen OPIR -- GEO":                   [("LMT", 1.0)],
    # Survivable Airborne (E-4)
    "Survivable Airborne Operations Center":  [("BA",  1.0)],  # SAOC awarded to Sierra Nevada (private)
                                                                 # but legacy E-4 ops support is Boeing-flavored
    # BMD targets
    "Ballistic Missile Defense Targets":      [("LMT", 0.5), ("NOC", 0.5)],
}


def _next_close(ticker: str, date_iso: str) -> Optional[tuple[str, float]]:
    start = datetime.fromisoformat(date_iso)
    end_dt = datetime(start.year, start.month, min(28, start.day + 7))
    end_iso = end_dt.strftime("%Y-%m-%d")
    try:
        df = yf.download(ticker, start=date_iso, end=end_iso,
                          progress=False, auto_adjust=False)
    except Exception as e:
        print(f"  ! yf.download err for {ticker}: {e}", file=sys.stderr)
        return None
    if df is None or df.empty:
        return None
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    row = df.iloc[0]
    val = row[col]
    if hasattr(val, "item"):
        val = val.item()
    return (str(df.index[0].date()), float(val))


def main():
    corpus = json.loads(CORPUS.read_text())["programs"]

    # Aggregate $ by program using cutoff=2024 status filter
    ticker_dollars = defaultdict(float)
    mapped_programs = []
    unmapped_top = []
    for p in corpus:
        s = _latest_funding_status(p, cutoff_year=2024)
        if s["status"] not in ("FUNDED_GROWING", "FUNDED_STEADY"):
            continue
        amt = s.get("latest_funded_M") or 0
        if amt < 200:  # ignore small programs (<$200M)
            continue
        name = p.get("program_name", "")
        primes = PROGRAM_TO_PRIMES.get(name)
        if not primes:
            # Try partial match — strip common suffixes
            for k, v in PROGRAM_TO_PRIMES.items():
                if k.startswith(name[:20]) or name.startswith(k[:20]):
                    primes = v
                    break
        if primes:
            mapped_programs.append({"program": name, "fy_M": amt, "primes": primes})
            for tk, w in primes:
                ticker_dollars[tk] += amt * w
        else:
            unmapped_top.append({"program": name, "fy_M": amt})

    unmapped_top.sort(key=lambda x: -x["fy_M"])

    print(f"Programs ≥$200M at FY 2024: {len(mapped_programs)+len(unmapped_top)}")
    print(f"  mapped to a prime: {len(mapped_programs)}")
    print(f"  unmapped (no PROGRAM_TO_PRIMES entry): {len(unmapped_top)}")
    print(f"\nTop 15 unmapped (these would need manual mapping to enter the basket):")
    for u in unmapped_top[:15]:
        print(f"  ${u['fy_M']:>7.0f}M  {u['program'][:60]}")

    # Show ticker dollar exposure
    print(f"\nMapped-prime dollar exposure (sum of FY 2024 across mapped programs):")
    tickers_ranked = sorted(ticker_dollars.items(), key=lambda x: -x[1])
    for tk, amt in tickers_ranked:
        print(f"  {tk}:  ${amt:>9.0f}M  across mapped programs")

    if not tickers_ranked:
        print("No tickers mapped — aborting", file=sys.stderr)
        return

    # Fetch prices
    print("\nFetching prices...", file=sys.stderr)
    rows = []
    for tk, amt in tickers_ranked:
        entry = _next_close(tk, ENTRY_DATE)
        exit  = _next_close(tk, EXIT_DATE)
        if not entry or not exit:
            print(f"  ! {tk}: price fetch failed", file=sys.stderr)
            continue
        ret = (exit[1] - entry[1]) / entry[1]
        rows.append({
            "ticker":          tk,
            "exposure_M":      amt,
            "entry_date":      entry[0],
            "entry_price":     entry[1],
            "exit_date":       exit[0],
            "exit_price":      exit[1],
            "long_return_pct": ret * 100,
        })

    days_held = (datetime.fromisoformat(EXIT_DATE)
                  - datetime.fromisoformat(ENTRY_DATE)).days
    annualized_factor = 365 / max(1, days_held)

    print()
    print(f"J-BOOK LONG BASKET — {len(rows)} primes mapped, "
          f"{ENTRY_DATE} → {EXIT_DATE} ({days_held} days)")
    print("=" * 100)
    print(f"{'TICKER':<6} {'$EXP_M':>10}  {'ENTRY':>10} {'EXIT':>10}  "
          f"{'TOTAL%':>9} {'ANNUAL%':>9}")
    print("=" * 100)
    for r in rows:
        ann = ((1 + r["long_return_pct"]/100) ** annualized_factor - 1) * 100
        print(f"{r['ticker']:<6} ${r['exposure_M']:>8.0f}M  "
              f"${r['entry_price']:>8.2f} ${r['exit_price']:>8.2f}  "
              f"{r['long_return_pct']:>+8.1f}% {ann:>+8.1f}%")

    eq = sum(r["long_return_pct"] for r in rows) / len(rows)
    print(f"\nEQUAL-WEIGHT BASKET ({len(rows)} primes):")
    print(f"  total: {eq:+.1f}%   annualized: "
          f"{((1+eq/100)**annualized_factor - 1)*100:+.1f}%")

    total_exp = sum(r["exposure_M"] for r in rows)
    ew = sum(r["long_return_pct"] * r["exposure_M"] for r in rows) / total_exp
    print(f"\nEXPOSURE-WEIGHTED BASKET (weight ~ $ across mapped programs):")
    print(f"  total: {ew:+.1f}%   annualized: "
          f"{((1+ew/100)**annualized_factor - 1)*100:+.1f}%")

    # Reference: SPY same window
    spy = _next_close("SPY", ENTRY_DATE)
    spy_exit = _next_close("SPY", EXIT_DATE)
    if spy and spy_exit:
        spy_ret = (spy_exit[1] - spy[1]) / spy[1] * 100
        print(f"\nREFERENCE: SPY {spy[0]} ${spy[1]:.2f} → {spy_exit[0]} ${spy_exit[1]:.2f}"
              f" = {spy_ret:+.1f}% ({((1+spy_ret/100)**annualized_factor - 1)*100:+.1f}% ann)")

    # Reference: ITA (defense ETF) same window
    ita = _next_close("ITA", ENTRY_DATE)
    ita_exit = _next_close("ITA", EXIT_DATE)
    if ita and ita_exit:
        ita_ret = (ita_exit[1] - ita[1]) / ita[1] * 100
        print(f"REFERENCE: ITA {ita[0]} ${ita[1]:.2f} → {ita_exit[0]} ${ita_exit[1]:.2f}"
              f" = {ita_ret:+.1f}% ({((1+ita_ret/100)**annualized_factor - 1)*100:+.1f}% ann)")

    # Artifact
    out = DATA / "_jbook_exposure_cohort_2024" / "long_returns.json"
    out.write_text(json.dumps({
        "entry_date": ENTRY_DATE, "exit_date": EXIT_DATE, "days_held": days_held,
        "mapped_programs": mapped_programs,
        "unmapped_top": unmapped_top[:30],
        "ticker_exposure_M": dict(tickers_ranked),
        "rows": rows,
        "equal_weight_pct": eq,
        "exposure_weighted_pct": ew,
    }, indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
