"""The shadow book: every template runs every session on the captured chain, filled at the touch.
One row per (template, date) in desk/data/odte/shadow_ledger.jsonl. The in-progress day lives in
shadow_state_DATE.json so a daemon restart mid-session resumes rather than re-enters.

Session context the templates need (built by the runner from the capture stream):
  first30_range  SPX (hi - lo) / open over 09:30-10:00
  vix1d_open     VIX1D at the first capture (~09:31)
  is_event_day   calendar
"""
from __future__ import annotations

import datetime as dt
import json

from desk.odte.doctrine import (DATA, SHADOW_LEDGER, TEMPLATES, CONTRACTS, SETTLE_ET, template_hash)
from desk.odte.storage import atomic_json
from desk.odte.templates import build_condor, manage, settle, pnl_usd, entry_allowed


def _state_path(date: str):
    return DATA / f"shadow_state_{date}.json"


def load_state(date: str) -> dict:
    p = _state_path(date)
    if p.exists():
        return json.loads(p.read_text())
    return {"date": date, "templates": {k: {"status": "NONE", "hash": template_hash(k)} for k in TEMPLATES},
            "session": {}, "n_snapshots": 0}


def save_state(st: dict) -> None:
    atomic_json(_state_path(st["date"]), st)


def append_ledger(row: dict, path=None) -> None:
    path = path or SHADOW_LEDGER            # resolved at call time so tests can monkeypatch the module global
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row) + "\n")


def read_ledger(path=None) -> list[dict]:
    path = path or SHADOW_LEDGER
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def update_session(sess: dict, snap: dict, now_et: tuple[int, int]) -> dict:
    """Accumulate the open/first-30 stats from the capture stream."""
    spx, vix = snap.get("spx"), snap.get("vix1d")
    if spx:
        sess.setdefault("spx_open", spx)
        if now_et < (10, 0):
            sess["spx_hi30"] = max(sess.get("spx_hi30", spx), spx); sess["spx_lo30"] = min(sess.get("spx_lo30", spx), spx)
        sess["spx_last"] = spx
    if vix:
        sess.setdefault("vix1d_open", vix); sess["vix1d_last"] = vix
    if snap.get("xsp"):
        sess["xsp_last"] = snap["xsp"]
    if sess.get("spx_open") and sess.get("spx_hi30") is not None and now_et >= (10, 0):
        sess["first30_range"] = round((sess["spx_hi30"] - sess["spx_lo30"]) / sess["spx_open"], 5)
    return sess


def step(st: dict, snap: dict, now_et: tuple[int, int], is_event_day: bool) -> list[dict]:
    """Advance every template one snapshot. Returns the rows closed on this step."""
    sess = update_session(st.setdefault("session", {}), snap, now_et)
    st["n_snapshots"] = st.get("n_snapshots", 0) + 1
    ctx = {"now_et": now_et, "is_event_day": is_event_day, "first30_range": sess.get("first30_range"),
           "vix1d_open": sess.get("vix1d_open"), "vix1d_now": snap.get("vix1d")}
    rows = snap.get("rows") or []
    closed = []
    for name, t in TEMPLATES.items():
        ts = st["templates"][name]
        if ts["status"] == "NONE":
            ok, why = entry_allowed(name, ctx)
            if tuple(t["entry_et"]) <= now_et <= tuple(t["entry_close_et"]) and not ok:
                reg = t.get("regime")
                known = (t["blackout"] and is_event_day) or (reg and all(ctx.get(k) is not None for k in
                         ("first30_range", "vix1d_open", "vix1d_now")))
                ts["saw_strategy_skip" if known else "entry_data_gap"] = True
            if now_et > tuple(t["entry_close_et"]) and ts.get("skip_reason") is None:
                ts["status"] = "SKIPPED"; ts["skip_reason"] = ts.get("last_why") or why or "no entry in window"
                closed.append(_row(name, st, ts, snap, pnl=None, reason="NO_ENTRY"))
                continue
            if not ok:
                ts["last_why"] = why; continue
            c = build_condor(rows, t["short_delta"], t["wing"])
            if not c["ok"]:
                ts["entry_data_gap"] = True
                ts["last_why"] = c["why"]; continue
            ts.update({"status": "OPEN", "entry_ts": snap["ts"], "credit": c["credit"], "legs": c["legs"],
                       "max_loss_usd": c["max_loss_usd"], "entry_data_type": snap.get("data_type"),
                       "entry_greeks": snap.get("greeks"), "max_cost": c["credit"]})
        elif ts["status"] == "OPEN":
            m = manage({"credit": ts["credit"], "legs": ts["legs"]}, rows, now_et, t["stop_mult"], tuple(t["time_exit_et"]))
            if m.get("cost") is not None:
                ts["max_cost"] = max(ts.get("max_cost", 0.0), m["cost"])
            if m["action"] in ("CLOSE_STOP", "CLOSE_TIME") and m.get("cost") is not None:
                ts.update({"status": "CLOSED", "exit_ts": snap["ts"], "exit_cost": m["cost"], "exit_reason": m["action"]})
                closed.append(_row(name, st, ts, snap, pnl=pnl_usd(ts["credit"], m["cost"], CONTRACTS), reason=m["action"]))
            elif m["action"] == "CLOSE_TIME" and m.get("cost") is None and now_et >= SETTLE_ET and sess.get("xsp_last"):
                s = settle(ts["legs"], sess["xsp_last"])
                ts.update({"status": "CLOSED", "exit_ts": snap["ts"], "exit_cost": s, "exit_reason": "SETTLED"})
                closed.append(_row(name, st, ts, snap, pnl=pnl_usd(ts["credit"], s, CONTRACTS), reason="SETTLED"))
    return closed


def _row(name: str, st: dict, ts: dict, snap: dict, pnl, reason: str) -> dict:
    sess = st.get("session", {})
    return {"template": name, "hash": ts.get("hash"), "date": st["date"], "book": "shadow", "contracts": CONTRACTS,
            "entry_ts": ts.get("entry_ts"), "exit_ts": ts.get("exit_ts"), "credit": ts.get("credit"), "exit_cost": ts.get("exit_cost"),
            "max_cost": ts.get("max_cost"), "pnl_usd": pnl, "reason": reason, "skip_reason": ts.get("skip_reason"),
            "skip_kind": ("strategy_cash" if ts.get("saw_strategy_skip") and not ts.get("entry_data_gap")
                          else "data_unavailable") if reason == "NO_ENTRY" else None,
            "legs": ts.get("legs"), "max_loss_usd": ts.get("max_loss_usd"), "data_type": ts.get("entry_data_type") or snap.get("data_type"),
            "greeks": ts.get("entry_greeks"), "first30_range": sess.get("first30_range"), "vix1d_open": sess.get("vix1d_open"),
            "spx_open": sess.get("spx_open"), "xsp_settle": sess.get("xsp_last"),
            "recorded_utc": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"}


def finalize_day(st: dict) -> list[dict]:
    """After the close: any template still OPEN with no settle quote is settled on xsp_last; any
    NONE that never entered is recorded NO_ENTRY. Returns the rows written."""
    out = []
    sess = st.get("session", {})
    for name, ts in st["templates"].items():
        if ts["status"] == "OPEN" and sess.get("xsp_last"):
            s = settle(ts["legs"], sess["xsp_last"])
            ts.update({"status": "CLOSED", "exit_cost": s, "exit_reason": "SETTLED", "exit_ts": "close"})
            out.append(_row(name, st, ts, {"ts": "close"}, pnl=pnl_usd(ts["credit"], s, CONTRACTS), reason="SETTLED"))
        elif ts["status"] == "NONE":
            ts["status"] = "SKIPPED"; ts["skip_reason"] = ts.get("last_why") or "no entry"
            out.append(_row(name, st, ts, {"ts": "close"}, pnl=None, reason="NO_ENTRY"))
    for r in out:
        append_ledger(r)
    st["finalized"] = True
    return out
