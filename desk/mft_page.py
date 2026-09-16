"""mft_page — renders the MFT sleeve dashboard (the MFT tab).

Reads the live cohort + the forward-test ledger + the signal specs and renders
desk/ui/static/mft.html: the thesis, the two calibration gauges, the live
frozen predictions, the cohort with gate pills, the signal classes, and the
dropped-names slaughterhouse. Regenerated hourly + on demand.

    python3 -m desk.mft_page
READ-ONLY.
"""
from __future__ import annotations

import datetime
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COHORT = ROOT / "desk" / "data" / "mft_cohort.json"
LEDGER = ROOT / "desk" / "data" / "mft_forward_ledger.jsonl"
OUT = ROOT / "desk" / "ui" / "static" / "mft.html"


def _rows():
    if not LEDGER.exists():
        return []
    return [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]


def _brier(rows, layer):
    g = [r for r in rows if r["layer"] == layer and r.get("outcome") is not None]
    if not g:
        return {"n": 0, "brier": None}
    b = sum((r["our_p"] - r["outcome"]) ** 2 for r in g) / len(g)
    coin = sum((0.5 - r["outcome"]) ** 2 for r in g) / len(g)
    return {"n": len(g), "brier": round(b, 3), "coin": round(coin, 3), "beats": b < coin}


CSS = """
:root{
  --ground:#FAFBFA; --panel:#FFFFFF; --ink:#14201C; --dim:#5A655F; --line:#DCE2DE; --faint:#F1F5F2;
  --accent:#0E6E5C; --pass:#1C6B45; --fail:#A3311C; --pend:#8A6D1F; --paper:#3A5A8C;
}
*{box-sizing:border-box}
body{font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;background:var(--ground);color:var(--ink);
     max-width:980px;margin:0 auto;padding:26px 22px 70px;line-height:1.5;font-size:14.5px;-webkit-font-smoothing:antialiased}
.eyebrow{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:700}
h1{font-size:27px;letter-spacing:-.01em;margin:5px 0 4px;text-wrap:balance}
.lede{color:var(--dim);font-size:14px;max-width:74ch;margin:0 0 6px}
.statusbar{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 26px}
.pill{font-size:10.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:3px 9px;border-radius:100px;color:#fff;white-space:nowrap}
.pill.paper{background:var(--paper)} .pill.pass{background:var(--pass)} .pill.fail{background:var(--fail)}
.pill.pend{background:var(--pend)} .pill.accent{background:var(--accent)} .pill.ghost{background:#fff;color:var(--dim);border:1px solid var(--line)}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.11em;border-bottom:2px solid var(--ink);padding-bottom:5px;margin:34px 0 12px;display:flex;justify-content:space-between;align-items:baseline}
h2 .sub{font-size:10.5px;color:var(--dim);font-weight:400;letter-spacing:.02em;text-transform:none}
.mono{font-family:ui-monospace,'SF Mono',Menlo,monospace;font-variant-numeric:tabular-nums}
.gauges{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:640px){.gauges{grid-template-columns:1fr}}
.gauge{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:15px 18px}
.gauge .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--dim);font-weight:700}
.gauge .big{font-size:30px;font-weight:800;letter-spacing:-.02em;margin:2px 0}
.gauge .foot{font-size:12px;color:var(--dim)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:640px){.cards{grid-template-columns:1fr}}
.pcard{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:13px 16px}
.pcard.nowcast{border-left-color:var(--accent)} .pcard.price{border-left-color:var(--paper)}
.pcard .top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.pcard .tkr{font-size:16px;font-weight:800}
.pcard .p{font-size:22px;font-weight:800}
.pcard .est{font-size:13px;margin:5px 0 3px}
.pcard .basis{font-size:11.5px;color:var(--dim);max-width:48ch}
.pcard .when{font-size:11px;color:var(--pend);font-weight:700;margin-top:5px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--dim);border-bottom:2px solid var(--ink);padding:6px 8px;font-weight:700}
td{padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:top}
td.tkr{font-weight:800;white-space:nowrap}
.fitbar{display:inline-block;height:7px;border-radius:4px;background:var(--accent);vertical-align:middle}
.fitwrap{display:inline-block;width:52px;height:7px;background:var(--faint);border-radius:4px;margin-right:6px;vertical-align:middle}
.scard{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 15px;margin:8px 0}
.scard h3{font-size:14px;margin:0 0 3px}
.scard p{font-size:12.5px;color:var(--dim);margin:2px 0}
.drop{font-size:12.5px;color:var(--dim);padding:4px 0;border-bottom:1px solid var(--faint)}
.drop b{color:var(--ink)}
.note{background:var(--faint);border:1px solid var(--line);border-radius:8px;padding:13px 16px;font-size:13px;max-width:80ch;margin:10px 0}
.note b{color:var(--accent)}
.gates{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}
@media(max-width:640px){.gates{grid-template-columns:1fr}}
.gate{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:9px 12px;font-size:12.5px}
.gate .n{font-weight:800;color:var(--accent)}
.foot-meta{color:var(--dim);font-size:11.5px;border-top:1px solid var(--line);margin-top:40px;padding-top:12px}
"""


def render():
    cohort = json.loads(COHORT.read_text()) if COHORT.exists() else {"names": {}}
    names = cohort.get("names", {})
    dropped = cohort.get("_dropped", {})
    sig = cohort.get("_signal_classes", {})
    rows = _rows()
    today = datetime.date.today()
    L1, L2 = _brier(rows, "nowcast"), _brier(rows, "price")
    live = [r for r in rows if r.get("outcome") is None]

    def g(v):
        return html.escape(str(v))

    o = [f"<style>{CSS}</style>",
         "<div class='eyebrow'>SignalOS · research sleeve</div>",
         "<h1>Medium-Frequency Trading</h1>",
         "<div class='lede'>Front-running the analyst's next revision on lightly-covered smallcaps — the days-to-weeks clock between HFT and the fundamental book. Edge source: <b>analyst latency</b>. Crystallization: the print or the revision itself. Nothing here trades real capital until the forward test shows edge net of short-term tax.</div>",
         "<div class='statusbar'>",
         "<span class='pill paper'>PAPER — research phase</span>",
         f"<span class='pill ghost'>{len(names)} cohort names</span>",
         f"<span class='pill ghost'>{len(live)} live predictions</span>",
         f"<span class='pill {'accent' if (L1['n'] or L2['n']) else 'ghost'}'>calibration n={L1['n']+L2['n']}</span>",
         f"<span class='pill ghost'>as of {today.isoformat()}</span>",
         "</div>"]

    # calibration gauges
    def gauge(name, br, cadence):
        if br["n"] == 0:
            body = "<div class='big mono'>—</div><div class='foot'>0 graded · first grade " + cadence + "</div>"
        else:
            verdict = ("BEATS coin" if br.get("beats") else "≤ coin")
            body = (f"<div class='big mono'>{br['brier']}</div>"
                    f"<div class='foot'>n={br['n']} · vs coin {br['coin']} · <b style='color:{'var(--pass)' if br.get('beats') else 'var(--fail)'}'>{verdict}</b></div>")
        return f"<div class='gauge'><div class='lbl'>{name}</div>{body}</div>"

    o.append("<h2>Forward-test calibration <span class='sub'>the only thing that earns this sleeve capital</span></h2>")
    o.append("<div class='gauges'>")
    o.append(gauge("Layer 1 · nowcast accuracy", L1, "≈ Jul 10 (BKE)"))
    o.append(gauge("Layer 2 · price edge", L2, "post-print"))
    o.append("</div>")
    o.append("<div class='note'><b>Two layers, on purpose.</b> Layer 1 (monthly cadence, fast n) asks <i>can we nowcast the operating metric</i>; Layer 2 (quarterly) asks <i>does being early move the price after tax</i>. Layer 1 must clear first — being right on the number is worthless if the price already knows (the FLL null). Real capital waits for Layer 2 to beat coin <i>net of ~54% short-term tax</i>.</div>")

    # live frozen predictions
    o.append("<h2>Live frozen predictions <span class='sub'>recorded before the event · append-only</span></h2>")
    if live:
        o.append("<div class='cards'>")
        for r in sorted(live, key=lambda x: x.get("event_date", "")):
            try:
                dd = (datetime.date.fromisoformat(r["event_date"]) - today).days
                when = f"resolves {r['event_date']} · in {dd}d" if dd >= 0 else f"awaiting grade ({r['event_date']})"
            except Exception:
                when = r.get("event_date", "")
            o.append(
                f"<div class='pcard {g(r['layer'])}'>"
                f"<div class='top'><span class='tkr'>{g(r['name'])}</span>"
                f"<span class='p mono'>{g(r['our_p'])}</span></div>"
                f"<div class='est mono'>{g(r.get('estimate') or '')}</div>"
                f"<div class='basis'>{g(r.get('note') or r.get('data_used') or '')[:220]}</div>"
                f"<div class='when'>{g(when)}</div></div>")
        o.append("</div>")
    else:
        o.append("<div class='note'>No live predictions — the ledger is empty.</div>")

    # cohort
    o.append("<h2>The cohort <span class='sub'>survivors of the 4-gate screen · weighted to monthly cadence</span></h2>")
    o.append("<table><tr><th>Name</th><th>Cap</th><th>Cad.</th><th>Analysts</th><th>Gate 2 (vol/lev)</th><th>Nowcast feed</th><th>Fit</th></tr>")
    for tk, c in sorted(names.items(), key=lambda x: -(x[1].get("fit", 0) or 0)):
        fit = c.get("fit", 0) or 0
        gate = c.get("gate", "")
        gpass = "PASS" in str(gate).upper() or "trade" not in str(gate).lower()
        gate_pill = f"<span class='pill {'pass' if 'PASS' in str(gate).upper() else 'fail'}' style='font-size:9px'>{g(gate)[:34]}</span>"
        feed = c.get("feed") or c.get("nowcast_feed") or ""
        cad = c.get("cadence", "")
        o.append(
            f"<tr><td class='tkr'>{g(tk)}</td><td class='mono'>{g(c.get('cap',''))}</td>"
            f"<td>{g(cad)}</td><td class='mono'>{g(c.get('analysts',''))}</td>"
            f"<td>{gate_pill}</td>"
            f"<td style='font-size:12px'>{g(str(feed)[:64])}</td>"
            f"<td><span class='fitwrap'><span class='fitbar' style='width:{int(fit*10)}%'></span></span>"
            f"<span class='mono'>{fit}</span></td></tr>")
    o.append("</table>")

    # signal classes
    o.append("<h2>Signal classes <span class='sub'>the free feeds · each must pass its own latency event-study</span></h2>")
    feeds = [
        ("Census imports (HS × country)", "import_nowcast.py · ~5wk lag · weekly", "importers w/ narrow HS codes (HBB, WEYS)"),
        ("State gaming monthlies", "gaming_monthlies.py · ~2wk lag · per-operator", "route ops / single-state casinos (ACEL) — FLL latency = NULL, nowcast-only"),
        ("State cannabis excise", "MI/AZ/OH monthly · nowcast-only", "single-state MSOs (VEXTF, AAWH) — data rich, equities un-tradeable"),
        ("Consumer review velocity", "review_velocity_spec.json · Target-search workhorse · DAILY", "the scuttlebutt leg — flipped HBB brand-death→distribution; the kettle test"),
        ("Monthly-comp reporters", "BKE press release · monthly · the crystallization IS the data", "predict the print from a leading signal, or trade the reaction"),
    ]
    for name, meta, use in feeds:
        o.append(f"<div class='scard'><h3>{g(name)}</h3><p class='mono'>{g(meta)}</p><p>{g(use)}</p></div>")

    # dropped
    o.append("<h2>Dropped — the gate slaughterhouse <span class='sub'>Gate 2 (leverage/vol) is what kills most names, not the nowcast</span></h2>")
    drops = [("FLL","the null — 9.4x levered + refi tape buries the signal (nowcast worked fine)"),
             ("CNTY","7x net debt + strategic review — the FLL failure mode"),
             ("MCRI","13 analysts — already nowcast"),
             ("GDEN","VICI take-private (corporate-action tape)"),
             ("LCUT","5.8% daily vol + >3x levered — FLL mode in an importer"),
             ("MSO equities","cannabis data is the cleanest monthly feed in the US, but the equities are 6% daily-vol PINK — nowcast-only, un-tradeable")]
    for tk, why in drops:
        o.append(f"<div class='drop'><b>{g(tk)}</b> — {g(why)}</div>")

    # edge condition + tax
    o.append("<h2>The edge condition <span class='sub'>all four required — the FLL null defined them</span></h2>")
    o.append("<div class='gates'>"
             "<div class='gate'><span class='n'>1 ·</span> Thin coverage (1–4 analysts) — the analyst is stale &amp; beatable</div>"
             "<div class='gate'><span class='n'>2 ·</span> Low idiosyncratic vol (&lt;1.5%/day, &lt;3x levered, no live corp-action) — <b>the binding gate</b></div>"
             "<div class='gate'><span class='n'>3 ·</span> A nowcastable metric with free public lead data</div>"
             "<div class='gate'><span class='n'>4 ·</span> A crystallization clock (print / revision date)</div></div>")
    o.append("<div class='note'><b>The tax constraint.</b> Medium-frequency = short holding periods = short-term gains at ~54% CA all-in (or ~37% while they displace the earmarked September loss pool, which is finite). An MFT edge must clear a <i>much</i> higher bar than the fair-carry book — which is exactly why this sleeve stays on paper until Layer 2 beats coin net of tax across adequate n.</div>")

    o.append(f"<div class='foot-meta'>Paper research sleeve · no real capital deployed · regenerated by desk.mft_page · "
             f"cohort {len(names)} names, {len(rows)} freezes, calibration n={L1['n']+L2['n']} · {today.isoformat()}</div>")
    return "".join(o)


def main():
    OUT.write_text("<title>MFT Sleeve</title>" + render())
    print(f"[mft_page] rendered -> mft.html")


if __name__ == "__main__":
    main()
