"""
Pre-J-Book-release short basket backtest.

Trade structure per J-Book release:
  Entry: T-60 calendar days before PB release (nearest trading day)
  Exit:  T+45 calendar days after PB release (nearest trading day)
  Universe: tickers with composite ≥ THRESHOLD at the most recent vintage
            cutoff PRIOR to the PB release (no peeking forward)
  Weights: equal + composite-weighted (both reported)

Vintage rule (honest):
  - FY23 PB (Mar 2022): no vintage available pre-PB (our earliest is 2022-06).
    Skip — can't trade without signal.
  - FY24 PB (Mar 2023): use 2022-06-01 vintage composites
  - FY25 PB (Mar 2024): use 2022-06-01 vintage composites (still no 2023)
  - FY26 PB (Jun 2025): use 2024-09-01 vintage composites
  - FY27 PB (Apr 2026): use 2024-09-01 vintage composites
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

DATA = Path("verticals/public_co/data")

# J-Book / PB release dates and which vintage to use
PB_EVENTS = [
    # {"date": "2022-03-28", "label": "FY23_PB", "vintage": "2022"},   # skip — no pre-PB signal
    {"date": "2023-03-09", "label": "FY24_PB", "vintage": "2022"},
    {"date": "2024-03-11", "label": "FY25_PB", "vintage": "2022"},
    {"date": "2025-06-15", "label": "FY26_PB", "vintage": "2024"},
    {"date": "2026-04-28", "label": "FY27_PB", "vintage": "2024"},
]

ENTRY_OFFSET_DAYS = -60   # T-60 entry
EXIT_OFFSET_DAYS  = +45   # T+45 exit

THRESHOLDS = [0.50, 0.75, 1.00]  # composite thresholds for inclusion

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


def _load_composites_by_vintage() -> dict[str, dict[str, float]]:
    """Returns {vintage: {ticker: composite}}."""
    local = DATA / "_local"
    out = {"2022": {}, "2024": {}}
    # 2022 vintage
    for path in local.glob("*.jbook.2022.scores.json"):
        tk = path.name.split(".")[0]
        c = _composite_from_file(path)
        if c is not None:
            out["2022"][tk] = c
    # 2024 vintage — use the matrix.json from the backtest aggregator (covers original 12)
    matrix_path = DATA / "_jbook_exposure_cohort_2024" / "matrix.json"
    if matrix_path.exists():
        for row in json.loads(matrix_path.read_text()):
            if row.get("status") == "OK":
                out["2024"][row["ticker"]] = row["backtest_composite"]
    # 2024 vintage Phase 2a additions — read scores files directly
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
    composites = _load_composites_by_vintage()
    print(f"Loaded composites: "
          f"{len(composites['2022'])} (2022 vintage), "
          f"{len(composites['2024'])} (2024 vintage)\n", file=sys.stderr)

    all_event_results = []
    pooled_by_threshold = {th: [] for th in THRESHOLDS}

    TODAY = "2026-05-20"
    today_dt = datetime.fromisoformat(TODAY)
    for event in PB_EVENTS:
        pb_d = datetime.fromisoformat(event["date"])
        entry_target = (pb_d + timedelta(days=ENTRY_OFFSET_DAYS)).strftime("%Y-%m-%d")
        exit_dt = pb_d + timedelta(days=EXIT_OFFSET_DAYS)
        # Cap exit at today if future
        if exit_dt > today_dt:
            exit_dt = today_dt
            event["exit_capped"] = True
        exit_target = exit_dt.strftime("%Y-%m-%d")
        vintage_comps = composites[event["vintage"]]

        print(f"\n{'=' * 110}")
        print(f"{event['label']} ({event['date']}, {event['vintage']} vintage)")
        print(f"  Entry T-60: ~{entry_target}   Exit T+45: ~{exit_target}")
        print(f"  Universe (composite ≥ {min(THRESHOLDS):.2f}): "
              f"{', '.join(t for t, c in vintage_comps.items() if c >= min(THRESHOLDS))}")
        print(f"{'=' * 110}")
        if not vintage_comps:
            print("  no composites — skip")
            continue

        # Fetch prices for every ticker in vintage with composite ≥ min threshold
        candidates = [(tk, c) for tk, c in vintage_comps.items() if c >= min(THRESHOLDS)]
        candidates.sort(key=lambda x: -x[1])

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

        # Print event detail
        print(f"  {'TICKER':<6} {'COMP':>5}  {'ENTRY':<12} {'ENTRY $':>9}  "
              f"{'EXIT':<12} {'EXIT $':>9}  {'SHORT %':>9}")
        for r in rows:
            print(f"  {r['ticker']:<6} {r['composite']:>5.2f}  "
                  f"{r['entry'][0]:<12} ${r['entry'][1]:>7.2f}  "
                  f"{r['exit'][0]:<12} ${r['exit'][1]:>7.2f}  "
                  f"{r['short_return_pct']:>+8.1f}%")

        # Compute basket returns per threshold
        for th in THRESHOLDS:
            basket = [r for r in rows if r["composite"] >= th]
            if not basket:
                continue
            eq = sum(r["short_return_pct"] for r in basket) / len(basket)
            total_w = sum(r["composite"] for r in basket)
            cw = sum(r["short_return_pct"] * r["composite"] for r in basket) / total_w if total_w else 0
            wins = sum(1 for r in basket if r["short_return_pct"] > 0)
            print(f"  → threshold ≥{th:.2f} (n={len(basket)}): "
                  f"equal {eq:+.1f}%, comp-wtd {cw:+.1f}%, wins {wins}/{len(basket)}")
            pooled_by_threshold[th].append({
                "event": event["label"],
                "n": len(basket),
                "equal_return": eq,
                "comp_weighted_return": cw,
                "win_rate": wins / len(basket),
                "names": [r["ticker"] for r in basket],
            })

        all_event_results.append({"event": event, "rows": rows})

    # Pooled summary
    print(f"\n\n{'=' * 110}")
    print(f"POOLED ACROSS ALL PB EVENTS")
    print(f"{'=' * 110}")
    for th in THRESHOLDS:
        pooled = pooled_by_threshold[th]
        if not pooled:
            print(f"\n  Threshold ≥ {th:.2f}: no events")
            continue
        n_events = len(pooled)
        n_total = sum(p["n"] for p in pooled)
        eq_mean = sum(p["equal_return"] for p in pooled) / n_events
        cw_mean = sum(p["comp_weighted_return"] for p in pooled) / n_events
        wins = sum(p["win_rate"] * p["n"] for p in pooled)
        win_rate_overall = wins / n_total
        print(f"\n  Threshold ≥ {th:.2f}: {n_events} events, {n_total} ticker-trades")
        print(f"    Mean equal-weight per event: {eq_mean:+.1f}%")
        print(f"    Mean comp-weighted per event: {cw_mean:+.1f}%")
        print(f"    Overall win rate: {win_rate_overall*100:.0f}%")
        for p in pooled:
            print(f"      {p['event']}: eq {p['equal_return']:+.1f}%, "
                  f"cw {p['comp_weighted_return']:+.1f}%, win {p['win_rate']*100:.0f}%, "
                  f"names: {','.join(p['names'])}")

    # Write artifact
    out = DATA / "_jbook_exposure_cohort_2024" / "pre_pb_short_returns.json"
    out.write_text(json.dumps({
        "trade_structure": {
            "entry_offset_days": ENTRY_OFFSET_DAYS,
            "exit_offset_days":  EXIT_OFFSET_DAYS,
            "thresholds":        THRESHOLDS,
        },
        "events": all_event_results,
        "pooled_by_threshold": pooled_by_threshold,
    }, indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
