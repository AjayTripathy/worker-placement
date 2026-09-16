"""
Multi-cycle compounding + regime analysis.

Stacks the 3 PB-cycle returns (FY24, FY25, FY26) for each strategy variant
and computes compounded returns. Also identifies drawdown sub-periods in the
test window and measures how each strategy behaves during them.

Strategies compared:
  1. Long ITA-clean basket (no hedge)             — directional sector alpha
  2. Pair: long ITA-clean / short ITA              — pure framework alpha
  3. Long ITA (passive sector tilt)                — benchmark
  4. Long SPY (passive market)                     — benchmark

Regimes identified empirically from ITA price action:
  - Defense bull I (Jan 2023 → late 2024): general rally + AI hype begins
  - Quantum crash sub-period (Dec 2024 → Mar 2025): hype unwind
  - Trump 2.0 rally (Apr 2025 → Jan 2026): defense buildout repricing
  - FY27 PB pullback (Feb 2026 → Apr 2026): sector pullback into PB release
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import yfinance as yf

DATA = Path("verticals/public_co/data")
START = "2023-01-01"
END   = "2026-05-21"

CYCLE_RETURNS = {
    # From the validated FY24/FY25/FY26 backtest (long ITA-clean ITA-weighted)
    # Long-only basket returns (ITA-wt-renormalized) from the ITA universe run
    "FY24": {"long": 0.194,  "ita": 0.159, "pair": 0.035, "n": 2},
    "FY25": {"long": 3.592,  "ita": 0.492, "pair": 3.100, "n": 2},
    "FY26": {"long": 0.554,  "ita": 0.452, "pair": 0.102, "n": 18},
}
# Equal-weight versions
CYCLE_RETURNS_EQ = {
    "FY24": {"long": 0.408,  "ita": 0.159, "pair": 0.249, "n": 2},
    "FY25": {"long": 2.692,  "ita": 0.492, "pair": 2.200, "n": 2},
    "FY26": {"long": 0.734,  "ita": 0.452, "pair": 0.282, "n": 18},
}

# Sub-period regime windows
REGIMES = [
    {"label": "Defense bull I",         "start": "2023-01-09", "end": "2024-12-18"},
    {"label": "Quantum/AI crash",       "start": "2024-12-18", "end": "2025-03-10"},
    {"label": "Trump 2.0 defense rally", "start": "2025-04-16", "end": "2026-01-29"},
    {"label": "FY27 PB pullback",       "start": "2026-02-27", "end": "2026-04-28"},
]


def _close(ticker: str, date_iso: str):
    start = datetime.fromisoformat(date_iso)
    end = start + timedelta(days=7)
    df = yf.download(ticker, start=date_iso, end=end.strftime("%Y-%m-%d"),
                      progress=False, auto_adjust=False)
    if df is None or df.empty: return None
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    v = df.iloc[0][col]
    if hasattr(v, "item"): v = v.item()
    return float(v)


def _ret(ticker: str, start: str, end: str) -> float:
    p_s = _close(ticker, start)
    p_e = _close(ticker, end)
    if not p_s or not p_e: return None
    return (p_e - p_s) / p_s * 100


def _compound(returns: list[float]) -> float:
    p = 1.0
    for r in returns:
        p *= (1 + r)
    return (p - 1) * 100


def _annualized(total_return_pct: float, days: int) -> float:
    return (((1 + total_return_pct / 100) ** (365 / days)) - 1) * 100


def main():
    full_days = (datetime.fromisoformat(END) - datetime.fromisoformat(START)).days

    # ─── Multi-cycle compounding ─────────────────────────────────────
    print("\n" + "=" * 90)
    print("MULTI-CYCLE COMPOUNDING (FY24 → FY25 → FY26, equal-weighted)")
    print("=" * 90)
    print(f"{'CYCLE':<7} {'LONG':>10} {'ITA':>10} {'PAIR':>10}")
    for label, r in CYCLE_RETURNS_EQ.items():
        print(f"{label:<7} {r['long']*100:>+9.1f}% {r['ita']*100:>+9.1f}% {r['pair']*100:>+9.1f}%")
    long_eq    = [r["long"] for r in CYCLE_RETURNS_EQ.values()]
    ita_eq     = [r["ita"]  for r in CYCLE_RETURNS_EQ.values()]
    pair_eq    = [r["pair"] for r in CYCLE_RETURNS_EQ.values()]
    print(f"{'COMPOUND':<7} {_compound(long_eq):>+9.1f}% {_compound(ita_eq):>+9.1f}% {_compound(pair_eq):>+9.1f}%")

    print("\nMULTI-CYCLE COMPOUNDING (ITA-weight-renormalized)")
    print("=" * 90)
    print(f"{'CYCLE':<7} {'LONG':>10} {'ITA':>10} {'PAIR':>10}")
    for label, r in CYCLE_RETURNS.items():
        print(f"{label:<7} {r['long']*100:>+9.1f}% {r['ita']*100:>+9.1f}% {r['pair']*100:>+9.1f}%")
    long_iw    = [r["long"] for r in CYCLE_RETURNS.values()]
    ita_iw     = [r["ita"]  for r in CYCLE_RETURNS.values()]
    pair_iw    = [r["pair"] for r in CYCLE_RETURNS.values()]
    print(f"{'COMPOUND':<7} {_compound(long_iw):>+9.1f}% {_compound(ita_iw):>+9.1f}% {_compound(pair_iw):>+9.1f}%")

    # ─── Benchmarks over full window ────────────────────────────────
    print(f"\n\nBENCHMARKS — buy-and-hold {START} → {END} ({full_days} days)")
    print("=" * 90)
    for tk in ["SPY", "ITA"]:
        r = _ret(tk, START, "2026-05-20")
        ann = _annualized(r, full_days)
        print(f"  {tk:<6} total {r:+.1f}%, annualized {ann:+.1f}%")

    # Compounded strategy returns
    print(f"\nCompounded strategy over 3 cycles (~{full_days/365.25:.1f}yr):")
    for label, returns in [
        ("Long-only EQ",   long_eq),
        ("Long-only ITA-WT", long_iw),
        ("Pair EQ",        pair_eq),
        ("Pair ITA-WT",    pair_iw),
    ]:
        c = _compound(returns)
        ann = _annualized(c, full_days)
        print(f"  {label:<20} total {c:+.1f}%, annualized {ann:+.1f}%")

    # ─── Regime analysis ─────────────────────────────────────────────
    print(f"\n\n{'=' * 90}")
    print("REGIME ANALYSIS — buy-and-hold per sub-period for each benchmark")
    print(f"{'=' * 90}")
    print(f"{'REGIME':<26} {'WINDOW':<26} {'DAYS':>5} {'SPY':>9} {'ITA':>9}")
    print("-" * 90)
    for r in REGIMES:
        days = (datetime.fromisoformat(r["end"]) - datetime.fromisoformat(r["start"])).days
        spy_r = _ret("SPY", r["start"], r["end"])
        ita_r = _ret("ITA", r["start"], r["end"])
        spy_s = f"{spy_r:>+8.1f}%" if spy_r is not None else "    -    "
        ita_s = f"{ita_r:>+8.1f}%" if ita_r is not None else "    -    "
        print(f"  {r['label']:<24} {r['start']}→{r['end']} {days:>5} {spy_s} {ita_s}")

    # Also compute basket performance in the quantum crash + FY27 PB pullback sub-periods
    print(f"\n{'=' * 90}")
    print("LONG-BASKET RETURNS during specific drawdown sub-periods")
    print(f"{'=' * 90}")
    LONG = ["RTX","BA","GD","HWM","LHX","LMT","CW","FTAI","WWD","ATI","CRS","BWXT",
            "HEI","TXT","HII","MOG-A","AVAV","AXON"]   # 18-name FY26 long basket
    for r in REGIMES[-2:]:
        print(f"\n  --- {r['label']} ({r['start']} → {r['end']}) ---")
        rets = []
        for tk in LONG:
            x = _ret(tk, r["start"], r["end"])
            if x is not None:
                rets.append((tk, x))
        rets.sort(key=lambda x: x[1])
        if rets:
            mean = sum(x[1] for x in rets) / len(rets)
            ita_r = _ret("ITA", r["start"], r["end"])
            spy_r = _ret("SPY", r["start"], r["end"])
            print(f"    Basket EQ mean: {mean:+.1f}%  (vs ITA {ita_r:+.1f}%, SPY {spy_r:+.1f}%)")
            print(f"    Basket vs ITA: {mean - (ita_r or 0):+.1f}pp alpha")
            print(f"    Worst 3: {', '.join(f'{t}{v:+.0f}%' for t,v in rets[:3])}")
            print(f"    Best 3:  {', '.join(f'{t}{v:+.0f}%' for t,v in rets[-3:])}")

    # ─── Volatility & risk metrics ──────────────────────────────────
    print(f"\n\n{'=' * 90}")
    print("VOLATILITY / DRAWDOWN — daily series, full window")
    print(f"{'=' * 90}")
    for tk in ["SPY", "ITA"]:
        df = yf.download(tk, start=START, end=END,
                          progress=False, auto_adjust=False)
        col = "Adj Close" if "Adj Close" in df.columns else "Close"
        prices = df[col].values
        if prices.ndim > 1: prices = prices[:, 0]
        # Daily returns
        daily = np.diff(prices) / prices[:-1]
        vol_ann = float(np.std(daily) * np.sqrt(252) * 100)
        # Drawdown
        peak = np.maximum.accumulate(prices)
        dd = (prices - peak) / peak * 100
        max_dd = float(np.min(dd))
        print(f"  {tk:<5} annualized vol: {vol_ann:>5.1f}%   max drawdown: {max_dd:>+6.1f}%")


if __name__ == "__main__":
    main()
