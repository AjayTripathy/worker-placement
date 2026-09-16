"""implied_binary — options-implied P(up) anchors for stock-reaction calls (built 2026-07-27).

Born from the Brier-book decomposition: our operating calls score ~0.02-0.09 (connector-fed,
real skill) while stock-reaction calls score 0.45-0.56 (frozen naked — no implied move, no
positioning input) AND the market-beating sizing gate is starved at n~6 because most ledger
market_p's are DERIVED from our own FVs (consistency gauges, not anchors). This module fixes
both with one number: the risk-neutral probability the stock is above its anchor at the
reaction window's end, read off the listed option chain.

  P(S_T > K) = -dC/dK at K = anchor  (undiscounted digital; fine for <=6-week windows)

estimated by central finite difference on call mids around the anchor strike, with a
Black-Scholes N(d2) fallback (ATM IV) when the chain is too sparse for a clean difference.

Provenance discipline: every stamp writes market_p_source ("options_implied:<venue> <asof>")
so the calibration gate can separate GENUINE external anchors from derived ones. Stamps only
OPEN reaction-class records whose market_p is None — a frozen our_p is never touched, and an
existing anchor is never overwritten (freeze-discipline: the crowd annotation is an add-only
field, like freeze_call's venue check).

Chain source: yfinance (delayed, adequate for a probability estimate; tagged honestly).
IBKR chain via ib_insync is the intended upgrade once the gateway's reqExecutions handshake
wedge (2026-07-06, still live 2026-07-27) makes new API sessions reliable — the source tag
makes the two regimes distinguishable in the ledger forever.

CLI:
  python3 -m desk.implied_binary TICKER [--anchor PX] [--window-end YYYY-MM-DD]   # print only
  python3 -m desk.implied_binary TICKER --stamp CAT_DATE                          # stamp one record
  python3 -m desk.implied_binary --stamp-open                                     # sweep all stampable
READ-ONLY on the market; never places orders.
"""
from __future__ import annotations
import json, math, datetime, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "calibration_ledger.jsonl"

# reaction-class detection must survive the event-enum drift (stock_reaction vs
# earnings_stock_reaction, plus -STK/-RXN ticker suffixes on records with kind=catalyst)
REACTION_TYPES = {"stock_reaction", "earnings_stock_reaction"}
REACTION_SUFFIXES = ("-STK", "-RXN")

# ledger tickers that are not US-listed optionable lines — no chain to read
NON_US_HINTS = (".KS", ".KQ", ".T", ".DE", ".PA", ".MI", ".L", ".WA", ".TA", ".HE", ".WAR")


def is_reaction(rec: dict) -> bool:
    t = str(rec.get("ticker") or "")
    return (rec.get("event_type") in REACTION_TYPES) or t.endswith(REACTION_SUFFIXES)


def underlying_of(ticker: str) -> str:
    for suf in REACTION_SUFFIXES:
        if ticker.endswith(suf):
            return ticker[: -len(suf)]
    return ticker


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def implied_up_prob(ticker: str, window_end: str, anchor: float | None = None) -> dict | None:
    """Risk-neutral P(underlying > anchor at ~window_end) from the listed chain.
    Returns {p, anchor, expiry, method, source} or None if no usable chain."""
    sym = underlying_of(ticker)
    if any(sym.endswith(h) for h in NON_US_HINTS):
        return None
    try:
        import yfinance as yf
        tk = yf.Ticker(sym)
        expiries = list(tk.options or [])
        if not expiries:
            return None
        we = datetime.date.fromisoformat(window_end[:10])
        # nearest expiry ON/AFTER the window end (the digital covers the whole window)
        after = [e for e in expiries if datetime.date.fromisoformat(e) >= we]
        expiry = after[0] if after else expiries[-1]
        if anchor is None:
            h = tk.history(period="5d")
            if h is None or h.empty:
                return None
            anchor = float(h["Close"].iloc[-1])
        chain = tk.option_chain(expiry)
        calls = chain.calls
        if calls is None or len(calls) < 3:
            return None
        calls = calls.dropna(subset=["strike"]).sort_values("strike")

        def mid(row):
            b, a = float(row.get("bid") or 0), float(row.get("ask") or 0)
            if b > 0 and a > 0:
                return (a + b) / 2
            lp = float(row.get("lastPrice") or 0)
            return lp if lp > 0 else None

        # central finite difference on call mids across the anchor
        lo = calls[calls["strike"] <= anchor].tail(1)
        hi = calls[calls["strike"] > anchor].head(1)
        if len(lo) and len(hi):
            c_lo, c_hi = mid(lo.iloc[0]), mid(hi.iloc[0])
            k_lo, k_hi = float(lo.iloc[0]["strike"]), float(hi.iloc[0]["strike"])
            if c_lo is not None and c_hi is not None and k_hi > k_lo and c_lo > c_hi:
                p = (c_lo - c_hi) / (k_hi - k_lo)
                if 0.0 < p < 1.0:
                    wide = " WIDE-STRIKES low-confidence" if (k_hi - k_lo) / anchor > 0.12 else ""
                    return {"p": round(max(0.02, min(0.98, p)), 3), "anchor": round(anchor, 2),
                            "expiry": expiry, "method": f"digital dC/dK strikes {k_lo}/{k_hi}{wide}",
                            "source": f"options_implied:yfinance {datetime.date.today().isoformat()}"}
        # fallback: N(d2) with the ATM IV
        calls["dist"] = (calls["strike"] - anchor).abs()
        atm = calls.nsmallest(1, "dist").iloc[0]
        iv = float(atm.get("impliedVolatility") or 0)
        if iv <= 0:
            return None
        t_yrs = max((datetime.date.fromisoformat(expiry) - datetime.date.today()).days, 1) / 365.0
        d2 = (math.log(anchor / anchor) + (-0.5 * iv * iv) * t_yrs) / (iv * math.sqrt(t_yrs))
        p = _norm_cdf(d2)  # ATM digital: N(d2) with S=K -> below 0.5 by the lognormal drift term
        return {"p": round(max(0.02, min(0.98, p)), 3), "anchor": round(anchor, 2),
                "expiry": expiry, "method": f"BS N(d2) fallback, ATM IV {iv:.2f}",
                "source": f"options_implied:yfinance {datetime.date.today().isoformat()}"}
    except Exception:
        return None


def reaction_context(ticker: str, anchor: float | None = None) -> dict | None:
    """The four numbers a reaction call must know before it deserves a conviction number
    (2026-07-27, from the HCA-STK/AMV0 lessons): the implied move, the run-up into the print
    (sell-the-news is mostly a function of what already ran), short interest, and where IV sits.
    Best-effort — fields the source can't supply come back None, never fabricated."""
    sym = underlying_of(ticker)
    if any(sym.endswith(h) for h in NON_US_HINTS):
        return None
    out = {"asof": datetime.date.today().isoformat(), "source": "yfinance best-effort"}
    try:
        import yfinance as yf
        tk = yf.Ticker(sym)
        h = tk.history(period="2mo")
        if h is not None and len(h) >= 21:
            c = h["Close"]
            px = float(c.iloc[-1])
            out["px"] = round(px, 2)
            out["run_up_5d_pct"] = round((px / float(c.iloc[-6]) - 1) * 100, 1)
            out["run_up_20d_pct"] = round((px / float(c.iloc[-21]) - 1) * 100, 1)
        # implied move: ATM straddle mid / spot, nearest expiry
        try:
            exps = list(tk.options or [])
            if exps and out.get("px"):
                ch = tk.option_chain(exps[0])
                for side, df in (("call", ch.calls), ("put", ch.puts)):
                    df = df.dropna(subset=["strike"])
                    df["dist"] = (df["strike"] - out["px"]).abs()
                    row = df.nsmallest(1, "dist").iloc[0]
                    b, a2 = float(row.get("bid") or 0), float(row.get("ask") or 0)
                    mid = (a2 + b) / 2 if (b > 0 and a2 > 0) else float(row.get("lastPrice") or 0)
                    out[f"atm_{side}_mid"] = round(mid, 2)
                if out.get("atm_call_mid") and out.get("atm_put_mid"):
                    out["implied_move_pct"] = round(100 * (out["atm_call_mid"] + out["atm_put_mid"]) / out["px"], 1)
                    out["implied_move_expiry"] = exps[0]
        except Exception:
            pass
        try:
            si = (tk.info or {}).get("shortPercentOfFloat")
            if si:
                out["short_pct_float"] = round(float(si) * 100, 1)
        except Exception:
            pass
        return out if len(out) > 2 else None
    except Exception:
        return None


def stamp(ticker: str, cat_date: str | None = None, quiet: bool = False) -> int:
    """Stamp market_p onto matching OPEN reaction records lacking one. Add-only; never
    overwrites an existing anchor, never touches our_p or non-OPEN records."""
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    n = 0
    for r in rows:
        if str(r.get("status") or "OPEN").upper() != "OPEN" or not is_reaction(r):
            continue
        if r.get("ticker") != ticker or (cat_date and str(r.get("cat_date"))[:10] != cat_date):
            continue
        if r.get("market_p") is not None:
            if not quiet:
                print(f"  {ticker} {r.get('cat_date')}: market_p already set ({r['market_p']}) — not overwritten")
            continue
        # window end ~ cat_date + 7 calendar days covers the 5-session reaction window
        we = (datetime.date.fromisoformat(str(r["cat_date"])[:10]) + datetime.timedelta(days=7)).isoformat()
        anchor = r.get("px_at_pred")
        res = implied_up_prob(ticker, we, float(anchor) if anchor else None)
        if not res:
            if not quiet:
                print(f"  {ticker} {r.get('cat_date')}: no usable chain — left unstamped")
            continue
        r["market_p"] = res["p"]
        r["market_p_source"] = f"{res['source']} | exp {res['expiry']} | {res['method']} | anchor {res['anchor']}"
        n += 1
        if not quiet:
            print(f"  STAMPED {ticker} {r.get('cat_date')}: market_p={res['p']} (our_p {r.get('our_p')}) "
                  f"[{res['method']}, exp {res['expiry']}]")
    if n:
        LEDGER.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return n


def stamp_open() -> int:
    """Sweep every OPEN reaction record missing market_p; stamp the US-optionable ones."""
    rows = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    targets = {(r["ticker"], str(r.get("cat_date"))[:10]) for r in rows
               if str(r.get("status") or "OPEN").upper() == "OPEN"
               and is_reaction(r) and r.get("market_p") is None}
    total = 0
    for t, d in sorted(targets):
        total += stamp(t, d)
    print(f"[implied_binary] stamped {total}/{len(targets)} stampable reaction records")
    return total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", nargs="?")
    ap.add_argument("--anchor", type=float, default=None)
    ap.add_argument("--window-end", default=None)
    ap.add_argument("--stamp", default=None, metavar="CAT_DATE")
    ap.add_argument("--stamp-open", action="store_true")
    a = ap.parse_args()
    if a.stamp_open:
        stamp_open()
    elif a.ticker and a.stamp:
        stamp(a.ticker, a.stamp)
    elif a.ticker:
        we = a.window_end or (datetime.date.today() + datetime.timedelta(days=7)).isoformat()
        r = implied_up_prob(a.ticker, we, a.anchor)
        print(json.dumps(r, indent=1) if r else f"no usable chain for {a.ticker}")
    else:
        ap.print_help()
