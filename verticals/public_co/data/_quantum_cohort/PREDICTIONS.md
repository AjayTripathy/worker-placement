# Quantum Computing Cohort — HELD-OUT Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T07:20:48.402344Z — cutoff 2026-05-16_

## Methodology

Five US-listed quantum-computing or QKD pure-plays: RGTI (Rigetti, superconducting gate-model), IONQ (IonQ, trapped-ion), QBTS (D-Wave, annealing), ARQQ (Arqit, QKD encryption — UK foreign private issuer, 20-F), QUBT (Quantum Computing Inc., photonic).

**This is a HELD-OUT cohort.** The calibration heuristics in the subagent prompt template were authored from eVTOL, defense, lidar, and nuclear runs — NOT from any prior quantum-cohort outcomes. Per TECH_DEBT.md ('Calibration heuristics tuned on a single cohort are contaminated'), this run tests whether the framework's discrimination generalizes to a vertical it wasn't tuned on.

Each ticker was analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch access, no shared context with other tickers. Subagent workflow now includes checkpointing: input.json written immediately after claim extraction; scores.json rewritten after each claim is scored (so a watchdog kill preserves partial work).

Forward-bet emission uses the shared v2 emitter (`forward_bet_emission.py`): composite >= 0.6 AND discovery_advantage_tier IN {HIGH, MED}. Crowded shorts (high SI, well-followed) are suppressed even when Truth_signal is high.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | ARQQ | Arqit Quantum Inc. | 8 | 1 | 4 | 1 | 2 | 0 | 1.50 |
| 2 | QUBT | Quantum Computing Inc. | 8 | 2 | 3 | 1 | 2 | 0 | 1.38 |
| 3 | QBTS | D-Wave Quantum Inc. | 8 | 0 | 6 | 2 | 0 | 0 | 1.25 |
| 4 | RGTI | Rigetti Computing, Inc. | 9 | 4 | 4 | 0 | 0 | 1 | 0.50 |
| 5 | IONQ | IonQ, Inc. | 8 | 5 | 3 | 0 | 0 | 0 | 0.38 |

## Per-ticker findings

### ARQQ — Arqit Quantum Inc.

- **Filing analyzed:** `0001104659-25-119500_20-F.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=1, MODERATE=4, SEVERE=1, RED_FLAG=2, UNVERIFIABLE=0
- **Composite severity:** 1.50

#### 🔴 RED_FLAG_NEGATIVE claims
- **C5** — Total revenue FY2025 was $530K (FY24: $293K; FY23: $640K); one customer represented >56% of FY25 revenue.
  - M-check: `Intrinsic to filing: Note 2 Revenue + Note 23 Retained earnings (cohort heuristics 10 and 11)`
  - M-value: Cumulative retained-earnings deficit $373.8M against TTM revenue of $530K; revenue actually FELL from $640K (FY23) to $293K (FY24) and only partially recovered. Largest 'multi-year' contract is one customer at $297K.
  - Interpretation: Heuristic 11 (revenue-recognition pattern): the qualitative claims about 'first U.S. Department of War contract', 'largest license contract' to a Middle East government, OEM channels with Juniper/Fortinet/Cisco, and major partner programs (Oracle Defense Ecosystem, Vodafone Tomorrow Street) are RADICALLY out of proportion to GAAP revenue. After 4+ post-deSPAC years, a quantum-encryption software c
- **C7** — Prior-period restatement of FY24/FY23 for IFRS 2 share-based-payment error; prior FY22 material weaknesses; 25-for-1 reverse share split (Sep 2024); $7.0M class-action settlement provision (Oct 2025 t
  - M-check: `Intrinsic to filing: Note 21 Prior period error, Risk Factors (material weakness), Definitions (Reverse Share Split), Note 25 Provisions`
  - M-value: Three distinct distress fingerprints stacked: (1) second restatement in this company's short public life (the 2022 financials were also restated; this 2025 filing now restates FY23 and FY24 for IFRS 2), (2) 25-for-1 reverse split — extreme ratio, characteristic of names that have lost 95%+ of de-SPA
  - Interpretation: Heuristic 10 (delisting / going-concern fingerprints) explicitly elevates these as claim-adjacent signals. The 25:1 reverse split alone implies the pre-split price was a small fraction of the $1 Nasdaq minimum-bid threshold. The repeated restatement pattern (FY21/FY22 originally; now FY23/FY24) plus prior material weaknesses indicates persistent internal-control issues. The class-action provision 
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C8** — Raised ~$37.18M via ATM Program in FY25 (1,959,420 shares); cash $36.978M at 9/30/25 vs $29.553M operating burn; net loss $35.343M.
  - Interpretation: Heuristics 10 and 11: a quantum-encryption software business that requires continuous ATM equity issuance to cover operating burn, with revenue still under $1M after five years public, is in structural distress regardless of management's going-concern reassurance. The auditor accepted the going-concern basis only on the back of management's 'ability to raise additional funding' — i.e., further ATM
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Arqit's first U.S. Department of War contract is in partnership with a large, leading U.S. IT vendor.
  - Interpretation: Indirect prime-contract structure (sub through unnamed IT vendor) makes USAspending absence non-disqualifying, but the lack of NAMED counterparty plus zero direct federal-recipient record means the dollar magnitude is almost certainly small. FY25 revenue of $530K corroborates that this contract is s
- **C2** — Arqit's largest license contract is a multi-year agreement via a Middle East IT vendor partner to several government agencies of a major Middle Eastern country.
  - Interpretation: The Middle East end customer and IT vendor partner are both unnamed, so EDGAR cannot CIK-restrict; and a Middle Eastern government's IT vendor often is not an SEC filer. Heuristic 7 caveats apply (non-US counterparty disclosure threshold weaker). However, the FY25 revenue table shows one customer at
- **C3** — NetworkSecure integrates with OEM firewalls, routers and edge platforms from Juniper, Fortinet, and Cisco.
  - Interpretation: Claim language is carefully scoped ('available to integrate with' — not 'commercially deployed by' or 'design-win at'). Under Heuristic 4 and Heuristic 7, technical-compatibility / 'integrates with' language is the weakest tier of partnership claim and does not require counterparty disclosure (the O
- **C6** — Selected as member of Oracle Defense Ecosystem (June 2025); joined Vodafone's Tomorrow Street Scaleup X 2025 cohort (August 2025).
  - Interpretation: Heuristic 4 (investment vs operating) and Heuristic 7 lower bound: 'membership in an ecosystem' and 'innovation-center cohort' are partner-program marketing relationships, not commercial design wins. The fact that neither Oracle nor Vodafone reference Arqit in any SEC filing is consistent with the p

### QUBT — Quantum Computing Inc.

- **Filing analyzed:** `0001213900-26-022417_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=2, MODERATE=3, SEVERE=1, RED_FLAG=2, UNVERIFIABLE=0
- **Composite severity:** 1.38

#### 🔴 RED_FLAG_NEGATIVE claims
- **C6** — Active securities-class-action + 4 shareholder derivative suits; 2nd amended complaint (Feb 13, 2026) alleges misrepresentations re: Quad M, QPhoton, NASA, millionways, TFLN foundry
  - M-check: `EDGAR FTS to confirm the named subjects of allegation are themselves disclosed by QUBT (and not a counterparty)`
  - M-value: {'securities_class_action_active': True, 'derivative_actions_n': 4, 'derivative_actions_status': 'stayed pending MTD', 'amended_complaint_dates': ['2025-08-26', '2026-02-13'], 'millionways_filing_hits_qubt_self': 16, 'bv_advisory_settlement_usd_cash': 750000, 'bv_advisory_settlement_shares': 1900000
  - Interpretation: Heuristic 10 (distress / going-concern fingerprints) explicitly satisfied: active 10b-5 securities class action alleging the Company misled investors on CUSTOMERS, CONTRACTS, and BUSINESS OPERATIONS during 2020-03-30 to 2025-01-15. The plaintiff's specifically-named subjects (NASA, TFLN foundry, QPhoton, millionways, Quad M) ALL recur in QUBT's own historical PR-cycle — confirmed by 16 QUBT-self f
- **C7** — NASA contract for imaging applications (per cohort metadata; not affirmatively disclosed in 10-K Item 1 Business or revenue notes)
  - M-check: `USAspending NASA-specific awarding-agency filter for 'Quantum Computing'`
  - M-value: {'nasa_contracts_n': 1, 'nasa_contracts_total_usd': 26163.2, 'nasa_award_id': '80NSSC25PA273', 'nasa_description': 'CONSULTING AND DEVELOPMENT SERVICES', 'nasa_mentions_in_10K_item1': 0, 'nasa_mentions_in_10K_revenue_notes': 0, 'nasa_mentions_in_10K_legal_proceedings': 'context of securities-class-a
  - Interpretation: HARD CONTRADICTION (Layer 3 Rule 7 + Heuristic 7 analogs): cohort metadata frames 'NASA contract for imaging applications' as a major narrative claim. Reality per USAspending: one $26,163.20 consulting/development award, with no NASA imaging program of record. The 10-K itself does NOT affirmatively claim a NASA imaging contract in Item 1 Business or revenue notes — NASA appears in the 10-K only in
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C5** — FY2025 total GAAP revenue $682K (Services $368K + Products $314K) vs $1,475.1M equity raised in FY2025; cash & investments ~$1.52B at YE2025
  - Interpretation: Heuristic 11 (revenue-recognition pattern, quantum-specific) and Heuristic 4 (investment vs operating) both triggered: $1.475B of equity raised in a single year to support $682K of revenue is an extreme equity-to-revenue ratio (~2,163x). Federal-contract corroboration confirms the picture — only ~$96K of cumulative federal contract awards over 6 years, with no DARPA / AFRL / national-lab programs.
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Dirac-3 EQC launched Q1 2024 and is available as cloud + on-prem product; Dirac-4 in development
  - Interpretation: Product exists as a marketing/PR construct (QUBT's own 8-Ks and 10-Qs reference Dirac-3 and Entropy Quantum). No third-party 10-K filer (hyperscaler, defense prime, national lab, customer) corroborates Dirac-3 by name. Stage-ladder discipline (Heuristic 3): announced/launched != benchmarked at claim
- **C2** — AZ Chips TFLN facility substantially completed March 2025; FAB 2 in planning
  - Interpretation: EPA FRS absence is per Heuristic 1 not a red flag (small-batch / outsourced TFLN). Filing itself describes a 9,261 sq ft leased space in a multi-tenant building — a prototyping line, not a production fab. Phrase 'TFLN foundry' appears only in QUBT's own filings (no industry partner / customer / fabl
- **C8** — Neurawave (photonics-based reservoir computer) launched November 2025; Emucore RC launched June 2023
  - Interpretation: Both Neurawave (Nov 2025) and Emucore (Jun 2023) are real product launches per QUBT's own filings, but no external counterparty (customer, partner, integrator) corroborates either by name across all EDGAR filers. Stage-ladder Heuristic 3: 'launched' is consistent with announce/PR-stage; the products

### QBTS — D-Wave Quantum Inc.

- **Filing analyzed:** `0001907982-26-000026_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=0, MODERATE=6, SEVERE=2, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 1.25

#### 🟠 SEVERE_UNDERDELIVERY claims
- **QBTS-5** — FY2025 GAAP revenue of $24.6M (vs $8.8M FY2024); net loss $355.1M; accumulated deficit $982.0M.
  - Interpretation: Revenue is verifiably non-zero (real engagements with named customers), but the gap between commercial-stage marketing rhetoric ('the only commercial-grade quantum computing supplier with proven customers and production deployments') and the GAAP financial reality ($24.6M revenue, $355M annual loss, ~285x P/S multiple) is the canonical Quantum-vertical pattern. Calibration Heuristic 11 (revenue-re
- **QBTS-8** — Net cash from financing activities of $779.1M in FY2025 — completed 100% of FOUR ATMs ($100M + $75M + $150M + $400M) plus $202.9M from warrant exercises — while shares outstanding grew from ~192M weig
  - Interpretation: Calibration Heuristic 10 (delisting / distress fingerprints) and Heuristic 11 (revenue-recognition divergence) are both implicated. Raising ~$779M in equity in a single fiscal year while generating $24.6M of revenue, plus the immediate deployment of $250M of that cash into a balance-sheet-pivot acquisition (Quantum Circuits), is the classic 'capital markets are the real business model' pattern. Th
#### 🟡 MODERATE_UNDERDELIVERY claims
- **QBTS-1** — D-Wave claims headline commercial customers including Mastercard, Pfizer, BASF, NTT DOCOMO, Davidson Technologies, etc. as 'blue-chip enterprise companies'.
  - Interpretation: Layer 3 Rule 7 (counterparty-disclosure threshold) — Mastercard, a $400B+ market-cap counterparty, makes ZERO mention of D-Wave in any SEC filing. External cross-filer corroboration is essentially nil — virtually every public mention of D-Wave / Leap originates with D-Wave itself. This is the canoni
- **QBTS-2** — D-Wave's Leap and Advantage/Advantage2 systems are available via AWS Marketplace.
  - Interpretation: Layer 3 Rule 7 reading: distribution-via-AWS-Marketplace is a partner-ecosystem relationship, not a deployment/revenue claim. D-Wave's framing is 'access can be purchased ... through AWS Marketplace' which is precisely the 'available via / partner ecosystem' wording the heuristic flags as MODERATE r
- **QBTS-3** — D-Wave demonstrated 'quantum supremacy on useful real-world problem' in March 2025 using 1,200 qubit Advantage2 prototype, peer-reviewed in Science.
  - Interpretation: The IP footprint is genuine (PASS on patent depth). However, per the Quantum-vertical-specific risk rubric: 'quantum supremacy / quantum advantage' is research-paper jargon that does NOT correspond to any commercial deployment milestone. The Science paper is real, but a published demonstration on a 
- **QBTS-4** — Advantage2 (sixth-gen annealing) launched May 2025 with 'more than 4,400 qubits' available via Leap cloud, claimed as 'the world's largest' QPUs.
  - Interpretation: The qubit count claim is technically defensible — D-Wave's annealing architecture does provide thousands of *physical* qubits, but this is fundamentally different from gate-model qubit counts. Per Calibration Heuristic 9, headline qubit counts that conflate physical with logical qubits are MODERATE.
- **QBTS-6** — Completed acquisition of Quantum Circuits, Inc. on Jan-20-2026 for $250M cash + 10.43M shares (~$455M total at the Feb-25-2026 $19.65 price), pivoting D-Wave into error-corrected gate-model technology
  - Interpretation: Calibration Heuristic 10 reading: 'large balance-sheet-pivot acquisitions are distress markers' — a $250M+ cash spend (more than 10x FY25 revenue) on a private gate-model startup that lacks any independent third-party SEC disclosure history is precisely the balance-sheet-pivot pattern the heuristic 
- **QBTS-7** — D-Wave generates revenue from 'research, academic, and government customers' purchasing on-premises Advantage2 systems.
  - Interpretation: The 10-K explicitly cites 'government customers' as a revenue source for on-prem Advantage2 system sales, but USAspending shows ZERO US federal contracts or grants to D-Wave under any naming variant. This does not rise to RED_FLAG under Layer 3 Rule 7 (D-Wave is a Canadian-headquartered company and 

### RGTI — Rigetti Computing, Inc.

- **Filing analyzed:** `0001104659-26-023454_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=4, MODERATE=4, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.50

#### 🟡 MODERATE_UNDERDELIVERY claims
- **RGTI-1** — Distribution agreement with Amazon Braket; 84-qubit Ankaa-3 available on AWS Braket.
  - Interpretation: Layer-3 Rule 7: hyperscaler distribution exists historically but is immaterial to Amazon. Rigetti's language is 'available via Braket', not 'commercial revenue from AWS-as-customer', so this is the MODERATE bucket per the rubric (distribution real, revenue scale tiny) — consistent with the 10-K desc
- **RGTI-2** — Distribution agreement with Microsoft Azure Quantum.
  - Interpretation: Counterparty disclosure threshold: a $3T issuer would not typically itemize one quantum partner, so absence alone is not RED. But Microsoft's complete silence on its own 'Azure Quantum' product line in SEC filings indicates Azure Quantum is a tiny, R&D-stage offering — Rigetti's revenue contribution
- **RGTI-5** — $8.4M C-DAC India purchase order (Jan 2026) for 108-qubit system, 2H 2026 deployment.
  - Interpretation: Calibration heuristic 3 (planned vs operational): the C-DAC system is *contracted to deliver* in 2H 2026 — i.e. fabricated-but-not-yet-deployed at filing date. The 108-qubit fidelity (99.0%) is at the level the 84-qubit Ankaa-3 hit, well below the 99.9% needed for QA. The $8.4M revenue won't show up
- **RGTI-8** — 84-qubit Ankaa-3 (99.0% 2Q fidelity) and 36-qubit Cepheus-1-36Q (99.6% 2Q fidelity) deployed on QCS.
  - Interpretation: Calibration heuristic 3 (planned vs operational) + heuristic 9 (physical vs logical): all reported qubit counts are PHYSICAL. Heuristic 11 (revenue recognition): only $5.7M in 2025 Novera POs and $8.4M C-DAC order — tiny relative to capex and burn. The headline qubit numbers are real fabricated syst

### IONQ — IonQ, Inc.

- **Filing analyzed:** `0001193125-26-071562_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=5, MODERATE=3, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.38

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — IonQ's quantum computing solution is currently delivered via AWS Amazon Braket, Microsoft Azure Quantum, and Google Cloud Marketplace.
  - Interpretation: Hyperscaler distribution is technically real (Braket/Azure/GCP do list IonQ in marketing pages) but none of the three $1T+ hyperscalers consider IonQ material enough to mention in any SEC filing post-2020. Per Heuristic 7, this is the 'available via partner ecosystem' pre-deployment pattern: the cha
- **C4** — IonQ reported GAAP revenue of $130.0M for FY2025, up from $43.1M in FY2024 (~3.0x).
  - Interpretation: GAAP revenue jumped 3x to $130M while only $13M shows in direct federal prime-contract awards. A material share of the FY25 revenue jump is plausibly driven by the 2025 acquisitions rather than organic trapped-ion quantum-computer revenue. Per Heuristics 11 and 4 (acquisitive growth obscures organic
- **C6** — Net loss attributable to IonQ was $510.4M in 2025 (vs $331.6M in 2024 and $157.8M in 2023); accumulated deficit $1,194.1M as of Dec 31, 2025; net cash used in operations $283.2M in 2025.
  - Interpretation: Losses are real and audited (no contradiction, hence supports=true). MODERATE_UNDERDELIVERY because: (a) loss-to-revenue ratio of 3.9x is consistent with pre-commercialization research stage despite the 'we sell to customers' framing in Item 1, (b) operating cash burn nearly tripled YoY in 2025 even

## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### ARQQ
- Composite: **1.50**   RED_FLAGs: 2   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=12.4%   inst_own=26%   recom=1.00
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months of 2026-05-16, at least one of the following occurs: (a) the next 10-K/10-Q/20-F materially restates the RED_FLAG claim; (b) the company announces a strategic pivot away from the disputed claim; (c) the counterparty publicly contradicts the company's representation; (d) the company files Form 15-12G / 25-NSE / Chapter 11; (e) the stock falls >50% from cutoff price.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### QUBT
- Composite: **1.38**   RED_FLAGs: 2   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=30.1%   inst_own=42%   recom=1.67
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### QBTS
- Composite: **1.25**   RED_FLAGs: 0   SEVERE: 2   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=14.6%   inst_own=47%   recom=1.27
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### RGTI
- Composite: **0.50**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=15.5%   inst_own=53%   recom=1.77
- **Decision: no bet.** Composite 0.50 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### IONQ
- Composite: **0.38**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=23.0%   inst_own=56%   recom=1.43
- **Decision: no bet.** Composite 0.38 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** RED_FLAG_NEGATIVE means filings diverge from independent registries at the cutoff; legitimate reasons exist (e.g. confidential cloud-distribution agreements, early-stage government grants flow-through, foreign-jurisdiction national-lab work).
- **Not a trade recommendation.** Quantum names trade on narrative cycles; even high-Truth_signal + high-Discovery_advantage names can squeeze hard.
- **Not pre-registered.** Commit this report's hash to git for honest forward-bet bookkeeping.

## Debt and tradeoffs

- **HELD-OUT cohort = real validation, not perfect.** If the emission decisions on this cohort match what a discretionary analyst would have called pre-cutoff, the calibration heuristics generalize. If they diverge, calibration is overfit to the prior cohorts and needs refactoring (e.g. extracting per-cohort heuristic blocks into structured config rather than free-text prompt).
- **Coverage gaps surfaced by subagents** will be captured in `connectors_to_add.md` (NIST quantum-program docket, DARPA ONISQ program list, AFRL Information Directorate / IARPA quantum program registries, hyperscaler partner-page scrapes for AWS Braket / Azure Quantum / GCP Quantum AI).
