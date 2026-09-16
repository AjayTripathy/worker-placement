"""intraday_sentinel — the held-book's fast loop (alerts only, NEVER trades).

Born 2026-07-08 from the OLLI gap: a resting rung filled into a downgrade gap
at the open and the desk learned of it hours later from the user. The slow
watchers (6:15/7:45 + hourly) read closes; the book's risk events are intraday.

Every run (cron */15 during RTH + one premarket pass), from the quote daemon's
live file (ib_live_quotes.json — US names only; foreign lines stay on the slow
loop), against the ledger + resting orders:

  1. GAP/SHOCK: any held or resting-order name moving >4% vs prior close
     -> alert with the size of the move (the "your name is gapping" call).
  2. TRADED-THROUGH RUNG: live px at/below a resting GTC buy limit
     -> "your rung is filling INTO this move — decide whether later rungs stand"
     (the adverse-selection guard; fill inference only — the portal confirms).
  3. KILL PROXIMITY: any ledger kill/invalidation level within 2%
     -> prep alert (kill rules are CLOSE-based; this is the heads-up).
  4. Dedup via state; re-arm when the trigger clears by 1.5%.

    python3 -m desk.intraday_sentinel          # safe to run any time
READ-ONLY. Foreign-listed names and volume-decay metrics: v2 (needs bars).
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUOTES = ROOT / "desk" / "data" / "ib_live_quotes.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
ORDERS = ROOT / "desk" / "ui" / "data" / "orders_cache.json"
STATE = ROOT / "desk" / "data" / "intraday_sentinel_state.json"
PRIOR = ROOT / "desk" / "data" / "intraday_prior_closes.json"

GAP_PCT = 4.0
KILL_PROX_PCT = 2.0

# ledger kill/invalidation levels enforced on CLOSES; sentinel gives the intraday heads-up
KILL_LEVELS = {}  # MFP exited 2026-07-09; add live positions' close-based kill lines here


def _notify(msg: str):
    try:
        from desk.gauntlet_sentinel import _notify as n
        n(msg)
    except Exception:
        print(f"[intraday] NOTIFY: {msg}")


def _prior_closes(symbols):
    """Cache prior closes once per day (yfinance); quotes file carries live px only."""
    today = datetime.date.today().isoformat()
    cache = json.loads(PRIOR.read_text()) if PRIOR.exists() else {}
    if cache.get("date") != today:
        import yfinance as yf
        closes = {}
        for s in symbols:
            try:
                h = yf.Ticker(s).history(period="5d")["Close"]
                # prior close = last close STRICTLY before today
                idx = [d.date().isoformat() for d in h.index]
                for d, v in list(zip(idx, h))[::-1]:
                    if d < today:
                        closes[s] = float(v)
                        break
            except Exception:
                pass
        cache = {"date": today, "closes": closes}
        PRIOR.write_text(json.dumps(cache, indent=1))
    return cache.get("closes", {})


def main():
    try:                       # EDGAR all-forms fast poll for windowed kill-facts (red-team remediation 2026-07-28)
        from desk.filing_watch import main as _filings
        _filings()
    except Exception as e:
        print(f"[filing_watch] skipped: {e}")

    if not QUOTES.exists():
        print("[intraday] no live quotes file (daemon down?)")
        return
    q = json.loads(QUOTES.read_text())
    age_min = (datetime.datetime.now().timestamp() - q.get("asof", 0)) / 60
    if age_min > 30:
        print(f"[intraday] quotes stale ({age_min:.0f}m) — market closed or daemon down; exiting")
        return
    px = {k.split()[0]: v.get("px") for k, v in q.get("quotes", {}).items() if isinstance(v, dict) and v.get("px")}

    led = {n["ticker"]: n for n in json.loads(LEDGER.read_text())["names"]}
    held = {t for t, n in led.items() if (n.get("verdict") or n.get("state", "")).upper() in ("HELD", "STARTER")}
    resting = {}
    try:
        for o in json.loads(ORDERS.read_text()).get("orders", []):
            s = o["symbol"].split(".")[0].split()[0]
            if o.get("limit"):
                resting.setdefault(s, []).append(float(o["limit"]))
    except Exception:
        pass

    watch = (held | set(resting) | set(KILL_LEVELS)) & set(px)
    prior = _prior_closes(sorted(watch))
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    fired = []

    for s in sorted(watch):
        p = px[s]
        pc = prior.get(s)
        # 1) gap/shock
        if pc:
            chg = (p / pc - 1) * 100
            key = f"{s}|gap"
            if abs(chg) >= GAP_PCT and state.get(key) != "fired":
                fired.append(f"{s} is moving {chg:+.1f}% intraday ({pc:.2f} -> {p:.2f})"
                             + (" — YOU HAVE RESTING BUY RUNGS on this name; decide if they should stand" if s in resting else ""))
                state[key] = "fired"
            elif abs(chg) < GAP_PCT - 1.5:
                state[key] = "armed"
        # 2) traded-through rung
        for lim in resting.get(s, []):
            key = f"{s}|rung|{lim}"
            if p <= lim * 1.001 and state.get(key) != "fired":
                fired.append(f"{s} live {p:.2f} is AT/THROUGH your resting buy limit {lim:.2f} — "
                             f"the rung is likely FILLING into this move; check the portal and decide whether lower rungs stand")
                state[key] = "fired"
            elif p > lim * 1.015:
                state[key] = "armed"
        # 3) kill proximity
        k = KILL_LEVELS.get(s)
        if k:
            key = f"{s}|kill"
            if p <= k * (1 + KILL_PROX_PCT / 100) and state.get(key) != "fired":
                fired.append(f"{s} live {p:.2f} is within {KILL_PROX_PCT}% of the KILL line {k:.2f} — "
                             f"the rule fires on a CLOSE below; be ready")
                state[key] = "fired"
            elif p > k * 1.04:
                state[key] = "armed"

    # 4) EVENT WINDOWS — court-registered intraday triggers (the MFP lesson v2:
    #    slow-clock signals, fast-clock execution; the court writes the trigger,
    #    the machine measures it instead of the desk eyeballing the tape).
    EVENTS = ROOT / "desk" / "data" / "event_windows.json"
    if EVENTS.exists():
        today = datetime.date.today().isoformat()
        for ev in json.loads(EVENTS.read_text()).get("windows", []):
            if not (ev["start"] <= today <= ev["end"]):
                continue
            s = ev["symbol"]
            key = f"{s}|event|{ev['name']}"
            try:
                import yfinance as yf
                bars = yf.Ticker(s).history(period="6d")
                vols = bars["Volume"]
                px_now = px.get(s) or float(bars["Close"].iloc[-1])
                cum_turnover = float(vols[-ev.get("days", 5):].sum()) / ev["float_shares"]
                vol_today, vol_peak = float(vols.iloc[-1]), float(vols[-ev.get("days", 5):].max())
                decay = vol_today < ev.get("decay_frac", 0.5) * vol_peak
                exhausted = cum_turnover >= ev.get("turnover_min", 0.4)
                if decay and exhausted and state.get(key) != "fired":
                    fired.append(f"EVENT {ev['name']}: {s} @ {px_now:.2f} — the court's trigger just went TRUE "
                                 f"(cumulative turnover {cum_turnover:.0%} of float, today's volume {vol_today/vol_peak:.0%} of the peak = decay). "
                                 f"Per the pre-registration: {ev.get('action', 'review the record')}")
                    state[key] = "fired"
            except Exception as e:
                print(f"[intraday] event {ev['name']} check failed: {e}")

    STATE.write_text(json.dumps(state, indent=1))
    if fired:
        _notify("INTRADAY: " + " | ".join(fired)[:900])
    print(f"[intraday] {len(watch)} names checked, {len(fired)} alerts" + (f": {fired}" if fired else ""))


if __name__ == "__main__":
    main()
