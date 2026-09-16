"""sync — the asset sync / maintenance layer: truth upkeep for the Office.

Finance storage is fragmented; every institution is another interface. The ruling
(principal, 2026-09-02): **interface what we need, and let integrations compound**
— a new institution is a new registered connector + a test, never an engine edit.
This is the effects-registry law applied to custody.

A connector is a function registered with @connector(...) whose fetch returns a
SNAPSHOT (or raises — failures NEVER pass silently):

    {"as_of": "YYYY-MM-DD",
     "provenance": "human-readable source note",
     "updates": [
        {"match": {"category": "..."} and/or {"name_contains": "..."},
         "value": <float>,            # new sleeve value
         "holdings": [...]           # optional holdings refresh
        }, ...]}

sync.run() fetches every registered connector; sync.apply() writes matching
sleeve values IN MEMORY at render time (the JSON balance sheet stays the manual
base layer; sync is a live overlay, and every touched sleeve carries a `sync`
stamp — connector id, as_of, provenance, SLA — that the office renders as a
freshness badge). Staleness math: age > max_age_days => STALE, and the report
row for a failed connector is ERROR, not an absent line. Degrade LOUD.

The engine stays pure: this module defines only the contract, the registry, the
application, and the freshness math. Connectors live with the deployment — the
desk registers its private ones (IBKR, Parametric); the OSS package ships the
generic file-based ones. That per-institution long tail is the compounding asset.
"""
from __future__ import annotations

from datetime import date, datetime

REGISTRY = {}          # id -> fetch fn (with .meta)


def connector(id, label, kind="positions", max_age_days=3):
    """Register a custody connector. fetch() -> snapshot dict (see module doc)."""
    def deco(fn):
        fn.meta = {"id": id, "label": label, "kind": kind, "max_age_days": max_age_days}
        REGISTRY[id] = fn
        return fn
    return deco


def _age_days(as_of, today):
    try:
        d = datetime.strptime(str(as_of)[:10], "%Y-%m-%d").date()
        return (today - d).days
    except Exception:
        return None


def run(ids=None):
    """Fetch every (or the named) registered connector. Returns a list of
    {"meta", "snapshot"|None, "error"|None} — an exception becomes an ERROR row
    downstream, never a silent absence."""
    out = []
    for cid, fn in REGISTRY.items():
        if ids is not None and cid not in ids:
            continue
        try:
            out.append({"meta": fn.meta, "snapshot": fn(), "error": None})
        except Exception as e:
            out.append({"meta": fn.meta, "snapshot": None, "error": f"{type(e).__name__}: {e}"})
    return out


def _match(sleeve, match):
    if "category" in match and sleeve.get("category") != match["category"]:
        return False
    if "name_contains" in match and match["name_contains"] not in sleeve.get("name", ""):
        return False
    return bool(match)


def apply(data, fetched, today=None):
    """Apply fetched snapshots to data['sleeves'] in memory. Returns a report:
    one row per connector {connector, label, status FRESH|STALE|ERROR, as_of,
    age_days, detail}, plus a WARN row per update that matched no sleeve."""
    today = today or date.today()
    report = []
    for f in fetched:
        meta = f["meta"]
        if f["error"]:
            report.append({"connector": meta["id"], "label": meta["label"], "status": "ERROR",
                           "as_of": None, "age_days": None, "detail": f["error"]})
            continue
        snap = f["snapshot"]
        age = _age_days(snap.get("as_of"), today)
        status = "FRESH" if (age is not None and age <= meta["max_age_days"]) else "STALE"
        touched = []
        for upd in snap.get("updates", []):
            hit = next((s for s in data["sleeves"] if _match(s, upd.get("match", {}))), None)
            if hit is None:
                report.append({"connector": meta["id"], "label": meta["label"], "status": "WARN",
                               "as_of": snap.get("as_of"), "age_days": age,
                               "detail": f"no sleeve matched {upd.get('match')}"})
                continue
            if upd.get("value") is not None:
                hit["value"] = round(float(upd["value"]))
            if upd.get("holdings") is not None:
                hit["holdings"] = upd["holdings"]
            hit["sync"] = {"connector": meta["id"], "as_of": snap.get("as_of"),
                           "provenance": snap.get("provenance", meta["label"]),
                           "max_age_days": meta["max_age_days"]}
            touched.append(hit["name"])
        report.append({"connector": meta["id"], "label": meta["label"], "status": status,
                       "as_of": snap.get("as_of"), "age_days": age,
                       "detail": "updated: " + ", ".join(touched) if touched else "no updates"})
    return report


def stamp_freshness(sleeves, today=None):
    """Annotate synced sleeves in place with _sync_age / _sync_stale from their
    stamps; returns (n_synced, n_stale)."""
    today = today or date.today()
    n = stale = 0
    for s in sleeves:
        st = s.get("sync")
        if not st:
            continue
        n += 1
        age = _age_days(st.get("as_of"), today)
        s["_sync_age"] = age
        s["_sync_stale"] = age is None or age > st.get("max_age_days", 3)
        stale += 1 if s["_sync_stale"] else 0
    return n, stale
