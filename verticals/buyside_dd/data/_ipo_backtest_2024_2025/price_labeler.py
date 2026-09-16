"""Price-based outcome layer, survivorship-aware.

yfinance retains names that still trade (incl. penny stocks down 90%) but DROPS
fully-delisted names. We do NOT treat a yfinance gap as benign: the EDGAR
hard-event layer (outcomes_edgar.json) fills those gaps, so a name yfinance
can't price is checked against delisting/deregistration before being labeled.

Per name (entry = first-day close, per the audit — not the IPO offer price):
  - r_current     latest close / entry - 1
  - r_180d        first close on/after ipo_date+180d / entry - 1
  - max_drawdown  min(close) / entry - 1   (trough from entry)
  - coverage      yfinance | empty

Unified labels written to outcomes.json:
  - catastrophe (bool): EDGAR hard-adverse OR max_dd<=-0.70 OR r_current<=-0.50
  - delisted_no_price (bool): yfinance empty AND EDGAR ADVERSE-delisted/deregistered
  - merger_no_price (bool): yfinance empty AND delisted via merger/take-private —
    NOT a loss; shareholders cashed out. Excluded from return basket (no buyout
    price), never assigned -1.0.

Run: python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/price_labeler.py
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).parent
COHORT = HERE / "cohort.json"
EDGAR = HERE / "outcomes_edgar.json"
OUT = HERE / "outcomes.json"

END = "2026-05-29"
CATASTROPHE_DD = -0.70
CATASTROPHE_RET = -0.50

import yfinance as yf  # noqa: E402


def _history(ticker: str, ipo_date: str):
    import time
    last_exc = None
    for attempt in range(4):
        try:
            return yf.Ticker(ticker).history(start=ipo_date, end=END, auto_adjust=True)
        except Exception as e:  # transient yfinance/network errors
            last_exc = e
            time.sleep(1.5 * (attempt + 1))
    raise last_exc


def price_one(ticker: str, ipo_date: str) -> dict:
    h = _history(ticker, ipo_date)
    if h.empty:
        return {"coverage": "empty"}
    c = h["Close"].dropna()
    if c.empty:
        return {"coverage": "empty"}
    entry = float(c.iloc[0])
    if entry <= 0:
        return {"coverage": "empty"}
    last = float(c.iloc[-1])
    horizon = (date.fromisoformat(ipo_date) + timedelta(days=180)).isoformat()
    after = c[c.index.strftime("%Y-%m-%d") >= horizon]
    r_180d = (float(after.iloc[0]) / entry - 1) if len(after) else None
    return {
        "coverage": "yfinance",
        "entry_close": round(entry, 4),
        "last_close": round(last, 4),
        "last_data_date": c.index[-1].strftime("%Y-%m-%d"),
        "n_trading_days": int(len(c)),
        "r_current": round(last / entry - 1, 4),
        "r_180d": round(r_180d, 4) if r_180d is not None else None,
        "max_drawdown": round(float(c.min()) / entry - 1, 4),
    }


def main() -> None:
    cohort = json.loads(COHORT.read_text())["cohort"]
    edgar = {e["cik"]: e for e in json.loads(EDGAR.read_text())["labels"]}

    out = []
    for i, rec in enumerate(cohort):
        cik = rec["cik"]
        ticker = (rec["tickers"] or [None])[0]
        ed = edgar.get(cik, {})
        hard = bool(ed.get("hard_adverse"))
        merger = bool(ed.get("merger_delist"))
        # Adverse delist only; merger delists are cash-outs, not failures.
        adverse_delisted = bool(ed.get("delisted_date") or ed.get("deregistered_date")) \
            and not merger

        p = {"coverage": "no_ticker"} if not ticker else price_one(ticker, rec["ipo_date"])

        max_dd = p.get("max_drawdown")
        r_cur = p.get("r_current")
        price_catastrophe = (max_dd is not None and max_dd <= CATASTROPHE_DD) or \
                            (r_cur is not None and r_cur <= CATASTROPHE_RET)
        catastrophe = hard or price_catastrophe
        no_price = p["coverage"] != "yfinance"
        delisted_no_price = no_price and adverse_delisted
        merger_no_price = no_price and merger

        out.append({
            "cik": cik, "ticker": ticker, "company_name": rec["company_name"],
            "ipo_date": rec["ipo_date"], "sic": rec.get("sic"),
            **{k: ed.get(k) for k in
               ("delisted_date", "deregistered_date", "bankruptcy_date",
                "restatement_date", "auditor_exit_date", "merger_delist",
                "hard_adverse")},
            **p,
            "catastrophe": catastrophe,
            "delisted_no_price": delisted_no_price,
            "merger_no_price": merger_no_price,
        })
        if i % 25 == 24:
            nc = sum(1 for o in out if o["catastrophe"])
            ne = sum(1 for o in out if o["coverage"] != "yfinance")
            print(f"  {i+1}/{len(cohort)} | catastrophe {nc} | unpriced {ne}", file=sys.stderr)

    n = len(out)
    priced = [o for o in out if o["coverage"] == "yfinance"]
    summary = {
        "n": n,
        "n_priced": len(priced),
        "n_unpriced": n - len(priced),
        "n_delisted_no_price": sum(1 for o in out if o["delisted_no_price"]),
        "n_merger_delist": sum(1 for o in out if o.get("merger_delist")),
        "n_merger_no_price": sum(1 for o in out if o["merger_no_price"]),
        "n_catastrophe": sum(1 for o in out if o["catastrophe"]),
        "catastrophe_rate": round(sum(1 for o in out if o["catastrophe"]) / max(1, n), 4),
        "median_r_current": _median([o["r_current"] for o in priced]),
        "median_max_drawdown": _median([o["max_drawdown"] for o in priced]),
    }
    OUT.write_text(json.dumps({"summary": summary, "labels": out}, indent=2))
    print("\n=== OUTCOME SUMMARY ===", file=sys.stderr)
    for k, v in summary.items():
        print(f"  {k:<22} {v}", file=sys.stderr)
    print(f"Wrote {OUT.name}", file=sys.stderr)


def _median(xs):
    xs = sorted(v for v in xs if v is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return round((xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2), 4)


if __name__ == "__main__":
    main()
