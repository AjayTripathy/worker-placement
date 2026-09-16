"""brain_page — the dispatch-brain map: channels -> watches -> three-ring dispatcher -> detector atlas.

Rendered LIVE from knowledge_graph/knowledge_graph.json + desk/registry.py on every request, so the
page tracks the KG as APPLIES_TO coverage grows and watches come and go. Route: GET /brain.
First published as the 2026-07-29 artifact; this module is the standing in-UI version.
"""
from __future__ import annotations
import json, re, html, datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]

VCOLOR = {  # fixed categorical assignment (dataviz-validated palette, slot per vertical)
    "public_co": ("v1", "Public-company forensics"),
    "buyside_dd": ("v2", "Buyside / IPO diligence"),
    "muni_credit": ("v3", "Muni credit"),
    "rent_stabilization": ("v4", "Rent stabilization"),
    "art_donation_fraud": ("v5", "Art-donation fraud"),
}

CHANNEL_BUCKETS = [
    ("Securities filings", r"SEC|EDGAR|XBRL|Form 990|Schedule K"),
    ("Muni & CA public finance", r"CDIAC|EMMA|53356|Tax-Default|Recorder|HCAI|CDE |CAASPP|LCFF|FCMAT|COE |Controller|ROPS|RDA|Covenant|Charter"),
    ("Health & enforcement", r"CMS|HHS|OIG|DOJ|False Claims"),
    ("Federal programs & spend", r"USASpending|DoD|DOE|NIH|FDA|Pentagon|NASA|SAM|Census|BLS|EPA|FCC|NHTSA|FMCSA|DOL|HUD|IRS"),
    ("Courts / labor / property", r"PACER|CourtListener|OSHA|WARN|H-?1B|UCC|permit|Recorder|Laserfiche"),
    ("Physical truth (satellite/energy)", r"Sentinel|Planet|Carbon|methane|NDVI|thermal|oil|NREL"),
    ("Attention & positioning", r"Reddit|Trends|Stocktwits|Wikipedia|GDELT|13F|FINRA|short|borrow"),
    ("Markets & venues", r"Polymarket|Kalshi|IBKR|option"),
]

NAME_INSTRUMENTS = {"kalmar_order_nowcast", "bank_callreport_watch", "vrla_volume_watch",
                    "sterv_demerger_watch", "bke_monthly_comps", "hubs_breeze_tripwires",
                    "aumovio_peer", "stvn_book", "lab_scheduler_panel", "beauty_virality",
                    "crossborder_twins", "biotech_clearing", "deal_cycle"}
SCREENS = {"smallcap_value", "financials_screen", "dislocation_sweep", "krx_value", "luxury_heat",
           "import_anomaly", "december_dislocation", "social_thesis", "polymarket_whales",
           "seasonality_calendar"}


def _channel_counts(chan_names):
    counts, used = [], set()
    for label, pat in CHANNEL_BUCKETS:
        n = 0
        for c in chan_names:
            if c in used:
                continue
            if re.search(pat, c, re.I):
                used.add(c); n += 1
        if n:
            counts.append((label, n))
    rest = len(chan_names) - len(used)
    if rest:
        counts.append(("Other primary sources", rest))
    return counts


def _watch_groups():
    from desk.registry import WATCHES
    wg = defaultdict(list)
    for w in WATCHES:
        if not w.get("enabled"):
            continue
        n = w["name"]
        if n.startswith("gen_"):
            wg["Generators (idea factories)"].append(w)
        elif n.startswith("det_"):
            wg["Detector sweeps over the book"].append(w)
        elif n in NAME_INSTRUMENTS:
            wg["Name-specific instruments (v1.5)"].append(w)
        elif n in SCREENS:
            wg["Screens & sweeps"].append(w)
        else:
            wg["Desk ops, calibration & hygiene"].append(w)
    return wg


def render() -> str:
    kg = json.loads((ROOT / "knowledge_graph" / "knowledge_graph.json").read_text())
    ch = json.loads((ROOT / "knowledge_graph" / "signal_channels.json").read_text())
    channels = ch["channels"]
    chan_names = [c.get("name", "?") if isinstance(c, dict) else str(c) for c in channels]
    dispatch = {d["name"]: d for d in kg["dispatch_index"]}
    counts = _channel_counts(chan_names)
    wg = _watch_groups()

    by_vert = defaultdict(list)
    for d in kg["detector_inventory"]:
        by_vert[d["vertical"]].append(d)

    def chip(d):
        cls, _ = VCOLOR[d["vertical"]]
        di = dispatch.get(d["name"])
        ring = ""
        if di:
            a = di.get("applies_to") or {}
            kind = a.get("kind") or di.get("kind") or ""
            ring = (f' <span class="ring" title="APPLIES_TO contract ({html.escape(str(kind))}) '
                    f'— Ring-0 dispatchable">&#9673;</span>')
        summ = html.escape((d.get("summary") or "").strip()[:220], quote=True)
        return f'<span class="det {cls}" title="{summ}">{html.escape(d["name"])}{ring}</span>'

    det_html = ""
    for v in ["public_co", "buyside_dd", "muni_credit", "rent_stabilization", "art_donation_fraud"]:
        ds = sorted(by_vert.get(v, []), key=lambda x: x["name"])
        if not ds:
            continue
        cls, label = VCOLOR[v]
        idx = sum(1 for d in ds if d["name"] in dispatch)
        det_html += (f'<div class="vgroup"><div class="vhead"><span class="dot {cls}"></span><b>{label}</b>'
                     f'<span class="vmeta">{len(ds)} modules · {idx} contracted</span></div>'
                     f'<div class="chips">{"".join(chip(d) for d in ds)}</div></div>\n')

    rows = ""
    for d in sorted(kg["dispatch_index"], key=lambda x: (x["vertical"], x["name"])):
        a = d.get("applies_to") or {}
        sic = " ".join(str(s) for s in (a.get("sic_prefixes") or a.get("sic_codes") or [])) or "—"
        feats = ", ".join((a.get("issuer_features") or [])[:3]) or "—"
        kind = a.get("kind") or d.get("kind") or "—"
        univ = "always" if a.get("applies_universally") else "conditional"
        cls, _ = VCOLOR.get(d["vertical"], ("v1", ""))
        rows += (f'<tr><td><span class="dot {cls}"></span> <code>{html.escape(d["name"])}</code></td>'
                 f'<td class="n">{html.escape(str(kind))}</td><td class="n">{sic}</td>'
                 f'<td>{html.escape(feats)}</td><td class="n">{univ}</td></tr>\n')

    def watch_chips(ws):
        return "".join(
            f'<span class="wchip" title="{html.escape((w.get("note") or "")[:200], quote=True)}">'
            f'{html.escape(w["name"])}<i>{w["cadence"] if isinstance(w["cadence"], str) else str(w["cadence"]) + "m"}</i></span>'
            for w in sorted(ws, key=lambda x: x["name"]))

    watch_html = "".join(
        f'<div class="wgroup"><b>{g}</b> <span class="vmeta">{len(ws)}</span>'
        f'<div class="chips">{watch_chips(ws)}</div></div>'
        for g, ws in sorted(wg.items(), key=lambda kv: -len(kv[1])))

    chan_html = "".join(f'<span class="cchip">{html.escape(l)} <i>{n}</i></span>' for l, n in counts)

    n_det = kg["_counts"]["detectors"]
    n_chan = kg["_counts"]["channels"]
    n_ac = kg["_counts"]["asset_classes"]
    n_di = len(dispatch)
    n_watch = sum(len(v) for v in wg.values())
    today = datetime.date.today().isoformat()

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SignalOS — the dispatch brain</title>
<style>
.viz-root{{color-scheme:light;
 --surface-1:#fcfcfb;--surface-2:#f3f3f1;--text-primary:#0b0b0b;--text-secondary:#52514e;--hair:#dddcd8;
 --v1:#2a78d6;--v2:#eb6834;--v3:#1baf7a;--v4:#eda100;--v5:#e87ba4;--accent:#2a78d6;}}
@media (prefers-color-scheme: dark){{:root:where(:not([data-theme="light"])) .viz-root{{color-scheme:dark;
 --surface-1:#1a1a19;--surface-2:#222220;--text-primary:#ffffff;--text-secondary:#c3c2b7;--hair:#3a3a37;
 --v1:#3987e5;--v2:#d95926;--v3:#199e70;--v4:#c98500;--v5:#d55181;--accent:#3987e5;}}}}
:root[data-theme="dark"] .viz-root{{color-scheme:dark;
 --surface-1:#1a1a19;--surface-2:#222220;--text-primary:#ffffff;--text-secondary:#c3c2b7;--hair:#3a3a37;
 --v1:#3987e5;--v2:#d95926;--v3:#199e70;--v4:#c98500;--v5:#d55181;--accent:#3987e5;}}
html{{background:var(--surface-1)}} body{{margin:0}}
.viz-root{{font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--text-primary);
 background:var(--surface-1);padding:2.2rem 1.2rem 4rem;min-height:100vh}}
main{{max-width:1020px;margin:0 auto}}
h1{{font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;font-size:1.9rem;margin:.2rem 0 .4rem;text-wrap:balance}}
h2{{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-secondary);margin:0 0 .6rem}}
.sub{{color:var(--text-secondary);max-width:78ch;margin:0 0 1.4rem}}
.layer{{background:var(--surface-2);border:1px solid var(--hair);border-radius:8px;padding:1.1rem 1.3rem}}
.flow{{display:flex;flex-direction:column}}
.conn{{display:flex;align-items:center;gap:.6rem;color:var(--text-secondary);font-size:.78rem;padding:.35rem 0 .35rem 1.3rem}}
.conn::before{{content:"";display:block;width:2px;height:2.2rem;background:var(--hair);margin-right:.35rem}}
.statrow{{display:flex;flex-wrap:wrap;gap:1.6rem;margin:.9rem 0 1.6rem}}
.stat b{{display:block;font-size:1.5rem;font-variant-numeric:tabular-nums}}
.stat span{{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:var(--text-secondary)}}
.chips{{display:flex;flex-wrap:wrap;gap:5px;margin-top:.45rem}}
.cchip,.wchip{{font:12px/1.5 ui-monospace,"SF Mono",Menlo,monospace;border:1px solid var(--hair);
 border-radius:4px;padding:2px 8px;background:var(--surface-1);white-space:nowrap}}
.cchip i,.wchip i{{font-style:normal;color:var(--text-secondary);margin-left:.45em;font-size:11px}}
.det{{font:11.5px/1.45 ui-monospace,"SF Mono",Menlo,monospace;border:1px solid var(--hair);border-radius:4px;
 padding:1.5px 7px;background:var(--surface-1);white-space:nowrap;border-left-width:4px;cursor:default}}
.det.v1{{border-left-color:var(--v1)}}.det.v2{{border-left-color:var(--v2)}}.det.v3{{border-left-color:var(--v3)}}
.det.v4{{border-left-color:var(--v4)}}.det.v5{{border-left-color:var(--v5)}}
.ring{{color:var(--accent);font-size:10px}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
.dot.v1{{background:var(--v1)}}.dot.v2{{background:var(--v2)}}.dot.v3{{background:var(--v3)}}
.dot.v4{{background:var(--v4)}}.dot.v5{{background:var(--v5)}}
.vgroup{{margin:.9rem 0}}.vhead{{display:flex;align-items:baseline;gap:.5rem}}
.vmeta{{color:var(--text-secondary);font-size:.78rem}}
.wgroup{{margin:.8rem 0}}
.brain{{border-left:4px solid var(--accent)}}
.rings{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:.8rem;margin:.8rem 0}}
.ringcard{{background:var(--surface-1);border:1px solid var(--hair);border-radius:6px;padding:.7rem .9rem;font-size:.86rem}}
.ringcard b{{display:block;margin-bottom:.2rem}}
.tablewrap{{overflow-x:auto;border:1px solid var(--hair);border-radius:6px;background:var(--surface-1);margin:.8rem 0 0}}
table{{border-collapse:collapse;width:100%;font-size:.82rem}}
th{{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--text-secondary);text-align:left;font-weight:600}}
th,td{{padding:.4rem .6rem;border-bottom:1px solid var(--hair);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
td.n{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;white-space:nowrap}}
code{{font:12px ui-monospace,Menlo,monospace}}
.note{{color:var(--text-secondary);font-size:.82rem;max-width:80ch}}
details summary{{cursor:pointer;color:var(--accent);font-size:.85rem;margin-top:.5rem}}
.foot{{margin-top:2.2rem;color:var(--text-secondary);font-size:.8rem;border-top:1px solid var(--hair);padding-top:.9rem}}
a{{color:var(--accent)}}
</style></head><body>
<div class="viz-root"><main>
<h1>The dispatch brain</h1>
<p class="sub">How SignalOS decides what to run: primary-source channels feed the always-on watch layer;
when a name needs verification, the dispatcher reads the issuer's profile and queries the knowledge graph
for the detector subset that applies — it never runs everything against everything. Rendered live from the
knowledge graph and registry on every load. Hover any module for its summary.</p>
<div class="statrow">
<div class="stat"><b>{n_chan}</b><span>signal channels</span></div>
<div class="stat"><b>{n_watch}</b><span>watches live</span></div>
<div class="stat"><b>{n_det}</b><span>modules in atlas</span></div>
<div class="stat"><b>{n_di}</b><span>APPLIES_TO contracts</span></div>
<div class="stat"><b>{n_ac}</b><span>asset classes indexed</span></div>
</div>

<div class="flow">
<section class="layer"><h2>1 · Signals in — {n_chan} named primary-source channels</h2>
<div class="chips">{chan_html}</div>
<p class="note">Catalogued in <code>knowledge_graph/signal_channels.json</code>. Doctrine: primary sources
only; a blocked source is DATA MISSING, never zero.</p></section>

<div class="conn">continuous — the cron heartbeat polls on cadence</div>

<section class="layer"><h2>2 · Always-on senses — {n_watch} enabled watches (desk/registry.py)</h2>
{watch_html}
<p class="note">Generators propose, never size. Every watch needs <code>enabled:True</code> or it is
silently dead (the 2026-07-22 lesson).</p></section>

<div class="conn">on demand — a name needs verification (court, DD, print, dislocation)</div>

<section class="layer brain"><h2>3 · The dispatcher — three-ring open-set selection</h2>
<p class="note">Input: an issuer profile <code>{{sic, asset_classes, features}}</code>. Output: the module
subset that applies, with a pre-flight coverage validator and output-side validation (the selector is a
model; its output gets checked, not trusted).</p>
<div class="rings">
<div class="ringcard"><b>Ring 0 — vetted atlas</b>Modules carrying a formal <code>APPLIES_TO</code>
contract ({n_di} today, table below). Deterministic match on SIC / issuer feature / asset class.</div>
<div class="ringcard"><b>Ring 1 — alias + recall floor</b>Named-but-uncontracted modules matched on the
verification <em>attribute</em>, not subject tokens (the OSHA 46&rarr;2 over-fire fix).</div>
<div class="ringcard"><b>Ring 2 — agent-invents</b>No existing module fits: draft one, sandbox it,
promote through the gate. How the atlas grows.</div>
</div>
<details><summary>All {n_di} APPLIES_TO contracts</summary>
<div class="tablewrap"><table>
<tr><th>Module</th><th>Kind</th><th>SIC</th><th>Issuer features (first 3)</th><th>Scope</th></tr>
{rows}</table></div></details></section>

<div class="conn">dispatch returns the applicable subset</div>

<section class="layer"><h2>4 · The atlas — {n_det} modules across {len(by_vert)} verticals</h2>
<p class="note"><span class="ring">&#9673;</span> = carries an APPLIES_TO contract (Ring-0 dispatchable;
hover the badge for its kind). Color = vertical, fixed assignment.</p>
{det_html}</section>

<div class="conn">verdicts flow out</div>

<section class="layer"><h2>5 · What the verdicts feed</h2>
<p class="note" style="max-width:100%">Detector fires &rarr; <b>two-mode diligence</b> &rarr;
<b>independent court + red team</b> (generator never grades itself) &rarr; <b>edge classification</b> with
kill triggers &rarr; <b>frozen calibration calls</b> (detector-linked, graded at the print) &rarr;
<b>entry plan</b> (envelopes; the principal places) &rarr; this UI. Composition doctrine: narrow
high-precision detectors compose by <em>union</em>, never weighted average.</p></section>
</div>

<p class="foot">Rendered {today} · live from <code>knowledge_graph.json</code> + <code>desk/registry.py</code>
· <a href="/">desk home</a> · <a href="/static/atlas.html">thesis atlas</a></p>
</main></div></body></html>"""
