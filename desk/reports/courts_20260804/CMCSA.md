# CMCSA — Comcast Corporation, Class A (NASDAQ: CMCSA)
**Court: COURT_QUEUE_20260804, tier 1. Sat 2026-08-03 (US evening), grading for the 08-04 session.**
Queue entry: score 75.7, cap $87,155M, "-40% from own 3y high, gm 69%, rev3y 0.6%", ai_complex: false.
Prior art: none in `research_ledger.json` or `resolution_packs.json`. Cross-reference: **VSNT**, the January
2026 spin-off from this parent, sits in TIER_4 of the same queue tagged FORCED_SELL_DOWNGRADE.

**VERDICT: REJECT 3/10.** This is a derailment, not a de-rate. The screen's frame is misapplied.

---

## 0. THE PARENT LANE'S HYPOTHESIS, ANSWERED FIRST

The lane brief asked me to tape-verify the −40% on a spin-adjusted basis, on the theory that the screen may
be measuring pre-spin against post-spin prices naively — the ADIG-class error — and to raise a **P1 generator
defect** if the premise breaks.

**The premise does NOT break. There is no naive spin error, and the direction of any residual error is
conservative, not inflationary.** Full working in section 1. That is a negative finding, and it retires the
concern for the whole spinoff-adjacent cohort rather than just this name.

There is a separate, smaller measurement defect I did find (a total-return vs price basis mismatch), plus one
structural gap in the generator that matters much more than either. Both are in section 11.

---

## 1. PRICE PREMISE — TAPE-VERIFIED, AND THE SPIN QUESTION SETTLED

### 1a. The tape

| Fact | Value | Source / basis |
|---|---|---|
| Live price | **$24.56** | IBKR contract 267748, 2026-08-03 session close (weekly bar O 24.45 / H 24.90 / L 24.39 / C 24.56); after-hours print 24.58 |
| 3-year high, total-return basis | **$39.75 on 2024-02-01** | yfinance `history(period="3y")` — the generator's own call |
| 3-year high, price basis | **$44.16 on 2023-08-30** | yfinance `auto_adjust=False` Close |
| 3-year low | **$21.92 close on 2026-07-23** ($21.28 intraday 07-24) | yfinance daily; IBKR daily confirms |
| Drawdown, total-return basis | **−38.2%** at $24.56 | computed (the screen's −40% used the 07-31 close of $23.96) |
| Drawdown, price basis | **−44.4%** | computed |
| Off the 3y low | **+12.0%** (+15.4% off the intraday low) | computed |
| Days since the 3y low | **10** | computed |
| Dividend yield | **5.42%** | IBKR dividend-yield field; $0.33/quarter confirmed in the IBKR corporate-actions feed |

**A live-quote trap worth recording:** the IBKR snapshot for contract 267748 returned `last: 245.80` and
`priorClose: 245.60` — a **10x price-magnifier artifact** — while the same response's `misc-statistics`
carried a 52-week range of 21.28–32.4775 in true dollars. The dividend-yield field (5.42% against a known
$1.32 annual dividend) and the daily/weekly bars both resolve it to **$24.56–24.58**. This is the same class
of unit failure as the POLI.TA agorot-vs-shekel incident. **Never take a bare `last` from a snapshot as the
price premise.**

### 1b. Is the price series spin-adjusted? YES — verified from primary sources, not inferred.

The chain:

1. **Distribution terms, from the primary filing.** Versant Media Group 10-Q for Q1-2026 (CIK 0002067876,
   accession 0002067876-26-000027), **Note 7, Stockholders' Equity**, verbatim: *"The Separation from Comcast
   was completed on January 2, 2026 through the distribution of 100% of the shares of Versant Class A common
   stock … as of the close of business on the record date of December 16, 2025. Comcast's shareholders of
   record received **one share of Versant Class A common stock … for every 25 shares of Comcast Class A
   common stock**."*
2. **Value distributed.** VSNT's first regular-way close was ≈ **$46.63** (2026-01-02; it fell 13.0% to $40.57
   on 01-05). At 1:25 that is **$1.87 of value per CMCSA share.**
3. **Implied adjustment factor.** CMCSA's pre-spin close on 2025-12-31, unadjusted, would be
   $28.01 + $1.87 = **$29.88**. The back-adjustment factor is 28.01 / 29.88 = **0.9374**.
4. **Independent confirmation from the vendor series.** IBKR's own pre-2026-01-02 daily bars carry a
   **constant** non-round scaling that solves to **0.93678** — matching the filing-derived 0.9374 to within
   0.06%, and constant across ex-dividend dates (so it is a spin factor, not a dividend factor). Yahoo's raw
   `Close` series shows **no ex-date gap whatsoever** across 2025-12-31 → 2026-01-02 (28.01 → 27.69, −1.2%,
   an ordinary market day), which is only possible if the spin factor is already baked in.
5. **Both vendors agree on the pre-spin level.** IBKR $28.001 vs Yahoo raw $28.013 on 2025-12-31; IBKR $30.455
   vs Yahoo raw $30.469 on 2025-08-05. Same series, same adjustment.

**Conclusion — CONFIRMED:** the generator's price source (`yf.Ticker(tk).history(period="3y")["Close"]`)
is spin-adjusted for Versant. The −40% is **not** a pre/post-spin artifact.

**And the error direction is the opposite of the one feared.** If the series had been left *unadjusted*, the
pre-spin prices would be **higher** by 6.3%, so the naive drawdown would read **deeper** (roughly −44% rather
than −40%). A naive screen would have over-selected this name, not under-selected it. **The spin is worth
6.3% of CMCSA — the drawdown qualifies for the 35–78% band on any of the three bases.** No P1 defect here.

### 1c. Path test — FAILS on substance even though it passes the numeric guard

+12.0% off a **10-day-old** low technically clears every threshold in the generator. But the number is
misleading. The low of $21.92 (2026-07-23) is the Q2 earnings-day close, the $21.28 intraday low was the
following session, and the +15.4% bounce since is not dip-buying — it is the market repricing the **June 29
breakup announcement** and the Q2 confirmation of it. **We are late to the capitulation and early to a
12-month corporate reorganisation.** That is the worst intersection of the two, and the numeric path guard
cannot see it. See section 11.

---

## 2. CAUSE-CHECK — WHY THE −40%

| Date | Move | Cause | Evidence status |
|---|---|---|---|
| 2024-02-01 → 2026-04-22 | $39.75 → $29.37 total-return basis | The long structural cable de-rate: broadband subscriber growth going to zero, then negative | CONFIRMED |
| **2026-04-23** | **+7.7%** to $31.64 on 46.5M shares | **Q1-2026 print.** 8-K 2026-04-23, item 2.02. The market bought "the pivot is working": broadband net losses improved **117,000** y/y to just −65,000, record wireless adds, Theme Parks EBITDA **+33%**, Peacock revenue **+71%** past $2bn. It bought this *despite* adjusted EPS **−27.5%**, adjusted EBITDA **−16.8%** and FCF **−28.0%** in the same release | CONFIRMED |
| **2026-04-24** | **−12.9%** to $27.56 on 65.5M shares | **Sector, not company.** Charter reported Q1 broadband subscriber losses and had its worst trading day on record. Headlines that day: Deadline, *"Charter Shares Plummet After Broadband Losses And Q1 Earnings Disappoint Wall Street"*; Barron's, *"Is the Cable Era Over? Charter's Subscriber Slump Reignites Fears of a Fiber and Satellite Threat"*; MarketWatch, *"Charter's stock just got hammered — its worst day on record"*; Seeking Alpha, *"…dragging down sector peers."* No CMCSA 8-K on 04-24 (only the DEF 14A) | CONFIRMED — the largest single down-day in the series is an exogenous sector repricing |
| **2026-06-29** | **+4.5%** to $24.22 | **Comcast announced the breakup.** 8-K 2026-06-29, Ex-99.1: intention to separate into two public companies via a tax-free spin-off of NBCUniversal and Sky, ~one year out; **share repurchase programme PAUSED** | CONFIRMED |
| **2026-07-23** | **−6.8%** to $21.92 — the 3-year low | **Q2-2026 print.** 8-K 2026-07-23, item 2.02 | CONFIRMED |
| **2026-07-28** | **+6.1%** to $24.19 | Breakup/sum-of-the-parts re-rating; institutional accumulation (BofA bought 3.78M shares 07-30/31) | PLAUSIBLE |
| 2026-08-03 | +2.5% to $24.56 | Universal's £6bn UK resort announcement | PLAUSIBLE |

**Cause-check verdict: READ.** The −40% is the structural cable de-rate, punctuated by a peer's collapse and
by Comcast's own decision to break itself up.

---

## 3. THE DECISIVE NUMBER — DOMESTIC BROADBAND REVENUE IS DOWN 5.5%

From the 8-K 2026-07-23, Ex-99.1, Residential Connectivity & Platforms revenue table:

| Line | Q2-2026 | Q2-2025 | Change |
|---|---|---|---|
| **Domestic Broadband** | **$6,280M** | $6,649M | **−5.5%** |
| Domestic Wireless Service | $1,007M | $882M | +14.2% |
| **Domestic Convergence (broadband + wireless service)** | **$7,287M** | $7,530M | **−3.2%** |
| Video | $6,092M | $6,605M | −7.8% |
| Total Residential C&P revenue | **$17,124M** | $17,839M | **−4.0%** |
| Total Residential C&P Adjusted EBITDA | **$6,448M** | $7,006M | **−8.0%** |
| Residential C&P Adjusted EBITDA margin | **37.7%** | 39.3% | **−160bps** |

Comcast's own explanation, verbatim: *"Domestic broadband revenue decreased due to **lower average rates and
a decline in the number of domestic broadband customers**."*

**Both terms of the product are negative.** Subscribers 28,486k vs 28,989k = **−1.7%**; revenue **−5.5%**;
therefore **ARPU is down ~3.9%**. This is the single most important fact about Comcast and it is fully
disclosed.

Residential Connectivity & Platforms generates **$6.45bn of the company's $8.90bn of quarterly adjusted
EBITDA — 72%.** The segment that is 72% of the earnings is shrinking 8% a year with margins compressing.

---

## 4. MODE B — THE FIRST-PRINCIPLES QUESTIONS

### B-1. Is the "strategic pivot in broadband" working? **The evidence says it is working LESS, not more.**

The pivot is deliberate: give up price (5-year locks, simplified pricing) to slow subscriber losses. Fine as
a strategy. The question is the elasticity. Comcast has now run the experiment twice:

| | Domestic broadband net losses | y/y improvement |
|---|---|---|
| **Q1-2026** | **−65,000** | **+117,000** |
| **Q2-2026** | **−167,000** | **+34,000** |

**The improvement collapsed from 117k to 34k in one quarter while the price giveaway continued and deepened.**
That is the disconfirming evidence. Q1 looked like proof of concept; Q2 says the elasticity is far worse than
Q1 implied — or that Q1's improvement was seasonal/promotional pull-forward.

Crude but instructive arithmetic: the ~3.9% ARPU decline is worth roughly **$255M of forgone quarterly
broadband revenue**. It bought **34,000** subscribers of year-over-year improvement, worth roughly **$9M** of
quarterly revenue at ~$88/month. The counterfactual is unknowable — losses without the pivot might have been
far worse — but management has not offered one, and the trend in the ratio is the wrong way.

**Honesty read.** The marketed takeaway is *"our strategic pivot in broadband is gaining traction, and we are
seeing that progress extend across the broader connectivity portfolio."* The highlights bullet leads with
*"Domestic Residential Broadband Customer Net Losses Improving by 34,000 Year-over-Year."* The data underneath
shows the rate of improvement **fell by two thirds** quarter over quarter while the revenue cost rose. Every
input is disclosed in the segment tables — this is not concealment. It is emphasis. **Grade: REVIEW_FLAG on
emphasis, not ELEVATE.** Per house doctrine, honestly disclosed bad news is CLEAN; re-detecting it is not the
product. But the *direction of the second derivative* is the alpha-relevant read and it is the one the
release does not frame.

### B-2. What are we actually buying? **Not the company in the screen's price history — and not the one you would own in a year.**

- **2026-01-02:** Versant (the cable networks) already spun out.
- **2026-05-31:** Sky Germany sold.
- **2026-06-29:** intention announced to spin **NBCUniversal + Sky** — parks, studios, Peacock, NBC, Telemundo,
  Bravo, Sky — into a second independent public company, targeted **~one year out**. Michael Angelakis
  (former CFO) returns as CEO of the connectivity RemainCo; Mike Cavanagh runs NBCU.
- **May–June 2026:** cash tender offers across eleven Comcast and two Comcast Cable note series (8-K
  2026-05-27 et seq.) — the capital stack is being restructured ahead of the split.
- **2026-06-29:** **buyback paused** for the duration.

**The lane brief described CMCSA as "post-Versant-spin RemainCo." It is not. The large separation is ahead,
not behind.** The security on offer today is a pre-breakup conglomerate roughly twelve months from splitting
into a levered, declining connectivity business and a media company. The screen's "own 3-year high" reference
of $39.75 belongs to an entity that contained Versant **and** NBCUniversal **and** Sky Germany. Two of those
are already gone; the third is going.

### B-3. Where does the debt go? **The unanswerable question that decides the outcome.**

Verified capital structure, 2026-06-30 (XBRL, 10-Q):

| Item | Value |
|---|---|
| Long-term debt and capital-lease obligations | **$84,264M** |
| Current debt | **$6,117M** |
| **Gross debt** | **$90,381M** |
| Cash and equivalents | $7,661M |
| Short-term investments | $17M |
| **Net debt** | **$82,703M** |
| Diluted shares (Q2-2026) | **3,570M** |
| Market cap @ $24.56 | **$87.7bn** |
| **Enterprise value** | **$170.4bn** |

Annualising H1-2026 adjusted EBITDA of $16,831M gives ~**$33.5bn**, so **EV/EBITDA ≈ 5.1x** and **net leverage
≈ 2.47x**. Fine at the consolidated level. But post-split, connectivity carries ~$31.9bn of EBITDA that is
**declining**, and NBCU carries ~$5bn that is growing. If the debt follows the cash flow — which it will,
because that is where the coverage is — the connectivity RemainCo becomes a **~2.5x-levered melting asset**,
and the ratings and the equity both re-price against a shrinking denominator. **The Form 10 has not been
filed. The allocation is UNVERIFIABLE, and it is the swing factor in the whole thesis.**

### B-4. What does the sibling spin tell us? **VSNT is the read-through, and it is negative.**

Versant, distributed 2026-01-02, traded when-issued around $46–47 in December, opened regular-way ~$46.6, and
is **$36.82 today — −22.6% from its own high**, having fallen 13.0%/10.6%/8.2% on 2026-01-05/06/07 as index
funds and mandate-constrained holders dumped a small-cap media stub. The parallel tier-4 lane courts it as
**FORCED_SELL_DOWNGRADE** for exactly that reason. **The same mechanical forced-selling will apply to the
NBCU stub in ~2027, and to a much larger float.** Anyone holding CMCSA through the separation inherits it.

---

## 5. MODE A — CLAIM VERIFICATION, Q2-2026 (8-K 2026-07-23, Ex-99.1)

| Metric | Q2-2026 | Q2-2025 | Change | Q1-2026 change |
|---|---|---|---|---|
| Revenue | $29,940M | $30,313M | −1.2% | +5.3% |
| **Pro forma revenue** (ex-Versant, ex-Sky Germany) | $29,568M | $28,249M | **+4.7%** | +10.9% |
| Adjusted EBITDA | $8,902M | $10,283M | **−13.4%** | −16.8% |
| **Pro forma Adjusted EBITDA** | $8,923M | $9,423M | **−5.3%** | **−8.8%** |
| **Adjusted EPS** | **$1.04** | $1.25 | **−16.7%** | **−27.5%** |
| GAAP EPS | $0.99 | $2.98 | −66.9% (prior year held a $9.4bn Hulu gain) | −32.6% |
| Free cash flow | $4,604M | $4,501M | +2.3% | −28.0% |
| Capital expenditure | $2.9bn | — | **+8.3%**; C&P capex **+19.9%** | +4.4% |

Segment detail, Q2-2026: Business Services $2,671M **+3.7%**, EBITDA $1,516M **+5.0%**, margin 56.7% (the one
genuinely healthy connectivity line). **Theme Parks revenue $2,413M +2.7% but EBITDA $609M −5.1%** — Epic
Universe's second year is dilutive to margin, and management concedes *"near-term softness in Theme Parks."*
Peacock EBITDA **+$189M**, first-ever quarterly profit, 48M subscribers. Studios EBITDA **+$141M**. Media
revenue +25.3% but **+15.6% excluding the FIFA World Cup**; Media EBITDA only **+3.7%**.

**Claim → finding, the three that matter:**

1. **Claim:** "Pro forma revenue increased 4.7%." → **Method:** read the same table's EBITDA line.
   **Finding: TRUE AND MATERIALLY INCOMPLETE.** On the identical pro-forma basis, **Adjusted EBITDA fell 5.3%**.
   Revenue growth is being purchased with margin — and 2026 carries an unusually heavy sports slate (Milan
   Cortina Winter Olympics + Super Bowl LX in Q1, FIFA World Cup in Q2) that inflates the revenue line and
   barely moves EBITDA. Media revenue +25.3% converts to Media EBITDA **+3.7%**.
2. **Claim:** "our best wireless quarter ever … 448,000 line additions … 10.2 million total lines."
   **Finding: CONFIRMED and genuinely good.** Wireless service revenue **+14.2%**. But it is $1,007M against
   $6,280M of broadband — **the whole wireless business is 16% the size of the line it is meant to defend**,
   and Domestic Convergence revenue (the two combined, which is the actual strategic unit) is still **−3.2%**.
3. **Claim:** "Peacock reached profitability for the first time."
   **Finding: CONFIRMED**, +$189M EBITDA, +$290M y/y. Real. And it is going to the other company.

### Verified valuation

| Multiple | Value |
|---|---|
| Adjusted P/E on FY26E adjusted EPS ~$3.65 (H1 $1.83 × 2) | **~6.7x** |
| EV / FY26E adjusted EBITDA ~$33.5bn | **5.1x** |
| FCF yield on equity (H1 $8.5bn → FY ~$13bn) | **~14.8%** |
| Dividend yield | **5.42%**, ~36% payout — well covered |
| Net leverage | 2.47x |

At 6.7x earnings with a 5.4% covered dividend and a ~15% free-cash-flow yield, Comcast is statistically very
cheap. **That is exactly what a value trap looks like, and the burden of proof is on the denominator.**

---

## 6. DE-RATE vs DERAILMENT — THE RULING

**DERAILMENT. Unambiguously.** The queue's own test is "multiple compressed with the business intact versus
estimates falling and the multiple following." Here the estimates are falling and the multiple is following:

- Adjusted EPS: **−27.5%** (Q1), **−16.7%** (Q2).
- Pro forma Adjusted EBITDA: **−8.8%** (Q1), **−5.3%** (Q2) — on a basis that already strips both divestitures.
- Domestic broadband **revenue** −5.5%; Residential C&P EBITDA −8.0%, margin −160bps.
- Theme Parks EBITDA −5.1%. Capex +8.3% with connectivity capex **+19.9%** — spending more to shrink.
- The buyback, which was the main per-share support at ~$2.2bn in H1 (~5%/yr of the cap), is **paused for
  roughly twelve months.**

There is no version of the HUBS/CTSH/SAP pattern here. Those were businesses whose *numbers kept going up*
while the multiple came down. Comcast's numbers are going down.

**The screen's frame is misapplied to this name.** "Quality-at-own-history-discount" presumes a fallen
compounder. The 69% gross margin that got CMCSA through the quality gate is an artifact of cable's cost
structure (programming is the only major cost above the line), not a proxy for a moat — and the moat is
precisely what fibre overbuild, fixed-wireless access and LEO satellite are eroding, as Charter's April print
demonstrated to the whole sector in one session.

---

## 7. FOUR-IDEA FRAME

1. **The cheapness is real and the decline is real, and the decline is in the 72% of EBITDA that matters.**
   6.7x earnings and a 15% FCF yield are not enough when domestic broadband — the crown jewel — is losing
   both price and volume simultaneously.
2. **The pivot's own evidence turned against it between Q1 and Q2.** The year-over-year improvement in
   subscriber losses fell from 117k to 34k while the price concession deepened. One more quarter like that
   and the strategy is falsified by its own metric.
3. **You are buying a company that will not exist in this form in twelve months, and the debt allocation —
   the thing that determines whether the connectivity RemainCo is a cash cow or a levered melting asset —
   has not been disclosed.** The Form 10 is the gating document and it is not filed.
4. **The sibling spin already ran this experiment.** VSNT is −23% from its own high on exactly the forced
   selling the tier-4 lane is courting. The NBCU stub will be larger and the mechanism identical.

---

## 8. SCENARIOS (12–18 months)

| | p | Reasoning | FV |
|---|---|---|---|
| **Bear** | 0.35 | Broadband revenue decline steepens toward −7/−8% as fibre, FWA and LEO competition compounds (Charter's print showed this is sector-structural, not Comcast-specific); Residential EBITDA −10%; FY27 adjusted EPS ~$3.00; cable multiple compresses to ~4x EBITDA; NBCU spins into a discounted media tape | **$19** |
| **Base** | 0.45 | The pivot stabilises losses around −150k/quarter, ARPU decline moderates as the price-lock cohort matures; consolidated EBITDA flat to −2%; conservative sum-of-the-parts — connectivity 4.5x × $31.9bn = $143.6bn, NBCU 7x × $5.0bn = $35bn, less $82.7bn net debt = ~$96bn equity | **$28** |
| **Bull** | 0.20 | The breakup executes cleanly, connectivity stabilises and re-rates on a clean 5.5x, NBCU gets a parks-led 9–10x, buyback resumes post-separation | **$34** |

**E[FV] = $26.05. Price edge vs $24.56 = +6.1%.** Adding the 5.42% dividend gives a ~**11.5%** expected
total return over 12–18 months, with a 35% probability of a 23% drawdown to $19.

**That is not enough compensation for an unhedgeable structural decline in 72% of the earnings base, with an
undisclosed debt allocation ahead.** For comparison, TYL — courted in the same block — offers +10.3% price
edge with a bear case only 7% below spot.

---

## 9. CATALYST MAP

| Catalyst | Date | p | Magnitude | Leading indicator |
|---|---|---|---|---|
| **Q3-2026 print** | ~late Oct 2026 (estimated from prior-year cadence, **not** confirmed) | 1.00 | ±8–12% | Domestic broadband **revenue** growth; whether the y/y improvement in net losses keeps shrinking |
| **NBCU/Sky Form 10 filing** | H1-2027 | 0.85 | ±10–15% | **The debt allocation.** This is the document that decides the thesis |
| Separation completion | ~mid-2027 | 0.75 | forced-selling drag on the stub | VSNT's January 2026 pattern is the template |
| Buyback resumption | post-separation, ~2027 | 0.70 | +4–5%/yr | only after the split |
| Dividend action | ~Jan 2027 declaration | 0.60 raise | +1–2% | Comcast raised $0.31 → $0.33 in Jan-2025; payout is only ~36% |
| Competitive data points (Charter, T-Mobile, Verizon, LEO) | continuous | 1.00 | ±5–10% | 2026-04-24 showed a peer's print moves CMCSA more than its own |

**Note the asymmetry:** the two largest catalysts (Form 10, separation) are both *structural* rather than
*operational*, both are 6–12 months out, and both carry mechanical selling pressure rather than a re-rating
trigger. Meanwhile the operational catalyst — Q3 broadband — is the one that can only confirm or worsen.

---

## 10. PLAN

**REJECT. No position. No staged order. No watch-list entry beyond the re-open triggers below.**

Below 4/10 the contract requires no entry band, and none is warranted. The name is not a candidate; it is a
cheap declining asset in the middle of a corporate reorganisation.

### Re-open triggers (any ONE re-opens the court; none of them is a buy signal on its own)
1. **Domestic broadband revenue** decline narrows to better than **−3.0% y/y for two consecutive quarters.**
   This is the only operational fact that would change the ruling.
2. **NBCU/Sky Form 10 filed** with the debt allocation disclosed, and connectivity RemainCo pro-forma net
   leverage **≤2.5x** against an EBITDA base that has stopped declining.
3. **Price below $19** — inside the bear case — with the dividend intact and coverage under 45% of FCF.
4. **Buyback resumed** at scale post-separation.

### Freezable call
**CMCSA | 2026-10-31 | "Comcast's Q3-2026 domestic broadband revenue declines year-over-year by MORE than
4.0%" | our_p = 0.72**

Reasoning: Q2 printed −5.5% with both price and volume negative; the price-lock cohort is still rolling on,
so the ARPU drag mechanically persists into H2; the subscriber base entered Q3 503,000 smaller than a year
earlier, which is a locked-in ~1.7-point volume headwind before any Q3 churn. The 28% weight on a
better-than-−4% print is the possibility that Q1's promotional intensity does not repeat and the ARPU
comparison eases.

---

## 11. GENERATOR FEEDBACK — one P1, one P3, one confirmed clean

Per house doctrine, an agent-suggested framework change from a court run is a validated hypothesis and
should be wired in, not left as a note.

### CONFIRMED CLEAN — the spin-adjustment concern the lane raised
`yf.Ticker(tk).history(period="3y")["Close"]` **is** spin-adjusted. Verified three ways: the VSNT 10-Q Note 7
distribution ratio (1:25, record 2025-12-16), VSNT's ~$46.63 first regular-way close implying $1.87 per CMCSA
share = 6.3% of a $29.88 pre-spin price, and a matching **constant** 0.9368 factor in IBKR's own pre-2026 bars
with **no ex-date gap** in Yahoo's raw series. Had it been unadjusted, the drawdown would have read *deeper*
(−44% vs −40%), so the naive error would over-select rather than under-select. **No fix needed. Retire the
concern for the cohort.**

### P1 — MISSING: a `pending_corporate_action` gate
The screen has no field for "this company has announced that it is splitting itself in two." CMCSA announced
a tax-free spin of NBCUniversal and Sky on **2026-06-29** and **paused its buyback** the same day. Three
consequences the score cannot see:
- The "own 3-year high" reference is measured against a materially different asset mix (that $39.75 high
  included Versant, Sky Germany **and** NBCU; two are gone and the third is going). No price adjustment fixes
  a *forward* change in composition.
- The security you buy is not the security you hold.
- The buyback — often the main per-share support in a de-rated large cap — can be switched off by the action
  itself.

**Recommendation:** parse recent 8-K items 1.01 / 2.01 / 8.01 headlines for separation/spin/merger/split
language over a trailing 12 months, set a `pending_corporate_action` flag, and apply a hard score multiplier
in the style of the existing `factor_costume` × 0.30. This is a sibling of the existing `spinoff_orphans`
generator and can share its corporate-action feed.

### P3 — BASIS MISMATCH: drawdown measured on total return, premise is about price
The premise is *multiple compression*, which is a price concept, but the drawdown is computed on
`history(period="3y")` with `auto_adjust=True` — a **total-return** series. For CMCSA at a 5.4% yield the two
diverge materially: **−38.2% total-return vs −44.4% price** at $24.56, a 6.2-point gap. For a zero-dividend
name like TYL they are identical. **The metric is therefore not comparable across names, and the bias
systematically under-ranks high-yielders.** Direction is conservative, hence P3 not P1.
**Recommendation:** compute `drawdown_from_3y_high_pct` on `auto_adjust=False` Close (which is still split-
and spin-adjusted), and keep the total-return series only for the P1-4 factor-residual regression, where
total return is the correct input.

### Also worth tightening — the ice-cube guard is too loose for segmented businesses
CMCSA cleared `MIN_REV_CAGR_3Y = −0.02` with a 3-year revenue CAGR of **+0.6%** — a hair above the floor —
while the segment producing **72% of EBITDA** was contracting 8%. This is the segment-level-flooring lesson:
an aggregate floor hides mix erosion. **Recommendation:** where segment data exists, fail a name whose
largest-EBITDA segment is in revenue decline, regardless of the consolidated CAGR.

## 12. CLASSIFICATION

**RISK_PREMIUM, and the premium is not being paid.** No informational edge exists in a $88bn mega-cap covered
by every desk on the street. What is on offer is a statistically cheap security whose cheapness is a correct
assessment of a structurally declining core, wrapped in a twelve-month corporate reorganisation whose central
financial term — the debt allocation — is undisclosed. Under the fairly-paid-risk doctrine the bar is
*fairness verified* plus *tails bounded*; here the fairness is roughly verified (E[FV] +6% price, +11.5% total)
but the tail is neither bounded nor unlevered — a levered connectivity RemainCo against declining EBITDA is
precisely an unbounded tail. **REJECT.**
