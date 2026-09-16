"""thesis_index — the persistent THESIS INDEX. Renders thesis_index.html (the 'theses' tab).

Born 2026-07-12 (user): one page that shows EVERY thesis we've run — all ~40 ledger sleeves +
the by-edge-class buckets for un-sleeved names — with each name's current verdict, edge class,
and a one-line thesis, every ticker linking to its /ticker/{sym} dossier. The whole research
corpus at a glance (GLP-1, K-beauty, EM banks, deep-value, muni, … not just the latest sweep).

Data: desk/data/research_ledger.json (the book) + edge_source_map.json (classes).
    python3 -m desk.thesis_index        # -> desk/ui/static/thesis_index.html
READ-ONLY.
"""
from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
EMAP = ROOT / "desk" / "data" / "edge_source_map.json"
OUT = ROOT / "desk" / "ui" / "static" / "thesis_index.html"

# human-readable thesis titles + one-line blurbs for the known sleeves (fallback = title-case the key)
SLEEVE_META = {
    "glp1_medtech":        ("GLP-1 — MedTech & Beneficiaries", "obesity-drug ecosystem: device, delivery, and downstream-demand plays"),
    "glp1_honesty":        ("GLP-1 — Honesty / Muscle-Preservation", "the enobosarm/lean-mass angle + honest-vs-hype catalyst screen (STVN)"),
    "cosmeceutical":       ("K-Beauty / Cosmeceuticals", "clinical/active skincare de-anchored from GLP-1 — COSMECCA/COSMAX/K-beauty ODM"),
    "aesthetics":          ("Aesthetics — Injectables & Devices", "neurotoxins/fillers/energy devices — EOLS/INMD/HUGEL/GALD"),
    "male_aesthetics":     ("Aesthetics — Male Market", "the male-TAM DD: DTC funnel (LFMD/HIMS) vs the priced-out medical leg"),
    "luxury_champions":    ("Luxury Champions", "brand-heat leaders — LVMH/Hermès/Richemont, quality-at-a-price"),
    "deep_value":          ("Deep Value — Core", "TTM-hardened cheap-finder + trap-filter survivors"),
    "deep_value_thesis1":  ("Deep Value — THESIS-1 Basket", "the original diligenced basket: GCT/DFIN/EVER/EPAM/BKE/SBH/BKE/CRCT"),
    "k_shaped_top":        ("K-Shaped — Top", "premiumization winners in a bifurcating consumer"),
    "k_shaped_bottom":     ("K-Shaped — Bottom", "value/trade-down beneficiaries (SFM-class)"),
    "hnw_shovels":         ("HNW Picks-&-Shovels", "sell-the-shovels to the wealth-management boom"),
    "insurance_brokers":   ("Insurance Brokers", "capital-light compounders / fee annuities"),
    "hnw_insurers":        ("HNW Insurers", "high-net-worth P&C / specialty carriers"),
    "country_risk_arb":    ("International — Country-Risk Arb", "market-implied CRP wider than structural; insulated hard-currency vehicles"),
    "intl_risk":           ("International — Risk Mispricing", "the wide-premium-is-often-deserved screen (ASR/OTP/PAC/KAP)"),
    "war_unwind":          ("Ukraine — War Unwind", "peace-optionality convexity, sized for permanent-impairment tails"),
    "ukraine_recovery":    ("Ukraine — Recovery", "post-war reconstruction; the Step-Up B bond is the cleanest convexity"),
    "ukraine_reconstruction_b": ("Ukraine — Reconstruction (Bond)", "the GDP-warrant-dead / step-up-bond reconstruction leg"),
    "georgia_banks":       ("Georgian Banks", "BGEO/TBC — funding moat vs the political tail"),
    "frontier_banks":      ("Frontier Banks", "the two-leg EM-bank method on frontier names"),
    "contrarian_credit":   ("Contrarian Credit / Alt-Managers", "OWL/APO — owner-cash multiple vs the sector optic"),
    "quality_carry":       ("Quality Carry (RP_FAIR)", "fairly-paid, bounded risk — paid to hold, edge is overlay"),
    "ai_application":      ("AI Application Layer", "who monetizes AI vs who gets disrupted"),
    "ai_sass_dislocation": ("AI × SaaS Dislocation", "margin compression on AI-impacted SaaS/consultancies (HUBS/CTSH)"),
    "grid_bottleneck":     ("Grid Bottleneck", "electrification/datacenter load → grid-equipment scarcity"),
    "trade_data":          ("Trade-Data Nowcast", "Census imports / customs-BOL / federal award-flow that lead the print"),
    "import_inversion":    ("Import-Anomaly Inversion", "HS4 import accel/rollover as a demand tell"),
    "mall_recovery":       ("Mall / Venue Recovery", "A-mall-skewed retailers at mall-retail multiples"),
    "gov_services_recovery": ("Gov-Services Recovery", "post-DOGE federal-services de-rate (ICFI)"),
    "detector_inversion":  ("Detector Inversion", "names surfaced by inverting a detector's fire condition"),
    "dispersion_slate":    ("Dispersion Slate", "single-name vol / dispersion candidates"),
    "catalyst_sleeve":     ("Catalyst Sleeve", "dated-catalyst handicaps"),
    "event_arb":           ("Event / Merger Arb", "contested deals & special situations (NNDM)"),
    "preferred_oddlot":    ("Preferred / Baby-Bond Odd-Lot", "$25-par preferreds too small for institutions to price — discount-to-par × illiquidity carry"),
    "russell_recon":       ("Russell Reconstitution (FLOW)", "the year's biggest price-insensitive forced flow — adds/deletes/migration air-pockets each June"),
    "kalshi_divergence":   ("Kalshi Divergence (INFO)", "prediction-market P vs equity-implied — crowd nowcast of the print + lognormal price divergences"),
    "slate2":              ("Screen Slate 2", "batch-screen cohort"),
    "slate4":              ("Screen Slate 4", "batch-screen cohort"),
    "held":                ("Held (legacy tag)", "positions tagged before the sleeve taxonomy"),
}

# verdict → (tone, group). owned/ownable=teal, tracking=gold, anti-portfolio=coral
VERDICT_TONE = {
    "HELD": ("held", "own"), "OWNABLE": ("ownable", "own"), "STARTER": ("starter", "own"),
    "WATCH": ("watch", "track"), "WAIT": ("wait", "track"), "NOT_YET": ("notyet", "track"),
    "TO_DILIGENCE": ("todil", "track"), "AVOID": ("avoid", "avoid"), "SHORT": ("short", "avoid"),
}
EDGE_ACCENT = {"FLOW": "#3fb6a8", "INFO": "#c9922e", "VALUE": "#5b8def", "CARRY": "#8a7fd6",
               "CONVEXITY": "#c56b6b", "EXCLUSION": "#6b7280", "UNCLASSIFIED": "#4b5563"}


def esc(x):
    return html.escape(str(x if x is not None else ""))


def _title(key):
    if key in SLEEVE_META:
        return SLEEVE_META[key]
    return (key.replace("_", " ").title(), "")


def build():
    led = json.loads(LEDGER.read_text()).get("names", [])
    # group: sleeved names by sleeve; un-sleeved by edge-class bucket
    by_sleeve = defaultdict(list)
    for n in led:
        s = n.get("sleeve")
        if s and s != "?":
            by_sleeve[("sleeve", s)].append(n)
        else:
            by_sleeve[("edge", n.get("edge_source") or "UNCLASSIFIED")].append(n)

    # order: real theses first (by size desc), then the edge-class buckets (by size desc)
    sleeve_groups = sorted([k for k in by_sleeve if k[0] == "sleeve"], key=lambda k: -len(by_sleeve[k]))
    edge_groups = sorted([k for k in by_sleeve if k[0] == "edge"], key=lambda k: -len(by_sleeve[k]))

    # top stats
    N = len(led)
    vcount = defaultdict(int)
    for n in led:
        vcount[n.get("verdict", "?")] += 1
    own = sum(vcount[v] for v in ("HELD", "OWNABLE", "STARTER"))
    track = sum(vcount[v] for v in ("WATCH", "WAIT", "NOT_YET", "TO_DILIGENCE"))
    avoid = vcount.get("AVOID", 0) + vcount.get("SHORT", 0)
    ecount = defaultdict(int)
    for n in led:
        ecount[n.get("edge_source") or "UNCLASSIFIED"] += 1

    P = []
    P.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Thesis Index</title>
<style>
:root{{--bg:#0b0e12;--panel:#14181d;--panel2:#1a1f25;--line:#242a31;--ink:#e8ebee;--dim:#828a94;--faint:#5c646e;
--own:#35c98f;--track:#d9a441;--avoid:#e0736a;--blue:#5b8def;--violet:#8b7cf6}}
*{{box-sizing:border-box}}body{{margin:0}}
.wrap{{max-width:1240px;margin:0 auto;padding:24px 22px 90px;font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
h1{{font-size:24px;margin:0 0 3px;letter-spacing:-.02em;font-weight:650}} .sub{{color:var(--dim);font-size:13px;margin:0 0 20px}}
.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:10px}}
@media(max-width:720px){{.stats{{grid-template-columns:1fr 1fr}}}}
.stats>div{{background:var(--panel);padding:13px 15px}} .stats .n{{font:660 21px/1 ui-monospace,Menlo,monospace}} .stats .l{{font-size:10.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;margin-top:5px}}
.stats .own{{color:var(--own)}} .stats .track{{color:var(--track)}} .stats .avoid{{color:var(--avoid)}}
.edgebar{{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 20px}}
.edgechip{{font-size:11px;padding:5px 11px;border-radius:20px;border:1px solid var(--line);background:var(--panel)}}
.edgechip b{{font-family:ui-monospace,Menlo,monospace}}
h2{{font-size:11.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--dim);margin:26px 0 11px;font-weight:600}}
.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
@media(max-width:820px){{.cards{{grid-template-columns:1fr}}}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.card.edge{{border-style:dashed}}
.chd{{display:flex;align-items:baseline;gap:9px;margin-bottom:3px}}
.chd .t{{font-weight:650;font-size:15px;letter-spacing:-.01em}} .chd .c{{margin-left:auto;font:600 12px ui-monospace,Menlo,monospace;color:var(--dim)}}
.blurb{{font-size:11.5px;color:var(--dim);line-height:1.45;margin-bottom:10px}}
.mix{{display:flex;height:4px;border-radius:3px;overflow:hidden;margin-bottom:11px;background:#0c0f13}}
.mix>span{{display:block;height:100%}} .mix .own{{background:var(--own)}} .mix .track{{background:var(--track)}} .mix .avoid{{background:var(--avoid)}}
.names{{display:flex;flex-direction:column;gap:1px}}
.nm{{display:grid;grid-template-columns:auto auto 1fr;gap:9px;align-items:baseline;padding:5px 0;border-top:1px solid var(--line)}}
.nm:first-child{{border-top:0}}
.tk{{font:700 12.5px ui-monospace,Menlo,monospace}} .tk a{{color:var(--ink);text-decoration:none;border-bottom:1px dotted var(--faint)}} .tk a:hover{{color:#fff}}
.vb{{font-size:9px;font-weight:700;letter-spacing:.03em;padding:1px 6px;border-radius:10px;white-space:nowrap;justify-self:start}}
.vb.own{{color:#8ee5c1;background:rgba(53,201,143,.15)}} .vb.track{{color:#eccb8a;background:rgba(217,164,65,.15)}} .vb.avoid{{color:#f0a89f;background:rgba(224,115,106,.15)}}
.th{{font-size:11.5px;color:var(--dim);line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.ec{{font-size:8.5px;font-weight:700;letter-spacing:.04em;color:var(--faint)}}
.foot{{font-size:11px;color:var(--faint);margin-top:26px;border-top:1px solid var(--line);padding-top:14px;line-height:1.6}}
</style></head><body>
<div class="wrap">
  <h1>Thesis Index</h1>
  <p class="sub">Every thesis in the book — {len(sleeve_groups)} named sleeves + {len(edge_groups)} edge-class buckets, {N} names, each linking to its dossier. The whole corpus at a glance.</p>
  <div class="stats">
    <div><div class="n">{N}</div><div class="l">Names</div></div>
    <div><div class="n">{len(sleeve_groups)}</div><div class="l">Theses (sleeves)</div></div>
    <div><div class="n own">{own}</div><div class="l">Held / Ownable</div></div>
    <div><div class="n track">{track}</div><div class="l">Watch / Tracking</div></div>
    <div><div class="n avoid">{avoid}</div><div class="l">Anti-portfolio</div></div>
  </div>
  <div class="edgebar">""")
    for e in ["FLOW", "INFO", "VALUE", "CARRY", "CONVEXITY", "EXCLUSION", "UNCLASSIFIED"]:
        if ecount.get(e):
            P.append(f'<span class="edgechip" style="border-color:{EDGE_ACCENT[e]}55">{e} <b>{ecount[e]}</b></span>')
    P.append('</div>')

    def _card(group_key, extra=""):
        kind, key = group_key
        names = by_sleeve[group_key]
        if kind == "sleeve":
            title, blurb = _title(key)
        else:
            title, blurb = f"◇ {key} — un-sleeved", f"names classified {key} but not yet in a named thesis sleeve"
        # verdict mix
        g = defaultdict(int)
        for n in names:
            g[VERDICT_TONE.get(n.get("verdict"), ("", "track"))[1]] += 1
        tot = len(names) or 1
        mix = "".join(f'<span class="{grp}" style="width:{g[grp]/tot*100:.0f}%"></span>' for grp in ("own", "track", "avoid") if g[grp])
        # order names: own > track > avoid, then ticker
        order = {"own": 0, "track": 1, "avoid": 2}
        names_sorted = sorted(names, key=lambda n: (order.get(VERDICT_TONE.get(n.get("verdict"), ("", "track"))[1], 1), n.get("ticker", "")))
        rows = []
        for n in names_sorted:
            tone, grp = VERDICT_TONE.get(n.get("verdict"), ("watch", "track"))
            th = (n.get("thesis") or n.get("conviction") or "").strip()
            rows.append(
                f'<div class="nm"><span class="tk"><a href="/ticker/{esc(n.get("ticker"))}" target="_blank">{esc(n.get("ticker"))}</a></span>'
                f'<span class="vb {grp}">{esc(n.get("verdict"))}</span>'
                f'<span class="th" title="{esc(th)}"><span class="ec">{esc(n.get("edge_source") or "")}</span> · {esc(th[:120])}</span></div>')
        return (f'<div class="card {extra}"><div class="chd"><span class="t">{esc(title)}</span>'
                f'<span class="c">{len(names)}</span></div>'
                f'{f"<div class=blurb>{esc(blurb)}</div>" if blurb else ""}'
                f'<div class="mix">{mix}</div><div class="names">{"".join(rows)}</div></div>')

    P.append('<h2>Theses</h2><div class="cards">')
    for gk in sleeve_groups:
        P.append(_card(gk))
    P.append('</div>')

    if edge_groups:
        P.append('<h2>Un-sleeved — grouped by edge class</h2><div class="cards">')
        for gk in edge_groups:
            P.append(_card(gk, extra="edge"))
        P.append('</div>')

    P.append('<div class="foot">Every ticker links to its /ticker/{sym} dossier (all its DD + analysis). Verdict tones: '
             '<b style="color:var(--own)">held/ownable/starter</b> · <b style="color:var(--track)">watch/wait/not-yet/to-diligence</b> · '
             '<b style="color:var(--avoid)">avoid (anti-portfolio)</b>. Reads the research ledger + edge-source map; regenerates on every ledger change. '
             'Un-sleeved names are classified by edge but not yet in a named thesis — surfaced here, never hidden.</div>')
    P.append('</div></body></html>')
    return "\n".join(P)


def main():
    OUT.write_text(build())
    print(f"[thesis_index] rendered -> {OUT}")


if __name__ == "__main__":
    main()
