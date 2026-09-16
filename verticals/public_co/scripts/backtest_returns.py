"""
Out-of-sample returns for the J-Book exposure backtest.

Universe filter:
  - Remove IONQ — in-sample (the AFRL Quantum Networking program was
    hand-curated into the corpus *because* of the Wolfpack short report,
    so the framework "catching" it isn't out-of-sample evidence).
  - Remove ARQQ — UK 20-F filer; US borrow availability historically poor.
  - Remove AIRO — IPO'd 2024-06; no usable pre-2024-09-01 filing.

Entry: 2024-09-01 close (using next-available trading day's open / close)
Exit:  2026-05-20 close

Returns:
  short_return = (entry_close - exit_close) / entry_close
  After borrow:  short_return − (borrow_bps × days_held / 365)

Reports:
  - Per-ticker P&L
  - Equal-weight basket
  - Composite-weighted basket (weight ~ backtest composite score; tickers
    with composite < threshold get weight 0)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yfinance as yf

DATA = Path("verticals/public_co/data")
BACKTEST_MATRIX = DATA / "_jbook_exposure_cohort_2024" / "matrix.json"

ENTRY_DATE = "2024-09-01"
EXIT_DATE  = "2026-05-20"
BORROW_BPS_PER_YEAR = 500   # 5% annual borrow cost — conservative-but-realistic
                              # for small-cap defense/quantum names

EXCLUDED_FROM_UNIVERSE = {
    "IONQ":  "in-sample (AFRL Quantum Networking curated into corpus per Wolfpack report)",
    "ARQQ":  "UK 20-F filer; US borrow availability poor",
    "AIRO":  "IPO 2024-06; no pre-cutoff filing usable",
}


def _next_close_after(ticker: str, date_iso: str, max_days: int = 7) -> Optional[tuple[str, float]]:
    """Get the first available close at or after date_iso. Returns (date, close)."""
    start = datetime.fromisoformat(date_iso)
    end_iso = (start.replace(year=start.year, month=start.month, day=min(28, start.day + max_days))).strftime("%Y-%m-%d")
    try:
        df = yf.download(ticker, start=date_iso, end=end_iso,
                          progress=False, auto_adjust=False)
    except Exception as e:
        print(f"  ! yf.download err for {ticker}: {e}", file=sys.stderr)
        return None
    if df is None or df.empty:
        return None
    # Prefer Adj Close (handles splits/dividends); fall back to Close
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    row = df.iloc[0]
    val = row[col]
    if hasattr(val, "item"):
        val = val.item()
    return (str(df.index[0].date()), float(val))


def main():
    matrix = json.loads(BACKTEST_MATRIX.read_text())
    backtest_rows = {r["ticker"]: r for r in matrix if r.get("status") == "OK"}
    print(f"Backtest rows: {len(backtest_rows)} tickers", file=sys.stderr)

    # Build universe
    universe = [tk for tk in backtest_rows if tk not in EXCLUDED_FROM_UNIVERSE]
    print(f"Universe after exclusions: {len(universe)} tickers", file=sys.stderr)
    for tk, reason in EXCLUDED_FROM_UNIVERSE.items():
        print(f"  EXCLUDED {tk}: {reason}", file=sys.stderr)

    # Fetch prices
    prices = {}
    for tk in universe:
        entry = _next_close_after(tk, ENTRY_DATE)
        exit  = _next_close_after(tk, EXIT_DATE)
        if not entry or not exit:
            print(f"  ! {tk}: price fetch failed entry={entry} exit={exit}",
                  file=sys.stderr)
            continue
        prices[tk] = {"entry": entry, "exit": exit}
        print(f"  {tk}: entry {entry[0]} ${entry[1]:.2f}  →  exit {exit[0]} ${exit[1]:.2f}",
              file=sys.stderr)

    # Compute returns
    days_held = (datetime.fromisoformat(EXIT_DATE)
                  - datetime.fromisoformat(ENTRY_DATE)).days
    borrow_drag = BORROW_BPS_PER_YEAR / 10000 * days_held / 365

    rows = []
    for tk, p in prices.items():
        ep = p["entry"][1]
        xp = p["exit"][1]
        gross_short = (ep - xp) / ep  # positive = short was profitable
        net_short = gross_short - borrow_drag
        rows.append({
            "ticker":          tk,
            "entry_date":      p["entry"][0],
            "entry_price":     ep,
            "exit_date":       p["exit"][0],
            "exit_price":      xp,
            "gross_return_pct": gross_short * 100,
            "net_return_pct":   net_short * 100,
            "bt_composite":    backtest_rows[tk]["backtest_composite"],
            "bt_red":          backtest_rows[tk]["backtest_severity_counts"]["RED_FLAG_NEGATIVE"],
            "bt_seve":         backtest_rows[tk]["backtest_severity_counts"]["SEVERE_UNDERDELIVERY"],
        })

    # Sort by backtest composite (the signal we'd act on)
    rows.sort(key=lambda r: -r["bt_composite"])

    # Per-ticker table
    print()
    print(f"OUT-OF-SAMPLE SHORT RETURNS — {len(rows)} tickers, "
          f"{ENTRY_DATE} → {EXIT_DATE} ({days_held} days)")
    print(f"Borrow drag applied: {borrow_drag*100:.1f}% "
          f"({BORROW_BPS_PER_YEAR}bps/yr × {days_held}/365)")
    print("=" * 100)
    print(f"{'TICKER':<7} {'BT_COMP':>8} {'RED':>4} {'SEVE':>5}  "
          f"{'ENTRY':>10} {'EXIT':>10}  {'GROSS%':>9} {'NET%':>9}")
    print("=" * 100)
    for r in rows:
        print(f"{r['ticker']:<7} {r['bt_composite']:>8.2f} "
              f"{r['bt_red']:>4} {r['bt_seve']:>5}  "
              f"${r['entry_price']:>8.2f} ${r['exit_price']:>8.2f}  "
              f"{r['gross_return_pct']:>+8.1f}% {r['net_return_pct']:>+8.1f}%")

    # Equal-weight
    eq_gross = sum(r["gross_return_pct"] for r in rows) / max(1, len(rows))
    eq_net   = sum(r["net_return_pct"]   for r in rows) / max(1, len(rows))
    print()
    print(f"EQUAL-WEIGHT BASKET (all {len(rows)} shortable):")
    print(f"  gross: {eq_gross:+.1f}%   net: {eq_net:+.1f}%")

    # Composite-weighted (signal strength)
    total_w = sum(r["bt_composite"] for r in rows)
    if total_w > 0:
        cw_gross = sum(r["gross_return_pct"] * r["bt_composite"] for r in rows) / total_w
        cw_net   = sum(r["net_return_pct"]   * r["bt_composite"] for r in rows) / total_w
        print(f"\nCOMPOSITE-WEIGHTED BASKET (weight = backtest composite):")
        print(f"  gross: {cw_gross:+.1f}%   net: {cw_net:+.1f}%")

    # Top-half by signal (cut at median composite)
    medians = sorted(r["bt_composite"] for r in rows)
    median_comp = medians[len(medians) // 2]
    top = [r for r in rows if r["bt_composite"] >= median_comp]
    if top:
        th_gross = sum(r["gross_return_pct"] for r in top) / len(top)
        th_net   = sum(r["net_return_pct"]   for r in top) / len(top)
        print(f"\nTOP-HALF BY SIGNAL (composite ≥ {median_comp:.2f}, {len(top)} tickers):")
        print(f"  {', '.join(r['ticker'] for r in top)}")
        print(f"  gross: {th_gross:+.1f}%   net: {th_net:+.1f}%")

    # Threshold ≥ 0.50 (signal-bearing only)
    sig = [r for r in rows if r["bt_composite"] >= 0.50]
    if sig:
        sg = sum(r["gross_return_pct"] for r in sig) / len(sig)
        sn = sum(r["net_return_pct"]   for r in sig) / len(sig)
        print(f"\nSIGNAL-BEARING ONLY (composite ≥ 0.50, {len(sig)} tickers):")
        print(f"  {', '.join(r['ticker'] for r in sig)}")
        print(f"  gross: {sg:+.1f}%   net: {sn:+.1f}%")

    # Write artifact
    out_dir = DATA / "_jbook_exposure_cohort_2024"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "entry_date": ENTRY_DATE,
        "exit_date":  EXIT_DATE,
        "days_held":  days_held,
        "borrow_bps_per_year": BORROW_BPS_PER_YEAR,
        "borrow_drag_pct":     borrow_drag * 100,
        "excluded": EXCLUDED_FROM_UNIVERSE,
        "tickers": rows,
        "baskets": {
            "equal_weight_all":      {"gross_pct": eq_gross, "net_pct": eq_net,
                                       "n": len(rows)},
            "composite_weighted":    {"gross_pct": cw_gross if total_w > 0 else None,
                                       "net_pct":   cw_net   if total_w > 0 else None,
                                       "n": len(rows)},
            "top_half_signal":       {"gross_pct": th_gross, "net_pct": th_net,
                                       "n": len(top),
                                       "tickers": [r["ticker"] for r in top]},
            "signal_bearing_only":   {"gross_pct": sg if sig else None,
                                       "net_pct":   sn if sig else None,
                                       "n": len(sig),
                                       "tickers": [r["ticker"] for r in sig]},
        },
    }
    (out_dir / "returns.json").write_text(json.dumps(artifact, indent=2, default=str))
    print(f"\nWrote {out_dir}/returns.json", file=sys.stderr)


if __name__ == "__main__":
    main()
