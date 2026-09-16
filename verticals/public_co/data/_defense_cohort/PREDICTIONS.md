# Defense-Tech Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T07:20:48.129634Z — cutoff 2026-05-16_

## Methodology

Five US-listed defense-tech / military-drone names. Each ticker was analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch access, no shared context with other tickers. Each subagent:

1. Read the company's most recent pre-cutoff filing (most recent 10-K or S-1).
2. Extracted 5-8 specific, testable, falsifiable factual claims.
3. Picked M-source queries from the catalog (USAspending, USPTO ODP, EDGAR full-text against counterparty CIKs, EPA FRS).
4. Executed queries and scored each claim PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

**This is the Signal OS thesis applied as intended:** R (claim made by the company in SEC filing) − f(M, where M is an independent registry the prevailing analysis isn't using). The framework's edge is in M-side lookups (USAspending for DoD contracts, USPTO ODP for patents, EDGAR for counterparty disclosure) that ordinary screeners don't perform.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | ONDS | Ondas Inc. | 8 | 3 | 1 | 1 | 2 | 1 | 1.29 |
| 2 | RCAT | Red Cat Holdings, Inc. | 8 | 3 | 1 | 2 | 0 | 2 | 0.83 |
| 3 | AIRO | AIRO Group Holdings, Inc. | 8 | 3 | 0 | 0 | 1 | 4 | 0.75 |
| 4 | UMAC | Unusual Machines, Inc. | 8 | 6 | 0 | 0 | 0 | 2 | 0.00 |
| 5 | KTOS | Kratos Defense & Security Solutions | 8 | 7 | 0 | 0 | 0 | 1 | 0.00 |

## Per-ticker forward predictions

### ONDS — Ondas Inc.

- **Filing analyzed:** `0001213900-26-035981_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=3, MODERATE=1, SEVERE=1, RED_FLAG=2, UNVERIFIABLE=1
- **Composite severity:** 1.29

#### 🔴 RED_FLAG_NEGATIVE claims
- **C1** — OAS primarily targets defense, homeland security, and public safety customers. A significant portion of revenue depends on government customers.
  - M-check: `USAspending federal contracts/grants for Ondas, Airobotics, American Robotics, Sentrycs, Roboteam (2020-2026)`
  - M-value: Direct 'Ondas' substring matches = 10 awards / $206K, but ALL 10 are HONDASHOKAI Y.K. (a Japanese supplier — plywood, freezer boxes, flow meter calibration in Iwakuni). Zero awards to Ondas Inc., Ondas Holdings, Ondas Networks, Ondas Autonomous Systems. Airobotics: 0 contracts, 0 grants. Sentrycs: 0
  - Interpretation: Apply Layer 3 Rule 7 + Heuristic 9: company positions itself as a US-defense / homeland-security / public-safety contractor and explicitly tells investors that 'a significant portion of our business... involves sales to government customers, including defense, homeland security, and public safety agencies.' USAspending shows essentially zero federal contract obligations across the parent and every
- **C6** — Sentrycs (CoRF CUAS), Roboteam (UGV), 4M Defense (demining) are deployed defense capabilities feeding the US DoD / Western military customer base.
  - M-check: `USAspending federal contracts for Sentrycs and Roboteam (2020-2026)`
  - M-value: Sentrycs: 0 federal awards. Roboteam: 0 federal awards. (Both queried unrestricted by awarding agency — covers DoD, DHS, State, every federal buyer.)
  - Interpretation: Per Heuristic 9: company markets Sentrycs and Roboteam as integrated CUAS/UGV defense platforms that can be deployed for 'defense, homeland security, and public safety customers' and ties them directly to US DoD spending ('U.S. defense budget surging to nearly $748 million for small unmanned systems in FY2026'). Zero federal contract obligations for either named subsidiary is a HARD CONTRADICTION 
#### 🟠 SEVERE_UNDERDELIVERY claims
- **C5** — Ondas Networks has historically targeted North American freight rail (AAR, Class I railroads) as the early adoption market for FullMAX; industry bodies including AAR adopted IEEE 802.16.
  - Interpretation: Apply Heuristic 7 with caveat: railroads ARE the claimed end customer and FullMAX/AAR/802.16 deployment is the company's headline rail proof-point. A genuine Class I railroad rolling out FullMAX over a multi-year PTC/next-gen-comms program would typically appear in 10-K risk factors, capex disclosures, or vendor-concentration mentions; total absence across the five US Class I railroads and Wabtec 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C2** — Two customers accounted for $27.8M (55%) and $5.4M (11%) of 2025 revenue (vs. $3.8M / $1.9M / $0.7M for top 3 customers in 2024 — a 7x+ jump in concentration revenue), with one customer = 73% of A/R a
  - Interpretation: Apply Heuristic 7 (counterparty-disclosure threshold): a $27.8M relationship is generally NOT material to a Class I railroad ($25B-$30B revenue) or a top-5 defense prime ($30B-$70B revenue), so absence of mention there alone is not dispositive. However, combined with the 73% A/R concentration and re

### RCAT — Red Cat Holdings, Inc.

- **Filing analyzed:** `0001628280-26-019861_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=3, MODERATE=1, SEVERE=2, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.83

#### 🟠 SEVERE_UNDERDELIVERY claims
- **C1** — Teal selected as winner of U.S. Army SRR Program of Record (Nov 2024); FY2025 revenue growth attributed primarily to scaling drone deliveries under SRR program.
  - Interpretation: RCAT claims FY2025 $40.7M revenue with ~73% from US Government (~$29.7M), primarily driven by SRR Program of Record scaling. USAspending shows only ~$4.9M of DoD obligations across ALL RCAT subsidiaries (Teal, FlightWave, Red Cat) and ~$7.0M including non-DoD federal — a ~4-6x gap vs. claimed government revenue. Per Heuristic 9 (DoD-CONTRACT-SPECIFIC): absence of SRR-named obligations for a compan
- **C2** — FY2025: ~73% of $40.7M revenue from US Government (~$29.7M).
  - Interpretation: Either claimed revenue substantially overstates real federal demand, OR USAspending recipient-name search materially undercounts via (a) prime-sub flow-throughs where RCAT is a subcontractor not the named recipient (NDAA/Blue UAS purchases via large primes); (b) sales through DIU's Blue UAS Marketplace where final recipient may be a procurement office aggregator; (c) Foreign Military Sales not in 
#### 🟡 MODERATE_UNDERDELIVERY claims
- **C7** — FlightWave (acquired Sept 2024) has existing relationships with several U.S. government agencies including classification as approved vendors — basis for $8.7M of goodwill.
  - Interpretation: FlightWave's DoD presence is real but modest ($2.3M lifetime). Ascribing $8.7M of goodwill to 'approved vendor' relationships with 'several US government agencies' is a soft claim — the actually-traceable federal contracting footprint is small. Not a hard contradiction (federal relationship exists),

### AIRO — AIRO Group Holdings, Inc.

- **Filing analyzed:** `0001493152-26-014116_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=3, MODERATE=0, SEVERE=0, RED_FLAG=1, UNVERIFIABLE=4
- **Composite severity:** 0.75

#### 🔴 RED_FLAG_NEGATIVE claims
- **AIRO-8** — Material related-party/stock-for-services/contingent-equity outflows + disclosed material weaknesses in ICFR.
  - M-check: `Filing self-disclosure - no external M-source needed`
  - M-value: {'stock_for_services_patterns': ['Dangroup: 20% of Sky-Watch EBITDA as annual incentive ($5.7M expensed 2025, related-party payable) + diluted to 5% fully-diluted equity stake at IPO', 'Jaunt Carter Aviation contingent payable: $44.6M converted to 1,122,437 shares + $5M cash at IPO', 'Aspen Bridge N
  - Interpretation: Cluster of generic distress fingerprints from Memory's stock-for-services-as-distress-flag rubric: vendor payables converted to equity at IPO across multiple subsidiaries (Jaunt, Aspen, Coastal Defense, Agile Defense, AIRO Drone), 20% of subsidiary EBITDA payable to a stockholder via 'incentive agreement', and investor notes accruing interest at PRINCIPAL-multiple rates (100-150% in stock). Combin

### UMAC — Unusual Machines, Inc.

- **Filing analyzed:** `0001683168-26-001730_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.00


### KTOS — Kratos Defense & Security Solutions, Inc.

- **Filing analyzed:** `0001069258-26-000013_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=7, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### ONDS
- Composite: **1.29**   RED_FLAGs: 2   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=34.5%   inst_own=41%   recom=1.00
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### RCAT
- Composite: **0.83**   RED_FLAGs: 0   SEVERE: 2   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=27.0%   inst_own=56%   recom=1.00
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### AIRO
- Composite: **0.75**   RED_FLAGs: 1   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=10.7%   inst_own=29%   recom=1.67
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months of 2026-05-16, at least one of the following occurs: (a) the next 10-K/10-Q/20-F materially restates the RED_FLAG claim; (b) the company announces a strategic pivot away from the disputed claim; (c) the counterparty publicly contradicts the company's representation; (d) the company files Form 15-12G / 25-NSE / Chapter 11; (e) the stock falls >50% from cutoff price.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### UMAC
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=19.6%   inst_own=64%   recom=1.00
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### KTOS
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=5.6%   inst_own=91%   recom=1.39
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** RED_FLAG_NEGATIVE means the filing claim diverges from independent registry evidence at the cutoff. It does not mean the company is lying. Multiple legitimate reasons exist for registry absence (early-stage programs, prime/sub flow-through, foreign sales, classified IP) and are noted per-claim where they apply.
- **Not a trade recommendation.** Most names in this cohort are micro-cap and may not be cleanly shortable (see prior `_distress_sift/PREDICTIONS.md` for the shortability methodology — same applies here).
- **Not pre-registered.** For the predictions to count as honest forward bets they need a cryptographic timestamp. Recommend committing this report's hash to git or an external timestamp service.

## Debt and tradeoffs

- **Subagent variance.** Five independent runs produced slightly different claim selection per ticker. UMAC's 8 claims overlap only partially with what RCAT's subagent picked even though both are drone names. The framework's discrimination depends on the LLM picking the right claims; a re-run with different temperature could shift the result.
- **USAspending recipient-name matching is fuzzy.** AIRO's subagent caught the 'Agile Defense LLC' name collision ($1B unrelated IT contractor); ONDS's subagent caught the 'HONDASHOKAI' substring noise. Both were correctly excluded but a less careful run might credit the company with another entity's contracts.
- **Coverage gaps surfaced by subagents (queued for `connectors_to_add.md`):**
  - DIU Blue UAS Cleared List (no current connector — every drone company's     core regulatory-milestone claim scores UNVERIFIABLE without it)
  - FAA UAS registry (similar)
  - Class I freight railroad counterparty CIKs (need to add to common-counterparties)
- **Process rules surfaced by subagents are captured to memory** in `feedback_*.md` files per the subagent-rule-capture rule (`feedback_subagent_rule_capture.md`).
