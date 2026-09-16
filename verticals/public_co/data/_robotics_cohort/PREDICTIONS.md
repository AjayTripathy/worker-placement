# Robotics / Autonomous-Systems Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T07:20:48.795344Z — cutoff 2026-05-16_

## Methodology

Six names spanning speculative robotics / autonomous-systems pure-plays and mature robotics-adjacent controls: SYM (Symbotic warehouse automation), KSCP (Knightscope security robots), BBAI (BigBear.AI defense AI), SERV (Serve Robotics delivery) + IRBT (iRobot — control), TER (Teradyne, Universal Robots parent — control). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch access, no shared context. Subagent workflow includes checkpointing.

Robotics-specific calibration emphasis: **pilot-vs-commercial-deployment conflation** (Heuristic 9). Robotics names routinely headline 'deployed at N customer sites' without separating pilots-as-PR from commercial-scale revenue-bearing deployments. ARR vs one-time-sale split is the cleanest cross-check.

Forward-bet emission uses the shared v2 emitter.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | SERV | Serve Robotics Inc. | 7 | 0 | 3 | 1 | 2 | 1 | 1.83 |
| 2 | KSCP | Knightscope, Inc. | 9 | 2 | 4 | 0 | 3 | 0 | 1.44 |
| 3 | BBAI | BigBear.ai Holdings, Inc. | 7 | 1 | 4 | 1 | 0 | 1 | 1.00 |
| 4 | SYM | Symbotic Inc. | 7 | 2 | 3 | 1 | 0 | 1 | 0.83 |
| 5 | IRBT | iRobot Corp. | 8 | 6 | 1 | 0 | 1 | 0 | 0.50 |
| 6 | TER | Teradyne, Inc. | 9 | 8 | 1 | 0 | 0 | 0 | 0.11 |

## Per-ticker findings

### SERV — Serve Robotics Inc.

- **Filing analyzed:** `0001832483-26-000010_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=0, MODERATE=3, SEVERE=1, RED_FLAG=2, UNVERIFIABLE=1
- **Composite severity:** 1.83

#### 🔴 RED_FLAG_NEGATIVE claims
- **C4_revenue_27m_fy2025** — Serve generated $2.7 million in revenue for FY2025 (vs $1.8M in FY2024) against a net loss of $101.4 million and accumulated deficit of $208.9 million.
  - M-check: `Internal financials only — no external M-source needed for arithmetic. The headline is staggering: gross margin is negative 580% (cost to provide $1 of delivery service is $6.80). Combined with the disclosed material weaknesses in ICFR (see C5), this is a Heuristic 10 distress fingerprint.`
  - M-value: {'revenue_m': 2.65, 'cogs_m': 18.0, 'gross_margin_pct': -580, 'net_loss_m': -101.4, 'accumulated_deficit_m': -208.9, 'cash_burn_m': -80.2, 'revenue_to_loss_ratio': 0.026}
  - Interpretation: Heuristic 10 + Heuristic 11. The company is generating $2.7M of revenue against $101M of annual losses (revenue is 2.6% of losses), with deeply-negative gross margins indicating the unit economics of robotic delivery do NOT work at current scale. Note the company's three acquisitions (Voysys Apr-25, Vayu Aug-25, Diligent Jan-26, Vebu Feb-26) and capital raises are stretching capital ahead of any c
- **C5_material_weakness_icfr** — Management concluded disclosure controls and internal control over financial reporting were not effective as of Dec 31, 2025 due to multiple material weaknesses (segregation of duties, control environ
  - M-check: `Self-disclosure. This is a serious, broad, multi-area failure — not a narrow technical material weakness. It explicitly admits the company lacks the size/resources for effective controls. Particularly notable given the company completed FOUR acquisitions (Voysys, Vayu, Diligent, Vebu) in a 10-month window across 2025–early 2026, each requiring complex purchase-price allocation, and acknowledges that Diligent and Vebu accounting is incomplete at filing.`
  - M-value: {'icfr_effective': False, 'disclosure_controls_effective': False, 'weaknesses_disclosed': ['control environment', 'segregation of duties', 'controls over substantially all accounts and disclosures'], 'acquisition_accounting_incomplete': ['Diligent (Jan 2026)', 'Vebu (Feb 2026)']}
  - Interpretation: Broad-scope material weakness in a company actively executing serial M&A is a Heuristic 10 distress fingerprint and elevates the reliability risk of all other financial claims in this filing (including the customer concentration table and revenue disclosure). Scored RED because the weaknesses are not narrow / remediated — they cover 'substantially all accounts and disclosures' which is essentially
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C2_uber_eats_platform_integration** — Serve maintains platform-level integrations with food delivery platforms, such as Uber Eats and DoorDash, that enable real-time order dispatch and operational coordination.
  - Interpretation: Hard counterparty-asymmetry signal. Uber's 10-K does not name Serve as a material partner/customer at any point — only a 2022 earnings-press-release tag-out. For Uber, the Serve relationship is immaterial (which is consistent with Uber's scale — ~$45B revenue), but on the SERV side this relationship is the entire business thesis. Heuristic 7 says ABSENCE for a pilot-stage relationship = MODERATE; 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1_fleet_size_2000_robots** — As of December 31, 2025, Serve's fleet consisted of over 2,000 sidewalk delivery robots.
  - Interpretation: STAGE LADDER applied (Heuristic 3). Headline 'over 2,000 robots' is a fleet/inventory figure not a commercial-deployment figure. $2.7M revenue across 2,000+ robots = ~$1,350/robot/year — clearly inconsistent with commercial utilization. Either fleet is heavily idle / inventory-staged, or many robots
- **C3_customer_concentration_a_b** — For FY2025, Customer A represented 37% and Customer B represented 18% of total revenues; combined ~55% from two unnamed customers (likely Uber Eats and DoorDash).
  - Interpretation: Two concerning sub-signals: (1) Customer B's share collapsed from 65% to 18% YoY — and since total revenue only grew 46% ($1.8M → $2.7M), Customer B's absolute revenue dropped from ~$1.18M to ~$0.48M, a ~60% decline. That looks like a major customer churn or pilot wind-down. (2) Refusal to name part
- **C6_diligent_healthcare_acquisition** — On January 27, 2026 Serve completed the acquisition of Diligent Robotics Inc. (Moxi healthcare robots) for ~$29M, extending the platform to hospitals and citing 'established commercial relationships w
  - Interpretation: Patent footprint validates Diligent's technology bona-fides. The 'established commercial relationships' phrasing without naming any specific health system or disclosing the inherited revenue base earns a MODERATE rating. The fact that the acquisition closed only ~6 weeks before 10-K filing and PPA i

### KSCP — Knightscope, Inc.

- **Filing analyzed:** `0001104659-26-036240_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=2, MODERATE=4, SEVERE=0, RED_FLAG=3, UNVERIFIABLE=0
- **Composite severity:** 1.44

#### 🔴 RED_FLAG_NEGATIVE claims
- **KSCP-C2** — Going concern: $227.0M accumulated deficit, $33.8M net loss, $30.3M cash used in operating activities for FY2025; auditor issued substantial-doubt going-concern qualifier.
  - M-check: `edgar_fts.query_fulltext (KSCP own filings) + 10-K/10-Q text`
  - M-value: {'accumulated_deficit_M': 227.0, 'FY2025_op_cash_burn_M': 30.3, 'YE2025_cash_M': 20.6, 'Q1_2026_op_burn_M': 11.6, 'Mar31_2026_cash_M': 11.4, 'implied_runway_quarters': '<3 without new ATM issuance'}
  - Interpretation: Going-concern qualifier is explicit and reaffirmed in Q1 2026. Cash burn accelerated QoQ (from ~$7.6M/quarter FY2025 avg to $11.6M in Q1 2026, partly due to KSF acquisition cash outflow of $6.1M). Company is structurally dependent on ATM equity issuance — see C8.
- **KSCP-C5** — Total order backlog of approximately $3.1M as of March 24, 2026 ($0.6M ASR + $2.5M ECD).
  - M-check: `internal_disclosure + cross-check via Q1 2026 10-Q (no backlog uplift disclosed)`
  - M-value: {'total_backlog_M': 3.1, 'ASR_backlog_M': 0.6, 'ECD_backlog_M': 2.5, 'backlog_to_FY2025_revenue_pct': 27}
  - Interpretation: Tiny $0.6M ASR backlog is direct quantitative contradiction of the 'building the nation's first Autonomous Security Force' positioning. With ASR depreciation alone at $2.0M/yr and ASR-related service revenue ~$8.0M total, $0.6M of new ASR orders implies the install-base lift is decelerating. Combined with the going-concern overhang, this is a HARD signal of forward-revenue weakness in the core pla
- **KSCP-C8** — ATM offering program produced $42.8M FY2025 + $9.0M Q1 2026 + $3.3M April-May 8 2026 ($55M+ net in 16 months); $18.3M remaining on shelf at May 8 2026. Class A shares grew from 4.07M (YE2024) to 12.19
  - M-check: `internal_filings + edgar_fts (KSCP S-3, 424B5, 8-K)`
  - M-value: {'ATM_net_FY2025_M': 42.8, 'ATM_net_Q1_2026_M': 9.0, 'ATM_net_AprMay8_2026_M': 3.3, 'shelf_remaining_M_May8': 18.3, 'share_count_YE2024_M': 4.07, 'share_count_YE2025_M': 12.19, 'share_count_post_KSF_M_est': 14.91, 'dilution_multiplier_15mo': '~3.7x'}
  - Interpretation: ~3.7x share-count expansion in 15 months funded almost entirely by ATM dilution — this IS the going-concern remediation. Combined with multiple historical reverse-splits (per cohort metadata and the 'fractional share adjustment due to reverse stock split' line in FY2024 equity rollforward), the structural dependence on ATM issuance against a declining ASR backlog is a classic distress fingerprint 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **KSCP-C3** — One client = 19% of FY2025 revenue (zero such clients in 2024); two clients = 28% and 11% of AR at YE2025.
  - Interpretation: Per Calibration 7, absence of counterparty disclosure for a $2M customer is NOT a hard contradiction — too immaterial to trigger 10-K mention on the customer side. Score MODERATE because the named-customer transparency is missing and the new concentration risk (zero to 19% YoY) suggests a single-dea
- **KSCP-C4** — K7 ASR remains in development; commercial production not expected until late 2026 or early 2027; K7 contributed zero revenue in 2025.
  - Interpretation: Per Calibration 3 (planned vs operational): K7 is still at pre-commercial stage. The repeated push of commercial production timeline (now 'late 2026 or early 2027') is a soft-deferral pattern consistent with pilots-as-PR risk. Not a hard fabrication — the company is transparent that K7 has $0 revenu
- **KSCP-C6** — Acquired Event Risk LLC (KSF) on Feb 27, 2026 for ~$18M total consideration; recorded $7.7M goodwill + $15.5M customer-relationships intangible.
  - Interpretation: Acquisition is verified via 8-K/A with full Reg S-X financial statements (filed 2026-05-15). However, two cautions per Calibration 4: (a) for a $30M-burn microcap with going-concern qualifier to pay ~$11M cash+debt-repay+deferred (plus shares) for a security-guarding services business is a pivot awa
- **KSCP-C9** — Knightscope serves government clients (per cohort metadata, municipal/private-security customers).
  - Interpretation: Per Calibration 5 + 7: USAspending captures federal contracts. There IS one DoD/Air Force ASR contract ($73K — directly on-mission), which validates the existence of federal ASR pilot activity — score is NOT RED. However, $241K cumulative over 5+ years vs. company emphasis on 'government' as a marke

### BBAI — BigBear.ai Holdings, Inc.

- **Filing analyzed:** `0001836981-26-000018_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=1, MODERATE=4, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 1.00

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C4** — $248M total backlog at 12/31/25; $27M attributable to 10%+-customers; only $8.2M of Remaining Performance Obligations (RPO).
  - Interpretation: Backlog disclosure conflates ceiling/option value with firm contract value. This is the defense-services analog of Calibration Heuristic 9 (pilot-vs-deployment conflation): unfunded/optioned backlog presented as commercial visibility. The $8.2M RPO is the only number bound by GAAP. SEVERE_UNDERDELIVERY of the backlog narrative — headline overstates near-term contracted revenue by an order of magni
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — FY2025 revenue $127.7M; US gov 90% ($114.7M); 10%+-concentration customers = $65M (51% of revenue).
  - Interpretation: US government revenue claim is plausible only with heavy subcontract intermediation. Year-over-year revenue decline of ~20%, combined with single-customer A/R >10% concentration and material $65M=51% revenue concentration in 10%+ customers, plus EPASS wind-down — supports MODERATE_UNDERDELIVERY of t
- **C5** — BigBear.ai holds patent IP across AI, computer vision, predictive analytics, biometrics, perception, orchestration and digital identity.
  - Interpretation: Filing language is careful ('not dependent on any particular patent or application'), which is consistent with the absence of a BBAI-branded patent footprint. The biometrics-and-digital-identity narrative (acquired via Pangiam for biometric/digital-identity tech) is not supported by Pangiam having g
- **C6** — $461.5M total liquidity at 12/31/25; debt reduced from $200.8M to $17.7M subsequent to year-end (88% reduction). 'Strongest financial position in history.'
  - Interpretation: Liquidity is real but bought at extreme dilution + convert-into-equity rather than retire-with-cash. Calibration Heuristic 10 applies (distress fingerprints): three back-to-back ATMs in one year, mass convert-to-equity, growing restructuring charges. The 'strongest in history' framing of capital str
- **C7** — Pangiam acquisition (Feb 2024) brought biometric/digital identity capabilities; Air Force EPASS wound down Q2 2023; cost of revenues rose to 78% in FY25 (vs 71% in FY24).
  - Interpretation: Pangiam's biometrics capability does not appear as a federal-prime revenue line. Either it is also subcontracted (typical for cleared biometrics work to CBP/TSA via primes) or commercial in nature. Combined with margin compression and EPASS wind-down, the 'transformation' narrative is moderate-under

### SYM — Symbotic Inc.

- **Filing analyzed:** `0001837240-25-000278_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=2, MODERATE=3, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.83

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C5** — Material weakness in ICFR re cost-of-revenue timing (FY25, adverse Grant Thornton opinion) + prior FY24 material weakness on revenue recognition (remediated FY25) + pending securities class actions (D
  - Interpretation: SEVERE_UNDERDELIVERY. Per Heuristic 11 (revenue-recognition pattern, robotics-specific) and Heuristic 9 (pilot vs deployment conflation tied to deployment-time misstatement allegations in the class action), this is the central forensic-disclosure concern. The framework should treat any forward-revenue or backlog-conversion claim by SYM with elevated skepticism while (a) the adverse ICFR opinion re
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — Jan 2025 ASR acquisition from Walmart + 2025 Walmart MAA: 400 micro-fulfillment system commitment, $520M dev funding to SYM
  - Interpretation: MODERATE_UNDERDELIVERY. The headline '400-unit + $520M' figure is real-contract but mostly contingent and forward-looking. Calibration Heuristic 3 (planned vs operational) and Heuristic 9 (pilot vs deployment conflation) apply: 'several' operating micro-fulfillment systems vs 400 promised is a wide 
- **C3** — GreenBox JV with SoftBank (SYM 35% / SoftBank 65%): $7.5B 6-year commitment; $11.6B remaining performance obligation at Sept 27, 2025; SYM max exposure $1.57B incl. $1.56B future funding commitments
  - Interpretation: MODERATE_UNDERDELIVERY. The JV structure and commitments are real and disclosed, but the $7.5B / $11.6B headline backlog with a 35%-owned VIE that SYM must FUND (max exposure $1.57B) raises Heuristic 11 concerns: the second-largest 'customer' is one in which SYM is a material equity participant and 
- **C6** — C&S Wholesale Grocers is an affiliate / related-party customer; shared executives with SYM; FY revenue from C&S: $12.2M (FY25), $58.9M (FY24), $15.8M (FY23)
  - Interpretation: MODERATE_UNDERDELIVERY. The relationship is real and corroborated by third-party filings. Concern: (1) related-party customer with shared executives is a governance/conflict flag per the 10-K's own risk factor; (2) the steep FY24→FY25 revenue decline from C&S (-79%) is not highlighted in management 

### IRBT — iRobot Corp.

- **Filing analyzed:** `0001159167-25-000011_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=0, RED_FLAG=1, UNVERIFIABLE=0
- **Composite severity:** 0.50

#### 🔴 RED_FLAG_NEGATIVE claims
- **C4** — iRobot received a going-concern qualifier in its FY2024 auditor opinion (PwC) and is in covenant-waiver mode with Carlyle (TCG Senior Funding) on a $200M senior secured term loan maturing July 24, 202
  - M-check: `filings_index distress-fingerprint check + audited financials self-disclosure`
  - M-value: Self-disclosed in 10-K (PwC auditor going-concern paragraph; Amendment No.1 to Credit Agreement Mar 11 2025; warrants for 1,840,503 shares = ~6% of outstanding at $0.01 strike issued to lenders; $40M restricted cash returned to controlled account; $3.6M PIK fee). Filings index (2026 entries) further
  - Interpretation: This is a candid self-disclosure of severe financial distress, not a false claim. The 'claim' here is iRobot honestly saying it has substantial doubt about going concern, near-term covenant breach, ATM equity offering suspended, and is exploring sale/refinancing. M-side check (filings_index distress fingerprints) CORROBORATES the severity rather than contradicting it. This is RED_FLAG_NEGATIVE not
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — One customer accounted for 22.2% of total revenue in fiscal 2024 (24.0% in 2023, 22.6% in 2022).
  - Interpretation: The 22.2% customer is unnamed in iRobot's 10-K (only required to disclose if a single customer >10%; name not required by GAAP). At ~$151M of annual revenue (22.2% of $681.8M), this is material to iRobot but immaterial to any megacap retailer (Amazon retail GMV >$500B, Walmart ~$650B revenue), so th

### TER — Teradyne, Inc.

- **Filing analyzed:** `0001193125-26-059002_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=8, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.11

#### 🟡 MODERATE_UNDERDELIVERY claims
- **TER-7** — Robotics: third consecutive quarter of sequential revenue growth in Q4 2025; full-year Robotics revenue $308.3M (-15.5% YoY).
  - Interpretation: MODERATE caveat: the headline 'three sequential quarters of growth' is a real sequential-growth fact but obscures that the segment is still down ~15.5% year-over-year and required a ~400-head restructuring. This is the robotics-specific 'sequential growth' framing that hides absolute decline. Not de

## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### SERV
- Composite: **1.83**   RED_FLAGs: 2   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=31.6%   inst_own=38%   recom=1.25
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### KSCP
- Composite: **1.44**   RED_FLAGs: 3   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=18.5%   inst_own=10%   recom=1.00
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months of 2026-05-16, at least one of the following occurs: (a) the next 10-K/10-Q/20-F materially restates the RED_FLAG claim; (b) the company announces a strategic pivot away from the disputed claim; (c) the counterparty publicly contradicts the company's representation; (d) the company files Form 15-12G / 25-NSE / Chapter 11; (e) the stock falls >50% from cutoff price.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### BBAI
- Composite: **1.00**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=29.7%   inst_own=39%   recom=2.33
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### SYM
- Composite: **0.83**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=22.1%   inst_own=42%   recom=2.33
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### IRBT
- Composite: **0.50**   RED_FLAGs: 1   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **UNKNOWN**   short_float=?   inst_own=?   recom=?
- **Decision: SUPPRESS (data unavailable)** — Truth_signal present but finviz couldn't price the discovery side (often because the issuer is delisted / deregistered, e.g. Form 15-12G already filed). Bearish reality is likely already in the filings; treat as confirmation, not bet.

### TER
- Composite: **0.11**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=3.5%   inst_own=95%   recom=1.95
- **Decision: no bet.** Composite 0.11 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** Pilot deployments are real customer engagements even when they don't convert to commercial scale.
- **Not a trade recommendation.** Several names are micro-cap with limited borrow.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **Defense-intel customer disclosure gap** for BBAI: many DoD intelligence-community customers don't disclose contractors by name in 10-Ks. USAspending covers some but classified-IC contracts are off-USAspending. Score classified-IC-customer claims as UNVERIFIABLE rather than false-clean.
- **Walmart-related-party (SYM)** — SYM has a Greenbox Systems joint-venture structure with Walmart that creates structural related-party-revenue risk worth a dedicated cross-check.
