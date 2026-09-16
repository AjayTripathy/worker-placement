# AI Data-Center / Crypto-Pivot Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T22:14:04.544830Z — cutoff 2026-05-16_

## Methodology

Seven names spanning AI-DC crypto-pivots and mature DC-REIT controls: CIFR / IREN / APLD / CORZ / BTDR (crypto-miner pivots) + EQIX / DLR (controls). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch access, no shared context. Subagent workflow includes checkpointing.

AI-DC-specific calibration emphasis: **TCV-vs-current-period-revenue conflation** (Heuristic 9). AI-DC pivot names routinely headline multi-billion-dollar contract values that span 10-15 years while only a small fraction is currently energized and revenue-bearing. The hyperscaler counterparty-disclosure threshold (Rule 7) is the killer cross-check — hyperscaler 10-Ks discuss data-center capex commitments and should name material partners at scale.

**CoreWeave exception:** CoreWeave is private and won't appear in EDGAR; CoreWeave-named contracts are UNVERIFIABLE on the counterparty axis. APLD and CORZ have major CoreWeave deal claims that fall into this coverage gap.

Forward-bet emission uses the shared v2 emitter (`forward_bet_emission.py`): composite >= 0.6 AND discovery_advantage_tier IN {HIGH, MED}.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | BTDR | Bitdeer Technologies Group | 9 | 1 | 4 | 3 | 1 | 0 | 1.44 |
| 2 | IREN | Iris Energy Limited | 8 | 0 | 5 | 1 | 0 | 2 | 1.17 |
| 3 | APLD | Applied Digital Corp. | 8 | 1 | 4 | 2 | 0 | 1 | 1.14 |
| 4 | CORZ | Core Scientific, Inc. | 10 | 4 | 2 | 3 | 1 | 0 | 1.10 |
| 5 | CIFR | Cipher Mining Inc. | 6 | 1 | 5 | 0 | 0 | 0 | 0.83 |
| 6 | EQIX | Equinix, Inc. | 8 | 8 | 0 | 0 | 0 | 0 | 0.00 |
| 7 | DLR | Digital Realty Trust, Inc. | 8 | 8 | 0 | 0 | 0 | 0 | 0.00 |

## Per-ticker findings

### BTDR — Bitdeer Technologies Group

- **Filing analyzed:** `0001213900-26-049770_20-F.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=1, MODERATE=4, SEVERE=3, RED_FLAG=1, UNVERIFIABLE=0
- **Composite severity:** 1.44

#### 🔴 RED_FLAG_NEGATIVE claims
- **C8** — Heavy related-party financial dependence on BIT Group (chairman Jihan Wu is co-founder/chairman of BIT Group): $521.8M borrowings; $135.6M crypto receivable; new 6,000 BTC facility Feb-Mar 2026; subst
  - M-check: `edgar_fts 'Jihan Wu' / 'BIT Group Bitdeer' / 'Matrixport'`
  - M-value: 'Jihan Wu' returns 34 EDGAR hits, dominated by BTDR's own 20-F exhibits/certifications and a related Mercurity Fintech filing; no independent counterparty corroboration of BIT Group as a financing source; the structure is disclosed solely by BTDR.
  - Interpretation: Calibration #10 (distress fingerprints): structurally circular financing — BIT Group (controlled by chairman) is simultaneously (a) custodian of substantially all BTDR cryptocurrencies, (b) the largest single lender ($521.8M out of $1.0B total borrowings), (c) the counterparty for BTC-denominated put-option premium ($6.4M Feb 2026), and (d) the counterparty for a 6,000 BTC structured facility ente
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C3** — Clarington, OH 570 MW under contract with local utility for colocation; AHP litigation may delay timing.
  - Interpretation: BTDR claims 570 MW power 'under contract' but provides no utility name and no third party (utility, IOU, or counterparty) corroborates a 570 MW load in EDGAR. The site is in active litigation with energization 'to be updated' (i.e., indefinite). The 'colocation' usage label has no named customer. Calibration #3 stage-ladder analysis: this is at most a power MOU stage, not lease/shell/energized. SE
- **C5** — BTDR offers AI cloud services in Asia powered by NVIDIA DGX SuperPOD H100/H200/B200 + GB200 NVL72; AI cloud revenue FY2025 = US$6.769M (1.1% of $620M total).
  - Interpretation: AI-pivot narrative is loud (153 mentions of 'AI cloud' / 'AI infrastructure' across the 20-F) but actual revenue is tiny ($6.8M, 1.1%). Calibration #11 (rev-rec pattern) and Calibration #3 (planned vs operational) both apply. NVIDIA does not corroborate the SuperPOD/GB200 deployment in its own filings — these are likely commercial purchases (not strategic-partner status). Two AI-cloud datacenters 
- **C9** — Cash dropped from $476.3M to $149.4M (Dec 2025); FY2025 operating cash burn $1.74B; financed in 2025 via $751M converts net + $668M RPT loans + $351M equity issuance, plus $375M Feb 2026 5.00% convert
  - Interpretation: Calibration #10: heavy/serial convertible issuance ($200M Aug-2024, $200M Nov-2024, $375M Jun-2025, $400M Nov-2025, $375M Feb-2026 = $1.55B aggregate principal of converts in ~18 months) plus $668M RPT loans plus $351M ATM/registered direct equity issuance is classic AI-DC distress-financing footprint. Embedded derivative accounting drove a $444.9M non-cash adjustment that produced BTDR's $65.6M *
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — 1,744 MW aggregate operating capacity across 10 datacenters as of March 31, 2026; 1,259.5 MW pipeline; 3,003.5 MW total potential.
  - Interpretation: Operating MW figure is large (1,744) but breakdown shows it is overwhelmingly BTC-mining capacity (Rockdale 563, Bhutan 600, Norway 309, Ohio 121, Ethiopia 50). Only Cyberjaya 2 MW is explicitly AI-cloud. Calibration #11: legacy crypto floor space is not equivalent to AI capacity. Total 'pipeline' i
- **C2** — Massillon, Ohio operational 121 MW with 26 MW fire-damaged (Nov 2025) and 74 MW additional phases Q2 2026.
  - Interpretation: Site is genuinely operational (impairment recorded; specific MW disclosed; insurance recovery in progress). But: (i) Nov 2025 fire damaged ~26 MW; (ii) usage labeled 'Crypto' not AI per the site chart; (iii) timeline for 74 MW phase-in is Q2 2026. MODERATE underdelivery: a real, in-use site, but wit
- **C4** — Niles, OH 300 MW grid-interconnected site (41.8 acres owned) with utility transmission-line extension agreement, intended for colocation/AI cloud, Q4 2028 energization.
  - Interpretation: Land-owned + transmission-line agreement is an early-but-legitimate development-stage milestone. However Q4 2028 energization is 2.5+ years out; no named customer; usage labeled 'Colocation / AI cloud' (not yet bound). Calibration #3: term-sheet/early-development stage. MODERATE: real grid-interconn
- **C7** — Customer concentration: 4 unnamed customers each >10% of FY2025 revenue (B 16.65%, C 15.81%, D 12.20%, E 10.28%), aggregating ~55% of $620M revenue; Customer A (related party) was 19.05% of FY2023; no
  - Interpretation: Four customers each >10% in FY2025 implies real concentration risk but none are named. Customers B/C/D/E most likely include: SEALMINER bulk-order buyers (FY2025 mining-rig revenue surged to $108M from <$1M), cloud-hash-rate sub buyers, and large hosting clients. None are hyperscalers (corroborated 

### IREN — Iris Energy Limited

- **Filing analyzed:** `0001878848-26-000026_10-Q.txt (FY26 Q3 10-Q, period ending 2026-03-31, filed 2026-05-08); cross-referenced with 0001878848-25-000063_10-K.txt (FY25 10-K, period ending 2025-06-30)`
- **Claims extracted:** 8
- **Severity distribution:** PASS=0, MODERATE=5, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 1.17

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C6** — >$7B fresh capital (debt + equity) raised in <18 months: $3.69B convertibles outstanding at Mar 31 2026 + $3.0B 2031 Convert issued May 14 2026 + $635M ATM equity through Aug 2025.
  - Interpretation: Funding cadence is consistent with a company racing to fund a capex commitment that exceeds current cash flow capacity. Capped call + prepaid forward structures on each convertible tranche reduce dilution mechanics but also signal management acutely concerned about share-price-sensitive dilution. Convertible-debt levels ($7.3B principal) now substantially exceed market cap-implied operating cash f
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Microsoft Agreement: $9.7B TCV over ~5 years, signed Nov 2 2025, dedicated GPU services at Childress; zero tranches delivered/accepted as of Mar 31 2026; no Microsoft RPO recognized.
  - Interpretation: CRITICAL: IREN claims a $9.7B 5-year dedicated GPU services contract with Microsoft, yet zero corroboration in Microsoft's EDGAR filings. Combined with the fact that zero tranches have been delivered/accepted, no Microsoft consideration is in RPO, the related $3.6B GS/JPM financing remains a non-bin
- **C2** — 4,510MW grid-connected power capacity claim with new 1,600MW Oklahoma site added since FY25 year-end.
  - Interpretation: The 4,510MW headline conflates: 810MW operating + 75MW Childress Horizon 1 under construction + 1,400MW Sweetwater 1 substation under construction + ~2,225MW that is at LOA / connection-agreement-signed / development stage including the new 1,600MW Oklahoma site whose connection rights amortization 
- **C3** — Childress Horizon 1-4 liquid-cooled AI data centers under construction; Horizon 1 (~50-75MW) targeted CY2025 energization to support the Microsoft Agreement.
  - Interpretation: 10-K target was Horizon 1 energization by end of CY2025 to begin AI hosting deliveries. As of the 10-Q reporting date 2026-03-31, no Microsoft tranches have been delivered or accepted — implying the Horizon 1 facility has slipped or is not yet generating Microsoft revenue. The Horizons 2-4 facilitie
- **C5** — Q3 FY26 revenue $144.8M (flat YoY), net loss $(247.8)M, Adj EBITDA $59.5M (down from $83.1M); Microsoft contribution = $0 (nil tranches delivered).
  - Interpretation: Per Heuristic 11, revenue mix has not yet shifted to AI Cloud Services despite the company's pivot narrative and $9.7B Microsoft contract. Headline 'AI Cloud provider' branding is not yet supported by recognized revenue. Quarter shows widening losses and Adj EBITDA contraction. MODERATE — disclosure
- **C7** — Two M&A transactions in the four days immediately preceding the May 11-14 2026 $3B convertible offering: Mirantis ($625M ~90% stock) on May 4 and Ingenostrum/Nostrum Group (~EUR 165M) on May 7.
  - Interpretation: Two acquisitions announced in four days, immediately followed by a $3B convertible raise on May 11-14, suggests a deliberate sequencing of news flow ahead of a capital raise. Mirantis is paid ~90% in IREN stock (price-sensitive), Ingenostrum is 65% cash / 35% stock. The Spanish DC pipeline (490MW) a

### APLD — Applied Digital Corp.

- **Filing analyzed:** `0001144879-25-000021_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=1, MODERATE=4, SEVERE=2, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 1.14

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C6** — Capital structure: $450M 2.75% Convertibles (June 2030), $375M SMBC Loan (August 2026 maturity), Macquarie/SMBC refinancing chain, $160M PIPE at $3.24, multiple preferred series (E/E-1/F/G), $193.9M p
  - Interpretation: SEVERE per heuristic 10 distress fingerprints. The pattern -- repeated bridge financings within 12 months, 76% one-year share-count dilution, running out of authorized shares mid-derivative-settlement, August 2026 SMBC wall against a still-not-yet-cash-flow-positive HPC build, and reliance on continued ATM sales -- is consistent with a structurally undercapitalized issuer that needs the HPC ramp t
- **C7** — March 30, 2026 CoreWeave lease restructuring: Building 2 term suspended on two of four data halls (replaced by a parallel SPV lease); Building 3 lease assigned entirely to CoreWeave SPV (Compute Acqui
  - Interpretation: SEVERE per heuristic 7 logic adapted for an UNVERIFIABLE counterparty. The economic substance is: 14 months after signing, CoreWeave (a) suspended half the term on half the data halls of Building 2, (b) substituted an SPV with a springing-only parent guaranty on Building 3. This is a clear weakening of CoreWeave's commitment to take MW. The framework's stage-ladder (term sheet -> definitive lease 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — January 13, 2025 Unit Purchase Agreement with Macquarie Asset Management (MIP VI HPC Holdings, LLC) to sell HPC Hosting Business interest, conditioned on hyperscaler lease execution at the first 100 M
  - Interpretation: The 'sale of HPC Hosting to Macquarie' did NOT close (CoreWeave is not the hyperscaler form MAM contemplated; the deadline lapsed). APLD continues to consolidate HPC Hosting and is borrowing rather than selling. This is a MODERATE under-delivery against the FY25-headline plan; not strictly a contrad
- **C4** — HPC Hosting Business has a single counterparty (CoreWeave) on 15-year leases for 100% of contracted base, with no diversification.
  - Interpretation: MODERATE because (a) the entire HPC story is single-counterparty risk on a still-private neocloud (CoreWeave's own financial health is itself dependent on hyperscaler demand and Nvidia capacity allocation); (b) the March 30, 2026 SPV substitution + springing guaranty is a clear credit-quality DETERI
- **C5** — Material weakness in ICFR (complex financial instruments) and DCP not effective as of May 31, 2025; multiple prior material weaknesses (segregation of duties, related party transactions, financial rep
  - Interpretation: MODERATE: this is a non-trivial open control gap on a company with $450M of convertibles and several preferred series in flight. The same control area (complex financial instruments) directly produced an $89.6M loss event in FY25, so the weakness is not merely theoretical. Management commits to reme
- **C8** — FY26 YTD HPC revenue of $182.3M (Building 1 operating), of which $118.2M (65%) is tenant fit-out services, $55.7M (30%) is base rent, $8.4M (5%) is power pass-through. Q3 split is 28% fit-out / 62% re
  - Interpretation: MODERATE per heuristic 9 (TCV vs current-period revenue conflation) AND heuristic 11 (revenue-recognition pattern). Reporting tenant fit-out at gross (as $118M of revenue with offsetting cost of revenues) inflates the apparent top-line ramp of the HPC business in headline numbers; the true recurring

### CORZ — Core Scientific, Inc.

- **Filing analyzed:** `0001628280-26-013305_10-K.txt`
- **Claims extracted:** 10
- **Severity distribution:** PASS=4, MODERATE=2, SEVERE=3, RED_FLAG=1, UNVERIFIABLE=0
- **Composite severity:** 1.10

#### 🔴 RED_FLAG_NEGATIVE claims
- **C6** — Company identified a material weakness in internal control over financial reporting as of December 31, 2025 related to accounting for demolished property/equipment during HDC conversion; concurrently 
  - M-check: `Calibration Heuristic 10 (going-concern/control fingerprints) hard trigger. A post-emergence company with an adverse ICFR opinion AND a four-period restatement AND material weakness AND a restated FY2024 (its first full post-emergence year) is exhibiting clear financial-reporting distress. The restatement is specifically about the conversion process — meaning the central strategic claim (mass HDC conversion) is the same thing that the controls failed to account for properly.`
  - M-value: material_weakness_flag=TRUE; restated_periods=4 (FY24 10-K/A + Q1/Q2/Q3 2025 10-Q/A); auditor_adverse_opinion_on_ICFR=TRUE; disclosure_controls_ineffective=TRUE; remediation_in_progress=TRUE (not yet remediated)
  - Interpretation: RED FLAG. This is a textbook combination: (a) restated post-emergence financials, (b) adverse auditor opinion on ICFR, (c) material weakness directly in the asset class being most aggressively transformed (PP&E conversion from BTC to HDC), and (d) disclosure controls also ineffective. Per Heuristic 10, this is a hard fingerprint of distress and a forward-looking risk that the conversion-related ca
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C4** — Colocation segment revenue is 100% concentrated with a single customer (Customer J = CoreWeave); Customer F became a minority shareholder on the Effective Date and was 31% of Digital Asset Hosted Mini
  - Interpretation: Customer-concentration risk is acknowledged in the filing (good disclosure), but the substantive risk is SEVERE: (1) 100% of the AI/HDC pivot rides on one private counterparty; (2) that counterparty just attempted and failed to acquire CORZ, leaving the commercial relationship intact but the strategic relationship strained; (3) hyperscaler downstream demand (Microsoft) does not even acknowledge Co
- **C5** — Total revenue declined to $319.0 million in 2025 from $510.7 million in 2024; Adjusted EBITDA collapsed to $29.7 million in 2025 from $157.4 million in 2024; operating loss expanded to $245.6 million 
  - Interpretation: This is the central financial-distress signal: the company is mid-pivot and the new business (HDC/colocation) is not yet generating enough revenue to replace the legacy business (BTC mining) that is being dismantled. With $1.4B+ committed capex and ~$533M liquidity, the operating-loss trajectory means CORZ has roughly 12-18 months of runway before requiring substantial external financing. SEVERE_U
- **C9** — Company holds 2,537 bitcoin worth $222.0 million at year-end 2025; intends to monetize substantially all bitcoin holdings during 2026 (mostly Q1) to fund planned capex; already sold 1,924 BTC for $175
  - Interpretation: SEVERE_UNDERDELIVERY. Selling 76% of the BTC stack in <2 months and stating intent to sell substantially all of it during 2026 is a clear forced-liquidation pattern, not a treasury-management decision. Combined with cash decline ($836M -> $311M YoY) and material weakness/restatement, this puts CORZ in a position where any colocation revenue shortfall, customer prepayment delay, or capex overrun wo
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — Company has $989.8 million of contractually committed capital expenditures as of December 31, 2025 (with $716.8M passed through to customer as invoiced), plus an additional $418.1 million committed th
  - Interpretation: Capex commitments are real and disclosed in good faith, BUT the financing math is tight: net company-funded capex (~$584M after pass-through to customer) materially exceeds year-end cash+BTC (~$533M). Mgmt's 'next 12 months sufficient liquidity' assertion depends on (a) monetizing essentially all BT
- **C8** — In January 2026 (subsequent event), Company entered a long-term power supply arrangement obligating it to purchase firm utility power capacity beginning in 2028; made an $80 million cash deposit into 
  - Interpretation: MODERATE_UNDERDELIVERY. The disclosure itself is honest, but the move further stresses liquidity: an additional $80M restricted (on top of $1.4B in committed capex) for capacity that does not generate revenue until 2028. This is consistent with growing reliance on customer prepayments and BTC moneti

### CIFR — Cipher Mining Inc.

- **Filing analyzed:** `0001819989-26-000009_10-K.txt`
- **Claims extracted:** 6
- **Severity distribution:** PASS=1, MODERATE=5, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.83

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — 15-year, 300 MW Black Pearl HPC lease with Amazon Web Services; phased delivery commencing 2026.
  - Interpretation: Lease is real and disclosed in Cipher's 10-K with specificity (Cipher Black Pearl LLC subsidiary, 15-year term, 300 MW, phased delivery). Counterparty side: Amazon doesn't name Cipher in its filings — but Amazon rarely names individual DC lessors and a 300 MW lease (vs Amazon's hundreds of GW of glo
- **C2** — Long-term HPC lease with Fluidstack USA II Inc. at 300 MW Barber Lake Facility; backstopped by Google LLC via Lease Recognition Agreement plus Google Warrants (exercise period to Sept 2030).
  - Interpretation: The structure is layered: Cipher's primary tenant is a private neocloud (Fluidstack), with Google providing only a contingent backstop. Google's commitment is sized to the lease payments and is presumably below Alphabet's materiality threshold (Alphabet does not disclose individual lease-backstop ob
- **C3** — 4.2 GW portfolio across 10 sites: 207 MW operating BTC (Odessa); 600 MW HPC under development (Barber Lake 300 + Black Pearl 300); 3.4 GW pipeline across seven Texas sites + one Ohio site.
  - Interpretation: 207 MW operating + 600 MW under-construction is supported by Cipher's own contemporaneous 8-Ks (interconnection approvals, lease executions). But the 3.4 GW pipeline figure — '7 Texas sites + 1 Ohio site' — is mostly LAND OPTIONS or early-stage development without confirmed interconnect approvals no
- **C5** — Cipher raised ~$3.2B in 2025 (172.5M 2030 converts + $1.3B 2031 0% converts + $1.733B 7.125% 2030 senior secured notes at Cipher Compute SPV); subsequent $2.0B 6.125% 2031 senior secured notes at Blac
  - Interpretation: Capital structure is leveraged but cleanly disclosed and well-corroborated by external evidence (high 8-K frequency for note issuances; SPV-level financing structure that requires lender diligence on site rights). No distress fingerprints per Heuristic 10. HOWEVER, Heuristic 11 applies: 100% of reco
- **C6** — Construction commitments of $713.5M (mostly Barber Lake, fully funded with restricted cash); Black Pearl BTC mining ceased early 2026 awaiting HPC lease commencement mid-2026; AWS/Fluidstack-Google re
  - Interpretation: Cipher's disclosure is reasonably good on the construction-cost side ($713.5M committed, fully funded with restricted cash from the SPV note proceeds) and on stage-ladder language ('phased delivery', 'rent commencement'). But Heuristic 9 applies (TCV-vs-recognized-revenue): the company narratively c

### EQIX — Equinix, Inc.

- **Filing analyzed:** `0001101239-26-000032_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=8, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


### DLR — Digital Realty Trust, Inc.

- **Filing analyzed:** `0001104659-26-015365_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=8, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### BTDR
- Composite: **1.44**   RED_FLAGs: 1   SEVERE: 3   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=41.8%   inst_own=41%   recom=1.36
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### IREN
- Composite: **1.17**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=18.0%   inst_own=45%   recom=1.88
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### APLD
- Composite: **1.14**   RED_FLAGs: 0   SEVERE: 2   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=30.9%   inst_own=70%   recom=1.00
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### CORZ
- Composite: **1.10**   RED_FLAGs: 1   SEVERE: 3   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=21.8%   inst_own=113%   recom=1.18
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### CIFR
- Composite: **0.83**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=16.8%   inst_own=63%   recom=1.00
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### EQIX
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=1.9%   inst_own=99%   recom=1.48
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### DLR
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=2.2%   inst_own=99%   recom=1.65
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** RED_FLAG_NEGATIVE means filings diverge from registries at the cutoff.
- **CoreWeave gap.** CoreWeave is private; deals with it are structurally UNVERIFIABLE in EDGAR. Coverage limitation, not verdict.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **CoreWeave UNVERIFIABLE gap** is the largest coverage gap for this cohort. A connector for CoreWeave's senior-secured-note indenture filings (CoreWeave issued $7.5B in senior secured notes in 2024-2025 across multiple deals) would partially close this — CoreWeave's hosting-customer obligations would appear in those indentures.
- **Utility-side grid-interconnect filings** (utility-regulator filings at state PUCs for MW-scale interconnect) are off-EDGAR; verifying claimed grid interconnect requires per-state PUC scraping.
