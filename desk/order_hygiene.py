"""order_hygiene — resting-order × print-date sweep (the NATR postmortem, 2026-08-07).

The miss: NATR's court starter (BUY 353 @ 19.81 GTC) rested at the broker while NATR
printed; the limit filled into the print drop (~$1k adverse selection — the STNG rule
executed against us by our own resting book). catalyst_calendar_guard guards CALIBRATION
CALLS against early prints; NOTHING guarded ORDERS. This module closes that: every
resting order's ticker is joined against its next earnings date, and any order riding
into a print inside WINDOW_DAYS is emailed as PRINCIPAL-ACTION unless a court has
RATIFIED the ride (desk/data/order_ride_ratifications.json — the ACEL precedent, where
the court explicitly ruled "rungs RIDE the print").

Policy:
  BUY  inside window -> CRITICAL PULL-BEFORE-PRINT (a below-market buy fills on BAD news)
  SELL inside window -> TRIM-RIDES-PRINT notice (a trim filling on a pop is usually the
       intent, but it caps upside — SLS lesson — so it's surfaced, not alarmed)
  orders_cache stale (>36h) with prints upcoming -> CRITICAL ORDER-HYGIENE-BLIND
       (silence must not read as a clean book)

Runs inside pipeline_monitor's hourly pass (flags merge into the same rate-limited
email rail) and by hand: python3 -m desk.order_hygiene
"""
from __future__ import annotations

import datetime
import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDERS_CACHE = ROOT / "desk" / "ui" / "data" / "orders_cache.json"
RATIFICATIONS = ROOT / "desk" / "data" / "order_ride_ratifications.json"
STATE = ROOT / "desk" / "data" / "calendar_guard_state.json"   # SHARED earnings cache (merge-only)

WINDOW_DAYS = 5           # calendar days ~ 3 trading days
CACHE_DAYS = 7
STALE_CACHE_H = 36
PER_TICKER_TIMEOUT = 15
MAX_WORKERS = 8


def _load(p: Path, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def _ratified() -> dict:
    """{order_id_or_ticker: {until, basis}} — court-blessed ride-throughs."""
    out = {}
    today = datetime.date.today().isoformat()
    for k, v in _load(RATIFICATIONS, {}).items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if (v.get("until") or "9999") >= today:
            out[str(k)] = v
    return out


def _earnings_for(tickers: list[str]) -> dict[str, str | None]:
    """ticker -> next print date, via the shared calendar_guard cache + yfinance pool.
    Merge-only writes to the shared state (the overwrite-clobber rule)."""
    from desk.catalyst_calendar_guard import _next_earnings, _yf_symbol
    st = _load(STATE, {})
    cache = st.setdefault("earnings_cache", {})
    today = datetime.date.today()
    out, fetch = {}, []
    for t in tickers:
        c = cache.get(t)
        if c and c.get("fetched") and \
           (today - datetime.date.fromisoformat(c["fetched"])).days < CACHE_DAYS and \
           (c.get("next") is None or c["next"] >= today.isoformat()):
            out[t] = c.get("next")
        else:
            fetch.append(t)
    if fetch:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futs = {t: pool.submit(_next_earnings, _yf_symbol(t) or t) for t in fetch}
            for t, f in futs.items():
                try:
                    out[t] = f.result(timeout=PER_TICKER_TIMEOUT)
                except (FutTimeout, Exception):
                    out[t] = None                      # DATA MISSING, reported below
                cache[t] = {"next": out[t], "fetched": today.isoformat()}
        st2 = _load(STATE, {})                          # merge-only: re-read, update, write
        st2.setdefault("earnings_cache", {}).update(cache)
        STATE.write_text(json.dumps(st2, indent=1))
    return out


def sweep() -> list[str]:
    oc = _load(ORDERS_CACHE, {})
    orders = oc.get("orders", [])
    flags: list[str] = []
    today = datetime.date.today()
    horizon = (today + datetime.timedelta(days=WINDOW_DAYS)).isoformat()

    asof = oc.get("asof")
    stale_h = (time.time() - asof) / 3600 if isinstance(asof, (int, float)) else 1e9
    if not orders:
        return ["CRITICAL ORDER-HYGIENE-BLIND: orders_cache empty/unreadable — the resting "
                "book is unverifiable; run positions_sync (gateway up?)"]

    tickers = sorted({str(o.get("ticker") or o.get("symbol") or "") for o in orders} - {""})
    earnings = _earnings_for(tickers)
    rat = _ratified()

    if stale_h > STALE_CACHE_H:
        soon = [t for t in tickers if earnings.get(t) and earnings[t] <= horizon]
        if soon:
            flags.append(f"CRITICAL ORDER-HYGIENE-BLIND: orders_cache is {stale_h:.0f}h old and "
                         f"{len(soon)} order-tickers print within {WINDOW_DAYS}d ({', '.join(soon[:8])}) — "
                         f"refresh positions_sync (gateway) so the pre-print sweep sees the live book")

    unresolvable = []
    for o in orders:
        t = str(o.get("ticker") or o.get("symbol") or "")
        nxt = earnings.get(t)
        if not t:
            continue
        if nxt is None:
            unresolvable.append(t)
            continue
        if not (today.isoformat() <= nxt <= horizon):
            continue
        oid = str(o.get("order_id") or o.get("orderId") or o.get("permId") or "")
        if oid in rat or t in rat:
            continue                                    # court-blessed ride (ACEL pattern)
        side = str(o.get("side") or o.get("action") or "?").upper()
        desc = (f"{t} prints {nxt} — resting {side} {o.get('qty') or o.get('totalQuantity')}"
                f"@{o.get('limit') or o.get('lmtPrice')} (order {oid or 'id?'})")
        if side.startswith("B"):
            flags.append(f"CRITICAL PULL-BEFORE-PRINT: {desc} — a below-market buy fills on "
                         f"BAD news (NATR/STNG rule): cancel in TWS, or ratify the ride in "
                         f"order_ride_ratifications.json with a court basis")
        else:
            flags.append(f"TRIM-RIDES-PRINT: {desc} — trim fills on a pop (usually intended; "
                         f"caps upside — confirm or ratify)")
    if unresolvable:
        uniq = sorted(set(unresolvable))
        flags.append(f"ORDER-HYGIENE-NODATE: no earnings date resolvable for {len(uniq)} "
                     f"order-tickers ({', '.join(uniq[:10])}{'…' if len(uniq) > 10 else ''}) — "
                     f"unguarded, not clean (foreign names need manual dates in the ratifications "
                     f"file or calendar_guard cache)")
    return flags


if __name__ == "__main__":
    for f in sweep():
        print(f)
