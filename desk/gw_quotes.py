"""gw_quotes — screen-scale bulk quotes from the LOCAL IBKR Gateway (readonly).

Why: the screens grew up on yahoo's bulk endpoint and inherited its failure modes —
IP rate-limit storms (the 6,801-quote 429 wipeout, 2026-08-06), phantom ticks, unit
mislabels — while desk/prices.py doctrine already names the Gateway the TRUE live
layer. This module is the tape-scale sibling of the per-name daemon: delayed-OK
snapshot sweeps for screening (a screen needs yesterday-ish prices, not streams).

Mechanics: delayed market data (type 3 — no subscription dependence), snapshot=True
(frees market-data lines immediately), batches of ~80 under the line cap, conId cache
so qualification is one-time (desk/data/gw_conid_cache.json). Distinct clientId 41 —
never the positions_sync (23) or daemon connections. READONLY. Gateway down -> returns
{} and the caller falls back to its yahoo path (fallback, not default).

  from desk.gw_quotes import bulk_quotes
  qs = bulk_quotes(["AAPL", "FSBW", ...])   # {sym: {px, close, conid, ts}}
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONID_CACHE = ROOT / "desk" / "data" / "gw_conid_cache.json"
BATCH = 80
CLIENT_ID = 41


def _load_conids() -> dict:
    try:
        return json.loads(CONID_CACHE.read_text())
    except Exception:
        return {}


def bulk_stats(symbols: list[str], exchange="SMART", currency="USD",
               wait=4.0, verbose=True) -> dict:
    """px + 52-week high/low per symbol (generic tick 165). Generic ticks are refused in
    snapshot mode, so this streams each batch briefly and cancels — same line budget,
    slightly slower. Feeds the class-dislocation detector (drawdown = px/hi52 − 1)."""
    try:
        from ib_insync import IB, Contract
    except ImportError:
        return {}
    ib = IB()
    try:
        ib.connect("127.0.0.1", 4001, clientId=CLIENT_ID + 2, timeout=10, readonly=True)
    except Exception as e:
        if verbose:
            print(f"[gw_quotes.stats] gateway unreachable ({type(e).__name__})")
        return {}
    out = {}
    try:
        ib.reqMarketDataType(3)
        conids = _load_conids()
        missing = [s for s in symbols if s not in conids]
        if missing:
            from ib_insync import Stock
            for i in range(0, len(missing), 50):
                chunk = [Stock(s, exchange, currency) for s in missing[i:i + 50]]
                try:
                    ib.qualifyContracts(*chunk)
                except Exception:
                    pass
                for c in chunk:
                    conids[c.symbol] = c.conId or 0
            CONID_CACHE.write_text(json.dumps(conids))
        now = time.time()
        work = [(s, conids[s]) for s in symbols if conids.get(s)]
        for i in range(0, len(work), BATCH):
            batch = work[i:i + BATCH]
            try:
                tickers = []
                for s, cid in batch:
                    c = Contract(conId=cid, exchange=exchange)
                    tickers.append((s, c, ib.reqMktData(c, "165", False, False)))
                ib.sleep(wait)
            except (ConnectionError, OSError) as e:
                # flapping gateway: return the partial sweep — the CALLER's coverage
                # floor decides whether to fall back, never a mid-sweep exception
                if verbose:
                    print(f"[gw_quotes.stats] socket dropped at {i}/{len(work)} "
                          f"({type(e).__name__}) — returning partial ({len(out)} priced)")
                break
            for s, c, t in tickers:
                px = t.marketPrice()
                if px is None or (isinstance(px, float) and math.isnan(px)):
                    px = t.close
                hi = getattr(t, "high52week", None)
                lo = getattr(t, "low52week", None)
                ok = lambda x: x is not None and not (isinstance(x, float) and math.isnan(x)) and x > 0
                if ok(px):
                    out[s] = {"px": round(float(px), 4),
                              "hi52": round(float(hi), 4) if ok(hi) else None,
                              "lo52": round(float(lo), 4) if ok(lo) else None,
                              "conid": conids[s], "ts": now}
                ib.cancelMktData(c)
            if verbose and i % 800 == 0:
                print(f"[gw_quotes.stats] {i + len(batch)}/{len(work)} swept, {len(out)} priced")
    finally:
        ib.disconnect()
    return out


def bulk_quotes(symbols: list[str], exchange="SMART", currency="USD",
                snapshot_wait=3.0, verbose=True) -> dict:
    try:
        from ib_insync import IB, Stock, Contract
    except ImportError:
        if verbose:
            print("[gw_quotes] ib_insync unavailable — caller should fall back")
        return {}
    ib = IB()
    try:
        ib.connect("127.0.0.1", 4001, clientId=CLIENT_ID, timeout=10, readonly=True)
    except Exception as e:
        if verbose:
            print(f"[gw_quotes] gateway unreachable ({type(e).__name__}) — caller should fall back")
        return {}
    out = {}
    try:
        ib.reqMarketDataType(3)                       # delayed: subscription-independent
        conids = _load_conids()
        # ---- qualification (one-time per symbol, cached) ----
        unknown = [s for s in symbols if s not in conids]
        if unknown and verbose:
            print(f"[gw_quotes] qualifying {len(unknown)} new symbols (cached: {len(symbols)-len(unknown)})")
        for i in range(0, len(unknown), 50):
            chunk = [Stock(s, exchange, currency) for s in unknown[i:i + 50]]
            try:
                ib.qualifyContracts(*chunk)
            except Exception:
                pass
            for c in chunk:
                conids[c.symbol] = c.conId or 0       # 0 = unresolvable; cached so never retried
            if i % 1000 == 0 and i:
                CONID_CACHE.write_text(json.dumps(conids))
        CONID_CACHE.write_text(json.dumps(conids))
        # ---- snapshot sweep ----
        now = time.time()
        work = [(s, conids[s]) for s in symbols if conids.get(s)]
        for i in range(0, len(work), BATCH):
            batch = work[i:i + BATCH]
            tickers = []
            for s, cid in batch:
                c = Contract(conId=cid, exchange=exchange)
                tickers.append((s, ib.reqMktData(c, "", True, False)))
            ib.sleep(snapshot_wait)
            for s, t in tickers:
                px = t.marketPrice()
                if px is None or (isinstance(px, float) and math.isnan(px)):
                    px = t.close
                if px is not None and not (isinstance(px, float) and math.isnan(px)) and px > 0:
                    out[s] = {"px": round(float(px), 4),
                              "close": (round(float(t.close), 4)
                                        if t.close and not math.isnan(t.close) else None),
                              "conid": conids[s], "ts": now}
            if verbose and i % 800 == 0:
                print(f"[gw_quotes] {i + len(batch)}/{len(work)} swept, {len(out)} priced")
    finally:
        ib.disconnect()
    return out
