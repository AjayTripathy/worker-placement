# Brick-and-Mortar Retail Distress Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T08:32:22.892489Z — cutoff 2026-05-16_

## Methodology

Seven names spanning distressed-narrative department stores (KSS Kohl's, M Macy's, JWN Nordstrom), apparel (GPS Gap), discount post-Ch.11 (BIG Big Lots), and retail-resilient controls (TJX off-price, COST membership warehouse). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch, no shared context. Subagent workflow includes checkpointing.

Retail-specific calibration emphasis: **comp-store-sales claim test** (Heuristic 9) + **going-concern / form-15 fingerprints** (Heuristic 10, applied hard). Retail-distress names often have multi-year transformation plans where announced milestones diverge from realized progress.

**Cohort caveat:** retail-distress is slow-bleed. Even validated Truth_signals can grind sideways for years. Emissions should be paired with tighter exit rules than the default 12-month falsification window.

Forward-bet emission uses the shared v2 emitter.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | BIG | Big Lots, Inc. | 7 | 1 | 0 | 2 | 3 | 1 | 2.17 |
| 2 | KSS | Kohl's Corporation | 8 | 4 | 2 | 1 | 1 | 0 | 0.88 |
| 3 | M | Macy's, Inc. | 8 | 4 | 4 | 0 | 0 | 0 | 0.50 |
| 4 | JWN | Nordstrom, Inc. | 7 | 6 | 1 | 0 | 0 | 0 | 0.14 |
| 5 | GPS | The Gap, Inc. | 7 | 6 | 1 | 0 | 0 | 0 | 0.14 |
| 6 | TJX | The TJX Companies, Inc. | 6 | 6 | 0 | 0 | 0 | 0 | 0.00 |
| 7 | COST | Costco Wholesale Corporation | 7 | 7 | 0 | 0 | 0 | 0 | 0.00 |

## Per-ticker findings

### BIG — Big Lots, Inc.

- **Filing analyzed:** `0000768835-24-000026_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=1, MODERATE=0, SEVERE=2, RED_FLAG=3, UNVERIFIABLE=1
- **Composite severity:** 2.17

#### 🔴 RED_FLAG_NEGATIVE claims
- **C1** — Net sales -13.6%, comp -13.5%, operating loss $387.4M, diluted LPS ($16.53), liquidity down to $281M, $148.6M impairments + $146M deferred tax valuation allowance
  - M-check: `edgar_fts: 'going concern' cik=BIG 2024-04-01 to 2026-05-16; 'Big Lots' 8-K cluster cik=BIG 2024-06-01 to 2026-05-16`
  - M-value: 9 hits for 'going concern' at BIG including 10-Q (2024-06-13) and 10-Q (2024-09-12); 117 hits 'Big Lots' in 8-K post-cutoff include Monthly Operating Reports (MOR) — debtor-in-possession filings; ticker became BIGGQ (Q-suffix = bankruptcy); Asset Purchase Agreement 8-K on 2024-09-10; 'FORMER BL STOR
  - Interpretation: BIG filed Chapter 11 in September 2024 (5 months after the 10-K). The 10-K's distress disclosures were directionally correct but understated the imminent collapse. The cohort prompt's note that BIG already emerged from Ch.11 in 2024 via Nexus is contradicted by the M-side data — BIG's actual Ch.11 was filed in Sep 2024, and the post-cutoff state through May 2026 is debtor monthly-operating-reports
- **C2** — 1,392 stores at FY23 year-end; only 33 net closures in 2023; plan to open ~3 new stores in 2024; 'real estate team has identified more than 500 markets' for future growth; long lease portfolio with 17
  - M-check: `edgar_fts: 'Big Lots' cik=SPG (0001063761); cik=MAC (0000912242); 'store closures' cik=BIG`
  - M-value: SPG 0 hits, MAC 0 hits (consistent with BIG being primarily strip-center / rural — not a hard contradiction under Heuristic 7). 'store closures' 7 hits at BIG including DIP term loan and DIP ABL agreements (8-K 2024-09-10) — Ch.11 store-closure motion documents.
  - Interpretation: The 'identify 500 markets for new store growth' marketing-tier claim is FALSIFIED by subsequent events (Ch.11 filing, DIP financing, eventual liquidation/asset sale). Heuristic 11 (planned vs operational store-count trajectory) maxes out as RED: announced ~3 new stores in 2024 vs actual mass closures via Ch.11 lease rejection. Mall-REIT counterparty silence is expected (BIG is non-mall) so not con
- **C4** — April 18, 2024 First Amendment to 2022 Credit Agreement: permitted new Term Loan Facility, expanded collateral to non-working-capital + mortgage on HQ, added Term Pushdown Reserve, increased rate spre
  - M-check: `edgar_fts: 'Nexus Capital' no-cik 2024-01-01 to 2026-05-16; 'Big Lots' 8-K no-cik 2024-08-01 to 2026-05-16`
  - M-value: Nexus Capital appears in BIG 8-Ks on 2024-09-10 and 2024-12-27 — Nexus was named in BIG's Ch.11 process, NOT as a clean post-emergence acquirer. 106 hits 'Big Lots' in 8-Ks post-Aug 2024 dominated by Monthly Operating Reports under BIGGQ ticker (bankruptcy-court reports). DIP term loan and DIP ABL a
  - Interpretation: The April 2024 ABL Amendment is best read as a stopgap that bought ~4-5 months before Ch.11 filing on or about 2024-09-10. The cohort prompt's framing ('emerged from Ch.11 in 2024 via Nexus Capital') misstates the chronology: BIG ENTERED Ch.11 in Sep 2024 and was still operating as a debtor (BIGGQ filing MORs) through at least Oct 2025 per the index. Distress trajectory is RED-confirmed. Heuristic
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C5** — Project Springboard announced target: >$200M operating-income improvement (40% from reduced COGS, 40% from other GM, 20% from SG&A). Management 'confident' significant savings will be realized in 2024
  - Interpretation: Heuristic 3 stage-ladder fail: announced $200M operating-income improvement target vs operating loss widening into Ch.11. The plan was almost entirely aspirational and was not even discussed in court filings after Sep 2024. SEVERE — not RED because the claim is a forward target, not a fact-claim about completed operations.
- **C6** — Forward guidance: 'We expect to return to comp sales growth in 2024 and to significantly improve our gross margin in 2024 compared to 2023.'
  - Interpretation: Heuristic 9 (comp-store-sales test) FAILS hard. Forward inflection promise (comp growth in 2024) is unsupported by any operating data and is shortly followed by going-concern, then Ch.11. SEVERE-leaning-RED, scored SEVERE because the claim is a guidance/forecast not an actual-results statement.

### KSS — Kohl's Corporation

- **Filing analyzed:** `0001193125-26-115982_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=4, MODERATE=2, SEVERE=1, RED_FLAG=1, UNVERIFIABLE=0
- **Composite severity:** 0.88

#### 🔴 RED_FLAG_NEGATIVE claims
- **kss_008_management_turnover** — Buchanan joined as CEO Jan 15 2025 replacing Kingsbury. 10-K characterizes this as orderly leadership transition.
  - M-check: `Self-corroboration via 8-K filings: 'Buchanan' appears in 8 KSS 8-K filings. CRITICAL FINDING in 2025-05-01 8-K (accession 0001193125-25-109074): 'On April 30, 2025, the Board of Directors of the Company terminated J. Ashley Buchanan as the Company's Chief Executive Officer for Cause (as defined in the Executive Compensation Agreement dated as of January 15, 2025)...' — Buchanan was TERMINATED FOR CAUSE on April 30, 2025, ~3.5 months after joining. The 10-K filed March 19, 2026 (after this event) lists Buchanan's offer letter, ECA, and RSU agreements as exhibits but the prompt-summary 10-K narrative I sliced did not surface 'for cause' termination disclosure. Additional finding: dividend cut from $0.50/qtr to $0.125/qtr (75% reduction) announced March 11, 2025. Activist Macellum Badger relationship goes back to 2021, with formal Cooperation Agreement Feb 2023 (21 hits across KSS filings).`
  - M-value: Buchanan: 8 self-mentions including the for-cause termination 8-K dated May 1, 2025. Macellum: 21 hits. Dividend: cut 75% in March 2025.
  - Interpretation: RED — for-cause CEO termination ~3.5 months into tenure is an extremely high-severity governance event. The pattern (activist 2021 -> Cooperation 2023 -> Kingsbury CEO -> Buchanan CEO Jan 2025 -> for-cause termination April 2025 + 75% dividend cut) is consistent with a deeply unstable governance and strategic-direction situation. Combined with credit downgrades (claim 3), the cluster of distress m
#### 🟠 SEVERE_UNDERDELIVERY claims
- **kss_003_credit_rating_downgrades** — Moody's downgraded corporate credit Ba3->B2 in 2025; senior unsecured B1->B3. S&P BB- -> B+. 10.000% senior secured notes due 2030 issued in 2025 ($360M). 3.375% notes due 2031 coupon stepped up 175bp
  - Interpretation: SEVE — A 10.000% coupon on senior SECURED paper is a distressed-grade pricing signal. The cumulative 175bps step-up on the 3.375% 2031 notes (coupon adjustment provision tied to ratings) means the company is structurally absorbing higher interest cost for years. Three rating agencies all downgraded; Moody's senior unsecured at B3 is deep in single-B territory. Layer 3 Rule 10: while not a going-co
#### 🟡 MODERATE_UNDERDELIVERY claims
- **kss_002_comp_sales_decline** — Net sales decreased 4.0% to $14.775B in fiscal 2025; transaction volume down ~4%; all lines of business except Accessories declined.
  - Interpretation: MODE — comp-sales decline is honestly disclosed in financial-statement notes (-4.0% revenue, -4% transactions). Counterparty 10-Ks corroborate that Kohl's wholesale-channel importance to top apparel brands has faded over time. The MD&A narrative ('strong inventory management,' 'gross margin +34bps')
- **kss_006_lease_portfolio** — Operating lease ROU $2.338B, operating lease liabilities $2.744B; finance leases + financing obligations $2.450B. Combined ~$5.2B lease/financing liability vs $4.048B shareholders equity at Jan 31 202
  - Interpretation: MODE — the lease/financing-obligation footprint is large relative to equity and constitutes a real fixed-cost overhang. The disclosure itself is complete (balance sheet + notes). Severity MODE because the magnitude is a structural risk; not SEVE because Kohl's owns a meaningful portion of its store 

### M — Macy's, Inc.

- **Filing analyzed:** `0001628280-26-021721_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=4, MODERATE=4, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.50

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — Capital structure: ~$6.0B operating leases primarily due after 2030; $2.4B long-term debt; senior unsecured notes $2,441M outstanding maturing 2027-2043; credit ratings split-rated (Moody's Ba1 / S&P 
  - Interpretation: Layer 3 Rule 10 distress markers NOT triggered (no GC, no 25-NSE, no Form 15). However, the structural picture is mixed: two of three rating agencies hold sub-IG (Ba1/BB+) while M targets 'investment-grade credit metrics' as a capital-allocation goal — claim partially contradicted by current rating 
- **C5** — ABL Credit Facility REDUCED from $3,000M to $2,100M on April 9, 2025; maturity extended to April 2030; $0 outstanding. FY2025 debt actions: issued $500M of 7.375% senior unsecured notes due 2033; rede
  - Interpretation: Two readings: (a) Bull — M proactively termed out at favorable maturity (2033 notes, 2030 ABL), ABL undrawn, no covenant issues — clean liability management; (b) Bear — 7.375% coupon on 2033 notes is structurally high (well above pre-2022 cost of capital); ABL reduced by $900M (30%) signals lender-s
- **C6** — Macy's operates as a major department-store carrier of national apparel brands with $21.8B net sales and ~$3.6B merchandise purchase obligations (majority <1 year). By scale, M should appear as a mate
  - Interpretation: Calibration Heuristic 7 reading: ABSENCE across 4 major apparel suppliers indicates M is below the 'major-customer' disclosure threshold (typically 10% of supplier revenue) for HBI/VFC/LEVI/TPR. This is INFORMATIVE in two directions: (a) limited supplier-side concentration risk — M isn't propping up
- **C8** — FY2025 real estate gains $48M (down from $144M FY2024 and $61M FY2023); $107M net proceeds from asset dispositions. Impairment+restructuring $230M (vs $171M FY2024, $1,027M FY2023). Bold New Chapter i
  - Interpretation: Heuristic 3 stage-ladder application: 'Bold New Chapter' announced Feb 2024 is now in operational year 2. Three pillars (Reimagine 125 / Luxury / Simplify Operations) all have M-side evidence in MD&A: 125 stores reimagined (executed), China Grove opened (executed), Bloomingdale's/Bluemercury comps p

### JWN — Nordstrom, Inc.

- **Filing analyzed:** `0000072333-25-000039_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.14

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C7** — CFO Catherine R. Smith departure announced via 8-K filed 2025-03-04, last day ~2025-03-21. PEO Erik Nordstrom serves as both principal executive officer and the 10-K cover-page filer.
  - Interpretation: Verified event. Calibration: CFO departure 4 days before annual reporting deadline and 10 weeks after a definitive go-private signing is a governance event with moderate severity. Three plausible reads: (a) routine pre-close transition / non-renewal; (b) economic incentive — CFO's change-in-control 

### GPS — The Gap, Inc.

- **Filing analyzed:** `0001628280-26-018573_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.14

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C4** — Fiscal 2025 net sales +2% to $15.4B; store+franchise sales +1%, online sales +4%; gross margin 40.8% (vs 41.3%) — 50 bp compression.
  - Interpretation: Heuristic 9 (comp-sales vs marketing tier): the headline narrative emphasizes 'transformation momentum,' but the financial-statement disclosure shows only +1% store/franchise comp and a 50bp gross-margin compression (with merchandise inventory +7% YoY — Heuristic 12 inventory-turn watch). This is a 

### TJX — The TJX Companies, Inc.

- **Filing analyzed:** `0000109198-26-000008_10-K.txt`
- **Claims extracted:** 6
- **Severity distribution:** PASS=6, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


### COST — Costco Wholesale Corporation

- **Filing analyzed:** `0000909832-25-000101_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=7, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### BIG
- Composite: **2.17**   RED_FLAGs: 3   SEVERE: 2   → Truth_signal: YES
- Discovery_advantage: **UNKNOWN**   short_float=?   inst_own=?   recom=?
- **Decision: SUPPRESS (data unavailable)** — Truth_signal present but finviz couldn't price the discovery side (often because the issuer is delisted / deregistered, e.g. Form 15-12G already filed). Bearish reality is likely already in the filings; treat as confirmation, not bet.

### KSS
- Composite: **0.88**   RED_FLAGs: 1   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=24.4%   inst_own=110%   recom=3.33
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### M
- Composite: **0.50**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=12.0%   inst_own=98%   recom=2.60
- **Decision: no bet.** Composite 0.50 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### JWN
- Composite: **0.14**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **UNKNOWN**   short_float=?   inst_own=?   recom=?
- **Decision: no bet.** Composite 0.14 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### GPS
- Composite: **0.14**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=12.2%   inst_own=64%   recom=1.67
- **Decision: no bet.** Composite 0.14 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### TJX
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=1.4%   inst_own=93%   recom=1.68
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### COST
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=1.5%   inst_own=71%   recom=2.03
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** Retail distress is structural; framework-flagged claims are disclosure-quality concerns.
- **Wholesale-supplier counterparty disclosure is partial.** Suppliers disclose top customers; not all material relationships are surfaced in 10-K narrative.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **Mall-REIT tenant-exposure data** (SPG / MAC top-tenant concentration tables) is in their 10-Ks but unstructured; a small parser would surface retailer-by-retailer exposure for direct cross-check.
- **Consumer / credit-card spend data** (Affinity Solutions, Earnest Analytics) are paid data sources; coverage gap.
