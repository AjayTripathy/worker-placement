"""
Post-peak / pre-next-PB short backtest.

Trade structure per J-Book release:
  Entry: D + 120 calendar days (post-PB-rally entry; peaks typically ~4-6 mo after PB)
  Exit:  next PB release date
  Universe: tickers with composite ≥ THRESHOLD at the most recent vintage
            cutoff PRIOR to the entry date
  Position weight: equal + composite-weighted

This is a NO-HINDSIGHT rule: entry timing is calendar-driven from publicly-
known PB release dates, not from observed peaks. The composite at entry-
time is the most recent backtest cutoff that occurred BEFORE entry day.

Backtestable events:
  Entry Jul 2023 (FY24 PB + 120) → exit Mar 2024 (FY25 PB)   [246 day hold]
  Entry Jul 2024 (FY25 PB + 120) → exit Jun 2025 (FY26 PB)   [341 day hold]
  Entry Oct 2025 (FY26 PB + 120) → exit Apr 2026 (FY27 PB)   [197 day hold]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

DATA = Path("verticals/public_co/data")

# (PB release date, label, vintage to use at entry, next PB release date OR today)
EVENTS = [
    {"pb_date": "2023-03-09", "label": "FY24_PB",
     "entry_offset": 120, "exit_date": "2024-03-11",
     "vintage": "2022"},
    {"pb_date": "2024-03-11", "label": "FY25_PB",
     "entry_offset": 120, "exit_date": "2025-06-15",
     "vintage": "2022"},
    {"pb_date": "2025-06-15", "label": "FY26_PB",
     "entry_offset": 120, "exit_date": "2026-04-28",
     "vintage": "2024"},
]

THRESHOLDS = [0.50, 0.75, 1.00]

SEVERITY_WEIGHT = {
    "PASS": 0.0, "UNVERIFIABLE": 0.0,
    "MODERATE_UNDERDELIVERY": 1.0,
    "SEVERE_UNDERDELIVERY": 2.0,
    "RED_FLAG_NEGATIVE": 3.0,
}


def _composite_from_file(path: Path) -> float | None:
    if not path.exists():
        return None
    j = json.loads(path.read_text())
    scores = j.get("scores", [])
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted:
        return 0.0
    return sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted) / len(counted)


def _load_composites():
    local = DATA / "_local"
    out = {"2022": {}, "2024": {}}
    for path in local.glob("*.jbook.2022.scores.json"):
        tk = path.name.split(".")[0]
        c = _composite_from_file(path)
        if c is not None:
            out["2022"][tk] = c
    matrix_path = DATA / "_jbook_exposure_cohort_2024" / "matrix.json"
    if matrix_path.exists():
        for row in json.loads(matrix_path.read_text()):
            if row.get("status") == "OK":
                out["2024"][row["ticker"]] = row["backtest_composite"]
    for path in local.glob("*.jbook.2024.scores.json"):
        tk = path.name.split(".")[0]
        if tk in out["2024"]:
            continue
        c = _composite_from_file(path)
        if c is not None:
            out["2024"][tk] = c
    return out


def _next_close_after(ticker: str, date_iso: str, max_pad: int = 7):
    start = datetime.fromisoformat(date_iso)
    end = start + timedelta(days=max_pad)
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


def main():
    composites = _load_composites()

    pooled = {th: [] for th in THRESHOLDS}
    all_results = []

    for event in EVENTS:
        pb_d = datetime.fromisoformat(event["pb_date"])
        entry_target = (pb_d + timedelta(days=event["entry_offset"])).strftime("%Y-%m-%d")
        exit_target  = event["exit_date"]
        vintage = composites[event["vintage"]]

        print(f"\n{'=' * 110}")
        print(f"{event['label']} entry T+{event['entry_offset']}d "
              f"(~{entry_target}) → exit {exit_target}")
        print(f"  Vintage: {event['vintage']}")
        print(f"  Universe: {len(vintage)} tickers with composites; "
              f"composite ≥ {min(THRESHOLDS):.2f}: "
              f"{', '.join(t for t, c in vintage.items() if c >= min(THRESHOLDS))}")
        print(f"{'=' * 110}")

        candidates = sorted(
            [(tk, c) for tk, c in vintage.items() if c >= min(THRESHOLDS)],
            key=lambda x: -x[1],
        )

        rows = []
        for tk, comp in candidates:
            entry = _next_close_after(tk, entry_target)
            exit  = _next_close_after(tk, exit_target)
            if not entry or not exit:
                continue
            short_ret = (entry[1] - exit[1]) / entry[1] * 100
            rows.append({
                "ticker": tk, "composite": comp,
                "entry": entry, "exit": exit,
                "short_return_pct": short_ret,
            })

        print(f"  {'TICKER':<6} {'COMP':>5}  {'ENTRY':<12} {'ENTRY $':>9}  "
              f"{'EXIT':<12} {'EXIT $':>9}  {'SHORT %':>9}")
        for r in rows:
            print(f"  {r['ticker']:<6} {r['composite']:>5.2f}  "
                  f"{r['entry'][0]:<12} ${r['entry'][1]:>7.2f}  "
                  f"{r['exit'][0]:<12} ${r['exit'][1]:>7.2f}  "
                  f"{r['short_return_pct']:>+8.1f}%")

        for th in THRESHOLDS:
            basket = [r for r in rows if r["composite"] >= th]
            if not basket:
                continue
            eq = sum(r["short_return_pct"] for r in basket) / len(basket)
            tw = sum(r["composite"] for r in basket)
            cw = sum(r["short_return_pct"] * r["composite"] for r in basket) / tw if tw else 0
            wins = sum(1 for r in basket if r["short_return_pct"] > 0)
            print(f"  → threshold ≥{th:.2f} (n={len(basket)}): "
                  f"equal {eq:+.1f}%, comp-wtd {cw:+.1f}%, wins {wins}/{len(basket)}")
            pooled[th].append({
                "event": event["label"], "n": len(basket),
                "equal_return": eq, "comp_weighted_return": cw,
                "win_rate": wins / len(basket),
                "names": [r["ticker"] for r in basket],
            })

        all_results.append({"event": event, "rows": rows})

    print(f"\n\n{'=' * 110}")
    print(f"POOLED ACROSS ALL EVENTS")
    print(f"{'=' * 110}")
    for th in THRESHOLDS:
        ps = pooled[th]
        if not ps:
            continue
        n_events = len(ps)
        n_total = sum(p["n"] for p in ps)
        eq_mean = sum(p["equal_return"] for p in ps) / n_events
        cw_mean = sum(p["comp_weighted_return"] for p in ps) / n_events
        wins = sum(p["win_rate"] * p["n"] for p in ps)
        win_rate = wins / n_total
        print(f"\n  Threshold ≥ {th:.2f}: {n_events} events, {n_total} trades")
        print(f"    Mean equal-weight per event: {eq_mean:+.1f}%")
        print(f"    Mean comp-weighted per event: {cw_mean:+.1f}%")
        print(f"    Overall win rate: {win_rate*100:.0f}%")
        for p in ps:
            print(f"      {p['event']}: eq {p['equal_return']:+.1f}%, cw {p['comp_weighted_return']:+.1f}%, "
                  f"wins {p['win_rate']*100:.0f}%, names: {','.join(p['names'])}")

    out = DATA / "_jbook_exposure_cohort_2024" / "post_peak_short_returns.json"
    out.write_text(json.dumps({"events": all_results, "pooled": pooled},
                                indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
