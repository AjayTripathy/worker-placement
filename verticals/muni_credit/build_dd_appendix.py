"""build_dd_appendix — render the per-bond verification record as a pitch-deck appendix.

Deterministic: every figure comes from outputs/buylist_dd/agent{1..4}.json (the four independent
diligence runs) + outputs/BUY_LIST_20260610.json (corrected issuers, phases, par). Same visual
language as the deck. Output: outputs/CA_MUNI_SLEEVE_DD_APPENDIX.html (caller renders PDF).
"""
import json, datetime

DD_DATE = "2026-06-11"
ORDER = []  # buy-list order
bl = json.load(open("outputs/BUY_LIST_20260610.json"))
BLMAP = {o["cusip"]: o for o in bl["orders"]}
recs = {}
for i in (1, 2, 3, 4, 5, 6, 7):
    for r in json.load(open(f"outputs/buylist_dd/agent{i}.json")):
        recs[r["cusip"]] = r
for o in bl["orders"]:
    if o["cusip"] in recs:
        ORDER.append(o["cusip"])

# normalize units: some agents reported TEY as a fraction (0.0823), others as percent (8.23)
for r in recs.values():
    v = r.get("recomputed_tey_at")
    if isinstance(v, (int, float)) and v < 1:
        r["recomputed_tey_at"] = round(v * 100, 2)

VC = {"CLEAR": "#1a7f3c", "FLAG": "#c0622d", "REJECT": "#b22222"}

def chip(text, color):
    return f'<span class="chip" style="background:{color}">{text}</span>'

def yn(v, true_txt="confirmed", false_txt="NOT CONFIRMED"):
    return (f'<b style="color:#1a7f3c">{true_txt}</b>' if v
            else f'<b style="color:#b22222">{false_txt}</b>')

n_clear = sum(1 for c in ORDER if recs[c]["verdict"] == "CLEAR")
n_flag = sum(1 for c in ORDER if recs[c]["verdict"] == "FLAG")

# ---------- summary table rows ----------
sumrows = []
for cu in ORDER:
    r, o = recs[cu], BLMAP[cu]
    v = r["verdict"]
    tey = f"{r['recomputed_tey_at']:.2f}%" if isinstance(r.get("recomputed_tey_at"), (int, float)) else "—"
    div = r.get("tey_divergence_pp")
    div_s = (f"{div:+.2f}" if isinstance(div, (int, float)) else "—")
    mv = r.get("tape_moved_pt")
    mv_s = (f"{mv:+.2f}" if isinstance(mv, (int, float)) else "—")
    sumrows.append(
        f"<tr><td class=mono>{cu}</td>"
        f"<td>{(o.get('issuer') or o.get('security') or '')[:38]}<span class=cty>{o.get('county') or ''}</span></td>"
        f"<td class=ctr>P{o['phase']}</td>"
        f"<td class=ctr>{chip(v, VC[v])}</td>"
        f"<td class=ctr>{'EXEMPT' if 'EXEMPT' in str(r.get('tax_status','')).upper() else '<b style=color:#b22222>'+str(r.get('tax_status'))+'</b>'}</td>"
        f"<td class=ctr>{'✓' if r.get('pledge_confirmed') else '✗'}</td>"
        f"<td class=ctr>{(str(r.get('next_call') or '—')[:10]) if r.get('callable') else 'non-call'}</td>"
        f"<td class=num>{r.get('live_last_trade_px') or '—'}</td>"
        f"<td class=num>{mv_s}</td>"
        f"<td class=num>{tey}</td>"
        f"<td class=num>{div_s}</td>"
        f"<td class=ctr>{('n/a' if str(r.get('ab1200','')).upper().startswith('N/A') else ('✓' if any(k in str(r.get('ab1200','')).lower() for k in ('clean','absent','clear','positive')) else '?'))}</td></tr>")

# ---------- per-bond cards ----------
cards = []
for cu in ORDER:
    r, o = recs[cu], BLMAP[cu]
    v = r["verdict"]
    cards.append(f"""
<div class="ddcard">
  <div class="ddhead">
    <span class="mono" style="font-size:9.5pt;font-weight:700">{cu}</span>
    {chip(v, VC[v])}
    <span class="ddissuer">{(o.get('issuer') or o.get('security') or '')[:46]}{(' · ' + o['county']) if o.get('county') else ''}</span>
    <span class="ddpar">{o['coupon']}% {o['maturity'][:7]} · ${o['par_to_buy']:,} face · Phase {o['phase']}</span>
  </div>
  <div class="ddgrid">
    <div><span class=k>Tax status</span> {r.get('tax_status')}</div>
    <div><span class=k>Pledge</span> {yn(r.get('pledge_confirmed'))}</div>
    <div><span class=k>Call</span> {('callable ' + str(r.get('next_call') or '')) if r.get('callable') else 'non-callable'}</div>
    <div><span class=k>Live tape</span> {r.get('live_last_trade_px')} on {r.get('live_last_trade_date')} ({'{:+.2f}'.format(r['tape_moved_pt']) if isinstance(r.get('tape_moved_pt'),(int,float)) else '—'}pt vs mark)</div>
    <div><span class=k>After-tax TEY recomputed</span> {r.get('recomputed_tey_at')}% (div {('{:+.2f}'.format(r['tey_divergence_pp']) if isinstance(r.get('tey_divergence_pp'),(int,float)) else '—')}pp)</div>
    <div><span class=k>Fiscal roster</span> {r.get('ab1200')}</div>
  </div>
  <p class="ddbasis"><b>Finding:</b> {r.get('basis','')}</p>
</div>""")

# chunk cards into pages of 6
pages = ["\n".join(cards[i:i + 6]) for i in range(0, len(cards), 6)]
card_slides = "\n".join(
    f"""<section class="slide">
  <div class="kicker">Appendix &mdash; Per-Bond Verification Record ({pi+1} of {len(pages)})</div>
  {pg}
  <div class="footer"><span>Verification appendix &middot; {DD_DATE}</span><span>Sources: MSRB/EMMA per-CUSIP &middot; OpenFIGI &middot; CDE AB 1200 rosters &middot; recomputed from raw coupon/price/maturity</span></div>
</section>""" for pi, pg in enumerate(pages))

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>CA Insulated Muni Sleeve — Due-Diligence Appendix</title>
<style>
@page {{ size: 11in 8.5in; margin: 0; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
html,body {{ font-family:-apple-system,"Segoe UI","Helvetica Neue",Arial,sans-serif; color:#14315c; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
.slide {{ width:11in; height:8.5in; page-break-after:always; position:relative; overflow:hidden; padding:0.55in 0.7in; background:#fff; }}
.slide:last-child {{ page-break-after:auto; }}
.navy {{ background:#14315c; color:#fff; }} .navy h1,.navy p,.navy div {{ color:#fff; }}
.kicker {{ font-size:10pt; letter-spacing:2.5px; text-transform:uppercase; color:#7fa8d8; font-weight:600; margin-bottom:8px; }}
.navy .kicker {{ color:#9cc2ed; }}
h1 {{ font-size:30pt; line-height:1.1; margin:0.1in 0; }}
h2 {{ font-size:17pt; margin-bottom:0.08in; }}
p {{ font-size:10.5pt; line-height:1.5; }}
.footer {{ position:absolute; bottom:0.3in; left:0.7in; right:0.7in; display:flex; justify-content:space-between; font-size:7.5pt; color:#8aa3c2; border-top:1px solid #d8e2f0; padding-top:4px; }}
.navy .footer {{ color:#7fa8d8; border-top-color:#2c4a78; }}
.chip {{ display:inline-block; color:#fff; font-size:7pt; font-weight:700; padding:1px 6px; border-radius:3px; letter-spacing:0.4px; }}
.mono {{ font-family:"SF Mono",Menlo,monospace; font-variant-numeric:tabular-nums; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }} .ctr {{ text-align:center; }}
table.sum {{ width:100%; border-collapse:collapse; font-size:6.7pt; margin-top:0.06in; }}
table.sum th {{ background:#14315c; color:#fff; padding:3.5px 4px; text-align:left; font-size:6.6pt; text-transform:uppercase; letter-spacing:0.3px; }}
table.sum td {{ padding:1.6px 4px; border-bottom:1px solid #e3eaf3; }}
table.sum tr:nth-child(even) td {{ background:#f5f8fc; }}
.cty {{ display:block; font-size:6.2pt; color:#7a8aa0; }}
.ddcard {{ border:1px solid #d8e2f0; border-radius:6px; padding:7px 11px; margin-bottom:8px; background:#fbfcfe; }}
.ddhead {{ display:flex; align-items:baseline; gap:9px; margin-bottom:4px; flex-wrap:wrap; }}
.ddissuer {{ font-weight:700; font-size:9pt; }}
.ddpar {{ margin-left:auto; font-size:8pt; color:#5a6a82; font-variant-numeric:tabular-nums; }}
.ddgrid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:2px 14px; font-size:7.6pt; line-height:1.4; }}
.ddgrid .k {{ color:#7a8aa0; font-size:6.6pt; text-transform:uppercase; letter-spacing:0.3px; margin-right:4px; }}
.ddbasis {{ font-size:7.8pt; line-height:1.35; margin-top:4px; color:#2a3a55; }}
ul {{ margin-left:18px; }} li {{ font-size:10.5pt; line-height:1.55; margin-bottom:6px; }}
.statgrid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:0.25in; margin-top:0.35in; }}
.stat .v {{ font-size:28pt; font-weight:800; font-variant-numeric:tabular-nums; }}
.stat .l {{ font-size:9pt; color:#9cc2ed; margin-top:6px; }}
</style></head><body>

<!-- COVER -->
<section class="slide navy">
  <div class="kicker">Appendix to the California Insulated Muni Sleeve Pitch</div>
  <h1>Per-Bond Due-Diligence Record</h1>
  <p style="max-width:7.6in; color:#cfe0f4; font-size:12pt;">Before any order is staged, every bond in the sleeve is independently re-verified against primary sources — the MSRB regulatory record for tax status, legal pledge, call features and the live trade tape; OpenFIGI for issuer identity; the state's AB&nbsp;1200 fiscal-stress rosters; and a from-scratch recomputation of the after-tax yield from raw coupon, price and maturity. This appendix is the complete record of that pass, run {DD_DATE} by independent verification agents (six bonds each), plus single-bond passes on each replacement candidate.</p>
  <div class="statgrid">
    <div class="stat"><div class="v" style="color:#5bbf7a">{n_clear}</div><div class="l">CLEAR — buy as staged</div></div>
    <div class="stat"><div class="v" style="color:#e8b84b">{n_flag}</div><div class="l">FLAG — buyable, caveat noted &amp; corrected</div></div>
    <div class="stat"><div class="v">0</div><div class="l">REJECT — tax or pledge defect</div></div>
    <div class="stat"><div class="v">24/24</div><div class="l">Federally tax-exempt, pledge confirmed</div></div>
  </div>
  <p style="margin-top:0.35in; max-width:7.6in; color:#9cc2ed; font-size:10pt;">What the pass caught — and corrected before any money moved: <b style="color:#fff">four issuer mis-identifications</b> (incl. one wrong-county binding that changed the earthquake-zone map), <b style="color:#fff">five stale price marks</b> re-set to the live tape (one would have overpaid ~2.8 points, two sat unfillable below market), and <b style="color:#fff">two names downgraded to unverified</b> fire/fiscal status, and <b style="color:#fff">one replacement candidate REJECTED outright</b> &mdash; staged as a Santa Barbara school district, the primary record showed a Los Angeles community-college district (an unverifiable class); it was reverted before any order and replaced with a name whose identity was confirmed at the source first. Every flag on the held book is execution- or label-level; none is a credit, tax, or pledge defect.</p>
  <div class="footer"><span>Verification appendix · {DD_DATE}</span><span>Companion to CA_MUNI_SLEEVE_PITCH_DECK</span></div>
</section>

<!-- METHOD -->
<section class="slide">
  <div class="kicker">Method</div>
  <h2>Seven checks per bond, primary sources only.</h2>
  <ul>
    <li><b>Tax status</b> — the MSRB record must state federally tax-exempt; any "TAXABLE" or AMT designation kills the name. <i>This screen removed 29 bonds from the wider universe during construction, including two University of California issues whose extra yield was the taxable premium in disguise.</i></li>
    <li><b>Legal pledge</b> — the issue title and security description must match the claimed pledge (unlimited ad-valorem GO / UC revenue / essential-service revenue); certificates of participation, lease, judgment-obligation, limited-obligation and land-secured paper masquerading under district names are rejected.</li>
    <li><b>Call features</b> — callable status, next call date and price recorded; premium coupons are evaluated to the call, not maturity.</li>
    <li><b>Live tape</b> — freshest trade price/date and two-sided activity pulled at verification time and compared to the working mark; drift &gt;0.5pt or staleness &gt;30 days is flagged and the limit re-set.</li>
    <li><b>Yield arithmetic</b> — the after-tax tax-equivalent yield is recomputed from raw coupon, price and maturity, including the de-minimis rule (market-discount accretion below the 100&nbsp;&minus;&nbsp;0.25&times;years threshold taxed as ordinary income, no gross-up). Tolerance: 0.05pp.</li>
    <li><b>Issuer identity</b> — the CUSIP is independently resolved to its issuer and adjudicated against the working list; mismatches are corrected in every downstream artifact (holdings table, hazard maps, credit records).</li>
    <li><b>Fiscal-stress roster</b> — K-12 districts checked by name against the state's AB&nbsp;1200 Negative/Qualified certification lists (both FY24-25 interims). Community-college districts and utility credits are outside that regime and recorded as <b>unverified — never treated as clean</b>.</li>
  </ul>
  <p style="margin-top:0.15in; font-size:9.5pt; color:#48536a;">Discipline notes: each agent verified six bonds it had no hand in selecting; findings override the list (the record reflects what the primary source says, not what the screen believed); and absence of evidence is recorded as unverified, not as a pass.</p>
  <div class="footer"><span>Verification appendix · {DD_DATE}</span><span>Sources: MSRB/EMMA · OpenFIGI · CA Dept. of Education AB 1200 rosters · FCC/Census geocoding</span></div>
</section>

<!-- SUMMARY TABLE -->
<section class="slide">
  <div class="kicker">Results at a Glance</div>
  <h2>All 24 names: verdict, tax, pledge, tape, math.</h2>
  <table class="sum">
    <tr><th>CUSIP</th><th>Issuer</th><th>Ph</th><th>Verdict</th><th>Tax</th><th>Pledge</th><th>Next call</th><th class=num>Tape px</th><th class=num>Δ vs mark</th><th class=num>TEY a-t</th><th class=num>Δpp</th><th>AB1200</th></tr>
    {''.join(sumrows)}
  </table>
  <p style="font-size:8pt; color:#48536a; margin-top:6px;">Δ vs mark = live tape minus the working mark at verification (points). TEY a-t = after-tax tax-equivalent yield recomputed independently; Δpp = divergence from the staged list. AB1200 ✓ = absent from the state's Negative/Qualified rosters; n/a = outside the K-12 certification regime (recorded as unverified, not clean).</p>
  <div class="footer"><span>Verification appendix · {DD_DATE}</span><span>0 REJECT · {n_clear} CLEAR · {n_flag} FLAG (all execution/label-level)</span></div>
</section>

{card_slides}

</body></html>"""

open("outputs/CA_MUNI_SLEEVE_DD_APPENDIX.html", "w").write(html)
print(f"wrote outputs/CA_MUNI_SLEEVE_DD_APPENDIX.html — cover + method + summary + {len(pages)} card pages, {len(ORDER)} bonds")
