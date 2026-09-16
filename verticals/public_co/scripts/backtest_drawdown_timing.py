"""
Test whether the drawdowns we observed for high-composite names happen
within ~1 quarter of a J-Book release.

For each ticker's peak-to-trough drawdown:
  - Did a J-Book release fall between peak date and trough date?
  - How many days from each J-Book release to the start of the drawdown?
  - How many days from each J-Book release to the bottom of the drawdown?
  - Did the trough complete within 90/120 days of a J-Book release?
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path("verticals/public_co/data/_jbook_exposure_cohort_2024")
ARC = json.loads((DATA / "arc_4year.json").read_text())

# J-Book / President's Budget release dates
JBOOK_DATES = [
    ("FY23_PB", "2022-03-28"),
    ("FY24_PB", "2023-03-09"),
    ("FY25_PB", "2024-03-11"),
    ("FY26_PB", "2025-06-15"),
    ("FY27_PB", "2026-04-28"),
]


def _days_between(a: str, b: str) -> int:
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).days


def _nearest_jbook_release(date_iso: str) -> tuple[str, int]:
    """Find the J-Book release closest in time (signed); negative if release was before date."""
    d = datetime.fromisoformat(date_iso)
    best = None
    for label, jd in JBOOK_DATES:
        delta = (d - datetime.fromisoformat(jd)).days
        if best is None or abs(delta) < abs(best[1]):
            best = (label, delta)
    return best


def _jbook_releases_in_window(start_iso: str, end_iso: str) -> list[tuple[str, str]]:
    """List J-Book releases that fall WITHIN [start, end]."""
    return [(label, d) for label, d in JBOOK_DATES if start_iso <= d <= end_iso]


def main():
    # Take only tickers with non-zero composite and meaningful drawdown
    rows = [r for r in ARC["rows"]
             if r.get("backtest_composite") is not None
             and r["peak_to_trough_pct"] < -25]   # only material drawdowns
    rows.sort(key=lambda r: -r["backtest_composite"])

    print(f"Drawdown timing analysis — {len(rows)} tickers with >25% peak-to-trough DD\n")
    print(f"{'TICKER':<6} {'COMP':>5}  {'PEAK DT':<11} {'TROUGH DT':<11} "
          f"{'DD%':>6} {'PEAK→TR DAYS':>13}  J-BOOK RELEASES IN PEAK→TROUGH WINDOW")
    print("=" * 130)

    pre_pb_drawdowns = 0
    post_pb_drawdowns = 0
    spans_pb = 0
    no_pb_match = 0

    for r in rows:
        peak_dt = r["peak_date"]
        trough_dt = r["trough_after_peak_date"]
        dur = _days_between(peak_dt, trough_dt)
        pbs_in = _jbook_releases_in_window(peak_dt, trough_dt)
        if pbs_in:
            spans_pb += 1
            pb_str = ", ".join(f"{label}@{d}" for label, d in pbs_in)
        else:
            # Find nearest before/after
            nearest = _nearest_jbook_release(trough_dt)
            pb_str = f"none in window (nearest: {nearest[0]} {nearest[1]:+d}d from trough)"
            no_pb_match += 1

        print(f"{r['ticker']:<6} {r['backtest_composite']:>5.2f}  "
              f"{peak_dt:<11} {trough_dt:<11} "
              f"{r['peak_to_trough_pct']:>+5.1f}% {dur:>13}  {pb_str}")

    # Per-J-Book-release: how many drawdowns started or ended within 90d of each release?
    print(f"\n\nDRAWDOWN-WINDOWS BY J-BOOK RELEASE")
    print("=" * 100)
    for label, jd in JBOOK_DATES:
        jd_dt = datetime.fromisoformat(jd)
        in_90d_after_start = []   # drawdowns that BEGAN within 90 days after release
        ended_90d_after_start = []  # drawdowns that ENDED within 90 days after release
        in_90d_before_end = []  # drawdowns that began within 90 days BEFORE release
        for r in rows:
            peak_d = datetime.fromisoformat(r["peak_date"])
            trough_d = datetime.fromisoformat(r["trough_after_peak_date"])
            d_to_peak = (peak_d - jd_dt).days
            d_to_trough = (trough_d - jd_dt).days
            # Did the drawdown START within ±90 days of release?
            if -90 <= d_to_peak <= 90:
                in_90d_after_start.append(f"{r['ticker']}({d_to_peak:+d}d)")
            # Did the drawdown END within ±90 days of release?
            if -90 <= d_to_trough <= 90:
                ended_90d_after_start.append(f"{r['ticker']}({d_to_trough:+d}d)")
        print(f"\n  {label} ({jd}):")
        if in_90d_after_start:
            print(f"    Drawdowns BEGAN ±90d of release: {', '.join(in_90d_after_start)}")
        if ended_90d_after_start:
            print(f"    Drawdowns ENDED  ±90d of release: {', '.join(ended_90d_after_start)}")

    # Summary
    print(f"\n\nSUMMARY")
    print(f"  Drawdowns spanning at least one J-Book release in [peak, trough]:  {spans_pb} / {len(rows)}")
    print(f"  Drawdowns entirely between J-Book releases (no PB in window):      {no_pb_match} / {len(rows)}")


if __name__ == "__main__":
    main()
