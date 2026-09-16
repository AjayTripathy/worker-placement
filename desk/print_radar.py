"""print_radar — event-aware sampling. Look HARDER when a print is due, and never
let a landed print sit ungraded.

Born 2026-07-09: BKE's June comp printed, our watcher caught the HEADLINE but couldn't
parse the number and the frozen p=0.78 call sat OPEN for hours — detection worked,
grading didn't. The fix is two-fold:

  1. HIGHER LOOKING RATE near a print. This runs hourly (vs the daily/weekly baseline
     of the source watchers). For a name whose catalyst date is TODAY/±1 and has a mapped
     source watcher (e.g. BKE -> bke_monthly_comps), it TRIGGERS that watcher so fresh
     data is pulled at hourly cadence through the print window, then relaxes.
  2. LOOP-NOT-CLOSED alarm. Any calibration call whose cat_date has PASSED but is still
     OPEN = a print that landed and wasn't graded -> a high-priority "grade it NOW" alert.
     (This is the BKE gap; it would have fired within the hour.)

Reads calibration_ledger.jsonl (frozen calls) + event_windows.json (FLOW clocks).

    python3 -m desk.print_radar
READ-ONLY on markets; may run other REGISTERED read-only watchers on print day.
"""
from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "desk" / "data"
CALIB = D / "calibration_ledger.jsonl"
EVENTS = D / "event_windows.json"
STATE = D / "print_radar_state.json"

HORIZON = 5          # 'upcoming' heads-up window (days)
# ticker -> registry watcher that pulls that name's primary print data; kicked on print day
SOURCE_WATCHERS = {"BKE": "bke_monthly_comps"}
# self-audit meta-tickers are graded by their own process, not a market print
SKIP = {"BOOK-SHARPE", "HONESTY-BACKTEST"}
FAST_HOURS_ET = set(range(6, 14))   # monthly comps release pre-market through midday ET


def _now_et():
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        return None


def _landed(r, now_et):
    """An AMC print has NOT published before ~16:00 ET, so it isn't 'landed' yet — don't kick the
    grader on it (the same same-day-AMC-looks-due-from-midnight bug that false-fired the NOW email)."""
    return not (r.get("session") == "amc" and now_et is not None and now_et.hour < 16)


def _print_window(today=None):
    """Return registered auto-confirm (comp) names with a call due ~today, IF we're inside the
    intraday release window (weekday, 6am–2pm ET). Empty => --fast mode is a cheap no-op.
    Keeps the 15-min sampler nearly free except during an actual comp print window."""
    try:
        from zoneinfo import ZoneInfo
        now_et = datetime.datetime.now(ZoneInfo("America/New_York"))
    except Exception:
        now_et = datetime.datetime.now()
    if now_et.weekday() >= 5 or now_et.hour not in FAST_HOURS_ET:
        return []
    today = today or now_et.date()
    try:
        from desk.catalyst_action import _registry
        comp = {t for t, a in _registry().items() if isinstance(a, dict) and a.get("auto_confirm")}
    except Exception:
        comp = set()
    due = []
    for r in _open_calls(today):
        if r.get("ticker") not in comp:
            continue
        try:
            d = datetime.date.fromisoformat(r["cat_date"])
        except Exception:
            continue
        if -1 <= (d - today).days <= 2:      # print-day window; monthly-comp estimates can slip a day or two
            due.append(r)
    return due


def _notify(msg: str):
    try:
        from desk.gauntlet_sentinel import _notify as n
        n(msg)
    except Exception:
        print(f"[print_radar] NOTIFY: {msg}")


def _open_calls(today):
    seen = {}
    if CALIB.exists():
        for line in CALIB.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if (r.get("status") or "OPEN").upper() == "OPEN" and r.get("cat_date") and r.get("ticker") not in SKIP:
                seen[(r["ticker"], r["cat_date"])] = r
    # ARMED PACKS join the radar universe (2026-07-29: QCOM's AMC print sat ungraded for 5h
    # because the pack lived only in the registry and the radar keyed off frozen calls only).
    # Pack entries carry an explicit `cat_date` + optional `status`; DONE/GRADED are skipped.
    try:
        reg = json.loads((D / "catalyst_action_registry.json").read_text())
        for tick, a in (reg.get("actions") or {}).items():
            cd = a.get("cat_date")
            st = str(a.get("status") or "").upper()
            if not cd or tick in SKIP or any(k in st for k in ("DONE", "GRADED")):
                continue
            if (tick, cd) not in seen:
                seen[(tick, cd)] = {"ticker": tick, "cat_date": cd, "our_p": a.get("our_p"),
                                    "catalyst": a.get("catalyst", ""), "session": a.get("session"),
                                    "_pack": True}
    except Exception:
        pass
    return list(seen.values())


def _run_watcher(name):
    """Run a REGISTERED read-only watcher to pull fresh print data. Whitelisted to the registry."""
    try:
        from desk.registry import WATCHES
        w = next((x for x in WATCHES if x["name"] == name), None)
        if not w:
            return f"{name}: not registered"
        subprocess.run(w["cmd"], cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        return f"{name}: pulled"
    except Exception as e:
        return f"{name}: {type(e).__name__}"


def _fast():
    """15-min print-window sampler: no-op unless a comp name is in its intraday release window;
    inside it, kick the comp watcher + run the grader (which self-dedups to ~1 claude/print and
    auto-confirms/arms the action). This is the sub-30-min MFT SLA path."""
    today = datetime.date.today()
    win = _print_window(today)
    if not win:
        print(f"[print_radar --fast] {today}: no comp print window active — no-op")
        return
    pulled = []
    for r in win:
        w = SOURCE_WATCHERS.get(r["ticker"])
        if w:
            pulled.append(_run_watcher(w))
    if pulled:
        try:
            from desk.headless_grader import main as _grade
            _grade()
        except Exception as e:
            print(f"[print_radar --fast] grade skipped: {type(e).__name__}")
    print(f"[print_radar --fast] {today}: WINDOW ACTIVE {[r['ticker'] for r in win]} — pulled {pulled}")


def main():
    if "--fast" in sys.argv:
        return _fast()
    today = datetime.date.today()
    calls = _open_calls(today)
    overdue, due, upcoming = [], [], []
    for r in calls:
        try:
            d = datetime.date.fromisoformat(r["cat_date"])
        except Exception:
            continue
        days = (d - today).days
        if days < 0:
            overdue.append((days, r))
        elif days == 0:
            due.append(r)
        elif days <= HORIZON:
            upcoming.append((days, r))

    # print-day / just-landed: kick the source watcher so we're sampling at hourly cadence.
    # Gate AMC names before 16:00 ET out of the 'landed' set (they can't have published yet).
    now_et = _now_et()
    landed = [r for r in due if _landed(r, now_et)] + [r for _, r in overdue]
    pulled = []
    for r in landed:
        w = SOURCE_WATCHERS.get(r["ticker"])
        if w:
            pulled.append(_run_watcher(w))

    # same-tick DETECT -> GRADE -> ARM: if a print is due/just-landed, run the headless grader NOW
    # (event-gated + capped) so the pre-registered action arms within this tick — the 30-min MFT SLA
    # dies if we wait for the grader's own cron. The grader auto-confirms mechanical grades + provisional-
    # arms the rest; catalyst_action then surfaces the plan.
    if pulled:
        try:
            from desk.headless_grader import main as _grade
            _grade()
        except Exception as e:
            print(f"[print_radar] same-tick grade skipped: {type(e).__name__}")

    fired = []
    if overdue:
        items = ", ".join(f"{r['ticker']}(cat {r['cat_date']}, p={r.get('our_p')})" for _, r in sorted(overdue, key=lambda x: x[0]))
        fired.append(f"⚠ CAT-DATE PASSED, CALL STILL OPEN — intelligent-read grade needed (`python3 -m desk.grade_brief --due`), then confirm+resolve or re-date: {items}")
    if due:
        items = ", ".join(f"{r['ticker']} (p={r.get('our_p')})" for r in due)
        fired.append(f"PRINT DUE TODAY — sampling up: {items}" + (f" [pulled {', '.join(pulled)}]" if pulled else ""))

    # dedup: only re-alert overdue once per (ticker,cat_date) per day
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    key = today.isoformat()
    prior = set(state.get(key, []))
    now_keys = {f"{r['ticker']}|{r['cat_date']}" for _, r in overdue} | {f"{r['ticker']}|due" for r in due}
    new = now_keys - prior
    if fired and new:
        _notify("PRINT RADAR: " + " | ".join(fired)[:850])
    state[key] = sorted(prior | now_keys)
    STATE.write_text(json.dumps(state, indent=1))

    print(f"[print_radar] {today}: {len(overdue)} overdue-OPEN, {len(due)} due-today, {len(upcoming)} upcoming(<= {HORIZON}d)")
    for _, r in sorted(overdue, key=lambda x: x[0]):
        print(f"  OVERDUE-OPEN  {r['cat_date']}  {r['ticker']:8} p={r.get('our_p')}  (grade it)")
    for r in due:
        print(f"  DUE TODAY     {r['cat_date']}  {r['ticker']:8} p={r.get('our_p')}")
    for days, r in sorted(upcoming, key=lambda x: x[0]):
        print(f"  upcoming +{days}d {r['cat_date']}  {r['ticker']:8} p={r.get('our_p')}")


if __name__ == "__main__":
    main()
