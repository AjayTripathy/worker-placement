# Value-Detector Book (standalone) — small-cap-value rotation thesis

*2026-06-27. ONLY the deep-value detector output — beauty/aesthetics/wellness sleeves stripped out. This is the intentional bet: in a small-cap rotation the edge is EXCLUSION (the screen-cheapest are traps), so own the cheap-AND-quality-AND-trap-filtered survivors. READ-ONLY, no orders.*

## Method (how these 7 were selected)
1. **Universe:** micro/small-cap ex-financials (Nasdaq screener), US-listed only (ADRs/FPIs dropped via 20-F/6-K test).
2. **Fundamentals:** whole-universe TTM cross-section from SEC XBRL frames API (rolling TTM = CY2025 annual − CY2025Q1 + CY2026Q1). Debt tags broadened after the COLL miss (convertibles + custom term-loans → bias to over-state leverage).
3. **Cheapness:** EV/EBIT, FCF-yield, P/B, net-cash, NCAV.
4. **Quality overlay (Greenblatt + guards):** reject stale (no fresh quarter), burning/neg-equity, EBIT collapsing >20% YoY (GIII stale-peak guard), latest-QUARTER EBIT negative or down >15% YoY (UPWK/VITL/PSIX recent-inflection guard), net-debt/EBIT >3.5x (UPBD hidden-leverage), ROIC <10%, earn-yield <8%. Then Magic-Formula rank. Pending-merger names gated out (CPRX — a stock at its deal price is a merger claim, not value).
5. **R/f(M) trap-filter:** per-name recompute from the latest 10-Q. **16 candidates trap-filtered → these 7 survive.**

### Gate fix (2026-06-27) — one-time-gain normalization
The prior skeptic found the inflection guard read *reported* quarterly EBIT, so a one-time gain inflated it (the BKE $19.1M litigation-settlement case: reported +37% growth was really −7%). Fixed:
- **Strip discrete one-time gains** (litigation settlement / asset & business disposition / bargain purchase / unusual-infrequent / other-nonrecurring, summed from XBRL) from BOTH comparison quarters before the inflection + earn-yield gates.
- **Run-rate-spike backstop** for *untagged* one-timers: reject when a quarter prints >2.2× the TTM/4 run-rate (unverifiable spike → DD); flag 1.6–2.2× as `ebit_quality: needs-DD`.
- **`ebit_quality` is now emitted on every name** — the screen no longer silently labels a name "clean."
- **Validated:** a synthetic BKE-class name (reported +36.5% → adjusted −7.3%, one-time = 32% of EBIT) is now correctly *rejected* ("EBIT inflated by one-time gain — needs DD"); clean controls and a 5%-one-time control pass without false flags. Re-run added two reject buckets (`adj`: 104 names, `Q`-spike: 31). None of the 7 survivors flag.
- **HONEST LIMITATION:** XBRL one-time-gain recall is partial (many filers bury settlements in SG&A untagged) and the fix only sees items *inside* OperatingIncomeLoss — a below-the-line MTM gain (e.g. INVA's equity-stake mark) won't trip it. Per-name DD remains the final backstop; the symmetric-DD pass below is that backstop applied evenly.

### Gate fix v2 (2026-06-27, after 2nd skeptic pass) — the v1 fix did NOT catch the real BKE
The 2nd skeptic verified (and so did I, against EDGAR CIK 885245) that v1 was **security theater for its own namesake case**: BKE *is* in the CY2026Q1 frames cross-section (EBIT $59.5M vs $43.5M = +36.5%) but reports **none** of the 7 strip-tags (settlement untagged in SG&A) → `one_time_pct=0`, strip is a no-op; the run-rate backstop misses it (seasonally-soft Q1 = 0.86× run-rate, below the 1.6× trigger); and the inflection guard only rejects *negative* YoY, so a fake **+36.5%** passed as "clean." Measured strip-tag recall is only **~9% of the universe** (361/3,965 filers; 2 of the 7 tags are dead universe-wide).
- **Root cause:** the gate only hunted EBIT *collapses*, never implausible *positive* jumps — which is the shape of a one-time gain.
- **v2 fix:** you cannot tell an untagged operating one-timer from real growth via frames, so don't *reject* a positive jump (that would nuke genuine growth like NUTX +111%). Instead **refuse to certify it**: any quarter with **>30% YoY EBIT jump downgrades `ebit_quality` to `needs-DD`, never "clean."** Validated on BKE's REAL numbers → now reads `"+37% YoY Q-EBIT jump — one-time vs growth UNVERIFIED, needs-DD"`; a stable +5% control stays `clean`.
- **What this means for the book (the skeptic's deepest point, now structural not cosmetic):** "no flag" was near-uninformative at 9% recall. Under v2, **`ebit_quality: clean` now actually means something** (no large unexplained inflection), and several names with big jumps (incl. EVER's +132% trough-base) now correctly read `needs-DD` — which their per-name DDs then clear or fail. The screen no longer over-certifies; the DD carries the one-timer axis explicitly, by design.

**Traps killed (did NOT survive):** GIII (stale-peak EBIT), UPBD (hidden lease leverage), SIGA (peak-gov lumpiness), CRMD (reimbursement cliff), YELP/PSIX (recent-quarter inflection), COLL ($803M debt mislabeled net-cash → really 6.1x net-debt), UPWK/VITL (fresh-quarter EBIT collapse), IDT/CCSI (fair, not cheap), EZPW (already re-rated), CPRX (merger-arb at deal price).

## The 7 survivors (live 2026-06-27)
| Name | Live | Zone | Conv | FV bear/base/bull | EV/EBIT | Thesis (1-line) | The honest catch |
|---|---|---|---|---|---|---|---|
| **GCT** | $32.03 | WATCH (entry $32–25) | HIGH | $24 / $43 / $60 | 5.1x | net-cash (31% of mcap, 97% US) B2B furniture distributor+3PL mis-priced as China-fraud; KPMG-audited, no-VIE; SCOTUS struck IEEPA Feb-26 | it's a **1P-distributor (29.8% GM), NOT the asset-light marketplace** bulls sell; controlled-co (Wu 70.7% vote); undisclosed China-origin GMV → tariff bear unsizable |
| **DFIN** | $40.55 | **ENTRY ($42–36)** | HIGH | $45 / $56 / $60 | 8.6x | compliance-software transition compounder mis-priced as dying-print; SW 47% rev/45% profit, +21% EBITDA; EBIT GROWS on declining rev | the scary GAAP net-income drop was a 1-time non-cash pension settlement; catalyst (IPO/M&A recovery) = the small-cap/risk-on factor itself |
| **EVER** | $23.20 | WATCH (entry $23–18) | MED (half) | $25 / $38 / $41 | — | online insurance lead-gen; cyclical-peak REFUTED — Q1 RECORD op-income + 12.3% margin; net cash $178M, zero debt | **ONE carrier = 40% of revenue, ~90% auto** = hard concentration cap → half-size |
| **EPAM** | $80.68 | WATCH (entry $80–70) | MED (starter) | $65 / $115 / $131 | 6.2x | premium digital-engineering at 6.2x, net cash ~$17/sh, de-rated −60% on AI-disruption fears; India now #1 delivery; AI net-positive so far | organic growth low-single-digit + guide LOWERED; **AI-disruption secular question genuinely unverifiable** = starter only |
| **SBH** | $14.46 | **ENTRY ($15–12)** | MED-LOW | $16 / $20 / $22 | — | Sally Beauty + CosmoProf pro-distribution; 'dying retail' REFUTED — comps +1.3%, traffic up; net debt 1.7x & falling | return = re-rate + ~6%/yr buyback + de-lever, **NOT organic growth** |
| **BKE** | $43.24 | WATCH (entry $43–38) | LOW (income) | $40 / $49 / $52 | 6.8–7.3x | net-cash ($5.73/sh) 33%-ROIC mall apparel; MELT thesis REFUTED — comps +5.1%, transactions +2.6% | the **+37% EBIT was a 1-time $19.1M litigation settlement** → underlying EBIT DECLINED YoY; own the cash-return, not growth |
| **CRCT** | $4.63 | WATCH (entry $4.40–4.10) | LOW (income, thin) | $3.22 / $5.20 / $7.72 | — | 89%-GM Cricut Access subscription annuity in a declining-hardware shell | annuity GROWING but **MATURING** (penetration ~92%, first sequential sub-decline); Class-B 5-vote → 93% controlled = **lowball take-under risk** |

Rank by conviction: **GCT > DFIN > EVER(half) > EPAM(starter) > SBH > BKE > CRCT.** Thin names (CRCT/SBH/EVER) = use limits.

## What this book is / isn't
- **IS:** a US-listed, sector-diversified-ish, cheap-and-quality long book sized to a small-cap *value-rotation* thesis, with per-name kill-triggers.
- **ISN'T:** proven to have basket-alpha. Prior small-cap honesty work showed recall (exclusion) is durable but basket-alpha fails placebo. The claim here is narrower: *avoid the value traps the screen surfaces*, not *this 7-pack beats the Russell value index*.
- **Open risks (self-flagged):** still mostly consumer-discretionary by GICS (GCT/SBH/BKE/CRCT/EVER all consumer-ish); shares small-cap/liquidity beta with the whole rotation; DFIN's catalyst IS the macro factor; 3 names controlled-co (GCT/CRCT take-under risk); EVER 40% customer concentration; EPAM AI-disruption unverifiable.

## Screened diversifiers (symmetric DD, 2026-06-27) — half were traps
The skeptic flagged that the consumer-skew names got DD but the non-consumer survivors didn't. Applying the *same* R/f(M) trap-filter to the four it named:
| Name | Sector | Verdict | Finding | Action |
|---|---|---|---|---|
| **REPX** | Energy (Permian) | ✅ **REAL-VALUE but re-rated** | −17% EBIT is *price not roll-over* (WTI deck −14%, production +8%); Silverback was an in-basin bolt-on (not a leverage-up Eagle Ford entry); FV bear $22 / base $40 / bull $55; maint-capex-adj FCF ~12% of equity, div covered 3.5×; borrowing base *raised* $400→425M. **CORRECTION: IBKR live $34.07, +31% YTD** — the trap-filter mis-stated spot as ~$22; at $34 base FV is only **~+17%** (not +75%), and it's *already re-rated* | **WATCH (half-size, energy diversifier)** — entry $30–26, accumulate on a pullback to high-$20s; NOT an add at $34 |
| **SD** | Energy (Mid-Con) | ⚠️ **WAIT** | honest reinvest-and-grow (reserves grew, not liquidating), but 17% earn-yield is NOL-flattered + oil-rich; true post-capex FCF yield ~7%; FV base ≈ spot, no margin of safety; the $4.72 special-div era is over (~5.3% ordinary now) | **WATCH** — buy only on a gas dislocation to $10–11 |
| **WLKP** | Industrials (chem MLP) | ❌ **TRAP** | 2.1x EV/EBIT is an MLP look-through artifact — WLKP owns 22.8% of OpCo but consolidates 100% of EBIT over a 22.8%-economic mcap; true EV/EBIT 5.3x consolidated / ~15.5x look-through, earn-yield 6.1%; parent-set transfer price resetting 2026; take-under risk | **KILL** (bond-proxy, not value) |
| **INVA** | Healthcare (royalty) | ❌ **TRAP** | 60% of EPS is non-cash MTM gain on one biotech stake (Armata); operating profit = a *melting* GSK royalty (−2% → −11.5% YoY) subsidizing a ~$73M/yr opco drain; statutory IRA price cut on BREO/RELVAR Jan-2027; FV base ~$19–20 < $23.6 spot | **KILL** (declining annuity + one-time-gain optics) |

**Net:** symmetric DD qualified **REPX** (real energy diversifier — but already +31% YTD, so WATCH-not-add at $34) and benched **SD** as a watch-lower; killed **WLKP/INVA**. The 50% trap rate on the "unscreened" names confirms the skeptic's structural point — and that the fix is to DD evenly, not to lower the bar. Per-name files: `REPX_trap.md`, `SD_trap.md`, `WLKP_trap.md`, `INVA_trap.md`.

## The honest book after the gate fix + symmetric DD
**7 buyable-on-band + 2 energy WATCH:** GCT, DFIN, EVER(half), EPAM(starter), SBH, BKE(income), CRCT(income, thin) — plus **REPX(half, energy, WATCH high-$20s)** and **SD** on the watch-lower bench. REPX is the first genuine non-consumer leg but it's already re-rated, so it's a pullback-watch not an add. Still pending the prior skeptic's portfolio-layer point: this is cheap-cyclical *selection*, not a proven-alpha basket; size at the factor level.
