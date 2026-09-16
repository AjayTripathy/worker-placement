"""envelope_runner — principal-run executor for RATIFIED order envelopes.

RAIL CHANGE THIS IMPLEMENTS (2026-08-21, principal-directed). The house rail was per-order:
desk stages transmit=False, principal clicks each order in TWS. The principal has overridden it
to an ENVELOPE-LEVEL trigger: the principal ratifies an envelope once (in chat), then RUNS THIS
PROGRAM, and the program places that envelope's orders inside its coded gates. The trigger moves
from per-order to per-campaign; it remains HUMAN — this program is the principal's finger, run by
the principal, and the assistant never invokes it with live execution.

Context that shaped the design (same week): a foreign agent (antigravity_v2) transmitted 24 GTC
orders into this account from a table of confabulated prices with no tape check. The lesson was
not "no automation" — it was that the dangerous step is UNGATED TRANSMISSION, not automation.
So: every envelope's gates live in ITS OWN MODULE as code (price ceiling/floor, participation
cap, size target, tape-sanity refusal), the registry below controls WHAT may run, and this runner
controls WHEN. Foreign agents get no envelopes: entries carry `origin`, and anything not
"signalos_desk+principal" is refused at load.

The autonomy ladder's Rung-1 gates (Brier/TCA/integrity/shadow-month) are NOT met as of this
writing; the principal explicitly waived them for envelope #1 (SANYU-ACCUM) on 2026-08-21.
Fills continue feeding the TCA ledger as Rung-1 evidence either way.

    python3 -m desk.envelope_runner                # execute today's chunk for every ARMED envelope
    python3 -m desk.envelope_runner --dry-run      # plan only, place nothing
    python3 -m desk.envelope_runner --daemon       # stay up; run each Tokyo weekday ~08:46 JST
    python3 -m desk.envelope_runner --status
    python3 -m desk.envelope_runner --halt "why"   # halt all envelopes (also: touch desk/data/ENVELOPE_HALT)
    python3 -m desk.envelope_runner --resume
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import os
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REGISTRY = ROOT / "desk" / "data" / "envelopes.json"
HALT_FILE = ROOT / "desk" / "data" / "ENVELOPE_HALT"
LOCK = ROOT / "desk" / "data" / "envelope_runner.lock"
JST = ZoneInfo("Asia/Tokyo")


def _registry() -> dict:
    try:
        return json.loads(REGISTRY.read_text())
    except Exception:
        return {"envelopes": {}}


def _save(reg: dict) -> None:
    REGISTRY.write_text(json.dumps(reg, indent=1))


def _halted() -> str | None:
    if HALT_FILE.exists():
        return HALT_FILE.read_text().strip() or "ENVELOPE_HALT file present"
    return None


def _lock() -> bool:
    """Single instance. A lock whose pid is dead is stale and reclaimed — a crashed run must not
    disable the runner forever, and a live one must never double-place."""
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip())
            os.kill(pid, 0)
            return False                      # live instance exists
        except (ValueError, ProcessLookupError, PermissionError):
            pass                              # stale
    LOCK.write_text(str(os.getpid()))
    return True


def _unlock() -> None:
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass


def run_once(execute: bool = True) -> list[dict]:
    why = _halted()
    if why:
        print(f"[envelope_runner] HALTED — {why}. `--resume` or remove {HALT_FILE.name} to continue.")
        return []
    if not _lock():
        print("[envelope_runner] another instance is live — refusing to double-run")
        return []
    results = []
    try:
        reg = _registry()
        today = dt.datetime.now(JST).date().isoformat()
        for name, env in reg.get("envelopes", {}).items():
            if env.get("status") != "ARMED":
                print(f"[envelope_runner] {name}: {env.get('status')} — skipped")
                continue
            if env.get("origin") != "signalos_desk+principal":
                # The antigravity lesson as a load-time refusal, not a comment.
                print(f"[envelope_runner] {name}: origin {env.get('origin')!r} is not "
                      f"'signalos_desk+principal' — FOREIGN ENVELOPES DO NOT RUN")
                continue
            if env.get("expires") and today > env["expires"]:
                env["status"] = "EXPIRED"
                print(f"[envelope_runner] {name}: expired {env['expires']} — marked EXPIRED")
                continue
            try:
                mod = importlib.import_module(env["module"])
                res = mod.run(execute=execute)
                action = res.get("action")
                if action == "TARGET_REACHED":
                    env["status"] = "COMPLETE"
                    env["completed"] = today
                    print(f"[envelope_runner] {name}: TARGET REACHED — envelope COMPLETE")
                results.append({"envelope": name, "action": action, "executed": execute,
                                "tokyo_date": today})
            except Exception as e:
                # A failing envelope halts ITSELF, never the others; and it halts LOUD.
                env["status"] = "ERROR"
                env["error"] = f"{type(e).__name__}: {e}"
                print(f"[envelope_runner] {name}: ERRORED and self-halted — {env['error']}")
                results.append({"envelope": name, "action": "ERROR", "error": env["error"]})
        _save(reg)
    finally:
        _unlock()
    return results


def daemon() -> None:
    """Stay resident; run once per Tokyo weekday at ~08:46 JST (pre-open, joins the opening
    auction). Sleep/wake safe: checks the clock, never counts ticks."""
    print("[envelope_runner] daemon up — placing each Tokyo weekday ~08:46 JST. Ctrl-C to stop; "
          f"halt-switch: {HALT_FILE}")
    last_run_date = None
    while True:
        now = dt.datetime.now(JST)
        if (now.weekday() < 5 and now.hour == 8 and now.minute >= 46 and
                last_run_date != now.date()):
            print(f"[envelope_runner] {now.isoformat(timespec='minutes')} — running")
            run_once(execute=True)
            last_run_date = now.date()
        time.sleep(60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--daemon", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--halt", metavar="WHY")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    if a.halt:
        HALT_FILE.write_text(a.halt)
        print(f"[envelope_runner] HALTED: {a.halt}")
    elif a.resume:
        HALT_FILE.unlink(missing_ok=True)
        print("[envelope_runner] resumed")
    elif a.status:
        print(json.dumps(_registry(), indent=1))
        h = _halted()
        if h:
            print(f"HALTED: {h}")
    elif a.daemon:
        daemon()
    else:
        run_once(execute=not a.dry_run)
