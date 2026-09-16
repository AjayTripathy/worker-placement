# KKR & Co. Inc. (NYSE: KKR) — Adversarial Court
**Court:** COURT_QUEUE_20260804, TIER_1_clean | **Date:** 2026-08-03 (US evening, grading for 08-04)
**Verdict: RISK_PREMIUM 4/10 — real de-rate, real franchise, edge-thin at spot. Entry gated well below the tape.**
**Red team required? NO** (score < 6)

---

## 0. Price basis (tape-verified)

| Item | Value | Source |
|---|---|---|
| Last | **$106.56** (`is_close: true`, 2026-08-03 session) | IBKR `get_price_snapshot`, cid 321328198 |
| 08-03 session | open 102.95 / high 107.30 / low 102.60 / close 106.56, vol 2.845M | IBKR daily bars |
| **08-03 move** | **+5.06%** vs 07-31 close $101.43 | IBKR daily bars |
| 52w high / low | $151.545 / $82.71 (intraday); close-low $83.88 on 2026-03-12 | IBKR `misc_statistics` + daily bars |
| ~3y high | $170.40 (week of 2025-01-27) | IBKR weekly bars, 2y |
| YTD | −16.26% | IBKR `year_to_date_change` |
| Annualised IV | 39.5% | IBKR `implied_vol_underlying` |

**The screen's "gm 54% / rev3y 51.1%" fields are meaningless here** and were discarded: KKR consolidates Global Atlantic's insurance revenue ($3.52B of the $5.73B GAAP Q2 revenue), so GAAP "revenue" and "gross margin" describe an annuity balance sheet, not the asset manager. All economics below are re-derived from FRE, carry realizations, AUM flows and Global Atlantic separately, per instruction.

---

## 1. CAUSE-CHECK — what actually caused the de-rate

The drawdown is **two distinct events**, and neither is a KKR earnings miss.

**(a) A sector-wide multiple unwind through 2025.** KKR fell from ~$170 (late Jan-2025) to ~$103 by the Feb-2026 Q4 print — a 40% decline that happened *before* any bad news, while FY25 was a record year. This is pure multiple compression of the 2021-24 "perpetual capital / retail democratization / insurance flywheel" re-rating.

**(b) A private-credit accident at the affiliated BDC, Feb–May 2026.** Confirmed at primary source:

| Event | Date | Source |
|---|---|---|
| FSK dividend cut, jump in troubled loans | 2026-02-26 | Bloomberg/FT headlines via news RSS — PLAUSIBLE (secondary) |
| KKR −8.9% in one session ($101.18 → $92.19) | 2026-02-23 | IBKR daily bars — CONFIRMED |
| KKR 52w low $82.67 intraday | 2026-03-12 | IBKR daily bars — CONFIRMED |
| FSK Q1'26: NAV/sh **$18.83 vs $20.89** (−9.9% in one quarter); EPS **$(1.57)**; net realized+unrealized loss $2.00/sh; net debt/equity 131% vs 122% | 2026-05-11 | FSK 8-K EX-99.1, acc 0001104659-26-058250 — **CONFIRMED** |
| JPM-led revolver **cut to $4,051.7M from $4,700.0M**, margin raised, **minimum-equity covenant floor reset DOWN to $3,750.0M from $5,048.6M** | 2026-05-08 | same EX-99.1, Subsequent Events — **CONFIRMED** |
| KKR subsidiary buys **$150.0M** FSK Cumulative Convertible Perpetual Preferred Series A, 5.00% cash **or 7.00% PIK at FSK's option**; closed at $25.00/sh | agreed 2026-05-10, **closed 2026-06-29** | FSK 8-K 2026-06-29, acc 0001104659-26-078916 — **CONFIRMED** |
| KKR subsidiary tender for **$150M** of FSK common at $11.00; FSK board authorises **$300M** buyback; **KKR waives 100% of its 50% share of the subordinated income incentive fee for 4 quarters** | 2026-05-11 | same EX-99.1 — **CONFIRMED** |
| FSK "new investment originations may be reduced as the Company will focus on supporting existing portfolio companies, reducing leverage, and repurchasing stock" | 2026-05-11 | same EX-99.1 — **CONFIRMED (verbatim)** |

The news feed's "$300 million injection" figure is **PARTIALLY REFUTED**: the SEC-confirmed KKR preferred injection is **$150M**; a separate $150M is the tender. Do not carry the $300M number.

**(c) A Q4'25 carried-interest clawback.** PE Realized Performance Income was **negative $(70.9)M** in 4Q'25, "negatively impacted by $207 million as a result of the previously disclosed carried interest repayment obligation" — net of amounts already recouped from current and former employees. Cost $0.18/adj. share in the quarter (ANI $1.12 reported vs $1.30 ex-clawback). *Source: Q4'25 EX-99.1, acc 0001404912-26-000002 — CONFIRMED.* KKR gave carry back. That is a genuine statement about a PE vintage's marks.

**Cause is fully read. This is not an unknown drawdown.**

---

## 2. MODE B (led) — first-principles disconfirmation

I ignored the "record quarter" framing and asked: *if this franchise were quietly deteriorating, where would it show?* Four places. Three of them show it.

### B1. The "record FRE, +37%" headline is roughly half a reclassification — and the recast was selective

Q2'26 release, Asset Management segment note, **verbatim**:

> "Beginning in 2Q'26, KKR has reported realized performance fees from its K-Series Private Equity vehicles in Fee Related Performance Revenues. Historically, these realized performance fees were included within Realized Performance Income."

Prior periods were **not** recast. The PE segment table proves it: Fee Related Performance Revenues **$0 in 2Q'25 → $167,960k in 2Q'26**, and YTD 2Q'26 $168,806k (i.e. essentially all of it landed in the single quarter).

FRE is the highest-multiple line in an alt manager (recurring, ~20-25x) and realized carry is the lowest (lumpy, ~8-12x). This change moves money from the cheap line to the expensive line and then reports the YoY growth un-recast.

| Measure | Reported | Ex-reclass | Overstatement |
|---|---|---|---|
| Q2'26 FRE | $1,214.1M, **+36.9%** YoY | $1,046.2M, **+18.0%** | ~19pp |
| Q2'26 FRE/adj sh | **$1.32** (record) | ~$1.14 | ~16% |
| 1H'26 FRE/adj sh | $2.45, **+29.0%** | ~$2.27, **+19.2%** | ~10pp |

**The tell is the selectivity.** On the very same document (Insurance segment, p.16) KKR writes: *"See Appendix for endnotes explaining certain prior period information that has been **recast** to conform to the current period presentation. This reclassification had no impact on Insurance Operating Earnings."* KKR recast the change that was neutral and did **not** recast the change that flattered FRE growth by ~19pp. That is the honesty finding: the datum is disclosed in a footnote, the marketed takeaway ("record Fee Related Earnings… up 37%") diverges from the organic result.

**Grading note (house doctrine):** this is takeaway-vs-data divergence, not undisclosed bad news. It does **not** make KKR a liar and it does not make the reclass illegitimate — K-Series performance fees genuinely *are* more recurring than fund carry, and a permanent reclass is defensible. It makes the headline growth rate unusable. Organic FRE/share growth is **+16% to +19%**, which is still good.

### B2. The credit franchise is stalling — in KKR's own flow data

The market's de-rate axis is "private-credit cycle." The print is marketed as refuting it. **KKR's own segment tables confirm it.**

| Credit & Liquid Strategies | 2Q'25 | 2Q'26 | Δ |
|---|---|---|---|
| Management fees | $313.3M | $340.9M | **+8.8%** (vs PE +32.0%, Real Assets +34.6%) |
| Fee Related Performance Revenues | $17.7M | $6.4M | **−64%** |
| Realized Performance Income | $36.0M | $16.8M | **−53%** |
| New capital raised (qtr) | $14.25B | $9.10B | **−36%** |
| New capital raised (YTD) | $28.58B | $24.35B | **−15%** |
| AUM growth YoY | — | **+13%** | slowest of the three segments |

And the decisive one, from the FPAUM rollforward, six months ended 2026-06-30:

> Credit FPAUM: **$289,454M → $294,968M**. New capital raised **+$23,783M**, Distributions and Other **−$22,401M**, Change in value +$4,132M.

**Credit fee-paying AUM organic net flow over H1'26 = +$1.38B on a $289B base = +0.5% in six months.** The credit fee engine is treading water; the reported growth is marks. Meanwhile FSK — the sponsor's own flagship BDC — is explicitly reducing new originations. Morningstar's 2026-03-19 note "KKR's Private Credit Exposure Creates Headwinds for Fundraising" is *independently corroborated by the filings*.

### B3. Global Atlantic is earning a falling ROE on a rising book

| Insurance segment | 2Q'25 | 2Q'26 | Δ |
|---|---|---|---|
| Net investment income | $1,788.5M | $1,954.0M | +9.3% |
| Net cost of insurance | $(1,327.0)M | $(1,468.9)M | **+10.7%** |
| Insurance Operating Earnings | $277.9M | $288.2M | **+3.7%** |
| …of which investment realizations | — | **~$40M** (disclosed) | |
| **IOE ex-realizations** | ~$278M | **~$248M** | **−11%** |
| GA book value | $9,565M | $11,799M | **+23.4%** |
| Implied annualised ROE | ~11.6% | ~9.8% (ex-realizations ~8.4%) | **compressing** |

KKR's own words: higher funding costs "as well as the routine run off of older business that was originated in a lower cost environment." That is honest disclosure of an annuity spread squeeze. Global Atlantic is **19% of Total Operating Earnings** and is going backwards per unit of capital. This is the second-largest earnings pillar and it is the one nobody is discussing.

### B4. Headline AUM growth includes $16B of bought AUM

Arctos closed 2026-05-04; the Q2 AUM rollforward shows **Acquisitions +$15,996M** of AUM and **+$10,084M** of FPAUM.

| Metric | Headline | Organic ex-Arctos |
|---|---|---|
| AUM | $796B, **+16%** | **+13.8%** |
| FPAUM | $638B, **+15%** | **+13.0%** |
| PE AUM | $255B, **+19%** | **+11.3%** |

Consideration was **$1.4B initial equity (vesting through 2033) + up to $550M contingent (through 2031)** — i.e. paid in stock that the "record per adjusted share" figures exclude (see §4).

### B5. Where Mode B found NOTHING (anti-masking — catalogue it)

- **The realization drought is genuinely over for PE.** Realized Performance Income $847.5M vs $418.9M (+102%), with a named, checkable transaction list: Kokusai 20.0x, Hyundai Marine Solutions 7.5x, BrightSpring 6.2x, OHB IPO 5.5x, OneStream 4.5x, MasOrange 2.5x, CoolIT ~15x. "Strongest monetization quarter ever" is **supported**. This is the single most important refutation of the bear case and it is real.
- **The balance sheet is not the risk.** Cash + investments $13.9B, debt at par $9.3B, **net cash and investments $4.6B**, $2.75B undrawn revolver, 'A' rated by S&P and Fitch, average debt maturity ~15 years at a 3% after-tax weighted-average fixed coupon. Nothing hidden.
- **The preferred is not a trap** (see §4) — it is close to per-share neutral on conversion.

---

## 3. MODE A — claim verification

| # | Claim (source) | Method / authority | Finding |
|---|---|---|---|
| 1 | "Record FRE, TOE and ANI per share, quarterly and LTM" | Q2'26 EX-99.1 segment tables vs 2Q'25 | **CONFIRMED as reported / MISLEADING as growth.** Records are real; the +37% growth rate is ~19pp reclass (§B1) |
| 2 | "FRE of $1.2bn, up 37% YoY" | Recompute ex-K-Series-PE reclass | **REFUTED as organic.** +18.0% organic |
| 3 | "Strongest monetization quarter ever" | Realized Performance Income $847.5M vs $418.9M + named deal list | **CONFIRMED** |
| 4 | "Record new capital inflows over the past 12 months" ($133B LTM) | AUM rollforward; YTD $62.1B vs $58.5B | **CONFIRMED but thin** — YTD only +6.1%, and Q1'26 was −9.1% YoY |
| 5 | "AUM $796bn, up 16%" | Rollforward: Acquisitions +$15,996M | **CONFIRMED as reported; +13.8% organic** |
| 6 | Screen: "−39% from own 3y high" | IBKR weekly bars, 3y high $170.40 | **CONFIRMED** (−37.5% at $106.56) |
| 7 | Screen: "gm 54%, rev3y 51.1%" | GAAP income statement | **REFUTED as meaningful** — consolidated insurance float; discarded |
| 8 | Realization drought (de-rate premise) | §B5 | **REFUTED for PE; CONFIRMED for Real Assets** (realized perf income **$0** in 2Q'26 vs $27.4M) **and Credit** (−53%) |
| 9 | Private-credit cycle fear (de-rate premise) | §B2 + FSK primary | **CONFIRMED** |
| 10 | Denominator effect (de-rate premise) | Fundraising $133B LTM record; 93% of AUM ≥8y duration or perpetual | **NOT SUPPORTED** — this leg of the bear case is the weakest |
| 11 | KKR injected $300M into FSK (news) | FSK 8-K 2026-06-29 | **PARTIALLY REFUTED** — $150M preferred (SEC-confirmed) + $150M tender |
| 12 | Net cash position | Q2'26 p.28 | **CONFIRMED** $4,627M, excludes GA |
| 13 | Carry backlog | Gross unrealized carried interest $10.2B; $2.5B net at the 75% mid-point comp accrual | **CONFIRMED** (≈$2.73/adj sh net) |
| 14 | Carry-eligible quality | $410B carry-eligible AUM, **$325B above cost** → **21% below cost** | **CONFIRMED** — one fifth of carry-eligible AUM is under water |

---

## 4. Cap structure (pulled BEFORE any per-share or EV claim — house rule)

| Item | Amount | Source |
|---|---|---|
| Adjusted shares (the per-share denominator) | **~916M** (FRE $1,214.1M ÷ $1.32; cross-checks: ANI ÷ $1.63 = 915.8M; TOE ÷ $1.68 = 916.3M) | derived from Q2'26 EX-99.1 |
| GAAP diluted shares | 945.6M | Q2'26 GAAP table |
| **6.25% Series D Mandatory Convertible Preferred** (NYSE: KKR PR D) | dividend $0.78125/sh/qtr → **51.75M pref shares × $50 = ~$2,587M face**; total pref dividends **$40.4M/qtr = $161.7M/yr** | Q2'26 p.29 + GAAP table |
| Mandatory conversion date | **no later than 2028-03-01** | Q2'26 p.30 footnote (4) |
| Sub notes | KKRS 4.625% due 2061; **KKRT 6.875% due 2065** | 8-K cover, 2026-07-31 |
| Arctos consideration | $1.4B initial equity vesting to 2033 + up to $550M contingent to 2031 | 8-K EX-99.1, 2026-02-05 |
| Debt at par (KKR & Co. only, **excludes GA**) | $9,299M | Q2'26 p.28 |

**The critical disclosure**, Q2'26 p.30 footnote (4), verbatim — adjusted shares *"Excludes the potential dilutive impact of: (i) any conversion of the Series D Mandatory Convertible Preferred Stock (expected no later than March 1, 2028) and (ii) unvested shares of common stock and exchangeable securities."*

So every "record per adjusted share" figure is struck on a denominator that omits the mandatory convert, unvested stock, and the Arctos equity. Fully-loaded share count is plausibly ~955-970M vs 916M ≈ **5% look-through dilution**.

**But — honest correction, this is close to neutral, not a trap.** ANI is computed *before* the $161.7M preferred dividend while adjusted shares *exclude* the preferred shares. Conversion adds ~20.7M shares (≈2.3%) but extinguishes a cash cost worth 3.2% of LTM ANI. Net: roughly a wash, mildly positive. The real, smaller issue is that **today's $5.55 LTM ANI/adj share overstates earnings actually available to common by ~$0.18/share (3.2%)** because the preferred dividend is never deducted. I use $5.37 and $5.92 (FY26E) accordingly.

---

## 5. DE-RATE vs DERAILMENT — the whole job

**Ruling: DE-RATE, with a genuine and confirmed impairment in one of three legs (credit).**

Estimates are **not** falling. The business metric that drives the multiple is compounding straight through the 32% price decline:

| | FY24 | FY25 | LTM 2Q'26 |
|---|---|---|---|
| FRE/adj share | $3.62 | $4.13 (+14%) | $4.68 (+13%) |
| FRE/adj share, ex-reclass | $3.62 | $4.13 | ~$4.40 |
| Price | ~$170 peak | ~$103 (Feb-26) | **$106.56** |
| **P/FRE** | **~47x** | **~25x** | **22.8x (24.2x clean)** |

The multiple halved while per-share earnings power rose ~29%. That is the HUBS/CTSH/SAP winner pattern *in form*.

**The three qualifications that stop this being a 7/10:**
1. The de-rate is **sector-wide**, so no KKR-specific mispricing has been identified (§6).
2. The de-rate axis is **corroborated, not refuted**: credit FPAUM organic net flow +0.5%/6mo, credit fundraising −15% YTD, a live sponsor rescue at FSK, a $207M carry clawback, and Global Atlantic ROE compressing.
3. Growth headlines are **~40-50% manufactured** relative to organic (§B1, §B4).

---

## 6. Sector vs idiosyncratic — the decisive discrimination

Off own 52-week high, close 2026-07-31 (yfinance daily closes; KKR cross-checked to IBKR):

| Alt manager | Off 52w high | | BDC | Off 52w high |
|---|---|---|---|---|
| APO | **−17.8%** | | ARCC | **−17.3%** |
| BX | −32.3% | | OBDC | −25.2% |
| **KKR** | **−32.1%** | | BXSL | −25.9% |
| ARES | −33.6% | | **FSK** | **−47.8%** |
| CG | −33.6% | | | |
| TPG | −37.3% | | | |
| OWL | **−49.3%** | | | |

Two clean reads:

**(1) KKR's de-rate is sector beta, dead mid-pack.** The market is discriminating rationally along the private-credit axis — Blue Owl (purest private credit) −49%, Apollo (most insurance/annuity) −18%. KKR at −32% is priced as what it is: a diversified manager with a big credit book. **There is no KKR-specific dislocation to arbitrage.** This is the finding that caps the score.

**(2) But FSK is a 22-30pp outlier among BDCs.** ARCC −17%, OBDC −25%, BXSL −26%, FSK −48%. The private-credit cycle is turning for everyone; **KKR Credit's flagship vehicle is turning much harder than peers'**. That is a statement about underwriting, not only about the cycle.
*Blue-team concession:* a large share of FSK's bad paper is inherited legacy FS Investments credit (KKR took over management in 2018, merged FSKR in 2021), and FSK has traded at a structural discount for years. So FSK is a *weak* read on KKR-originated credit quality. It is not zero, because Global Atlantic's $164B credit AUM is marked by the same KKR Credit organisation — but I am not treating it as proof.

**(3) Path check — the entry is being offered into a one-day sector melt-up.**

| | 07-31 close | 08-03 close | move |
|---|---|---|---|
| KKR | $101.43 | **$106.56** | **+5.06%** |
| BX | $127.75 | **$134.68** | **+5.42%** |

**No KKR 8-K on 08-03**; the last filing was the 07-30 earnings 8-K. The +5% is sector, not name. Combined with **+28.9% off a 52-week low that is 144 days old**, and −29.7% still below the 52w high: this is a **mature bounce, and today is the worst tick in 90 days to buy it.**

---

## 7. AI-complex conflict — OVERRIDING the queue's `ai_complex: false` to **PARTIAL**

The queue tagged KKR non-AI. That is wrong, per the principal's instruction to treat KKR's private-credit AI-datacenter exposure as the same channel as the house HYG finding (8.27% AI-capex paper, *COMPUTE LLC SPVs). Three routes, all evidenced in the Q2 release:

1. **Infra equity fundraising.** Q2 Real Assets new capital raised was *"primarily driven by **Helix Digital Infrastructure**, K-Series Infrastructure, Asia Infrastructure III and Global Infrastructure V"* — the digital-infrastructure vehicle **led the quarter's biggest fundraise**, and Real Assets is the fastest-growing segment (+18% AUM, mgmt fees +34.6%).
2. **Asset-based finance lending.** Credit AUM includes **$91B of asset-based finance**, and Q2 deployment was *"most active in high grade asset-based finance."* ABF is the primary channel for data-centre / GPU / equipment paper.
3. **Global Atlantic's balance sheet.** $164B of GA's $220B AUM is Credit AUM, invested by KKR Credit, weighted to private IG and ABF.

**Against the frozen house call AI-BREAK | 2027-12-31 @ p=0.45 — stated explicitly, not averaged away:**

- **Does the entry REQUIRE the cycle holding?** *Partially, yes.* Base-case FRE growth leans on the fastest-growing leg (Real Assets/digital infra) continuing to raise and on ABF credit marks holding. An AI-capex break hits KKR three ways at once: infra fundraising stalls → FRE decelerates; ABF/private-credit marks fall → GA book value (only $11.8B of equity against $220B of AUM, ~5.4%) and KKR's own marks take losses; carry realizations dry up. A 3% credit loss on GA's $164B credit AUM = $4.9B = **42% of GA book value**. That is the derailment channel and it is unhedged.
- **Does the de-rate already price the break?** *No — it prices a credit-cycle turn, not an AI break.* At −32% (mid-pack, in line with BX/ARES/CG) the market has repriced the private-credit growth narrative. An actual AI-capex break would take KKR materially lower; that is what the $74 bear case is.
- **Household context:** ~$5.2M / 26% AI-complex exposure already. KKR at 0.4-0.5% adds partial, second-order AI-capex beta. Tolerable at this size, and it must be counted — not booked as a diversifier.

**Book overlap (credit axis).** Current credit-axis positions: OMF $12.9k, BBD $15.6k, HSBK $10.9k, WAL $10.4k, FSBW $8.5k, CAI $7.3k, WF $6.2k ≈ **$72k ≈ 2.2% of the $3.3M deployable**. Light, so KKR is not blocked. But note KKR is a *higher-beta and broader* credit expression than OMF (US consumer) or the banks: it stacks private-credit-cycle beta + AI-capex beta + equity-market beta + rate beta in one line. It **dominates rather than diversifies** the existing sleeve — size accordingly.

---

## 8. Valuation and scenarios

**Multiples at $106.56** (adjusted shares ~916M → adjusted market cap ~$97.6B):

| Metric | LTM/adj sh | Multiple | "Clean" version | Clean multiple |
|---|---|---|---|---|
| FRE | $4.68 | 22.8x | $4.40 (ex-reclass) | **24.2x** |
| TOE | $6.13 | 17.4x | — | — |
| ANI | $5.55 | 19.2x | $5.37 (less pref div) | **19.8x** |

**Scenarios** (FY27 earnings power, discounted to a 12-18 month view):

| | p | Driver | FV |
|---|---|---|---|
| **Bear** | **0.30** | AI-capex break and/or private-credit cycle turns properly. Organic FRE growth → 0; credit FPAUM shrinks; GA takes credit losses against a 5.4% equity layer; carry dries up; multiple to 14x on a flat $5.30 | **$74** |
| **Base** | **0.50** | Credit stays stalled but does not break; PE monetization cycle continues; organic FRE compounds ~14-16%; GA ROE stabilises ~9-10%; 19x on FY26E ANI-to-common $5.92 | **$112** |
| **Bull** | **0.20** | Credit scare fades, FSK stabilises, rate cuts reopen sponsor M&A, $143B dry powder + $72B of AUM-not-yet-paying-fees (~90bps ≈ $650M of embedded management fee) converts; 23x on FY27 $6.40 | **$147** |

**E[FV] = 0.30(74) + 0.50(112) + 0.20(147) = $107.6**

**Edge vs $106.56 spot = +1.0%. Essentially ZERO.**

This is the decisive number and it drives the ruling. **KKR was cheap at $83-92 in March-June. After a +5% sector day it is fairly priced.** The name is ownable, at a price that is not today's.

---

## 9. Four-idea frame

| Idea | Read |
|---|---|
| **Business quality** | **High.** 93% of AUM perpetual or ≥8y duration at inception; 42% perpetual; $143B dry powder; $72B AUM not yet paying fees at ~90bps; 84% of segment earnings from the "durable and recurring" portion; net cash; 'A' rated; 15y average debt at a 3% after-tax coupon. Genuinely a compounder. |
| **Valuation** | **Fair, not cheap.** 22.8x FRE (24.2x clean), 19.2x ANI. Half the 47x peak, but well above the 12-18x the group traded pre-2021. Zero edge at spot. |
| **Trajectory** | **Two legs rising, one falling.** PE and Real Assets compounding (mgmt fees +32%/+35%); Credit stalling (fees +8.8%, FPAUM organic +0.5%/6mo, perf fees −64%); Global Atlantic ROE compressing 11.6% → 9.8%. |
| **Honesty** | **Poor-to-mediocre — REVIEW_FLAG, not EXCLUDE.** Selective recast (Insurance recast; the FRE-flattering K-Series change not recast) is the tell. Growth headlines overstate organic by ~10-19pp; AUM headline includes $16B of bought AUM; per-share "records" exclude ~5% of look-through dilution. **All of it is disclosed somewhere in the document** — this is takeaway-vs-data divergence, not concealment. It does not disqualify the name; it disqualifies the headlines. Offsetting: the $207M clawback, the FSK fee waiver, and the GA funding-cost squeeze were all disclosed plainly and without spin. |

---

## 10. Catalyst map (probability × timing × magnitude)

| Catalyst | Date | p | Magnitude | Leading indicator |
|---|---|---|---|---|
| **Q3'26 print** (Q2 was 07-30; Q3 ≈ **2026-11-04/05**, VERIFY before acting) | ~Nov-26 | 1.0 | ±6-9% | Credit FPAUM net flow; first clean YoY on the reclassified FRE basis |
| FSK Q2'26 results (8-K item 2.02 due ~mid-Aug-26; last was 05-11) | Aug-26 | 1.0 | ∓3-6% on KKR | NAV/share vs $18.83; new non-accruals |
| Series D mandatory conversion | **by 2028-03-01** | 1.0 | ~2.3% share count, ~neutral to ANI/sh | fixed date, no surprise |
| Fed cuts reopening sponsor M&A → monetization + fundraising | H2'26-2027 | 0.45 | +10-20% | announced-but-unclosed sale list; transaction fees (Q2 $178M, **−10.7% YoY** — currently a negative) |
| Further KKR capital support to an affiliated credit vehicle | any | 0.30 | −5-10% | 8-K items 1.01/3.02 at FSK or K-Series credit |
| AI-capex break transmits to ABF/infra marks | by end-27 | 0.45 house call × ~0.6 transmission | −25-35% | GA credit impairments; ABF deployment pace; Helix fundraising |

**Nowcast-vs-tape:** the print is **behind us** (07-30), so the 2-week print blackout does **not** apply — that is the one genuinely favourable timing fact. The blocking issue is path (§6.3), not print risk.

---

## 11. RULING

**RISK_PREMIUM 4/10.** Not a reject: the cause is fully read, the ruling is de-rate not derailment, FRE per share is compounding mid-to-high-teens organically, the balance sheet is unlevered and 'A' rated, and the realization drought is genuinely refuted for PE. Not a clear (≥6): the de-rate is sector beta with KKR dead mid-pack (no identified mispricing), the credit leg of the de-rate thesis is *confirmed* by KKR's own flow data rather than refuted, Global Atlantic's ROE is compressing, the growth headlines are ~40-50% manufactured, and **E[FV] $107.6 vs $106.56 spot = +1.0pp edge — zero.**

This is fairly-paid risk, ownable per house doctrine (RP_FAIR), with the fairness *verified* and the tails bounded (no leverage, net cash, sleeve-capped). But it is only ownable at a price, and today's +5% sector melt-up is the wrong tick.

**Entry plan — gated, below the tape:**

| | Level | Size | Note |
|---|---|---|---|
| Band | **$88 – $95** | total **0.45% of $3.3M ≈ $15k** | requires ≥15% expected upside to E[FV] $107.6 → $93.6 ceiling |
| Tranche 1 | GTC limit **$95.00** | $5k (~53 sh) | 13w low is $87.66; stock closed $95.53 on 07-22 — band is live |
| Tranche 2 | GTC limit **$91.00** | $5k (~55 sh) | |
| Tranche 3 | GTC limit **$87.00** | $5k (~57 sh) | near the 13w low |

Sized at the **lower half** of the 1.2% ruled cap deliberately: the barbell instruction applies to red-team survivors, and this is a 4/10 that did not require one. **No premium selling** (taxable book, house rule). **Do not chase above $100.**

**Freezable call:**
> **KKR | 2026-11-05 | Bar: KKR's Credit & Liquid Strategies FEE-PAYING AUM organic net flow (New Capital Raised minus Distributions and Other) for the nine months ended 2026-09-30, per the Q3'26 earnings release FPAUM rollforward, is BELOW +$5.8B (i.e. below +2.0% of the 2025-12-31 base of $289.454B). | our_p = 0.70**

Rationale: H1'26 ran **+$1.38B (+0.5%)**. For this bar to FAIL, Q3 alone must deliver +$4.4B of net credit fee-paying flow — a sharp reacceleration in the exact franchise that is under sponsor rescue. This directly tests whether the credit stall is cyclical noise or the real thing, and it is checkable from one primary table.

**Kill triggers (dated, at entry):**
1. **FSK NAV/share < $17.00** at any quarter-end (Q2'26 due ~Aug-26; Q3 ~Nov-26) → KKR Credit marks still unwinding. **KILL.**
2. **Any further KKR capital support to an affiliated credit vehicle** beyond the $150M Series A preferred — new injection, expanded/extended fee waiver, or a second tender. **KILL.**
3. **Credit & Liquid Strategies fee-paying AUM declines sequentially** in any quarter. **KILL.**
4. **FRE/adj share ex the K-Series PE reclass grows < +10% YoY** in any quarter → the organic engine has decelerated below the base case. **KILL.**
5. **Global Atlantic Insurance Operating Earnings ex-realizations falls YoY for a 2nd consecutive quarter** → the annuity spread squeeze is structural, not transitional. **HALVE.**
6. **Close above $120 with the band unfilled** → log to the missed-entry ledger, do not chase.

---

## 12. Verification gaps — UNVERIFIABLE ≠ clean

1. **TOP GAP — KKR does not disclose data-centre / AI-capex exposure as a line item.** Not in the credit AUM breakdown ($143B leveraged credit / $91B ABF / $48B corporate private credit / $11B strategic / $38B liquid), not in the Real Assets detail, not in Global Atlantic's portfolio. I inferred exposure from the Helix Digital Infrastructure fundraise and the ABF concentration. **The single most decision-relevant number for the AI-BREAK conflict cannot be sourced.** Sizing reflects this.
2. **The reclass amount is disclosed as revenue, not as FRE.** KKR gives the $167,960k of Fee Related Performance Revenues but not the associated Fee Related Compensation, so my ex-reclass FRE (+18.0%) is a *lower* bound on the adjustment; the true organic figure is likely +18-23%.
3. **Sell-side estimate trajectory not obtained** (WebSearch budget exhausted session-wide). The de-rate/derailment call rests on *reported* per-share trajectory, which is stronger evidence than consensus anyway — but I could not confirm whether consensus FRE estimates fell during 2025.
4. **Q3'26 earnings date not confirmed from primary source** (inferred ~2026-11-04/05 from the Feb-05 / May-05 / Jul-30 cadence). Verify from the IR page or an 8-K before acting on the freezable call date.
5. **FSK Q2'26 results not yet filed** (last item-2.02 8-K was 2026-05-11). The NAV kill trigger cannot be evaluated until ~mid-Aug-26.
6. **Global Atlantic below-investment-grade share, CECL allowance trend, and portfolio credit quality** were not pulled from the 10-Q equity/investment notes — the ROE analysis is from the segment table only. This is the second-most important gap and would be the first thing to fix before upsizing.
7. **The "$300M KKR injection" news figure is partially refuted** ($150M preferred + $150M tender). Any downstream note carrying $300M as a single injection is wrong.
8. **Series D conversion rate band not read from the certificate of designations** — the ~20.7M share estimate assumes a ~$125 initial reference price. Directionally safe (the neutrality conclusion holds across the plausible band) but not verified.
