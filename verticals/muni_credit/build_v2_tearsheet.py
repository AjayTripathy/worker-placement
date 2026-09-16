"""Tearsheet: v2 dual-axis methodology pitch + current portfolio stats. Defensible framing."""
import json, html, statistics as st

P = json.load(open("data/v2_portfolio.json"))
SC = json.load(open("data/channel_scores_v2.json"))
H = P["holdings"]; S = P["stats"]; CW = SC["channel_weights"]
OUT = "outputs/CA_MUNI_V2_TEARSHEET.html"

CH_NAME = {"income_tax":"State-GF capital-gains income tax", "property_av":"Tech-hub property / assessed value",
 "pension":"CalPERS/CalSTRS pension contributions", "tech_firm_conc":"Tech-firm taxpayer/employer concentration",
 "hospital_balsheet":"Hospital balance-sheet (investments/philanthropy)", "cre_office":"Commercial real estate / office",
 "housing_price":"Bay-Area housing prices", "sales_tax_tot":"Local sales / hotel (TOT) tax", "transit_airport":"Transit / airport"}
# portfolio avg exposure per channel (0=insulated..1=fully exposed)
pexp = {c: st.mean(b["channels"].get(c, 0) for b in H) for c in CW}
avg_ytm = st.mean(b["ytm_pct"] for b in H if b.get("ytm_pct"))

# plain-language explanation of each tech/AI transmission channel (mechanism -> who it hits)
CH_DESC = {
 "income_tax": "CA's General Fund leans on capital-gains / stock-option / IPO income tax &mdash; the most tech-levered state revenue base in the U.S. A tech/AI bust evaporates it. &rarr; <b>State GO &amp; appropriation debt</b>.",
 "property_av": "Tech wealth bids up Bay-Area/Silicon-Valley property; a bust softens assessed value (Prop-8 reductions, slower turnover). &rarr; <b>tax-increment (TAB) &amp; land-secured bonds</b>.",
 "pension": "CalPERS/CalSTRS hold large equity + growing VC/tech; an equity crash &rarr; investment losses &rarr; higher required contributions for every CA local government. &rarr; <b>operating budgets / appropriation debt</b> (NOT protected GO debt service).",
 "tech_firm_conc": "Some local credits lean on one tech firm as a dominant taxpayer/employer (Apple&middot;Cupertino, Google&middot;Mtn View). A firm contraction hits them directly. &rarr; <b>concentrated tech-hub local credits</b>.",
 "hospital_balsheet": "Silicon-Valley hospital reserves (investment income), tech-donor philanthropy, and elective volumes (tech employment/insurance) are tech-linked. &rarr; <b>CHFFA hospital conduits</b>.",
 "cre_office": "Tech layoffs + AI-driven lower office demand &rarr; SF/SV office vacancy (&lsquo;doom loop&rsquo;) &rarr; falling commercial AV &amp; assessments. &rarr; <b>CRE-heavy city GF, TABs, assessment districts</b>.",
 "housing_price": "Tech wealth drives Bay-Area home prices; a bust &rarr; mortgage delinquency. &rarr; <b>CalHFA single-family + multifamily / workforce housing</b>.",
 "sales_tax_tot": "Tech-worker spending + tech business travel/conferences feed local sales tax + hotel (TOT) tax. &rarr; <b>tech-hub city general funds</b>.",
 "transit_airport": "Bay-Area transit ridership + business travel (SFO, BART, bridges) ride tech employment/travel (remote-work/AI compounding). &rarr; <b>transportation revenue credits</b>.",
}
chan_rows2 = "".join(
    f"<tr><td><b>{CH_NAME[c]}</b></td><td>{CH_DESC[c]}</td>"
    f"<td style='text-align:center'>{CW[c]:.2f}</td><td style='text-align:center'>{pexp[c]*100:.0f}%</td></tr>"
    for c in sorted(CW, key=lambda x: -CW[x]))

# the creditworthiness-check dimensions and what each verifies
CRED_DIMS = [
 ("Security &amp; lien", "<b>What is pledged and how senior your claim is</b> &mdash; statutory first lien &gt; revenue covenant &gt; naked conduit &gt; appropriation/lease. The single most important credit fact.", "EMMA official statement + CA Gov Code", "CORE (base score)"),
 ("External rating", "Independent agency rating (S&amp;P / Moody&rsquo;s / Fitch) as third-party corroboration of the credit.", "Rating agencies", "CORE (overlay)"),
 ("Default &amp; draw history", "Has the obligor ever defaulted or drawn on its debt-service reserve? A recorded event is a hard exclude.", "CDIAC DebtWatch default-draw index (live)", "CORE"),
 ("Liquidity &amp; disclosure", "Does the bond actually trade (so you can mark &amp; exit), and is the issuer current on disclosure? Stale / never-traded = penalty.", "EMMA RTRS trade tape", "CORE (penalty)"),
 ("Covenant compliance", "Debt-service coverage, additional-bonds test, reserve maintenance &mdash; is the issuer meeting its covenants?", "EMMA continuing disclosure / audits", "EXTENDED (covenant_breach)"),
 ("Fiscal distress", "Going-concern flags, late filings, county fiscal certifications (school GO).", "Auditor opinions / EMMA / COE AB-1200", "EXTENDED"),
 ("Pension / OPEB burden", "Pension/OPEB funded ratio and 5-year trajectory &mdash; the slow-burn local-budget risk.", "CalPERS/CalSTRS valuations", "EXTENDED"),
]
cred_rows = "".join(
    f"<tr><td><b>{n}</b></td><td>{d}</td><td>{m}</td><td style='text-align:center'>{tag}</td></tr>"
    for n, d, m, tag in CRED_DIMS)

chan_rows = "".join(
    f"<tr><td>{CH_NAME[c]}</td><td style='text-align:center'>{CW[c]:.2f}</td>"
    f"<td style='text-align:center'>{pexp[c]*100:.0f}%</td></tr>"
    for c in sorted(CW, key=lambda x:-CW[x]))

EX = {b["slot"]: b for b in SC["bonds"]}
def example(slot, verdict, color, bg, decision):
    b = EX[slot]
    ch = ", ".join(f"{CH_NAME.get(c,c)} {int(v*100)}%" for c, v in b["channels"].items() if v > 0) or "none — insulated across all nine"
    rows = "".join(f"<tr><td>{d['component'].replace('_',' ')}</td><td>{html.escape(d['R'][:92])}</td>"
                   f"<td>{html.escape(d['M'][:56])}</td><td style='text-align:center'><b>{d['finding']}</b></td></tr>"
                   for d in b["rfm_diligence"])
    return (f"<div class='ex' style='border-left:5px solid {color};background:{bg};padding:6px 10px;margin:6px 0;border-radius:4px'>"
            f"<b style='color:{color}'>{verdict}</b> &mdash; <b>{html.escape(b['obligor'][:40])}</b>"
            f"&nbsp; <span style='font-size:10px'>AI-insulation <b>{b['ai_insulation']:.0f}</b> &middot; "
            f"creditworthiness <b>{b['creditworthiness']:.0f}</b> &middot; YTW {(b['ytw_pct'] or 0):.2f}%</span>"
            f"<div style='font-size:9.5px;margin:2px 0'><em>Channel exposure: {ch}</em></div>"
            f"<table style='font-size:9.5px'><tr><th>Diligence component</th><th>Claim</th><th>Source / authority</th>"
            f"<th>Finding</th></tr>{rows}</table><div style='font-size:10px'><b>Decision:</b> {decision}</div></div>")

ex_incl = example(1, "INCLUDED", "#1a7f3c", "#eaf6ee",
   "passes BOTH gates &mdash; VERIFIED SB-222 statutory first lien on the ad-valorem levy (credit 90), and insulated across all nine channels (99).")
ex_cred = example(7, "DILIGENCE RESOLVED &mdash; credit VERIFIED, now excluded for AI", "#c8902a", "#fff6e6",
   "Previously flagged <b>UNVERIFIABLE</b> (covenants unread). We pulled the official statement and verified the security: a <b>Gross Revenues pledge under a Master Trust Indenture, &ge;1.15&times; rate covenant</b> (1.10&times; default floor), no debt-service reserve &mdash; an investment-grade package, corroborated by the AA rating. Credit re-scored <b>73 &rarr; 88 (VERIFIED)</b>. It is now excluded for the <em>right</em> reason &mdash; <b>AI-channel exposure</b> (insulation 88 &lt; 90: hospital balance-sheet + Silicon-Valley concentration), not for an unread document. <em>The diligence loop: UNVERIFIABLE is a to-do, not a verdict.</em>")
ex_ai = example(19, "EXCLUDED &mdash; AI correlation", "#c8902a", "#fff6e6",
   "strong, VERIFIED credit (86) but fails insulation (66): <b>100% exposed to the state-GF capital-gains income-tax channel</b> &mdash; the exact tech/AI pipe (CA State GO fell ~6 notches in dot-com). The orthogonality in action: good credit, wrong channel.")

ex_creditexcl = ("<div class='ex' style='border-left:5px solid #b22222;background:#fdecec;padding:6px 10px;margin:6px 0;border-radius:4px'>"
   "<b style='color:#b22222'>EXCLUDED &mdash; creditworthiness</b> &mdash; <b>Oroville Public Financing Authority</b>"
   "&nbsp; <span style='font-size:10px'>AI-insulation <b>76</b> &middot; creditworthiness <b>18</b></span>"
   "<div style='font-size:9.5px;margin:2px 0'><em>illustrative, drawn from the live CDIAC index &mdash; not a portfolio candidate</em></div>"
   "<table style='font-size:9.5px'><tr><th>Diligence component</th><th>Claim</th><th>Source / authority</th><th>Finding</th></tr>"
   "<tr><td>security lien</td><td>Marks-Roos pooled financing-authority revenue (land-secured / assessment pool) &mdash; junior, no statutory lien</td><td>EMMA / CDIAC</td><td style='text-align:center'><b>WEAK-STRUCTURE</b></td></tr>"
   "<tr><td>cdiac default draw</td><td><b>14 recorded DEFAULTS + 6 reserve draws, 1996&ndash;2004</b></td><td>CDIAC DebtWatch default-draw index (live)</td><td style='text-align:center'><b>SEVERE / EXCLUDE</b></td></tr>"
   "</table>"
   "<div style='font-size:10px'><b>Decision:</b> Excluded on creditworthiness. The CDIAC default-draw record shows a <b>documented serial-default history</b> (14 defaults, 6 reserve draws). A recorded default is the hardest credit fail there is &mdash; an actual failure to pay, not a thin score &mdash; so the <b>cdiac_default_draw</b> screen hard-excludes it regardless of yield or insulation. The credit gate at its sharpest.</div></div>")

hold_rows = ""
for b in H:
    f0 = b["rfm_diligence"][0]["finding"]
    hold_rows += (f"<tr><td>{html.escape(b['obligor'][:34])}</td><td>{b['security'].replace('_',' ')}</td>"
                  f"<td style='text-align:center'>{b['ai_insulation']:.0f}</td>"
                  f"<td style='text-align:center'>{b['creditworthiness']:.0f}</td>"
                  f"<td style='text-align:right'>{(b['ytw_pct'] or 0):.2f}</td>"
                  f"<td style='text-align:right'>{(b['ytm_pct'] or 0):.2f}</td>"
                  f"<td style='text-align:right'>{(b['dur_to_worst'] or 0):.1f}</td></tr>")

in_slots = {b["slot"] for b in P["holdings"]}
PITCH = {
 1: "Unlimited ad-valorem school GO under an SB-222 statutory FIRST LIEN &mdash; the strongest security in the book and structurally disconnected from every tech/AI channel. The core archetype.",
 2: "SB-222 statutory-lien school GO; property-tax-secured, fully tech-insulated, 5.0% yield-to-worst.",
 3: "SB-222 statutory-lien school GO, insulated; credit a notch lower (82) only because the trade mark is stale &mdash; a disclosure flag, not a security weakness.",
 4: "SB-222 statutory-lien school GO, insulated; premium-callable, so its realized (to-worst) duration is shorter &mdash; handy for the intermediate-duration target.",
 5: "SB-222 statutory-lien school GO; the highest yield in the book (5.5% YTW) with full insulation.",
 6: "SB-222 statutory-lien school GO, insulated, 4.8% YTW.",
 7: "Now VERIFIED investment-grade (gross-revenue pledge, &ge;1.15&times; rate covenant, AA) &mdash; but excluded for the hospital-balance-sheet channel (Silicon-Valley investment income, philanthropy, elective volumes): insulation 88. Good credit, wrong place.",
 8: "VERIFIED AA- (&ge;1.25&times; rate covenant); the same hospital + Silicon-Valley-concentration exposure pulls insulation to 88. Excluded for AI, not credit.",
 9: "Senior-living revenue wrapped by Cal-Mortgage/HCAI &mdash; a state-program credit substitution (~AA-) carrying the credit, over a pledge orthogonal to the tech/AI channels.",
 10: "Cal-Mortgage-insured senior living; the state wrap does the credit work; insulated.",
 11: "State housing-finance program bonds &mdash; over-collateralized mortgage pools; only a modest housing-price channel, comfortably inside the insulation gate.",
 12: "Tax-increment (RPTTF) bond &mdash; its security IS assessed-value growth, the property/AV channel a tech bust hits; insulation 80, below the gate.",
 13: "Insulated (96) but excluded on CREDIT &mdash; a municipal financing-authority lease/revenue pledge scores below the 75 floor; softer security than a statutory-lien GO.",
 14: "The most tech-exposed name here &mdash; Silicon-Valley tax increment (property/AV + CRE + tech-firm-concentration, all SV-boosted &rarr; insulation 74) plus a never-traded mark dragging credit to 62. Fails BOTH gates.",
 15: "Tax-increment bond &mdash; property/AV channel exposure, insulation 80.",
 16: "Tax-increment bond &mdash; property/AV channel exposure, insulation 80.",
 17: "Metropolitan Water District essential-service revenue &mdash; usage-based cash flow orthogonal to all nine channels; about the most recession- and tech-proof pledge there is.",
 18: "Essential-service water revenue, insulated; shorter duration.",
 19: "The orthogonality case in one bond: VERIFIED AA credit (86) but 100% exposed to the state-GF capital-gains income-tax channel &mdash; the exact pipe a tech/AI bust runs through (it fell ~6 notches in dot-com). Insulation 66.",
 20: "Fails BOTH &mdash; a pension-obligation certificate of participation (annual-appropriation + abatement risk, no statutory lien &rarr; credit 64) with pension/appropriation channel exposure (insulation 86).",
}
BYSLOT = {b["slot"]: b for b in SC["bonds"]}
def _rat(slots):
    return "".join(f"<li><b>{html.escape(BYSLOT[s]['obligor'][:36])}</b> (ins {BYSLOT[s]['ai_insulation']:.0f} / cred {BYSLOT[s]['creditworthiness']:.0f}) &mdash; {PITCH[s]}</li>" for s in slots)
in_rat = _rat(sorted(in_slots, key=lambda s: -BYSLOT[s]["creditworthiness"]))
ex_rat = _rat(sorted([b["slot"] for b in SC["bonds"] if b["slot"] not in in_slots], key=lambda s: -BYSLOT[s]["creditworthiness"]))

HTML = f"""<!doctype html><html><head><meta charset='utf-8'><style>
@page{{margin:13mm 12mm}} body{{font:11.5px/1.45 -apple-system,'Helvetica Neue',Arial,sans-serif;color:#1a1a1a}}
h1{{font-size:20px;color:#0b2545;margin:0 0 1px}} .sub{{color:#566;font-size:11px;margin-bottom:8px}}
h2{{font-size:14px;color:#0b2545;border-bottom:1px solid #ccd;padding-bottom:2px;margin-top:15px}}
table{{border-collapse:collapse;width:100%;margin:5px 0;font-size:10.5px}}
th{{background:#0b2545;color:#fff;text-align:left;padding:4px 6px}} td{{border:1px solid #ccc;padding:3px 6px;vertical-align:top}}
tr:nth-child(even) td{{background:#f5f7fa}}
.kpi{{display:flex;gap:6px;margin:6px 0}} .kpi>div{{flex:1;background:#0b2545;color:#fff;border-radius:6px;padding:6px;text-align:center}}
.big{{font-size:16px;font-weight:700}} .lbl{{font-size:8.5px;opacity:.85;line-height:1.15}}
.two{{display:flex;gap:8px;margin:5px 0}} .two>div{{flex:1;padding:7px 9px;border-radius:6px;background:#eef1f6;font-size:10.5px}}
.is{{display:flex;gap:8px;margin:5px 0}} .is>div{{flex:1;padding:7px 9px;border-radius:6px;font-size:10px}}
.yes{{background:#eaf6ee;border-left:4px solid #1a7f3c}} .no{{background:#fdecec;border-left:4px solid #b22222}}
.warn{{background:#fff6e6;border-left:4px solid #c8902a;padding:6px 9px;margin:5px 0;font-size:10px}}
strong{{color:#0b2545}} em{{color:#555}} ul{{margin:2px 0;padding-left:16px}} li{{margin:1px 0}}
.foot{{color:#777;font-size:8.5px;margin-top:9px;border-top:1px solid #ddd;padding-top:4px}}
.pagebreak{{page-break-before:always}} table,.ex,.is,.kpi,.two{{page-break-inside:avoid}} h2{{page-break-after:avoid}}
</style></head><body>

<h1>California Tax-Exempt Income &mdash; Dual-Axis Credit &amp; Tech/AI-Insulation Methodology</h1>
<div class='sub'>Sample tearsheet &middot; v2 multi-channel framework &middot; Signal OS muni_credit &middot; 2026-06-07
&middot; <b>illustrative; not an offer or investment advice</b></div>

<div class='kpi'>
 <div><div class='big'>{S['avg_ai_insulation']:.0f}/100</div><div class='lbl'>avg AI-insulation score</div></div>
 <div><div class='big'>{S['avg_creditworthiness']:.0f}/100</div><div class='lbl'>avg creditworthiness (verified)</div></div>
 <div><div class='big'>{S['avg_ytw_pct']:.2f}%</div><div class='lbl'>avg yield-to-worst</div></div>
 <div><div class='big'>{avg_ytm:.2f}%</div><div class='lbl'>avg yield-to-maturity</div></div>
 <div><div class='big'>{S['tey_pct']:.2f}%</div><div class='lbl'>taxable-equiv (&times;2.01)</div></div>
 <div><div class='big'>{S['dur_to_worst']:.1f}y</div><div class='lbl'>duration-to-worst</div></div>
 <div><div class='big'>{S['n']}</div><div class='lbl'>holdings (research universe)</div></div>
</div>

<h2>Executive summary</h2>
<p><b>The problem.</b> A high-bracket Californian &mdash; especially in tech &mdash; is already heavily exposed to the
tech/AI cycle through salary, equity comp (RSUs/options), and portfolio. Yet the obvious tax shelter for their bond
allocation, California munis, is at the state level the <em>most tech-levered government revenue base in the country</em>
(capital-gains / stock-option income tax). Buy a generic CA muni fund and you may be <b>doubling down on the very risk
you're trying to diversify away from</b>.</p>
<p><b>The product.</b> A California tax-exempt income strategy selected on <b>two independent, auditable screens</b>:
(1) <b>creditworthiness</b>, verified bond-by-bond against primary sources, and (2) <b>tech/AI income-channel
insulation</b>, measuring exposure across <b>nine</b> distinct transmission channels at the bond-security level. The
result: double-tax-exempt income (~{S['avg_ytw_pct']:.1f}% YTW / {S['tey_pct']:.1f}% taxable-equivalent) from credits
whose <em>creditworthiness does not deteriorate when tech/AI wealth evaporates</em>.</p>
<p><b>Why it's different &mdash; and defensible.</b> No generic CA muni ETF offers <b>income-channel diversification</b>.
Every score is transparent and every exclusion is auditable (see worked examples). And we are deliberately precise about
what this is <em>not</em>: not a price hedge, not alpha, not a market forecast &mdash; just tax-exempt income, verified
credit quality, and a diversification axis no one else screens for.</p>

<h2>The pitch &mdash; two independent screens</h2>
<p><b>Creditworthiness screen (verified diligence).</b> Each bond's pledged security is verified against primary
sources and the full trail is retained: the claim (the security/lien), how it was checked, the authority that
confirms it (EMMA official statements, CA Gov Code, CDIAC default-draw, rating actions), and the verdict
(Verified / Verified-wrap / <b>Unverifiable</b>). The diligence is auditable, not a black box &mdash; and
<em>Unverifiable &ne; clean</em>: a bond whose security we have not actually read is excluded, not assumed good.</p>
<p><b>Tech/AI insulation screen (multi-channel).</b> A tech/AI bust reaches California muni credit through nine
distinct channels, not one. We score each separately and at the bond-security level (the pledged revenue), not the
issuer's general economy &mdash; so a property-tax GO levy scores insulated even if the issuer's <em>budget</em>
feels pension or sales-tax pressure. The composite score is insulation across all nine channels.</p>

<h2 class='pagebreak'>Tech/AI Transmission Channels</h2>
<p style='font-size:10.5px'>An AI/tech bust reaches CA muni credit through <b>nine distinct channels</b>, not one. We score
each separately and at the <b>bond-security level</b> (does the channel reach the <em>pledged revenue</em>?). &ldquo;Wt&rdquo;
= weight in the insulation composite; &ldquo;Port. exp&rdquo; = this portfolio's average exposure to that channel.</p>
<table><tr><th style='width:21%'>Channel</th><th>What it is &mdash; how a tech/AI bust reaches the bond</th><th>Wt</th><th>Port.<br>exp</th></tr>
{chan_rows2}</table>
<p style='font-size:10px'><em>The portfolio is built from pledges (property-tax GO debt service, essential-service revenue,
insured/agency) structurally disconnected from <b>all nine</b> channels &mdash; not just income tax. <b>That</b> is the
defensible meaning of &ldquo;insulated.&rdquo; Note the budget-vs-security distinction: the pension channel can squeeze a
school district's <em>operating budget</em> while its GO <em>debt-service levy</em> stays untouched &mdash; we score the
pledge, not the issuer's general economy.</em></p>

<h2 class='pagebreak'>Creditworthiness Check (verified diligence)</h2>
<p style='font-size:10.5px'>Every credit claim is verified against a primary authority and <b>documented end-to-end</b>: the claim, how it was
checked, the authority that confirms it, and the verdict (Verified / Verified-wrap / <b>Unverifiable</b>). &ldquo;CORE&rdquo; dimensions drive
the v2 creditworthiness score; &ldquo;EXTENDED&rdquo; are sector-specific diligence layers from the detector library,
applied where the pledge warrants.</p>
<table><tr><th style='width:18%'>Dimension</th><th>What we verify</th><th>Authority / source</th><th>In score</th></tr>
{cred_rows}</table>
<p style='font-size:10px'><em>Guiding rule: <b>UNVERIFIABLE &ne; clean.</b> A bond whose security we have not actually read is
excluded until it is &mdash; a strong agency rating does not substitute for the unread lien (see El Camino, below).</em></p>

<h2 class='pagebreak'>Worked example &mdash; Included</h2>
{ex_incl}
<h2 class='pagebreak'>Worked example &mdash; Excluded for creditworthiness</h2>
{ex_creditexcl}
<h2 class='pagebreak'>Worked example &mdash; Diligence resolved (was unverifiable)</h2>
{ex_cred}
<h2 class='pagebreak'>Worked example &mdash; Excluded for AI correlation</h2>
{ex_ai}

<h2 class='pagebreak'>Portfolio holdings ({S['n']}, equal-weight)</h2>
<table><tr><th>Obligor</th><th>Security</th><th>AI-ins</th><th>Credit</th><th>YTW %</th><th>YTM %</th><th>Dur-w</th></tr>
{hold_rows}</table>
<p style='font-size:10px'><b>Stats:</b> avg AI-insulation {S['avg_ai_insulation']:.0f} &middot; avg creditworthiness
{S['avg_creditworthiness']:.0f} &middot; YTW {S['avg_ytw_pct']:.2f}% / TEY {S['tey_pct']:.2f}% &middot; duration-to-worst
{S['dur_to_worst']:.1f}y / to-maturity {S['dur_to_maturity']:.1f}y &middot; 6 school GO (SB-222 lien) / 2 water / 2 CCRC
(Cal-Mortgage) / 1 CalHFA.</p>

<h2 class='pagebreak'>Selection rationale &mdash; why each name is in or out</h2>
<p style='font-weight:700;color:#1a7f3c;margin:4px 0 1px'>Included ({S['n']}) &mdash; clears both gates</p>
<ul style='font-size:10px;margin-top:0'>{in_rat}</ul>
<p style='font-weight:700;color:#b22222;margin:7px 0 1px'>Excluded (9)</p>
<ul style='font-size:10px;margin-top:0'>{ex_rat}</ul>

<h2>What this IS &mdash; and is NOT</h2>
<div class='is'>
 <div class='yes'><b>IS</b><ul>
  <li>Tax-exempt (fed+CA) income, primary-source credit-vetted</li>
  <li><b>Income-channel diversification</b> for tech-comp-concentrated CA holders &mdash; credit insulated from the tech/AI cycle across nine channels</li>
  <li>Two transparent, auditable, orthogonal scores</li></ul></div>
 <div class='no'><b>IS NOT</b><ul>
  <li>A price hedge / return anti-correlation (that's a duration bet that <b>inverted &minus;30% in 2022</b>)</li>
  <li>Alpha &mdash; not return-backtested vs a CA muni ETF</li>
  <li>A <em>validated predictive</em> rating &mdash; scores are STRUCTURAL classifications + diligence verdicts for selection, not forecasts</li></ul></div>
</div>

<div class='warn'><b>Honest limits.</b> (1) <b>{S['n']} holdings, not 20</b> &mdash; the dual-axis gate clears only
{S['n']} of the 20-name <em>research</em> universe; a diversified 20 needs a broader CA screen (same archetypes,
more names). (2) <b>Long duration</b> ({S['dur_to_worst']:.1f}y to-worst) &mdash; production targets <b>intermediate
~4&ndash;7y</b> via maturity selection; this is income + credit quality, NOT crash protection. (3) Scores are
structural, not validated betas. (4) Single-state (CA) concentration; some sectors trade thinly.</div>

<div class='foot'>Reproducible: channel_scoring_v2.py, build_v2_portfolio.py, data/channel_scores_v2.json, data/v2_portfolio.json.
Sources: EMMA RTRS (yields/terms), CA Gov Code (SB-222), CDIAC DebtWatch (default-draw), HCAI/Cal-Mortgage,
agency ratings. Yields gross of fees, as-of 2026-06-05/07. Non-claims reflect two adversarial reviews and are stated
deliberately. Illustrative; not an offer, solicitation, or investment advice.</div>
</body></html>"""
open(OUT, "w").write(HTML)
print("wrote", OUT, len(HTML), "bytes | portfolio channel exposure:",
      {c: round(pexp[c]*100) for c in pexp if pexp[c] > 0})
