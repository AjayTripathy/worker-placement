"""PURE live-rail gates for the 0DTE sleeve. Every gate is a line of code with a reason string; the
runner refuses a live entry when any gate fails and records the reasons in the day's row.

State the gates read (all plain dicts so tests can build them):
  envelope: the ODTE-XSP-LIVE entry from desk/data/envelopes.json
  ledger:   list of live ledger rows [{"date", "pnl_usd", ...}]
  ctx:      {"date", "now_et", "vix1d_open", "vix1d_now", "first30_range", "is_event_day",
             "calendar_verified", "halted", "structures_today"}
"""
from __future__ import annotations

import datetime as dt

from desk.odte.doctrine import (DAILY_STRUCTURES, WEEKLY_LOSS_CAP, MONTHLY_LOSS_CAP, CONSECUTIVE_LOSS_PAUSE,
                                VIX1D_LEVEL_KILL, VIX1D_JUMP_KILL, FIRST30_RANGE_KILL, FEE_RESERVE_USD)


def _iso_week(d: str) -> tuple[int, int]:
    y, w, _ = dt.date.fromisoformat(d).isocalendar()
    return (y, w)


def _pnl(r: dict) -> float | None:
    """Net when reconciled. Otherwise GROSS minus the commissions already reported minus a reserve
    for the ones still missing — a row awaiting a fee report or a statement counts against the loss
    caps and missing costs never make a loss smaller. None = no result yet."""
    if r.get("pnl_usd") is not None:
        return float(r["pnl_usd"])
    if r.get("gross_pnl_usd") is not None:
        fees = float(r.get("commissions_usd") or 0.0)
        reserve = 0.0 if r.get("fees_complete") else FEE_RESERVE_USD
        return round(float(r["gross_pnl_usd"]) - fees - reserve, 2)
    return None


def week_pnl(ledger: list[dict], date: str) -> float:
    wk = _iso_week(date)
    return round(sum(_pnl(r) or 0 for r in ledger if r.get("date") and _iso_week(r["date"]) == wk), 2)


def month_pnl(ledger: list[dict], date: str) -> float:
    return round(sum(_pnl(r) or 0 for r in ledger if str(r.get("date", ""))[:7] == date[:7]), 2)


def consecutive_losses(ledger: list[dict]) -> int:
    n = 0
    for r in sorted((r for r in ledger if _pnl(r) is not None), key=lambda r: r["date"], reverse=True):
        if _pnl(r) < 0:
            n += 1
        else:
            break
    return n


def envelope_gates(env: dict | None, date: str) -> list[str]:
    bad = []
    if not env:
        return ["envelope missing"]
    if env.get("status") != "ARMED":
        bad.append(f"envelope status {env.get('status')}")
    if env.get("origin") != "signalos_desk+principal":
        bad.append("envelope origin is not signalos_desk+principal")
    if env.get("expires") and date > env["expires"]:
        bad.append(f"envelope expired {env['expires']}")
    return bad


def live_gates(env: dict | None, ledger: list[dict], ctx: dict) -> tuple[bool, list[str], str | None]:
    """(ok, reasons, pause_reason). pause_reason != None means the envelope must be PAUSED (needs
    re-ratification), not just skipped today."""
    reasons = envelope_gates(env, ctx["date"])
    pause = None
    # Only an UNRESOLVED POSITION blocks (an order intent with no reconciled outcome, contracts
    # possibly still open). A closed trade awaiting its commission report (pending_fees) or an
    # expired one awaiting the statement (pending_statement) counts in the caps at gross and does
    # not lock the rail (2026-10-07 review: the broader rule self-locked after one session).
    unresolved = [r for r in ledger if r.get("accounting_status") == "pending_execution"]
    if unresolved:
        reasons.append(f"prior live accounting unresolved — position {unresolved[-1].get('date')}: "
                       f"{unresolved[-1].get('why') or 'pending execution'}; reconcile before entry")
    if ctx.get("halted"):
        reasons.append(f"HALT file present: {ctx['halted']}")
    if not ctx.get("calendar_verified"):
        reasons.append("event calendar not verified through this date")
    if ctx.get("is_event_day"):
        reasons.append("event-day blackout")
    if int(ctx.get("structures_today", 0)) >= DAILY_STRUCTURES:
        reasons.append("daily structure cap reached")
    wp = week_pnl(ledger, ctx["date"])
    if wp <= -WEEKLY_LOSS_CAP:
        reasons.append(f"weekly loss cap hit ({wp:+.0f} <= -{WEEKLY_LOSS_CAP:.0f})")
    mp = month_pnl(ledger, ctx["date"])
    if mp <= -MONTHLY_LOSS_CAP:
        reasons.append(f"monthly loss cap hit ({mp:+.0f})"); pause = f"monthly loss cap {mp:+.0f}"
    cl = consecutive_losses(ledger)
    if cl >= CONSECUTIVE_LOSS_PAUSE:
        reasons.append(f"{cl} consecutive losses"); pause = pause or f"{cl} consecutive losses"
    vo, vn = ctx.get("vix1d_open"), ctx.get("vix1d_now")
    if vn is None:
        reasons.append("VIX1D unavailable")
    else:
        if vn >= VIX1D_LEVEL_KILL:
            reasons.append(f"VIX1D {vn:.1f} >= {VIX1D_LEVEL_KILL}")
        if vo and vo > 0 and (vn / vo - 1) >= VIX1D_JUMP_KILL:
            reasons.append(f"VIX1D jump {vn / vo - 1:+.0%} vs open")
    fr = ctx.get("first30_range")
    if fr is None:
        reasons.append("first-30-min range unavailable")
    elif fr > FIRST30_RANGE_KILL:
        reasons.append(f"first-30 SPX range {fr:.2%} > {FIRST30_RANGE_KILL:.1%}")
    return (not reasons), reasons, pause


def flatten_now(ctx: dict) -> str | None:
    """Mid-session kill for an OPEN live position (independent of the stop): VIX1D jump."""
    vo, vn = ctx.get("vix1d_open"), ctx.get("vix1d_now")
    if vo and vn and vo > 0 and (vn / vo - 1) >= VIX1D_JUMP_KILL:
        return f"VIX1D jump {vn / vo - 1:+.0%} vs open"
    if ctx.get("halted"):
        return f"HALT: {ctx['halted']}"
    return None
