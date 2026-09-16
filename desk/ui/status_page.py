"""status_page — the pipeline-status view (principal request 2026-08-28: 'the desk page needs a
status UI' — twice asked, after two days of conveyor work were invisible outside emails).

One page answering: is the machine running, what is it working on, what came out, what is owed.
READ-ONLY, assembled fresh per request from the same files the pipeline writes.
"""
from __future__ import annotations

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "desk" / "data"


def _age_min(p: Path) -> float | None:
    try:
        return (datetime.datetime.now().timestamp() - p.stat().st_mtime) / 60
    except FileNotFoundError:
        return None


def _proc_alive(pattern: str) -> bool:
    return subprocess.run(["pgrep", "-f", pattern], capture_output=True).returncode == 0


def status_payload() -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)

    # queue census + per-stage names with ages
    q = json.loads((DATA / "court_queue.json").read_text())
    items = q.get("items", q) if isinstance(q, dict) else q
    stages: dict = {}
    recent_rulings = []
    for it in items:
        st, t = it.get("stage"), it.get("ticker")
        h = it.get("history", [])
        last = h[-1].get("utc") if h else it.get("enqueued_utc")
        if st not in ("DONE", "KILLED"):
            stages.setdefault(st, []).append({"ticker": t, "since": last})
        else:
            for e in reversed(h):
                if e.get("to") in ("DONE", "KILLED") and e.get("utc"):
                    try:
                        tt = datetime.datetime.fromisoformat(e["utc"].replace("Z", "+00:00"))
                        if (now - tt).total_seconds() < 3 * 86400:
                            decks = sorted(set((ROOT / "desk" / "reports").glob(f"{t}_PITCH_DECK_*.md"))
                                           | set((ROOT / "desk" / "reports").glob(f"{t.replace('.', '_')}_PITCH_DECK_*.md")))
                            recent_rulings.append({
                                "ticker": t, "outcome": e["to"], "utc": e["utc"],
                                "note": (e.get("note") or "")[:220],
                                "has_artifact": bool(e.get("artifact")),
                                "deck": f"desk/reports/{decks[-1].name}" if decks else None})
                    except ValueError:
                        pass
                    break
    recent_rulings.sort(key=lambda r: r["utc"], reverse=True)

    # runner: lock + last log line + last cycle time
    lock = DATA / "court_runner.lock"
    runner = {
        "drain_in_progress": lock.exists(),
        "log_age_min": _age_min(DATA / "court_runner.out"),
        "last_lines": []}
    try:
        tail = (DATA / "court_runner.out").read_text()[-3000:].strip().splitlines()
        runner["last_lines"] = [l for l in tail if l.startswith("  ") or "[court_runner]" in l][-8:]
    except FileNotFoundError:
        pass

    # daemons + watchers
    daemons = {
        "envelope_runner": _proc_alive("desk.envelope_runner"),
        "order_sentinel_log_age_min": _age_min(DATA / "order_sentinel.out"),
        "band_watch_state_age_min": _age_min(DATA / "band_watch_state.json"),
    }

    # dated packs due soon (the desk calendar)
    packs = json.loads((DATA / "resolution_packs.json").read_text()).get("packs", {})
    upcoming = []
    for k, v in packs.items():
        if not isinstance(v, dict) or v.get("lifecycle") not in (None, "open"):
            continue
        try:
            d = datetime.date.fromisoformat(k.split("|")[1])
        except (IndexError, ValueError):
            continue
        delta = (d - now.date()).days
        if -3 <= delta <= 14:
            upcoming.append({"pack": k, "days": delta,
                             "what": (v.get("adjudication") or "")[:180]})
    upcoming.sort(key=lambda r: r["days"])

    # open calibration calls
    open_calls = []
    try:
        for line in (DATA / "calibration_ledger.jsonl").read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("status") == "OPEN":
                open_calls.append({"ticker": r.get("ticker"), "cat_date": r.get("cat_date"),
                                   "p": r.get("our_p"), "direction": (r.get("direction") or "")[:120]})
    except FileNotFoundError:
        pass
    open_calls.sort(key=lambda r: r.get("cat_date") or "9999")

    # consistency flags (best-effort, cheap checks only — no network)
    flags = []
    try:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from desk.consistency_check import (check_packs_have_dates,
                                            check_unverified_ledger_drains,
                                            check_band_touches_dispositioned)
        for fn in (check_packs_have_dates, check_unverified_ledger_drains,
                   check_band_touches_dispositioned):
            try:
                fn(flags)
            except Exception as e:
                flags.append(f"{fn.__name__} errored: {type(e).__name__}")
    except Exception as e:
        flags.append(f"consistency import failed: {type(e).__name__}")

    return {"asof": now.isoformat(timespec="seconds"),
            "queue": {k: v for k, v in sorted(stages.items())},
            "queue_counts": {k: len(v) for k, v in stages.items()},
            "recent_rulings_72h": recent_rulings[:40],
            "runner": runner, "daemons": daemons,
            "upcoming_packs_14d": upcoming[:30],
            "open_calibration_calls": open_calls[:40],
            "flags": flags}


def render_html() -> str:
    p = status_payload()
    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rows = []
    rows.append(f"<h1>Pipeline status</h1><p class=meta>as of {esc(p['asof'])} · auto-refresh 60s</p>")
    ok = p["runner"]["drain_in_progress"]
    rows.append("<div class=cards>")
    rows.append(f"<div class='card {'on' if ok else ''}'><b>court runner</b><br>"
                f"{'DRAIN IN PROGRESS' if ok else 'idle'} · log {p['runner']['log_age_min'] and round(p['runner']['log_age_min']) or '?'}m ago</div>")
    rows.append(f"<div class='card {'on' if p['daemons']['envelope_runner'] else 'bad'}'><b>envelope runner</b><br>"
                f"{'alive' if p['daemons']['envelope_runner'] else 'NOT RUNNING'}</div>")
    sa = p["daemons"]["order_sentinel_log_age_min"]
    rows.append(f"<div class='card {'on' if sa is not None and sa < 45 else 'bad'}'><b>order sentinel</b><br>"
                f"last run {sa and round(sa) or '?'}m ago</div>")
    counts = " · ".join(f"{k} {v}" for k, v in p["queue_counts"].items()) or "queue empty"
    rows.append(f"<div class=card><b>queue</b><br>{esc(counts)}</div>")
    rows.append("</div>")
    if p["flags"]:
        rows.append("<h2>Flags</h2><ul>" + "".join(f"<li class=flag>{esc(f)}</li>" for f in p["flags"]) + "</ul>")
    if p["queue"]:
        rows.append("<h2>In the conveyor</h2><table><tr><th>stage</th><th>names</th></tr>")
        for st, names in p["queue"].items():
            nm = ", ".join(f"<a href='/ticker/{esc(n['ticker'])}'>{esc(n['ticker'])}</a>" for n in names)
            rows.append(f"<tr><td>{esc(st)}</td><td>{nm}</td></tr>")
        rows.append("</table>")
    rows.append("<h2>Rulings — last 72h</h2><table><tr><th>utc</th><th>name</th><th>outcome</th><th>deck</th><th>note</th></tr>")
    for r in p["recent_rulings_72h"]:
        cls = "" if r["has_artifact"] else " class=flag title='no adjudication artifact'"
        deck = (f"<a href='/doc?file={esc(r['deck'])}'>deck</a> · "
                f"<a href='/doc?file={esc(r['deck'][:-3])}.pdf'>pdf</a>") if r.get("deck") else "—"
        rows.append(f"<tr{cls}><td>{esc(r['utc'][5:16])}</td><td><a href='/ticker/{esc(r['ticker'])}'>{esc(r['ticker'])}</a></td>"
                    f"<td>{esc(r['outcome'])}</td><td>{deck}</td><td>{esc(r['note'])}</td></tr>")
    rows.append("</table>")
    rows.append("<h2>Calendar — dated packs ±14d</h2><table><tr><th>d</th><th>pack</th><th>what</th></tr>")
    for u in p["upcoming_packs_14d"]:
        rows.append(f"<tr><td>{u['days']:+d}</td><td>{esc(u['pack'])}</td><td>{esc(u['what'])}</td></tr>")
    rows.append("</table>")
    rows.append("<h2>Open calibration calls</h2><table><tr><th>date</th><th>call</th><th>p</th><th>direction</th></tr>")
    for c in p["open_calibration_calls"]:
        rows.append(f"<tr><td>{esc(c['cat_date'])}</td><td>{esc(c['ticker'])}</td><td>{c['p']}</td><td>{esc(c['direction'])}</td></tr>")
    rows.append("</table>")
    style = """<style>body{font:14px -apple-system,sans-serif;margin:24px;max-width:1100px}
    h1{margin-bottom:2px} .meta{color:#777;margin-top:0} h2{margin-top:26px;border-bottom:1px solid #ddd}
    .cards{display:flex;gap:12px;flex-wrap:wrap} .card{border:1px solid #ccc;border-radius:8px;padding:10px 14px;min-width:150px}
    .card.on{border-color:#2a2;background:#f3fff3} .card.bad{border-color:#c33;background:#fff3f3}
    table{border-collapse:collapse;width:100%} td,th{border:1px solid #e3e3e3;padding:5px 8px;text-align:left;vertical-align:top}
    th{background:#f7f7f7} .flag{background:#fff3f3} a{color:#0366d6;text-decoration:none}</style>
    <meta http-equiv=refresh content=60>"""
    return f"<!doctype html><html><head><title>Desk — pipeline status</title>{style}</head><body>{''.join(rows)}</body></html>"
