# J-Book Exposure Cohort — Forward-Test Predictions

_Generated 2026-05-20T17:58:13.247159Z — cutoff 2026-05-20_

_Tickers: 13 completed, 0 pending_

## Methodology

Each ticker is analyzed by an isolated, **blinded** Claude Code subagent that focuses on the J-BOOK EXPOSURE DIVERGENCE PATTERN: company makes a material claim about a named Pentagon program → pentagon_jbook M-source returns the program's forward funding status from a 410-program corpus (DARPA + MDA + SOCOM + OSD + AF RDT&E Vol I-IV + Space Force RDT&E + selected procurement). Severity tiers map directly from J-Book status:
- FUNDED_GROWING / FUNDED_STEADY → PASS
- FUNDED_SHRINKING → MODERATE_UNDERDELIVERY
- UNFUNDED_THIS_YEAR → SEVERE_UNDERDELIVERY
- UNFUNDED_TWO_PLUS_YEARS / TERMINATED → RED_FLAG_NEGATIVE
- NOT_FOUND → UNVERIFIABLE (coverage gap)

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | JBook hits | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | ARQQ | Arqit Quantum Inc. | 9 | 5 | 1 | 2 | 1 | 1 | 4 | 1.40 |
| 2 | IONQ | IonQ, Inc. | 11 | 5 | 4 | 1 | 1 | 3 | 3 | 1.33 |
| 3 | BBAI | BigBear.ai Holdings, Inc. | 10 | 5 | 0 | 6 | 3 | 0 | 1 | 1.33 |
| 4 | QBTS | D-Wave Quantum Inc. | 13 | 3 | 4 | 2 | 5 | 1 | 1 | 1.25 |
| 5 | QUBT | Quantum Computing Inc. | 11 | 4 | 2 | 2 | 4 | 0 | 3 | 1.25 |
| 6 | AIRO | AIRO Group Holdings, Inc. | 8 | 5 | 1 | 4 | 2 | 0 | 1 | 1.14 |
| 7 | RDW | Redwire Corporation | 12 | 7 | 3 | 4 | 2 | 1 | 2 | 1.10 |
| 8 | RCAT | Red Cat Holdings, Inc. | 10 | 4 | 2 | 2 | 0 | 1 | 5 | 1.00 |
| 9 | KTOS | Kratos Defense & Security Solutions | 12 | 8 | 4 | 3 | 2 | 0 | 3 | 0.78 |
| 10 | ASTS | AST SpaceMobile, Inc. | 9 | 5 | 3 | 2 | 1 | 0 | 3 | 0.67 |
| 11 | RKLB | Rocket Lab USA, Inc. | 10 | 5 | 5 | 3 | 0 | 0 | 2 | 0.38 |
| 12 | RGTI | Rigetti Computing, Inc. | 12 | 5 | 4 | 2 | 0 | 0 | 6 | 0.33 |
| 13 | PL | Planet Labs PBC | 12 | 8 | 6 | 2 | 0 | 0 | 4 | 0.25 |

## Per-ticker forward predictions

### ARQQ — Arqit Quantum Inc.

- **Filing analyzed:** `0001104659-25-119500_20-F.txt`
- **Claims extracted:** 9  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=1, MODERATE=2, SEVERE=1, RED_FLAG=1, UNVERIFIABLE=4
- **Composite severity:** 1.40

#### 🔴 RED_FLAG_NEGATIVE claims
- **C1** — Arqit's first U.S. Department of War (DoD) contract is in partnership with a large, leading U.S. IT vendor; symmetric-key encryption integrated into that vendor's product offering to the U.S. government.
  - M-check: `pentagon_jbook + usaspending.query_dod_contracts`
  - M-value: J-Book NOT_FOUND on contractor; USAspending shows zero DoD awards on either Arqit Quantum Inc. or Arqit Limited
  - Interpretation: The company narrates a 'first U.S. Department of War contract' but neither the prime nor the unnamed channel-partner-as-prime route surfaces any DoD obligation tied to Arqit anywhere in USAspending. Even allowing for sub-tier obligations being invisible to USAspending's recipient view, the absence of any direct or pass-through obligation through 2026-05-20 is a hard contradiction to a material 'fi

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C5** — One customer represents >56% of FY2025 total revenue ($530k); FY2024 one customer = 10% of $293k; FY2023 two customers = 10% each of $640k.
  - Interpretation: The customer-concentration *numbers* are factual (disclosed in audited footnote) and are verifiable as filed. The interpretive severity comes from cross-checking against the company's defense-narrative weight: government & military are claimed as the 'largest potential source of revenue' yet (a) total revenue across all categories is $530k, (b) one undisclosed customer drives 56% of that and is co

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C6** — GTM is B-2-B-2-B channel model; named channel partners are Sparkle (Italy), Fabric/RSG (Canada), unnamed US IT vendor for DoW, unnamed Middle East IT vendor.

- **C9** — FY2025 financing inflow $47.1m vs $0.53m revenue and $29.6m opex burn — equity-funded narrative.


### IONQ — IonQ, Inc.

- **Filing analyzed:** `0001193125-26-071562_10-K.txt`
- **Claims extracted:** 11  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=4, MODERATE=1, SEVERE=1, RED_FLAG=3, UNVERIFIABLE=3
- **Composite severity:** 1.33

#### 🔴 RED_FLAG_NEGATIVE claims
- **C1** — IonQ names AFRL, DARPA, and Oak Ridge National Laboratory as government customers / partners — IonQ's AFRL trapped-ion / quantum-networking work is the company's flagship DoD program-of-record narrative; ORNL is the named DOE national-lab partner.
  - M-check: `pentagon_jbook.query_program_funding(program_name=AFRL Quantum Networking, cutoff=2026-05-20); doe_budget.query_program_funding(program_name=Advanced Computing Technologies, qis_only=True)`
  - M-value: pentagon_jbook: UNFUNDED_TWO_PLUS_YEARS — primary contractor IonQ Inc; FY22=$13M, FY23=$26M, FY24=$12M (all earmark-funded, never Pentagon-requested), FY25=$0, FY26=$0 (second consecutive unfunded year per FY26 bipartisan budget signed Jan 20 2026). PIID FA8750-22-C-1022 ($13.4M obligated via AFRL R
  - Interpretation: CANONICAL J-BOOK DIVERGENCE — unchanged from v1. IonQ's marquee federal program-of-record (AFRL Rome quantum-networking contract) has been zero-funded by the Pentagon for two consecutive fiscal years through cutoff; pure congressional add (earmark) from FY22-FY24 that the Pentagon never requested. Earmark sponsors (Tester-MT, Cardin-MD, Van Hollen-MD, Hoyer-MD) lost majority power after Nov 2024 e

- **C8** — IonQ executed 7 acquisitions in ~12 months (ID Quantique, Lightsynq, Capella Space, Oxford Ionics, Vector Atomic, Skyloom, SkyWater-pending).
  - M-check: `acq_coherence.score_acquisition_coherence(parent_thesis=quantum platform, acquisitions=[8])`
  - M-value: Aggregate signal=INCOHERENT_ROLLUP. 4 of 8 acquisitions scored low_coherence with is_revenue_synthetic=true: Capella Space (SAR Earth observation, score 0.05), Vector Atomic (atomic clocks/PNT, 0.35), Skyloom Global (optical inter-sat links, 0.35), SkyWater Technology (semiconductor foundry, 0.15). 
  - Interpretation: Unchanged from v1. Canonical IonQ-thesis rollup pattern: the parent loses its core federal revenue stream (AFRL Quantum Networking earmark zeroed) and pivots into incoherent acquisitions including a SAR satellite company, a semiconductor foundry, and a laser-comms company — none of which have technology overlap with trapped-ion quantum computing. Per heuristic 'acq_coherence.INCOHERENT_ROLLUP + pe

- **C-INSIDER-SUPP** — [SUPPLEMENTARY] Insider sales clustering around budget-vote dates while AFRL Quantum Networking was being zeroed.
  - M-check: `insider_vs_calendar.query_insider_sales_near_budget_events(cik=0001824920, lookback_days=730, cutoff=2026-05-20)`
  - M-value: 99 Form 4 filings; 74 sales = $460.6M total; 14 proximate to budget events = $77.4M; 12 discretionary proximate; 4 unique proximate sellers. Top proximate sale: Peter Hume Chapman (ex-CEO) on 2025-03-11 (same day House passed FY25 full-year CR confirming AFRL earmark zeroing) — 2 lots of 2,000,000 s
  - Interpretation: Unchanged from v1. CLUSTERED_DISCRETIONARY signal is unambiguous: the ex-CEO and two named officers sold discretionarily (non-10b5-1) on the exact dates of three budget actions that quietly zeroed out the AFRL Quantum Networking line. This is the canonical YSS/IONQ pattern explicitly called out in the m-source catalog description for insider_vs_calendar. Treats as RED_FLAG_NEGATIVE supplementary s

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C2** — IonQ states $370.0M in remaining performance obligations (mix funded + unfunded) and that 'anticipated future revenues from the U.S. government result from contracts awarded under various U.S. government programs.'
  - Interpretation: Unchanged from v1. The $370M backlog is the most narrative-load-bearing forward number in the filing, but IonQ concedes in plain text that it includes UNFUNDED orders. The flagship AFRL Quantum Networking is zero-funded for the second consecutive FY through cutoff. v2 DOE retry materially STRENGTHENS the v1 reading: the $370M RPO cannot be implicitly defended as 'DOE-program revenue' because doe_b

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — Three customers = 53% of FY2025 revenue; IonQ expects increasing concentration. Two customers = 77% in FY24; two = 58% in FY23.


### BBAI — BigBear.ai Holdings, Inc.

- **Filing analyzed:** `0001836981-26-000018_10-K.txt`
- **Claims extracted:** 10  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=0, MODERATE=6, SEVERE=3, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 1.33

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C4** — Revenue is heavily concentrated in U.S. government T&M (61%) and FFP (25%) contracts; positioned as a defense / national security AI prime.
  - Interpretation: This is the strongest J-Book divergence finding in the filing. The 10-K positions BBAI as a defense / national security AI prime concentrated in U.S. government T&M and FFP contracts (61% + 25% = 86%) — but the company does not name a single Program Element or program-of-record by name anywhere in the 10-K. USAspending reveals what the 10-K elides: the recent post-2022 contract footprint is a seri

- **C5** — Biometrics / digital identity (Pangiam) and customs (CargoSeer) are forward growth vectors tied to CBP / TSA / DHS programs.
  - Interpretation: Pangiam (acquired Feb 2024 for $70M) and CargoSeer (acquired Jan 2026 for $5M) jointly anchor BBAI's stated 'travel and trade' / 'digital identity' / 'customs' growth thesis. USAspending shows ZERO federal contract obligations for either entity — meaning the biometric / customs revenue, if it exists, runs through the BigBear.ai or BigBear.ai Federal entity rather than the subsidiary brand, OR runs

- **C9** — Forward thesis depends on the January 2026 'AI Acceleration Strategy', 'Pace-Setting Projects', and 'AI Model Parity' policy framework.
  - Interpretation: The 10-K explicitly elevates the January 2026 'AI Acceleration Strategy' / 'Pace-Setting Projects' / 'AI Model Parity' policy framework to the level of THE principal forward growth catalyst. Pentagon_jbook returns NOT_FOUND for all three terms — meaning none of these slogans has yet been translated into a budgeted Program Element with appropriated dollars. The earmark_detector also returns NOT_EAR

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Ask Sage is used by '100,000 Department of War users' and is positioned as the central pillar anchored by the U.S. 'AI Acceleration Strategy' Pace-Setting Projects.

- **C3** — ConductorOS was 'central to exercise Talisman Sabre' in 2025; positioned as flagship DoD-deployed edge-AI orchestration product.

- **C6** — Operational readiness business 'streamlines manpower, equipment, and supply chain data', positioning the company in Army force-generation / readiness decision-support.

- **C7** — Strongest financial position in company history; $461M cash; $637M ATM gross proceeds; $271.6M Ask Sage purchase + Pangiam + ProModel + CargoSeer rollup.

- **C8** — DHS remains unfunded post-Feb 3, 2026 shutdown deal; 'impact of the January shutdown did not have a meaningful impact on our results'.

- **C10** — Company relies on patents / trade secrets but is 'not dependent on any particular patent or application'.


### QBTS — D-Wave Quantum Inc.

- **Filing analyzed:** `0001907982-26-000026_10-K.txt`
- **Claims extracted:** 13  (J-Book M-source fired on 3)
- **Severity distribution:** PASS=4, MODERATE=2, SEVERE=5, RED_FLAG=1, UNVERIFIABLE=1
- **Composite severity:** 1.25

#### 🔴 RED_FLAG_NEGATIVE claims
- **C5** — Customer A = 67% of FY2025 revenue (vs 17% in FY2024); not named.
  - M-check: `usaspending.query_federal_presence(D-Wave variants) + usaspending.query_dod_contracts(D-Wave)`
  - M-value: {'federal_presence_signal': 'INFLATION_SUSPECT', 'n_contracts': 0, 'contracts_amount_M': 0.0, 'dod_signal': {'n_awards': 0, 'total_amount': 0.0}, 'fy2025_total_revenue_M': 24.6, 'implied_customer_a_M': 16.5}
  - Interpretation: Unchanged from v1. Customer A is ~$16.5M (67% of $24.6M FY2025 revenue) and went from 17%->67% YoY. USAspending shows ZERO federal contracts/grants under any D-Wave name variant, including the UEI-anchored D-Wave Government Inc. - so Customer A is NOT a U.S. federal customer. Cross-referencing the 10-K narrative, the most likely identity is Forschungszentrum Juelich, which 'purchased' the Advantag

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C1** — D-Wave achieved 'awardable' status through the CDAO Tradewinds Solutions Marketplace.
  - Interpretation: INFLATION_SUSPECT (unchanged from v1). D-Wave Government Inc. is registered as a federal contractor (UEI PATGKJM747F7) but has $0 in contracts and $0 in grants across 2018-05/2026. Tradewinds 'awardable' status is a marketplace eligibility flag, not a contract - it confirms that no DoD program has actually obligated dollars to D-Wave. Claim materially overstates federal traction.

- **C4** — D-Wave formed a new business unit dedicated to U.S. government adoption, led by a public-sector executive.
  - Interpretation: Unchanged from v1. A federal contracting subsidiary (D-Wave Government Inc.) exists and is SAM-registered, but has obligated $0 across the entire 2018-2026 window - confirmed via UEI-anchored USAspending lookup. A 'new business unit' with a 'seasoned public sector executive' is forward narrative; there is no historical federal revenue base to extend. SEVERE_UNDERDELIVERY.

- **C9** — D-Wave addresses 'unique research and government classified applications' as a growth market.
  - Interpretation: v2 HARDENS to SEVERE_UNDERDELIVERY (was SEVERE_UNDERDELIVERY in v1; not changed in tier but evidentially strengthened). New evidence: (i) doe_budget.query_program_funding(contractor='D-Wave') returns NOT_FOUND - independent funding line, same answer; (ii) DOE-side QIS programs (ASCR Advanced Computing Technologies FUNDED_GROWING $105M->$112M, BES-QIS, HEP-QIS) ARE funded and growing, so the 'class

- **C10** — D-Wave Government Inc. is the primary federal contracting entity.
  - Interpretation: Unchanged from v1. UEI exists, $0 in awards. The subsidiary functions as a registration vehicle without an operating federal contract footprint. SEVERE_UNDERDELIVERY relative to the framing that the entity is the 'primary federal contracting' arm.

- **C13** — [NEW v2] D-Wave annealing systems used at ORNL, LANL, Juelich Supercomputing Centre, USC ISI, NASA QuAIL, USRA - multi-DOE-lab footprint anchoring federal-relevance narrative; Science paper benchmarks Advantage2 vs ORNL Frontier supercomputer.
  - Interpretation: NEW v2 SEVERE_UNDERDELIVERY. The 10-K name-drops ORNL, LANL, NASA QuAIL, USC ISI, FZJ and USRA in a single 'institutions that have used our technology' sentence, immediately following a Lockheed Martin / Frontier supercomputer benchmark paragraph - framing for federal-research credibility. doe_budget cross-check: (a) the host program (Oak Ridge Leadership Computing Facility) is FUNDED_STEADY at $2

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — Davidson Technologies hosts the second U.S.-based D-Wave Advantage2 quantum computer in Huntsville, AL.

- **C3** — D-Wave worked with Davidson + Anduril on a missile-defense planning proof-of-concept (>=10x speedup, +45-60 missiles intercepted).


### QUBT — Quantum Computing Inc.

- **Filing analyzed:** `0001213900-26-022417_10-K.txt`
- **Claims extracted:** 11  (J-Book M-source fired on 4)
- **Severity distribution:** PASS=2, MODERATE=2, SEVERE=4, RED_FLAG=0, UNVERIFIABLE=3
- **Composite severity:** 1.25

#### 🟠 SEVERE_UNDERDELIVERY claims
- **c1** — QCi's anticipated future revenues from the U.S. government are expected to result from contracts awarded under various U.S. government programs.
  - Interpretation: Two independent federal forward-funding corpora (Pentagon J-Book + DOE Office of Science) both fail to identify QUBT/QPhoton as a contractor anywhere. Combined with $95K lifetime federal contract revenue at the parent, the 'anticipated future revenue from U.S. government programs' narrative is unsupported on both forward (budget-justification books) and backward (USAspending) axes. v1 SEVERE ratin

- **c4** — QCi's quantum secured communication systems and the NuCrypt acquisition broaden QCi's quantum secured network product line for commercial and government customers.
  - Interpretation: v2 strengthens c4 by adding the DOE-side picture: the federal quantum-networking-research funding lines DO exist (DOE BES/ASCR QIS, HEP QIS) and they are funded — but QUBT/NuCrypt are not primary contractors on any of them. So the 'broaden quantum secured network product line for government customers' narrative falls in the gap: the DoD-side proxy program (AFRL Quantum Networking) is unfunded post

- **c9** — QCi FY2025 revenue was $682K (up 83% from $373K in FY2024), primarily derived from professional-services contracts provided to multiple commercial and government customers.
  - Interpretation: Mode-B customer-concentration misrepresentation. Heuristic #6 (USAspending shows zero DoD obligations against claimed program forward narrative → SEVERE_UNDERDELIVERY). v2 DOE retry independently confirms zero DOE-side contractor presence; the 'government customers' label is sustained by sub-$70K Commerce + NASA SBIRs only. SEVERE retained.

- **c11** — QCi's vision is to 'lead the revolution in photonics and quantum information technology with scalable, accessible, and affordable solutions to bring quantum technology into reality' — an implied positioning against the federally funded Quantum Inform
  - Interpretation: This is the explicit v2 test of the QUBT vision statement against the new DOE M-source. The hypothesis tested: 'QUBT positions to lead the quantum information technology revolution → there should be at least one DOE Office of Science line that lists a QUBT entity as a primary contractor or major awardee.' Result: ZERO matches across parent + 3 acquired sub names. The DOE QIS funding lines DO exist

#### 🟡 MODERATE_UNDERDELIVERY claims
- **c2** — QCi serves customers in aerospace and defense applications, in particular through LSI (Luminar Semiconductor) acquired February 2026.

- **c7** — Freedom Photonics, LLC (an LSI subsidiary) jointly owns and developed patents with Northrop Grumman Systems Corporation.


### AIRO — AIRO Group Holdings, Inc.

- **Filing analyzed:** `0001493152-26-014116_10-K.txt`
- **Claims extracted:** 8  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=1, MODERATE=4, SEVERE=2, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 1.14

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C3** — AIRO is pursuing DoD Blue UAS certification (target June 2026) to enable U.S. DoD sales of Sky-Watch / RQ-35 Heidrun small drones; certification expected to open access to U.S. small-UAS programs.
  - Interpretation: SEVERE_UNDERDELIVERY. Sky-Watch / RQ-35 Heidrun has ZERO DoD obligations in USAspending — the entire $70.5M+ FY25 Sky-Watch revenue (implied from 79% concentration on European NATO customers, foreign sovereigns) sits outside the U.S. budget. The 10-K narrative that Blue UAS certification will 'allow us to sell drones to the DoD' depends on a non-existent forward funding pool: PE 0208201F (Offensiv

- **C4** — AIRO's military drones target the 'arsenals of the future' — U.S. military pivot to smaller/agile force using endurance UAVs.
  - Interpretation: SEVERE_UNDERDELIVERY (on the rhetorical framing, not on AIRO's specific products). The 10-K's 'arsenals of the future' narrative implicitly maps Sky-Watch into the U.S. military's small/medium-altitude endurance UAV pool. The Air Force's Endurance UAV PE has been zeroed for two consecutive years and SOCOM's MQ-9 R&D line went to zero in FY26 — the very budget category AIRO is trying to position in

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — AIRO's CDI / Coastal Defense is 'mandated recipient on a $5.7 billion IDIQ contract and a $1.9 million IDIQ contract' for adversary air / CAS / ISR / JTAC training with SEAL teams, Naval Air Warfare C

- **C2** — Training segment expects forward growth from U.S. Air Force pilot training pipeline (advanced / undergraduate pilot training).

- **C5** — Two customers = 79% of FY2025 consolidated revenue, all Drone segment (Sky-Watch sales to Netherlands / Denmark / Germany sovereign defense procurements).

- **C6** — AIRO is a rollup of CDI training + Sky-Watch drones + Aspen Avionics + Agile Defense + Jaunt eVTOL + AIRO Drone; recent IPO; $210.6M accumulated deficit.


### RDW — Redwire Corporation

- **Filing analyzed:** `0001819810-26-000029_10-K.txt`
- **Claims extracted:** 12  (J-Book M-source fired on 7)
- **Severity distribution:** PASS=3, MODERATE=4, SEVERE=2, RED_FLAG=1, UNVERIFIABLE=2
- **Composite severity:** 1.10

#### 🔴 RED_FLAG_NEGATIVE claims
- **C12** — Material weaknesses in ICFR + adverse KPMG opinion as of Dec 31, 2025 — control-environment disclosure.
  - M-check: `insider_vs_calendar.query_insider_sales_near_budget_events(cik='0001819810') + edgar_fts.query_fulltext('Redwire')`
  - M-value: insider_vs_calendar: signal=PROXIMATE_DISCRETIONARY; n_form4_filings=57; n_proximate_sales=21 (ALL discretionary, ZERO via 10b5-1); proximate_value_usd=$858.7M sold by 2 unique owners (AE Red Holdings, Bain Capital Credit). Three matched budget-event clusters: (a) 2025-09-30 fiscal-year-end — Bain C
  - Interpretation: This is the textbook YSS/IONQ signature applied to RDW. Per heuristic 6 cross-check + insider-vs-calendar primary signal: $858M of proximate discretionary insider sales clustered around exactly the two budget events that confirmed SDA Transport Layer T3 going unfunded (claim C2's primary verifier). The largest single block ($231.8M, AE Red Holdings) sold 6 days BEFORE the FY27 J-Book confirmation.

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C2** — Redwire claims it is 'delivering multiple advanced RF payloads for a constellation of satellites for a national security satellite constellation in LEO' — unnamed but the only plausible LEO national-security-satellite-constellation customers in FY25 
  - Interpretation: MAJOR J-BOOK DIVERGENCE. The forward growth narrative for Redwire's Space segment (which carries $299.8M of the $411.2M backlog) leans on an unnamed 'national security LEO constellation' that is almost certainly PWSA. Per FY26/FY27 J-Books: Tranche 3 Transport Layer is unfunded for the second straight year, SDA is being dissolved as a standalone agency, and the replacement (Space Data Network) is 

- **C4** — Stalker UAS received DIU Authority to Operate / Blue UAS List status on July 14, 2025; positioned as DoD program-of-record growth lever.
  - Interpretation: USAspending cross-check (heuristic 6) reveals the canonical pattern: company narrative paints Stalker as a DoD program-of-record growth lever via Blue UAS listing, but post-listing federal obligations to Edge Autonomy LLC are essentially zero ($1.48M FMS to a third-country). RDW disclosed (Note: Edge Autonomy contributed $107M FY25 revenue, but mostly from foreign-military / Ukraine / commercial c

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — Redwire claims its Space segment supports U.S. Space Force's GPS Satellite program (flight heritage).

- **C6** — 46.9% of FY2025 revenue (~$157M) from national-security customers (Army, USMC, USAF, USSF, DARPA, NRO + allied agencies).

- **C7** — $411.2M total contracted backlog ($299.8M Space + $111.4M Defense Tech) characterized as 'firm funded executed contracts'.

- **C11** — Edge Autonomy acquisition (Jun 2025) — $1.025B consideration, $721M goodwill (70% of purchase), $34.7M goodwill+intangible impairment booked Q4 2025; concurrent ~$1B equity raise + Adams Street paydow


### RCAT — Red Cat Holdings, Inc.

- **Filing analyzed:** `0001628280-26-019861_10-K.txt`
- **Claims extracted:** 10  (J-Book M-source fired on 4)
- **Severity distribution:** PASS=2, MODERATE=2, SEVERE=0, RED_FLAG=1, UNVERIFIABLE=5
- **Composite severity:** 1.00

#### 🔴 RED_FLAG_NEGATIVE claims
- **C10** — Material weakness in internal control over financial reporting persists for second straight year as of 12/31/2025.
  - M-check: `sec_filings.list_filings_by_form + insider_vs_calendar`
  - M-value: Material weakness DISCLOSED (repeat); insider sales PROXIMATE_DISCRETIONARY around fiscal-year-end
  - Interpretation: This is not a J-Book claim but is the most concrete framework-actionable signal in the filing. Repeat material weakness + KPMG CAM on performance-obligation determination + 73% single-customer revenue concentration + discretionary insider selling around the period close is a stack of red flags. Score RED_FLAG_NEGATIVE for control quality, independent of the J-Book divergence pattern.

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — One customer (Army/SRR) accounted for 73% of FY2025 revenue; Customer A 88% of A/R at 12/31/2025.

- **C9** — Blue Ops launched Aug 2025, first USV delivered to FL showroom Q4 2025; expanding into all-domain via USV weapons.


### KTOS — Kratos Defense & Security Solutions, Inc.

- **Filing analyzed:** `0001069258-26-000013_10-K.txt`
- **Claims extracted:** 12  (J-Book M-source fired on 8)
- **Severity distribution:** PASS=4, MODERATE=3, SEVERE=2, RED_FLAG=0, UNVERIFIABLE=3
- **Composite severity:** 0.78

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C5** — Kratos positions its Valkyrie tactical drone (and broader UCAV / loyal-wingman portfolio) for the USAF/USMC Collaborative Combat Aircraft (CCA) opportunity, including teaming with Northrop Grumman on the MUX TACAIR CCA prime award, and describes ongo
  - Interpretation: CCA is one of the most prominent forward-revenue narratives in Kratos's 10-K (multiple mentions, the GE Aerospace teaming explicitly cites 'CCA-type aircraft' as the use case, and the MUX TACAIR / Northrop teaming is described as a significant 'recent' competitive win). The named AF CCA PE just absorbed an ~84% cut from FY25 to FY26 — Increments 1 (Anduril/General Atomics) appear funded through co

- **C6** — Kratos describes its GE Aerospace teaming agreement on the GEK800 and GEK1500 small turbofan/turbojet engines as a key forward-revenue driver supporting CCAs and unmanned aerial systems, citing successful October 2025 altitude testing on the GEK800.
  - Interpretation: The closest AF RDT&E lines to GEK800/GEK1500 small affordable turbofan engines are: 0603216F (Aerospace Propulsion and Power Technology — small-engine and air-breathing propulsion S&T) which is zeroed for 2+ years, and 0604010F (Next Generation Adaptive Propulsion — F-35-class engines, less directly relevant) which is funded but shrinking. The S&T pipeline that would fund expendable-engine prototy

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — Kratos is the prime sole-source producer of USAF BQM-167 (production year 21) and USN BQM-177 (production year 7) jet target drones, and explicitly identifies the BQM-167 and BQM-177 as programs that 

- **C4** — Kratos cites a $116.7 million prime contract from the U.S. Space Development Agency to create and operate the Advanced Fire Control Ground Infrastructure (AFCGI) and notes a clean September 2025 PDR —

- **C7** — Kratos cites the Erinyes, Dark Fury, Zeus 1 / Zeus 2 hypersonic vehicle and solid-rocket-motor portfolio as core forward-revenue platforms tied to OUSD(R&E) hypersonic flight test demand, with a 'rece


### ASTS — AST SpaceMobile, Inc.

- **Filing analyzed:** `0001780312-26-000006_10-K.txt`
- **Claims extracted:** 9  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=3, MODERATE=2, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=3
- **Composite severity:** 0.67

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C2** — AST has a direct ~$30M SDA agreement for the 'Europa Track 2 commercial solutions program'.
  - Interpretation: This is the canonical J-Book divergence catch. The company names a forward-leaning $30M SDA commercial-solutions program. The J-Book shows SDA's Tranche 3 Transport (the parent commercial-vehicle architecture) was zeroed in FY25 and FY26 (Congress added $500M and Pentagon rejected it); SDA itself is being dissolved, with requirements absorbed into SDN, sole-sourced to SpaceX. The replacement_progr

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — AST has a $43.0M SDA prime-contractor pass-through contract for testing services with initial BB satellites.

- **C6** — AST expects future revenue contributions from U.S. government or prime contractors for non-commercial BB satellite use.


### RKLB — Rocket Lab USA, Inc.

- **Filing analyzed:** `0001819994-26-000013_10-K.txt`
- **Claims extracted:** 10  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=5, MODERATE=3, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.38

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — Photon spacecraft can fly as a secondary payload on launches conducted under the National Security Space Launch (NSSL) program of the U.S. Space Force, framing NSSL as part of RKLB's go-to-market.

- **C8** — Rocket Lab reports a $12.8M unfavorable cumulative catch-up adjustment to revenue on a single contract for FY 2025, signaling cost-to-complete deterioration on a long-term fixed-price (likely governme

- **C10** — Rocket Lab cumulatively grew revenue to $601.8M (FY25) vs $436.2M (FY24) vs $244.6M (FY23), with continued net losses ($198M FY25). Forward narrative leans on SDA T3 plus GEOST plus HASTE plus Neutron


### RGTI — Rigetti Computing, Inc.

- **Filing analyzed:** `0001104659-26-023454_10-K.txt`
- **Claims extracted:** 12  (J-Book M-source fired on 5)
- **Severity distribution:** PASS=4, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=6
- **Composite severity:** 0.33

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Rigetti lists AFRL as a key multi-year development partnership for quantum networking hardware research and superconducting quantum computing networking.

- **C4** — Substantial majority of current revenues from development contracts; expects this to continue for several more years.


### PL — Planet Labs PBC

- **Filing analyzed:** `0001193125-26-119957_10-K.txt`
- **Claims extracted:** 12  (J-Book M-source fired on 8)
- **Severity distribution:** PASS=6, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=4
- **Composite severity:** 0.25

#### 🟡 MODERATE_UNDERDELIVERY claims
- **PL-008** — Capex 26% of revenue ($79.9M FY26) building Pelican + medium-res satellites; ROIC depends on signed SwAF contract + future D&I demand.

- **PL-012** — 10-K contains ZERO references to named Pentagon Program Elements (no PE numbers, no Project Maven, no EOCL, no SDA, no NRO/NGA in prose, no DIU, no JADC2, no Replicator, no Tradewind).

