"""ib_quote_daemon — streams IBKR Gateway quotes into the desk (2026-07-03).

Standalone process (launchd-supervised, own asyncio loop — never inside the web server): connects
READ-ONLY (readonly=True: zero write-tier calls), polls snapshots for the decision-relevant registry
names every cycle, writes desk/data/ib_live_quotes.json. The price service layers this file ABOVE
yfinance: fresh IB quote -> basis 'live', and yfinance becomes the cross-check leg of the divergence
rail (a true second source at last).

Gracefully degrades: empty ticks (live-session held by the user's mobile) -> the file simply doesn't
update and the price service falls through to yfinance. The daemon never places, modifies, or queries
orders — the Gateway's Read-Only mode enforces this at the wire.

  python3 -m desk.ib_quote_daemon           # foreground loop
"""
from __future__ import annotations
import json, time, datetime, sys, functools
print = functools.partial(print, flush=True)   # launchd logs buffer without this
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "data" / "ib_live_quotes.json"
CYCLE_S = 15
US_ONLY = True          # foreign lines need per-exchange contracts — phase 2


def decision_names() -> list[tuple[str, str]]:
    """(ticker, yf) for ledger names worth streaming: held/ownable/starter + calendar names, US lines."""
    from desk.verdicts import BUYISH
    out = []
    try:
        led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text())["names"]
        for n in led:
            if (n.get("state") or n.get("verdict")) in BUYISH and n.get("yf"):
                yf = n["yf"]
                if US_ONLY and "." in yf:
                    continue
                out.append((n["ticker"], yf))
    except Exception:
        pass
    return out[:40]


def run():
    from ib_insync import IB, Stock
    ib = IB()
    print(f"ib_quote_daemon starting {datetime.datetime.utcnow().isoformat()}Z")
    ib.connect("127.0.0.1", 4001, clientId=42, timeout=15, readonly=True)
    ib.reqMarketDataType(3)          # live if entitled, delayed otherwise
    names = decision_names()
    contracts = {}
    for t, yf in names:
        try:
            c = Stock(yf, "SMART", "USD")
            ib.qualifyContracts(c)
            contracts[t] = c
        except Exception:
            pass
    print(f"ib_quote_daemon: {len(contracts)} US decision names subscribed (readonly)")
    tickers = {t: ib.reqMktData(c, "", False, False) for t, c in contracts.items()}
    while True:
        ib.sleep(CYCLE_S)
        now = time.time()
        payload = {}
        for t, tk in tickers.items():
            px = tk.last if tk.last == tk.last else (tk.marketPrice() if tk.marketPrice() == tk.marketPrice() else None)
            if px and px > 0:
                payload[t] = {"px": round(float(px), 4),
                              "bid": (round(float(tk.bid), 4) if tk.bid and tk.bid > 0 else None),
                              "ask": (round(float(tk.ask), 4) if tk.ask and tk.ask > 0 else None),
                              "mdt": tk.marketDataType, "asof": now}
        if payload:
            OUT.write_text(json.dumps({"asof": now, "asof_iso": datetime.datetime.utcnow().isoformat() + "Z",
                                       "quotes": payload}))
            print(f"wrote {len(payload)} quotes")
        else:
            print("cycle: no ticks (live slot busy or market closed)")
        if not ib.isConnected():
            print("gateway connection lost — exiting for launchd restart")
            raise SystemExit(1)


if __name__ == "__main__":
    run()
