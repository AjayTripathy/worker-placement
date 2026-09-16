"""
J-Book L/S pair trade — isolate framework alpha from sector beta.

Structure (market-neutral, synchronous legs):
  Long basket: tickers with composite ≤ LONG_THRESHOLD
  Short basket: tickers with composite ≥ SHORT_THRESHOLD
  Both legs enter T-60 days before each PB release.
  Both legs exit at next PB release.
  Equal dollar weight per leg.

Pair return = avg_long_return - avg_short_stock_return
            = avg_long_return + avg_short_pnl
  where short_pnl is positive when the short stock falls.

If pair return is ≈ 0, all the long-side excess return was sector beta.
If pair return is materially positive, the framework's composite is the
source of alpha.
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

PAIR_VARIANTS = [
    # (long_max_composite, short_min_composite, label)
    (0.00, 0.50, "L≤0.00 / S≥0.50"),
    (0.20, 0.50, "L≤0.20 / S≥0.50"),
    (0.20, 0.75, "L≤0.20 / S≥0.75"),
    (0.40, 0.50, "L≤0.40 / S≥0.50"),
]

ENTRY_OFFSET_DAYS = -60

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
    TODAY = datetime.fromisoformat("2026-05-20")

    pooled = {v[2]: [] for v in PAIR_VARIANTS}

    for event in EVENTS:
        pb_d = datetime.fromisoformat(event["pb_date"])
        entry_dt = pb_d + timedelta(days=ENTRY_OFFSET_DAYS)
        exit_dt = datetime.fromisoformat(event["next_pb"])
        if exit_dt > TODAY:
            exit_dt = TODAY
        entry_target = entry_dt.strftime("%Y-%m-%d")
        exit_target = exit_dt.strftime("%Y-%m-%d")
        vintage = composites[event["vintage"]]

        # Fetch prices for ALL tickers in vintage
        print(f"\n\n{'=' * 100}")
        print(f"{event['label']} ({event['pb_date']})  Entry {entry_target} → Exit {exit_target}")
        print(f"  Vintage: {event['vintage']}, universe size: {len(vintage)}")
        print(f"{'=' * 100}")

        prices = {}
        for tk in vintage:
            e = _next_close(tk, entry_target)
            x = _next_close(tk, exit_target)
            if e and x:
                prices[tk] = {
                    "comp": vintage[tk],
                    "entry": e, "exit": x,
                    "long_ret_pct":  (x[1] - e[1]) / e[1] * 100,
                    "short_pnl_pct": (e[1] - x[1]) / e[1] * 100,
                }

        # ITA bench
        ita_e = _next_close("ITA", entry_target)
        ita_x = _next_close("ITA", exit_target)
        ita_ret = (ita_x[1]-ita_e[1])/ita_e[1]*100 if ita_e and ita_x else None

        # For each pair variant, compute basket-level returns
        for long_max, short_min, label in PAIR_VARIANTS:
            longs  = [(tk, d) for tk, d in prices.items() if d["comp"] <= long_max]
            shorts = [(tk, d) for tk, d in prices.items() if d["comp"] >= short_min]
            if not longs or not shorts:
                continue
            long_ret  = sum(d["long_ret_pct"]  for _, d in longs)  / len(longs)
            short_pnl = sum(d["short_pnl_pct"] for _, d in shorts) / len(shorts)
            pair_pct  = long_ret + short_pnl

            print(f"\n  {label}:")
            print(f"    LONG  basket ({len(longs)} names): {', '.join(t for t,_ in longs[:8])}{'...' if len(longs)>8 else ''}")
            print(f"      avg long return:  {long_ret:+.1f}%")
            print(f"    SHORT basket ({len(shorts)} names): {', '.join(t for t,_ in shorts)}")
            print(f"      avg short P&L:    {short_pnl:+.1f}%")
            print(f"    PAIR (long + short): {pair_pct:+.1f}%")
            print(f"    Benchmark ITA:       {ita_ret:+.1f}%" if ita_ret is not None else "    Benchmark ITA: -")
            print(f"    Alpha over ITA (long-only): {long_ret - (ita_ret or 0):+.1f}%")
            print(f"    Pair vs ITA (market-neutral spread): {pair_pct:+.1f}%")

            pooled[label].append({
                "event": event["label"],
                "n_long": len(longs), "n_short": len(shorts),
                "long_ret": long_ret, "short_pnl": short_pnl,
                "pair_pct": pair_pct, "ita_ret": ita_ret,
            })

    # Pooled
    print(f"\n\n{'#' * 100}")
    print(f"# POOLED — PAIR TRADE (synchronous L/S, equal-weighted, T-60 → next PB)")
    print(f"{'#' * 100}")
    print(f"\n{'VARIANT':<25} {'EVENTS':>7} {'AVG LONG':>10} {'AVG SHORT':>11} "
          f"{'AVG PAIR':>10} {'AVG ITA':>9} {'PAIR vs ITA':>12}")
    print("=" * 95)
    for label in [v[2] for v in PAIR_VARIANTS]:
        ps = pooled[label]
        if not ps:
            continue
        n = len(ps)
        avg_long  = sum(p["long_ret"]  for p in ps) / n
        avg_short = sum(p["short_pnl"] for p in ps) / n
        avg_pair  = sum(p["pair_pct"]  for p in ps) / n
        avg_ita   = sum(p["ita_ret"]   for p in ps) / n
        print(f"{label:<25} {n:>7} {avg_long:>+9.1f}% {avg_short:>+10.1f}% "
              f"{avg_pair:>+9.1f}% {avg_ita:>+8.1f}% {avg_pair - avg_ita:>+11.1f}%")
        for p in ps:
            print(f"  {p['event']:<22}         {p['long_ret']:>+9.1f}% {p['short_pnl']:>+10.1f}% "
                  f"{p['pair_pct']:>+9.1f}% {p['ita_ret']:>+8.1f}%")

    out = DATA / "_jbook_exposure_cohort_2024" / "pair_trade_returns.json"
    out.write_text(json.dumps({"pooled": pooled, "events": [e["label"] for e in EVENTS]},
                                indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
