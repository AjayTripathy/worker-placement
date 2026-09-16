"""catalyst_calendar_guard — the mechanical version of the KER postmortem's root cause 3.

The KER miss: our frozen record said "the 7/29 print pre-determines this binary" while the
calendar carried only Oct-21 — the decisive EARLIER print lived in prose and nothing listened.
This guard makes that impossible to repeat silently: for every OPEN forward-dated call in the
calibration ledger, resolve the ticker's ACTUAL next earnings date and flag any print that
lands more than GRACE_DAYS before the call's cat_date ("X prints on D1, N days before its D2
trigger — arm a pack for the earlier print").

Design notes:
  - Working set = OPEN calls with today < cat_date <= today+HORIZON_DAYS (the actionable window).
  - Earnings dates via yfinance in a thread pool with a hard per-ticker timeout (the first
    build attempt stalled on serial unbounded polling); failures = DATA MISSING, never silence.
  - Dates CACHED in state for CACHE_DAYS so the weekly cadence stays cheap.
  - One flag per (ticker, earlier-date); re-arms when the earlier date passes.

Runs on the weekly registry heartbeat and by hand: python3 -m desk.catalyst_calendar_guard
"""
from __future__ import annotations

import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
RESEARCH = ROOT / "desk" / "data" / "research_ledger.json"
STATE = ROOT / "desk" / "data" / "calendar_guard_state.json"

GRACE_DAYS = 3          # a print this close to the trigger is the same event window
HORIZON_DAYS = 180      # only guard calls inside the actionable horizon
CACHE_DAYS = 7          # earnings-date cache lifetime
PER_TICKER_TIMEOUT = 15  # seconds — the stall guard
MAX_WORKERS = 8


def _open_calls(today: str, horizon: str) -> list[dict]:
    out = []
    for line in LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if (r.get("status") or "OPEN").upper() != "OPEN":
            continue
        cd = r.get("cat_date") or ""
        if today < cd <= horizon:
            out.append(r)
    return out


def _yf_symbol(ticker: str) -> str | None:
    """Base ticker -> quote symbol. Suffixed call keys (HCA-OPS, IVN-MRE) collapse to the base."""
    base = ticker.split("|")[0]
    for sep in ("-OPS", "-STK", "-RXN", "-MRE", "-VOL"):
        if base.endswith(sep):
            base = base[: -len(sep)]
    try:
        from desk.band_watch import YF_MAP
        if base in YF_MAP:
            return YF_MAP[base]          # may be None (bonds etc.) = un-guardable
    except Exception:
        pass
    try:
        for n in json.loads(RESEARCH.read_text())["names"]:
            if n["ticker"] == base:
                return n.get("yf") or base
    except Exception:
        pass
    return base


def _next_earnings(sym: str) -> str | None:
    """Next earnings date (ISO) after today, or None. Runs inside the timeout pool."""
    import yfinance as yf
    t = yf.Ticker(sym)
    today = datetime.date.today()
    try:
        ed = t.get_earnings_dates(limit=8)
        if ed is not None and len(ed):
            future = [d.date() for d in ed.index if d.date() > today]
            if future:
                return min(future).isoformat()
    except Exception:
        pass
    try:
        cal = t.calendar
        dates = (cal or {}).get("Earnings Date") or []
        future = [d for d in dates if isinstance(d, datetime.date) and d > today]
        if future:
            return min(future).isoformat()
    except Exception:
        pass
    return None


def main(dry: bool = False) -> list[str]:
    today = datetime.date.today()
    horizon = (today + datetime.timedelta(days=HORIZON_DAYS)).isoformat()
    calls = _open_calls(today.isoformat(), horizon)
    state = json.loads(STATE.read_text()) if STATE.exists() else {"earnings_cache": {}, "flagged": {}}
    cache = state.setdefault("earnings_cache", {})
    flagged = state.setdefault("flagged", {})

    # unique quote symbols needing a (re)fresh earnings date
    need: dict[str, str] = {}
    for r in calls:
        sym = _yf_symbol(r.get("ticker", ""))
        if not sym:
            continue
        c = cache.get(sym)
        if c and c.get("fetched") and (today - datetime.date.fromisoformat(c["fetched"])).days < CACHE_DAYS:
            continue
        need[sym] = sym

    misses = []
    if need:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futs = {pool.submit(_next_earnings, s): s for s in need}
            for fut, s in list(futs.items()):
                try:
                    nd = fut.result(timeout=PER_TICKER_TIMEOUT)
                    cache[s] = {"next": nd, "fetched": today.isoformat()}
                    if nd is None:
                        misses.append(s)
                except (FutTimeout, Exception):
                    cache[s] = {"next": None, "fetched": today.isoformat()}
                    misses.append(s)

    flags = []
    for r in calls:
        tick = r.get("ticker", "")
        sym = _yf_symbol(tick)
        if not sym:
            continue
        nd = (cache.get(sym) or {}).get("next")
        if not nd:
            continue
        cat = r.get("cat_date")
        gap = (datetime.date.fromisoformat(cat) - datetime.date.fromisoformat(nd)).days
        if gap > GRACE_DAYS:
            key = f"{tick}|{nd}"
            if flagged.get(key) and nd >= today.isoformat():
                continue                      # already flagged, earlier date not yet passed
            flagged[key] = today.isoformat()
            flags.append(f"NEEDS-PACK: {tick} prints {nd}, {gap}d BEFORE its {cat} trigger "
                         f"— the earlier print can pre-determine the binary (the KER lesson); arm a pack for {nd}")
    # re-arm: drop flag keys whose earlier date has passed
    for k in list(flagged):
        if k.split("|")[1] < today.isoformat():
            del flagged[k]

    if not dry:
        STATE.write_text(json.dumps(state, indent=1))
    print(f"[calendar_guard] {len(calls)} open calls in horizon, {len(need)} dates fetched, "
          f"{len(misses)} DATA MISSING ({', '.join(misses[:12])}{'...' if len(misses) > 12 else ''})")
    for f in flags:
        print("  " + f)
    if not flags:
        print("  no early-print gaps — every trigger's next real print is at or inside its window")
    return flags


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
