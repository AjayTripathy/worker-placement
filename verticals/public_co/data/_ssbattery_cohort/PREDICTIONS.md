# Solid-State / Next-Gen Battery Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T22:14:04.627044Z — cutoff 2026-05-16_

## Methodology

Seven names spanning solid-state / next-gen battery pure-plays and lithium-supply controls: QS / SES / SLDP / MVST / ENVX (battery) + ALB / LAC (lithium supply controls). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch access, no shared context. Subagent workflow includes checkpointing.

Battery-specific calibration emphasis: **energy-density / cycle-life without test conditions** (Heuristic 9). Battery names routinely cite Wh/kg or cycle-count headlines without disclosing rate, temperature, or depth-of-discharge — the conditions that decide whether the number is lab-scale or production-realistic.

**Foreign-OEM counterparty coverage:** most major battery customer OEMs (VW, BMW, Mercedes, Hyundai, Toyota) file foreign annual reports (20-F or none); EDGAR coverage is partial. UNVERIFIABLE rather than false-clean for these counterparty-disclosure tests.

Forward-bet emission uses the shared v2 emitter.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | MVST | Microvast Holdings, Inc. | 9 | 2 | 1 | 2 | 2 | 2 | 1.57 |
| 2 | SES | SES AI Corp. | 7 | 0 | 4 | 1 | 1 | 1 | 1.50 |
| 3 | SLDP | Solid Power, Inc. | 10 | 2 | 5 | 1 | 1 | 1 | 1.11 |
| 4 | QS | QuantumScape Corp. | 8 | 2 | 4 | 1 | 0 | 1 | 0.86 |
| 5 | ENVX | Enovix Corp. | 8 | 1 | 5 | 0 | 0 | 2 | 0.83 |
| 6 | LAC | Lithium Americas Corp. | 7 | 5 | 2 | 0 | 0 | 0 | 0.29 |
| 7 | ALB | Albemarle Corp. | 8 | 7 | 1 | 0 | 0 | 0 | 0.12 |

## Per-ticker findings

### MVST — Microvast Holdings, Inc.

- **Filing analyzed:** `0001628280-26-018264_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=2, MODERATE=1, SEVERE=2, RED_FLAG=2, UNVERIFIABLE=2
- **Composite severity:** 1.57

#### 🔴 RED_FLAG_NEGATIVE claims
- **C5** — Loss of conditional DOE grant; subject of stockholder demands and Schelling securities class action.
  - M-check: `usaspending.query_recipient_contracts / grants for DOE award verification`
  - M-value: Only $499,972 in cumulative DOE-grant assistance; no large-dollar DOE LPO / grant present
  - Interpretation: Heuristic 5 (USAspending DOE coverage) — major DOE LPO and grant awards DO show up. The absence of any large MVST DOE award post-cutoff confirms the rescission. The company itself acknowledges loss of the conditional grant and resulting securities litigation, with class certification briefing scheduled for June-October 2026. This is a hard adverse signal: a flagship US-policy win that did not mate
- **C6** — Going-concern doubt initially raised; $169.2M cash (only $105M unrestricted; $62.2M trapped in China + Europe subsidiaries); $140.9M convertible loan at SOFR+9.75%; stock at $2.10 vs $11.50 warrant st
  - M-check: `edgar_fts.query_fulltext for capital-event 8-K cadence; self-disclosure of going concern`
  - M-value: Going-concern doubt + distressed convertible coupon + trapped foreign cash + sub-$3 share price
  - Interpretation: Heuristic 10 (delisting / going-concern fingerprints) — multiple distress markers present. Critically, $62.2M of cash is held in China/Europe subsidiaries and is NOT readily repatriable due to PRC FX controls + adverse US tax — effectively the US parent has only ~$43M of usable cash against $140.9M of distressed convertible debt and $19.95M+ in unpaid US construction liens. The going-concern quali
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C4** — Clarksville, TN 577,000 sq ft owned facility for ESS/LFP cell production; construction slowed Q4 2023 due to financing; $19.95M DPR Construction lien dispute; $23.6M total liens received.
  - Interpretation: Heuristic 1 (EPA FRS scope) — battery production facilities ARE EPA-regulated for hazmat / air permits. Absence of a Microvast-named EPA-permitted facility in TN, despite a 577,000 sq ft 'owned manufacturing' property, confirms the structure exists but is NOT operating as a permitted battery factory. The disclosed mechanics liens ($23.6M), WARN-Act layoff class action, $19.95M unpaid contractor di
- **C9** — Restatement of Q2 2024 and Q3 2024 quarterly financial statements due to Clarksville facility impairment error; material weakness in internal controls.
  - Interpretation: Restatement is corroborated by the actual 10-Q/A filing in EDGAR. Heuristic 11 (revenue-recognition pattern) is adjacent — material weakness + restatement focused on the SAME asset (Clarksville) that is the subject of mechanics liens, WARN-Act layoff settlement, and construction-dispute litigation. This is a clustered red-flag pattern: bad accounting and bad operating outcome on the same flagship 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C7** — Order backlog of $196.1M as of YE2025, majority expected fulfilled in 2026 and 2027.
  - Interpretation: MVST does not claim Ford or GM as customers, so the Ford/GM absence is not a contradiction. However, $196.1M of backlog (~12 months of revenue at current run rate) with no segmentation between firm POs and indicative orders, and 'majority' fulfilled across 2026 AND 2027 (i.e., back-end loaded), agai

### SES — SES AI Corp.

- **Filing analyzed:** `0001819142-26-000010_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=0, MODERATE=4, SEVERE=1, RED_FLAG=1, UNVERIFIABLE=1
- **Composite severity:** 1.50

#### 🔴 RED_FLAG_NEGATIVE claims
- **C4** — Strategic pivot from in-house Li-Metal battery manufacturing toward AI/Molecular Universe; capex redirected from manufacturing equipment to AI infrastructure; reduced headcount.
  - M-check: `epa_frs.query_facilities for Woburn MA`
  - M-value: SES (search='SES', state=MA, city=Woburn): 0 facilities. SolidEnergy (state=MA): 1 facility found — SOLIDENERGY SYSTEMS CORP, 35 Cabot Rd, Woburn MA — registered under legacy name, NOT updated to current SES AI branding
  - Interpretation: Pattern-recognition RED_FLAG: A pre-revenue battery name that originally raised SPAC capital on the OEM JDA / Li-Metal SOP story has, by FY2025, (a) seen its three US-named OEM JDAs all conclude or downshift, (b) zeroed out OEM-funded R&D ($0 vs $8.575M PY), (c) explicitly redirected capex AWAY from battery manufacturing equipment toward 'AI infrastructure / GPU rental / software,' (d) rebranded i
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C1** — Hyundai B-sample JDA concluded December 2025; no announced advancement to C-sample, validation, or SOP.
  - Interpretation: Calibration Heuristic 3 (planned vs operational / STAGE LADDER): Hyundai started in Dec 2020 with a discovery JDA, advanced to A-sample (Aug 2021), then to B-sample (March 2024 extension). The B-sample JDA *concluded* in December 2025 with NO disclosed follow-on for C-sample or validation. Under the framework's stage ladder, this is a STALLED ladder: the JDA reached B-sample and then was let to ex
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — GM JDA concluded September 2024 and GM mutually terminated Director Nomination Agreement October 29, 2024; GM no longer a related party.
  - Interpretation: Calibration Heuristic 7 (counterparty-disclosure threshold): SES's flagship US-OEM JDA (one of the framework's HARD-CONTRADICTION candidates per the cohort prompt) concluded September 2024 and GM exited the board the next month. GM's 10-K filings contain ZERO references to SES AI or SolidEnergy. Whi
- **C3** — Honda A-sample JDA concluded June 2023; replaced by B-sample services agreement (Jan 2025 through June 2026). Another OEM B-Sample JDA concluded December 2025.
  - Interpretation: Calibration Heuristic 7: Honda IS a SEC-filer (HMC 20-F), so this is partially verifiable. Honda's FY2022-2024 20-Fs reference SES AI as a battery JDA counterparty (consistent with disclosed Honda A-sample JDA Dec 2021-June 2023). However the MOST RECENT pre-cutoff Honda 20-F (filed June 18, 2025, c
- **C5** — Acquired UZ Energy (China BESS manufacturer) on September 15, 2025 for ~$25.8M; UZ Energy contributed ~35% of FY2025 revenue.
  - Interpretation: Calibration Heuristic 11 (revenue-recognition pattern): SES's $21.0M of FY2025 'revenue from customers' is essentially manufactured: $13.6M is service revenue from OEM JDA contracts that have now all concluded; the $7.4M of product revenue is driven almost entirely by UZ Energy ESS systems sales — a
- **C6** — Plan to develop NDAA-compliant drone cell manufacturing capacity in Korean facility for U.S. government and defense-related customers as a future revenue driver.
  - Interpretation: Calibration Heuristic 5 (source-jurisdiction): USAspending covers DoD contracts that would feed an NDAA-compliant drone-cell program. SES has ZERO federal contracts of any kind through cutoff. The claim is explicitly phrased as forward-planned ('we are planning to develop... uncertainty regarding th

### SLDP — Solid Power, Inc.

- **Filing analyzed:** `0001104659-26-019435_10-K.txt`
- **Claims extracted:** 10
- **Severity distribution:** PASS=2, MODERATE=5, SEVERE=1, RED_FLAG=1, UNVERIFIABLE=1
- **Composite severity:** 1.11

#### 🔴 RED_FLAG_NEGATIVE claims
- **C2_FORD_JDA_WINDDOWN** — Ford JDA extended again Dec 31 2025 'in connection with winding up of cell development activities,' expected to expire March 31, 2026.
  - M-check: `edgar_fts.query_fulltext search_term='Solid Power' cik='0000037996' = 1 hit (2021 8-K only).`
  - M-value: Ford EDGAR mentions of Solid Power: 1 (announcement 8-K 2021). Zero in Ford 10-K filings. Ford was previously a >5% holder; now winding down cell-development side of JDA.
  - Interpretation: This is a HARD CONTRADICTION to the original 2021 design-win narrative. Ford was one of two flagship OEM JDA partners (along with BMW). The cell-development JDA is being wound up; the company is left hoping to 'pursue opportunities to supply Ford with our electrolyte material' post-expiration -- aspirational, not contracted. Per Layer 3 Rule 7, Ford 10-K silence on the relationship after 2022 + ex
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C8_REVENUE_QUALITY_RELATED_PARTY** — 2025 revenue $21.7M = $6.0M government + $15.8M collaborative (primarily SK On milestone work); BMW related-party revenue collapsed $5.41M -> $0.189M (-96% YoY); $122.6M operating loss; $274.9M accumu
  - Interpretation: Calibration Heuristic 11 + Calibration Heuristic 4: revenue is overwhelmingly (a) milestone-based development services from OEM/Tier-1 partners that are ALSO equity investors (SK On invested $30M at de-SPAC; BMW holds >5% and board seat), and (b) DOE grant. There is essentially NO commercial-product revenue. The 96% YoY collapse in BMW revenue, combined with Ford wind-down (C2), suggests the JDA-m
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1_BMW_JDA** — Long-standing JDA with BMW (since 2016/2017); JDA was amended September 2024 to extend until certain development milestones, with BMW termination rights beginning Dec 31, 2025; BMW i7 test vehicle May
  - Interpretation: JDA itself is real (signed 2017+) and BMW retains board seat + >5% stake. But Stage Ladder: still JDA / R&D-license stage, no SOP. Termination rights now active. 96% YoY collapse in BMW-related revenue + i7 'test vehicle' (demonstration, not production) signals deceleration. Apply Calibration Heuris
- **C4_SAMSUNG_BMW_JEA** — October 2025 Joint Evaluation Agreement with Samsung SDI and BMW AG to develop a demonstration vehicle with all-solid-state batteries.
  - Interpretation: Stage ladder: 'Joint Evaluation Agreement' (Oct 2025) sits BELOW a JDA, BELOW A-sample / B-sample / C-sample, and far below SOP. Solid Power supplies electrolyte; Samsung SDI fabricates cells; BMW determines pass/fail. Demonstration vehicle, not SOP. Calibration Heuristic 3 (extra weight): conflatin
- **C7_CONTINUOUS_PILOT_LINE** — Continuous electrolyte production pilot line to be commissioned by end of 2026; 75 MT/yr capacity; aspirational ROK partner facility up to 500 MT/yr.
  - Interpretation: Pilot existence is verified by EPA FRS. However, two-stage claim: (a) 75 MT/yr continuous line by end-2026 = aspirational but supported by funded equipment ordering (PASS); (b) 500 MT/yr Korean facility = pure forward projection with no named partner, no permits, no site. Apply Calibration Heuristic
- **C9_LIQUIDITY_AND_CAPITAL_RAISES** — Total liquidity $336.5M at 12/31/2025; ATM $88.8M net in 2025 (avg $5.06/sh); $122.2M Registered Direct Offering Jan 2026; buyback at $1.05/sh avg in 2025.
  - Interpretation: Two competing signals: (a) liquidity is strong with multi-year runway (PASS-leaning), (b) buyback at $1.05 vs ATM at $5.06 is an opportunistic dilution-at-rallies pattern that, while not distress, is a signature of perceived-share-price-management at a pre-revenue speculative name. Net = MODERATE --
- **C10_VEHICLE_INTEGRATION_BMW** — BMW Group i7 test vehicle featuring Solid Power cells unveiled May 2025 -- 'significant achievement in our partnership.'
  - Interpretation: A test vehicle is a demonstrator, NOT a production design-win. Stage ladder: test vehicle ~ B-sample / C-sample stage. Conflating test-vehicle reveal with commercialization progress is the central evasion pattern per Calibration Heuristic 3. Combined with the JDA's now-active termination rights (Dec

### QS — QuantumScape Corp.

- **Filing analyzed:** `0001193125-26-071556_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=2, MODERATE=4, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.86

#### 🟠 SEVERE_UNDERDELIVERY claims
- **QS-003** — Pre-revenue; FY2025 op loss $472.6M, net loss $435.1M, accumulated deficit $3.8B, ATM raises $264.2M FY25 + $128.5M FY24.
  - Interpretation: Self-disclosure is fully corroborated by recurring EDGAR ATM filings. Calibration #10 (distress fingerprints) applies: ATM-driven cash funding model + listing transfer (NYSE->Nasdaq Dec 2025) + 16 years post-founding still pre-revenue (founded 2010) + 6 years post-deSPAC (2020) still pre-revenue. Accumulated deficit of $3.8B against ZERO commercial revenue is a hard signal of capital destruction. 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **QS-001** — PowerCo SE (Volkswagen subsidiary) up to $130.7M collaboration; $130M IP-license royalty pre-pay contemplated. Goal: industrialize QSE-5.
  - Interpretation: Calibration #2 (foreign-issuer caveat) applies: Volkswagen Group is a German company that does NOT file SEC forms, so EDGAR cannot corroborate. Calibration #3 (stage ladder): QSE-5 is at B/B1 sample, NOT SOP. The amended Collaboration Agreement is a pre-SOP JDA. The PowerCo IP License Agreement and 
- **QS-002** — QSE-5 B-samples achieve >800 Wh/L and 15-min 10-80% fast-charge; B1 demoed in Ducati V21L at IAA 2025.
  - Interpretation: Patent base is robust per Calibration Heuristic #8 (n_granted=125 >> 10 threshold, dominant in solid-state/lithium buckets) — PASS-quality on the IP-portfolio dimension. HOWEVER, Calibration Heuristic #9 (battery-specific energy-density disclosure quality) applies: the >800 Wh/L and 15-min fast-char
- **QS-004** — Class A stock transferred from NYSE to Nasdaq effective Dec 23, 2025.
  - Interpretation: Per the filing's plain language and the 8-K trail, this is a voluntary listing transfer, NOT a non-compliance delisting. However, voluntary mid-life NYSE->Nasdaq transfers by deSPAC companies are commonly associated with cost-saving / compliance-flexibility motives. Calibration #10 (delisting/going-
- **QS-008** — Volkswagen has cumulative equity investment of ~$380M in QS since 2012.
  - Interpretation: Calibration #4 (investment vs operating) is the key heuristic: $380M equity is real and consistently re-disclosed in QS's own filings, but it is an INVESTMENT, NOT a design-win, NOT a series-production commitment. The pattern of disclosing the equity investment alongside the PowerCo JDA (QS-001) is 

### ENVX — Enovix Corp.

- **Filing analyzed:** `0001828318-26-000006_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=1, MODERATE=5, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.83

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Independent testing laboratory confirmed in December 2025 that the AI-1 smartphone battery delivered volumetric energy density of 935 Wh/L (+12% vs leading silicon-doped commercial smartphone battery)
  - Interpretation: Patent depth (61 granted, mostly battery/electrode/cell, 7 silicon-anode in title) is fully consistent with a real silicon-anode platform company — PASS on patent corroboration. However the 935 Wh/L claim is reported WITHOUT test conditions (rate, temperature, depth-of-discharge) in the 10-K busines
- **C2** — Cell architecture designed to enable silicon anodes to achieve >=1,000 cycles to 80% remaining capacity.
  - Interpretation: Cycle-life number is also given without rate / DoD / temperature qualifications and is explicitly framed as a DESIGN TARGET ('designed to enable') rather than a measured value on AI-1 production cells. Smartphone applications typically test at 0.5C-1C with shallow DoD, where 1000 cycles is industry-
- **C3** — Partnered with a top-tier mobile OEM (unnamed) on AI-1 smartphone battery; delivered 1,000+ AI-1 packs to lead smart-eyewear customer + samples to 9 OEMs/ODMs.
  - Interpretation: The mobile OEM is UNNAMED — the framework cannot do a counterparty-disclosure cross-check. Apple's filings contain ZERO mentions of Enovix as of cutoff, but Apple does not disclose suppliers individually so absence is not dispositive (UNVERIFIABLE for any specific OEM). On the stage ladder, 'partner
- **C7** — Distress markers: accumulated deficit $977.8M, working capital $477.2M, $60M buyback FY25, additional $75M subsequent buyback authorized, 2028 (3.00%) + 2030 (4.75%) Convertibles, ATM, warrant dividen
  - Interpretation: Mixed signals. Going-concern language is present BUT the company has $477M working capital and is buying back its own shares — that is INCONSISTENT with classic Heuristic 10 distress fingerprint, suggesting more solvency than a typical SPAC-era battery name. However, the simultaneous mix is unusual:
- **C8** — Securities class action (N.D. Cal. 23-cv-00071-SI) alleges material misstatements about manufacturing scale-up / equipment testing; one statement remains active after Oct 2025 partial dismissal; class
  - Interpretation: Active securities-fraud case targeting the EXACT category of claims the framework is scoring (manufacturing scale-up, equipment testing). One statement survived motion practice and is proceeding to class certification. The 10-K's own forward statements about Fab2 ramp (C4), AI-1 testing (C1), and cy

### LAC — Lithium Americas Corp.

- **Filing analyzed:** `0001193125-26-118478_20-F.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=5, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.29

#### 🟡 MODERATE_UNDERDELIVERY claims
- **LAC-3** — Material uncertainty / going-concern language: auditor flagged substantial doubt depending on ability to repatriate Cauchari-Olaroz cash flows to service current portion of long-term debt.
  - Interpretation: Heuristic 10 — going-concern qualifier IS a distress fingerprint, and per the claim's own source quote the language is at PCAOB 'substantial doubt' level. Recurring (also in the June-2025 20-F/A). However, this is honestly disclosed by the issuer rather than discovered through M-source contradiction
- **LAC-7** — Convertible Notes classified current as of Dec 31, 2025; total contractual financial liabilities of ~$297.7M (incl. $261M convertibles), against $61.1M cash and $23.2M receivables.
  - Interpretation: Convertible Notes are real (continuously disclosed since 2022 40-F). Issuer's own narrative explains that current-classification is technical (holder-option conversion conditions beyond the Company's control under IFRS), not a maturity event. Maturity schedule shows only $4.5M cash interest in 2026 

### ALB — Albemarle Corp.

- **Filing analyzed:** `0000915913-26-000018_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=7, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.12

#### 🟡 MODERATE_UNDERDELIVERY claims
- **ALB-3** — Kemerton, Australia plant: Trains 3 and 4 construction stopped in 2024, Train 2 placed in care and maintenance in 2024, and Train 1 placed in care and maintenance on February 6, 2026 — all constructed
  - Interpretation: Disclosure is transparent and audit trail exists. However the substance is a HARD operational underdelivery: entire constructed Australian hydroxide conversion complex now idle within ~3 years of commissioning, $150-225M cash charges expected, $245.6M long-lived asset impairment, $510M consolidated 

## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### MVST
- Composite: **1.57**   RED_FLAGs: 2   SEVERE: 2   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=10.2%   inst_own=23%   recom=1.00
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months of 2026-05-16, at least one of the following occurs: (a) the next 10-K/10-Q/20-F materially restates the RED_FLAG claim; (b) the company announces a strategic pivot away from the disputed claim; (c) the counterparty publicly contradicts the company's representation; (d) the company files Form 15-12G / 25-NSE / Chapter 11; (e) the stock falls >50% from cutoff price.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### SES
- Composite: **1.50**   RED_FLAGs: 1   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **HIGH**   short_float=7.2%   inst_own=19%   recom=2.00
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months of 2026-05-16, at least one of the following occurs: (a) the next 10-K/10-Q/20-F materially restates the RED_FLAG claim; (b) the company announces a strategic pivot away from the disputed claim; (c) the counterparty publicly contradicts the company's representation; (d) the company files Form 15-12G / 25-NSE / Chapter 11; (e) the stock falls >50% from cutoff price.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### SLDP
- Composite: **1.11**   RED_FLAGs: 1   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=11.1%   inst_own=40%   recom=1.00
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months of 2026-05-16, at least one of the following occurs: (a) the next 10-K/10-Q/20-F materially restates the RED_FLAG claim; (b) the company announces a strategic pivot away from the disputed claim; (c) the counterparty publicly contradicts the company's representation; (d) the company files Form 15-12G / 25-NSE / Chapter 11; (e) the stock falls >50% from cutoff price.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### QS
- Composite: **0.86**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=20.7%   inst_own=37%   recom=3.44
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### ENVX
- Composite: **0.83**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=28.0%   inst_own=50%   recom=1.73
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### LAC
- Composite: **0.29**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=14.9%   inst_own=32%   recom=2.64
- **Decision: no bet.** Composite 0.29 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### ALB
- Composite: **0.12**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=8.8%   inst_own=92%   recom=2.04
- **Decision: no bet.** Composite 0.12 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** Battery JDAs are real research and development relationships even when they don't produce series production by the originally claimed SOP year.
- **Foreign-OEM disclosure gap.** Counterparty-disclosure checks for VW/BMW/Mercedes/Hyundai/Toyota are partial because their primary annual reports are off-EDGAR.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **Foreign-OEM counterparty disclosure gap** is the largest coverage limit. A connector for foreign-OEM annual reports (Volkswagen Group Annual Report Germany, BMW Annual Report, Mercedes-Benz Group Annual Report, Hyundai Motor Annual Report, Toyota Motor Annual Report) would close it.
- **Battery-cell test-condition normalization** is currently manual; a structured registry of independent battery-cell test results (e.g. DOE/INL benchmarking publications) would let the framework cross-check energy-density claims directly.
