"""Styled HTML tearsheet (color-coded rating chips) for the blended sleeve -> headless-Chrome PDF.
Reuses the rating logic; reads muni_etf_sleeve_blended.json -> outputs/CA_MUNI_SLEEVE_C_TEARSHEET.html"""
import json
from collections import Counter

S = json.load(open('muni_etf_sleeve_blended.json')); SUM = S['basket_summary']; B = S['barbell']
ASOF = "2026-06-09"

def liq_rating(m):
    sp = m.get('px_spread'); n = m.get('n365', 0); ts = m.get('two_sided_days', 0)
    if sp is not None and sp <= 0.25 and n >= 50 and ts >= 10: return "L1", "Highly liquid"
    if (sp is None or sp <= 0.40) and n >= 24 and ts >= 3:     return "L2", "Liquid"
    if (sp is None or sp <= 0.75) and n >= 12 and ts >= 1:     return "L3", "Moderate"
    return "L4", "Thin"
def ai_rating(insul):
    e = (100 - insul) / 100.0
    return (("AI-1","Insulated") if e<=0.05 else ("AI-2","Low") if e<=0.15 else ("AI-3","Moderate")
            if e<=0.30 else ("AI-4","High") if e<=0.60 else ("AI-5","Direct"))
def cred_grade(s): return ("Strong" if s>=88 else "Solid" if s>=80 else "Adequate" if s>=72 else "Conditional" if s>=64 else "Unverified")
CK = {"school_go_sb222":("Unlimited ad-valorem tax + SB-222 statutory <b>first lien</b>","~Aa2–Aa3 / AA– to AA"),
 "uc_grb":("UC broad General Revenues; med-center excluded","Aa2 / AA+"),
 "uc_lprb":("UC specific project revenues; no state approp.","~Aa3 / AA–"),
 "water":("Essential-service net revenue + ~1.2× covenant","~A1–Aa3 / A+ to AA–"),
 "state_go":("State GO full faith & credit","Aa2 / AA–")}
SECT2CK = {"SCHOOL-GO":"school_go_sb222","WATER-REV":"water","ELEC-REV":"water"}
AICOL = {"AI-1":"#1a7f3c","AI-2":"#5a9e2f","AI-3":"#c8902a","AI-4":"#d2691e","AI-5":"#b22222"}
LQCOL = {"L1":"#1a7f3c","L2":"#5a9e2f","L3":"#c8902a","L4":"#d2691e"}
CRCOL = {"Strong":"#1a7f3c","Solid":"#2f6f9e","Adequate":"#c8902a","Conditional":"#d2691e","Unverified":"#b22222"}

def chip(text, color): return f'<span class="chip" style="background:{color}">{text}</span>'

rows = []
for b in sorted(B, key=lambda x:(x['maturity'], -x.get('ytw',0))):
    m=b.get('liq',{}); ck=b.get('security_credit_key') or SECT2CK.get(b.get('sectype'),"school_go_sb222")
    lr,ln=liq_rating(m); ar,an=ai_rating(b['insul']); cg=cred_grade(b['credit'])
    cert=b.get('cert_status') or ''
    certtxt={'POSITIVE(absent)':'AB1200 clear','NOT-COVERED-CC':'CC: n/a','QUALIFIED':'QUALIFIED','NEGATIVE':'NEGATIVE','UNRESOLVED':'unresolved'}.get(cert, '—')
    issuer=(b.get('issuer') or '').title() if b.get('issuer') else ''
    rows.append(dict(cusip=b['cusip'], sl=("A" if b.get('sleeve','').startswith('A') else "B"), cls=CK[ck][0],
        issuer=(f"{issuer} ({b['county']})" if issuer and b.get('county') else issuer or '—'),
        cert=certtxt, ss=(f"{b['seismic_ss']:.2f}" if b.get('seismic_ss') is not None else '—'),
        fire=(f"{100*b['fire_high_share']:.0f}%" if b.get('fire_high_share') is not None else '—'),
        firehot=(b.get('fire_high_share') or 0) > 0.30,
        cpn=("%g"%b['coupon']), mat=b['maturity'][:7], px="%.1f"%b['emma_px'], ytw="%.2f"%(b['ytw']*100),
        tey="%.2f"%(b.get('tey_ytw_aftertax',b.get('tey_ytw',0))*100), lr=lr,ln=ln, ar=ar,an=an, insul="%.0f"%b['insul'],
        cs=b['credit'], cg=cg, agency=CK[ck][1], par="%s"%format(b['par'],',')))

ai_d=Counter(r['ar'] for r in rows); lq_d=Counter(r['lr'] for r in rows); cr_d=Counter(r['cg'] for r in rows)

# ---- Phase-2 illiquidity quantification (computed live from the tape metrics) ----
import statistics as _st, datetime as _dt
def _fastb(b):
    l=b.get('liq') or {}
    return (l.get('px_spread') or 9)<=0.30 and (l.get('n365') or 0)>=24
def _yrsb(m):
    y,mo,d=[int(x) for x in m.split('-')]
    return max(0.5,( _dt.date(y,mo,d)-_dt.date(2026,6,11)).days/365.25)
_p1=[b for b in B if _fastb(b)]; _p2=[b for b in B if not _fastb(b)]
_p2par=sum(b['par'] for b in _p2)
_prem=100*(_st.mean(b['tey_ytw_aftertax'] for b in _p2)-_st.mean(b['tey_ytw_aftertax'] for b in _p1))
_sps=[(b['liq'].get('px_spread')) for b in _p2 if (b.get('liq') or {}).get('px_spread') is not None]
_mh=_st.mean(s/2 for s in _sps)
_acq=sum((b['liq'].get('px_spread', 2*_mh) or 2*_mh)/2/100*b['par'] for b in _p2)
_amort=_st.mean(((b['liq'].get('px_spread', 2*_mh) or 2*_mh)/2)/_yrsb(b['maturity'])*100 for b in _p2)
_exitn=sum((b['liq'].get('px_spread', 0.5) or 0.5)/100*b['par'] for b in _p2)
_exits=sum((2*(b['liq'].get('px_spread', 0.5) or 0.5)+(1.0 if (b['liq'].get('two_sided_days') or 0)<3 else 0.25))/100*b['par'] for b in _p2)
PATIENCE = f"""
<h2>The price of patience &mdash; Phase&nbsp;2 illiquidity, quantified</h2>
<p class=small>Measured from each bond's own regulatory trade tape (not modeled): the {len(_p2)} patient names (${_p2par:,}) yield <b>{_st.mean(b['tey_ytw_aftertax'] for b in _p2)*100:.2f}%</b> after-tax vs <b>{_st.mean(b['tey_ytw_aftertax'] for b in _p1)*100:.2f}%</b> for the liquid anchor &mdash; an illiquidity premium of <b>~{_prem*100:.0f} bps/yr (&asymp; ${_prem/100*_p2par:,.0f}/yr)</b>. Against that: entry costs a mean half-spread of {_mh:.2f}pt &mdash; <b>~${_acq:,.0f} one-time ({100*_acq/_p2par:.2f}%), &asymp;{_amort:.0f} bps/yr amortized</b> to maturity, a roughly {max(1,round(_prem*100/_amort))}:1 earn-to-cost ratio for a hold-to-maturity buyer. The asymmetry: a <b>forced</b> exit costs ~{100*_exitn/_p2par:.1f}% normally and <b>~{100*_exits/_p2par:.1f}% (&asymp;${_exits:,.0f}) under stress</b> &mdash; about one year's premium &mdash; so the bargain holds only if early liquidation stays improbable. Build window ~4&ndash;8 weeks working all names in parallel; {sum(1 for b in _p2 if (b['liq'].get('med_block') or 0)>=40000 or (b['liq'].get('max_block') or 0)>=40000)}/{len(_p2)} names have printed &ge;$40k blocks. Per-name spreads on thin names are few-observation medians &mdash; real error bars; first fills will calibrate them.</p>
"""

trows="\n".join(
 f"<tr><td class=mono>{r['cusip']}</td><td class=ctr>{r['sl']}</td>"
 f"<td>{r['issuer']}<br><span class=sub>{r['cls']}</span></td>"
 f"<td class=ctr>{r['cpn']}%</td><td class=ctr>{r['mat']}</td><td class=num>{r['px']}</td>"
 f"<td class=num>{r['ytw']}</td><td class=num><b>{r['tey']}</b></td>"
 f"<td>{chip(r['lr'],LQCOL[r['lr']])} <span class=sub>{r['ln']}</span></td>"
 f"<td>{chip(r['ar'],AICOL[r['ar']])} <span class=sub>{r['an']} ({r['insul']})</span></td>"
 f"<td>{chip(str(r['cs'])+' '+r['cg'],CRCOL[r['cg']])}<br><span class=sub>{r['cert']}</span></td>"
 f"<td class=num>{r['ss']}</td>"
 f"<td class=num style='{'color:#b22222;font-weight:700' if r['firehot'] else ''}'>{r['fire']}</td>"
 f"<td class=sub>{r['agency']}</td><td class=num>{r['par']}</td></tr>"
 for r in rows)

ai_scale="".join(f"<tr><td><b style='color:{AICOL[t]}'>{t}</b></td><td>{e}</td><td>{mng}</td><td>{ex}</td><td>{oc}</td></tr>"
 for t,e,mng,ex,oc in [
 ("AI-1","≤5%","Insulated","Statutory-lien property-tax school GO; essential-service water/utility revenue","Untouched"),
 ("AI-2","5–15%","Low","University general/limited-project revenue; insured enterprise revenue","Minor spread drift"),
 ("AI-3","15–30%","Moderate","Tax-increment; tech-hub hospital; county GF appropriation","1–2 notch / widening"),
 ("AI-4","30–60%","High","Local GF appropriation; weak tax increment","Multi-notch in deep shock"),
 ("AI-5",">60%","Direct","State General Fund / income-tax-backed GO & appropriation","4–5 notches (CA AA→BBB '03)")])

html=f"""<!doctype html><html><head><meta charset=utf-8><style>
@page {{ size: 11in 8.5in; margin: 11mm; }}
* {{ box-sizing:border-box; }}
body {{ font-family:-apple-system,'Helvetica Neue',Arial,sans-serif; color:#1a1a1a; font-size:10px; line-height:1.45; margin:0; }}
h1 {{ font-size:20px; margin:0 0 2px; }}
h2 {{ font-size:13px; margin:16px 0 6px; border-bottom:2px solid #14315c; padding-bottom:3px; color:#14315c; }}
h3 {{ font-size:11px; margin:10px 0 4px; color:#14315c; }}
.subtle {{ color:#666; font-style:italic; margin:0 0 8px; }}
.snap {{ display:grid; grid-template-columns:repeat(4,1fr); gap:6px; margin:8px 0; }}
.snap div {{ background:#f3f6fb; border:1px solid #d7e0ee; border-radius:5px; padding:6px 8px; }}
.snap .k {{ color:#666; font-size:8.5px; text-transform:uppercase; letter-spacing:.4px; }}
.snap .v {{ font-size:15px; font-weight:700; color:#14315c; }}
table {{ border-collapse:collapse; width:100%; margin:6px 0; }}
th,td {{ border:1px solid #dde3ec; padding:2.5px 4px; text-align:left; vertical-align:top; }}
th {{ background:#14315c; color:#fff; font-size:8px; text-transform:uppercase; letter-spacing:.3px; }}
.hold td {{ font-size:7.6px; padding:2px 3px; }}
.mono {{ font-family:'SF Mono',Menlo,monospace; font-size:7.4px; }}
.num {{ text-align:right; font-variant-numeric:tabular-nums; }} .ctr {{ text-align:center; }}
.sub {{ color:#555; font-size:7px; }}
.chip {{ display:inline-block; color:#fff; border-radius:3px; padding:.5px 4px; font-size:7px; font-weight:700; white-space:nowrap; }}
.mix span {{ font-weight:700; }}
p {{ margin:5px 0; }} .small {{ font-size:8.5px; color:#444; }}
ul {{ margin:4px 0 4px 16px; padding:0; }} li {{ margin:2px 0; }}
</style></head><body>

<h1>California Insulated Muni Sleeve</h1>
<p class=subtle>Blended liquid-anchor / yield-core ladder &middot; as of {ASOF} &middot; analyst review, not investment advice</p>

<div class=snap>
 <div><div class=k>Par / positions</div><div class=v>${SUM['total_par']:,}</div><div class=sub>{SUM['n']} bonds · after-tax-TEY optimized · {int(SUM.get('fast_share',0)*100)}% liquid anchor</div></div>
 <div><div class=k>Yield to worst</div><div class=v>{SUM['par_weighted_ytw_pct']}%</div><div class=sub>after-tax TEY <b>{SUM['par_weighted_tey_aftertax_pct']}%</b> (CA top bkt)</div></div>
 <div><div class=k>AI-insulation</div><div class=v>{SUM['par_weighted_insulation']}</div><div class=sub>0–100; higher = safer in AI crash</div></div>
 <div><div class=k>Our credit</div><div class=v>{SUM['par_weighted_credit']}</div><div class=sub>med spread {SUM['median_same_day_spread_pt']}pt · {SUM['ladder'][:4]}–{SUM['ladder'][-10:-6]}</div></div>
</div>
<p class="small mix">Rating mix &mdash; AI-insulation: {', '.join(f"{k}&times;{ai_d[k]}" for k in sorted(ai_d))}. &nbsp; Liquidity: {', '.join(f"{k}&times;{lq_d[k]}" for k in sorted(lq_d))}. &nbsp; Our credit: {', '.join(f"{k}&times;{cr_d[k]}" for k in sorted(cr_d,key=lambda x:-cr_d[x]))}.</p>

<h2>Thesis</h2>
<p>This sleeve holds California municipal bonds chosen for one property the market under-prices: <b>structural insulation of the <i>credit</i> from an AI/technology-sector crash.</b> California's General Fund leans on personal income tax, whose most volatile slice is capital-gains realizations from tech equity. A severe AI de-rating would collapse those realizations &mdash; the dot-com bust cut California capital-gains revenue ~71% and pressured state-General-Fund-backed credits an estimated 4–5 notches &mdash; yet bonds secured by a statutory property-tax lien (school GO) or essential-service utility revenue kept paying, untouched. We buy those insulated pledges and <i>exclude</i> the state-General-Fund channel. Yield is competitive not from credit or insulation risk but because these issues are small, obscure and lightly traded: <b>we are paid for illiquidity and obscurity inside verified-safe credits</b> &mdash; a very different risk than reaching down the quality curve.</p>

<h2>How to read the three ratings</h2>
<h3>AI-insulation (AI-1 … AI-5) — rates credit, not price</h3>
<p class=small>We decompose each security's revenue pledge into exposure to nine economic channels, weighted by how hard an AI crash hits each (capital-gains/income tax heaviest, then property assessed value, pensions, tech-employer concentration, hospital balance sheets, office CRE, housing, sales tax, transit). Weighted sum = exposure; <b>insulation = 100 − exposure</b>; binned to five tiers. It states which pledges keep paying when tech-driven state revenue collapses — not mark-to-market in a rate shock.</p>
<table><tr><th>Tier</th><th>Exposure</th><th>Meaning</th><th>Typical security</th><th>Dot-com (2001–03)</th></tr>{ai_scale}</table>

<h3>Our credit (0–100) — and why it sits beside the agency rating</h3>
<p class=small>We score the <b>actual legal pledge</b>, read from the official statement / statute: statutory first-lien unlimited-ad-valorem school GO (~90, SB-222 puts bondholders ahead of other claims and the levy self-adjusts); UC Regents General Revenue Bonds (~82, broad University pledge but medical-center revenue excluded); UC Limited Project Revenue Bonds (~74, narrower specific-project revenues, no state appropriation); essential-service water/wastewater (~80, ~1.2× rate covenant). We down-rate lease/COP structures for appropriation + abatement risk and flag <i>Unverified</i> where the OS wasn't read — unverified is never treated as clean. <b>EMMA publishes no third-party rating for most of these issuers</b>, so our security read substitutes for the missing agency letter; the Agency column is a security-<i>class</i> benchmark for context, not an issue-specific rating.</p>

<h3>Liquidity (L1 … L4) — from the MSRB trade tape</h3>
<p class=small>Municipals have no consolidated quote, so we use realized trades: same-day round-trip spread, trade frequency, and two-sided trading days. <b>L1</b> ≤0.25pt/≥50yr/≥10 two-sided · <b>L2</b> ≤0.40/≥24/≥3 · <b>L3</b> ≤0.75/≥12/≥1 · <b>L4</b> thin. Every holding clears a floor (traded ≤90d, ≥12/yr, ≥1 two-sided); un-buildable names are excluded regardless of credit. For a hold-to-maturity ladder the spread is paid once and the bond redeems at par, so liquidity governs deployment pace and early-exit cost, not income.</p>

<h2>Holdings ({len(rows)})</h2>
<table class=hold>
<tr><th>CUSIP</th><th>Sl</th><th>District / issuer + pledge</th><th>Cpn</th><th>Maturity</th><th>Px</th><th>YTW</th><th>TEY a-t</th><th>Liquidity</th><th>AI-insulation</th><th>Our credit + AB1200²</th><th>EQ SS³</th><th>Fire⁴</th><th>Agency (class)¹</th><th>Par</th></tr>
{trows}
</table>

<h2>Deployment</h2>
<ul>
<li><b>Phase 1 — now (~${SUM['phase1_deployable_now_par']:,}, {SUM['phase1_pct']}%):</b> liquid anchor + already-active core names, buildable on demand at tight spreads. Invested at the full after-tax TEY from day one.</li>
<li><b>Phase 2 — over weeks (~${SUM['phase2_accumulate_par']:,}, {SUM['phase2_n_names']} names):</b> thinner core names worked opportunistically on offerings/bids-wanted, funded by trimming the anchor as they fill. Worst case you hold the anchor longer — it still out-yields cash — so you're never waiting to be invested.</li>
</ul>

{PATIENCE}

<h2 style="border:none;margin-bottom:2px">Caveats</h2>
<p class=small><b>Selection metric is after-tax TEY</b> (de-minimis aware) — gross YTW selection mechanically over-buys tax-dragged discounts. TEY grossed up at CA top combined bracket (×2.01); {SUM.get('demin_breaches','several')} discount bonds breach de-minimis (accretion taxed as ordinary income) — the after-tax TEY shown already reflects that drag. Marks are EMMA last-trade prices (munis trade by appointment; a print may be days old). <b>¹ Agency (class)</b> is a security-class benchmark, not an issue-specific rating — EMMA carries no third-party rating for most of these issuers. <b>² AB1200</b> = CDE interim certification (the official CA school fiscal-distress flag): "clear" = district certified it will meet obligations and is absent from the QUALIFIED/NEGATIVE lists (FY24-25 interims); community-college districts are not CDE-covered (CCCCO monitors) and are marked n/a, not clean. An adverse certification reflects operating-fund stress; the GO levy is separate, county-collected, with the SB-222 statutory lien — state takeovers (Inglewood 2012, Oakland 2003) did not interrupt GO debt service. <b>³ EQ SS</b> = USGS ASCE7-22 short-period spectral acceleration at the district office — a seismic-hazard overlay used for single-event concentration management, not a per-bond credit deduction. <b>⁴ Fire</b> = share of the district's building value in FEMA National Risk Index Relatively-High / Very-High wildfire tracts (district↔tract join via NCES boundaries). Districts above 30% are flagged red and capped at 15% of names in construction — the channel is insurer withdrawal dragging the assessed-value base, not the burn itself (no CA school GO defaulted through Loma Prieta, Northridge, or the Camp Fire). AI-insulation rates credit, not price. Not investment advice; for analyst review.</p>

</body></html>"""
open("outputs/CA_MUNI_SLEEVE_C_TEARSHEET.html","w").write(html)
print("wrote outputs/CA_MUNI_SLEEVE_C_TEARSHEET.html")
