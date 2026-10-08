"""Chain capture for the 0DTE sleeve: XSP 0DTE band (±BAND_PCT around spot), SPX, VIX1D — one
row per minute into desk/data/odte/chains/DATE.jsonl. Streaming subscriptions (not snapshots: a
snapshot per leg per minute is billed), re-centred when spot drifts out of the band.

Market data honesty: if the feed carries no live quotes after the grace period the capture
switches to DELAYED (reqMarketDataType 3) and tags every row data_type="delayed"; the shadow book
still runs (a shadow fill on delayed data is marked as such) and the LIVE rail refuses to trade on
anything but data_type="live". Model greeks come from tick 106 when the subscription carries them;
otherwise delta falls back to Black-Scholes with VIX1D as the vol and the row says so.
"""
from __future__ import annotations

import datetime as dt
import json
import math
from zoneinfo import ZoneInfo

from desk.odte.doctrine import (CHAINS, INSTRUMENT, UNDERLYING_CONID, SPX_CONID, VIX1D_CONID, STRIKE_STEP, BAND_PCT)
from desk.odte.templates import bs_delta

ET = ZoneInfo("America/New_York")
MAX_QUOTE_AGE_SECONDS = 90              # indices: SPX/XSP/VIX1D tick continuously; 90s silent = dead
# Options: IBKR only sends a tick when the quote CHANGES. A 0.00/0.05 wing can sit unchanged for many
# minutes and is still the quote (2026-10-07 review: a 90s per-leg rule nulled unchanged wings and
# would have blocked the 15:45 exit). A leg is valid while the CHAIN is alive (any option price tick
# in the last CHAIN_LIVENESS_SECONDS) and the leg itself has quoted within a generous window.
OPTION_QUOTE_MAX_AGE_SECONDS = 1800
CHAIN_LIVENESS_SECONDS = 120


def _f(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def t_years_to_close(now_et: dt.datetime) -> float:
    close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
    return max(0.0, (close - now_et).total_seconds()) / (365.0 * 24 * 3600)


class ChainCapture:
    def __init__(self, ib, expiry: str, band_pct: float = BAND_PCT):
        self.ib = ib; self.expiry = expiry; self.band_pct = band_pct
        self.tickers: dict[tuple[float, str], object] = {}
        self.idx = {}; self.data_type = "unknown"; self._centre = None; self._live_checked = False
        self._quote_times = {}
        ib.pendingTickersEvent += self._on_ticks
        ib.reqMarketDataType(1)
        from ib_insync import Index
        self.xsp = Index(INSTRUMENT, "CBOE", "USD"); self.spx = Index("SPX", "CBOE", "USD"); self.vix1d = Index("VIX1D", "CBOE", "USD")
        ib.qualifyContracts(self.xsp, self.spx, self.vix1d)
        assert self.xsp.conId == UNDERLYING_CONID and self.spx.conId == SPX_CONID and self.vix1d.conId == VIX1D_CONID, "conId drift"
        for c in (self.xsp, self.spx, self.vix1d):
            self.idx[c.symbol] = ib.reqMktData(c, "", False, False)

    def _on_ticks(self, tickers) -> None:
        # Ticker.time can advance on size/greek updates while the actual price
        # stays stale. Track the relevant price tick, not the snapshot clock.
        fields = {1: "bid", 2: "ask", 4: "last", 66: "bid", 67: "ask", 68: "last"}
        for ticker in tickers:
            times = self._quote_times.setdefault(ticker.contract.conId, {})
            for tick in ticker.ticks:
                if tick.tickType in fields:
                    times[fields[tick.tickType]] = tick.time

    def _fresh(self, ticker, fields, now, max_age: float = MAX_QUOTE_AGE_SECONDS) -> bool:
        times = self._quote_times.get(ticker.contract.conId, {})
        return all(isinstance(times.get(field), dt.datetime) and times[field].tzinfo is not None
                   and 0 <= (now - times[field]).total_seconds() <= max_age for field in fields)

    def chain_live(self, now) -> bool:
        """The option feed is alive if ANY option leg printed a price tick recently. Unchanged quotes
        on individual legs are not staleness; a silent chain is."""
        latest = None
        for t in self.tickers.values():
            for ts in self._quote_times.get(t.contract.conId, {}).values():
                if isinstance(ts, dt.datetime) and ts.tzinfo is not None and (latest is None or ts > latest):
                    latest = ts
        return latest is not None and 0 <= (now - latest).total_seconds() <= CHAIN_LIVENESS_SECONDS

    def _index_price(self, symbol, now):
        ticker = self.idx[symbol]
        price = _f(ticker.last)
        return price if price is not None and price > 0 and self._fresh(ticker, ("last",), now) else None

    def _spot(self) -> float | None:
        return self._index_price(INSTRUMENT, dt.datetime.now(ET))

    def ensure_band(self, spot: float) -> None:
        """Subscribe the strike band around spot; re-centre when spot moves > 40% of the half-band."""
        if self._centre is not None and abs(spot - self._centre) < 0.4 * self.band_pct * spot:
            return
        from ib_insync import Option
        lo = math.floor(spot * (1 - self.band_pct)); hi = math.ceil(spot * (1 + self.band_pct))
        want = {(float(k), r) for k in range(lo, hi + 1) for r in ("P", "C")}
        for key in [k for k in self.tickers if k not in want]:
            try:
                self.ib.cancelMktData(self.tickers[key].contract)
            except Exception:
                pass
            del self.tickers[key]
        new = [Option(INSTRUMENT, self.expiry, k, r, "SMART", tradingClass=INSTRUMENT, currency="USD")
               for (k, r) in sorted(want) if (k, r) not in self.tickers]
        if new:
            q = self.ib.qualifyContracts(*new)
            for c in q:
                if c.conId:
                    self.tickers[(float(c.strike), c.right)] = self.ib.reqMktData(c, "106", False, False)
        self._centre = spot

    def maybe_fallback_delayed(self, grace_s: float = 20.0) -> None:
        if self._live_checked:
            return
        self.ib.sleep(grace_s)
        if not any(_f(t.bid) is not None and t.bid >= 0 for t in self.tickers.values()):
            self.ib.reqMarketDataType(3); self.data_type = "delayed"
            for key, t in list(self.tickers.items()):
                self.tickers[key] = self.ib.reqMktData(t.contract, "106", False, False)
        self._live_checked = True

    def snapshot(self, now_et: dt.datetime | None = None) -> dict:
        now_et = now_et or dt.datetime.now(ET)
        spot = self._index_price(INSTRUMENT, now_et)
        spx = self._index_price("SPX", now_et)
        vix = self._index_price("VIX1D", now_et)
        indices_live = all(self._index_price(symbol, now_et) is not None and ticker.marketDataType == 1
                           for symbol, ticker in self.idx.items())
        rows = []; greeks_src = "model"
        T = t_years_to_close(now_et)
        chain_live = self.chain_live(now_et)
        for (k, r), t in sorted(self.tickers.items()):
            g = getattr(t, "modelGreeks", None)
            delta = _f(g.delta) if g else None
            if delta is None and spot and vix:
                delta = round(bs_delta(spot, k, T, vix / 100.0, r), 4); greeks_src = "bs_vix1d"
            bid = _f(t.bid); ask = _f(t.ask)
            bid = 0.0 if (bid is not None and bid < 0) else bid     # IBKR reports "no bid" as -1 (seen 2026-10-07 smoke test)
            ask = None if (ask is not None and ask < 0) else ask
            fresh = chain_live and self._fresh(t, ("bid", "ask"), now_et, OPTION_QUOTE_MAX_AGE_SECONDS)
            live_eligible = fresh and t.marketDataType == 1 and bid is not None and ask is not None and 0 <= bid <= ask and ask > 0
            if not chain_live:
                bid = ask = None                 # the whole feed is silent: nothing here is a quote
            times = self._quote_times.get(t.contract.conId, {})
            age = max(((now_et - ts).total_seconds() for ts in times.values() if isinstance(ts, dt.datetime) and ts.tzinfo is not None), default=None)
            rows.append({"live_eligible": live_eligible, "market_data_type": t.marketDataType, "quote_age_s": round(age) if age is not None else None,
                         "strike": k, "right": r, "bid": bid, "ask": ask, "last": _f(t.last),
                         "delta": delta, "iv": _f(g.impliedVol) if g else None, "conId": t.contract.conId})
        return {"ts": now_et.isoformat(timespec="seconds"), "expiry": self.expiry, "xsp": spot, "spx": spx, "vix1d": vix,
                "data_type": "live" if indices_live and all(t.marketDataType == 1 for t in self.tickers.values()) else ("delayed" if any(t.marketDataType in (3, 4) for t in self.idx.values()) else "unavailable"),
                "indices_live": indices_live, "chain_live": chain_live, "greeks": greeks_src,
                "n_quoted": sum(1 for r in rows if r["bid"] is not None), "rows": rows}

    @staticmethod
    def write(snap: dict, date: str) -> None:
        CHAINS.mkdir(parents=True, exist_ok=True)
        with (CHAINS / f"{date}.jsonl").open("a") as f:
            f.write(json.dumps(snap) + "\n")

    def close(self) -> None:
        self.ib.pendingTickersEvent -= self._on_ticks
        for t in list(self.tickers.values()) + list(self.idx.values()):
            try:
                self.ib.cancelMktData(t.contract)
            except Exception:
                pass


def replay(date: str) -> list[dict]:
    p = CHAINS / f"{date}.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
