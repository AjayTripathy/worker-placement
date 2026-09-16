"""
ITA-universe pair trade: long framework-clean subset of ITA vs short ITA.

Test: does the framework's clean composite (≤ THRESHOLD) selection from
ITA's own constituents beat ITA itself? Pure cross-sectional stock-picking
alpha — both legs are defense; sector beta cancels precisely.

This is the institutional version of the strategy:
  Long basket = ITA constituents with composite ≤ 0.20 (framework "clean")
  Short = ITA ETF (~37 holdings, expense ratio 0.40%)
  Both legs T-60 → next PB

If pair return is positive, framework's stock selection produces
genuine within-sector alpha. If near zero, framework adds no value
beyond holding ITA passively.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

DATA = Path("verticals/public_co/data")

# ITA constituents we have composites for (covers ~95% of ITA by weight)
ITA_CONSTITUENTS = {
    # ticker -> ITA weight (approximate, from Q1 2026 fact sheet)
    "GE":     0.194,   "RTX":   0.151,   "BA":    0.102,
    "GD":     0.048,   "HWM":   0.052,   "TDG":   0.045,
    "LHX":    0.043,   "LMT":   0.039,   "NOC":   0.039,
    "RKLB":   0.051,   "AXON":  0.020,   "CW":    0.018,
    "FTAI":   0.018,   "WWD":   0.015,   "ATI":   0.015,
    "CRS":    0.012,   "BWXT":  0.015,   "HEI":   0.020,
    "TXT":    0.020,   "HII":   0.018,   "KTOS":  0.012,
    "MOG-A":  0.012,   "HXL":   0.010,   "AVAV":  0.018,
}

EVENTS = [
    {"pb_date": "2023-03-09", "label": "FY24_PB", "next_pb": "2024-03-11", "vintage": "2022"},
    {"pb_date": "2024-03-11", "label": "FY25_PB", "next_pb": "2025-06-15", "vintage": "2022"},
    {"pb_date": "2025-06-15", "label": "FY26_PB", "next_pb": "2026-04-28", "vintage": "2024"},
]

ENTRY_OFFSET_DAYS = -60
LONG_THRESHOLD = 0.20
SEVERITY_WEIGHT = {"PASS":0.0,"UNVERIFIABLE":0.0,"MODERATE_UNDERDELIVERY":1.0,
                    "SEVERE_UNDERDELIVERY":2.0,"RED_FLAG_NEGATIVE":3.0}


def _composite_from_file(path: Path):
    if not path.exists(): return None
    j = json.loads(path.read_text())
    scores = j.get("scores", [])
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted: return 0.0
    return sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted) / len(counted)


def _load_composites_by_vintage():
    local = DATA / "_local"
    out = {"2022": {}, "2024": {}}
    for path in local.glob("*.jbook.2022.scores.json"):
        tk = path.name.split(".")[0]
        c = _composite_from_file(path)
        if c is not None: out["2022"][tk] = c
    matrix_path = DATA / "_jbook_exposure_cohort_2024" / "matrix.json"
    if matrix_path.exists():
        for row in json.loads(matrix_path.read_text()):
            if row.get("status") == "OK":
                out["2024"][row["ticker"]] = row["backtest_composite"]
    for path in local.glob("*.jbook.2024.scores.json"):
        tk = path.name.split(".")[0]
        if tk in out["2024"]: continue
        c = _composite_from_file(path)
        if c is not None: out["2024"][tk] = c
    return out


def _next_close(ticker: str, date_iso: str, max_pad: int = 7):
    start = datetime.fromisoformat(date_iso)
    end = start + timedelta(days=max_pad)
    try:
        df = yf.download(ticker, start=date_iso, end=end.strftime("%Y-%m-%d"),
                          progress=False, auto_adjust=False)
    except Exception: return None
    if df is None or df.empty: return None
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    row = df.iloc[0]
    v = row[col]
    if hasattr(v, "item"): v = v.item()
    return (str(df.index[0].date()), float(v))


def main():
    comps = _load_composites_by_vintage()
    TODAY = datetime.fromisoformat("2026-05-20")

    print("\n" + "=" * 100)
    print(f"ITA-UNIVERSE PAIR TRADE")
    print(f"  Long basket: ITA constituents with composite ≤ {LONG_THRESHOLD}")
    print(f"  Short: ITA ETF")
    print(f"  Both legs T-60 → next PB")
    print("=" * 100)

    results = []
    for event in EVENTS:
        pb_d = datetime.fromisoformat(event["pb_date"])
        entry_dt = pb_d + timedelta(days=ENTRY_OFFSET_DAYS)
        exit_dt  = datetime.fromisoformat(event["next_pb"])
        if exit_dt > TODAY: exit_dt = TODAY
        entry_target = entry_dt.strftime("%Y-%m-%d")
        exit_target  = exit_dt.strftime("%Y-%m-%d")
        vintage = comps[event["vintage"]]

        # Build long basket: ITA constituents with composite ≤ 0.20 at this vintage
        longs = [(tk, w) for tk, w in ITA_CONSTITUENTS.items()
                  if tk in vintage and vintage[tk] <= LONG_THRESHOLD]

        # Fallback for tickers without vintage composite (e.g., Phase 3/4 names
        # not yet at 2022 vintage) — exclude from long basket honestly
        ita_entry = _next_close("ITA", entry_target)
        ita_exit  = _next_close("ITA", exit_target)
        ita_ret = (ita_exit[1] - ita_entry[1]) / ita_entry[1] * 100 if ita_entry and ita_exit else None

        if not longs:
            print(f"\n--- {event['label']}: no ITA constituents with composites at {event['vintage']} vintage ---")
            continue

        # Fetch prices
        print(f"\n--- {event['label']} ({event['pb_date']}, {event['vintage']} vintage) ---")
        print(f"  Entry {entry_target} → Exit {exit_target}")
        long_rets = []
        for tk, weight in longs:
            e = _next_close(tk, entry_target)
            x = _next_close(tk, exit_target)
            if not e or not x: continue
            r = (x[1] - e[1]) / e[1] * 100
            long_rets.append({"ticker": tk, "comp": vintage[tk], "weight": weight, "ret": r})

        # Equal-weighted basket
        eq_long = sum(r["ret"] for r in long_rets) / len(long_rets) if long_rets else 0
        # ITA-weight-weighted (use the LONG names' ITA weights, renormalized)
        total_w = sum(r["weight"] for r in long_rets)
        ita_wt_long = sum(r["ret"] * r["weight"] for r in long_rets) / total_w if total_w else 0

        # Pair vs ITA (synthetic short ITA)
        eq_pair = eq_long - (ita_ret or 0)
        ita_wt_pair = ita_wt_long - (ita_ret or 0)

        print(f"  Long basket ({len(long_rets)} names, composite ≤ {LONG_THRESHOLD}):")
        for r in long_rets:
            print(f"    {r['ticker']:<7} comp={r['comp']:.2f}  ITA wt={r['weight']*100:.1f}%  return={r['ret']:+.1f}%")
        print(f"\n  Equal-weight long: {eq_long:+.1f}%")
        print(f"  ITA-wt-renormalized long: {ita_wt_long:+.1f}%")
        print(f"  ITA benchmark: {ita_ret:+.1f}%" if ita_ret is not None else "  ITA: -")
        print(f"  PAIR (equal-wt long − ITA): {eq_pair:+.1f}%")
        print(f"  PAIR (ITA-wt-renorm long − ITA): {ita_wt_pair:+.1f}%")
        results.append({
            "event": event["label"],
            "n_longs": len(long_rets),
            "long_eq": eq_long, "long_ita_wt": ita_wt_long,
            "ita_ret": ita_ret,
            "pair_eq": eq_pair, "pair_ita_wt": ita_wt_pair,
        })

    # Pooled
    print(f"\n\n{'=' * 100}")
    print(f"POOLED")
    print(f"{'=' * 100}")
    print(f"{'CYCLE':<10} {'#LONG':>5} {'EQ LONG':>10} {'ITA-WT LONG':>13} {'ITA':>8} {'PAIR EQ':>10} {'PAIR ITA-WT':>12}")
    for r in results:
        print(f"{r['event']:<10} {r['n_longs']:>5} {r['long_eq']:>+9.1f}% {r['long_ita_wt']:>+12.1f}% "
              f"{r['ita_ret']:>+7.1f}% {r['pair_eq']:>+9.1f}% {r['pair_ita_wt']:>+11.1f}%")
    if results:
        eq_mean = sum(r["pair_eq"] for r in results) / len(results)
        iw_mean = sum(r["pair_ita_wt"] for r in results) / len(results)
        print(f"{'MEAN':<10} {'':>5} {'':>10} {'':>13} {'':>8} {eq_mean:>+9.1f}% {iw_mean:>+11.1f}%")

    out = DATA / "_jbook_exposure_cohort_2024" / "ita_universe_returns.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
