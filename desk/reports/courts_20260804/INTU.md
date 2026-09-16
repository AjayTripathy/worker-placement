# INTU — Intuit Inc. | COURT_QUEUE_20260804 (Tier 1, ai_complex:true)

**Court date:** 2026-08-03 (grading for the 08-04 session)
**Verdict: STARTER 5/10 — RISK_PREMIUM (not EDGE). Tranche-gated on the Aug-20 print.**
**RED TEAM REQUIRED: NO** (score below the 6/10 trigger)

---

## 0. Price basis (tape-verified)

| Item | Value | Source |
|---|---|---|
| Last | **$317.05** | IBKR snapshot, cid 270662, 2026-08-03 (`is_close:false`) |
| Prior close | $318.39 | IBKR, 2026-08-03 session |
| 52w high | $788.71 (2025-08-05) | IBKR daily bars, raw |
| 52w low | $252.84 (2026-06-22) | IBKR daily bars, raw (yfinance div-adj $251.72, same date — cross-verified) |
| From high | **−59.8%** | computed |
| Off the low | **+25.4%, 42 days elapsed** | computed |
| YTD | −51.9% | IBKR |
| IV (annual) / HV(30d) | **68.3% / 60.3%** | IBKR |
| Implied move to Aug-20 (17d) | **±14.7%** | 0.683 × √(17/365) |
| Shares o/s | 274.268M (2026-04-30) | 424B5 capitalization table |
| Market cap / EV | ~$85.9B / **~$86B** | computed, see §4 |

Queue premise "−60% from own 3y high" **CONFIRMED** off raw bars.

---

## 1. CAUSE-CHECK — the drawdown is fully read from primary sources

The de-rate has **two distinct phases**. Both are read; nothing here is an unknown.

**Phase 1 — sector AI-disruption de-rate (Jan–Feb 2026), narrative, not fundamental.**

| Date | Move | Cause | Evidence | Status |
|---|---|---|---|---|
| 2026-01-14 | −6.4% | software AI-disruption wave | news RSS | PLAUSIBLE |
| 2026-01-29 | −6.6% | same; INTU −24% YTD by Jan-30 | Yahoo Finance 2026-01-30 | PLAUSIBLE |
| **2026-02-03** | **−10.9%** | **"AI disruption fears rock software stocks again"** (CNBC, sector-wide) + an analyst downgrade (MarketBeat) | news RSS, dated | **CONFIRMED (sector event)** |
| 2026-02-26 | <5% | FQ2 print — "Guidance Misses Estimates. CEO Says AI Isn't a Threat" (Barron's) | 8-K 2026-02-26 + RSS | CONFIRMED |

Note the tell: the FQ2 print itself did **not** produce a large drop. The Jan–Feb leg was multiple compression on an unchanged guide — the classic de-rate signature.

**Phase 2 — name-specific, fundamental (Apr–Jun 2026).**

| Date | Move | Cause | Evidence | Status |
|---|---|---|---|---|
| 2026-04-09 | −6.9% | AI-does-taxes narrative | RSS | PLAUSIBLE |
| 2026-04-13 | — | *"Claude Did This Redditor's Taxes. They Claim Intuit Is 'Cooked'"* (inc.com) | RSS, dated | CONFIRMED (as a published narrative event) |
| 2026-04-23 | −6.2% | "Claude Taps Spotify, Uber, TurboTax in AI Assistant War" | RSS | PLAUSIBLE |
| 2026-04-28 | — | **Marianna Tessel steps down as EVP/GM Small Business Group**, eff. 2026-05-31; Ashley Still absorbs SBG into Mid-Market | **8-K Item 5.02, 2026-04-28** | **CONFIRMED** |
| **2026-05-21** | **−20.0%** (22.4M sh, ~10× normal) | **FQ3 print: beat + raise, PLUS a 17% workforce cut, PLUS the first TurboTax guidance cut** | **8-K 2026-05-20 Items 2.02/2.05/7.01/8.01 + Ex-99.01** | **CONFIRMED** |
| **2026-06-02** | **−8.9%** | **Goldman Sachs cuts to SELL — "Tax Software Giant Faces AI Pricing War"** | RSS, dated 2026-06-02 | **CONFIRMED** |
| 2026-07-28 | — | TD Cowen downgrade, "more negative near-term catalyst path" | RSS | CONFIRMED |
| 2026-07-29 | **+6.4%** | downgrade absorbed, stock rallied — exhaustion tell | IBKR bars | CONFIRMED |

**Cause verdict:** an AI-disruption narrative de-rate (sector-wide first, name-specific second) that management's own May-20 actions then *validated* in the market's eyes. Nothing is unexplained.

---

## 2. THE HONESTY FINDING — aggregate raise floors segment erosion

This is the core of the court. Read across three sequential press releases from EDGAR (primary, not secondary summaries):

**FY26 segment revenue guidance trajectory:**

| Segment | Q1 guide (2025-11-20) | Q2 guide (2026-02-26) | Q3 guide (2026-05-20) | Direction |
|---|---|---|---|---|
| **TurboTax** | **8%** | **8%** (reiterated) | **~7%** | **CUT** ⬇ |
| Credit Karma | 10–13% | 10–13% | **~19%** | RAISED ⬆⬆ |
| ProTax | 2–3% | 2–3% | ~4% | raised |
| Consumer (total) | 8–9% | 8–9% | **~10%** | raised |
| GBS | 14–15% | 14–15% | **~16%** | raised |
| **Total revenue** | $20.997–21.186B | reiterated | **$21.341–21.374B** | RAISED |

**Marketed takeaway:** *"Intuit Reports Strong Third-Quarter Results and Raises Full-Year Revenue Guidance."*

**What the same document says, in the Consumer section:**
- "Total TurboTax Online units to **decline approximately 2 percent**"
- "TurboTax **share of e-files to decline approximately 1 point**"
- "Pay-nothing customers of approximately **7 million, down from 8 million** last year" (−12.5%)
- TurboTax Online **paying** units +2%, on **ARPU +11%** → the 7% revenue growth is **price/mix, not volume**
- "Intuit plans to provide a TurboTax federal tax unit comparison in its **fourth-quarter 2026 earnings release**" — the unit disclosure is **deferred to Aug-20**

**Finding: takeaway-vs-data divergence, mid-grade (spin, not fraud).** The single franchise the entire bear thesis concerns was **cut for the first time all year — in the quarter that contains the completed US tax season** — while the aggregate was raised on a Credit Karma acceleration (10–13% → 19%). This is the **BAH-Civil pattern from the segment-flooring doctrine: an aggregate floor hiding mix erosion.**

Two disciplined qualifications, both of which matter:
1. **Intuit disclosed the datum.** Units, share, and the pay-nothing decline are all in the same press release. Per the honesty doctrine, disclosed-bad-news is not an ELEVATE; the divergence is in the *headline framing*, not in concealment.
2. **The market already repriced it (−20% the next session).** So this finding generates **no honesty alpha** — it is correct re-detection of a disclosed-and-priced fact. Its value here is forward-looking: it establishes that **management's aggregate framing cannot be taken at face value going into Aug-20**, and it identifies the exact metric to watch.

---

## 3. DE-RATE vs DERAILMENT — the ruling

**Ruling: a genuine consolidated DE-RATE wrapped around a real, disclosed, segment-level DERAILMENT in ~23% of revenue.** It is a hybrid, not the clean HUBS/CTSH/SAP pattern, and not a full derailment.

**De-rate evidence (multiple compressed, estimates rising) — audited 9-month FY26 from XBRL:**

| Metric | 9mo FY25 | 9mo FY26 | Δ |
|---|---|---|---|
| Revenue | $15,000M | **$17,094M** | **+14.0%** |
| GAAP operating income | $4,584M | **$5,409M** | **+18.0%** |
| GAAP net income | $3,488M | $4,203M | +20.5% |
| Operating cash flow | $5,826M | **$7,507M** | **+28.8%** |
| SBC | $1,478M | $1,549M | +4.8% (**9.9% → 9.1% of revenue**) |
| Buybacks | $2,026M | **$3,341M** | **+64.9%** |

Consolidated FY26 guidance was **raised twice and never cut**. Operating leverage is real and improving *before* the restructuring. SBC intensity is *falling*. Buybacks *accelerated 65%* into the de-rate.

**Derailment evidence (confined to Consumer/TurboTax):**
- TurboTax FY26 guide cut 8% → 7%; units −2%; e-file share −1pt; free funnel 8M → 7M.
- **17% workforce reduction** (8-K Item 2.05, 2026-05-20): ~3,000 roles, **$300–340M charge**, largely in FQ4, substantially complete by FQ1-FY27. This is by far the largest RIF in Intuit's history. CNBC framed it as "reckons with slowing growth."
- SBG leadership departure three weeks before the print (8-K 5.02).
- Sell-side estimate revisions still negative (GS → Sell Jun-2; TD Cowen → downgrade Jul-28).

**Revenue at risk, sized:** FY26E TurboTax ≈ $5.0B on $21.36B total = **~23% of revenue** (~30–35% of profit at tax-software margins). The other **~77% — QuickBooks/GBS and Credit Karma — is accelerating**: GBS Online Ecosystem +19% (**+22% ex-Mailchimp**), QuickBooks Online Accounting revenue **+22%**, mid-market "north of 30%", Credit Karma +15% and guided to +19%.

The counter-read on the unit loss, which is legitimate and unresolved: Intuit has spent three years deliberately migrating from free/DIY to assisted. **TurboTax Live revenue +36% to $2.8B = 53% of TurboTax revenue**, Live customers +38%, and **paying units still grew +2%**. Losing 1M *pay-nothing* customers is arguably the stated strategy executing, not cannibalization. The bear and bull readings of the same datum are both internally consistent — which is precisely why IV is 68%.

---

## 4. CAP STRUCTURE — pulled BEFORE any EV/valuation claim

From the **424B5 capitalization table (2026-06-08), as of 2026-04-30**:

| | Actual | As adjusted |
|---|---|---|
| Cash & equivalents | $4,681M | $6,416M |
| Total principal debt | $6,200M | **$7,950M** |
| Total long-term debt | $6,162M | $7,897M |
| Total stockholders' equity | $20,629M | $20,629M |
| **Preferred stock** | **none issued or outstanding** | — |
| Shares outstanding | 274,268k | — |

June 2026 raise: **$750M 4.950% notes due 2031 + $1,000M 5.500% notes due 2036 = $1.75B** ($1.739B net), settled 2026-06-11. **Use of proceeds: general corporate purposes, may include refinancing the 5.250% 2026 Notes ($750M, due 2026-09-15) and the 1.350% 2027 Notes ($500M).** This is a refinancing/terming-out, not a hole-filler.

**No preferred outstanding. No convertibles. No warrants. No pre-funded warrants.** Includes a $1,200M **secured** revolver draw — the only non-vanilla item, worth monitoring.

Investments = $6.8B cash+investments (per Q3 PR) − $4.681B cash = **~$2.12B**. Pro forma cash+investments $8.54B vs debt $7.95B → **net cash ≈ +$0.59B at Apr-30**; after FQ4 buybacks (~$1.1B) and restructuring cash (~$0.3B), the Jul-31 balance sheet is likely **net-debt-neutral to modestly net-debt (±$1B)**. Investment-grade, unlevered on any measure. **EV ≈ market cap ≈ $86B.**

---

## 5. VALUATION — and the SBC honesty correction

| Metric (FY26E, company guide) | Multiple @ $317.05 |
|---|---|
| Non-GAAP diluted EPS $23.80–23.85 | **13.3×** ← the number the bulls quote |
| **GAAP diluted EPS $15.79–15.84** | **20.0×** |
| EV / revenue $21.36B | 4.0× |
| EV / non-GAAP operating income $8.79B | 9.8× |
| EV / GAAP operating income $5.71B | 15.1× |
| EV / FCF (~$7.4B) | 11.6× |
| **EV / FCF less SBC (~$5.35B)** | **~16.1×** ← the honest number |

**The SBC correction, and its limits.** Non-GAAP operating income $8.79B vs GAAP $5.71B = **$3.08B of add-backs on $21.36B revenue (14.4% of revenue)**, of which only $0.30B is restructuring; the balance is SBC plus acquired-intangible amortization. FY25 SBC was $1,968M = **10.4% of revenue**. Diluted WASO was **283M in FY22 and 283M in FY25** — four years and ~$8.6B of buybacks produced a **~0.4% net share reduction**, i.e. repurchases were almost entirely consumed offsetting dilution.

**So "INTU at 13×" is not the honest multiple. The honest multiple is ~16× EV/FCF-after-SBC, or 20× GAAP EPS.** The queue's "−60% from the high, gm 81%" cheapness premise is **materially softened, though not refuted** — 16× honest owner earnings on 14% revenue growth with 77% of the mix accelerating is still genuinely reasonable.

Two things partially rehabilitate the SBC picture and should be said: **SBC intensity is falling** (9.9% → 9.1% of revenue YoY), and **share count is now actually shrinking** (278.8M Aug-25 → 273.5M May-26, −1.9% in 9 months) because the de-rate doubled the buyback's accretion power. The **$8B authorization is 9.2% of the shares at $317**, versus ~4.5% at $650. Buybacks ran $3,341M in 9 months, **+65% YoY**. Management is buying its own stock hard, which is a credible signal.

Historical context: INTU traded at roughly **30–35× forward non-GAAP** for most of the last decade. At 13.3× it sits near **one-third of its own history** — the own-history discount is extreme and real.

---

## 6. THE AI-BREAK CONFLICT — courted as the conflict, not averaged away

House frozen call: **AI-BREAK | 2027-12-31 @ p=0.45.** Household already carries ~$5.2M / ~26% AI-complex exposure.

**INTU's conflict runs OPPOSITE to the capex-cycle names, and the queue is right to flag it.** Being precise about which leg does what:

- **AI-WINS leg (cycle holds, p=0.55) — this leg HURTS INTU.** If LLMs keep improving and become agentic and reliable enough to complete a 1040 and run SMB books, DIY tax and bookkeeping commoditize toward free. TurboTax's ~$5.0B and QuickBooks' pricing power both erode. INTU is a **casualty of the AI-WINS scenario** — the named bear ("Claude did this Redditor's taxes… Intuit is cooked", inc.com 2026-04-13; Goldman's "AI pricing war") is explicitly an AI-WINS-world argument.
- **AI-BREAK leg (cycle breaks, p=0.45) — this leg HELPS INTU.** Capability plateaus, providers stop subsidizing free inference and must charge economic prices, agentic reliability disappoints. The disruption narrative deflates and INTU re-rates toward its franchise multiple.

**Does the entry REQUIRE the AI-capex cycle holding? NO — the opposite.** INTU is one of very few liquid, high-quality, cash-generative large-caps that **pays off in the AI-BREAK scenario the house already assigns 45% to**, inside a household that is long the AI-WINS scenario in size. That diversification value is real and is not captured in the standalone FV.

**But the hedge is PARTIAL, and I will not overclaim it.** In an actual AI-capex bust: (a) the whole software complex de-rates on multiple compression — INTU fell hard on Feb-3 purely as a software-beta event, with no company news; (b) a capex bust plausibly comes with a recession, and small-business formation and payments volume are cyclical, which hits QuickBooks/GBS — the 77% that is currently carrying the thesis; (c) Credit Karma is a credit-cycle-levered lead-gen business and is the most cyclical piece of all. So AI-BREAK helps the **narrative axis** while hurting the **beta and SMB-cyclical axes**. Net: a genuine but **imperfect narrative hedge, not a clean short-AI expression.**

**Does the de-rate already price the break?** Partially. At 20× GAAP / 16× honest FCF versus a 30–35× history, the market has priced substantial AI-WINS disruption but not terminal impairment (which would be high-single-digit GAAP multiples). Solving the scenario set below for the market-implied distribution at $317.05 gives **p(bear) ≈ 0.52** against my 0.30 — i.e. the tape is meaningfully more bearish than my base case. That gap is the entire edge, and it rests on a question I **cannot verify**.

---

## 7. SCENARIOS

| | p | FV | Thesis |
|---|---|---|---|
| **Bear** | **0.30** | **$255** | Aug-20 federal unit comparison shows units down mid-single-digits and share down 1.5–2pts; FY27 revenue guided +8–10% (below consensus) with TurboTax ~flat. The "AI does taxes" thesis gets its first hard confirmation. Multiple → ~10–11× FY27 non-GAAP. Revisits the 52w low ($252.84). |
| **Base** | **0.50** | **$395** | FY27 guided +11–12% revenue, non-GAAP EPS $26.75–27.25 (+12–14%) with RIF-driven margin expansion. Units −2–3% but paying units and ARPU up; framed as deliberate upmarket mix and largely accepted. Re-rates to ~14.5–15.5× — roughly the pre-May-print level ($383–400). |
| **Bull** | **0.20** | **$555** | FY27 guide at/above consensus with a margin surprise (17% RIF cuts ~$1.0–1.2B run-rate opex, half retained); non-GAAP EPS guide $28+; federal units roughly flat with paying units up; Credit Karma keeps accelerating; AI narrative cools. Re-rates to 19–20×. |

**E[FV] = 0.30(255) + 0.50(395) + 0.20(555) = $385.0**
**Edge vs $317.05 = +21.4pp**

---

## 8. FOUR-IDEA FRAME

1. **The cheapness is half-real.** 13.3× is a non-GAAP artifact; 16× EV/FCF-after-SBC is the honest figure. Still a large own-history discount, but not the fat pitch the screen implies.
2. **77% of the business is accelerating and 23% is contested.** GBS Online Ecosystem +22% ex-Mailchimp and QuickBooks Online Accounting +22% are not the numbers of a company being disrupted. The disruption is real but ring-fenced in DIY tax — for now.
3. **The company scheduled its own binary.** Intuit committed in writing to publish the TurboTax federal unit comparison on Aug-20. The bear's decisive metric arrives on a known date, 17 days out, with IV at 2.3× normal. Entering size before that is paying full freight for a coin-flip.
4. **The portfolio argument outranks the standalone argument.** INTU is a partial hedge to a household that is $5.2M long the AI-WINS scenario. That is the best reason to own it and the reason a starter is justified despite only risk-premium-grade standalone edge.

---

## 9. CLASSIFICATION — RISK_PREMIUM, not EDGE

The decisive question — *will LLMs commoditize DIY tax preparation and SMB bookkeeping by 2029?* — is one on which we have **no informational advantage and no verification path**. We cannot check it against a filing, a satellite image, a customs record, or a docket. The ~+21pp expected return is compensation for underwriting genuine, unresolvable uncertainty, not payment for a fact the market has mispriced.

Per the RP_FAIR doctrine, fairly-paid risk is ownable without edge, subject to: fairness verified (**yes** — §5 valuation work is primary-sourced), tails bounded and unlevered (**yes** — no preferred, no converts, no warrants, net-debt-neutral, investment-grade), sleeve-capped (**yes** — see §10), and carry-vs-edge labeled (**this is carry, and it is labeled**).

---

## 10. PLAN — entry band, tranche, sizing

**Size: 0.60% of the $3.3M deployable = ~$19.8k total.** Cut from the 1.2% ruled cap because (a) classification is RISK_PREMIUM not EDGE, (b) the decisive question is unverifiable, and (c) the ledger flags a correlated software/IT-services book (NOW/HUBS/MNDY/CTSH/DFIN/SAP/G) — INTU adds to an existing factor.

Per the response-taxonomy doctrine this is **two findings, two instruments**: a **timing** problem (Aug-20 binary) → **tranche**; and a **business-risk** problem (unverifiable terminal value) → **size cut**. Neither is a valuation problem, so this is *not* a WAIT.

| Tranche | Trigger | Limit | Size |
|---|---|---|---|
| **T1** | now, pre-print | **≤ $312** GTC limit | $6.5k (0.20%) |
| **T2a** | after 2026-08-20, if no kill fires | ≤ $345 | $13.3k (0.40%) |
| **T2b** | after 2026-08-20, if the print breaks but GBS Online Ecosystem ex-Mailchimp still ≥18% | ≤ $270 | $13.3k (0.40%) |

T1 is set *below* spot deliberately: at **+25.4% off a 42-day-old low**, we are not buying the bottom tick, and the contract's path check says say so. **No premium selling** (taxable book — CSP/CC premium is non-deferrable short-term ordinary income; use GTC limit ladders).

---

## 11. CATALYST MAP (probability × timing × magnitude)

| Catalyst | Date | p | Magnitude | Leading indicator |
|---|---|---|---|---|
| **FQ4-FY26 print + first FY27 guide + pre-committed TurboTax federal unit comparison** | **2026-08-20** (verified) | 1.00 | **±15%** (68% IV → ±14.7% over 17d) | pre-announcement sell-side revisions; TurboTax app-store/download proxies |
| 17% RIF flows through the P&L (opex step-down) | FQ1-FY27, reported ~Nov-2026 | 0.85 | +5–8% if retained | FQ4 restructuring charge lands at $300–340M as guided |
| $8B buyback executed at depressed prices | continuous | 0.90 | +2–4%/yr accretion | quarterly `PaymentsForRepurchaseOfCommonStock` ≥$1.5B/qtr |
| 2027 tax-season DIY share data (the real terminal test) | Apr–May 2027 | 1.00 | ±20% | IRS e-file statistics; Direct File status |
| Regulatory/monopoly-pricing tail (FTC/state AG on pricing or free-file marketing) | open-ended | 0.15 | −5–10% | FTC docket; state AG filings |

**PRIOR ART — respected, not contradicted.** An INTU resolution pack is **ARMED for 2026-08-20 at frozen p(HIT)=0.46** (HIT = FY27 revenue + EPS guide at/above consensus with no AI-cannibalization disclosure on TurboTax/Consumer). **I do not reprice that call.** I note only, from primary sources, that Intuit has **pre-committed in writing** to publishing the TurboTax federal unit comparison in that same release, and that units are already guided −2% with e-file share −1pt — so the *variance* around the pack's second leg is higher than a naive read suggests. That is a reason to court around the pack and hold T2 back, not a reason to move the frozen p. The research-ledger entry (WATCH; "adjudicate TurboTax-AI terminal-vs-cyclical + GBS+CK sum-of-parts BEFORE any position") asked for exactly this adjudication; §3 and §5 deliver it and the answer is "ring-fenced, not terminal — but unverifiable."

---

## 12. FREEZABLE CALL

**`INTU | 2026-08-20`** — Intuit's FQ4-FY26 earnings release will publish the promised TurboTax federal tax unit comparison, **and it will show total TurboTax federal units DOWN year-over-year.**
**our_p = 0.78**

Basis: the FY26 guide already states total TurboTax Online units −2% and e-file share −1pt, and pay-nothing customers 8M → 7M. For federal units to print flat-or-up, the shrinking desktop channel would have to offset an Online decline. Resolvable from the press release text alone. **This is a different bar from the armed pack's (which turns on the FY27 guide vs consensus) and does not overlap or contradict it.**

---

## 13. KILL TRIGGERS (dated, set AT ENTRY)

1. **2026-08-20** — FY27 revenue guide below **+9%** → the derailment leg wins. Exit T1, cancel T2.
2. **2026-08-20** — TurboTax federal units down **>5% YoY** OR e-file share down **>2pts** → terminal-impairment evidence. Kill.
3. **2026-08-20 / FQ1-FY27** — **segment kill bar (LDOS template):** GBS Online Ecosystem growth below **15%** (below **18% ex-Mailchimp**) → the 77%-intact premise breaks. Kill regardless of the consolidated number.
4. **2026-12-31** — Credit Karma growth below **10%** → the offset that funded the FY26 "raise" is gone. Re-court from scratch.
5. **Any quarter** — non-GAAP-to-GAAP add-backs above **15% of revenue** ex-restructuring → SBC honesty breach. Size cut by half.
6. **Any quarter with the stock below $350** — buybacks below **$1.5B/quarter** → management does not believe its own valuation. Kill.

---

## 14. VERIFICATION NOTES — claim | method | authority | finding

| Claim | Method | Authority | Finding |
|---|---|---|---|
| −60% from the 3y high | raw daily bars, two independent feeds | IBKR cid 270662; yfinance | **CONFIRMED** (−59.8%) |
| The May-21 −20% was a "beat + raise" | read the actual release | EDGAR 8-K 2026-05-20 Ex-99.01 | **CONFIRMED** — and materially incomplete; see next row |
| The May print was clean | compare segment guides across three releases | EDGAR FY26 Q1/Q2/Q3 press releases | **REFUTED** — TurboTax cut 8%→7%; aggregate raised on Credit Karma 10-13%→19% |
| 17% workforce reduction, $300–340M | primary filing | **8-K Item 2.05, 2026-05-20** | **CONFIRMED** |
| SBG leadership departure pre-print | primary filing | **8-K Item 5.02, 2026-04-28** | **CONFIRMED** (Tessel out eff. 2026-05-31) |
| Estimates rising, not falling (consolidated) | 9-month audited XBRL + guide history | data.sec.gov companyfacts CIK 896878 | **CONFIRMED** (+14.0% rev, +18.0% op inc, guide raised twice) |
| Net cash / no dilutive securities | capitalization table | **424B5 2026-06-08** | **CONFIRMED** — no preferred/converts/warrants; net cash +$0.59B pro forma |
| June 2026 debt raise size and purpose | prospectus | **424B5** | **CONFIRMED** — $1.75B, refinancing the 2026/2027 notes |
| Buybacks retire ~no net shares historically | diluted WASO series | XBRL | **CONFIRMED** (283M FY22 → 283M FY25); *now* shrinking (−1.9% in 9mo) |
| "13× forward" is the honest multiple | GAAP/non-GAAP bridge + SBC | XBRL + guide | **REFUTED** — honest figure ~16× EV/FCF-after-SBC, 20× GAAP |
| Aug-20 print date | news + IR calendar reference in the releases | RSS + Ex-99.01 | **CONFIRMED** |
| Goldman → Sell on Jun-2 caused the −8.9% | dated headline vs dated bar | RSS + IBKR bars | **CONFIRMED** (date match) |

### Gaps — UNVERIFIABLE (these are NOT clean)

1. **TOP GAP — the terminal question itself.** Whether LLMs commoditize DIY tax prep and SMB bookkeeping is **not verifiable from any primary source available to us**. It is the single load-bearing input to the FV and it is unknowable today. This is why the classification is RISK_PREMIUM and the size is cut.
2. **IRS Direct File status not independently verified.** The queue asked for the statutory/political channel from primary sources. WebSearch budget was exhausted session-wide and the subagent pool was saturated by parallel lanes, so irs.gov / congress.gov were not reached. Intuit's own FY26 disclosures do not cite Direct File as a driver of the unit decline, and the pay-nothing cohort (8M → 7M) is where Direct File would bite — but I did **not** confirm whether Direct File operated in the 2026 season or was terminated. **Carry this forward; it is a genuine coverage gap, not a clean finding.**
3. **FQ3 earnings-call transcript and prepared remarks not read.** The 8-K exhibits are read; management's Q&A framing of the unit decline and any FY27 color is not. A −20% move on a beat-and-raise suggests the call carried incremental content.
4. **Consensus FY27 estimates not independently sourced.** Scenario bands are anchored to company guidance and the historical multiple, not to a verified consensus number. The armed pack's HIT/MISS bar ("at/above consensus") therefore cannot be pre-computed here.
5. **Monopoly-pricing regulatory tail scoped but not researched.** No FTC/state-AG docket pull was run (same budget constraint). Sized at p=0.15 on priors only.

---

## 15. SCORE — 5/10, STARTER

**For:** cause fully read from primary sources with nothing unexplained; 77% of revenue accelerating (GBS Online Ecosystem +22% ex-Mailchimp, QBO Accounting +22%, mid-market +30%); consolidated estimates *rising* while the multiple collapsed; clean investment-grade cap structure with no dilutive securities; buyback accelerating 65% YoY into the de-rate with an $8B authorization worth 9.2% of the shares; SBC intensity falling; a genuine (if partial) AI-BREAK hedge for a household that is $5.2M long AI-WINS; extreme and real own-history discount.

**Against:** the honest multiple is ~16×/20×, not the 13× the screen implies — the queue's cheapness premise is softened; the decisive question is unverifiable and covers ~23% of revenue and ~30–35% of profit; TurboTax was cut while the headline said "raises"; the largest RIF in company history says management sees slower growth than it guides; a scheduled binary in 17 days on the bear's exact metric with IV at 2.3× normal; +25.4% off a 42-day-old low; sell-side revisions still negative; classification is RISK_PREMIUM with no informational advantage; adds to an existing correlated software sleeve; and two named coverage gaps (Direct File, transcript) remain open.

**5/10 — below the 6/10 red-team trigger.** Good business, fairly-to-modestly-cheap on honest numbers, decisive question unverifiable, entry timing poor. A tranche-gated starter, not a position.
