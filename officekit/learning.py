"""learning — the loop's learning edge: an append-only local outcome ledger.

Ruling (principal, 2026-09-02): learning is LOCAL-FIRST, but the record contract
is multi-tenant from day one. Every record carries a schema version and a tenant
id, and payloads are BORN SHAREABLE — category weights, betas, ratios, statuses,
an order-of-magnitude bucket — never names, never dollars, never tickers. A
larger system learning across many clients consumes these same records; going
multi-tenant is a transport decision (opt-in phone-home), not a schema migration.

Record kinds (v1):
  snapshot      daily balance-sheet fingerprint: category weights (% of gross),
                aggregate factor betas, net-worth DECADE (log10 bucket, not the
                number), sleeve count, sync freshness counts
  scenario_run  the planner's per-scenario drawdown predictions (dd %) — the
                graded-call seam: after a real drawdown, realized-vs-predicted
                is the calibration grade
  goal_status   per-goal {kind, status, ratio} at baseline — status transitions
                over time are the product's own outcome metric
  agent_call    a frozen intelligence-plugin call (ratified 2026-09-04):
                capability, model, and the claim made — the record id is the
                `ref` in any agent-origin mandate, so every proposal points at
                the exact call that argued for it. Gradeable like scenario
                predictions. NOT in the shareable allowlist: payloads may
                contain client-specific text.

observe() writes at most one record per kind per day (idempotent under an hourly
render loop). export_shareable() is the ONLY sanctioned exit path for records;
a test asserts nothing personal survives it.
"""
from __future__ import annotations

import json
import math
import time
import uuid
from datetime import date
from pathlib import Path

SCHEMA_V = 1


def _read(ledger_path):
    p = Path(ledger_path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


from officekit.office_lock import transaction

@transaction("ledger_path", parent=True)
def record(ledger_path, kind, payload, tenant="local", today=None, office_id=None):
    """Append one record. Every record carries a per-record `id` (upload dedupe)
    and the office's `office_id` (multitenant attribution). Returns the record."""
    rec = {"v": SCHEMA_V, "id": str(uuid.uuid4()), "tenant": tenant,
           "office_id": office_id, "kind": kind,
           "date": (today or date.today()).isoformat(),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "payload": payload}
    p = Path(ledger_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def _already(ledger_path, kind, day):
    return any(r.get("kind") == kind and r.get("date") == day for r in _read(ledger_path))


def observe(m, ledger_path, results=None, tenant="local", today=None):
    """Record today's snapshot (+ scenario predictions and goal statuses when
    available). One record per kind per day; re-runs are no-ops. Returns the
    kinds written."""
    today = today or date.today()
    day = today.isoformat()
    office_id = m["d"].get("office_id")
    written = []

    if not _already(ledger_path, "snapshot", day):
        gross = sum(s["value"] for s in m["assets"]) or 1
        weights = {}
        for s in m["assets"]:
            weights[s["category"]] = round(weights.get(s["category"], 0) + s["value"] / gross * 100, 1)
        payload = {"cat_weights": weights,
                   "agg_beta": {f: round(b, 2) for f, b in m["agg"].items()},
                   "nw_decade": int(math.log10(max(abs(m["NW"]), 1))),
                   "n_sleeves": len(m["sleeves"]),
                   "sync": {"n": m.get("sync_n", 0), "stale": m.get("sync_stale", 0)}}
        record(ledger_path, "snapshot", payload, tenant, today, office_id)
        written.append("snapshot")

    if results is not None and not _already(ledger_path, "scenario_run", day):
        payload = {"dd_pct": {r["sc"]["key"]: round(r["dd_pct"], 2) for r in results},
                   "p": {r["sc"]["key"]: r["sc"]["p"] for r in results if r["sc"].get("p")},
                   "worst": results[0]["sc"]["key"]}
        record(ledger_path, "scenario_run", payload, tenant, today, office_id)
        written.append("scenario_run")

    goals = m["d"].get("goals") or []
    if goals and not _already(ledger_path, "goal_status", day):
        from officekit.goals import evaluate, investable
        base_inv = investable([(s, 0.0) for s in m["sleeves"]])
        base_liq = (sum(s["value"] for s in m["assets"] if s["category"] == "cash")
                    + sum(s["value"] for s in m["assets"]
                          if s["category"] in ("public_equity", "direct_index", "single_name_equity",
                                               "municipal_credit", "fixed_income", "alpha_market_neutral")) * 0.98)
        evs = [evaluate(g, base_inv, base_liq, m["d"].get("as_of", day)) for g in goals]
        payload = {"goals": [{"i": i, "id": g.get("id"), "kind": e["kind"],
                              "status": e["status"], "ratio": round(e["ratio"], 2)}
                             for i, (g, e) in enumerate(zip(goals, evs))]}
        record(ledger_path, "goal_status", payload, tenant, today, office_id)
        written.append("goal_status")
    return written


# fields a shareable record may carry, per kind — the allowlist IS the contract
_SHAREABLE = {"snapshot": {"cat_weights", "agg_beta", "nw_decade", "n_sleeves", "sync"},
              "scenario_run": {"dd_pct", "p", "worst"},
              "goal_status": {"goals"}}


def export_shareable(ledger_path, tenant=None):
    """The only sanctioned exit path for phone-home: records filtered to the
    per-kind field allowlist. Anything not on the allowlist never leaves,
    whatever a future record writer added."""
    out = []
    for r in _read(ledger_path):
        allow = _SHAREABLE.get(r.get("kind"))
        if not allow:
            continue
        out.append({"v": r["v"], "id": r.get("id"),
                    "tenant": tenant or r.get("tenant", "local"),
                    "office_id": r.get("office_id"),
                    "kind": r["kind"], "date": r["date"],
                    "payload": {k: v for k, v in r.get("payload", {}).items() if k in allow}})
    return out
