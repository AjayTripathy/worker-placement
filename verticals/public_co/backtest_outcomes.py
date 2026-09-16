"""
Compute forward returns on a set of emitted pairs over a measurement window.

Used by both Tier A (current emits projected back over the past 12 months)
and Tier B (historical emits projected forward over their realized 12 months).

For each pair:
  long_ret_pct  = price(L, t_end) / price(L, t_start) - 1
  short_ret_pct = 1 - price(S, t_end) / price(S, t_start)
                   (profit-on-short, positive when stock fell)
  pair_ret_$_neutral   = long_ret_pct + short_ret_pct
  pair_ret_$_beta      = long_ret_pct + short_ret_pct * hedge_ratio
                          (overweight short by hedge ratio)

Aggregates:
  hit rate (% of pairs with positive pair return)
  avg return
  Tier 1 vs Tier 2 breakdown
  comparison to SPY over same window

Usage:
    # Tier A: current emit list projected back over past 12 months
    python3 -m verticals.public_co.backtest_outcomes \
        --pairs data/_pair_trades/position_sizing.json \
        --start 2025-05-17 --end 2026-05-16

    # Tier B: historical emits forward
    python3 -m verticals.public_co.backtest_outcomes \
        --pairs data/_backtest/pairs_2024_05_17.json \
        --start 2024-05-17 --end 2025-05-17
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import yfinance as yf

HERE = Path(__file__).parent
DATA = HERE / "data"


def _close_on_or_after(ticker: str, target_date: str, lookback_days: int = 10) -> tuple[float | None, str | None]:
    """Return the close price on or just after target_date, plus the actual date.
    Tries up to lookback_days days after target_date (for weekends/holidays).
    """
    from datetime import datetime, timedelta
    start = datetime.fromisoformat(target_date)
    end   = start + timedelta(days=lookback_days)
    try:
        df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"),
                         progress=False, auto_adjust=False)
        if df.empty:
            return None, None
        # df has multi-ticker columns; handle both shapes
        close_col = df["Close"]
        if hasattr(close_col, "iloc"):
            first_idx = close_col.index[0]
            v = close_col.iloc[0]
            if hasattr(v, "iloc"):
                v = v.iloc[0]
            return float(v), str(first_idx.date())
    except Exception as e:
        return None, None
    return None, None


def compute_pair_return(short: str, long: str, hedge_ratio: float,
                        start_date: str, end_date: str) -> dict:
    s_start, s_start_d = _close_on_or_after(short, start_date)
    s_end,   s_end_d   = _close_on_or_after(long if False else short, end_date)
    l_start, l_start_d = _close_on_or_after(long, start_date)
    l_end,   l_end_d   = _close_on_or_after(long, end_date)

    out = {
        "short": short, "long": long,
        "hedge_ratio": hedge_ratio,
        "short_start_price": s_start, "short_start_date": s_start_d,
        "short_end_price":   s_end,   "short_end_date":   s_end_d,
        "long_start_price":  l_start, "long_start_date":  l_start_d,
        "long_end_price":    l_end,   "long_end_date":    l_end_d,
    }

    if None in (s_start, s_end, l_start, l_end):
        out["error"] = "missing price data"
        return out
    if s_start == 0 or l_start == 0:
        out["error"] = "zero start price"
        return out

    long_ret  = l_end / l_start - 1            # positive = long won
    short_ret = 1 - s_end / s_start            # positive = short won (stock fell)
    out["long_ret_pct"]  = round(long_ret * 100, 2)
    out["short_ret_pct"] = round(short_ret * 100, 2)
    # Dollar-neutral 1:1
    out["pair_ret_dollar_neutral_pct"] = round((long_ret + short_ret) * 100, 2)
    # Beta-neutral: short is sized by hedge_ratio. Total return per $1 long:
    #   long: +long_ret
    #   short: +short_ret * hedge_ratio   (because short notional = hedge_ratio * long)
    out["pair_ret_beta_neutral_pct"] = round((long_ret + short_ret * hedge_ratio) * 100, 2)

    return out


def measure_pairs(pairs: list[dict], start_date: str, end_date: str) -> list[dict]:
    out = []
    for p in pairs:
        hedge = p.get("hedge", {}).get("ratio", 1.0)
        r = compute_pair_return(p["short"], p["long"], hedge, start_date, end_date)
        r["tier"] = p.get("tier", "?")
        r["composite"] = p.get("short_composite") or p.get("composite")
        r["theme"] = p.get("theme")
        out.append(r)
    return out


def summary(results: list[dict]) -> dict:
    by_tier: dict[str, list[dict]] = {}
    valid = [r for r in results if "error" not in r and r.get("pair_ret_beta_neutral_pct") is not None]
    invalid = [r for r in results if r not in valid]
    for r in valid:
        by_tier.setdefault(r["tier"], []).append(r)

    def _agg(rows):
        if not rows:
            return {}
        dn = [r["pair_ret_dollar_neutral_pct"] for r in rows]
        bn = [r["pair_ret_beta_neutral_pct"]   for r in rows]
        sr = [r["short_ret_pct"] for r in rows]
        lr = [r["long_ret_pct"]  for r in rows]
        return {
            "n_pairs": len(rows),
            "avg_dollar_neutral_pct":   round(sum(dn) / len(dn), 2),
            "avg_beta_neutral_pct":     round(sum(bn) / len(bn), 2),
            "hit_rate_dollar_neutral":  round(sum(1 for x in dn if x > 0) / len(dn), 3),
            "hit_rate_beta_neutral":    round(sum(1 for x in bn if x > 0) / len(bn), 3),
            "avg_short_ret_pct":        round(sum(sr) / len(sr), 2),
            "avg_long_ret_pct":         round(sum(lr) / len(lr), 2),
            "best_pair":                max(rows, key=lambda r: r["pair_ret_beta_neutral_pct"])["short"] + "/" + max(rows, key=lambda r: r["pair_ret_beta_neutral_pct"])["long"],
            "best_return":              max(r["pair_ret_beta_neutral_pct"] for r in rows),
            "worst_pair":               min(rows, key=lambda r: r["pair_ret_beta_neutral_pct"])["short"] + "/" + min(rows, key=lambda r: r["pair_ret_beta_neutral_pct"])["long"],
            "worst_return":             min(r["pair_ret_beta_neutral_pct"] for r in rows),
        }

    return {
        "overall":    _agg(valid),
        "by_tier":    {t: _agg(rows) for t, rows in by_tier.items()},
        "n_total":    len(results),
        "n_valid":    len(valid),
        "n_excluded": len(invalid),
        "excluded":   [(r["short"], r["long"], r.get("error", "no return")) for r in invalid],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, help="path to pairs.json or position_sizing.json")
    ap.add_argument("--start", required=True, help="ISO date for entry")
    ap.add_argument("--end",   required=True, help="ISO date for exit")
    ap.add_argument("--out",   help="optional output JSON path")
    ap.add_argument("--include-spy", action="store_true", help="add SPY comparator")
    args = ap.parse_args()

    pairs = json.loads(Path(args.pairs).read_text())
    print(f"Measuring {len(pairs)} pairs from {args.start} to {args.end}...")
    results = measure_pairs(pairs, args.start, args.end)

    if args.include_spy:
        spy = compute_pair_return("SPY", "SPY", 1.0, args.start, args.end)
        spy_ret = spy.get("long_ret_pct")
        print(f"\nSPY return over same window: {spy_ret}%")

    print()
    summ = summary(results)
    print(f"=== Overall ({summ['n_valid']}/{summ['n_total']} valid) ===")
    for k, v in summ["overall"].items():
        print(f"  {k:30s} {v}")

    print(f"\n=== By tier ===")
    for tier, agg in summ["by_tier"].items():
        print(f"  {tier}: n={agg['n_pairs']}, avg_bn={agg['avg_beta_neutral_pct']}%, "
              f"hit_rate_bn={agg['hit_rate_beta_neutral']*100:.0f}%, "
              f"best={agg['best_pair']} ({agg['best_return']}%), "
              f"worst={agg['worst_pair']} ({agg['worst_return']}%)")

    if summ.get("excluded"):
        print(f"\n=== Excluded ({summ['n_excluded']}) ===")
        for ex in summ["excluded"]:
            print(f"  {ex[0]}/{ex[1]}: {ex[2]}")

    print(f"\n=== Per-pair detail ===")
    for r in sorted(results, key=lambda r: -(r.get("pair_ret_beta_neutral_pct") or -999)):
        if "error" in r:
            print(f"  {r['short']:>6}/{r['long']:<5} [{r['tier']:<5}] EXCLUDED: {r['error']}")
            continue
        print(f"  {r['short']:>6}/{r['long']:<5} [{r['tier']:<5}] "
              f"L={r['long_ret_pct']:+6.1f}%  S={r['short_ret_pct']:+6.1f}%  "
              f"DN={r['pair_ret_dollar_neutral_pct']:+6.1f}%  BN={r['pair_ret_beta_neutral_pct']:+6.1f}%")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "start": args.start, "end": args.end,
            "n_pairs": len(results),
            "results": results,
            "summary": summ,
        }, indent=2, default=str))
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
