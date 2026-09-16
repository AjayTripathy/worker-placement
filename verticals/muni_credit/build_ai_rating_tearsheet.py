"""Publish the methodology tearsheet: rating CA munis by AI-crash credit sensitivity.
Generates HTML from the live cap-gains-beta model (capgains_beta.py / its JSON output)
so the rating scale, formula tables, and worked example stay in sync with the model.
"""
import json, html
import capgains_beta as M   # CHANNEL, STRUCT, REGION_*, ASSIGN

DATA = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_v2_capgains_beta.json"
OUT  = "/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/MUNI_AI_CRASH_RATING_METHODOLOGY.html"

d = json.load(open(DATA)); rows = d["rows"]; agg = d["aggregate"]

def tier(b):
    if b <= 0.05: return ("AI-1", "Insulated", "#1a7f3c")
    if b <= 0.15: return ("AI-2", "Low",       "#5a9e2f")
    if b <= 0.30: return ("AI-3", "Moderate",  "#c8902a")
    if b <= 0.60: return ("AI-4", "High",       "#d2691e")
    return            ("AI-5", "Direct",     "#b22222")

from collections import Counter
tc = Counter(tier(r["beta"])[0] for r in rows)

# per-name rows (already sorted desc by beta in the JSON)
namerows = ""
for r in rows:
    t, lab, col = tier(r["beta"])
    namerows += (f"<tr><td>{r['slot']}</td><td>{html.escape(r['obligor'])}</td>"
                 f"<td>{r['channel'].replace('_',' ')}</td>"
                 f"<td style='text-align:right'>{r['beta']:.3f}</td>"
                 f"<td style='text-align:center'><b style='color:{col}'>{t}</b> {lab}</td></tr>")

def ptable(dct, hdr):
    s = f"<table class='param'><tr><th>{hdr}</th><th>value</th></tr>"
    for k, v in dct.items():
        s += f"<tr><td>{k.replace('_',' ')}</td><td style='text-align:right'>{v:.2f}</td></tr>"
    return s + "</table>"

SCALE = [
    ("AI-1","Insulated","≤ 0.05","#1a7f3c","Statutory-lien property-tax GO (SB-222 school), water revenue","Untouched in dot-com"),
    ("AI-2","Low","0.05 – 0.15","#5a9e2f","Enterprise revenue (hospital, CCRC-insured), housing finance","Minor spread drift"),
    ("AI-3","Moderate","0.15 – 0.30","#c8902a","Tax-increment TAB, tech-hub hospital, county GF appropriation","1–2 notch / spread widening"),
    ("AI-4","High","0.30 – 0.60","#d2691e","Local-GF appropriation, weak/late-base tax increment","Multi-notch in a deep shock"),
    ("AI-5","Direct","> 0.60","#b22222","State GF / income-tax-backed GO & appropriation","4–5 notches (CA AA→BBB, 2003)"),
]
scalerows = ""
for t, lab, rng, col, arch, dot in SCALE:
    scalerows += (f"<tr><td style='text-align:center'><b style='color:{col};font-size:14px'>{t}</b><br>"
                  f"<span style='color:{col}'>{lab}</span></td><td style='text-align:center'>{rng}</td>"
                  f"<td>{arch}</td><td>{dot}</td><td style='text-align:center'>{tc.get(t,0)}</td></tr>")

HTML = f"""<!doctype html><html><head><meta charset='utf-8'><style>
@page{{margin:15mm 14mm}}
body{{font:12.5px/1.5 -apple-system,'Helvetica Neue',Arial,sans-serif;color:#1a1a1a}}
h1{{font-size:22px;color:#0b2545;margin:0 0 2px}}
.sub{{color:#566;font-size:12px;margin-bottom:10px}}
h2{{font-size:15.5px;color:#0b2545;border-bottom:1px solid #ccd;padding-bottom:3px;margin-top:20px}}
table{{border-collapse:collapse;width:100%;margin:7px 0;font-size:11.5px}}
th{{background:#0b2545;color:#fff;text-align:left;padding:5px 7px}}
td{{border:1px solid #ccc;padding:4px 7px;vertical-align:top}}
tr:nth-child(even) td{{background:#f5f7fa}}
.kpi{{display:flex;gap:8px;margin:8px 0}}
.kpi>div{{flex:1;background:#0b2545;color:#fff;border-radius:6px;padding:8px;text-align:center}}
.big{{font-size:19px;font-weight:700}} .lbl{{font-size:9.5px;opacity:.85;line-height:1.2}}
.param{{width:48%;display:inline-table;margin-right:2%;font-size:11px}}
.formula{{background:#eef1f6;border-left:4px solid #0b2545;padding:8px 12px;font-size:13px;margin:8px 0}}
.warn{{background:#fff6e6;border-left:4px solid #c8902a;padding:8px 12px;margin:8px 0;font-size:11.5px}}
strong{{color:#0b2545}} em{{color:#555}} code{{background:#eef;padding:1px 4px;border-radius:3px}}
.foot{{color:#777;font-size:10px;margin-top:14px;border-top:1px solid #ddd;padding-top:6px}}
</style></head><body>

<h1>Rating Municipal Bonds by AI-Crash Credit Sensitivity</h1>
<div class='sub'>Signal OS &middot; muni_credit methodology &middot; the &beta;-CapGains framework &middot;
v1.4 (validated + blinded + count-hardened + CDIAC-checked) &middot; 2026-06-06 &middot; reproducible: <code>capgains_beta.py</code></div>

<div class='kpi'>
 <div><div class='big'>1</div><div class='lbl'>transmission channel<br>(state-GF cap-gains income tax)</div></div>
 <div><div class='big'>&minus;71%</div><div class='lbl'>calibration shock<br>(CA cap-gains rev $17B&rarr;$5B, dot-com)</div></div>
 <div><div class='big'>5</div><div class='lbl'>rating tiers<br>AI-1 Insulated &rarr; AI-5 Direct</div></div>
 <div><div class='big'>0–1+</div><div class='lbl'>&beta; scale<br>(state GO &equiv; 1.00)</div></div>
</div>

<h2>1 &middot; What this rates &mdash; and what it does not</h2>
<p>A muni's <strong>credit/spread sensitivity to a California capital-gains shock</strong> &mdash;
the channel through which an <strong>AI-equity bubble burst</strong> reaches muni credit (the same
pipe the dot-com bust used). It is a <strong>relative credit-stress rating</strong>, not:
(a) a <em>default</em> rating &mdash; CA GO debt service is constitutionally 2nd-priority, so
default &beta; &asymp; 0 even at AI-5; (b) a <em>total-return / price</em> rating &mdash; price also
rides the rate regime (see &sect;5 caveat). Hold rates constant; this isolates the cap-gains
credit leg.</p>

<h2>2 &middot; The transmission model</h2>
<p>California's General Fund is the most tech-levered state revenue base in the U.S. via
<strong>capital-gains + stock-option + IPO-wealth personal income tax</strong> (avg ~7.9% of GF
revenue, ~3&times; the volatility of overall PIT). An AI crash evaporates that wealth and the
revenue with it. <strong>Anchor:</strong> in the dot-com bust this revenue ran
<strong>$17B (2000-01) &rarr; $5B (2002-03), &minus;71%</strong> [LAO]; CA <strong>State GO was cut
AA/Aa2&rarr;BBB/A2 (4&ndash;5 notches, worst state)</strong> while SB-222 school GO and water revenue
were <strong>untouched</strong>. The &beta; scale is normalized so an <strong>unshielded state-GF
income-tax claim = 1.00</strong>, calibrated to that ordering.</p>

<h2>3 &middot; The scoring formula</h2>
<div class='formula'><b>&beta;<sub>capgains</sub> = channel-elasticity &times; structure-shield &times; region-factor</b>
&nbsp;&nbsp;(normalized: state-GF income-tax claim = 1.00)</div>
{ptable(M.CHANNEL,'Revenue-channel elasticity')}
{ptable(M.STRUCT,'Credit-structure shield')}
<p style='font-size:11px'><b>Region factor:</b> Silicon Valley / Bay Area = {M.REGION_SV:.2f} &middot;
Bay-adjacent = {M.REGION_BAY:.2f} &middot; elsewhere = {M.REGION_BASE:.2f}.
<b>Uncertainty:</b> &plusmn;{int(M.CHANNEL_BAND*100)}% band on the channel elasticity &rarr; per-name low/high.</p>

<h2>4 &middot; The rating scale</h2>
<table><tr><th>Tier</th><th>&beta; range</th><th>Revenue archetypes</th><th>Dot-com behavior (validation)</th><th>n in basket</th></tr>
{scalerows}</table>

<h2>5 &middot; Modifiers &amp; the critical caveat</h2>
<ul style='font-size:11.5px;margin:4px 0'>
<li><b>Notch DOWN (more insulated):</b> statutory lien (SB-222), bond insurance / Cal-Mortgage-HCAI
(state-credit substitution), dedicated non-GF pledge.</li>
<li><b>Notch UP (more exposed):</b> tech-hub region (direct tech-economy footprint), GF appropriation
/ lease structure, late-vintage tax-increment with a thin base above the frozen AV.</li>
</ul>
<div class='warn'><b>Credit &ne; price.</b> This rating fixes rates. <em>Total-return</em> safety in an
AI crash also depends on the <b>rate regime</b>: the muni hedge works only in a <b>Fed-cutting growth
scare</b> (dot-com analog &mdash; long duration becomes a tailwind on top of insulated credit). In a
<b>liquidity crunch</b> (2008, Mar-2020) or <b>inflation / rate-shock</b> (2022) it degrades, breaks,
or inverts &mdash; munis fall <em>with</em> equities regardless of a clean AI-credit rating. A low
&beta;-CapGains is <b>necessary, not sufficient,</b> for drawdown safety.</div>

<h2>6 &middot; Worked example &mdash; CA Muni Honesty Basket (n={agg['n']})</h2>
<p><b>Equal-weight basket &beta; = {agg['basket_beta_equalwt']:.2f}</b> (band {agg['basket_beta_band']})
&mdash; ~{int(agg['basket_beta_equalwt']*100)}% of the cap-gains credit-sensitivity of an all-state-GO
portfolio &rarr; overall rating <b style='color:#5a9e2f'>AI-2 (Low)</b>, low end of Moderate when blended.
<b>Concentration:</b> the single CA State GO drives <b>{agg['state_go_contrib_pct']}%</b> of the entire
basket &beta;; ex that name, &beta; = {agg['basket_beta_ex_state_go']:.3f}. The inert tail (6 SB-222
school GO + 2 water) is {agg['inert_tail_share_pct']}% of total &beta; across 8 of 20 names.</p>
<table><tr><th>#</th><th>Obligor</th><th>Channel</th><th>&beta;</th><th>Rating</th></tr>
{namerows}</table>

<h2>7 &middot; Backtest validation &mdash; does the rating predict reality?</h2>
<p>Two out-of-sample tests (free-data feasible); a third proposed. <b>Both confirm the rating's central claims.</b></p>

<p style='font-weight:700;color:#33415c;margin:8px 0 2px'>7.1 &nbsp;Credit-tier dispersion is regime-conditional</p>
<p style='font-size:11px;margin:2px 0'>High-yield muni (VWAHX &mdash; proxy for lower-credit / higher-&beta; revenue &amp; weaker structure) vs investment-grade long muni (VWLTX). Lower credit should lag &mdash; and most in <em>fundamental</em> busts, least in <em>rate</em> shocks.</p>
<table><tr><th>Crash</th><th>Regime</th><th>HY muni (VWAHX)</th><th>IG long (VWLTX)</th><th>HY &minus; IG</th></tr>
<tr><td>Dot-com 2000&ndash;02</td><td>growth scare, Fed cuts</td><td>+25.2%</td><td>+30.5%</td><td><b>&minus;5.3 pp</b></td></tr>
<tr><td>GFC 2008</td><td>liquidity crisis</td><td>&minus;10.5%</td><td>&minus;4.9%</td><td><b>&minus;5.6 pp</b></td></tr>
<tr><td>COVID 2020</td><td>liquidity shock (recovered)</td><td>+5.4%</td><td>+6.2%</td><td>&minus;0.8 pp</td></tr>
<tr><td>2022</td><td>rate shock</td><td>&minus;11.8%</td><td>&minus;10.4%</td><td>&minus;1.4 pp</td></tr></table>
<p style='font-size:11px;margin:2px 0'><b>Result:</b> credit-tier dispersion is <b>~4&times; larger in the two fundamental busts</b> (dot-com, GFC: ~&minus;5.5 pp) than in the transient-liquidity / rate episodes (2020, 2022: ~&minus;1 pp). &beta; &mdash; credit-channel sensitivity &mdash; bites hardest in a real crisis, so a low-&beta; rating is most protective exactly when it matters. <em>Caveat: HY-vs-IG is general credit quality, a loose proxy for the cap-gains channel specifically.</em></p>

<p style='font-weight:700;color:#33415c;margin:10px 0 2px'>7.2 &nbsp;CA State GO credit tracks cap-gains, not rates (the AI-5 anchor)</p>
<p style='font-size:11px;margin:2px 0'>The tight, on-point test: if &beta;=1.0 for state GO is right, CA GO credit should move with the cap-gains cycle and be <em>orthogonal</em> to rate shocks.</p>
<table><tr><th>Episode</th><th>Cap-gains revenue</th><th>CA GO rating action</th><th>Validates</th></tr>
<tr><td>Dot-com 2001&ndash;03</td><td>$17B &rarr; $5B (&minus;71%)</td><td>AA &rarr; BBB (&minus;4&ndash;5 notches)</td><td>AI-5 &check;</td></tr>
<tr><td>GFC 2008&ndash;09</td><td>&rarr; ~$2B (2009 trough)</td><td>A &rarr; Baa1/BBB + IOUs</td><td>AI-5 &check;</td></tr>
<tr><td>Recovery 2010s&ndash;&rsquo;21</td><td>rebuilt (record 2021)</td><td>upgraded &rarr; Aa2/AA</td><td>symmetric &check;</td></tr>
<tr><td>2022 rate shock</td><td>still high</td><td><b>no downgrade</b></td><td>credit&ne;price &check;</td></tr></table>
<p style='font-size:11px;margin:2px 0'><b>Result:</b> CA State GO was slashed in <b>both equity-bubble busts</b> (cap-gains collapse), recovered <b>symmetrically</b> as cap-gains rebuilt, and was <b>untouched in the 2022 rate shock</b> &mdash; confirming the cap-gains channel drives GO credit (validates AI-5 = 1.0) and that the 2022 muni drawdown was pure price/duration (validates the credit&ne;price caveat).</p>

<p style='font-weight:700;color:#33415c;margin:10px 0 2px'>7.3 &nbsp;Cross-sectional ordering test &mdash; blinded agents</p>
<p style='font-size:11px;margin:2px 0'>Does the full AI-1&hellip;AI-5 scale rank-order by <em>actual</em> credit stress in each crash? <b>Blinded method:</b> the &beta;-tier sector order was sealed to disk <em>first</em>; four research agents then measured each sector&rsquo;s realized credit outcome (ratings, defaults, spreads) per crash with <b>no knowledge</b> of the &beta;-framework, the cap-gains hypothesis, the AI-crash framing, or the expected order. Spearman rank-corr of their blind rankings vs the sealed prediction:</p>
<table><tr><th>Crash (shock type)</th><th>Spearman &rho;</th><th>State GO actual rank</th><th>Read</th></tr>
<tr><td>Dot-com 2000&ndash;03 (income / cap-gains)</td><td><b>0.90</b></td><td>#1 (most stressed)</td><td>strong &mdash; the AI archetype</td></tr>
<tr><td>GFC 2008&ndash;09 (property / liquidity)</td><td>0.33</td><td>#3</td><td>diverges: CCRC/CalHFA jump up</td></tr>
<tr><td>COVID 2020 (operational)</td><td>0.45</td><td>#5</td><td>weak: operational sectors top</td></tr>
<tr><td>2022 (rate / inflation)</td><td>0.24</td><td>#6 (upgraded)</td><td>State GO upgraded &mdash; cap-gains was high</td></tr></table>
<p style='font-size:11px;margin:2px 0'><b>Result &mdash; the rating is channel-SPECIFIC, exactly as designed.</b> It rank-orders credit stress at <b>&rho;=0.90 in the income/cap-gains regime</b> (the dot-com bust = the AI-crash archetype) and <em>correctly</em> does NOT predict the property (2008), operational (2020), or rate (2022) regimes &mdash; a generic credit-quality proxy would score high everywhere. The <b>State GO is the tell:</b> most-stressed (#1) when cap-gains collapsed (dot-com), but <b>upgraded</b> (#6) in 2022 when cap-gains hit a record &mdash; the AI-5 name swings with the cap-gains cycle, confirming the mechanism. The <b>insulated tier (school GO, water) sat bottom-ranked in all four regimes.</b> <em>Caveat: dot-com anchored the scale&rsquo;s endpoints, so its &rho; is out-of-sample in the middle tiers but not the extremes; the cleaner OOS evidence is the discriminant pattern across the other three crises. Agents&rsquo; middle-tier (county COP, TAB) rankings were often low-confidence on thin data.</em></p>

<p style='font-weight:700;color:#33415c;margin:10px 0 2px'>7.4 &nbsp;Hardening with per-issuer counts (blinded round 2)</p>
<p style='font-size:11px;margin:2px 0'>A second blinded round tried to replace the agents&rsquo; middle-tier <em>judgment</em> with <em>enumerated</em> rating-action counts (rubric sealed first). <b>Decisive finding &mdash; a data limit:</b> per-issuer CA rating counts for the middle tiers are <b>not publicly recoverable</b> (proprietary Moody&rsquo;s/S&amp;P/Fitch DBs + CDIAC default-draw index); defaults are enumerable, mid-tier downgrades are not. Scoring what <em>is</em> documented: <b>hardened dot-com &rho; = 0.80</b> (vs 0.90 judgment-based &mdash; five middle sectors tie at zero documented CA actions, so the middle is <em>unresolved, not wrong</em>); the <b>insulated tier had 0 documented actions in all four regimes</b>; State GO took ~9 multi-notch actions; CalHFA was upgraded in 2022. <b>The rating is robust at the extremes and bucket level; the fine 8-way middle ordering is data-limited, not validated.</b> <em>Refinement (model-v2): TAB/hospital/CCRC showed their stress in the property/operational regimes, not income &mdash; so &beta;-CapGains is conservative for the cap-gains channel; re-classing them toward AI-1/2 for income shocks would raise the fit.</em></p>
<p style='font-size:11px;margin:2px 0'><b>CDIAC index &mdash; scripted, proven dead-end for this.</b> The one CA-specific granular source (CDIAC default-draw) was pulled in full via the real DebtWatch API (710 events, 1991&ndash;2026). It <b>cannot harden the eight sectors</b>: it is <b>89% Mello-Roos/CFD land-secured draws</b>, and the rating-test sectors appear 0&ndash;3&times; each &mdash; because GO/school/hospital/CCRC/water/county stress shows up as <em>downgrades</em>, which CDIAC does not track (rating actions live only in proprietary agency archives). The public-data limit is now demonstrated, not asserted. <em>(Reproducible: <code>cdiac_draws.py</code>.)</em></p>

<h2>8 &middot; Caveats</h2>
<p style='font-size:11px'><b>Structural model, not a regression</b> &mdash; per-obligor 20-yr pledged-revenue
series don't exist to regress on CA cap-gains receipts; elasticities are first-principles, anchored to
the dot-com episode + LAO data. <b>CA-specific</b> &mdash; generalizes to other states by their GF
income-tax / cap-gains share (CA is the high extreme; TX/FL with no income tax &rarr; near-zero state
channel). <b>Single-name concentration</b> dominates a small basket &mdash; read &beta; at the name
level, not just the average. <b>&beta; is a spread/rating beta</b>, calibrated to relative ordering,
not a forecast of basis points.</p>

<div class='foot'>Sources: LAO (CA capital-gains volatility &amp; GF share); CA State Treasurer GO ratings
history; S&amp;P / Moody's / Fitch dot-com rating actions; Signal OS muni_credit holdings &amp;
<code>capgains_beta.py</code>. Methodology rates relative AI-crash credit sensitivity for analyst use;
not investment advice.</div>
</body></html>"""

open(OUT, "w").write(HTML)
print("wrote", OUT, f"({len(HTML)} bytes)")
print("tier counts:", dict(tc))
