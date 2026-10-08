"""The 0DTE resident daemon (PRINCIPAL-LAUNCHED, like envelope_runner):

    nohup caffeinate -is python3 -u -m desk.odte.runner --daemon         > desk/data/odte/runner.out 2>&1 &   # capture + shadow only
    nohup caffeinate -is python3 -u -m desk.odte.runner --daemon --live  > desk/data/odte/runner.out 2>&1 &   # + the live rail

Per session (ET weekdays): connect ~09:28, capture every 60s 09:30-16:05, run the shadow book
on every snapshot, and — with --live AND the envelope ARMED AND every risk gate green — follow
LIVE_TEMPLATE with one real contract: open in the entry window, manage (stop / VIX1D kill /
15:45 time exit), cancel-all at 15:50, write the live row, email the day's card at the close.

Halt: `python3 -m desk.odte.runner --halt "why"` writes desk/data/odte/HALT (the live rail
flattens and refuses; shadow continues). `--resume` removes it. `--probe` = connect, build
today's candidate, run whatIf, print — no order. `--once` = one capture snapshot to stdout.
Infra errors reconnect with backoff and never self-halt; a LOGIC error halts the live rail
(HALT file + email) and leaves the shadow book running.
"""
from __future__ import annotations

import argparse
import fcntl
import datetime as dt
import json
import os
import sys
import time
import traceback
from zoneinfo import ZoneInfo

from desk.odte import calendar as cal
from desk.odte.doctrine import (DATA, HALT_FILE, LOCK_FILE, ENVELOPE, LIVE_TEMPLATE, TEMPLATES, CONTRACTS, RTH_OPEN_ET,
                                CANCEL_ALL_ET, SETTLE_ET, freeze)
from desk.odte import shadow as S
from desk.odte import risk as R
from desk.odte.capture import ChainCapture, ET
from desk.odte.templates import build_condor, manage, settle
from desk.odte.rail import LiveRail, append_live, read_live, live_pnl_usd

RECONCILE_IDLE_S = 300        # before any order exists, poll the broker every 5 min, not every tick

ROOT = DATA.parents[2]
ENVELOPES = ROOT / "desk" / "data" / "envelopes.json"
CLIENT_ID = 78


def _envelope() -> dict | None:
    try:
        return json.loads(ENVELOPES.read_text())["envelopes"].get(ENVELOPE)
    except Exception:
        return None


def _set_envelope(**kw) -> None:
    reg = json.loads(ENVELOPES.read_text()); reg["envelopes"].setdefault(ENVELOPE, {}).update(kw)
    ENVELOPES.write_text(json.dumps(reg, indent=1))


def _halted() -> str | None:
    return HALT_FILE.read_text().strip() if HALT_FILE.exists() else None


def _mail(subject: str, body: str) -> None:
    try:
        from desk.mailer import send_raw
        send_raw(subject, body)
    except Exception as e:
        print(f"[odte] mail failed: {e}")


def _connect(readonly: bool):
    from ib_insync import IB
    ib = IB(); ib.connect("127.0.0.1", 4001, clientId=CLIENT_ID, readonly=readonly, timeout=20)
    return ib


def _hm(now: dt.datetime) -> tuple[int, int]:
    return (now.hour, now.minute)


_LOCK_HANDLE = None


def _lock() -> bool:
    """Hold an OS lock for the daemon lifetime; checking a PID alone races."""
    global _LOCK_HANDLE
    DATA.mkdir(parents=True, exist_ok=True)
    handle = LOCK_FILE.open("a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close(); return False
    handle.seek(0)
    old_pid = handle.read().strip()
    if old_pid:
        try:
            os.kill(int(old_pid), 0)
        except (ValueError, ProcessLookupError):
            pass
        else:
            handle.close(); return False  # also respect a pre-upgrade daemon
    handle.seek(0); handle.truncate(); handle.write(str(os.getpid())); handle.flush()
    _LOCK_HANDLE = handle
    return True


def _unlock() -> None:
    global _LOCK_HANDLE
    if _LOCK_HANDLE is not None:
        _LOCK_HANDLE.seek(0); _LOCK_HANDLE.truncate(); _LOCK_HANDLE.flush()
        fcntl.flock(_LOCK_HANDLE, fcntl.LOCK_UN)
        _LOCK_HANDLE.close(); _LOCK_HANDLE = None
    # Retain the inode: unlinking it would permit a second lock on a new file.


class Session:
    """One trading date: capture + shadow + optional live."""

    def __init__(self, ib, date: str, live: bool):
        self.ib = ib; self.date = date; self.live = live
        self.cap = ChainCapture(ib, date.replace("-", ""))
        self.st = S.load_state(date); self.is_event = cal.is_event_day(date)
        self.rail = None; self.lv = self.st.setdefault("live", {"status": "NONE"})
        self._last_recon = 0.0; self._last_prior_sweep = 0.0; self._prior_unresolved = 0
        if live:
            from desk.account_registry import require_alpha
            self.rail = LiveRail(ib, require_alpha(ib), date=date, checkpoint=self._journal_order)
            self._settle_prior()
            self._repair_ledger(self.st, self.lv, self.date)
            self._reconcile_live(force=True)
        self.cancelled = False; self.mailed = bool(self.st.get("mailed"))

    # ---- earlier sessions: settlement, late fees, overnight cancels --------------------------------
    @staticmethod
    def _needs_work(lv: dict) -> bool:
        """Anything a later broker read could still change: an open/in-flight position, a closed
        trade whose fee reports are incomplete, or a prior reconciliation error."""
        return (lv.get("status") in {"OPEN", "OPENING", "CLOSING"}
                or (lv.get("status") == "CLOSED" and not lv.get("fees_complete"))
                or bool(lv.get("reconciliation_error") or lv.get("external_executions")))

    def _repair_ledger(self, st: dict, lv: dict, d: str) -> None:
        """Replay the checkpoint's ledger projection after an interrupted upsert.

        Older checkpoints have no projection. Rebuild their terminal row when
        needed, including the pre-upgrade crash between saving state and ledger.
        Reconciliation errors always keep their pending-execution row.
        """
        row = lv.get("ledger_row")
        existing = next((r for r in read_live() if r.get("book", "live") == "live"
                         and r["date"] == d and r["template"] == LIVE_TEMPLATE), None)
        terminal = lv.get("status") in {"CLOSED", "NO_FILL", "SKIPPED"}
        blocked = lv.get("reconciliation_error") or lv.get("external_executions")
        if blocked and (not row or row.get("accounting_status") != "pending_execution"):
            with self._context(st, lv, d):
                self._record_pending()
        elif terminal and not blocked and (not row or row.get("accounting_status") == "pending_execution"):
            if not existing or existing.get("accounting_status") == "pending_execution":
                with self._context(st, lv, d):
                    self._record_live()
        elif row and row != existing:
            append_live(row)

    def _settle_prior(self) -> int:
        """Reconcile every prior session that still needs work, through the SAME state machine as
        the live session (expiry -> EXPIRED_SETTLED off the official close; round trip -> CLOSED;
        terminal zero-fill -> NO_FILL; late commission reports -> net). Returns how many are still
        needing retry (including fees); tick() retries those every RECONCILE_IDLE_S.
        This count is work to do, not an entry veto: the ledger's exposure and loss
        gates decide whether another entry is permitted."""
        self._last_prior_sweep = time.time(); unresolved = 0
        for p in sorted(DATA.glob("shadow_state_*.json")):
            d = p.stem.replace("shadow_state_", "")
            if d >= self.date:
                continue
            try:
                st = json.loads(p.read_text())
            except Exception:
                continue
            lv = st.get("live") or {}
            self._repair_ledger(st, lv, d)
            if not self._needs_work(lv):
                continue
            ok = self._reconcile_state(st, lv, d, force=True)
            if not ok or self._needs_work(lv):
                unresolved += 1
                print(f"[odte] prior session {d} still unresolved: {lv.get('reconciliation_error') or lv.get('status')}")
        self._prior_unresolved = unresolved
        return unresolved

    def _book_settlement(self, res: dict) -> bool:
        """self.* already point at the session being settled (see _context)."""
        close = self.rail.official_close(self.date)
        if close is None:
            self.lv["reconciliation_error"] = "expired; official close not yet available"
            self._record_pending()
            print(f"[odte] {self.date}: expired, official close not available yet"); return False
        s = settle(self.lv["legs"], close)
        self.lv.update(credit=res["credit"], exit_cost=s, status="CLOSED", exit_reason="EXPIRED_SETTLED", exit_ts="settlement",
                       remaining=0, filled_contracts=res["opened"], commissions_usd=res["commissions"], fees_complete=res["fees_complete"],
                       settlement={"xsp_official_close": close, "source": "broker daily bar (XSP PM settles to the closing index value)",
                                   "statement_confirmed": False})
        self.lv.pop("reconciliation_error", None)
        self._record_live()
        print(f"[odte] {self.date}: EXPIRED_SETTLED at XSP {close} -> exit {s}")
        return True

    def _context(self, st: dict, lv: dict, d: str):
        """Temporarily point self.st/self.lv/self.date at another session's state."""
        import contextlib
        sess = self

        @contextlib.contextmanager
        def cm():
            saved = (sess.st, sess.lv, sess.date)
            sess.st, sess.lv, sess.date = st, lv, d
            try:
                yield
            finally:
                sess.st, sess.lv, sess.date = saved
        return cm()

    def tick(self, now: dt.datetime) -> None:
        hm = _hm(now)
        spot = self.cap._spot()
        if spot:
            self.cap.ensure_band(spot); self.cap.maybe_fallback_delayed()
        snap = self.cap.snapshot(now); ChainCapture.write(snap, self.date)
        if self.live and snap.get("indices_live"):
            S.update_session(self.st.setdefault("live_session", {}), snap, hm)
        closed = S.step(self.st, snap, hm, self.is_event)
        for r in closed:
            S.append_ledger(r); print(f"[odte] shadow {r['template']} {r['reason']} pnl={r['pnl_usd']}")
        if self.live and self.rail:
            try:
                if self._prior_unresolved and (time.time() - self._last_prior_sweep) >= RECONCILE_IDLE_S:
                    self._settle_prior()          # an official close / fee report can land any time
                self._live_tick(snap, hm)
            except Exception as e:
                if _is_infra(e):
                    raise
                HALT_FILE.write_text(f"{self.date} live logic error: {type(e).__name__}: {e}")
                _mail(f"ODTE LIVE HALTED — {type(e).__name__}", traceback.format_exc()[-3000:])
                print(f"[odte] LIVE HALTED: {e}")
        if hm >= CANCEL_ALL_ET and self.rail and not self.cancelled:
            self.rail.cancel_all_ours(); self.cancelled = True
        if self.rail and hm >= SETTLE_ET:
            self._finish_live(snap)
        # Research runs after broker management. Only local observation IO is
        # allowed here; inference runs in a separate, broker-free worker.
        if (S.DATA / "text_overlay" / "manifest.json").exists():
            try:
                from desk.odte.text_overlay import observe
                observe(S.DATA / "text_overlay", self.st, snap, cal.load(), now=dt.datetime.now(dt.timezone.utc))
                self.st.pop("text_overlay_error", None)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                if self.st.get("text_overlay_error") != error:
                    print(f"[odte] TEXT RESEARCH UNAVAILABLE: {error}")
                self.st["text_overlay_error"] = error
        # The separate arms protocol names any ongoing forecast source. Keep its
        # calibration independent of the original one-day registration.
        if (S.DATA / "arm_experiment" / "manifest.json").exists():
            try:
                from desk.odte import arms
                arm_root = S.DATA / "arm_experiment"
                manifest = arms.protocol(arm_root)
                if manifest.get("continuation_root") and self.date > manifest["continuation_after"]:
                    try:
                        from desk.odte.text_overlay import observe
                        observe(manifest["continuation_root"], self.st, snap, cal.load(), now=dt.datetime.now(dt.timezone.utc))
                        self.st.pop("arm_forecast_error", None)
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                        if self.st.get("arm_forecast_error") != error:
                            print(f"[odte] ARM FORECAST RESEARCH UNAVAILABLE: {error}")
                        self.st["arm_forecast_error"] = error
                arms.observe(arm_root, self.st, snap, cal.load(), now=dt.datetime.now(dt.timezone.utc))
                self.st.pop("arm_experiment_error", None)
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                if self.st.get("arm_experiment_error") != error:
                    print(f"[odte] ARM RESEARCH UNAVAILABLE: {error}")
                self.st["arm_experiment_error"] = error
        if hm >= SETTLE_ET and not self.st.get("finalized"):
            for r in S.finalize_day(self.st):
                print(f"[odte] shadow {r['template']} {r['reason']} pnl={r['pnl_usd']}")
            if not self.mailed:
                self._mail_card(); self.mailed = True; self.st["mailed"] = True
        S.save_state(self.st)

    # ---- live ------------------------------------------------------------------------------
    def _ctx(self, snap: dict, hm) -> dict:
        sess = self.st.get("live_session", {})
        return {"date": self.date, "now_et": hm, "vix1d_open": sess.get("vix1d_open"), "vix1d_now": snap.get("vix1d") if snap.get("indices_live") else None,
                "first30_range": sess.get("first30_range"), "is_event_day": self.is_event,
                "calendar_verified": cal.calendar_verified_for(self.date), "halted": _halted(),
                "structures_today": 1 if self.lv.get("orders") or self.lv["status"] != "NONE" else 0}

    def _journal_order(self, order: dict) -> None:
        self.lv.setdefault("orders", []).append(order)
        self.lv["status"] = "OPENING" if order["action"] == "BUY" else "CLOSING"
        # This survives a crash before the next tick, including a restart on a
        # later trading date whose session uses a different checkpoint file.
        # Both checkpoint and ledger must succeed before broker submission.
        self._record_pending()

    def _reconcile_live(self, force: bool = False) -> bool:
        """Cadence: every tick while anything is in flight or open; every RECONCILE_IDLE_S while
        idle (observation only). Anything that leads to an ORDER passes force=True — a cached read
        is never the basis for a submission (2026-10-07 review, item 2)."""
        idle = self.lv["status"] in {"NONE", "SKIPPED", "NO_FILL"} and not self.lv.get("reconciliation_error")
        if idle and not force and (time.time() - self._last_recon) < RECONCILE_IDLE_S:
            return True
        self._last_recon = time.time()
        return self._reconcile_state(self.st, self.lv, self.date)

    def _reconcile_state(self, st: dict, lv: dict, d: str, force: bool = False) -> bool:
        """One broker read applied to one session's live state (current or prior)."""
        result = self.rail.reconcile(lv, d)
        with self._context(st, lv, d):
            if result.get("ok") and result.get("expired"):
                return self._book_settlement(result)
            if not result["ok"]:
                changed = self.lv.get("reconciliation_error") != result["why"]
                self.lv["reconciliation_error"] = result["why"]
                self._record_pending()
                if changed:
                    print(f"[odte] RECONCILIATION REQUIRED ({d}): {result['why']}")
                    _mail(f"ODTE reconciliation required ({d})", result["why"])
                return False
            self.lv.pop("reconciliation_error", None)
            self.lv.update(remaining=result["remaining"], filled_contracts=result["opened"], commissions_usd=result["commissions"],
                           fees_complete=result["fees_complete"])
            if result["pending"]:
                self.lv["status"] = "CLOSING" if any(o["action"] == "SELL" for o in self.lv["orders"]) else "OPENING"
            elif result["opened"]:
                self.lv["credit"] = result["credit"]
                self.lv["status"] = "OPEN" if result["remaining"] else "CLOSED"
                if not result["remaining"]:
                    self.lv.update(exit_cost=result["debit"], exit_reason=self.lv.get("exit_reason", "RECONCILED_CLOSE"))
            elif self.lv.get("orders"):
                self.lv.update(status="NO_FILL", why="all entry orders terminal with no executions")
            if self.lv["status"] in {"CLOSED", "NO_FILL", "SKIPPED"}:
                self._record_live()
            elif self.lv.get("orders"):
                self._record_pending()
            else:
                S.save_state(self.st)
        return True

    def _persist_live_row(self, row: dict) -> None:
        # The atomic checkpoint is the durable outbox. If the ledger write fails,
        # startup replays this exact row, including terminal states with no work.
        self.lv["ledger_row"] = row
        S.save_state(self.st)
        append_live(row)

    def _record_pending(self) -> None:
        self._persist_live_row({**self._live_row(None, "UNRESOLVED"), "position_status": self.lv["status"],
                                "accounting_status": "pending_execution"})

    def _record_live(self) -> None:
        gross = net = None
        if self.lv["status"] == "CLOSED":
            gross = live_pnl_usd(self.lv["credit"], self.lv["exit_cost"], contracts=self.lv["filled_contracts"])
            if self.lv.get("fees_complete"):
                net = round(gross - self.lv["commissions_usd"], 2)
        reason = self.lv.get("exit_reason") or ("NO_ENTRY" if self.lv["status"] == "SKIPPED" else "NO_FILL")
        row = self._live_row(net, reason)
        status = "pending_fees" if gross is not None and net is None else "complete"
        if self.lv.get("settlement") and not self.lv["settlement"].get("statement_confirmed"):
            status = "pending_statement"          # booked off the official close; statement confirmation owed
        row.update(gross_pnl_usd=gross, commissions_usd=self.lv.get("commissions_usd"), fees_complete=bool(self.lv.get("fees_complete")),
                   accounting_status=status, settlement=self.lv.get("settlement"), manual_resolution=self.lv.get("manual_resolution"))
        self._persist_live_row(row)

    def _entry_risk_ok(self, snap: dict, hm) -> bool:
        ok, reasons, pause = R.live_gates(_envelope(), read_live(), self._ctx(snap, hm))
        if pause:
            _set_envelope(status="PAUSED", paused=f"{self.date}: {pause}")
            _mail(f"ODTE envelope PAUSED — {pause}", "Re-ratify in chat to re-arm.")
        if not ok:
            self.lv["last_why"] = "; ".join(reasons)
        return ok

    def _live_tick(self, snap: dict, hm) -> None:
        if not self._reconcile_live():
            return
        t = TEMPLATES[LIVE_TEMPLATE]; ctx = self._ctx(snap, hm)
        rows = [r for r in snap.get("rows", []) if r.get("live_eligible")]
        if self.lv["status"] == "NONE":
            if not (tuple(t["entry_et"]) <= hm <= tuple(t["entry_close_et"])):
                if hm > tuple(t["entry_close_et"]):
                    self.lv.update(status="SKIPPED", why=self.lv.get("last_why") or "no entry in window")
                    self._record_live()
                return
            if not snap.get("indices_live"):
                self.lv["last_why"] = "required index prices are not fresh live ticks"; return
            if not self._entry_risk_ok(snap, hm):
                return
            c = build_condor(rows, t["short_delta"], t["wing"])
            if not c["ok"]:
                self.lv["last_why"] = c["why"]; return
            if not self.rail.margin_checked:
                w = self.rail.what_if(c["legs"], c["credit"], c["max_loss_usd"])
                if not w["ok"]:
                    self.lv["last_why"] = f"whatIf refused: {w}"
                    HALT_FILE.write_text(f"{self.date} whatIf margin {w['init_margin_change']} vs max loss {c['max_loss_usd']}")
                    _mail("ODTE LIVE HALTED — whatIf margin mismatch", json.dumps(w, indent=1)); return
            if self._prior_unresolved:
                self._settle_prior()
            # Fresh current exposure, then caps based on every reconciliation above.
            # Missing fees remain retry work; they are charged a reserve by risk.
            if not self._reconcile_live(force=True) or self.lv["status"] != "NONE":
                self.lv["last_why"] = self.lv.get("reconciliation_error") or f"state {self.lv['status']} at entry"; return
            if not self._entry_risk_ok(snap, hm):
                return
            self.lv.update(legs=c["legs"], credit_asked=c["credit"], entry_ts=snap["ts"],
                           max_loss_usd=c["max_loss_usd"], max_cost=c["credit"])
            self.lv["open_order"] = self.rail.open_condor(c["legs"], c["credit"])
            self._reconcile_live(force=True)
        elif self.lv["status"] == "OPEN":
            kill = R.flatten_now(ctx)
            m = manage({"credit": self.lv["credit"], "legs": self.lv["legs"]}, rows, hm,
                       t["stop_mult"], tuple(t["time_exit_et"]))
            if m.get("cost") is not None:
                self.lv["max_cost"] = max(self.lv.get("max_cost", 0.), m["cost"])
            if kill or m["action"] in ("CLOSE_STOP", "CLOSE_TIME"):
                if hm >= SETTLE_ET:
                    self.lv["last_why"] = "awaiting broker settlement reconciliation"; return
                if m.get("cost") is None and not kill:
                    self.lv["last_why"] = "no fresh live quotes for exit"; return
                self.lv.update(exit_ts=snap["ts"], exit_reason=("KILL:" + kill) if kill else m["action"])
                self.lv["close_order"] = self.rail.close_condor(
                    self.lv["legs"], m["cost"] if m.get("cost") is not None else .05,
                    quantity=self.lv["remaining"])
                self._reconcile_live()

    def _finish_live(self, snap: dict) -> None:
        # A last market quote is not an execution or broker cash settlement.
        # Keep unresolved positions visible instead of fabricating realized P&L.
        if self.lv["status"] in {"OPEN", "OPENING", "CLOSING"}:
            self.lv["last_why"] = "awaiting broker execution/settlement reconciliation"
            self._record_pending()

    def _live_row(self, pnl, reason: str) -> dict:
        sess = self.st.get("session", {})
        return {"template": LIVE_TEMPLATE, "date": self.date, "book": "live", "contracts": self.lv.get("filled_contracts", CONTRACTS),
                "credit": self.lv.get("credit"), "credit_asked": self.lv.get("credit_asked"),
                "exit_cost": self.lv.get("exit_cost"), "max_cost": self.lv.get("max_cost"),
                "pnl_usd": pnl, "reason": reason, "why": self.lv.get("reconciliation_error") or self.lv.get("why") or self.lv.get("last_why"),
                "legs": self.lv.get("legs"), "entry_ts": self.lv.get("entry_ts"), "exit_ts": self.lv.get("exit_ts"),
                "first30_range": sess.get("first30_range"), "vix1d_open": sess.get("vix1d_open"),
                "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

    def _mail_card(self) -> None:
        L = [f"0DTE {self.date} — XSP {self.st['session'].get('xsp_last')}  VIX1D open {self.st['session'].get('vix1d_open')}  "
             f"first-30 range {self.st['session'].get('first30_range')}  event-day {self.is_event}  snapshots {self.st.get('n_snapshots')}", ""]
        for name, ts in self.st["templates"].items():
            if ts["status"] == "CLOSED":
                L.append(f"  {name:12s} {ts['exit_reason']:10s} credit {ts['credit']:.2f} exit {ts['exit_cost']:.2f} "
                         f"pnl ${(ts['credit'] - ts['exit_cost']) * 100 * CONTRACTS:+.0f}  ({ts['legs']['sp']['strike']:.0f}P/{ts['legs']['sc']['strike']:.0f}C)")
            else:
                L.append(f"  {name:12s} {ts['status']:10s} {ts.get('skip_reason') or ts.get('last_why') or ''}")
        lv = self.lv
        L += ["", f"  LIVE ({LIVE_TEMPLATE}, {CONTRACTS} contract): {lv.get('status')} {lv.get('exit_reason') or lv.get('why') or ''}"
              + (f" credit {lv.get('credit')} exit {lv.get('exit_cost')} gross ${live_pnl_usd(lv['credit'], lv['exit_cost'], contracts=lv['filled_contracts']):+.0f}"
                 + (f" net ${live_pnl_usd(lv['credit'], lv['exit_cost'], contracts=lv['filled_contracts'], commissions=lv['commissions_usd']):+.0f}"
                    if lv.get("fees_complete") else " net pending fees") if lv.get("status") == "CLOSED" else "")
              + f" {lv.get('reconciliation_error') or lv.get('last_why') or ''}"]
        _mail(f"0DTE card {self.date}: " + ", ".join(f"{n} {('$%+.0f' % ((t['credit']-t['exit_cost'])*100*CONTRACTS)) if t['status']=='CLOSED' else t['status']}" for n, t in self.st["templates"].items()), "\n".join(L))


def _is_infra(e: BaseException) -> bool:
    return isinstance(e, (TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError, OSError)) or "not connected" in str(e).lower()


def daemon(live: bool) -> None:
    if not _lock():
        print("[odte] another runner is live — refusing to double-run"); return
    freeze()
    print(f"[odte] daemon up live={live} — capture 09:30-16:05 ET weekdays; halt-switch {HALT_FILE}")
    sess = None; ib = None; backoff = 30
    last_research_log = 0.
    while True:
        now = dt.datetime.now(ET); hm = _hm(now); date = now.date().isoformat()
        in_window = now.weekday() < 5 and (9, 28) <= hm <= (16, 6)
        try:
            # Diagnose drift before connecting, including outside market hours.
            # Research can fail closed without preventing ordinary capture or
            # order management. Remind once per 15 minutes while blocked.
            try:
                from desk.odte import research_health
                health, changed = research_health.publish(DATA)
                if changed or not last_research_log or (health["status"] == "blocked" and time.monotonic()-last_research_log >= 900):
                    research_health.log(health); last_research_log = time.monotonic()
            except Exception as exc:
                if not last_research_log or time.monotonic()-last_research_log >= 900:
                    print(f"[odte] !!! RESEARCH PREFLIGHT FAILED: {type(exc).__name__}; check research_health.json !!!", flush=True)
                    last_research_log = time.monotonic()
            if in_window:
                if ib is None or not ib.isConnected():
                    if sess is not None:
                        sess.cap.close()
                    sess = None
                    ib = _connect(readonly=not live); backoff = 30
                    print(f"[odte] connected {ib.managedAccounts()} at {now.isoformat(timespec='minutes')}")
                if sess is None or sess.date != date:
                    sess = Session(ib, date, live)
                if hm >= RTH_OPEN_ET:
                    sess.tick(now)
                ib.sleep(max(1.0, 60 - dt.datetime.now(ET).second))
            else:
                if ib is not None and ib.isConnected():
                    try:
                        sess.cap.close()
                    except Exception:
                        pass
                    ib.disconnect(); ib = None; sess = None; print("[odte] session closed — disconnected")
                time.sleep(60)
        except KeyboardInterrupt:
            break
        except Exception as e:
            if _is_infra(e):
                print(f"[odte] infra: {type(e).__name__}: {e} — retry in {backoff}s")
                try:
                    if ib: ib.disconnect()
                except Exception:
                    pass
                ib = None; sess = None; time.sleep(backoff); backoff = min(300, backoff * 2)
            else:
                print(f"[odte] ERROR {type(e).__name__}: {e}\n{traceback.format_exc()[-2000:]}")
                if live:
                    HALT_FILE.write_text(f"{date} runner error: {type(e).__name__}: {e}")
                    _mail(f"ODTE runner error — live rail halted: {type(e).__name__}", traceback.format_exc()[-3000:])
                time.sleep(60)
    _unlock()


def probe() -> None:
    """Connect, build today's candidate from a 20s capture, run whatIf, print. No order."""
    from desk.account_registry import require_alpha
    now = dt.datetime.now(ET); date = now.date().isoformat()
    ib = _connect(readonly=False)
    try:
        cap = ChainCapture(ib, date.replace("-", "")); ib.sleep(5)
        spot = cap._spot(); print("spot", spot, "VIX1D", cap.idx["VIX1D"].last)
        if not spot:
            print("no spot (market closed?)"); return
        cap.ensure_band(spot); cap.maybe_fallback_delayed(); snap = cap.snapshot(now)
        print(f"data_type={snap['data_type']} greeks={snap['greeks']} quoted={snap['n_quoted']}/{len(snap['rows'])}")
        c = build_condor(snap["rows"], TEMPLATES[LIVE_TEMPLATE]["short_delta"], TEMPLATES[LIVE_TEMPLATE]["wing"])
        print(json.dumps({k: v for k, v in c.items() if k != "legs"}, indent=1))
        if c["ok"]:
            rail = LiveRail(ib, require_alpha(ib)); print(json.dumps(rail.what_if(c["legs"], c["credit"], c["max_loss_usd"]), indent=1, default=str))
        cap.close()
    finally:
        ib.disconnect()


def resolve(date: str, exit_cost: float, fees: float, note: str, credit: float | None = None, by: str = "principal") -> dict:
    """MANUAL RESOLUTION of a blocked session from the broker STATEMENT (a manual close in TWS, an
    execution the Gateway can no longer show). Books the row CLOSED / MANUAL_CLOSE with the
    statement's exit cost and fees, clears the external-execution evidence and the reconciliation
    error, and leaves an audit record of who, when and why. Offline — no broker connection.

        python3 -m desk.odte.runner --resolve YYYY-MM-DD --exit-cost 1.50 --fees 3.25 --note "statement-verified manual close"
    """
    if not note or not note.strip():
        raise SystemExit("--note is required: cite the statement line you are booking from")
    st = S.load_state(date); lv = st.get("live") or {}
    blocked = lv.get("status") in {"OPEN", "OPENING", "CLOSING"} or lv.get("external_executions") or lv.get("reconciliation_error")
    if not blocked:
        raise SystemExit(f"{date}: nothing to resolve (status {lv.get('status')}, no reconciliation error)")
    credit = lv.get("credit") if credit is None else credit
    if credit is None:
        raise SystemExit("entry credit unknown (no fill was ever reconciled): pass --credit from the statement")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    lv["manual_resolution"] = {"by": by, "note": note.strip(), "utc": now, "prior_status": lv.get("status"),
                               "prior_error": lv.get("reconciliation_error"), "external_executions": lv.get("external_executions") or {},
                               "exit_cost": float(exit_cost), "fees": float(fees), "credit": float(credit)}
    lv.update(status="CLOSED", exit_reason="MANUAL_CLOSE", exit_ts="manual", credit=float(credit), exit_cost=float(exit_cost),
              remaining=0, filled_contracts=lv.get("filled_contracts") or CONTRACTS, commissions_usd=float(fees), fees_complete=True,
              external_executions={})
    lv.pop("reconciliation_error", None); lv.pop("last_why", None); lv["why"] = f"manual resolution by {by}"
    sess = Session.__new__(Session); sess.st, sess.lv, sess.date, sess.rail = st, lv, date, None
    sess._record_live()
    from desk.odte.rail import _audit
    _audit("MANUAL_RESOLVE", {"date": date, **lv["manual_resolution"]})
    row = {r["date"]: r for r in read_live()}[date]
    print(f"[odte] {date} resolved by {by}: credit {credit} exit {exit_cost} fees {fees} -> net ${row.get('pnl_usd')} ({row.get('accounting_status')})")
    return row


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--daemon", action="store_true"); ap.add_argument("--live", action="store_true")
    ap.add_argument("--probe", action="store_true"); ap.add_argument("--once", action="store_true")
    ap.add_argument("--halt", metavar="WHY"); ap.add_argument("--resume", action="store_true"); ap.add_argument("--status", action="store_true")
    ap.add_argument("--resolve", metavar="DATE", help="book a blocked session from the broker statement (see resolve())")
    ap.add_argument("--exit-cost", type=float); ap.add_argument("--fees", type=float); ap.add_argument("--credit", type=float)
    ap.add_argument("--note", default=""); ap.add_argument("--by", default="principal")
    a = ap.parse_args()
    if a.resolve:
        if a.exit_cost is None or a.fees is None:
            raise SystemExit("--resolve needs --exit-cost and --fees (per-share exit cost, total USD fees) from the statement")
        resolve(a.resolve, a.exit_cost, a.fees, a.note, credit=a.credit, by=a.by)
    elif a.halt:
        DATA.mkdir(parents=True, exist_ok=True); HALT_FILE.write_text(a.halt); print(f"[odte] HALTED: {a.halt}")
    elif a.resume:
        HALT_FILE.unlink(missing_ok=True); print("[odte] resumed")
    elif a.status:
        print(json.dumps({"envelope": _envelope(), "halted": _halted(), "live_rows": len(read_live()),
                          "shadow_rows": len(S.read_ledger()), "frozen": freeze()}, indent=1))
    elif a.probe:
        probe()
    elif a.once:
        ib = _connect(readonly=True)
        try:
            cap = ChainCapture(ib, dt.datetime.now(ET).date().isoformat().replace("-", "")); ib.sleep(5)
            s = cap._spot(); cap.ensure_band(s) if s else None; cap.maybe_fallback_delayed(); snap = cap.snapshot()
            print(json.dumps({k: v for k, v in snap.items() if k != "rows"}, indent=1)); print("rows", len(snap["rows"]), snap["rows"][:3])
        finally:
            ib.disconnect()
    elif a.daemon:
        daemon(a.live)
    else:
        ap.print_help()
