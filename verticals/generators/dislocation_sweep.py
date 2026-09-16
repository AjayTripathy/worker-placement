"""dislocation_sweep — year-round value-dislocation watch over the KNOWN universe (built 2026-07-28).

THE GAP IT FILLS: december_dislocation only runs Oct-Dec (other people's tax-loss selling);
band_watch only fires on ledger names with explicit alert bands; the smallcap watch covers the
8 verified basket names. Nothing watched the WHOLE researched universe for fresh idiosyncratic
drops. This does: every name we have a verdict, a shortlist entry, or a position on, checked
every weekday for a sharp fall the MARKET didn't share.

SIGNAL = idiosyncratic drawdown, not raw drawdown: excess return vs SPY over 5 and 21 sessions.
A name falling with the tape is beta, not a dislocation (the Cosmecca lesson: beta-bleed staged
on triage, court reversed it). Thresholds:
    DISLOC:  excess_5d <= -8%  or excess_21d <= -15%   (HIGH at <= -12% / <= -20%)
    held names fire earlier (excess_5d <= -6%) — a held name dislocating is a re-underwrite.

DOCTRINE GUARDS (printed on every fire, enforced downstream):
  - PROPOSES ONLY. The pipeline is: cause-check (what actually happened?) -> discovery_state
    (is it crowded/degraded?) -> independent court (v1.4) -> thesis doc -> THEN staging.
    "No cause found" after a shallow look is NOT a mispricing — find the cause or stand down.
  - Names on our own harvested list (wash-sale window) are tagged DO-NOT-BUY-31D.
  - New fires only: a name alerts when it ENTERS dislocation, then stays quiet ~10 sessions
    unless it deepens a tier (MED->HIGH).

Emits DETFIRE|dislocation|<ticker>|<SEV>|<evidence> lines (the detector_scan extractor routes
them into the desk feed with needs_verification=True). Writes data/DISLOCATION_SWEEP.json +
data/dislocation_state.json. READ-ONLY; proposes, never sizes.

  python3 verticals/generators/dislocation_sweep.py [--min-excess5 -8] [--quiet-sessions 10]
"""
from __future__ import annotations
import json, re, sys, argparse, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:                 # so the shared price-fallback ladder is importable
    sys.path.insert(0, str(ROOT))
DATA = HERE / "data"
OUT_JSON = DATA / "DISLOCATION_SWEEP.json"
STATE = DATA / "dislocation_state.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
POSCACHE = ROOT / "desk" / "ui" / "data" / "positions_cache.json"
HARVESTED = ROOT / "desk" / "data" / "harvested_2026.json"
SHORTLISTS = [ROOT / "verticals" / "deep_value" / "data" / f for f in
              ("shortlist.json", "quality_shortlist.json", "financials_shortlist.json")]

# verdict first-words that mean "we decided NOT to own this" — their dislocations are not our business
DEAD_VERDICTS = ("AVOID", "PASS", "DECLINE", "KILL", "SELL", "EXIT", "SOLD", "REJECT", "TRAP")


def _yf_symbol(tk: str) -> str | None:
    """Map a ledger/desk ticker to a yfinance symbol; None = not price-screenable here."""
    if not tk or not re.fullmatch(r"[A-Za-z0-9.\-]{1,12}", tk):
        return None
    if tk.endswith(("-STK", "-OPS", "-RXN")) or tk.upper() != tk and "." not in tk:
        return None
    if re.fullmatch(r"\d{4}", tk):
        return tk + ".T"          # bare TSE code
    if re.fullmatch(r"\d{6}", tk):
        return tk + ".KS"         # bare KRX code
    if re.fullmatch(r"\d+", tk):
        return None
    return tk


def build_universe() -> dict[str, dict]:
    """ticker -> {source, held, verdict} across ledger + shortlists + held book."""
    uni: dict[str, dict] = {}
    try:
        for r in json.loads(LEDGER.read_text()).get("names", []):
            tk, v = r.get("ticker"), str(r.get("verdict") or "").strip().upper()
            if not tk or any(v.startswith(d) for d in DEAD_VERDICTS):
                continue
            uni[tk] = {"source": "ledger", "held": False, "verdict": (v.split(" ")[0][:24] or "UNJUDGED")}
    except Exception:
        pass
    for f in SHORTLISTS:
        try:
            data = json.loads(f.read_text())
            rows = data if isinstance(data, list) else data.get("names") or data.get("rows") or []
            for r in rows:
                tk = r.get("ticker") if isinstance(r, dict) else (r if isinstance(r, str) else None)
                if tk and tk not in uni:
                    uni[tk] = {"source": f.stem, "held": False, "verdict": "SCREEN"}
        except Exception:
            continue
    try:
        pos = json.loads(POSCACHE.read_text()).get("positions", {})
        held = pos.keys() if isinstance(pos, dict) else [p.get("symbol") for p in pos]
        for tk in held:
            if not tk:
                continue
            uni.setdefault(tk, {"source": "book", "verdict": "HELD"})
            uni[tk]["held"] = True
    except Exception:
        pass
    # LEDGER-ROT GUARD (the SLS lesson, 2026-07-28): a ledger verdict of HELD for a name the
    # blotter does NOT hold is stale — eleven days after the SLS covered-call assignment the
    # ledger still said HELD and a summary repeated it. Mark it so the fire line says so.
    for tk, meta in uni.items():
        if meta["verdict"].startswith("HELD") and not meta["held"]:
            meta["verdict"] = "HELD?-STALE(not-on-blotter)"
    return uni


def sweep(min_excess5: float, quiet_sessions: int) -> list[dict]:
    import yfinance as yf
    uni = build_universe()
    symmap = {tk: s for tk in uni if (s := _yf_symbol(tk))}
    symbols = sorted(set(symmap.values()) | {"SPY"})
    px = yf.download(symbols, period="3mo", progress=False, auto_adjust=True)["Close"]

    def series(sym):
        try:
            s = (px[sym] if sym in px.columns else px).dropna()
            return s if len(s) >= 22 else None
        except Exception:
            return None

    spy = series("SPY")
    if spy is None:
        print("SWEEP ABORT: no SPY reference series")
        return []

    # FALLBACK LADDER + DEGRADED-LOUD (2026-08-11). Names yfinance refused used to scroll past as
    # download noise and were then counted as "not priced" — indistinguishable from "no dislocation".
    # Ladder: (1) alternate suffix forms, (2) the local IBKR gateway as a LIVENESS check (it has no
    # history, so it can only tell us the line is alive and Yahoo dropped it = INFRA failure, loud).
    try:
        from verticals.generators.intl_dislocation_sweep import alt_symbols, gw_probe
    except Exception as e:                                   # ladder unavailable = say so, don't die
        print(f"[dislocation_sweep] fallback ladder unavailable ({type(e).__name__}) — "
              f"unpriced names will be reported without a retry")
        alt_symbols, gw_probe = (lambda s: []), (lambda s, **k: ({}, "NOT RUN (ladder unavailable)"))
    sermap = {tk: s for tk, sym in symmap.items() if (s := series(sym)) is not None}
    missing = [tk for tk in symmap if tk not in sermap]
    if missing:
        alt_map = {a: tk for tk in missing for a in alt_symbols(symmap[tk])}
        if alt_map:
            try:
                px2 = yf.download(sorted(alt_map), period="3mo", progress=False,
                                  auto_adjust=True)["Close"]
                for a, tk in alt_map.items():
                    if tk in sermap:
                        continue
                    try:
                        s2 = (px2[a] if a in px2.columns else px2).dropna()
                    except Exception:
                        continue
                    if len(s2) >= 22:
                        sermap[tk] = s2
                        print(f"[dislocation_sweep] symbol-fix: {tk} priced as {a}")
            except Exception as e:
                print(f"[dislocation_sweep] alt-symbol retry failed: {type(e).__name__}")
    unpriced = [tk for tk in symmap if tk not in sermap]
    gw_alive, gw_status = (gw_probe(unpriced, default_venue=("SMART", "USD")) if unpriced
                           else ({}, "not attempted"))
    spy5 = float(spy.iloc[-1] / spy.iloc[-6] - 1) * 100
    spy21 = float(spy.iloc[-1] / spy.iloc[-22] - 1) * 100

    try:
        harvested = {h.get("ticker") for h in json.loads(HARVESTED.read_text()) if isinstance(h, dict)}
    except Exception:
        harvested = set()
    state = {}
    try:
        state = json.loads(STATE.read_text())
    except Exception:
        pass

    today = datetime.date.today().isoformat()
    hits, scanned = [], 0
    for tk, meta in sorted(uni.items()):
        s = sermap.get(tk)
        if s is None:
            continue
        scanned += 1
        last = float(s.iloc[-1])
        r5 = (last / float(s.iloc[-6]) - 1) * 100
        r21 = (last / float(s.iloc[-22]) - 1) * 100
        ex5, ex21 = r5 - spy5, r21 - spy21
        if r21 > 15:                                            # pullback after a moonshot is not cheapness
            continue
        floor5 = min_excess5 + (2 if meta["held"] else 0)      # held names fire 2pp earlier
        sev = None
        if ex5 <= -12 or ex21 <= -20:
            sev = "HIGH"
        elif ex5 <= floor5 or ex21 <= -15:
            sev = "MED"
        prior = state.get(tk, {})
        if sev is None:
            if prior:
                state.pop(tk, None)                             # recovered — re-arm
            continue
        # suppress repeats unless the tier deepened
        if prior and prior.get("sev") == sev:
            try:
                age = (datetime.date.fromisoformat(today) -
                       datetime.date.fromisoformat(prior.get("fired", today))).days
                if age < quiet_sessions * 1.5:                  # calendar-day approximation
                    continue
            except Exception:
                pass
        state[tk] = {"sev": sev, "fired": today, "ex5": round(ex5, 1), "ex21": round(ex21, 1)}
        wash = " DO-NOT-BUY-31D(wash-sale: our own harvest)" if tk in harvested else ""
        held = " HELD->re-underwrite" if meta["held"] else ""
        hit = {"ticker": tk, "severity": sev, "px": round(last, 2),
               "r5_pct": round(r5, 1), "r21_pct": round(r21, 1),
               "excess5_pct": round(ex5, 1), "excess21_pct": round(ex21, 1),
               "source": meta["source"], "verdict": meta["verdict"], "held": meta["held"],
               "wash_sale_blocked": tk in harvested, "fired": today}
        hits.append(hit)
        print(f"DETFIRE|dislocation|{tk}|{sev}|{meta['verdict']} ({meta['source']}) fell "
              f"{r5:+.1f}%/5d {r21:+.1f}%/21d = {ex5:+.1f}/{ex21:+.1f}pp vs SPY @ {last:.2f}{held}{wash}"
              f" — PROPOSES ONLY: cause-check -> discovery_state -> court (v1.4) before any staging;"
              f" a shallow 'no cause found' is beta, not a dislocation")

    STATE.write_text(json.dumps(state, indent=1))
    no_symbol = sorted(set(uni) - set(symmap))
    OUT_JSON.write_text(json.dumps({"asof": today, "spy5_pct": round(spy5, 1), "spy21_pct": round(spy21, 1),
                                    "universe": len(uni), "priced": scanned, "hits": hits,
                                    "unpriced_names": sorted(unpriced),
                                    "gw_alive_no_history": sorted(gw_alive),
                                    "not_price_screenable": no_symbol}, indent=1))
    print(f"[dislocation_sweep] {today}: universe {len(uni)} ({scanned} priced) · SPY {spy5:+.1f}%/5d "
          f"{spy21:+.1f}%/21d · {len(hits)} new/deepened dislocations")
    if unpriced:
        gw = ((f" | {len(gw_alive)} QUOTE LIVE at the IBKR gateway = a Yahoo history gap "
               f"(INFRA failure, not an observation): {', '.join(sorted(gw_alive))}") if gw_alive
              else f" | gateway liveness probe: {gw_status} — 0 alive")
        print(f"DEGRADED-LOUD: {scanned} of {len(symmap)} priced; {len(unpriced)} DEGRADED "
              f"— {', '.join(sorted(unpriced))}{gw}")
    if no_symbol:
        print(f"NOT PRICE-SCREENABLE ({len(no_symbol)}, no yfinance symbol mapping): "
              f"{', '.join(no_symbol)}")
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-excess5", type=float, default=-8.0)
    ap.add_argument("--quiet-sessions", type=int, default=10)
    a = ap.parse_args()
    sweep(a.min_excess5, a.quiet_sessions)
