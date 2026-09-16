"""
4-year arc study: 2022-01-01 → 2026-05-20 across the cohort.

For each ticker:
  - 4-year total return (entry 2022-01-03, exit 2026-05-20)
  - All-time high in window + date
  - All-time low in window + date
  - Max drawdown from peak
  - Time-from-peak to trough
  - 2024-09-01 backtest composite (if available)

Correlate composite ↔ outcome to see whether J-Book divergence (as
measured at 2024) was a leading indicator of long-run underperformance,
a lagging description of names that had already de-rated, or
uncorrelated noise.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import yfinance as yf

DATA = Path("verticals/public_co/data")
COMPOSITES_PATH = DATA / "_jbook_exposure_cohort_2024" / "matrix.json"

START = "2022-01-01"
END   = "2026-05-21"   # +1 day so 2026-05-20 close is included


TICKERS = [
    # 13 cohort
    "IONQ", "ARQQ", "QBTS", "QUBT", "RGTI",
    "RKLB", "ASTS", "RDW", "PL",
    "BBAI", "RCAT", "AIRO", "KTOS",
    # Phase 2 expansion (defense mid-caps)
    "AVAV", "BWXT", "CACI", "SAIC", "LDOS",
    "MRCY", "CW", "HEI", "TDG", "VSAT",
    # Phase 3 expansion (big primes + sub-tier suppliers)
    "LMT", "NOC", "RTX", "BA", "LHX",
    "HII", "HXL", "MOG-A", "TXT",
    "EH",
    # Benchmarks
    "ITA", "SPY",
]


SEVERITY_WEIGHT = {
    "PASS": 0.0, "UNVERIFIABLE": 0.0,
    "MODERATE_UNDERDELIVERY": 1.0,
    "SEVERE_UNDERDELIVERY": 2.0,
    "RED_FLAG_NEGATIVE": 3.0,
}


def _compute_composite_from_scores_file(path: Path) -> dict | None:
    """Read a <TICKER>.jbook.2024.scores.json file, return composite + severity counts."""
    if not path.exists():
        return None
    j = json.loads(path.read_text())
    scores = j.get("scores", [])
    from collections import Counter
    c = Counter(s.get("severity") for s in scores)
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    composite = (sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted)
                  / max(1, len(counted))) if counted else 0.0
    return {
        "backtest_composite": composite,
        "n_red":  c.get("RED_FLAG_NEGATIVE", 0),
        "n_seve": c.get("SEVERE_UNDERDELIVERY", 0),
        "n_mod":  c.get("MODERATE_UNDERDELIVERY", 0),
    }


def _load_composites() -> dict:
    out = {}
    # 1) Original cohort matrix from the 2024 backtest aggregator
    if COMPOSITES_PATH.exists():
        m = json.loads(COMPOSITES_PATH.read_text())
        for row in m:
            if row.get("status") == "OK":
                out[row["ticker"]] = {
                    "backtest_composite":  row["backtest_composite"],
                    "forward_composite":   row.get("forward_composite"),
                    "n_red":  row["backtest_severity_counts"]["RED_FLAG_NEGATIVE"],
                    "n_seve": row["backtest_severity_counts"]["SEVERE_UNDERDELIVERY"],
                    "n_mod":  row["backtest_severity_counts"]["MODERATE_UNDERDELIVERY"],
                }
    # 2) Phase 2a new tickers — read each <T>.jbook.2024.scores.json directly
    local = Path("verticals/public_co/data/_local")
    PHASE_TICKERS = ["CACI","SAIC","LDOS","MRCY","CW","HEI","TDG","VSAT","AVAV","BWXT",
                      "LMT","NOC","RTX","BA","LHX","HII","HXL","MOG-A","TXT"]
    for tk in PHASE_TICKERS:
        if tk in out:
            continue  # already covered by matrix.json
        c = _compute_composite_from_scores_file(local / f"{tk}.jbook.2024.scores.json")
        if c:
            out[tk] = c
    return out


def _fetch_arc(ticker: str):
    try:
        df = yf.download(ticker, start=START, end=END,
                          progress=False, auto_adjust=False)
    except Exception as e:
        print(f"  ! yf err {ticker}: {e}", file=sys.stderr)
        return None
    if df is None or df.empty:
        return None
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    series = df[col]
    if hasattr(series, "values"):
        vals = series.values
        if vals.ndim > 1:
            vals = vals[:, 0]
    else:
        vals = np.array(series)
    return {"dates": [d.date() for d in df.index], "prices": vals}


def _analyze(ticker: str, arc: dict, composite: dict | None):
    p = arc["prices"]
    d = arc["dates"]
    if len(p) < 50:
        return None

    entry_px = float(p[0])
    entry_dt = d[0]
    exit_px  = float(p[-1])
    exit_dt  = d[-1]
    total_ret = (exit_px - entry_px) / entry_px * 100

    max_i = int(np.argmax(p))
    min_i = int(np.argmin(p))
    peak_px = float(p[max_i]); peak_dt = d[max_i]
    low_px  = float(p[min_i]); low_dt  = d[min_i]

    # Drawdown from peak: look at min AFTER the peak
    if max_i + 1 < len(p):
        post_peak = p[max_i + 1:]
        trough_offset = int(np.argmin(post_peak))
        trough_after_peak = float(post_peak[trough_offset])
        trough_after_peak_dt = d[max_i + 1 + trough_offset]
        peak_to_trough_pct = (trough_after_peak - peak_px) / peak_px * 100
    else:
        trough_after_peak = peak_px
        trough_after_peak_dt = peak_dt
        peak_to_trough_pct = 0.0

    return {
        "ticker":             ticker,
        "entry_date":         str(entry_dt),
        "entry_price":        entry_px,
        "exit_date":          str(exit_dt),
        "exit_price":         exit_px,
        "total_return_pct":   total_ret,
        "peak_price":         peak_px,
        "peak_date":          str(peak_dt),
        "low_price":          low_px,
        "low_date":           str(low_dt),
        "trough_after_peak":  trough_after_peak,
        "trough_after_peak_date": str(trough_after_peak_dt),
        "peak_to_trough_pct": peak_to_trough_pct,
        "backtest_composite": composite.get("backtest_composite") if composite else None,
        "n_red":              composite.get("n_red") if composite else None,
        "n_seve":             composite.get("n_seve") if composite else None,
    }


def main():
    composites = _load_composites()
    print(f"Loaded composites for {len(composites)} tickers", file=sys.stderr)

    rows = []
    for tk in TICKERS:
        print(f"  fetching {tk}…", file=sys.stderr)
        arc = _fetch_arc(tk)
        if not arc:
            print(f"    no data", file=sys.stderr)
            continue
        r = _analyze(tk, arc, composites.get(tk))
        if r:
            rows.append(r)

    # Sort by composite desc (NA at bottom)
    def _sort_key(r):
        c = r.get("backtest_composite")
        return (-c if c is not None else 1e9, -r["total_return_pct"])
    rows.sort(key=_sort_key)

    # Print table
    print()
    exit_date_s = rows[0]['exit_date'] if rows else END
    print(f"4-YEAR ARC — {START} to {exit_date_s}")
    print("=" * 130)
    print(f"{'TICKER':<6} {'BT_COMP':>7} {'RED':>3} {'SEVE':>4}  "
          f"{'ENTRY $':>8} {'EXIT $':>8} {'TOTAL %':>9}  "
          f"{'PEAK':>8} {'PEAK DT':<11} "
          f"{'POST-PEAK TROUGH':>10} {'TROUGH DT':<11} {'DD %':>7}")
    print("=" * 130)
    for r in rows:
        bc = r.get("backtest_composite")
        bc_s = f"{bc:.2f}" if bc is not None else "  -- "
        red = r.get("n_red")
        red_s = f"{red}" if red is not None else "-"
        sev = r.get("n_seve")
        sev_s = f"{sev}" if sev is not None else "-"
        print(f"{r['ticker']:<6} {bc_s:>7} {red_s:>3} {sev_s:>4}  "
              f"${r['entry_price']:>7.2f} ${r['exit_price']:>7.2f} "
              f"{r['total_return_pct']:>+8.1f}%  "
              f"${r['peak_price']:>7.2f} {r['peak_date']:<11} "
              f"${r['trough_after_peak']:>8.2f} "
              f"{r['trough_after_peak_date']:<11} "
              f"{r['peak_to_trough_pct']:>+6.1f}%")

    # Correlations
    paired = [r for r in rows if r.get("backtest_composite") is not None
               and r["ticker"] not in ("ITA","SPY")]
    if paired:
        comps = np.array([r["backtest_composite"] for r in paired])
        totals = np.array([r["total_return_pct"] for r in paired])
        dds    = np.array([r["peak_to_trough_pct"] for r in paired])
        if len(paired) > 1:
            corr_total = np.corrcoef(comps, totals)[0,1]
            corr_dd    = np.corrcoef(comps, dds)[0,1]
            print()
            print(f"Correlation (composite vs 4yr total return):  {corr_total:+.3f}")
            print(f"Correlation (composite vs peak-to-trough dd): {corr_dd:+.3f}")

    # Write artifact
    out = DATA / "_jbook_exposure_cohort_2024" / "arc_4year.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"start": START, "end": END, "rows": rows},
                                indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
