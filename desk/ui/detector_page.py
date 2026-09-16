"""detector_page — /detector/{name}: a SignalOS detector's definition + its PREDICTION TRACK RECORD.

Completes the loop. Forward: a prediction's calibration record carries `detectors` (which ran to
generate it). Reverse (here): a detector page shows the definition (registry watcher + KG inventory)
AND every prediction it generated, how each graded, and its aggregate Brier — the detector's own
calibrated track record.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def esc(x):
    return html.escape(str(x if x is not None else ""))


def _meta(name):
    w = None
    try:
        from desk.registry import WATCHES
        w = next((x for x in WATCHES if x.get("name") == name), None)
    except Exception:
        pass
    kg = None
    try:
        inv = json.loads((ROOT / "knowledge_graph" / "knowledge_graph.json").read_text()).get("detector_inventory", [])
        kg = next((d for d in inv if d.get("name") == name), None)
    except Exception:
        pass
    return w, kg


def _predictions(name):
    out = []
    p = ROOT / "desk" / "data" / "calibration_ledger.jsonl"
    if p.exists():
        for l in p.read_text().splitlines():
            if not l.strip():
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if name in (r.get("detectors") or []):
                out.append(r)
    return out


def render(name: str) -> str:
    w, kg = _meta(name)
    preds = _predictions(name)
    resolved = [r for r in preds if r.get("resolution") and isinstance(r.get("our_p"), (int, float))]
    briers = [(r["our_p"] - r["resolution"]["y"]) ** 2 for r in resolved]
    avg_b = sum(briers) / len(briers) if briers else None

    S = []
    S.append(f'<div class="hd"><h1>{esc(name)}</h1><span class="tag">detector</span></div>')
    if not (w or kg or preds):
        S.append(f'<div class="empty">No detector named <b>{esc(name)}</b> is registered or in the knowledge graph, '
                 'and no prediction references it.</div>')
    else:
        # DEFINITION
        S.append('<section><h2>What it is</h2>')
        note = (w or {}).get("note") or (kg or {}).get("summary") or "(no description on file)"
        S.append(f'<div class="def">{esc(note)}</div>')
        rows = []
        if w:
            rows.append(("Runs", f'{" ".join(w.get("cmd", []))} · {esc(w.get("cadence"))}'))
            if w.get("asset_class"):
                rows.append(("Asset class", w.get("asset_class")))
            if w.get("log"):
                rows.append(("Log", w.get("log")))
        if kg:
            rows.append(("Vertical", kg.get("vertical")))
            rows.append(("File", kg.get("file")))
            if kg.get("category"):
                rows.append(("Category", kg.get("category")))
            if kg.get("likely_signal_channels"):
                rows.append(("Channels", ", ".join(kg.get("likely_signal_channels"))))
        for k, v in rows:
            S.append(f'<div class="kv"><span class="k">{esc(k)}</span><span class="mono">{esc(v)}</span></div>')
        S.append('</section>')

        # TRACK RECORD — the reverse loop
        S.append('<section><h2>Prediction track record</h2>')
        if avg_b is not None:
            bcls = "good" if avg_b < 0.25 else "bad"
            S.append(f'<div class="trk"><b>{len(resolved)}</b> graded · aggregate Brier '
                     f'<b class="{bcls}">{avg_b:.3f}</b> · <b>{len(preds)-len(resolved)}</b> open '
                     '<span class="mut">— how the predictions this detector generated actually resolved</span></div>')
        else:
            S.append('<div class="trk"><span class="mut">No graded predictions yet — none of its calls have resolved.</span></div>')
        if preds:
            S.append('<table><tr><th>Name</th><th>Catalyst</th><th>Our call</th><th>Result</th><th>Brier</th></tr>')
            for r in sorted(preds, key=lambda x: x.get("cat_date") or "", reverse=True):
                res = r.get("resolution")
                if res:
                    oc = res.get("outcome", "")
                    badge = f'<span class="pill {"win" if oc=="FAVORABLE" else "miss" if oc=="UNFAVORABLE" else ""}">{esc(oc.title())}</span>'
                    b = f'{(r["our_p"]-res["y"])**2:.3f}' if isinstance(r.get("our_p"), (int, float)) else "—"
                else:
                    badge, b = '<span class="pill">open</span>', "—"
                p = r.get("our_p")
                pc = f'{int(round(p*100))}%' if isinstance(p, (int, float)) else "—"
                S.append(f'<tr><td><a href="/ticker/{esc(r.get("ticker"))}" target="_blank" class="tkl">{esc(r.get("ticker"))}</a></td>'
                         f'<td class="cat">{esc((r.get("catalyst") or "")[:70])}</td>'
                         f'<td class="mono">{pc}</td><td>{badge}</td><td class="mono">{b}</td></tr>')
            S.append('</table>')
        S.append('</section>')

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(name)} · detector</title>
<style>
:root{{--bg:#0b0e14;--panel:#131722;--line:#252b3b;--fg:#d7dce5;--mut:#7d869c;--blu:#3d7eff;--grn:#26a17b;--red:#e0524a;--vio:#9a6bff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
.wrap{{max-width:820px;margin:0 auto;padding:26px 22px 80px}}
.bk{{margin-bottom:14px}} a{{color:var(--blu);text-decoration:none}} a:hover{{text-decoration:underline}}
.hd{{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid var(--line);padding-bottom:14px}}
.hd h1{{font-size:23px;margin:0;font-family:ui-monospace,Menlo,monospace}} .tag{{color:var(--vio);font:700 11px ui-monospace,Menlo,monospace;border:1px solid var(--line);border-radius:20px;padding:2px 10px}}
section{{margin:24px 0}} h2{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--mut);margin:0 0 10px;font-weight:600}}
.def{{background:var(--panel);border-left:3px solid var(--vio);border-radius:6px;padding:12px 15px;font-size:14px}}
.kv{{display:flex;gap:12px;font-size:12.5px;padding:4px 0;border-bottom:1px solid var(--line)}} .kv .k{{color:var(--mut);width:100px;flex-shrink:0;text-transform:uppercase;font-size:10px;letter-spacing:.08em;padding-top:2px}}
.trk{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 14px;font-size:13px;margin-bottom:10px}} .trk b{{font-variant-numeric:tabular-nums}} .trk .good{{color:var(--grn)}} .trk .bad{{color:var(--red)}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}} th{{text-align:left;color:var(--mut);font-size:10px;text-transform:uppercase;letter-spacing:.06em;padding:6px 8px;border-bottom:1px solid var(--line)}}
td{{padding:6px 8px;border-bottom:1px solid #1b2030;vertical-align:top}} .mono{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}} .cat{{color:var(--mut)}} .tkl{{font-weight:600}}
.pill{{font-size:10px;padding:1px 8px;border-radius:20px;border:1px solid var(--line);color:var(--mut)}} .pill.win{{color:var(--grn);border-color:var(--grn)}} .pill.miss{{color:var(--red);border-color:var(--red)}}
.mut{{color:var(--mut)}} .empty{{color:var(--mut);padding:30px 0}}
</style></head><body>
  <div class="wrap"><div class="bk"><a href="javascript:history.back()">← back</a></div>{''.join(S)}</div>
</body></html>"""
