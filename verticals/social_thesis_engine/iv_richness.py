"""iv_richness — is a name's options vol RICH (sellable) or CHEAP, per SPEC.md §4.

For each ticker: current option-implied vol (IV) vs 30d realized historical vol (HV), and IV's
percentile vs its own trailing-1Y history. RICH = IV/HV >= 1.20 AND IV-percentile >= 70.
CHEAP = IV <= HV. Source = IBKR/TWS via ib_insync (TWS must be running with API enabled).

Used by triage.py: social attention pumps IV → this flags where the vol is actually overpriced
so the "be the casino" arm can sell defined-risk premium into it.
"""
from __future__ import annotations

import statistics
import sys
from typing import Optional

from ib_insync import IB, Stock

RICH_IV_HV = 1.20
RICH_PCTILE = 70.0


def _connect(ib: IB) -> Optional[int]:
    for port in (7496, 7497, 4001, 4002):
        try:
            ib.connect("127.0.0.1", port, clientId=29, timeout=8, readonly=True)
            return port
        except Exception:
            continue
    return None


def richness_batch(tickers: list[str]) -> dict:
    """Return {ticker: {iv, hv, iv_hv, iv_pctile, verdict: RICH|CHEAP|NEUTRAL|UNAVAILABLE}}."""
    ib = IB()
    port = _connect(ib)
    if not port:
        return {t: {"verdict": "UNAVAILABLE", "error": "no TWS connection"} for t in tickers}
    ib.reqMarketDataType(1)
    out: dict[str, dict] = {}
    for t in tickers:
        try:
            c = Stock(t, "SMART", "USD")
            ib.qualifyContracts(c)
            tk = ib.reqMktData(c, genericTickList="104,106", snapshot=False)
            ib.sleep(2.0)
            iv = tk.impliedVolatility
            hv = tk.histVolatility
            # 1Y daily implied-vol history for the percentile
            pctile = None
            try:
                bars = ib.reqHistoricalData(c, endDateTime="", durationStr="1 Y",
                                            barSizeSetting="1 day",
                                            whatToShow="OPTION_IMPLIED_VOLATILITY",
                                            useRTH=True, timeout=20)
                hist = [b.close for b in bars if b.close and b.close > 0]
                if hist and iv:
                    pctile = round(100 * sum(1 for x in hist if x <= iv) / len(hist), 1)
            except Exception:
                pass
            ib.cancelMktData(c)
            rec = {"iv": round(iv, 3) if iv else None,
                   "hv": round(hv, 3) if hv else None,
                   "iv_hv": round(iv / hv, 2) if (iv and hv) else None,
                   "iv_pctile": pctile}
            if iv and hv:
                if rec["iv_hv"] >= RICH_IV_HV and (pctile is None or pctile >= RICH_PCTILE):
                    rec["verdict"] = "RICH"
                elif iv <= hv:
                    rec["verdict"] = "CHEAP"
                else:
                    rec["verdict"] = "NEUTRAL"
            else:
                rec["verdict"] = "UNAVAILABLE"
            out[t] = rec
        except Exception as e:
            out[t] = {"verdict": "UNAVAILABLE", "error": str(e)[:80]}
        ib.sleep(0.3)
    ib.disconnect()
    return out


if __name__ == "__main__":
    ts = sys.argv[1:] or ["MU", "MSFT", "BB", "SNDK", "ASTS"]
    res = richness_batch(ts)
    print(f"{'TICKER':7}{'IV':>7}{'HV':>7}{'IV/HV':>7}{'IVpct':>7}  VERDICT")
    for t in ts:
        r = res.get(t, {})
        print(f"{t:7}{str(r.get('iv','-')):>7}{str(r.get('hv','-')):>7}"
              f"{str(r.get('iv_hv','-')):>7}{str(r.get('iv_pctile','-')):>7}  {r.get('verdict')}")
