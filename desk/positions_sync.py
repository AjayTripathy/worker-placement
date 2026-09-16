"""positions_sync — pulls ACTUAL holdings from the IB Gateway (read-only) into positions_cache.json.
The single source of "we hold X" (plans != holdings lesson, 2026-07-04). Runs on the heartbeat;
the validator cross-checks ledger HELD states against this cache both directions.

  python3 -m desk.positions_sync
READ-ONLY (readonly=True — zero write-tier calls).
"""
from __future__ import annotations
import json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "ui" / "data" / "positions_cache.json"
ORDERS_OUT = ROOT / "desk" / "ui" / "data" / "orders_cache.json"
# IBKR contract symbols -> our ledger tickers (venue suffixes differ)
SYMBOL_MAP = {"BRBY": "BRBY.L", "HSBK": "HSBK.L", "TBCG": "TBCG.L", "MHPC": "MHPC.L",
              "AST": "AST.WAR", "PEO": "PEO.WA", "MC": "MC.PA", "SAP": "SAP.DE", "POLI": "POLI.TA",
              "005387": "005387.KS", "003550": "003550.KS", "KER": "KER.PA"}


def main():
    from ib_insync import IB
    ib = IB()
    ib.connect("127.0.0.1", 4001, clientId=23, timeout=15, readonly=True)
    rows = []
    for p in ib.positions():
        sym = p.contract.symbol
        t = SYMBOL_MAP.get(sym, sym)
        # avgCost for OPT/FOP is per CONTRACT (premium x multiplier); per-unit is what the
        # ledger/UI compare against quoted premiums (verified live on the SLS Jul17 10C: 117.71 vs 1.1771)
        mult = float(p.contract.multiplier or 1) if p.contract.secType in ("OPT", "FOP") else 1.0
        row = {"symbol": t, "qty": p.position, "avg_cost": round(p.avgCost, 4),
               "avg_cost_per_unit": round(p.avgCost / mult, 4), "multiplier": mult,
               "conid": p.contract.conId, "sec_type": p.contract.secType,
               "ccy": p.contract.currency}
        if p.contract.secType in ("OPT", "FOP"):
            # right (P/C) is load-bearing: the stacking watch mislabeled a short CALL as
            # "PUT LIFTED" because the cache didn't carry it (CAI, 2026-09-03)
            row.update({"right": p.contract.right, "strike": p.contract.strike,
                        "expiry": p.contract.lastTradeDateOrContractMonth})
        rows.append(row)
    # open working orders — the ground truth the ENTRY tab's approve state should reflect
    orders = []
    try:
        for tr in ib.reqAllOpenOrders():
            c, o, st = tr.contract, tr.order, tr.orderStatus.status
            sym = SYMBOL_MAP.get(c.symbol, c.symbol)
            row = {"symbol": sym, "action": o.action, "qty": o.totalQuantity,
                   "limit": getattr(o, "lmtPrice", None), "status": st,
                   "conid": c.conId, "ccy": c.currency, "sec_type": c.secType}
            if c.secType in ("OPT", "FOP"):
                row.update({"right": c.right, "strike": c.strike,
                            "expiry": c.lastTradeDateOrContractMonth})
            orders.append(row)
    except Exception as e:
        print(f"  open-orders pull failed: {e}")
    ib.disconnect()
    ORDERS_OUT.write_text(json.dumps({"asof": time.time(), "source": "ib_gateway_readonly",
                                      "orders": orders}, indent=1))
    OUT.write_text(json.dumps({"asof": time.time(), "source": "ib_gateway_readonly",
                               "positions": rows}, indent=1))
    print(f"positions_sync: {len(rows)} positions + {len(orders)} working orders cached")
    for r in rows:
        print(f"  {r['symbol']:<9} {r['qty']:>9} {r['sec_type']} {r['ccy']}")


if __name__ == "__main__":
    main()
