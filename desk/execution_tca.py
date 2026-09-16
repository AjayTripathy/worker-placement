"""execution_tca — post-fill transaction-cost analysis: the CALIBRATION LEDGER FOR EXECUTION
(2026-07-03: entries and predictions had scorecards; execution advice had none — unmeasured skill
doesn't improve).

Every fill is scored against: (a) the day's open, (b) the day's VWAP (1-minute bars when available,
daily approximation otherwise), (c) the day's close — slippage in bps, signed so NEGATIVE = we did
better than the benchmark. Fills are ingested from IBKR trade records (the assistant pastes them from
get_account_trades on its positions polls — this module never touches the broker).

  python3 -m desk.execution_tca ingest '{"symbol":"IBEX","side":"BUY","qty":155,"price":32.11,"date":"2026-07-03","yf":"IBEX"}'
  python3 -m desk.execution_tca report
READ-ONLY w.r.t. the broker.
"""
from __future__ import annotations
import json, sys, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "desk" / "data" / "execution_tca.json"


def _benchmarks(yf_sym: str, date: str) -> dict:
    import yfinance as yf
    out = {}
    try:
        t = yf.Ticker(yf_sym)
        intraday = t.history(start=date, period="1d", interval="1m")
        if len(intraday) > 30:
            v = intraday["Volume"].sum()
            out["vwap"] = float((intraday["Close"] * intraday["Volume"]).sum() / v) if v else None
            out["vwap_basis"] = "1m"
        daily = t.history(start=date, interval="1d")
        if len(daily):
            d0 = daily.iloc[0]
            out.setdefault("vwap", float((d0["High"] + d0["Low"] + d0["Close"]) / 3))
            out.setdefault("vwap_basis", "hlc3-approx")
            out["open"] = float(d0["Open"]); out["close"] = float(d0["Close"])
    except Exception:
        pass
    return out


def score_fill(fill: dict) -> dict:
    """Pure scoring given fill + benchmarks (separable for offline tests)."""
    b = fill.get("benchmarks") or {}
    px, side = fill["price"], fill.get("side", "BUY").upper()
    sgn = 1 if side == "BUY" else -1
    def bps(bench):
        return round((px - bench) / bench * 1e4 * sgn, 1) if bench else None
    return {**fill, "slip_vs_open_bps": bps(b.get("open")),
            "slip_vs_vwap_bps": bps(b.get("vwap")),
            "slip_vs_close_bps": bps(b.get("close"))}


def ingest(fill: dict) -> dict:
    fill.setdefault("benchmarks", _benchmarks(fill.get("yf") or fill["symbol"], fill["date"]))
    scored = score_fill(fill)
    store = json.loads(STORE.read_text()) if STORE.exists() else {"fills": []}
    key = (scored["symbol"], scored["date"], scored["qty"], scored["price"])
    if key not in [(f["symbol"], f["date"], f["qty"], f["price"]) for f in store["fills"]]:
        store["fills"].append(scored)
        STORE.write_text(json.dumps(store, indent=1))
    return scored


def report():
    if not STORE.exists():
        print("no fills ingested yet"); return
    fills = json.loads(STORE.read_text())["fills"]
    print(f"=== EXECUTION TCA  ({len(fills)} fills; negative bps = beat the benchmark) ===")
    for f in fills[-15:]:
        print(f"  {f['date']} {f['side']:<4} {f['qty']:>6} {f['symbol']:<8} @ {f['price']:<9}"
              f" vs VWAP {f.get('slip_vs_vwap_bps','—'):>7}bps  vs open {f.get('slip_vs_open_bps','—'):>7}bps  vs close {f.get('slip_vs_close_bps','—'):>7}bps")
    v = [f["slip_vs_vwap_bps"] for f in fills if f.get("slip_vs_vwap_bps") is not None]
    if v:
        print(f"  CUMULATIVE vs VWAP: median {statistics.median(v):+.1f}bps over {len(v)} fills")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "ingest":
        print(json.dumps(ingest(json.loads(sys.argv[2])), indent=1))
    else:
        report()


if __name__ == "__main__":
    main()
