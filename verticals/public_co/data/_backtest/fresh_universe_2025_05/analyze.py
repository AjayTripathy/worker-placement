"""Phase 4 analysis for fresh-universe framework alpha test.

After Phase 1 (planners) + Phase 2 (plan_executor) + Phase 3 (scorer)
have produced scores.json for each of the 8 names, this script:

  1. Computes composite_score + severity_counts per name
  2. Applies is_truth_signal (dual-gate emit rule)
  3. Applies discovery_advantage filter (HIGH/MED/UNKNOWN keep, LOW suppress)
  4. Buckets names into:
     - framework_emit:    truth_signal AND DA != LOW
     - truth_no_DA:       truth_signal but DA == LOW
     - no_truth_signal:   doesn't pass emit gate
  5. For each bucket, computes:
     - mean / median forward return
     - sector-hedged pair P&L (entry 2025-05-15, exit 2026-05-15)
  6. Compares framework's discrimination against the full-8 baseline

The headline number is: does the framework's emit subset have
significantly different forward return from the no-emit subset?
"""
from __future__ import annotations

import json
import statistics
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import pandas as pd
import yfinance as yf

HERE = Path(__file__).parent
BACKTEST_DIR = Path("verticals/public_co/data/_backtest/2025_05_15")


# Forward returns from v1 AIRO backtest (already computed)
FORWARD_RETURNS = {
    "LRHC": -0.999,  # -99.9%
    "KULR": -0.696,
    "HDSN": -0.376,
    "PESI": +0.018,
    "CWCO": +0.131,
    "CDNA": +0.240,
    "ALMU": +1.034,  # +103.4%
    "KLIC": +2.045,  # +204.5%
}

ENTRY = "2025-05-15"
EXIT  = "2026-05-15"

# Sector ETF mapping (live; classify via yfinance.info)
SECTOR_TO_ETF = {
    "Communication Services": "XLC", "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP", "Energy": "XLE",
    "Financial Services": "XLF", "Healthcare": "XLV",
    "Industrials": "XLI", "Technology": "XLK",
    "Utilities": "XLU", "Real Estate": "XLRE", "Basic Materials": "XLB",
}
BIOTECH_INDS = {"Biotechnology", "Drug Manufacturers - Specialty & Generic",
                "Drug Manufacturers - General", "Diagnostics & Research"}
SEMI_INDS = {"Semiconductors", "Semiconductor Equipment & Materials"}


def classify_etf(sector: str | None, industry: str | None) -> str:
    if industry in BIOTECH_INDS: return "XBI"
    if industry in SEMI_INDS:    return "SMH"
    return SECTOR_TO_ETF.get(sector, "IWM")


def etf_return(etf: str) -> float | None:
    try:
        h = yf.Ticker(etf).history(start="2025-05-01", end="2026-05-20", auto_adjust=True)
        if h.empty: return None
        e_idx = h.index.get_indexer([pd.Timestamp(ENTRY, tz=h.index.tz)], method="nearest")[0]
        x_idx = h.index.get_indexer([pd.Timestamp(EXIT,  tz=h.index.tz)], method="nearest")[0]
        return float(h.iloc[x_idx]["Close"]) / float(h.iloc[e_idx]["Close"]) - 1
    except Exception:
        return None


def get_ticker_sector(tk: str) -> tuple[str|None, str|None]:
    try:
        info = yf.Ticker(tk).info or {}
        return info.get("sector"), info.get("industry")
    except Exception:
        return None, None


def main():
    from verticals.public_co.forward_bet_emission import EMIT_DA_TIERS, is_truth_signal
    from verticals.public_co.discovery_advantage import compute_discovery_advantage

    tickers = list(FORWARD_RETURNS.keys())
    rows = []
    for tk in tickers:
        # Load scores
        scores_path = BACKTEST_DIR / f"{tk}.scores.json"
        if not scores_path.exists():
            print(f"  {tk}: NO SCORES on disk — skipping")
            continue
        data = json.loads(scores_path.read_text())
        scores = data.get("scores", [])
        # Counts + composite
        counts = {}
        SEV_W = {"SEVERE_UNDERDELIVERY":2.0,"RED_FLAG_NEGATIVE":3.0,
                 "MODERATE_UNDERDELIVERY":1.0,"PASS":0.0,"UNVERIFIABLE":0.0}
        counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
        comp = sum(SEV_W.get(s.get("severity"), 0) for s in counted) / max(1, len(counted))
        for s in scores:
            sev = s.get("severity", "UNVERIFIABLE")
            counts[sev] = counts.get(sev, 0) + 1
        # Sector ETF
        sector, industry = get_ticker_sector(tk)
        etf = classify_etf(sector, industry)
        r_etf = etf_return(etf)
        r_name = FORWARD_RETURNS[tk]
        pair_pnl = (r_etf - r_name) if r_etf is not None else None
        # Truth signal + DA
        ts = is_truth_signal({"composite_score": comp, "severity_counts": counts})
        da = compute_discovery_advantage(tk)
        da_tier = da.get("tier")
        emit = ts and da_tier in EMIT_DA_TIERS
        rows.append({
            "ticker":     tk,
            "composite":  comp,
            "counts":     counts,
            "truth_signal": ts,
            "da_tier":    da_tier,
            "emit":       emit,
            "sector":     sector,
            "industry":   industry,
            "etf":        etf,
            "etf_return": r_etf,
            "name_return": r_name,
            "pair_pnl":   pair_pnl,
        })

    # Output
    print(f"{'TK':5s} {'comp':>5s} {'R/S/M':>7s} {'TS':>3s} {'DA':>4s} {'EMIT':>5s} "
          f"{'etf':>5s} {'name_R':>8s} {'etf_R':>7s} {'pair':>7s}")
    print("=" * 85)
    for r in sorted(rows, key=lambda r: -(r.get("pair_pnl") or -99)):
        c = r["counts"]
        rsm = f"{c.get('RED_FLAG_NEGATIVE',0)}/{c.get('SEVERE_UNDERDELIVERY',0)}/{c.get('MODERATE_UNDERDELIVERY',0)}"
        ts_s = "Y" if r["truth_signal"] else "n"
        emit_s = "EMIT" if r["emit"] else "  -"
        nr = f"{r['name_return']*100:+7.1f}%"
        er = f"{r['etf_return']*100:+6.1f}%" if r['etf_return'] is not None else "    ?"
        pp = f"{r['pair_pnl']*100:+6.1f}%" if r['pair_pnl'] is not None else "    ?"
        print(f"  {r['ticker']:5s} {r['composite']:>5.2f} {rsm:>7s} {ts_s:>2s}  {r['da_tier'] or '?':>4s} {emit_s:>5s} "
              f"{r['etf']:>5s} {nr:>7s} {er:>7s} {pp:>7s}")

    # Bucket analysis
    emit_set    = [r for r in rows if r["emit"]]
    truth_no_da = [r for r in rows if r["truth_signal"] and not r["emit"]]
    no_truth    = [r for r in rows if not r["truth_signal"]]
    print()
    for label, bucket in [("EMIT (truth_signal AND DA != LOW)", emit_set),
                          ("Truth-signal, DA blocked (LOW)", truth_no_da),
                          ("No truth signal", no_truth)]:
        prs = [r["pair_pnl"] for r in bucket if r["pair_pnl"] is not None]
        names = [r["ticker"] for r in bucket]
        if prs:
            print(f"  {label:40s}: n={len(prs):2d}  mean pair={statistics.mean(prs)*100:+7.2f}%  "
                  f"median={statistics.median(prs)*100:+7.2f}%  names={names}")
        else:
            print(f"  {label:40s}: n=0   (empty)  names={names}")
    # Full-8 baseline
    all_prs = [r["pair_pnl"] for r in rows if r["pair_pnl"] is not None]
    print(f"  {'Full-8 baseline':40s}: n={len(all_prs):2d}  mean pair={statistics.mean(all_prs)*100:+7.2f}%  "
          f"median={statistics.median(all_prs)*100:+7.2f}%")

    # Save
    (HERE / "framework_emit_analysis.json").write_text(
        json.dumps(rows, indent=2, default=str)
    )


if __name__ == "__main__":
    main()
