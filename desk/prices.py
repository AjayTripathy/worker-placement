"""prices — the SINGLE source of pricing truth for the desk (built test-first, 2026-07-03).

Every consumer (aggregator, scanners, watches) calls get_price()/get_prices() and receives a
PriceQuote dict — never a bare float. Design goals map 1:1 to real incidents:
  - AMV0 stale-GO (2026-07-03): every quote carries asof/age/basis; freshness is EXCHANGE-HOURS aware
  - VSH bad tick: range sanity — outside the 52wk band ±20% => suspect, never silently trusted
  - CIB phantom book: cross-source divergence >2% => suspect
  - IVN/FM symbol drift: canonical REGISTRY resolves ticker -> {yf, exchange, ccy}; unknown symbols
    raise UnknownSymbol instead of silently returning nothing

yfinance is the default transport; IBKR-sourced quotes (agent-side MCP) can be pushed in via
register_external_quote() and take precedence while fresh. READ-ONLY.
"""
from __future__ import annotations
import json, math, time, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"


class UnknownSymbol(Exception):
    pass


PriceQuote = dict  # contract alias: quotes are plain dicts with the _mk_quote shape


# suffix -> (exchange, currency); exchange keys index MARKET_HOURS_UTC below
_SUFFIX = {
    ".TO": ("TSX", "CAD"), ".DE": ("XETRA", "EUR"), ".L": ("LSE", "GBP"), ".IL": ("LSE", "USD"),
    ".T": ("TSE", "JPY"), ".KS": ("KRX", "KRW"), ".WA": ("WSE", "PLN"), ".MI": ("BIT", "EUR"),
    ".PA": ("EPA", "EUR"), ".VI": ("WBAG", "EUR"), ".AT": ("ATH", "EUR"), ".AX": ("ASX", "AUD"),
}
# approximate regular-session hours in UTC (h_open, h_close); DST drift of ±1h is acceptable for
# freshness gating (we gate at 20min vs 3h scales, not minutes)
MARKET_HOURS_UTC = {
    "US": (13, 21), "NYSE": (13, 21), "NASDAQ": (13, 21),
    "TSX": (13, 21), "LSE": (7, 16), "XETRA": (7, 16), "BIT": (7, 16), "EPA": (7, 16),
    "WBAG": (7, 16), "ATH": (7, 16), "WSE": (7, 16),
    "TSE": (0, 6), "KRX": (0, 7), "ASX": (0, 6),
}
FRESH_OPEN_S = 20 * 60          # during session: quote must be < 20min old
FRESH_CLOSED_S = 24 * 3600      # session closed: yesterday's close is acceptable

# curated core (tradeable decision names); the rest auto-derive from the ledger's yf field
_CURATED = {
    "IVN":  {"yf": "IVN.TO"}, "FM": {"yf": "FM.TO"},
    "AMV0.DE": {"yf": "AMV0.DE"}, "8750.T": {"yf": "8750.T"},
    # LSE minefield: UK ordinaries quote in PENCE (GBp); IOB GDRs quote in USD — never infer from .L
    "HSBK.L": {"yf": "HSBK.IL", "ccy": "USD"}, "BRBY.L": {"yf": "BRBY.L", "ccy": "GBp"},
    "CBKD": {"yf": "CBKD.L", "ccy": "USD"}, "MHPC.L": {"yf": "MHPC.L", "ccy": "USD"},
    "TBCG.L": {"yf": "TBCG.L", "ccy": "GBp"},
    "003550.KS": {"yf": "003550.KS"}, "028260.KS": {"yf": "028260.KS"},
    "PEO.WA": {"yf": "PEO.WA"}, "FCT.MI": {"yf": "FCT.MI"},
}


def _exchange_for(yf_sym: str) -> tuple[str, str]:
    for suf, (ex, ccy) in _SUFFIX.items():
        if yf_sym.endswith(suf):
            return ex, ccy
    return "US", "USD"


def _build_registry() -> dict:
    reg = {}
    try:
        names = json.loads(LEDGER.read_text()).get("names", [])
    except Exception:
        names = []
    for n in names:
        yf = (n.get("yf") or "").strip()
        if not yf:
            continue
        ex, ccy = _exchange_for(yf)
        reg[n["ticker"]] = {"yf": yf, "exchange": ex, "ccy": ccy}
    for t, v in _CURATED.items():
        ex, ccy = _exchange_for(v["yf"])
        reg[t] = {"yf": v["yf"], "exchange": ex, "ccy": v.get("ccy", ccy)}
    return reg


REGISTRY = _build_registry()


def resolve(ticker: str) -> dict:
    r = REGISTRY.get(ticker)
    if not r:
        raise UnknownSymbol(f"{ticker} is not in the price registry — add its yf mapping to the ledger or _CURATED")
    return r


def _sanity(px: float, lo52: float | None, hi52: float | None) -> str | None:
    """VSH rule: a print outside the 52wk band ±20% is a data problem until proven otherwise."""
    if px is None or not lo52 or not hi52 or hi52 <= 0:
        return None
    if px < lo52 * 0.8 or px > hi52 * 1.2:
        return f"px {px} outside 52wk band [{lo52}, {hi52}] ±20% — suspect tick"
    return None


def _divergence(a: float | None, b: float | None, tol: float = 0.02) -> str | None:
    """CIB rule: two live sources disagreeing >2% means at least one is wrong."""
    if not a or not b:
        return None
    d = abs(a - b) / ((a + b) / 2)
    return f"cross-source divergence {d:.1%}" if d > tol else None


def _is_fresh(age_s: float | None, exchange: str, now_utc_hour: int | None = None) -> bool:
    """AMV0 rule: freshness is judged against the EXCHANGE clock, not the wall clock."""
    if age_s is None:
        return False
    h = datetime.datetime.utcnow().hour if now_utc_hour is None else now_utc_hour
    o, c = MARKET_HOURS_UTC.get(exchange, (13, 21))
    session_open = (o <= h < c) if o < c else (h >= o or h < c)
    return age_s < (FRESH_OPEN_S if session_open else FRESH_CLOSED_S)


def _mk_quote(ticker: str, px: float | None, source: str, basis: str, asof: float | None,
              lo52: float | None = None, hi52: float | None = None,
              alt_px: float | None = None, exchange: str = "US", ccy: str = "USD") -> dict:
    age = None if asof is None else max(0.0, time.time() - asof)
    if px is not None and (math.isnan(px) or math.isinf(px)):
        px = None
    reason = _sanity(px, lo52, hi52) or _divergence(px, alt_px)
    return {"ticker": ticker, "px": px, "source": source, "basis": basis, "ccy": ccy,
            "exchange": exchange, "asof": asof, "age_s": age,
            "fresh": _is_fresh(age, exchange), "suspect": bool(reason), "suspect_reason": reason}


# ---- cache + external (IBKR) quote injection ----
_CACHE: dict[str, dict] = {}          # yf_sym -> quote
_CLOSE_CACHE_PATH = ROOT / "desk" / "data" / "price_close_cache.json"


def _close_cache() -> dict:
    try:
        return json.loads(_CLOSE_CACHE_PATH.read_text())
    except Exception:
        return {}


def _remember_close(yf_sym: str, px: float):
    """Update the sticky referee — WITH HYSTERESIS (poisoning lesson 2026-07-03: a correlated flap
    passed the rails and overwrote the sticky with the phantom 1.71, after which the guard blessed
    the lie). A >15% move vs the current sticky must be CONFIRMED by a second consecutive update in
    the same direction before it's accepted; a real crash confirms in two cycles, a flap flip-flops
    and never does."""
    try:
        c = _close_cache()
        cur = c.get(yf_sym)
        newpx = round(float(px), 4)
        if cur and cur.get("px") and abs(newpx / cur["px"] - 1) > 0.15:
            pend = cur.get("pending")
            # confirmation needs BOTH agreement AND >=6h elapsed — a real crash persists across
            # sessions; a correlated flap window lasts minutes and self-confirms otherwise
            if pend and abs(newpx / pend - 1) <= 0.15 and (time.time() - cur.get("pending_asof", 0)) >= 6 * 3600:
                c[yf_sym] = {"px": newpx, "asof": time.time()}          # confirmed big move
            else:
                cur["pending"] = newpx                                   # first sighting — hold
                cur["pending_asof"] = time.time()
                c[yf_sym] = cur
        else:
            c[yf_sym] = {"px": newpx, "asof": time.time()}
        _CLOSE_CACHE_PATH.write_text(json.dumps(c))
    except Exception:
        pass
_EXTERNAL: dict[str, dict] = {}       # ticker -> quote pushed from an IBKR-sourced context
_TTL = 120


def register_external_quote(ticker: str, px: float, source: str = "ibkr", basis: str = "live"):
    r = resolve(ticker)
    _EXTERNAL[ticker] = _mk_quote(ticker, px, source, basis, time.time(),
                                  exchange=r["exchange"], ccy=r["ccy"])


def _reconcile_ccy(px, feed_ccy, want_ccy):
    """Return (px_in_want_ccy, problem). ONLY the pence/pounds pair is convertible (a unit, not an FX
    guess); any other disagreement quarantines the quote — never silently convert across real FX."""
    if px is None or not feed_ccy or not want_ccy or feed_ccy == want_ccy:
        return px, None
    pair = (feed_ccy, want_ccy)
    if pair == ("GBp", "GBP"):
        return px / 100.0, None
    if pair == ("GBP", "GBp"):
        return px * 100.0, None
    return px, f"feed says {feed_ccy}, registry says {want_ccy} — currency mismatch"


def quote_yf(yf_sym: str, ticker: str | None = None, exchange: str = "US", ccy: str = "USD") -> dict:
    now = time.time()
    c = _CACHE.get(yf_sym)
    if c and (now - (c["asof"] or 0)) < _TTL:
        return c
    px = lo = hi = None
    _ccy_prob = None
    basis, asof = "close", None
    try:
        import yfinance as yf
        fi = yf.Ticker(yf_sym).fast_info
        px = fi.get("last_price") or fi.get("lastPrice")
        lo = fi.get("year_low") or fi.get("yearLow")
        hi = fi.get("year_high") or fi.get("yearHigh")
        pc = fi.get("previous_close") or fi.get("previousClose")
        feed_ccy = fi.get("currency")
        px, _ccy_prob = _reconcile_ccy(px, feed_ccy, ccy)
        pc, _ = _reconcile_ccy(pc, feed_ccy, ccy)
        lo, _ = _reconcile_ccy(lo, feed_ccy, ccy)
        hi, _ = _reconcile_ccy(hi, feed_ccy, ccy)
        if px:
            asof = now                      # yfinance fast_info is delayed-live during sessions
            basis = "delayed"
    except Exception:
        pass
    q = _mk_quote(ticker or yf_sym, px, "yfinance", basis, asof, lo, hi, exchange=exchange, ccy=ccy)
    try:
        if _ccy_prob and not q["suspect"]:
            q = dict(q, suspect=True, suspect_reason=_ccy_prob)
    except NameError:
        pass
    # phantom-tick rail v4 (CBKD lesson 2026-07-03, three versions deep): the bad flap is time-correlated
    # across ALL yahoo endpoints (fast_info AND history return GBP-labeled-USD for the same window), so no
    # within-source check works. Referee = the STICKY last-known-good close on disk: it survives the flap
    # window; >15% divergence vs it (age <=5d) = suspect. Good quotes refresh the sticky close.
    try:
        refs = []
        if pc:
            refs.append(pc)
        try:
            import yfinance as _yf
            _h = _yf.Ticker(yf_sym).history(period="2d")["Close"]
            if len(_h):
                refs.append(float(_h.iloc[-1]))
        except Exception:
            pass
        sticky = _close_cache().get(yf_sym)
        if sticky and (time.time() - sticky.get("asof", 0)) < 5 * 86400:
            refs.append(sticky["px"])
        # FX-mislabel detector (CBKD persistent flap: the phantom is EXACTLY the GBP conversion of the
        # true USD price) — if px x GBPUSD reproduces a reference within 3%, it's a currency flap:
        # quarantine AND poison-proof (never let it near the sticky)
        try:
            if px and refs:
                fx = _close_cache().get("GBPUSD=X", {}).get("px") or 1.48
                for r in refs:
                    if r and abs(px * fx / r - 1) < 0.03:
                        q = dict(q, suspect=True, suspect_reason=f"px {px} x GBPUSD {fx} = {round(px*fx,2)} ≈ ref {round(r,2)} — currency-mislabel flap")
                        _CACHE[yf_sym] = q
                        return q
        except Exception:
            pass
        bad = [r for r in refs if r and px and abs(px / r - 1) > 0.15]
        if px and bad and not q["suspect"]:
            q = dict(q, suspect=True, suspect_reason=f"px {px} vs reference(s) {sorted(round(r,3) for r in bad)} = >15% gap — phantom-tick guard v4")
            _CACHE[yf_sym] = q
        elif px and not q["suspect"]:
            hist_ref = next((r for r in refs if r and r != pc), None)
            _remember_close(yf_sym, hist_ref if hist_ref else px)
    except Exception:
        pass
    _CACHE[yf_sym] = q
    return q


_IB_FILE = ROOT / "desk" / "data" / "ib_live_quotes.json"


def _ib_file_quote(ticker: str, r: dict) -> dict | None:
    """Gateway-daemon quote (a separate process writes the file) — the TRUE live layer when fresh."""
    try:
        d = json.loads(_IB_FILE.read_text())
        q = d.get("quotes", {}).get(ticker)
        if not q:
            return None
        age = time.time() - q["asof"]
        if age > 90:
            return None
        return _mk_quote(ticker, q["px"], "ibkr-gateway", "live" if q.get("mdt") == 1 else "delayed",
                         q["asof"], exchange=r["exchange"], ccy=r["ccy"])
    except Exception:
        return None


def get_price(ticker: str) -> dict:
    r = resolve(ticker)
    ib_q = _ib_file_quote(ticker, r)
    if ib_q and not ib_q["suspect"]:
        # yfinance becomes the divergence cross-check — a genuine second source
        y = quote_yf(r["yf"], ticker, r["exchange"], r["ccy"])
        d = _divergence(ib_q["px"], y["px"])
        if d:
            return dict(ib_q, suspect=True, suspect_reason=d + " (gateway vs yfinance)")
        return ib_q
    ext = _EXTERNAL.get(ticker)
    q = quote_yf(r["yf"], ticker, r["exchange"], r["ccy"])
    if ext and ext["age_s"] is not None and ext["age_s"] < _TTL:
        # IBKR-sourced quote takes precedence; cross-check vs yfinance for the divergence rail
        d = _divergence(ext["px"], q["px"])
        if d:
            ext = dict(ext, suspect=True, suspect_reason=d)
        return ext
    return q


def get_prices(tickers) -> dict:
    return {t: get_price(t) for t in tickers}
