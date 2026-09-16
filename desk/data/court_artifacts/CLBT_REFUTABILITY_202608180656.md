## EVIDENCE PACK — CLBT — REFUTABILITY TRIAGE OUTPUT

**Cause-check first (required before refutability): this is a PRINT + NEWS event, not beta.** CLBT reported Q2'26 pre-market Thursday 2026-08-13 and closed -29.18% at $10.80 that session (the cohort record dates the move 08-14; the tape event is the 08-13 session — one-day offset in the event record). Same tape: an ARR miss vs the company's own guide, a full-year ARR/revenue guide-down, and a same-day CEO replacement. The cohort is degenerate — MEMBERS TO TRIAGE lists only CLBT, and `knowledge_graph/cohorts.json` was permission-denied to me, so the "dispersion vs cohort median" comparison specified by R2.3 **cannot be computed**; what follows is dispersion vs the company's own guidance arithmetic instead, and that substitution is disclosed, not hidden.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| CLBT | DAMAGE-ABSENT | (1) Dollar-based net retention rate; (2) implied H2'26 net-new ARR bar vs H2'25 actual | (1) **NRR 117%, UP 2pts from 115% in Q1'26** ([Q1 PR: 115%](https://www.prnewswire.com/news-releases/cellebrite-announces-first-quarter-2026-results-302772161.html); [Q2 6-K: 117%](https://www.sec.gov/Archives/edgar/data/1854587/000121390026089065/)). Gross retention "up several points" on Inseyets; CRO: "no deals are lost." (2) **Reset guide requires LESS absolute net-new ARR in H2'26 than the company actually added in H2'25** — see reconstruction below. | **~2026-11-11 (yfinance-derived) / 2026-11-18 (broker calendar) — UNCONFIRMED; no company PR names it yet** | The narrative sold was demand destruction/competitive displacement. That is testably absent: retention rose, net-new ARR in the "miss" quarter ($14.8M) EXCEEDED the year-ago quarter ($12.3M), defense/intel ARR +25%, and adj-EBITDA guidance was **raised**. What IS real is a separate, smaller narrative — a growth-algorithm step-down from 18–19% to 14–16% ARR growth — plus unresolved guidance credibility under a day-one CEO. Split disclosed rather than laundered into one label. |

### The arithmetic the tape ignored

Guidance, midpoint to midpoint (Q1 PR 2026-05-14 → Q2 6-K 2026-08-13):

| FY26 guide | prior | new | delta |
|---|---|---|---|
| ARR | $567–573M (18–19% gr) | $550–560M (14–16% gr) | **−$15.0M = −2.63%** |
| Revenue | $565–571M | $555–561M | −$10.0M = −1.76% |
| Adj. EBITDA | $149–155M | $153–159M | **+$4.0M = +2.63% (RAISED both ends)** |

Q2 itself: ARR guided $510–513M, delivered **$507.8M** — a **0.4%–1.0% miss**. Revenue guided $130–133M, delivered **$131.1M — inside the range**. Adj. EBITDA guided $29–31M, delivered $31.8M — **above the range**.

**Price move ÷ guidance cut = 29.18% ÷ 2.63% ≈ 11.1x.** That ratio is the entire trade question.

**H2 net-new ARR reconstruction (fully public, pre-print derivable):**
- FY25 exit ARR backs out of the new guide's own growth rates: $550/1.14 = $482.5M; $560/1.16 = $482.8M → **base ≈ $482.6M** *(derived from guidance percentages, not directly disclosed — a court must confirm against the 20-F)*.
- Q4'25 $482.6M → Q1'26 $493.0M (+$10.4M) → Q2'26 $507.8M (+$14.8M). **H1'26 net-new = +$25.2M.**
- New FY26 guide therefore requires **H2'26 net-new of $42.2M–$52.2M**.
- H2'25 actual net-new: Q2'25 $419.7M (from $507.8M at +21%) → Q4'25 $482.6M = **+$62.9M**.

**The reset bar is 67%–83% of last year's H2 net-new dollars, off a 21%-larger installed base.** The *old* guide required $59.2–65.2M, i.e. 94–104% of H2'25 — a repeat performance. The cut moved the bar from "match last year" to "do two-thirds of it." That is the signature of a new CEO's first, deliberately beatable guide, and it is the single most decision-relevant fact on the name — it is not in any of the sell-side or newswire coverage I read.

### What survives as genuinely adverse (not laundered)

- **Growth step-down is real.** 18–19% → 14–16% ARR growth is a permanent-until-disproven change in the algorithm for a name that carried a growth multiple. Multiple compression of *some* size is correct.
- **Federal FEP friction is procedural, not one-time.** A Foreign Entity Permit requirement adds "four to five weeks" to U.S. federal cloud cycles; European FOI-compliance rules delayed four cloud migrations. Timing tax, but a recurring one.
- **Integrity overhang exists but does not yet meet the RP_TAINTED bar.** Kaplan Fox, Levi & Korsinsky and SueWallSt have all opened §10(b) solicitations off the same-day miss-plus-CEO-exit fact pattern. These are law-firm press releases, not filed complaints. **Anti-masking finding, and it cuts the bull's way:** the Form 144s dated 08-07 and 08-11 (days pre-print) sit inside an already-established cadence — 144s were also filed 06-30, 07-01, and 07-06 ×2 — so the insider-sale timing looks like a running 10b5-1 program, not opportunistic pre-announcement selling. A court should confirm plan-adoption dates from the 144 face pages before either side uses this.
- **Valuation is stated on market cap, not EV, deliberately.** At $10.44 / $2.694B: 4.83x FY26E revenue, 17.3x FY26E adj. EBITDA, 18.7x TTM FCF ($144.2M, 28.0% margin). Cash & equivalents are $141.3M; **total cash + short-term investments is NOT verified in this pack**, so true EV multiples are lower by an unquantified amount. Per cap-structure doctrine, no EV multiple may be asserted until the Q2 balance sheet is pulled.
- **No dead-cat bounce.** The tape has drifted a further ~3.3% below the 08-13 close of $10.80 to $10.44, sitting 9% off the 52-week low and −47.7% from the $19.98 high. The market has not started re-rating this back.

### Prior that argues against me, stated up front

The desk's earnings-dislocation template graded **0-for-7** on exactly this shape, under the rule "the headline IS the news." That prior is the strongest single argument for scoring this low. What distinguishes CLBT from the graded cohort is that the refuting metric here moved in the *opposite* direction from the narrative (NRR up, not merely "less bad"), and the reset bar is arithmetically below prior-year seasonality. That is a testable difference, not a rationalization — and it is precisely what a court exists to break.

**COURT-WORTHY (damage-absent, ranked):**
1. **CLBT** — an 11.1x price-move-to-guidance-cut ratio, against a retention metric that *rose* and an EBITDA guide that was *raised*, with a reset H2 bar demanding only two-thirds of last year's net-new ARR; the entire bear case reduces to whether 14–16% is the new structural rate or a sandbagged floor, and that is a question a red/blue bench can actually resolve from public filings before Q3.

**COURT-WORTHINESS CLBT: 7/10** — a court flips the sizing decision between FLAT and a real starter, because the decisive question (structural deceleration vs. beatable day-one reset) is resolvable from public disclosure and the 0-for-7 earnings-dislocation prior deserves an adversarial test rather than an automatic veto.

**PRINT PROXIMITY: NONE within 5 trading days — next print ~2026-11-11 (yfinance-derived) to 2026-11-18 (broker calendar), ~60 trading days out; UNCONFIRMED, no company PR names the date, and Cellebrite's practice is to announce it ~2–3 weeks prior (the Q2 date was announced by PR on 2026-07-2x for 08-13).** The print-decisive reconstruction is therefore not mandatory here, but I ran it anyway above (H2 net-new ARR bar) because it is the reconstruction that will decide the Q3 print, and it is available now rather than in November.

**PRE-PRINT POSITION: STARTER** — the refuting metric (NRR 115→117) and the sub-seasonal H2 bar justify establishing a position now rather than waiting for Q3 confirmation, but sized as a starter only, because the growth step-down is genuinely unresolved, the securities-investigation overhang is unadjudicated, and no EV multiple can be asserted until the balance sheet is pulled.

**Verification path, disclosed:** `sec.gov/Archives` returned HTTP 403 to every direct fetch attempt in this session, so the 6-K contents were verified through the issuer's own PR Newswire distribution and a filing mirror rather than read off EDGAR directly. Accession numbers are cited from the machine-built pack. A court should re-pull 0001213900-26-089065 and 0001213900-26-089232 with a full browser fingerprint before relying on any figure above.

Sources: [Q1'26 results / prior guidance (PR Newswire, issuer distribution)](https://www.prnewswire.com/news-releases/cellebrite-announces-first-quarter-2026-results-302772161.html) · [Q2'26 6-K, new guidance (SEC accession 0001213900-26-089065)](https://www.sec.gov/Archives/edgar/data/1854587/000121390026089065/) · [Q2'26 6-K mirror with figures](https://www.stocktitan.net/sec-filings/CLBT/6-k-cellebrite-di-ltd-current-report-foreign-issuer-2fee840b5c69.html) · [Q2'26 earnings call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-cellebrite-cuts-outlook-in-q2-2026-despite-eps-beat-93CH-4858388) · [CEO succession PR](https://www.prnewswire.com/news-releases/cellebrite-appoints-shiven-ramji-chief-executive-officer-succeeding-thomas-e-hogan-302850249.html) · [Tape / -29.18% session](https://www.theglobeandmail.com/investing/markets/markets-news/motley/3839911/stock-market-today-aug-13-cellebrite-shares-plummet-29-after-missing-earnings-cutting-2026-revenue-guidance/) · [Securities investigation notice](http://www.prnewswire.com/news-releases/cellebrite-di-investigation-notice-levi--korsinsky-notifies-investors-of-pending-investigation-into-cellebrite-di-clbt-302851437.html) · [Guidance vs FactSet consensus](https://www.marketscreener.com/news/clbt-cellebrite-di-expects-2026-revenue-range-555m-561m-vs-factset-est-of-568m-ce7859d9dc81f620)