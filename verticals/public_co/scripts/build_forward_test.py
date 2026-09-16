"""
Build the live forward-test prescription for the FY27 → FY28 PB cycle.

For each ticker in the cohort:
  - Pull the most recent framework composite available
  - Tag as LONG (≤ 0.20), SHORT (≥ 0.50), or NEUTRAL (0.20 < x < 0.50)
  - Pull current price (close on 2026-05-20)

Output: forward_test_FY27_FY28.json with the live prescription.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import yfinance as yf

DATA = Path("verticals/public_co/data")
TODAY = "2026-05-20"
NEXT_PB_EST = "2027-03-15"  # estimate FY28 PB release
ENTRY_TARGETS = {
    "early_2026_05_20":  "2026-05-20",   # entry today
    "canonical_T_minus_60": "2027-01-15",  # canonical T-60 before FY28 PB
}
LONG_THRESHOLD  = 0.20
SHORT_THRESHOLD = 0.50

SEVERITY_WEIGHT = {"PASS":0.0,"UNVERIFIABLE":0.0,"MODERATE_UNDERDELIVERY":1.0,
                    "SEVERE_UNDERDELIVERY":2.0,"RED_FLAG_NEGATIVE":3.0}


def _composite_from_file(path: Path):
    if not path.exists():
        return None
    j = json.loads(path.read_text())
    scores = j.get("scores", [])
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted:
        return 0.0
    return sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted) / len(counted)


def _load_best_composite(ticker: str) -> tuple[float | None, str]:
    """Return (composite, vintage_label) using the most recent available run."""
    local = DATA / "_local"
    # Prefer forward (2026-05-20) > 2024 > 2022
    fwd_path = local / f"{ticker}.jbook.input.json"
    fwd_sco  = local / f"{ticker}.jbook.scores.json"
    # The forward test (2026-05-20 cutoff) wrote to the bare .jbook.* files
    # The 2024 backtest wrote to .jbook.2024.* and the 2022 to .jbook.2022.*
    if fwd_sco.exists():
        return (_composite_from_file(fwd_sco), "forward_2026_05_20")
    sco24 = local / f"{ticker}.jbook.2024.scores.json"
    if sco24.exists():
        return (_composite_from_file(sco24), "backtest_2024_09_01")
    sco22 = local / f"{ticker}.jbook.2022.scores.json"
    if sco22.exists():
        return (_composite_from_file(sco22), "backtest_2022_06_01")
    return (None, "no_run")


def _close_on(ticker: str, date_iso: str):
    from datetime import timedelta
    start = datetime.fromisoformat(date_iso)
    end = start + timedelta(days=7)
    try:
        df = yf.download(ticker, start=date_iso, end=end.strftime("%Y-%m-%d"),
                          progress=False, auto_adjust=False)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    row = df.iloc[0]
    v = row[col]
    if hasattr(v, "item"):
        v = v.item()
    return (str(df.index[0].date()), float(v))


# Universe: 13 cohort + 10 Phase 2 expansion. AIRO excluded (no pre-2024 data).
COHORT_TICKERS = [
    "IONQ","ARQQ","QBTS","QUBT","RGTI","RKLB","ASTS","RDW","PL",
    "BBAI","RCAT","KTOS",
    "AVAV","BWXT","CACI","SAIC","LDOS","MRCY","CW","HEI","TDG","VSAT",
    "LMT","NOC","RTX","BA","LHX","HII","HXL","MOG-A","TXT",
]


def main():
    rows = []
    for tk in COHORT_TICKERS:
        comp, vintage = _load_best_composite(tk)
        if comp is None:
            print(f"  ! {tk}: no composite available", file=sys.stderr)
            continue
        cur = _close_on(tk, TODAY)
        if not cur:
            print(f"  ! {tk}: no current price", file=sys.stderr)
            continue
        if comp <= LONG_THRESHOLD:
            side = "LONG"
        elif comp >= SHORT_THRESHOLD:
            side = "SHORT"
        else:
            side = "NEUTRAL"
        rows.append({
            "ticker":          tk,
            "composite":       comp,
            "vintage":         vintage,
            "side":            side,
            "current_date":    cur[0],
            "current_price":   cur[1],
        })
        print(f"  {tk:<6} comp={comp:.2f}  {side:<8}  vintage={vintage:<22}  "
              f"current ${cur[1]:.2f}", file=sys.stderr)

    # Rank: longs ascending by composite (cleanest first), shorts descending (most divergent first)
    longs   = sorted([r for r in rows if r["side"] == "LONG"],   key=lambda x: x["composite"])
    shorts  = sorted([r for r in rows if r["side"] == "SHORT"],  key=lambda x: -x["composite"])
    neutral = sorted([r for r in rows if r["side"] == "NEUTRAL"], key=lambda x: x["composite"])

    artifact = {
        "_meta": {
            "today":          TODAY,
            "next_pb_estimated": NEXT_PB_EST,
            "long_threshold":  LONG_THRESHOLD,
            "short_threshold": SHORT_THRESHOLD,
            "entry_windows":   ENTRY_TARGETS,
            "exit_event":      "FY28 PB release (~March 2027)",
            "validated_alpha_reference": "Methodology section 12",
        },
        "long_basket":   longs,
        "short_basket":  shorts,
        "neutral":       neutral,
    }

    out_dir = DATA / "_jbook_exposure_cohort"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "forward_test_FY27_FY28.json"
    out_path.write_text(json.dumps(artifact, indent=2, default=str))
    print(f"\nWrote {out_path}")

    # Print clean table
    print(f"\n{'#' * 100}")
    print(f"# FORWARD TEST — FY27 → FY28 PB CYCLE")
    print(f"# Today: {TODAY}    Next PB estimate: {NEXT_PB_EST}")
    print(f"# Entry windows: early {ENTRY_TARGETS['early_2026_05_20']}, canonical {ENTRY_TARGETS['canonical_T_minus_60']}")
    print(f"{'#' * 100}")

    def _show(label, basket):
        print(f"\n  {label} basket (n={len(basket)}):")
        print(f"  {'TICKER':<7} {'COMP':>5}  {'PRICE':>9}  {'VINTAGE':<25}")
        for r in basket:
            print(f"  {r['ticker']:<7} {r['composite']:>5.2f}  "
                  f"${r['current_price']:>7.2f}  {r['vintage']:<25}")

    _show("LONG  (composite ≤ 0.20)", longs)
    _show("SHORT (composite ≥ 0.50)", shorts)
    _show("NEUTRAL (0.20 < composite < 0.50)", neutral)


if __name__ == "__main__":
    main()
