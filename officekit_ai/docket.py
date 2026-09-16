"""docket — the court-on-touch conveyor, promoted (F2 final piece, 2026-09-05).

The desk's court_queue proved the shape: screens and watchers ENQUEUE candidates,
a drain CONVENES the court, and nothing surfaced by machinery ever grades itself.
This is the tenant-generic promotion — one docket file per office folder, drained
through run_court (RED/BLUE benches + adjudicator via the BYOM slots, evidence
packs when a contact is available).

Invariants carried over from the desk rail:
  - enqueue is IDEMPOTENT per (symbol, strategy): an open docket item dedupes,
    and a (symbol, strategy) pair that already holds an adjudication is refused
    unless recourt=True (a re-court is a deliberate act, never a side effect)
  - the drain is BUDGETED (max_dispatch) so a full docket never burns unbounded
    tokens; errors mark the item ERROR with the reason and the drain continues
    (degrade loud, never silently skip)
  - a DONE item records the adjudication id — the docket is an audit trail,
    not a scratch list

READ-ONLY with respect to positions: a docket verdict feeds the strategy page's
decision surfaces; it never places orders.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

STATUSES = ("QUEUED", "DONE", "ERROR", "KILLED")


def _path(folder):
    return Path(folder) / "docket.json"


def load_docket(folder):
    p = _path(folder)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text()).get("items", [])
    except Exception:
        return []


def _save(folder, items):
    _path(folder).write_text(json.dumps(
        {"updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "items": items}, indent=1))


def _adjudicated_pairs(folder):
    from officekit_ai.court import load_adjudications
    return {(r.get("symbol", "").upper(), r.get("strategy"))
            for r in load_adjudications(folder) if r.get("subject_kind", "security") == "security"}


from officekit.office_lock import transaction

@transaction()
def enqueue(folder, symbol, strategy_id, source, context=None, recourt=False):
    """Queue one candidate for one strategy's court. Returns the item, or None
    when refused (already open, or already adjudicated without recourt)."""
    symbol = str(symbol).upper()
    items = load_docket(folder)
    for it in items:
        if (it["symbol"] == symbol and it["strategy"] == strategy_id
                and it["status"] == "QUEUED"):
            return None                                   # already awaiting court
    if not recourt and (symbol, strategy_id) in _adjudicated_pairs(folder):
        return None                                       # verdict exists — re-court is deliberate
    item = {"id": str(uuid.uuid4()), "symbol": symbol, "strategy": strategy_id,
            "source": source, "context": context, "status": "QUEUED",
            "enqueued_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "history": []}
    items.append(item)
    _save(folder, items)
    return item


def pending(folder, strategy_id=None):
    items = [i for i in load_docket(folder) if i["status"] == "QUEUED"]
    return [i for i in items if i["strategy"] == strategy_id] if strategy_id else items


@transaction()
def kill(folder, item_id, note=None):
    """Withdraw a queued item without convening (a decline is knowledge — the
    note records why)."""
    items = load_docket(folder)
    for it in items:
        if it["id"] == item_id and it["status"] == "QUEUED":
            it["status"] = "KILLED"
            it["history"].append({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "note": note or "killed before court"})
            _save(folder, items)
            return it
    return None


@transaction()
def drain(folder, personal_context, decisions=None, lib=None, clients=None,
          today=None, office_data=None, contact=None, max_dispatch=4):
    """Convene courts for up to max_dispatch queued items, oldest first.
    `decisions`: {strategy_id: decision-dict} so the court sees the mandate it
    serves (contract #5 rows); an unknown strategy still convenes with a bare
    context rather than stalling the conveyor. Returns the drain log."""
    from officekit_ai.court import run_court
    decisions = decisions or {}
    items = load_docket(folder)
    queue = sorted((i for i in items if i["status"] == "QUEUED"),
                   key=lambda i: i["enqueued_utc"])
    log = []
    from officekit.api_errors import report, clear
    for it in queue[:max_dispatch]:
        decision = decisions.get(it["strategy"], {"status": "considering"})
        try:
            rec = run_court(it["symbol"], it["strategy"], decision,
                            personal_context, folder, lib=(lib or {}).get(it["strategy"]),
                            clients=clients, today=today, context=it.get("context"),
                            office_data=office_data, contact=contact)
            it["status"] = "DONE"
            clear(folder, context='court:' + it['id'])
            it["adjudication_id"] = rec["id"]
            it["history"].append({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "note": f"adjudicated {rec['verdict']}"})
            log.append(f"{it['symbol']} [{it['strategy']}]: {rec['verdict']}")
        except Exception as e:
            it["status"] = "ERROR"
            report(folder, 'court:' + it['id'], 'Court review failed', e,
                   href='/pages/strategies.html')
            it["history"].append({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "note": f"{type(e).__name__}: {e}"})
            log.append(f"{it['symbol']} [{it['strategy']}]: ERROR {type(e).__name__}: {e}")
    _save(folder, items)
    return log


@transaction()
def requeue_errors(folder):
    """Flip ERROR items back to QUEUED (after an infra outage). Returns count."""
    items = load_docket(folder)
    n = 0
    for it in items:
        if it["status"] == "ERROR":
            it["status"] = "QUEUED"
            it["history"].append({"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "note": "requeued after error"})
            n += 1
    if n:
        _save(folder, items)
    return n
