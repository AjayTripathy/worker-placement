"""Defensible product tearsheet: CA tax-exempt income, credit-vetted (R/f/M) + tech/AI
income-channel-INSULATED. Built only on findings that survived two adversarial reviews.
Reads data/etf_insulated_sample.json. Renders HTML -> PDF.
"""
import json, html, statistics as st

S = json.load(open("/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_insulated_sample.json"))
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/CA_MUNI_INSULATED_INCOME_TEARSHEET.html"

ytw = st.mean(r["ytw"] for r in S); ytm = st.mean(r["ytm"] for r in S)
dmat = st.mean(r["dmat"] for r in S); dworst = st.mean(r["dworst"] for r in S)
beta = st.mean(r["beta"] for r in S); tey = ytw * 100 * 2.01
CHAN = {"school_go_av": "K-12 GO (property tax, SB-222 statutory lien)",
        "water_revenue": "Water / essential-service revenue",
        "housing_finance": "State housing finance (CalHFA)"}

namerows = ""
for r in sorted(S, key=lambda x: (x["chan"], -x["dmat"])):
    namerows += (f"<tr><td>{html.escape(r['obl'])}</td><td>{CHAN.get(r['chan'],r['chan'])}</td>"
                 f"<td style='text-align:center'>{r['tier']}</td><td style='text-align:right'>{r['cpn']}</td>"
                 f"<td style='text-align:center'>{r['mat']}</td><td style='text-align:right'>{r['ytw']*100:.2f}</td>"
                 f"<td style='text-align:right'>{r['ytm']*100:.2f}</td>"
                 f"<td style='text-align:right'>{r['dworst']:.1f}</td></tr>")

H = f"""<!doctype html><html><head><meta charset='utf-8'><style>
@page{{margin:14mm 13mm}}
body{{font:12px/1.5 -apple-system,'Helvetica Neue',Arial,sans-serif;color:#1a1a1a}}
h1{{font-size:21px;color:#0b2545;margin:0 0 1px}} .sub{{color:#566;font-size:11.5px;margin-bottom:9px}}
h2{{font-size:14.5px;color:#0b2545;border-bottom:1px solid #ccd;padding-bottom:3px;margin-top:17px}}
table{{border-collapse:collapse;width:100%;margin:6px 0;font-size:11px}}
th{{background:#0b2545;color:#fff;text-align:left;padding:4px 6px}} td{{border:1px solid #ccc;padding:3px 6px;vertical-align:top}}
tr:nth-child(even) td{{background:#f5f7fa}}
.kpi{{display:flex;gap:7px;margin:7px 0}} .kpi>div{{flex:1;background:#0b2545;color:#fff;border-radius:6px;padding:7px;text-align:center}}
.big{{font-size:17px;font-weight:700}} .lbl{{font-size:9px;opacity:.85;line-height:1.15}}
.is{{display:flex;gap:8px;margin:6px 0}} .is>div{{flex:1;padding:8px 10px;border-radius:6px;font-size:10.5px}}
.yes{{background:#eaf6ee;border-left:4px solid #1a7f3c}} .no{{background:#fdecec;border-left:4px solid #b22222}}
.warn{{background:#fff6e6;border-left:4px solid #c8902a;padding:7px 10px;margin:6px 0;font-size:10.5px}}
strong{{color:#0b2545}} em{{color:#555}} .foot{{color:#777;font-size:9px;margin-top:11px;border-top:1px solid #ddd;padding-top:5px}}
ul{{margin:3px 0 3px 0;padding-left:17px}} li{{margin:1px 0}}
</style></head><body>

<h1>California Tax-Exempt Income — Tech/AI Credit-Insulated</h1>
<div class='sub'>Sample tearsheet &middot; a CA muni strategy screened on (1) creditworthiness [R/f(M)] and
(2) tech/AI income-channel insulation &middot; Signal OS muni_credit &middot; 2026-06-06 &middot; <b>illustrative — not an offer or investment advice</b></div>

<div class='kpi'>
 <div><div class='big'>{ytw*100:.2f}%</div><div class='lbl'>avg yield-to-worst (MSRB)</div></div>
 <div><div class='big'>{tey:.2f}%</div><div class='lbl'>taxable-equiv (&times;2.01, CA top)</div></div>
 <div><div class='big'>&beta; {beta:.03f}</div><div class='lbl'>avg tech/AI channel exposure<br>(state-GO &equiv; 1.00)</div></div>
 <div><div class='big'>{dworst:.1f} yr</div><div class='lbl'>avg duration-to-worst</div></div>
 <div><div class='big'>{len(S)}</div><div class='lbl'>sample holdings (all AI-1/AI-2)</div></div>
</div>

<h2>1 &middot; The strategy &mdash; two independent screens</h2>
<p><b>Screen A — Creditworthiness [R/f(M)].</b> Each candidate's pledged security and covenants are
verified against PRIMARY sources: R = the claim (security, coverage, lien), f = the verification
method, M = the authority (EMMA official statements / continuing disclosure, CDIAC default &amp;
draw index, the detector framework). Bonds with impaired credit, recorded defaults/draws, covenant
breaches, or unverifiable security are EXCLUDED. (Diligence-replication, not alpha.)</p>
<p><b>Screen B — Tech/AI income-channel insulation.</b> An AI/tech-equity bust reaches CA muni
<em>credit</em> through ONE channel: the state General Fund's capital-gains / stock-option income
tax (the most tech-levered state revenue base in the U.S.). We score each bond's revenue source on
that channel (&beta;, state-GF claim &equiv; 1.00) and SELECT only credits structurally outside it
&mdash; <b>property-tax GO (SB-222 statutory lien) and essential-service revenue</b> &mdash; whose
creditworthiness does not deteriorate when tech wealth evaporates.</p>

<h2>2 &middot; What this IS &mdash; and what it is NOT (read first)</h2>
<div class='is'>
 <div class='yes'><b>IS</b><ul>
  <li>Tax-exempt (fed + CA) income for a high-bracket CA holder</li>
  <li>High credit quality, primary-source-vetted</li>
  <li><b>Income-channel diversification</b>: credit insulated from the tech/AI cap-gains cycle &mdash; useful precisely for tech-comp-concentrated holders</li>
  <li>Intermediate-duration target (rate-risk managed)</li></ul></div>
 <div class='no'><b>IS NOT</b><ul>
  <li>A price hedge or return anti-correlation to equities &mdash; that is a regime-conditional duration bet that <b>inverted &minus;30% in 2022</b></li>
  <li>Alpha &mdash; not return-backtested vs a CA muni ETF</li>
  <li>A validated predictive credit rating &mdash; &beta; is a <em>structural selection screen</em>, not a forecast</li>
  <li>A default model (CA GO default risk is ~nil regardless)</li></ul></div>
</div>

<h2>3 &middot; Sample portfolio ({len(S)} holdings, equal-weight)</h2>
<table><tr><th>Obligor</th><th>Channel / security</th><th>AI-tier</th><th>Cpn</th><th>Maturity</th><th>YTW %</th><th>YTM %</th><th>Dur-worst</th></tr>
{namerows}</table>
<p style='font-size:10.5px'><em><b>YTW</b> (yield-to-worst, the conservative planning number) = lower of YTM and yield-to-call;
<b>YTM</b> (yield-to-maturity) assumes no call. They match on the low-coupon GO discounts and diverge on the premium
callables (Met Water / Downey / CalHFA), where YTW &lt; YTM = the call give-up. Sample drawn from the research
universe to demonstrate the credit + channel screens; it
currently skews long-duration. A production sleeve targets <b>intermediate duration (~4&ndash;7 yr)</b> via
maturity selection &mdash; duration is a separate dial set deliberately short of the 2022 rate-shock zone.</em></p>

<h2>4 &middot; Portfolio statistics</h2>
<table>
<tr><td style='width:42%'>Avg yield-to-worst (MSRB) / YTM</td><td>{ytw*100:.2f}% / {ytm*100:.2f}% (gross, pre-fee)</td></tr>
<tr><td>Taxable-equivalent yield</td><td>{tey:.2f}% on YTW (&times;2.01, CA ~50.3% top bracket, double-exempt)</td></tr>
<tr><td>Avg tech/AI channel &beta;</td><td>{beta:.3f} (vs an all-state-GO book = 1.00) &mdash; ~{beta*100:.0f}% of the cap-gains credit sensitivity</td></tr>
<tr><td>AI-tier distribution</td><td>{sum(1 for r in S if r['tier']=='AI-1')} AI-1 (Insulated) &middot; {sum(1 for r in S if r['tier']=='AI-2')} AI-2 (Low)</td></tr>
<tr><td>Duration: to-maturity / to-worst</td><td>{dmat:.1f} yr / {dworst:.1f} yr (sample; production target intermediate)</td></tr>
<tr><td>Channel / sector mix</td><td>{sum(1 for r in S if r['chan']=='school_go_av')} K-12 property-tax GO &middot; {sum(1 for r in S if r['chan']=='water_revenue')} water revenue &middot; {sum(1 for r in S if r['chan']=='housing_finance')} state housing finance</td></tr>
<tr><td>Credit notes</td><td>K-12 GO = unlimited ad-valorem + SB-222 statutory lien; water = essential-service rate covenant; all primary-source vetted</td></tr>
</table>

<h2>5 &middot; Why "insulated" is defensible (the evidence that survived review)</h2>
<ul style='font-size:11px'>
<li><b>Mechanism:</b> CA cap-gains+option income-tax revenue ran $17B (2000-01) &rarr; $5B (2002-03), &minus;71% [LAO] &mdash; the dot-com income shock.</li>
<li><b>The tell:</b> CA <b>State GO was cut ~6 notches (AA&rarr;BBB)</b> in that bust, while these property-tax/essential-service sectors were untouched.</li>
<li><b>The strongest result:</b> across dot-com, GFC, COVID and 2022, <b>property-tax school GO and water revenue took ZERO documented rating actions in all four regimes</b> (CDIAC + agency record). The insulation is a multi-regime, count-based fact, not a model output.</li>
</ul>

<div class='warn'><b>Risk factors.</b> (1) <b>Rate/duration risk</b> &mdash; even intermediate duration falls in a rate
shock (long CA muni &minus;10 to &minus;30% in 2022); this is income + credit quality, <em>not</em> crash
protection. (2) <b>Single-state (CA) concentration.</b> (3) <b>Liquidity</b> &mdash; some sectors trade thinly;
favor benchmark issues / a fund wrapper. (4) The channel-&beta; is a <b>structural classification</b>, not a
validated predictive rating &mdash; it segregates revenue sources, it does not forecast spreads. (5) A CA muni
<b>ETF (e.g. ~8 bp)</b> captures most of the core value; this strategy's marginal case is the credit screen +
the income-channel tilt for tech-concentrated holders, best realized at SMA scale.</div>

<div class='foot'>Methodology &amp; data: EMMA RTRS (yields/terms), CDIAC DebtWatch (default-draw), LAO (cap-gains revenue),
CA State Treasurer (ratings), Signal OS muni_credit (capgains_beta.py, detectors/, compute_bond_analytics.py).
Yields gross of fees, as-of 2026-06-05/06. Non-claims (price hedge / alpha / validated rating / channel-specificity)
reflect findings of two adversarial reviews and are stated deliberately. Illustrative; not an offer, solicitation,
or investment advice.</div>
</body></html>"""
open(OUT, "w").write(H)
print("wrote", OUT, len(H), "bytes")
