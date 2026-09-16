"""diagnostics — the desk's self-interrogation page (standing goal, 2026-07-07).

Collects the live status of EVERY subsystem — launchd jobs, the cron heartbeat,
all registry watches, the sentinel's inline watchers + their state files, the
UI server, resolution packs, the calibration ledger — grades each green /
yellow / red by staleness-vs-cadence and error markers, and renders both
desk/ui/data/diagnostics.json and desk/ui/static/diag.html (the DIAG tab).

    python3 -m desk.diagnostics
Registered hourly on the desk heartbeat; also runnable any time. READ-ONLY.
"""
from __future__ import annotations

import datetime
import html
import json
import re
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "desk" / "ui" / "data" / "diagnostics.json"
OUT_HTML = ROOT / "desk" / "ui" / "static" / "diag.html"

# staleness thresholds (hours) by cadence; weekend-tolerant
THRESH = {"hourly": 3, "daily": 30, "weekday": 78, "weekly": 8 * 24, "heartbeat": 3}
ERR_MARKERS = ("failed:", "Traceback", "ERR ", "Error:", "timed out")


def _age_h(p: Path) -> float | None:
    try:
        return (time.time() - p.stat().st_mtime) / 3600
    except Exception:
        return None


def _grade(age_h, cadence, err=False):
    if err:
        return "RED"
    if age_h is None:
        return "RED"
    lim = THRESH.get(cadence, 30)
    if age_h <= lim:
        return "GREEN"
    if age_h <= lim * 2:
        return "YELLOW"
    return "RED"


def collect() -> dict:
    now = datetime.datetime.now().isoformat(timespec="minutes")
    d = {"asof": now, "sections": {}}

    # 1) launchd jobs
    jobs = []
    try:
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
        for ln in out.splitlines():
            if "signalos" in ln:
                pid, status, label = (ln.split("\t") + ["", "", ""])[:3]
                running = pid.strip() != "-"
                ok = running or status.strip() in ("0", "-15")
                jobs.append({"name": label.strip(), "pid": pid.strip(), "last_exit": status.strip(),
                             "grade": "GREEN" if ok else "RED",
                             "note": "running" if running else f"scheduled (last exit {status.strip()})"})
    except Exception as e:
        jobs.append({"name": "launchctl", "grade": "RED", "note": str(e)[:80]})
    d["sections"]["launchd"] = jobs

    # 2) crontab heartbeat
    crons = []
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
        for ln in out.splitlines():
            if "signalos" in ln and not ln.startswith("#"):
                crons.append({"name": ln.split("#")[-1].strip() or "cron", "spec": ln.split(" cd ")[0].strip(),
                              "grade": "GREEN", "note": "installed"})
    except Exception as e:
        crons.append({"name": "crontab", "grade": "RED", "note": str(e)[:80]})
    # heartbeat freshness via the desk cron log
    hb = ROOT / "desk" / "data" / "desk_cron.out"
    age = _age_h(hb)
    crons.append({"name": "heartbeat output (desk_cron.out)", "spec": f"age {age:.1f}h" if age else "missing",
                  "grade": _grade(age, "heartbeat"), "note": "the hourly runner's tee"})
    d["sections"]["cron"] = crons

    # 3) registry watches — log freshness + error scan
    watches = []
    try:
        import sys
        sys.path.insert(0, str(ROOT))
        from desk import registry
        for w in registry.WATCHES:
            if w.get("dormant"):
                watches.append({"name": w["name"], "cadence": "dormant", "age_h": None,
                                "grade": "GREEN", "note": f"DORMANT: {w['dormant'][:120]}"})
                continue
            lg = ROOT / w.get("log", "nonexistent")
            age = _age_h(lg)
            err = False
            tailtxt = ""
            if lg.exists():
                try:
                    tailtxt = lg.read_text(errors="ignore")[-1500:]
                    # only flag errors in the FINAL block
                    last_block = tailtxt.split("=====")[-1] if "=====" in tailtxt else tailtxt
                    err = any(m in last_block for m in ERR_MARKERS)
                except Exception:
                    pass
            watches.append({"name": w["name"], "cadence": w.get("cadence", "?"),
                            "age_h": round(age, 1) if age is not None else None,
                            "grade": _grade(age, w.get("cadence", "daily"), err),
                            "note": ("LAST RUN ERRORED" if err else "ok") if age is not None else "log missing"})
    except Exception as e:
        watches.append({"name": "registry import", "grade": "RED", "note": str(e)[:100]})
    d["sections"]["registry_watches"] = sorted(watches, key=lambda x: ({"RED": 0, "YELLOW": 1, "GREEN": 2}[x["grade"]], x["name"]))

    # 4) sentinel inline watchers — state-file freshness + key stats
    states = []
    SF = {
        "gauntlet flags": ("desk/data/gauntlet_flags.json", "weekday", lambda j: f"{len(j.get('events', []))} pack events on {j.get('date')}"),
        "band_watch": ("desk/data/band_watch_state.json", "weekday", lambda j: f"{sum(1 for v in j.values() if isinstance(v, dict) and not v.get('armed', True))} bands fired/unarmed"),
        "hormuz_watch": ("desk/data/hormuz_watch_state.json", "weekday", lambda j: f"{len(j.get('days', {}))} days cached; kill_armed={j.get('kill_armed', True)}"),
        "squeeze_watch": ("desk/data/squeeze_watch_state.json", "weekday", lambda j: f"{len(j.get('days', {}))} days; armed={j.get('armed', True)}"),
        "season_watch": ("desk/data/season_watch_state.json", "weekday", lambda j: f"storms alerted: {j.get('storms_alerted', [])}; ONON last check {j.get('onon_last_check', 'never')}"),
        "news_scan": ("desk/data/news_scan_state.json", "hourly", lambda j: f"{len(j.get('seen', []))} seen keys"),
        "positions_cache": ("desk/ui/data/positions_cache.json", "daily", lambda j: f"{len(j.get('positions', []))} positions @ {datetime.datetime.fromtimestamp(j.get('asof', 0)).isoformat(timespec='minutes') if j.get('asof') else '?'}"),
        "orders_cache": ("desk/ui/data/orders_cache.json", "daily", lambda j: f"{len(j.get('orders', []))} working orders"),
        "write_lane": ("desk/data/write_lane.json", "weekly", lambda j: f"holder: {j.get('holder', '?')[:40]}"),
        "memory_lint": ("desk/data/memory_lint.json", "weekly", lambda j: f"top rot: {', '.join(r['file'][:30] for r in j.get('review_queue_top10', [])[:3])}"),
        "parametric_scorecard": ("desk/data/parametric_scorecard.json", "daily", lambda j: f"harvest surface ${j.get('harvest', {}).get('total_surface', 0):,} ({j.get('harvest', {}).get('surface_pct_of_mv')}% of MV); embedded {j.get('embedded', {}).get('gl_pct')}%; overlap {list(j.get('our_book_overlap', {}))[:4]}"),
    }
    for name, (rel, cad, fn) in SF.items():
        p = ROOT / rel
        age = _age_h(p)
        note = "missing"
        if p.exists():
            try:
                note = fn(json.loads(p.read_text()))
            except Exception as e:
                note = f"unreadable ({type(e).__name__})"
        states.append({"name": name, "age_h": round(age, 1) if age is not None else None,
                       "grade": _grade(age, cad), "note": note})
    d["sections"]["state_files"] = states

    # 5) UI server
    ui = {"name": "UI :8765", "grade": "RED", "note": "no response"}
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=5) as r:
            ui = {"name": "UI :8765", "grade": "GREEN" if r.status == 200 else "YELLOW", "note": f"HTTP {r.status}"}
    except Exception as e:
        ui["note"] = str(e)[:60]
    # gateway probe (the flaky dependency)
    gw = {"name": "IB Gateway :4001", "grade": "RED", "note": "unreachable (IV/positions legs degrade)"}
    try:
        import socket
        with socket.create_connection(("127.0.0.1", 4001), timeout=3):
            gw = {"name": "IB Gateway :4001", "grade": "GREEN", "note": "port open"}
    except Exception:
        pass
    d["sections"]["services"] = [ui, gw]

    # 6) calendars — packs due, open calls next up
    cal = []
    try:
        packs = json.loads((ROOT / "desk" / "data" / "resolution_packs.json").read_text())["packs"]
        today = datetime.date.today()
        upcoming = []
        for k in packs:
            t, dt = k.split("|")
            if dt == "weekly":
                upcoming.append((0, k, "every Monday"))
                continue
            try:
                dd = (datetime.date.fromisoformat(dt) - today).days
                if 0 <= dd <= 10:
                    upcoming.append((dd, k, f"in {dd}d"))
            except Exception:
                pass
        for dd, k, note in sorted(upcoming)[:10]:
            cal.append({"name": f"pack {k}", "grade": "GREEN", "note": note})
    except Exception as e:
        cal.append({"name": "packs", "grade": "RED", "note": str(e)[:80]})
    try:
        rows = [json.loads(l) for l in (ROOT / "desk" / "data" / "calibration_ledger.jsonl").read_text().splitlines() if l.strip()]
        openc = [r for r in rows if not r.get("outcome") and r.get("cat_date")]
        openc.sort(key=lambda r: str(r["cat_date"]))
        nxt = [f"{r['ticker']} {r['cat_date']} p={r.get('our_p')}" for r in openc[:5]]
        cal.append({"name": f"calibration: {len(openc)} open calls", "grade": "GREEN", "note": "next: " + "; ".join(nxt)})
    except Exception as e:
        cal.append({"name": "calibration ledger", "grade": "RED", "note": str(e)[:80]})
    d["sections"]["calendars"] = cal

    return d


def render(d: dict) -> str:
    C = {"GREEN": "#1E6B4F", "YELLOW": "#8A5F13", "RED": "#A32B18"}
    rows = []
    reds = sum(1 for sec in d["sections"].values() for it in sec if it.get("grade") == "RED")
    yels = sum(1 for sec in d["sections"].values() for it in sec if it.get("grade") == "YELLOW")
    head = (f"<title>Desk Diagnostics</title><style>body{{font-family:'Helvetica Neue',Arial,sans-serif;max-width:920px;"
            f"margin:0 auto;padding:24px;color:#000;background:#fff}}h1{{font-size:24px;margin:0 0 2px}}"
            f".sub{{color:#3D453F;font-size:13px;margin-bottom:14px}}h2{{font-size:13px;text-transform:uppercase;"
            f"letter-spacing:.08em;border-bottom:2px solid #000;padding-bottom:4px;margin:22px 0 6px}}"
            f"table{{border-collapse:collapse;width:100%;font-size:12.5px}}td{{padding:5px 8px;border-bottom:1px solid #D8DDD8;"
            f"vertical-align:top}}.g{{display:inline-block;color:#fff;font-size:10px;font-weight:700;padding:2px 7px;"
            f"border-radius:3px}}td.num{{font-family:ui-monospace,Menlo,monospace;white-space:nowrap}}</style>"
            f"<h1>Desk Diagnostics</h1><div class='sub'>as of {d['asof']} &middot; "
            f"<b style='color:{C['RED']}'>{reds} RED</b> &middot; <b style='color:{C['YELLOW']}'>{yels} YELLOW</b> "
            f"&middot; regenerated hourly by desk.diagnostics</div>")
    for sec, items in d["sections"].items():
        rows.append(f"<h2>{html.escape(sec.replace('_', ' '))}</h2><table>")
        for it in items:
            g = it.get("grade", "?")
            age = it.get("age_h")
            agecell = f"{age}h" if age is not None else (it.get("spec") or it.get("pid") or "")
            rows.append(f"<tr><td><span class='g' style='background:{C.get(g, '#666')}'>{g}</span></td>"
                        f"<td><b>{html.escape(str(it.get('name', '')))}</b></td>"
                        f"<td class='num'>{html.escape(str(agecell))}</td>"
                        f"<td>{html.escape(str(it.get('note', '')))[:180]}</td></tr>")
        rows.append("</table>")
    return head + "".join(rows)


def main():
    d = collect()
    OUT_JSON.write_text(json.dumps(d, indent=1))
    OUT_HTML.write_text(render(d))
    reds = [it["name"] for sec in d["sections"].values() for it in sec if it.get("grade") == "RED"]
    print(f"[diagnostics] {sum(len(s) for s in d['sections'].values())} subsystems graded; "
          f"RED: {reds if reds else 'none'} -> diag.html")


if __name__ == "__main__":
    main()
