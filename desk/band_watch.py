"""Band watch — makes every ledger alert_below band ACTUALLY fire.

Reads research_ledger.json, takes every name with an alert_below whose entry is
NOT already covered by a resting order (a GTC ladder IS the trigger for those),
pulls a live/last price, and notifies (macOS + ntfy push + Gmail) when price is
at or through the band. READ-ONLY: it alerts, the user decides, the desk stages.

Re-arm logic: one alert per crossing. A name re-arms after price closes >5%
back above its band, so a hoverer doesn't spam every run. State in
desk/data/band_watch_state.json.

Runs from the gauntlet sentinel (launchd 6:15 + 7:45 weekdays) and by hand:
    python3 -m desk.band_watch [--dry]
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
STATE = ROOT / "desk" / "data" / "band_watch_state.json"

# ledger ticker -> yfinance symbol, where they differ
YF_MAP = {
    "PEO.WA": "PEO.WA", "MC.PA": "MC.PA", "8750.T": "8750.T",
    "003550.KS": "003550.KS", "005387.KS": "005387.KS",
    "HSBK.L": "HSBK.L", "TBCG.L": "TBCG.L", "BRBY.L": "BRBY.L",
    "MHPC.L": "MHPC.IL", "AST.WAR": "AST.WA", "WIE.VIE": "WIE.VI",
    "SAP.DE": "SAP", "POLI.TA": "POLI.TA", "AMV0.DE": "AMV0.DE",
    "UKRAIN-StepUp-B": None,  # bond, no yf line — pack-governed
    "IVN": "IVN.TO", "FM": "FM.TO", "NBG.AT": "ETE.AT", "EMAAR": "EMAAR.AE",
    "EMAARDEV": "EMAARDEV.AE", "CBKD": "CBKD.IL", "GALD": "GALD.SW",
    "CRDA": "CRDA.L",
}

# names whose bands are already expressed as resting GTC orders (the order IS
# the trigger); refreshed manually when the order book changes materially
ORDER_COVERED_STATIC = {
    # FALLBACK ONLY (2026-08-25 hardening): coverage is now derived LIVE from the blotter each
    # run — a name is order-covered iff a BUY order actually rests right now. This static set is
    # used only when the gateway is unreachable, because a hand-maintained list rots: on 08-25,
    # 12 of its 15 names had zero live buys and ONON sat THROUGH its band unwatched.
    "PEO.WA", "FSBW", "VRLA.PA",
}

# gateway localSymbol -> ledger ticker, where suffix heuristics don't cover it
_LOCAL_TO_LEDGER = {
    "PEO": "PEO.WA", "VRLA": "VRLA.PA", "SFPI": "SFPI.PA", "ETL": "ETL.PA",
    "KALMAR": "KALMAR.HE", "STERV": "STERV.HE", "SAP": "SAP.DE",
}


def _order_covered() -> set:
    """Names with a live BUY order resting NOW (the order IS the band trigger)."""
    try:
        from desk.order_executor import IBKROrderExecutor
        ex = IBKROrderExecutor(client_id=94)
        ex.connect(timeout=8)
        # non-zero clientId sees only its OWN orders unless all are requested explicitly
        ex._ib.reqAllOpenOrders()
        ex._ib.sleep(1.5)
        orders = ex.get_open_orders()
        ex.disconnect()
        covered = set()
        for o in orders:
            if o.get("action") != "BUY":
                continue
            sym = o.get("localSymbol") or o.get("symbol") or ""
            cur = o.get("currency", "")
            t = _LOCAL_TO_LEDGER.get(sym)
            if t is None:
                t = sym + ".T" if cur == "JPY" else sym + ".L" if cur == "GBP" else sym
            covered.add(t)
        print(f"[band_watch] order-coverage LIVE from blotter: {len(covered)} names")
        return covered
    except Exception as e:
        print(f"[band_watch] blotter unreachable ({e}) — STATIC fallback "
              f"({len(ORDER_COVERED_STATIC)} names); coverage may be stale")
        return set(ORDER_COVERED_STATIC)


_LEDGER_YF: dict = {}
_COVERED: set = set()   # ticker -> ledger 'yf' symbol (the row owns its own quote line;
                        # 034730 went dark 2026-07 because only the hardcoded map was consulted)


def _bands() -> list[tuple[str, float, str]]:
    """(ticker, level, side) — side 'below' = buy-zone touch, 'above' = SELL-ZONE touch."""
    global _COVERED
    _COVERED = _order_covered()
    led = json.load(open(LEDGER))
    out = []
    for n in led["names"]:
        t = n["ticker"]
        if n.get("yf") and n["yf"] != t:
            _LEDGER_YF[t] = n["yf"]
        if YF_MAP.get(t, t) is None:
            continue
        ab = n.get("alert_below")
        if ab and t not in _COVERED:
            out.append((t, float(ab), "below"))
        aa = n.get("alert_above")
        if aa:  # sell-zone alerts fire even for order-covered names — exits are never order-covered
            out.append((t, float(aa), "above"))
    return out


def _prices(tickers: list[str]) -> dict[str, dict]:
    """Per ticker: last close + TODAY's intraday low/high. TOUCH SEMANTICS FIX
    (BELFA 2026-09-03: intraday 194.40 pierced a 195 band while the close, 201.65,
    never did — close-only reads structurally miss every intraday touch)."""
    import yfinance as yf
    px = {}
    for t in tickers:
        sym = YF_MAP.get(t) or _LEDGER_YF.get(t) or t
        try:
            h = yf.Ticker(sym).history(period="5d")
            if len(h):
                px[t] = {"close": float(h["Close"].iloc[-1]),
                         "low": float(h["Low"].iloc[-1]),
                         "high": float(h["High"].iloc[-1])}
        except Exception:
            pass
    return px


def _queue_armed_envelopes(fired: list[str]):
    """Band touch on a COURT-ARMED name -> append its pre-committed order spec to the
    envelope queue. Cron cannot reach the claude.ai IBKR connector, so the queue is swept
    by the next LIVE session (cold-start protocol), which creates the AI instruction; the
    user's click in the panel remains the execution gate (autonomy rung 0 unchanged).
    Only armed_envelopes.json names participate — v1.4 forbids auto-envelopes elsewhere."""
    armed_p = ROOT / "desk" / "data" / "armed_envelopes.json"
    queue_p = ROOT / "desk" / "data" / "envelope_queue.jsonl"
    if not armed_p.exists():
        return
    import datetime
    armed = json.load(open(armed_p))
    for f in fired:
        t = f.split()[2] if f.startswith("SELL") else f.split()[0]
        spec = armed.get(t)
        if not isinstance(spec, dict):
            continue
        row = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "ticker": t,
               "fire_line": f, "spec": spec, "status": "QUEUED_AWAITING_SESSION_SWEEP"}
        with open(queue_p, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"[band_watch] ENVELOPE QUEUED: {t} {spec.get('side')} {spec.get('qty')}@{spec.get('limit')}")


def _email_clear(fired: list[str]):
    """A CLEAR entry-band email (user directive 2026-07-29, post the KER.PA miss):
    subject names the tickers; body carries each name's ledger verdict + entry note +
    dossier link, so the email IS the decision brief, not a breadcrumb. Same
    ~/.signalos_smtp app-password rail as the sentinel; silently inactive without it."""
    try:
        from desk.mailer import send
        led = {n["ticker"]: n for n in json.load(open(LEDGER))["names"]}
        tickers = list(dict.fromkeys(f.split()[2] if f.startswith("SELL") else f.split()[0] for f in fired))
        armed_p = ROOT / "desk" / "data" / "armed_envelopes.json"
        armed = json.load(open(armed_p)) if armed_p.exists() else {}
        sections = []
        for f in fired:
            t = f.split()[2] if f.startswith("SELL") else f.split()[0]
            n = led.get(t, {})
            body = [f]
            if isinstance(armed.get(t), dict):
                s = armed[t]
                body.append(f"An order envelope is queued: {s.get('side')} {s.get('qty')} @ {s.get('limit')} — "
                            f"it will be staged as an IBKR instruction at the next session sweep; your click executes it.")
            v = (n.get("conviction") or n.get("verdict") or "")[:400]
            e = (n.get("entry") or "")[:200]
            g = (n.get("gate_basis") or "")[:400]
            if g:
                body.append(f"WHAT THIS TOUCH MEANS: {g}")
            if not isinstance(armed.get(t), dict):
                body.append("NEXT: WATCH-band touch — the desk owes a cause-check and a dated disposition "
                            "within 48h (court / re-point the band / explicit pass). Undispositioned fires "
                            "flag in consistency_check. Nothing is staged by this email.")
            if v:
                body.append(f"The record: {v}")
            if e:
                body.append(f"Entry plan: {e}")
            body.append(f"Full dossier: http://127.0.0.1:8765/ticker/{t}")
            sections.append((f"{t} — band touched", body))
        send(f"ENTRY BAND HIT: {', '.join(tickers)}", sections,
             footer=("Before acting: a fired gate fills or gets a missed-entry row the same day — "
                     "moving the band after a fire is gate-moving (the Kering lesson)."))
    except Exception as ex:
        print(f"[band_watch] clear-email failed: {ex}")


def main(dry: bool = False) -> list[str]:
    state = json.load(open(STATE)) if STATE.exists() else {}
    bands = _bands()
    px = _prices([t for t, _, _ in bands])
    fired = []
    for t, band, side in bands:
        d = px.get(t)
        if d is None:
            continue
        if isinstance(d, float):                       # defensive: old-format state/callers
            d = {"close": d, "low": d, "high": d}
        p = d["close"]
        key = t if side == "below" else f"{t}|above"
        st = state.get(key, {"armed": True})
        if side == "below":
            # TOUCH semantics: fire on the intraday LOW piercing the band (BELFA fix);
            # re-arm still keyed off the close so a wick doesn't immediately re-arm.
            if d["low"] <= band and st.get("armed", True):
                tag = "intraday touch" if p > band else "touch"
                fired.append(f"{t} low {d['low']:,.2f} <= band {band:,.2f} (last {p:,.2f}, {tag}) — WATCH band touched; review the record before staging")
                state[key] = {"armed": False, "fired_at": d["low"], "fired_date": _dt.date.today().isoformat()}
            elif p > band * 1.05 and not st.get("armed", True):
                state[key] = {"armed": True}  # re-arm after a 5% bounce clear
        else:
            if d["high"] >= band and st.get("armed", True):
                fired.append(f"SELL ZONE: {t} high {d['high']:,.2f} >= {band:,.2f} (last {p:,.2f}) — the exit plan says SELL INTO THIS; review the record and stage the exit")
                state[key] = {"armed": False, "fired_at": d["high"], "fired_date": _dt.date.today().isoformat()}
            elif p < band * 0.95 and not st.get("armed", True):
                state[key] = {"armed": True}
    if not dry:
        json.dump(state, open(STATE, "w"), indent=1)
        if fired:
            from desk.gauntlet_sentinel import _notify
            _notify("BAND WATCH: " + " | ".join(fired)[:900])   # short push (macOS + ntfy)
            _queue_armed_envelopes(fired)                        # court-armed names -> staging queue (2026-07-29)
            # COURT-ON-TOUCH AUTO-ENQUEUE (principal 2026-09-04: "did those get automatically
            # queued?" - they didn't; now they do). A below-band fire on a ledger name enqueues
            # a band-touch court row so the conveyor picks it up without a session sweep.
            # Envelope names excluded (they stage, not court); SELL-ZONE fires excluded.
            try:
                from desk.court_queue import enqueue_candidates
                rows = []
                for f in fired:
                    if f.startswith("SELL ZONE"):
                        continue
                    t = f.split()[0]
                    rows.append({"ticker": t, "context": f"band-touch court-on-touch: {f}. "
                                 f"Review the ledger gate_basis FIRST - conditional gates "
                                 f"(disclosure-dependent adds) court the CONDITION, not a fresh thesis."})
                if rows:
                    c = enqueue_candidates(rows, source=f"band_touch/{_dt.date.today().isoformat()}",
                                           allow_ledger=True)
                    print(f"[band_watch] court-on-touch enqueued: {c['added']}")
            except Exception as e:
                print(f"[band_watch] auto-enqueue failed (fires still notified): {e}")
            _email_clear(fired)                                  # the CLEAR email (2026-07-29)
    for line in fired:
        print("[band_watch] FIRE:", line)
    if not fired:
        print(f"[band_watch] {len(px)}/{len(bands)} bands priced, none touched")
    return fired


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
