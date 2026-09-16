"""catalyst_action — close the loop from a graded catalyst to its PRE-REGISTERED ACTION, fast.

Born 2026-07-10: BKE's June comp printed, the call graded FAVORABLE, but the pre-registered
"positive comp -> add" action sat in a PROSE field and nothing surfaced/staged it — so we acted
the next morning AFTER a ~2% pop instead of at the print. Detection + grading closed; the ACTION
loop was never built. For MFT/INFO nowcasts the edge IS latency (beat the analyst), so a slow
action doesn't just cost slippage — it erases the edge. Target: action ARMED within a 30-MIN SLA
of the print.

Design:
  - Actions are REGISTERED in catalyst_action_registry.json, keyed by ticker (+event_type), with
    {anchor, favorable:{do,plan}, unfavorable:{do,plan}}. Kept OUT of the append-only calibration
    ledger (the PROBABILITY is frozen at prediction; the PLAN is registered/updated here).
  - On resolution, match outcome -> action, ARM it (catalyst_actions.json) + fire a loud push alert.
    Idempotent (one arm per ticker+cat_date). calibration.resolve() calls this the instant a call
    resolves, so arming is immediate; the morning brief surfaces ARMED actions at the TOP.
  - The anchor keeps a LATE action disciplined: entries anchor to the PRE-CATALYST close, never the
    post-print pop — if price already ran past the anchor, STAND DOWN, don't chase.
  - SLA: MFT/INFO actions carry sla_min=30. `--check` flags any ARMED action older than its SLA and
    still unexecuted (a nag: you're burning the latency edge). Grade->arm is instant here; the SLA
    is really on the upstream DETECT->GRADE (see print_radar) + the human's stage->submit.

    python3 -m desk.catalyst_action           # scan resolved calls, arm new actions + alert
    python3 -m desk.catalyst_action --check   # report ARMED-but-unexecuted actions past SLA
READ-ONLY on markets; it surfaces/stages a plan, it never submits.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "desk" / "data"
CALIB = D / "calibration_ledger.jsonl"
REGISTRY = D / "catalyst_action_registry.json"
QUEUE = D / "catalyst_actions.json"
PENDING = D / "pending_grades.json"   # headless grader's PROPOSED (unconfirmed) grades

# default execution SLA by skill class — MFT/INFO is latency-critical
SLA_MIN = {"INFO": 30, "FLOW": 30}
DEFAULT_SLA = 120


def _notify(msg: str):
    try:
        from desk.gauntlet_sentinel import _notify as n
        n(msg)
    except Exception:
        print(f"[catalyst_action] NOTIFY: {msg}")


def _registry():
    try:
        return json.loads(REGISTRY.read_text()).get("actions", {})
    except Exception:
        return {}


def _resolved_calls():
    """Latest RESOLVED record per (ticker, cat_date)."""
    seen = {}
    if not CALIB.exists():
        return []
    for line in CALIB.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if (r.get("status") or "").upper() == "RESOLVED":
            seen[(r.get("ticker"), r.get("cat_date"))] = r
    return list(seen.values())


def _proposed():
    """Headless grader's AWAITING_CONFIRM proposals — the PROPOSED (unconfirmed) grades."""
    try:
        return [p for p in json.loads(PENDING.read_text()).get("proposals", [])
                if p.get("status") == "AWAITING_CONFIRM"]
    except Exception:
        return []


def _sources():
    """Unified grade signals keyed (ticker, cat_date): a PROPOSED grade (fast, unconfirmed) or a
    CONFIRMED resolution. CONFIRMED wins — so a provisional arm upgrades in place when it confirms."""
    out = {}
    for p in _proposed():
        out[(p.get("ticker"), p.get("cat_date"))] = {
            "outcome": (p.get("proposed_outcome") or "").upper(), "grade_status": "PROPOSED",
            "our_p": p.get("our_p"), "px": None, "when": p.get("graded_on")}
    for r in _resolved_calls():
        res = r.get("resolution") or {}
        if isinstance(res, str):    # legacy hand-resolved records carried a bare outcome string
            res = {"outcome": res}
        elif not isinstance(res, dict):
            res = {}
        out[(r.get("ticker"), r.get("cat_date"))] = {
            "outcome": (res.get("outcome") or "").upper(), "grade_status": "CONFIRMED",
            "our_p": r.get("our_p"), "px": res.get("px_at_resolve"), "when": res.get("date")}
    return out


def _branch(act, outcome):
    b = act.get("favorable") if outcome == "FAVORABLE" else act.get("unfavorable") if outcome == "UNFAVORABLE" else None
    return b or {"do": "REVIEW", "plan": f"Resolved {outcome or 'MIXED'} — adjudicate the action manually."}


def _load_queue():
    try:
        return json.loads(QUEUE.read_text())
    except Exception:
        return {"actions": []}


def _sla_for(action, r):
    from desk.strategy_book import EVENT_CLASS
    cls = EVENT_CLASS.get(action.get("event_type") or r.get("event_type"), None)
    return SLA_MIN.get(cls, DEFAULT_SLA)


def arm(now_iso=None):
    """Arm actions off the fastest available grade. A PROPOSED grade (headless, ~within the hour)
    arms PROVISIONALLY so the plan surfaces at the print; a CONFIRMED grade upgrades it in place.
    This is the 30-min unlock: the action no longer waits for a human to confirm the grade."""
    now_iso = now_iso or datetime.datetime.now().isoformat(timespec="seconds")
    reg = _registry()
    q = _load_queue()
    idx = {(a["ticker"], a["cat_date"]): a for a in q["actions"]}
    fired, upgraded = [], []
    for (tk, cd), g in _sources().items():
        act = reg.get(tk)
        if not act:
            continue
        if act.get("calibration_only"):
            continue   # auto-CONFIRMS for the calibration cohort (via the grader) but arms NO trade action
        existing = idx.get((tk, cd))
        if existing:
            if existing.get("grade_status") == "PROPOSED" and g["grade_status"] == "CONFIRMED":
                br = _branch(act, g["outcome"])
                existing.update({"grade_status": "CONFIRMED", "outcome": g["outcome"], "do": br.get("do"),
                                 "plan": br.get("plan"), "px_at_resolve": g["px"], "resolved_at": g["when"],
                                 "confirmed_at": now_iso})
                upgraded.append(existing)
            continue
        br = _branch(act, g["outcome"])
        rec = {"ticker": tk, "cat_date": cd, "event_type": act.get("event_type"),
               "outcome": g["outcome"], "grade_status": g["grade_status"], "do": br.get("do"),
               "plan": br.get("plan"), "anchor": act.get("anchor"), "our_p": g["our_p"],
               "px_at_resolve": g["px"], "resolved_at": g["when"] if g["grade_status"] == "CONFIRMED" else None,
               "armed_at": now_iso, "sla_min": _sla_for(act, {}), "status": "ARMED"}
        q["actions"].append(rec)
        idx[(tk, cd)] = rec
        fired.append(rec)
    if fired or upgraded:
        QUEUE.write_text(json.dumps(q, indent=1))
    for rec in fired:
        prov = " (PROVISIONAL — grade proposed, not yet confirmed)" if rec["grade_status"] == "PROPOSED" else ""
        _notify(f"⚡ CATALYST ACTION ARMED [{rec['do']} · SLA {rec['sla_min']}m]{prov} — {rec['ticker']} "
                f"{rec['outcome']} (our_p {rec['our_p']}). {rec['plan'][:200]}")
    for rec in upgraded:
        _notify(f"✓ ACTION GRADE CONFIRMED — {rec['ticker']} {rec['outcome']} ({rec['do']}); execute within SLA.")
    return fired


def check(now=None):
    """ARMED-but-unexecuted actions older than their SLA — the latency-edge nag."""
    now = now or datetime.datetime.now()
    q = _load_queue()
    breaches = []
    for a in q["actions"]:
        if a.get("status") != "ARMED":
            continue
        try:
            armed = datetime.datetime.fromisoformat(a["armed_at"])
        except Exception:
            continue
        age = (now - armed).total_seconds() / 60.0
        if age > a.get("sla_min", DEFAULT_SLA):
            breaches.append((round(age), a))
    return breaches


def pending():
    return [a for a in _load_queue()["actions"] if a.get("status") == "ARMED"]


def main():
    if "--check" in sys.argv:
        br = check()
        if br:
            msg = "; ".join(f"{a['ticker']} {a['do']} ARMED {age}m ago (SLA {a['sla_min']}m) — EXECUTE or stand down" for age, a in br)
            _notify("⏱ ACTION SLA BREACH: " + msg[:800])
            print("[catalyst_action] SLA breaches:", msg)
        else:
            print("[catalyst_action] no SLA breaches")
        return
    fired = arm()
    print(f"[catalyst_action] armed {len(fired)} new action(s)" + (": " + ", ".join(f"{r['ticker']}:{r['do']}" for r in fired) if fired else ""))


if __name__ == "__main__":
    main()
