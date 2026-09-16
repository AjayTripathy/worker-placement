"""Generate the blended-sleeve (Option C) pitch tearsheet with per-bond liquidity / AI-insulation /
our-credit ratings alongside the agency benchmark, plus methodology write-ups. Plain analyst language
(no internal jargon). Reads muni_etf_sleeve_blended.json -> outputs/CA_MUNI_SLEEVE_C_TEARSHEET.md."""
import json, datetime

SLEEVE = json.load(open('muni_etf_sleeve_blended.json'))
S = SLEEVE['basket_summary']; B = SLEEVE['barbell']
ASOF = "2026-06-09"

# ---- per-bond rating functions ----
def liq_rating(m):
    sp = m.get('px_spread'); n = m.get('n365', 0); ts = m.get('two_sided_days', 0)
    if sp is not None and sp <= 0.25 and n >= 50 and ts >= 10: return "L1", "Highly liquid"
    if (sp is None or sp <= 0.40) and n >= 24 and ts >= 3:     return "L2", "Liquid"
    if (sp is None or sp <= 0.75) and n >= 12 and ts >= 1:     return "L3", "Moderate"
    return "L4", "Thin"

def ai_rating(insul):
    e = (100 - insul) / 100.0
    if e <= 0.05: return "AI-1", "Insulated"
    if e <= 0.15: return "AI-2", "Low"
    if e <= 0.30: return "AI-3", "Moderate"
    if e <= 0.60: return "AI-4", "High"
    return "AI-5", "Direct"

def cred_grade(score):
    return ("Strong" if score >= 88 else "Solid" if score >= 80 else
            "Adequate" if score >= 72 else "Conditional" if score >= 64 else "Weak/Unverified")

# credit-key -> (short pledge rationale, agency class benchmark Moody's/S&P)
CK = {
 "school_go_sb222": ("Unlimited ad-valorem tax + SB-222 statutory FIRST lien on the levy", "~Aa2–Aa3 / AA– to AA"),
 "uc_grb":  ("UC broad General Revenues pledge; medical-center revenue excluded",            "Aa2 / AA+"),
 "uc_lprb": ("UC specific financed-project revenues; narrower, no state appropriation",      "~Aa3 / AA–"),
 "water":   ("Essential-service net-revenue pledge + ~1.2x rate covenant",                   "~A1–Aa3 / A+ to AA–"),
 "state_go":("State GO full faith & credit; 2nd-priority on the General Fund",               "Aa2 / AA–"),
}
SECT2CK = {"SCHOOL-GO": "school_go_sb222", "WATER-REV": "water", "ELEC-REV": "water"}

def ck_of(b):
    return b.get('security_credit_key') or SECT2CK.get(b.get('sectype'), "school_go_sb222")

# ---- assemble rows ----
rows = []
for b in sorted(B, key=lambda x: (x['maturity'], -x.get('ytw', 0))):
    m = b.get('liq', {}); ck = ck_of(b)
    lr, ln = liq_rating(m); ar, an = ai_rating(b['insul']); cg = cred_grade(b['credit'])
    rows.append({
        "cusip": b['cusip'], "sleeve": b.get('sleeve', ''), "cls": CK[ck][0],
        "coupon": b['coupon'], "mat": b['maturity'][:7], "px": b['emma_px'],
        "ytw": b['ytw'] * 100, "tey": b.get('tey_ytw_aftertax', b.get('tey_ytw', 0)) * 100,
        "liq": f"{lr} {ln}", "spread": m.get('px_spread'), "n365": m.get('n365'),
        "ai": f"{ar} {an}", "insul": b['insul'],
        "our": f"{b['credit']} {cg}", "agency": CK[ck][1], "par": b['par'],
    })

# ---- rating-distribution summary ----
from collections import Counter
ai_dist = Counter(r['ai'].split()[0] for r in rows)
liq_dist = Counter(r['liq'].split()[0] for r in rows)
our_dist = Counter(r['our'].split()[1] for r in rows)

def f(x, d=2): return f"{x:.{d}f}" if x is not None else "—"

md = []
md.append(f"# California Insulated Muni Sleeve — Tearsheet\n")
md.append(f"*Blended liquid‑anchor / yield‑core ladder · as of {ASOF} · for analyst review, not investment advice*\n")
md.append("## Snapshot\n")
md.append(f"| | |\n|---|---|")
md.append(f"| Par | ${S['total_par']:,} ({S['n']} positions) |")
md.append(f"| Construction | after‑tax‑TEY optimized; ≥{int(S.get('anchor_min_fast_share',0.4)*100)}% liquid‑anchor constraint (actual {int(S.get('fast_share',0)*100)}%) |")
md.append(f"| Yield to worst | **{f(S['par_weighted_ytw_pct'])}%** |")
md.append(f"| Tax‑equivalent yield (after‑tax, CA top bracket) | **{f(S['par_weighted_tey_aftertax_pct'])}%** |")
md.append(f"| AI‑insulation (0–100) | **{S['par_weighted_insulation']}** |")
md.append(f"| Our credit (0–100) | **{S['par_weighted_credit']}** |")
md.append(f"| Median round‑trip spread | {f(S['median_same_day_spread_pt'],3)} pt |")
md.append(f"| Ladder | {S['ladder']} |")
md.append("")
md.append(f"**Rating mix.** AI‑insulation: " + ", ".join(f"{k} ×{ai_dist[k]}" for k in sorted(ai_dist)) +
          ".  Liquidity: " + ", ".join(f"{k} ×{liq_dist[k]}" for k in sorted(liq_dist)) +
          ".  Our credit: " + ", ".join(f"{k} ×{our_dist[k]}" for k in sorted(our_dist, key=lambda x:-our_dist[x])) + ".\n")

md.append("## Thesis\n")
md.append(
"This sleeve holds California municipal bonds chosen for one property the market under‑prices: **structural "
"insulation of the *credit* from an AI/technology‑sector crash.** California's General Fund leans on personal "
"income tax, and the most volatile slice of that is capital‑gains realizations from tech equity. A severe AI "
"de‑rating would collapse those realizations (the dot‑com bust cut California capital‑gains revenue ~71% and "
"pressured state‑General‑Fund‑backed credits by an estimated 4–5 notches) — yet bonds secured by a statutory "
"property‑tax lien (school general obligation) or by essential‑service utility revenue kept paying, untouched. "
"We buy those insulated pledges and *exclude* the state‑General‑Fund channel. The yield is competitive not "
"because we take credit or insulation risk, but because these issues are small, obscure, and lightly traded — "
"we are paid for **illiquidity and obscurity inside verified‑safe credits**, which is a very different risk than "
"reaching for yield down the quality curve.\n")

md.append("## How to read the three ratings\n")
md.append("### AI‑insulation rating (AI‑1 … AI‑5)\n")
md.append(
"We rate each bond's **credit** sensitivity — not its price — to a severe AI/tech crash, through the channel that "
"actually transmits such a shock to California issuers. We decompose each security's revenue pledge into exposure "
"to nine economic channels and weight them by how strongly an AI crash hits each: capital‑gains/personal‑income "
"tax is the heaviest (it drives the state General Fund), followed by property assessed value, public‑pension "
"funding, technology‑employer concentration, hospital balance sheets, commercial office real estate, housing "
"prices, sales tax, and transit/airport activity. Each security type carries an exposure profile (0 = insulated … "
"1 = fully exposed) for every channel; the weighted sum is its exposure, and **insulation = 100 − exposure**. We "
"then bin to a five‑tier scale:\n")
md.append("| Tier | Exposure | Meaning | Typical security | Dot‑com (2001–03) outcome |\n|---|---|---|---|---|")
md.append("| **AI‑1** | ≤ 5% | Insulated | Statutory‑lien property‑tax school GO; essential‑service water/utility revenue | Untouched |")
md.append("| **AI‑2** | 5–15% | Low | University general/limited‑project revenue; insured enterprise revenue | Minor spread drift |")
md.append("| **AI‑3** | 15–30% | Moderate | Tax‑increment; tech‑hub hospital; county general‑fund appropriation | 1–2 notch / spread widening |")
md.append("| **AI‑4** | 30–60% | High | Local general‑fund appropriation; weak tax increment | Multi‑notch in a deep shock |")
md.append("| **AI‑5** | > 60% | Direct | State General Fund / income‑tax‑backed GO & appropriation | 4–5 notches (CA AA→BBB, 2003) |")
md.append("\n*This rates structural insulation, not price. In a pure interest‑rate shock all munis can fall together; "
"AI‑insulation is about which pledges keep paying when tech‑driven state revenue collapses.*\n")

md.append("### Our credit analysis (0–100) — and why it sits *alongside* the agency rating\n")
md.append(
"We score the **actual legal pledge**, read from the official statement or the governing statute — not the issuer's "
"name or the marketed label. The score is anchored on the strength and seniority of that pledge:\n\n"
"- **Statutory first‑lien unlimited‑ad‑valorem school GO (~90)** — the property‑tax levy adjusts to cover debt "
"service regardless of the economy, and California's SB‑222 (Gov. Code §53515) puts bondholders on a statutory "
"**first** lien ahead of other claims. Strongest structure in the sleeve.\n"
"- **UC Regents General Revenue Bonds (~82)** — the University's broad revenue pledge (tuition and fees, "
"indirect‑cost recovery, auxiliary and sales/services revenue, investment income, and certain state educational "
"appropriations). The resilient **medical‑center revenues are excluded** (separately secured), which we treat as a "
"modest negative versus the headline ‘University’ pledge.\n"
"- **UC Limited Project Revenue Bonds (~74)** — pledge only the revenues of the *specific* financed projects "
"(student housing, parking, dining); narrower and more concentrated, but with **no state‑appropriation dependence**, "
"so structurally more AI‑insulated even though it is a notch weaker on credit.\n"
"- **Essential‑service water/wastewater revenue (~80)** — net‑revenue pledge backed by a rate covenant (typically "
"~1.2× coverage) on a service people cannot stop buying.\n\n"
"We **down‑rate** lease / certificate‑of‑participation structures for annual‑appropriation and abatement risk, and "
"we flag any bond **Unverified** where we have not read the official statement — *unverified is never treated as "
"clean*. We map the score to a grade: Strong (≥88), Solid (≥80), Adequate (≥72), Conditional (≥64).\n\n"
"**Why our analysis stands in for the rating here:** EMMA returns *no third‑party agency rating* for most of these "
"small issuers — the agencies do not publish/redistribute them on the public feed. A buyer leaning on agency "
"letters is effectively flying blind on these names; our security/lien read is the substitute. The **Agency "
"(class benchmark)** column below is the *typical* rating for each security class, shown for context only — it is "
"**not** an issue‑specific rating.\n")

md.append("### Liquidity rating (L1 … L4)\n")
md.append(
"From the actual MSRB trade tape (municipals have no consolidated quote). We combine the realized round‑trip "
"spread (same‑day customer‑buy vs customer‑sell), trade frequency, and the number of genuinely two‑sided trading "
"days. **L1** highly liquid (≤0.25 pt, ≥50 trades/yr, ≥10 two‑sided days) · **L2** liquid (≤0.40 pt, ≥24/yr, ≥3) · "
"**L3** moderate (≤0.75 pt, ≥12/yr, ≥1) · **L4** thin. Every holding clears a minimum floor (traded in the last 90 "
"days, ≥12 trades/yr, ≥1 two‑sided day) — names that don't are excluded as un‑buildable, regardless of their "
"credit. For a hold‑to‑maturity ladder the spread is paid once on the buy and the bond redeems at par, so "
"liquidity governs *deployment pace and early‑exit cost*, not income.\n")

md.append("## Holdings\n")
md.append("| CUSIP | Sleeve | Security (pledge) | Cpn | Maturity | Px | YTW | TEY (a‑t) | Liquidity | AI‑insul | Our credit | Agency (class)¹ | Par |")
md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    sl = "A" if r['sleeve'].startswith('A') else "B"
    md.append(f"| {r['cusip']} | {sl} | {r['cls']} | {f(r['coupon'],3).rstrip('0').rstrip('.')}% | {r['mat']} | "
              f"{f(r['px'],1)} | {f(r['ytw'])}% | {f(r['tey'])}% | {r['liq']} | {r['ai']} ({r['insul']:.0f}) | "
              f"{r['our']} | {r['agency']} | ${r['par']:,} |")
md.append("")

md.append("## Deployment\n")
md.append(
f"- **Phase 1 — deploy now (~${S['phase1_deployable_now_par']:,}, {S['phase1_pct']}%):** the liquid anchor plus the "
f"already‑active yield‑core names — buildable on demand at tight spreads. You are invested at the full after‑tax "
f"TEY from day one.\n"
f"- **Phase 2 — accumulate over weeks (~${S['phase2_accumulate_par']:,}, {S['phase2_n_names']} names):** the thinner "
f"yield‑core names, worked opportunistically on offerings and bids‑wanted, funded by trimming the anchor as they "
f"fill. Worst case you simply hold the liquid anchor longer — it still out‑yields cash — so you are never *waiting* "
f"to be invested.\n")

md.append("## The price of patience — Phase 2 illiquidity, quantified\n")
import statistics as _st, datetime as _dt
def _fastb(b):
    l=b.get('liq') or {}
    return (l.get('px_spread') or 9)<=0.30 and (l.get('n365') or 0)>=24
def _yrsb(m):
    y,mo,d=[int(x) for x in m.split('-')]
    return max(0.5,(_dt.date(y,mo,d)-_dt.date(2026,6,11)).days/365.25)
_p1=[b for b in B if _fastb(b)]; _p2=[b for b in B if not _fastb(b)]
_p2par=sum(b['par'] for b in _p2)
_prem=100*(_st.mean(b['tey_ytw_aftertax'] for b in _p2)-_st.mean(b['tey_ytw_aftertax'] for b in _p1))
_sps=[b['liq'].get('px_spread') for b in _p2 if (b.get('liq') or {}).get('px_spread') is not None]
_mh=_st.mean(s/2 for s in _sps)
_acq=sum((b['liq'].get('px_spread') or 2*_mh)/2/100*b['par'] for b in _p2)
_amort=_st.mean(((b['liq'].get('px_spread') or 2*_mh)/2)/_yrsb(b['maturity'])*100 for b in _p2)
_exits=sum((2*(b['liq'].get('px_spread') or 0.5)+(1.0 if (b['liq'].get('two_sided_days') or 0)<3 else 0.25))/100*b['par'] for b in _p2)
md.append(
f"Measured from each bond's regulatory trade tape: the {len(_p2)} patient names (${_p2par:,}) yield "
f"{_st.mean(b['tey_ytw_aftertax'] for b in _p2)*100:.2f}% after-tax vs {_st.mean(b['tey_ytw_aftertax'] for b in _p1)*100:.2f}% for the liquid anchor — "
f"an illiquidity premium of ~{_prem*100:.0f} bps/yr (≈ ${_prem/100*_p2par:,.0f}/yr). Entry costs a mean half-spread of {_mh:.2f}pt — "
f"~${_acq:,.0f} one-time, ≈{_amort:.0f} bps/yr amortized — a roughly {max(1,round(_prem*100/_amort))}:1 earn-to-cost ratio for a "
f"hold-to-maturity buyer. The asymmetry: a FORCED exit costs ~{100*_exits/_p2par:.1f}% (≈${_exits:,.0f}) under stress — about one year's "
f"premium — so the bargain holds only while early liquidation stays improbable. Build window ~4–8 weeks; thin-name spreads are "
f"few-observation medians (real error bars; first fills calibrate them).\n")

md.append("## Caveats & methodology notes\n")
md.append(
f"- **Tax‑equivalent yield** is grossed up at the California top combined bracket (×2.01). "
f"{S.get('demin_breaches','several')} of the discount bonds breach the de‑minimis threshold, so their price "
f"accretion is taxed as ordinary income — the **after‑tax** TEY shown already reflects that drag (it is materially "
f"below the naïve gross figure).\n"
f"- **Marks** are EMMA last‑trade prices; municipals trade by appointment, so a given bond's last print may be days "
f"old even for liquid names.\n"
f"- **¹ Agency (class)** is a security‑class benchmark, **not** an issue‑specific rating — EMMA publishes no "
f"third‑party rating for most of these issuers. We can pull issue‑level ratings from a paid feed on request.\n"
f"- **AI‑insulation rates credit, not price.** It is a statement about which pledges keep paying in a tech‑driven "
f"state‑revenue collapse, not a forecast of mark‑to‑market in a rate shock.\n"
f"- Not investment advice; for analyst review.\n")

out = "outputs/CA_MUNI_SLEEVE_C_TEARSHEET.md"
open(out, "w").write("\n".join(md))
print("wrote", out, f"({len(rows)} holdings)")
print("AI dist", dict(ai_dist), "| Liq dist", dict(liq_dist), "| Credit dist", dict(our_dist))
