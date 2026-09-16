"""ai_reference_class — the actuarial outside view (ensemble member 'reference_class').

Member of the 6-model ensemble on the AI-capex credit cycle (frame: desk/models/ai_capex_break.py).
Everything else in the ensemble reasons INSIDE this cycle; this member deliberately refuses
to. It treats the AI buildout as one draw from the reference class "large capex/credit
manias" and asks only: in comparable episodes, how long from the peak of investment-growth
ACCELERATION to the first visible credit event — and where is the AI cycle on that clock?

METHOD: 8 episodes, each dated for (a) peak investment scale (%GDP or best available),
(b) external/vendor-financing intensity, (c) quarters from peak investment-growth-
acceleration to first visible CREDIT event (not equity event), (d) quarters to the equity
trough of the bubble complex, (e) peak-to-trough drawdown. From (c) an empirical CDF —
Kaplan-Meier is overkill at N=8 with no censoring (every episode's clock rang). Dating the
acceleration peak is genuinely fuzzy; each episode carries a [lo, hi] quarter range and the
CDF is computed three ways (lo/mid/hi) so the uncertainty is visible, not laundered.

HEADLINE SHAPE OF THE REFERENCE CLASS: median accel-peak -> first credit event ~5-8 qtrs
(range 1-13 at mid dating). The SHORT tail is telecom 2000 (2-3q) — vendor financing made
the suppliers the credit market, so the first defaults landed while headline capex was
still RISING — and China property (1-2q, policy-triggered). The LONG tail is 1873 and
shale (11-13q), where financing ran through public bond markets with slower feedback.
Equity troughs cluster at 12-15 qtrs from accel-peak in 6 of 8 episodes.

THE PARAMETER: where the AI cycle's acceleration-peak sits is exactly what the ensemble
disputes, so it is a CASE PARAMETER, not a finding:
  CASE A (article's claim)   realized capex growth-acceleration peaked ~mid-2025 -> the
                             clock has run ~4-5 quarters already. Probabilities are
                             CONDITIONAL on having survived those quarters event-free.
  CASE B (mechanism model)   ai_capex_break's measurement rule: realized accel is NOT yet
                             negative (guides still rising) -> clock unstarted; assume it
                             starts ~2026Q4 when the 2026->2027 growth step-down (consensus
                             13-22% vs 50-84%) becomes realized. Unconditional from there.
  BLEND                      50/50 A/B.

CAVEATS PRINTED, NOT HIDDEN: N=8; acceleration-peak dating is judgment (ranges encoded);
the CDF treats episodes as exchangeable draws though financing structures differ; the
covariate block says WHERE in the reference distribution to expect this draw (vendor-
financing HIGH argues short-tail like telecom; fortress core balance sheets argue damped
amplitude, not a longer clock), not a different distribution.

    python3 -m desk.models.ai_reference_class
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

# ── Reference-class table ────────────────────────────────────────────────────
# q_credit / q_trough: quarters from peak investment-growth-ACCELERATION, [lo, hi]
# judgment ranges (dating rationale in accel_dating). drawdown_pct = bubble complex.
EPISODES = [
    {
        "name": "UK railway mania", "years": "1844-1845/47-1849",
        "peak_inv_pct_gdp": 7.5, "scale_metric": "railway capex GBP44M 1847 ~7-8% UK GDP (largest capex/GDP in table)",
        "vendor_fin": "MED", "vendor_fin_note": "no vendor credit; leverage sat in part-paid shares "
            "(10% deposit, calls on demand) — retail shareholders were the levered financiers",
        "q_credit": [4, 8], "q_trough": [12, 17], "drawdown_pct": -63,
        "accel_dating": "accel-peak ~mid-1846 (capex growth steepest 1845->46, authorizations peaked 1846); "
                        "credit event = Oct-1847 commercial crisis (bank failures, Bank Charter Act suspended)",
        "mechanism": "capital calls on part-paid shares collided with the 1847 monetary squeeze; holders "
                     "dumped shares to meet calls; drawdown -60 to -65% (to -85% speculative tail)",
        "source": "Campbell 'Deriving the Railway Mania' (QUB); Odlyzko 'The collapse of the Railway Mania'; "
                  "FocusEconomics railway-mania note",
    },
    {
        "name": "US railroads / Panic of 1873", "years": "1868-1871/72-1877",
        "peak_inv_pct_gdp": 4.5, "scale_metric": "~4-5% GNP (soft), 15-20% of US gross capital formation; "
                                                 "track added peaked 7,379mi 1871",
        "vendor_fin": "HIGH", "vendor_fin_note": "Jay Cooke mass-distributed construction bonds to retail/European "
            "buyers; construction-company self-dealing (Credit Mobilier); bond-financed cash burners",
        "q_credit": [9, 17], "q_trough": [26, 30], "drawdown_pct": -60,
        "accel_dating": "accel-peak ~1870 (mileage growth accelerating 1868-71), fuzzy 1869-1871; "
                        "credit event = Jay Cooke failure 18-Sep-1873 (NYSE closed 10 days)",
        "mechanism": "unsold Northern Pacific bonds stranded on Cooke's book as European demand dried up; "
                     "bank failure -> money-market seizure -> 5yr depression, ~25% of roads in receivership by 1876",
        "source": "Fels 'American Business Cycles 1865-79'; Fishlow railroad-investment estimates",
    },
    {
        "name": "US electricity/utilities 1920s (Insull)", "years": "1922-1929-1932",
        "peak_inv_pct_gdp": 0.9, "scale_metric": "utility construction ~$800-900M/yr 1929-30 ~0.9% GDP — the mania "
                                                 "was the financing pyramid, not the physical build",
        "vendor_fin": "HIGH", "vendor_fin_note": "holding-company pyramids (Insull, Electric Bond & Share) financed "
            "opco capex with holdco debt + retail flotation; 5-10x leverage amplification through the layers",
        "q_credit": [5, 11], "q_trough": [11, 13], "drawdown_pct": -90,
        "accel_dating": "accel-peak ~mid-1929 (construction + holdco flotation still accelerating into the crash); "
                        "credit event = Caldwell/Bank of US failures Nov-Dec-1930 (Oct-1929 was a PRICE event, ~5-6q); "
                        "sector credit event = Middle West Utilities receivership Apr-1932 (~11q, tripped by a $3,000 "
                        "printing bill against $10M of short-term notes)",
        "mechanism": "holdco dividends depended on opco equity distributions; small base-revenue declines "
                     "insolvenced the levered top; short-term notes couldn't roll in 1931-32. Dow -89%, utilities ~-90%",
        "source": "TIME 'After Insull' (1932); American Heritage 'The Fall of Samuel Insull'; EBA 'From Insull to Enron'",
    },
    {
        "name": "Japan land/equity", "years": "1985-1989/91-1992(2003)",
        "peak_inv_pct_gdp": 19.5, "scale_metric": "private nonresidential fixed investment ~19-20% GDP 1990-91 (G7 record)",
        "vendor_fin": "HIGH", "vendor_fin_note": "bank/keiretsu credit against LAND COLLATERAL not cash flow; zaitech "
            "cross-holdings; jusen shadow housing lenders",
        "q_credit": [8, 10], "q_trough": [12, 13], "drawdown_pct": -63,
        "accel_dating": "accel-peak ~mid-1989 (capex growth peaked 1988-90; BoJ hiking from May-1989), fuzzy "
                        "1988H2-1990H1; first VISIBLE credit event 1991 (Toyo Shinkin, first credit-coop failures, "
                        "jusen distress); first true bank failure 1995 (~25q) — forbearance stretched the tape",
        "mechanism": "tightening -> equity crash -> land collateral repriced with 1-2yr lag -> bank capital erosion; "
                     "forbearance converted a crash into a 13yr grind. Nikkei -63% to Aug-92 first trough, -82% ultimate",
        "source": "BoJ/IMF bubble-economy retrospectives; Hoshi-Kashyap banking-crisis chronology",
    },
    {
        "name": "telecom/fiber (KEY ANALOG)", "years": "1996-2000-2002",
        "peak_inv_pct_gdp": 1.2, "scale_metric": "US carrier capex ~$110-120B in 2000 ~1.2% GDP; comms equipment "
                                                 "~7% of total US private investment; >$500B cumulative build",
        "vendor_fin": "HIGH", "vendor_fin_note": "THE canonical vendor-financing episode: Lucent FY2000 $8.1B customer "
            "credit/guarantee commitments (~$2.1B drawn; $2.2B+$1.3B bad-debt provisions 2001-02; Winstar alone $2B "
            "committed, ~$700M written off — Lucent's refusal of a final $90M draw triggered Winstar's filing). "
            "Nortel ~$4.1B undrawn + $1.1B funded end-2000, ~$1.4B provision 2001. Cisco ~$2.4B program. Vendors "
            "booked revenue they were lending into existence; CLECs layered ~$650B HY debt on top",
        "q_credit": [1, 4], "q_trough": [11, 13], "drawdown_pct": -93,
        "accel_dating": "accel-peak ~Q4-1999 +/-2q (growth-RATE peaked ~mid-2000, second derivative rolled late-1999; "
                        "equipment investment LEVEL peaked Q4-2000); first credit event = GST Telecom bankruptcy "
                        "12-May-2000, ICG Sep-Nov-2000 — defaults arrived while headline capex was still RISING; "
                        "cascade NorthPoint Jan-01 -> Winstar Apr-01 -> PSINet Jun-01 -> Global Crossing Jan-02 -> "
                        "WorldCom Jul-02",
        "mechanism": "vendor financing let unfundable CLECs keep buying after capital markets closed mid-2000, making "
                     "vendors the marginal credit providers; when CLECs died the vendors ate the receivables AND lost "
                     "the revenue — demand and credit collapsed as one variable; <5% of fiber lit in 2002. Telecom "
                     "indices -90/-95%; Lucent -99%, Nortel -99.6%, Nasdaq -78%",
        "source": "Lucent FY2000 10-K405 (EDGAR CIK 1006240); Nortel FY2000 filings; Richmond Fed EQ Fall-2003 "
                  "(Wolman) 'Boom and Bust in Telecommunications'; FRBSF 'Boom and Bust in IT Investment'; "
                  "Fabricated Knowledge 'Rise and Fall of the Telecom Bubble'",
    },
    {
        "name": "US housing/structured credit", "years": "2003-2005/06-2009",
        "peak_inv_pct_gdp": 6.7, "scale_metric": "residential investment 6.7% GDP Q4-2005/Q1-2006 (BEA), highest "
                                                 "since early 1950s",
        "vendor_fin": "HIGH", "vendor_fin_note": "originate-to-distribute: warehouse lines -> MBS/CDO -> ABCP/SIV "
            "maturity transformation; the structured-credit buyer financed the origination machine",
        "q_credit": [7, 9], "q_trough": [14, 16], "drawdown_pct": -85,
        "accel_dating": "accel-peak ~Q2-Q3 2005 +/-1q (Case-Shiller HPA y/y peaked ~14.5% mid-2005 then decelerated); "
                        "first credit events = subprime originator failures Dec-2006 (Ownit) - Apr-2007 (New Century) "
                        "~7-8q; systemic freeze BNP 9-Aug-2007 ~9q; Lehman ~13q",
        "mechanism": "HPA DECELERATION (not decline) broke the refi treadmill for 2006-vintage subprime -> "
                     "delinquencies turned mid-2006 -> ABX marks -> ABCP/repo run -> dealer failure. Homebuilders "
                     "~-85%, KBW banks ~-85%, SPX -57%",
        "source": "BEA NIPA 1.1.10; S&P Case-Shiller; FCIC Report (2011) chronology",
    },
    {
        "name": "US shale capex", "years": "2010-2014-2016",
        "peak_inv_pct_gdp": 1.0, "scale_metric": "E&P capex ~$150-200B 2014 ~1.0% GDP; energy ~30% of S&P 500 capex",
        "vendor_fin": "MED", "vendor_fin_note": "HY bonds + reserve-based lending funded structurally negative FCF "
            "(~$200B+ HY energy issuance 2010-14); no vendor financing — service cos got squeezed, didn't lend",
        "q_credit": [8, 14], "q_trough": [14, 15], "drawdown_pct": -79,
        "accel_dating": "accel-peak ~mid-2012 (growth rates peaked 2011-12, decelerating 2013-14 as levels rose), "
                        "fuzzy 2011H2-2013H1; first credit events Q1-2015 (WBH Jan-15, Quicksilver Mar-15; 44 E&P "
                        "filings/$17.4B in 2015); market-freeze = Third Avenue gating + HY rout Dec-2015",
        "mechanism": "price (OPEC Nov-2014) not demand broke it; RBL borrowing-base redeterminations Apr/Oct-2015 "
                     "mechanically pulled credit as reserves repriced; hedges rolling off staged defaults into 2016. "
                     "XOP -79%; HY energy OAS ~1,600bp; 114 bankruptcies/$74B debt 2015-16",
        "source": "Haynes & Boone Oil Patch Bankruptcy Monitor; FRED BAMLHYENER; EIA capex series",
    },
    {
        "name": "China property", "years": "2016-2020/21-2024",
        "peak_inv_pct_gdp": 13.0, "scale_metric": "NBS real-estate development investment ~RMB14.8T 2021 ~13% GDP "
                                                  "(narrow measure; full property complex ~25-29%)",
        "vendor_fin": "HIGH", "vendor_fin_note": "presales = customers prepaid ~50%+ of funding; trust/WMP shadow "
            "credit; unpaid supplier commercial paper = involuntary vendor financing of Evergrande",
        "q_credit": [1, 5], "q_trough": [14, 16], "drawdown_pct": -83,
        "accel_dating": "accel-peak ~Q4-2020 (post-COVID re-acceleration, growth peaked Feb-2021) — policy-set: Three "
                        "Red Lines Aug-2020 capped leverage by fiat; first credit event = China Fortune Land default "
                        "Feb-2021 ~1-2q (fastest in table); Evergrande formal default (Fitch RD) 9-Dec-2021 ~4-5q",
        "mechanism": "regulator cut the funding rope -> presale escrow tightening; presales are confidence-contingent "
                     "so the funding run and the demand collapse were the same event; contagion via supplier paper. "
                     "HS Mainland Properties -80/-85%; Evergrande -99.8% (liquidated Jan-2024)",
        "source": "NBS RE development investment series; NBER w27697 'Peak China Housing' (Rogoff-Yang); "
                  "Fitch/WaPo Evergrande RD 9-Dec-2021",
    },
]

# ── AI-cycle covariates vs the reference median ──────────────────────────────
AI_COVARIATES = {
    "worse_than_median": [
        "vendor-financing intensity HIGH — the telecom tell, and telecom is the SHORT tail of the clock "
        "(2-3q): NVDA equity stakes in customers (OpenAI/CRWV), hyperscaler take-or-pay backlog as loan book, "
        "GPU-collateralized neocloud debt. Vendor financing pulls the credit event EARLIER because suppliers "
        "become the credit market and defaults surface while capex still rises",
        "private-credit share HIGH — GPU ABS/DDTLs and lab funding sit in unmarked private books; opacity "
        "delays VISIBILITY (Japan-style) then gap-reprices; it does not prevent the event",
        "scale: 2026 hyperscaler capex ~$700B ~2.3% US GDP — above telecom's 1.2%, and concentrated in 5 "
        "names + one Ponzi-financed lab layer with a DATED terminal refinance (ai_capex_break refinance wall)",
    ],
    "better_than_median": [
        "corporate balance sheets FORTRESS — MSFT/GOOGL/META run 0.6-0.9 capex/OCF with modest net debt vs "
        "2008 banks at 30:1; the marginal financiers (ORCL, neoclouds, OpenAI) are levered but the core can "
        "absorb writedowns — argues DAMPED AMPLITUDE, not a longer clock",
        "demand is contracted and real (take-or-pay RPO) vs telecom's projected traffic — though the "
        "question is counterparty quality, which loops back to the lab layer",
        "sovereign/strategic backstop plausibility (federal stake, hyperscaler re-wrap of OpenAI) — the "
        "Japan forbearance covariate: stretches the tape between accel-peak and VISIBLE event",
    ],
}

CASES = {
    "A_article_peaked_2025": {
        "accel_peak": dt.date(2025, 6, 15), "conditional": True,
        "why": "article's claim: realized capex growth-acceleration peaked ~mid-2025; we are ~4-5q in, "
               "event-free -> probabilities conditional on survival to date",
    },
    "B_clock_unstarted": {
        "accel_peak": dt.date(2026, 12, 15), "conditional": False,
        "why": "ai_capex_break measurement rule: realized accel not yet negative (guides still rising); "
               "clock assumed to start ~2026Q4 when the consensus 2027 growth step-down becomes realized",
    },
}


# ── survival machinery ───────────────────────────────────────────────────────
def cdf(qs: list[float], q: float) -> float:
    """Empirical P(credit event within q quarters of acceleration peak), with a
    small-sample tail guard: N=8 observed episodes cannot certify certainty, so F is
    capped at n/(n+1) — 'every clock in the class rang by here' reads 0.89, not 1.00."""
    n = len(qs)
    return min(sum(1 for x in qs if x <= q) / n, n / (n + 1))


def q_between(d0: dt.date, d1: dt.date) -> float:
    return (d1.year - d0.year) * 4 + (d1.month - d0.month) / 3.0


def clocks(which: str) -> list[float]:
    """Episode clock lengths under lo/mid/hi dating of each accel peak."""
    out = []
    for e in EPISODES:
        lo, hi = e["q_credit"]
        out.append({"lo": lo, "mid": (lo + hi) / 2, "hi": hi}[which])
    return out


def survival_curve() -> list[dict]:
    qs = clocks("mid")
    return [{"q": q, "P_event_by_q": round(cdf(qs, q), 3)} for q in range(0, 19, 2)]


def case_probs(accel_peak: dt.date, asof: dt.date, conditional: bool) -> dict:
    """P(credit event by end-2027/2028). If the clock started in the past and no event has
    happened, condition on survival-to-date — the actuarially honest read of 'we are ~5q
    in, still quiet'. Dating uncertainty reported as a [min, max] P range over lo/mid/hi."""
    ends = {"2027": dt.date(2027, 12, 31), "2028": dt.date(2028, 12, 31)}
    elapsed = max(0.0, q_between(accel_peak, asof)) if conditional else 0.0
    res = {"elapsed_q_survived": round(elapsed, 1)}
    for tag, end in ends.items():
        q_end = max(0.0, q_between(accel_peak, end))
        per = {}
        for w in ("lo", "mid", "hi"):
            qs = clocks(w)
            F_end, F_now = cdf(qs, q_end), cdf(qs, elapsed)
            per[w] = round((F_end - F_now) / (1 - F_now), 3) if F_now < 1 else 1.0
        res[tag] = {"q_from_accel_peak": round(q_end, 1), "P": per["mid"],
                    "P_dating_range": [min(per.values()), max(per.values())]}
    return res


def state_of(blend27: float, blend28: float) -> tuple[str, str]:
    """Outside-view state map, on the actuarial clock alone: RED = reference class puts a
    credit event more-likely-than-not by end-2027 (or >=75% by 2028); AMBER = 2028 is at
    least a coin flip; GREEN otherwise."""
    if blend27 >= 0.5 or blend28 >= 0.75:
        return "RED", "reference class puts a credit event more-likely-than-not inside the window"
    if blend28 >= 0.4:
        return "AMBER", "base rates make a credit event by end-2028 at least a coin flip"
    return "GREEN", "reference class does not yet put material mass in the window"


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    asof = dt.date.today()
    print(f"=== AI REFERENCE-CLASS MODEL — the actuarial outside view ({asof}) ===\n")
    print(f"-- reference table (N={len(EPISODES)}) --")
    for e in EPISODES:
        lo, hi = e["q_credit"]
        print(f"  {e['name']:40} {e['years']:23} inv {e['peak_inv_pct_gdp']:>4}%GDP  "
              f"fin {e['vendor_fin']:4}  accel->credit {lo}-{hi}q  "
              f"->trough {e['q_trough'][0]}-{e['q_trough'][1]}q  dd {e['drawdown_pct']}%")

    print("\n-- empirical survival curve (mid dating): P(first credit event by q quarters) --")
    for r in survival_curve():
        bar = "#" * int(r["P_event_by_q"] * 40)
        print(f"  q={r['q']:>2}  {r['P_event_by_q']:.3f}  {bar}")
    mids = sorted(clocks("mid"))
    med = (mids[3] + mids[4]) / 2
    print(f"  median clock ~{med:.0f}q (mid dating); short tail = telecom/China (vendor/policy-financed), "
          f"long tail = 1873/shale (public-bond-financed)")

    results = {}
    for name, c in CASES.items():
        r = case_probs(c["accel_peak"], asof, c["conditional"])
        results[name] = r
        cond = (f"conditional on {r['elapsed_q_survived']}q survived" if c["conditional"]
                else "unconditional, clock starts at accel-peak")
        print(f"\n-- CASE {name} (accel-peak {c['accel_peak']}, {cond}) --")
        print(f"   {c['why']}")
        for tag in ("2027", "2028"):
            x = r[tag]
            print(f"   P(credit event by end-{tag}) = {x['P']:.2f}  "
                  f"(dating range {x['P_dating_range'][0]:.2f}-{x['P_dating_range'][1]:.2f}, "
                  f"{x['q_from_accel_peak']}q from accel-peak)")

    blend27 = round((results["A_article_peaked_2025"]["2027"]["P"] +
                     results["B_clock_unstarted"]["2027"]["P"]) / 2, 3)
    blend28 = round((results["A_article_peaked_2025"]["2028"]["P"] +
                     results["B_clock_unstarted"]["2028"]["P"]) / 2, 3)
    print(f"\n-- BLEND 50/50: P(by end-2027) = {blend27:.2f}   P(by end-2028) = {blend28:.2f} --")

    state, why = state_of(blend27, blend28)
    print(f"\n-- STATE: {state} ({why}) --")

    print("\n-- covariates vs reference median --")
    print("  WORSE:")
    for c in AI_COVARIATES["worse_than_median"]:
        print(f"   - {c}")
    print("  BETTER:")
    for c in AI_COVARIATES["better_than_median"]:
        print(f"   - {c}")

    out = {
        "member": "reference_class",
        "asof": asof.isoformat(),
        "state": state,
        "reading": {
            "n_episodes": len(EPISODES),
            "episodes": EPISODES,
            "survival_curve_mid_dating": survival_curve(),
            "median_clock_q": [mids[3], mids[4]],
            "cases": {name: {**results[name], "accel_peak": CASES[name]["accel_peak"].isoformat(),
                             "why": CASES[name]["why"]} for name in CASES},
            "covariates": AI_COVARIATES,
            "state_why": why,
        },
        "P_break_by_2027": blend27,
        "P_break_by_2028": blend28,
        "notes": [
            "P_break = 50/50 blend of Case A (accel peaked mid-2025, conditional on ~4.5q survived "
            "event-free) and Case B (clock unstarted, starts 2026Q4). Case-level numbers in reading.cases.",
            "Credit event = first visible default/failure/freeze in the complex, matching ai_capex_break's "
            "break definition — NOT an equity drawdown.",
            "N=8, no censoring; accel-peak dating is judgment — lo/mid/hi CDFs encoded, headline uses mid. "
            "Empirical CDF capped at n/(n+1)=0.889 so the small sample never certifies certainty.",
            "Covariate read: vendor-financing HIGH argues the telecom SHORT tail; fortress core balance "
            "sheets argue damped amplitude, not a longer clock; backstop plausibility argues Japan-style "
            "visibility delay.",
            "Equity-trough cluster 12-15q from accel-peak (6 of 8 episodes) — sizes the drawdown window "
            "even where the credit-event call comes early.",
        ],
    }
    path = Path(__file__).resolve().parents[1] / "data" / "ai_ensemble" / "reference_class.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
