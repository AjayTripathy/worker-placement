"""pipeline_metrics — computes the PRD success-metric set (PIPELINE_PRD.md) into a
history-keeping store. One snapshot row per run day (merge by date); served at
/api/pipeline_metrics and consumed by pipeline_monitor's weekly digest.

  python3 -m desk.pipeline_metrics          # compute + persist + print
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

from desk.store import Store, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "desk" / "data"
OUT = Store("desk/data/pipeline_metrics.json", schema="pipeline_metrics",
            list_path="snapshots", key=lambda s: s["date"])


def _load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _norm(sym: str) -> str:
    return re.split(r"[.\s]", str(sym or "").strip())[0].upper()


# ---------------- P1: orphan verification ----------------
def p1_metrics() -> dict:
    rl = _load(DATA / "research_ledger.json") or {}
    packs = (_load(DATA / "resolution_packs.json") or {}).get("packs", {})
    today = datetime.date.today().isoformat()
    future_fams = set()
    for key in packs:
        if "|" in key:
            name, d = key.rsplit("|", 1)
            if re.match(r"\d{4}-\d{2}-\d{2}$", d) and d >= today:
                future_fams.add(_norm(re.sub(r"-[A-Z]+$", "", name)))
    watch = [n for n in rl.get("names", [])
             if str(n.get("verdict", "")).upper().startswith(("WATCH", "STAGE2"))]
    wired = sum(1 for n in watch if _norm(n["ticker"]) in future_fams)
    # batch advance rates from the trap-batch docs (## header verdict grep)
    batches = {}
    vpat = re.compile(r"^## .+?\([A-Z0-9.\-]+.*?\*\*(.+?)\*\*", re.M)
    for doc in ROOT.glob("verticals/*/global/data/*TRAP_BATCH*.md"):
        v = vpat.findall(doc.read_text())
        if v:
            adv = sum(1 for x in v if "REAL" in x.upper() and "TRAP" not in x.upper().split("REAL")[0][-8:])
            batches[doc.stem] = {"n": len(v), "advance": adv, "advance_rate": round(adv / len(v), 2)}
    defects = read_jsonl(DATA / "screen_defects.jsonl") if (DATA / "screen_defects.jsonl").exists() else []
    open_defects = [d for d in defects if d.get("status") == "open"]
    # net open: an open row is cleared by a later fix_landed row naming its fragment
    fixed_frags = " ".join(d.get("defect", "") for d in defects if d.get("status") == "fix_landed")
    net_open = [d for d in open_defects
                if not any(w in fixed_frags for w in d["defect"][:30].split()[:3])]
    return {
        "watch_count": len(watch), "watch_wired": wired,
        "watch_wired_pct": round(100 * wired / len(watch), 1) if watch else None,
        "batches": batches,
        "defects_open": len(net_open), "defects_total": len(defects),
    }


# ---------------- P2: class dislocation (detector not yet built — report absence honestly) ----------------
def p2_metrics() -> dict:
    ev = _load(DATA / "class_dislocation_events.json")
    events = (ev or {}).get("events", [])
    if not ev:
        built = (ROOT / "desk" / "class_dislocation.py").exists()
        return {"status": "live_no_events" if built else "detector_not_built", "events": 0}
    tri = [e for e in events if e.get("triaged_utc")]
    unanchored = [e for e in events if e.get("narrative_anchor") == "UNEXPLAINED"]
    return {"status": "live", "events": len(events), "triaged": len(tri),
            "unanchored": len(unanchored)}


# ---------------- P3: trigger conversion ----------------
def p3_metrics() -> dict:
    packs = (_load(DATA / "resolution_packs.json") or {}).get("packs", {})
    resolved = set()
    lat = []
    cal = DATA / "calibration_ledger.jsonl"
    if cal.exists():
        for line in cal.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(r.get("status", "")).upper() in ("RESOLVED", "VOID", "VOIDED"):
                resolved.add((_norm(r.get("ticker", "")), str(r.get("cat_date", ""))))
                rd = (r.get("resolution") or {}).get("date")
                if rd and r.get("cat_date"):
                    try:
                        lat.append((datetime.date.fromisoformat(rd)
                                    - datetime.date.fromisoformat(r["cat_date"])).days)
                    except ValueError:
                        pass
    today = datetime.date.today()
    past = stale = 0
    for key, p in packs.items():
        if "|" not in key or not isinstance(p, dict):
            continue
        name, d = key.rsplit("|", 1)
        if not re.match(r"\d{4}-\d{2}-\d{2}$", d) or d >= today.isoformat():
            continue
        past += 1
        fam = _norm(re.sub(r"-[A-Z]+$", "", name))
        ok = (p.get("lifecycle") in ("adjudicated", "branch_executed", "expired")
              or any(k.startswith("graded_") for k in p)
              or any(rf == fam and abs((datetime.date.fromisoformat(d)
                                        - datetime.date.fromisoformat(rd)).days) <= 5
                     for rf, rd in resolved if re.match(r"\d{4}-\d{2}-\d{2}$", rd)))
        stale += 0 if ok else 1
    lat.sort()
    p90 = lat[int(len(lat) * 0.9)] if lat else None
    # unclassified held cost
    pc = _load(ROOT / "desk" / "ui" / "data" / "positions_cache.json") or {}
    board = _load(ROOT / "desk" / "ui" / "static" / "positions_board.json") or {}
    ec_dir = DATA / "edge_classifications"
    fx = board.get("fx", {})
    uncls_cost = 0.0
    uncls = []
    for p_ in pc.get("positions", []):
        if p_.get("sec_type") != "STK" or float(p_.get("qty") or 0) <= 0:
            continue
        fam = _norm(p_["symbol"])
        if fam == "SGOV":
            continue
        if not ((ec_dir / f"{p_['symbol']}.json").exists() or (ec_dir / f"{fam}.json").exists()
                or list(ec_dir.glob(f"{fam}[._]*.json"))):
            avg = p_.get("avg_cost_per_unit") or p_.get("avg_cost") or 0
            uncls_cost += avg * p_["qty"] * fx.get(p_.get("ccy", "USD"), 1.0)
            uncls.append(p_["symbol"])
    return {"packs_total": len(packs), "packs_past_date": past, "packs_stale": stale,
            "adjudication_p90_days": p90, "graded_n": len(lat),
            "unclassified_held": uncls, "unclassified_cost_usd": round(uncls_cost)}


# ---------------- cross-cutting ----------------
def cross_metrics() -> dict:
    q = _load(DATA / "unwired_tripwires.json") or {}
    b = _load(ROOT / "desk" / "ui" / "static" / "positions_board.json") or {}
    age_h = None
    try:
        gen = b.get("generated_utc", "").rstrip("Z")
        age_h = round((datetime.datetime.utcnow()
                       - datetime.datetime.fromisoformat(gen)).total_seconds() / 3600, 1)
    except ValueError:
        pass
    return {"unwired_strict": len(q.get("strict", [])), "unwired_tail": len(q.get("tail", [])),
            "positions_board_age_h": age_h}


def snapshot() -> dict:
    return {"date": datetime.date.today().isoformat(),
            "p1": p1_metrics(), "p2": p2_metrics(), "p3": p3_metrics(),
            "cross": cross_metrics()}


def main():
    s = snapshot()
    counts = OUT.upsert([s], generated_by="pipeline_metrics")
    print(f"[pipeline_metrics] {s['date']}: "
          f"P1 wired {s['p1']['watch_wired']}/{s['p1']['watch_count']} "
          f"({s['p1']['watch_wired_pct']}%), defects open {s['p1']['defects_open']} | "
          f"P2 {s['p2']['status']} | "
          f"P3 stale packs {s['p3']['packs_stale']}/{s['p3']['packs_past_date']}, "
          f"unclassified ${s['p3']['unclassified_cost_usd']:,} "
          f"({len(s['p3']['unclassified_held'])} names) | "
          f"unwired {s['cross']['unwired_strict']}+{s['cross']['unwired_tail']} "
          f"[{counts['added']} added / {counts['updated']} updated]")
    return s


if __name__ == "__main__":
    main()
