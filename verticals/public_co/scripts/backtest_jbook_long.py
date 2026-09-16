"""
J-Book LONG basket — flipped from the post-peak short.

Strategy: pick longs in names where the J-Book signal CONFIRMS strong
funding (low composite, ideally high J-Book hit rate with FUNDED status).
Hold across the PB cycle.

Three structural variants tested:
  A) Buy at PB release, hold to next PB         (catches post-PB hype rally)
  B) Buy at PB + 120d, hold to next PB          (mirrors the short structure)
  C) Buy at PB - 60d (anticipate rally), hold to next PB

Universe: tickers with composite ≤ THRESHOLD at the most recent vintage
cutoff PRIOR to the entry date.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

DATA = Path("verticals/public_co/data")

EVENTS = [
    {"pb_date": "2023-03-09", "label": "FY24_PB", "next_pb": "2024-03-11",
     "vintage": "2022"},
    {"pb_date": "2024-03-11", "label": "FY25_PB", "next_pb": "2025-06-15",
     "vintage": "2022"},
    {"pb_date": "2025-06-15", "label": "FY26_PB", "next_pb": "2026-04-28",
     "vintage": "2024"},
]

VARIANTS = [
    {"name": "A_buy_at_PB",          "entry_offset_days": 0},
    {"name": "B_buy_at_PB_plus_120", "entry_offset_days": 120},
    {"name": "C_buy_at_PB_minus_60", "entry_offset_days": -60},
]

# LONG basket = composite ≤ this threshold
CLEAN_THRESHOLDS = [0.00, 0.20, 0.40]

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


def _next_close(ticker: str, date_iso: str, max_pad: int = 7):
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
    TODAY = "2026-05-20"

    # Benchmarks (ITA + SPY) for comparison
    print("\nFetching benchmark prices...")

    pooled = {(v["name"], th): [] for v in VARIANTS for th in CLEAN_THRESHOLDS}

    for variant in VARIANTS:
        print(f"\n\n{'#' * 110}")
        print(f"# VARIANT {variant['name']}  (entry offset {variant['entry_offset_days']:+d}d from PB)")
        print(f"{'#' * 110}")

        for event in EVENTS:
            pb_d = datetime.fromisoformat(event["pb_date"])
            entry_dt = pb_d + timedelta(days=variant["entry_offset_days"])
            exit_dt = datetime.fromisoformat(event["next_pb"])
            today = datetime.fromisoformat(TODAY)
            if exit_dt > today:
                exit_dt = today
            entry_target = entry_dt.strftime("%Y-%m-%d")
            exit_target  = exit_dt.strftime("%Y-%m-%d")
            vintage = composites[event["vintage"]]

            print(f"\n{'=' * 110}")
            print(f"{event['label']} ({event['pb_date']}, {event['vintage']} vintage)")
            print(f"  Entry: {entry_target}    Exit: {exit_target}")
            print(f"{'=' * 110}")

            candidates = sorted(
                [(tk, c) for tk, c in vintage.items() if c <= max(CLEAN_THRESHOLDS)],
                key=lambda x: x[1],
            )

            rows = []
            for tk, comp in candidates:
                entry = _next_close(tk, entry_target)
                exit  = _next_close(tk, exit_target)
                if not entry or not exit:
                    continue
                long_ret = (exit[1] - entry[1]) / entry[1] * 100
                rows.append({
                    "ticker": tk, "composite": comp,
                    "entry": entry, "exit": exit,
                    "long_return_pct": long_ret,
                })

            print(f"  {'TICKER':<6} {'COMP':>5}  {'ENTRY':<12} {'ENTRY $':>9}  "
                  f"{'EXIT':<12} {'EXIT $':>9}  {'LONG %':>9}")
            for r in rows:
                print(f"  {r['ticker']:<6} {r['composite']:>5.2f}  "
                      f"{r['entry'][0]:<12} ${r['entry'][1]:>7.2f}  "
                      f"{r['exit'][0]:<12} ${r['exit'][1]:>7.2f}  "
                      f"{r['long_return_pct']:>+8.1f}%")

            # Benchmarks
            ita_entry = _next_close("ITA", entry_target)
            ita_exit  = _next_close("ITA", exit_target)
            spy_entry = _next_close("SPY", entry_target)
            spy_exit  = _next_close("SPY", exit_target)
            ita_ret = (ita_exit[1]-ita_entry[1])/ita_entry[1]*100 if ita_entry and ita_exit else None
            spy_ret = (spy_exit[1]-spy_entry[1])/spy_entry[1]*100 if spy_entry and spy_exit else None
            print(f"  ITA      {ita_entry[0] if ita_entry else '-':<12} "
                  f"${(ita_entry or [0,0])[1]:>7.2f}  "
                  f"{ita_exit[0] if ita_exit else '-':<12} "
                  f"${(ita_exit or [0,0])[1]:>7.2f}  "
                  f"{'-' if ita_ret is None else f'{ita_ret:+8.1f}%'}")
            print(f"  SPY      {spy_entry[0] if spy_entry else '-':<12} "
                  f"${(spy_entry or [0,0])[1]:>7.2f}  "
                  f"{spy_exit[0] if spy_exit else '-':<12} "
                  f"${(spy_exit or [0,0])[1]:>7.2f}  "
                  f"{'-' if spy_ret is None else f'{spy_ret:+8.1f}%'}")

            for th in CLEAN_THRESHOLDS:
                basket = [r for r in rows if r["composite"] <= th]
                if not basket:
                    continue
                eq = sum(r["long_return_pct"] for r in basket) / len(basket)
                wins = sum(1 for r in basket if r["long_return_pct"] > 0)
                alpha_vs_ita = (eq - ita_ret) if ita_ret is not None else None
                print(f"  → comp ≤ {th:.2f} (n={len(basket)}): "
                      f"long {eq:+.1f}%, wins {wins}/{len(basket)}, "
                      f"alpha vs ITA: {alpha_vs_ita:+.1f}%" if alpha_vs_ita is not None else "")
                pooled[(variant["name"], th)].append({
                    "event": event["label"], "n": len(basket),
                    "long_return": eq, "ita_return": ita_ret,
                    "alpha_vs_ita": alpha_vs_ita,
                    "win_rate": wins / len(basket),
                    "names": [r["ticker"] for r in basket],
                })

    # Pooled summary
    print(f"\n\n{'#' * 110}")
    print(f"# POOLED SUMMARY")
    print(f"{'#' * 110}")
    for variant in VARIANTS:
        print(f"\n  VARIANT {variant['name']}:")
        for th in CLEAN_THRESHOLDS:
            ps = pooled[(variant["name"], th)]
            if not ps:
                continue
            n_events = len(ps)
            mean_ret = sum(p["long_return"] for p in ps) / n_events
            mean_alpha = sum(p["alpha_vs_ita"] for p in ps if p["alpha_vs_ita"] is not None) / max(1, sum(1 for p in ps if p["alpha_vs_ita"] is not None))
            total_n = sum(p["n"] for p in ps)
            wins = sum(p["win_rate"] * p["n"] for p in ps)
            print(f"    comp ≤ {th:.2f}: {n_events} events, {total_n} trades  "
                  f"avg long {mean_ret:+.1f}%, avg alpha vs ITA {mean_alpha:+.1f}%, "
                  f"win rate {wins/total_n*100:.0f}%")
            for p in ps:
                print(f"      {p['event']}: long {p['long_return']:+.1f}% "
                      f"(ITA {p['ita_return']:+.1f}% → α {p['alpha_vs_ita']:+.1f}%), "
                      f"wins {p['win_rate']*100:.0f}%")

    out = DATA / "_jbook_exposure_cohort_2024" / "jbook_long_returns.json"
    out.write_text(json.dumps({"variants": VARIANTS, "events": EVENTS,
                                "pooled": {f"{k[0]}|{k[1]}": v for k, v in pooled.items()}},
                                indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
