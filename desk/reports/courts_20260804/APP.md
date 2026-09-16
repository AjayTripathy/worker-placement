# APP — AppLovin Corporation | COURT_QUEUE_20260804, tier-2 AI-COMPLEX conflict cohort #1

**Court date** 2026-08-03 (evening, US) for the 2026-08-04 session.
**Verdict: WATCH 5/10 — the best business-versus-price combination in the cohort and the only name whose earnings survive an AI-capex break, blocked by a print inside 72 hours and by a growth driver that the filings do not let anyone verify.**
**No red team required (below 6/10).**
**Basis: IBKR live snapshot 2026-08-03, `last` $413.73, `is_close:false`, +1.86% (implies an 8/3 regular close ≈$406.16). 52w range $359.00–$745.61 (IBKR). Historic closes from yfinance daily bars: 7/31 $395.90.**

---

## 1. Cause-check — one identifiable event, and it was not the company

| Event | Source | Result |
|---|---|---|
| Q1-2026 reported 2026-05-06: revenue **$1,842M, +59% y/y**; income from operations **$1,440M — a 78.2% operating margin**; net income $1,206M; diluted EPS **$3.56** (+70% vs $2.10 continuing) | 8-K 0001751008-26-000042 EX-99.1 + 10-Q `app-20260331.htm` | CONFIRMED |
| Adjusted EBITDA $1,557M (84.5%); OCF $1,291M; **FCF $1.3B**; **SBC only $83.4M = 4.5% of revenue**; purchases of PP&E: **none disclosed in investing activities** | 10-Q cash-flow statement | CONFIRMED |
| **Q2-2026 guide: revenue $1,915–1,945M** (+52–55% vs Q2-25 $1,259M), adj-EBITDA margin **84–85%** | 8-K EX-99.1 | CONFIRMED |
| Repurchased/withheld 2.2M shares for **$1.01B in Q1 alone**; shares out 336.3M (from 340.0M a year earlier) | 10-Q statement of stockholders' equity | CONFIRMED |
| Balance sheet: cash **$2,758.7M**, long-term debt **$3,514.0M** → **net debt ~$0.75B** | 10-Q / companyfacts | CONFIRMED |
| **2026-07-13: −12.6% in one session** to $442.85 — a Bank of America note flagging that **June was soft in e-commerce "pixel adds"**, from third-party data | yfinance bars (move CONFIRMED) + Google-News RSS 2026-07-13 (IBD, Barron's, Stocktwits, finance.biggo) for the attribution (PLAUSIBLE) | move CONFIRMED / cause PLAUSIBLE |
| July: **−29.9% on the month**; the 7/31 close of $395.90 was within 1% of the 60-day minimum ($391.98, 7/24) | yfinance bars | CONFIRMED |
| Securities class action *Brownback* (N.D. Cal.), class period **2024-11-07 → 2025-03-27**, alleging materially false statements "regarding the Company's advertising solutions and financial growth"; amended complaint 2025-09-12; **motion to dismiss fully briefed February 2026, undecided**. Consolidated derivative suits stayed behind it. **No SEC investigation disclosed.** | 10-Q Part II Item 1 | CONFIRMED |

## 2. The Mode-B finding — a growth driver with no disclosure venue

**AppLovin's income statement has one revenue line.** The Q1-2026 10-Q reports `Revenue $1,842,449` and nothing beneath it: no e-commerce segment, no e-commerce revenue, no advertiser count, no pixel/tag count, no self-service cohort. The entire "e-commerce advertising pivot" — the thing the equity story now rests on — exists **only in shareholder-letter and earnings-call narrative**.

That is the mechanism, stated in channel terms:

- **Masking channel:** absence, not misstatement. Single-line revenue presentation means the marketed growth driver cannot be reconciled to any audited figure. Nothing false is asserted; the checkable version is simply never published.
- **Signal channel:** third-party web-telemetry — merchant pixel/tag installation counts, scraped by sell-side and alt-data vendors.
- **Signal-to-price latency:** the telemetry leads the print by weeks. On 2026-07-13 a single bank's read of **June** pixel adds moved a $150B company **−12.6% in one session**, three weeks before the quarter it described would be reported. When the only verification channel is external, that channel gets the whole price impact.

Under the honesty-elevate boundary this is the structural limit case: there is **no datum to grade**. The finding is not that APP lied — it is that on its single most price-relevant claim, APP is *unverifiable*, and UNVERIFIABLE is not clean. That is what caps the score at 5.

The *Brownback* complaint alleges false statements about exactly this — "advertising solutions and financial growth" — over the short-seller window. It is fully disclosed in the 10-Q, so under the disclosed-bad-news rule it is not itself the edge. But it is an undecided binary sitting on the same claim the disclosure will not let anyone check.

## 3. Gate test

- **`GUIDE-DECEL` — RIGHT, and benign.** The forward/trailing ratio is genuinely below 0.60, but the cause is a **base effect**, the first of the four PEG-distortion modes already in the knowledge graph. APP's 2H-2025 revenue exploded (Q3-25 $1,405M, Q4-25 $1,658M by subtraction from the FY25 total of $5,481M), so y/y growth mechanically decelerates from +59% (Q1) to a guided +52–55% (Q2) to ~+30s in FY27 without anything breaking. The flag correctly identifies decelerating *reported* growth and correctly cannot tell base effect from business decay — which is the court's job, and here the answer is base effect.
- **`falling` — RIGHT.** On 7/31 APP closed 1.0% above its 60-day minimum, failing the `basing` test (`close > 60d-min × 1.05`) by a wide margin. It is the only name in the cohort that is genuinely still making lows rather than retracing a blow-off. Per the queue's own standing rule — *"FALLING = still making new lows, court only with a named catalyst"* — the named catalyst exists (the Q2 print, §6) and it is imminent, which is precisely why the answer is WATCH and not BUY.
- Path: unlike ARM/MRVL/KLAC, APP is **not** exhausted — only **+15.2%** off a 52w low that is **172 days old**, and its three-year high (2025-12-22) is eight months old. APP's drawdown is a real multi-quarter de-rate, not a seven-week retrace.

## 4. Which leg of the AI cycle funds the earnings — the queue's hypothesis, tested and CONFIRMED

The queue's hypothesis was that "the ads-model channel is the AI leg that survives a capex break best." The filings support it, and more strongly than the framing suggests:

- APP's revenue is **advertiser return-on-ad-spend budgets** — mobile-game user acquisition plus e-commerce performance advertising. Not hyperscaler capital budgets, not GPU units, not WFE.
- **APP is not a buyer of AI infrastructure in any material sense.** Cost of revenue is $203.6M on $1,842M (11%), and the Q1 investing-activities section shows **no purchases of property and equipment at all** — total investing outflow was $5.2M. Axon runs on leased inference capacity at trivial cost relative to revenue. A company with a 78% operating margin and effectively zero capex is not exposed to the capex cycle from either side.
- **No credit exposure to the complex:** $3.51B of ordinary senior notes, $2.76B cash, net debt 0.15× EBITDA. No neocloud counterparties, no take-or-pay, no GPU-backed paper, no vendor financing.

Transmission from an AI-BREAK to APP is therefore **second-order only**: (a) a general advertising recession — real, but gaming UA is among the more resilient ad verticals and is not itself AI-funded; (b) multiple compression by association, which is what the last month has been. A marginal cohort of AI-app advertisers is venture-funded and would vanish, but that cohort is not disclosed (see §2) and cannot be sized.

## 5. Conflict resolution vs AI-BREAK | 2027-12-31 @ 0.45

- **Does the entry require the cycle holding?** On the revenue leg: **no** — the only genuine "no" in this five-name cohort. On the multiple leg: partially, through sentiment.
- **Does the −44.5% de-rate price the break?** Partially, and here that answer is different from the other four. APP's TTM P/S is **22.7×** ($140.1B ÷ $6,164M TTM) against a three-year range of 4.5× → 40.3× — roughly the **50th percentile of its own history**, and 17.6× on FY26E revenue of ~$8.0B. Together with PLTR it is one of only two names in this cohort in the lower half of its own valuation range. On earnings it is ~**27–29× trailing** and ~**21× EV/adj-EBITDA** for a business growing 50%+ with 78% operating margins.
- **Not averaged away:** the honest statement is that APP is the one name here where a positive expected edge survives the 45% break probability — and it is still not buyable tomorrow, for a reason that has nothing to do with the AI cycle.

## 6. The blocker — a print inside 72 hours

APP reports **Q2-2026 this week**. Corroboration: Zacks published "Should AppLovin Stock Be in Your Portfolio **Before Q2 Earnings**?" dated **2026-08-03**, and Kiplinger's earnings calendar for **August 3–7** includes it; APP's Q1 was reported 2026-05-06 and Q2-2025 was reported in the first week of August. Exact date **NOT filing-verified** — no 8-K announcing the call date has been filed.

The contract's rule — *no blind entry inside ~2 weeks of a print* — binds absolutely here. Additional evidence the print is priced: IBKR `implied_vol_underlying` annual **86.9%** against `historical_vol` **66.8%**, a ~20-point IV-over-HV premium that is the market paying up for exactly this event.

**No order on 2026-08-04. None.**

## 7. Scenarios (FY-2027 basis, revenue ~$10.5B mid, net margin ~62%)

| | p | assumption | FV/sh |
|---|---|---|---|
| Bear | 0.30 | e-commerce ramp stalls (the BofA read proves out) and/or *Brownback* MTD denied; FY27 revenue $9.0B (+13%), net income $5.6B, 18× | **$298** |
| Base | 0.50 | e-commerce contributes but decelerates to trend; FY27 $10.5B (+32%), NI $6.5B, 26× | **$499** |
| Bull | 0.20 | self-service e-commerce scales; FY27 $11.6B (+45%), NI $7.2B, 32× | **$679** |

**E[FV] $474.7 vs $413.73 → edge +14.7%.**

A positive edge that does not convert into a position, for three separate reasons: the print (§6), the unverifiable driver (§2), and an undecided securities-fraud MTD on the same claim. Under the response taxonomy this is a **timing** finding (tranche/wait), not a valuation finding — so the correct instrument is a dated re-court, not a price gate.

## 8. Four-idea frame

1. **Buy on 8/4** — rejected. Inside a print window, IV 20 points over HV.
2. **Buy post-print into weakness** — the live idea. If the print confirms the e-commerce ramp and the stock is *still* below ~$430, this becomes a genuine candidate at 0.6–0.9% of the deployable base. Governed by §9.
3. **Buy post-print into strength** — rejected in advance. A relief gap above ~$480 removes the edge (E[FV] $475) and converts this to FAIR.
4. **Premium sale into the 87% IV** — rejected on doctrine (no premium selling in the taxable book; short premium is non-deferrable short-term ordinary income) *and* on the meme-momentum lesson: a flow-driven IV pump around a binary is exactly the setup where a sold call gets overrun.

## 9. Freezable call and the post-print gate

**Freezable:** `APP | 2026-08-31` — bar: *AppLovin's reported Q2-2026 revenue lands at or above the top of its own guide ($1,945M)*. **our_p = 0.55.** (Rationale: APP has beaten the top of its revenue guide in each of the last several quarters, but the BofA June-pixel read is a genuine, independent, adverse data point on the incremental driver — so this is meaningfully below the ~0.75 an unconditional beat-rate prior would give.)

**Post-print re-court gate (all four must hold):**
1. Q2 revenue ≥ $1,915M (the low end of the guide) — a miss inside its own guide is a kill, not a dip.
2. Q3 guide ≥ +40% y/y.
3. Price ≤ **$430** at the re-court.
4. Management provides *some* quantification of the e-commerce contribution — a percentage of revenue, an advertiser count, a cohort figure, anything checkable. **If the disclosure gap persists after the print, cap any position at 0.5% of the deployable base and treat it as a diligence-limited holding, not a conviction one.**

If all four hold: entry band **$370–430**, two tranches, 0.6% then +0.3%.

## 10. Kills

- **Kill outright** if the *Brownback* motion to dismiss is **denied** — that converts an unverifiable claim into a litigated one, and the response taxonomy's data-gap rule then applies at full force.
- Kill if adjusted EBITDA margin falls below 80% (from 84–85%) — that would mean the e-commerce mix is structurally lower-margin than the gaming core, which is the quiet bear case nobody is modelling.
- Kill if the buyback stops — $1B/quarter against $1.3B of FCF is the management signal that matters most in the absence of segment disclosure.

## 11. Verification notes / gaps

- **Top UNVERIFIABLE item: the e-commerce revenue contribution.** There is no segment, no cohort, no advertiser count in the 10-K or 10-Q. It cannot be verified from any primary source. Everything in the bull case about the pivot is company narrative plus third-party telemetry we do not hold.
- **Second gap: the exact Q2 earnings date is not filing-verified** — no 8-K announcing the call. Sourced from news-calendar corroboration only. This does not change the verdict (any date in the Aug 3–7 window blocks entry), but it is stated rather than assumed.
- Cap structure pulled before the EV claim: $3,514M long-term senior notes, no preferred, no converts, no warrants; 336.3M Class A + Class B shares outstanding, 338.7M diluted; dual-class (Class B held by founders — control, not economics). Net debt ~$0.75B.
- Q1-2025 comparatives include a $147.1M loss from discontinued operations (the divested Apps/games business) and a $188.9M goodwill impairment in the prior-year cash flow — both prior-period, both disclosed; growth rates above use continuing operations.
- Honesty read: **not clean, not caught.** Every audited number is straightforward and the adverse items (litigation, discontinued operations, the prior impairment) are all disclosed. The single defect is structural: the growth claim that sets the price has no disclosure venue. That is a *review flag with a size cap*, not an exclusion — and it is the reason a +14.7% modelled edge produces a 5/10 rather than a 7/10.
