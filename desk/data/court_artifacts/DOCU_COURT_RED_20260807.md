# RED BENCH — DOCUSIGN, INC. (NASDAQ: DOCU)

**Court date 2026-08-07 · Fable tier · Posture: default-REJECT the LONG**
**Live price (IBKR, 2026-08-07): $57.39** (bid 57.13 / ask 58.00, +0.86% on day, YTD −16.1%, 52w range $40.16–$86.65 → **−33.8% from high**). Annualized IV 62.1%. 90d avg USD volume $220M.
Cohort context: `agentic_saas_exposed`, triage **7/10 DAMAGE-ARRIVING** with a disclosure-withdrawal flag ([SAAS_STRAGGLERS_REFUTABILITY_20260807.md](./SAAS_STRAGGLERS_REFUTABILITY_20260807.md)).

**Headline: the priority task refutes the flag that generated the referral.** I reconstructed billings exactly and it does not deteriorate. The withdrawal is a *verifiability* downgrade, not a concealment of an inflection. I still reject the long — on valuation and on eight quarters of zero IAM-driven acceleration — but the honesty thesis the triage was built on is dead, and I say so first because the bench that only prosecutes is worthless.

---

## PART 1 — PRIORITY TASK: BILLINGS RECONSTRUCTION

### 1.1 The formula, taken from the company's own words

Docusign's definition, printed verbatim in every earnings release through Q4 FY26:

> "We define billings as total revenues plus the change in our contract liabilities and refund liability less contract assets and unbilled accounts receivable in a given period."
> — [Q4 FY26 EX-99.1, Non-GAAP Financial Measures](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000017/q426ex-991er.htm)

Formalized: `Billings = Revenue + (CL+RL)_end − (CL+RL)_beg + (CA+UAR)_beg − (CA+UAR)_end + acquisition adjustments`

### 1.2 Validation — the reconstruction is exact, not approximate

I rebuilt the formula from the *inputs disclosed in the "Computation of billings" tables* of eight consecutive EX-99.1s and checked it against the printed Non-GAAP billings line. **Error = $0 on 8 of 8 quarters.**

| Quarter | Reconstructed | Printed Non-GAAP billings | Diff |
|---|---|---|---|
| Q1 FY25 | 709,538 | 709,538 | **0** |
| Q2 FY25 | 724,508 | 724,508 | **0** |
| Q3 FY25 | 752,307 | 752,307 | **0** |
| Q4 FY25 | 923,206 | 923,206 | **0** |
| Q1 FY26 | 739,612 | 739,612 | **0** |
| Q2 FY26 | 818,031 | 818,031 | **0** |
| Q3 FY26 | 829,459 | 829,459 | **0** |
| Q4 FY26 | 1,019,180 | 1,019,180 | **0** |

*($000. Sources: [Q1FY25](https://www.sec.gov/Archives/edgar/data/1261333/000126133324000083/q125ex-991er.htm) · [Q2FY25](https://www.sec.gov/Archives/edgar/data/1261333/000126133324000118/q225ex-991er.htm) · [Q3FY25](https://www.sec.gov/Archives/edgar/data/1261333/000126133324000148/q325ex-991er.htm) · [Q4FY25](https://www.sec.gov/Archives/edgar/data/1261333/000126133325000016/q425ex-991er.htm) · [Q1FY26](https://www.sec.gov/Archives/edgar/data/1261333/000126133325000073/q126ex-991er.htm) · [Q2FY26](https://www.sec.gov/Archives/edgar/data/1261333/000126133325000129/q226ex-991er.htm) · [Q3FY26](https://www.sec.gov/Archives/edgar/data/1261333/000126133325000146/q326ex-991er.htm) · [Q4FY26](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000017/q426ex-991er.htm))*

Because the formula reproduces the printed figure to the dollar, the Q1 FY27 reconstruction inherits that fidelity — subject only to two inputs the company stopped publishing (below).

### 1.3 The two inputs that went dark with the metric

The billings table was the *only* place Docusign disclosed the **refund liability** and **unbilled accounts receivable**. Both are now unobservable. I back them out at the last date they were visible:

- Refund liability @ 1/31/26 = 1,663,128 − (1,631,168 + 29,956) = **$2,004k**
- Unbilled AR @ 1/31/26 = 14,905 − 10,782 = **$4,123k**

*(Balance-sheet contract liabilities from the [Q1 FY27 10-Q](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000074/docu-20260430.htm): current 1,564,942 / 1,631,168; noncurrent 29,735 / 29,956; contract assets 8,024 / 10,782.)*

Both are ≤$4.2M against a ~$766M quarter. Full sensitivity:

| Assumption for the two dark inputs | Q1 FY27 billings | y/y vs $739,612 |
|---|---|---|
| carry forward 1/31/26 values (base case) | **$766,546** | **+3.64%** |
| both go to zero | $768,665 | +3.93% |
| refund liab. +$4M, unbilled AR → 0 | $774,665 | +4.74% |
| refund liab. → 0, unbilled AR +$5M | $759,665 | +2.71% |

**Reconstruction uncertainty is ±~1pp.** Q1 FY27 revenue of $830,235k is the audited-tagged figure ([10-Q Note 2](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000074/docu-20260430.htm)).

### 1.4 The reconstructed series — and why it exonerates the withdrawal

| Quarter | Billings ($000) | y/y | TTM billings | TTM y/y |
|---|---|---|---|---|
| Q1 FY25 | 709,538 | +5.15% | 2,945,606 | — |
| Q2 FY25 | 724,508 | +1.87% | 2,958,920 | — |
| Q3 FY25 | 752,307 | +8.74% | 3,019,421 | — |
| Q4 FY25 | 923,206 | +10.82% | 3,109,559 | +6.83% |
| Q1 FY26 | 739,612 | +4.24% | 3,139,633 | +6.59% |
| Q2 FY26 | 818,031 | +12.91% | 3,233,156 | +9.27% |
| Q3 FY26 | 829,459 | +10.26% | 3,310,308 | +9.63% |
| Q4 FY26 | 1,019,180 | +10.40% | 3,406,282 | +9.54% |
| **Q1 FY27 (RECONSTRUCTED)** | **766,546** | **+3.64%** | **3,433,216** | **+9.35%** |

**The prosecution's own reconstruction does not convict.** Three independent reads:

1. **Single quarter looks weak but is seasonal payback.** Q1 is structurally the weakest billings quarter every year (+5.15% / +4.24% / +3.64%). Q4 FY26 built deferred revenue +$188.5M q/q — an unusually large build against +$146.3M the prior Q4 — and Q1 FY27 gave back −$66.4M against −$29.6M. Rolling the pair together: Q4+Q1 billings **$1,785.7M vs $1,662.8M = +7.39%**, against the prior pair's **+7.79%**. A 0.4pp deceleration, not a cliff.
2. **TTM billings is stable at +9.3–9.6% across four quarters** — *above* the 8.0% ARR growth and *above* the 8.2% revenue growth it is supposed to lead.
3. **The unwithdrawable corroborator agrees.** Total contract liabilities (current + noncurrent), a GAAP balance-sheet line Docusign cannot retire: **$1,337.0M (4/30/24) → $1,447.3M (4/30/25, +8.25%) → $1,594.7M (4/30/26, +10.18%)**. Deferred revenue is growing *faster* than revenue. A company whose bookings were inflecting down would not show that.

> **FINDING — REFUTED.** The core honesty catch the referral was built on does not exist. The reconstructed series does **not** deteriorate at the point disclosure stopped; on a TTM and a deferred-revenue-balance basis it is flat-to-improving. Per the honesty-alpha boundary — grade on takeaway-vs-data divergence, not on datum withdrawal — the marketed takeaway ("durable revenue growth") is **CONSISTENT** with the reconstructed data. **DOCU is not a masking case on billings.**

### 1.5 Dating the retirement steps precisely

| Date | Filing | What changed |
|---|---|---|
| 2025-12-04 | [Q3 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133325000146/q326ex-991er.htm) | Billings **reported** ($829.5M) **and guided** (Q4 $992–1,002M; FY26 $3,379–3,389M). Normal. |
| **2026-03-17** | [Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000017/q426ex-991er.htm) | Billings **reported** for the last time ($1,019.2M Q4 / $3,406.3M FY26, +10%). Billings **guidance dropped**; replaced by a newly-introduced **"Annual recurring revenue year-over-year growth rate"** guide of 8.25–8.75%. Explicit written notice: *"Beginning in the first fiscal quarter of 2027, we will no longer report or guide to billings."* Same release introduces **ARR** as a metric for the first time ($3,272M FY26 / $3,030M FY25). |
| 2026-03-18 | [FY26 10-K](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000021/docu-20260131.htm) | Same notice repeated in Non-GAAP definitions. Also: *"In fiscal 2027, we plan to distinguish between enterprise, commercial mid-market and SMB customers on the basis of annual recurring revenue"* — a third definitional change queued. |
| **2026-06-04** | [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000072/q127ex-991er.htm) | The word **"billings" appears zero times**. Also: subscription-revenue and professional-services **guidance lines deleted**; the income-statement lines **combined** (*"Effective in the first quarter of fiscal 2027, we changed the presentation of revenue... to combine the financial statement line items labeled 'Subscription revenue' and 'Professional services and other revenue'"* — 10-Q Note 1). No quarterly ARR dollar figure; only IAM as a **percentage of an undisclosed denominator**. |

**Verdict on the sequencing.** The retirement was **pre-announced in writing on 2026-03-17**, six weeks into the quarter that would have printed the weakest Q1 billings in three years — and eight weeks before that quarter closed. That is uncomfortable timing. But it is disclosed timing, it is a metric the company had reported for eight years, and the withdrawn quarter is **reconstructible to ±1pp from the balance sheet**, as proven above. Absent a deterioration to conceal, the sequencing is suggestive of nothing. **CONSISTENT, not REFUTED-adverse.**

### 1.6 What the withdrawal actually cost — the real, narrower finding

Docusign swapped:

- **Billings** — quarterly, eight-year history, **fully reconstructible from GAAP balance-sheet lines to $0 error**, formula published by the company; for

- **ARR** — **annual** (reported once, at FY-end), **introduced in the same release that retired billings**, with exactly **one** back-year comparative, management-defined, **reconcilable to no financial-statement line**, and computed on an allocation methodology the company controls: *"we allocate the support contract value to each product offering based on its proportional share of the total contract value"* (10-K, Non-GAAP definitions).

> **FINDING — the masking channel is VERIFIABILITY FREQUENCY, not level.** Outside verification of Docusign's forward growth dropped from 4×/year on a reconstructible metric to 1×/year on a non-reconstructible one. Our reconstruction closes the gap today; it **decays over time**, because the refund liability and unbilled AR are now unobservable and will drift silently. Reconstruction error is ±1pp now and widens each quarter.

**Mechanism for the knowledge graph:** masking channel = *metric substitution toward non-reconstructibility* (not figure suppression) × signal channel = *deferred-revenue roll-forward in the 10-Q balance sheet* × signal-to-price latency = **~0 days for a reconstructor** (10-Q lands 1 day after the release), **indefinite for a screen reader** (requires the retired formula plus two now-dark inputs). This is an **anti-masking finding**: the expected concealment is absent, and the absence is the result.

---

## PART 2 — CLAIM LEDGER

### 2.1 IAM platform adoption — dated numbers versus marketing

| # | Claim | Source | Method | Result | Verdict |
|---|---|---|---|---|---|
| 1 | "IAM represented 12.6% of our total ARR as of April 30, 2026, compared to 10.8% as of January 31, 2026" | [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000072/q127ex-991er.htm) | Read primary | Stated as printed | **VERIFIED (as a mix ratio)** |
| 2 | "In 2026, customers using IAM represented over $350 million in ARR" | [Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000017/q426ex-991er.htm) | 10.8% × $3,272M = $353.4M | Ties exactly | **VERIFIED** |
| 3 | IAM adoption is driving growth | CEO framing, Q1 FY27 & Q4 FY26 | Total-revenue growth across the entire IAM life | FY24 +9.8% → FY25 +7.8% → **FY26 +8.2%** → FY27 guide **+8.7% reported / +7.4% cc**. IAM went **2.3% → 10.8% → 12.6% of ARR** across that span with **no acceleration whatsoever** | **REFUTED as a growth driver** |
| 4 | Legacy (non-IAM) ARR direction | Derived from #2 + ARR dollars | Non-IAM ARR: 1/31/25 $3,030M × 97.7% = **$2,960.3M**; 1/31/26 $3,272M × 89.2% = **$2,918.6M** → **−$41.7M, −1.41% y/y** | 117% of total ARR growth came from IAM; the non-IAM balance shrank | **VERIFIED arithmetically — but see rebuttal** |
| 5 | Docusign's ARR allocation reallocates a bundled customer's *entire* contract value to IAM | 10-K Non-GAAP definitions | Read primary | Confirmed | **VERIFIED** |
| 6 | IAM customer count | 10-K (1/31/26): *"more than 25,000 customers are on IAM today."* Q3 FY26 release (10/31/25): *"more than 25,000 customers."* Q1 FY27 release (4/30/26) CEO quote: *"**40,000 customers** investing in our rapidly expanding roadmap"* | Cross-venue consistency | Count is flat at ">25,000" for two consecutive quarters, then jumps to 40,000 (+60% in one quarter) **under changed wording that omits "on IAM"**. Transcript/prepared remarks not obtainable this session (web-search budget exhausted; IR page 404) | **UNVERIFIABLE — definition-drift flag, not a refutation** |
| 7 | ARR per IAM customer | Derived, #1/#2/#6 | 1/31/26: $353.4M / ~25,000 ≈ **$14.1k**. 4/30/26: 12.6% × est. ARR ~$3,330M ≈ $420M / 40,000 ≈ **$10.5k** | If both counts are the same metric, ARR/IAM customer fell ~25% in one quarter — consistent with migrating small self-serve accounts onto IAM SKUs | **CONSISTENT with migration-mix, contingent on #6** |

**Blue-team rebuttal I accept on #4:** because a bundled customer's *whole* contract reallocates to IAM (#5), "non-IAM ARR declining" is partly a definitional artifact of migration and does **not** prove same-customer legacy erosion. The defensible surviving version is #3, which uses only audited GAAP revenue: **eight quarters and 12.6% of ARR into the IAM transition, Docusign has produced zero measurable growth acceleration.** IAM is a repackaging with no price uplift and no attach uplift visible at the total-company line. Everything above that in the press releases — *"clear market leadership as the agreement system of action," "rapidly expanding," "AI-native"* — is marketing on top of a flat 8% base.

### 2.2 Churn / net dollar retention

| # | Claim | Source | Method | Result | Verdict |
|---|---|---|---|---|---|
| 8 | NDR / dollar-based net retention trend | FY26 10-K, FY25 10-K, all eight releases | Full-text search for "net retention" / "dollar-based" / "retention rate" | **Zero hits.** Docusign has not disclosed a net-retention metric in either 10-K or in any FY25–FY27 earnings release | **UNVERIFIABLE — and UNVERIFIABLE IS NOT CLEAN** |
| 9 | Enterprise/commercial customer counts | [FY26 10-K](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000021/docu-20260131.htm), [FY25 10-K](https://www.sec.gov/Archives/edgar/data/1261333/000126133325000024/docu-20250131.htm) | Read primary | Direct enterprise + commercial: 242,000 (1/31/24) → 260,000 (1/31/25) → **280,000 (1/31/26, +7.7%)**. Total customers 1.5M → 1.7M → 1.8M | **VERIFIED — stable** |
| 10 | Customers with >$300,000 annualized contract value | Both 10-Ks | Read primary | **1,060 → 1,131 (+6.7%) → 1,205 (+6.5%)** | **VERIFIED — decidedly NOT decaying** |
| 11 | Remaining performance obligation | XBRL `RevenueRemainingPerformanceObligation`, 10-Q/10-K | Pulled full series | $2.2B (4/30/24) → $2.3B (10/31/24) → $2.4B (1/31/25) → $2.3B for **five of the last six quarters**, $2.3B at 4/30/26. 58% due within 12 months | **CONSISTENT but LOW-RESOLUTION** — rounded to $0.1B (±4.3% on the base), so a 9% revenue grower can look flat. Directionally soft; not a usable gate |

**The item that hurts the bear case most is #10.** The agentic-SaaS narrative says AI agents destroy per-seat enterprise contracts first. Docusign's >$300k ACV cohort grew +6.7% then +6.5% — flat, positive, and in line with total ARR. The narrative predicts decay at exactly the place where none is present.

**The item that hurts the company most is #8.** Docusign is the only name in the eleven-name cohort that discloses **no retention metric at all**. GTLB gives DBNRR, PATH gives DBNR, TWLO gives DBNE, FRSH gives cc NDR, BRZE gives DBNR, ESTC gives NER. Docusign gives nothing, and the one metric it did give quarterly (billings) it has now retired. On disclosure *breadth* against its own peer set, Docusign is last.

### 2.3 Margin and free-cash-flow quality

| # | Claim | Source | Method | Result | Verdict |
|---|---|---|---|---|---|
| 12 | "Free cash flow was $289.4 million compared to $227.8 million" (+27%) | Q1 FY27 EX-99.1 | Tie to 10-Q cash flow: OCF $321,688 − capex $32,253 = $289,435 | Ties | **VERIFIED** |
| 13 | FCF growth of +27% reflects business strength | Company framing | Decompose the 10-Q cash-flow statement | OCF rose $70.2M y/y **while the contract-liability drag worsened** (−$65,553 vs −$34,240, a $31.3M *bigger* headwind). The beat came from **accounts receivable collapsing $516.4M → $300.7M** and accrued compensation −$88.4M. This is collections and comp timing, **not** billings quality | **MISLEADING EMPHASIS — CONSISTENT but not attributable to demand** |
| 14 | Gross margin | Q1 FY27 EX-99.1 | Read primary | GAAP GM **79.4%, flat y/y**. **Non-GAAP GM 81.5% vs 82.3% — down 80bps.** FY26 non-GAAP GM 82.0% vs 82.2% | **VERIFIED — mild adverse.** A company whose entire forward story is AI inference is seeing non-GAAP gross margin erode, not expand |
| 15 | GAAP profitability inflection | Q1 FY27 10-Q | Read primary | GAAP operating income **$111.3M vs $60.3M, +85%** on 13.4% margin. Genuine. But GAAP net income only **$78.2M vs $72.1M (+8.5%)** because the tax provision went **$1.7M → $39.6M (33.6% ETR)** — the FY25 $819.9M valuation-allowance release is fully lapped and Docusign is now a taxpayer on the P&L | **VERIFIED — the GAAP EPS optics are worse than the operating optics** |
| 16 | Stock-based compensation | Q4 FY26 EX-99.1 + Q1 FY27 10-Q | Sum the SBC lines | FY26 SBC **$622.3M = 19.3% of revenue**; FY25 $610.3M. Q1 FY27 $141.4M = 17.0% of revenue. **TTM SBC ≈ $618M.** Unrecognized RSU cost $1.0B over 2.3 years | **VERIFIED — this is the number the FCF headline suppresses** |

### 2.4 Buyback versus dilution — the strongest bull fact, verified

| # | Claim | Source | Method | Result | Verdict |
|---|---|---|---|---|---|
| 17 | "Repurchases of common stock were $317.5 million... record share buybacks" | Q1 FY27 EX-99.1 | XBRL `PaymentsForRepurchaseOfCommonStock` Q1 series | $0 (FY23) → $40.5M → $149.1M → $183.4M → **$317.5M**. Monotonic, and a Q1 record | **VERIFIED** |
| 18 | Authorization | Q1 FY27 10-Q | Read primary | Board raised authorization by **$2.0B in March 2026** to $4.5B aggregate; **$2.4B remaining** as of 4/30/26 = **21.9% of market cap** | **VERIFIED** |
| 19 | Share count is actually shrinking | DEI `EntityCommonStockSharesOutstanding` | Cover-page series | **202.49M (2/28/25) → 194.43M (2/28/26) → 190.94M (5/29/26).** −4.0% in FY26, **−1.8% in a single quarter** | **VERIFIED — real, not optical** |
| 20 | "Non-GAAP diluted EPS $1.09 vs $0.90" (+21%) | Q1 FY27 EX-99.1 | Decompose | Non-GAAP net income 1.09 × 196.5 = **$214.2M** vs 0.90 × 212.8 = **$191.5M = +11.9%.** **~9 of the 21 points of EPS growth are share count, not earnings** | **CONSISTENT but flattered** |
| 21 | Buyback is net-accretive after dilution | Derived | FY26: ~$1.0B repurchased at ~$75 avg ≈ 13.3M shares gross; net reduction 8.06M → **~5.3M shares of SBC issuance absorbed, net/gross ≈ 61%** | ~39% of every buyback dollar merely neutralizes SBC | **VERIFIED — accretive, but only 61c on the dollar** |
| 22 | Diluted share count fell 213M → 196M (−7.7%) | Q1 FY27 10-Q EPS note | Read the antidilution table | **13,151k RSUs were excluded as antidilutive this quarter vs 1,077k a year ago.** A meaningful part of the *diluted* count decline is a lower share price making RSUs antidilutive — a mechanical artifact of the drawdown, not capital return | **MISLEADING if read as buyback alone** |

### 2.5 Valuation — computed off the live quote, with cap structure pulled first

Cap structure check (per the standing rule): [Q1 FY27 10-Q](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000074/docu-20260430.htm) balance sheet — total liabilities $2,164,257k, of which contract liabilities $1,594,677k, operating leases $183,333k, deferred tax $24,205k, other $54,495k, AP $23,970k, accrued $283,577k. **No debt line. No converts. No preferred. No warrants.** Revolving facility of up to $750M is **undrawn**.

- Shares outstanding **190,944,608** (10-Q cover, 5/29/26) × **$57.39** = **market cap $10,958M**
- Cash + investments = 548.027 + 266.152 + 209.897 = **$1,024M** → **EV = $9,934M**

| Metric | Value | Multiple |
|---|---|---|
| FY27 revenue guide (mid) | $3,496M | **EV/S 2.84×** |
| FY27 non-GAAP operating income (30.75% mid) | $1,075M | **EV/EBIT(non-GAAP) 9.24×** |
| TTM free cash flow | $1,120M | **EV/FCF 8.87× — 11.3% yield** |
| **TTM FCF less TTM SBC ($618M)** | **$502M** | **EV/(FCF−SBC) 19.8× — 5.05% yield** |
| Growth attached to it | FY27 rev **+7.4% cc**, ARR **+8.5%** | **SBC-adjusted PEG ≈ 2.6×** |

> **FINDING.** The bull case is built on "8.9× free cash flow." That multiple is an SBC illusion: Docusign pays ~19% of revenue in stock and buys back ~61 cents of net share reduction per dollar spent. On the honest denominator the name trades at **~20× owner earnings for 7–8% growth**. That is not a dislocated 34%-drawdown value name; it is a fairly-priced low-growth compounder that de-rated from an unfair multiple to roughly a fair one.

---

## PART 3 — MODE B: FIRST-PRINCIPLES, PROMOTER FRAMING STRIPPED

Leading with the disconfirming pass, as doctrine requires, and deliberately *not* asking the question the pitch asks.

**B1. Is Docusign actually the cohort's per-seat victim?** Partly not. Docusign bills on **seats plus an envelope allowance** — a hybrid. An agent that negotiates a contract still has to get it **signed by a human with legal authority**, and the envelope still gets sent. Agentic workflows plausibly *increase* envelope volume while compressing seat count. The cohort tag treats it as a pure seat name; the billing model says otherwise. **The narrative is weaker on DOCU than the cohort tag implies.**

**B2. If agents were eating enterprise seats, where would it show first?** In the >$300k ACV cohort and in large-customer count. Both are **growing +6.5–7.7%** (claims #9, #10). The predicted damage is absent at the predicted location. **Disconfirming evidence found, and it disconfirms the bear.**

**B3. What is the actual disease, if not agents?** Docusign grows 8% and has grown 8% for three years, through IAM's entire launch-to-12.6%-of-ARR arc. The disease is **market saturation of e-signature**, disclosed and old news, priced since the 2022 de-rate. It has nothing to do with AI agents. The cohort screen sorted DOCU into an AI-narrative bucket on a drawdown that is a **multiple compression on an already-known 8% grower**, not a fundamental inflection.

**B4. Where could a real lie hide, given they retired the metric?** Exactly where I looked — and it is not there. The strongest test available (an exact reconstruction, validated 8/8 at $0 error) says billings did not break. **Absence of the expected masking is itself the finding.**

**B5. What is genuinely under-covered?** That Docusign now discloses **less than any peer in its cohort** and has queued a **third** definitional change (customer segmentation) for FY27. Not fraud; a governance-quality drift that raises the discount rate a serious owner should apply, and that makes every future quarter harder to falsify. **Encode as a standing disclosure-quality demerit, not a thesis.**

**B6. Discovery state.** DOCU carries ~$220M/day of dollar volume, full sell-side coverage, and 62% IV. Nothing here is undiscovered. Any edge would have to be a *reconstruction* edge — and my reconstruction says the consensus worry is wrong, which is a reason not to be short, not a reason to be long.

---

## PART 4 — VERDICT

### STRONGEST KILL

**Eight quarters and 12.6% of ARR into the IAM transition, Docusign has produced zero measurable growth acceleration — and the market is being asked to pay ~20× owner earnings for the acceleration to arrive.** Revenue growth ran +9.8% (FY24) → +7.8% (FY25) → +8.2% (FY26) → **+7.4% cc guided (FY27)** while IAM went from nonexistent to 2.3% to 10.8% to 12.6% of ARR ([Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000017/q426ex-991er.htm), [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000072/q127ex-991er.htm)). Because Docusign's own methodology reallocates a bundled customer's **entire** contract value to IAM, the rising IAM percentage is fully explained by migration with **no price uplift** — the total line proves it, since a genuine uplift would have shown up there. Strip SBC of $618M from $1,120M of TTM FCF and the name trades at **19.8× / 5.05% yield on 7–8% growth (PEG ~2.6)** at a $9.93B EV. That is not a dislocation; it is a de-rate that has landed near fair. **The long has no edge left in it.**

### KILLS I ATTEMPTED AND WITHDREW — reported faithfully

1. **"Billings was withdrawn to hide an inflection." REFUTED by my own reconstruction.** The formula reproduces eight quarters at $0 error; the Q1 FY27 figure is +3.64% y/y but is seasonal payback from an outsized Q4 build. TTM billings +9.35%, Q4+Q1 rolling +7.39% vs +7.79%, and total contract liabilities **+10.18% y/y** — faster than revenue. **This was the referral's core thesis and it is dead.** The withdrawal degrades verification *frequency*, not truth.
2. **"Agents are eating the enterprise seat base." REFUTED.** >$300k ACV customers +6.7% then +6.5%; direct enterprise/commercial 260k → 280k. The narrative's predicted damage is absent at its predicted location.
3. **"Non-IAM ARR is in absolute decline (−1.4%)." WITHDRAWN to CONSISTENT.** Arithmetically true from disclosed figures, but the company's stated ARR allocation methodology makes it partly a definitional artifact of migration. I will not stake a verdict on it.

### WHAT WOULD CHANGE MY MIND

**Toward LONG (I would flip on any two of):**
1. **Reconstructed Q2 FY27 billings.** I can compute it from the Q2 10-Q within one day of the print. Gate: **H1 FY27 (Q1+Q2) reconstructed billings vs H1 FY26's $1,557,643k — above +7.5% and the growth base is intact and better than the multiple implies.**
2. **Total contract liabilities at 7/31/26 growing >+8% y/y vs $1,463.4M** — the one growth signal management cannot retire.
3. Docusign **restores a retention metric** (any NDR/DBNR) or resumes a quarterly ARR dollar. Disclosure re-expansion at a company that just contracted it is a strong governance signal and would remove my discount-rate demerit.
4. Buyback sustains ≥$300M/quarter with net share count falling ≥6% annualized while the stock is below $60 — at 21.9% of cap authorized and ~$1.1B of FCF, this alone can carry a 12–14% total return on 8% growth.
5. A **quantified, defined** IAM metric — IAM ARR in dollars with a customer count on a stable definition — showing ARR-per-IAM-customer rising rather than falling. That would convert claim #3 from "repackaging" to "uplift."

**Toward SHORT (I would need):**
1. H1 FY27 reconstructed billings **below +4%** *and* contract liabilities y/y decelerating below revenue growth — two quarters, not one, because Q1 alone is seasonal.
2. FY27 ARR growth guidance cut below 8.25%, or the >$300k ACV customer count printing a decline at FY27 year-end.
3. The "40,000 IAM customers" figure proving to be a redefinition of the ">25,000" series — which would convert claim #6 from UNVERIFIABLE to a live metric-inflation finding.

**Standing caveat:** the reconstruction's power **decays**. Refund liability and unbilled AR are now unobservable and will drift. Error is ±1pp today; assume ±2pp by FY28. Re-anchor whenever a figure becomes visible again.

### CONVICTION: **7 / 10**

High confidence (9/10) in the *analytical* findings: the reconstruction validated 8/8 at zero error, and the honesty thesis is definitively refuted. Moderate confidence (6/10) in the *sizing* conclusion, because the buyback math is genuinely strong — $2.4B of authorization against a $10.96B cap, funded by $1.1B of real FCF, at 20× owner earnings with no debt — and that is the single fact most capable of making this rejection wrong.

### RECOMMEND: **REJECT the long — EDGE-DEAD, not impaired.**

Classification: **RP_FAIR / no overlay.** Not a short: the balance sheet is clean, the customer base is not decaying, the reconstruction exonerates the disclosure flag, and 21.9% of the cap is authorized for repurchase — the tail is bounded and the carry is real. Not a long: an 8% grower at ~20× SBC-adjusted FCF with the sector's thinnest disclosure and eight quarters of AI-platform effort that produced no acceleration offers no edge over the beta it would consume.

**Downgrade the triage tag from DAMAGE-ARRIVING (7/10) to DAMAGE-ABSENT / DISCLOSURE-DEGRADED.** The cohort membership is a screening artifact: DOCU's drawdown is a multiple de-rate on an honestly-disclosed saturation problem that predates the agentic narrative by three years.

**Gate for re-examination: Q2 FY27 print, est. 2026-09-03** (prior year 2025-09-04; not yet company-announced). **Action at the gate: reconstruct H1 FY27 billings from the Q2 10-Q within one day and test against the +7.5% threshold.** No fireable catalyst before then — this is dead money in the interim, which is itself a reason not to hold it.

---

*Every figure above is read from the SEC-filed primary document; prices are a live IBKR snapshot taken 2026-08-07. Reconstruction methodology, validation, and sensitivity are shown in full in Part 1 so this verdict can be attacked on its arithmetic.*
