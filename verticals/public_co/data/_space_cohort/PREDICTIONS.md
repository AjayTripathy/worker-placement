# Space / Satcom Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T08:31:59.388418Z — cutoff 2026-05-16_

## Methodology

Six names spanning space-launch (RKLB Rocket Lab), direct-to-mobile sat (ASTS AST SpaceMobile), space-infrastructure (RDW Redwire), earth-observation (PL Planet Labs), satcom (SATS EchoStar), and mature LEO-constellation control (IRDM Iridium). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch, no shared context. Subagent workflow includes checkpointing.

Space-specific calibration emphasis: **constellation-announced vs constellation-operational** (Heuristic 9). Sat-network claims routinely conflate test-sats, on-orbit-but-pre-commercial, and commercial-service-active. Federal-contract claims (NASA, USSF, DARPA, NOAA) are USAspending-verifiable at the program level.

Forward-bet emission uses the shared v2 emitter.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | RDW | Redwire Corp. | 8 | 3 | 3 | 1 | 0 | 1 | 0.71 |
| 2 | ASTS | AST SpaceMobile, Inc. | 8 | 5 | 3 | 0 | 0 | 0 | 0.38 |
| 3 | SATS | EchoStar Corporation | 8 | 6 | 1 | 1 | 0 | 0 | 0.38 |
| 4 | RKLB | Rocket Lab USA, Inc. | 8 | 6 | 1 | 0 | 0 | 1 | 0.14 |
| 5 | PL | Planet Labs PBC | 8 | 6 | 1 | 0 | 0 | 1 | 0.14 |
| 6 | IRDM | Iridium Communications Inc. | 8 | 7 | 1 | 0 | 0 | 0 | 0.12 |

## Per-ticker findings

### RDW — Redwire Corp.

- **Filing analyzed:** `0001819810-26-000029_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=3, MODERATE=3, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.71

#### 🟠 SEVERE_UNDERDELIVERY claims
- **RDW-007** — Material weakness in internal controls over financial reporting (KPMG adverse opinion as of Dec 31, 2025). Net loss of $226.6M on $335.4M revenue in 2025. $94.5M cash + $35M revolver capacity; $88.4M 
  - Interpretation: Severe distress / quality-of-earnings markers per heuristic 10. KPMG issued an adverse opinion on internal control over financial reporting as of Dec 31, 2025. Two distinct material weaknesses identified (process-level controls; IT general controls). Net loss expanded to $226.6M (-68% operating margin) on $335.4M revenue. EAC unfavorable adjustments are accelerating year-over-year (-$3.5M -> -$17.
#### 🟡 MODERATE_UNDERDELIVERY claims
- **RDW-003** — Redwire is the prime mission integrator on DARPA's Otter VLEO air-breathing satellite program using its SabreSat platform, and Phantom is being used on ESA's Skimsat VLEO program.
  - Interpretation: Partial corroboration. DoD aggregate ($70.4M, 12 awards) supports the general defense relationship, but the SPECIFIC DARPA Otter prime-integrator contract does not appear in USAspending awards under DARPA-labeled awarding sub-agency or with 'Otter / VLEO / air-breathing' keywords in descriptions. Th
- **RDW-006** — Defense Tech segment includes Stalker UAS and Penguin UAS. On July 14, 2025, Stalker UAS was granted Authority to Operate by the DIU and placed on the DIU Blue UAS List. Stalker has 'thousands of flig
  - Interpretation: Mixed corroboration. The acquired Edge Autonomy entity shows just $1.6M of USAspending contracts post-2020 (a single VXE30 STALKER purchase order with the Department of the Navy), plus $61K to legacy UAV Factory (Penguin's original OEM). Foreign sales (Ukraine, Latvia, Lithuania, Saudi) are heuristi
- **RDW-008** — Redwire's solar/power systems are flight-deployed on NASA's Imaging X-ray Polarimetry Explorer (IXPE), NASA's DART, NASA's Artemis I lunar mission, ISS, and Space Force GPS Satellite program. Redwire 
  - Interpretation: Mixed. The 'national security satellite constellation in LEO' claim is a vague / unnamed-program reference (likely SDA or NRO Proliferated LEO) and is NOT verifiable in USAspending top-50 awards under either USSF, SDA, or NRO as awarding agency. None of the three defense primes plausibly involved (L

### ASTS — AST SpaceMobile, Inc.

- **Filing analyzed:** `0001780312-26-000006_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=5, MODERATE=3, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.38

#### 🟡 MODERATE_UNDERDELIVERY claims
- **ASTS-1** — ASTS has a federal contract with the U.S. Space Development Agency (SDA) — including a $43.0M contract via a prime contractor for testing services using the initial BB satellites, plus a direct $30.0M
  - Interpretation: Calibration Heuristic Layer 3 Rule 7 fires. The SHIELD IDIQ existence IS corroborated (a $500 'initial order' under HQ085926DG110 / HQ085926FF777 matches the 10-K's IDIQ disclosure), so the relationship is genuine. The $43M SDA-via-prime contract may legitimately be off-USAspending under ASTS's name
- **ASTS-4** — ASTS has 5 Block 1 BB satellites in orbit (launched September 12, 2024) and launched its first Block 2 BB satellite (BB6) on December 23, 2025 — i.e. 6 commercial BB satellites in orbit at cutoff, wit
  - Interpretation: Calibration Heuristic 3 (planned vs operational) AND Heuristic 9 (constellation-operational vs constellation-announced) — the 6-satellites-in-orbit count is internally consistent and externally well-mentioned. HOWEVER the much larger constellation (multiple hundreds at design) required for global co
- **ASTS-6** — ASTS reports $2.8 billion of cash and restricted cash at 12/31/2025 (up from $567.5M at 12/31/2024), reported FY2025 net loss before NCI of approximately $461M; SpaceMobile Service has not been launch
  - Interpretation: Calibration Heuristic 10 (DELISTING / GOING-CONCERN) — the surface looks fine right now: $2.8B cash, no active going-concern qualifier, no recent reverse split. HOWEVER (a) the company has $0 service revenue and a $461M annual loss, with capex still required for the Block 2 production ramp, (b) the 

### SATS — EchoStar Corporation

- **Filing analyzed:** `0001558370-25-001663_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.38

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C4** — $26.6B total debt / finance lease obligations outstanding (Dec 31, 2024); $53.1B total 5-year long-term obligations including interest; $5.356B 10-3/4% Senior Secured Notes due 2029 issued Nov 2024; $
  - Interpretation: SEVERE. From a Signal OS forward-test posture (cutoff 2026-05-16, FY2024 10-K filed Feb 2025): the financing structure disclosed in this 10-K is already a forensic distress pattern — distressed-pricing senior secured + senior unsecured exchange offers extinguishing par-value convertibles + related-party backstop + buyer (DTV) walking away from the proposed Pay-TV divestiture. The fact that EchoSta
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — $30B+ invested in Wireless spectrum licenses; total carrying amount $38.99B (including $9.5B capitalized interest) as of Dec 31, 2024; FCC Extension Request grants final-deadline extensions from June 
  - Interpretation: Spectrum investment claim is verifiable and corroborated by capitalized cost on balance sheet ($9.5B capitalized interest specifically suggests aging-asset, not productive return). The FCC Extension Request is a real regulatory event but is itself an EXTENSION of build-out deadlines that have repeat

### RKLB — Rocket Lab USA, Inc.

- **Filing analyzed:** `0001819994-26-000013_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.14

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C7** — Neutron medium-lift vehicle (13,000 kg reusable to LEO) under development at LC-3 Wallops; Jan 21 2026 Stage 1 tank ruptured in hydro qual test, impacting launch schedule; securities class action re N
  - Interpretation: MODERATE per Calibration Heuristic 3 (planned-vs-operational with EXTRA WEIGHT). Neutron is squarely in the 'design/prototype' stage of the stage ladder — not yet first-launched. The Jan 2026 tank rupture is candidly disclosed as a subsequent event, and the 8-K trail confirms timely public disclosur

### PL — Planet Labs PBC

- **Filing analyzed:** `0001193125-26-119957_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.14

#### 🟡 MODERATE_UNDERDELIVERY claims
- **PL-C8** — Remaining performance obligations of $852.4M as of Jan 31, 2026; ~34% to be recognized within 12 months, ~65% within 24 months.
  - Interpretation: RPO is a real GAAP number, but the lack of counterparty corroboration in US-listed defense primes is consistent with PL's customer base being non-US-filer governments (Sweden, NATO, Ukraine, IC). MODERATE rather than PASS because Heuristic 9 (constellation-operational vs announced) applies: a meanin

### IRDM — Iridium Communications Inc.

- **Filing analyzed:** `0001418819-26-000009_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=7, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.12

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C5** — Iridium NTN Direct (3GPP Release 19 standards-based NB-IoT / D2D service) expected to commercially launch in 2026 from existing constellation.
  - Interpretation: MODERATE: pure NTN Direct stage = planned/imminent, not operational. Standards acceptance (3GPP R19) and chipset partner (GCT) corroborate technical readiness, but commercial service is not yet live. Track 2026 launch milestone.

## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### RDW
- Composite: **0.71**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=14.6%   inst_own=47%   recom=1.50
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### ASTS
- Composite: **0.38**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=20.8%   inst_own=41%   recom=2.69
- **Decision: no bet.** Composite 0.38 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### SATS
- Composite: **0.38**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=31.2%   inst_own=59%   recom=1.83
- **Decision: no bet.** Composite 0.38 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### RKLB
- Composite: **0.14**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **HIGH**   short_float=5.8%   inst_own=52%   recom=1.45
- **Decision: no bet.** Composite 0.14 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### PL
- Composite: **0.14**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=12.2%   inst_own=60%   recom=1.55
- **Decision: no bet.** Composite 0.14 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### IRDM
- Composite: **0.12**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=5.9%   inst_own=85%   recom=2.27
- **Decision: no bet.** Composite 0.12 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** Space milestones slip routinely for engineering reasons.
- **FAA launch records** aren't plumbed as an M-source; launch-cadence claims rely on counterparty disclosure.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **FAA launch registry / launch-license tracking is the #1 coverage gap.** A connector would directly verify launch-cadence claims.
- **Foreign-launch / foreign-sat-operator contracts** (ESA, JAXA, ISRO, Telesat) are off-EDGAR.
