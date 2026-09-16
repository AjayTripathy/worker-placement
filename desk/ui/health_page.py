"""health_page — the infrastructure health board: every registered watch's liveness, the
consistency-checker's current flags, cron/server heartbeats, and the INCIDENTS ledger
(desk/data/infra_incidents.jsonl — every infrastructure failure gets a row: symptom,
root cause, fix, status; the postmortem discipline applied to our own plumbing).

Born 2026-07-31 (user: "we need a dashboard of all of our healthchecks and infrastructure
failings") after the headless grader crashed silently for ~36h and was caught by a human
eyeballing the dashboard rather than by the system. Routes: GET /health (page),
GET /api/health (JSON). Computed LIVE on request — no cron, no cache.
"""
from __future__ import annotations
import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "desk" / "data"
INCIDENTS = D / "infra_incidents.jsonl"

# cadence -> max acceptable log age (hours) before STALE
MAX_AGE_H = {"15min": 1, "hourly": 3, "daily": 30, "weekday": 78, "weekly": 200, "monthly": 800}
ERR_PAT = re.compile(r"Traceback|Error|error:|DATA MISSING|failed|FAIL|Exception", re.I)
OK_NOISE = re.compile(r"0 (errors|failed)|no errors", re.I)


def _watch_rows():
    from desk.registry import WATCHES
    now = datetime.datetime.now()
    rows = []
    for w in WATCHES:
        log = ROOT / w.get("log", "")
        age_h, errs, last = None, 0, ""
        if log.exists():
            age_h = (now - datetime.datetime.fromtimestamp(log.stat().st_mtime)).total_seconds() / 3600
            tail = log.read_text(errors="replace")[-4000:]
            errs = len([m for m in ERR_PAT.finditer(tail) if not OK_NOISE.search(tail[max(0, m.start()-30):m.end()+30])])
            last = tail.strip().splitlines()[-1][:160] if tail.strip() else ""
        if not w.get("enabled", True):
            status = "DISABLED"
        elif age_h is None:
            status = "NO-LOG"
        elif age_h > MAX_AGE_H.get(w.get("cadence", "daily"), 30):
            status = "STALE"
        elif errs >= 3:
            status = "ERRORS"
        else:
            status = "OK"
        rows.append({"name": w["name"], "cadence": w.get("cadence", "?"), "status": status,
                     "age_h": round(age_h, 1) if age_h is not None else None,
                     "recent_error_mentions": errs, "last_line": last})
    order = {"ERRORS": 0, "STALE": 1, "NO-LOG": 2, "OK": 3, "DISABLED": 4}
    return sorted(rows, key=lambda r: (order.get(r["status"], 9), r["name"]))


def _consistency_flags():
    """Parse the last consistency_check run block for FLAG lines + run its grader-health check live."""
    out = []
    f = D / "consistency_check.out"
    if f.exists():
        tail = f.read_text(errors="replace")[-6000:]
        blocks = tail.split("=====")
        last = blocks[-1] if blocks else tail
        out += [ln.strip()[:220] for ln in last.splitlines() if "FLAG" in ln or "⚠" in ln][:20]
        m = re.findall(r"=====\s*([0-9:\- ]+)", tail)
        stamp = m[-1].strip() if m else "?"
    else:
        stamp = "no output file"
    live = []
    try:
        from desk.consistency_check import check_grader_health
        check_grader_health(live)
    except Exception as e:
        live.append(f"grader-health check unrunnable: {type(e).__name__}")
    return {"last_run": stamp, "flags": out, "live_grader_health": live}


def _heartbeats():
    now = datetime.datetime.now()
    def age(p):
        p = Path(p)
        return round((now - datetime.datetime.fromtimestamp(p.stat().st_mtime)).total_seconds() / 3600, 1) if p.exists() else None
    hb = {"desk_cron_out_age_h": age(D / "desk_cron.out"),
          "positions_cache_age_h": age(ROOT / "desk" / "ui" / "data" / "positions_cache.json"),
          "server_err_age_h": age(ROOT / "desk" / "ui" / "data" / "server.err")}
    try:
        hb["last_run"] = json.loads((D / "last_run.json").read_text())
    except Exception:
        hb["last_run"] = None
    serr = ROOT / "desk" / "ui" / "data" / "server.err"
    if serr.exists():
        tail = serr.read_text(errors="replace")[-2000:]
        hb["server_recent_errors"] = [l[:160] for l in tail.splitlines() if ERR_PAT.search(l)][-5:]
    return hb


def _incidents():
    rows = []
    if INCIDENTS.exists():
        for line in INCIDENTS.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                rows.append({"date": "?", "system": "incidents_ledger", "severity": "MED",
                             "symptom": f"unparseable incident row: {line[:80]}", "status": "OPEN"})
    order = {"OPEN": 0, "MITIGATED": 1, "RECOVERED": 2, "FIXED": 3}
    return sorted(rows, key=lambda r: (order.get(r.get("status", "OPEN"), 9), r.get("date", "")), reverse=False)


def collect():
    watches = _watch_rows()
    counts = {}
    for r in watches:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"asof": datetime.datetime.now().isoformat(timespec="seconds"),
            "summary": counts, "watches": watches,
            "consistency": _consistency_flags(), "heartbeats": _heartbeats(),
            "incidents": _incidents()}


SEV_CLASS = {"HIGH": "crit", "MED": "warn", "LOW": "ok"}
ST_CLASS = {"OK": "ok", "DISABLED": "mut", "STALE": "warn", "ERRORS": "crit", "NO-LOG": "warn",
            "OPEN": "crit", "MITIGATED": "warn", "RECOVERED": "ok", "FIXED": "ok"}


def render() -> str:
    d = collect()
    e = html.escape
    chip = lambda s: f'<span class="chip {ST_CLASS.get(s,"mut")}">{e(s)}</span>'
    watch_tr = "".join(
        f"<tr><td>{chip(r['status'])}</td><td>{e(r['name'])}</td><td class=m>{e(r['cadence'])}</td>"
        f"<td class=m>{r['age_h'] if r['age_h'] is not None else '—'}h</td>"
        f"<td class=m>{r['recent_error_mentions'] or ''}</td>"
        f"<td class=last>{e(r['last_line'])}</td></tr>"
        for r in d["watches"])
    cflags = d["consistency"]["flags"] + d["consistency"]["live_grader_health"]
    flags_html = ("".join(f'<li>{e(f)}</li>' for f in cflags) or "<li class=okline>no flags</li>")
    inc_tr = "".join(
        f"<tr><td class=m>{e(str(i.get('date','')))}</td><td>{chip(i.get('status','OPEN'))}</td>"
        f"<td>{e(i.get('system',''))}</td><td>{e(i.get('symptom',''))[:180]}</td>"
        f"<td>{e(i.get('root_cause',''))[:160]}</td><td>{e(i.get('fix',''))[:160]}</td></tr>"
        for i in d["incidents"])
    hb = d["heartbeats"]
    s = d["summary"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>desk health</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
 :root{{--bg:#fcfcfb;--card:#fff;--ink:#1d2129;--ink2:#555b66;--mut:#8a8f99;--hair:rgba(29,33,41,.12);
  --ok:#2e7d32;--warn:#9a6d00;--crit:#c62828;--okbg:rgba(46,125,50,.1);--warnbg:rgba(154,109,0,.1);--critbg:rgba(198,40,40,.1);}}
 @media(prefers-color-scheme:dark){{:root{{--bg:#16181d;--card:#1d2026;--ink:#e7e9ee;--ink2:#aab0bb;--mut:#7c828d;
  --hair:rgba(231,233,238,.14);--ok:#69b06c;--warn:#d3a73a;--crit:#e06c60;--okbg:rgba(105,176,108,.12);--warnbg:rgba(211,167,58,.12);--critbg:rgba(224,108,96,.12);}}}}
 body{{background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,"Segoe UI",sans-serif;margin:0;padding:24px;}}
 .wrap{{max-width:1200px;margin:0 auto;}}
 h1{{font-size:20px;margin:0 0 2px}} h2{{font-size:15px;margin:26px 0 8px}}
 .sub{{color:var(--mut);font-size:12.5px;margin-bottom:14px}}
 .strip{{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}}
 .stat{{background:var(--card);border:1px solid var(--hair);border-radius:8px;padding:8px 14px;font-size:13px}}
 .stat b{{font-size:18px;display:block}}
 table{{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--hair);border-radius:8px;font-size:12.5px}}
 td,th{{padding:5px 9px;border-bottom:1px solid var(--hair);text-align:left;vertical-align:top}}
 .m{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;white-space:nowrap}}
 .last{{color:var(--mut);font-family:ui-monospace,Menlo,monospace;font-size:11px;max-width:480px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
 .chip{{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:999px;white-space:nowrap}}
 .ok{{color:var(--ok);background:var(--okbg)}} .warn{{color:var(--warn);background:var(--warnbg)}}
 .crit{{color:var(--crit);background:var(--critbg)}} .mut{{color:var(--mut);background:var(--hair)}}
 ul{{background:var(--card);border:1px solid var(--hair);border-radius:8px;margin:0;padding:10px 28px;font-size:13px}}
 .okline{{color:var(--ok)}}
 .hb{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--ink2)}}
 a{{color:inherit}}
</style></head><body><div class="wrap">
<h1>Desk health &amp; infrastructure</h1>
<div class="sub">as of {e(d['asof'])} · computed live · <a href="/api/infra">JSON</a> · <a href="/">desk</a> · <a href="/brain">brain</a></div>
<div class="strip">
 <div class="stat"><b>{s.get('OK',0)}</b>watches OK</div>
 <div class="stat" style="{'color:var(--crit)' if s.get('ERRORS') else ''}"><b>{s.get('ERRORS',0)}</b>erroring</div>
 <div class="stat" style="{'color:var(--warn)' if s.get('STALE') else ''}"><b>{s.get('STALE',0)}</b>stale</div>
 <div class="stat"><b>{s.get('DISABLED',0)+s.get('NO-LOG',0)}</b>disabled/no-log</div>
 <div class="stat" style="{'color:var(--crit)' if any(i.get('status')=='OPEN' for i in d['incidents']) else ''}"><b>{sum(1 for i in d['incidents'] if i.get('status')=='OPEN')}</b>open incidents</div>
</div>
<h2>Consistency flags <span class="sub">(last run {e(d['consistency']['last_run'])} + live grader-health)</span></h2>
<ul>{flags_html}</ul>
<h2>Heartbeats</h2>
<div class="hb">desk_cron.out age: {hb['desk_cron_out_age_h']}h · positions_cache age: {hb['positions_cache_age_h']}h · server.err age: {hb['server_err_age_h']}h</div>
{"<ul>" + "".join(f"<li>{e(l)}</li>" for l in hb.get("server_recent_errors", [])) + "</ul>" if hb.get("server_recent_errors") else ""}
<h2>Watches ({len(d['watches'])})</h2>
<table><tr><th></th><th>watch</th><th>cadence</th><th>log age</th><th>err✕</th><th>last line</th></tr>{watch_tr}</table>
<h2>Incidents ledger <span class="sub">(desk/data/infra_incidents.jsonl — append every failure; open first)</span></h2>
<table><tr><th>date</th><th></th><th>system</th><th>symptom</th><th>root cause</th><th>fix</th></tr>{inc_tr}</table>
</div></body></html>"""
