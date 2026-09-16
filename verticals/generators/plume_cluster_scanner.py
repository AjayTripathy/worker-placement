"""plume_cluster_scanner — Stage 0b generator: METHANE SUPER-EMITTER clusters (Carbon Mapper, instrument truth).

Inverts the carbon_mapper verifier: instead of checking a named facility's claim, pull ALL recent annotated
plumes and cluster them geographically (0.5-degree cells ~ basin resolution). A dense new cluster = operators
with environmental-liability/enforcement exposure (short/avoid seeds) or, inverted, evidence of activity levels.
Operator attribution is the SignalOS mapping step (facility -> operator via state well registries); the
deterministic layer reports WHERE and HOW MUCH.

  python3 verticals/generators/plume_cluster_scanner.py [--days 60]
Writes data/PLUME_CLUSTERS.json. Free non-commercial API. READ-ONLY.
"""
from __future__ import annotations
import json, datetime, argparse, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "PLUME_CLUSTERS.json"
API = "https://api.carbonmapper.org/api/v1/catalog/plumes/annotated"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}


def _fetch(days: int) -> list[dict]:
    since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    out, offset = [], 0
    while offset < 4000:
        q = urllib.parse.urlencode({"limit": 500, "offset": offset, "datetime": f"{since}T00:00:00Z/.."})
        try:
            req = urllib.request.Request(f"{API}?{q}", headers=HDRS)
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
        except Exception:
            break
        items = d.get("items", d.get("features", []))
        if not items:
            break
        out.extend(items)
        offset += 500
        if len(items) < 500:
            break
    return out


def scan(days: int) -> dict:
    plumes = _fetch(days)
    cells = {}
    for p in plumes:
        geom = p.get("geometry_json") or p.get("geometry") or {}
        coords = geom.get("coordinates") or [None, None]
        lon, lat = (coords + [None, None])[:2]
        if lon is None:
            continue
        emis = p.get("emission_auto") or p.get("emission") or 0
        sector = (p.get("sector") or "")[:20]
        cell = f"{round(lat * 2) / 2:.1f},{round(lon * 2) / 2:.1f}"
        c = cells.setdefault(cell, {"lat": round(lat, 1), "lon": round(lon, 1), "n": 0, "kghr": 0.0, "sectors": {}})
        c["n"] += 1
        c["kghr"] += emis or 0
        c["sectors"][sector] = c["sectors"].get(sector, 0) + 1
    rows = [{"cell": k, "lat": v["lat"], "lon": v["lon"], "plumes": v["n"], "total_kg_hr": round(v["kghr"]),
             "top_sector": max(v["sectors"], key=v["sectors"].get) if v["sectors"] else ""}
            for k, v in cells.items() if v["n"] >= 3]
    rows.sort(key=lambda r: -r["total_kg_hr"])
    return {"asof": datetime.date.today().isoformat(), "window_days": days, "n_plumes": len(plumes),
            "n_clusters": len(rows), "clusters": rows[:20],
            "note": "operator attribution = SignalOS mapping step (state well registries / facility DBs); free tier non-commercial"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60)
    a = ap.parse_args()
    res = scan(a.days)
    print(f"=== METHANE PLUME-CLUSTER SCANNER  {res['asof']}  ({res['n_plumes']} plumes, {res['n_clusters']} clusters >=3 plumes, {res['window_days']}d) ===")
    for r in res["clusters"][:12]:
        print(f"   {r['cell']:<14} {r['plumes']:>3} plumes  {r['total_kg_hr']:>8,} kg/hr  {r['top_sector']}")
    print("  PROMOTE: SignalOS attributes dense NEW clusters to operators -> enforcement/liability seeds.")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
