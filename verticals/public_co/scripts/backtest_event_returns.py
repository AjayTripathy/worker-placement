"""
Event-window short returns for J-Book exposure cohort.

Two event types:
  1. J-Book release dates (when Pentagon dumps fresh truth into the market)
  2. Each ticker's first 10-Q filed AFTER each J-Book release (management's
     first chance to acknowledge or deflect the J-Book signal)

Universe: framework's 2024-09-01 backtest signal-bearing names (composite ≥ 0.50,
excluding IONQ as in-sample): QBTS, QUBT, RDW, BBAI, RCAT.

For each event, compute:
  T-1 close → T+1, T+5, T+10, T+20 close
  short P&L = (T-1_close − T+N_close) / T-1_close
  positive = short made money

Aggregate across basket and across events.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yfinance as yf

DATA = Path("verticals/public_co/data")

import os

# Two universes — selectable via env var COHORT=red|clean (default red)
RED_UNIVERSE     = ["QBTS", "QUBT", "RDW", "BBAI", "RCAT"]  # composite ≥ 0.50 at 2024-09-01
CLEAN_UNIVERSE   = ["RKLB", "RGTI", "PL"]                    # composite ≤ 0.33 at 2024-09-01
TIGHT_UNIVERSE   = ["QBTS", "QUBT"]                          # composite ≥ 0.75 (excl IONQ in-sample, ARQQ UK)
STRICT_UNIVERSE  = ["ARQQ"]                                  # composite ≥ 1.0 — only ARQQ left (IONQ in-sample)
_COHORT = os.environ.get("COHORT", "red").lower()
UNIVERSE = {
    "red":    RED_UNIVERSE,
    "clean":  CLEAN_UNIVERSE,
    "tight":  TIGHT_UNIVERSE,
    "strict": STRICT_UNIVERSE,
}.get(_COHORT, RED_UNIVERSE)
print(f"COHORT={_COHORT!r}  UNIVERSE={UNIVERSE}", file=__import__("sys").stderr)

# J-Book / President's Budget release dates (public DoD/SAFFM publication dates)
JBOOK_RELEASES = [
    {"date": "2022-03-28", "label": "FY23_PB", "note": "Biden FY23 PB submission"},
    {"date": "2023-03-09", "label": "FY24_PB", "note": "Biden FY24 PB submission"},
    {"date": "2024-03-11", "label": "FY25_PB", "note": "Biden FY25 (late) PB submission"},
    {"date": "2025-06-15", "label": "FY26_PB", "note": "Trump 2.0 PB (delayed)"},
    {"date": "2026-04-28", "label": "FY27_PB", "note": "Trump FY27 PB; confirmed SDN replacement"},
]

HOLDING_PERIODS = [1, 5, 10, 20]   # trading days


def _fetch_window(ticker: str, around_date: str, pad_days: int = 35):
    """Fetch a ~70-day window of daily closes centered on around_date."""
    center = datetime.fromisoformat(around_date)
    start = (center - timedelta(days=pad_days)).strftime("%Y-%m-%d")
    end   = (center + timedelta(days=pad_days)).strftime("%Y-%m-%d")
    try:
        df = yf.download(ticker, start=start, end=end,
                          progress=False, auto_adjust=False)
    except Exception as e:
        print(f"  ! yf err {ticker}: {e}", file=sys.stderr)
        return None
    if df is None or df.empty:
        return None
    col = "Adj Close" if "Adj Close" in df.columns else "Close"
    out = []
    for idx, row in df.iterrows():
        v = row[col]
        if hasattr(v, "item"):
            v = v.item()
        out.append((idx.date(), float(v)))
    return out


def _event_returns(prices, event_date_iso: str):
    """Given a list of (date, close), compute T-1 → T+N returns for N in HOLDING_PERIODS."""
    target = datetime.fromisoformat(event_date_iso).date()
    # Find T-1: the last trading day STRICTLY BEFORE target
    pre = [p for p in prices if p[0] < target]
    if not pre:
        return None
    t_minus_1 = pre[-1]
    # Find T+N: the Nth trading day at or after target
    at_or_after = [p for p in prices if p[0] >= target]
    out = {"T_minus_1": (str(t_minus_1[0]), t_minus_1[1])}
    for n in HOLDING_PERIODS:
        if n - 1 >= len(at_or_after):
            out[f"T_plus_{n}"] = None
            out[f"short_return_T{n}_pct"] = None
            continue
        t_plus = at_or_after[n - 1]
        short_ret = (t_minus_1[1] - t_plus[1]) / t_minus_1[1] * 100
        out[f"T_plus_{n}"] = (str(t_plus[0]), t_plus[1])
        out[f"short_return_T{n}_pct"] = short_ret
    return out


def _ten_q_dates_after(ticker: str, after_date_iso: str, max_count: int = 1) -> list[dict]:
    """From the ticker's filings_index.json, return the first N 10-Q (or 10-K) filings dated AFTER after_date_iso."""
    idx_path = DATA / ticker.lower() / "filings_index.json"
    if not idx_path.exists():
        return []
    idx = json.loads(idx_path.read_text())
    filings = idx if isinstance(idx, list) else idx.get("filings") or []
    candidates = []
    for f in filings:
        d = f.get("filing_date", "")
        form = f.get("form", "")
        if d > after_date_iso and form in ("10-Q", "10-Q/A", "10-K", "10-K/A"):
            candidates.append({"date": d, "form": form, "accession": f.get("accession") or f.get("accessionNumber","")})
    candidates.sort(key=lambda x: x["date"])
    return candidates[:max_count]


def main():
    # ─── J-Book release events ───────────────────────────────────────────
    print("=" * 100)
    print("EVENT 1: J-Book release dates (T-1 close → T+N close)")
    print("=" * 100)
    jbook_rollup = {n: [] for n in HOLDING_PERIODS}
    per_event_jbook = []
    for event in JBOOK_RELEASES:
        d = event["date"]
        label = event["label"]
        print(f"\n--- {label} ({d}) — {event['note']} ---")
        print(f"{'TICKER':<7} {'T-1':>12} {'T-1$':>9}", end="")
        for n in HOLDING_PERIODS:
            print(f" {f'T+{n}%':>7}", end="")
        print()
        event_rollup = {n: [] for n in HOLDING_PERIODS}
        for tk in UNIVERSE:
            prices = _fetch_window(tk, d)
            if not prices:
                print(f"{tk:<7} (no prices)")
                continue
            er = _event_returns(prices, d)
            if not er:
                print(f"{tk:<7} (window err)")
                continue
            t_minus = er["T_minus_1"]
            print(f"{tk:<7} {t_minus[0]:>12} ${t_minus[1]:>7.2f}", end="")
            for n in HOLDING_PERIODS:
                r = er.get(f"short_return_T{n}_pct")
                if r is None:
                    print(f" {'-':>7}", end="")
                else:
                    print(f" {r:>+6.1f}%", end="")
                    event_rollup[n].append(r)
                    jbook_rollup[n].append(r)
            print()
        # Per-event means
        print(f"{'MEAN':<7} {'':>12} {'':>9}", end="")
        for n in HOLDING_PERIODS:
            vals = event_rollup[n]
            if vals:
                print(f" {sum(vals)/len(vals):>+6.1f}%", end="")
            else:
                print(f" {'-':>7}", end="")
        print()
        per_event_jbook.append({"event": label, "date": d,
                                  "means_by_holding_days": {n: (sum(event_rollup[n])/len(event_rollup[n]) if event_rollup[n] else None) for n in HOLDING_PERIODS}})

    # Pooled across events
    print("\n--- POOLED across all J-Book release events ---")
    print(f"  N={len(UNIVERSE)*len(JBOOK_RELEASES)} ticker-events (basket size × n events)")
    for n in HOLDING_PERIODS:
        vals = jbook_rollup[n]
        if vals:
            mean = sum(vals) / len(vals)
            wins = sum(1 for v in vals if v > 0)
            print(f"  T+{n:>2d} mean short return: {mean:+.2f}%  "
                  f"(win rate {wins}/{len(vals)} = {100*wins/len(vals):.0f}%)")

    # ─── First 10-Q after each J-Book release ─────────────────────────────
    print("\n" + "=" * 100)
    print("EVENT 2: First quarterly report after each J-Book release "
          "(short T-1 close → T+N close)")
    print("=" * 100)
    quarterly_rollup = {n: [] for n in HOLDING_PERIODS}
    for event in JBOOK_RELEASES:
        d = event["date"]
        label = event["label"]
        print(f"\n--- First 10-Q after {label} ({d}) ---")
        print(f"{'TICKER':<7} {'10-Q DATE':<12} {'FORM':<6} {'T-1':>12} {'T-1$':>9}", end="")
        for n in HOLDING_PERIODS:
            print(f" {f'T+{n}%':>7}", end="")
        print()
        for tk in UNIVERSE:
            qs = _ten_q_dates_after(tk, d, max_count=1)
            if not qs:
                print(f"{tk:<7} (no 10-Q found after {d})")
                continue
            q = qs[0]
            q_date = q["date"]
            prices = _fetch_window(tk, q_date)
            if not prices:
                print(f"{tk:<7} {q_date:<12} {q['form']:<6} (no prices)")
                continue
            er = _event_returns(prices, q_date)
            if not er:
                print(f"{tk:<7} {q_date:<12} {q['form']:<6} (window err)")
                continue
            t_minus = er["T_minus_1"]
            print(f"{tk:<7} {q_date:<12} {q['form']:<6} {t_minus[0]:>12} ${t_minus[1]:>7.2f}", end="")
            for n in HOLDING_PERIODS:
                r = er.get(f"short_return_T{n}_pct")
                if r is None:
                    print(f" {'-':>7}", end="")
                else:
                    print(f" {r:>+6.1f}%", end="")
                    quarterly_rollup[n].append(r)
            print()

    print("\n--- POOLED across all post-JBook quarterly reports ---")
    for n in HOLDING_PERIODS:
        vals = quarterly_rollup[n]
        if vals:
            mean = sum(vals) / len(vals)
            wins = sum(1 for v in vals if v > 0)
            print(f"  T+{n:>2d} mean short return: {mean:+.2f}%  "
                  f"(win rate {wins}/{len(vals)} = {100*wins/len(vals):.0f}%)")

    # Write artifact
    artifact = {
        "universe": UNIVERSE,
        "jbook_releases": JBOOK_RELEASES,
        "holding_periods_days": HOLDING_PERIODS,
        "jbook_pooled_means": {
            n: (sum(jbook_rollup[n])/len(jbook_rollup[n]) if jbook_rollup[n] else None,
                 sum(1 for v in jbook_rollup[n] if v > 0), len(jbook_rollup[n]))
            for n in HOLDING_PERIODS
        },
        "quarterly_pooled_means": {
            n: (sum(quarterly_rollup[n])/len(quarterly_rollup[n]) if quarterly_rollup[n] else None,
                 sum(1 for v in quarterly_rollup[n] if v > 0), len(quarterly_rollup[n]))
            for n in HOLDING_PERIODS
        },
    }
    out = DATA / "_jbook_exposure_cohort_2024" / f"event_returns_{_COHORT}.json"
    out.write_text(json.dumps(artifact, indent=2, default=str))
    print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
