"""render_signals — the SIGNALS surfaces (F3a, principal-directed 2026-09-05).

Three pages, glass-box all the way down:
  signals.html          index of every registered capability with kind, health,
                        last run — the desk machinery, enumerated
  capability_<name>.html one page per primitive: description, DATASOURCES
                        enumerated, applies-to axes, cadence, last run + output,
                        and the ACTUAL CODE that powers it
  asset_<SYM>.html      one page per asset: its strategies, holdings,
                        adjudications, and the capability UNION that applies —
                        the strategy -> asset click-through's landing page

Read-only; never places orders.
"""
from __future__ import annotations

import json

from officekit.fmt import esc

import re as _re


def asset_slug(symbol):
    """Filesystem/URL-safe asset page name — private holding names carry
    spaces and punctuation ("SG2-ZZ, LLC")."""
    return _re.sub(r"[^A-Za-z0-9._-]+", "_", str(symbol).upper()).strip("_")


CSS = """
:root{--violet:#b1a5ff;--dim:#9aa4b0;--ink:#e8ebee;--panel2:#1a1f25;--line:#242a31}
body{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:940px;margin:0 auto;padding:26px 24px 90px}
a{color:#b1a5ff} h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:#9aa4b0;margin:0 0 20px;font-size:13px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.12em;color:#9aa4b0;margin:24px 0 8px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:7px 10px;border-bottom:1px solid #242a31;text-align:left;vertical-align:top}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:#9aa4b0}
.k{font-size:10px;font-weight:700;letter-spacing:.05em;padding:2px 8px;border-radius:20px}
.k-generator{color:#c3b8fb;background:rgba(177,165,255,.15)}
.k-detector{color:#eccb8a;background:rgba(217,164,65,.15)}
.k-watcher{color:#8ee5c1;background:rgba(53,201,143,.15)}
.k-evidence{color:#b3bcc6;background:rgba(138,147,158,.15)}
.h-OK{color:#35c98f} .h-STALE{color:#d9a441} .h-ERROR{color:#e0736a} .h-NEVER_RUN{color:#8a939e}
pre{background:#14181d;border:1px solid #242a31;border-radius:12px;padding:14px;overflow-x:auto;font-size:12px;line-height:1.5}
.panel{background:#14181d;border:1px solid #242a31;border-radius:12px;padding:14px 18px;margin-bottom:12px}
ul{margin:4px 0;padding-left:20px} li{margin-bottom:4px}
.mono{font-family:ui-monospace,Menlo,monospace}
.table-scroll{overflow:auto} .table-scroll table{min-width:600px} summary{cursor:pointer} details[open]>summary{margin-bottom:12px}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid #35c98f;outline-offset:3px}
.signal-row{display:flex;gap:14px;align-items:baseline;justify-content:space-between;padding:16px 0;border-bottom:1px solid #242a31}.signal-row>div{min-width:0}.signal-row a{font-weight:600}.signal-row .sub{margin:4px 0 0}.signal-state{font-size:12px;white-space:nowrap}
@media(max-width:600px){.wrap{padding:22px 16px 60px} .signal-row{flex-wrap:wrap}.wrap>table{display:block;overflow:auto}}
"""


def _page(title, sub, body):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{CSS}</style></head><body><div class="wrap">'
            f'<h1>{esc(title)}</h1><p class="sub">{sub}</p>{body}</div></body></html>')


def render_signals_index(caps, rt):
    groups = {"attention": [], "active": [], "available": []}
    labels = {"OK": "Up to date", "STALE": "Refresh needed", "ERROR": "Run failed", "NEVER_RUN": "Not run yet"}
    for c in sorted(caps.values(), key=lambda c: (c["kind"], c["name"])):
        r = rt.get(c["name"], {})
        health = r.get("health", "NEVER_RUN")
        key = "attention" if health in ("STALE", "ERROR") else "active" if health == "OK" else "available"
        row = (f'<div class="signal-row"><div><a href="capability_{esc(c["name"])}.html">{esc(c["label"])}</a>'
               f'<p class="sub">{esc(c["desc"][:160])}</p></div>'
               f'<span class="signal-state h-{esc(health)}">{labels.get(health, health.replace("_", " ").capitalize())}</span></div>')
        groups[key].append(row)
    body = '<div class="panel"><b>' + str(len(groups["active"])) + ' up to date · ' + str(len(groups["attention"])) + ' need attention</b>'
    body += '<p class="sub" style="margin:6px 0 0">Readiness reflects recorded runs in this office. A registered capability has not necessarily run or produced a finding.</p></div>'
    if groups["attention"]:
        body += '<h2>Needs attention</h2>' + ''.join(groups["attention"])
    if groups["active"]:
        body += '<h2>Latest recorded checks</h2>' + ''.join(groups["active"])
    else:
        body += '<p>No up-to-date signal runs are recorded yet. Open a capability below to review its data requirements and run it.</p>'
    body += '<details class="panel" style="margin-top:24px"><summary>Available capabilities · ' + str(len(groups["available"])) + '</summary>' + ''.join(groups["available"]) + '</details>'
    body += '<p class="sub">Each capability includes its sources, last output, and implementation details. No orders are placed from this page.</p>'
    return _page("Signals", "Monitor the checks that support your investment decisions.", body)


def render_capability(cap, rt_entry, code):
    a = cap["applies_to"]
    ax = []
    if a["universal"]:
        ax.append("<li><b>universal</b> — applies to every asset and strategy</li>")
    for key, label in (("strategies", "strategies"), ("symbols", "assets"),
                       ("categories", "categories"), ("issuer_features", "issuer features")):
        if a[key]:
            ax.append(f"<li><b>{label}:</b> {esc(', '.join(a[key]))}</li>")
    ds = "".join(f"<li>{esc(d)}</li>" for d in cap["datasources"]) or "<li>(none declared)</li>"
    r = rt_entry or {}
    out = ""
    if r.get("output") is not None:
        out = (f'<h2>Last run output</h2><pre>{esc(json.dumps(r["output"], indent=1)[:6000])}</pre>')
    run_form = (f'<form method="POST" action="/signals/run" style="margin:10px 0">'
                f'<input type="hidden" name="name" value="{esc(cap["name"])}">'
                f'<input name="symbol" placeholder="symbol (if applicable)" '
                f'style="background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:7px 10px">'
                f'<input name="symbols" placeholder="universe, comma-sep (generators)" '
                f'style="background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:7px 10px;margin-left:6px">'
                f'<button type="submit" style="background:var(--violet);color:#0b0e12;border:0;border-radius:8px;'
                f'padding:7px 14px;font-weight:700;cursor:pointer;margin-left:6px">Run now</button></form>')
    body = (f'<a href="signals.html">&larr; all signals</a>'
            f'<div class="panel" style="margin-top:10px"><span class="k k-{cap["kind"]}">{cap["kind"].upper()}</span> '
            f'&nbsp;<span class="h-{r.get("health", "NEVER_RUN")}"><b>{esc(r.get("health", "NEVER_RUN"))}</b></span>'
            f' · last run <span class="mono">{esc(r.get("last_run") or "never")}</span>'
            + (f' · cadence {cap["cadence_days"]}d' if cap.get("cadence_days") else "")
            + (f'<div class="sub" style="margin-top:6px">{esc(r.get("note", ""))}</div>' if r.get("note") else "")
            + f'</div>'
            f'<p>{esc(cap["desc"])}</p>{run_form}'
            f'<h2>Datasources</h2><ul>{ds}</ul>'
            f'<h2>Applies to</h2><ul>{"".join(ax)}</ul>'
            f'{out}'
            f'<h2>The code</h2><pre>{esc(code)}</pre>')
    return _page(cap["label"], f'registered capability · {cap["name"]}', body)


def render_asset(symbol, data, adjudications, caps_union, strategies_of):
    holds = []
    for s in data.get("sleeves", []):
        for h in s.get("holdings", []):
            if str(h.get("company", "")).upper() == symbol:
                adj = (h.get("adjudication") or {}).get("verdict", "")
                holds.append(f'<tr><td>{esc(s.get("name", ""))}</td>'
                             f'<td class="mono">{h.get("amount", 0):,.0f}</td><td>{esc(adj)}</td></tr>')
    adj_rows = "".join(
        f'<tr><td>{esc(a["date"])}</td><td>{esc(a.get("strategy", ""))}</td>'
        f'<td><b>{esc(a["verdict"])}</b></td>'
        f'<td><a href="deck_{a["id"][:8]}.html">deck &rarr;</a></td></tr>'
        for a in adjudications if a.get("symbol") == symbol)
    cap_rows = "".join(
        f'<tr><td><span class="k k-{c["kind"]}">{c["kind"].upper()}</span></td>'
        f'<td><a href="capability_{esc(c["name"])}.html">{esc(c["label"])}</a></td>'
        f'<td class="sub">{esc(c["desc"][:110])}…</td></tr>'
        for c in caps_union)
    body = (f'<a href="strategies.html">&larr; strategies</a>'
            f'<h2>Strategies serving</h2><p>{esc(", ".join(strategies_of) or "none — not a member of any strategy")}</p>'
            + (f'<h2>Positions</h2><table><tr><th>sleeve</th><th>amount</th><th>adjudication</th></tr>{"".join(holds)}</table>'
               if holds else '<h2>Positions</h2><p class="sub">not held</p>')
            + (f'<h2>Adjudications</h2><table><tr><th>date</th><th>strategy</th><th>verdict</th><th></th></tr>{adj_rows}</table>'
               if adj_rows else "")
            + f'<h2>Applicable capabilities — the union for this asset</h2>'
            f'<p class="sub">strategy bindings + asset bindings + feature matches + universal, derived at render time</p>'
            f'<table><tr><th>kind</th><th>capability</th><th></th></tr>{cap_rows}</table>')
    return _page(f"{symbol} — asset view",
                 "every asset exposes its deliberations and the machinery watching it", body)
